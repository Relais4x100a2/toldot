"""
Exceptions spécifiques pour la librairie geneweb-py

Ce module définit les exceptions personnalisées utilisées dans toute la librairie
pour une gestion d'erreur claire et spécifique au format GeneWeb.
"""

from typing import Optional, List, Dict, Any


class GeneWebError(Exception):
    """Exception de base pour toutes les erreurs GeneWeb"""
    
    def __init__(self, message: str, line_number: Optional[int] = None, **kwargs):
        self.message = message
        self.line_number = line_number
        self.context = kwargs
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur avec le numéro de ligne si disponible"""
        if self.line_number:
            return f"Ligne {self.line_number}: {self.message}"
        return self.message


class GeneWebParseError(GeneWebError):
    """Erreur lors du parsing d'un fichier .gw
    
    Cette exception est levée quand le parser rencontre une erreur de syntaxe
    ou une structure invalide dans le fichier .gw.
    """
    
    def __init__(
        self, 
        message: str, 
        line_number: Optional[int] = None,
        token: Optional[str] = None,
        expected: Optional[str] = None,
        **kwargs
    ):
        self.token = token
        self.expected = expected
        super().__init__(message, line_number, **kwargs)
    
    def _format_message(self) -> str:
        """Formate le message d'erreur de parsing"""
        parts = []
        
        if self.line_number:
            parts.append(f"Ligne {self.line_number}")
        
        parts.append(self.message)
        
        if self.token:
            parts.append(f"Token rencontré: '{self.token}'")
        
        if self.expected:
            parts.append(f"Attendu: {self.expected}")
        
        return ": ".join(parts)


class GeneWebValidationError(GeneWebError):
    """Erreur de validation des données généalogiques
    
    Cette exception est levée quand les données parsées ne respectent pas
    les règles de cohérence généalogique.
    """
    
    def __init__(
        self, 
        message: str, 
        line_number: Optional[int] = None,
        person_id: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        **kwargs
    ):
        self.person_id = person_id
        self.validation_errors = validation_errors or []
        super().__init__(message, line_number, **kwargs)
    
    def _format_message(self) -> str:
        """Formate le message d'erreur de validation"""
        parts = []
        
        if self.line_number:
            parts.append(f"Ligne {self.line_number}")
        
        if self.person_id:
            parts.append(f"Personne {self.person_id}")
        
        parts.append(self.message)
        
        if self.validation_errors:
            parts.append("Erreurs détaillées:")
            for error in self.validation_errors:
                parts.append(f"  - {error}")
        
        return "\n".join(parts)


class GeneWebConversionError(GeneWebError):
    """Erreur lors de la conversion vers un autre format
    
    Cette exception est levée quand la conversion vers GEDCOM, JSON ou autre
    format échoue.
    """
    
    def __init__(
        self, 
        message: str, 
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        **kwargs
    ):
        self.source_format = source_format
        self.target_format = target_format
        super().__init__(message, **kwargs)
    
    def _format_message(self) -> str:
        """Formate le message d'erreur de conversion"""
        if self.source_format and self.target_format:
            return f"Erreur de conversion {self.source_format} → {self.target_format}: {self.message}"
        return self.message


class GeneWebEncodingError(GeneWebError):
    """Erreur d'encodage lors de la lecture d'un fichier .gw"""
    
    def __init__(
        self, 
        message: str, 
        detected_encoding: Optional[str] = None,
        attempted_encoding: Optional[str] = None,
        **kwargs
    ):
        self.detected_encoding = detected_encoding
        self.attempted_encoding = attempted_encoding
        super().__init__(message, **kwargs)
    
    def _format_message(self) -> str:
        """Formate le message d'erreur d'encodage"""
        parts = [self.message]
        
        if self.detected_encoding:
            parts.append(f"Encodage détecté: {self.detected_encoding}")
        
        if self.attempted_encoding:
            parts.append(f"Encodage tenté: {self.attempted_encoding}")
        
        return " - ".join(parts)
