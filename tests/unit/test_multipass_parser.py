"""Tests du parser multi-passes et de l'intégration ``use_multipass``."""

import pytest

from geneweb_py import GeneWebParser, MultiPassParser
from geneweb_py.core.parser.lexical import LexicalParser
from geneweb_py.core.parser.syntax import SyntaxParser


def test_multiparse_requires_gene_web_parser() -> None:
    """``MultiPassParser.parse_syntax_nodes`` exige un parser principal."""
    mp = MultiPassParser(content="")
    with pytest.raises(ValueError, match="gene_web_parser"):
        mp.parse_syntax_nodes([])


def test_use_multipass_builds_genealogy() -> None:
    """Le drapeau ``use_multipass`` produit une généalogie cohérente."""
    content = """fam Dupont Jean + Martin Marie
beg
- h Dupont Paul
end
"""
    parser = GeneWebParser(validate=False, use_multipass=True)
    g = parser.parse_string(content)
    assert len(g.families) >= 1
    assert len(g.persons) >= 3


def test_multipass_consistent_counts_with_standard_mode() -> None:
    """Les effectifs restent alignés avec le mode incrémental standard."""
    content = """fam A Alpha + B Beta
beg
- h A Child1
end
fam C Gamma + D Delta
beg
- f C Child2
end
"""
    p_std = GeneWebParser(validate=False, use_multipass=False)
    p_mp = GeneWebParser(validate=False, use_multipass=True)
    g_std = p_std.parse_string(content)
    g_mp = p_mp.parse_string(content)
    assert len(g_std.persons) == len(g_mp.persons)
    assert len(g_std.families) == len(g_mp.families)


def test_multipass_parser_public_api() -> None:
    """``MultiPassParser`` peut être piloté via lexique + syntaxe (API avancée)."""
    content = "fam X Foo + Y Bar\n"
    lex = LexicalParser(content, None)
    tokens = lex.tokenize()
    nodes = SyntaxParser().parse(tokens)
    main = GeneWebParser(validate=False)
    main.lexical_parser = lex
    main.syntax_nodes = nodes
    mp = MultiPassParser(content=content, gene_web_parser=main)
    g = mp.parse_syntax_nodes(nodes)
    assert len(g.persons) == 2
    assert len(g.families) == 1
