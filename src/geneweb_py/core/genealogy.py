"""
Modèle Genealogy : conteneur principal des données généalogiques

Ce module définit la classe principale qui regroupe toutes les personnes,
familles et métadonnées d'une base généalogique GeneWeb.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .exceptions import GeneWebError, GeneWebValidationError
from .family import Family
from .person import Person


@dataclass
class GenealogyMetadata:
    """Métadonnées de la base généalogique"""

    # Informations sur le fichier source
    source_file: Optional[str] = None
    encoding: str = "iso-8859-1"
    is_gwplus: bool = False

    # Informations de création
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    geneweb_version: Optional[str] = None

    # Notes de base de données
    database_notes: List[str] = field(default_factory=list)

    # Pages étendues
    extended_pages: Dict[str, str] = field(default_factory=dict)

    # Notes de wizard
    wizard_notes: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class Genealogy:
    """Conteneur principal pour toutes les données généalogiques

    Cette classe regroupe les personnes, familles et métadonnées
    d'une base généalogique GeneWeb complète.
    """

    # Collections principales
    persons: Dict[str, Person] = field(default_factory=dict)
    families: Dict[str, Family] = field(default_factory=dict)

    # Métadonnées
    metadata: GenealogyMetadata = field(default_factory=GenealogyMetadata)

    # Validation gracieuse
    is_valid: bool = field(default=True)
    validation_errors: List[GeneWebError] = field(default_factory=list)

    # Statistiques (calculées automatiquement)
    _stats_cache: Dict[str, Any] = field(default_factory=dict, init=False)

    def __post_init__(self):
        """Validation et initialisation après création"""
        # Mettre à jour les références croisées
        self._update_cross_references()

        # Calculer les statistiques
        self._calculate_stats()

    def add_person(self, person: Person) -> None:
        """Ajoute une personne à la généalogie

        Args:
            person: Personne à ajouter

        Raises:
            GeneWebValidationError: Si la personne existe déjà
        """
        person_id = person.unique_id

        if person_id in self.persons:
            raise GeneWebValidationError(
                f"Personne '{person_id}' déjà présente dans la généalogie"
            )

        self.persons[person_id] = person
        self._invalidate_stats_cache()

    def add_or_update_person(self, person: Person) -> Person:
        """Ajoute une personne ou met à jour si elle existe déjà

        Cette méthode gère intelligemment les cas où une personne apparaît
        plusieurs fois dans le fichier GeneWeb (comme témoin, dans des notes, etc.).
        Si la personne existe déjà, les informations sont fusionnées.

        Args:
            person: Personne à ajouter ou mettre à jour

        Returns:
            La personne ajoutée ou mise à jour (référence existante si doublon)
        """
        person_id = person.unique_id

        if person_id in self.persons:
            # La personne existe déjà, fusionner les informations
            existing = self.persons[person_id]

            # Fusionner le sexe (priorité au sexe connu)
            from .person import Gender

            if person.gender != Gender.UNKNOWN and existing.gender == Gender.UNKNOWN:
                existing.gender = person.gender

            # Fusionner les informations si la nouvelle personne a plus de détails
            if person.birth_date and not existing.birth_date:
                existing.birth_date = person.birth_date
            if person.birth_place and not existing.birth_place:
                existing.birth_place = person.birth_place
            if person.death_date and not existing.death_date:
                existing.death_date = person.death_date
            if person.death_place and not existing.death_place:
                existing.death_place = person.death_place
            if person.baptism_date and not existing.baptism_date:
                existing.baptism_date = person.baptism_date
            if person.baptism_place and not existing.baptism_place:
                existing.baptism_place = person.baptism_place
            if person.occupation and not existing.occupation:
                existing.occupation = person.occupation
            if person.public_name and not existing.public_name:
                existing.public_name = person.public_name
            if person.nickname and not existing.nickname:
                existing.nickname = person.nickname

            # Fusionner les événements (éviter les doublons)
            for event in person.events:
                if event not in existing.events:
                    existing.events.append(event)

            # Fusionner les notes
            for note in person.notes:
                if note not in existing.notes:
                    existing.notes.append(note)

            # Fusionner les sources spécifiques
            if person.birth_source and not existing.birth_source:
                existing.birth_source = person.birth_source
            if person.death_source and not existing.death_source:
                existing.death_source = person.death_source
            if person.baptism_source and not existing.baptism_source:
                existing.baptism_source = person.baptism_source
            if person.burial_source and not existing.burial_source:
                existing.burial_source = person.burial_source
            if person.person_source and not existing.person_source:
                existing.person_source = person.person_source

            return existing
        else:
            # Nouvelle personne, l'ajouter
            self.persons[person_id] = person
            self._invalidate_stats_cache()
            return person

    def add_family(self, family: Family) -> None:
        """Ajoute une famille à la généalogie

        Args:
            family: Famille à ajouter

        Raises:
            GeneWebValidationError: Si la famille existe déjà
        """
        if family.family_id in self.families:
            raise GeneWebValidationError(
                f"Famille '{family.family_id}' déjà présente dans la généalogie"
            )

        self.families[family.family_id] = family
        self._invalidate_stats_cache()

    def find_person(
        self, last_name: str, first_name: str, occurrence: int = 0
    ) -> Optional[Person]:
        """Recherche une personne par nom

        Args:
            last_name: Nom de famille
            first_name: Prénom
            occurrence: Numéro d'occurrence (0 par défaut)

        Returns:
            Personne trouvée ou None
        """
        person_id = f"{last_name}_{first_name}_{occurrence}"
        return self.persons.get(person_id)

    def find_person_by_id(self, person_id: str) -> Optional[Person]:
        """Recherche une personne par ID unique

        Args:
            person_id: ID unique de la personne

        Returns:
            Personne trouvée ou None
        """
        return self.persons.get(person_id)

    def find_family(self, family_id: str) -> Optional[Family]:
        """Recherche une famille par ID

        Args:
            family_id: ID de la famille

        Returns:
            Famille trouvée ou None
        """
        return self.families.get(family_id)

    def get_families_for_person(self, person_id: str) -> List[Family]:
        """Retourne toutes les familles d'une personne

        Args:
            person_id: ID de la personne

        Returns:
            Liste des familles (comme parent ou enfant)
        """
        families = []

        for family in self.families.values():
            if family.is_member(person_id):
                families.append(family)

        return families

    def get_children(self, person_id: str) -> List[Person]:
        """Retourne tous les enfants d'une personne

        Args:
            person_id: ID de la personne

        Returns:
            Liste des enfants
        """
        children = []

        for family in self.families.values():
            if family.is_parent(person_id):
                for child_id in family.child_ids:
                    child = self.find_person_by_id(child_id)
                    if child:
                        children.append(child)

        return children

    def get_parents(self, person_id: str) -> List[Person]:
        """Retourne les parents d'une personne

        Args:
            person_id: ID de la personne

        Returns:
            Liste des parents (père et/ou mère)
        """
        parents = []

        for family in self.families.values():
            if family.is_child(person_id):
                for parent_id in family.spouse_ids:
                    parent = self.find_person_by_id(parent_id)
                    if parent:
                        parents.append(parent)
                break  # Une personne n'a qu'une seule famille parentale

        return parents

    def get_siblings(self, person_id: str) -> List[Person]:
        """Retourne les frères et sœurs d'une personne

        Args:
            person_id: ID de la personne

        Returns:
            Liste des frères et sœurs
        """
        siblings = []

        for family in self.families.values():
            if family.is_child(person_id):
                for sibling_id in family.child_ids:
                    if sibling_id != person_id:
                        sibling = self.find_person_by_id(sibling_id)
                        if sibling:
                            siblings.append(sibling)
                break

        return siblings

    def get_spouses(self, person_id: str) -> List[Person]:
        """Retourne tous les conjoints d'une personne

        Args:
            person_id: ID de la personne

        Returns:
            Liste des conjoints
        """
        spouses = []

        for family in self.families.values():
            if family.is_parent(person_id):
                spouse_id = family.spouse(person_id)
                if spouse_id:
                    spouse = self.find_person_by_id(spouse_id)
                    if spouse:
                        spouses.append(spouse)

        return spouses

    def validate_consistency(self, strict: bool = True) -> List[GeneWebValidationError]:
        """Valide la cohérence des données généalogiques

        Args:
            strict: Si True, met à jour is_valid en fonction des erreurs trouvées

        Returns:
            Liste des erreurs de validation trouvées
        """
        errors = []

        # Vérifier les références de personnes dans les familles
        for family in self.families.values():
            # Vérifier les époux
            if family.husband_id and family.husband_id not in self.persons:
                errors.append(
                    GeneWebValidationError(
                        f"Époux '{family.husband_id}' de la famille '{family.family_id}' non trouvé"  # noqa: E501
                    )
                )

            if family.wife_id and family.wife_id not in self.persons:
                errors.append(
                    GeneWebValidationError(
                        f"Épouse '{family.wife_id}' de la famille '{family.family_id}' non trouvée"  # noqa: E501
                    )
                )

            # Vérifier les enfants
            for child_id in family.child_ids:
                if child_id not in self.persons:
                    errors.append(
                        GeneWebValidationError(
                            f"Enfant '{child_id}' de la famille '{family.family_id}' non trouvé"  # noqa: E501
                        )
                    )

        # Vérifier les références de familles dans les personnes
        for person in self.persons.values():
            for family_id in person.get_families():
                if family_id not in self.families:
                    errors.append(
                        GeneWebValidationError(
                            f"Famille '{family_id}' référencée par '{person.unique_id}' non trouvée"  # noqa: E501
                        )
                    )

        # Mettre à jour les attributs de validation
        if strict and errors:
            self.is_valid = False
            self.validation_errors.extend(errors)

        return errors

    def add_validation_error(self, error: GeneWebError) -> None:
        """Ajoute une erreur de validation à la généalogie

        Args:
            error: L'erreur à ajouter
        """
        self.validation_errors.append(error)
        self.is_valid = False

    def clear_validation_errors(self) -> None:
        """Efface toutes les erreurs de validation"""
        self.validation_errors.clear()
        self.is_valid = True

    def get_validation_summary(self) -> str:
        """Retourne un résumé des erreurs de validation

        Returns:
            Résumé textuel des erreurs
        """
        if self.is_valid:
            return "Généalogie valide"

        from .exceptions import ErrorSeverity

        # Compter par sévérité
        by_severity = {
            ErrorSeverity.WARNING: 0,
            ErrorSeverity.ERROR: 0,
            ErrorSeverity.CRITICAL: 0,
        }

        for error in self.validation_errors:
            by_severity[error.severity] += 1

        parts = []
        if by_severity[ErrorSeverity.WARNING] > 0:
            parts.append(f"{by_severity[ErrorSeverity.WARNING]} avertissement(s)")
        if by_severity[ErrorSeverity.ERROR] > 0:
            parts.append(f"{by_severity[ErrorSeverity.ERROR]} erreur(s)")
        if by_severity[ErrorSeverity.CRITICAL] > 0:
            parts.append(f"{by_severity[ErrorSeverity.CRITICAL]} erreur(s) critique(s)")

        return f"Généalogie avec erreurs: {', '.join(parts)}"

    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques de la généalogie

        Returns:
            Dictionnaire contenant diverses statistiques
        """
        if not self._stats_cache:
            self._calculate_stats()

        return self._stats_cache.copy()

    def _calculate_stats(self) -> None:
        """Calcule et met en cache les statistiques"""
        stats = {
            "total_persons": len(self.persons),
            "total_families": len(self.families),
            "living_persons": sum(1 for p in self.persons.values() if p.is_alive),
            "deceased_persons": sum(1 for p in self.persons.values() if not p.is_alive),
            "unknown_status_persons": sum(
                1 for p in self.persons.values() if p.is_deceased is None
            ),
            "persons_with_birth_date": sum(
                1 for p in self.persons.values() if p.birth_date
            ),
            "persons_with_death_date": sum(
                1 for p in self.persons.values() if p.death_date
            ),
            "families_with_children": sum(
                1 for f in self.families.values() if f.children
            ),
            "total_children": sum(len(f.children) for f in self.families.values()),
        }

        # Statistiques par sexe
        stats["male_persons"] = sum(
            1 for p in self.persons.values() if p.gender.value == "m"
        )
        stats["female_persons"] = sum(
            1 for p in self.persons.values() if p.gender.value == "f"
        )
        stats["unknown_gender_persons"] = sum(
            1 for p in self.persons.values() if p.gender.value == "?"
        )

        # Âges
        ages = []
        for person in self.persons.values():
            if person.age_at_death is not None:
                ages.append(person.age_at_death)

        if ages:
            stats["average_age_at_death"] = sum(ages) / len(ages)
            stats["oldest_death"] = max(ages)
            stats["youngest_death"] = min(ages)

        self._stats_cache = stats

    def _invalidate_stats_cache(self) -> None:
        """Invalide le cache des statistiques"""
        self._stats_cache = {}

    def _update_cross_references(self) -> None:
        """Met à jour les références croisées entre personnes et familles"""
        # Mettre à jour les références des personnes vers les familles
        for person in self.persons.values():
            person.families_as_child.clear()
            person.families_as_spouse.clear()

        for family in self.families.values():
            # Mettre à jour les références des époux
            if family.husband_id:
                husband = self.find_person_by_id(family.husband_id)
                if husband:
                    husband.families_as_spouse.append(family.family_id)

            if family.wife_id:
                wife = self.find_person_by_id(family.wife_id)
                if wife:
                    wife.families_as_spouse.append(family.family_id)

            # Mettre à jour les références des enfants
            for child_id in family.child_ids:
                child = self.find_person_by_id(child_id)
                if child:
                    child.families_as_child.append(family.family_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convertit la généalogie en dictionnaire pour sérialisation"""
        return {
            "metadata": {
                "source_file": self.metadata.source_file,
                "encoding": self.metadata.encoding,
                "is_gwplus": self.metadata.is_gwplus,
                "database_notes": self.metadata.database_notes,
                "extended_pages": self.metadata.extended_pages,
            },
            "persons": {pid: person.to_dict() for pid, person in self.persons.items()},
            "families": {
                fid: family.to_dict() for fid, family in self.families.items()
            },
            "statistics": self.get_statistics(),
            "validation": {
                "is_valid": self.is_valid,
                "error_count": len(self.validation_errors),
                "errors": [e.to_dict() for e in self.validation_errors],
            },
        }

    def __len__(self) -> int:
        """Retourne le nombre total de personnes"""
        return len(self.persons)

    def __str__(self) -> str:
        """Représentation string de la généalogie"""
        stats = self.get_statistics()
        return f"Genealogy({stats['total_persons']} personnes, {stats['total_families']} familles)"  # noqa: E501

    def __repr__(self) -> str:
        """Représentation pour debug"""
        return f"Genealogy(persons={len(self.persons)}, families={len(self.families)})"
