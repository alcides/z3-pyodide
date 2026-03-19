"""Tests for algebraic datatypes."""

import pytest
from z3_pyodide import (
    Int, Ints, IntVal,
    Solver, sat, unsat,
    And, Or, Not, If, Distinct, ForAll,
    IntSort, BoolSort,
    Datatype, CreateDatatypes,
)


class TestDatatypeCreation:
    def test_simple_enum(self):
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color.declare("Blue")
        Color = Color.create()
        assert Color.name() == "Color"
        assert Color.num_constructors() == 3

    def test_constructor_attributes(self):
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color.declare("Blue")
        Color = Color.create()
        assert hasattr(Color, "Red")
        assert hasattr(Color, "Green")
        assert hasattr(Color, "Blue")

    def test_recognizer_attributes(self):
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color = Color.create()
        assert hasattr(Color, "is_Red")
        assert hasattr(Color, "is_Green")


class TestDatatypeSolving:
    def test_enum_sat(self):
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color.declare("Blue")
        Color = Color.create()

        from z3_pyodide._exprs import DatatypeRef
        x = DatatypeRef(Color, smtlib_name="x")
        s = Solver()
        s.add(Color.is_Red(x))
        assert s.check() == sat

    def test_enum_distinct(self):
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color.declare("Blue")
        Color = Color.create()

        from z3_pyodide._exprs import DatatypeRef
        x = DatatypeRef(Color, smtlib_name="x")
        y = DatatypeRef(Color, smtlib_name="y")
        s = Solver()
        s.add(Color.is_Red(x))
        s.add(Color.is_Red(y))
        s.add(x != y)
        assert s.check() == unsat

    def test_enum_exhaustive(self):
        """A color must be Red, Green, or Blue."""
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color.declare("Blue")
        Color = Color.create()

        from z3_pyodide._exprs import DatatypeRef
        x = DatatypeRef(Color, smtlib_name="x")
        s = Solver()
        s.add(Not(Color.is_Red(x)))
        s.add(Not(Color.is_Green(x)))
        s.add(Not(Color.is_Blue(x)))
        assert s.check() == unsat


class TestDatatypeWithAccessors:
    def test_pair(self):
        Pair = Datatype("Pair")
        Pair.declare("mk_pair", ("fst", IntSort()), ("snd", IntSort()))
        Pair = Pair.create()

        assert hasattr(Pair, "mk_pair")
        assert hasattr(Pair, "fst")
        assert hasattr(Pair, "snd")

    def test_pair_solving(self):
        Pair = Datatype("Pair")
        Pair.declare("mk_pair", ("fst", IntSort()), ("snd", IntSort()))
        Pair = Pair.create()

        p = Pair.mk_pair(IntVal(1), IntVal(2))
        s = Solver()
        s.add(Pair.fst(p) == 1)
        s.add(Pair.snd(p) == 2)
        assert s.check() == sat

    def test_pair_accessor_constraint(self):
        Pair = Datatype("Pair")
        Pair.declare("mk_pair", ("fst", IntSort()), ("snd", IntSort()))
        Pair = Pair.create()

        from z3_pyodide._exprs import DatatypeRef
        p = DatatypeRef(Pair, smtlib_name="p")
        s = Solver()
        s.add(Pair.fst(p) + Pair.snd(p) == 10)
        s.add(Pair.fst(p) == 3)
        assert s.check() == sat


class TestRecursiveDatatype:
    def test_list_creation(self):
        IntList = Datatype("IntList")
        IntList.declare("nil")
        IntList.declare("cons", ("head", IntSort()), ("tail", "IntList"))
        IntList = IntList.create()

        assert hasattr(IntList, "nil")
        assert hasattr(IntList, "cons")
        assert hasattr(IntList, "head")
        assert hasattr(IntList, "tail")
        assert hasattr(IntList, "is_nil")
        assert hasattr(IntList, "is_cons")

    def test_list_solving(self):
        IntList = Datatype("IntList")
        IntList.declare("nil")
        IntList.declare("cons", ("head", IntSort()), ("tail", "IntList"))
        IntList = IntList.create()

        from z3_pyodide._exprs import DatatypeRef
        l = DatatypeRef(IntList, smtlib_name="l")
        s = Solver()
        s.add(IntList.is_cons(l))
        s.add(IntList.head(l) == 42)
        assert s.check() == sat

    def test_list_nil(self):
        IntList = Datatype("IntList")
        IntList.declare("nil")
        IntList.declare("cons", ("head", IntSort()), ("tail", "IntList"))
        IntList = IntList.create()

        from z3_pyodide._exprs import DatatypeRef
        l = DatatypeRef(IntList, smtlib_name="l")
        s = Solver()
        s.add(IntList.is_nil(l))
        s.add(IntList.is_cons(l))
        assert s.check() == unsat


class TestMutuallyRecursiveDatatypes:
    def test_tree_forest(self):
        Tree = Datatype("Tree")
        Forest = Datatype("Forest")
        Tree.declare("leaf", ("val", IntSort()))
        Tree.declare("node", ("children", "Forest"))
        Forest.declare("empty")
        Forest.declare("cons_tree", ("first", "Tree"), ("rest", "Forest"))

        Tree, Forest = CreateDatatypes(Tree, Forest)

        assert Tree.name() == "Tree"
        assert Forest.name() == "Forest"
        assert hasattr(Tree, "leaf")
        assert hasattr(Tree, "node")
        assert hasattr(Forest, "empty")
        assert hasattr(Forest, "cons_tree")

    def test_tree_forest_solving(self):
        Tree = Datatype("Tree")
        Forest = Datatype("Forest")
        Tree.declare("leaf", ("val", IntSort()))
        Tree.declare("node", ("children", "Forest"))
        Forest.declare("empty")
        Forest.declare("cons_tree", ("first", "Tree"), ("rest", "Forest"))

        Tree, Forest = CreateDatatypes(Tree, Forest)

        from z3_pyodide._exprs import DatatypeRef
        t = DatatypeRef(Tree, smtlib_name="t")
        s = Solver()
        s.add(Tree.is_leaf(t))
        s.add(Tree.val(t) == 42)
        assert s.check() == sat


class TestDatatypeSMTLIB2:
    def test_declare_datatypes_format(self):
        Color = Datatype("Color")
        Color.declare("Red")
        Color.declare("Green")
        Color.declare("Blue")
        Color = Color.create()

        assert hasattr(Color, "_smtlib2_declare")
        decl = Color._smtlib2_declare
        assert "declare-datatypes" in decl
        assert "Color" in decl
        assert "Red" in decl
        assert "Green" in decl
        assert "Blue" in decl
