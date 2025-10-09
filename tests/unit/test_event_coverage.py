"""
Tests supplémentaires pour améliorer la couverture de event.py
"""

import pytest
from geneweb_py.core.event import (
    Event, FamilyEvent, PersonalEvent,
    EventType, FamilyEventType
)
from geneweb_py.core.date import Date


class TestEventMetadata:
    """Tests pour les métadonnées d'événement"""
    
    def test_set_metadata(self):
        """Test set_metadata"""
        event = Event(event_type=EventType.BIRTH)
        event.set_metadata("custom_field", "custom_value")
        assert event.metadata["custom_field"] == "custom_value"
    
    def test_set_multiple_metadata(self):
        """Test set_metadata avec plusieurs valeurs"""
        event = Event(event_type=EventType.BIRTH)
        event.set_metadata("field1", "value1")
        event.set_metadata("field2", "value2")
        assert len(event.metadata) == 2
        assert event.metadata["field1"] == "value1"
        assert event.metadata["field2"] == "value2"


class TestEventDisplay:
    """Tests pour display_name"""
    
    def test_display_name_birth(self):
        """Test display_name pour naissance"""
        event = Event(event_type=EventType.BIRTH)
        assert event.display_name == "BIRT"
    
    def test_display_name_death(self):
        """Test display_name pour décès"""
        event = Event(event_type=EventType.DEATH)
        assert event.display_name == "DEAT"
    
    def test_display_name_marriage(self):
        """Test display_name pour mariage"""
        event = Event(event_type=EventType.MARRIAGE)
        assert event.display_name == "MARR"


class TestEventIsFamilyEvent:
    """Tests pour is_family_event"""
    
    def test_is_family_event_marriage(self):
        """Test is_family_event pour mariage"""
        event = Event(event_type=EventType.MARRIAGE)
        assert event.is_family_event is True
    
    def test_is_family_event_divorce(self):
        """Test is_family_event pour divorce"""
        event = Event(event_type=EventType.DIVORCE)
        assert event.is_family_event is True
    
    def test_is_family_event_separation(self):
        """Test is_family_event pour séparation"""
        event = Event(event_type=EventType.SEPARATION)
        assert event.is_family_event is True
    
    def test_is_family_event_engagement(self):
        """Test is_family_event pour fiançailles"""
        event = Event(event_type=EventType.ENGAGEMENT)
        assert event.is_family_event is True
    
    def test_is_family_event_pacs(self):
        """Test is_family_event pour PACS"""
        event = Event(event_type=EventType.PACS)
        assert event.is_family_event is True
    
    def test_is_family_event_birth(self):
        """Test is_family_event pour naissance (non familial)"""
        event = Event(event_type=EventType.BIRTH)
        assert event.is_family_event is False
    
    def test_is_family_event_death(self):
        """Test is_family_event pour décès (non familial)"""
        event = Event(event_type=EventType.DEATH)
        assert event.is_family_event is False


class TestFamilyEvent:
    """Tests pour FamilyEvent"""
    
    def test_family_event_post_init_marriage(self):
        """Test __post_init__ pour FamilyEvent avec mariage"""
        event = FamilyEvent(
            event_type=EventType.CUSTOM,
            family_event_type=FamilyEventType.MARRIAGE
        )
        assert event.event_type == EventType.MARRIAGE
    
    def test_family_event_post_init_divorce(self):
        """Test __post_init__ pour FamilyEvent avec divorce"""
        event = FamilyEvent(
            event_type=EventType.CUSTOM,
            family_event_type=FamilyEventType.DIVORCE
        )
        assert event.event_type == EventType.DIVORCE
    
    def test_family_event_post_init_separation(self):
        """Test __post_init__ pour FamilyEvent avec séparation"""
        event = FamilyEvent(
            event_type=EventType.CUSTOM,
            family_event_type=FamilyEventType.SEPARATION
        )
        assert event.event_type == EventType.SEPARATION
    
    def test_family_event_post_init_engagement(self):
        """Test __post_init__ pour FamilyEvent avec fiançailles"""
        event = FamilyEvent(
            event_type=EventType.CUSTOM,
            family_event_type=FamilyEventType.ENGAGEMENT
        )
        assert event.event_type == EventType.ENGAGEMENT
    
    def test_family_event_post_init_pacs(self):
        """Test __post_init__ pour FamilyEvent avec PACS"""
        event = FamilyEvent(
            event_type=EventType.CUSTOM,
            family_event_type=FamilyEventType.PACS
        )
        assert event.event_type == EventType.PACS
    
    def test_family_event_is_family_event(self):
        """Test is_family_event pour FamilyEvent"""
        event = FamilyEvent(
            event_type=EventType.BIRTH,
            family_event_type=FamilyEventType.MARRIAGE
        )
        # Devrait toujours être True pour FamilyEvent
        assert event.is_family_event is True


class TestPersonalEvent:
    """Tests pour PersonalEvent"""
    
    def test_personal_event_is_family_event(self):
        """Test is_family_event pour PersonalEvent"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        assert event.is_family_event is False
    
    def test_personal_event_with_marriage_type(self):
        """Test PersonalEvent même avec type mariage"""
        # Un PersonalEvent n'est jamais familial, même si le type est MARRIAGE
        event = PersonalEvent(event_type=EventType.MARRIAGE)
        assert event.is_family_event is False


class TestEventToDict:
    """Tests pour to_dict"""
    
    def test_to_dict_simple_event(self):
        """Test to_dict avec événement simple"""
        event = Event(event_type=EventType.BIRTH)
        result = event.to_dict()
        assert result['type'] == 'birt'
        assert result['date'] is None
        assert result['place'] is None
        assert result['witnesses'] == []
    
    def test_to_dict_complete_event(self):
        """Test to_dict avec événement complet"""
        date = Date.parse("25/12/1990")
        event = Event(
            event_type=EventType.BIRTH,
            date=date,
            place="Paris",
            source="Registre d'état civil"
        )
        event.add_note("Note de test")
        event.set_metadata("custom", "value")
        
        result = event.to_dict()
        assert result['type'] == 'birt'
        assert result['date'] == "25/12/1990"
        assert result['place'] == "Paris"
        assert result['source'] == "Registre d'état civil"
        assert result['notes'] == ["Note de test"]
        assert result['metadata'] == {"custom": "value"}


class TestFamilyEventWithoutType:
    """Tests pour FamilyEvent sans family_event_type"""
    
    def test_family_event_without_family_event_type(self):
        """Test FamilyEvent sans family_event_type défini"""
        event = FamilyEvent(event_type=EventType.MARRIAGE)
        # Ne devrait pas crasher
        assert event.event_type == EventType.MARRIAGE
        assert event.family_event_type is None

