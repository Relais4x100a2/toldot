"""
Routers FastAPI pour l'API geneweb-py.
"""

# Import des routers
from . import persons, families, events, genealogy

__all__ = ["persons", "families", "events", "genealogy"]
