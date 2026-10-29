#!/usr/bin/env bash
# Lance l'application Streamlit depuis la racine du monorepo (workspace uv).
# Usage : ./run_app.sh [options streamlit, ex. --server.port 8502]
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
exec uv run --package geneweb-app streamlit run app/docker/geneweb-app/app.py "$@"
