#!/bin/bash

# Script pour configurer l'accès direct aux fichiers .gw
# Les fichiers .gw sont le format natif de GeneWeb, pas besoin de conversion !

set -e

if [ $# -ne 1 ]; then
    echo "Usage: $0 <nom_fichier.gw>"
    echo "Exemple: $0 famille_martin.gw"
    echo ""
    echo "Le fichier sera accessible directement via GeneWeb !"
    exit 1
fi

GW_FILE="$1"
BASE_NAME="${GW_FILE%.gw}"  # Retire l'extension .gw

echo "🌳 Configuration de l'accès direct au fichier .gw..."
echo "📁 Fichier source: $GW_FILE"
echo "🗂️  Nom de base: $BASE_NAME"

# Vérifier que le fichier existe
if [ ! -f "data/geneweb_bases/$GW_FILE" ]; then
    echo "❌ Erreur: Le fichier data/geneweb_bases/$GW_FILE n'existe pas"
    echo "📁 Fichiers disponibles dans data/geneweb_bases/:"
    ls -la data/geneweb_bases/*.gw 2>/dev/null || echo "   Aucun fichier .gw trouvé"
    exit 1
fi

echo "✅ Fichier .gw trouvé !"
echo ""
echo "🎉 Configuration terminée !"
echo "🌐 Accès direct à votre base: http://localhost:2317/$BASE_NAME"
echo ""
echo "📝 Note: Les fichiers .gw sont le format natif de GeneWeb."
echo "   Aucune conversion n'est nécessaire - GeneWeb les lit directement !"
echo ""
echo "📊 Fichiers .gw disponibles:"
ls -la data/geneweb_bases/*.gw 2>/dev/null | awk '{print "   - " $9 " → http://localhost:2317/" substr($9,1,length($9)-3)}'
