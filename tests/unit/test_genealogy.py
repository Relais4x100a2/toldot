"""
Tests unitaires pour le modèle Genealogy

Ces tests vérifient la création et manipulation de la généalogie
et toutes ses méthodes de recherche et validation.
"""

import pytest
from geneweb_py.core.genealogy import Genealogy, GenealogyMetadata
from geneweb_py.core.person import Person, Gender, AccessLevel
from geneweb_py.core.family import Family, MarriageStatus, ChildSex
from geneweb_py.core.date import Date
from geneweb_py.core.exceptions import GeneWebValidationError


class TestGenealogyCreation:
    """Tests pour la création de généalogie"""
    
    def test_create_empty_genealogy(self):
        """Test création d'une généalogie vide"""
        genealogy = Genealogy()
        
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0
        assert isinstance(genealogy.metadata, GenealogyMetadata)
    
    def test_create_genealogy_with_metadata(self):
        """Test création avec métadonnées"""
        metadata = GenealogyMetadata(
            source_file="test.gw",
            encoding="utf-8",
            is_gwplus=True
        )
        genealogy = Genealogy(metadata=metadata)
        
        assert genealogy.metadata.source_file == "test.gw"
        assert genealogy.metadata.encoding == "utf-8"
        assert genealogy.metadata.is_gwplus is True


class TestGenealogyAddPerson:
    """Tests pour l'ajout de personnes"""
    
    def test_add_person(self):
        """Test ajout d'une personne"""
        genealogy = Genealogy()
        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            gender=Gender.MALE,
            access_level=AccessLevel.PUBLIC
        )
        
        genealogy.add_person(person)
        
        assert len(genealogy.persons) == 1
        assert "CORNO_Joseph_0" in genealogy.persons
        assert genealogy.persons["CORNO_Joseph_0"] == person
    
    def test_add_duplicate_person(self):
        """Test ajout d'une personne déjà existante"""
        genealogy = Genealogy()
        person1 = Person(last_name="CORNO", first_name="Joseph")
        person2 = Person(last_name="CORNO", first_name="Joseph")  # Même ID
        
        genealogy.add_person(person1)
        
        with pytest.raises(GeneWebValidationError) as exc_info:
            genealogy.add_person(person2)
        
        assert "déjà présente" in str(exc_info.value)


class TestGenealogyAddFamily:
    """Tests pour l'ajout de familles"""
    
    def test_add_family(self):
        """Test ajout d'une famille"""
        genealogy = Genealogy()
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        
        genealogy.add_family(family)
        
        assert len(genealogy.families) == 1
        assert "FAM001" in genealogy.families
        assert genealogy.families["FAM001"] == family
    
    def test_add_duplicate_family(self):
        """Test ajout d'une famille déjà existante"""
        genealogy = Genealogy()
        family1 = Family(family_id="FAM001", husband_id="CORNO_Joseph_0")
        family2 = Family(family_id="FAM001", husband_id="CORNO_Pierre_0")
        
        genealogy.add_family(family1)
        
        with pytest.raises(GeneWebValidationError) as exc_info:
            genealogy.add_family(family2)
        
        assert "déjà présente" in str(exc_info.value)


class TestGenealogyFindMethods:
    """Tests pour les méthodes de recherche"""
    
    def test_find_person(self):
        """Test recherche de personne par nom"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        found = genealogy.find_person("CORNO", "Joseph")
        assert found == person
        
        not_found = genealogy.find_person("DUPONT", "Pierre")
        assert not_found is None
    
    def test_find_person_by_id(self):
        """Test recherche de personne par ID"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        found = genealogy.find_person_by_id("CORNO_Joseph_0")
        assert found == person
        
        not_found = genealogy.find_person_by_id("DUPONT_Pierre_0")
        assert not_found is None
    
    def test_find_family(self):
        """Test recherche de famille"""
        genealogy = Genealogy()
        family = Family(family_id="FAM001", husband_id="CORNO_Joseph_0")
        genealogy.add_family(family)
        
        found = genealogy.find_family("FAM001")
        assert found == family
        
        not_found = genealogy.find_family("FAM002")
        assert not_found is None
    
    def test_get_families_for_person(self):
        """Test récupération des familles d'une personne"""
        genealogy = Genealogy()
        
        # Créer une personne
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        # Créer une famille où elle est parent
        family1 = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        genealogy.add_family(family1)
        
        # Créer une famille où elle est enfant
        parent = Person(last_name="PARENT", first_name="Pierre")
        genealogy.add_person(parent)
        family2 = Family(
            family_id="FAM002",
            husband_id="PARENT_Pierre_0"
        )
        family2.add_child("CORNO_Joseph_0")
        genealogy.add_family(family2)
        
        families = genealogy.get_families_for_person("CORNO_Joseph_0")
        assert len(families) == 2
        family_ids = {f.family_id for f in families}
        assert family_ids == {"FAM001", "FAM002"}


class TestGenealogyRelations:
    """Tests pour les relations familiales"""
    
    def test_get_children(self):
        """Test récupération des enfants"""
        genealogy = Genealogy()
        
        # Créer les parents
        father = Person(last_name="CORNO", first_name="Joseph")
        mother = Person(last_name="THOMAS", first_name="Marie")
        genealogy.add_person(father)
        genealogy.add_person(mother)
        
        # Créer les enfants
        child1 = Person(last_name="CORNO", first_name="Jean")
        child2 = Person(last_name="CORNO", first_name="Sophie")
        genealogy.add_person(child1)
        genealogy.add_person(child2)
        
        # Créer la famille
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("CORNO_Jean_0", ChildSex.MALE)
        family.add_child("CORNO_Sophie_0", ChildSex.FEMALE)
        genealogy.add_family(family)
        
        children = genealogy.get_children("CORNO_Joseph_0")
        assert len(children) == 2
        child_names = {child.full_name for child in children}
        assert child_names == {"CORNO Jean", "CORNO Sophie"}
    
    def test_get_parents(self):
        """Test récupération des parents"""
        genealogy = Genealogy()
        
        # Créer les parents
        father = Person(last_name="CORNO", first_name="Joseph")
        mother = Person(last_name="THOMAS", first_name="Marie")
        genealogy.add_person(father)
        genealogy.add_person(mother)
        
        # Créer l'enfant
        child = Person(last_name="CORNO", first_name="Jean")
        genealogy.add_person(child)
        
        # Créer la famille
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("CORNO_Jean_0")
        genealogy.add_family(family)
        
        parents = genealogy.get_parents("CORNO_Jean_0")
        assert len(parents) == 2
        parent_names = {parent.full_name for parent in parents}
        assert parent_names == {"CORNO Joseph", "THOMAS Marie"}
    
    def test_get_siblings(self):
        """Test récupération des frères et sœurs"""
        genealogy = Genealogy()
        
        # Créer les parents
        father = Person(last_name="CORNO", first_name="Joseph")
        mother = Person(last_name="THOMAS", first_name="Marie")
        genealogy.add_person(father)
        genealogy.add_person(mother)
        
        # Créer les enfants
        child1 = Person(last_name="CORNO", first_name="Jean")
        child2 = Person(last_name="CORNO", first_name="Sophie")
        child3 = Person(last_name="CORNO", first_name="Paul")
        genealogy.add_person(child1)
        genealogy.add_person(child2)
        genealogy.add_person(child3)
        
        # Créer la famille
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("CORNO_Jean_0")
        family.add_child("CORNO_Sophie_0")
        family.add_child("CORNO_Paul_0")
        genealogy.add_family(family)
        
        siblings = genealogy.get_siblings("CORNO_Jean_0")
        assert len(siblings) == 2
        sibling_names = {sibling.full_name for sibling in siblings}
        assert sibling_names == {"CORNO Sophie", "CORNO Paul"}
    
    def test_get_spouses(self):
        """Test récupération des conjoints"""
        genealogy = Genealogy()
        
        # Créer les personnes
        husband = Person(last_name="CORNO", first_name="Joseph")
        wife1 = Person(last_name="THOMAS", first_name="Marie")
        wife2 = Person(last_name="DUPONT", first_name="Claire")
        genealogy.add_person(husband)
        genealogy.add_person(wife1)
        genealogy.add_person(wife2)
        
        # Créer les familles
        family1 = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0",
            marriage_status=MarriageStatus.DIVORCED
        )
        family2 = Family(
            family_id="FAM002",
            husband_id="CORNO_Joseph_0",
            wife_id="DUPONT_Claire_0"
        )
        genealogy.add_family(family1)
        genealogy.add_family(family2)
        
        spouses = genealogy.get_spouses("CORNO_Joseph_0")
        assert len(spouses) == 2
        spouse_names = {spouse.full_name for spouse in spouses}
        assert spouse_names == {"THOMAS Marie", "DUPONT Claire"}


class TestGenealogyValidation:
    """Tests pour la validation de cohérence"""
    
    def test_validate_consistency_valid(self):
        """Test validation avec données cohérentes"""
        genealogy = Genealogy()
        
        # Créer les personnes
        father = Person(last_name="CORNO", first_name="Joseph")
        mother = Person(last_name="THOMAS", first_name="Marie")
        child = Person(last_name="CORNO", first_name="Jean")
        genealogy.add_person(father)
        genealogy.add_person(mother)
        genealogy.add_person(child)
        
        # Créer la famille
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("CORNO_Jean_0")
        genealogy.add_family(family)
        
        errors = genealogy.validate_consistency()
        assert len(errors) == 0
    
    def test_validate_consistency_missing_husband(self):
        """Test validation avec époux manquant"""
        genealogy = Genealogy()
        
        # Créer seulement la mère
        mother = Person(last_name="THOMAS", first_name="Marie")
        genealogy.add_person(mother)
        
        # Créer une famille avec époux inexistant
        family = Family(
            family_id="FAM001",
            husband_id="INEXISTANT_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        genealogy.add_family(family)
        
        errors = genealogy.validate_consistency()
        assert len(errors) == 1
        assert "Époux 'INEXISTANT_Joseph_0'" in str(errors[0])
    
    def test_validate_consistency_missing_child(self):
        """Test validation avec enfant manquant"""
        genealogy = Genealogy()
        
        # Créer les parents
        father = Person(last_name="CORNO", first_name="Joseph")
        mother = Person(last_name="THOMAS", first_name="Marie")
        genealogy.add_person(father)
        genealogy.add_person(mother)
        
        # Créer une famille avec enfant inexistant
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("INEXISTANT_Jean_0")
        genealogy.add_family(family)
        
        errors = genealogy.validate_consistency()
        assert len(errors) == 1
        assert "Enfant 'INEXISTANT_Jean_0'" in str(errors[0])


class TestGenealogyStatistics:
    """Tests pour les statistiques"""
    
    def test_get_statistics_empty(self):
        """Test statistiques d'une généalogie vide"""
        genealogy = Genealogy()
        stats = genealogy.get_statistics()
        
        assert stats['total_persons'] == 0
        assert stats['total_families'] == 0
        assert stats['living_persons'] == 0
        assert stats['deceased_persons'] == 0
        assert stats['male_persons'] == 0
        assert stats['female_persons'] == 0
    
    def test_get_statistics_with_data(self):
        """Test statistiques avec données"""
        genealogy = Genealogy()
        
        # Créer des personnes avec différents statuts
        living_male = Person(
            last_name="CORNO", first_name="Joseph", 
            gender=Gender.MALE  # Pas de date de décès = vivant
        )
        deceased_female = Person(
            last_name="THOMAS", first_name="Marie", 
            gender=Gender.FEMALE, death_date=Date.parse("10/01/2020")
        )
        unknown_gender = Person(
            last_name="DUPONT", first_name="Pierre",
            gender=Gender.UNKNOWN
        )
        
        genealogy.add_person(living_male)
        genealogy.add_person(deceased_female)
        genealogy.add_person(unknown_gender)
        
        # Créer une famille
        family = Family(family_id="FAM001", husband_id="CORNO_Joseph_0")
        genealogy.add_family(family)
        
        stats = genealogy.get_statistics()
        
        assert stats['total_persons'] == 3
        assert stats['total_families'] == 1
        assert stats['male_persons'] == 1
        assert stats['female_persons'] == 1
        assert stats['unknown_gender_persons'] == 1
        assert stats['living_persons'] == 2  # Joseph (pas de date de décès) + Pierre
        assert stats['deceased_persons'] == 1  # Marie
        assert stats['persons_with_birth_date'] == 0
        assert stats['persons_with_death_date'] == 1
    
    def test_statistics_cache(self):
        """Test mise en cache des statistiques"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        # Premier appel
        stats1 = genealogy.get_statistics()
        assert stats1['total_persons'] == 1
        
        # Deuxième appel (doit utiliser le cache)
        stats2 = genealogy.get_statistics()
        assert stats2['total_persons'] == 1
        assert stats1 is not stats2  # Copie, pas référence
        
        # Ajout d'une personne (invalide le cache)
        person2 = Person(last_name="DUPONT", first_name="Pierre")
        genealogy.add_person(person2)
        
        stats3 = genealogy.get_statistics()
        assert stats3['total_persons'] == 2


class TestGenealogyCrossReferences:
    """Tests pour les références croisées"""
    
    def test_update_cross_references(self):
        """Test mise à jour des références croisées"""
        genealogy = Genealogy()
        
        # Créer les personnes
        father = Person(last_name="CORNO", first_name="Joseph")
        mother = Person(last_name="THOMAS", first_name="Marie")
        child = Person(last_name="CORNO", first_name="Jean")
        genealogy.add_person(father)
        genealogy.add_person(mother)
        genealogy.add_person(child)
        
        # Créer la famille
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("CORNO_Jean_0")
        genealogy.add_family(family)
        
        # Forcer la mise à jour des références croisées
        genealogy._update_cross_references()
        
        # Vérifier les références
        father = genealogy.find_person("CORNO", "Joseph")
        mother = genealogy.find_person("THOMAS", "Marie")
        child = genealogy.find_person("CORNO", "Jean")
        
        assert "FAM001" in father.families_as_spouse
        assert "FAM001" in mother.families_as_spouse
        assert "FAM001" in child.families_as_child


class TestGenealogySerialization:
    """Tests pour la sérialisation"""
    
    def test_to_dict(self):
        """Test conversion en dictionnaire"""
        genealogy = Genealogy()
        
        # Ajouter des métadonnées
        genealogy.metadata.source_file = "test.gw"
        genealogy.metadata.encoding = "utf-8"
        
        # Ajouter une personne
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        # Ajouter une famille
        family = Family(family_id="FAM001", husband_id="CORNO_Joseph_0")
        genealogy.add_family(family)
        
        data = genealogy.to_dict()
        
        assert 'metadata' in data
        assert 'persons' in data
        assert 'families' in data
        assert 'statistics' in data
        
        assert data['metadata']['source_file'] == "test.gw"
        assert len(data['persons']) == 1
        assert len(data['families']) == 1
        assert data['statistics']['total_persons'] == 1


class TestGenealogyStringRepresentation:
    """Tests pour les représentations string"""
    
    def test_str_representation(self):
        """Test représentation string"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        str_repr = str(genealogy)
        assert "Genealogy(" in str_repr
        assert "personnes" in str_repr
        assert "familles" in str_repr
    
    def test_repr_representation(self):
        """Test représentation pour debug"""
        genealogy = Genealogy()
        person = Person(last_name="CORNO", first_name="Joseph")
        genealogy.add_person(person)
        
        repr_str = repr(genealogy)
        assert "Genealogy(persons=1, families=0)" == repr_str
    
    def test_len_method(self):
        """Test méthode __len__"""
        genealogy = Genealogy()
        assert len(genealogy) == 0
        
        person1 = Person(last_name="CORNO", first_name="Joseph")
        person2 = Person(last_name="DUPONT", first_name="Pierre")
        genealogy.add_person(person1)
        genealogy.add_person(person2)
        
        assert len(genealogy) == 2


class TestGenealogyMetadata:
    """Tests pour les métadonnées"""
    
    def test_metadata_creation(self):
        """Test création des métadonnées"""
        metadata = GenealogyMetadata(
            source_file="test.gw",
            encoding="iso-8859-1",
            is_gwplus=True,
            database_notes=["Note 1", "Note 2"],
            extended_pages={"page1": "content1"},
            wizard_notes={"wizard1": {"key": "value"}}
        )
        
        assert metadata.source_file == "test.gw"
        assert metadata.encoding == "iso-8859-1"
        assert metadata.is_gwplus is True
        assert len(metadata.database_notes) == 2
        assert "page1" in metadata.extended_pages
        assert "wizard1" in metadata.wizard_notes
    
    def test_metadata_defaults(self):
        """Test valeurs par défaut des métadonnées"""
        metadata = GenealogyMetadata()
        
        assert metadata.source_file is None
        assert metadata.encoding == "iso-8859-1"
        assert metadata.is_gwplus is False
        assert metadata.created_date is None
        assert metadata.modified_date is None
        assert metadata.geneweb_version is None
        assert len(metadata.database_notes) == 0
        assert len(metadata.extended_pages) == 0
        assert len(metadata.wizard_notes) == 0
