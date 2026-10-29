#!/bin/bash

echo "🌳 Installation Simple de GeneWeb AI Processor"
echo "=============================================="

# Installation directe des dépendances
echo "Installation des dépendances..."

uv pip install --system \
    streamlit>=1.28.0 \
    pandas>=2.0.0 \
    plotly>=5.15.0 \
    dspy-ai>=2.4.0 \
    openai>=1.0.0 \
    anthropic>=0.18.0 \
    python-dotenv>=1.0.0 \
    scikit-learn>=1.3.0 \
    jsonlines>=4.0.0

echo ""
echo "✅ Installation terminée!"
echo ""
echo "Lancez l'application avec :"
echo "  streamlit run app.py"
