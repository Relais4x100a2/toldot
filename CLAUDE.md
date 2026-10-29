# CLAUDE.md

@AGENTS.md

Règles complètes (règle d'or sur les données réelles, workspace `uv`, Docker) dans `AGENTS.md` ; détails du moteur dans `core/AGENTS.md`.

## Commandes rapides

```bash
uv sync --all-packages --all-extras                                  # installer
uv run --package geneweb-py python -m pytest core                    # tests du core (ou: uv run --package geneweb-py pytest core)
uv run --package geneweb-app streamlit run app/docker/geneweb-app/app.py   # app Streamlit (ou ./run_app.sh)
docker compose -f app/docker-compose.yml up -d --build               # app en conteneur
```

## Rappels pour Claude Code

- Monorepo **public** : jamais de `*.gw`/`*.ged` réels, de clé d'API ni de nom de vraie personne (fixtures synthétiques uniquement).
- Pas de `git add -A` ; pas de `git push` ni `--force` sans accord explicite.
- Le paquet applicatif s'appelle `geneweb-app` (pas `app`) et vit dans `app/docker/geneweb-app/`.
