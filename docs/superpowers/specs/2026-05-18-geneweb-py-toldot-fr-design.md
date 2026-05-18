# Design : geneweb-py.toldot.fr — Interface web publique

**Date :** 2026-05-18
**Statut :** Approuvé

---

## Contexte

L'association Toldot héberge un outil de parsing GeneWeb sur PythonAnywhere (Toldot_Geneweb_parser) : upload d'un `.gw` → téléchargement d'un export JSON/CSV. Ce service est remplacé par une interface moderne reposant sur l'API geneweb-py avec session éphémère (privacy by design), déployée sur CapRover.

Le sous-site `geneweb-py.toldot.fr` est le premier sous-domaine du nouveau dispositif `toldot.fr`. Il offre deux fonctions complémentaires :
- **Conversion** : export GEDCOM / JSON / XML d'un fichier `.gw`
- **Navigation interactive** : parcourir personnes, familles et événements pendant la durée de la session

---

## Architecture générale

```
CapRover App : geneweb-py.toldot.fr
  │
  └── Docker container (Python)
        ├── API FastAPI  →  /api/v1/  (READ_ONLY=true)
        └── Static files →  /         (HTML + JS + CSS)
```

FastAPI sert à la fois l'API REST et les fichiers statiques du front-end via `StaticFiles`. Un seul conteneur, un seul domaine, zéro configuration CORS inter-domaines.

**Variables d'environnement CapRover :**

| Variable | Valeur production |
|----------|------------------|
| `READ_ONLY` | `true` |
| `SESSION_MAX_SESSIONS` | `10` |
| `SESSION_TTL_SECONDS` | `3600` |
| `MAX_UPLOAD_BYTES` | `10485760` (10 Mo) |

---

## Structure des fichiers

```
src/geneweb_py/api/static/
  index.html        ← page unique (SPA vanilla)
  app.js            ← logique session + navigation + rendu
  style.css         ← thème héritage/patrimoine
  img/
    TOLDOT.png      ← logo existant

Dockerfile          ← à la racine du repo
captain-definition  ← à la racine du repo
```

---

## Style visuel

**Thème : Héritage & Patrimoine**

- Palette : fond `#fdf6ec` (parchemin), accent `#8b6914` (or brun), texte `#2c1810` (brun foncé)
- Typographie : Georgia / serif pour les titres et noms ; système sans-serif pour l'UI
- Accents : bordure gauche `3px solid #8b6914` sur les cartes personnes/familles
- Bootstrap 5 comme base de mise en page (grille, responsive), surcharge CSS pour le thème
- Logo `TOLDOT.png` existant réutilisé dans la navbar

---

## Flux utilisateur

### État 1 — Landing (aucune session)

La page présente :
- Navbar : logo Toldot + nom de l'outil
- Zone d'upload : drag-and-drop + clic, accepte uniquement `.gw`
- Bouton "Charger et analyser"
- Trois points de réassurance (icônes + texte court) :
  - "Parsing en mémoire — fichier supprimé immédiatement"
  - "Export GEDCOM · JSON · XML"
  - "Code source libre · GitHub"
- Mentions légales courtes en pied de page

**Comportement upload :**
1. `POST /api/v1/sessions` (multipart)
2. Succès → token stocké dans `sessionStorage`, affichage de l'interface principale
3. Erreur 413 → message sur la zone d'upload ("Fichier trop volumineux")
4. Erreur 400/415 → message ("Format invalide, attendu .gw")
5. Erreur 503 → message ("Serveur saturé, réessayez dans quelques minutes")

### État 2 — Interface principale (session active)

**Navbar permanente :**
- Logo + nom
- Statistiques courtes : "247 personnes · 89 familles" (depuis `GET /api/v1/genealogy/stats`)
- Timer de session : compte à rebours rafraîchi toutes les 30 secondes
- Bouton "Quitter" : `DELETE /api/v1/sessions/{token}` → effacement `sessionStorage` → retour landing

**Cinq onglets :**

| Onglet | Contenu |
|--------|---------|
| Personnes | Liste paginée + recherche + fiche avec mini-arbre |
| Familles | Liste paginée + détail famille |
| Événements | Filtres date + types cumulatifs + liste résultats |
| Stats | Chiffres clés du fichier |
| Export | Boutons de téléchargement GEDCOM / JSON / XML |

---

## Onglet Personnes

- Recherche par nom (champ texte → `GET /api/v1/genealogy/search?q=…`)
- Liste paginée : 50 personnes par page, boutons Précédent / Suivant
- Chaque ligne : `Nom, Prénom · °année · †année` + lien "Voir ›"
- Au clic "Voir ›" : panneau de détail déroulé sous la ligne (pas de navigation)

**Panneau de détail — mini-arbre :**
```
[Parent 1]  →  [Personne]  →  [Enfant 1]
[Parent 2]                    [Enfant 2]
                              [Enfant 3]
```
- Parents : issus des familles où la personne est enfant
- Enfants : issus des familles où la personne est parent
- Chaque nom dans le mini-arbre est cliquable → ouvre la fiche de cette personne
- Implémenté via `GET /api/v1/families` filtré par identifiant

---

## Onglet Familles

- Liste paginée : 50 familles par page
- Chaque ligne : `Époux · Épouse · (N enfants)` + date de mariage si disponible
- Au clic : panneau de détail avec liste complète des enfants (noms cliquables → fiche personne)

---

## Onglet Événements

**Filtres (tous optionnels, cumulables) :**

- **Jour** : champ numérique 1–31
- **Mois** : champ numérique 1–12
- **Année** : champ numérique (ex. 1914)
- **Types** : sélection multiple (checkboxes) — valeurs : Naissance, Décès, Mariage, Séparation, Divorce, Autre

Exemple d'usage : "tous les mariages et divorces en avril 1923".

**Résultats :**
- Liste chronologique : type · date · nom de la personne · lieu (si disponible)
- Chaque résultat cliquable → ouvre la fiche personne (onglet Personnes)
- Appel API : `GET /api/v1/events` avec paramètres de filtrage

---

## Onglet Stats

Affichage des métriques retournées par `GET /api/v1/genealogy/stats` :
- Nombre de personnes, familles, événements
- Plage temporelle (date min / max)
- Nom du fichier source (effacé en session, affiché comme "—")

---

## Onglet Export

Trois boutons de téléchargement :
- **GEDCOM** → `GET /api/v1/genealogy/export/gedcom`
- **JSON** → `GET /api/v1/genealogy/export/json`
- **XML** → `GET /api/v1/genealogy/export/xml`

Chaque export déclenche un téléchargement direct via l'attribut `download` sur un lien `<a>`.
Message de réassurance rappelant que la session sera supprimée après téléchargement si l'utilisateur le souhaite.

---

## Gestion de session côté client

| Situation | Comportement |
|-----------|-------------|
| Token stocké | `sessionStorage` uniquement (effacé à la fermeture de l'onglet) |
| 401 reçu | Alerte "Votre session a expiré" → retour automatique landing |
| Bouton Quitter | `DELETE /api/v1/sessions/{token}` → effacement sessionStorage → landing |
| Fermeture onglet | sessionStorage effacé → session expire côté serveur par TTL |
| Timer | Rafraîchi toutes les 30s depuis `expires_at` retourné par l'API |

---

## Gestion des erreurs

| Erreur | Message affiché | Comportement |
|--------|----------------|-------------|
| 400 / 415 | "Format invalide, attendu .gw" | Affichage sur zone upload |
| 401 | "Session expirée" | Retour landing automatique |
| 413 | "Fichier trop volumineux (max 10 Mo)" | Affichage sur zone upload |
| 503 | "Serveur saturé, réessayez dans quelques minutes" | Affichage sur zone upload |
| Réseau | "Impossible de joindre le serveur" | Toast d'erreur |

Aucun message d'erreur n'expose de données généalogiques ni de détails techniques internes.

---

## Déploiement CapRover

### `Dockerfile`

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir ".[api]"
EXPOSE 8000
CMD ["uvicorn", "geneweb_py.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `captain-definition`

```json
{
  "schemaVersion": 2,
  "dockerfilePath": "./Dockerfile"
}
```

### Montage des fichiers statiques dans FastAPI

```python
# Dans api/main.py, après la définition des routers
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="src/geneweb_py/api/static", html=True), name="static")
```

Le montage `/` doit être déclaré **après** tous les routers API pour ne pas écraser `/api/v1/`.

---

## Ce qui n'est pas dans ce sous-projet

- `www.toldot.fr` (site statique de l'association) → spec séparée
- Mode CRUD / mutations de données → `READ_ONLY=true` en production
- Authentification utilisateur → hors scope
- Visualisation arbre complet (d3.js) → hors scope (mini-arbre relationnel uniquement)
- Correspondances entre fichiers de différents utilisateurs → hors scope
