"""
Module API FastAPI pour geneweb-py.

Ce module fournit une API REST moderne pour manipuler les données généalogiques
au format GeneWeb (.gw) avec FastAPI.
"""

from .main import app, create_app
from .services.genealogy_service import GenealogyService

__all__ = ["app", "create_app", "GenealogyService"]
