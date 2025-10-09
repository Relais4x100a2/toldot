"""
Tests supplémentaires pour améliorer la couverture de validation.py
"""

import pytest
from geneweb_py.core.validation import (
    ValidationContext,
    validate_person_basic,
    validate_family_basic,
    validate_person_relationships,
    validate_family_members,
    validate_genealogy_consistency,
    validate_bidirectional_references
)
from geneweb_py.core.person import Person
from geneweb_py.core.family import Family
from geneweb_py.core.genealogy import Genealogy
from geneweb_py.core.exceptions import GeneWebValidationError


class TestValidationContextAddError:
    """Tests pour add_error avec différents types d'erreurs"""
    
    def test_add_error_with_non_geneweb_error(self):
        """Test add_error avec une erreur non GeneWebError"""
        context = ValidationContext()
        
        # Ajouter une erreur standard (non GeneWebValidationError)
        context.add_error(ValueError("Erreur de valeur"))
        
        assert context.has_errors()
        errors = context.get_errors()
        assert len(errors) == 1
        # L'erreur devrait être convertie en GeneWebValidationError
        assert any("Erreur de valeur" in str(e) for e in errors)


class TestValidatePersonRelationships:
    """Tests pour validate_person_relationships"""
    
    def test_validate_person_family_as_spouse_not_found(self):
        """Test validation avec famille référencée comme conjoint inexistante"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        person.families_as_spouse.append("FAM_INEXISTANTE")
        
        genealogy.add_person(person)
        
        context = ValidationContext()
        validate_person_relationships(person, genealogy, context)
        
        assert context.has_errors()
        assert any("FAM_INEXISTANTE" in str(e) for e in context.get_errors())
        assert any("conjoint" in str(e).lower() for e in context.get_errors())
    
    def test_validate_person_family_as_child_not_found(self):
        """Test validation avec famille référencée comme enfant inexistante"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        person.families_as_child.append("FAM_PARENTS_INEXISTANTE")
        
        genealogy.add_person(person)
        
        context = ValidationContext()
        validate_person_relationships(person, genealogy, context)
        
        assert context.has_errors()
        assert any("FAM_PARENTS_INEXISTANTE" in str(e) for e in context.get_errors())
        assert any("enfant" in str(e).lower() for e in context.get_errors())
    
    def test_validate_person_with_default_context(self):
        """Test validate_person_relationships sans context (None par défaut)"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        person.families_as_spouse.append("FAM_INEXISTANTE")
        
        genealogy.add_person(person)
        
        # Sans passer de context (il sera créé par défaut)
        result = validate_person_relationships(person, genealogy, context=None)
        
        assert result.has_errors()


class TestValidateFamilyBasic:
    """Tests pour validate_family_basic"""
    
    def test_validate_family_without_parents_or_children(self):
        """Test validation d'une famille sans parents ni enfants"""
        family = Family(family_id="FAM001")
        # Pas de husband_id, pas de wife_id, pas d'enfants
        
        context = ValidationContext()
        validate_family_basic(family, context)
        
        assert context.has_errors()
        assert any("au moins un parent ou un enfant" in str(e).lower() for e in context.get_errors())


class TestValidateBidirectionalReferences:
    """Tests pour validate_bidirectional_references"""
    
    def test_validate_bidirectional_references_with_default_context(self):
        """Test validate_bidirectional_references sans context (None par défaut)"""
        genealogy = Genealogy()
        
        # Créer une famille avec un mari
        family = Family(family_id="FAM001", husband_id="CORNO_Joseph_0")
        genealogy.add_family(family)
        
        # Créer la personne mais sans référence à la famille
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        # Appeler sans context (il sera créé par défaut)
        result = validate_bidirectional_references(genealogy, context=None)
        
        # Devrait avoir des avertissements car la personne ne référence pas la famille
        assert result.has_warnings() or result.has_errors()
    
    def test_validate_bidirectional_references_child_not_referencing_family(self):
        """Test validation enfant ne référençant pas sa famille"""
        genealogy = Genealogy()
        
        # Créer une famille avec un enfant
        family = Family(family_id="FAM001", husband_id="CORNO_Joseph_0")
        from geneweb_py.core.family import Child, ChildSex
        family.children.append(Child(person_id="CORNO_Jean_0", sex=ChildSex.MALE))
        genealogy.add_family(family)
        
        # Créer les personnes
        husband = Person(last_name="CORNO", first_name="Joseph")
        husband.families_as_spouse.append("FAM001")
        genealogy.add_person(husband)
        
        child = Person(last_name="CORNO", first_name="Jean")
        # L'enfant ne référence PAS la famille dans families_as_child
        genealogy.add_person(child)
        
        context = ValidationContext()
        validate_bidirectional_references(genealogy, context)
        
        # Devrait avoir un avertissement
        assert context.error_collector.has_warnings()
        warnings = context.error_collector.get_warnings()
        assert any("ne référence pas la famille" in str(w).lower() for w in warnings)


class TestValidateGenealogyConsistency:
    """Tests pour validation complète de la généalogie"""
    
    def test_validate_genealogy_consistency_with_all_issues(self):
        """Test validation avec plusieurs types d'erreurs"""
        genealogy = Genealogy()
        
        # Personne avec famille inexistante
        person1 = Person(last_name="CORNO", first_name="Joseph")
        person1.families_as_spouse.append("FAM_INEXISTANTE")
        genealogy.add_person(person1)
        
        # Famille vide
        family1 = Family(family_id="FAM001")
        genealogy.add_family(family1)
        
        # Famille avec références manquantes
        family2 = Family(family_id="FAM002", husband_id="CORNO_Jean_0")
        genealogy.add_family(family2)
        
        result = validate_genealogy_consistency(genealogy)
        
        # Devrait avoir plusieurs erreurs
        assert result.has_errors()
        assert len(result.errors) >= 2

