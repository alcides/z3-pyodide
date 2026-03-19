"""Tests for SMT-LIB2 serialization."""

from z3_pyodide import Int, Ints, Bool, And, Or, Not, Implies, IntVal, BoolVal
from z3_pyodide._smtlib2 import collect_declarations


def test_int_variable_sexpr():
    x = Int("x")
    assert x.sexpr() == "x"


def test_int_literal_sexpr():
    v = IntVal(42)
    assert v.sexpr() == "42"


def test_negative_literal():
    v = IntVal(-5)
    assert v.sexpr() == "(- 5)"


def test_addition():
    x = Int("x")
    expr = x + 1
    assert expr.sexpr() == "(+ x 1)"


def test_subtraction():
    x = Int("x")
    expr = x - 1
    assert expr.sexpr() == "(- x 1)"


def test_multiplication():
    x = Int("x")
    expr = x * 2
    assert expr.sexpr() == "(* x 2)"


def test_equality():
    x, y = Ints("x y")
    expr = x == y
    assert expr.sexpr() == "(= x y)"


def test_inequality():
    x = Int("x")
    expr = x != 0
    assert expr.sexpr() == "(not (= x 0))"


def test_less_than():
    x = Int("x")
    expr = x < 10
    assert expr.sexpr() == "(< x 10)"


def test_greater_equal():
    x = Int("x")
    expr = x >= 0
    assert expr.sexpr() == "(>= x 0)"


def test_and():
    p, q = Bool("p"), Bool("q")
    expr = And(p, q)
    assert expr.sexpr() == "(and p q)"


def test_or():
    p, q = Bool("p"), Bool("q")
    expr = Or(p, q)
    assert expr.sexpr() == "(or p q)"


def test_not():
    p = Bool("p")
    expr = Not(p)
    assert expr.sexpr() == "(not p)"


def test_implies():
    p, q = Bool("p"), Bool("q")
    expr = Implies(p, q)
    assert expr.sexpr() == "(=> p q)"


def test_complex_expression():
    x, y = Ints("x y")
    expr = And(x + y == 10, x > 0, y > 0)
    assert "(and" in expr.sexpr()


def test_collect_declarations():
    x = Int("x")
    y = Int("y")
    expr = x + y == 10

    declared: set[str] = set()
    decls = collect_declarations(expr, declared)
    assert "(declare-const x Int)" in decls
    assert "(declare-const y Int)" in decls
    assert "x" in declared
    assert "y" in declared


def test_no_duplicate_declarations():
    x = Int("x")
    expr = x + x == 10

    declared: set[str] = set()
    decls = collect_declarations(expr, declared)
    # x should only be declared once
    assert decls.count("(declare-const x Int)") == 1


def test_literals_not_declared():
    x = Int("x")
    expr = x + 1 == 10

    declared: set[str] = set()
    decls = collect_declarations(expr, declared)
    # Only x should be declared, not the literals
    assert len(decls) == 1
    assert "(declare-const x Int)" in decls


def test_bool_literal_sexpr():
    t = BoolVal(True)
    f = BoolVal(False)
    assert t.sexpr() == "true"
    assert f.sexpr() == "false"


def test_negation():
    x = Int("x")
    expr = -x
    assert expr.sexpr() == "(- x)"
