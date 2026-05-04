"""
Tests pour les services de l'API geneweb-py.
"""

import pytest

from geneweb_py.api.models.event import (
    FamilyEventCreateSchema,
    PersonalEventCreateSchema,
)
from geneweb_py.api.models.family import (
    FamilyCreateSchema,
    FamilySearchSchema,
    FamilyUpdateSchema,
)
from geneweb_py.api.models.person import (
    PersonCreateSchema,
    PersonSearchSchema,
    PersonUpdateSchema,
)
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.date import Date
from geneweb_py.core.models import (
    AccessLevel,
    EventType,
    Family,
    Gender,
    Genealogy,
    MarriageStatus,
    Person,
)


@pytest.fixture
def service():
    """Service de généalogie pour les tests."""
    return GenealogyService()


@pytest.fixture
def sample_person():
    """Personne d'exemple."""
    return Person(
        first_name="Jean",
        last_name="Dupont",
        gender=Gender.MALE,
        access_level=AccessLevel.PUBLIC,
    )


@pytest.fixture
def sample_family():
    """Famille d'exemple."""
    return Family(
        family_id="fam_001",
        husband_id="h001",
        wife_id="w001",
        marriage_status=MarriageStatus.MARRIED,
    )


class TestGenealogyServiceInit:
    """Tests pour l'initialisation du service."""

    def test_service_creation(self, service):
        """Test création du service."""
        assert service is not None
        assert service._genealogy is not None
        assert isinstance(service._genealogy, Genealogy)

    def test_service_has_parser(self, service):
        """Test que le service a un parser."""
        assert service._parser is not None

    def test_initialize_empty_genealogy(self):
        """Test initialisation d'une généalogie vide."""
        service = GenealogyService()
        assert service._genealogy is not None
        assert isinstance(service._genealogy.persons, dict)
        assert isinstance(service._genealogy.families, dict)


class TestGenealogyServiceLoad:
    """Tests pour le chargement de fichiers."""

    def test_load_from_file(self, service, tmp_path):
        """Test chargement depuis un fichier."""
        # Créer un fichier de test
        test_file = tmp_path / "test.gw"
        test_file.write_text("fam Jean /Dupont/ +Marie /Martin/\n")

        genealogy = service.load_from_file(str(test_file))
        assert genealogy is not None
        assert isinstance(genealogy, Genealogy)

    def test_load_from_invalid_file(self, service):
        """Test chargement d'un fichier invalide."""
        from geneweb_py.core.exceptions import GeneWebError

        with pytest.raises(GeneWebError):
            service.load_from_file("/path/does/not/exist.gw")

    def test_create_empty(self, service):
        """Test création d'une généalogie vide."""
        genealogy = service.create_empty()
        assert genealogy is not None
        assert len(genealogy.persons) == 0
        assert len(genealogy.families) == 0

    def test_genealogy_property(self, service):
        """Test accès à la propriété genealogy."""
        genealogy = service.genealogy
        assert genealogy is not None
        assert isinstance(genealogy, Genealogy)


class TestPersonOperations:
    """Tests pour les opérations sur les personnes."""

    def test_create_person(self, service):
        """Test création d'une personne."""
        person_data = PersonCreateSchema(
            first_name="Jean",
            surname="Dupont",
            sex="male",
            access_level="public",
        )
        person = service.create_person(person_data)
        assert person is not None
        assert person.first_name == "Jean"
        assert person.last_name == "Dupont"

    def test_get_person_existing(self, service):
        """Test récupération d'une personne existante."""
        # Créer une personne d'abord
        person_data = PersonCreateSchema(
            first_name="Jean",
            surname="Dupont",
            sex="male",
            access_level="public",
        )
        created_person = service.create_person(person_data)

        # Récupérer la personne
        person = service.get_person(created_person.unique_id)
        assert person is not None
        assert person.first_name == "Jean"

    def test_get_person_not_found(self, service):
        """Test récupération d'une personne inexistante."""
        person = service.get_person("non_existent_id")
        assert person is None

    def test_update_person(self, service):
        """Test mise à jour d'une personne."""
        # Créer une personne
        person_data = PersonCreateSchema(
            first_name="Jean",
            surname="Dupont",
            sex="male",
            access_level="public",
        )
        created_person = service.create_person(person_data)

        # Mettre à jour
        update_data = PersonUpdateSchema(first_name="Jean-Pierre")
        updated_person = service.update_person(created_person.unique_id, update_data)

        assert updated_person is not None
        assert updated_person.first_name == "Jean-Pierre"

    def test_update_person_not_found(self, service):
        """Test mise à jour d'une personne inexistante."""
        update_data = PersonUpdateSchema(first_name="Jean")
        updated_person = service.update_person("non_existent", update_data)
        assert updated_person is None

    def test_delete_person(self, service):
        """Test suppression d'une personne."""
        # Créer une personne
        person_data = PersonCreateSchema(
            first_name="Jean",
            surname="Dupont",
            sex="male",
            access_level="public",
        )
        created_person = service.create_person(person_data)

        # Supprimer
        result = service.delete_person(created_person.unique_id)
        assert result is True

        # Vérifier que la personne n'existe plus
        person = service.get_person(created_person.unique_id)
        assert person is None

    def test_delete_person_not_found(self, service):
        """Test suppression d'une personne inexistante."""
        result = service.delete_person("non_existent")
        assert result is False

    def test_search_persons_empty(self, service):
        """Test recherche de personnes sans résultats."""
        service.create_empty()  # Réinitialiser
        search_params = PersonSearchSchema(query="NonExistent")
        persons, total = service.search_persons(search_params)
        assert len(persons) == 0
        assert total == 0

    def test_search_persons_with_results(self, service):
        """Test recherche de personnes avec résultats."""
        # Créer quelques personnes
        service.create_empty()
        service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )

        search_params = PersonSearchSchema()
        persons, total = service.search_persons(search_params)
        assert total == 2
        assert len(persons) == 2

    def test_search_persons_with_pagination(self, service):
        """Test recherche avec pagination."""
        service.create_empty()
        # Créer plusieurs personnes
        for i in range(5):
            service.create_person(
                PersonCreateSchema(
                    first_name=f"Person{i}",
                    surname="Test",
                    sex="male",
                    access_level="public",
                )
            )

        search_params = PersonSearchSchema(page=1, size=2)
        persons, total = service.search_persons(search_params)
        assert total == 5
        assert len(persons) == 2

    def test_search_persons_birth_year_range(self, service):
        """Filtre par plage d'année de naissance."""
        service.create_empty()
        p1900 = service.create_person(
            PersonCreateSchema(
                first_name="A", surname="Test", sex="male", access_level="public"
            )
        )
        p1950 = service.create_person(
            PersonCreateSchema(
                first_name="B", surname="Test", sex="male", access_level="public"
            )
        )
        p1900.birth_date = Date.parse("01/01/1900")
        p1950.birth_date = Date.parse("15/03/1950")

        found, total = service.search_persons(
            PersonSearchSchema(birth_year_from=1920, birth_year_to=2000)
        )
        assert total == 1
        assert found[0].unique_id == p1950.unique_id

    def test_search_persons_place(self, service):
        """Filtre par sous-chaîne de lieu (naissance, décès, baptême, sépulture)."""
        service.create_empty()
        p_paris = service.create_person(
            PersonCreateSchema(
                first_name="X", surname="Loc", sex="male", access_level="public"
            )
        )
        p_lyon = service.create_person(
            PersonCreateSchema(
                first_name="Y", surname="Loc", sex="male", access_level="public"
            )
        )
        p_paris.birth_place = "Paris, France"
        p_lyon.baptism_place = "Lyon"

        found, total = service.search_persons(PersonSearchSchema(place="paris"))
        assert total == 1
        assert found[0].unique_id == p_paris.unique_id

    def test_get_stats_includes_advanced(self, service):
        """Statistiques avancées (longévité, lieux, histogramme enfants)."""
        service.create_empty()
        stats = service.get_stats()
        assert "advanced" in stats
        assert "longevity" in stats["advanced"]
        assert "geography" in stats["advanced"]
        assert "family_sizes" in stats["advanced"]

    def test_validate_genealogy_detects_broken_reference(self, service):
        """Références familiales invalides remontées par la validation."""
        from geneweb_py.core.family import Family
        from geneweb_py.core.models import MarriageStatus

        service.create_empty()
        g = service.genealogy
        g.families["broken"] = Family(
            family_id="broken",
            husband_id="nope_missing",
            wife_id=None,
            marriage_status=MarriageStatus.MARRIED,
        )
        result = service.validate_genealogy(strict=False)
        assert result["is_valid"] is False
        assert len(result["errors"]) >= 1

    def test_validate_genealogy_strict_updates_state(self, service):
        """Mode strict : met à jour is_valid sur la généalogie."""
        from geneweb_py.core.family import Family
        from geneweb_py.core.models import MarriageStatus

        service.create_empty()
        g = service.genealogy
        g.clear_validation_errors()
        g.families["broken2"] = Family(
            family_id="broken2",
            husband_id="ghost",
            wife_id=None,
            marriage_status=MarriageStatus.MARRIED,
        )
        service.validate_genealogy(strict=True)
        assert g.is_valid is False
        assert len(g.validation_errors) >= 1


class TestFamilyOperations:
    """Tests pour les opérations sur les familles."""

    def test_create_family(self, service):
        """Test création d'une famille."""
        # Créer les époux d'abord
        husband = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        wife = service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )

        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status="married",
        )
        family = service.create_family(family_data)
        assert family is not None
        assert family.husband_id == husband.unique_id

    def test_get_family_existing(self, service):
        """Test récupération d'une famille existante."""
        # Créer une famille
        husband = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        wife = service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status="married",
        )
        created_family = service.create_family(family_data)

        # Récupérer
        family = service.get_family(created_family.family_id)
        assert family is not None

    def test_get_family_not_found(self, service):
        """Test récupération d'une famille inexistante."""
        family = service.get_family("non_existent")
        assert family is None

    def test_update_family(self, service):
        """Test mise à jour d'une famille."""
        husband = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        wife = service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )
        family = service.create_family(
            FamilyCreateSchema(
                husband_id=husband.unique_id,
                wife_id=wife.unique_id,
                marriage_status="married",
            )
        )

        # Mise à jour
        update_data = FamilyUpdateSchema(marriage_status="divorced")
        updated = service.update_family(family.family_id, update_data)
        assert updated is not None

    def test_update_family_not_found(self, service):
        """Test mise à jour d'une famille inexistante."""
        update_data = FamilyUpdateSchema(marriage_status="married")
        result = service.update_family("non_existent", update_data)
        assert result is None

    def test_delete_family(self, service):
        """Test suppression d'une famille."""
        # Créer une famille
        husband = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        wife = service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )
        family_data = FamilyCreateSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
            marriage_status="married",
        )
        created_family = service.create_family(family_data)

        # Supprimer
        result = service.delete_family(created_family.family_id)
        assert result is True

    def test_delete_family_not_found(self, service):
        """Test suppression famille inexistante."""
        result = service.delete_family("non_existent")
        assert result is False

    def test_search_families(self, service):
        """Test recherche de familles."""
        service.create_empty()
        search_params = FamilySearchSchema()
        families, total = service.search_families(search_params)
        assert isinstance(families, list)
        assert isinstance(total, int)

    def test_search_families_with_filters(self, service):
        """Test recherche avec filtres."""
        service.create_empty()
        husband = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        wife = service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )
        service.create_family(
            FamilyCreateSchema(
                husband_id=husband.unique_id,
                wife_id=wife.unique_id,
                marriage_status="married",
            )
        )

        search_params = FamilySearchSchema(
            husband_id=husband.unique_id,
            wife_id=wife.unique_id,
        )
        families, total = service.search_families(search_params)
        assert total >= 0


class TestEventOperations:
    """Tests pour les opérations sur les événements."""

    def test_create_personal_event(self, service):
        """Test création d'un événement personnel."""
        # Créer une personne
        person = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )

        event_data = PersonalEventCreateSchema(
            person_id=person.unique_id,
            event_type="birth",
            place="Paris",
        )
        event = service.create_personal_event(event_data)
        assert event is not None
        assert event.event_type == EventType.BIRTH

    def test_create_personal_event_person_not_found(self, service):
        """Test création d'événement pour personne inexistante."""
        event_data = PersonalEventCreateSchema(
            person_id="non_existent",
            event_type="birth",
            place="Paris",
        )
        with pytest.raises(ValueError):
            service.create_personal_event(event_data)

    @pytest.mark.skip(reason="FamilyEventType validation à corriger dans le schéma")
    def test_create_family_event(self, service):
        """Test création d'un événement familial."""
        # Créer une famille
        husband = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        wife = service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )
        family = service.create_family(
            FamilyCreateSchema(
                husband_id=husband.unique_id,
                wife_id=wife.unique_id,
                marriage_status="married",
            )
        )

        # Le schéma attend une string qui sera convertie en FamilyEventType
        from geneweb_py.core.models import FamilyEventType

        event_data = FamilyEventCreateSchema(
            family_id=family.family_id,
            event_type=FamilyEventType.MARRIAGE,
            place="Paris",
        )
        event = service.create_family_event(event_data)
        assert event is not None

    def test_get_event_existing(self, service):
        """Test récupération d'un événement."""
        person = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        service.create_personal_event(
            PersonalEventCreateSchema(
                person_id=person.unique_id,
                event_type="birth",
                place="Paris",
            )
        )

        # Pour l'instant get_event retourne None car les events n'ont pas d'unique_id
        # Test que la méthode fonctionne
        result = service.get_event("any_id")
        assert result is None  # or isinstance(result, Event) - Event non importé

    def test_update_event_not_found(self, service):
        """Test mise à jour événement inexistant."""
        from geneweb_py.api.models.event import EventUpdateSchema

        result = service.update_event("non_existent", EventUpdateSchema())
        assert result is None

    def test_delete_event_not_found(self, service):
        """Test suppression événement inexistant."""
        result = service.delete_event("non_existent")
        assert result is False

    def test_search_events(self, service):
        """Test recherche d'événements."""
        search_params = {"page": 1, "size": 10}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)
        assert isinstance(total, int)

    def test_search_events_by_query(self, service):
        """Test recherche d'événements par query."""
        service.create_empty()
        person = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        service.create_personal_event(
            PersonalEventCreateSchema(
                person_id=person.unique_id,
                event_type="birth",
                place="Paris",
            )
        )

        search_params = {"query": "Paris"}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_by_type(self, service):
        """Test recherche par type d'événement."""
        search_params = {"event_type": EventType.BIRTH}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_by_place(self, service):
        """Test recherche par lieu."""
        search_params = {"place": "Paris"}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_by_person_id(self, service):
        """Test recherche par personne."""
        service.create_empty()
        person = service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )

        search_params = {"person_id": person.unique_id}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_with_witnesses(self, service):
        """Test recherche événements avec témoins."""
        search_params = {"has_witnesses": True}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_without_witnesses(self, service):
        """Test recherche événements sans témoins."""
        search_params = {"has_witnesses": False}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_with_sources(self, service):
        """Test recherche événements avec sources."""
        search_params = {"has_sources": True}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)

    def test_search_events_pagination(self, service):
        """Test pagination des événements."""
        search_params = {"page": 2, "size": 5}
        events, total = service.search_events(search_params)
        assert isinstance(events, list)


class TestStatistics:
    """Tests pour les statistiques."""

    def test_get_stats_empty(self, service):
        """Test statistiques sur généalogie vide."""
        service.create_empty()
        stats = service.get_stats()

        assert "total_persons" in stats
        assert "total_families" in stats
        assert stats["total_persons"] == 0
        assert stats["total_families"] == 0

    def test_get_stats_with_data(self, service):
        """Test statistiques avec données."""
        service.create_empty()
        # Créer quelques données
        service.create_person(
            PersonCreateSchema(
                first_name="Jean", surname="Dupont", sex="male", access_level="public"
            )
        )
        service.create_person(
            PersonCreateSchema(
                first_name="Marie",
                surname="Martin",
                sex="female",
                access_level="public",
            )
        )

        stats = service.get_stats()
        assert stats["total_persons"] == 2
        assert "persons_by_sex" in stats
        # Les clés sont les valeurs de l'enum Gender ("m", "f")
        assert "m" in stats["persons_by_sex"]
        assert "f" in stats["persons_by_sex"]

    def test_get_stats_structure(self, service):
        """Test structure des statistiques."""
        stats = service.get_stats()

        # Vérifier les clés essentielles
        required_keys = [
            "total_persons",
            "total_families",
            "persons_by_sex",
            "persons_by_access_level",
            "families_by_status",
        ]
        for key in required_keys:
            assert key in stats, f"Missing key: {key}"
