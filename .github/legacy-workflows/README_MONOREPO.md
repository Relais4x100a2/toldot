# Workflows hérités de geneweb-py (non actifs)

GitHub n'exécute que `.github/workflows/`. Ce dossier conserve les anciens workflows de `geneweb-py`,
écrits pour un dépôt à la racine du paquet (`pip install -e .`, chemins `tests/`, `src/`), pour référence :

- `tests.yml`, `lint.yml` : remplacés par `.github/workflows/ci.yml` (uv, Python 3.11 à 3.13).
- `release.yml`, `test-pypi.yml` : publication PyPI. Non reprise (dépôt privé, secrets `PYPI_API_TOKEN` absents) ;
  à réécrire avec `uv build --package geneweb-py` le jour d'une publication.
- `pr-checks.yml`, `coverage-report.yml`, `performance.yml`, `security.yml`, `weekly-report.yml` :
  rapports ; à porter au besoin avec `uv run --package geneweb-py` et les chemins `core/…`.
