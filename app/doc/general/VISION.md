## Vision du Projet : GeneWeb Entity Structurer (GES)

### 1. Le But du Projet (La Vision 🎯)

L'objectif principal du projet est d'**enrichir et de structurer les données généalogiques contenues dans les fichiers GeneWeb (`.gw`)**.

Actuellement, des informations de grande valeur sur les liens entre des individus et des entités (comme des entreprises, des associations, des régiments, etc.) sont souvent "perdues" dans des champs de texte libre, sous forme d'événements personnalisés.

Ce projet vise à **transformer cette information implicite en connaissance explicite**. En identifiant automatiquement ces organisations et en les traitant comme des entités à part entière, nous pouvons :
* **Améliorer la qualité des données** : Rendre la base de données plus cohérente et structurée.
* **Ouvrir de nouvelles perspectives d'analyse** : Permettre d'étudier les réseaux de relations entre les personnes et les organisations, visualiser les carrières, les affiliations, etc.
* **Accroître l'interopérabilité** : Faciliter l'export et l'utilisation des données généalogiques dans d'autres systèmes d'analyse ou de visualisation.

En bref, il s'agit de faire passer la généalogie d'une simple collection d'arbres familiaux à un véritable **graphe de connaissances sociales et historiques**.

---

### 2. État Actuel : Le Prototype Fonctionnel (Ce qui est codé ✅)

Nous disposons déjà d'une application web fonctionnelle développée avec **Streamlit**. Cet outil permet de réaliser le cœur de la transformation :

* **Interface Utilisateur Simple** : L'utilisateur peut facilement téléverser un fichier `.gw`.
* **Configuration Flexible du LLM** : Un panneau latéral permet de configurer l'accès à un modèle de langage (LLM) externe via **OpenRouter**, en saisissant une clé API et en choisissant un modèle spécifique.
* **Détection et Analyse** : L'application analyse le fichier, isole les blocs d'événements personnels (`pevt`) et identifie les événements qui ne sont pas standards.
* **Classification par l'IA** : Chaque événement personnalisé est soumis au LLM configuré, qui détermine s'il s'agit d'une référence à une organisation.
* **Transformation Automatique** : Si une organisation est identifiée :
    * L'événement d'origine est supprimé du bloc de la personne.
    * Un **nouveau bloc `pevt` est créé** pour l'organisation, la traitant comme une nouvelle entité.
    * L'événement est standardisé (par défaut `#occu` pour "occupation" ou "membre") et placé dans le bloc de l'organisation.
    * Le lien est conservé en ajoutant la personne d'origine comme **témoin (`wit`)** de ce nouvel événement.
* **Restitution et Téléchargement** : L'application affiche un résumé des nouvelles organisations créées, un journal détaillé des opérations et propose en téléchargement le fichier `.gw` entièrement modifié.

---

### 3. Feuille de Route à Court Terme (Les Prochaines Étapes 🚀)

Les prochaines évolutions se concentreront sur l'amélioration de l'interactivité et de la finesse du contrôle pour l'utilisateur.

* **Phase de Validation et Fusion Interactive** :
    * **Objectif** : Éviter la création de doublons (ex: "Société Dupont" et "Sté. Dupont").
    * **Implémentation** : Après l'analyse, au lieu de générer directement le fichier final, l'application présentera une **étape de validation**. Elle listera toutes les organisations identifiées et proposera de fusionner les doublons potentiels. L'utilisateur pourra cocher les entités à regrouper avant de lancer la génération finale du fichier.

* **Règles de Renommage d'Événements Personnalisables** :
    * **Objectif** : Permettre à l'utilisateur d'aller au-delà de la transformation par défaut en `#occu`.
    * **Implémentation** : Ajouter une section "Règles avancées" dans l'interface où l'utilisateur pourra définir des mappages. Par exemple :
        * Si le nom de l'événement contient "Fondateur", le nouvel événement sera `#creation`.
        * Si le nom contient "Actionnaire", le nouvel événement sera `#shareholder`.

---

### 4. Vision à Long Terme (Le Futur du Projet 🌟)

Une fois le cœur de l'application stabilisé et interactif, nous pourrons étendre ses capacités.

* **Traitement par Lots (Batch Processing)** : Permettre de traiter plusieurs fichiers `.gw` en une seule fois (via une archive ZIP ou la sélection d'un dossier).
* **Gestion de l'État et Base de Données** : Utiliser une petite base de données (ex: SQLite) pour conserver l'historique des traitements, gérer une liste d'organisations déjà validées et permettre à l'utilisateur de reprendre un travail interrompu.
* **Visualisation des Données** : Intégrer un module de visualisation pour générer et afficher un **graphe des relations** entre les individus et les organisations nouvellement créées.
* **Extension de la Reconnaissance d'Entités** : Utiliser le LLM pour identifier d'autres types d'entités structurables, comme des régiments militaires, des propriétés immobilières, des navires, etc.
* **Packaging et Distribution Simplifiée** : Empaqueter l'application (avec PyInstaller ou Docker) pour la rendre facilement installable et exécutable par des utilisateurs non techniciens.

---

### 5. Points Techniques à Creuser (Les Défis 🔬)

Pour réaliser cette vision, plusieurs points techniques méritent une attention particulière.

* **Fiabilité et "Prompt Engineering" du LLM** : Comment améliorer la précision du LLM pour qu'il retourne systématiquement un JSON valide et pertinent ? Il faudra affiner le "prompt" (la consigne donnée au LLM), peut-être en utilisant des techniques de "few-shot learning" (lui donner plusieurs exemples dans le prompt).
* **Performance sur les Gros Fichiers** : Tester l'application avec des fichiers `.gw` de plusieurs dizaines de mégaoctets. La méthode actuelle de chargement en mémoire pourrait atteindre ses limites et nécessiter une approche de lecture ligne par ligne ("stream processing").
* **Algorithmes de Similarité de Chaînes** : Pour la fonctionnalité de fusion, il faudra évaluer les meilleurs algorithmes (Levenshtein, Jaro-Winkler, etc.) pour détecter efficacement les noms d'organisations similaires.
* **Gestion de l'État dans Streamlit** : La future étape de validation/fusion nécessitera un workflow en plusieurs étapes. Il faudra maîtriser l'objet `st.session_state` de Streamlit pour conserver les informations entre les interactions de l'utilisateur.