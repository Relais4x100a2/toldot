# Data Cleaning & Normalization - Interface Streamlit avec IA

**Date de création** : 9 octobre 2025  
**Statut** : 📋 Concept - À développer  
**Priorité** : 🟡 Moyenne  
**Complexité estimée** : 4-6 semaines  

---

## 🎯 Vision et objectifs

### Concept principal
Créer une **interface Streamlit interactive** pour nettoyer, uniformiser et corriger automatiquement les données généalogiques parsées, en exploitant les statistiques, la correspondance floue (fuzzy matching) et l'intelligence artificielle via API.

### Objectifs
- **Uniformisation** : Standardiser les formats de lieux, dates, noms
- **Détection d'erreurs** : Identifier les incohérences et doublons
- **Correction automatique** : Proposer et appliquer des corrections
- **Interface intuitive** : Streamlit pour une expérience utilisateur fluide
- **IA intégrée** : Utilisation d'APIs pour suggestions intelligentes

---

## 🏗️ Architecture proposée

### Structure de l'application
```
streamlit-data-cleaning/
├── app.py                          # Application Streamlit principale
├── pages/                          # Pages de l'application
│   ├── 01_Overview.py             # Vue d'ensemble des données
│   ├── 02_Places.py               # Nettoyage des lieux
│   ├── 03_Events.py               # Uniformisation des événements
│   ├── 04_Names.py                # Correction des noms
│   ├── 05_Notes.py                # Nettoyage des notes
│   └── 06_Export.py               # Export des données nettoyées
├── modules/                        # Modules de traitement
│   ├── data_analyzer.py           # Analyse statistique
│   ├── fuzzy_matcher.py           # Correspondance floue
│   ├── ai_corrector.py            # Corrections IA
│   ├── place_normalizer.py        # Normalisation des lieux
│   └── event_classifier.py        # Classification des événements
├── config/                         # Configuration
│   ├── settings.py                # Paramètres généraux
│   ├── ai_models.py               # Configuration IA
│   └── normalization_rules.py     # Règles de normalisation
└── utils/                          # Utilitaires
    ├── data_loader.py             # Chargement des données
    ├── export_manager.py          # Gestion des exports
    └── validation.py              # Validation des corrections
```

### Flux de données
```
Données brutes (GeneWeb) 
    ↓
Analyse statistique
    ↓
Détection des anomalies
    ↓
Suggestions IA + Fuzzy matching
    ↓
Interface utilisateur (Streamlit)
    ↓
Validation/Correction manuelle
    ↓
Export des données nettoyées
```

---

## 🔧 Modules de traitement

### 1. Data Analyzer (`data_analyzer.py`)
**Objectif** : Analyser les données pour identifier les patterns et anomalies

#### Fonctionnalités
- **Statistiques descriptives** : Distribution des lieux, dates, types d'événements
- **Détection d'outliers** : Dates impossibles, lieux improbables
- **Analyse de cohérence** : Vérification des relations logiques
- **Métriques de qualité** : Pourcentage de données complètes

#### Métriques calculées
```python
# Exemples de métriques
{
    "total_persons": 1250,
    "data_completeness": {
        "birth_dates": 0.85,
        "birth_places": 0.72,
        "death_dates": 0.68,
        "occupations": 0.45
    },
    "anomalies_detected": {
        "impossible_dates": 12,
        "duplicate_places": 45,
        "inconsistent_ages": 8
    },
    "geographic_distribution": {
        "France": 0.78,
        "Belgique": 0.12,
        "Suisse": 0.05,
        "Autres": 0.05
    }
}
```

### 2. Fuzzy Matcher (`fuzzy_matcher.py`)
**Objectif** : Identifier les doublons et variantes via correspondance floue

#### Algorithmes utilisés
- **Levenshtein Distance** : Pour les noms et lieux
- **Jaro-Winkler** : Pour les noms de famille
- **Soundex/Metaphone** : Pour les variantes phonétiques
- **Cosine Similarity** : Pour les descriptions d'événements

#### Cas d'usage
```python
# Exemples de correspondances détectées
{
    "places": [
        ("Paris", "paris", 0.95),
        ("Lyon", "Lion", 0.90),
        ("Marseille", "Marseilles", 0.88)
    ],
    "names": [
        ("Dupont", "Du Pont", 0.92),
        ("Martin", "Martins", 0.89),
        ("Bernard", "Bernhard", 0.85)
    ],
    "events": [
        ("Mariage", "mariage", 0.98),
        ("Naissance", "naissance", 0.98),
        ("Décès", "deces", 0.95)
    ]
}
```

### 3. AI Corrector (`ai_corrector.py`)
**Objectif** : Utiliser l'IA pour suggérer des corrections intelligentes

#### APIs intégrées
- **OpenAI GPT** : Suggestions contextuelles
- **Hugging Face** : Modèles spécialisés NER
- **Google Places API** : Géolocalisation et normalisation
- **Wikipedia API** : Vérification des lieux historiques

#### Types de corrections
- **Géolocalisation** : "Lyon" → "Lyon, Rhône, France"
- **Dates** : "vers 1850" → "~1850"
- **Professions** : "cultivateur" → "Agriculteur"
- **Relations** : Détection automatique des liens familiaux

### 4. Place Normalizer (`place_normalizer.py`)
**Objectif** : Standardiser et enrichir les informations géographiques

#### Fonctionnalités
- **Normalisation** : Majuscules, accents, abréviations
- **Géolocalisation** : Coordonnées GPS, codes postaux
- **Historique** : Noms anciens des lieux
- **Hiérarchie** : Commune → Département → Région → Pays

#### Base de données géographique
```python
# Structure des lieux normalisés
{
    "original": "lyon",
    "normalized": "Lyon",
    "coordinates": {"lat": 45.7640, "lng": 4.8357},
    "administrative": {
        "commune": "Lyon",
        "departement": "Rhône",
        "region": "Auvergne-Rhône-Alpes",
        "pays": "France"
    },
    "historical_names": ["Lugdunum", "Lion"],
    "confidence": 0.98
}
```

### 5. Event Classifier (`event_classifier.py`)
**Objectif** : Classifier et standardiser les événements personnalisés

#### Classification automatique
- **Types d'événements** : Naissance, mariage, décès, profession, etc.
- **Niveaux de confiance** : Score de certitude pour chaque classification
- **Suggestions de fusion** : Événements similaires à regrouper

#### Règles de classification
```python
# Exemples de règles
{
    "birth_indicators": ["né", "naissance", "baptême", "baptisé"],
    "death_indicators": ["décédé", "mort", "enterrement", "inhumé"],
    "marriage_indicators": ["marié", "épousé", "union", "noces"],
    "occupation_indicators": ["profession", "métier", "travail", "emploi"]
}
```

---

## 🎨 Interface Streamlit

### Page 1 : Overview (`01_Overview.py`)
**Objectif** : Vue d'ensemble des données et métriques de qualité

#### Widgets
- **Métriques globales** : Nombre de personnes, familles, événements
- **Graphiques de qualité** : Pourcentage de données complètes
- **Carte géographique** : Distribution des lieux
- **Timeline** : Répartition temporelle des événements
- **Alertes** : Anomalies détectées automatiquement

#### Visualisations
```python
# Exemples de graphiques
- st.metric("Qualité globale", "78%", "↗️ +5%")
- st.plotly_chart(geographic_distribution_map)
- st.plotly_chart(timeline_chart)
- st.dataframe(anomalies_table)
```

### Page 2 : Places (`02_Places.py`)
**Objectif** : Nettoyage et normalisation des lieux

#### Fonctionnalités
- **Liste des lieux** : Avec compteurs d'occurrence
- **Suggestions de fusion** : Lieux similaires détectés
- **Géolocalisation** : Enrichissement automatique
- **Validation manuelle** : Interface de correction
- **Prévisualisation** : Avant/après normalisation

#### Interface
```python
# Widgets Streamlit
col1, col2 = st.columns(2)
with col1:
    st.subheader("Lieux à normaliser")
    selected_place = st.selectbox("Choisir un lieu", places_list)
    st.write(f"Occurrences: {place_count[selected_place]}")
    
with col2:
    st.subheader("Suggestions")
    st.write("Lieux similaires détectés:")
    for suggestion in fuzzy_suggestions:
        st.checkbox(f"{suggestion['name']} (confiance: {suggestion['confidence']})")
```

### Page 3 : Events (`03_Events.py`)
**Objectif** : Classification et uniformisation des événements

#### Fonctionnalités
- **Classification automatique** : Types d'événements détectés
- **Fusion d'événements** : Regroupement des doublons
- **Standardisation** : Format uniforme des descriptions
- **Validation IA** : Suggestions de corrections

### Page 4 : Names (`04_Names.py`)
**Objectif** : Correction et standardisation des noms

#### Fonctionnalités
- **Détection de variantes** : Noms similaires
- **Correction orthographique** : Erreurs de frappe
- **Standardisation** : Format uniforme
- **Détection de doublons** : Personnes en double

### Page 5 : Notes (`05_Notes.py`)
**Objectif** : Nettoyage et structuration des notes

#### Fonctionnalités
- **Extraction d'informations** : Dates, lieux, personnes
- **Structuration** : Formatage automatique
- **Détection de sources** : Identification des références
- **Nettoyage** : Suppression des doublons

### Page 6 : Export (`06_Export.py`)
**Objectif** : Export des données nettoyées

#### Options d'export
- **Format GeneWeb** : Fichier .gw corrigé
- **GEDCOM** : Export standard
- **JSON** : Données structurées
- **Rapport** : Résumé des corrections appliquées

---

## 🤖 Intégration IA

### APIs externes

#### OpenAI GPT
```python
# Exemple d'utilisation
def suggest_place_correction(place_name: str) -> dict:
    prompt = f"""
    Normalise ce nom de lieu français historique: "{place_name}"
    Retourne le nom moderne, les coordonnées et le contexte historique.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return parse_ai_response(response)
```

#### Hugging Face
```python
# Modèle NER pour extraction d'entités
from transformers import pipeline

ner_pipeline = pipeline("ner", model="dbmdz/bert-large-cased-finetuned-conll03-english")

def extract_entities_from_notes(notes: str) -> list:
    entities = ner_pipeline(notes)
    return [{"text": e["word"], "label": e["entity"]} for e in entities]
```

#### Google Places API
```python
# Géolocalisation et normalisation
def geocode_place(place_name: str) -> dict:
    result = places_client.find_place(
        input=place_name,
        input_type="textquery",
        fields=["formatted_address", "geometry", "place_id"]
    )
    return result
```

### Modèles locaux

#### Modèle de classification d'événements
```python
# Entraînement sur données généalogiques
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier

def train_event_classifier(events_data: list) -> RandomForestClassifier:
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform([event["description"] for event in events_data])
    y = [event["type"] for event in events_data]
    
    classifier = RandomForestClassifier()
    classifier.fit(X, y)
    return classifier
```

---

## 📊 Métriques et KPIs

### Métriques de qualité
- **Complétude** : % de champs renseignés
- **Cohérence** : % de données logiquement cohérentes
- **Unicité** : % de doublons détectés et corrigés
- **Précision** : % de corrections validées par l'utilisateur

### Métriques de performance
- **Temps de traitement** : Durée d'analyse des données
- **Taux de détection** : % d'anomalies identifiées
- **Précision IA** : % de suggestions correctes
- **Adoption** : % de corrections acceptées

### Tableau de bord
```python
# Métriques en temps réel
{
    "data_quality": {
        "completeness": 0.78,
        "consistency": 0.85,
        "uniqueness": 0.92,
        "accuracy": 0.88
    },
    "processing_stats": {
        "total_processed": 1250,
        "anomalies_found": 45,
        "corrections_applied": 38,
        "user_validations": 35
    },
    "ai_performance": {
        "suggestion_accuracy": 0.82,
        "processing_time": "2.3s",
        "api_calls": 156,
        "cost_estimate": "$0.45"
    }
}
```

---

## 🚀 Plan de développement

### Phase 1 : Infrastructure de base (2 semaines)
- [ ] Configuration Streamlit et structure de l'app
- [ ] Module de chargement des données geneweb-py
- [ ] Page Overview avec métriques de base
- [ ] Tests unitaires des modules principaux

### Phase 2 : Modules de traitement (2 semaines)
- [ ] Data Analyzer avec statistiques descriptives
- [ ] Fuzzy Matcher avec algorithmes de correspondance
- [ ] Place Normalizer avec base géographique
- [ ] Interface de validation manuelle

### Phase 3 : Intégration IA (1-2 semaines)
- [ ] Configuration des APIs externes
- [ ] Module AI Corrector avec suggestions
- [ ] Modèles de classification locaux
- [ ] Optimisation des performances

### Phase 4 : Interface avancée (1 semaine)
- [ ] Pages spécialisées (Events, Names, Notes)
- [ ] Visualisations interactives
- [ ] Export et rapports
- [ ] Documentation utilisateur

---

## 🔧 Considérations techniques

### Performance
- **Traitement par lots** : Gestion des grandes bases de données
- **Cache intelligent** : Mise en cache des résultats IA
- **Parallélisation** : Traitement multi-thread des corrections
- **Optimisation mémoire** : Streaming pour gros volumes

### Sécurité
- **APIs externes** : Gestion sécurisée des clés
- **Données sensibles** : Chiffrement des informations personnelles
- **Audit trail** : Traçabilité des modifications
- **Backup** : Sauvegarde avant corrections

### Scalabilité
- **Base de données** : Stockage des règles et corrections
- **Microservices** : Architecture modulaire
- **Load balancing** : Distribution de charge
- **Monitoring** : Surveillance des performances

---

## 🎯 Cas d'usage prioritaires

### Généalogiste amateur
- **Nettoyage rapide** : Interface simple pour corrections de base
- **Détection d'erreurs** : Identification automatique des incohérences
- **Suggestions intelligentes** : Aide à la correction
- **Export propre** : Données prêtes pour publication

### Chercheur professionnel
- **Analyse statistique** : Métriques de qualité détaillées
- **Corrections en masse** : Traitement de grandes bases
- **Validation experte** : Interface de contrôle avancée
- **Rapports détaillés** : Documentation des modifications

### Archiviste
- **Standardisation** : Uniformisation des formats
- **Géolocalisation** : Enrichissement des lieux
- **Classification** : Organisation des événements
- **Préservation** : Sauvegarde des données originales

---

## 🔮 Évolutions futures

### Fonctionnalités avancées
- **Machine Learning** : Modèles entraînés sur données généalogiques
- **OCR intégré** : Reconnaissance de documents scannés
- **Blockchain** : Traçabilité des modifications
- **API REST** : Intégration avec d'autres outils

### Intégrations
- **Bases de données** : PostgreSQL, MongoDB
- **Services cloud** : AWS, Google Cloud, Azure
- **Outils généalogiques** : Gramps, FamilySearch
- **Systèmes d'information** : ERP, CRM

### Formats d'export
- **Web** : Interface web dédiée
- **Mobile** : Application mobile
- **Desktop** : Application native
- **Cloud** : Service SaaS

---

## 📚 Ressources et références

### Technologies
- [Streamlit](https://streamlit.io/) - Framework d'interface
- [FuzzyWuzzy](https://github.com/seatgeek/fuzzywuzzy) - Correspondance floue
- [OpenAI API](https://openai.com/api/) - Intelligence artificielle
- [Hugging Face](https://huggingface.co/) - Modèles NLP

### Bibliothèques Python
- [scikit-learn](https://scikit-learn.org/) - Machine Learning
- [pandas](https://pandas.pydata.org/) - Manipulation de données
- [plotly](https://plotly.com/python/) - Visualisations
- [geopy](https://geopy.readthedocs.io/) - Géolocalisation

### Standards
- [GEDCOM](https://www.gedcom.org/) - Format généalogique
- [ISO 19115](https://www.iso.org/standard/26020.html) - Métadonnées géographiques
- [GeoNames](https://www.geonames.org/) - Base de données géographique

---

## 📝 Notes de développement

### Défis identifiés
- **Performance IA** : Coût et latence des APIs externes
- **Qualité des données** : Variabilité des sources généalogiques
- **Interface utilisateur** : Équilibre entre automatisation et contrôle
- **Validation** : Fiabilité des corrections automatiques

### Solutions envisagées
- **Cache intelligent** : Réduction des appels API
- **Règles configurables** : Adaptation aux besoins spécifiques
- **Mode hybride** : Automatisation + validation manuelle
- **Tests A/B** : Validation des algorithmes

### Questions ouvertes
- **Modèles IA** : Entraînement sur données généalogiques ?
- **APIs** : Quels services externes privilégier ?
- **Interface** : Streamlit ou solution web complète ?
- **Déploiement** : Local, cloud ou hybride ?

---

**Dernière mise à jour** : 9 octobre 2025  
**Prochaine révision** : À définir selon priorité projet  
**Contact** : projet geneweb-py
