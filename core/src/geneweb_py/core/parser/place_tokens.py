"""Lecture des jetons d'un lieu GeneWeb, crochets compris (``[complément]_-_lieu``)."""

from typing import List

from .lexical import Token, TokenType


def join_tokens_text(tokens: List[Token], par_ligne: bool = False) -> str:
    """Recolle des jetons en un texte, avec un espace là où la source en avait un.

    Un espace est inséré quand deux jetons ne sont pas contigus (positions) ; les
    chaînes collées (URL, ``f°42v``, ``[a]_-_b``) restent donc intactes. Avec
    ``par_ligne``, un changement de ligne source donne un retour à la ligne.
    """
    parts: List[str] = []
    prev_end = -1
    prev_line = None
    for tok in tokens:
        if parts and par_ligne and tok.line_number != prev_line:
            parts.append("\n")
        elif parts and tok.position != prev_end:
            parts.append(" ")
        prev_line = tok.line_number
        parts.append(tok.value)
        prev_end = tok.position + len(tok.value)
    return "".join(parts)


def place_run_end(tokens: List[Token], start: int) -> int:
    """Index après le lieu qui commence à ``start`` (``start`` si ce n'en est pas un).

    Un lieu est un identifiant ou un groupe ``[…]``, suivi d'identifiants collés
    et de segments séparés par des virgules (``Ville,_Code,_Pays``).
    """
    n = len(tokens)
    j = start
    if j < n and tokens[j].type == TokenType.BRACKET_OPEN:
        j += 1
        while j < n and tokens[j].type not in (
            TokenType.BRACKET_CLOSE,
            TokenType.NEWLINE,
            TokenType.EOF,
        ):
            j += 1
        if j >= n or tokens[j].type != TokenType.BRACKET_CLOSE:
            return start
        j += 1
    elif j < n and tokens[j].type == TokenType.IDENTIFIER:
        j += 1
    else:
        return start
    while j < n:
        tok = tokens[j]
        collé = tok.position == tokens[j - 1].position + len(tokens[j - 1].value)
        if tok.type == TokenType.IDENTIFIER and collé:
            j += 1
        elif (
            tok.type == TokenType.UNKNOWN
            and tok.value == ","
            and j + 1 < n
            and tokens[j + 1].type == TokenType.IDENTIFIER
        ):
            j += 2
        else:
            break
    return j


def texte_libre(tokens: List[Token], limite: int) -> str:
    """Texte d'une note : les ``limite`` premiers jetons utiles, à l'identique."""
    utiles = [
        t for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.WHITESPACE)
    ]
    return join_tokens_text(utiles[:limite], par_ligne=True)
