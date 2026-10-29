# Parser GeneWeb — Revue de conformité spec officielle

**Date :** 2026-05-20  
**Référence :** https://geneweb.tuxfamily.org/wiki/gw/fr + https://geneweb.tuxfamily.org/wiki/wikitext/fr  
**Approche retenue :** Itératif par couche (4 phases indépendantes)  
**Périmètre :** Bug + champs manquants + événements complets + wikitext (texte brut + métadonnées)  
**Compatibilité :** Ajouts de champs optionnels autorisés dans les dataclasses et l'API REST  

---

## Contexte et périmètre

Le parser actuel (`lexical.py` + `gw_parser.py`) couvre les cas les plus courants du format `.gw` GeneWeb mais présente des écarts par rapport à la spec officielle :

1. Un **bug** : `#apriv`/`#apubl` écrivent sur des attributs dynamiques inexistants au lieu de `Person.access_level`
2. Des **champs de personne tokenisés mais jamais peuplés** : aliases, sources, lieux baptême/inhumation, image
3. Des **syntaxes de personne non interprétées** : `(PublicName)`, `{FirstNameAlias}`, titres `[...]`
4. Des **~45 types d'événements pevt/fevt manquants** sur les 56 définis par la spec
5. Des **qualificateurs fam manquants** : `#nsck`, `#banns`, `#contract`, `#license`, etc.
6. Le **wikitext des notes** non structuré : liens vers personnes/pages stockés en texte brut

---

## Phase 1 — Lexer complet + bug `access_level`

### Fichiers : `lexical.py`, `gw_parser.py`

### 1.1 Bug `access_level`

**Localisation :** `gw_parser.py:2266-2271`

**Avant :**
```python
elif token.type == TokenType.APRIV:
    person.access_private = True   # attribut dynamique inexistant — données perdues

elif token.type == TokenType.APUBL:
    person.access_public = True    # attribut dynamique inexistant — données perdues
```

**Après :**
```python
elif token.type == TokenType.APRIV:
    person.access_level = AccessLevel.PRIVATE

elif token.type == TokenType.APUBL:
    person.access_level = AccessLevel.PUBLIC
```

**Note sur les tests existants :** Les tests `test_parse_access_public_explicit` et `test_parse_access_private_explicit` vérifient seulement que la personne est trouvée (`assert jean is not None`) — ils ne valident PAS la valeur de l'attribut buggé. La correction ne cassera donc pas les 916 tests. En revanche, ces tests doivent être améliorés pour vérifier `person.access_level == AccessLevel.PUBLIC/PRIVATE` après le fix.

### 1.2 Nouveaux tokens `hash_modifiers` dans `lexical.py`

Ajouter dans le dictionnaire `hash_modifiers` de `LexicalParser._compile_patterns()` :

| Clé GW | `TokenType` à créer | Champ cible |
|---|---|---|
| `nick` | `NICK` | `Person.nickname` |
| `salias` | `SALIAS` | `Person.surname_alias` |
| `alias` | `ALIAS` | `Person.general_alias` |
| `image` | `IMAGE` | `Person.image_path` |
| `bs` | `BS` | `Person.birth_source` |
| `ds` | `DS` | `Person.death_source` |
| `pp` | `PP` | `Person.baptism_place` |
| `ps` | `PS` | `Person.baptism_source` |
| `rp` | `RP` | `Person.burial_place` |
| `rs` | `RS` | `Person.burial_source` |
| `ms` | `MS` | `Family.marriage_source` |

Tous ces `TokenType` sont des membres simples de l'enum (valeur = clé GW).

**Note sur la ponctuation :** Le lexer existant (`_parse_identifier`, ligne 674) accepte déjà `isalnum() or in "_-'"`. Les noms composés (`Jean-Baptiste`, `d'Artagnan`) sont produits comme un seul token `IDENTIFIER`. Aucune modification de la règle IDENTIFIER n'est nécessaire.

### 1.3 Tests de la phase 1

- Tokenisation d'une ligne `#nick Qualifier #salias Dupont #image /path.jpg` → tokens corrects
- `#apriv` peuple `person.access_level == AccessLevel.PRIVATE` (test amélioré)
- `#apubl` peuple `person.access_level == AccessLevel.PUBLIC` (test amélioré)
- Les 916 tests existants passent sans modification

---

## Phase 2 — Parsing des champs de personne

### Fichiers : `gw_parser.py`

Tous les champs cibles (`nickname`, `surname_alias`, `general_alias`, `image_path`, `birth_source`, `death_source`, `baptism_place`, `baptism_source`, `burial_place`, `burial_source`) sont **déjà déclarés** dans `Person` — seul le parser doit être complété.

### 2.1 Nouveaux tokens dans `_parse_inline_personal_info`

**Règle sur `_parse_source_value` :** Cette méthode retourne `Tuple[Optional[str], int]`. Toutes les utilisations doivent capturer les deux valeurs :

```python
elif token.type == TokenType.BS:
    i += 1
    value, i = self._parse_source_value(tokens, i)  # capture i mis à jour
    if value:
        person.birth_source = value

# Idem pour DS→death_source, PP→baptism_place (via _parse_place_value),
# PS→baptism_source, RP→burial_place, RS→burial_source
```

Pour les lieux, utiliser `_parse_place_value` (même signature `Tuple[Optional[str], int]`).

Ajouter également :

```python
elif token.type == TokenType.NICK:
    i += 1
    if i < len(tokens):
        person.nickname = tokens[i].value.replace("_", " ")
        i += 1

elif token.type == TokenType.SALIAS:
    i += 1
    if i < len(tokens):
        person.surname_alias = tokens[i].value
        i += 1

elif token.type == TokenType.ALIAS:
    i += 1
    if i < len(tokens):
        person.general_alias = tokens[i].value
        i += 1

elif token.type == TokenType.IMAGE:
    i += 1
    if i < len(tokens):
        person.image_path = tokens[i].value  # les espaces dans les chemins
        i += 1                               # sont en pratique remplacés par _ en GW
```

### 2.2 Parsing de `(PublicName)`

Séquence attendue : `PAREN_OPEN token+ PAREN_CLOSE`

La boucle accepte tout type de token (pas seulement `IDENTIFIER`) jusqu'au `PAREN_CLOSE` — les noms composés arriveront comme un seul `IDENTIFIER` grâce au lexer existant.

**Garde contre fichier mal formé (IndexError) :**

```python
elif token.type == TokenType.PAREN_OPEN:
    parts = []
    i += 1
    while i < len(tokens) and tokens[i].type != TokenType.PAREN_CLOSE:
        parts.append(tokens[i].value.replace("_", " "))
        i += 1
    if i < len(tokens) and tokens[i].type == TokenType.PAREN_CLOSE:
        i += 1  # consommer PAREN_CLOSE seulement s'il est présent
    if parts:
        person.public_name = " ".join(parts)
```

### 2.3 Parsing de `{FirstNameAlias}`

Même garde obligatoire :

```python
elif token.type == TokenType.BRACE_OPEN:
    parts = []
    i += 1
    while i < len(tokens) and tokens[i].type != TokenType.BRACE_CLOSE:
        parts.append(tokens[i].value.replace("_", " "))
        i += 1
    if i < len(tokens) and tokens[i].type == TokenType.BRACE_CLOSE:
        i += 1
    if parts:
        person.first_name_alias = " ".join(parts)
```

### 2.4 Parsing des titres `[TitleName:Title:TitlePlace:StartDate:EndDate:Nth]`

**Séquence :** `BRACKET_OPEN (token COLON?)* BRACKET_CLOSE`

**Format :** 6 champs séparés par `:` ; deux `:` consécutifs signifient un champ vide. Le parser suit un compteur de position (0 à 5) et avance à chaque `COLON`. Les tokens qui ne sont pas `COLON` ni `BRACKET_CLOSE` s'accumulent dans le champ courant.

**Valeurs par défaut :**
- `TitleName` absent → `""`
- `Nth` absent ou vide → `1` (première occurrence, sémantique GeneWeb)
- `StartDate`/`EndDate` absents → `None`
- `is_main = True` si `TitleName == "*"`

**Garde contre `BRACKET_CLOSE` manquant** (même pattern que 2.2/2.3) :

```python
if i < len(tokens) and tokens[i].type == TokenType.BRACKET_CLOSE:
    i += 1
```

La méthode `_parse_title_bracket(tokens, i) -> Tuple[Title, int]` retourne l'objet `Title` et le prochain index.

### 2.5 Source mariage `#ms` dans `_parse_family_block`

Utilise `_parse_source_value` (pas d'assignation directe) :

```python
elif token.type == TokenType.MS:
    i += 1
    value, i = self._parse_source_value(tokens, i)
    if value:
        family.marriage_source = value
```

### 2.6 Tests de la phase 2

- `(NomPublic)` → `person.public_name` peuplé
- `{AliasPrenom}` → `person.first_name_alias` peuplé
- `[*:Comte:Paris:1720:1740:2]` → `person.titles[0]` correct (is_main=True, Nth=2)
- `[:Comte::1720::]` → champs vides préservés, Nth par défaut = 1
- `(PublicName` non fermé → pas d'IndexError, `public_name` ignoré
- `#nick LeGrand #salias DeSaintPaul` → champs corrects
- `1750 #bp Paris #bs Archives_de_la_ville` → `birth_source` multi-tokens correct
- Famille avec `#ms Registre_paroissial_de_Lyon` → `family.marriage_source` correct

---

## Phase 3 — Événements complets et qualificateurs `fam`

### Fichiers : `lexical.py`, `event.py`, `family.py`, `gw_parser.py`

### 3.1 Stratégie : pas de lexer stateful — token IDENTIFIER existant réutilisé

**Le lexer actuel** (ligne 604) produit déjà `TokenType.IDENTIFIER` pour tout `#xxx` non reconnu, avec `value = "#xxx"`. C'est le comportement correct.

**Aucune modification du lexer pour les types d'événements inconnus.** Le parser `_parse_person_events_block` et `_parse_family_events_block`, qui connaissent le contexte syntaxique, traitent un `IDENTIFIER` dont la `value` commence par `#` comme un nom d'événement brut.

Cette approche :
- Préserve la pureté du lexer (fonction pure de la chaîne d'entrée)
- Élimine le risque de corruption en cas de `end pevt` manquant
- Ne nécessite aucune modification du lexer pour les 45 types

### 3.2 Compléter `EventType` et `FamilyEventType` dans `event.py`

**`PersonalEventType` (renommé depuis `EventType`) — membres manquants :**

```python
ACCOMPLISHMENT = "acco"
ACQUISITION = "acqu"
ADHESION = "adhe"
BAPTISM_LDS = "bapl"
BAR_MITZVAH = "barm"
BAT_MITZVAH = "basm"
BENEDICTION = "bles"
RECENSEMENT = "cens"
CHANGE_NAME = "chgn"
CIRCUMCISION = "circ"
CONFIRMATION_LDS = "conl"
DIPLOMA = "degr"
DECORATION = "awar"
DEMOBILISATION = "demm"
DISTINCTION = "dist"
DOTATION = "endl"
DOTATION_LDS = "dotl"
EDUCATION = "educ"
ELECTION = "elec"
EMIGRATION = "emig"
EXCOMMUNICATION = "exco"
FAMILY_LINK_LDS = "flkl"
FIRST_COMMUNION = "fcom"
FUNERAL = "fune"
GRADUATE = "grad"
HOSPITALISATION = "hosp"
ILLNESS = "illn"
IMMIGRATION = "immi"
LAST_PASSAGE = "lpas"
MILITARY_DISCHARGE = "mdis"
MILITARY_PROMOTION = "mpro"
MILITARY_SERVICE = "mser"
MILITARY_MOBILISATION = "mobm"
NATURALISATION = "natu"
ORDINATION = "ordn"
PROPERTY = "prop"
RETIREMENT = "reti"
SEALING_CHILD = "slgc"
SEALING_PARENT = "slgp"
SEALING_SPOUSE = "slgs"
VOTE = "vteb"
WILL = "will"
STRNG = "strng"
```

**`FamilyEventType` — membres manquants :**

```python
ANNULATION = "anul"
MARRIAGE_BANN = "marb"
MARRIAGE_CONTRACT = "marc"
MARRIAGE_LICENSE = "marl"
PACS = "pacs"
RESIDENCE = "resi"
STRNG = "strng"
```

### 3.3 Champ `event_type_raw` pour les types inconnus

Ajouter dans les dataclasses `PersonalEvent` et `FamilyEvent` dans `event.py` :

```python
event_type: Optional[PersonalEventType] = None   # None si type non reconnu
event_type_raw: Optional[str] = None             # ex: "xyz" pour #xyz inconnu
```

Invariant : exactement l'un des deux est peuplé. MyPy strict est satisfait sans `Union`.

Dans le parser : si `IDENTIFIER.value.startswith('#')` dans un bloc `pevt`/`fevt`, tenter de résoudre en `PersonalEventType` via `PersonalEventType(value[1:])` ; en cas d'échec, stocker dans `event_type_raw`.

### 3.4 Qualificateurs `fam` avec enum typé

**Nouveau `Enum` dans `family.py` :**

```python
class FamilyQualifier(str, Enum):
    """Qualificateurs de la ligne fam GeneWeb."""
    NO_SEX_CHECK = "nsck"          # #nsck — pas de vérification sexe des époux
    NO_SEX_CHECK_MARRIAGE = "nsckm" # #nsckm
    NO_MENTION = "noment"          # #noment — relation sans mention
    BANNS = "banns"                # #banns — publication des bans
    CONTRACT = "contract"          # #contract — contrat de mariage
    LICENSE = "license"            # #license — licence de mariage
```

**Champs à ajouter dans `Family` :**

```python
marriage_source: Optional[str] = None
family_qualifiers: List[FamilyQualifier] = field(default_factory=list)
```

(Renommé `family_qualifiers` au lieu de `marriage_qualifiers` pour refléter que `#nsck`/`#noment` qualifient la relation, pas uniquement la cérémonie.)

**Nouveaux tokens** dans `hash_modifiers` du lexer :

| Clé | `TokenType` |
|---|---|
| `nsck` | `NSCK` |
| `nsckm` | `NSCKM` |
| `noment` | `NOMENT` |
| `banns` | `BANNS` |
| `contract` | `CONTRACT` |
| `license` | `LICENSE` |

### 3.5 Tests de la phase 3

- Bloc `pevt` avec `#grad 1/6/1985 #p Paris` → `event_type == PersonalEventType.GRADUATE`
- Bloc `fevt` avec `#marb 12/3/1720 #p Lyon` → `event_type == FamilyEventType.MARRIAGE_BANN`
- Type inconnu `#xyz` → `event_type is None`, `event_type_raw == "xyz"`
- Ligne `fam` avec `#banns #contract` → `family.family_qualifiers == [FamilyQualifier.BANNS, FamilyQualifier.CONTRACT]`
- `#nsck` → `FamilyQualifier.NO_SEX_CHECK`
- MyPy strict passe sur les deux champs `event_type`/`event_type_raw`

---

## Phase 4 — Wikitext : texte brut + métadonnées extraites

### Fichiers : `core/parser/wikitext.py` (nouveau), `core/person.py`, API models

### 4.1 Nouveau module `wikitext.py`

```python
# src/geneweb_py/core/parser/wikitext.py

@dataclass
class PersonLink:
    first_name: str
    last_name: str
    occurrence: int = 0
    display_text: str = ""

@dataclass
class PageLink:
    page_name: str
    display_text: str = ""

@dataclass
class WizardLink:
    wizard_name: str
    display_text: str = ""

@dataclass
class FicheTags:
    """Balises de renvoi sur fiche individu. Last-write-wins si balise dupliquée."""
    head: Optional[str] = None
    occu: Optional[str] = None
    death: Optional[str] = None
    biblio: Optional[str] = None
    bnote: Optional[str] = None
    note: Optional[str] = None

@dataclass
class NoteContent:
    raw: str
    person_links: List[PersonLink] = field(default_factory=list)
    page_links: List[PageLink] = field(default_factory=list)
    wizard_links: List[WizardLink] = field(default_factory=list)
    fiche_tags: FicheTags = field(default_factory=FicheTags)
```

### 4.2 `WikitextParser`

**Patterns compilés au niveau classe** (pas par instance — évite la recompilation à chaque appel) :

```python
class WikitextParser:
    # Ordre d'application : PAGE_LINK en premier (triple crochets englobent doubles)
    _PAGE_LINK   = re.compile(r'\[\[\[([^/\]\[]+)(?:/([^\]\[]*))?\]\]\]')
    _PERSON_LINK = re.compile(
        r'\[\[(?!w:)([^/\]\[]+)/([^/\]\[]+)(?:/(\d*))?(?:/([^\]\[]*))?\]\]'
    )
    _WIZARD_LINK = re.compile(r'\[\[w:([^/\]\[]+)(?:/([^\]\[]*))?\]\]')
    _FICHE_TAG   = re.compile(r'^(HEAD|OCCU|DEATH|BIBLIO|BNOTE|NOTE)=(.*)$', re.MULTILINE)

    def parse(self, raw: str) -> NoteContent: ...
```

**Modifications par rapport à la spec initiale :**
- `PERSON_LINK` : occurrence `(\d*)` et display_text `([^\]\[]*)` rendus optionnels avec `(?:/...)?` — un lien `[[Jean/Dupont]]` ou `[[Jean/Dupont/0]]` est valide
- Occurrence vide → `int(m.group(3) or "0")` pour éviter `ValueError` sur `int("")`

**Algorithme d'extraction — `finditer` avec déduplication par position :**

```python
def parse(self, raw: str) -> NoteContent:
    # 1. Extraire tous les matches avec leur position de début
    matches = []
    for pattern, kind in [
        (self._PAGE_LINK, "page"),
        (self._WIZARD_LINK, "wizard"),
        (self._PERSON_LINK, "person"),
    ]:
        for m in pattern.finditer(raw):
            matches.append((m.start(), kind, m))

    # 2. Trier par position, filtrer les overlaps (premier match gagne)
    matches.sort(key=lambda x: x[0])
    used_spans: List[Tuple[int, int]] = []
    # ... filtrage des chevauchements

    # 3. Extraire FicheTags
    fiche = FicheTags()
    for m in self._FICHE_TAG.finditer(raw):
        tag, value = m.group(1), m.group(2).strip()
        setattr(fiche, tag.lower(), value)  # last-write-wins sur duplicates
```

**Limitations documentées (v1) :**
- Les séquences d'échappement `%[` et `%]` ne sont pas pré-traitées avant le matching regex. Un lien dans `%[%[fake/link%]%]` pourrait produire un faux positif. Comportement accepté pour v1 ; à corriger dans une itération suivante si nécessaire.
- Le formatage `''italique''`, `'''gras'''`, `{surligné}`, listes `*`/`#`, titres `=`, indentation `:` restent dans `raw` non interprétés.

### 4.3 Intégration dans `Person` — méthode on-demand (source de vérité unique)

`notes: List[str]` reste la **seule source de vérité**. Pas de champ parallèle — pas de risque de désynchronisation quelle que soit la façon dont `notes` est manipulée (`.append()`, `.pop()`, assignation directe, désérialisation JSON).

```python
# Inchangé
notes: List[str] = field(default_factory=list)

# Nouveau — calcul à la demande
def get_notes_structured(self) -> List[NoteContent]:
    """Parse et retourne les notes structurées (wikitext extrait).
    Calcul on-demand depuis self.notes — toujours cohérent.
    """
    parser = WikitextParser()
    return [parser.parse(note) for note in self.notes]
```

Cette approche :
- Élimine tout risque de drift entre `notes` et une représentation structurée
- Ne modifie pas `to_dict()` ni les 916 tests existants
- Ne casse pas les 12 appelants existants (`gedcom.py`, `xml.py`, `genealogy.py`, etc.)
- Accepte un coût de parsing à chaque appel (acceptable pour une utilisation non-hot-path)

### 4.4 API REST

Ajouter un endpoint ou un champ optionnel `notes_structured` sur demande explicite (query param `?include_notes_structured=true` ou champ dans le schéma de réponse étendu). Les modèles Pydantic sont cohérents — tous les types de liens sont explicitement définis :

```python
class PersonLinkModel(BaseModel):
    first_name: str
    last_name: str
    occurrence: int = 0
    display_text: str = ""

class PageLinkModel(BaseModel):
    page_name: str
    display_text: str = ""

class WizardLinkModel(BaseModel):
    wizard_name: str
    display_text: str = ""

class FicheTagsModel(BaseModel):
    head: Optional[str] = None
    occu: Optional[str] = None
    death: Optional[str] = None
    biblio: Optional[str] = None
    bnote: Optional[str] = None
    note: Optional[str] = None

class NoteModel(BaseModel):
    raw: str
    person_links: List[PersonLinkModel] = []
    page_links: List[PageLinkModel] = []
    wizard_links: List[WizardLinkModel] = []
    fiche_tags: FicheTagsModel = FicheTagsModel()
```

### 4.5 Tests de la phase 4

- `[[Jean/Dupont/0/Jean Dupont]]` → `person_links[0].first_name == "Jean"`, `occurrence == 0`
- `[[Jean/Dupont]]` (sans occurrence ni texte) → `PersonLink` correct, pas d'exception
- `[[Jean/Dupont//]]` (occurrence vide) → `occurrence == 0` (pas de `ValueError`)
- `[[[arbre_corno/Arbre Corno]]]` → `page_links[0].page_name == "arbre_corno"`
- `[[w:Admin/Administrateur]]` → `wizard_links[0].wizard_name == "Admin"`
- `HEAD=Généalogie\nHEAD=Dupont` (doublon) → `fiche_tags.head == "Dupont"` (last-write-wins)
- Note avec triple et double crochets mêlés → pas de faux positifs
- `person.notes.append("foo"); person.get_notes_structured()` → cohérent, pas de drift
- `person.notes = ["note1", "note2"]; len(person.get_notes_structured()) == 2`

---

## Résumé des changements par fichier

| Fichier | Phase | Nature |
|---|---|---|
| `core/parser/lexical.py` | 1, 3 | +11 tokens hash + 6 qualificateurs fam (`NSCK`, `NSCKM`, `NOMENT`, `BANNS`, `CONTRACT`, `LICENSE`) |
| `core/parser/gw_parser.py` | 1, 2, 3 | Bug fix `access_level` + 10 champs peuplés + `(PublicName)` + `{alias}` + titres + `#ms` + qualificateurs fam |
| `core/event.py` | 3 | +35 membres `PersonalEventType` + 9 membres `FamilyEventType` + champ `event_type_raw: Optional[str]` |
| `core/family.py` | 3 | `FamilyQualifier(Enum)` + `marriage_source: Optional[str]` + `family_qualifiers: List[FamilyQualifier]` |
| `core/person.py` | 4 | +méthode `get_notes_structured() -> List[NoteContent]` |
| `core/parser/wikitext.py` | 4 | Nouveau module (`NoteContent`, `PersonLink`, `PageLink`, `WizardLink`, `FicheTags`, `WikitextParser`) |
| `api/models/person.py` | 4 | Ajout modèles Pydantic : `PersonLinkModel`, `PageLinkModel`, `WizardLinkModel`, `FicheTagsModel`, `NoteModel` |

## Invariants à respecter

- Toute modification est **additive** — aucun champ existant n'est supprimé ni renommé
- `to_dict()` non modifié pour `notes` — les 916 tests existants passent à la fin de chaque phase
- Le seuil de couverture de **80 %** est maintenu
- `mypy --strict` passe après chaque phase
- Les tests `test_parse_access_public_explicit` et `_private_explicit` sont mis à jour pour vérifier `access_level` (pas seulement l'existence de la personne)
- Les tokens `UNKNOWN` ne doivent pas augmenter après la phase 1 sur des fichiers `.gw` standards

---

## Analyse REDTEAM intégrée

### Points acceptés et corrigés dans cette spec

| Point | Correction |
|---|---|
| Lexer stateful `_in_event_block` anti-pattern (R1+R2) | Supprimé — `IDENTIFIER(#xxx)` existant réutilisé, parser arbitre selon contexte |
| `IndexError` sur délimiteurs non fermés (R2) | Guard `if i < len(tokens)` ajouté en 2.2, 2.3, 2.4 |
| `_parse_source_value` retour ignoré (R1+R2) | Signature `Tuple[str, int]` documentée ; pattern `value, i = self._parse_source_value(...)` imposé |
| `int("")` sur occurrence vide (R2) | `int(m.group(3) or "0")` dans `WikitextParser` |
| Regex `PERSON_LINK` trop stricte (R1+R2) | Occurrence et display_text rendus optionnels avec `(?:/...)?` |
| Notes drift double source de vérité (R1+R2) | Remplacé par méthode on-demand `get_notes_structured()` — source unique |
| `event_type_raw` non déclaré (R2) | Ajouté au dataclass `Event` et au tableau de synthèse |
| Ordre regex wikitext non spécifié (R2) | `finditer` + déduplication par position documentés |
| `%[`/`%]` non traités (R2) | Limitation v1 documentée explicitement |
| Pydantic `List[dict]` incohérent (R2) | `PageLinkModel`, `WizardLinkModel`, `FicheTagsModel` ajoutés |
| FicheTags multi-occurrence (R2) | Last-write-wins documenté |
| `List[str]` pour qualificateurs (R2) | `FamilyQualifier(str, Enum)` adopté |
| `WikitextParser` instanciation à chaque appel (R2) | Patterns compilés au niveau classe |

### Points rejetés

| Point | Raison |
|---|---|
| "Impossibilité logique" — tests valident le comportement buggé (R1) | Les tests vérifient seulement `jean is not None`, pas `access_private`. La garantie tient. |
| Ponctuation dans alias — IDENTIFIER ne gère pas `-'` (R1) | `_parse_identifier` (ligne 674) accepte déjà `isalnum() or in "_-'"`. Jean-Baptiste = un token. |
| `#nsck`/`#nsckm` qualifient les enfants (R2) | Dans la spec GeneWeb, ils qualifient la vérification de sexe des **époux**. Grouper dans `FamilyQualifier` est correct. |
