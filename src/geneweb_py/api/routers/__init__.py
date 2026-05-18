"""
Routers FastAPI pour l'API geneweb-py.
"""

# Import des routers
from . import events, families, genealogy, persons, sessions

__all__ = ["persons", "families", "events", "genealogy", "sessions"]
