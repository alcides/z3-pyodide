"""Tests for Array theory."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal, Real,
    Array, Select, Store, K,
    Solver, sat, unsat,
    And, Not, ForAll, Distinct,
    IntSort, RealSort, BoolSort, ArraySort,
    is_array,
)


class TestArrayBasic:
    def test_create_array(self):
        a = Array("a", IntSort(), IntSort())
        assert is_array(a)
        assert a.sexpr() == "a"

    def test_array_sort(self):
        a = Array("a", IntSort(), IntSort())
        s = a.sort()
        assert isinstance(s, type(ArraySort(IntSort(), IntSort())))

    def test_select_sexpr(self):
        a = Array("a", IntSort(), IntSort())
        expr = a[0]
        assert expr.sexpr() == "(select a 0)"

    def test_select_function(self):
        a = Array("a", IntSort(), IntSort())
        expr = Select(a, 0)
        assert expr.sexpr() == "(select a 0)"

    def test_store_sexpr(self):
        a = Array("a", IntSort(), IntSort())
        expr = Store(a, 0, 42)
        assert expr.sexpr() == "(store a 0 42)"

    def test_store_method(self):
        a = Array("a", IntSort(), IntSort())
        expr = a.store(0, 42)
        assert expr.sexpr() == "(store a 0 42)"


class TestArraySolving:
    def test_array_select(self):
        a = Array("a", IntSort(), IntSort())
        s = Solver()
        s.add(a[0] == 42)
        assert s.check() == sat

    def test_array_store_select(self):
        a = Array("a", IntSort(), IntSort())
        s = Solver()
        b = Store(a, 0, 42)
        s.add(Select(b, 0) == 42)
        assert s.check() == sat

    def test_array_store_other_index(self):
        """Store at index 0, read at index 1 — should be unconstrained."""
        a = Array("a", IntSort(), IntSort())
        s = Solver()
        b = Store(a, 0, 42)
        s.add(Select(b, 1) == 99)
        assert s.check() == sat

    def test_array_axiom(self):
        """Store then select at same index returns stored value."""
        a = Array("a", IntSort(), IntSort())
        i = Int("i")
        v = Int("v")
        s = Solver()
        b = Store(a, i, v)
        s.add(Select(b, i) != v)
        assert s.check() == unsat

    def test_array_extensionality(self):
        """Two arrays that differ at some index are not equal."""
        a = Array("a", IntSort(), IntSort())
        b = Array("b", IntSort(), IntSort())
        i = Int("i")
        s = Solver()
        s.add(a == b)
        s.add(Select(a, i) != Select(b, i))
        assert s.check() == unsat

    def test_array_with_variable_index(self):
        a = Array("a", IntSort(), IntSort())
        i, j = Ints("i j")
        s = Solver()
        s.add(Store(a, i, 10)[j] == 10)
        s.add(i == j)
        assert s.check() == sat

    def test_multiple_stores(self):
        a = Array("a", IntSort(), IntSort())
        b = Store(Store(a, 0, 10), 1, 20)
        s = Solver()
        s.add(Select(b, 0) == 10)
        s.add(Select(b, 1) == 20)
        assert s.check() == sat


class TestConstantArray:
    def test_constant_array_sexpr(self):
        a = K(IntSort(), 0)
        # Should produce ((as const (Array Int Int)) 0)
        assert "as const" in a.sexpr()

    def test_constant_array_solving(self):
        a = K(IntSort(), 0)
        i = Int("i")
        s = Solver()
        s.add(Select(a, i) == 0)
        assert s.check() == sat

    def test_constant_array_nonzero(self):
        a = K(IntSort(), 42)
        i = Int("i")
        s = Solver()
        s.add(Select(a, i) == 42)
        assert s.check() == sat


class TestArrayTypes:
    def test_int_to_bool_array(self):
        """Array from Int to Bool."""
        a = Array("a", IntSort(), BoolSort())
        s = Solver()
        s.add(a[0])
        s.add(Not(a[1]))
        assert s.check() == sat

    def test_nested_select_type(self):
        """Select from Int->Int array returns ArithRef."""
        a = Array("a", IntSort(), IntSort())
        expr = a[0]
        from z3_pyodide import is_int
        assert is_int(expr)


class TestArrayForAll:
    def test_forall_array(self):
        """All elements of array are positive."""
        a = Array("a", IntSort(), IntSort())
        i = Int("i")
        s = Solver()
        s.add(ForAll(i, a[i] > 0))
        s.add(a[5] < 0)
        assert s.check() == unsat
