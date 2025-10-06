"""
Service de test pour l'API geneweb-py.

Ce module fournit un service de test avec isolation des données
pour les tests d'intégration.
"""

from typing import Dict, Any, Optional
from geneweb_py.api.services.genealogy_service import GenealogyService
from geneweb_py.core.models import Genealogy, Person, Family, Event


class TestGenealogyService(GenealogyService):
    """Service de test avec isolation des données."""
    
    def __init__(self):
        """Initialise le service de test."""
        super().__init__()
        self._test_data: Dict[str, Any] = {}
        self._reset_test_data()
    
    def _reset_test_data(self) -> None:
        """Remet à zéro les données de test."""
        self._test_data = {
            'persons': {},
            'families': {},
            'events': {}
        }
        # Réinitialiser la généalogie
        self._genealogy = self._create_empty_genealogy()
    
    def _create_empty_genealogy(self) -> Genealogy:
        """Crée une généalogie vide pour les tests."""
        from geneweb_py.core.genealogy import Genealogy, GenealogyMetadata
        from datetime import datetime
        
        metadata = GenealogyMetadata(
            source_file=None,
            encoding="utf-8",
            is_gwplus=False,
            created_date=datetime.now(),
            modified_date=datetime.now(),
            geneweb_version="1.0"
        )
        
        return Genealogy(
            persons={},
            families={},
            metadata=metadata
        )
    
    def create_person(self, person_data):
        """Crée une personne dans les données de test."""
        # Créer la personne directement dans notre généalogie de test
        from geneweb_py.core.person import Person, Title
        from geneweb_py.core.models import Gender, AccessLevel
        
        # Conversion des titres
        titles = []
        for title_data in person_data.titles:
            title = Title(
                name=title_data.name,
                title_type=title_data.title_type,
                place=title_data.place,
                start_date=None,
                end_date=None,
                number=title_data.number,
                is_main=title_data.is_main
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
            notes=[]
        )
        
        # Ajouter à la généalogie de test
        self._genealogy.add_person(person)
        self._test_data['persons'][person.unique_id] = person
        
        
        return person
    
    def get_person(self, person_id: str) -> Optional[Person]:
        """Récupère une personne depuis les données de test."""
        person = self._genealogy.find_person_by_id(person_id)
        return person
    
    def create_family(self, family_data):
        """Crée une famille dans les données de test."""
        family = super().create_family(family_data)
        self._test_data['families'][family.family_id] = family
        # Ajouter à la généalogie principale
        self._genealogy.add_family(family)
        return family
    
    def get_family(self, family_id: str) -> Optional[Family]:
        """Récupère une famille depuis les données de test."""
        return self._genealogy.find_family(family_id)
    
    def create_personal_event(self, event_data):
        """Crée un événement personnel dans les données de test."""
        # Vérifier que la personne existe
        person = self.get_person(event_data.person_id)
        if not person:
            raise ValueError(f"Personne avec l'ID {event_data.person_id} non trouvée")
        
        # Créer l'événement
        event = super().create_personal_event(event_data)
        # Utiliser l'ID unique de l'événement
        event_id = f"{event_data.person_id}_{event.event_type}_{len(person.events)}"
        self._test_data['events'][event_id] = event
        
        # L'événement est déjà ajouté par super().create_personal_event
        # Ne pas l'ajouter à nouveau
        
        return event
    
    def get_event(self, event_id: str) -> Optional[Event]:
        """Récupère un événement depuis les données de test."""
        return self._test_data['events'].get(event_id)
    
    def get_persons(self, page: int = 1, size: int = 20, **filters):
        """Récupère les personnes depuis les données de test."""
        persons = list(self._genealogy.persons.values())
        total = len(persons)
        
        # Pagination
        start = (page - 1) * size
        end = start + size
        paginated_persons = persons[start:end]
        
        return paginated_persons, total
    
    def get_families(self, page: int = 1, size: int = 20, **filters):
        """Récupère les familles depuis les données de test."""
        families = list(self._genealogy.families.values())
        total = len(families)
        
        # Pagination
        start = (page - 1) * size
        end = start + size
        paginated_families = families[start:end]
        
        return paginated_families, total
    
    def get_events(self, page: int = 1, size: int = 20, **filters):
        """Récupère les événements depuis les données de test."""
        events = list(self._test_data['events'].values())
        total = len(events)
        
        # Pagination
        start = (page - 1) * size
        end = start + size
        paginated_events = events[start:end]
        
        return paginated_events, total
    
    def get_stats(self):
        """Récupère les statistiques depuis les données de test."""
        return {
            'total_persons': len(self._genealogy.persons),
            'total_families': len(self._genealogy.families),
            'total_events': len(self._test_data['events']),
            'persons_by_sex': {'male': 0, 'female': 0},
            'persons_by_access_level': {'public': 0, 'private': 0},
            'families_by_status': {'married': 0, 'divorced': 0},
            'events_by_type': {'birth': 0, 'death': 0},
            'average_children_per_family': 0.0,
            'metadata': {
                'source_file': None,
                'created': None,
                'updated': None,
                'version': '1.0',
                'encoding': 'utf-8'
            }
        }
    
    def search(self, query: str, limit: int = 50):
        """Recherche dans les données de test."""
        results = {
            'persons': [],
            'families': [],
            'events': []
        }
        
        # Recherche dans les personnes
        for person in self._genealogy.persons.values():
            if (query.lower() in person.first_name.lower() or 
                query.lower() in person.last_name.lower()):
                results['persons'].append(person)
        
        # Recherche dans les familles
        for family in self._genealogy.families.values():
            if family.family_id and query.lower() in family.family_id.lower():
                results['families'].append(family)
        
        # Recherche dans les événements
        for event in self._test_data['events'].values():
            if (hasattr(event, 'place') and event.place and 
                query.lower() in event.place.lower()):
                results['events'].append(event)
        
        total_results = len(results['persons']) + len(results['families']) + len(results['events'])
        
        return {
            'results': results,
            'total_results': total_results,
            'query': query
        }
    
    def reset(self) -> None:
        """Remet à zéro toutes les données de test."""
        self._reset_test_data()
