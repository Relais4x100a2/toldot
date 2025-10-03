# ⚙️ Configuration Commune

Ce document centralise les informations de configuration partagées entre les différents guides.

## 🌐 Services et URLs

### **Services Disponibles**
| Service | URL | Port | Description |
|---------|-----|------|-------------|
| **Streamlit App** | http://localhost:8501 | 8501 | Application de traitement |
| **GeneWeb 7.0.0** | http://localhost:2317 | 2317 | Serveur généalogique |
| **Base Martin** | http://localhost:2317/martin | 2317 | Exemple avec 3 générations |

### **URLs d'Accès GeneWeb**
- **Page d'accueil** : http://localhost:2317/
- **Sélection de base** : http://localhost:2317/base
- **Base spécifique** : http://localhost:2317/{nom_base}

## 🐳 Configuration Docker

### **Variables d'Environnement**
```yaml
# GeneWeb Server
GW_PORT: 2317
GW_LANG: fr
GW_BASES_DIR: /opt/geneweb/bases
GENEWEB_VERSION: v7.0.0

# Streamlit App
STREAMLIT_SERVER_PORT: 8501
STREAMLIT_SERVER_ADDRESS: 0.0.0.0
```

### **Volumes Docker**
```yaml
volumes:
  - ./data/geneweb_bases:/opt/geneweb/bases
  - ./data/streamlit_data:/opt/geneweb/shared_data
```

## 📁 Structure des Répertoires

### **Répertoires de Données**
```
data/
├── geneweb_bases/          # Bases généalogiques GeneWeb
│   ├── *.gw               # Fichiers sources GeneWeb
│   ├── *.gwb/             # Bases compilées
│   └── *.ged              # Fichiers GEDCOM
└── streamlit_data/         # Données de l'application Streamlit
    ├── app.py
    ├── pyproject.toml
    └── uv.lock
```

### **Répertoires Docker**
```
docker/
├── geneweb-app/            # Application Streamlit
│   ├── Dockerfile
│   ├── app.py
│   └── pyproject.toml
└── geneweb-server/         # Serveur GeneWeb
    ├── Dockerfile
    ├── Dockerfile.geneweb
    └── geneweb-launch.sh
```

## 🔧 Commandes Utiles

### **Docker Compose**
```bash
# Démarrer tous les services
docker compose up -d

# Démarrer un service spécifique
docker compose up -d geneweb-server

# Voir les logs
docker compose logs -f

# Redémarrer un service
docker compose restart geneweb-server

# Arrêter tous les services
docker compose down
```

### **Gestion des Bases**
```bash
# Convertir un fichier .ged en base GeneWeb
docker compose exec geneweb-server bash
cd /opt/geneweb
./gw/ged2gwb mon_fichier.ged -o bases/ma_base

# Compiler un fichier .gw
./gw/gwc -o /opt/geneweb/bases/mabase /opt/geneweb/bases/mabase.gw
```

## 🚨 Résolution des Problèmes

### **Problèmes Courants**
1. **Port déjà utilisé** : Changer le port dans docker-compose.yml
2. **Base non visible** : Vérifier que le fichier est dans geneweb_bases/
3. **Erreur de compilation** : Vérifier la syntaxe du fichier .gw
4. **Service ne démarre pas** : Consulter les logs Docker

### **Commandes de Diagnostic**
```bash
# Vérifier les services
docker compose ps

# Voir les logs détaillés
docker compose logs geneweb-server

# Accéder au shell d'un service
docker compose exec geneweb-server bash

# Vérifier les bases disponibles
docker compose exec geneweb-server ls -la /opt/geneweb/bases/
```

## 📚 Documentation Officielle

- **GeneWeb** : https://geneweb.tuxfamily.org/
- **Docker Compose** : https://docs.docker.com/compose/
- **Streamlit** : https://docs.streamlit.io/
