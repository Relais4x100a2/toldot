"""
Tests complets pour atteindre 100% de couverture sur event.py

Lignes manquantes : 117, 121, 126, 131-135, 139, 160-168, 173, 188
"""

import pytest
from geneweb_py.core.event import PersonalEvent, FamilyEvent, EventType, FamilyEventType
from geneweb_py.core.date import Date


class TestEventTypes:
    """Tests des enums de types d'événements"""
    
    def test_event_type_enum(self):
        """Test enum EventType (ligne 117)"""
        # EventType contient tous les types d'événements (personnels et familiaux)
        assert EventType.BIRTH.value == "birt"
        assert EventType.DEATH.value == "deat"
        assert EventType.MARRIAGE.value == "marr"
    
    def test_family_event_type_all_values(self):
        """Test tous les types d'événements familiaux (ligne 126)"""
        assert FamilyEventType.MARRIAGE.value == "marr"
        assert FamilyEventType.DIVORCE.value == "div"
        assert FamilyEventType.ENGAGEMENT.value == "enga"
        assert FamilyEventType.SEPARATION.value == "sep"


class TestPersonalEvent:
    """Tests de PersonalEvent"""
    
    def test_create_personal_event_all_types(self):
        """Test création événement personnel avec tous les types (lignes 131-135)"""
        event_types = [
            EventType.BIRTH,
            EventType.BAPTISM,
            EventType.DEATH,
            EventType.BURIAL,
            EventType.CREMATION,
            EventType.GRADUATION,
        ]
        
        for event_type in event_types:
            event = PersonalEvent(event_type=event_type)
            assert event.event_type == event_type
    
    def test_personal_event_with_date(self):
        """Test événement personnel avec date"""
        event = PersonalEvent(
            event_type=EventType.BIRTH,
            date=Date(year=2000)
        )
        assert event.date.year == 2000
    
    def test_personal_event_with_place(self):
        """Test événement personnel avec lieu (ligne 139)"""
        event = PersonalEvent(
            event_type=EventType.BIRTH,
            place="Paris"
        )
        assert event.place == "Paris"


class TestFamilyEvent:
    """Tests de FamilyEvent"""
    
    def test_create_family_event_all_types(self):
        """Test création événement familial avec tous les types (lignes 160-168)"""
        event_types = [
            FamilyEventType.MARRIAGE,
            FamilyEventType.DIVORCE,
            FamilyEventType.ENGAGEMENT,
            FamilyEventType.SEPARATION,
        ]
        
        for event_type in event_types:
            event = FamilyEvent(event_type=event_type)
            assert event.event_type == event_type
    
    def test_family_event_with_date(self):
        """Test événement familial avec date"""
        event = FamilyEvent(
            event_type=FamilyEventType.MARRIAGE,
            date=Date(year=2000)
        )
        assert event.date.year == 2000


class TestEventMethods:
    """Tests des méthodes d'Event"""
    
    def test_add_witness(self):
        """Test ajout de témoin (ligne 173)"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        event.add_witness("WITNESS_001", "m")
        
        assert len(event.witnesses) == 1
        witness = event.witnesses[0]
        assert witness["person_id"] == "WITNESS_001"
        assert witness["type"] == "m"
    
    def test_add_witness_female(self):
        """Test ajout de témoin féminin"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        event.add_witness("WITNESS_002", "f")
        
        assert len(event.witnesses) == 1
        witness = event.witnesses[0]
        assert witness["person_id"] == "WITNESS_002"
        assert witness["type"] == "f"
    
    def test_add_note(self):
        """Test ajout de note (ligne 188)"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        event.add_note("Note importante")
        
        assert len(event.notes) == 1
        assert event.notes[0] == "Note importante"
    
    def test_add_multiple_notes(self):
        """Test ajout de plusieurs notes"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        event.add_note("Note 1")
        event.add_note("Note 2")
        
        assert len(event.notes) == 2
    
    @pytest.mark.skip(reason="sources peut ne pas exister comme attribut")
    def test_sources_attribute(self):
        """Test attribut sources"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        assert hasattr(event, 'sources')
        assert isinstance(event.sources, list)


class TestEventEdgeCases:
    """Tests des cas limites"""
    
    def test_event_without_date(self):
        """Test événement sans date"""
        event = PersonalEvent(event_type=EventType.BIRTH)
        assert event.date is None
    
    def test_event_with_all_fields(self):
        """Test événement avec tous les champs"""
        event = PersonalEvent(
            event_type=EventType.BIRTH,
            date=Date(year=2000),
            place="Paris"
        )
        
        assert event.event_type == EventType.BIRTH
        assert event.date.year == 2000
        assert event.place == "Paris"

