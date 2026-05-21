# Spec : Onglet Événements — Tableau triable/filtrable

**Date** : 2026-05-21  
**Statut** : Approuvé

---

## Contexte

L'onglet Événements affiche actuellement des cards `div` simples sans tri ni filtre avancé. L'objectif est de remplacer ce rendu par un tableau Tabulator.js avec filtre gate obligatoire, tri multi-colonnes, et affichage enrichi (noms, témoins, notes, sources).

---

## Décisions de conception

| Sujet | Décision |
|---|---|
| Chargement | Tout charger en une fois (client-side), filtre gate obligatoire |
| Librairie tableau | Tabulator.js via CDN |
| Noms personnes/familles | Enrichissement API (pas de join client-side) |
| Traversée graphe | Nouveau endpoint backend `/api/v1/persons/{id}/related` |
| Layout filtres | Panneau fixe au-dessus du tableau |
| Notes/Sources | Texte tronqué + expansion inline au clic de ligne |

---

## Filtre gate

Le bouton "Rechercher" est désactivé tant qu'aucun filtre n'est rempli. Au moins un filtre parmi les quatre est obligatoire.

### Filtres disponibles

| Filtre | Type | Comportement |
|---|---|---|
| Type d'événement | Multi-select checkboxes | Passe `event_type` à l'API (un appel par type sélectionné, dédoublonnage par `id`) |
| Lieu | Texte libre | Passe `place` à l'API |
| Personne | Autocomplete + degré 1/2/3 | Résout les person_ids liés via `/api/v1/persons/{id}/related?degree=N`, puis filtre client-side |
| Nom de famille | Texte libre | Filtre client-side sur `person_name` et `family_label` (contains, insensible à la casse) |

### Degrés de lien (filtre personne)

- **Degré 1** : événements où `person_id = X` + événements des familles où X est conjoint(e) (`family_id ∈ X.families_as_spouse`) + événements où X apparaît dans `witnesses`
- **Degré 2** : degré 1 + événements des parents, enfants, fratrie de X
- **Degré 3** : degré 2 + événements des personnes pour lesquelles X a été témoin

### Réponse de `/related`

```json
{
  "person_ids": ["id1", "id2"],
  "family_ids": ["fam1", "fam2"],
  "witness_person_id": "X"
}
```

`witness_person_id` est retourné tel quel pour que le client filtre aussi sur `event.witnesses.includes(X)`.

### Séquence de chargement

1. Si filtre personne actif : `GET /api/v1/persons/{id}/related?degree=N` → `{person_ids, family_ids, witness_person_id}`
2. `GET /api/v1/events` avec paramètres API-level uniquement si disponibles : `event_type` (type filtre) et/ou `place` (lieu filtre). Boucle sur toutes les pages jusqu'à `has_next = false`, taille de page 100
3. Filtre client-side :
   - Nom de famille → `person_name` ou `family_label` contains (insensible casse)
   - Personne → `event.person_id ∈ person_ids` OR `event.family_id ∈ family_ids` OR `witness_person_id ∈ event.witnesses`
4. Tabulator initialisé ou rechargé avec le dataset résultant

> **Note perf** : si le seul filtre actif est "Personne" ou "Nom de famille" (sans type ni lieu), tous les événements sont chargés côté serveur puis filtrés client-side. Acceptable pour les fichiers .gw typiques (< 50 000 événements). Le filtre gate garantit qu'aucun chargement ne se fait sans filtre.

---

## Tableau Tabulator

### Colonnes

| # | Colonne | Champ | Tri | Filtre header |
|---|---|---|---|---|
| 1 | Type événement | `event_type` + label FR | ✓ | select |
| 2 | Date | `date` (display_text) | ✓ sur `date_sort_year` | texte |
| 3 | Lieu | `place` | ✓ | texte |
| 4 | Personne / Famille | `person_name` ou `family_label` | ✓ | texte |
| 5 | Témoins | `witness_names[]` (joint par `, `) | — | — |
| 6 | Notes | `note` (tronqué 60 chars) | — | — |
| 7 | Sources | `sources[]` (tronqué) | — | — |

### Tri date

Tabulator trie sur le champ numérique `date_sort_year` (entier, fourni par l'API). La colonne Date affiche `date` (texte humain avec préfixes ~, ?, <, >, ..).

### Notes et Sources — expansion inline

- Cellule affiche les 60 premiers caractères + `…` si texte plus long
- Clic sur une ligne → Tabulator `rowClick` → toggle d'une classe CSS → `rowFormatter` affiche un sous-panneau avec le texte complet des notes ET des sources
- Second clic referme le sous-panneau

---

## Modifications backend

### 1. Enrichissement de `EventSchema` (`api/models/event.py`)

```python
person_name: Optional[str] = None    # "Dupont Jean" ou None
family_label: Optional[str] = None   # "Dupont × Martin" ou None
witness_names: List[str] = []        # ["Martin Pierre", "Leroy Paul"]
date_sort_year: Optional[int] = None # année principale pour tri Tabulator
```

### 2. Enrichissement de `event_to_schema` (`api/serialization.py`)

Signature étendue pour recevoir un lookup de noms :

```python
def event_to_schema(
    event: Event,
    *,
    event_id: str,
    person_id: Optional[str],
    family_id: Optional[str],
    genealogy: Optional[Genealogy] = None,  # nouveau
) -> EventSchema:
```

Logique ajoutée :
- Résoudre `person_name` depuis `genealogy.persons[person_id]` si disponible
- Résoudre `family_label` depuis `genealogy.families[family_id]` (conjoints)
- Résoudre `witness_names` depuis `genealogy.persons[wid]` pour chaque wid dans `witnesses`
- Extraire `date_sort_year` depuis `event.date.sort_year()` si date présente

Tous les appelants de `event_to_schema` dans `routers/events.py` et `services/genealogy_service.py` passent l'objet `genealogy` via le service existant.

### 3. Nouveau endpoint (`api/routers/persons.py` ou nouveau router)

```
GET /api/v1/persons/{person_id}/related?degree=1
```

Paramètre `degree` : entier 1, 2 ou 3 (défaut 1).  
Retourne :
```json
{"person_ids": ["id1", "id2", "id3"]}
```

Implémentation dans `GenealogyService` :

```python
def get_related_person_ids(self, person_id: str, degree: int) -> List[str]:
```

Logique :
- **Degré 1** :
  - `person_id` lui-même
  - `family_ids` = familles où X est conjoint(e) (`X.families_as_spouse`)
  - `witness_person_id = X` (le client filtre ensuite `X ∈ event.witnesses`)
- **Degré 2** : degré 1 + parents (via families où X est enfant) + enfants (children dans families_as_spouse) + fratrie (autres enfants des mêmes familles parentales) → ajoutés à `person_ids`
- **Degré 3** : degré 2 + persons pour qui X a été témoin → scan de tous les events de la généalogie pour trouver les `person_id` dont l'event contient X dans `witnesses`, ajoutés à `person_ids`

> **Note** : la traversée degré 3 (inverse des témoins) peut être coûteuse sur de grands fichiers. Un index `witness_to_events` calculé une fois à la création de session dans `GenealogyService` évite un scan complet à chaque appel.

---

## Modifications frontend

### `index.html`

- Ajouter balises CDN Tabulator (CSS + JS) avant `</head>` / avant `</body>`
- Remplacer contenu de `#panel-events` : filtre gate + `<div id="events-table"></div>`

### `app.js`

- Supprimer : `buildEventTypeCheckboxes`, `wireEventsTab`, `searchEvents`, `fetchAllEventItems`, `renderEvents`, `extractMonth`, `extractDay`
- Ajouter :
  - `initEventsTab()` : monte le panneau filtre, branche les événements, désactive le bouton si vide
  - `loadEvents(filters)` : séquence de chargement (related persons + events API + filtre client-side)
  - `buildEventsTable(data)` : initialise/détruit et recrée l'instance Tabulator
  - `personAutocomplete(input)` : autocomplete sur l'endpoint personnes existant
  - `rowExpansionFormatter` : affiche notes + sources sous la ligne au clic

---

## Périmètre exclu

- Export CSV depuis Tabulator (hors scope)
- Filtre par mois/jour dans l'API (reste client-side via `date_sort_year` et parsing du display_text)
- Sauvegarde de l'état des filtres entre sessions

---

## Critères de succès

1. Bouton "Rechercher" inactif sans filtre
2. Tableau s'affiche avec les 7 colonnes après recherche
3. Tri multi-colonnes fonctionnel (clic header, shift+clic second tri)
4. Filtres header Tabulator fonctionnels sur Type, Date, Lieu, Personne/Famille
5. Noms résolus (pas d'IDs bruts dans le tableau)
6. Clic ligne → notes et sources s'affichent/masquent inline
7. Filtre personne degré 1/2/3 retourne les bons événements
8. Coverage >= 80% maintenu
