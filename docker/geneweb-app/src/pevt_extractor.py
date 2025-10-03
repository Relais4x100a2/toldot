"""
Extracteur et classificateur de PEVT personnalisés
"""
from typing import List, Dict, Tuple
from collections import Counter
from .data_models import PEVTRaw
from .gw_parser import extract_custom_pevts


class PEVTExtractor:
    """Extracteur intelligent de PEVT personnalisés"""
    
    def __init__(self):
        self.all_pevts: List[PEVTRaw] = []
        self.stats: Dict = {}
    
    def load_from_file(self, file_path: str) -> None:
        """Charge les PEVT depuis un fichier .gw"""
        self.all_pevts = extract_custom_pevts(file_path)
        self._compute_stats()
    
    def _compute_stats(self) -> None:
        """Calcule des statistiques sur les PEVT"""
        event_types = [pevt.event_tag for pevt in self.all_pevts]
        
        self.stats = {
            'total_pevts': len(self.all_pevts),
            'unique_event_types': len(set(event_types)),
            'event_type_distribution': dict(Counter(event_types)),
            'with_date': sum(1 for p in self.all_pevts if p.date),
            'with_place': sum(1 for p in self.all_pevts if p.place),
            'with_witnesses': sum(1 for p in self.all_pevts if p.witnesses),
            'with_notes': sum(1 for p in self.all_pevts if p.notes),
        }
    
    def get_diverse_sample(self, n: int = 30) -> List[PEVTRaw]:
        """
        Sélectionne un échantillon diversifié de PEVT
        Stratégie: prendre des exemples de chaque type d'événement
        """
        if not self.all_pevts:
            return []
        
        # Grouper par type d'événement
        by_type: Dict[str, List[PEVTRaw]] = {}
        for pevt in self.all_pevts:
            if pevt.event_tag not in by_type:
                by_type[pevt.event_tag] = []
            by_type[pevt.event_tag].append(pevt)
        
        # Calculer combien prendre de chaque type
        num_types = len(by_type)
        per_type = max(1, n // num_types)
        
        sample = []
        for event_type, pevts in by_type.items():
            # Prendre les premiers de chaque type
            sample.extend(pevts[:per_type])
            if len(sample) >= n:
                break
        
        return sample[:n]
    
    def get_sample_by_type(self, event_type: str, n: int = 10) -> List[PEVTRaw]:
        """Récupère un échantillon d'un type d'événement spécifique"""
        filtered = [p for p in self.all_pevts if p.event_tag == event_type]
        return filtered[:n]
    
    def get_all_event_types(self) -> List[Tuple[str, int]]:
        """Retourne tous les types d'événements avec leur fréquence"""
        return sorted(
            self.stats['event_type_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        )
