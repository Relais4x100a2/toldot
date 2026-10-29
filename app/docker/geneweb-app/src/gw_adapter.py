"""
Adaptateur geneweb-py -> PEVTRaw (branché dans pevt_extractor)

Remplace l'ancien parseur regex interne (supprimé) par le moteur central
``geneweb-py``.

Les pages Streamlit continuent de consommer des ``PEVTRaw`` : rien d'autre ne change.
``geneweb-py`` est importé à l'appel pour que l'application démarre même si la
dépendance n'est pas installée (elle est dans le groupe ``dev`` tant que le
paquet n'est pas publié).
"""
from typing import List

from .data_models import PEVTRaw


def extract_custom_pevts(file_path: str) -> List[PEVTRaw]:
    """Extrait les événements personnels non standardisés (#strng) d'un .gw"""
    from geneweb_py.core.event import EventType
    from geneweb_py.core.parser.gw_parser import GeneWebParser

    genealogy = GeneWebParser().parse_file(file_path)
    pevts: List[PEVTRaw] = []

    for person in genealogy.persons.values():
        for event in person.events:
            # Les tags standard (dont l'alias #bapm) sont typés par geneweb-py ;
            # seuls les tags personnalisés restent en OTHER avec leur tag brut.
            if event.event_type is not EventType.OTHER or not event.event_type_raw:
                continue

            witnesses = []
            for witness in event.witnesses:
                other = genealogy.persons.get(witness["person_id"])
                label = f"{other.last_name} {other.first_name}" if other else ""
                kind = witness.get("type") or ""
                witnesses.append(f"wit {kind}: {label}".replace(" :", ":").strip())

            pevts.append(
                PEVTRaw(
                    person_name=person.first_name.replace("_", " "),
                    person_surname=person.last_name,
                    event_tag=event.event_type_raw,
                    date=event.date.display_text if event.date else None,
                    place=event.place,
                    raw_text=_raw_line(event),
                    witnesses=witnesses,
                    notes=list(event.notes),
                    sources=[event.source] if event.source else [],
                )
            )
    return pevts


def _raw_line(event) -> str:
    """Ligne ``#tag date #p lieu`` reconstituée (le texte exact n'est pas conservé)"""
    parts = [f"#{event.event_type_raw}"]
    if event.date:
        parts.append(event.date.display_text)
    if event.place:
        parts.append(f"#p {event.place}")
    if event.source:
        parts.append(f"#s {event.source}")
    return " ".join(parts)
