"""
Tests pour la validation gracieuse des données généalogiques

Ces tests vérifient que le système de validation peut détecter et rapporter
plusieurs erreurs au lieu de s'arrêter à la première.
"""

import pytest

from geneweb_py.core.person import Person, Gender
from geneweb_py.core.family import Family, MarriageStatus
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.date import Date
from geneweb_py.core.validation import (
    validate_person_basic,
    validate_person_relationships,
    validate_family_basic,
    validate_family_members,
    validate_genealogy_consistency,
    validate_bidirectional_references,
    ValidationContext,
    create_partial_person,
    create_partial_family,
)
from geneweb_py.core.exceptions import (
    GeneWebValidationError,
    ErrorSeverity,
)


class TestValidationContext:
    """Tests pour le contexte de validation"""
    
    def test_validation_context_creation(self):
        """Test de création d'un contexte de validation"""
        context = ValidationContext()
        
        assert context.error_collector is not None
        assert not context.has_errors()
    
    def test_validation_context_add_error(self):
        """Test d'ajout d'erreur au contexte"""
        context = ValidationContext()
        
        error = GeneWebValidationError("Test error")
        context.add_error(error)
        
        assert context.has_errors()
        assert len(context.get_errors()) == 1
    
    def test_validation_context_add_warning(self):
        """Test d'ajout d'avertissement"""
        context = ValidationContext()
        
        context.add_warning("Test warning", line_number=10)
        
        assert context.has_errors()
        errors = context.get_errors()
        assert len(errors) == 1
        assert errors[0].severity == ErrorSeverity.WARNING
    
    def test_validation_context_get_result(self):
        """Test de récupération du résultat de validation"""
        context = ValidationContext()
        
        context.add_error(GeneWebValidationError("Error 1"))
        context.add_warning("Warning 1")
        
        result = context.get_result()
        
        assert not result.is_valid()
        assert result.has_warnings()


class TestPersonValidation:
    """Tests de validation des personnes"""
    
    def test_valid_person(self):
        """Test de validation d'une personne valide"""
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE,
            occurrence_number=0
        )
        
        result = validate_person_basic(person)
        assert result.is_valid()
    
    def test_person_missing_last_name(self):
        """Test de personne sans nom de famille"""
        person = Person(
            last_name="",
            first_name="Jean",
            gender=Gender.MALE,
            occurrence_number=0
        )
        
        result = validate_person_basic(person)
        assert not result.is_valid()
        assert len(result.errors) > 0
        assert any("nom de famille" in str(e).lower() for e in result.errors)
    
    def test_person_missing_first_name(self):
        """Test de personne sans prénom"""
        person = Person(
            last_name="DUPONT",
            first_name="",
            gender=Gender.MALE,
            occurrence_number=0
        )
        
        result = validate_person_basic(person)
        assert not result.is_valid()
        assert any("prénom" in str(e).lower() for e in result.errors)
    
    def test_person_birth_after_death(self):
        """Test de personne née après son décès"""
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE,
            occurrence_number=0,
            birth_date=Date(year=2000),
            death_date=Date(year=1990)
        )
        
        result = validate_person_basic(person)
        assert not result.is_valid()
        assert any("postérieure" in str(e).lower() for e in result.errors)
    
    def test_person_baptism_before_birth(self):
        """Test de baptême avant naissance"""
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE,
            occurrence_number=0,
            birth_date=Date(year=2000),
            baptism_date=Date(year=1999)
        )
        
        result = validate_person_basic(person)
        assert not result.is_valid()
        assert any("baptême" in str(e).lower() and "antérieure" in str(e).lower() 
                  for e in result.errors)
    
    def test_person_deceased_without_death_date(self):
        """Test de personne décédée sans date de décès (avertissement)"""
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE,
            occurrence_number=0,
            is_deceased=True
        )
        
        result = validate_person_basic(person)
        assert result.is_valid()  # Valide mais avec warning
        assert result.has_warnings()
    
    def test_person_death_date_without_is_deceased(self):
        """Test de date de décès sans is_deceased défini (avertissement)"""
        person = Person(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE,
            occurrence_number=0,
            death_date=Date(year=2000),
            is_deceased=None
        )
        
        result = validate_person_basic(person)
        assert result.is_valid()  # Valide mais avec warning
        assert result.has_warnings()


class TestFamilyValidation:
    """Tests de validation des familles"""
    
    def test_valid_family(self):
        """Test de validation d'une famille valide"""
        family = Family(
            family_id="FAM_001",
            husband_id="DUPONT_Jean_0",
            wife_id="MARTIN_Marie_0"
        )
        
        result = validate_family_basic(family)
        assert result.is_valid()
    
    def test_family_marriage_after_divorce(self):
        """Test de mariage après divorce"""
        family = Family(
            family_id="FAM_001",
            husband_id="DUPONT_Jean_0",
            wife_id="MARTIN_Marie_0",
            marriage_date=Date(year=2010),
            divorce_date=Date(year=2005)
        )
        
        result = validate_family_basic(family)
        assert not result.is_valid()
        assert any("mariage" in str(e).lower() and "divorce" in str(e).lower() 
                  for e in result.errors)
    
    def test_family_divorce_date_without_is_separated(self):
        """Test de date de divorce sans is_separated"""
        family = Family(
            family_id="FAM_001",
            husband_id="DUPONT_Jean_0",
            wife_id="MARTIN_Marie_0",
            divorce_date=Date(year=2005),
            is_separated=False
        )
        
        result = validate_family_basic(family)
        assert result.is_valid()  # Valide mais avec warning
        assert result.has_warnings()


class TestFamilyMembersValidation:
    """Tests de validation des membres de famille"""
    
    def test_family_members_exist(self):
        """Test que les membres de famille existent"""
        genealogy = Genealogy()
        
        # Créer les personnes
        husband = Person(last_name="DUPONT", first_name="Jean", 
                        gender=Gender.MALE, occurrence_number=0)
        wife = Person(last_name="MARTIN", first_name="Marie",
                     gender=Gender.FEMALE, occurrence_number=0)
        
        genealogy.add_person(husband)
        genealogy.add_person(wife)
        
        # Créer la famille
        family = Family(
            family_id="FAM_001",
            husband_id=husband.unique_id,
            wife_id=wife.unique_id
        )
        
        result = validate_family_members(family, genealogy)
        assert result.is_valid()
    
    def test_family_missing_husband(self):
        """Test de mari manquant"""
        genealogy = Genealogy()
        
        wife = Person(last_name="MARTIN", first_name="Marie",
                     gender=Gender.FEMALE, occurrence_number=0)
        genealogy.add_person(wife)
        
        family = Family(
            family_id="FAM_001",
            husband_id="DUPONT_Jean_0",  # N'existe pas
            wife_id=wife.unique_id
        )
        
        result = validate_family_members(family, genealogy)
        assert not result.is_valid()
        assert any("Époux" in str(e) and "non trouvé" in str(e) 
                  for e in result.errors)
    
    def test_family_missing_child(self):
        """Test d'enfant manquant"""
        from geneweb_py.core.family import Child, ChildSex
        
        genealogy = Genealogy()
        
        husband = Person(last_name="DUPONT", first_name="Jean",
                        gender=Gender.MALE, occurrence_number=0)
        genealogy.add_person(husband)
        
        family = Family(
            family_id="FAM_001",
            husband_id=husband.unique_id
        )
        
        # Ajouter un enfant qui n'existe pas
        family.children.append(Child(person_id="GHOST_Child_0", sex=ChildSex.MALE))
        
        result = validate_family_members(family, genealogy)
        assert not result.is_valid()
        assert any("Enfant" in str(e) and "non trouvé" in str(e)
                  for e in result.errors)


class TestGenealogyValidation:
    """Tests de validation de généalogie complète"""
    
    def test_valid_genealogy(self):
        """Test de validation d'une généalogie valide"""
        genealogy = Genealogy()
        
        # Créer des personnes
        jean = Person(last_name="DUPONT", first_name="Jean",
                     gender=Gender.MALE, occurrence_number=0)
        marie = Person(last_name="MARTIN", first_name="Marie",
                      gender=Gender.FEMALE, occurrence_number=0)
        
        genealogy.add_person(jean)
        genealogy.add_person(marie)
        
        # Créer une famille
        family = Family(
            family_id="FAM_001",
            husband_id=jean.unique_id,
            wife_id=marie.unique_id
        )
        genealogy.add_family(family)
        
        result = validate_genealogy_consistency(genealogy)
        assert result.is_valid()
    
    def test_genealogy_with_multiple_errors(self):
        """Test de généalogie avec plusieurs erreurs"""
        genealogy = Genealogy()
        
        # Personne avec nom manquant
        invalid_person = Person(last_name="", first_name="",
                               gender=Gender.MALE, occurrence_number=0)
        genealogy.add_person(invalid_person)
        
        # Famille avec références manquantes
        invalid_family = Family(
            family_id="FAM_001",
            husband_id="GHOST_1",
            wife_id="GHOST_2"
        )
        genealogy.add_family(invalid_family)
        
        result = validate_genealogy_consistency(genealogy)
        assert not result.is_valid()
        assert len(result.errors) >= 2  # Au moins 2 erreurs


class TestPartialObjectCreation:
    """Tests de création d'objets partiels"""
    
    def test_create_partial_person(self):
        """Test de création d'une personne partielle"""
        person = create_partial_person(
            "DUPONT",
            "Jean",
            error_message="Erreur de parsing"
        )
        
        assert person is not None
        assert not person.is_valid
        assert len(person.validation_errors) > 0
    
    def test_create_partial_family(self):
        """Test de création d'une famille partielle"""
        family = create_partial_family(
            "FAM_001",
            error_message="Famille incomplète"
        )
        
        assert family is not None
        assert not family.is_valid
        assert len(family.validation_errors) > 0


class TestGenealogyValidationIntegration:
    """Tests d'intégration de validation"""
    
    def test_genealogy_validation_errors_attribute(self):
        """Test de l'attribut validation_errors de Genealogy"""
        genealogy = Genealogy()
        
        assert genealogy.is_valid
        assert len(genealogy.validation_errors) == 0
        
        # Ajouter une erreur
        error = GeneWebValidationError("Test error")
        genealogy.add_validation_error(error)
        
        assert not genealogy.is_valid
        assert len(genealogy.validation_errors) == 1
    
    def test_genealogy_clear_validation_errors(self):
        """Test de l'effacement des erreurs de validation"""
        genealogy = Genealogy()
        
        error = GeneWebValidationError("Test error")
        genealogy.add_validation_error(error)
        
        assert not genealogy.is_valid
        
        genealogy.clear_validation_errors()
        
        assert genealogy.is_valid
        assert len(genealogy.validation_errors) == 0
    
    def test_genealogy_validation_summary(self):
        """Test du résumé de validation"""
        genealogy = Genealogy()
        
        # Généalogie valide
        assert "valide" in genealogy.get_validation_summary().lower()
        
        # Avec erreurs
        error = GeneWebValidationError("Test error", severity=ErrorSeverity.ERROR)
        genealogy.add_validation_error(error)
        
        summary = genealogy.get_validation_summary()
        assert "erreur" in summary.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

