# CLAUDE.md

@AGENTS.md

Les consignes complètes (règle d'or sur les données réelles, `uv`, architecture, API, format `.gw`) sont dans `AGENTS.md`.
Les règles transverses du workspace TOLDOT se trouvent dans `../AGENTS.md` (hors dépôt).

## Commandes rapides

```bash
uv sync --extra dev --extra api                  # installer
uv run python -m pytest                          # tests (et non `uv run pytest`)
uv run python -m pytest -k "nom" -x              # un test, arrêt au premier échec
uv run ruff check src/ tests/ && uv run ruff format src/ tests/
uv run mypy src/geneweb_py/
uv run python run_api.py --reload                # API sur http://127.0.0.1:8000
```

## Rappels pour Claude Code

- Dépôt **public** : jamais de `*.gw`/`*.ged` réels ni de nom de vraie personne (fixtures synthétiques uniquement).
- Pas de `git add -A` ; pas de `git push` ni `--force` sans accord explicite.
- Couverture ≥ 80 %, mypy strict, annotations de types obligatoires.
