"""
Exceptions spécifiques pour la librairie geneweb-py

Ce module définit les exceptions personnalisées utilisées dans toute la librairie
pour une gestion d'erreur claire et spécifique au format GeneWeb.
"""

from typing import Optional, List, Dict, Any


class GeneWebError(Exception):
    """Exception de base pour toutes les erreurs GeneWeb"""
    
    def __init__(self, message: str, line_number: Optional[int] = None, context: Optional[str] = None, **kwargs):
        self.message = message
        self.line_number = line_number
        self.context = context
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
        expected_token: Optional[str] = None,
        actual_token: Optional[str] = None,
        column: Optional[int] = None,
        context: Optional[str] = None,
        cause: Optional[Exception] = None,
        **kwargs
    ):
        self.token = token
        self.expected_token = expected_token
        self.actual_token = actual_token
        self.column = column
        self.cause = cause
        super().__init__(message, line_number, context, **kwargs)
    
    def _format_message(self) -> str:
        """Formate le message d'erreur de parsing"""
        parts = []
        
        if self.line_number:
            parts.append(f"Ligne {self.line_number}")
        
        parts.append(self.message)
        
        if self.token:
            parts.append(f"Token rencontré: '{self.token}'")
        
        if self.expected_token:
            parts.append(f"Attendu: {self.expected_token}")
        
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
        field: Optional[str] = None,
        value: Optional[Any] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[str] = None,
        person_id: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
        **kwargs
    ):
        self.field = field
        self.value = value
        self.entity_type = entity_type
        self.entity_id = entity_id
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
        data_type: Optional[str] = None,
        data_value: Optional[str] = None,
        causes: Optional[List[Exception]] = None,
        **kwargs
    ):
        self.source_format = source_format
        self.target_format = target_format
        self.data_type = data_type
        self.data_value = data_value
        self.causes = causes or []
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
        encoding: Optional[str] = None,
        detected_encoding: Optional[str] = None,
        attempted_encoding: Optional[str] = None,
        byte_position: Optional[int] = None,
        invalid_byte: Optional[bytes] = None,
        **kwargs
    ):
        self.encoding = encoding
        self.detected_encoding = detected_encoding
        self.attempted_encoding = attempted_encoding
        self.byte_position = byte_position
        self.invalid_byte = invalid_byte
        super().__init__(message, **kwargs)
    
    def _format_message(self) -> str:
        """Formate le message d'erreur d'encodage"""
        parts = [self.message]
        
        if self.detected_encoding:
            parts.append(f"Encodage détecté: {self.detected_encoding}")
        
        if self.attempted_encoding:
            parts.append(f"Encodage tenté: {self.attempted_encoding}")
        
        return " - ".join(parts)


class GeneWebErrorCollector:
    """Collecteur d'erreurs pour validation gracieuse"""
    
    def __init__(self):
        self.errors: List[GeneWebError] = []
    
    def add_error(self, error: GeneWebError) -> None:
        """Ajoute une erreur au collecteur"""
        self.errors.append(error)
    
    def has_errors(self) -> bool:
        """Retourne True si des erreurs ont été collectées"""
        return len(self.errors) > 0
    
    def get_errors(self, error_type: Optional[type] = None) -> List[GeneWebError]:
        """Retourne les erreurs, optionnellement filtrées par type"""
        if error_type is None:
            return self.errors.copy()
        return [error for error in self.errors if isinstance(error, error_type)]
    
    def clear_errors(self) -> None:
        """Supprime toutes les erreurs"""
        self.errors.clear()
    
    def error_count(self) -> int:
        """Retourne le nombre d'erreurs"""
        return len(self.errors)
    
    def get_error_summary(self) -> str:
        """Retourne un résumé des erreurs"""
        if not self.errors:
            return "Aucune erreur"
        
        error_types = {}
        for error in self.errors:
            error_type = type(error).__name__
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        if len(error_types) == 1:
            error_type = list(error_types.keys())[0]
            count = error_types[error_type]
            return f"{count} erreur{'s' if count > 1 else ''} de {error_type.lower()}"
        else:
            total = len(self.errors)
            return f"{total} erreurs de types variés"
    
    def __enter__(self):
        """Support du contexte manager"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Support du contexte manager"""
        pass
    
    def __str__(self) -> str:
        """Représentation string du collecteur"""
        return f"GeneWebErrorCollector({len(self.errors)} erreur{'s' if len(self.errors) != 1 else ''})"


class ValidationResult:
    """Résultat de validation avec gestion des erreurs"""
    
    def __init__(self):
        self.errors: List[GeneWebError] = []
    
    def add_error(self, error: GeneWebError) -> None:
        """Ajoute une erreur au résultat"""
        self.errors.append(error)
    
    def add_errors_from_collector(self, collector: GeneWebErrorCollector) -> None:
        """Ajoute toutes les erreurs d'un collecteur"""
        self.errors.extend(collector.get_errors())
    
    def is_valid(self) -> bool:
        """Retourne True si la validation est réussie"""
        return len(self.errors) == 0
    
    def has_errors(self) -> bool:
        """Retourne True si des erreurs ont été trouvées"""
        return len(self.errors) > 0
    
    def get_error_messages(self) -> List[str]:
        """Retourne la liste des messages d'erreur"""
        return [str(error) for error in self.errors]
    
    def __str__(self) -> str:
        """Représentation string du résultat"""
        if self.is_valid():
            return "Validation réussie"
        else:
            return f"Validation échouée avec {len(self.errors)} erreur{'s' if len(self.errors) != 1 else ''}"
