"""S-expression parser for Z3 output."""

from __future__ import annotations


def parse_sexpr(s: str) -> list | str:
    """Parse an S-expression string into nested Python lists and strings.

    Examples:
        "42" -> "42"
        "(+ x 1)" -> ["+", "x", "1"]
        "(model (define-fun x () Int 42))" ->
            ["model", ["define-fun", "x", [], "Int", "42"]]
    """
    tokens = _tokenize(s)
    if not tokens:
        return []
    result, _ = _parse_tokens(tokens, 0)
    return result


def parse_sexprs(s: str) -> list:
    """Parse multiple S-expressions from a string."""
    tokens = _tokenize(s)
    results = []
    pos = 0
    while pos < len(tokens):
        result, pos = _parse_tokens(tokens, pos)
        results.append(result)
    return results


def _tokenize(s: str) -> list[str]:
    """Tokenize an S-expression string."""
    tokens: list[str] = []
    i = 0
    n = len(s)
    while i < n:
        c = s[i]
        if c.isspace():
            i += 1
        elif c == '(':
            tokens.append('(')
            i += 1
        elif c == ')':
            tokens.append(')')
            i += 1
        elif c == '"':
            # Quoted string
            j = i + 1
            while j < n and s[j] != '"':
                if s[j] == '\\':
                    j += 1  # skip escaped char
                j += 1
            tokens.append(s[i:j + 1])
            i = j + 1
        elif c == '|':
            # Quoted symbol
            j = i + 1
            while j < n and s[j] != '|':
                j += 1
            tokens.append(s[i:j + 1])
            i = j + 1
        elif c == ';':
            # Comment - skip to end of line
            while i < n and s[i] != '\n':
                i += 1
        else:
            # Atom (symbol, numeral, etc.)
            j = i
            while j < n and s[j] not in '() \t\n\r;':
                j += 1
            tokens.append(s[i:j])
            i = j
    return tokens


def _parse_tokens(tokens: list[str], pos: int) -> tuple[list | str, int]:
    """Parse tokens starting at pos. Returns (result, new_pos)."""
    if pos >= len(tokens):
        return [], pos

    token = tokens[pos]

    if token == '(':
        # Parse a list
        items: list = []
        pos += 1
        while pos < len(tokens) and tokens[pos] != ')':
            item, pos = _parse_tokens(tokens, pos)
            items.append(item)
        if pos < len(tokens):
            pos += 1  # skip closing ')'
        return items, pos
    else:
        # Atom
        return token, pos + 1
