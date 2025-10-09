"""
Tests unitaires pour le modèle Family

Ces tests vérifient la création et manipulation des familles
dans le format GeneWeb.
"""

import pytest
from geneweb_py.core.family import Family, Child, MarriageStatus, ChildSex
from geneweb_py.core.date import Date


class TestFamilyCreation:
    """Tests pour la création de familles"""
    
    def test_create_simple_family(self):
        """Test création d'une famille simple"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        assert family.family_id == "FAM001"
        assert family.husband_id == "CORNO_Joseph_0"
        assert family.wife_id == "THOMAS_Marie_0"
        assert family.marriage_status == MarriageStatus.MARRIED
    
    def test_create_family_with_marriage_date(self):
        """Test création avec date de mariage"""
        marriage_date = Date.parse("10/08/2015")
        
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            marriage_date=marriage_date
        )
        
        assert family.marriage_date == marriage_date
    
    def test_create_family_with_children(self):
        """Test création avec enfants"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_child("CORNO_Jean_0", ChildSex.MALE)
        family.add_child("CORNO_Sophie_0", ChildSex.FEMALE)
        
        assert len(family.children) == 2
        assert family.child_ids == ["CORNO_Jean_0", "CORNO_Sophie_0"]
    
    def test_create_single_parent_family(self):
        """Test création famille monoparentale"""
        family = Family(
            family_id="FAM002",
            husband_id="CORNO_Joseph_0"
        )
        
        assert family.husband_id == "CORNO_Joseph_0"
        assert family.wife_id is None


class TestFamilyValidation:
    """Tests pour la validation des familles"""
    
    def test_family_without_spouses(self):
        """Test famille sans époux (doit générer une erreur de validation)"""
        family = Family(family_id="FAM001")
        # Vérifier qu'une erreur de validation a été ajoutée
        assert len(family.validation_errors) > 0
        assert any("au moins un époux" in str(err) for err in family.validation_errors)
    
    def test_invalid_marriage_divorce_dates(self):
        """Test dates incohérentes (mariage > divorce)"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            marriage_date=Date.parse("10/08/2015"),
            divorce_date=Date.parse("10/08/2010")  # Avant le mariage
        )
        # Vérifier qu'une erreur de validation a été ajoutée
        assert len(family.validation_errors) > 0
        assert any("postérieure" in str(err) for err in family.validation_errors)


class TestFamilyProperties:
    """Tests pour les propriétés des familles"""
    
    def test_spouse_ids(self):
        """Test liste des IDs d'époux"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        assert family.spouse_ids == ["CORNO_Joseph_0", "THOMAS_Marie_0"]
    
    def test_all_member_ids(self):
        """Test tous les membres de la famille"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_child("CORNO_Jean_0")
        
        expected = ["CORNO_Joseph_0", "THOMAS_Marie_0", "CORNO_Jean_0"]
        assert family.all_member_ids == expected
    
    def test_is_married(self):
        """Test statut marié"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            marriage_status=MarriageStatus.MARRIED
        )
        
        assert family.is_married is True
    
    def test_is_not_married(self):
        """Test statut non marié"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            marriage_status=MarriageStatus.NOT_MARRIED
        )
        
        assert family.is_married is False
    
    def test_is_divorced(self):
        """Test statut divorcé"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            divorce_date=Date.parse("10/01/2020")
        )
        
        assert family.is_divorced is True


class TestFamilyMethods:
    """Tests pour les méthodes des familles"""
    
    def test_add_child(self):
        """Test ajout d'enfant"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_child("CORNO_Jean_0", ChildSex.MALE)
        
        assert len(family.children) == 1
        child = family.children[0]
        assert child.person_id == "CORNO_Jean_0"
        assert child.sex == ChildSex.MALE
    
    def test_remove_child(self):
        """Test suppression d'enfant"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_child("CORNO_Jean_0")
        family.add_child("CORNO_Sophie_0")
        
        # Supprimer le premier enfant
        removed = family.remove_child("CORNO_Jean_0")
        
        assert removed is True
        assert len(family.children) == 1
        assert family.children[0].person_id == "CORNO_Sophie_0"
    
    def test_remove_nonexistent_child(self):
        """Test suppression d'enfant inexistant"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        removed = family.remove_child("INEXISTANT_0")
        assert removed is False
    
    def test_add_witness(self):
        """Test ajout de témoin"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_witness("TEMOIN_Pierre_0", "m")
        
        assert len(family.witnesses) == 1
        witness = family.witnesses[0]
        assert witness["person_id"] == "TEMOIN_Pierre_0"
        assert witness["type"] == "m"
    
    def test_add_comment(self):
        """Test ajout de commentaire"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_comment("Mariage célébré à Paris")
        
        assert len(family.comments) == 1
        assert family.comments[0] == "Mariage célébré à Paris"


class TestFamilyRelations:
    """Tests pour les relations familiales"""
    
    def test_spouse_method(self):
        """Test méthode spouse"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        # Le mari trouve sa femme
        spouse = family.spouse("CORNO_Joseph_0")
        assert spouse == "THOMAS_Marie_0"
        
        # La femme trouve son mari
        spouse = family.spouse("THOMAS_Marie_0")
        assert spouse == "CORNO_Joseph_0"
        
        # Personne non membre
        spouse = family.spouse("INCONNU_0")
        assert spouse is None
    
    def test_is_parent(self):
        """Test vérification parent"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        assert family.is_parent("CORNO_Joseph_0") is True
        assert family.is_parent("THOMAS_Marie_0") is True
        assert family.is_parent("INCONNU_0") is False
    
    def test_is_child(self):
        """Test vérification enfant"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_child("CORNO_Jean_0")
        
        assert family.is_child("CORNO_Jean_0") is True
        assert family.is_child("CORNO_Joseph_0") is False
    
    def test_is_member(self):
        """Test vérification membre"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        family.add_child("CORNO_Jean_0")
        
        assert family.is_member("CORNO_Joseph_0") is True  # Parent
        assert family.is_member("CORNO_Jean_0") is True    # Enfant
        assert family.is_member("INCONNU_0") is False      # Non membre


class TestChild:
    """Tests pour la classe Child"""
    
    def test_child_creation(self):
        """Test création d'enfant"""
        child = Child(
            person_id="CORNO_Jean_0",
            sex=ChildSex.MALE,
            last_name="CORNO"
        )
        
        assert child.person_id == "CORNO_Jean_0"
        assert child.sex == ChildSex.MALE
        assert child.last_name == "CORNO"
    
    def test_child_string_representation(self):
        """Test représentation string de l'enfant"""
        child = Child(
            person_id="CORNO_Jean_0",
            sex=ChildSex.MALE
        )
        
        expected = "-h CORNO_Jean_0"
        assert str(child) == expected
        
        child_unknown = Child(person_id="CORNO_Jean_0")
        expected_unknown = "- CORNO_Jean_0"
        assert str(child_unknown) == expected_unknown


class TestFamilySerialization:
    """Tests pour la sérialisation des familles"""
    
    def test_to_dict(self):
        """Test conversion en dictionnaire"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            marriage_date=Date.parse("10/08/2015"),
            marriage_place="Paris"
        )
        
        family.add_child("CORNO_Jean_0", ChildSex.MALE)
        
        data = family.to_dict()
        
        assert data["family_id"] == "FAM001"
        assert data["husband_id"] == "CORNO_Joseph_0"
        assert data["wife_id"] == "THOMAS_Marie_0"
        assert data["marriage_place"] == "Paris"
        assert len(data["children"]) == 1
        assert data["children"][0]["person_id"] == "CORNO_Jean_0"
