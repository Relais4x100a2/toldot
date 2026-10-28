# AGENTS.md : geneweb-py

Consignes pour les assistants de code (Claude Code, Cursor, Codex…) sur ce dépôt.

**geneweb-py** parse, manipule et convertit les fichiers généalogiques GeneWeb (`.gw`). C'est le **moteur central (`core`)** de
l'écosystème TOLDOT : source de vérité pour le parsing `.gw`, les entités métier (dont l'entité `Organisation`, à venir),
l'export (GEDCOM / JSON / XML) et l'API REST. Il fournit une bibliothèque Python, une API REST (FastAPI) et un CLI.

Rôle dans l'écosystème : une application Streamlit/LLM (dépôt privé) et des outils d'analyse (prosopographie, graphes)
sont ou seront **consommateurs** de cette bibliothèque. Stratégie : dépôts reliés d'abord (Scénario C), monorepo TOLDOT ensuite (Scénario A).
Pas de refonte brutale : évolutions incrémentales, tests verts à chaque étape.

## RÈGLE D'OR : aucune donnée généalogique réelle dans ce dépôt (public)

- Interdit de versionner : `*.gw`, `*.gwo`, `*.ged`, `*.gedcom` issus d'une vraie base, exports CSV/HTML de vraies données,
  logs avec noms réels. Aucun nom, lieu ou date de vraie personne dans le code, les tests, les docs ou les messages de commit.
- Tests et exemples : **fixtures synthétiques uniquement** (`tests/fixtures/*.gw`, noms fictifs : `DUPONT Jean`, `MARTIN Pierre_Jean`,
  `CORNO Joseph`…). Les seules exceptions du `.gitignore` sont `!tests/fixtures/*.gw` et `!tests/fixtures/*.gwplus`.
- Pour tester à grande échelle, utiliser une base réelle **locale, hors dépôt**, en lecture seule ; ne jamais recopier son contenu.
- Avant tout commit : chemins explicites avec `git add` (pas de `-A`), puis `git diff --cached --name-only`.
- Aucun `git push` ni `--force` sans accord explicite de l'utilisateur.

## Environnement et commandes (`uv` exclusivement)

Pas de `pip install` direct. `.venv/` est local et n'est jamais commité. Dépendances dans `pyproject.toml` (+ `uv.lock`).

```bash
# Installation du dev environment
uv sync --extra dev --extra api            # + --extra cli pour le CLI

# Tests (forme fiable : python -m pytest)
uv run python -m pytest                          # toute la suite (976 passés, 19 ignorés au dernier passage)
uv run python -m pytest tests/unit/              # unitaires seulement
uv run python -m pytest tests/unit/test_lexical_parser.py   # un fichier
uv run python -m pytest -k "test_name"           # un test par nom
uv run python -m pytest --cov=geneweb_py --cov-report=html  # couverture
uv run python -m pytest -m "not slow"            # sans les tests lents

# Qualité
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/geneweb_py/

# API
uv run python run_api.py --reload                # dev : http://127.0.0.1:8000
uv run python run_api.py --env prod --workers 4  # prod
```

Python ≥ 3.8 (CI : 3.8 à 3.12 à chaque push/PR). Le seuil de couverture est de **80 %** : ne pas le faire baisser.

## Architecture (`src/geneweb_py/`)

```
core/
  parser/
    lexical.py           # Tokenisation (Token, TokenType, cache LRU de regex)
    syntax.py            # Parsing syntaxique (BlockType, SyntaxNode)
    gw_parser.py         # Orchestrateur : détection d'encodage → lex → parse → modèles
    multipass_parser.py  # Résolution des références croisées après le parse complet
    streaming.py         # Mode streaming pour gros fichiers (>10 Mo, ~80 % de mémoire en moins)
    regex_extractor.py   # Helpers d'extraction de champs par regex
  date.py           # Date : multi-calendriers, préfixes (~/?/</>), intervalles
  person.py         # Dataclass Person
  family.py         # Dataclass Family (conjoints, enfants, témoins)
  event.py          # Dataclass Event (personnel / familial)
  genealogy.py      # Conteneur : Genealogy(persons, families, metadata)
  exceptions.py     # GeneWebParseError, GeneWebValidationError, GeneWebEncodingError
  validation.py     # Validation en modes strict / gracieux
  models.py         # Ré-exporte les classes publiques du modèle

api/
  main.py                      # App FastAPI, CORS, en-têtes de sécurité, lifespan
  session_store.py             # SessionStore en mémoire (TTL, thread-safe, privacy by design)
  dependencies.py              # get_store, get_session_service (en-tête X-Session-Token)
  limits.py                    # Constantes via env : MAX_UPLOAD_BYTES, SESSION_*, CORS
  rate_limit.py                # Limiter SlowAPI (5/heure sur POST /sessions)
  routers/{persons,families,events,genealogy,sessions}.py
  services/genealogy_service.py  # Logique métier entre l'API et les modèles
  models/{person,family,event,responses}.py  # Modèles Pydantic

cli/
  entry.py      # Point d'entrée du binaire `geneweb-py` (Click)
  commands.py   # Commandes parse, convert (GEDCOM/JSON/XML), stats

formats/
  base.py / gedcom.py / json.py / xml.py   # Import/export
```

Flux de données :

```
.gw → lexical.py (tokens) → syntax.py (SyntaxNode) → gw_parser.py [+ MultiPassParser] (Genealogy)
    → formats/ (GEDCOM / JSON / XML)  ou  api/ (REST, par session)  ou  cli/
```

### API par session

Tous les endpoints de données exigent une session créée par `POST /api/v1/sessions` (upload d'un `.gw`). Le `session_token` renvoyé
doit figurer dans l'en-tête `X-Session-Token` de chaque requête. Les sessions expirent (TTL 1 h glissante par défaut) et ne sont
conservées qu'en mémoire : aucune persistance.

### Décisions de conception clés

- **Dataclasses** pour tous les modèles (Date, Person, Family, Event, Genealogy).
- **mypy strict** : toujours annoter les types ; cible `python_version = "3.8"`.
- **Collecteur d'erreurs** : `validation.py` accumule les erreurs en mode gracieux au lieu de lever à la première.
- **`__slots__`** sur Token/SyntaxNode (chemin chaud du parsing).
- **`lark` est une dépendance optionnelle mais n'est PAS utilisé** : le parser est en regex / écrit à la main.
- **Garde-fous DoS** : `_FAMILY_COMM_AGGREGATE_MAX_CHARS`, `_FEVT_MAX_EVENTS_PER_BLOCK`, etc. dans `gw_parser.py`.
- **Rate limiting** SlowAPI (désactivé en test via `conftest.py`).

### Variables d'environnement

| Variable | Défaut | Rôle |
|---|---|---|
| `GENEWEB_API_ENV` | `dev` | `dev`/`prod`/`test` : valeurs CORS par défaut |
| `ALLOWED_ORIGINS` | – | Origines CORS séparées par des virgules (prioritaire sur `CORS_ORIGINS`) |
| `GENEWEB_MAX_UPLOAD_BYTES` | 50 Mo | Taille max d'un `.gw` uploadé |
| `SESSION_MAX_SESSIONS` | 10 | Nombre max de sessions simultanées |
| `SESSION_TTL_SECONDS` | 3600 | TTL glissant par session |
| `READ_ONLY` | `false` | Désactive les endpoints d'écriture (405) |

### Marqueurs de test

`slow`, `integration`, `unit`, `coverage`, `parser`, `validation`, `formats`, `api`, `security`, `performance`.

## Format `.gw`

Spécification : `doc/geneweb/gw_format_documentation.md`. Éléments gérés par le parser :
blocs `fam` (famille) et `ind` (individu), `wit` (témoins), `sep`/`div`, enfants `beg`/`end`, commentaires `*`,
numéros d'occurrence (`Dupont.1`), dates multi-calendriers / préfixes / intervalles, extensions GW Plus (`fevt`, `#ms`/`#bs`/`#ds`),
blocs `notes-db`, `page-ext`, `wizard-note`, événements personnels `pevt`.

## Feuille de route immédiate (à valider avec l'utilisateur avant d'agir)

1. Audit comparatif du parser vs les parsers regex historiques (extraction des `pevt` / `#strng`, cas limites) : ne rien perdre.
2. Ajouter l'entité `Organisation` dans `core/` (modèle, parsing, validation, export `.gw`), spécifiée via le fork OCaml `geneweb-org`.
3. Porter les analyses de réseau/prosopographie (graphes) issues de l'ancien parser regex, comme module optionnel.
4. Permettre à l'application Streamlit/LLM de dépendre de ce paquet (via `uv`).
