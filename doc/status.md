# État du projet geneweb-py

## 🎉 Résumé

geneweb-py est une librairie Python pour parser, manipuler et convertir les fichiers généalogiques GeneWeb (.gw), assortie d'une API REST moderne. Le projet dispose d'une architecture modulaire, d'un parser avancé, de convertisseurs (GEDCOM/JSON/XML), d'exemples et d'une suite de tests.

## ✅ Fonctionnalités implémentées

### 1. Structure du projet et configuration
- Configuration complète via `pyproject.toml`
- Architecture modulaire: `core/`, `api/`, `formats/`, `utils/`, `tests/`, `examples/`
- Pytest configuré avec rapport de couverture et génération `htmlcov/`
- Installation en mode développement

### 2. Modèles de données (core)
- Date: parsing de préfixes (~, ?, <, >), calendriers (Grégorien, Julien, Républicain, Hébreu), dates textuelles, alternatives OR '|' et BETWEEN '..', gestion des valeurs vides/None
- Person: noms, dates, lieux, événements, relations
- Family: époux/épouse, enfants (avec sexe), événements
- Event: événements personnels/familiaux, témoins, notes
- Genealogy: conteneur principal, validation de cohérence, statistiques, support de validation gracieuse
- Exceptions dédiées: `GeneWebError`, `GeneWebParseError`, `GeneWebValidationError`, `GeneWebConversionError`, `GeneWebEncodingError`

#### 🎯 Messages d'erreur enrichis et validation gracieuse (nouveau)
- **ErrorSeverity** : Classification des erreurs en WARNING, ERROR, CRITICAL
- **ParseWarning** : Avertissements non-bloquants pour problèmes mineurs
- **Messages contextuels** : Chaque erreur contient le numéro de ligne, le contexte, les tokens attendus/trouvés
- **GeneWebErrorCollector** : Collecte multiple d'erreurs au lieu de s'arrêter à la première
  - Mode strict (`strict=True`) : Lève exception à la première erreur (comportement par défaut)
  - Mode gracieux (`strict=False`) : Continue le parsing et collecte toutes les erreurs
  - Filtrage par type et par sévérité
  - Rapports détaillés avec résumés et statistiques
- **Validation gracieuse** :
  - Les objets `Person`, `Family`, `Genealogy` ont des attributs `is_valid` et `validation_errors`
  - Module `validation.py` avec fonctions de validation non-destructives
  - Création d'objets partiels en cas d'erreur de parsing
  - Validation bidirectionnelle des références entre personnes et familles
- **Intégration parser** : Le `GeneWebParser` supporte `strict=True/False` pour choisir le comportement

### 3. Parser GeneWeb (lexical, syntaxique, principal)
- Support des apostrophes dans les identifiants (`d'Arc`, `O'Brien`, `L'Église`)
- Gestion des caractères spéciaux dans les occupations (virgules, parenthèses, apostrophes, tirets)
- Reconnaissance des tokens spéciaux (`h`, `f`, `m`) pour les sexes
- Parsing des numéros d'occurrence (.1, .2, etc.) pour la déduplication
- Support des blocs `notes-db`, `page-ext`, `wizard-note`
- Parsing des enfants et témoins avec toutes leurs informations
- Intégration vers les modèles de données

#### 🚀 Optimisations de performance (nouveau)
- **Mode streaming automatique** : Détection automatique des gros fichiers (>10MB) avec parsing ligne par ligne
- **Réduction mémoire** : `__slots__` dans les dataclasses Token et SyntaxNode (~40% de réduction)
- **Cache LRU** : Cache des patterns regex compilés pour éviter les recompilations
- **Optimisations CPU** : 
  - Dictionnaires pour lookups O(1) au lieu de conditionnels multiples
  - Détection d'encodage optimisée (UTF-8 d'abord, chardet seulement si nécessaire)
  - Pré-compilation des symboles et mots-clés
- **Gains mesurés** (fichiers >10MB) :
  - Mémoire : ~80% de réduction avec le mode streaming
  - Vitesse : ~15-20% plus rapide pour les petits fichiers grâce aux optimisations CPU
- **Benchmarks** : `tests/performance/benchmark_parser.py` pour mesurer temps/mémoire sur différentes tailles

### 4. API REST (FastAPI)
- Endpoints CRUD pour personnes, familles, événements
- Validation des entrées (Pydantic), documentation OpenAPI/Swagger automatique
- Middleware (gestion d'erreurs, CORS, logging) avec messages enrichis pour le parsing (ligne/token/attendu)
- Services métiers dédiés

### 5. Conversion de formats
- Export: GEDCOM, JSON, XML
- Import: JSON, XML
- Convertisseurs extensibles et testés

### 6. Exemples et démonstrations
- `examples/basic_usage.py`, `examples/parser_usage.py`, `examples/api_usage.py`, `examples/conversion_usage.py`
- Fichiers de fixtures `.gw` et `.gwplus` pour tests et démos

## 🧪 Qualité et tests

### Couverture de tests : **80%+** ✅

**Dernière mise à jour** : 9 octobre 2025 - **Structure consolidée** ✅

| Catégorie | Couverture | État |
|-----------|-----------|------|
| **Modules Core** | 80-95% | ⭐ Excellent |
| **Parser** | 80-95% | ⭐ Excellent |
| **API Models** | 90-94% | ✅ Excellent |
| **API Routers** | 69-90% | 🟡 Bon |
| **API Services** | 59% | 🟡 À améliorer |
| **Formats** | 76-90% | 🟡 Bon |
| **TOTAL** | **80%+** | ⭐ Excellent |

**377 tests organisés** ✅ - Structure consolidée et cohérente

**Consolidation accomplie** : 
- **Réduction de 42 à 18 fichiers** de tests unitaires
- **Suppression des doublons** : `*_complete.py`, `*_coverage.py`
- **Structure cohérente** : Un fichier par module principal
- **Documentation complète** : README des tests et tests skippés

### Structure des tests consolidée

```
tests/
├── unit/                    # Tests unitaires (18 fichiers consolidés)
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

### Tests disponibles
- **349 tests passants** (92.6%) - Tous les tests critiques sont verts
- **28 tests skippés** (7.4%) - Documentés avec raisons (fixtures manquantes, fonctionnalités non implémentées)
- Tests de récupération d'erreurs (`test_error_recovery.py`)
- Tests de validation gracieuse (`test_validation_graceful.py`)
- Tests de parsing complet avec vrais fichiers
- Fixtures de test avec erreurs syntaxiques et données incohérentes
- Couverture mesurée automatiquement (rapport HTML dans `htmlcov/index.html`)

### Configuration des tests
- **Couverture minimale** : 80% (objectif atteint)
- **Marqueurs** : `slow`, `integration`, `unit`, `coverage`, `parser`, `validation`, `formats`
- **Filtres d'avertissements** : Déprecations ignorées
- **Traceback court** : Pour des rapports concis
- Seuil CI défini à 50% dans `pyproject.toml` (objectif 100%)

### Rapport détaillé
Voir `COVERAGE_REPORT.md` pour le rapport complet incluant :
- Couverture par module
- Lignes manquantes identifiées
- Plan d'action pour atteindre 100%
- Estimation d'effort : 17-24h pour 100%

## 🚧 Travaux en cours
- **Préparation publication PyPI** 🚀 (En cours)
  - Tests de packaging : ✅ Complets
  - Tests de compatibilité Python 3.7-3.12 : ✅ Implémentés
  - Tests de sécurité : ✅ Implémentés
  - CI/CD GitHub Actions : ✅ Configuré
  - Scripts de validation : ✅ Créés
  - Documentation : ✅ Mise à jour
- Amélioration continue de la documentation
- Extension des tests de performance sur fichiers réels volumineux
- Optimisations additionnelles pour les conversions (GEDCOM, JSON, XML)

## 🏗️ Architecture (vue d'ensemble)
```
geneweb_py/
├── core/                    # Modèles et logique principale
│   ├── date.py              # Parser et modèle Date
│   ├── person.py            # Modèle Person avec validation
│   ├── family.py            # Modèle Family avec validation
│   ├── event.py             # Modèle Event
│   ├── genealogy.py         # Modèle Genealogy avec validation gracieuse
│   ├── exceptions.py        # Exceptions avec messages enrichis et collecteur
│   ├── validation.py        # Système de validation gracieuse
│   └── parser/              # Parser lexical, syntaxique et principal
│       ├── lexical.py       # Tokenisation avec cache LRU et __slots__
│       ├── syntax.py        # Parsing syntaxique optimisé
│       ├── gw_parser.py     # Parser principal avec mode streaming et strict
│       └── streaming.py     # Parsing streaming pour gros fichiers
├── api/                     # API REST (FastAPI)
│   ├── main.py              # Application FastAPI
│   ├── routers/             # Routers par entité
│   ├── models/              # Modèles Pydantic
│   ├── services/            # Services métier
│   └── middleware/          # Middleware
├── formats/                 # Convertisseurs (GEDCOM/JSON/XML)
├── tests/                   # Tests unitaires et d'intégration
│   └── performance/         # Benchmarks de performance
└── examples/                # Exemples d'utilisation
```

## 🔧 Standards de code
- Type hints obligatoires pour toutes les fonctions publiques
- Docstrings en français pour les APIs publiques
- `dataclasses` pour les modèles
- Formatage: Black (88 colonnes), linting: Flake8, typage: mypy

## 🚀 Utilisation rapide
Consultez les exemples dans `examples/` ainsi que la documentation d'API (Swagger UI) exposée par l'application FastAPI.

## 🚀 Préparation PyPI

**État** : En préparation pour publication v0.1.0

### Checklist PyPI ✅

| Critère | État | Notes |
|---------|------|-------|
| **Tests fonctionnels** | ✅ 84% | 858 tests passent |
| **Tests packaging** | ✅ Complets | `tests/packaging/` |
| **Tests compatibilité** | ✅ Python 3.7-3.12 | `tests/compatibility/` |
| **Tests sécurité** | ✅ Implémentés | `tests/security/` |
| **CI/CD** | ✅ GitHub Actions | Publication automatisée |
| **Scripts validation** | ✅ Créés | `scripts/validate_pypi.sh` |
| **Documentation** | ✅ Complète | README, CHANGELOG, LICENSE |
| **Métadonnées** | ✅ Complètes | pyproject.toml à jour |

### Prochaines étapes

1. ✅ Finaliser tests de packaging
2. ✅ Configurer GitHub Actions pour TestPyPI/PyPI
3. ✅ Créer scripts de validation
4. ⏳ Tester publication sur TestPyPI
5. ⏳ Publication officielle sur PyPI

### Ressources

- [Stratégie de tests PyPI](PYPI_TESTING_STRATEGY.md)
- [Script de validation](../scripts/validate_pypi.sh)
- [Workflow CI/CD](../.github/workflows/test-pypi.yml)

## 🔗 Liens utiles
- Documentation du format GeneWeb: `doc/geneweb/gw_format_documentation.md`
- Rapport de couverture: `htmlcov/index.html`
- Stratégie tests PyPI: `doc/PYPI_TESTING_STRATEGY.md`
- Dépôt: `https://github.com/guillaumecayeux/geneweb-py`
- PyPI (bientôt): `https://pypi.org/project/geneweb-py/`


