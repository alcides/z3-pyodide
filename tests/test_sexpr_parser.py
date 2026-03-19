"""Tests for the S-expression parser."""

from z3_pyodide._sexpr_parser import parse_sexpr, parse_sexprs


def test_parse_atom():
    assert parse_sexpr("42") == "42"
    assert parse_sexpr("hello") == "hello"


def test_parse_simple_list():
    assert parse_sexpr("(+ x 1)") == ["+", "x", "1"]


def test_parse_nested():
    result = parse_sexpr("(assert (= (+ x y) 10))")
    assert result == ["assert", ["=", ["+", "x", "y"], "10"]]


def test_parse_model():
    text = """(model
  (define-fun x () Int 42)
  (define-fun y () Int 5)
)"""
    result = parse_sexpr(text)
    assert result[0] == "model"
    assert result[1] == ["define-fun", "x", [], "Int", "42"]
    assert result[2] == ["define-fun", "y", [], "Int", "5"]


def test_parse_negative():
    result = parse_sexpr("(- 5)")
    assert result == ["-", "5"]


def test_parse_rational():
    result = parse_sexpr("(/ 1 3)")
    assert result == ["/", "1", "3"]


def test_parse_empty_list():
    assert parse_sexpr("()") == []


def test_parse_bool_values():
    assert parse_sexpr("true") == "true"
    assert parse_sexpr("false") == "false"


def test_parse_multiple():
    results = parse_sexprs("sat\n(model\n  (define-fun x () Int 1)\n)")
    assert results[0] == "sat"
    assert results[1][0] == "model"


def test_parse_quoted_string():
    result = parse_sexpr('(error "some error message")')
    assert result == ["error", '"some error message"']


def test_parse_quoted_symbol():
    result = parse_sexpr("(|foo bar|)")
    assert result == ["|foo bar|"]
