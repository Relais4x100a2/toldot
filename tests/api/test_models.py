"""
Tests pour les modèles Pydantic de l'API.
"""

import pytest
from pydantic import ValidationError

from geneweb_py.api.models.event import (
    EventSchema,
    PersonalEventCreateSchema,
)
from geneweb_py.api.models.family import (
    FamilyCreateSchema,
)
from geneweb_py.api.models.person import (
    PersonCreateSchema,
    PersonSchema,
    TitleSchema,
)
from geneweb_py.api.models.responses import (
    ErrorResponse,
    PaginatedResponse,
    PaginationInfo,
    SuccessResponse,
)
from geneweb_py.core.models import Gender


class TestPersonModels:
    """Tests pour les modèles Person."""

    def test_person_create_schema_valid(self):
        """Test validation d'un schéma de création valide."""
        data = {
            "first_name": "Jean",
            "surname": "Dupont",
            "sex": "male",
            "access_level": "public",
        }
        person = PersonCreateSchema(**data)
        assert person.first_name == "Jean"
        assert person.surname == "Dupont"
        assert person.sex == Gender.MALE

    def test_person_create_schema_invalid_name(self):
        """Test validation avec nom invalide."""
        with pytest.raises(ValidationError):
            PersonCreateSchema(
                first_name="",  # Nom vide
                surname="Dupont",
                sex="male",
            )

    def test_person_schema_conversion(self):
        """Test conversion des enums."""
        person = PersonSchema(
            id="test",
            first_name="Jean",
            surname="Dupont",
            sex="male",  # String converti en enum
            access_level="public",
        )
        assert isinstance(person.sex, Gender)
        assert person.sex == Gender.MALE

    def test_title_schema(self):
        """Test schéma de titre."""
        title = TitleSchema(name="Duc", title_type="noblesse", place="Paris")
        assert title.name == "Duc"
        assert title.place == "Paris"


class TestFamilyModels:
    """Tests pour les modèles Family."""

    def test_family_create_schema(self):
        """Test création d'une famille."""
        family = FamilyCreateSchema(
            husband_id="h001",
            wife_id="w001",
            marriage_status="married",
        )
        assert family.husband_id == "h001"
        assert family.wife_id == "w001"


class TestEventModels:
    """Tests pour les modèles Event."""

    def test_personal_event_create(self):
        """Test création d'événement personnel."""
        event = PersonalEventCreateSchema(
            person_id="p001",
            event_type="birth",
            place="Paris",
        )
        assert event.person_id == "p001"
        # event_type est converti en enum
        from geneweb_py.core.models import EventType

        assert event.event_type == EventType.BIRTH

    def test_personal_event_with_all_fields(self):
        """Test événement avec tous les champs."""
        event = PersonalEventCreateSchema(
            person_id="p001",
            event_type="birth",
            date="1950-01-01",
            place="Paris",
            reason="Raison",
            note="Note de test",
            witnesses=["Témoin 1"],
            sources=["Source 1"],
        )
        assert event.person_id == "p001"
        assert event.date == "1950-01-01"
        assert event.place == "Paris"
        assert len(event.witnesses) == 1

    def test_family_event_create(self):
        """Test création d'événement familial."""
        from geneweb_py.api.models.event import FamilyEventCreateSchema
        from geneweb_py.core.models import FamilyEventType

        event = FamilyEventCreateSchema(
            family_id="f001",
            event_type=FamilyEventType.MARRIAGE,
            place="Lyon",
        )
        assert event.family_id == "f001"

    def test_event_update_schema(self):
        """Test schéma de mise à jour événement."""
        from geneweb_py.api.models.event import EventUpdateSchema

        update = EventUpdateSchema(
            place="New Place",
            reason="New Reason",
        )
        assert update.place == "New Place"

    def test_event_schema_complete(self):
        """Test schéma événement complet."""
        from geneweb_py.core.models import EventType

        event = EventSchema(
            id="evt_001",
            event_type=EventType.BIRTH,
            date="1950-01-01",
            place="Paris",
            reason="Raison",
            notes=["Note 1"],
            witnesses=["Témoin 1"],
            sources=["Source 1"],
            person_id="p001",
        )
        assert event.id == "evt_001"


class TestResponseModels:
    """Tests pour les modèles de réponse."""

    def test_success_response(self):
        """Test réponse de succès."""
        response = SuccessResponse(
            message="Succès",
            data={"key": "value"},
        )
        assert response.success is True
        assert response.message == "Succès"
        assert response.data == {"key": "value"}

    def test_error_response(self):
        """Test réponse d'erreur."""
        from geneweb_py.api.models.responses import ErrorDetail

        response = ErrorResponse(
            message="Erreur",
            code="ERR_001",
            details=[ErrorDetail(field="test_field", message="Erreur de validation")],
        )
        assert response.error is True
        assert response.code == "ERR_001"

    def test_paginated_response(self):
        """Test réponse paginée."""
        pagination = PaginationInfo(
            page=1,
            size=20,
            total=100,
            pages=5,
            has_next=True,
            has_prev=False,
        )
        response = PaginatedResponse(
            items=[{"id": "1"}, {"id": "2"}],
            pagination=pagination,
        )
        assert len(response.items) == 2
        assert response.pagination.total == 100
        assert response.pagination.has_next is True
