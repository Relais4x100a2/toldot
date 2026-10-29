"""Décomposition des lieux GeneWeb de la forme ``[complément]_-_lieu``."""

import re
from dataclasses import dataclass
from typing import Optional

# "[Atelier_Rose]_-_Lyon" ou "Ecole_primaire_-_Lyon" (séparateur "_-_" ou " - ")
_COMPLEMENT_RE = re.compile(r"^(?P<complement>.+?)(?:_-_|\s+-\s+)(?P<name>.+)$")


@dataclass(frozen=True)
class ParsedPlace:
    """Lieu décomposé ; ``raw`` conserve la chaîne d'origine pour la sérialisation."""

    raw: str
    name: str
    complement: Optional[str] = None


def _humanize(text: str) -> str:
    """Remplace les ``_`` GeneWeb par des espaces."""
    return text.replace("_", " ").strip()


def parse_place(raw: Optional[str]) -> Optional[ParsedPlace]:
    """Décompose un lieu en ``(complément, nom)`` sans altérer la chaîne brute.

    Args:
        raw: Lieu tel qu'écrit dans le ``.gw`` (``[Atelier_Rose]_-_Lyon``, ``Paris``…).

    Returns:
        ``ParsedPlace`` ou ``None`` si le lieu est vide.
    """
    if raw is None or not raw.strip():
        return None

    text = raw.strip()
    match = _COMPLEMENT_RE.match(text)
    if match is None:
        return ParsedPlace(raw=raw, name=_humanize(text))

    complement = match.group("complement").strip()
    if complement.startswith("[") and complement.endswith("]"):
        complement = complement[1:-1]
    return ParsedPlace(
        raw=raw,
        name=_humanize(match.group("name")),
        complement=_humanize(complement) or None,
    )
