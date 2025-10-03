# Test rapide de GeneWeb

## 🚀 Démarrage

Le service GeneWeb est maintenant déployé avec succès ! 

## 📍 Accès

- **URL**: http://localhost:2317
- **Service**: `geneweb-server` 
- **État**: ✅ Opérationnel sur le port 2317

## 🧪 Test avec l'exemple fourni

1. **Un fichier d'exemple** a été créé dans `geneweb_bases/exemple.gw`
   - Contient une famille Martin avec 3 générations
   - Format GeneWeb standard avec encodage UTF-8

2. **Convertir l'exemple en base GeneWeb** :
   ```bash
   # Entrer dans le conteneur
   docker compose exec geneweb-server bash
   
   # Convertir le fichier .gw en base
   gwc -o /usr/local/var/geneweb/martin /usr/local/var/geneweb/exemple.gw
   ```

3. **Accéder à la base** :
   - Ouvrez votre navigateur sur http://localhost:2317
   - Cliquez sur "martin" pour voir l'arbre généalogique
   - Ou accédez directement à http://localhost:2317/martin

## 🔍 Logs du service

```
geneweb-server  | GeneWeb 6.08 - Possible addresses:
geneweb-server  |    http://localhost:2317/base
geneweb-server  |    http://127.0.0.1:2317/base
geneweb-server  |    http://4a322db7dc3a:2317/base
geneweb-server  | where "base" is the name of the database
geneweb-server  | Ready 2025-09-30 20:48 port 2317...
```

## ✅ Configuration validée

- ✅ Image Docker officielle : `jeffernz/geneweb:latest`
- ✅ Port 2317 exposé et accessible
- ✅ Volume de données persistant : `./geneweb_bases`
- ✅ Service démarré avec succès
- ✅ Exemple de fichier .gw fourni

## 🔧 Commandes utiles

```bash
# Voir les logs
docker compose logs -f geneweb-server

# Redémarrer le service
docker compose restart geneweb-server

# Arrêter le service
docker compose stop geneweb-server

# Entrer dans le conteneur
docker compose exec geneweb-server bash
```

## 📁 Structure des données

```
geneweb_bases/
├── exemple.gw          # Fichier d'exemple fourni
├── martin/            # Base convertie (après gwc)
└── .gitkeep           # Maintient le répertoire dans git
```

Le déploiement de GeneWeb est maintenant opérationnel ! 🎉
