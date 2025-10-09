"""
Routers FastAPI pour l'API geneweb-py.
"""

# Import des routers
from . import events, families, genealogy, persons

__all__ = ["persons", "families", "events", "genealogy"]
