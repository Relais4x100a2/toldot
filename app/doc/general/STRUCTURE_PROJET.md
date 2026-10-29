# 📁 Structure du Projet GeneWeb Revamped

## 🏗️ **Architecture Organisée**

```
geneweb_revamped/
├── 📁 docker/                          # Configuration Docker par service
│   ├── 📁 geneweb-app/                 # Application Streamlit
│   │   ├── 📄 Dockerfile               # Image Streamlit
│   │   ├── 📄 app.py                   # Code de l'application
│   │   └── 📄 pyproject.toml           # Dépendances Python
│   └── 📁 geneweb-server/              # Serveur GeneWeb 7.0.0
│       └── 📄 Dockerfile.geneweb       # Image GeneWeb
├── 📁 data/                            # Données persistantes
│   ├── 📁 geneweb_bases/               # Bases généalogiques GeneWeb
│   │   ├── 📄 exemple.ged              # Fichier GEDCOM d'exemple
│   │   ├── 📄 martin.gwb/              # Base d'exemple compilée
│   │   └── 📄 .gitkeep                 # Maintient le répertoire
│   └── 📁 streamlit_data/              # Données de l'application Streamlit
│       ├── 📄 app.py                   # Code Streamlit (copie)
│       ├── 📄 pyproject.toml           # Dépendances (copie)
│       └── 📄 uv.lock                  # Verrou des versions
├── 📄 docker-compose.yml               # Orchestration des services
├── 📄 ACCES_GENEWEB.md                 # Guide d'accès GeneWeb
├── 📄 GENEWEB_DEPLOYMENT.md            # Documentation de déploiement
├── 📄 gw_format_documentation.md       # Documentation format GW
├── 📄 README.md                        # Documentation principale
├── 📄 VISION.md                        # Vision du projet
└── 📄 pyproject.toml                   # Configuration racine (legacy)
```

## 🎯 **Avantages de cette Structure**

### **1. Séparation des Responsabilités**
- **`docker/`** : Chaque service a son propre Dockerfile
- **`data/`** : Données séparées par type (bases généalogiques vs Streamlit)
- **Racine** : Configuration globale et documentation

### **2. Modularité**
- **Développement indépendant** : Chaque service peut être modifié séparément
- **Builds optimisés** : Seuls les services modifiés sont reconstruits
- **Tests isolés** : Chaque service peut être testé individuellement

### **3. Persistance des Données**
- **`data/geneweb_bases/`** : Bases généalogiques persistantes
- **`data/streamlit_data/`** : Données et code Streamlit
- **Volumes Docker** : Mappés correctement vers les répertoires

### **4. Maintenance Facile**
- **Structure claire** : Chaque élément a sa place
- **Documentation centralisée** : Guides et docs à la racine
- **Configuration centralisée** : `docker-compose.yml` unique

## 🚀 **Utilisation**

### **Démarrage des Services**
```bash
docker compose up -d
```

### **Ajout de Bases Généalogiques**
1. Placer vos fichiers `.ged` dans `data/geneweb_bases/`
2. Convertir avec : `docker compose exec geneweb-server ./gw/ged2gwb mon_fichier.ged -o bases/ma_base`
3. Accéder via : `http://localhost:2317/ma_base`

### **Développement Streamlit**
1. Modifier `docker/geneweb-app/app.py`
2. Les changements sont reflétés via le volume monté
3. Redémarrer si nécessaire : `docker compose restart geneweb-app`

## 📊 **Services Disponibles**

| Service | URL | Description |
|---------|-----|-------------|
| **Streamlit App** | http://localhost:8501 | Application de traitement |
| **GeneWeb 7.0.0** | http://localhost:2317 | Serveur généalogique |
| **Base Martin** | http://localhost:2317/martin | Exemple avec 3 générations |

## 🔧 **Commandes Utiles**

```bash
# Voir les logs
docker compose logs -f

# Redémarrer un service
docker compose restart geneweb-server

# Accéder au shell d'un service
docker compose exec geneweb-server bash

# Reconstruire après modification
docker compose build && docker compose up -d

# Arrêter tous les services
docker compose down
```

---

**🎉 Structure optimisée pour la maintenance et l'évolutivité !**
