#!/bin/bash

# Script de setup rapide
echo "🌳 Setup de GeneWeb AI Processor"

# Rendre le script d'installation exécutable
chmod +x install.sh

# Copier .env.example si .env n'existe pas
if [ ! -f "../../.env" ]; then
    if [ -f ".env.example" ]; then
        echo "📝 Création du fichier .env depuis .env.example"
        cp .env.example ../../.env
        echo "⚠️  N'oubliez pas de renseigner votre clé API_KEY_OPENROUTER dans ../../.env"
    fi
fi

echo "✅ Setup terminé!"
echo "Lancez maintenant: ./install.sh"