"""
Exceptions spécifiques pour la librairie geneweb-py

Ce module définit les exceptions personnalisées utilisées dans toute la librairie
pour une gestion d'erreur claire et spécifique au format GeneWeb.
"""

from typing import Optional, List, Dict, Any


class GeneWebError(Exception):
    """Exception de base pour toutes les erreurs GeneWeb"""
    
    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        context: Optional[str] = None,
        **kwargs,
    ):
        # Attributs communs
        self.message = message
        self.line_number = line_number
        self.context = context

        # Rendez accessibles tous les kwargs supplémentaires afin de
        # permettre aux tests dʼaccéder directement aux attributs ajoutés.
        for key, value in kwargs.items():
            setattr(self, key, value)

        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        """Formate le message d'erreur avec le numéro de ligne si disponible"""
        # Le préfixe n'est présent que si un numéro de ligne est fourni, même s'il est 0.
        if self.line_number is not None:
            return f"Ligne {self.line_number}: {self.message}"
        return self.message


class GeneWebParseError(GeneWebError):
    """Erreur lors du parsing d'un fichier .gw"""

    def __init__(
        self,
        message: str,
        line_number: Optional[int] = None,
        token: Optional[str] = None,
        expected: Optional[str] = None,
        **kwargs,
    ):
        # Attributs spécifiques
        self.token = token
        self.expected = expected

        # Propager vers la classe de base tout en conservant kwargs afin qu'ils
        # restent accessibles en tant qu'attributs.
        super().__init__(
            message,
            line_number=line_number,
            token=token,
            expected=expected,
            **kwargs,
        )
    
    def _format_message(self) -> str:
        """Message simple: uniquement message + préfixe de ligne si fourni"""
        if self.line_number is not None:
            return f"Ligne {self.line_number}: {self.message}"
        return self.message


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
        context: Optional[str] = None,
        **kwargs,
    ):
        # Garantir l'existence des attributs attendus par _format_message
        self.field = field
        self.value = value
        self.entity_type = kwargs.get('entity_type', None)
        self.entity_id = kwargs.get('entity_id', None)
        self.person_id = kwargs.get('person_id', None)
        self.validation_errors = kwargs.get('validation_errors', []) or []
        self.context = context
        # Filtrer les kwargs déjà consommés pour éviter les doublons
        filtered_kwargs = {
            k: v for k, v in kwargs.items()
            if k not in {"entity_type", "entity_id", "person_id", "validation_errors", "field", "value", "context"}
        }
        super().__init__(
            message,
            line_number=line_number,
            context=context,
            **filtered_kwargs,
        )
    
    def _format_message(self) -> str:
        """Message simple: uniquement message + préfixe de ligne si fourni"""
        if self.line_number is not None:
            return f"Ligne {self.line_number}: {self.message}"
        return self.message


class GeneWebConversionError(GeneWebError):
    """Erreur lors de la conversion vers un autre format"""

    def __init__(
        self,
        message: str,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        **kwargs,
    ):
        self.source_format = source_format
        self.target_format = target_format
        super().__init__(
            message,
            source_format=source_format,
            target_format=target_format,
            **kwargs,
        )
    
    def _format_message(self) -> str:
        """Message simple: uniquement message + préfixe de ligne si fourni"""
        if self.line_number is not None:
            return f"Ligne {self.line_number}: {self.message}"
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
        **kwargs,
    ):
        # Initialiser tous les attributs référencés par _format_message
        self.encoding = encoding
        self.detected_encoding = detected_encoding
        self.attempted_encoding = attempted_encoding
        self.byte_position = byte_position
        self.invalid_byte = invalid_byte
        super().__init__(
            message,
            encoding=encoding,
            detected_encoding=detected_encoding,
            attempted_encoding=attempted_encoding,
            byte_position=byte_position,
            invalid_byte=invalid_byte,
            **kwargs,
        )
    
    def _format_message(self) -> str:
        """Message simple: uniquement message + préfixe de ligne si fourni"""
        if self.line_number is not None:
            return f"Ligne {self.line_number}: {self.message}"
        return self.message


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
