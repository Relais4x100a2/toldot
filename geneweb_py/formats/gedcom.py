"""
Convertisseur GEDCOM pour geneweb-py.

Ce module fournit les fonctionnalités d'export et d'import vers/depuis
le format GEDCOM (Genealogical Data Communication), un standard
international pour l'échange de données généalogiques.
"""

from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime

from .base import BaseExporter, BaseImporter, ConversionError
from ..core.genealogy import Genealogy
from ..core.person import Person
from ..core.family import Family
from ..core.event import Event
from ..core.date import Date


class GEDCOMExporter(BaseExporter):
    """Exporteur vers le format GEDCOM."""
    
    def __init__(self, encoding: str = "utf-8", version: str = "5.5.1"):
        """
        Initialise l'exporteur GEDCOM.
        
        Args:
            encoding: Encodage à utiliser (défaut: utf-8)
            version: Version GEDCOM à utiliser (défaut: 5.5.1)
        """
        super().__init__(encoding)
        self.version = version
        self._person_ids: Dict[Person, str] = {}
        self._family_ids: Dict[Family, str] = {}
        self._next_person_id = 1
        self._next_family_id = 1
    
    def export(self, genealogy: Genealogy, output_path: Union[str, Path]) -> None:
        """
        Exporte une généalogie vers un fichier GEDCOM.
        
        Args:
            genealogy: Objet Genealogy à exporter
            output_path: Chemin du fichier de sortie
            
        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        self._validate_genealogy(genealogy)
        
        try:
            gedcom_content = self.export_to_string(genealogy)
            
            with open(output_path, 'w', encoding=self.encoding) as f:
                f.write(gedcom_content)
                
        except Exception as e:
            raise ConversionError(f"Erreur lors de l'export GEDCOM : {e}")
    
    def export_to_string(self, genealogy: Genealogy) -> str:
        """
        Exporte une généalogie vers une chaîne GEDCOM.
        
        Args:
            genealogy: Objet Genealogy à exporter
            
        Returns:
            Chaîne GEDCOM formatée
            
        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        self._validate_genealogy(genealogy)
        
        # Réinitialiser les compteurs
        self._person_ids.clear()
        self._family_ids.clear()
        self._next_person_id = 1
        self._next_family_id = 1
        
        lines = []
        
        # En-tête GEDCOM
        lines.extend(self._generate_header())
        
        # Assigner des IDs aux personnes et familles
        for person in genealogy.persons.values():
            person_id = f"I{self._next_person_id:04d}"
            self._person_ids[person.unique_id] = person_id
            self._next_person_id += 1
        
        for family in genealogy.families.values():
            family_id = f"F{self._next_family_id:04d}"
            self._family_ids[family.family_id] = family_id
            self._next_family_id += 1
        
        # Exporter les personnes
        for person in genealogy.persons.values():
            lines.extend(self._export_person(person))
        
        # Exporter les familles
        for family in genealogy.families.values():
            lines.extend(self._export_family(family))
        
        # Trailer
        lines.append("0 TRLR")
        
        return "\n".join(lines)
    
    def _generate_header(self) -> List[str]:
        """Génère l'en-tête GEDCOM."""
        lines = []
        lines.append("0 HEAD")
        lines.append("1 GEDC")
        lines.append("2 VERS 5.5.1")
        lines.append("2 FORM LINEAGE-LINKED")
        lines.append("1 CHAR UTF-8")
        lines.append("1 SOUR geneweb-py")
        lines.append("2 VERS 1.0.0")
        lines.append("2 NAME geneweb-py")
        lines.append("2 CORP geneweb-py")
        lines.append("1 DATE")
        lines.append(f"2 TIME {datetime.now().strftime('%H:%M:%S')}")
        lines.append(f"2 DATE {datetime.now().strftime('%d %b %Y')}")
        lines.append("1 FILE")
        lines.append("1 GEDC")
        lines.append("2 VERS 5.5.1")
        lines.append("2 FORM LINEAGE-LINKED")
        return lines
    
    def _export_person(self, person: Person) -> List[str]:
        """Exporte une personne vers le format GEDCOM."""
        lines = []
        person_id = self._person_ids[person.unique_id]
        
        lines.append(f"0 {person_id} INDI")
        
        # Nom
        if person.last_name or person.first_name:
            lines.append("1 NAME")
            name_parts = []
            if person.first_name:
                name_parts.append(person.first_name)
            if person.last_name:
                name_parts.append(f"/{person.last_name}/")
            lines.append(f"2 GIVN {person.first_name or ''}")
            lines.append(f"2 SURN {person.last_name or ''}")
        
        # Sexe
        if person.gender:
            sex_code = "M" if person.gender.value == "m" else "F"
            lines.append(f"1 SEX {sex_code}")
        
        # Date de naissance
        if person.birth_date:
            birth_lines = self._export_date(person.birth_date, "BIRT")
            lines.extend(birth_lines)
        
        # Lieu de naissance
        if person.birth_place:
            lines.append("1 BIRT")
            lines.append(f"2 PLAC {person.birth_place}")
        
        # Date de décès
        if person.death_date:
            death_lines = self._export_date(person.death_date, "DEAT")
            lines.extend(death_lines)
        
        # Lieu de décès
        if person.death_place:
            lines.append("1 DEAT")
            lines.append(f"2 PLAC {person.death_place}")
        
        # Titres et professions
        if person.titles:
            for title in person.titles:
                lines.append(f"1 TITL {title.name}")
        
        if person.occupation:
            lines.append(f"1 OCCU {person.occupation}")
        
        # Notes
        if person.notes:
            lines.append("1 NOTE")
            for note in person.notes:
                lines.append(f"2 CONT {note}")
        
        # Événements personnels
        if person.events:
            for event in person.events:
                if event.event_type:
                    event_lines = self._export_event(event)
                    lines.extend(event_lines)
        
        return lines
    
    def _export_event(self, event: Event) -> List[str]:
        """Exporte un événement vers le format GEDCOM."""
        lines = []
        
        # Mapper le type d'événement vers le tag GEDCOM
        event_tag = self._map_event_type(event.event_type.value)
        
        lines.append(f"1 {event_tag}")
        
        # Date
        if event.date:
            date_lines = self._export_date(event.date, "")
            lines.extend(date_lines)
        
        # Lieu
        if event.place:
            lines.append(f"2 PLAC {event.place}")
        
        # Notes
        if event.notes:
            for note in event.notes:
                lines.append(f"2 NOTE {note}")
        
        return lines
    
    def _export_family(self, family: Family) -> List[str]:
        """Exporte une famille vers le format GEDCOM."""
        lines = []
        family_id = self._family_ids[family.family_id]
        
        lines.append(f"0 {family_id} FAM")
        
        # Époux
        if family.husband_id:
            lines.append(f"1 HUSB {family.husband_id}")
        
        # Épouse
        if family.wife_id:
            lines.append(f"1 WIFE {family.wife_id}")
        
        # Enfants
        for child in family.children:
            lines.append(f"1 CHIL {child.person_id}")
        
        # Événements familiaux
        for event in family.events:
            event_lines = self._export_event(event)
            lines.extend(event_lines)
        
        return lines
    
    def _export_event(self, event: Event) -> List[str]:
        """Exporte un événement vers le format GEDCOM."""
        lines = []
        
        # Mapper les types d'événements GeneWeb vers GEDCOM
        gedcom_type = self._map_event_type(event.event_type.value if event.event_type else "")
        if gedcom_type:
            lines.append(f"1 {gedcom_type}")
            
            if event.date:
                date_lines = self._export_date(event.date, gedcom_type)
                lines.extend(date_lines)
            
            if event.place:
                lines.append(f"2 PLAC {event.place}")
            
            if event.notes:
                for note in event.notes:
                    lines.append(f"2 NOTE {note}")
        
        return lines
    
    def _export_date(self, date: Date, event_type: str) -> List[str]:
        """Exporte une date vers le format GEDCOM."""
        lines = []
        
        if date.year:
            gedcom_date = self._format_gedcom_date(date)
            lines.append(f"2 DATE {gedcom_date}")
        
        return lines
    
    def _format_gedcom_date(self, date: Date) -> str:
        """Formate une date au format GEDCOM."""
        parts = []
        
        if date.day:
            parts.append(str(date.day))
        if date.month:
            month_names = [
                "", "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
                "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"
            ]
            parts.append(month_names[date.month])
        if date.year:
            parts.append(str(date.year))
        
        return " ".join(parts)
    
    def _map_event_type(self, event_type: str) -> Optional[str]:
        """Mappe un type d'événement GeneWeb vers GEDCOM."""
        mapping = {
            "birth": "BIRT",
            "death": "DEAT",
            "marriage": "MARR",
            "divorce": "DIV",
            "baptism": "BAPM",
            "burial": "BURI",
            "confirmation": "CONF",
            "graduation": "GRAD",
            "grad": "GRAD",  # Alias pour EventType.GRADUATION.value
            "immigration": "IMMI",
            "emigration": "EMIG",
            "naturalization": "NATU",
            "occupation": "OCCU",
            "residence": "RESI",
        }
        return mapping.get(event_type.lower())


class GEDCOMImporter(BaseImporter):
    """Importeur depuis le format GEDCOM."""
    
    def __init__(self, encoding: str = "utf-8"):
        """
        Initialise l'importeur GEDCOM.
        
        Args:
            encoding: Encodage à utiliser (défaut: utf-8)
        """
        super().__init__(encoding)
        self._person_map: Dict[str, Person] = {}
        self._family_map: Dict[str, Family] = {}
    
    def import_from_file(self, input_path: Union[str, Path]) -> Genealogy:
        """
        Importe une généalogie depuis un fichier GEDCOM.
        
        Args:
            input_path: Chemin du fichier à importer
            
        Returns:
            Objet Genealogy importé
            
        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        path = self._validate_file_path(input_path)
        
        try:
            with open(path, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            return self.import_from_string(content)
            
        except Exception as e:
            raise ConversionError(f"Erreur lors de l'import GEDCOM : {e}")
    
    def import_from_string(self, data: str) -> Genealogy:
        """
        Importe une généalogie depuis une chaîne GEDCOM.
        
        Args:
            data: Chaîne GEDCOM à importer
            
        Returns:
            Objet Genealogy importé
            
        Raises:
            ConversionError: En cas d'erreur de conversion
        """
        try:
            # Réinitialiser les maps
            self._person_map.clear()
            self._family_map.clear()
            
            # Parser le contenu GEDCOM
            lines = data.strip().split('\n')
            genealogy = Genealogy()
            
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                if not line:
                    i += 1
                    continue
                
                # Parser les en-têtes et métadonnées
                if line.startswith("0 HEAD"):
                    i = self._parse_header(lines, i)
                elif line.startswith("0 ") and " INDI" in line:
                    person, i = self._parse_individual(lines, i)
                    if person:
                        genealogy.add_person(person)
                elif line.startswith("0 ") and " FAM" in line:
                    family, i = self._parse_family(lines, i)
                    if family:
                        genealogy.add_family(family)
                else:
                    i += 1
            
            return genealogy
            
        except Exception as e:
            raise ConversionError(f"Erreur lors du parsing GEDCOM : {e}")
    
    def _parse_header(self, lines: List[str], start_idx: int) -> int:
        """Parse l'en-tête GEDCOM."""
        i = start_idx + 1
        while i < len(lines) and not lines[i].startswith("0 "):
            i += 1
        return i
    
    def _parse_individual(self, lines: List[str], start_idx: int) -> tuple[Optional[Person], int]:
        """Parse un individu GEDCOM."""
        # Cette implémentation est simplifiée
        # Dans une version complète, il faudrait parser tous les champs
        i = start_idx + 1
        return None, i
    
    def _parse_family(self, lines: List[str], start_idx: int) -> tuple[Optional[Family], int]:
        """Parse une famille GEDCOM."""
        # Cette implémentation est simplifiée
        # Dans une version complète, il faudrait parser tous les champs
        i = start_idx + 1
        return None, i
