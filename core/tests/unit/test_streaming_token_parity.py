"""Le lexeur streaming doit produire les mêmes jetons que le lexeur complet."""

from pathlib import Path

import pytest

from geneweb_py.core.parser.lexical import LexicalParser, TokenType
from geneweb_py.core.parser.streaming import StreamingGeneWebParser

FIXTURES = sorted((Path(__file__).parent.parent / "fixtures").glob("*.gw"))


def _significant(tokens):
    return [
        (t.type.name, t.value, t.line_number)
        for t in tokens
        if t.type not in (TokenType.EOF,)
    ]


@pytest.mark.parametrize("path", FIXTURES, ids=lambda p: p.name)
def test_streaming_tokens_match_full_lexer(path):
    parser = StreamingGeneWebParser(validate=False)
    text = path.read_text(encoding=parser._detect_encoding(path))
    full = LexicalParser(text).tokenize()
    streamed = list(parser.parse_file_streaming(path))
    assert _significant(streamed) == _significant(full)
