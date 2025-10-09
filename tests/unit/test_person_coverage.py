"""
Tests supplémentaires pour améliorer la couverture de person.py
"""

import pytest
from geneweb_py.core.person import Person, Title, Gender
from geneweb_py.core.date import Date
from geneweb_py.core.event import PersonalEvent, EventType


class TestPersonIsAlive:
    """Tests pour la propriété is_alive"""
    
    def test_is_alive_explicit_false(self):
        """Test is_alive avec is_deceased=False explicite"""
        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            is_deceased=False
        )
        assert person.is_alive is True
    
    def test_is_alive_explicit_true(self):
        """Test is_alive avec is_deceased=True"""
        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            is_deceased=True
        )
        assert person.is_alive is False


class TestPersonAddEvent:
    """Tests pour add_event"""
    
    def test_add_event(self):
        """Test ajout d'un événement personnel"""
        person = Person(last_name="CORNO", first_name="Joseph")
        event = PersonalEvent(event_type=EventType.BAPTISM)
        person.add_event(event)
        assert len(person.events) == 1
        assert person.events[0] == event


class TestPersonGetEventsByType:
    """Tests pour get_events_by_type"""
    
    def test_get_events_by_type(self):
        """Test récupération d'événements par type"""
        person = Person(last_name="CORNO", first_name="Joseph")
        
        baptism = PersonalEvent(event_type=EventType.BAPTISM)
        graduation = PersonalEvent(event_type=EventType.GRADUATION)
        baptism2 = PersonalEvent(event_type=EventType.BAPTISM)
        
        person.add_event(baptism)
        person.add_event(graduation)
        person.add_event(baptism2)
        
        baptisms = person.get_events_by_type("bapt")
        assert len(baptisms) == 2
        assert baptism in baptisms
        assert baptism2 in baptisms
        assert graduation not in baptisms


class TestPersonGetFamilies:
    """Tests pour get_families"""
    
    def test_get_families_empty(self):
        """Test get_families sans famille"""
        person = Person(last_name="CORNO", first_name="Joseph")
        assert person.get_families() == []
    
    def test_get_families_as_child(self):
        """Test get_families comme enfant"""
        person = Person(last_name="CORNO", first_name="Joseph")
        person.families_as_child.append("FAM001")
        families = person.get_families()
        assert len(families) == 1
        assert "FAM001" in families
    
    def test_get_families_as_spouse(self):
        """Test get_families comme conjoint"""
        person = Person(last_name="CORNO", first_name="Joseph")
        person.families_as_spouse.append("FAM002")
        families = person.get_families()
        assert len(families) == 1
        assert "FAM002" in families
    
    def test_get_families_both(self):
        """Test get_families à la fois comme enfant et conjoint"""
        person = Person(last_name="CORNO", first_name="Joseph")
        person.families_as_child.append("FAM001")
        person.families_as_spouse.append("FAM002")
        families = person.get_families()
        assert len(families) == 2
        assert "FAM001" in families
        assert "FAM002" in families


class TestPersonClearValidationErrors:
    """Tests pour clear_validation_errors"""
    
    def test_clear_validation_errors(self):
        """Test clear_validation_errors"""
        person = Person(last_name="CORNO", first_name="Joseph")
        
        # Ajouter quelques erreurs
        person.add_validation_error("Erreur 1")
        person.add_validation_error("Erreur 2")
        assert person.is_valid is False
        assert len(person.validation_errors) == 2
        
        # Effacer
        person.clear_validation_errors()
        assert person.is_valid is True
        assert len(person.validation_errors) == 0


class TestPersonStringRepresentation:
    """Tests pour __str__ et __repr__"""
    
    def test_str_representation(self):
        """Test __str__"""
        person = Person(
            last_name="CORNO",
            first_name="Joseph",
            nickname="Jo"
        )
        # __str__ devrait retourner display_name, qui devrait inclure le nickname
        result = str(person)
        assert "Jo" in result or "CORNO" in result
    
    def test_repr_representation(self):
        """Test __repr__"""
        person = Person(
            last_name="CORNO",
            first_name="Joseph"
        )
        result = repr(person)
        assert "Person" in result
        assert "CORNO" in result
        assert "Joseph" in result

