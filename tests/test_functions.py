"""Tests for uninterpreted functions and quantifiers."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal, Bool, Real, Reals,
    Solver, sat, unsat,
    And, Or, Not, Implies, ForAll, Exists,
    Function, FuncDeclRef,
    IntSort, RealSort, BoolSort,
)


class TestFuncDecl:
    def test_create_function(self):
        f = Function("f", IntSort(), IntSort())
        assert f.name() == "f"
        assert f.arity() == 1

    def test_function_application_sexpr(self):
        f = Function("f", IntSort(), IntSort())
        x = Int("x")
        expr = f(x)
        assert expr.sexpr() == "(f x)"

    def test_function_multi_arg(self):
        g = Function("g", IntSort(), IntSort(), BoolSort())
        x, y = Ints("x y")
        expr = g(x, y)
        assert expr.sexpr() == "(g x y)"
        assert g.arity() == 2

    def test_function_arity_check(self):
        f = Function("f", IntSort(), IntSort())
        x, y = Ints("x y")
        with pytest.raises(Exception):
            f(x, y)  # f expects 1 arg

    def test_function_smtlib2_declare(self):
        f = Function("f", IntSort(), IntSort())
        assert f.smtlib2_declare() == "(declare-fun f (Int) Int)"

    def test_function_multi_arg_declare(self):
        g = Function("g", IntSort(), RealSort(), BoolSort())
        assert g.smtlib2_declare() == "(declare-fun g (Int Real) Bool)"


class TestFunctionSolving:
    def test_uninterpreted_function(self):
        f = Function("f", IntSort(), IntSort())
        x = Int("x")
        s = Solver()
        s.add(f(x) == 10)
        s.add(x == 5)
        assert s.check() == sat

    def test_function_equality(self):
        f = Function("f", IntSort(), IntSort())
        x, y = Ints("x y")
        s = Solver()
        s.add(x == y)
        s.add(f(x) != f(y))
        assert s.check() == unsat  # congruence: x=y => f(x)=f(y)

    def test_function_with_constraints(self):
        f = Function("f", IntSort(), IntSort())
        x = Int("x")
        s = Solver()
        s.add(f(0) == 1)
        s.add(f(1) == 2)
        s.add(x == 0)
        s.add(f(x) == 1)
        assert s.check() == sat

    def test_function_bool_range(self):
        p = Function("p", IntSort(), BoolSort())
        x = Int("x")
        s = Solver()
        s.add(p(0))
        s.add(Not(p(1)))
        s.add(x == 0)
        s.add(p(x))
        assert s.check() == sat


class TestQuantifiers:
    def test_forall_sexpr(self):
        x = Int("x")
        expr = ForAll(x, x > 0)
        assert expr.sexpr() == "(forall ((x Int)) (> x 0))"

    def test_forall_multi_var(self):
        x, y = Ints("x y")
        expr = ForAll([x, y], x + y > 0)
        assert "(forall ((x Int) (y Int))" in expr.sexpr()

    def test_exists_sexpr(self):
        x = Int("x")
        expr = Exists(x, x > 0)
        assert expr.sexpr() == "(exists ((x Int)) (> x 0))"

    def test_forall_solving(self):
        """ForAll x: f(x) >= x  implies f(5) >= 5."""
        f = Function("f", IntSort(), IntSort())
        x = Int("x")
        s = Solver()
        s.add(ForAll(x, f(x) >= x))
        s.add(Not(f(5) >= 5))
        assert s.check() == unsat

    def test_exists_solving(self):
        """There exists an x such that x*x == 4."""
        x = Int("x")
        y = Int("y")
        s = Solver()
        s.add(Exists(x, x * x == y))
        s.add(y == 4)
        assert s.check() == sat

    def test_forall_not_declared_as_const(self):
        """Bound variables in ForAll should not be declared as constants."""
        x = Int("x")
        y = Int("y")
        expr = ForAll(x, x + y > 0)
        s = Solver()
        s.add(expr)
        sexpr = s.sexpr()
        # x should NOT have a declare-const (it's bound by forall)
        # y SHOULD have a declare-const (it's free)
        assert "(declare-const y Int)" in sexpr
        # x should not be declared as a const since it's quantifier-bound
        lines = sexpr.split("\n")
        declare_lines = [l for l in lines if l.startswith("(declare-const")]
        assert all("declare-const x" not in l for l in declare_lines)
