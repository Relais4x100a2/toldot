#!/bin/bash

# Script d'installation automatique pour GeneWeb AI Processor
# Usage: ./install.sh

set -e

echo "🌳 Installation de GeneWeb AI Processor"
echo "========================================"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

# Vérifier Python
echo ""
echo "1. Vérification de Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    info "Python $PYTHON_VERSION trouvé"
    
    # Vérifier la version (minimum 3.11)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 11 ]); then
        error "Python 3.11+ requis, version $PYTHON_VERSION détectée"
        exit 1
    fi
else
    error "Python 3 non trouvé. Installez Python 3.11+"
    exit 1
fi

# Vérifier uv
echo ""
echo "2. Vérification de uv..."
if command -v uv &> /dev/null; then
    info "uv déjà installé"
else
    warn "uv non trouvé, installation..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    info "uv installé"
fi

# Créer les dossiers nécessaires
echo ""
echo "3. Création des dossiers..."
mkdir -p /opt/geneweb/data/training 2>/dev/null || mkdir -p ../../data/training
info "Dossiers créés"

# Vérifier le fichier .env
echo ""
echo "4. Configuration des variables d'environnement..."
if [ -f "../../.env" ]; then
    info "Fichier .env trouvé à la racine"
    
    # Vérifier si API_KEY_OPENROUTER existe
    if grep -q "API_KEY_OPENROUTER=" ../../.env; then
        info "Clé API OpenRouter configurée"
    else
        warn "API_KEY_OPENROUTER non trouvée dans .env"
        echo "Ajoutez votre clé API OpenRouter dans ../../.env :"
        echo "API_KEY_OPENROUTER=sk-or-v1-..."
    fi
else
    warn "Fichier .env non trouvé"
    echo "Créez un fichier .env à la racine avec :"
    echo "API_KEY_OPENROUTER=sk-or-v1-..."
    
    # Copier .env.example si disponible
    if [ -f ".env.example" ]; then
        cp .env.example ../../.env
        info "Fichier .env créé depuis .env.example"
        echo "⚠️  N'oubliez pas de renseigner votre clé API!"
    fi
fi

# Installation des dépendances
echo ""
echo "5. Installation des dépendances Python..."
uv pip install --system -e .
info "Dépendances installées"

# Vérifier Streamlit
echo ""
echo "6. Vérification de Streamlit..."
if uv pip show streamlit --system &> /dev/null || python3 -c "import streamlit" &> /dev/null; then
    info "Streamlit installé"
else
    error "Problème lors de l'installation de Streamlit"
    exit 1
fi

# Créer les dossiers src et pages si nécessaire
echo ""
echo "7. Vérification de la structure..."
if [ -d "src" ] && [ -d "pages" ]; then
    info "Structure du projet OK"
else
    warn "Dossiers src/ ou pages/ manquants"
fi

# Test de l'application
echo ""
echo "8. Test de l'application..."
if python3 -c "import streamlit; import pandas; import plotly" 2>/dev/null; then
    info "Modules de base disponibles"
    
    # Test DSPY (peut ne pas être installé immédiatement)
    if python3 -c "import dspy" 2>/dev/null; then
        info "DSPY disponible"
    else
        warn "DSPY non disponible - tentative d'installation..."
        uv pip install --system dspy-ai
    fi
else
    error "Certains modules sont manquants"
    exit 1
fi

# Résumé
echo ""
echo "========================================"
echo "✅ Installation terminée avec succès!"
echo "========================================"
echo ""
echo "📋 Prochaines étapes :"
echo ""
echo "1. Assurez-vous que votre clé API OpenRouter est dans ../../.env :"
echo "   API_KEY_OPENROUTER=sk-or-v1-..."
echo ""
echo "2. Lancez l'application :"
echo "   streamlit run app.py"
echo ""
echo "3. Ou avec Docker :"
echo "   cd ../.. && docker compose up -d"
echo ""
echo "4. Accédez à l'application :"
echo "   http://localhost:8501"
echo ""
echo "📚 Documentation : docker/geneweb-app/README.md"
echo ""
info "Bonne généalogie! 🌳"
