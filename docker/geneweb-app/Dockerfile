# Dockerfile pour l'application Streamlit
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="Guillaume Cayeux"
LABEL description="GeneWeb AI Processor - Application Streamlit avec DSPY"
LABEL version="0.2.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_TELEMETRY=false

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Installer uv (gestionnaire de paquets Python ultra-rapide)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:$PATH"

# Créer les dossiers nécessaires
RUN mkdir -p /opt/geneweb/data/training \
    && mkdir -p /opt/geneweb/bases \
    && mkdir -p /app

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances (verrouillées par uv.lock)
COPY pyproject.toml uv.lock ./

# Installer les dépendances de production exactement telles que verrouillées
RUN uv sync --frozen --no-dev --no-install-project
ENV PATH="/app/.venv/bin:$PATH"

# Copier le code source
COPY . .

# Créer un fichier de configuration Streamlit
RUN mkdir -p /root/.streamlit && \
    echo "[server]" > /root/.streamlit/config.toml && \
    echo "port = 8501" >> /root/.streamlit/config.toml && \
    echo "address = \"0.0.0.0\"" >> /root/.streamlit/config.toml && \
    echo "headless = true" >> /root/.streamlit/config.toml && \
    echo "enableCORS = false" >> /root/.streamlit/config.toml && \
    echo "enableXsrfProtection = false" >> /root/.streamlit/config.toml && \
    echo "" >> /root/.streamlit/config.toml && \
    echo "[browser]" >> /root/.streamlit/config.toml && \
    echo "gatherUsageStats = false" >> /root/.streamlit/config.toml && \
    echo "" >> /root/.streamlit/config.toml && \
    echo "[theme]" >> /root/.streamlit/config.toml && \
    echo "primaryColor = \"#2E7D32\"" >> /root/.streamlit/config.toml && \
    echo "backgroundColor = \"#FFFFFF\"" >> /root/.streamlit/config.toml && \
    echo "secondaryBackgroundColor = \"#F0F2F6\"" >> /root/.streamlit/config.toml && \
    echo "textColor = \"#262730\"" >> /root/.streamlit/config.toml && \
    echo "font = \"sans serif\"" >> /root/.streamlit/config.toml

# Créer un fichier credentials.toml (désactiver la télémétrie)
RUN echo "[general]" > /root/.streamlit/credentials.toml && \
    echo "email = \"\"" >> /root/.streamlit/credentials.toml

# Exposer le port Streamlit
EXPOSE 8501

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Commande de démarrage
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]