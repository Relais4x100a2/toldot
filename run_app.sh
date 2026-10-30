#!/usr/bin/env bash
# Lance l'application Streamlit depuis la racine du monorepo (workspace uv).
# Usage : ./run_app.sh [options streamlit, ex. --server.port 8502]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
# Confinement en boucle locale : les bases chargées ne doivent jamais être joignables par le réseau.
exec uv run --package geneweb-app streamlit run app/docker/geneweb-app/app.py \
  --server.address 127.0.0.1 --browser.serverAddress localhost "$@"
