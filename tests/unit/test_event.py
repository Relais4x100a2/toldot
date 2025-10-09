"""
Tests unitaires pour le module Event (core/event.py).
"""

import pytest
from geneweb_py.core.event import (
    Event,
    EventType,
    FamilyEvent,
    FamilyEventType,
    PersonalEvent,
)
from geneweb_py.core.date import Date


class TestEvent:
    """Tests pour la classe Event."""

    def test_event_creation_minimal(self):
        """Test création d'un événement minimal."""
        event = Event(event_type=EventType.BIRTH)
        assert event.event_type == EventType.BIRTH
        assert event.date is None
        assert event.place is None
        assert len(event.witnesses) == 0
        assert len(event.notes) == 0

    def test_event_creation_complete(self):
        """Test création d'un événement complet."""
        date = Date(day=15, month=3, year=1950)
        event = Event(
            event_type=EventType.BIRTH,
            date=date,
            place="Paris",
            source="Acte de naissance",
            reason="Naissance normale",
            person_id="p001",
        )
        assert event.event_type == EventType.BIRTH
        assert event.date == date
        assert event.place == "Paris"
        assert event.source == "Acte de naissance"
        assert event.reason == "Naissance normale"
        assert event.person_id == "p001"

    def test_add_witness(self):
        """Test ajout d'un témoin."""
        event = Event(event_type=EventType.MARRIAGE)
        event.add_witness("wit001", "m")
        
        assert len(event.witnesses) == 1
        assert event.witnesses[0]["person_id"] == "wit001"
        assert event.witnesses[0]["type"] == "m"

    def test_add_witness_without_type(self):
        """Test ajout d'un témoin sans type."""
        event = Event(event_type=EventType.MARRIAGE)
        event.add_witness("wit002")
        
        assert len(event.witnesses) == 1
        assert event.witnesses[0]["person_id"] == "wit002"
        assert event.witnesses[0]["type"] is None

    def test_add_note(self):
        """Test ajout d'une note."""
        event = Event(event_type=EventType.DEATH)
        event.add_note("Décès à l'hôpital")
        event.add_note("Certificat médical joint")
        
        assert len(event.notes) == 2
        assert event.notes[0] == "Décès à l'hôpital"
        assert event.notes[1] == "Certificat médical joint"

    def test_set_metadata(self):
        """Test définition de métadonnées."""
        event = Event(event_type=EventType.OCCUPATION)
        event.set_metadata("profession", "Ingénieur")
        event.set_metadata("years", 10)
        
        assert event.metadata["profession"] == "Ingénieur"
        assert event.metadata["years"] == 10

    def test_display_name(self):
        """Test nom d'affichage de l'événement."""
        event = Event(event_type=EventType.BIRTH)
        assert event.display_name == "BIRT"
        
        event2 = Event(event_type=EventType.MARRIAGE)
        assert event2.display_name == "MARR"

    def test_is_family_event_true(self):
        """Test détection des événements familiaux."""
        marriage = Event(event_type=EventType.MARRIAGE)
        assert marriage.is_family_event is True
        
        divorce = Event(event_type=EventType.DIVORCE)
        assert divorce.is_family_event is True
        
        engagement = Event(event_type=EventType.ENGAGEMENT)
        assert engagement.is_family_event is True

    def test_is_family_event_false(self):
        """Test détection des événements non-familiaux."""
        birth = Event(event_type=EventType.BIRTH)
        assert birth.is_family_event is False
        
        death = Event(event_type=EventType.DEATH)
        assert death.is_family_event is False

    def test_to_dict_minimal(self):
        """Test conversion en dictionnaire (minimal)."""
        event = Event(event_type=EventType.BIRTH)
        result = event.to_dict()
        
        assert result["type"] == "birt"
        assert result["date"] is None
        assert result["place"] is None
        assert result["source"] is None
        assert result["witnesses"] == []
        assert result["notes"] == []
        assert result["metadata"] == {}

    def test_to_dict_complete(self):
        """Test conversion en dictionnaire (complet)."""
        date = Date(day=15, month=3, year=1950)
        event = Event(
            event_type=EventType.MARRIAGE,
            date=date,
            place="Paris",
            source="Acte de mariage",
        )
        event.add_witness("wit001")
        event.add_note("Mariage religieux")
        event.set_metadata("church", "Notre-Dame")
        
        result = event.to_dict()
        
        assert result["type"] == "marr"
        assert result["date"] == date.display_text
        assert result["place"] == "Paris"
        assert result["source"] == "Acte de mariage"
        assert result["witnesses"] == ["wit001"]
        assert result["notes"] == ["Mariage religieux"]
        assert result["metadata"]["church"] == "Notre-Dame"


class TestFamilyEvent:
    """Tests pour la classe FamilyEvent."""

    def test_family_event_creation(self):
        """Test création d'un événement familial."""
        event = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE,
        )
        assert event.event_type == EventType.MARRIAGE
        assert event.family_event_type == FamilyEventType.MARRIAGE

    def test_family_event_mapping_marriage(self):
        """Test mapping FamilyEventType.MARRIAGE vers EventType.MARRIAGE."""
        event = FamilyEvent(
            event_type=EventType.BIRTH,  # Valeur initiale
            family_event_type=FamilyEventType.MARRIAGE,
        )
        # Le __post_init__ doit override event_type
        assert event.event_type == EventType.MARRIAGE

    def test_family_event_mapping_divorce(self):
        """Test mapping FamilyEventType.DIVORCE vers EventType.DIVORCE."""
        event = FamilyEvent(
            event_type=EventType.BIRTH,
            family_event_type=FamilyEventType.DIVORCE,
        )
        assert event.event_type == EventType.DIVORCE

    def test_family_event_mapping_no_mapping(self):
        """Test FamilyEventType sans mapping disponible."""
        event = FamilyEvent(
            event_type=EventType.BIRTH,
            family_event_type=FamilyEventType.MARRIAGE_BANN,
        )
        # Pas de mapping pour MARRIAGE_BANN, event_type reste inchangé
        assert event.event_type == EventType.BIRTH

    def test_family_event_is_family_event(self):
        """Test que FamilyEvent.is_family_event est toujours True."""
        event = FamilyEvent(
            event_type=EventType.BIRTH,
            family_event_type=FamilyEventType.NO_MARRIAGE,
        )
        assert event.is_family_event is True


class TestPersonalEvent:
    """Tests pour la classe PersonalEvent."""

    def test_personal_event_creation(self):
        """Test création d'un événement personnel."""
        event = PersonalEvent(event_type=EventType.BIRTH)
        assert event.event_type == EventType.BIRTH

    def test_personal_event_is_family_event(self):
        """Test que PersonalEvent.is_family_event est toujours False."""
        event = PersonalEvent(event_type=EventType.MARRIAGE)
        # Même pour un type d'événement familial, PersonalEvent retourne False
        assert event.is_family_event is False

    def test_personal_event_post_init(self):
        """Test que __post_init__ ne fait rien pour PersonalEvent."""
        event = PersonalEvent(
            event_type=EventType.BIRTH,
            place="Paris",
            person_id="p001",
        )
        # Vérifier que l'initialisation fonctionne normalement
        assert event.event_type == EventType.BIRTH
        assert event.place == "Paris"
        assert event.person_id == "p001"


class TestEventTypes:
    """Tests pour les énumérations EventType et FamilyEventType."""

    def test_event_type_values(self):
        """Test valeurs des EventType principaux."""
        assert EventType.BIRTH.value == "birt"
        assert EventType.DEATH.value == "deat"
        assert EventType.MARRIAGE.value == "marr"
        assert EventType.DIVORCE.value == "div"

    def test_family_event_type_values(self):
        """Test valeurs des FamilyEventType principaux."""
        assert FamilyEventType.MARRIAGE.value == "marr"
        assert FamilyEventType.NO_MARRIAGE.value == "nmar"
        assert FamilyEventType.DIVORCE.value == "div"
        assert FamilyEventType.ENGAGEMENT.value == "enga"

    def test_event_type_unique_values(self):
        """Test que les EventType ont des valeurs uniques."""
        values = [e.value for e in EventType]
        assert len(values) == len(set(values))  # Pas de doublons

    def test_family_event_type_unique_values(self):
        """Test que les FamilyEventType ont des valeurs uniques."""
        values = [e.value for e in FamilyEventType]
        assert len(values) == len(set(values))  # Pas de doublons

