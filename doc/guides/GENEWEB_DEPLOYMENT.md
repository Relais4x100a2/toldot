# Déploiement GeneWeb avec Docker Compose

Ce projet inclut maintenant un serveur GeneWeb déployé via Docker Compose aux côtés de votre application Streamlit.

## Services disponibles

> 📋 **Configuration complète** : Consultez la [configuration commune](../common/configuration.md) pour tous les détails.

### 1. geneweb-app (Streamlit)
- **Port**: 8501
- **URL**: http://localhost:8501
- **Description**: Votre application Streamlit pour le traitement des données généalogiques

### 2. geneweb-server (GeneWeb 7.0.0)
- **Port**: 2317
- **URL**: http://localhost:2317
- **Description**: Serveur web GeneWeb 7.0.0 pour consulter et gérer les bases généalogiques

## Déploiement

### Démarrer tous les services
```bash
docker-compose up -d
```

### Démarrer seulement GeneWeb
```bash
docker-compose up -d geneweb-server
```

### Voir les logs
```bash
# Tous les services
docker-compose logs -f

# Seulement GeneWeb
docker-compose logs -f geneweb-server
```

### Arrêter les services
```bash
docker-compose down
```

## Configuration GeneWeb

### Répertoires et volumes

- **Bases de données**: `./geneweb_bases` → `/opt/geneweb/bases`
  - Placez vos fichiers `.gw`, `.gwb` dans ce répertoire
  - Les données sont persistantes entre les redémarrages

- **Données partagées**: `./data` → `/opt/geneweb/shared_data`
  - Partage de données avec l'application Streamlit

### Variables d'environnement

- `GW_PORT=2317`: Port d'écoute du serveur
- `GW_LANG=fr`: Langue de l'interface (fr, en, etc.)
- `GW_BASES_DIR=/opt/geneweb/bases`: Répertoire des bases
- `GENEWEB_VERSION=v7.0.0`: Version de GeneWeb utilisée

## Utilisation

### 1. Ajouter une base généalogique

1. Placez votre fichier `.gw` dans le répertoire `geneweb_bases/`
2. Convertissez-le en base GeneWeb :
```bash
# Entrer dans le conteneur
docker compose exec geneweb-server bash

# Convertir un fichier .gw en base (GeneWeb 7.0.0)
./gw/gwc -o /opt/geneweb/bases/mabase /opt/geneweb/bases/mabase.gw
```

### 2. Accéder à l'interface web

1. Ouvrez http://localhost:2317 dans votre navigateur
2. Cliquez sur le nom de votre base pour la consulter
3. Utilisez l'interface web pour naviguer dans l'arbre généalogique

### 3. Outils disponibles

Le conteneur GeneWeb 7.0.0 inclut tous les outils standard dans le répertoire `gw/` :

- `gwd`: Serveur web (démarré automatiquement)
- `gwc`: Compilateur de bases
- `gwu`: Exportateur de bases
- `gwb2ged`: Conversion vers GEDCOM
- `ged2gwb`: Conversion depuis GEDCOM
- `gwsetup`: Interface de configuration
- `gwfixbase`: Réparation de bases

## Troubleshooting

### Le serveur ne démarre pas
- Vérifiez les logs : `docker compose logs geneweb-server`
- Vérifiez que le port 2317 n'est pas utilisé par un autre service
- Attendez le démarrage complet (environ 15 secondes)

### Base non visible
- Vérifiez que le fichier `.gw` est dans `geneweb_bases/`
- Vérifiez les permissions des fichiers
- Compilez la base avec `gwc` depuis le conteneur

### Version de GeneWeb
- Utilise GeneWeb 7.0.0 compilé depuis les sources GitHub officielles
- Version définie par `GENEWEB_VERSION=v7.0.0` dans le Dockerfile
- Pour changer de version, modifiez cette variable et reconstruisez : `docker compose build geneweb-server`

## Documentation officielle

- Site web : https://geneweb.tuxfamily.org/
- Documentation : https://geneweb.tuxfamily.org/wiki/GeneWeb
- GitHub : https://github.com/geneweb/geneweb
