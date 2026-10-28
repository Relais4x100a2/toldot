"""
Parser de fichiers .gw (format GeneWeb)

Ce parser extrait uniquement les événements PEVT non standardisés (#strng)
qui nécessitent une reformulation en texte libre pour être compréhensibles.

Les événements déjà standardisés selon la documentation GeneWeb sont ignorés.
Chaque événement individuel est traité séparément avec ses propres notes, témoins, etc.
"""
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from .data_models import PEVTRaw


class GWParser:
    """Parser pour les fichiers .gw"""
    
    def __init__(self):
        self.current_line = 0
        self.content = []
    
    def parse_file(self, file_path: str) -> Dict[str, any]:
        """Parse un fichier .gw et extrait toutes les informations"""
        with open(file_path, 'r', encoding='utf-8') as f:
            self.content = f.readlines()
        
        return {
            'encoding': self._get_encoding(),
            'persons': self._extract_persons(),
            'families': self._extract_families(),
            'pevts': self._extract_pevts(),
            'fevts': self._extract_fevts(),
        }
    
    def _get_encoding(self) -> str:
        """Récupère l'encodage déclaré"""
        if self.content and 'encoding:' in self.content[0]:
            return self.content[0].split(':')[1].strip()
        return 'utf-8'
    
    def _extract_pevts(self) -> List[PEVTRaw]:
        """Extrait tous les blocs pevt du fichier"""
        all_pevts = []
        i = 0
        
        while i < len(self.content):
            line = self.content[i].strip()
            
            # Détection d'un bloc pevt
            if line.startswith('pevt '):
                pevt_events = self._parse_pevt_block(i)
                all_pevts.extend(pevt_events)  # Étendre la liste avec tous les événements
                i = self._find_end_pevt(i)  # Sauter à la fin du bloc
            i += 1
        
        return all_pevts
    
    def _find_end_pevt(self, start_line: int) -> int:
        """Trouve la ligne 'end pevt' correspondante"""
        i = start_line + 1
        while i < len(self.content):
            if self.content[i].strip() == 'end pevt':
                return i
            i += 1
        return len(self.content) - 1
    
    def _parse_pevt_block(self, start_line: int) -> List[PEVTRaw]:
        """Parse un bloc pevt et retourne une liste d'événements non standardisés"""
        header = self.content[start_line].strip()
        
        # Extraction du nom et prénom depuis "pevt SURNAME Name"
        match = re.match(r'pevt\s+(\S+)\s+([\S_]+)', header)
        if not match:
            return []
        
        surname = match.group(1)
        name = match.group(2).replace('_', ' ')
        
        # Lecture du contenu du bloc jusqu'à "end pevt"
        i = start_line + 1
        raw_text_lines = [header]
        events = []
        current_event = None
        
        while i < len(self.content):
            line = self.content[i].strip()
            raw_text_lines.append(self.content[i].rstrip())
            
            if line == 'end pevt':
                break
            
            # Extraction des événements (lignes commençant par #)
            if line.startswith('#'):
                # Sauvegarder l'événement précédent s'il existe
                if current_event:
                    events.append(current_event)
                
                event_match = re.match(r'#(\S+)\s*(.*)', line)
                if event_match:
                    event_tag = event_match.group(1)
                    event_data = event_match.group(2)
                    
                    # Créer un nouvel événement
                    current_event = {
                        'tag': event_tag,
                        'data': event_data,
                        'line': line,
                        'witnesses': [],
                        'notes': [],
                        'sources': []
                    }
            
            # Extraction des témoins pour l'événement courant UNIQUEMENT
            elif line.startswith('wit ') and current_event:
                current_event['witnesses'].append(line)
            
            # Extraction des notes pour l'événement courant UNIQUEMENT
            elif line.startswith('note ') and current_event:
                current_event['notes'].append(line[5:])
            
            # Extraction des sources pour l'événement courant UNIQUEMENT
            elif '#src' in line and current_event:
                src_match = re.search(r'#src\s+(\S+)', line)
                if src_match:
                    current_event['sources'].append(src_match.group(1))
            
            i += 1
        
        # Ajouter le dernier événement
        if current_event:
            events.append(current_event)
        
        # Liste complète des tags standardisés selon la documentation GeneWeb
        standard_tags = {
            'birt', 'bapt', 'deat', 'buri', 'crem', 'acco', 'acqu', 'adhe', 
            'bapl', 'barm', 'basm', 'bles', 'cens', 'chgn', 'circ', 'conf', 
            'conl', 'degr', 'awar', 'demm', 'dist', 'endl', 'dotl', 'educ', 
            'elec', 'emig', 'exco', 'flkl', 'fcom', 'fune', 'grad', 'hosp', 
            'illn', 'immi', 'lpas', 'mdis', 'mpro', 'mser', 'mobm', 'natu', 
            'occu', 'ordn', 'prop', 'resi', 'reti', 'slgc', 'slgp', 'slgs', 
            'vteb', 'will', 'marr', 'bapm'
        }
        
        # Créer un PEVTRaw pour chaque événement non standardisé
        raw_text = '\n'.join(raw_text_lines)
        strng_events = []
        
        for event in events:
            if event['tag'] not in standard_tags:
                # C'est un événement non standardisé qui nécessite une annotation
                strng_events.append(PEVTRaw(
                    person_name=name,
                    person_surname=surname,
                    event_tag=event['tag'],
                    date=self._extract_date(event['data']),
                    place=self._extract_place(event['data']),
                    raw_text=raw_text,
                    witnesses=event['witnesses'],  # Témoins spécifiques à cet événement
                    notes=event['notes'],  # Notes spécifiques à cet événement
                    sources=event['sources'],  # Sources spécifiques à cet événement
                    line_number=i
                ))
        
        return strng_events
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extrait une date d'une chaîne"""
        # Recherche de motifs de date
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # JJ/MM/AAAA
            r'\d{4}',  # AAAA
            r'~\d{4}',  # ~AAAA (approximation)
            r'\d{4}\.\.\d{4}',  # AAAA..AAAA (période)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_place(self, text: str) -> Optional[str]:
        """Extrait un lieu d'une chaîne"""
        # Recherche de #p suivi du lieu
        match = re.search(r'#p\s+([^#]+)', text)
        if match:
            return match.group(1).strip()
        return None
    
    def _extract_persons(self) -> List[Dict]:
        """Extrait la liste des personnes (à implémenter si nécessaire)"""
        return []
    
    def _extract_families(self) -> List[Dict]:
        """Extrait la liste des familles (à implémenter si nécessaire)"""
        return []
    
    def _extract_fevts(self) -> List[Dict]:
        """Extrait les événements familiaux (à implémenter si nécessaire)"""
        return []


def extract_custom_pevts(file_path: str) -> List[PEVTRaw]:
    """
    Fonction utilitaire pour extraire uniquement les PEVT non standardisés (#strng)
    
    Ces événements sont ceux qui ne correspondent pas aux tags standardisés de GeneWeb
    et nécessitent une reformulation en texte libre pour être exploitables.
    """
    parser = GWParser()
    data = parser.parse_file(file_path)
    return data['pevts']
