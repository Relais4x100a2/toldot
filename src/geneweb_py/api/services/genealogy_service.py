"""
Service principal pour la gestion de la généalogie dans l'API geneweb-py.

Ce service fournit les opérations CRUD et la logique métier pour manipuler
les données généalogiques.
"""

import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ...core.date import Date
from ...core.models import (
    Event,
    Family,
    FamilyEvent,
    Genealogy,
    Person,
    PersonalEvent,
)
from ...core.parser import GeneWebParser
from ..models.event import (
    EventUpdateSchema,
    FamilyEventCreateSchema,
    PersonalEventCreateSchema,
)
from ..models.family import FamilyCreateSchema, FamilySearchSchema, FamilyUpdateSchema
from ..models.person import PersonCreateSchema, PersonSearchSchema, PersonUpdateSchema


class GenealogyService:
    """Service principal pour la gestion de la généalogie."""

    def __init__(self):
        """Initialise le service de généalogie."""
        self._genealogy: Optional[Genealogy] = None
        self._parser = GeneWebParser(use_multipass=True)  # Mode multipass activé
        # Créer une généalogie vide par défaut
        self._initialize_empty_genealogy()

    def _initialize_empty_genealogy(self) -> None:
        """Initialise une généalogie avec des données de test."""
        from pathlib import Path

        # Essayer de charger un fichier de test
        test_file = (
            Path(__file__).parent.parent.parent.parent
            / "tests"
            / "fixtures"
            / "simple_test.gw"
        )

        if test_file.exists():
            try:
                self._genealogy = self._parser.parse_file(str(test_file))
                return
            except Exception:
                # Si le parsing échoue, continuer avec une généalogie vide
                pass

        # Créer une généalogie vide par défaut
        from ...core.genealogy import Genealogy, GenealogyMetadata

        metadata = GenealogyMetadata(
            source_file=None,
            encoding="utf-8",
            is_gwplus=False,
            created_date=datetime.now(),
            modified_date=datetime.now(),
            geneweb_version="1.0",
        )

        self._genealogy = Genealogy(persons={}, families={}, metadata=metadata)

    def load_from_file(self, file_path: str) -> Genealogy:
        """
        Charge une généalogie depuis un fichier .gw.

        Args:
            file_path: Chemin vers le fichier .gw

        Returns:
            Genealogy: Objet généalogie chargé

        Raises:
            GeneWebParseError: Erreur de parsing du fichier
        """
        self._genealogy = self._parser.parse_file(file_path)
        return self._genealogy

    def create_empty(self) -> Genealogy:
        """
        Crée une généalogie vide.

        Returns:
            Genealogy: Nouvelle généalogie vide
        """
        self._initialize_empty_genealogy()
        return self._genealogy

    @property
    def genealogy(self) -> Genealogy:
        """
        Retourne la généalogie actuelle.

        Returns:
            Genealogy: Généalogie actuelle

        Raises:
            ValueError: Si aucune généalogie n'est chargée
        """
        if self._genealogy is None:
            raise ValueError(
                "Aucune généalogie chargée. Utilisez load_from_file() ou create_empty()."  # noqa: E501
            )
        return self._genealogy

    # === GESTION DES PERSONNES ===

    def create_person(self, person_data: PersonCreateSchema) -> Person:
        """
        Crée une nouvelle personne.

        Args:
            person_data: Données de la personne à créer

        Returns:
            Person: Personne créée
        """
        genealogy = self.genealogy

        # Conversion des titres
        titles = []
        for title_data in person_data.titles:
            from ...core.person import Title

            title = Title(
                name=title_data.name,
                title_type=title_data.title_type,
                place=title_data.place,
                start_date=None,  # TODO: Parser les dates
                end_date=None,
                number=title_data.number,
                is_main=title_data.is_main,
            )
            titles.append(title)

        # Création de la personne
        person = Person(
            last_name=person_data.surname,
            first_name=person_data.first_name,
            public_name=person_data.public_name,
            titles=titles,
            image_path=person_data.image,
            gender=person_data.sex,
            access_level=person_data.access_level,
            notes=[],
        )

        # Utilisation de l'ID unique généré automatiquement
        person_id = person.unique_id

        # Vérification que la personne n'existe pas déjà
        if person_id in genealogy.persons:
            # Si elle existe, on incrémente le numéro d'occurrence
            occurrence = 1
            while (
                f"{person_data.surname}_{person_data.first_name}_{occurrence}"
                in genealogy.persons
            ):
                occurrence += 1
            person.occurrence_number = occurrence
            person_id = person.unique_id

        genealogy.persons[person_id] = person
        genealogy.metadata.modified_date = datetime.now()

        return person

    def get_person(self, person_id: str) -> Optional[Person]:
        """
        Récupère une personne par son ID.

        Args:
            person_id: Identifiant de la personne

        Returns:
            Person: Personne trouvée ou None
        """
        genealogy = self.genealogy
        return genealogy.persons.get(person_id)

    def update_person(
        self, person_id: str, person_data: PersonUpdateSchema
    ) -> Optional[Person]:
        """
        Met à jour une personne.

        Args:
            person_id: Identifiant de la personne
            person_data: Nouvelles données

        Returns:
            Person: Personne mise à jour ou None si non trouvée
        """
        genealogy = self.genealogy
        person = self.get_person(person_id)

        if person is None:
            return None

        # Mise à jour des champs fournis
        if person_data.first_name is not None:
            person.first_name = person_data.first_name
        if person_data.surname is not None:
            person.last_name = person_data.surname
        if person_data.public_name is not None:
            person.public_name = person_data.public_name
        if person_data.image is not None:
            person.image_path = person_data.image
        if person_data.sex is not None:
            person.gender = person_data.sex
        if person_data.access_level is not None:
            person.access_level = person_data.access_level
        if person_data.titles is not None:
            # Conversion des titres
            titles = []
            for title_data in person_data.titles:
                from ...core.person import Title

                title = Title(
                    name=title_data.name,
                    title_type=title_data.title_type,
                    place=title_data.place,
                    start_date=None,
                    end_date=None,
                    number=title_data.number,
                    is_main=title_data.is_main,
                )
                titles.append(title)
            person.titles = titles

        genealogy.metadata.modified_date = datetime.now()
        return person

    def delete_person(self, person_id: str) -> bool:
        """
        Supprime une personne.

        Args:
            person_id: Identifiant de la personne

        Returns:
            bool: True si supprimée, False si non trouvée
        """
        genealogy = self.genealogy
        person = self.get_person(person_id)

        if person is None:
            return False

        # Suppression des références dans les familles
        for family in genealogy.families.values():
            if family.husband_id == person_id:
                family.husband_id = None
            if family.wife_id == person_id:
                family.wife_id = None
            family.children = [
                child for child in family.children if child.person_id != person_id
            ]

        # Les événements personnels sont supprimés automatiquement avec la personne

        # Suppression de la personne
        if person_id in genealogy.persons:
            del genealogy.persons[person_id]
        genealogy.metadata.modified_date = datetime.now()

        return True

    def search_persons(
        self, search_params: PersonSearchSchema
    ) -> Tuple[List[Person], int]:
        """
        Recherche des personnes selon les critères.

        Args:
            search_params: Paramètres de recherche

        Returns:
            Tuple[List[Person], int]: (Personnes trouvées, nombre total)
        """
        genealogy = self.genealogy
        persons = list(genealogy.persons.values())

        # Filtrage par critères
        if search_params.query:
            query_lower = search_params.query.lower()
            persons = [
                p
                for p in persons
                if (
                    query_lower in p.first_name.lower()
                    or query_lower in p.last_name.lower()
                    or (p.public_name and query_lower in p.public_name.lower())
                )
            ]

        if search_params.first_name:
            persons = [
                p
                for p in persons
                if search_params.first_name.lower() in p.first_name.lower()
            ]

        if search_params.surname:
            persons = [
                p
                for p in persons
                if search_params.surname.lower() in p.last_name.lower()
            ]

        if search_params.sex:
            persons = [p for p in persons if p.gender == search_params.sex]

        if search_params.access_level:
            persons = [
                p for p in persons if p.access_level == search_params.access_level
            ]

        if (
            search_params.birth_year_from is not None
            or search_params.birth_year_to is not None
        ):
            persons = [
                p
                for p in persons
                if _person_year_in_range(
                    p.birth_date,
                    search_params.birth_year_from,
                    search_params.birth_year_to,
                )
            ]

        if (
            search_params.death_year_from is not None
            or search_params.death_year_to is not None
        ):
            persons = [
                p
                for p in persons
                if _person_year_in_range(
                    p.death_date,
                    search_params.death_year_from,
                    search_params.death_year_to,
                )
            ]

        if search_params.place:
            needle = _normalize_place_fragment(search_params.place)
            persons = [p for p in persons if _person_matches_place(p, needle)]

        total = len(persons)

        # Pagination
        start = (search_params.page - 1) * search_params.size
        end = start + search_params.size
        persons = persons[start:end]

        return persons, total

    # === GESTION DES FAMILLES ===

    def create_family(self, family_data: FamilyCreateSchema) -> Family:
        """
        Crée une nouvelle famille.

        Args:
            family_data: Données de la famille à créer

        Returns:
            Family: Famille créée
        """
        genealogy = self.genealogy

        # Génération d'un ID unique
        family_id = f"f{len(genealogy.families) + 1}"

        # Conversion des enfants
        children = []
        for child_data in family_data.children:
            from ...core.family import Child

            child = Child(
                person_id=child_data.person_id,
                sex=child_data.sex,
                last_name=child_data.last_name,
            )
            children.append(child)

        # Création de la famille
        family = Family(
            family_id=family_id,
            husband_id=family_data.husband_id,
            wife_id=family_data.wife_id,
            children=children,
            marriage_status=family_data.marriage_status,
            comments=family_data.notes,
            family_source=family_data.sources[0] if family_data.sources else None,
        )

        genealogy.families[family_id] = family
        genealogy.metadata.modified_date = datetime.now()

        return family

    def get_family(self, family_id: str) -> Optional[Family]:
        """
        Récupère une famille par son ID.

        Args:
            family_id: Identifiant de la famille

        Returns:
            Family: Famille trouvée ou None
        """
        genealogy = self.genealogy
        return genealogy.families.get(family_id)

    def update_family(
        self, family_id: str, family_data: FamilyUpdateSchema
    ) -> Optional[Family]:
        """
        Met à jour une famille.

        Args:
            family_id: Identifiant de la famille
            family_data: Nouvelles données

        Returns:
            Family: Famille mise à jour ou None si non trouvée
        """
        genealogy = self.genealogy
        family = self.get_family(family_id)

        if family is None:
            return None

        # Mise à jour des champs fournis
        if family_data.husband_id is not None:
            family.husband_id = family_data.husband_id
        if family_data.wife_id is not None:
            family.wife_id = family_data.wife_id
        if family_data.marriage_status is not None:
            family.marriage_status = family_data.marriage_status
        if family_data.notes is not None:
            family.notes = family_data.notes
        if family_data.sources is not None:
            family.sources = family_data.sources
        if family_data.children is not None:
            # Conversion des enfants
            children = []
            for child_data in family_data.children:
                from ...core.family import Child

                child = Child(
                    person_id=child_data.person_id,
                    sex=child_data.sex,
                    last_name=child_data.last_name,
                )
                children.append(child)
            family.children = children

        genealogy.metadata.modified_date = datetime.now()
        return family

    def delete_family(self, family_id: str) -> bool:
        """
        Supprime une famille.

        Args:
            family_id: Identifiant de la famille

        Returns:
            bool: True si supprimée, False si non trouvée
        """
        genealogy = self.genealogy
        family = self.get_family(family_id)

        if family is None:
            return False

        # Les événements familiaux sont supprimés automatiquement avec la famille

        # Suppression de la famille
        if family_id in genealogy.families:
            del genealogy.families[family_id]
        genealogy.metadata.modified_date = datetime.now()

        return True

    def search_families(
        self, search_params: FamilySearchSchema
    ) -> Tuple[List[Family], int]:
        """
        Recherche des familles selon les critères.

        Args:
            search_params: Paramètres de recherche

        Returns:
            Tuple[List[Family], int]: (Familles trouvées, nombre total)
        """
        genealogy = self.genealogy
        families = list(genealogy.families.values())

        # Filtrage par critères
        if search_params.husband_id:
            families = [f for f in families if f.husband_id == search_params.husband_id]

        if search_params.wife_id:
            families = [f for f in families if f.wife_id == search_params.wife_id]

        if search_params.marriage_status:
            families = [
                f
                for f in families
                if f.marriage_status == search_params.marriage_status
            ]

        if search_params.has_children is not None:
            if search_params.has_children:
                families = [f for f in families if len(f.children) > 0]
            else:
                families = [f for f in families if len(f.children) == 0]

        if search_params.min_children is not None:
            families = [
                f for f in families if len(f.children) >= search_params.min_children
            ]

        if search_params.max_children is not None:
            families = [
                f for f in families if len(f.children) <= search_params.max_children
            ]

        total = len(families)

        # Pagination
        start = (search_params.page - 1) * search_params.size
        end = start + search_params.size
        families = families[start:end]

        return families, total

    # === GESTION DES ÉVÉNEMENTS ===

    def create_personal_event(
        self, event_data: PersonalEventCreateSchema
    ) -> PersonalEvent:
        """
        Crée un nouvel événement personnel.

        Args:
            event_data: Données de l'événement à créer

        Returns:
            PersonalEvent: Événement créé
        """
        genealogy = self.genealogy

        # Vérifier que la personne existe
        person = self.get_person(event_data.person_id)
        if person is None:
            raise ValueError(f"Personne avec l'ID {event_data.person_id} non trouvée")

        # Création de l'événement
        event = PersonalEvent(
            event_type=event_data.event_type,
            date=None,  # TODO: Parser les dates
            place=event_data.place,
            notes=[event_data.note] if event_data.note else [],
            witnesses=event_data.witnesses or [],
        )

        # Ajout à la personne
        person.events.append(event)
        genealogy.metadata.modified_date = datetime.now()

        return event

    def create_family_event(self, event_data: FamilyEventCreateSchema) -> FamilyEvent:
        """
        Crée un nouvel événement familial.

        Args:
            event_data: Données de l'événement à créer

        Returns:
            FamilyEvent: Événement créé
        """
        genealogy = self.genealogy

        # Vérifier que la famille existe
        family = self.get_family(event_data.family_id)
        if family is None:
            raise ValueError(f"Famille avec l'ID {event_data.family_id} non trouvée")

        # Création de l'événement
        event = FamilyEvent(
            event_type=event_data.event_type,
            date=None,  # TODO: Parser les dates
            place=event_data.place,
            reason=event_data.reason,
            notes=event_data.notes,
            witnesses=event_data.witnesses or [],
            sources=event_data.sources or [],
        )

        # Ajout à la famille
        family.events.append(event)
        genealogy.metadata.modified_date = datetime.now()

        return event

    def get_event(self, event_id: str) -> Optional[Event]:
        """
        Récupère un événement par son ID.

        Args:
            event_id: Identifiant de l'événement

        Returns:
            Event: Événement trouvé ou None
        """
        genealogy = self.genealogy

        # Recherche dans les événements personnels
        for person in genealogy.persons.values():
            for event in person.events:
                if hasattr(event, "unique_id") and event.unique_id == event_id:
                    return event

        # Recherche dans les événements familiaux
        for family in genealogy.families.values():
            for event in family.events:
                if hasattr(event, "unique_id") and event.unique_id == event_id:
                    return event

        return None

    def update_event(
        self, event_id: str, event_data: EventUpdateSchema
    ) -> Optional[Event]:
        """
        Met à jour un événement.

        Args:
            event_id: Identifiant de l'événement
            event_data: Nouvelles données

        Returns:
            Event: Événement mis à jour ou None si non trouvé
        """
        genealogy = self.genealogy
        event = self.get_event(event_id)

        if event is None:
            return None

        # Mise à jour des champs fournis
        if event_data.event_type is not None:
            event.event_type = event_data.event_type
        if event_data.place is not None:
            event.place = event_data.place
        if event_data.reason is not None:
            event.reason = event_data.reason
        if event_data.notes is not None:
            event.notes = event_data.notes
        if event_data.witnesses is not None:
            event.witnesses = event_data.witnesses
        if event_data.sources is not None:
            event.sources = event_data.sources

        genealogy.metadata.modified_date = datetime.now()
        return event

    def delete_event(self, event_id: str) -> bool:
        """
        Supprime un événement.

        Args:
            event_id: Identifiant de l'événement

        Returns:
            bool: True si supprimé, False si non trouvé
        """
        genealogy = self.genealogy

        # Recherche et suppression dans les événements personnels
        for person in genealogy.persons.values():
            for i, event in enumerate(person.events):
                if hasattr(event, "unique_id") and event.unique_id == event_id:
                    del person.events[i]
                    genealogy.metadata.modified_date = datetime.now()
                    return True

        # Recherche et suppression dans les événements familiaux
        for family in genealogy.families.values():
            for i, event in enumerate(family.events):
                if hasattr(event, "unique_id") and event.unique_id == event_id:
                    del family.events[i]
                    genealogy.metadata.modified_date = datetime.now()
                    return True

        return False

    def search_events(self, search_params: Dict[str, Any]) -> Tuple[List[Event], int]:
        """
        Recherche des événements selon les critères.

        Args:
            search_params: Paramètres de recherche

        Returns:
            Tuple[List[Event], int]: (Événements trouvés, nombre total)
        """
        genealogy = self.genealogy
        events = []

        # Collecte de tous les événements
        for person in genealogy.persons.values():
            events.extend(person.events)

        for family in genealogy.families.values():
            events.extend(family.events)

        # Filtrage par critères
        if search_params.get("query"):
            query_lower = search_params["query"].lower()
            events = [
                e
                for e in events
                if (
                    query_lower in (e.place or "").lower()
                    or query_lower in (e.reason or "").lower()
                    or query_lower in (e.notes or "").lower()
                )
            ]

        if search_params.get("event_type"):
            events = [e for e in events if e.event_type == search_params["event_type"]]

        if search_params.get("person_id"):
            events = [
                e
                for e in events
                if hasattr(e, "person_id") and e.person_id == search_params["person_id"]
            ]

        if search_params.get("family_id"):
            events = [
                e
                for e in events
                if hasattr(e, "family_id") and e.family_id == search_params["family_id"]
            ]

        if search_params.get("place"):
            events = [
                e
                for e in events
                if search_params["place"].lower() in (e.place or "").lower()
            ]

        if search_params.get("has_witnesses") is not None:
            if search_params["has_witnesses"]:
                events = [e for e in events if len(e.witnesses) > 0]
            else:
                events = [e for e in events if len(e.witnesses) == 0]

        if search_params.get("has_sources") is not None:
            if search_params["has_sources"]:
                events = [e for e in events if len(e.sources) > 0]
            else:
                events = [e for e in events if len(e.sources) == 0]

        total = len(events)

        # Pagination
        page = search_params.get("page", 1)
        size = search_params.get("size", 20)
        start = (page - 1) * size
        end = start + size
        events = events[start:end]

        return events, total

    # === VALIDATION ===

    def validate_genealogy(self, strict: bool = False) -> Dict[str, Any]:
        """
        Valide la cohérence des références personnes/familles.

        Args:
            strict: Si True, met à jour ``is_valid`` et ``validation_errors`` sur
                l'objet ``Genealogy`` lorsque des erreurs sont trouvées (liste
                remplacée à chaque passe en mode strict).

        Returns:
            Dictionnaire sérialisable pour l'API (erreurs, indicateur de validité).

        Note:
            En mode non strict (défaut pour l'endpoint HTTP), les erreurs sont
            uniquement retournées sans modifier l'état de validation stocké.
        """
        genealogy = self.genealogy
        errors_list = genealogy.validate_consistency(strict=strict)
        error_payloads = [err.to_dict() for err in errors_list]
        suggestions: List[str] = []
        if error_payloads:
            suggestions.append(
                "Vérifiez que chaque identifiant cité dans une famille existe "
                "parmi les personnes chargées."
            )
        return {
            "is_valid": len(error_payloads) == 0,
            "warnings": [],
            "errors": error_payloads,
            "suggestions": suggestions,
        }

    # === STATISTIQUES ===

    def get_stats(self) -> Dict[str, Any]:
        """
        Récupère les statistiques de la généalogie.

        Returns:
            Dict[str, Any]: Statistiques détaillées
        """
        genealogy = self.genealogy

        # Statistiques des personnes
        persons_by_sex = {}
        persons_by_access = {}
        persons_with_birth_date = 0
        persons_with_death_date = 0

        for person in genealogy.persons.values():
            # Par sexe
            sex_key = person.gender.value if person.gender else "unknown"
            persons_by_sex[sex_key] = persons_by_sex.get(sex_key, 0) + 1

            # Par niveau d'accès
            access_key = person.access_level.value if person.access_level else "default"
            persons_by_access[access_key] = persons_by_access.get(access_key, 0) + 1

            # Dates
            if person.birth_date:
                persons_with_birth_date += 1
            if person.death_date:
                persons_with_death_date += 1

        # Statistiques des familles
        families_by_status = {}
        families_with_children = 0
        total_children = 0

        for family in genealogy.families.values():
            # Par statut
            status_key = (
                family.marriage_status.value if family.marriage_status else "married"
            )
            families_by_status[status_key] = families_by_status.get(status_key, 0) + 1

            # Enfants
            if len(family.children) > 0:
                families_with_children += 1
            total_children += len(family.children)

        # Statistiques des événements (collectés depuis les personnes et familles)
        events_by_type = {}
        personal_events = 0
        family_events = 0

        # Compter les événements personnels
        for person in genealogy.persons.values():
            for event in person.events:
                type_key = event.event_type.value if event.event_type else "unknown"
                events_by_type[type_key] = events_by_type.get(type_key, 0) + 1
                personal_events += 1

        # Compter les événements familiaux
        for family in genealogy.families.values():
            for event in family.events:
                type_key = event.event_type.value if event.event_type else "unknown"
                events_by_type[type_key] = events_by_type.get(type_key, 0) + 1
                family_events += 1

        base_stats = {
            "total_persons": len(genealogy.persons),
            "total_families": len(genealogy.families),
            "total_events": personal_events + family_events,
            "persons_by_sex": persons_by_sex,
            "persons_by_access_level": persons_by_access,
            "persons_with_birth_date": persons_with_birth_date,
            "persons_with_death_date": persons_with_death_date,
            "families_by_status": families_by_status,
            "families_with_children": families_with_children,
            "average_children_per_family": (
                total_children / len(genealogy.families) if genealogy.families else 0
            ),
            "events_by_type": events_by_type,
            "personal_events": personal_events,
            "family_events": family_events,
            "metadata": {
                "source_file": genealogy.metadata.source_file,
                "created": (
                    genealogy.metadata.created_date.isoformat()
                    if genealogy.metadata.created_date
                    else None
                ),
                "updated": (
                    genealogy.metadata.modified_date.isoformat()
                    if genealogy.metadata.modified_date
                    else None
                ),
                "version": genealogy.metadata.geneweb_version,
                "encoding": genealogy.metadata.encoding,
            },
        }
        base_stats["advanced"] = _build_advanced_genealogy_stats(genealogy)
        return base_stats


def _person_year_in_range(
    date_val: Optional[Date],
    year_from: Optional[int],
    year_to: Optional[int],
) -> bool:
    """Indique si au moins une année candidate chevauche ``[year_from, year_to]``.

    Pour les dates OR (``|``) ou BETWEEN (``..``), les années du segment principal
    et des ``alternative_dates`` sont prises en compte (chevauchement / overlap).
    """
    if year_from is None and year_to is None:
        return True
    if date_val is None:
        return False
    years = date_val.filter_years_for_range()
    if not years:
        return False
    for year in years:
        if year_from is not None and year < year_from:
            continue
        if year_to is not None and year > year_to:
            continue
        return True
    return False


def _normalize_place_fragment(text: str) -> str:
    """Normalisation NFKC + casefold pour comparaison de lieux."""
    return unicodedata.normalize("NFKC", text).casefold()


def _person_matches_place(person: Person, needle_normalized: str) -> bool:
    """Vérifie si ``needle_normalized`` est une sous-chaîne d'un lieu connu.

    Comparaison naive après NFKC et casefold (pas de collation locale).
    """
    fields = (
        person.birth_place,
        person.death_place,
        person.baptism_place,
        person.burial_place,
    )
    for raw in fields:
        if raw and needle_normalized in _normalize_place_fragment(raw):
            return True
    return False


def _build_advanced_genealogy_stats(genealogy: Genealogy) -> Dict[str, Any]:
    """Construit des statistiques complémentaires.

    Inclut longévité (âge au décès), répartition géographique (lieux fréquents)
    et distribution des tailles de famille (histogramme du nombre d'enfants).
    """
    persons = list(genealogy.persons.values())
    ages_at_death: List[int] = []
    for p in persons:
        if p.age_at_death is not None:
            ages_at_death.append(int(p.age_at_death))

    longevity: Dict[str, Any] = {
        "count_with_age_at_death": len(ages_at_death),
        "average_age_at_death": None,
        "min_age_at_death": None,
        "max_age_at_death": None,
    }
    if ages_at_death:
        longevity["average_age_at_death"] = sum(ages_at_death) / len(ages_at_death)
        longevity["min_age_at_death"] = min(ages_at_death)
        longevity["max_age_at_death"] = max(ages_at_death)

    birth_places = _top_places_from_persons(persons, "birth_place", limit=15)
    death_places = _top_places_from_persons(persons, "death_place", limit=15)

    child_counts = [len(f.children) for f in genealogy.families.values()]
    distribution: Dict[str, int] = {"0": 0, "1": 0, "2": 0, "3": 0, "4+": 0}
    for n in child_counts:
        if n <= 3:
            distribution[str(n)] += 1
        else:
            distribution["4+"] += 1

    family_sizes: Dict[str, Any] = {
        "max_children_per_family": max(child_counts) if child_counts else 0,
        "min_children_per_family": min(child_counts) if child_counts else 0,
        "children_per_family_histogram": distribution,
    }

    return {
        "longevity": longevity,
        "geography": {
            "distinct_birth_places": len(
                {
                    (p.birth_place or "").strip().lower()
                    for p in persons
                    if p.birth_place and str(p.birth_place).strip()
                }
            ),
            "top_birth_places": birth_places,
            "top_death_places": death_places,
        },
        "family_sizes": family_sizes,
    }


def _top_places_from_persons(
    persons: List[Person], attr: str, limit: int
) -> List[Dict[str, Any]]:
    """Agrège les lieux les plus fréquents pour l'attribut ``attr`` sur ``Person``."""
    counts: Dict[str, int] = {}
    label_for_key: Dict[str, str] = {}
    for person in persons:
        raw = getattr(person, attr, None)
        if raw is None:
            continue
        place = str(raw).strip()
        if not place:
            continue
        key = place.lower()
        counts[key] = counts.get(key, 0) + 1
        if key not in label_for_key:
            label_for_key[key] = place
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [
        {"place": label_for_key[key], "count": count} for key, count in ordered[:limit]
    ]
