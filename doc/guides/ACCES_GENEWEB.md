# 🌐 Guide d'accès à GeneWeb 7.0.0

## ✅ **URLs d'accès disponibles**

### **1. Page d'accueil principale**
```
http://localhost:2317/
```
*Note: Demande de spécifier une base - c'est normal !*

### **2. Accès direct à la base d'exemple**
```
http://localhost:2317/martin
```
*Famille Martin avec 3 générations (7 individus)*

### **3. Interface de sélection de base**
```
http://localhost:2317/base
```
*Liste des bases disponibles*

## 🎯 **Comment utiliser GeneWeb 7.0.0**

### **Étape 1 : Accéder à une base**
1. Ouvrez votre navigateur
2. Allez sur `http://localhost:2317/martin`
3. Vous verrez l'arbre généalogique de la famille Martin

### **Étape 2 : Naviguer dans l'arbre**
- **Cliquez sur un nom** pour voir les détails d'une personne
- **Utilisez les flèches** pour naviguer dans l'arbre
- **Consultez les menus** pour différentes vues (parents, enfants, etc.)

### **Étape 3 : Ajouter vos propres bases**
```bash
# Convertir un fichier GEDCOM
docker compose exec geneweb-server bash
cd /opt/geneweb
./gw/ged2gwb mon_fichier.ged -o bases/ma_base

# Accéder à votre base
http://localhost:2317/ma_base
```

## 🔧 **Résolution des problèmes**

### **Si vous voyez "Base" avec un champ de validation :**
- C'est normal ! Tapez le nom de votre base (ex: `martin`)
- Ou utilisez directement l'URL : `http://localhost:2317/martin`

### **Si vous voyez "[cannot access base]" :**
- Vérifiez que la base existe : `docker compose exec geneweb-server ls -la /opt/geneweb/bases/`
- Recréez la base si nécessaire

### **Si vous voyez "Cannot access file welcome.txt" :**
- Utilisez l'URL directe vers votre base : `http://localhost:2317/martin`

## 📊 **Services disponibles**

> 📋 **Configuration complète** : Consultez la [configuration commune](../common/configuration.md) pour tous les détails.

| Service | URL | Description |
|---------|-----|-------------|
| **GeneWeb 7.0.0** | http://localhost:2317 | Serveur généalogique |
| **Base Martin** | http://localhost:2317/martin | Exemple avec 3 générations |
| **Streamlit App** | http://localhost:8501 | Votre application de traitement |

## 🎉 **Test rapide**

1. Ouvrez http://localhost:2317/martin
2. Vous devriez voir la famille Martin
3. Cliquez sur "Jean Martin" pour voir ses détails
4. Explorez les liens familiaux !

---

**GeneWeb 7.0.0 est maintenant pleinement fonctionnel ! 🌟**
