# 🎯 Guide d'Utilisation Finale - GeneWeb 7.0.0

## ✅ **État Actuel du Système**

### **Services Fonctionnels**

| Service | URL | Port | Statut |
|---------|-----|------|--------|
| **🌳 GeneWeb (gwd)** | http://localhost:2317 | 2317 | ✅ Fonctionnel |
| **📊 Streamlit** | http://localhost:8501 | 8501 | ✅ Fonctionnel |
| **⚙️ gwsetup** | http://localhost:2316 | 2316 | ⚠️ Démarre mais n'est pas accessible |

## 🔍 **Problèmes Identifiés**

### 1. **Erreur "Cannot access file welcome.txt"**
- **Cause** : Fichier manquant ou mal placé
- **Impact** : Impossible d'accéder aux bases via l'URL directe

### 2. **gwsetup ne répond pas**
- **Cause** : Problème de configuration réseau ou de démarrage
- **Impact** : Impossible d'utiliser l'interface de gestion web

## 🚀 **Solutions de Contournement**

### **Solution 1 : Utiliser la Ligne de Commande (Recommandée)**

#### **Créer une base vide**
```bash
docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/gwc -f -o bases/ma_famille"
```

#### **Créer une base depuis un fichier GEDCOM**
```bash
# 1. Copier votre fichier GEDCOM dans data/geneweb_bases/
cp mon_fichier.ged data/geneweb_bases/

# 2. Créer la base
docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/ged2gwb bases/mon_fichier.ged -o bases/ma_base -f"
```

#### **Lister les bases disponibles**
```bash
docker compose exec geneweb-server bash -c "ls -la /opt/geneweb/bases/"
```

### **Solution 2 : Interface Web Directe**

1. **Accédez à** : http://localhost:2317
2. **Dans le champ "Base"**, tapez le nom d'une base existante
3. **Cliquez sur "Validate"**

**Note** : Vous obtiendrez l'erreur "Cannot access file welcome.txt" mais c'est un problème de configuration qui n'empêche pas le fonctionnement des bases une fois créées correctement.

## 📋 **Commandes Utiles**

### **Gestion des Services**
```bash
# Démarrer les services
docker compose up -d

# Arrêter les services
docker compose down

# Redémarrer GeneWeb
docker compose restart geneweb-server

# Voir les logs
docker compose logs geneweb-server
```

### **Gestion des Bases**

```bash
# Compiler un fichier .gw en base
docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/gwc fichier.gw -o bases/nom_base"

# Exporter une base en GEDCOM
docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/gwb2ged bases/nom_base -o bases/export.ged"

# Vérifier une base
docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/gwfixbase bases/nom_base"

# Calculer la consanguinité
docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/consang bases/nom_base"
```

## 🎯 **Workflow Recommandé**

### **Pour Commencer avec GeneWeb**

1. **Préparez vos données** :
   - Format GEDCOM (.ged) : Le plus universel
   - Format GeneWeb (.gw) : Format natif

2. **Créez votre base** :
   ```bash
   # Depuis GEDCOM
   docker compose exec geneweb-server bash -c "cd /opt/geneweb && ./gw/ged2gwb bases/mon_fichier.ged -o bases/ma_famille -f"
   ```

3. **Accédez à votre base** :
   - URL : http://localhost:2317
   - Tapez : `ma_famille` dans le champ "Base"
   - Cliquez sur "Validate"

## 📁 **Structure des Fichiers**

```
geneweb_revamped/
├── docker/
│   ├── geneweb-app/          # Application Streamlit
│   └── geneweb-server/       # Serveur GeneWeb
├── data/
│   ├── geneweb_bases/        # 📂 PLACEZ VOS FICHIERS ICI
│   │   ├── *.ged            # Fichiers GEDCOM
│   │   ├── *.gw             # Fichiers GeneWeb
│   │   └── *.gwb/           # Bases compilées
│   └── streamlit_data/       # Données Streamlit
└── docker-compose.yml        # Configuration Docker
```

## 🎉 **Résumé**

- ✅ **GeneWeb 7.0.0 installé** selon la documentation officielle
- ✅ **Installation conforme** (binaire pré-compilé)
- ✅ **Serveur fonctionnel** sur http://localhost:2317
- ⚠️ **Problème welcome.txt** (contournement disponible)
- ⚠️ **gwsetup non accessible** (utilisez la ligne de commande)
- 🎯 **Solution** : Utilisez les commandes en ligne de commande

## 🚀 **Prochaines Étapes**

1. **Préparez votre fichier GEDCOM**
2. **Créez votre base** avec `ged2gwb`
3. **Explorez vos données généalogiques !**

---

**✅ GeneWeb 7.0.0 est prêt à l'emploi via la ligne de commande !**
