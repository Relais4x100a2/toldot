# 🌳 Guide des Fichiers .gw - Format Natif GeneWeb

## ✅ **Fichiers .gw : Format Natif GeneWeb**

Les fichiers `.gw` sont le **format natif** de GeneWeb. Aucune conversion n'est nécessaire !

### 🎯 **Comment utiliser vos fichiers .gw**

#### **1. Placer vos fichiers**
```bash
# Copiez vos fichiers .gw dans le répertoire des bases
cp votre_fichier.gw data/geneweb_bases/
```

#### **2. Accès direct**
```bash
# Votre base est immédiatement accessible via :
http://localhost:2317/votre_fichier
# (sans l'extension .gw)
```

### 📁 **Structure Recommandée**

```
data/geneweb_bases/
├── famille_martin.gw          → http://localhost:2317/famille_martin
├── genealogie_dupont.gw       → http://localhost:2317/genealogie_dupont
├── arbre_bernard.gw          → http://localhost:2317/arbre_bernard
└── ...
```

### 🔧 **Script d'Aide**

```bash
# Utiliser le script pour configurer l'accès
./scripts/setup_gw_base.sh votre_fichier.gw
```

### 📝 **Format des Fichiers .gw**

Le format natif GeneWeb utilise une syntaxe simple :

```gw
Martin, Jean
- 0 birt 1890 #d Marseille, France
- 0 deat 1960 #d Marseille, France  
- 0 occu Cultivateur
- fam Dubois, Marie +1920 #md Marseille, France

Dubois, Marie
- 0 birt 1895 #d Lyon, France
- 0 deat 1965 #d Marseille, France
```

### 🎉 **Avantages du Format .gw**

1. **🚀 Accès Immédiat** : Pas de compilation nécessaire
2. **📝 Format Lisible** : Syntaxe simple et claire
3. **🔧 Édition Facile** : Modifiable avec n'importe quel éditeur
4. **⚡ Performance** : Chargement rapide par GeneWeb

### 🌐 **URLs d'Accès**

| Fichier | URL d'accès |
|---------|-------------|
| `famille_martin.gw` | http://localhost:2317/famille_martin |
| `genealogie.gw` | http://localhost:2317/genealogie |
| `mon_arbre.gw` | http://localhost:2317/mon_arbre |

### 📊 **Vérification des Fichiers**

```bash
# Voir tous vos fichiers .gw
ls -la data/geneweb_bases/*.gw

# Tester l'accès à une base
curl -s "http://localhost:2317/nom_de_votre_base" | grep -i "geneweb\|error"
```

---

**🎯 Vos fichiers .gw sont prêts à être utilisés directement dans GeneWeb 7.0.0 !**
