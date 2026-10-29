"""Déduction d'organisations à partir des événements personnalisés (``#strng``).

Deux étages :

1. règles déterministes sur le tag (``Membre_Academie``, ``Eleve_BeauxArts``) et sur le
   lieu décomposé (``[Atelier_Rose]_-_Lyon`` -> organisation « Atelier Rose ») ;
2. hook optionnel (``LLMExtractorProtocol``) appelé seulement quand les règles sont
   absentes ou peu fiables (notes à exploiter, confiance basse).

Sans hook, seules les règles s'appliquent. Le module n'importe aucun client LLM.
"""

import re
import unicodedata
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple

from typing_extensions import Protocol

from .date import Date
from .event import Event, EventType
from .organization import Organization, OrganizationType

if TYPE_CHECKING:
    from .genealogy import Genealogy

# En dessous, une organisation est marquée ``needs_review`` et le hook est sollicité
REVIEW_THRESHOLD = 0.7

_CONF_COMPLEMENT_AND_ROLE = 0.8
_CONF_COMPLEMENT_ONLY = 0.7
_CONF_TAG_NAME = 0.5


@dataclass
class OrganizationProposal:
    """Organisation proposée pour un événement (règles ou hook)"""

    name: str
    type: OrganizationType = OrganizationType.OTHER
    role: Optional[str] = None
    place: Optional[str] = None
    confidence: float = _CONF_TAG_NAME
    # ``None`` : déduit de ``confidence`` (< REVIEW_THRESHOLD => à revoir)
    needs_review: Optional[bool] = None
    aliases: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def review_required(self) -> bool:
        if self.needs_review is not None:
            return self.needs_review
        return self.confidence < REVIEW_THRESHOLD


@dataclass
class EventContext:
    """Ce que le hook reçoit : l'événement et la proposition des règles (ou None)"""

    person_id: str
    event_type_raw: str
    date: Optional[str]
    place: Optional[str]
    notes: List[str]
    heuristic: Optional[OrganizationProposal]


class LLMExtractorProtocol(Protocol):
    """Hook d'enrichissement : renvoie une proposition, ou ``None`` si rien à dire"""

    def __call__(self, context: EventContext) -> Optional[OrganizationProposal]: ...


@dataclass(frozen=True)
class PrefixRule:
    """Règle d'un préfixe de tag : rôle déduit, type d'organisation"""

    role: str
    type: OrganizationType
    # Le reste du tag nomme l'organisation (``Membre_Academie``) ; faux pour
    # ``Cours_peinture`` où il désigne une matière
    remainder_is_name: bool = True


DEFAULT_PREFIX_RULES: Dict[str, PrefixRule] = {
    "membre": PrefixRule("Membre", OrganizationType.ASSOCIATION),
    "eleve": PrefixRule("Élève", OrganizationType.SCHOOL),
    "cours": PrefixRule("Élève", OrganizationType.SCHOOL, remainder_is_name=False),
    "professeur": PrefixRule("Professeur", OrganizationType.SCHOOL),
    "employe": PrefixRule("Employé", OrganizationType.COMPANY),
    "ouvrier": PrefixRule("Ouvrier", OrganizationType.COMPANY),
    "directeur": PrefixRule("Directeur", OrganizationType.OTHER),
    "soldat": PrefixRule("Soldat", OrganizationType.MILITARY),
    "officier": PrefixRule("Officier", OrganizationType.MILITARY),
    "pretre": PrefixRule("Prêtre", OrganizationType.RELIGIOUS),
}


def _fold(text: str) -> str:
    stripped = unicodedata.normalize("NFKD", text).encode("ascii", "ignore")
    return stripped.decode("ascii").lower()


def _split_tag(
    tag: str, rules: Dict[str, PrefixRule]
) -> Tuple[Optional[PrefixRule], Optional[str]]:
    """Sépare un tag en (règle de rôle, nom d'organisation candidat)."""
    parts = [p for p in re.split(r"[_-]+", tag) if p]
    if not parts:
        return None, None
    rule = rules.get(_fold(parts[0]))
    remainder_parts = parts[1:] if rule else []
    if rule is not None and not rule.remainder_is_name:
        return rule, None
    words: List[str] = []
    for part in remainder_parts:
        if part.isdigit():
            continue
        words.extend(re.sub(r"(?<=[a-z])(?=[A-Z])", " ", part).split())
    return rule, (" ".join(words) or None)


class EventToOrganizationMapper:
    """Convertit les événements personnalisés d'une généalogie en organisations."""

    def __init__(
        self,
        llm: Optional[LLMExtractorProtocol] = None,
        custom_rules: Optional[Dict[str, PrefixRule]] = None,
    ) -> None:
        """
        Args:
            llm: hook d'enrichissement optionnel (étage 2).
            custom_rules: règles de préfixe ajoutées à ``DEFAULT_PREFIX_RULES`` ou les
                remplaçant ; clés insensibles à la casse et aux accents.
        """
        self.llm = llm
        self.rules: Dict[str, PrefixRule] = dict(DEFAULT_PREFIX_RULES)
        for prefix, rule in (custom_rules or {}).items():
            self.rules[_fold(prefix)] = rule

    # -- Étage 1 : règles ---------------------------------------------------
    def propose(self, event: Event) -> Optional[OrganizationProposal]:
        """Proposition déterministe pour un événement, ``None`` sans signal."""
        tag = event.event_type_raw
        if event.event_type is not EventType.OTHER or not tag:
            return None

        rule, tag_name = _split_tag(tag, self.rules)
        parts = event.place_parts
        complement = parts.complement if parts else None
        city = parts.name if parts else None

        if complement:
            confidence = _CONF_COMPLEMENT_AND_ROLE if rule else _CONF_COMPLEMENT_ONLY
            name = complement
        elif tag_name:
            confidence, name = _CONF_TAG_NAME, tag_name
        else:
            return None

        return OrganizationProposal(
            name=name,
            type=rule.type if rule else OrganizationType.OTHER,
            role=rule.role if rule else None,
            place=city,
            confidence=confidence,
        )

    # -- Étage 2 : hook -----------------------------------------------------
    def _refine(
        self,
        person_id: str,
        event: Event,
        heuristic: Optional[OrganizationProposal],
    ) -> Optional[OrganizationProposal]:
        if self.llm is None:
            return heuristic
        uncertain = (heuristic is None and bool(event.notes)) or (
            heuristic is not None and heuristic.confidence < REVIEW_THRESHOLD
        )
        if not uncertain:
            return heuristic

        context = EventContext(
            person_id=person_id,
            event_type_raw=event.event_type_raw or "",
            date=event.date.display_text if event.date else None,
            place=event.place,
            notes=list(event.notes),
            heuristic=heuristic,
        )
        try:
            answer = self.llm(context)
        except Exception:  # un hook défaillant ne doit pas casser l'inférence
            return heuristic
        if answer is None:
            return heuristic
        if heuristic is None:
            return answer

        merged = replace(
            answer,
            role=answer.role or heuristic.role,
            place=answer.place or heuristic.place,
            aliases=list(answer.aliases),
        )
        if merged.name != heuristic.name and heuristic.name not in merged.aliases:
            merged.aliases.append(heuristic.name)
        return merged

    # -- Application à une généalogie --------------------------------------
    def apply(self, genealogy: "Genealogy") -> Tuple[int, int]:
        """Ajoute organisations et liens.

        Returns:
            (organisations créées, liens créés)
        """
        created_orgs = 0
        created_links = 0
        seen: Set[Tuple[str, str, Optional[str], Optional[str], Optional[str]]] = {
            (
                link.person_id,
                link.organization_id,
                link.source_event_type,
                link.role,
                link.start_date.display_text if link.start_date else None,
            )
            for link in genealogy.organization_links
        }

        for person_id, person in genealogy.persons.items():
            for event in person.events:
                proposal = self._refine(person_id, event, self.propose(event))
                if proposal is None:
                    continue

                org = Organization.create(proposal.name, place=proposal.place)
                if org.id not in genealogy.organizations:
                    org.type = proposal.type
                    org.aliases = list(proposal.aliases)
                    org.notes = list(proposal.notes)
                    org.confidence = proposal.confidence
                    org.needs_review = proposal.review_required
                    genealogy.add_organization(org)
                    created_orgs += 1

                start: Optional[Date] = event.date
                key = (
                    person_id,
                    org.id,
                    event.event_type_raw,
                    proposal.role,
                    start.display_text if start else None,
                )
                if key in seen:
                    continue
                seen.add(key)
                genealogy.link_person_to_organization(
                    person_id,
                    org.id,
                    role=proposal.role,
                    start_date=start,
                    source_event_type=event.event_type_raw,
                )
                created_links += 1
        return created_orgs, created_links
