"""Tests du parser wikitext GeneWeb."""

from geneweb_py.core.parser.wikitext import (
    NoteContent,
    WikitextParser,
)


class TestPersonLinks:
    def test_full_person_link(self):
        raw = "Voir [[Jean/Dupont/0/Jean Dupont]] pour plus."
        note = WikitextParser().parse(raw)
        assert len(note.person_links) == 1
        link = note.person_links[0]
        assert link.first_name == "Jean"
        assert link.last_name == "Dupont"
        assert link.occurrence == 0
        assert link.display_text == "Jean Dupont"

    def test_person_link_no_occurrence(self):
        """[[Jean/Dupont]] sans occurrence ni texte."""
        note = WikitextParser().parse("[[Jean/Dupont]]")
        assert len(note.person_links) == 1
        assert note.person_links[0].occurrence == 0

    def test_person_link_empty_occurrence(self):
        """[[Jean/Dupont//Jean]] avec occurrence vide."""
        note = WikitextParser().parse("[[Jean/Dupont//Jean]]")
        assert len(note.person_links) == 1
        assert note.person_links[0].occurrence == 0  # int("" or "0") == 0

    def test_raw_preserved(self):
        raw = "Texte avec [[Jean/Dupont/0/JD]]."
        note = WikitextParser().parse(raw)
        assert note.raw == raw


class TestPageLinks:
    def test_page_link_with_text(self):
        note = WikitextParser().parse("[[[arbre_corno/Arbre Corno]]]")
        assert len(note.page_links) == 1
        assert note.page_links[0].page_name == "arbre_corno"
        assert note.page_links[0].display_text == "Arbre Corno"

    def test_page_link_no_text(self):
        note = WikitextParser().parse("[[[ma_page]]]")
        assert len(note.page_links) == 1
        assert note.page_links[0].page_name == "ma_page"

    def test_page_link_not_matched_as_person(self):
        """Triple crochet ne doit pas générer de PersonLink."""
        note = WikitextParser().parse("[[[arbre]]]")
        assert len(note.person_links) == 0


class TestWizardLinks:
    def test_wizard_link(self):
        note = WikitextParser().parse("[[w:Admin/Administrateur]]")
        assert len(note.wizard_links) == 1
        assert note.wizard_links[0].wizard_name == "Admin"
        assert note.wizard_links[0].display_text == "Administrateur"

    def test_wizard_link_no_display(self):
        note = WikitextParser().parse("[[w:Admin]]")
        assert len(note.wizard_links) == 1
        assert note.wizard_links[0].wizard_name == "Admin"


class TestFicheTags:
    def test_head_tag(self):
        note = WikitextParser().parse("HEAD=Généalogie Dupont\nTexte libre.")
        assert note.fiche_tags.head == "Généalogie Dupont"

    def test_multiple_tags(self):
        note = WikitextParser().parse("HEAD=Famille\nOCCU=Avocat\nBIBLIO=Sources")
        assert note.fiche_tags.head == "Famille"
        assert note.fiche_tags.occu == "Avocat"
        assert note.fiche_tags.biblio == "Sources"

    def test_duplicate_tag_last_write_wins(self):
        note = WikitextParser().parse("HEAD=Premier\nHEAD=Dernier")
        assert note.fiche_tags.head == "Dernier"

    def test_no_tags(self):
        note = WikitextParser().parse("Texte sans balises.")
        assert note.fiche_tags.head is None


class TestMixedContent:
    def test_no_false_positives_with_triple_bracket(self):
        """[[[page]]] ne génère pas de PersonLink."""
        note = WikitextParser().parse("[[[page]]] et [[Jean/Dupont/0/JD]]")
        assert len(note.page_links) == 1
        assert len(note.person_links) == 1
        assert len(note.wizard_links) == 0


class TestPersonGetNotesStructured:
    def test_returns_list_of_note_content(self):
        from geneweb_py.core.person import Gender, Person

        p = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        p.add_note("Voir [[Jean/Martin/0/Jean Martin]]")
        p.add_note("Texte libre.")

        structured = p.get_notes_structured()
        assert len(structured) == 2
        assert isinstance(structured[0], NoteContent)
        assert len(structured[0].person_links) == 1
        assert structured[0].person_links[0].last_name == "Martin"

    def test_coherent_after_direct_append(self):
        """Appel direct à notes.append() reste cohérent via get_notes_structured."""
        from geneweb_py.core.person import Gender, Person

        p = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        p.notes.append("Note directe [[A/B/0/AB]]")  # bypass add_note
        structured = p.get_notes_structured()
        assert len(structured) == 1
        assert structured[0].person_links[0].first_name == "A"

    def test_empty_notes(self):
        from geneweb_py.core.person import Gender, Person

        p = Person(last_name="DUPONT", first_name="Jean", gender=Gender.MALE)
        assert p.get_notes_structured() == []
