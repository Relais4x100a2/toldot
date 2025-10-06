"""
Modèle Genealogy : conteneur principal des données généalogiques

Ce module définit la classe principale qui regroupe toutes les personnes,
familles et métadonnées d'une base généalogique GeneWeb.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from datetime import datetime

from .person import Person
from .family import Family
from .exceptions import GeneWebValidationError


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
    
    def find_person(self, last_name: str, first_name: str, occurrence: int = 0) -> Optional[Person]:
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
    
    def validate_consistency(self) -> List[GeneWebValidationError]:
        """Valide la cohérence des données généalogiques
        
        Returns:
            Liste des erreurs de validation trouvées
        """
        errors = []
        
        # Vérifier les références de personnes dans les familles
        for family in self.families.values():
            # Vérifier les époux
            if family.husband_id and family.husband_id not in self.persons:
                errors.append(GeneWebValidationError(
                    f"Époux '{family.husband_id}' de la famille '{family.family_id}' non trouvé"
                ))
            
            if family.wife_id and family.wife_id not in self.persons:
                errors.append(GeneWebValidationError(
                    f"Épouse '{family.wife_id}' de la famille '{family.family_id}' non trouvée"
                ))
            
            # Vérifier les enfants
            for child_id in family.child_ids:
                if child_id not in self.persons:
                    errors.append(GeneWebValidationError(
                        f"Enfant '{child_id}' de la famille '{family.family_id}' non trouvé"
                    ))
        
        # Vérifier les références de familles dans les personnes
        for person in self.persons.values():
            for family_id in person.get_families():
                if family_id not in self.families:
                    errors.append(GeneWebValidationError(
                        f"Famille '{family_id}' référencée par '{person.unique_id}' non trouvée"
                    ))
        
        return errors
    
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
            'total_persons': len(self.persons),
            'total_families': len(self.families),
            'living_persons': sum(1 for p in self.persons.values() if p.is_alive),
            'deceased_persons': sum(1 for p in self.persons.values() if not p.is_alive),
            'unknown_status_persons': sum(1 for p in self.persons.values() if p.is_deceased is None),
            'persons_with_birth_date': sum(1 for p in self.persons.values() if p.birth_date),
            'persons_with_death_date': sum(1 for p in self.persons.values() if p.death_date),
            'families_with_children': sum(1 for f in self.families.values() if f.children),
            'total_children': sum(len(f.children) for f in self.families.values()),
        }
        
        # Statistiques par sexe
        stats['male_persons'] = sum(1 for p in self.persons.values() if p.gender.value == 'm')
        stats['female_persons'] = sum(1 for p in self.persons.values() if p.gender.value == 'f')
        stats['unknown_gender_persons'] = sum(1 for p in self.persons.values() if p.gender.value == '?')
        
        # Âges
        ages = []
        for person in self.persons.values():
            if person.age_at_death is not None:
                ages.append(person.age_at_death)
        
        if ages:
            stats['average_age_at_death'] = sum(ages) / len(ages)
            stats['oldest_death'] = max(ages)
            stats['youngest_death'] = min(ages)
        
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
            'metadata': {
                'source_file': self.metadata.source_file,
                'encoding': self.metadata.encoding,
                'is_gwplus': self.metadata.is_gwplus,
                'database_notes': self.metadata.database_notes,
                'extended_pages': self.metadata.extended_pages,
            },
            'persons': {pid: person.to_dict() for pid, person in self.persons.items()},
            'families': {fid: family.to_dict() for fid, family in self.families.items()},
            'statistics': self.get_statistics()
        }
    
    def __len__(self) -> int:
        """Retourne le nombre total de personnes"""
        return len(self.persons)
    
    def __str__(self) -> str:
        """Représentation string de la généalogie"""
        stats = self.get_statistics()
        return f"Genealogy({stats['total_persons']} personnes, {stats['total_families']} familles)"
    
    def __repr__(self) -> str:
        """Représentation pour debug"""
        return f"Genealogy(persons={len(self.persons)}, families={len(self.families)})"
