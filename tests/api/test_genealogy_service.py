"""
Tests pour le service GenealogyService
"""

import pytest
from unittest.mock import patch, MagicMock
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.api.models.person import PersonCreateSchema, PersonUpdateSchema, PersonSearchSchema
from geneweb_py.api.models.family import FamilyCreateSchema, FamilyUpdateSchema, FamilySearchSchema
from geneweb_py.api.models.event import PersonalEventCreateSchema, FamilyEventCreateSchema, EventUpdateSchema
from geneweb_py.core.models import Gender, AccessLevel, MarriageStatus, EventType, FamilyEventType
from geneweb_py.core.person import Person
from geneweb_py.core.family import Family
from geneweb_py.core.event import PersonalEvent, FamilyEvent
from geneweb_py.core.date import Date


@pytest.fixture
def service():
    """Service de généalogie pour les tests."""
    return GenealogyService()


@pytest.fixture
def sample_person_data():
    """Données d'exemple pour une personne."""
    return PersonCreateSchema(
        surname="DUPONT",
        first_name="Jean",
        sex=Gender.MALE,
        access_level=AccessLevel.PUBLIC
    )


@pytest.fixture
def sample_family_data():
    """Données d'exemple pour une famille."""
    return FamilyCreateSchema(
        husband_id="test_husband_id",
        wife_id="test_wife_id",
        marriage_status=MarriageStatus.MARRIED
    )


@pytest.fixture
def sample_personal_event_data():
    """Données d'exemple pour un événement personnel."""
    return PersonalEventCreateSchema(
        person_id="test_person_id",
        event_type=EventType.BIRTH,
        date="15/06/1990",
        place="Paris"
    )


@pytest.fixture
def sample_family_event_data():
    """Données d'exemple pour un événement familial."""
    return FamilyEventCreateSchema(
        family_id="test_family_id",
        event_type=FamilyEventType.MARRIAGE,
        date="15/06/1990",
        place="Paris"
    )


class TestGenealogyService:
    """Tests pour le service GenealogyService."""
    
    def test_init(self, service):
        """Test initialisation du service."""
        assert service._genealogy is not None
        assert service._parser is not None
        assert len(service._genealogy.persons) == 0
        assert len(service._genealogy.families) == 0
    
    def test_genealogy_property(self, service):
        """Test propriété genealogy."""
        genealogy = service.genealogy
        assert genealogy is not None
        assert isinstance(genealogy, type(service._genealogy))
    
    def test_create_empty(self, service):
        """Test création d'une généalogie vide."""
        genealogy = service.create_empty()
        assert genealogy is not None
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0
    
    def test_load_from_file_success(self, service):
        """Test chargement d'un fichier - succès."""
        with patch.object(service._parser, 'parse_file') as mock_parse:
            mock_genealogy = MagicMock()
            mock_parse.return_value = mock_genealogy
            
            result = service.load_from_file("test.gw")
            
            assert result == mock_genealogy
            assert service._genealogy == mock_genealogy
            mock_parse.assert_called_once_with("test.gw")
    
    def test_load_from_file_error(self, service):
        """Test chargement d'un fichier - erreur."""
        with patch.object(service._parser, 'parse_file') as mock_parse:
            mock_parse.side_effect = Exception("Erreur de parsing")
            
            with pytest.raises(Exception, match="Erreur de parsing"):
                service.load_from_file("test.gw")
    
    def test_create_person_success(self, service, sample_person_data):
        """Test création d'une personne - succès."""
        person = service.create_person(sample_person_data)
        
        assert person is not None
        assert person.last_name == "DUPONT"
        assert person.first_name == "Jean"
        assert person.gender == Gender.MALE
        assert person.unique_id in service._genealogy.persons
    
    def test_create_person_duplicate(self, service, sample_person_data):
        """Test création d'une personne en doublon."""
        # Créer la première personne
        person1 = service.create_person(sample_person_data)
        
        # Créer une deuxième personne avec les mêmes données
        person2 = service.create_person(sample_person_data)
        
        assert person1.unique_id != person2.unique_id
        assert person1.occurrence_number == 0
        assert person2.occurrence_number == 1
    
    def test_get_person_success(self, service, sample_person_data):
        """Test récupération d'une personne - succès."""
        person = service.create_person(sample_person_data)
        person_id = person.unique_id
        
        result = service.get_person(person_id)
        
        assert result is not None
        assert result.unique_id == person_id
        assert result.last_name == "DUPONT"
    
    def test_get_person_not_found(self, service):
        """Test récupération d'une personne inexistante."""
        result = service.get_person("nonexistent_id")
        assert result is None
    
    def test_update_person_success(self, service, sample_person_data):
        """Test mise à jour d'une personne - succès."""
        person = service.create_person(sample_person_data)
        person_id = person.unique_id
        
        update_data = PersonUpdateSchema(
            first_name="Jean-Pierre",
            notes="Mise à jour"
        )
        
        result = service.update_person(person_id, update_data)
        
        assert result is not None
        assert result.first_name == "Jean-Pierre"
        assert result.notes == "Mise à jour"
    
    def test_update_person_not_found(self, service):
        """Test mise à jour d'une personne inexistante."""
        update_data = PersonUpdateSchema(first_name="Test")
        
        result = service.update_person("nonexistent_id", update_data)
        assert result is None
    
    def test_delete_person_success(self, service, sample_person_data):
        """Test suppression d'une personne - succès."""
        person = service.create_person(sample_person_data)
        person_id = person.unique_id
        
        result = service.delete_person(person_id)
        
        assert result is True
        assert person_id not in service._genealogy.persons
    
    def test_delete_person_not_found(self, service):
        """Test suppression d'une personne inexistante."""
        result = service.delete_person("nonexistent_id")
        assert result is False
    
    def test_search_persons_by_name(self, service, sample_person_data):
        """Test recherche de personnes par nom."""
        service.create_person(sample_person_data)
        
        search_params = PersonSearchSchema(
            last_name="DUPONT",
            first_name="Jean"
        )
        
        results, total = service.search_persons(search_params)
        
        assert total == 1
        assert len(results) == 1
        assert results[0].last_name == "DUPONT"
    
    def test_search_persons_empty(self, service):
        """Test recherche de personnes - aucun résultat."""
        search_params = PersonSearchSchema(last_name="INEXISTANT")
        
        results, total = service.search_persons(search_params)
        
        assert total == 0
        assert len(results) == 0
    
    def test_create_family_success(self, service, sample_family_data):
        """Test création d'une famille - succès."""
        # Créer les personnes d'abord
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        service._genealogy.add_person(husband)
        service._genealogy.add_person(wife)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED
        )
        
        family = service.create_family(family_data)
        
        assert family is not None
        assert family.husband_id == husband.unique_id
        assert family.wife_id == wife.unique_id
        assert family.marriage_status == MarriageStatus.MARRIED
    
    def test_create_family_invalid(self, service):
        """Test création d'une famille invalide."""
        family_data = FamilyCreateSchema(
            husband_id="nonexistent",
            wife_id="nonexistent"
        )
        
        with pytest.raises(ValueError, match="Personne non trouvée"):
            service.create_family(family_data)
    
    def test_get_family_success(self, service, sample_family_data):
        """Test récupération d'une famille - succès."""
        # Créer les personnes d'abord
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        service._genealogy.add_person(husband)
        service._genealogy.add_person(wife)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED
        )
        
        family = service.create_family(family_data)
        family_id = family.family_id
        
        result = service.get_family(family_id)
        
        assert result is not None
        assert result.family_id == family_id
    
    def test_get_family_not_found(self, service):
        """Test récupération d'une famille inexistante."""
        result = service.get_family("nonexistent_id")
        assert result is None
    
    def test_update_family_success(self, service, sample_family_data):
        """Test mise à jour d'une famille - succès."""
        # Créer les personnes d'abord
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        service._genealogy.add_person(husband)
        service._genealogy.add_person(wife)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED
        )
        
        family = service.create_family(family_data)
        family_id = family.family_id
        
        update_data = FamilyUpdateSchema(
            marriage_status=MarriageStatus.DIVORCED,
            notes="Divorcé"
        )
        
        result = service.update_family(family_id, update_data)
        
        assert result is not None
        assert result.marriage_status == MarriageStatus.DIVORCED
        assert result.notes == "Divorcé"
    
    def test_update_family_not_found(self, service):
        """Test mise à jour d'une famille inexistante."""
        update_data = FamilyUpdateSchema(marriage_status=MarriageStatus.DIVORCED)
        
        result = service.update_family("nonexistent_id", update_data)
        assert result is None
    
    def test_delete_family_success(self, service, sample_family_data):
        """Test suppression d'une famille - succès."""
        # Créer les personnes d'abord
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        service._genealogy.add_person(husband)
        service._genealogy.add_person(wife)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED
        )
        
        family = service.create_family(family_data)
        family_id = family.family_id
        
        result = service.delete_family(family_id)
        
        assert result is True
        assert family_id not in service._genealogy.families
    
    def test_delete_family_not_found(self, service):
        """Test suppression d'une famille inexistante."""
        result = service.delete_family("nonexistent_id")
        assert result is False
    
    def test_search_families_by_status(self, service, sample_family_data):
        """Test recherche de familles par statut."""
        # Créer les personnes d'abord
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        service._genealogy.add_person(husband)
        service._genealogy.add_person(wife)
        
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED
        )
        
        service.create_family(family_data)
        
        search_params = FamilySearchSchema(
            marriage_status=MarriageStatus.MARRIED
        )
        
        results, total = service.search_families(search_params)
        
        assert total == 1
        assert len(results) == 1
        assert results[0].marriage_status == MarriageStatus.MARRIED
    
    def test_create_personal_event_success(self, service, sample_personal_event_data):
        """Test création d'un événement personnel - succès."""
        # Créer une personne d'abord
        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        service._genealogy.add_person(person)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.unique_id,
            event_type=EventType.BIRTH,
            date="15/06/1990",
            place="Paris"
        )
        
        event = service.create_personal_event(event_data)
        
        assert event is not None
        assert event.person_id == person.unique_id
        assert event.event_type == EventType.BIRTH
        assert event.place == "Paris"
    
    def test_create_family_event_success(self, service, sample_family_event_data):
        """Test création d'un événement familial - succès."""
        # Créer les personnes et la famille d'abord
        husband = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        wife = Person(last_name="MARTIN", first_name="Marie", gender=Gender.FEMALE)
        service._genealogy.add_person(husband)
        service._genealogy.add_person(wife)
        
        family = Family(
            family_id="test_family_1",
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status=MarriageStatus.MARRIED
        )
        service._genealogy.add_family(family)
        
        event_data = FamilyEventCreateSchema(
            family_id=family.family_id,
            event_type=FamilyEventType.MARRIAGE,
            date="15/06/1990",
            place="Paris"
        )
        
        event = service.create_family_event(event_data)
        
        assert event is not None
        assert event.family_id == family.family_id
        assert event.event_type == FamilyEventType.MARRIAGE
        assert event.place == "Paris"
    
    def test_get_event_success(self, service, sample_personal_event_data):
        """Test récupération d'un événement - succès."""
        # Créer une personne d'abord
        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        service._genealogy.add_person(person)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.unique_id,
            event_type=EventType.BIRTH,
            date="15/06/1990",
            place="Paris"
        )
        
        event = service.create_personal_event(event_data)
        event_id = event.event_id
        
        result = service.get_event(event_id)
        
        assert result is not None
        assert result.event_id == event_id
    
    def test_get_event_not_found(self, service):
        """Test récupération d'un événement inexistant."""
        result = service.get_event("nonexistent_id")
        assert result is None
    
    def test_update_event_success(self, service, sample_personal_event_data):
        """Test mise à jour d'un événement - succès."""
        # Créer une personne d'abord
        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        service._genealogy.add_person(person)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.unique_id,
            event_type=EventType.BIRTH,
            date="15/06/1990",
            place="Paris"
        )
        
        event = service.create_personal_event(event_data)
        event_id = event.event_id
        
        update_data = EventUpdateSchema(
            place="Lyon",
            notes="Mise à jour"
        )
        
        result = service.update_event(event_id, update_data)
        
        assert result is not None
        assert result.place == "Lyon"
        assert result.notes == "Mise à jour"
    
    def test_update_event_not_found(self, service):
        """Test mise à jour d'un événement inexistant."""
        update_data = EventUpdateSchema(place="Test")
        
        result = service.update_event("nonexistent_id", update_data)
        assert result is None
    
    def test_delete_event_success(self, service, sample_personal_event_data):
        """Test suppression d'un événement - succès."""
        # Créer une personne d'abord
        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        service._genealogy.add_person(person)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.unique_id,
            event_type=EventType.BIRTH,
            date="15/06/1990",
            place="Paris"
        )
        
        event = service.create_personal_event(event_data)
        event_id = event.event_id
        
        result = service.delete_event(event_id)
        
        assert result is True
        # Vérifier que l'événement a été supprimé de la personne
        assert event_id not in [e.event_id for e in person.events]
    
    def test_delete_event_not_found(self, service):
        """Test suppression d'un événement inexistant."""
        result = service.delete_event("nonexistent_id")
        assert result is False
    
    def test_search_events_by_type(self, service, sample_personal_event_data):
        """Test recherche d'événements par type."""
        # Créer une personne d'abord
        person = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        service._genealogy.add_person(person)
        
        event_data = PersonalEventCreateSchema(
            person_id=person.unique_id,
            event_type=EventType.BIRTH,
            date="15/06/1990",
            place="Paris"
        )
        
        service.create_personal_event(event_data)
        
        search_params = {
            "event_type": EventType.BIRTH
        }
        
        results, total = service.search_events(search_params)
        
        assert total == 1
        assert len(results) == 1
        assert results[0].event_type == EventType.BIRTH
    
    def test_search_events_empty(self, service):
        """Test recherche d'événements - aucun résultat."""
        search_params = {
            "event_type": EventType.DEATH
        }
        
        results, total = service.search_events(search_params)
        
        assert total == 0
        assert len(results) == 0
    
    def test_get_stats(self, service, sample_person_data):
        """Test récupération des statistiques."""
        # Créer quelques données de test
        service.create_person(sample_person_data)
        
        stats = service.get_stats()
        
        assert "total_persons" in stats
        assert "total_families" in stats
        assert "total_events" in stats
        assert "metadata" in stats
        assert stats["total_persons"] == 1
        assert stats["total_families"] == 0
        assert stats["total_events"] == 0
