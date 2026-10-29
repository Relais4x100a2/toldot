# Export Obsidian - Navigation réseau généalogique

**Date de création** : 9 octobre 2025  
**Statut** : 📋 Concept - À développer  
**Priorité** : 🟡 Moyenne  
**Complexité estimée** : 3-4 semaines  

---

## 🎯 Vision et objectifs

### Concept principal
Transformer une base généalogique parsée par geneweb-py en un **dossier Obsidian navigable** permettant d'explorer les relations familiales via une interface réseau intuitive.

### Objectifs
- **Navigation intuitive** : Liens bidirectionnels entre toutes les entités
- **Visualisation réseau** : Graph view automatique des relations
- **Recherche puissante** : Recherche globale dans tout le corpus
- **Extensibilité** : Base pour plugins et fonctionnalités avancées
- **Portabilité** : Fichiers Markdown standards

---

## 🏗️ Architecture proposée

### Structure de dossiers
```
obsidian-genealogy/
├── 00-Index.md                    # Page d'accueil avec statistiques
├── 01-Personnes/                  # Fiches individuelles
│   ├── Dupont_Albert_0.md        # Une fiche par personne
│   ├── Durand_Marie_0.md
│   └── ...
├── 02-Familles/                   # Fiches familiales
│   ├── Famille_Dupont-Durand.md  # Une fiche par famille
│   └── ...
├── 03-Événements/                 # Événements par type
│   ├── Mariages/
│   ├── Naissances/
│   ├── Décès/
│   └── ...
├── 04-Lieux/                      # Fiches géographiques
│   ├── Paris.md
│   ├── Lyon.md
│   └── ...
└── 05-Statistiques/               # Analyses et métriques
    ├── Arbres-généalogiques.md
    └── Métriques.md
```

### Types de fiches

#### Fiche Personne
- **Informations personnelles** : Nom, sexe, profession, statut
- **Dates importantes** : Naissance, décès, âge
- **Lieux** : Naissance, décès, résidence
- **Familles** : En tant qu'enfant et époux(se)
- **Événements personnels** : Liste chronologique
- **Relations** : Liens vers autres personnes
- **Notes** : Commentaires et sources

#### Fiche Famille
- **Époux** : Liens vers fiches personnes
- **Mariage** : Date, lieu, statut
- **Enfants** : Liste avec liens
- **Événements familiaux** : Mariage, divorce, etc.
- **Témoins** : Liens vers personnes
- **Notes** : Commentaires familiaux

#### Fiche Événement
- **Type d'événement** : Naissance, mariage, décès, etc.
- **Participants** : Liens vers personnes concernées
- **Date et lieu** : Informations spatio-temporelles
- **Sources** : Références documentaires
- **Témoins** : Personnes présentes

#### Fiche Lieu
- **Nom du lieu** : Avec variantes historiques
- **Événements** : Liste des événements survenus
- **Personnes** : Naissances, décès, mariages
- **Familles** : Mariages célébrés
- **Géolocalisation** : Coordonnées si disponibles

---

## 🔗 Système de liens et navigation

### Types de liens Obsidian
- **Liens directs** : `[[Nom_Personne]]` vers fiches personnes
- **Liens avec alias** : `[[Fichier|Texte affiché]]`
- **Liens vers dossiers** : `[[01-Personnes/]]`
- **Liens vers sections** : `[[Fichier#Section]]`

### Navigation bidirectionnelle
- Chaque fiche contient des liens vers les entités liées
- Les liens sont automatiquement détectés par Obsidian
- Le Graph View génère automatiquement le réseau de relations

### Tags et métadonnées
- **Tags temporels** : `#1800s`, `#1900s`, `#XXe_siècle`
- **Tags géographiques** : `#France`, `#Paris`, `#Lyon`
- **Tags relationnels** : `#ancêtre`, `#descendant`, `#cousin`
- **Tags événementiels** : `#mariage`, `#naissance`, `#décès`

---

## 🎨 Fonctionnalités Obsidian exploitées

### Graph View
- **Visualisation automatique** des relations familiales
- **Filtrage** par tags, dossiers, dates
- **Navigation interactive** dans le graphe
- **Détection de communautés** familiales

### Recherche avancée
- **Recherche globale** : Ctrl+Shift+F
- **Recherche par tags** : `tag:#1800s`
- **Recherche par liens** : `[[Personne]]`
- **Recherche par contenu** : Texte libre

### Plugins potentiels
- **Dataview** : Requêtes SQL-like sur les métadonnées
- **Templater** : Templates dynamiques
- **Calendar** : Timeline des événements
- **Kanban** : Gestion des recherches généalogiques
- **Excalidraw** : Schémas familiaux

---

## 📊 Données sources (geneweb-py)

### Modèles Person
- `Person.unique_id` → Nom de fichier
- `Person.display_name` → Titre de fiche
- `Person.events` → Événements personnels
- `Person.families_as_child/spouse` → Relations familiales
- `Person.birth_date/place` → Informations de naissance
- `Person.death_date/place` → Informations de décès

### Modèles Family
- `Family.family_id` → Nom de fichier famille
- `Family.husband_id/wife_id` → Liens vers époux
- `Family.children` → Liste des enfants
- `Family.events` → Événements familiaux
- `Family.marriage_date/place` → Informations mariage

### Modèles Event
- `PersonalEvent` → Événements individuels
- `FamilyEvent` → Événements familiaux
- `Event.date/place` → Informations spatio-temporelles
- `Event.witnesses` → Témoins

---

## 🚀 Plan de développement

### Phase 1 : Export de base (1-2 semaines)
- [ ] Créer `ObsidianExporter` dans `src/geneweb_py/formats/`
- [ ] Export des personnes avec liens de base
- [ ] Export des familles avec relations
- [ ] Structure de dossiers standardisée
- [ ] Tests unitaires de base

### Phase 2 : Enrichissement (1 semaine)
- [ ] Export des événements par type
- [ ] Export des lieux avec géolocalisation
- [ ] Système de tags automatiques
- [ ] Templates personnalisables
- [ ] Gestion des métadonnées

### Phase 3 : Optimisation (1 semaine)
- [ ] Index principal avec statistiques
- [ ] Graphiques et visualisations
- [ ] Configuration avancée
- [ ] Documentation utilisateur
- [ ] Tests d'intégration

### Phase 4 : Extensions (optionnel)
- [ ] Support des médias (photos, documents)
- [ ] Intégration avec plugins Obsidian
- [ ] Export vers autres formats (HTML, PDF)
- [ ] API pour extensions tierces

---

## 🔧 Considérations techniques

### Performance
- **Fichiers volumineux** : Gestion des bases avec >1000 personnes
- **Liens cassés** : Détection et correction automatique
- **Mise à jour incrémentale** : Éviter la régénération complète

### Compatibilité
- **Encodage** : UTF-8 pour caractères spéciaux
- **Noms de fichiers** : Échappement des caractères interdits
- **Chemins** : Compatibilité Windows/Linux/macOS

### Sécurité
- **Données sensibles** : Filtrage des informations privées
- **Accès** : Contrôle des niveaux de confidentialité
- **Backup** : Sauvegarde automatique des exports

---

## 📈 Métriques de succès

### Quantitatives
- **Couverture** : % de personnes/familles exportées
- **Liens** : Nombre de liens bidirectionnels créés
- **Performance** : Temps d'export pour bases de différentes tailles
- **Qualité** : % de liens cassés détectés

### Qualitatives
- **Navigabilité** : Facilité de navigation dans Obsidian
- **Lisibilité** : Clarté des fiches générées
- **Extensibilité** : Possibilité d'ajouter des fonctionnalités
- **Adoption** : Utilisation par la communauté généalogique

---

## 🎯 Cas d'usage prioritaires

### Généalogiste amateur
- **Navigation familiale** : Explorer les branches de l'arbre
- **Recherche** : Trouver rapidement une personne ou un événement
- **Documentation** : Ajouter des notes et sources
- **Partage** : Exporter vers d'autres formats

### Chercheur professionnel
- **Analyse** : Détecter des patterns familiaux
- **Visualisation** : Graphiques et statistiques
- **Collaboration** : Partage avec d'autres chercheurs
- **Publication** : Export vers formats académiques

### Archiviste
- **Inventaire** : Catalogue des personnes et familles
- **Indexation** : Recherche dans les archives
- **Numérisation** : Lien avec documents numérisés
- **Préservation** : Sauvegarde à long terme

---

## 🔮 Évolutions futures

### Intégrations possibles
- **Bases de données** : Export vers PostgreSQL, MongoDB
- **APIs généalogiques** : Intégration avec FamilySearch, Ancestry
- **Géolocalisation** : Cartes interactives des lieux
- **IA** : Suggestions de relations, détection d'erreurs

### Formats d'export
- **Web** : Site statique avec navigation
- **Mobile** : Application mobile dédiée
- **VR/AR** : Visualisation immersive des arbres
- **Print** : Livres généalogiques automatisés

---

## 📚 Ressources et références

### Documentation Obsidian
- [Obsidian Help](https://help.obsidian.md/) - Documentation officielle
- [Obsidian Community](https://forum.obsidian.md/) - Communauté et plugins
- [Obsidian Graph View](https://help.obsidian.md/Plugins/Graph+view) - Graph View

### Plugins utiles
- [Dataview](https://github.com/blacksmithgu/obsidian-dataview) - Requêtes sur métadonnées
- [Templater](https://github.com/SilentVoid13/Templater) - Templates dynamiques
- [Calendar](https://github.com/liamcain/obsidian-calendar-plugin) - Timeline
- [Excalidraw](https://github.com/zsviczian/obsidian-excalidraw-plugin) - Schémas

### Standards généalogiques
- [GEDCOM](https://www.gedcom.org/) - Format standard
- [FHISO](https://fhiso.org/) - Standards internationaux
- [GeneWeb](https://geneweb.org/) - Format source

---

## 📝 Notes de développement

### Défis identifiés
- **Noms de fichiers** : Gestion des homonymes et caractères spéciaux
- **Liens circulaires** : Éviter les références infinies
- **Performance** : Optimisation pour grandes bases
- **Maintenance** : Mise à jour des exports existants

### Solutions envisagées
- **Convention de nommage** : `Nom_Prenom_Occurrence.md`
- **Validation des liens** : Vérification automatique
- **Export incrémental** : Seulement les changements
- **Versioning** : Gestion des versions d'export

### Questions ouvertes
- **Templates** : Système de templates personnalisables ?
- **Médias** : Intégration des photos et documents ?
- **Collaboration** : Support multi-utilisateurs ?
- **Cloud** : Synchronisation avec services cloud ?

---

**Dernière mise à jour** : 9 octobre 2025  
**Prochaine révision** : À définir selon priorité projet  
**Contact** : projet geneweb-py
