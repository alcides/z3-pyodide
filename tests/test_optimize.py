"""Tests for the Optimize class."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal, Real, Reals, RealVal,
    Optimize, sat, unsat,
    And, Or, Not,
)


class TestOptimizeBasic:
    def test_optimize_sat(self):
        x = Int("x")
        o = Optimize()
        o.add(x >= 0, x <= 10)
        assert o.check() == sat

    def test_optimize_unsat(self):
        x = Int("x")
        o = Optimize()
        o.add(x > 0, x < 0)
        assert o.check() == unsat

    def test_optimize_model(self):
        x = Int("x")
        o = Optimize()
        o.add(x >= 0, x <= 10)
        o.check()
        m = o.model()
        val = m[x].as_long()
        assert 0 <= val <= 10


class TestMinimize:
    def test_minimize_basic(self):
        x = Int("x")
        o = Optimize()
        o.add(x >= 5, x <= 100)
        o.minimize(x)
        assert o.check() == sat
        m = o.model()
        assert m[x].as_long() == 5

    def test_minimize_with_constraints(self):
        x, y = Ints("x y")
        o = Optimize()
        o.add(x + y >= 10)
        o.add(x >= 0, y >= 0)
        o.minimize(x + y)
        assert o.check() == sat
        m = o.model()
        assert m[x].as_long() + m[y].as_long() == 10


class TestMaximize:
    def test_maximize_basic(self):
        x = Int("x")
        o = Optimize()
        o.add(x >= 0, x <= 42)
        o.maximize(x)
        assert o.check() == sat
        m = o.model()
        assert m[x].as_long() == 42

    def test_maximize_with_constraints(self):
        x, y = Ints("x y")
        o = Optimize()
        o.add(x + y <= 20)
        o.add(x >= 0, y >= 0)
        o.maximize(x)
        assert o.check() == sat
        m = o.model()
        assert m[x].as_long() == 20

    def test_multiple_objectives(self):
        x, y = Ints("x y")
        o = Optimize()
        o.add(x >= 0, x <= 10)
        o.add(y >= 0, y <= 10)
        o.add(x + y == 10)
        o.maximize(x)
        o.minimize(y)
        assert o.check() == sat
        m = o.model()
        assert m[x].as_long() == 10
        assert m[y].as_long() == 0


class TestOptimizeSexpr:
    def test_sexpr(self):
        x = Int("x")
        o = Optimize()
        o.add(x >= 0)
        o.minimize(x)
        sexpr = o.sexpr()
        assert "(assert (>= x 0))" in sexpr
        assert "(minimize x)" in sexpr


class TestOptimizeObjective:
    def test_objective_repr(self):
        x = Int("x")
        o = Optimize()
        obj = o.minimize(x)
        assert "minimize" in repr(obj)
        assert "x" in repr(obj)
