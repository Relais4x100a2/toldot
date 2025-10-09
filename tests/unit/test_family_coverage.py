"""
Tests supplémentaires pour améliorer la couverture de family.py
"""

import pytest
from geneweb_py.core.family import Family, Child, ChildSex, MarriageStatus
from geneweb_py.core.date import Date
from geneweb_py.core.event import FamilyEvent, FamilyEventType, EventType


class TestFamilyIdProperty:
    """Tests pour la propriété id"""
    
    def test_id_property(self):
        """Test propriété id (alias de family_id)"""
        family = Family(family_id="FAM001")
        assert family.id == "FAM001"
        assert family.id == family.family_id


class TestFamilyGetEventsByType:
    """Tests pour get_events_by_type"""
    
    def test_get_events_by_type_with_event_type(self):
        """Test get_events_by_type avec EventType"""
        family = Family(family_id="FAM001")
        
        marriage_event = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE
        )
        divorce_event = FamilyEvent(
            event_type=EventType.DIVORCE,
            family_event_type=FamilyEventType.DIVORCE
        )
        
        family.add_event(marriage_event)
        family.add_event(divorce_event)
        
        marriage_events = family.get_events_by_type(EventType.MARRIAGE)
        assert len(marriage_events) == 1
        assert marriage_events[0] == marriage_event
    
    def test_get_events_by_type_with_family_event_type(self):
        """Test get_events_by_type avec FamilyEventType"""
        family = Family(family_id="FAM001")
        
        marriage_event = FamilyEvent(
            event_type=EventType.MARRIAGE,
            family_event_type=FamilyEventType.MARRIAGE
        )
        
        family.add_event(marriage_event)
        
        marriage_events = family.get_events_by_type(FamilyEventType.MARRIAGE)
        assert len(marriage_events) == 1
        assert marriage_events[0] == marriage_event
    
    def test_get_events_by_type_not_found(self):
        """Test get_events_by_type quand aucun événement ne correspond"""
        family = Family(family_id="FAM001")
        
        divorce_event = FamilyEvent(
            event_type=EventType.DIVORCE,
            family_event_type=FamilyEventType.DIVORCE
        )
        
        family.add_event(divorce_event)
        
        marriage_events = family.get_events_by_type(EventType.MARRIAGE)
        assert len(marriage_events) == 0
    
    def test_get_events_by_type_event_type_not_mapped(self):
        """Test get_events_by_type avec EventType non familial"""
        family = Family(family_id="FAM001")
        
        # BIRTH n'est pas un événement familial
        events = family.get_events_by_type(EventType.BIRTH)
        assert len(events) == 0


class TestFamilyClearValidationErrors:
    """Tests pour clear_validation_errors"""
    
    def test_clear_validation_errors(self):
        """Test clear_validation_errors"""
        family = Family(family_id="FAM001")
        
        # Ajouter des erreurs
        family.add_validation_error("Erreur 1")
        family.add_validation_error("Erreur 2")
        assert family.is_valid is False
        # Il peut y avoir des erreurs de validation initiales
        error_count = len(family.validation_errors)
        assert error_count >= 2
        
        # Effacer
        family.clear_validation_errors()
        assert family.is_valid is True
        assert len(family.validation_errors) == 0


class TestFamilyStringRepresentation:
    """Tests pour __str__ et __repr__"""
    
    def test_str_representation_with_both_spouses(self):
        """Test __str__ avec deux conjoints"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        result = str(family)
        assert "CORNO_Joseph_0" in result
        assert "THOMAS_Marie_0" in result
        assert "+" in result
        assert "0 enfants" in result
    
    def test_str_representation_with_one_spouse(self):
        """Test __str__ avec un seul conjoint"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0"
        )
        result = str(family)
        assert "CORNO_Joseph_0" in result
        assert "0 enfants" in result
    
    def test_str_representation_with_children(self):
        """Test __str__ avec enfants"""
        family = Family(
            family_id="FAM001",
            husband_id="CORNO_Joseph_0",
            wife_id="THOMAS_Marie_0"
        )
        family.add_child("CORNO_Jean_0", ChildSex.MALE)
        family.add_child("CORNO_Sophie_0", ChildSex.FEMALE)
        
        result = str(family)
        assert "2 enfants" in result
    
    def test_repr_representation(self):
        """Test __repr__"""
        family = Family(family_id="FAM001")
        result = repr(family)
        assert "Family" in result
        assert "FAM001" in result

