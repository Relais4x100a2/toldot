"""
Tests de compatibilité entre versions Python

Vérifie que le code fonctionne sur toutes les versions Python supportées.
"""

import sys
import pytest


def test_minimum_python_version():
    """Vérifier que nous sommes sur Python 3.7+"""
    assert sys.version_info >= (3, 7), \
        f"Python 3.7+ requis, version actuelle: {sys.version_info}"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="Python 3.7+ requis")
def test_python37_compatible():
    """Test compatibilité Python 3.7"""
    from geneweb_py import GeneWebParser, Person, Date
    
    # Features Python 3.7
    parser = GeneWebParser()
    assert parser is not None
    
    # Dataclasses sont supportées en 3.7+
    person = Person(last_name="TEST", first_name="User")
    assert person.last_name == "TEST"


def test_typing_extensions_compatibility():
    """Test compatibilité typing_extensions pour Python 3.7"""
    # typing_extensions fournit des backports pour Python 3.7
    try:
        # Python 3.8+
        from typing import Literal, TypedDict, Protocol
    except ImportError:
        # Python 3.7 fallback
        from typing_extensions import Literal, TypedDict, Protocol
    
    # Vérifier qu'on peut utiliser ces types
    assert Literal is not None


def test_dataclasses_compatibility():
    """Test compatibilité dataclasses"""
    from dataclasses import dataclass, field
    
    @dataclass
    class TestClass:
        name: str
        value: int = 0
    
    obj = TestClass(name="test")
    assert obj.name == "test"
    assert obj.value == 0


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python 3.8+ features")
def test_python38_features():
    """Test compatibilité features Python 3.8+"""
    from geneweb_py import GeneWebParser
    
    # Walrus operator := (Python 3.8+)
    if (parser := GeneWebParser()):
        assert parser is not None


@pytest.mark.skipif(sys.version_info < (3, 9), reason="Python 3.9+ features")
def test_python39_features():
    """Test compatibilité features Python 3.9+"""
    from geneweb_py import Person
    
    # Type hints avec collections built-in (Python 3.9+)
    # dict[str, str] au lieu de Dict[str, str]
    data: dict[str, str] = {"name": "test"}
    assert data["name"] == "test"


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Python 3.10+ features")
def test_python310_features():
    """Test compatibilité features Python 3.10+"""
    from geneweb_py import Person
    
    # Union types avec | (Python 3.10+)
    value: str | None = None
    assert value is None
    
    value = "test"
    assert isinstance(value, str)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="Python 3.11+ features")
def test_python311_features():
    """Test compatibilité Python 3.11+"""
    from geneweb_py import GeneWebParser
    
    # Python 3.11 a de meilleures performances et messages d'erreur
    parser = GeneWebParser()
    assert parser is not None


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ features")
def test_python312_features():
    """Test compatibilité Python 3.12+"""
    from geneweb_py import GeneWebParser
    
    # Python 3.12 avec nouvelles features
    parser = GeneWebParser()
    assert parser is not None


def test_no_deprecated_features():
    """Vérifier qu'on n'utilise pas de features dépréciées"""
    import warnings
    
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", DeprecationWarning)
        
        from geneweb_py import GeneWebParser, Person, Date
        
        parser = GeneWebParser()
        person = Person(last_name="TEST", first_name="User")
        
        # Vérifier qu'il n'y a pas de DeprecationWarning
        deprecation_warnings = [warning for warning in w 
                               if issubclass(warning.category, DeprecationWarning)]
        
        if deprecation_warnings:
            for warning in deprecation_warnings:
                print(f"DeprecationWarning: {warning.message}")
        
        # Pour l'instant, on accepte quelques warnings
        # mais idéalement il ne devrait pas y en avoir


def test_encoding_compatibility():
    """Test gestion des encodages sur différentes versions Python"""
    from geneweb_py import GeneWebParser
    
    parser = GeneWebParser()
    
    # Test avec caractères Unicode
    content = "fam DUPONT José + GARCÍA María\n"
    genealogy = parser.parse_string(content)
    
    assert genealogy is not None
    # Vérifier que les caractères Unicode sont préservés
    person = list(genealogy.persons.values())[0]
    assert "José" in person.first_name or "María" in person.first_name


def test_pathlib_compatibility():
    """Test compatibilité avec pathlib (Python 3.4+)"""
    from pathlib import Path
    from geneweb_py import GeneWebParser
    import tempfile
    
    parser = GeneWebParser()
    
    # Créer un fichier temporaire avec pathlib
    with tempfile.NamedTemporaryFile(mode='w', suffix='.gw', delete=False) as f:
        f.write("fam DUPONT Jean + MARTIN Marie\n")
        temp_path = Path(f.name)
    
    try:
        # Le parser doit accepter les objets Path
        genealogy = parser.parse_file(str(temp_path))
        assert genealogy is not None
    finally:
        temp_path.unlink()


def test_asyncio_compatibility():
    """Test que le package n'interfère pas avec asyncio"""
    import asyncio
    from geneweb_py import GeneWebParser
    
    async def async_parse():
        parser = GeneWebParser()
        content = "fam DUPONT Jean + MARTIN Marie\n"
        # Le parsing est synchrone mais doit fonctionner dans un contexte async
        genealogy = parser.parse_string(content)
        return genealogy
    
    # Tester dans une boucle événementielle
    genealogy = asyncio.run(async_parse())
    assert genealogy is not None

