"""Tests des types d'événements complets et du champ event_type_raw."""

from geneweb_py.core.event import EventType


class TestEventTypeRaw:
    def test_known_type_in_pevt(self):
        """Un type reconnu est mappé vers EventType."""
        content = "pevt DUPONT Jean\n#grad 1/6/1985 #p Paris\nend pevt\n"
        from geneweb_py.core.parser.gw_parser import GeneWebParser

        genealogy = GeneWebParser().parse_string(content)
        person = next(
            (p for p in genealogy.persons.values() if p.first_name == "Jean"), None
        )
        assert person is not None
        grad_events = [e for e in person.events if e.event_type == EventType.GRADUATION]
        assert len(grad_events) == 1
        assert grad_events[0].place == "Paris"

    def test_unknown_type_stored_in_raw(self):
        """Un type inconnu (#xyz) est stocké dans event_type_raw avec EventType.OTHER."""
        content = "pevt DUPONT Jean\n#xyz 1/1/2000\nend pevt\n"
        from geneweb_py.core.parser.gw_parser import GeneWebParser

        genealogy = GeneWebParser().parse_string(content)
        person = next(
            (p for p in genealogy.persons.values() if p.first_name == "Jean"), None
        )
        assert person is not None
        raw_events = [e for e in person.events if e.event_type == EventType.OTHER]
        assert len(raw_events) >= 1
        assert raw_events[0].event_type_raw == "xyz"

    def test_event_type_raw_none_for_known_type(self):
        """Pour un type connu, event_type_raw doit être None."""
        content = "pevt DUPONT Jean\n#grad 1/6/1985\nend pevt\n"
        from geneweb_py.core.parser.gw_parser import GeneWebParser

        genealogy = GeneWebParser().parse_string(content)
        person = next(
            (p for p in genealogy.persons.values() if p.first_name == "Jean"), None
        )
        assert person is not None
        grad_events = [e for e in person.events if e.event_type == EventType.GRADUATION]
        assert len(grad_events) == 1
        assert grad_events[0].event_type_raw is None


class TestEventTypeCompleteness:
    def test_all_pevt_types_exist(self):
        """Tous les types pevt de la spec GeneWeb existent dans EventType."""
        required = [
            "acco", "acqu", "adhe", "bapl", "barm", "basm", "bles", "cens",
            "chgn", "circ", "conl", "degr", "awar", "demm", "dist", "endl",
            "dotl", "elec", "emig", "flkl", "fune", "hosp", "illn", "immi",
            "lpas", "mdis", "mpro", "mobm", "prop", "reti", "slgc", "slgp",
            "slgs", "vteb", "will", "strng",
        ]
        existing_values = {e.value for e in EventType}
        missing = [r for r in required if r not in existing_values]
        assert missing == [], f"Types manquants dans EventType : {missing}"
