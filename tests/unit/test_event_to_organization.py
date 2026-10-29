"""Déduction d'organisations depuis les événements personnalisés (#strng).

Fixtures 100 % synthétiques.
"""

from geneweb_py.core.event_to_organization import (
    EventContext,
    EventToOrganizationMapper,
    OrganizationProposal,
)
from geneweb_py.core.organization import OrganizationType
from geneweb_py.core.parser.gw_parser import GeneWebParser


def _parse(pevt_body: str):
    text = f"encoding: utf-8\ngwplus\n\npevt DUPONT Jean\n{pevt_body}\nend pevt\n"
    parser = GeneWebParser()
    return parser.parse_string(text)


def _jean(genealogy):
    return next(p for p in genealogy.persons.values() if p.last_name == "DUPONT")


class TestDeterministicRules:
    def test_place_complement_becomes_organization(self):
        g = _parse("#Cours_peinture 1890 #p [Atelier_Rose]_-_Lyon")
        assert g.infer_organizations() == (1, 1)
        org = g.get_organization("atelier_rose_lyon")
        assert org.name == "Atelier Rose"
        assert org.place == "Lyon"
        link = g.get_organization_links(person_id=next(iter(g.persons)))[0]
        assert link.source_event_type == "Cours_peinture"
        assert link.start_date.sort_year() == 1890
        assert link.role == "Élève"

    def test_name_taken_from_tag_remainder(self):
        g = _parse("#Membre_Academie 1900")
        assert g.infer_organizations() == (1, 1)
        org = g.get_organization("academie")
        assert org.name == "Academie"
        assert org.type is OrganizationType.ASSOCIATION
        link = g.get_organization_links()[0]
        assert link.role == "Membre"

    def test_camel_case_tag_is_split_and_typed(self):
        g = _parse("#Eleve_BeauxArts 1885 #p Paris")
        g.infer_organizations()
        org = next(iter(g.organizations.values()))
        assert org.name == "Beaux Arts"
        assert org.type is OrganizationType.SCHOOL
        assert org.place == "Paris"
        assert g.get_organization_links()[0].role == "Élève"

    def test_tag_without_signal_is_ignored(self):
        g = _parse("#Action-Sociale 1905\n#Membre_1900")
        assert g.infer_organizations() == (0, 0)

    def test_standard_events_are_ignored(self):
        g = _parse("#educ 1890 #p [Lycee_Hugo]_-_Lyon")
        assert g.infer_organizations() == (0, 0)

    def test_same_organization_is_shared_between_events(self):
        g = _parse("#Membre_Academie 1900\n#Membre_Academie 1910")
        assert g.infer_organizations() == (1, 2)

    def test_inference_is_idempotent(self):
        g = _parse("#Membre_Academie 1900")
        assert g.infer_organizations() == (1, 1)
        assert g.infer_organizations() == (0, 0)
        assert len(g.organization_links) == 1

    def test_deterministic_result_is_flagged_by_confidence(self):
        g = _parse(
            "#Membre_Academie 1900\n#Cours_peinture 1890 #p [Atelier_Rose]_-_Lyon"
        )
        g.infer_organizations()
        assert g.get_organization("academie").needs_review is True
        assert g.get_organization("atelier_rose_lyon").needs_review is False
        assert 0 < g.get_organization("academie").confidence < 1


class _Recorder:
    """Hook LLM factice : enregistre les contextes et renvoie une réponse fixe."""

    def __init__(self, answer=None, error=None):
        self.answer = answer
        self.error = error
        self.contexts = []

    def __call__(self, context: EventContext):
        self.contexts.append(context)
        if self.error:
            raise self.error
        return self.answer


class TestLLMHook:
    def test_not_called_when_rules_are_confident(self):
        hook = _Recorder()
        g = _parse("#Cours_peinture 1890 #p [Atelier_Rose]_-_Lyon")
        g.infer_organizations(EventToOrganizationMapper(llm=hook))
        assert hook.contexts == []

    def test_called_for_ambiguous_event_and_enriches(self):
        hook = _Recorder(
            OrganizationProposal(
                name="Société Archéologique",
                type=OrganizationType.ASSOCIATION,
                role="Secrétaire",
                confidence=0.9,
            )
        )
        g = _parse("#Action-Sociale 1905\nnote Secrétaire de la Société Archéologique")
        assert g.infer_organizations(EventToOrganizationMapper(llm=hook)) == (1, 1)

        context = hook.contexts[0]
        assert context.event_type_raw == "Action-Sociale"
        assert context.notes == ["Secrétaire de la Société Archéologique"]
        assert context.heuristic is None

        org = next(iter(g.organizations.values()))
        assert org.name == "Société Archéologique"
        assert org.confidence == 0.9 and org.needs_review is False
        assert g.get_organization_links()[0].role == "Secrétaire"

    def test_hook_refines_low_confidence_heuristic(self):
        hook = _Recorder(
            OrganizationProposal(
                name="Académie de Lyon",
                type=OrganizationType.INSTITUTION,
                confidence=0.85,
            )
        )
        g = _parse("#Membre_Academie 1900")
        g.infer_organizations(EventToOrganizationMapper(llm=hook))
        assert hook.contexts[0].heuristic.name == "Academie"
        org = next(iter(g.organizations.values()))
        assert org.name == "Académie de Lyon"
        assert "Academie" in org.aliases
        assert g.get_organization_links()[0].role == "Membre"

    def test_hook_returning_none_keeps_heuristic_for_review(self):
        g = _parse("#Membre_Academie 1900")
        g.infer_organizations(EventToOrganizationMapper(llm=_Recorder(None)))
        assert g.get_organization("academie").needs_review is True

    def test_hook_error_does_not_break_inference(self):
        hook = _Recorder(error=RuntimeError("API indisponible"))
        g = _parse("#Membre_Academie 1900\n#Action-Sociale 1905\nnote Un texte")
        assert g.infer_organizations(EventToOrganizationMapper(llm=hook)) == (1, 1)
        assert g.get_organization("academie").needs_review is True
