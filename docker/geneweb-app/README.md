# 🌳 GeneWeb AI Processor

Application Streamlit intelligente pour nettoyer et transformer les événements PEVT personnalisés de GeneWeb en utilisant l'IA et DSPY.

## 🎯 Objectif

Transformer des événements PEVT personnalisés (non-standard) en données structurées et normalisées grâce à :
- **Annotation manuelle** de 20-30 exemples
- **Enrichissement de prompt** par l'IA
- **Optimisation DSPY** automatique
- **Validation** et itération
- **Transformation de masse** automatisée

## 📋 Prérequis

- Python 3.11+
- Docker et Docker Compose
- Clé API OpenAI ou Anthropic
- Fichier `.gw` (format GeneWeb)

## 🚀 Installation

### 1. Avec Docker Compose (recommandé)

```bash
# Depuis la racine du projet
docker compose up -d
```

L'application sera disponible sur http://localhost:8501

### 2. Installation locale avec uv

```bash
cd docker/geneweb-app

# Installer les dépendances
uv pip install -e .

# Configurer les variables d'environnement
export OPENAI_API_KEY="votre_clé"
# OU
export ANTHROPIC_API_KEY="votre_clé"

# Lancer l'application
streamlit run app.py
```

## 📖 Guide d'utilisation

### Workflow complet

#### 1️⃣ Upload & Extraction
- Uploadez votre fichier `.gw`
- L'application extrait automatiquement les PEVT personnalisés
- Générez un échantillon diversifié (20-30 exemples recommandés)

#### 2️⃣ Annotation Manuelle
- Annotez les exemples un par un
- Côté gauche : données originales (non transformées)
- Côté droit : données nettoyées à renseigner
  - Type d'événement normalisé
  - Date au format ISO
  - Lieu structuré (ville, code INSEE, département, etc.)
  - Organisation/institution
  - Description claire
  - Score de confiance

#### 3️⃣ Enrichissement du Prompt
- Configurez votre API (OpenAI ou Anthropic)
- L'IA analyse vos annotations
- Le prompt de base est enrichi avec :
  - Règles spécifiques identifiées
  - Patterns de transformation
  - Exemples concrets
  - Cas particuliers

#### 4️⃣ Optimisation DSPY
- Configurez le split des données (60% train / 20% val / 20% test)
- DSPY optimise automatiquement le prompt
- Teste différentes stratégies de few-shot learning
- Évaluation sur le set de validation

#### 5️⃣ Validation
- Testez le modèle sur de nouveaux exemples
- Validez ou corrigez les transformations
- Métriques en temps réel (accuracy, etc.)
- Décisions basées sur les performances :
  - ✅ ≥80% : Passer à la transformation de masse
  - ⚠️ 60-80% : Annoter plus d'exemples et réoptimiser
  - ❌ <60% : Revoir les annotations et le prompt

#### 6️⃣ Transformation de Masse
- Appliquez le modèle à tous vos PEVT
- Traitement par batches
- Marquage automatique des transformations à réviser (confiance < 70%)
- Export en JSON, CSV ou JSONL

#### 7️⃣ Dashboard
- Vue d'ensemble complète
- Statistiques détaillées par étape
- Historique des versions de prompts
- Export complet du projet

## 📂 Structure du Projet

```
docker/geneweb-app/
├── app.py                          # Application principale
├── pyproject.toml                  # Dépendances
├── README.md                       # Ce fichier
├── src/                            # Code source
│   ├── __init__.py
│   ├── data_models.py              # Modèles de données
│   ├── gw_parser.py                # Parser de fichiers .gw
│   ├── pevt_extractor.py           # Extraction des PEVT
│   ├── dspy_optimizer.py           # Optimisation DSPY
│   └── utils.py                    # Utilitaires
└── pages/                          # Pages Streamlit
    ├── 1_📤_Upload_Extraction.py
    ├── 2_✏️_Annotation.py
    ├── 3_🤖_Enrichissement_Prompt.py
    ├── 4_🔧_Optimisation_DSPY.py
    ├── 5_✅_Validation.py
    ├── 6_🚀_Transformation_Masse.py
    └── 7_📊_Dashboard.py
```

## 🔧 Configuration

### Variables d'environnement

```bash
# API Keys
OPENAI_API_KEY=sk-...           # Pour OpenAI
ANTHROPIC_API_KEY=sk-ant-...    # Pour Anthropic

# Données (optionnel, par défaut /opt/geneweb/data)
DATA_DIR=/chemin/vers/données
```

### Modèles supportés

**OpenAI:**
- `gpt-4o` (recommandé pour la qualité)
- `gpt-4o-mini` (recommandé pour le coût)
- `gpt-4-turbo`

**Anthropic:**
- `claude-3-5-sonnet-20241022` (recommandé)
- `claude-3-opus-20240229`

## 💾 Données sauvegardées

Toutes les données sont sauvegardées dans `/opt/geneweb/data/training/` :

- `annotations.jsonl` : Annotations manuelles
- `prompts.json` : Historique des versions de prompts
- `validations.jsonl` : Résultats de validation
- `metrics.json` : Métriques de performance
- `pevt_transformed_*.json` : Résultats de transformation de masse
- `dspy_model_*.json` : Modèles DSPY optimisés

## 📊 Métriques

### Annotation
- Temps moyen par annotation
- Distribution des types d'événements
- Scores de confiance

### Validation
- Accuracy (taux de transformations correctes)
- Types d'erreurs détectés
- Évolution de la performance

### Transformation de masse
- Nombre de transformations réussies
- Transformations à réviser (confiance < seuil)
- Distribution des scores de confiance

## 🐛 Dépannage

### Problème : L'upload de fichier échoue
**Solution :** Vérifiez que le fichier est bien au format `.gw` et encodé en UTF-8

### Problème : Erreur API lors de l'enrichissement
**Solution :** Vérifiez votre clé API et vos quotas

### Problème : DSPY est très lent
**Solution :** 
- Utilisez `gpt-4o-mini` au lieu de `gpt-4o`
- Réduisez `max_bootstrapped_demos` et `max_labeled_demos`
- Réduisez la taille du set de validation

### Problème : Mauvaise performance (accuracy <60%)
**Solutions :**
1. Vérifiez la cohérence de vos annotations
2. Annotez plus d'exemples (40-50)
3. Enrichissez à nouveau le prompt
4. Ajoutez plus de détails dans les descriptions

## 🤝 Contribution

Pour contribuer :
1. Créez une branche feature
2. Implémentez vos modifications
3. Ajoutez des tests si nécessaire
4. Créez une Pull Request

## 📝 Licence

Ce projet fait partie de GeneWeb Revamped.

## 🙏 Remerciements

- **GeneWeb** pour le format et les outils de généalogie
- **DSPY** pour le framework d'optimisation de prompts
- **Streamlit** pour le framework d'interface utilisateur

---

**✨ Développé avec ❤️ pour la généalogie**
```

Voilà ! J'ai créé une architecture complète avec :

## ✅ Ce qui a été créé :

1. **Fichier principal** : `app.py` - Interface d'accueil
2. **Modules source** (dans `src/`) :
   - `data_models.py` - Modèles de données
   - `gw_parser.py` - Parser de fichiers .gw
   - `pevt_extractor.py` - Extraction intelligente
   - `dspy_optimizer.py` - Optimisation DSPY
   - `utils.py` - Utilitaires et DataManager
3. **7 Pages Streamlit** (workflow complet) :
   - Upload & Extraction
   - Annotation manuelle
   - Enrichissement du prompt
   - Optimisation DSPY
   - Validation
   - Transformation de masse
   - Dashboard
4. **Documentation** : README.md complet
5. **Dépendances** : pyproject.toml mis à jour

## 🎯 Prochaines étapes :

1. **Tester l'installation** des dépendances avec `uv`
2. **Créer le dossier** `/opt/geneweb/data/training/` pour les sauvegardes
3. **Configurer les clés API** (OpenAI ou Anthropic)
4. **Lancer l'application** et tester le workflow complet

Voulez-vous que je crée aussi :
- Un script d'installation automatique ?
- Un fichier `.env.example` pour les variables d'environnement ?
- Un Dockerfile mis à jour pour inclure toutes les dépendances ?
