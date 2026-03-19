"""Tests for Real arithmetic, conversions, and extended arithmetic operations."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal, Real, Reals, RealVal,
    Solver, sat, unsat,
    And, Or, Not, If, Distinct,
    ToReal, ToInt, IsInt, Abs,
    is_real, is_int,
    Sum, Product,
)


class TestRealBasic:
    def test_real_variable(self):
        x = Real("x")
        assert is_real(x)
        assert x.sexpr() == "x"

    def test_real_val(self):
        v = RealVal(3)
        assert v.as_string() == "3"

    def test_real_fraction_val(self):
        v = RealVal("1/3")
        assert v.numerator_as_long() == 1
        assert v.denominator_as_long() == 3

    def test_reals_constructor(self):
        x, y, z = Reals("x y z")
        assert is_real(x)
        assert is_real(y)
        assert is_real(z)


class TestRealSolving:
    def test_real_sat(self):
        x = Real("x")
        s = Solver()
        s.add(x > 0, x < 1)
        assert s.check() == sat

    def test_real_equality(self):
        x = Real("x")
        s = Solver()
        s.add(x == RealVal("1/3"))
        assert s.check() == sat
        m = s.model()
        val = m[x]
        assert val.numerator_as_long() == 1
        assert val.denominator_as_long() == 3

    def test_real_arithmetic(self):
        x, y = Reals("x y")
        s = Solver()
        s.add(x + y == RealVal(10))
        s.add(x - y == RealVal(4))
        assert s.check() == sat
        m = s.model()
        # x = 7, y = 3
        assert m[x].numerator_as_long() == 7
        assert m[y].numerator_as_long() == 3

    def test_real_division(self):
        x = Real("x")
        s = Solver()
        s.add(x * 3 == 1)
        assert s.check() == sat
        m = s.model()
        val = m[x]
        assert val.as_fraction() == pytest.approx(1 / 3)

    def test_real_mixed_with_int_literal(self):
        x = Real("x")
        s = Solver()
        s.add(x + 1 > 3)
        s.add(x < 5)
        assert s.check() == sat

    def test_real_negative(self):
        x = Real("x")
        s = Solver()
        s.add(x == RealVal(-5))
        assert s.check() == sat
        m = s.model()
        assert m[x].numerator_as_long() == -5


class TestConversions:
    def test_to_real_sexpr(self):
        x = Int("x")
        expr = ToReal(x)
        assert expr.sexpr() == "(to_real x)"

    def test_to_int_sexpr(self):
        x = Real("x")
        expr = ToInt(x)
        assert expr.sexpr() == "(to_int x)"

    def test_is_int_sexpr(self):
        x = Real("x")
        expr = IsInt(x)
        assert expr.sexpr() == "(is_int x)"


class TestAbs:
    def test_abs_positive(self):
        x = Int("x")
        s = Solver()
        s.add(x == -5)
        s.add(Abs(x) == 5)
        assert s.check() == sat

    def test_abs_sexpr(self):
        x = Int("x")
        assert Abs(x).sexpr() == "(abs x)"


class TestExtendedArithmetic:
    def test_sum(self):
        x, y, z = Ints("x y z")
        s = Solver()
        s.add(x == 1, y == 2, z == 3)
        s.add(Sum(x, y, z) == 6)
        assert s.check() == sat

    def test_product(self):
        x, y = Ints("x y")
        s = Solver()
        s.add(x == 3, y == 4)
        s.add(Product(x, y) == 12)
        assert s.check() == sat

    def test_sum_list(self):
        vars_ = [Int(f"x{i}") for i in range(5)]
        s = Solver()
        for v in vars_:
            s.add(v == 1)
        s.add(Sum(vars_) == 5)
        assert s.check() == sat

    def test_reverse_operators(self):
        """Test that Python int on the left works (radd, rsub, etc.)."""
        x = Int("x")
        s = Solver()
        s.add(10 - x == 3)
        assert s.check() == sat
        assert s.model()[x].as_long() == 7

    def test_reverse_mul(self):
        x = Int("x")
        s = Solver()
        s.add(3 * x == 12)
        assert s.check() == sat
        assert s.model()[x].as_long() == 4
