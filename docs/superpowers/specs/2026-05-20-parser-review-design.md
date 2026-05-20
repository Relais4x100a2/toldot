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
    person.access_private = True   # attribut dynamique inexistant

elif token.type == TokenType.APUBL:
    person.access_public = True    # attribut dynamique inexistant
```

**Après :**
```python
elif token.type == TokenType.APRIV:
    person.access_level = AccessLevel.PRIVATE

elif token.type == TokenType.APUBL:
    person.access_level = AccessLevel.PUBLIC
```

### 1.2 Nouveaux tokens `hash_modifiers` dans `lexical.py`

Ajouter dans le dictionnaire `hash_modifiers` de `LexicalParser._compile_patterns()` :

| Clé GW | `TokenType` à créer | Champ `Person` cible |
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

### 1.3 Tests de la phase 1

- Test unitaire : tokenisation d'une ligne `#nick Qualifier #salias Dupont #image /path.jpg`
- Test unitaire : `#apriv` peuple bien `person.access_level == AccessLevel.PRIVATE`
- Test de non-régression : les 916 tests existants passent sans modification

---

## Phase 2 — Parsing des champs de personne

### Fichiers : `gw_parser.py`

Tous les champs cibles (`nickname`, `surname_alias`, `general_alias`, `image_path`, `birth_source`, `death_source`, `baptism_place`, `baptism_source`, `burial_place`, `burial_source`) sont **déjà déclarés** dans `Person` — seul le parser doit être complété.

### 2.1 Nouveaux tokens dans `_parse_inline_personal_info`

Ajouter les branches suivantes dans la boucle `while` de `_parse_inline_personal_info` :

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
        person.image_path = tokens[i].value
        i += 1

elif token.type == TokenType.BS:
    i += 1
    if i < len(tokens):
        person.birth_source = _parse_source_value(tokens, i)  # méthode existante
        i += 1

# ... idem pour DS→death_source, PP→baptism_place, PS→baptism_source,
#           RP→burial_place, RS→burial_source
```

### 2.2 Parsing de `(PublicName)`

Séquence attendue : `PAREN_OPEN IDENTIFIER+ PAREN_CLOSE`

```python
elif token.type == TokenType.PAREN_OPEN:
    parts = []
    i += 1
    while i < len(tokens) and tokens[i].type != TokenType.PAREN_CLOSE:
        parts.append(tokens[i].value.replace("_", " "))
        i += 1
    if tokens[i].type == TokenType.PAREN_CLOSE:
        i += 1
    if parts:
        person.public_name = " ".join(parts)
```

### 2.3 Parsing de `{FirstNameAlias}`

Séquence attendue : `BRACE_OPEN IDENTIFIER+ BRACE_CLOSE`

```python
elif token.type == TokenType.BRACE_OPEN:
    parts = []
    i += 1
    while i < len(tokens) and tokens[i].type != TokenType.BRACE_CLOSE:
        parts.append(tokens[i].value.replace("_", " "))
        i += 1
    if tokens[i].type == TokenType.BRACE_CLOSE:
        i += 1
    if parts:
        person.first_name_alias = " ".join(parts)
```

### 2.4 Parsing des titres `[TitleName:Title:TitlePlace:StartDate:EndDate:Nth]`

Séquence : `BRACKET_OPEN (TOKEN COLON)* BRACKET_CLOSE`

Les 6 champs séparés par `:` peuvent être vides. La méthode `_parse_title_bracket(tokens, i)` retourne `(Title, next_index)` :

```
index 0 : TitleName (ou "*" pour titre principal)
index 1 : Title type
index 2 : TitlePlace
index 3 : StartDate → Date.parse_with_fallback()
index 4 : EndDate   → Date.parse_with_fallback()
index 5 : Nth       → int
```

L'objet `Title` est construit et ajouté via `person.add_title(title)`.

### 2.5 Source mariage `#ms` dans `_parse_family_block`

Dans la boucle de parsing de la ligne `fam`, ajouter :

```python
elif token.type == TokenType.MS:
    i += 1
    if i < len(tokens):
        family.marriage_source = tokens[i].value
        i += 1
```

### 2.6 Tests de la phase 2

- Personne avec `(NomPublic)` → `person.public_name` peuplé
- Personne avec `{AliasPrenom}` → `person.first_name_alias` peuplé
- Personne avec `[*:Comte:Paris:1720:1740:2]` → `person.titles[0]` correct
- Personne avec `#nick LeGrand #salias DeSaintPaul #image /img/photo.jpg` → champs corrects
- Personne avec `1750 #bp Paris #bs Archives #dp Lyon #ds Acte` → sources peuplées
- Famille avec `#ms RegistreParoissial` → `family.marriage_source` peuplé

---

## Phase 3 — Événements complets et qualificateurs `fam`

### Fichiers : `lexical.py`, `event.py`, `family.py`, `gw_parser.py`

### 3.1 Stratégie : token générique pour les événements

Plutôt que d'ajouter ~45 membres dans `TokenType`, on adopte un **token générique `EVENT_NAME`** produit par le lexer lorsqu'un modificateur `#xxx` est rencontré dans le contexte d'un bloc `fevt`/`pevt` actif et que `xxx` n'est pas dans `hash_modifiers`.

Le lexer maintient un état booléen `_in_event_block: bool` (passé à `True` à la rencontre de `FEVT`/`PEVT`, à `False` à `END_FEVT`/`END_PEVT`). Dans ce contexte, tout `#xxx` non reconnu produit :

```python
Token(type=TokenType.EVENT_NAME, value="xxx", ...)
```

Ajouter `EVENT_NAME = "event_name"` dans `TokenType`.

### 3.2 Compléter `EventType` et `FamilyEventType` dans `event.py`

**`PersonalEventType` — membres manquants :**

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
CONFIRMATION = "conf"
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
OTHER = "strng"
```

**`FamilyEventType` — membres manquants :**

```python
NO_MARRIAGE = "nmar"
NO_MENTION = "nmen"
ANNULATION = "anul"
MARRIAGE_BANN = "marb"
MARRIAGE_CONTRACT = "marc"
MARRIAGE_LICENSE = "marl"
PACS = "pacs"
RESIDENCE = "resi"
OTHER = "strng"
```

Le parser `_parse_person_events_block` et `_parse_family_events_block` utilisent le token `EVENT_NAME` pour construire des événements avec le type string brut quand le type n'est pas dans l'enum (évolutif pour de futurs types GeneWeb).

### 3.3 Qualificateurs fam dans `family.py`

Ajouter dans `Family` :

```python
marriage_source: Optional[str] = None          # #ms
marriage_qualifiers: List[str] = field(default_factory=list)
# valeurs possibles : "banns", "contract", "license", "nsck", "nsckm", "noment"
```

Ajouter dans `hash_modifiers` du lexer :

| Clé | `TokenType` |
|---|---|
| `nsck` | `NSCK` |
| `nsckm` | `NSCKM` |
| `noment` | `NOMENT` |
| `banns` | `BANNS` |
| `contract` | `CONTRACT` |
| `license` | `LICENSE` |

Dans `_parse_family_block`, les tokens `NSCK`, `NSCKM`, `NOMENT`, `BANNS`, `CONTRACT`, `LICENSE` sont ajoutés à `family.marriage_qualifiers`.

### 3.4 Tests de la phase 3

- Bloc `pevt` avec `#grad 1/6/1985 #p Paris` → `PersonalEventType.GRADUATE` avec date et lieu
- Bloc `fevt` avec `#marb 12/3/1720 #p Lyon` → `FamilyEventType.MARRIAGE_BANN`
- Bloc `fevt` avec type inconnu futur `#xyz` → événement avec `event_type_raw = "xyz"`
- Ligne `fam` avec `#banns #contract` → `family.marriage_qualifiers == ["banns", "contract"]`

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

Extraction par regex sur la chaîne brute. Aucune modification du texte brut.

```python
class WikitextParser:
    # Ordre important : PAGE_LINK avant PERSON_LINK (les [[[ ]]] englobent [[ ]])
    PAGE_LINK   = re.compile(r'\[\[\[([^/\]\[]+)(?:/([^\]\[]*))?\]\]\]')
    PERSON_LINK = re.compile(r'\[\[(?!w:)([^/\]\[]+)/([^/\]\[]+)/(\d*)/([^\]\[]*)\]\]')
    WIZARD_LINK = re.compile(r'\[\[w:([^/\]\[]+)(?:/([^\]\[]*))?\]\]')
    FICHE_TAG   = re.compile(r'^(HEAD|OCCU|DEATH|BIBLIO|BNOTE|NOTE)=(.*)$', re.MULTILINE)

    def parse(self, raw: str) -> NoteContent:
        ...
```

Règle de priorité des regex : appliquer `PAGE_LINK` d'abord (triple crochet), puis `WIZARD_LINK`, puis `PERSON_LINK` — pour éviter les faux positifs avec les sous-séquences `[[`.

### 4.3 Intégration dans `Person` — champ parallèle (non-breaking)

`notes: List[str]` est utilisé à 12 endroits dans le code (`gedcom.py`, `xml.py`, `genealogy.py`, `event.py`, `person_payload.py`, etc.). Le remplacer casserait tous ces appelants.

**Solution : champ parallèle additionnel** — `notes` reste `List[str]`, on ajoute `notes_structured: List[NoteContent]` :

```python
# Inchangé
notes: List[str] = field(default_factory=list)

# Nouveau — peuplé en parallèle
notes_structured: List[NoteContent] = field(default_factory=list)
```

**Comportement de `add_note(text: str)` :**

```python
def add_note(self, text: str) -> None:
    self.notes.append(text)                           # comportement existant inchangé
    self.notes_structured.append(WikitextParser().parse(text))  # nouveau
```

`to_dict()` expose `notes_structured` comme champ supplémentaire. Les consommateurs existants de `notes` ne changent pas.

### 4.4 API REST

Dans `api/models/person.py`, `notes: List[str]` reste inchangé. On ajoute `notes_structured: List[NoteModel]` :

```python
class PersonLinkModel(BaseModel):
    first_name: str
    last_name: str
    occurrence: int = 0
    display_text: str = ""

class NoteModel(BaseModel):
    raw: str
    person_links: List[PersonLinkModel] = []
    page_links: List[dict] = []
    wizard_links: List[dict] = []
    fiche_tags: dict = {}

# Dans PersonResponse (ou équivalent) :
notes: List[str] = []              # inchangé
notes_structured: List[NoteModel] = []  # nouveau champ additionnel
```

### 4.5 Ce qui reste en texte brut (non parsé)

- Formatage `''italique''`, `'''gras'''`, `{surligné}` → dans `raw`
- Listes `*`/`#`, titres `=`, indentation `:` → dans `raw`
- Échappements `%'`, `%%`, `%{`, `%}` → dans `raw`
- Tableaux wikitext → dans `raw`

### 4.6 Tests de la phase 4

- Note `"Voir [[Jean/Dupont/0/Jean Dupont]]"` → `person_links[0].first_name == "Jean"`
- Note `"[[[arbre_corno/Arbre Corno]]]"` → `page_links[0].page_name == "arbre_corno"`
- Note `"[[w:Admin/Administrateur]]"` → `wizard_links[0].wizard_name == "Admin"`
- Note `"HEAD=Généalogie Dupont\nOCCU=Avocat"` → `fiche_tags.head == "Généalogie Dupont"`
- Note avec triple et double crochets mêlés → pas de faux positifs entre les types de liens
- `person.add_note("texte brut")` → `notes[0].raw == "texte brut"`, `notes[0].person_links == []`

---

## Résumé des changements par fichier

| Fichier | Phase | Nature |
|---|---|---|
| `core/parser/lexical.py` | 1, 3 | +11 tokens hash + `EVENT_NAME` + 6 qualificateurs fam |
| `core/parser/gw_parser.py` | 1, 2, 3 | Bug fix + 10 champs peuplés + `(PublicName)` + `{alias}` + titres + `ms` + qualificateurs |
| `core/person.py` | 4 | `notes_structured: List[NoteContent]` (additionnel, `notes` inchangé) |
| `core/event.py` | 3 | +35 membres `PersonalEventType` + 9 membres `FamilyEventType` |
| `core/family.py` | 3 | `marriage_source`, `marriage_qualifiers` |
| `core/parser/wikitext.py` | 4 | Nouveau module |
| `api/models/person.py` | 4 | `NoteModel` Pydantic |

## Invariants à respecter

- Toute modification est **additive** — aucun champ existant n'est supprimé ni renommé
- Les 916 tests existants passent à la fin de chaque phase
- Le seuil de couverture de 80 % est maintenu
- `mypy` passe en mode strict après chaque phase
- Les tokens `UNKNOWN` ne doivent pas augmenter après la phase 1 sur des fichiers `.gw` standards
