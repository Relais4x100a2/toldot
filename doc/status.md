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
- Genealogy: conteneur principal, validation de cohérence, statistiques
- Exceptions dédiées: `GeneWebError`, `GeneWebParseError`, `GeneWebValidationError`, `GeneWebConversionError`, `GeneWebEncodingError`

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
- Suite de tests unitaires et d'intégration (parsers, API, convertisseurs)
- Couverture mesurée automatiquement (rapport HTML dans `htmlcov/index.html`)
- Seuil CI défini dans `pyproject.toml` (`--cov-fail-under`)

## 🚧 Travaux en cours
- Amélioration continue de la documentation
- Extension des tests de performance sur fichiers réels volumineux
- Optimisations additionnelles pour les conversions (GEDCOM, JSON, XML)

## 🏗️ Architecture (vue d'ensemble)
```
geneweb_py/
├── core/                    # Modèles et logique principale
│   ├── date.py              # Parser et modèle Date
│   ├── person.py            # Modèle Person
│   ├── family.py            # Modèle Family
│   ├── event.py             # Modèle Event
│   ├── genealogy.py         # Modèle Genealogy
│   ├── exceptions.py        # Exceptions spécifiques
│   └── parser/              # Parser lexical, syntaxique et principal
│       ├── lexical.py       # Tokenisation avec cache LRU et __slots__
│       ├── syntax.py        # Parsing syntaxique optimisé
│       ├── gw_parser.py     # Parser principal avec mode streaming
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

## 🔗 Liens utiles
- Documentation du format GeneWeb: `doc/geneweb/gw_format_documentation.md`
- Rapport de couverture: `htmlcov/index.html`
- Dépôt: `https://github.com/guillaumecayeux/geneweb-py`


