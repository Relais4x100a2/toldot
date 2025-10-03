"""
Parser de fichiers .gw (format GeneWeb)
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
        pevts = []
        i = 0
        
        while i < len(self.content):
            line = self.content[i].strip()
            
            # Détection d'un bloc pevt
            if line.startswith('pevt '):
                pevt_data = self._parse_pevt_block(i)
                if pevt_data:
                    pevts.append(pevt_data)
                    i = pevt_data.line_number  # Sauter à la fin du bloc
            i += 1
        
        return pevts
    
    def _parse_pevt_block(self, start_line: int) -> Optional[PEVTRaw]:
        """Parse un bloc pevt individuel"""
        header = self.content[start_line].strip()
        
        # Extraction du nom et prénom depuis "pevt SURNAME Name"
        match = re.match(r'pevt\s+(\S+)\s+([\S_]+)', header)
        if not match:
            return None
        
        surname = match.group(1)
        name = match.group(2).replace('_', ' ')
        
        # Lecture du contenu du bloc jusqu'à "end pevt"
        i = start_line + 1
        raw_text_lines = [header]
        witnesses = []
        notes = []
        sources = []
        events = []
        
        while i < len(self.content):
            line = self.content[i].strip()
            raw_text_lines.append(self.content[i].rstrip())
            
            if line == 'end pevt':
                break
            
            # Extraction des événements (lignes commençant par #)
            if line.startswith('#'):
                event_match = re.match(r'#(\S+)\s*(.*)', line)
                if event_match:
                    event_tag = event_match.group(1)
                    event_data = event_match.group(2)
                    events.append({
                        'tag': event_tag,
                        'data': event_data,
                        'line': line
                    })
            
            # Extraction des témoins
            elif line.startswith('wit '):
                witnesses.append(line)
            
            # Extraction des notes
            elif line.startswith('note '):
                notes.append(line[5:])
            
            # Extraction des sources
            elif '#src' in line:
                src_match = re.search(r'#src\s+(\S+)', line)
                if src_match:
                    sources.append(src_match.group(1))
            
            i += 1
        
        # Créer un PEVTRaw pour chaque événement personnalisé
        # Pour l'instant, on retourne le premier événement personnalisé trouvé
        raw_text = '\n'.join(raw_text_lines)
        
        # Identifier les événements personnalisés (non-standard)
        custom_events = []
        standard_tags = {'birt', 'deat', 'marr', 'bapm', 'buri', 'resi', 'occu', 'educ', 'grad'}
        
        for event in events:
            if event['tag'] not in standard_tags:
                # C'est un événement personnalisé
                custom_events.append(PEVTRaw(
                    person_name=name,
                    person_surname=surname,
                    event_tag=event['tag'],
                    date=self._extract_date(event['data']),
                    place=self._extract_place(event['data']),
                    raw_text=raw_text,
                    witnesses=witnesses,
                    notes=notes,
                    sources=sources,
                    line_number=i
                ))
        
        # Si pas d'événements personnalisés, retourner None
        # Si plusieurs, retourner le premier (on pourra itérer plus tard)
        if custom_events:
            return custom_events[0]
        
        return None
    
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
    Fonction utilitaire pour extraire uniquement les PEVT personnalisés
    """
    parser = GWParser()
    data = parser.parse_file(file_path)
    return data['pevts']
