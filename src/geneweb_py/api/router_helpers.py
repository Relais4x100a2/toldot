"""
Utilitaires communs aux routers HTTP (messages d'erreur sécurisés).
"""

import logging
from typing import NoReturn

from fastapi import HTTPException

logger = logging.getLogger(__name__)


def raise_internal_server_error(log_message: str, exc: Exception) -> NoReturn:
    """
    Journalise l'exception complète et renvoie une erreur HTTP 500 générique.

    Args:
        log_message: Contexte pour les journaux serveur.
        exc: Exception ayant provoqué l'échec.
    """
    logger.error("%s", log_message, exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Une erreur interne s'est produite. Réessayez plus tard.",
    ) from exc
