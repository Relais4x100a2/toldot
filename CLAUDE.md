# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Testing
pytest                                         # All tests
pytest tests/unit/                             # Unit tests only
pytest tests/unit/test_parser.py              # Single test file
pytest -k "test_name"                         # Single test by name
pytest --cov=geneweb_py --cov-report=html     # With coverage HTML report
pytest -m "not slow"                          # Skip slow tests

# Linting & formatting
ruff check src/ tests/                        # Lint
ruff format src/ tests/                       # Format

# Type checking
mypy src/geneweb_py/

# API server
python run_api.py --reload                    # Dev mode with hot reload
```

**Dev install:**
```bash
pip install -e ".[dev,api]"
```

## Architecture

**geneweb-py** is a Python library for parsing, manipulating, and converting GeneWeb `.gw` genealogical files. It provides both a programmatic API and a REST API.

### Package layout (`src/geneweb_py/`)

```
core/
  parser/
    lexical.py      # Tokenization (Token, TokenType, LRU regex cache)
    syntax.py       # Syntax parsing (BlockType, SyntaxNode)
    gw_parser.py    # Orchestrator: encoding detection → lex → parse → models
    streaming.py    # Streaming mode for large files (>10MB, ~80% memory reduction)
  date.py           # Date model: multi-calendar, prefixes (~/?/</>), ranges
  person.py         # Person dataclass
  family.py         # Family dataclass (spouses, children, witnesses)
  event.py          # Event dataclass (personal/family)
  genealogy.py      # Top-level container: Genealogy(persons, families, metadata)
  exceptions.py     # GeneWebParseError, GeneWebValidationError, GeneWebEncodingError
  validation.py     # Validation with graceful/strict modes
  models.py         # Re-exports all public model classes

api/
  main.py                      # FastAPI app, CORS, security headers
  routers/{persons,families,events,genealogy}.py
  services/genealogy_service.py  # Business logic between API and models
  models/{person,family,event,responses}.py  # Pydantic models
  middleware/{error_handler,logging}.py

formats/
  base.py    # Abstract exporter/importer base classes
  gedcom.py  # GEDCOM conversion
  json.py    # JSON conversion
  xml.py     # XML conversion
```

### Data flow

```
.gw file
  → lexical.py  (tokenize)
  → syntax.py   (SyntaxNode tree)
  → gw_parser.py (Genealogy dataclass)
  → formats/    (GEDCOM / JSON / XML export)
     or api/    (REST endpoints)
```

### Key design decisions

- **Dataclasses** for all models (Date, Person, Family, Event, Genealogy)
- **Strict mypy** throughout — always add type annotations
- **Error collector pattern**: `validation.py` accumulates errors in graceful mode rather than raising on the first issue
- **Token/SyntaxNode use `__slots__`** for memory efficiency in the hot parsing path
- **`lark` is listed as an optional dep but is NOT used** by the current parser (pure regex/hand-rolled)
- Coverage threshold is **80%** — do not drop below it

### Test markers

`slow`, `integration`, `unit`, `coverage`, `parser`, `validation`, `formats`, `api`

## GeneWeb `.gw` format

Spec: `doc/geneweb/gw_format_documentation.md`

Key syntax elements handled by the parser:
- `fam` blocks (family), `ind` blocks (individual)
- `wit` (witnesses), `sep`/`div` (separation/divorce)
- `beg`/`end` children blocks
- Comments starting with `*`
- Occurrence numbers for disambiguation (e.g. `Dupont.1`)
- Multi-calendar dates, date prefixes, date ranges
