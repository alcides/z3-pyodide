"""Basic integration tests: end-to-end solving with subprocess backend."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal, Bool, Bools, BoolVal,
    And, Or, Not, Implies, Distinct, If,
    Solver, sat, unsat, unknown,
    is_int, is_bool,
)


class TestBasicSolving:
    def test_simple_sat(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0)
        assert s.check() == sat

    def test_simple_unsat(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0, x < 0)
        assert s.check() == unsat

    def test_two_variables(self):
        x, y = Ints("x y")
        s = Solver()
        s.add(x + y == 10, x > 0, y > 0)
        assert s.check() == sat
        m = s.model()
        x_val = m[x]
        y_val = m[y]
        assert x_val.as_long() + y_val.as_long() == 10
        assert x_val.as_long() > 0
        assert y_val.as_long() > 0

    def test_equality(self):
        x = Int("x")
        s = Solver()
        s.add(x == 42)
        assert s.check() == sat
        m = s.model()
        assert m[x].as_long() == 42

    def test_distinct(self):
        x, y, z = Ints("x y z")
        s = Solver()
        s.add(Distinct(x, y, z))
        s.add(x >= 1, x <= 3)
        s.add(y >= 1, y <= 3)
        s.add(z >= 1, z <= 3)
        assert s.check() == sat
        m = s.model()
        vals = {m[x].as_long(), m[y].as_long(), m[z].as_long()}
        assert vals == {1, 2, 3}


class TestBooleans:
    def test_bool_sat(self):
        p = Bool("p")
        s = Solver()
        s.add(p)
        assert s.check() == sat

    def test_bool_and(self):
        p, q = Bools("p q")
        s = Solver()
        s.add(And(p, q))
        assert s.check() == sat
        m = s.model()
        assert str(m[p]) == "true"
        assert str(m[q]) == "true"

    def test_bool_contradiction(self):
        p = Bool("p")
        s = Solver()
        s.add(p, Not(p))
        assert s.check() == unsat

    def test_implies(self):
        p, q = Bools("p q")
        s = Solver()
        s.add(Implies(p, q))
        s.add(p)
        assert s.check() == sat
        m = s.model()
        assert str(m[q]) == "true"


class TestSolverFeatures:
    def test_push_pop(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0)
        s.push()
        s.add(x < 0)
        assert s.check() == unsat
        s.pop()
        assert s.check() == sat

    def test_reset(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0, x < 0)
        assert s.check() == unsat
        s.reset()
        s.add(x > 0)
        assert s.check() == sat

    def test_num_assertions(self):
        x = Int("x")
        s = Solver()
        assert s.num_assertions() == 0
        s.add(x > 0)
        assert s.num_assertions() == 1
        s.add(x < 10)
        assert s.num_assertions() == 2

    def test_sexpr(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0)
        sexpr = s.sexpr()
        assert "(declare-const x Int)" in sexpr
        assert "(assert (> x 0))" in sexpr


class TestArithmetic:
    def test_addition(self):
        x, y = Ints("x y")
        s = Solver()
        s.add(x == 3, y == 7, x + y == 10)
        assert s.check() == sat

    def test_subtraction(self):
        x = Int("x")
        s = Solver()
        s.add(x - 5 == 3)
        assert s.check() == sat
        assert s.model()[x].as_long() == 8

    def test_multiplication(self):
        x = Int("x")
        s = Solver()
        s.add(x * 3 == 12)
        assert s.check() == sat
        assert s.model()[x].as_long() == 4

    def test_modulo(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0, x < 10, x % 3 == 0)
        assert s.check() == sat
        assert s.model()[x].as_long() % 3 == 0

    def test_negation(self):
        x = Int("x")
        s = Solver()
        s.add(-x == 5)
        assert s.check() == sat
        assert s.model()[x].as_long() == -5

    def test_chained_comparisons(self):
        x = Int("x")
        s = Solver()
        s.add(x >= 0, x <= 10, x > 5, x < 8)
        assert s.check() == sat
        val = s.model()[x].as_long()
        assert 5 < val < 8


class TestIf:
    def test_if_then_else(self):
        x = Int("x")
        y = Int("y")
        s = Solver()
        s.add(x == 5)
        s.add(y == If(x > 3, x + 1, x - 1))
        assert s.check() == sat
        assert s.model()[y].as_long() == 6


class TestTypeChecking:
    def test_is_int(self):
        x = Int("x")
        assert is_int(x)
        assert not is_bool(x)

    def test_is_bool(self):
        p = Bool("p")
        assert is_bool(p)
        assert not is_int(p)


class TestModelAccess:
    def test_model_getitem(self):
        x = Int("x")
        s = Solver()
        s.add(x == 42)
        s.check()
        m = s.model()
        assert m[x].as_long() == 42

    def test_model_contains(self):
        x = Int("x")
        y = Int("y")
        s = Solver()
        s.add(x == 42)
        s.check()
        m = s.model()
        assert x in m

    def test_model_decls(self):
        x, y = Ints("x y")
        s = Solver()
        s.add(x == 1, y == 2)
        s.check()
        m = s.model()
        assert "x" in m.decls()
        assert "y" in m.decls()

    def test_model_repr(self):
        x = Int("x")
        s = Solver()
        s.add(x == 42)
        s.check()
        m = s.model()
        assert "x = 42" in repr(m)
