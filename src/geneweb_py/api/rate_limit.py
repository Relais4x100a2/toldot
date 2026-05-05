"""
Limitation de débit HTTP (slowapi).

Réduit le risque d'épuisement des ressources lorsque l'API est exposée
sur le réseau. Les limites peuvent être ajustées via GENEWEB_RATE_LIMIT.
"""

import os

from slowapi import Limiter
from slowapi.util import get_remote_address


def _default_rate_limit() -> str:
    """Retourne la limite globale par défaut (requêtes par minute par IP)."""
    raw = os.getenv("GENEWEB_RATE_LIMIT")
    if raw is not None and raw.strip():
        return raw.strip()
    return "600/minute"


limiter = Limiter(key_func=get_remote_address, default_limits=[_default_rate_limit()])
