# Tests - Structure et Organisation

## 📁 Structure des Tests

### 🎯 Organisation par Module

Les tests sont organisés par module principal avec une structure cohérente :

```
tests/
├── fixtures/               # Fichiers .gw de référence (voir section ci-dessous)
├── unit/                    # Tests unitaires par module
│   ├── test_date.py         # Tests pour core.date
│   ├── test_event.py        # Tests pour core.event  
│   ├── test_person.py       # Tests pour core.person
│   ├── test_family.py       # Tests pour core.family
│   ├── test_exceptions.py   # Tests pour core.exceptions
│   ├── test_validation.py   # Tests pour core.validation
│   ├── test_parser.py       # Tests pour core.parser
│   └── ...
├── integration/             # Tests d'intégration
├── compatibility/           # Tests de compatibilité Python
├── packaging/              # Tests de packaging PyPI
└── security/               # Tests de sécurité
```

### 🔄 Consolidation Réalisée

**Avant** : Structure redondante avec doublons
- `test_date.py` + `test_date_complete.py` + `test_date_coverage.py`
- `test_event.py` + `test_event_complete.py` + `test_event_coverage.py`
- `test_person.py` + `test_person_complete.py` + `test_person_coverage.py`
- etc.

**Après** : Structure consolidée
- Un seul fichier `test_*.py` par module principal
- Tests de couverture intégrés dans le fichier principal
- Suppression des fichiers redondants

### 📊 Couverture de Code

- **Objectif** : 80%+ de couverture globale
- **Modules critiques** : 90%+ (parser, validation, exceptions)
- **Tests de couverture** : Intégrés dans les fichiers principaux

### Répertoire `tests/fixtures/`

Fichiers `.gw` de référence pour les tests d'intégration et le mode gracieux.

| Fichier | Rôle |
| :--- | :--- |
| `simple_test.gw` | Cas minimal : une famille `fam` avec deux époux (id 0). Utilisé par `test_error_recovery.py`. |
| `minimal_iso8859.gw` | Même usage qu'un fichier minimal mais encodé en **ISO-8859-1** (sans ligne `[encoding: utf-8]`) pour valider la détection d'encodage par `chardet`. |
| `test_relations.gw` | Famille et bloc **`rel`** avec parrains/marraines (`godp`). |
| `test_witnesses.gw` | **Témoins** (`wit`), infos époux inline sur la ligne `fam`, **séparation/divorce** (`#sep`, `#div`) avant les noms de l'épouse. |
| `test_complete.gw` | Combinaison : témoins, séparation/divorce, enfants `beg`/`end`, plusieurs blocs `rel`. |
| `malformed_fragment.gw` | **Cas erroné** : première ligne invalide puis une famille valide ; avec `strict=False` le parsing doit encore produire au moins une personne (`test_malformed_fixture_still_recoverable`). |

Les lignes `[encoding: utf-8]` en tête de fichier sont évitées dans ces fixtures : elles ne correspondent pas au préfixe attendu par la validation initiale du parser (`encoding:` avec deux-points sans crochet).

### 🚫 Tests Skippés

Certains tests sont skippés pour les raisons suivantes :

1. **Données ou environnement indisponibles** : Par exemple fichier exemple très volumineux ou dépendances optionnelles
2. **Fonctionnalités non implémentées** : Features en développement
3. **Tests d'intégration complexes** : Nécessitant des données complètes ou du temps d'exécution élevé

### 🧪 Types de Tests

#### Tests Unitaires (`tests/unit/`)
- **Parsing** : Validation du parsing des formats GeneWeb
- **Modèles** : Tests des classes de données (Person, Family, Event, Date)
- **Validation** : Tests des règles de validation
- **Exceptions** : Tests de gestion d'erreurs

#### Tests d'Intégration (`tests/integration/`)
- **Parsing complet** : Tests avec des fichiers .gw réels
- **Workflows** : Tests de flux complets
- **Compatibilité** : Tests entre modules

#### Tests de Compatibilité (`tests/compatibility/`)
- **Versions Python** : Tests sur Python 3.8-3.12
- **Fonctionnalités** : Tests des features spécifiques par version
- **Dépendances** : Tests de compatibilité des dépendances

#### Tests de Packaging (`tests/packaging/`)
- **Installation** : Tests d'installation du package
- **Métadonnées** : Validation des métadonnées PyPI
- **Imports** : Tests d'importation des modules

### 🔧 Configuration des Tests

#### pytest Configuration (`pyproject.toml`)
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "coverage: marks tests for coverage analysis"
]
```

#### Couverture de Code
```bash
# Tests avec couverture
pytest --cov=geneweb_py --cov-report=html --cov-report=term

# Tests sans couverture (pour CI/CD)
pytest --no-cov
```

### 📈 Métriques de Qualité

- **Couverture globale** : 80%+
- **Tests passants** : 100%
- **Tests skippés** : Documentés avec raisons
- **Temps d'exécution** : < 30s pour la suite complète

### 🚀 Exécution des Tests

```bash
# Tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/

# Tests sans les tests lents
pytest -m "not slow"

# Tests avec couverture
pytest --cov=geneweb_py

# Tests spécifiques
pytest tests/unit/test_date.py -v
```

### 📝 Bonnes Pratiques

1. **Nommage** : `test_*.py` pour les fichiers, `test_*` pour les fonctions
2. **Classes** : `Test*` pour les classes de tests
3. **Documentation** : Docstrings en français pour les tests publics
4. **Fixtures** : Utilisation de fixtures pytest pour les données de test
5. **Assertions** : Messages d'erreur explicites
6. **Skipping** : Documentation des raisons de skip

### 🔍 Debugging des Tests

```bash
# Mode verbose
pytest -v

# Arrêt au premier échec
pytest -x

# Traceback complet
pytest --tb=long

# Tests spécifiques avec debug
pytest tests/unit/test_date.py::TestDateParsing::test_parse_simple_date -v -s
```
