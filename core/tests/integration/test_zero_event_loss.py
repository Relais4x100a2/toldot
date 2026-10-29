"""« Zéro événement perdu » : le moteur nominal doit couvrir l'oracle regex brut."""

from pathlib import Path

from geneweb_py.core.parser.gw_parser import GeneWebParser
from geneweb_py.core.parser.lexical import TokenType
from tests.helpers.gw_oracle import RegexPersonExtractor, compare_extraction_methods

FIXTURE = Path(__file__).parent.parent / "fixtures" / "rich_pevt_wit.gw"


def test_nominal_engine_covers_oracle_counts():
    stats = compare_extraction_methods(str(FIXTURE))
    assert stats["witnesses_tokens"] >= stats["witnesses_regex"] > 0
    assert stats["pevt_nodes"] >= stats["pevt_regex"] > 0


def test_every_pevt_event_line_becomes_an_event():
    content = FIXTURE.read_text(encoding="utf-8")
    expected = RegexPersonExtractor().count_pevt_event_lines(content)

    genealogy = GeneWebParser().parse_file(str(FIXTURE))
    parsed = sum(
        len(p.events) for p in genealogy.persons.values() if p.last_name != "_fevt_skip"
    )
    assert expected == 11
    assert parsed >= expected


def test_every_witness_line_is_a_witness_token():
    content = FIXTURE.read_text(encoding="utf-8")
    parser = GeneWebParser()
    parser.parse_file(str(FIXTURE))
    wit_tokens = sum(1 for t in parser.tokens if t.type == TokenType.WIT)
    assert wit_tokens >= len(RegexPersonExtractor().extract_all_witnesses(content))
