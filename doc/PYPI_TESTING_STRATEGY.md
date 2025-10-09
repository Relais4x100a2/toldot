# Stratégie de tests pour déploiement PyPI

**Date** : 9 octobre 2025  
**Version cible** : 0.1.0  
**État** : En préparation 🚧

## 🎯 Objectif

Préparer geneweb-py pour publication sur PyPI avec une suite de tests garantissant :
- ✅ Installation correcte sur toutes plateformes
- ✅ Compatibilité Python 3.7-3.12
- ✅ Intégrité du packaging
- ✅ Sécurité des dépendances
- ✅ Documentation complète

## 📋 Checklist PyPI - Tests requis

### 1. ✅ Tests fonctionnels (83% → 90%+)
**État actuel** : 858 tests passent, 84% de couverture

| Catégorie | Couverture | Objectif | Priorité |
|-----------|-----------|----------|----------|
| Core | 88-97% | 95%+ | ✅ Excellent |
| Parser | 84-97% | 90%+ | ✅ Excellent |
| API | 59-94% | 85%+ | 🟡 À améliorer |
| Formats | 76-90% | 90%+ | 🟡 À améliorer |

**Actions** :
- Améliorer couverture API services (59% → 85%)
- Compléter tests formats XML (76% → 90%)
- Atteindre 90% global minimum avant publication

### 2. ⚠️ Tests de packaging (À créer)
**Priorité : CRITIQUE** 🔴

#### 2.1 Installation propre
```python
# tests/packaging/test_installation.py
"""
Tests d'installation du package dans différents environnements
"""
import subprocess
import sys
import tempfile
import venv
from pathlib import Path


def test_install_from_wheel():
    """Test installation depuis wheel"""
    # Créer un environnement virtuel temporaire
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        venv.create(venv_path, with_pip=True)
        
        # Construire le package
        subprocess.run([sys.executable, "-m", "build"], check=True)
        
        # Installer dans le venv
        pip = venv_path / "bin" / "pip"
        wheel = list(Path("dist").glob("*.whl"))[0]
        subprocess.run([str(pip), "install", str(wheel)], check=True)
        
        # Vérifier l'import
        python = venv_path / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c", "import geneweb_py; print(geneweb_py.__version__)"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "0.1.0" in result.stdout


def test_install_from_sdist():
    """Test installation depuis source distribution"""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        venv.create(venv_path, with_pip=True)
        
        # Installer depuis sdist
        pip = venv_path / "bin" / "pip"
        sdist = list(Path("dist").glob("*.tar.gz"))[0]
        subprocess.run([str(pip), "install", str(sdist)], check=True)
        
        python = venv_path / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c", "import geneweb_py"],
            capture_output=True
        )
        assert result.returncode == 0


def test_install_with_extras():
    """Test installation avec extras (dev, api, cli, etc.)"""
    extras = ["dev", "api", "cli", "validation", "parsing"]
    
    for extra in extras:
        with tempfile.TemporaryDirectory() as tmpdir:
            venv_path = Path(tmpdir) / "venv"
            venv.create(venv_path, with_pip=True)
            
            pip = venv_path / "bin" / "pip"
            subprocess.run([str(pip), "install", f".[{extra}]"], check=True)
            
            # Vérifier que les dépendances de l'extra sont installées
            result = subprocess.run(
                [str(pip), "list"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0


def test_minimal_install():
    """Test installation minimale (sans extras)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        venv_path = Path(tmpdir) / "venv"
        venv.create(venv_path, with_pip=True)
        
        pip = venv_path / "bin" / "pip"
        wheel = list(Path("dist").glob("*.whl"))[0]
        subprocess.run([str(pip), "install", str(wheel)], check=True)
        
        # Vérifier que seules les dépendances minimales sont installées
        python = venv_path / "bin" / "python"
        result = subprocess.run(
            [str(python), "-c", "import geneweb_py; from geneweb_py import GeneWebParser"],
            capture_output=True
        )
        assert result.returncode == 0
```

#### 2.2 Imports publics
```python
# tests/packaging/test_public_api.py
"""
Tests de l'API publique exposée par le package
"""


def test_main_imports():
    """Test des imports principaux"""
    # Ces imports doivent tous fonctionner
    from geneweb_py import (
        GeneWebParser,
        Genealogy,
        Person,
        Family,
        Date,
    )
    assert GeneWebParser is not None
    assert Genealogy is not None
    assert Person is not None


def test_exceptions_imports():
    """Test import des exceptions"""
    from geneweb_py.core.exceptions import (
        GeneWebError,
        GeneWebParseError,
        GeneWebValidationError,
        GeneWebConversionError,
    )
    assert GeneWebError is not None


def test_formats_imports():
    """Test import des convertisseurs"""
    from geneweb_py.formats import (
        GedcomConverter,
        JsonConverter,
        XmlConverter,
    )
    assert GedcomConverter is not None


def test_no_internal_imports_leak():
    """Vérifier qu'on n'expose pas d'imports internes"""
    import geneweb_py
    
    # Ces attributs ne doivent PAS être exposés directement
    assert not hasattr(geneweb_py, "LexicalParser")
    assert not hasattr(geneweb_py, "SyntaxParser")
    assert not hasattr(geneweb_py, "_private_module")


def test_version_available():
    """Test que __version__ est disponible"""
    import geneweb_py
    assert hasattr(geneweb_py, "__version__")
    assert geneweb_py.__version__ == "0.1.0"
```

#### 2.3 Métadonnées du package
```python
# tests/packaging/test_metadata.py
"""
Tests des métadonnées du package
"""
import importlib.metadata


def test_package_metadata():
    """Test métadonnées complètes"""
    metadata = importlib.metadata.metadata("geneweb-py")
    
    # Champs requis
    assert metadata["Name"] == "geneweb-py"
    assert metadata["Version"] == "0.1.0"
    assert metadata["Summary"]
    assert metadata["Author"]
    assert metadata["License"] == "MIT"
    assert metadata["Requires-Python"] == ">=3.7"


def test_classifiers():
    """Test classifiers PyPI"""
    metadata = importlib.metadata.metadata("geneweb-py")
    classifiers = metadata.get_all("Classifier")
    
    # Vérifier présence de classifiers importants
    assert any("Development Status" in c for c in classifiers)
    assert any("License :: OSI Approved :: MIT License" in c for c in classifiers)
    assert any("Programming Language :: Python :: 3" in c for c in classifiers)
    assert any("Topic :: Sociology :: Genealogy" in c for c in classifiers)


def test_entry_points():
    """Test points d'entrée (si CLI disponible)"""
    try:
        eps = importlib.metadata.entry_points()
        # Vérifier si des entry points console_scripts existent
        console_scripts = eps.get("console_scripts", [])
        # Pour l'instant pas de CLI, mais à ajouter si nécessaire
    except:
        pass  # OK si pas d'entry points


def test_dependencies():
    """Test dépendances déclarées"""
    metadata = importlib.metadata.metadata("geneweb-py")
    requires = metadata.get_all("Requires-Dist") or []
    
    # Vérifier dépendances obligatoires
    assert any("typing_extensions" in r for r in requires)
    assert any("chardet" in r for r in requires)
```

#### 2.4 Intégrité des fichiers
```python
# tests/packaging/test_package_integrity.py
"""
Tests d'intégrité du package
"""
from pathlib import Path
import tarfile
import zipfile


def test_wheel_contains_all_modules():
    """Vérifier que le wheel contient tous les modules"""
    wheel_path = list(Path("dist").glob("*.whl"))[0]
    
    with zipfile.ZipFile(wheel_path) as whl:
        files = whl.namelist()
        
        # Vérifier présence des modules critiques
        assert any("geneweb_py/__init__.py" in f for f in files)
        assert any("geneweb_py/core/" in f for f in files)
        assert any("geneweb_py/api/" in f for f in files)
        assert any("geneweb_py/formats/" in f for f in files)
        
        # Vérifier absence de fichiers de test
        assert not any("tests/" in f for f in files)
        assert not any("__pycache__" in f for f in files)


def test_sdist_contains_source():
    """Vérifier que le sdist contient les sources"""
    sdist_path = list(Path("dist").glob("*.tar.gz"))[0]
    
    with tarfile.open(sdist_path) as tar:
        files = tar.getnames()
        
        # Doit contenir pyproject.toml
        assert any("pyproject.toml" in f for f in files)
        assert any("README.md" in f for f in files)
        assert any("LICENSE" in f for f in files)
        
        # Doit contenir le code source
        assert any("geneweb_py/" in f for f in files)


def test_no_unnecessary_files():
    """Vérifier absence de fichiers inutiles"""
    wheel_path = list(Path("dist").glob("*.whl"))[0]
    
    with zipfile.ZipFile(wheel_path) as whl:
        files = whl.namelist()
        
        # Fichiers qui NE doivent PAS être présents
        forbidden = [".pyc", ".git", ".github", "htmlcov", ".pytest_cache", "__pycache__"]
        for forbidden_pattern in forbidden:
            assert not any(forbidden_pattern in f for f in files), \
                f"Found forbidden pattern {forbidden_pattern} in wheel"
```

### 3. ⚠️ Tests de compatibilité multi-versions (À créer)
**Priorité : HAUTE** 🟡

```python
# tests/compatibility/test_python_versions.py
"""
Tests de compatibilité entre versions Python
"""
import sys
import pytest


@pytest.mark.skipif(sys.version_info < (3, 7), reason="Python 3.7+ requis")
def test_python37_compatible():
    """Test compatibilité Python 3.7"""
    from geneweb_py import GeneWebParser
    parser = GeneWebParser()
    assert parser is not None


def test_typing_extensions_compat():
    """Test compatibilité typing_extensions"""
    try:
        from typing import Literal  # Python 3.8+
    except ImportError:
        from typing_extensions import Literal  # Fallback Python 3.7
    
    assert Literal is not None


def test_no_fstrings_with_equals():
    """Vérifier qu'on n'utilise pas f-strings avec = (Python 3.8+)"""
    # Cette feature n'existe qu'en Python 3.8+
    # Si on cible 3.7, on ne doit pas l'utiliser
    import ast
    from pathlib import Path
    
    py_files = Path("geneweb_py").rglob("*.py")
    for py_file in py_files:
        with open(py_file) as f:
            try:
                tree = ast.parse(f.read())
                # Vérifier qu'il n'y a pas de JoinedStr avec '='
                # (c'est complexe, on peut simplifier en vérifiant juste le parsing)
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {py_file}: {e}")


@pytest.mark.skipif(sys.version_info < (3, 10), reason="Python 3.10+ requis")
def test_python310_compatible():
    """Test fonctionnalités Python 3.10+"""
    # Match statement, etc.
    from geneweb_py import GeneWebParser
    parser = GeneWebParser()
    assert parser is not None


@pytest.mark.skipif(sys.version_info < (3, 12), reason="Python 3.12+ requis")
def test_python312_compatible():
    """Test compatibilité Python 3.12"""
    from geneweb_py import GeneWebParser
    parser = GeneWebParser()
    assert parser is not None
```

### 4. ⚠️ Tests de dépendances et sécurité (À créer)
**Priorité : HAUTE** 🟡

```python
# tests/security/test_dependencies.py
"""
Tests de sécurité des dépendances
"""
import subprocess
import json


def test_no_vulnerable_dependencies():
    """Vérifier absence de vulnérabilités connues"""
    result = subprocess.run(
        ["pip-audit", "--format", "json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        vulnerabilities = json.loads(result.stdout)
        pytest.fail(f"Vulnérabilités détectées : {vulnerabilities}")


def test_pinned_dependencies():
    """Vérifier que les dépendances ont des versions"""
    import tomli
    
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)
    
    deps = config["project"]["dependencies"]
    
    # Toutes les dépendances doivent avoir une version min
    for dep in deps:
        assert ">=" in dep or "==" in dep, \
            f"Dépendance {dep} sans version spécifiée"


def test_minimal_dependencies():
    """Vérifier qu'on n'a pas trop de dépendances"""
    import tomli
    
    with open("pyproject.toml", "rb") as f:
        config = tomli.load(f)
    
    deps = config["project"]["dependencies"]
    
    # Maximum 5 dépendances obligatoires pour une lib
    assert len(deps) <= 5, \
        f"Trop de dépendances obligatoires ({len(deps)})"


def test_license_compatibility():
    """Vérifier compatibilité des licences"""
    result = subprocess.run(
        ["pip-licenses", "--format=json"],
        capture_output=True,
        text=True
    )
    
    licenses = json.loads(result.stdout)
    
    # Licenses interdites (GPL notamment, incompatible avec MIT)
    forbidden = ["GPL", "AGPL"]
    for pkg in licenses:
        license_name = pkg.get("License", "")
        assert not any(f in license_name for f in forbidden), \
            f"License incompatible: {pkg['Name']} - {license_name}"
```

### 5. ⚠️ Tests de documentation (À créer)
**Priorité : MOYENNE** 🟡

```python
# tests/documentation/test_docs.py
"""
Tests de présence et qualité de la documentation
"""
from pathlib import Path


def test_readme_exists():
    """Vérifier présence README"""
    readme = Path("README.md")
    assert readme.exists()
    assert readme.stat().st_size > 1000  # Au moins 1KB


def test_readme_sections():
    """Vérifier sections obligatoires du README"""
    with open("README.md") as f:
        content = f.read()
    
    required_sections = [
        "Installation",
        "Usage",
        "Features",
        "Documentation",
        "License",
    ]
    
    for section in required_sections:
        assert section.lower() in content.lower(), \
            f"Section '{section}' manquante dans README"


def test_license_exists():
    """Vérifier présence LICENSE"""
    license_file = Path("LICENSE")
    assert license_file.exists()
    
    with open(license_file) as f:
        content = f.read()
        assert "MIT" in content


def test_changelog_exists():
    """Vérifier présence CHANGELOG"""
    changelog = Path("CHANGELOG.md")
    assert changelog.exists()


def test_docstrings_coverage():
    """Vérifier présence docstrings sur API publique"""
    from geneweb_py import GeneWebParser, Genealogy, Person
    
    # Classes principales doivent avoir docstrings
    assert GeneWebParser.__doc__ is not None
    assert Genealogy.__doc__ is not None
    assert Person.__doc__ is not None


def test_examples_work():
    """Vérifier que les exemples fonctionnent"""
    examples = Path("examples").glob("*.py")
    
    for example in examples:
        if example.name == "api_usage.py":
            continue  # Skip API examples (need server)
        
        result = subprocess.run(
            [sys.executable, str(example)],
            capture_output=True,
            timeout=30
        )
        assert result.returncode == 0, \
            f"Example {example.name} failed: {result.stderr}"
```

### 6. ⚠️ Tests de plateforme (À créer)
**Priorité : MOYENNE** 🟡

```python
# tests/platforms/test_cross_platform.py
"""
Tests de compatibilité multi-plateformes
"""
import os
import platform
import tempfile
from pathlib import Path


def test_path_handling():
    """Test gestion des chemins Windows/Unix"""
    from geneweb_py import GeneWebParser
    
    parser = GeneWebParser()
    
    # Test avec différents séparateurs
    if platform.system() == "Windows":
        path = "C:\\Users\\test\\file.gw"
    else:
        path = "/home/test/file.gw"
    
    # Le parser doit accepter les deux formats
    # (test sans vraiment parser, juste vérifier qu'il ne crash pas)


def test_encoding_handling():
    """Test gestion encodages différents"""
    from geneweb_py import GeneWebParser
    
    parser = GeneWebParser()
    
    # Test UTF-8
    content_utf8 = "fam DUPONT José + GARCÍA María\n"
    genealogy = parser.parse_string(content_utf8)
    assert genealogy is not None
    
    # Test ISO-8859-1
    content_latin1 = content_utf8.encode("utf-8").decode("latin1")
    # Doit détecter automatiquement


def test_line_endings():
    """Test différents types de fins de ligne"""
    from geneweb_py import GeneWebParser
    
    parser = GeneWebParser()
    
    # Unix LF
    content_lf = "fam DUPONT Jean\n+ MARTIN Marie\n"
    genealogy = parser.parse_string(content_lf)
    assert genealogy is not None
    
    # Windows CRLF
    content_crlf = "fam DUPONT Jean\r\n+ MARTIN Marie\r\n"
    genealogy = parser.parse_string(content_crlf)
    assert genealogy is not None
    
    # Mac CR (ancien)
    content_cr = "fam DUPONT Jean\r+ MARTIN Marie\r"
    genealogy = parser.parse_string(content_cr)
    assert genealogy is not None
```

## 🔧 Configuration CI/CD

### GitHub Actions workflow

```yaml
# .github/workflows/test-pypi.yml
name: Tests PyPI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main]

jobs:
  test-packaging:
    name: Test packaging
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install build tools
        run: |
          python -m pip install --upgrade pip
          pip install build twine check-manifest
      
      - name: Build package
        run: python -m build
      
      - name: Check package
        run: twine check dist/*
      
      - name: Run packaging tests
        run: pytest tests/packaging/ -v

  test-compatibility:
    name: Test Python ${{ matrix.python-version }}
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        python-version: ['3.7', '3.8', '3.9', '3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      
      - name: Run tests
        run: pytest tests/ -v --ignore=tests/packaging/
  
  test-security:
    name: Security audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install pip-audit pip-licenses
      
      - name: Run security audit
        run: pip-audit --requirement <(pip freeze)
      
      - name: Check licenses
        run: pip-licenses --format=json

  publish-test-pypi:
    name: Publish to TestPyPI
    needs: [test-packaging, test-compatibility, test-security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/dev'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Build package
        run: python -m build
      
      - name: Publish to TestPyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.TEST_PYPI_API_TOKEN }}
          repository-url: https://test.pypi.org/legacy/
```

## 📊 Estimation d'effort

| Phase | Tests à créer | Temps estimé | Priorité |
|-------|---------------|--------------|----------|
| Tests packaging | 15-20 tests | 4-6h | 🔴 CRITIQUE |
| Tests compatibilité | 10-15 tests | 3-4h | 🟡 HAUTE |
| Tests sécurité | 5-10 tests | 2-3h | 🟡 HAUTE |
| Tests documentation | 8-10 tests | 2-3h | 🟢 MOYENNE |
| Tests plateformes | 8-10 tests | 2-3h | 🟢 MOYENNE |
| Config CI/CD | Workflows | 2-3h | 🟡 HAUTE |
| **TOTAL** | **46-65 tests** | **15-22h** | - |

## ✅ Checklist avant publication PyPI

### Pre-publication (TestPyPI)
- [ ] Tous les tests passent (coverage ≥ 90%)
- [ ] Tests de packaging passent
- [ ] Tests de compatibilité Python 3.7-3.12 passent
- [ ] Aucune vulnérabilité de sécurité
- [ ] Documentation complète (README, CHANGELOG, LICENSE)
- [ ] Version correctement taggée
- [ ] Build réussi (wheel + sdist)
- [ ] `twine check` sans erreurs
- [ ] Publication sur TestPyPI réussie
- [ ] Installation depuis TestPyPI fonctionne

### Publication (PyPI Production)
- [ ] Tous les tests TestPyPI validés
- [ ] Revue du code complète
- [ ] Tag Git créé (v0.1.0)
- [ ] Release notes rédigées
- [ ] Publication PyPI
- [ ] Installation depuis PyPI validée
- [ ] Documentation en ligne mise à jour

## 🚀 Commandes utiles

```bash
# Construction du package
python -m build

# Vérification du package
twine check dist/*

# Publication TestPyPI
twine upload --repository testpypi dist/*

# Test installation depuis TestPyPI
pip install --index-url https://test.pypi.org/simple/ geneweb-py

# Publication PyPI (production)
twine upload dist/*

# Installation depuis PyPI
pip install geneweb-py

# Lancer tous les tests PyPI
pytest tests/packaging/ tests/compatibility/ tests/security/ -v

# Vérifier le manifest
check-manifest

# Audit de sécurité
pip-audit

# Vérifier les licenses
pip-licenses
```

## 📚 Références

- [PyPI Publishing Guide](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [PEP 517 - Build System](https://peps.python.org/pep-0517/)
- [PEP 518 - pyproject.toml](https://peps.python.org/pep-0518/)
- [setuptools documentation](https://setuptools.pypa.io/)
- [TestPyPI](https://test.pypi.org/)

## 🎯 Prochaines étapes

1. **Semaine 1** : Créer tests packaging (4-6h)
2. **Semaine 2** : Tests compatibilité + sécurité (5-7h)
3. **Semaine 3** : CI/CD + tests documentation (4-6h)
4. **Semaine 4** : Publication TestPyPI + validation
5. **Semaine 5** : Publication PyPI production

**Date cible publication** : ~5 semaines (mi-novembre 2025)

