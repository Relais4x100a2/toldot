"""
Tests pour améliorer la couverture du service de généalogie
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.models import (
    Person, Family, PersonalEvent, FamilyEvent, Gender, AccessLevel, 
    MarriageStatus, EventType, FamilyEventType
)
from geneweb_py.api.models.person import PersonCreateSchema, PersonUpdateSchema, PersonSearchSchema
from geneweb_py.api.models.family import FamilyCreateSchema, FamilyUpdateSchema, FamilySearchSchema
from geneweb_py.api.models.event import PersonalEventCreateSchema, FamilyEventCreateSchema, EventUpdateSchema


class MockGenealogyServiceInitialization:
    """Tests pour l'initialisation du service"""
    
    def test_service_initialization(self):
        """Test initialisation du service"""
        service = GenealogyService()
        assert service is not None
        assert service._genealogy is not None
        assert service._parser is not None
    
    def test_service_initialization_with_mock_file(self):
        """Test initialisation avec fichier de test"""
        with patch('pathlib.Path.exists', return_value=True):
            with patch.object(GenealogyService, '_parser') as mock_parser:
                mock_genealogy = MagicMock()
                mock_parser.parse_file.return_value = mock_genealogy
                
                service = GenealogyService()
                assert service._genealogy == mock_genealogy
    
    def test_service_initialization_without_test_file(self):
        """Test initialisation sans fichier de test"""
        with patch('pathlib.Path.exists', return_value=False):
            service = GenealogyService()
            assert service._genealogy is not None


class MockGenealogyServiceFileOperations:
    """Tests pour les opérations de fichiers"""
    
    def test_load_from_file_success(self):
        """Test chargement réussi d'un fichier"""
        service = GenealogyService()
        mock_genealogy = MagicMock()
        
        with patch.object(service._parser, 'parse_file', return_value=mock_genealogy):
            result = service.load_from_file("test.gw")
            assert result == mock_genealogy
            assert service._genealogy == mock_genealogy
    
    def test_load_from_file_error(self):
        """Test chargement avec erreur"""
        service = GenealogyService()
        
        with patch.object(service._parser, 'parse_file', side_effect=Exception("Erreur de parsing")):
            with pytest.raises(Exception):
                service.load_from_file("invalid.gw")
    
    def test_create_empty(self):
        """Test création d'une généalogie vide"""
        service = GenealogyService()
        result = service.create_empty()
        assert result is not None
        assert service._genealogy == result
    
    def test_genealogy_property(self):
        """Test propriété genealogy"""
        service = GenealogyService()
        result = service.genealogy
        assert result is not None
        assert result == service._genealogy


class MockGenealogyServicePersonOperations:
    """Tests pour les opérations sur les personnes"""
    
    def test_create_person_success(self):
        """Test création réussie d'une personne"""
        service = GenealogyService()
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        
        result = service.create_person(person_data)
        assert result is not None
        assert result.last_name == "DUPONT"
        assert result.first_name == "Jean"
        assert result.gender == Gender.MALE
        assert result.unique_id in service._genealogy.persons
    
    def test_create_person_with_optional_fields(self):
        """Test création d'une personne avec champs optionnels"""
        service = GenealogyService()
        person_data = PersonCreateSchema(
            surname="MARTIN",
            first_name="Marie",
            sex=Gender.FEMALE,
            birth_date="01/01/1990",
            birth_place="Paris",
            death_date="31/12/2020",
            death_place="Lyon",
            access_level=AccessLevel.PRIVATE
        )
        
        result = service.create_person(person_data)
        assert result is not None
        assert result.last_name == "MARTIN"
        assert result.first_name == "Marie"
        assert result.gender == Gender.FEMALE
        assert result.access_level == AccessLevel.PRIVATE
    
    def test_get_person_existing(self):
        """Test récupération d'une personne existante"""
        service = GenealogyService()
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        created_person = service.create_person(person_data)
        
        result = service.get_person(created_person.unique_id)
        assert result is not None
        assert result.unique_id == created_person.unique_id
        assert result.last_name == "DUPONT"
    
    def test_get_person_nonexistent(self):
        """Test récupération d'une personne inexistante"""
        service = GenealogyService()
        result = service.get_person("nonexistent_id")
        assert result is None
    
    def test_update_person_success(self):
        """Test mise à jour réussie d'une personne"""
        service = GenealogyService()
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        created_person = service.create_person(person_data)
        
        update_data = PersonUpdateSchema(
            first_name="Jean-Pierre",
            birth_date="01/01/1985"
        )
        
        result = service.update_person(created_person.unique_id, update_data)
        assert result is not None
        assert result.first_name == "Jean-Pierre"
        assert result.birth_date is not None
    
    def test_update_person_nonexistent(self):
        """Test mise à jour d'une personne inexistante"""
        service = GenealogyService()
        update_data = PersonUpdateSchema(first_name="Jean")
        
        result = service.update_person("nonexistent_id", update_data)
        assert result is None
    
    def test_delete_person_success(self):
        """Test suppression réussie d'une personne"""
        service = GenealogyService()
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        created_person = service.create_person(person_data)
        
        result = service.delete_person(created_person.unique_id)
        assert result is True
        assert created_person.unique_id not in service._genealogy.persons
    
    def test_delete_person_nonexistent(self):
        """Test suppression d'une personne inexistante"""
        service = GenealogyService()
        result = service.delete_person("nonexistent_id")
        assert result is False
    
    def test_search_persons_by_name(self):
        """Test recherche de personnes par nom"""
        service = GenealogyService()
        
        # Créer quelques personnes
        person1_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person2_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Marie",
            sex=Gender.FEMALE
        )
        person3_data = PersonCreateSchema(
            surname="MARTIN",
            first_name="Pierre",
            sex=Gender.MALE
        )
        
        service.create_person(person1_data)
        service.create_person(person2_data)
        service.create_person(person3_data)
        
        # Rechercher par nom de famille
        search_params = PersonSearchSchema(surname="DUPONT")
        results, total = service.search_persons(search_params)
        
        assert total == 2
        assert len(results) == 2
        assert all(person.last_name == "DUPONT" for person in results)
    
    def test_search_persons_by_gender(self):
        """Test recherche de personnes par genre"""
        service = GenealogyService()
        
        # Créer quelques personnes
        person1_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person2_data = PersonCreateSchema(
            surname="MARTIN",
            first_name="Marie",
            sex=Gender.FEMALE
        )
        
        service.create_person(person1_data)
        service.create_person(person2_data)
        
        # Rechercher par genre
        search_params = PersonSearchSchema(sex=Gender.MALE)
        results, total = service.search_persons(search_params)
        
        assert total == 1
        assert len(results) == 1
        assert results[0].gender == Gender.MALE
    
    def test_search_persons_with_pagination(self):
        """Test recherche de personnes avec pagination"""
        service = GenealogyService()
        
        # Créer plusieurs personnes
        for i in range(10):
            person_data = PersonCreateSchema(
                surname="DUPONT",
                first_name=f"Person{i}",
                sex=Gender.MALE
            )
            service.create_person(person_data)
        
        # Rechercher avec pagination
        search_params = PersonSearchSchema(last_name="DUPONT", page=1, page_size=5)
        results, total = service.search_persons(search_params)
        
        assert total == 10
        assert len(results) == 5


class MockGenealogyServiceFamilyOperations:
    """Tests pour les opérations sur les familles"""
    
    def test_create_family_success(self):
        """Test création réussie d'une famille"""
        service = GenealogyService()
        
        # Créer les époux
        husband_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband = service.create_person(husband_data)
        wife = service.create_person(wife_data)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.id,
            wife_id=wife.id,
            marriage_date="01/01/2010",
            marriage_place="Paris"
        )
        
        result = service.create_family(family_data)
        assert result is not None
        assert result.husband_id == husband.id
        assert result.wife_id == wife.id
        assert result.id in service._genealogy.families
    
    def test_create_family_with_children(self):
        """Test création d'une famille avec enfants"""
        service = GenealogyService()
        
        # Créer les époux
        husband_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband = service.create_person(husband_data)
        wife = service.create_person(wife_data)
        
        # Créer un enfant
        child_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Pierre",
            gender=Gender.MALE
        )
        child = service.create_person(child_data)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.id,
            wife_id=wife.id,
            children_ids=[child.id]
        )
        
        result = service.create_family(family_data)
        assert result is not None
        assert child.id in result.children_ids
    
    def test_get_family_existing(self):
        """Test récupération d'une famille existante"""
        service = GenealogyService()
        
        # Créer une famille
        husband_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband = service.create_person(husband_data)
        wife = service.create_person(wife_data)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.id,
            wife_id=wife.id
        )
        created_family = service.create_family(family_data)
        
        result = service.get_family(created_family.id)
        assert result is not None
        assert result.id == created_family.id
    
    def test_get_family_nonexistent(self):
        """Test récupération d'une famille inexistante"""
        service = GenealogyService()
        result = service.get_family("nonexistent_id")
        assert result is None
    
    def test_update_family_success(self):
        """Test mise à jour réussie d'une famille"""
        service = GenealogyService()
        
        # Créer une famille
        husband_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband = service.create_person(husband_data)
        wife = service.create_person(wife_data)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.id,
            wife_id=wife.id
        )
        created_family = service.create_family(family_data)
        
        update_data = FamilyUpdateSchema(
            marriage_date="01/01/2015",
            marriage_place="Lyon"
        )
        
        result = service.update_family(created_family.id, update_data)
        assert result is not None
        assert result.marriage_date is not None
    
    def test_update_family_nonexistent(self):
        """Test mise à jour d'une famille inexistante"""
        service = GenealogyService()
        update_data = FamilyUpdateSchema(marriage_date="01/01/2015")
        
        result = service.update_family("nonexistent_id", update_data)
        assert result is None
    
    def test_delete_family_success(self):
        """Test suppression réussie d'une famille"""
        service = GenealogyService()
        
        # Créer une famille
        husband_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband = service.create_person(husband_data)
        wife = service.create_person(wife_data)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.id,
            wife_id=wife.id
        )
        created_family = service.create_family(family_data)
        
        result = service.delete_family(created_family.id)
        assert result is True
        assert created_family.id not in service._genealogy.families
    
    def test_delete_family_nonexistent(self):
        """Test suppression d'une famille inexistante"""
        service = GenealogyService()
        result = service.delete_family("nonexistent_id")
        assert result is False
    
    def test_search_families_by_husband(self):
        """Test recherche de familles par mari"""
        service = GenealogyService()
        
        # Créer des familles
        husband1_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        husband2_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Pierre",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="DURAND",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband1 = service.create_person(husband1_data)
        husband2 = service.create_person(husband2_data)
        wife = service.create_person(wife_data)
        
        family1_data = FamilyCreateSchema(
            husband_id=husband1.id,
            wife_id=wife.id
        )
        family2_data = FamilyCreateSchema(
            husband_id=husband2.id,
            wife_id=wife.id
        )
        
        service.create_family(family1_data)
        service.create_family(family2_data)
        
        # Rechercher par mari
        search_params = FamilySearchSchema(husband_last_name="DUPONT")
        results, total = service.search_families(search_params)
        
        assert total == 1
        assert len(results) == 1
        assert results[0].husband_id == husband1.id


class MockGenealogyServiceEventOperations:
    """Tests pour les opérations sur les événements"""
    
    def test_create_personal_event_success(self):
        """Test création réussie d'un événement personnel"""
        service = GenealogyService()
        
        # Créer une personne
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person = service.create_person(person_data)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.BIRTH,
            date="01/01/1990",
            place="Paris"
        )
        
        result = service.create_personal_event(event_data)
        assert result is not None
        assert result.person_id == person.id
        assert result.event_type == EventType.BIRTH
        assert result.id in service._genealogy.events
    
    def test_create_family_event_success(self):
        """Test création réussie d'un événement familial"""
        service = GenealogyService()
        
        # Créer une famille
        husband_data = PersonCreateSchema(
            last_name="DUPONT",
            first_name="Jean",
            gender=Gender.MALE
        )
        wife_data = PersonCreateSchema(
            last_name="MARTIN",
            first_name="Marie",
            gender=Gender.FEMALE
        )
        
        husband = service.create_person(husband_data)
        wife = service.create_person(wife_data)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.id,
            wife_id=wife.id
        )
        family = service.create_family(family_data)
        
        event_data = FamilyEventCreateSchema(
            family_id=family.id,
            event_type=FamilyEventType.MARRIAGE,
            date="01/01/2010",
            place="Paris"
        )
        
        result = service.create_family_event(event_data)
        assert result is not None
        assert result.family_id == family.id
        assert result.event_type == FamilyEventType.MARRIAGE
    
    def test_get_event_existing(self):
        """Test récupération d'un événement existant"""
        service = GenealogyService()
        
        # Créer une personne et un événement
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person = service.create_person(person_data)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.BIRTH,
            date="01/01/1990"
        )
        created_event = service.create_personal_event(event_data)
        
        result = service.get_event(created_event.id)
        assert result is not None
        assert result.id == created_event.id
    
    def test_get_event_nonexistent(self):
        """Test récupération d'un événement inexistant"""
        service = GenealogyService()
        result = service.get_event("nonexistent_id")
        assert result is None
    
    def test_update_event_success(self):
        """Test mise à jour réussie d'un événement"""
        service = GenealogyService()
        
        # Créer une personne et un événement
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person = service.create_person(person_data)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.BIRTH,
            date="01/01/1990"
        )
        created_event = service.create_personal_event(event_data)
        
        update_data = EventUpdateSchema(
            date="02/01/1990",
            place="Lyon"
        )
        
        result = service.update_event(created_event.id, update_data)
        assert result is not None
        assert result.date is not None
    
    def test_update_event_nonexistent(self):
        """Test mise à jour d'un événement inexistant"""
        service = GenealogyService()
        update_data = EventUpdateSchema(date="01/01/1990")
        
        result = service.update_event("nonexistent_id", update_data)
        assert result is None
    
    def test_delete_event_success(self):
        """Test suppression réussie d'un événement"""
        service = GenealogyService()
        
        # Créer une personne et un événement
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person = service.create_person(person_data)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.BIRTH,
            date="01/01/1990"
        )
        created_event = service.create_personal_event(event_data)
        
        result = service.delete_event(created_event.id)
        assert result is True
        assert created_event.id not in service._genealogy.events
    
    def test_delete_event_nonexistent(self):
        """Test suppression d'un événement inexistant"""
        service = GenealogyService()
        result = service.delete_event("nonexistent_id")
        assert result is False
    
    def test_search_events_by_type(self):
        """Test recherche d'événements par type"""
        service = GenealogyService()
        
        # Créer une personne et des événements
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person = service.create_person(person_data)
        
        birth_event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.BIRTH,
            date="01/01/1990"
        )
        death_event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.DEATH,
            date="31/12/2020"
        )
        
        service.create_personal_event(birth_event_data)
        service.create_personal_event(death_event_data)
        
        # Rechercher par type
        search_params = {"event_type": EventType.BIRTH}
        results, total = service.search_events(search_params)
        
        assert total == 1
        assert len(results) == 1
        assert results[0].event_type == EventType.BIRTH


class MockGenealogyServiceStats:
    """Tests pour les statistiques"""
    
    def test_get_stats_empty_genealogy(self):
        """Test statistiques d'une généalogie vide"""
        service = GenealogyService()
        # Créer une généalogie vide
        service._genealogy = service.create_empty()
        
        stats = service.get_stats()
        assert stats is not None
        assert "total_persons" in stats
        assert "total_families" in stats
        assert "total_events" in stats
        assert stats["total_persons"] == 0
        assert stats["total_families"] == 0
        assert stats["total_events"] == 0
    
    def test_get_stats_with_data(self):
        """Test statistiques avec des données"""
        service = GenealogyService()
        
        # Créer des données
        person_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person = service.create_person(person_data)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.id,
            event_type=EventType.BIRTH,
            date="01/01/1990"
        )
        service.create_personal_event(event_data)
        
        stats = service.get_stats()
        assert stats is not None
        assert stats["total_persons"] >= 1
        assert stats["total_events"] >= 1
    
    def test_get_stats_detailed(self):
        """Test statistiques détaillées"""
        service = GenealogyService()
        
        # Créer des données variées
        person1_data = PersonCreateSchema(
            surname="DUPONT",
            first_name="Jean",
            sex=Gender.MALE
        )
        person2_data = PersonCreateSchema(
            surname="MARTIN",
            first_name="Marie",
            sex=Gender.FEMALE
        )
        
        person1 = service.create_person(person1_data)
        person2 = service.create_person(person2_data)
        
        family_data = FamilyCreateSchema(
            husband_id=person1.id,
            wife_id=person2.id
        )
        service.create_family(family_data)
        
        stats = service.get_stats()
        assert stats is not None
        assert "total_persons" in stats
        assert "total_families" in stats
        assert "total_events" in stats
        assert "gender_distribution" in stats
        assert "marriage_status_distribution" in stats


class MockGenealogyServiceErrorHandling:
    """Tests pour la gestion d'erreurs"""
    
    def test_create_person_with_invalid_data(self):
        """Test création de personne avec données invalides"""
        service = GenealogyService()
        
        # Test avec données manquantes
        with pytest.raises(Exception):
            service.create_person(None)
    
    def test_create_family_with_invalid_persons(self):
        """Test création de famille avec personnes invalides"""
        service = GenealogyService()
        
        family_data = FamilyCreateSchema(
            husband_id="invalid_id",
            wife_id="invalid_id"
        )
        
        with pytest.raises(Exception):
            service.create_family(family_data)
    
    def test_create_event_with_invalid_person(self):
        """Test création d'événement avec personne invalide"""
        service = GenealogyService()
        
        event_data = PersonalEventCreateSchema(
            person_id="invalid_id",
            event_type=EventType.BIRTH,
            date="01/01/1990"
        )
        
        with pytest.raises(Exception):
            service.create_personal_event(event_data)
    
    def test_search_with_invalid_parameters(self):
        """Test recherche avec paramètres invalides"""
        service = GenealogyService()
        
        # Test avec paramètres None
        with pytest.raises(Exception):
            service.search_persons(None)
    
    def test_update_with_invalid_data(self):
        """Test mise à jour avec données invalides"""
        service = GenealogyService()
        
        # Test avec données None
        with pytest.raises(Exception):
            service.update_person("some_id", None)
