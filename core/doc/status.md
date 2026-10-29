# État du projet geneweb-py

## 🎉 Résumé

geneweb-py est une librairie Python pour parser, manipuler et convertir les fichiers généalogiques GeneWeb (.gw), assortie d'une API REST moderne. Le projet dispose d'une architecture modulaire, d'un parser avancé, de convertisseurs (GEDCOM/JSON/XML), d'exemples et d'une suite de tests.

## Source de vérité des métriques

Pour éviter des pourcentages ou des comptages de tests contradictoires entre README, `CHANGELOG.md`, `DOCUMENTATION.md` et la CI :

- **Couverture agrégée (CI / branche `main`)** : [Codecov — geneweb-py](https://codecov.io/gh/Relais4x100a2/geneweb-py) (rapports générés par le workflow *Tests et Couverture*).
- **Instantané chiffré dans le dépôt** : ce fichier (`doc/status.md`) est **le seul** document où l’on consigne des nombres absolus (tests passants/skippés, total de couverture) pour la documentation ; les autres fichiers **renvoient** ici ou vers Codecov.
- **Seuils automatiques** : le job principal des tests utilise `--cov-fail-under=80` ; les vérifications de PR utilisent `--cov-fail-under=84` (voir `.github/workflows/tests.yml` et `pr-checks.yml`).

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

### Couverture de tests : **88%** ✅

**Dernière mise à jour documentaire** : 7 mai 2026 — instantané obtenu avec  
`python3 -m pytest tests/ --cov=src/geneweb_py` (extras `dev`, `api`, `validation`).

| Catégorie | Indication | Détail |
|-----------|------------|--------|
| **Core** (date, person, family, validation…) | Très majorité > 90 % sur les modules ciblés | Rapport HTML local `htmlcov/index.html` |
| **Parser** (lexical, syntax, gw_parser, streaming) | Majorité > 85 % | idem |
| **API** | Variable selon routers/services | idem |
| **Formats** | Variable (ex. XML plus bas que JSON/GEDCOM) | idem |
| **TOTAL sur `src/geneweb_py`** | **88 %** | Doit rester ≥ seuil CI ; tendance : [Codecov](https://codecov.io/gh/Relais4x100a2/geneweb-py) |

**786 tests passants** ✅ — **28 tests skippés**

**Consolidation accomplie** : 
- **Réduction de 42 à 18 fichiers** de tests unitaires
- **Suppression des doublons** : `*_complete.py`, `*_coverage.py`
- **Structure cohérente** : Un fichier par module principal
- **Documentation complète** : README des tests et tests skippés

### Structure des tests consolidée

```
tests/
├── unit/                    # Tests unitaires (18 fichiers)
│   ├── test_date.py         # Tests pour core.date
│   ├── test_event.py        # Tests pour core.event  
│   ├── test_person.py       # Tests pour core.person
│   ├── test_family.py       # Tests pour core.family
│   ├── test_exceptions.py   # Tests pour core.exceptions
│   ├── test_validation.py   # Tests pour core.validation
│   ├── test_parser*.py      # Tests pour core.parser
│   └── test_formats*.py     # Tests pour formats.*
├── api/                     # Tests API (NOUVEAU) ✨
│   ├── test_routers_*.py    # Tests des routers FastAPI
│   ├── test_models.py       # Tests des modèles Pydantic
│   └── test_middleware.py   # Tests des middlewares
├── integration/             # Tests d'intégration
├── compatibility/           # Tests de compatibilité Python
├── packaging/              # Tests de packaging PyPI
└── security/               # Tests de sécurité
```

### Tests disponibles
- **786 tests passants** — TOUS les tests passent (0 erreur) ✅
- **28 tests skippés** — Documentés avec raisons claires (`tests/SKIPPED_TESTS.md`)
- Tests de récupération d'erreurs (`test_error_recovery.py`)
- Tests de validation gracieuse (`test_validation_graceful.py`)
- Tests de parsing complet avec vrais fichiers
- Fixtures de test avec erreurs syntaxiques et données incohérentes
- Couverture mesurée automatiquement (rapport HTML dans `htmlcov/index.html`)

### Configuration des tests
- **Couverture minimale CI** : 80 % (`--cov-fail-under` dans `tests.yml`)
- **Couverture instantanée (doc)** : 88 % sur `src/geneweb_py` (voir date ci-dessus ; confirmer sur Codecov)
- **Marqueurs** : `slow`, `integration`, `unit`, `coverage`, `parser`, `validation`, `formats`, `api`
- **Filtres d'avertissements** : Déprecations ignorées
- **Traceback court** : Pour des rapports concis

### Améliorations récentes (documentation / métriques)
- **Source unique des chiffres** : `doc/status.md` + badge Codecov ; README et index sans pourcentages divergents.
- 🧹 **Nettoyage antérieur** : 24 fichiers Markdown retirés de la racine (conformité aux règles Cursor)
- 📝 **Structure documentaire** : README, CHANGELOG, DOCUMENTATION à la racine ; détail technique dans `doc/`

## 🚧 Travaux en cours
- **Documentation** ✅ (structure stabilisée)
- **Améliorations potentielles**
  - Réduire tests skippés (voir `pytest -rs`)
  - Tests XML / formats (couverture encore plus homogène)
  - Extension tests de performance sur fichiers réels volumineux
  - Renforcer la couverture des services API où c’est pertinent

## 🏗️ Architecture (vue d'ensemble)
```
geneweb-py/
├── src/
│   └── geneweb_py/          # Package principal
│       ├── core/            # Modèles et logique principale
│       │   ├── date.py      # Parser et modèle Date
│       │   ├── person.py    # Modèle Person avec validation
│       │   ├── family.py    # Modèle Family avec validation
│       │   ├── event.py     # Modèle Event
│       │   ├── genealogy.py # Modèle Genealogy avec validation gracieuse
│       │   ├── exceptions.py # Exceptions avec messages enrichis et collecteur
│       │   ├── validation.py # Système de validation gracieuse
│       │   └── parser/      # Parser lexical, syntaxique et principal
│       │       ├── lexical.py # Tokenisation avec cache LRU et __slots__
│       │       ├── syntax.py # Parsing syntaxique optimisé
│       │       ├── gw_parser.py # Parser principal avec mode streaming et strict
│       │       └── streaming.py # Parsing streaming pour gros fichiers
│       ├── api/             # API REST (FastAPI)
│       │   ├── main.py      # Application FastAPI
│       │   ├── routers/     # Routers par entité
│       │   ├── models/      # Modèles Pydantic
│       │   ├── services/    # Services métier
│       │   └── middleware/  # Middleware
│       └── formats/         # Convertisseurs (GEDCOM/JSON/XML)
├── tests/                   # Tests unitaires et d'intégration
│   └── performance/         # Benchmarks de performance
└── examples/                # Exemples d'utilisation
```

## 🔧 Standards de code
- Type hints obligatoires pour toutes les fonctions publiques
- Docstrings en français pour les APIs publiques
- `dataclasses` pour les modèles
- Formatage et lint: **Ruff** (`ruff format`, `ruff check`, 88 colonnes) ; typage: mypy (strict)

## 🚀 Utilisation rapide
Consultez les exemples dans `examples/` ainsi que la documentation d'API (Swagger UI) exposée par l'application FastAPI.

## 🚀 Publication PyPI

**État** : ✅ Prêt pour publication v0.1.0

### Checklist PyPI

| Critère | État | Notes |
|---------|------|-------|
| **Tests fonctionnels** | ✅ Voir Codecov / tableau ci-dessus | 786 tests passants (instantané doc) |
| **Tests packaging** | ✅ 24 tests | API publique et métadonnées |
| **Tests compatibilité** | ✅ Python 3.8-3.12 | 13 tests multi-versions (CI : 5 versions × `tests.yml`) |
| **Tests sécurité** | ✅ 7 tests | Dépendances et vulnérabilités |
| **CI/CD** | ✅ GitHub Actions | 7 jobs automatisés |
| **Scripts validation** | ✅ Créés | Bash et Python |
| **Documentation** | ✅ Complète | README, CHANGELOG, LICENSE |
| **Métadonnées** | ✅ Complètes | pyproject.toml à jour |

### Publication

Le projet est **100% prêt** pour publication. Deux options :

**Option 1 - Manuelle** :
```bash
# 1. Valider
./scripts/validate_pypi.sh

# 2. Construire
python -m build

# 3. Tester sur TestPyPI
twine upload --repository testpypi dist/*

# 4. Publier sur PyPI
twine upload dist/*
```

**Option 2 - Automatique (GitHub Actions)** :
- Push sur `dev` → Publication TestPyPI
- Release GitHub → Publication PyPI

### Documentation

- [Guide publication complet](PYPI_PUBLICATION_GUIDE.md)
- [Stratégie de tests](PYPI_TESTING_STRATEGY.md)
- [Guide publication](PYPI_PUBLICATION_GUIDE.md) (démarrage inclus)
- [Script validation](../scripts/validate_pypi.sh)

## 🔗 Liens utiles
- Documentation du format GeneWeb: `doc/geneweb/gw_format_documentation.md`
- Rapport de couverture: `htmlcov/index.html`
- Stratégie tests PyPI: `doc/PYPI_TESTING_STRATEGY.md`
- Dépôt: `https://github.com/Relais4x100a2/geneweb-py`
- PyPI (bientôt): `https://pypi.org/project/geneweb-py/`


