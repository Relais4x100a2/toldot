# geneweb-py

[![Python Version](https://img.shields.io/badge/python-%3E%3D3.8-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue.svg)](https://pypi.org/project/geneweb-py/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://github.com/Relais4x100a2/geneweb-py/workflows/Tests%20PyPI%20et%20Publication/badge.svg)](https://github.com/Relais4x100a2/geneweb-py/actions)
[![Coverage](https://img.shields.io/badge/coverage-82%25-green.svg)](htmlcov/index.html)
[![Tests Passing](https://img.shields.io/badge/tests-704%20passing-success.svg)](tests/)

Librairie Python complète pour parser, manipuler et convertir les fichiers généalogiques au format GeneWeb (.gw).

## 🚀 Fonctionnalités

- **Parser complet** : Lecture et parsing des fichiers .gw avec support gwplus ✅
- **Parser avancé** : Support des apostrophes, caractères spéciaux, numéros d'occurrence ✅
- **Nouveaux blocs** : Support complet des blocs `notes-db`, `page-ext`, `wizard-note` ✅
- **Modèles de données** : Représentation structurée des personnes, familles et événements ✅
- **API REST moderne** : FastAPI avec endpoints complets pour CRUD ✅
- **Validation** : Vérification de cohérence des données généalogiques ✅
- **Messages d'erreur enrichis** : Erreurs contextuelles avec numéro de ligne, tokens, et suggestions ✅
- **Validation gracieuse** : Mode strict/gracieux pour collecter toutes les erreurs ou s'arrêter à la première ✅
- **Conversion** : Export/import vers GEDCOM, JSON, XML et autres formats ✅
- **Performance** : Optimisations avancées (streaming, cache LRU, __slots__) ✅
  - Mode streaming automatique pour gros fichiers (>10MB)
  - Réduction mémoire de ~80% sur fichiers volumineux
  - Optimisations CPU : ~15-20% plus rapide sur petits fichiers

## 📦 Installation

```bash
pip install geneweb-py
```

Pour le développement :

```bash
pip install geneweb-py[dev]
```

Extras disponibles (voir `pyproject.toml`) : `dev`, `docs`, `cli`, `validation`, `api`. L’extra optionnel **`parsing`** installe [Lark](https://github.com/lark-parser/lark) pour d’éventuels travaux sur une grammaire déclarative ; **le parser GeneWeb actuel n’en dépend pas** — réservé à un usage expérimental ou futur.

## 🎯 Utilisation rapide

### Parser un fichier .gw

```python
from geneweb_py import GeneWebParser

# Créer le parser
parser = GeneWebParser()

# Parser un fichier
genealogy = parser.parse_file("ma_famille.gw")

# Afficher des statistiques
print(f"Nombre de personnes : {len(genealogy.persons)}")
print(f"Nombre de familles : {len(genealogy.families)}")
```

### API REST avec FastAPI

```python
# Démarrer l'API
from geneweb_py.api import app
import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8000)

# L'API sera disponible sur http://localhost:8000/docs
```

### Rechercher une personne

```python
# Rechercher par nom
person = genealogy.find_person("CORNO", "Joseph")

if person:
    print(f"Nom : {person.full_name}")
    print(f"Naissance : {person.birth_date}")
    print(f"Décès : {person.death_date}")
    
    # Obtenir les familles
    families = person.get_families()
    for family in families:
        print(f"Époux(se) : {family.spouse(person)}")
```

### Utiliser l'API REST

```python
# Via l'API REST
import requests

# Lister les personnes
response = requests.get("http://localhost:8000/api/v1/persons")
print(f"Personnes : {response.json()}")

# Obtenir une personne
person = requests.get("http://localhost:8000/api/v1/persons/1")
print(f"Personne : {person.json()}")
```

### Nouvelles fonctionnalités du parser

```python
# Démontrer les améliorations récentes
python examples/parser_improvements_demo.py

# Exemple de parsing avec apostrophes et caractères spéciaux
content = """
fam d'Arc Jean-Marie .1 #occu Ingénieur_(ENSIA),_Aumônier_de_l'enseignement + O'Brien Marie-Claire .2
wit m: LEROY Bernard .1 #occu Dominicain,_Aumônier_de_l'enseignement_technique_à_Rouen
beg
- h Pierre_Bernard .1 #occu Ingénieur,_éditeur
- f Marie_Claire .2 #occu Conseillère_en_économie_sociale_et_familiale
end

notes-db
Notes générales sur cette famille
end notes-db

page-ext d'Arc Jean-Marie .1
<h1>Page de Jean-Marie d'Arc</h1>
end page-ext

wizard-note O'Brien Marie-Claire .2
Note générée par le wizard pour Marie-Claire
end wizard-note
"""

parser = GeneWebParser()
genealogy = parser.parse_string(content)

# Toutes les personnes sont correctement parsées avec leurs occupations
for person in genealogy.persons.values():
    print(f"{person.first_name} {person.last_name} - {person.occupation}")
```

### Validation gracieuse et gestion d'erreurs

Le parser supporte deux modes de gestion d'erreurs :

#### Mode strict (par défaut) - S'arrête à la première erreur

```python
from geneweb_py import GeneWebParser

parser = GeneWebParser(strict=True)  # Mode par défaut
try:
    genealogy = parser.parse_file("fichier_avec_erreur.gw")
except GeneWebParseError as e:
    print(f"Erreur de parsing : {e}")
    # Message enrichi avec ligne, token attendu, contexte
```

#### Mode gracieux - Collecte toutes les erreurs

```python
from geneweb_py import GeneWebParser

# Mode gracieux : continue le parsing malgré les erreurs
parser = GeneWebParser(strict=False, validate=True)
genealogy = parser.parse_file("fichier_avec_erreurs.gw")

# Vérifier si la généalogie est valide
if not genealogy.is_valid:
    print(f"Erreurs détectées : {len(genealogy.validation_errors)}")
    
    # Obtenir un résumé
    print(genealogy.get_validation_summary())
    
    # Afficher toutes les erreurs
    for error in genealogy.validation_errors:
        print(f"- {error}")  # Messages enrichis avec contexte

# Rapport détaillé des erreurs
if parser.error_collector.has_errors():
    print(parser.error_collector.get_detailed_report())
```

#### Messages d'erreur enrichis

Les erreurs incluent automatiquement :
- Numéro de ligne
- Token trouvé vs token attendu
- Contexte (quelle personne, famille, etc.)
- Sévérité (WARNING, ERROR, CRITICAL)

```python
# Exemple de message d'erreur enrichi :
# Ligne 42: Token inattendu
#   Token trouvé: 'invalid'
#   Attendu: fam, nom, ou date
#   Contexte: Parsing d'une personne
```

#### Validation des données

```python
from geneweb_py.core.validation import (
    validate_person_basic,
    validate_family_basic,
    validate_genealogy_consistency
)

# Valider une personne
result = validate_person_basic(person)
if not result.is_valid():
    print(f"Erreurs : {result.get_error_messages()}")
    print(f"Avertissements : {result.get_warning_messages()}")

# Valider toute la généalogie
result = validate_genealogy_consistency(genealogy)
print(result.get_summary())  # Résumé des erreurs et avertissements
```

### Conversion de formats

```python
from geneweb_py.formats import GEDCOMExporter, JSONExporter, XMLExporter

# Export vers GEDCOM
gedcom_exporter = GEDCOMExporter()
gedcom_exporter.export(genealogy, "ma_famille.ged")

# Export vers JSON
json_exporter = JSONExporter()
json_exporter.export(genealogy, "ma_famille.json")

# Export vers XML
xml_exporter = XMLExporter()
xml_exporter.export(genealogy, "ma_famille.xml")

# Import depuis JSON
from geneweb_py.formats import JSONImporter
json_importer = JSONImporter()
imported_genealogy = json_importer.import_from_file("ma_famille.json")
```

## ⚡ Optimisations de performance

geneweb-py inclut des optimisations avancées pour gérer efficacement les fichiers volumineux :

```python
from geneweb_py.core.parser.gw_parser import GeneWebParser

# Mode automatique : détecte la taille et choisit le meilleur mode
parser = GeneWebParser()
genealogy = parser.parse_file("gros_fichier.gw")  # Streaming si >10MB

# Estimer l'utilisation mémoire avant parsing
estimate = parser.get_memory_estimate("gros_fichier.gw")
print(f"Mémoire estimée : {estimate['estimated_streaming_memory_mb']} MB")
print(f"Économie : {estimate['memory_saving_percent']}%")

# Mode streaming forcé pour économiser la mémoire
parser = GeneWebParser(stream_mode=True)

# Désactiver la validation pour plus de vitesse
parser = GeneWebParser(validate=False)
```

**Gains mesurés** :
- Fichiers >10MB : ~80% de réduction mémoire avec le streaming
- Petits fichiers : ~15-20% plus rapide grâce aux optimisations CPU
- Exemple : fichier 50MB passe de ~375MB RAM à ~75MB RAM

**Voir aussi** :
- [Guide complet des performances](doc/PERFORMANCE.md)
- [Exemple de démonstration](examples/performance_demo.py)
- [Benchmarks](tests/performance/benchmark_parser.py)

## 📚 Documentation

**→ [Guide complet de la documentation](DOCUMENTATION.md)** - Index central et parcours recommandés

### Essentiel
- **[README.md](README.md)** - 👈 Vous êtes ici - Guide d'utilisation
- **[CHANGELOG.md](CHANGELOG.md)** - Historique des versions
- **[doc/status.md](doc/status.md)** - État du projet et métriques
- **[doc/roadmap.md](doc/roadmap.md)** - Vision à long terme

### Guides spécialisés
- **[doc/PERFORMANCE.md](doc/PERFORMANCE.md)** ⚡ - Optimisations et benchmarks
- **[QUICK_START_PYPI.md](QUICK_START_PYPI.md)** 📦 - Publication PyPI
- **[doc/geneweb/gw_format_documentation.md](doc/geneweb/gw_format_documentation.md)** - Format .gw

### Ressources
- **[examples/](examples/)** - Scripts de démonstration
- **[tests/](tests/)** - Suite de tests (858 tests, 84% couverture)
- **[Documentation API](http://localhost:8000/docs)** - Swagger UI (API REST)
- **[GeneWeb Community](https://web.archive.org/web/20250802144922/https://geneweb.tuxfamily.org/wiki/GeneWeb)** - Documentation communautaire

## 🧪 Tests

geneweb-py dispose d'une suite de tests **consolidée et organisée** avec **377 tests** et **80%+ de couverture**.

### 📁 Structure des Tests

```
tests/
├── unit/                    # Tests unitaires par module (18 fichiers)
│   ├── test_date.py         # Tests pour core.date
│   ├── test_event.py        # Tests pour core.event  
│   ├── test_person.py       # Tests pour core.person
│   ├── test_family.py       # Tests pour core.family
│   ├── test_exceptions.py   # Tests pour core.exceptions
│   ├── test_validation.py   # Tests pour core.validation
│   ├── test_parser*.py      # Tests pour core.parser
│   └── test_formats*.py     # Tests pour formats.*
├── integration/             # Tests d'intégration
├── compatibility/           # Tests de compatibilité Python
├── packaging/              # Tests de packaging PyPI
└── security/               # Tests de sécurité
```

### 🚀 Exécution des Tests

```bash
# Exécuter tous les tests
pytest

# Tests unitaires seulement (recommandé pour le développement)
pytest tests/unit/

# Tests avec couverture
pytest --cov=geneweb_py --cov-report=html

# Tests sans les tests lents
pytest -m "not slow"

# Tests d'intégration seulement
pytest tests/integration/

# Tests de packaging (PyPI)
pytest tests/packaging/

# Tests de compatibilité multi-versions
pytest tests/compatibility/

# Tests de sécurité
pytest tests/security/

# Voir les tests skippés et leurs raisons
pytest -rs
```

### 📊 Métriques de Qualité

- **Tests unitaires** : 349 passants, 28 skippés
- **Couverture globale** : 80%+ (objectif atteint)
- **Modules critiques** : 90%+ (parser, validation, exceptions)
- **Temps d'exécution** : < 30s pour la suite complète

### 🔧 Configuration des Tests

Les tests sont configurés dans `pyproject.toml` avec :
- **Couverture minimale** : 80%
- **Marqueurs** : `slow`, `integration`, `unit`, `coverage`, `parser`, `validation`, `formats`
- **Filtres d'avertissements** : Déprecations ignorées
- **Traceback court** : Pour des rapports concis

### 📝 Documentation des Tests

- **[Structure des tests](tests/README.md)** : Organisation et bonnes pratiques
- **[Tests skippés](tests/SKIPPED_TESTS.md)** : Documentation des tests temporairement désactivés
- **Couverture** : Rapport HTML généré dans `htmlcov/`

## 🚀 Développement et Publication

### Installation en mode développement

```bash
git clone https://github.com/Relais4x100a2/geneweb-py.git
cd geneweb-py
pip install -e .[dev]
```

### Validation avant publication PyPI

geneweb-py inclut des scripts de validation pour garantir la qualité avant publication :

```bash
# Validation complète (bash)
./scripts/validate_pypi.sh

# Vérification avancée (Python)
python scripts/check_pypi_readiness.py

# Construction du package
python -m build

# Vérification avec twine
twine check dist/*

# Tests de packaging
pytest tests/packaging/ -v
```

### Publication sur PyPI

```bash
# 1. Publication sur TestPyPI (pour tester)
twine upload --repository testpypi dist/*

# 2. Test d'installation depuis TestPyPI
pip install --index-url https://test.pypi.org/simple/ geneweb-py

# 3. Publication sur PyPI (production)
twine upload dist/*
```

**Note** : La publication est automatisée via GitHub Actions. Voir `.github/workflows/test-pypi.yml`

### Compatibilité

geneweb-py est testé et compatible avec :
- **Python** : 3.8, 3.9, 3.10, 3.11, 3.12 (voir `requires-python` dans `pyproject.toml`)
- **OS** : Linux, macOS, Windows
- **Architectures** : x86_64, arm64

## 🤝 Contribution

Les contributions sont les bienvenues ! Consultez le [Statut du projet](doc/status.md) et la [Roadmap](doc/roadmap.md) pour comprendre la direction actuelle et proposer des améliorations.

### Processus de contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Standards de qualité

- Tests unitaires obligatoires (couverture ≥ 90% sur les modules critiques)
- Annotations de type sur toutes les fonctions publiques
- Docstrings en français (style Google)
- **Ruff** pour le formatage et le lint (`ruff format`, `ruff check`) — aligné sur `pyproject.toml`
- Vérification des types avec **mypy** (mode strict)

## 📄 Licence

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

## 🔗 Liens utiles

- [GeneWeb GitHub repo](http://geneweb.org/)
- [Format .gw](doc/geneweb/gw_format_documentation.md)
- [Geneweb documentation by the community](https://web.archive.org/web/20250802144922/https://geneweb.tuxfamily.org/wiki/GeneWeb)
- [Issues](https://github.com/Relais4x100a2/geneweb-py/issues)
