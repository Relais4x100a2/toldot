"""
Parser streaming pour les fichiers .gw volumineux

Ce module implémente un parsing en mode streaming pour réduire l'utilisation mémoire
lors du traitement de gros fichiers .gw (>10MB).
"""

from pathlib import Path
from typing import Iterator, Optional, TextIO, Union

import chardet

from ..exceptions import GeneWebEncodingError, GeneWebParseError
from .lexical import LexicalParser, Token, TokenType


class StreamingLexicalParser:
    """Parser lexical en mode streaming

    Tokenise les fichiers .gw ligne par ligne au lieu de tout charger en mémoire.
    Optimisé pour les fichiers volumineux (>10MB).
    """

    def __init__(
        self,
        file_handle: TextIO,
        filename: Optional[str] = None,
        buffer_size: int = 8192,
    ):
        """Initialise le parser streaming

        Args:
            file_handle: Handle du fichier ouvert en lecture
            filename: Nom du fichier (pour les erreurs)
            buffer_size: Taille du buffer de lecture en octets
        """
        self.file_handle = file_handle
        self.filename = filename or "<stream>"
        self.buffer_size = buffer_size
        self.line_number = 0
        self.buffer = ""
        self.eof_reached = False

        # Réutiliser le parser lexical existant pour la logique de tokenisation
        # mais en mode lazy
        self.lexical_parser: Optional[LexicalParser] = None

    def tokenize_lazy(self) -> Iterator[Token]:
        """Générateur lazy de tokens

        Lit le fichier ligne par ligne et génère les tokens au fur et à mesure,
        sans charger tout le fichier en mémoire.

        Yields:
            Token: Prochain token dans le flux

        Raises:
            GeneWebParseError: En cas d'erreur de tokenisation
        """
        accumulated_text = []
        current_block = None
        inside_multiline_block = False

        for line in self.file_handle:
            self.line_number += 1
            line_stripped = line.strip()

            # Détecter les blocs multi-lignes (notes, notes-db, page-ext, wizard-note)
            if line_stripped.startswith("notes ") or line_stripped.startswith(
                "notes-db"
            ):
                inside_multiline_block = True
                current_block = (
                    "notes" if line_stripped.startswith("notes ") else "notes-db"
                )
                accumulated_text.append(line)
                continue
            elif line_stripped.startswith("page-ext "):
                inside_multiline_block = True
                current_block = "page-ext"
                accumulated_text.append(line)
                continue
            elif line_stripped.startswith("wizard-note "):
                inside_multiline_block = True
                current_block = "wizard-note"
                accumulated_text.append(line)
                continue
            elif inside_multiline_block:
                accumulated_text.append(line)
                # Vérifier la fin du bloc
                end_markers = {
                    "notes": "end notes",
                    "notes-db": "end notes-db",
                    "page-ext": "end page-ext",
                    "wizard-note": "end wizard-note",
                }
                if current_block and line_stripped == end_markers.get(
                    current_block, ""
                ):
                    # Fin du bloc multi-lignes, parser le bloc complet
                    block_text = "".join(accumulated_text)
                    parser = LexicalParser(block_text, self.filename)
                    tokens = parser.tokenize()
                    for token in tokens:
                        if token.type != TokenType.EOF:
                            yield token
                    accumulated_text = []
                    inside_multiline_block = False
                    current_block = None
                continue

            # Pour les lignes simples, parser directement
            if line_stripped and not line_stripped.startswith("#"):
                # Parser la ligne
                parser = LexicalParser(line + "\n", self.filename)
                tokens = parser.tokenize()
                for token in tokens:
                    if token.type != TokenType.EOF:
                        # Ajuster le numéro de ligne au numéro global
                        token = Token(
                            type=token.type,
                            value=token.value,
                            line_number=self.line_number,
                            column=token.column,
                            position=token.position,
                        )
                        yield token
            elif line_stripped.startswith("#"):
                # Commentaire
                parser = LexicalParser(line, self.filename)
                tokens = parser.tokenize()
                for token in tokens:
                    if token.type == TokenType.COMMENT:
                        token = Token(
                            type=token.type,
                            value=token.value,
                            line_number=self.line_number,
                            column=token.column,
                            position=token.position,
                        )
                        yield token

        # Token EOF final
        yield Token(
            type=TokenType.EOF,
            value="",
            line_number=self.line_number,
            column=1,
            position=0,
        )


class StreamingGeneWebParser:
    """Parser GeneWeb en mode streaming

    Optimisé pour les fichiers volumineux (>10MB) en parsant ligne par ligne
    et en construisant les objets au fur et à mesure.
    """

    def __init__(self, validate: bool = True, buffer_size: int = 8192):
        """Initialise le parser streaming

        Args:
            validate: Si True, valide la cohérence des données après parsing
            buffer_size: Taille du buffer de lecture en octets
        """
        self.validate = validate
        self.buffer_size = buffer_size

    def parse_file_streaming(self, file_path: Union[str, Path]):
        """Parse un fichier .gw en mode streaming

        Args:
            file_path: Chemin vers le fichier .gw

        Returns:
            Générateur de tokens

        Raises:
            GeneWebParseError: En cas d'erreur de parsing
            GeneWebEncodingError: En cas de problème d'encodage
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise GeneWebParseError(f"Fichier non trouvé: {file_path}")

        # Détection d'encodage
        encoding = self._detect_encoding(file_path)

        # Ouvrir le fichier et créer un parser streaming
        with open(file_path, encoding=encoding, buffering=self.buffer_size) as f:
            parser = StreamingLexicalParser(f, str(file_path), self.buffer_size)
            yield from parser.tokenize_lazy()

    def _detect_encoding(self, file_path: Path) -> str:
        """Détecte l'encodage du fichier de manière optimisée

        Lit seulement les premiers Ko du fichier pour la détection.

        Args:
            file_path: Chemin vers le fichier

        Returns:
            Encodage détecté
        """
        try:
            # Lire seulement les premiers 8KB pour la détection
            with open(file_path, "rb") as f:
                sample = f.read(8192)

            # Essayer d'abord UTF-8 (plus commun)
            try:
                sample.decode("utf-8")
                return "utf-8"
            except UnicodeDecodeError:
                pass

            # Détecter avec chardet uniquement si UTF-8 échoue
            result = chardet.detect(sample)
            detected_encoding = result["encoding"]
            confidence = result["confidence"]

            if confidence >= 0.7 and detected_encoding:
                return detected_encoding

            # Fallback ISO-8859-1
            return "iso-8859-1"

        except Exception as e:
            raise GeneWebEncodingError(f"Erreur lors de la détection d'encodage: {e}")


def should_use_streaming(
    file_path: Union[str, Path], threshold_mb: float = 10.0
) -> bool:
    """Détermine si le parsing streaming doit être utilisé

    Args:
        file_path: Chemin vers le fichier
        threshold_mb: Seuil en mégaoctets au-delà duquel utiliser le streaming

    Returns:
        True si le fichier est assez gros pour justifier le streaming
    """
    try:
        file_path = Path(file_path)
        size_mb = file_path.stat().st_size / (1024 * 1024)
        return size_mb >= threshold_mb
    except Exception:
        # En cas d'erreur, ne pas utiliser le streaming
        return False


def estimate_memory_usage(file_path: Union[str, Path]) -> dict:
    """Estime l'utilisation mémoire pour parser un fichier

    Args:
        file_path: Chemin vers le fichier

    Returns:
        Dictionnaire avec les estimations de mémoire
    """
    file_path = Path(file_path)
    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)

    # Estimation empirique: le parsing normal utilise ~5-10x la taille du fichier
    # Le streaming utilise seulement ~1-2x la taille du fichier
    normal_memory_mb = size_mb * 7.5  # Moyenne
    streaming_memory_mb = size_mb * 1.5

    return {
        "file_size_mb": round(size_mb, 2),
        "estimated_normal_memory_mb": round(normal_memory_mb, 2),
        "estimated_streaming_memory_mb": round(streaming_memory_mb, 2),
        "memory_saving_percent": round(
            (1 - streaming_memory_mb / normal_memory_mb) * 100, 1
        ),
        "recommended_mode": "streaming" if size_mb >= 10 else "normal",
    }
