"""
Limites et seuils de sécurité pour l'API HTTP.

Les valeurs peuvent être surchargées via les variables d'environnement
pour l'adaptation au déploiement.
"""

import os
from typing import List


def _parse_int_env(name: str, default: int) -> int:
    """Lit une variable d'environnement entière avec repli sur défaut."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _parse_csv_env(name: str, default: List[str]) -> List[str]:
    """Lit une liste d'origines CORS séparées par des virgules."""
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return list(default)
    return [item.strip() for item in raw.split(",") if item.strip()]


MAX_UPLOAD_BYTES: int = _parse_int_env("GENEWEB_MAX_UPLOAD_BYTES", 50 * 1024 * 1024)

DEFAULT_CORS_ORIGINS: List[str] = ["http://127.0.0.1:3000", "http://localhost:3000"]

CORS_ALLOW_ORIGINS: List[str] = _parse_csv_env("CORS_ORIGINS", DEFAULT_CORS_ORIGINS)
