"""
Modèle Date pour le format GeneWeb

Ce module implémente la représentation et le parsing des dates dans le format .gw,
avec support des calendriers multiples, préfixes et dates textuelles.
"""

from dataclasses import dataclass, field
from typing import Optional, Union, List
from enum import Enum
import re

# Regex précompilée pour les dates textuelles 0(texte)
TEXT_DATE_RE = re.compile(r'^0\((.+)\)$')


class DatePrefix(Enum):
    """Préfixes de date supportés par GeneWeb"""
    ABOUT = "~"  # ~10/5/1990
    MAYBE = "?"  # ?10/5/1990
    BEFORE = "<"  # <10/5/1990
    AFTER = ">"  # >10/5/1990
    OR = "|"  # 10/5/1990|1991
    BETWEEN = ".."  # 10/5/1990..1991


class CalendarType(Enum):
    """Types de calendriers supportés"""
    GREGORIAN = ""  # Par défaut
    JULIAN = "J"  # Julien
    FRENCH_REPUBLICAN = "F"  # Républicain français
    HEBREW = "H"  # Hébreu


class DeathType(Enum):
    """Types de décès avec préfixes spéciaux"""
    NORMAL = ""  # Normal
    KILLED = "k"  # Tué
    MURDERED = "m"  # Assassiné
    EXECUTED = "e"  # Exécuté
    DISAPPEARED = "s"  # Disparu


@dataclass
class Date:
    """Représentation d'une date dans le format GeneWeb
    
    Supporte les formats européens (dd/mm/yyyy), les préfixes (~, ?, <, >),
    les calendriers multiples et les dates textuelles.
    """
    
    # Composants de date
    day: Optional[int] = None
    month: Optional[int] = None
    year: Optional[int] = None
    
    # Préfixes et modificateurs
    prefix: Optional[DatePrefix] = None
    calendar: CalendarType = CalendarType.GREGORIAN
    
    # Dates alternatives (pour OR et BETWEEN)
    alternative_dates: List['Date'] = field(default_factory=list)
    
    # Date textuelle (format 0(5_Mai_1990))
    text_date: Optional[str] = None
    
    # Type de décès (pour les dates de décès)
    death_type: DeathType = DeathType.NORMAL
    
    # Date inconnue mais obligatoire
    is_unknown: bool = False
    
    def __post_init__(self):
        """Validation et normalisation après initialisation"""
        if self.is_unknown:
            self.day = self.month = self.year = None
            self.text_date = None
        
        # Validation de cohérence
        if self.day is not None and (self.day < 1 or self.day > 31):
            raise ValueError(f"Jour invalide: {self.day}")
        
        if self.month is not None and (self.month < 1 or self.month > 12):
            raise ValueError(f"Mois invalide: {self.month}")
        
        if self.year is not None and self.year < 1:
            raise ValueError(f"Année invalide: {self.year}")
    
    @property
    def is_complete(self) -> bool:
        """Vérifie si la date est complète (jour, mois, année)"""
        return all(x is not None for x in [self.day, self.month, self.year])
    
    @property
    def is_partial(self) -> bool:
        """Vérifie si la date est partielle (mois/année ou année seulement)"""
        if self.is_unknown or self.text_date:
            return False
        return self.year is not None and (self.day is None or self.month is None)
    
    @property
    def display_text(self) -> str:
        """Retourne la représentation textuelle de la date"""
        if self.text_date:
            return f"0({self.text_date})"
        
        if self.is_unknown:
            return "0"
        
        parts = []
        
        # Ajouter le préfixe (sauf pour OR et BETWEEN qui sont gérés séparément)
        if self.prefix and self.prefix not in [DatePrefix.OR, DatePrefix.BETWEEN]:
            parts.append(self.prefix.value)
        
        # Ajouter le type de décès
        if self.death_type != DeathType.NORMAL:
            parts.append(self.death_type.value)
        
        # Construire la date
        date_parts = []
        if self.day:
            date_parts.append(f"{self.day:02d}")
        if self.month:
            date_parts.append(f"{self.month:02d}")
        if self.year:
            date_parts.append(f"{self.year:04d}")
        
        if date_parts:
            date_str = "/".join(date_parts)
            parts.append(date_str)
        
        # Ajouter le calendrier
        if self.calendar != CalendarType.GREGORIAN:
            parts.append(self.calendar.value)
        
        # Ajouter les dates alternatives
        if self.alternative_dates:
            if self.prefix == DatePrefix.OR:
                # Pour OR, construire la chaîne avec le séparateur |
                alt_texts = [alt.display_text for alt in self.alternative_dates]
                parts.append("|".join(alt_texts))
            elif self.prefix == DatePrefix.BETWEEN:
                if self.alternative_dates:
                    parts.append(f"..{self.alternative_dates[0].year}")
        
        result = "".join(parts)
        
        # Pour OR, reconstruire la chaîne avec le bon format
        if self.prefix == DatePrefix.OR and self.alternative_dates:
            main_date = "".join(parts[:-1])  # Tous sauf la dernière partie
            alt_texts = [alt.display_text for alt in self.alternative_dates]
            result = f"{main_date}|{'|'.join(alt_texts)}"
        
        return result
    
    def to_iso_format(self) -> Optional[str]:
        """Convertit la date au format ISO (YYYY-MM-DD) si possible"""
        if not self.is_complete or self.is_unknown:
            return None
        
        return f"{self.year:04d}-{self.month:02d}-{self.day:02d}"
    
    @classmethod
    def parse(cls, date_str: Optional[str]) -> 'Date':
        """Parse une chaîne de date au format GeneWeb
        
        Args:
            date_str: Chaîne de date à parser (ex: "25/12/1990", "~10/5/1990", "0(5_Mai_1990)")
        
        Returns:
            Instance de Date parsée
        
        Raises:
            ValueError: Si la date ne peut pas être parsée
        """
        # Support None → date inconnue
        if date_str is None:
            return cls(is_unknown=True)
        
        # Nettoyer la chaîne de date; si vide ⇒ date inconnue
        date_str = date_str.strip()

        # Support des dates vides (ex: "#deat" sans date) → date inconnue
        if date_str == "":
            return cls(is_unknown=True)
        
        # Date inconnue
        if date_str == "0":
            return cls(is_unknown=True)
        
        # Date textuelle (0(texte))
        text_match = TEXT_DATE_RE.match(date_str)
        if text_match:
            return cls(text_date=text_match.group(1))
        
        # Parser les préfixes et modificateurs
        prefix = None
        death_type = DeathType.NORMAL
        calendar = CalendarType.GREGORIAN
        
        # Vérifier les préfixes
        if date_str.startswith("~"):
            prefix = DatePrefix.ABOUT
            date_str = date_str[1:]
        elif date_str.startswith("?"):
            prefix = DatePrefix.MAYBE
            date_str = date_str[1:]
        elif date_str.startswith("<"):
            prefix = DatePrefix.BEFORE
            date_str = date_str[1:]
        elif date_str.startswith(">"):
            prefix = DatePrefix.AFTER
            date_str = date_str[1:]
        
        # Vérifier les types de décès
        if date_str.startswith("k"):
            death_type = DeathType.KILLED
            date_str = date_str[1:]
        elif date_str.startswith("m"):
            death_type = DeathType.MURDERED
            date_str = date_str[1:]
        elif date_str.startswith("e"):
            death_type = DeathType.EXECUTED
            date_str = date_str[1:]
        elif date_str.startswith("s"):
            death_type = DeathType.DISAPPEARED
            date_str = date_str[1:]
        
        # Vérifier le calendrier
        if date_str.endswith("J"):
            calendar = CalendarType.JULIAN
            date_str = date_str[:-1]
        elif date_str.endswith("F"):
            calendar = CalendarType.FRENCH_REPUBLICAN
            date_str = date_str[:-1]
        elif date_str.endswith("H"):
            calendar = CalendarType.HEBREW
            date_str = date_str[:-1]
        
        # Parser les dates avec OR ou BETWEEN
        alternative_dates = []
        if "|" in date_str:
            prefix = DatePrefix.OR
            parts = date_str.split("|")
            date_str = parts[0]
            for part in parts[1:]:
                alt_date = cls.parse(part.strip())
                alternative_dates.append(alt_date)
        elif ".." in date_str:
            prefix = DatePrefix.BETWEEN
            parts = date_str.split("..")
            date_str = parts[0]
            if len(parts) > 1:
                # Pour BETWEEN, on stocke juste l'année de fin
                end_year = int(parts[1])
                alternative_dates.append(cls(year=end_year))
        
        # Parser la date principale avec gestion des champs vides
        if "/" in date_str:
            parts = date_str.split("/")
            
            # Filtrer les parties vides et convertir en entiers
            def safe_int(value):
                """Convertit une chaîne en entier, retourne None si vide ou invalide"""
                if not value or value.strip() == "":
                    return None
                try:
                    return int(value.strip())
                except ValueError:
                    return None
            
            if len(parts) == 3:
                day, month, year = map(safe_int, parts)
                
                # Si tous les champs sont vides, c'est une date inconnue
                if day is None and month is None and year is None:
                    return cls(is_unknown=True)
                
                return cls(
                    day=day, month=month, year=year,
                    prefix=prefix, calendar=calendar,
                    alternative_dates=alternative_dates,
                    death_type=death_type
                )
            elif len(parts) == 2:
                month, year = map(safe_int, parts)
                
                # Si les deux champs sont vides, c'est une date inconnue
                if month is None and year is None:
                    return cls(is_unknown=True)
                
                return cls(
                    month=month, year=year,
                    prefix=prefix, calendar=calendar,
                    alternative_dates=alternative_dates,
                    death_type=death_type
                )
        elif date_str.isdigit():
            # Année seulement
            year = int(date_str)
            return cls(
                year=year,
                prefix=prefix, calendar=calendar,
                alternative_dates=alternative_dates,
                death_type=death_type
            )
        
        # Si on arrive ici et que la chaîne n'est pas vide, c'est un format non reconnu
        # Mais on peut essayer de parser comme année si c'est numérique
        if date_str.replace("-", "").replace(".", "").isdigit():
            try:
                year = int(float(date_str))
                return cls(
                    year=year,
                    prefix=prefix, calendar=calendar,
                    alternative_dates=alternative_dates,
                    death_type=death_type
                )
            except ValueError:
                pass
        
        raise ValueError(f"Format de date non reconnu: {date_str}")
    
    @classmethod
    def parse_with_fallback(cls, date_str: str) -> 'Date':
        """Parse une date avec gestion gracieuse des erreurs
        
        Args:
            date_str: Chaîne de date à parser
            
        Returns:
            Instance de Date parsée ou date inconnue en cas d'erreur
        """
        try:
            return cls.parse(date_str)
        except ValueError:
            # En cas d'erreur, retourner une date inconnue
            return cls(is_unknown=True)
    
    def __str__(self) -> str:
        """Représentation string de la date"""
        return self.display_text
    
    def __repr__(self) -> str:
        """Représentation pour debug"""
        return f"Date('{self.display_text}')"
