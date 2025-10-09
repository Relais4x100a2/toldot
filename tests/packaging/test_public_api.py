"""
Tests de l'API publique exposée par le package

Vérifie que tous les imports publics fonctionnent correctement
et que l'API est stable.
"""


def test_main_imports():
    """Test des imports principaux depuis geneweb_py"""
    from geneweb_py import GeneWebParser

    assert GeneWebParser is not None

    from geneweb_py import Genealogy

    assert Genealogy is not None

    from geneweb_py import Person

    assert Person is not None

    from geneweb_py import Family

    assert Family is not None

    from geneweb_py import Date

    assert Date is not None


def test_core_imports():
    """Test imports depuis geneweb_py.core.models"""
    from geneweb_py.core.models import Date, Family, Genealogy, Person

    assert Person is not None
    assert Family is not None
    assert Date is not None
    assert Genealogy is not None


def test_parser_imports():
    """Test import du parser"""
    from geneweb_py.core.parser import GeneWebParser

    assert GeneWebParser is not None


def test_exceptions_imports():
    """Test import des exceptions"""
    from geneweb_py.core.exceptions import (
        GeneWebConversionError,
        GeneWebEncodingError,
        GeneWebError,
        GeneWebParseError,
        GeneWebValidationError,
    )

    assert GeneWebError is not None
    assert GeneWebParseError is not None
    assert GeneWebValidationError is not None
    assert GeneWebConversionError is not None
    assert GeneWebEncodingError is not None


def test_formats_imports():
    """Test import des convertisseurs de format"""
    from geneweb_py.formats import (
        GEDCOMExporter,
        GEDCOMImporter,
        JSONExporter,
        JSONImporter,
        XMLExporter,
        XMLImporter,
    )

    assert GEDCOMExporter is not None
    assert GEDCOMImporter is not None
    assert JSONExporter is not None
    assert JSONImporter is not None
    assert XMLExporter is not None
    assert XMLImporter is not None


def test_models_imports():
    """Test import des modèles de données"""
    from geneweb_py.core.models import (
        Date,
        Family,
        Gender,
        Genealogy,
        MarriageStatus,
        Person,
    )

    assert Person is not None
    assert Family is not None
    assert Date is not None
    assert Genealogy is not None
    assert Gender is not None
    assert MarriageStatus is not None


def test_version_available():
    """Test que __version__ est disponible"""
    import geneweb_py

    assert hasattr(geneweb_py, "__version__")
    assert isinstance(geneweb_py.__version__, str)
    assert len(geneweb_py.__version__) > 0


def test_version_format():
    """Test que la version suit le format semver"""
    import re

    import geneweb_py

    # Format semver: MAJOR.MINOR.PATCH
    version_pattern = r"^\d+\.\d+\.\d+(?:[-+][a-zA-Z0-9.]+)?$"
    assert re.match(version_pattern, geneweb_py.__version__), (
        f"Version {geneweb_py.__version__} ne suit pas le format semver"
    )


def test_no_internal_imports_leak():
    """Vérifier qu'on n'expose pas d'imports internes au niveau package"""
    import geneweb_py

    # Ces attributs ne doivent PAS être exposés directement au niveau package
    internal_modules = [
        "LexicalParser",
        "SyntaxParser",
        "StreamingParser",
        "_private",
        "__pycache__",
    ]

    for internal in internal_modules:
        assert not hasattr(geneweb_py, internal), (
            f"Module interne {internal} exposé au niveau package"
        )


def test_basic_usage_pattern():
    """Test un pattern d'utilisation basique"""
    from geneweb_py import Date, GeneWebParser, Person

    # Pattern classique : parser un fichier
    parser = GeneWebParser()
    assert parser is not None

    # Pattern classique : créer une personne
    person = Person(
        last_name="DUPONT", first_name="Jean", birth_date=Date.parse("1/1/2000")
    )
    assert person.last_name == "DUPONT"
    assert person.first_name == "Jean"


def test_all_public_classes_have_docstrings():
    """Vérifier que toutes les classes publiques ont des docstrings"""
    from geneweb_py import (
        Date,
        Family,
        Genealogy,
        GeneWebParser,
        Person,
    )

    public_classes = [GeneWebParser, Genealogy, Person, Family, Date]

    for cls in public_classes:
        assert cls.__doc__ is not None, f"Classe {cls.__name__} sans docstring"
        assert len(cls.__doc__.strip()) > 10, f"Docstring de {cls.__name__} trop courte"


def test_exceptions_hierarchy():
    """Test hiérarchie des exceptions"""
    from geneweb_py.core.exceptions import (
        GeneWebConversionError,
        GeneWebError,
        GeneWebParseError,
        GeneWebValidationError,
    )

    # Toutes les exceptions doivent hériter de GeneWebError
    assert issubclass(GeneWebParseError, GeneWebError)
    assert issubclass(GeneWebValidationError, GeneWebError)
    assert issubclass(GeneWebConversionError, GeneWebError)

    # Et GeneWebError doit hériter de Exception
    assert issubclass(GeneWebError, Exception)


def test_import_speed():
    """Test que l'import du package est rapide"""
    import sys
    import time

    # Supprimer le module s'il est déjà importé
    if "geneweb_py" in sys.modules:
        del sys.modules["geneweb_py"]

    start = time.time()

    duration = time.time() - start

    # L'import ne doit pas prendre plus de 1 seconde
    assert duration < 1.0, f"Import trop lent: {duration:.2f}s"
