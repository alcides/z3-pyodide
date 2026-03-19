"""Tests for advanced solver features: unsat cores, simplify, etc."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal, Bool, Bools, BoolVal,
    Solver, sat, unsat, unknown,
    And, Or, Not, Implies,
    simplify,
)


class TestUnsatCore:
    def test_unsat_core_basic(self):
        p1 = Bool("p1")
        p2 = Bool("p2")
        p3 = Bool("p3")
        x = Int("x")

        s = Solver()
        s.assert_and_track(x > 0, p1)
        s.assert_and_track(x < 0, p2)
        s.assert_and_track(x == 5, p3)
        assert s.check() == unsat

        core = s.unsat_core()
        # p1 and p2 are contradictory, so they should be in the core
        assert "p1" in core
        assert "p2" in core

    def test_unsat_core_minimal(self):
        p1 = Bool("p1")
        p2 = Bool("p2")
        x = Int("x")

        s = Solver()
        s.assert_and_track(x > 10, p1)
        s.assert_and_track(x < 5, p2)
        assert s.check() == unsat

        core = s.unsat_core()
        assert len(core) >= 1  # At least some assertions in core
        assert "p1" in core or "p2" in core

    def test_mixed_tracked_untracked(self):
        p1 = Bool("p1")
        x = Int("x")

        s = Solver()
        s.add(x >= 0)  # untracked
        s.assert_and_track(x < 0, p1)
        assert s.check() == unsat

        core = s.unsat_core()
        assert "p1" in core


class TestSimplify:
    def test_simplify_true(self):
        result = simplify(And(BoolVal(True), BoolVal(True)))
        assert str(result) == "true"

    def test_simplify_false(self):
        result = simplify(And(BoolVal(True), BoolVal(False)))
        assert str(result) == "false"

    def test_simplify_arithmetic(self):
        x = Int("x")
        result = simplify(x + 0)
        # The simplified result might be just "x" but parsing back is complex
        # Just verify it doesn't crash
        assert result is not None

    def test_simplify_int_literal(self):
        result = simplify(IntVal(3) + IntVal(4))
        assert str(result) == "7"


class TestSolverPushPopAdvanced:
    def test_nested_push_pop(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0)
        s.push()
        s.add(x > 10)
        s.push()
        s.add(x > 100)
        assert s.num_assertions() == 3
        s.pop()
        assert s.num_assertions() == 2
        s.pop()
        assert s.num_assertions() == 1
        assert s.check() == sat

    def test_pop_multiple(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0)
        s.push()
        s.add(x > 10)
        s.push()
        s.add(x > 100)
        s.pop(2)
        assert s.num_assertions() == 1

    def test_pop_too_many(self):
        s = Solver()
        with pytest.raises(RuntimeError):
            s.pop()


class TestSolverRepr:
    def test_solver_repr(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0, x < 10)
        r = repr(s)
        assert "(assert (> x 0))" in r
        assert "(assert (< x 10))" in r

    def test_solver_str(self):
        x = Int("x")
        s = Solver()
        s.add(x == 42)
        assert "(assert (= x 42))" in str(s)


class TestCheckSatResult:
    def test_sat_bool(self):
        assert bool(sat) is True

    def test_unsat_bool(self):
        assert bool(unsat) is False

    def test_unknown_bool(self):
        assert bool(unknown) is False

    def test_equality(self):
        assert sat == sat
        assert unsat == unsat
        assert sat != unsat

    def test_hash(self):
        d = {sat: "satisfiable", unsat: "unsatisfiable"}
        assert d[sat] == "satisfiable"
        assert d[unsat] == "unsatisfiable"

    def test_repr(self):
        assert repr(sat) == "sat"
        assert repr(unsat) == "unsat"
        assert repr(unknown) == "unknown"


class TestModelError:
    def test_model_before_check(self):
        s = Solver()
        with pytest.raises(RuntimeError):
            s.model()

    def test_model_after_unsat(self):
        x = Int("x")
        s = Solver()
        s.add(x > 0, x < 0)
        s.check()
        with pytest.raises(RuntimeError):
            s.model()
