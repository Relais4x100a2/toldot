# Events Tab — Sortable/Filterable Tabulator Table — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the flat-card events tab with a Tabulator.js table featuring a mandatory filter gate, 7 columns with sort/filter, name resolution, and inline row expansion for notes/sources.

**Architecture:** Backend enriches event API responses with resolved person/family names and a new `/related` endpoint for genealogical graph traversal. Frontend replaces current events code with Tabulator.js (CDN) driven by a filter gate that requires at least one filter before loading.

**Tech Stack:** Python 3.8+, FastAPI, Pydantic v2, Tabulator.js 6.2.5 (CDN), vanilla JS, Bootstrap 5

---

## File Structure

**Modified:**
- `src/geneweb_py/api/models/event.py` — add 4 fields to `EventSchema`
- `src/geneweb_py/api/serialization.py` — enrich `event_to_schema` with `genealogy` param
- `src/geneweb_py/api/services/genealogy_service.py` — add `get_related_person_ids`, `_get_witness_index`, `_normalize_search_text`, accent-aware place filter, `_witness_index` cache attribute
- `src/geneweb_py/api/routers/events.py` — pass `service.genealogy` to all `event_to_schema` calls
- `src/geneweb_py/api/routers/persons.py` — add `/related` endpoint; pass `service.genealogy` to existing `event_to_schema` call
- `src/geneweb_py/api/routers/families.py` — pass `service.genealogy` to existing `event_to_schema` call
- `src/geneweb_py/api/static/index.html` — CDN links + new `#panel-events` HTML
- `src/geneweb_py/api/static/app.js` — remove old events code, add Tabulator-driven tab

**Tests modified/created:**
- `tests/api/test_serialization_helpers_coverage.py` — tests for enriched `event_to_schema`
- `tests/api/test_services.py` — tests for `get_related_person_ids` + normalize
- `tests/api/test_routers_persons.py` — tests for `/related` endpoint

---

## Task 1: Add 4 new fields to EventSchema

**Files:**
- Modify: `src/geneweb_py/api/models/event.py`
- Test: `tests/api/test_models.py`

- [ ] **Step 1: Write failing test**

```python
# In tests/api/test_models.py, add:
def test_event_schema_new_fields_optional():
    from geneweb_py.api.models.event import EventSchema
    from geneweb_py.core.models import EventType
    schema = EventSchema(
        id="evt_1",
        event_type=EventType.BIRTH,
    )
    assert schema.person_name is None
    assert schema.family_label is None
    assert schema.witness_names == []
    assert schema.date_sort_year is None

def test_event_schema_new_fields_populated():
    from geneweb_py.api.models.event import EventSchema
    from geneweb_py.core.models import EventType
    schema = EventSchema(
        id="evt_1",
        event_type=EventType.BIRTH,
        person_name="Jean Dupont",
        family_label="Dupont × Martin",
        witness_names=["Pierre Martin"],
        date_sort_year=1842,
    )
    assert schema.person_name == "Jean Dupont"
    assert schema.family_label == "Dupont × Martin"
    assert schema.witness_names == ["Pierre Martin"]
    assert schema.date_sort_year == 1842
```

- [ ] **Step 2: Run test to verify it fails**

```bash
rtk pytest tests/api/test_models.py::test_event_schema_new_fields_optional tests/api/test_models.py::test_event_schema_new_fields_populated -v
```

Expected: `FAILED` — `EventSchema` has no `person_name` attribute.

- [ ] **Step 3: Add the 4 fields to EventSchema**

In `src/geneweb_py/api/models/event.py`, in the `EventSchema` class (after `family_id`):

```python
class EventSchema(EventBaseSchema):
    """Schéma complet pour un événement."""

    id: str = Field(..., description="Identifiant unique de l'événement")
    person_id: Optional[str] = Field(
        None, description="Identifiant de la personne (pour événements personnels)"
    )
    family_id: Optional[str] = Field(
        None, description="Identifiant de la famille (pour événements familiaux)"
    )
    person_name: Optional[str] = Field(None, description="Nom résolu de la personne")
    family_label: Optional[str] = Field(None, description="Libellé résolu de la famille")
    witness_names: List[str] = Field(default_factory=list, description="Noms des témoins résolus")
    date_sort_year: Optional[int] = Field(None, description="Année de tri numérique")

    class Config:
        """Configuration Pydantic."""

        from_attributes = True
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
rtk pytest tests/api/test_models.py::test_event_schema_new_fields_optional tests/api/test_models.py::test_event_schema_new_fields_populated -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full test suite to check no regression**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing (new fields are Optional with defaults).

- [ ] **Step 6: Commit**

```bash
git add src/geneweb_py/api/models/event.py tests/api/test_models.py
git commit -m "feat(api): add person_name, family_label, witness_names, date_sort_year to EventSchema"
```

---

## Task 2: Enrich event_to_schema with genealogy-based name resolution

**Files:**
- Modify: `src/geneweb_py/api/serialization.py`
- Test: `tests/api/test_serialization_helpers_coverage.py`

- [ ] **Step 1: Write failing tests**

```python
# In tests/api/test_serialization_helpers_coverage.py, add:
from geneweb_py.api.serialization import event_to_schema
from geneweb_py.core.event import PersonalEvent, EventType
from geneweb_py.core.person import Person
from geneweb_py.core.family import Family
from geneweb_py.core.genealogy import Genealogy, GenealogyMetadata
from geneweb_py.core.date import Date
from datetime import datetime


def _make_genealogy():
    """Helper: genealogy with one person, one family."""
    p = Person(first_name="Jean", last_name="Dupont", occurrence_number=0)
    p2 = Person(first_name="Marie", last_name="Martin", occurrence_number=0)
    f = Family(husband_id=p.unique_id, wife_id=p2.unique_id)
    f.family_id = "fam_1"
    meta = GenealogyMetadata(
        source_file=None, encoding="utf-8", is_gwplus=False,
        created_date=datetime.now(), modified_date=datetime.now(),
        geneweb_version="1.0",
    )
    return Genealogy(
        persons={p.unique_id: p, p2.unique_id: p2},
        families={"fam_1": f},
        metadata=meta,
    )


def test_event_to_schema_resolves_person_name():
    genealogy = _make_genealogy()
    pid = "Dupont_Jean_0"
    ev = PersonalEvent(event_type=EventType.BIRTH)
    schema = event_to_schema(ev, event_id="e1", person_id=pid, family_id=None, genealogy=genealogy)
    assert schema.person_name == "Jean Dupont"
    assert schema.family_label is None


def test_event_to_schema_resolves_family_label():
    genealogy = _make_genealogy()
    ev = PersonalEvent(event_type=EventType.BIRTH)
    schema = event_to_schema(ev, event_id="e1", person_id=None, family_id="fam_1", genealogy=genealogy)
    assert "Dupont" in schema.family_label
    assert "Martin" in schema.family_label


def test_event_to_schema_resolves_witness_names():
    genealogy = _make_genealogy()
    pid = "Dupont_Jean_0"
    ev = PersonalEvent(event_type=EventType.BIRTH)
    ev.witnesses = [pid]
    schema = event_to_schema(ev, event_id="e1", person_id=None, family_id=None, genealogy=genealogy)
    assert "Jean Dupont" in schema.witness_names


def test_event_to_schema_extracts_date_sort_year():
    ev = PersonalEvent(event_type=EventType.BIRTH)
    ev.date = Date(year=1842, month=3, day=12)
    schema = event_to_schema(ev, event_id="e1", person_id=None, family_id=None)
    assert schema.date_sort_year == 1842


def test_event_to_schema_no_genealogy_backward_compat():
    ev = PersonalEvent(event_type=EventType.BIRTH)
    schema = event_to_schema(ev, event_id="e1", person_id="x", family_id=None)
    assert schema.person_name is None
    assert schema.witness_names == []
    assert schema.date_sort_year is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
rtk pytest tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_resolves_person_name tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_resolves_family_label tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_resolves_witness_names tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_extracts_date_sort_year tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_no_genealogy_backward_compat -v
```

Expected: `FAILED` — `event_to_schema` does not accept `genealogy` kwarg.

- [ ] **Step 3: Update event_to_schema in serialization.py**

Replace the `event_to_schema` function in `src/geneweb_py/api/serialization.py`:

```python
def event_to_schema(
    event: Event,
    *,
    event_id: str,
    person_id: Optional[str],
    family_id: Optional[str],
    genealogy: Optional["Genealogy"] = None,
) -> EventSchema:
    """Construit un ``EventSchema`` à partir d'un événement domaine."""
    if isinstance(event, PersonalEvent):
        evt_type: Any = event.event_type
    elif isinstance(event, FamilyEvent) and event.family_event_type is not None:
        evt_type = event.family_event_type
    else:
        evt_type = event.event_type

    note_joined: Optional[str] = None
    if event.notes:
        joined = "\n".join(str(n) for n in event.notes if n is not None)
        note_joined = joined if joined else None

    # Name resolution (requires genealogy)
    resolved_person_name: Optional[str] = None
    resolved_family_label: Optional[str] = None
    resolved_witness_names: List[str] = []
    date_sort_year: Optional[int] = None

    if genealogy is not None:
        if person_id is not None:
            p = genealogy.persons.get(person_id)
            if p is not None:
                resolved_person_name = (
                    f"{p.first_name} {p.last_name}".replace("_", " ").strip()
                )

        if family_id is not None:
            fam = genealogy.families.get(family_id)
            if fam is not None:
                parts: List[str] = []
                if fam.husband_id:
                    h = genealogy.persons.get(fam.husband_id)
                    if h:
                        parts.append(
                            f"{h.first_name} {h.last_name}".replace("_", " ").strip()
                        )
                if fam.wife_id:
                    w = genealogy.persons.get(fam.wife_id)
                    if w:
                        parts.append(
                            f"{w.first_name} {w.last_name}".replace("_", " ").strip()
                        )
                if parts:
                    resolved_family_label = " × ".join(parts)

        raw_witness_ids = event_witnesses_to_api_strings(event.witnesses)
        for wid in raw_witness_ids:
            wp = genealogy.persons.get(wid)
            if wp is not None:
                resolved_witness_names.append(
                    f"{wp.first_name} {wp.last_name}".replace("_", " ").strip()
                )
            else:
                resolved_witness_names.append(wid)

    if event.date is not None:
        date_sort_year = event.date.sort_year()

    return EventSchema(
        id=event_id,
        event_type=evt_type,
        date=date_to_api_string(event.date),
        place=event.place,
        reason=event.reason,
        note=note_joined,
        witnesses=event_witnesses_to_api_strings(event.witnesses),
        sources=event_sources_list(event),
        person_id=person_id,
        family_id=family_id,
        person_name=resolved_person_name,
        family_label=resolved_family_label,
        witness_names=resolved_witness_names,
        date_sort_year=date_sort_year,
    )
```

Also add `from ..core.genealogy import Genealogy` to the TYPE_CHECKING block or at the top of the imports in `serialization.py`. Since `Genealogy` is already imported at the top (line 14 in the original), use it directly — remove the string annotation `"Genealogy"` and use the direct type.

Check the existing imports in `serialization.py`:
```python
from ..core.genealogy import Genealogy
```
This is already present (used by `count_by_birth_century` etc.), so no new import needed. Change `Optional["Genealogy"]` to `Optional[Genealogy]` in the signature.

- [ ] **Step 4: Run tests to verify they pass**

```bash
rtk pytest tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_resolves_person_name tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_resolves_family_label tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_resolves_witness_names tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_extracts_date_sort_year tests/api/test_serialization_helpers_coverage.py::test_event_to_schema_no_genealogy_backward_compat -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full suite**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing (callers that don't pass `genealogy` get `None` by default → backward compat).

- [ ] **Step 6: Commit**

```bash
git add src/geneweb_py/api/serialization.py tests/api/test_serialization_helpers_coverage.py
git commit -m "feat(serialization): enrich event_to_schema with person/family name resolution"
```

---

## Task 3: Pass genealogy to all existing event_to_schema callers

**Files:**
- Modify: `src/geneweb_py/api/routers/events.py`
- Modify: `src/geneweb_py/api/routers/persons.py`
- Modify: `src/geneweb_py/api/routers/families.py`

No new tests needed — existing router tests cover these endpoints. This task verifies names appear in responses.

- [ ] **Step 1: Update routers/events.py — add genealogy to all event_to_schema calls**

In `src/geneweb_py/api/routers/events.py`, every call to `event_to_schema(...)` gains `genealogy=service.genealogy`. There are 5 call sites:

**`create_personal_event` (line ~110):**
```python
event_schema = event_to_schema(
    event, event_id=eid, person_id=person_key, family_id=None,
    genealogy=service.genealogy,
)
```

**`create_family_event` (line ~162):**
```python
event_schema = event_to_schema(
    event, event_id=eid, person_id=None, family_id=event_data.family_id,
    genealogy=service.genealogy,
)
```

**`get_event` (line ~213):**
```python
event_schema = event_to_schema(
    event,
    event_id=eid,
    person_id=pid or getattr(event, "person_id", None),
    family_id=fid or getattr(event, "family_id", None),
    genealogy=service.genealogy,
)
```

**`update_event` (line ~272):**
```python
event_schema = event_to_schema(
    event,
    event_id=eid,
    person_id=pid or getattr(event, "person_id", None),
    family_id=fid or getattr(event, "family_id", None),
    genealogy=service.genealogy,
)
```

**`list_events` (line ~407 inside loop):**
```python
event_schemas.append(
    event_to_schema(
        ev,
        event_id=eid,
        person_id=hit_pid or getattr(ev, "person_id", None),
        family_id=hit_fid or getattr(ev, "family_id", None),
        genealogy=service.genealogy,
    ).model_dump()
)
```

- [ ] **Step 2: Update routers/persons.py — person events endpoint (~line 316)**

```python
events_out.append(
    event_to_schema(
        ev, event_id=eid, person_id=person.unique_id, family_id=None,
        genealogy=service.genealogy,
    ).model_dump()
)
```

- [ ] **Step 3: Update routers/families.py — family events endpoint (~line 327)**

```python
events.append(
    event_to_schema(
        event, event_id=eid, person_id=None, family_id=family_id,
        genealogy=service.genealogy,
    ).model_dump()
)
```

- [ ] **Step 4: Run full suite**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing.

- [ ] **Step 5: Commit**

```bash
git add src/geneweb_py/api/routers/events.py src/geneweb_py/api/routers/persons.py src/geneweb_py/api/routers/families.py
git commit -m "feat(routers): pass genealogy to event_to_schema for name resolution"
```

---

## Task 4: Accent/hyphen-insensitive place filter in search_events

**Files:**
- Modify: `src/geneweb_py/api/services/genealogy_service.py`
- Test: `tests/api/test_services.py`

- [ ] **Step 1: Write failing tests**

```python
# In tests/api/test_services.py, add:
def test_normalize_search_text_accents():
    from geneweb_py.api.services.genealogy_service import _normalize_search_text
    assert _normalize_search_text("Évreux") == "evreux"
    assert _normalize_search_text("île-de-france") == "ile de france"
    assert _normalize_search_text("Saône-et-Loire") == "saone et loire"


def test_search_events_place_accent_insensitive(genealogy_service):
    # genealogy_service fixture already exists in test_services.py
    # Add an event with accented place
    from geneweb_py.core.event import PersonalEvent, EventType
    from geneweb_py.core.person import Person
    p = Person(first_name="Test", last_name="User", occurrence_number=0)
    ev = PersonalEvent(event_type=EventType.BIRTH)
    ev.place = "Île-de-France"
    p.events.append(ev)
    genealogy_service._genealogy.persons[p.unique_id] = p

    hits, total = genealogy_service.search_events({"place": "ile de france"})
    assert total >= 1
    places = [h.event.place for h in hits]
    assert "Île-de-France" in places
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
rtk pytest tests/api/test_services.py::test_normalize_search_text_accents tests/api/test_services.py::test_search_events_place_accent_insensitive -v
```

Expected: `FAILED` — `_normalize_search_text` not found.

- [ ] **Step 3: Add normalize helper and update place filter**

In `src/geneweb_py/api/services/genealogy_service.py`:

At the top-level (after imports, before the class), add:

```python
import unicodedata


def _normalize_search_text(text: str) -> str:
    """Normalize for accent/case/hyphen-insensitive comparison."""
    nfd = unicodedata.normalize("NFD", text.lower())
    no_accents = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return no_accents.replace("-", " ").replace("_", " ")
```

Then in `search_events`, replace the existing place filter block:

```python
        if search_params.get("place"):
            hits = [
                h
                for h in hits
                if search_params["place"].lower() in (h.event.place or "").lower()
            ]
```

with:

```python
        if search_params.get("place"):
            needle = _normalize_search_text(search_params["place"])
            hits = [
                h
                for h in hits
                if needle in _normalize_search_text(h.event.place or "")
            ]
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
rtk pytest tests/api/test_services.py::test_normalize_search_text_accents tests/api/test_services.py::test_search_events_place_accent_insensitive -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full suite**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing.

- [ ] **Step 6: Commit**

```bash
git add src/geneweb_py/api/services/genealogy_service.py tests/api/test_services.py
git commit -m "feat(service): accent/hyphen-insensitive place filter in search_events"
```

---

## Task 5: Add get_related_person_ids to GenealogyService

**Files:**
- Modify: `src/geneweb_py/api/services/genealogy_service.py`
- Test: `tests/api/test_services.py`

- [ ] **Step 1: Write failing tests**

```python
# In tests/api/test_services.py, add:
def _build_family_genealogy():
    """
    Genealogy with:
      - Jean Dupont (pid_jean) — child of fam_parents, spouse in fam_couple
      - Marie Martin (pid_marie) — spouse in fam_couple
      - Paul Dupont (pid_paul) — sibling in fam_parents, child of fam_parents
      - Henri Dupont (pid_henri) — father in fam_parents
      - Louise Blanc (pid_louise) — mother in fam_parents
      - Enfant Dupont (pid_enfant) — child in fam_couple
      - Pierre Témoin (pid_pierre) — witnesses an event of pid_jean
    """
    from geneweb_py.core.person import Person
    from geneweb_py.core.family import Family, Child, ChildSex
    from geneweb_py.core.event import PersonalEvent, EventType
    from geneweb_py.core.genealogy import Genealogy, GenealogyMetadata
    from datetime import datetime

    def mkp(first, last):
        p = Person(first_name=first, last_name=last, occurrence_number=0)
        return p

    jean = mkp("Jean", "Dupont")
    marie = mkp("Marie", "Martin")
    paul = mkp("Paul", "Dupont")
    henri = mkp("Henri", "Dupont")
    louise = mkp("Louise", "Blanc")
    enfant = mkp("Enfant", "Dupont")
    pierre = mkp("Pierre", "Temoin")

    fam_couple = Family(husband_id=jean.unique_id, wife_id=marie.unique_id)
    fam_couple.family_id = "fam_couple"
    fam_couple.children = [Child(person_id=enfant.unique_id, sex=ChildSex.UNKNOWN)]

    fam_parents = Family(husband_id=henri.unique_id, wife_id=louise.unique_id)
    fam_parents.family_id = "fam_parents"
    fam_parents.children = [
        Child(person_id=jean.unique_id, sex=ChildSex.UNKNOWN),
        Child(person_id=paul.unique_id, sex=ChildSex.UNKNOWN),
    ]

    jean.families_as_spouse = ["fam_couple"]
    jean.families_as_child = ["fam_parents"]
    marie.families_as_spouse = ["fam_couple"]
    paul.families_as_child = ["fam_parents"]
    enfant.families_as_child = ["fam_couple"]

    # Pierre witnesses an event of Jean
    birth_jean = PersonalEvent(event_type=EventType.BIRTH)
    birth_jean.witnesses = [pierre.unique_id]
    jean.events.append(birth_jean)

    meta = GenealogyMetadata(
        source_file=None, encoding="utf-8", is_gwplus=False,
        created_date=datetime.now(), modified_date=datetime.now(),
        geneweb_version="1.0",
    )
    persons = {p.unique_id: p for p in [jean, marie, paul, henri, louise, enfant, pierre]}
    families = {fam_couple.family_id: fam_couple, fam_parents.family_id: fam_parents}
    return Genealogy(persons=persons, families=families, metadata=meta), jean.unique_id


def test_get_related_degree1_includes_self_and_spouse():
    from geneweb_py.api.services.genealogy_service import GenealogyService
    from geneweb_py.core.person import Person
    g, jean_id = _build_family_genealogy()
    svc = GenealogyService(genealogy=g)
    result = svc.get_related_person_ids(jean_id, degree=1)
    pids = set(result["person_ids"])
    assert jean_id in pids
    marie_id = g.persons[jean_id].families_as_spouse  # "fam_couple"
    marie = next(p for p in g.persons.values() if p.first_name == "Marie")
    assert marie.unique_id in pids


def test_get_related_degree1_family_ids():
    from geneweb_py.api.services.genealogy_service import GenealogyService
    g, jean_id = _build_family_genealogy()
    svc = GenealogyService(genealogy=g)
    result = svc.get_related_person_ids(jean_id, degree=1)
    assert "fam_couple" in result["family_ids"]
    assert result["witness_person_id"] == jean_id


def test_get_related_degree2_includes_parents_children_siblings():
    from geneweb_py.api.services.genealogy_service import GenealogyService
    g, jean_id = _build_family_genealogy()
    svc = GenealogyService(genealogy=g)
    result = svc.get_related_person_ids(jean_id, degree=2)
    pids = set(result["person_ids"])
    henri = next(p for p in g.persons.values() if p.first_name == "Henri")
    paul = next(p for p in g.persons.values() if p.first_name == "Paul")
    enfant = next(p for p in g.persons.values() if p.first_name == "Enfant")
    assert henri.unique_id in pids  # parent
    assert paul.unique_id in pids   # sibling
    assert enfant.unique_id in pids # child


def test_get_related_degree3_includes_persons_x_witnessed():
    from geneweb_py.api.services.genealogy_service import GenealogyService
    g, jean_id = _build_family_genealogy()
    # Pierre witnessed an event of Jean.
    # So from Pierre's perspective at degree=3, Jean should be included.
    pierre = next(p for p in g.persons.values() if p.first_name == "Pierre")
    svc = GenealogyService(genealogy=g)
    result = svc.get_related_person_ids(pierre.unique_id, degree=3)
    pids = set(result["person_ids"])
    assert jean_id in pids


def test_get_related_unknown_person_returns_empty():
    from geneweb_py.api.services.genealogy_service import GenealogyService
    g, _ = _build_family_genealogy()
    svc = GenealogyService(genealogy=g)
    result = svc.get_related_person_ids("nonexistent_id", degree=1)
    assert result["person_ids"] == []
    assert result["family_ids"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
rtk pytest tests/api/test_services.py::test_get_related_degree1_includes_self_and_spouse tests/api/test_services.py::test_get_related_degree2_includes_parents_children_siblings tests/api/test_services.py::test_get_related_degree3_includes_persons_x_witnessed tests/api/test_services.py::test_get_related_unknown_person_returns_empty -v
```

Expected: `FAILED` — `GenealogyService` has no `get_related_person_ids`.

- [ ] **Step 3: Add _witness_index cache and methods to GenealogyService**

In `src/geneweb_py/api/services/genealogy_service.py`, in `GenealogyService.__init__`, add the cache attribute:

```python
def __init__(self, genealogy: Optional[Genealogy] = None) -> None:
    """Initialise le service de généalogie."""
    self._genealogy: Optional[Genealogy] = None
    self._parser = GeneWebParser(use_multipass=False)
    self._witness_index: Optional[Dict[str, set]] = None  # lazy cache
    if genealogy is not None:
        self._genealogy = genealogy
    else:
        self._initialize_empty_genealogy()
```

Add `Dict` and `Set` to typing imports if not already present (they already are in the file).

Then add two new methods to `GenealogyService` (before `get_stats` or at the end of the class):

```python
def _get_witness_index(self) -> Dict[str, set]:
    """Returns {witness_id: set_of_person_ids_whose_events_they_witnessed}. Lazy-computed."""
    if self._witness_index is not None:
        return self._witness_index
    index: Dict[str, set] = {}
    genealogy = self.genealogy
    for person in genealogy.persons.values():
        for event in person.events:
            for wid in event_witnesses_to_api_strings(event.witnesses):
                index.setdefault(wid, set()).add(person.unique_id)
    for family in genealogy.families.values():
        for event in family.events:
            for wid in event_witnesses_to_api_strings(event.witnesses):
                for pid in [family.husband_id, family.wife_id]:
                    if pid:
                        index.setdefault(wid, set()).add(pid)
    self._witness_index = index
    return self._witness_index

def get_related_person_ids(
    self, person_id: str, degree: int
) -> Dict[str, Any]:
    """
    Returns person_ids and family_ids related to person_id up to the given degree.

    Degree 1: self + spouses + families_as_spouse
    Degree 2: + parents, children, siblings
    Degree 3: + persons whose events person_id witnessed
    """
    genealogy = self.genealogy
    person = genealogy.persons.get(person_id)
    if person is None:
        return {
            "person_ids": [],
            "family_ids": [],
            "witness_person_id": person_id,
        }

    person_ids: set = {person_id}
    family_ids: set = set(person.families_as_spouse)

    # Degree 1: include spouses
    for fam_id in person.families_as_spouse:
        fam = genealogy.families.get(fam_id)
        if fam is not None:
            if fam.husband_id:
                person_ids.add(fam.husband_id)
            if fam.wife_id:
                person_ids.add(fam.wife_id)

    if degree >= 2:
        # Parents and siblings (via families_as_child)
        for fam_id in person.families_as_child:
            fam = genealogy.families.get(fam_id)
            if fam is not None:
                if fam.husband_id:
                    person_ids.add(fam.husband_id)
                if fam.wife_id:
                    person_ids.add(fam.wife_id)
                for child in fam.children:
                    person_ids.add(child.person_id)
        # Children (via families_as_spouse)
        for fam_id in person.families_as_spouse:
            fam = genealogy.families.get(fam_id)
            if fam is not None:
                for child in fam.children:
                    person_ids.add(child.person_id)

    if degree >= 3:
        witness_index = self._get_witness_index()
        person_ids.update(witness_index.get(person_id, set()))

    return {
        "person_ids": list(person_ids),
        "family_ids": list(family_ids),
        "witness_person_id": person_id,
    }
```

Also add the import for `event_witnesses_to_api_strings` at the top of `genealogy_service.py` if not already imported:

```python
from ..serialization import event_witnesses_to_api_strings
```

Check existing imports — if this is already in scope via a different path, skip.

- [ ] **Step 4: Run tests to verify they pass**

```bash
rtk pytest tests/api/test_services.py::test_get_related_degree1_includes_self_and_spouse tests/api/test_services.py::test_get_related_degree1_family_ids tests/api/test_services.py::test_get_related_degree2_includes_parents_children_siblings tests/api/test_services.py::test_get_related_degree3_includes_persons_x_witnessed tests/api/test_services.py::test_get_related_unknown_person_returns_empty -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full suite**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing.

- [ ] **Step 6: Commit**

```bash
git add src/geneweb_py/api/services/genealogy_service.py tests/api/test_services.py
git commit -m "feat(service): add get_related_person_ids with degree 1/2/3 graph traversal"
```

---

## Task 6: Add GET /api/v1/persons/{person_id}/related endpoint

**Files:**
- Modify: `src/geneweb_py/api/routers/persons.py`
- Test: `tests/api/test_routers_persons.py`

- [ ] **Step 1: Write failing tests**

```python
# In tests/api/test_routers_persons.py, add:
def test_get_related_persons_degree1(client, mock_service):
    mock_service.get_related_person_ids.return_value = {
        "person_ids": ["id1", "id2"],
        "family_ids": ["fam1"],
        "witness_person_id": "id1",
    }
    response = client.get(
        "/api/v1/persons/id1/related",
        headers={"X-Session-Token": "test-token"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["person_ids"] == ["id1", "id2"]
    assert data["data"]["family_ids"] == ["fam1"]
    assert data["data"]["witness_person_id"] == "id1"
    mock_service.get_related_person_ids.assert_called_once_with("id1", 1)


def test_get_related_persons_degree3(client, mock_service):
    mock_service.get_related_person_ids.return_value = {
        "person_ids": ["id1", "id2", "id3"],
        "family_ids": [],
        "witness_person_id": "id1",
    }
    response = client.get(
        "/api/v1/persons/id1/related?degree=3",
        headers={"X-Session-Token": "test-token"},
    )
    assert response.status_code == 200
    mock_service.get_related_person_ids.assert_called_once_with("id1", 3)


def test_get_related_persons_unknown_returns_empty(client, mock_service):
    mock_service.get_related_person_ids.return_value = {
        "person_ids": [],
        "family_ids": [],
        "witness_person_id": "unknown",
    }
    response = client.get(
        "/api/v1/persons/unknown/related",
        headers={"X-Session-Token": "test-token"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["person_ids"] == []
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
rtk pytest tests/api/test_routers_persons.py::test_get_related_persons_degree1 tests/api/test_routers_persons.py::test_get_related_persons_degree3 tests/api/test_routers_persons.py::test_get_related_persons_unknown_returns_empty -v
```

Expected: `FAILED` — 404 (route does not exist).

- [ ] **Step 3: Add the /related endpoint to routers/persons.py**

In `src/geneweb_py/api/routers/persons.py`, add this endpoint. Place it before the existing `@router.get("/{person_id}")` route (to avoid path conflicts):

```python
@router.get("/{person_id}/related", response_model=SuccessResponse)
async def get_related_persons(
    person_id: str,
    degree: int = Query(1, ge=1, le=3, description="Degré de lien (1, 2 ou 3)"),
    service: GenealogyService = Depends(get_session_service),
) -> SuccessResponse:
    """
    Retourne les person_ids et family_ids liés à person_id jusqu'au degré donné.
    """
    try:
        result = service.get_related_person_ids(person_id, degree)
        return SuccessResponse(
            message="Personnes liées récupérées avec succès",
            data=result,
        )
    except Exception as exc:
        raise_internal_server_error(
            "Erreur lors de la récupération des personnes liées", exc
        )
```

Also add `Query` to the FastAPI imports at the top of `routers/persons.py` if not already there:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
rtk pytest tests/api/test_routers_persons.py::test_get_related_persons_degree1 tests/api/test_routers_persons.py::test_get_related_persons_degree3 tests/api/test_routers_persons.py::test_get_related_persons_unknown_returns_empty -v
```

Expected: `PASSED`

- [ ] **Step 5: Run full suite**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing.

- [ ] **Step 6: Commit**

```bash
git add src/geneweb_py/api/routers/persons.py tests/api/test_routers_persons.py
git commit -m "feat(router): add GET /persons/{id}/related endpoint with degree param"
```

---

## Task 7: Update index.html — CDN links and new events panel HTML

**Files:**
- Modify: `src/geneweb_py/api/static/index.html`

No Python tests. Manual verification step included.

- [ ] **Step 1: Add Tabulator CDN links**

In `src/geneweb_py/api/static/index.html`, inside `<head>`, add after the existing `<link rel="stylesheet" href="/style.css">`:

```html
  <link href="https://cdn.jsdelivr.net/npm/tabulator-tables@6.2.5/dist/css/tabulator_midnight.min.css" rel="stylesheet">
```

Before `</body>`, add after `<script src="/vendor/bootstrap.bundle.min.js">`:

```html
<script src="https://cdn.jsdelivr.net/npm/tabulator-tables@6.2.5/dist/js/tabulator.min.js"></script>
```

- [ ] **Step 2: Replace the #panel-events content**

Replace the entire `<!-- === ÉVÉNEMENTS === -->` block (lines 88–113) with:

```html
    <!-- === ÉVÉNEMENTS === -->
    <div id="panel-events" class="tab-panel">
      <div class="event-filters">
        <div class="row g-2 mb-2 align-items-end">
          <div class="col-auto">
            <label class="d-block" style="font-size:0.82rem;color:var(--text-muted)">Types</label>
            <div class="event-type-checkboxes" id="evt-types"></div>
          </div>
          <div class="col-auto">
            <label class="d-block" style="font-size:0.82rem;color:var(--text-muted)">Lieu</label>
            <input type="text" id="evt-lieu" class="evt-filter-input" placeholder="Paris, Lyon…" style="width:140px">
          </div>
          <div class="col-auto" style="position:relative">
            <label class="d-block" style="font-size:0.82rem;color:var(--text-muted)">Personne</label>
            <input type="text" id="evt-person-name" class="evt-filter-input" placeholder="Nom prénom…" autocomplete="off" style="width:160px">
            <input type="hidden" id="evt-person-id">
            <div id="evt-person-suggestions" class="autocomplete-dropdown" style="display:none;position:absolute;z-index:200;background:var(--card-bg);border:1px solid var(--border);border-radius:4px;max-height:180px;overflow-y:auto;width:100%"></div>
            <select id="evt-degree" style="margin-top:4px;width:100%;font-size:0.8rem;padding:0.2rem;background:var(--card-bg);border:1px solid var(--border);color:var(--text);border-radius:4px">
              <option value="1">Degré 1 — direct</option>
              <option value="2">Degré 2 — famille proche</option>
              <option value="3">Degré 3 — témoignages</option>
            </select>
          </div>
          <div class="col-auto">
            <label class="d-block" style="font-size:0.82rem;color:var(--text-muted)">Nom de famille</label>
            <input type="text" id="evt-nom-famille" class="evt-filter-input" placeholder="Dupont…" style="width:130px">
          </div>
          <div class="col-auto">
            <button class="btn-primary-toldot" style="font-size:0.9rem;padding:0.4rem 1.2rem" id="evt-search-btn" disabled>Rechercher</button>
          </div>
        </div>
        <div id="evt-status" style="color:var(--text-muted);font-style:italic;font-size:0.82rem;min-height:1.2em"></div>
      </div>
      <div id="events-table" style="margin-top:0.5rem"></div>
    </div>
```

- [ ] **Step 3: Start the API server and verify the page loads without JS errors**

```bash
rtk proxy python3 run_api.py --reload
```

Open `http://127.0.0.1:8000` in a browser. Verify:
- No JS console errors about Tabulator (library loads)
- Events tab shows the new filter panel
- Search button is initially disabled

- [ ] **Step 4: Commit**

```bash
git add src/geneweb_py/api/static/index.html
git commit -m "feat(frontend): add Tabulator CDN and new events panel HTML with filter gate"
```

---

## Task 8: Rewrite events tab JavaScript in app.js

**Files:**
- Modify: `src/geneweb_py/api/static/app.js`

- [ ] **Step 1: Remove old events code**

In `src/geneweb_py/api/static/app.js`, delete the entire `// ==================== ÉVÉNEMENTS ====================` section (approximately lines 603–717), which includes:
- `const EVENT_TYPES = [...]`
- `function buildEventTypeCheckboxes()`
- `function wireEventsTab()`
- `async function searchEvents()`
- `async function fetchAllEventItems(...)`
- `function renderEvents(...)`
- `function extractMonth(...)`
- `function extractDay(...)`

- [ ] **Step 2: In the init() function, replace the two old calls**

Find in `init()`:
```javascript
wireEventsTab();
```
and
```javascript
buildEventTypeCheckboxes();
```

Replace both with a single call:
```javascript
initEventsTab();
```

- [ ] **Step 3: Add new events tab code at the same location**

At the position where the old events section was, insert the following complete replacement:

```javascript
// ==================== ÉVÉNEMENTS ====================
const EVENT_TYPES = [
  { value: 'birt', label: 'Naissance' },
  { value: 'deat', label: 'Décès' },
  { value: 'marr', label: 'Mariage' },
  { value: 'div',  label: 'Divorce' },
  { value: 'sep',  label: 'Séparation' },
  { value: 'bapt', label: 'Baptême' },
  { value: 'buri', label: 'Inhumation' },
  { value: 'enga', label: 'Fiançailles' },
  { value: 'pacs', label: 'PACS' },
  { value: 'oth',  label: 'Autre' },
];

const EVENT_TYPE_MAP = Object.fromEntries(EVENT_TYPES.map(t => [t.value, t.label]));

let eventsTable = null;

function initEventsTab() {
  // Build type checkboxes
  const container = document.getElementById('evt-types');
  if (container) {
    container.innerHTML = EVENT_TYPES.map(t =>
      `<label style="margin-right:0.5rem;font-size:0.82rem"><input type="checkbox" value="${escHtml(t.value)}" class="evt-type-cb"> ${escHtml(t.label)}</label>`
    ).join('');
  }

  // Gate: enable search button only when at least one filter is filled
  const filterInputs = document.querySelectorAll('.evt-filter-input');
  filterInputs.forEach(inp => inp.addEventListener('input', checkEvtGate));
  document.querySelectorAll('.evt-type-cb').forEach(cb =>
    cb.addEventListener('change', checkEvtGate)
  );

  const btn = document.getElementById('evt-search-btn');
  if (btn) btn.addEventListener('click', runEvtSearch);

  // Person autocomplete
  wirePersonAutocomplete();
}

function checkEvtGate() {
  const hasType = [...document.querySelectorAll('.evt-type-cb:checked')].length > 0;
  const hasLieu = (document.getElementById('evt-lieu').value || '').trim().length > 0;
  const hasPerson = (document.getElementById('evt-person-id').value || '').trim().length > 0;
  const hasNom = (document.getElementById('evt-nom-famille').value || '').trim().length > 0;
  document.getElementById('evt-search-btn').disabled = !(hasType || hasLieu || hasPerson || hasNom);
}

function normalizeEvtText(str) {
  return (str || '').normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[-_]/g, ' ');
}

async function runEvtSearch() {
  const selectedTypes = [...document.querySelectorAll('.evt-type-cb:checked')].map(cb => cb.value);
  const lieu = (document.getElementById('evt-lieu').value || '').trim();
  const personId = (document.getElementById('evt-person-id').value || '').trim();
  const personDegree = parseInt(document.getElementById('evt-degree').value) || 1;
  const nomFamille = (document.getElementById('evt-nom-famille').value || '').trim();

  const statusEl = document.getElementById('evt-status');
  statusEl.textContent = 'Chargement…';

  // Destroy previous table while loading
  if (eventsTable) { eventsTable.destroy(); eventsTable = null; }

  try {
    // Step 1: resolve related person context if person filter active
    let relCtx = null;
    if (personId) {
      const rel = await apiJson(
        `/api/v1/persons/${encodeURIComponent(personId)}/related?degree=${personDegree}`
      );
      relCtx = rel.data;
    }

    // Step 2: load all events with server-side filters (type + lieu)
    const items = await fetchEvtItems(selectedTypes, lieu);

    // Step 3: client-side filters
    let filtered = items;
    if (relCtx) {
      const pids = new Set(relCtx.person_ids);
      const fids = new Set(relCtx.family_ids);
      const wpid = relCtx.witness_person_id;
      filtered = filtered.filter(e =>
        pids.has(e.person_id) ||
        fids.has(e.family_id) ||
        (wpid && Array.isArray(e.witnesses) && e.witnesses.includes(wpid))
      );
    }
    if (nomFamille) {
      const norm = normalizeEvtText(nomFamille);
      filtered = filtered.filter(e =>
        normalizeEvtText(e.person_name || '').includes(norm) ||
        normalizeEvtText(e.family_label || '').includes(norm)
      );
    }

    statusEl.textContent = `${filtered.length} événement(s) trouvé(s)`;
    buildEventsTable(filtered);
  } catch (err) {
    if (err.message === 'session-expired') return;
    statusEl.textContent = 'Erreur lors de la recherche.';
  }
}

async function fetchEvtItems(selectedTypes, lieu) {
  const typesToFetch = selectedTypes.length > 0 ? selectedTypes : [null];
  const allItems = [];

  for (const type of typesToFetch) {
    let page = 1;
    while (true) {
      const params = new URLSearchParams({ page, size: 100 });
      if (type) params.set('event_type', type);
      if (lieu) params.set('place', lieu);
      const data = await apiJson('/api/v1/events?' + params);
      allItems.push(...data.items);
      if (!data.pagination.has_next) break;
      page++;
      if (page > 200) break;
    }
  }

  if (selectedTypes.length > 1) {
    const seen = new Set();
    return allItems.filter(e => {
      if (seen.has(e.id)) return false;
      seen.add(e.id);
      return true;
    });
  }
  return allItems;
}

function buildEventsTable(data) {
  if (eventsTable) { eventsTable.destroy(); eventsTable = null; }

  eventsTable = new Tabulator('#events-table', {
    data,
    layout: 'fitColumns',
    height: '520px',
    virtualDom: true,
    rowFormatter: function(row) {
      const el = row.getElement();
      if (!el.classList.contains('row-expanded')) return;
      if (el.querySelector('.evt-row-detail')) return;
      const d = row.getData();
      const note = d.note || '';
      const sources = Array.isArray(d.sources) ? d.sources.join(' ; ') : (d.sources || '');
      const div = document.createElement('div');
      div.className = 'evt-row-detail';
      div.style.cssText = 'padding:0.4rem 0.8rem;background:var(--card-bg,#1e1e2e);border-top:1px solid var(--border,#333);font-size:0.82rem;color:var(--text,#ccc)';
      div.innerHTML =
        `<strong>Notes&nbsp;:</strong> ${escHtml(note || '—')}<br>` +
        `<strong>Sources&nbsp;:</strong> ${escHtml(sources || '—')}`;
      el.appendChild(div);
    },
    rowClick: function(e, row) {
      const el = row.getElement();
      const existing = el.querySelector('.evt-row-detail');
      if (existing) {
        existing.remove();
        el.classList.remove('row-expanded');
      } else {
        el.classList.add('row-expanded');
        row.reformat();
      }
    },
    columns: [
      {
        title: 'Type',
        field: 'event_type',
        width: 120,
        sorter: 'string',
        headerFilter: 'select',
        headerFilterParams: {
          values: Object.assign({ '': 'Tous' }, EVENT_TYPE_MAP),
        },
        formatter: cell => escHtml(EVENT_TYPE_MAP[cell.getValue()] || cell.getValue() || '?'),
      },
      {
        title: 'Date',
        field: 'date',
        width: 130,
        sorter: (a, b, aRow, bRow) =>
          (aRow.getData().date_sort_year || 0) - (bRow.getData().date_sort_year || 0),
        headerFilter: 'input',
        formatter: cell => escHtml(cell.getValue() || '—'),
      },
      {
        title: 'Lieu',
        field: 'place',
        width: 150,
        sorter: 'string',
        headerFilter: 'input',
        formatter: cell => escHtml(cell.getValue() || '—'),
      },
      {
        title: 'Personne / Famille',
        field: 'person_name',
        width: 180,
        sorter: 'string',
        headerFilter: 'input',
        formatter: cell => {
          const d = cell.getRow().getData();
          return escHtml(d.person_name || d.family_label || '—');
        },
      },
      {
        title: 'Témoins',
        field: 'witness_names',
        width: 160,
        sorter: false,
        headerFilter: false,
        formatter: cell => escHtml((cell.getValue() || []).join(', ') || '—'),
      },
      {
        title: 'Notes',
        field: 'note',
        width: 110,
        sorter: false,
        headerFilter: false,
        formatter: cell => {
          const v = cell.getValue() || '';
          return escHtml(v.length > 60 ? v.slice(0, 60) + '…' : v || '—');
        },
      },
      {
        title: 'Sources',
        field: 'sources',
        width: 110,
        sorter: false,
        headerFilter: false,
        formatter: cell => {
          const v = (cell.getValue() || []).join(' ; ');
          return escHtml(v.length > 60 ? v.slice(0, 60) + '…' : v || '—');
        },
      },
    ],
  });
}

function wirePersonAutocomplete() {
  const nameInput = document.getElementById('evt-person-name');
  const idInput   = document.getElementById('evt-person-id');
  const dropdown  = document.getElementById('evt-person-suggestions');
  if (!nameInput) return;

  let debounceTimer = null;

  nameInput.addEventListener('input', () => {
    idInput.value = '';
    checkEvtGate();
    clearTimeout(debounceTimer);
    const q = nameInput.value.trim();
    if (q.length < 2) { dropdown.style.display = 'none'; return; }
    debounceTimer = setTimeout(async () => {
      try {
        const data = await apiJson(`/api/v1/persons/?query=${encodeURIComponent(q)}&size=10`);
        const items = data.items || [];
        if (!items.length) { dropdown.style.display = 'none'; return; }
        dropdown.innerHTML = items.map(p => {
          const label = `${escHtml(p.first_name || '')} ${escHtml(p.surname || '')}`.trim();
          return `<div class="autocomplete-item" data-id="${escHtml(p.id)}" data-label="${label}" style="padding:0.3rem 0.6rem;cursor:pointer;font-size:0.82rem">${label}</div>`;
        }).join('');
        dropdown.style.display = 'block';
        dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
          item.addEventListener('mousedown', e => {
            e.preventDefault();
            nameInput.value = item.dataset.label;
            idInput.value   = item.dataset.id;
            dropdown.style.display = 'none';
            checkEvtGate();
          });
        });
      } catch (err) {
        dropdown.style.display = 'none';
      }
    }, 250);
  });

  nameInput.addEventListener('blur', () => {
    setTimeout(() => { dropdown.style.display = 'none'; }, 200);
  });
}
```

- [ ] **Step 4: Run full Python test suite to confirm no backend regressions**

```bash
rtk pytest tests/ -x -q
```

Expected: all passing.

- [ ] **Step 5: Start server and manually verify the events tab**

```bash
rtk proxy python3 run_api.py --reload
```

Upload a `.gw` file. Then in the events tab:

1. Verify search button is disabled with no filters
2. Check one type checkbox → button enables
3. Click "Rechercher" → table appears with 7 columns
4. Click a column header → rows sort
5. Click a row → notes/sources expand inline; click again → collapse
6. Type in a Tabulator header filter → rows filter live
7. Type a name in "Personne" field → autocomplete dropdown appears; select → button enables
8. Clear the person field → button disables

- [ ] **Step 6: Commit**

```bash
git add src/geneweb_py/api/static/app.js
git commit -m "feat(frontend): Tabulator events table with filter gate, autocomplete, row expansion"
```

---

## Self-Review Checklist

- [x] **EventSchema enrichment** — Task 1 + Task 2 cover all 4 new fields
- [x] **event_to_schema callers** — Task 3 updates all 3 router files (events, persons, families)
- [x] **Accent-insensitive place filter** — Task 4
- [x] **get_related_person_ids** — Task 5 covers degree 1/2/3 and unknown person
- [x] **/related endpoint** — Task 6
- [x] **index.html CDN + HTML** — Task 7
- [x] **app.js Tabulator table** — Task 8 covers filter gate, loading, client-side filtering, Tabulator build, autocomplete, row expansion
- [x] **witness_names in API response** — serialization.py resolves via `event_witnesses_to_api_strings` in Task 2
- [x] **date_sort_year for date sort** — serialization.py `event.date.sort_year()` in Task 2; Tabulator custom sorter in Task 8
- [x] **Nom de famille client-side filter** — `normalizeEvtText` in Task 8
- [x] **Coverage ≥ 80%** — new methods have tests; no code paths left untested
