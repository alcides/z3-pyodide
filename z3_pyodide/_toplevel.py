"""Module-level convenience functions matching z3-py's API."""

from __future__ import annotations

from ._exprs import (
    BoolRef, ArithRef, IntNumRef, RatNumRef, BoolValRef,
    BitVecRef, BitVecNumRef, ArrayRef, DatatypeRef,
    ExprRef, _coerce, _coerce_bool, _coerce_bv, _make_expr_for_sort,
)
from ._sorts import (
    IntSort, RealSort, BoolSort, BitVecSort, BitVecSortRef,
    ArraySort, ArraySortRef, SortRef,
)
from ._functions import (
    FuncDeclRef, Function, ForAll, Exists, QuantifierRef,
)
from ._datatypes import (
    Datatype, CreateDatatypes, DatatypeSortRef,
)


# --- Variable constructors ---

def Int(name: str, ctx=None) -> ArithRef:
    """Create an integer variable."""
    return ArithRef(IntSort(ctx), smtlib_name=name, ctx=ctx)


def Ints(names: str, ctx=None) -> tuple[ArithRef, ...]:
    """Create multiple integer variables from space-separated names."""
    return tuple(Int(n.strip(), ctx) for n in names.split())


def IntVal(val: int, ctx=None) -> IntNumRef:
    """Create an integer literal."""
    return IntNumRef(val, ctx)


def Real(name: str, ctx=None) -> ArithRef:
    """Create a real variable."""
    return ArithRef(RealSort(ctx), smtlib_name=name, ctx=ctx)


def Reals(names: str, ctx=None) -> tuple[ArithRef, ...]:
    """Create multiple real variables from space-separated names."""
    return tuple(Real(n.strip(), ctx) for n in names.split())


def RealVal(val, ctx=None) -> RatNumRef:
    """Create a real literal."""
    if isinstance(val, int):
        return RatNumRef(val, 1, ctx)
    if isinstance(val, float):
        from fractions import Fraction
        f = Fraction(val).limit_denominator()
        return RatNumRef(f.numerator, f.denominator, ctx)
    if isinstance(val, str):
        from fractions import Fraction
        f = Fraction(val)
        return RatNumRef(f.numerator, f.denominator, ctx)
    raise TypeError(f"Cannot create RealVal from {type(val).__name__}")


def Bool(name: str, ctx=None) -> BoolRef:
    """Create a boolean variable."""
    return BoolRef(smtlib_name=name, ctx=ctx)


def Bools(names: str, ctx=None) -> tuple[BoolRef, ...]:
    """Create multiple boolean variables from space-separated names."""
    return tuple(Bool(n.strip(), ctx) for n in names.split())


def BoolVal(val: bool, ctx=None) -> BoolValRef:
    """Create a boolean literal."""
    return BoolValRef(val, ctx)


# --- BitVector constructors ---

def BitVec(name: str, bv: int, ctx=None) -> BitVecRef:
    """Create a bitvector variable of given bit-width."""
    return BitVecRef(BitVecSort(bv, ctx), smtlib_name=name, ctx=ctx)


def BitVecs(names: str, bv: int, ctx=None) -> tuple[BitVecRef, ...]:
    """Create multiple bitvector variables from space-separated names."""
    return tuple(BitVec(n.strip(), bv, ctx) for n in names.split())


def BitVecVal(val: int, bv: int, ctx=None) -> BitVecNumRef:
    """Create a bitvector literal."""
    return BitVecNumRef(val, bv, ctx)


# --- BitVector operations ---

def UDiv(a: BitVecRef, b) -> BitVecRef:
    """Unsigned division."""
    b = _coerce_bv(b, a._sort)
    return BitVecRef(a._sort, "bvudiv", (a, b))


def URem(a: BitVecRef, b) -> BitVecRef:
    """Unsigned remainder."""
    b = _coerce_bv(b, a._sort)
    return BitVecRef(a._sort, "bvurem", (a, b))


def SDiv(a: BitVecRef, b) -> BitVecRef:
    """Signed division."""
    b = _coerce_bv(b, a._sort)
    return BitVecRef(a._sort, "bvsdiv", (a, b))


def SRem(a: BitVecRef, b) -> BitVecRef:
    """Signed remainder."""
    b = _coerce_bv(b, a._sort)
    return BitVecRef(a._sort, "bvsrem", (a, b))


def LShR(a: BitVecRef, b) -> BitVecRef:
    """Logical (unsigned) right shift."""
    b = _coerce_bv(b, a._sort)
    return BitVecRef(a._sort, "bvlshr", (a, b))


def RotateLeft(a: BitVecRef, b: int) -> BitVecRef:
    """Rotate bits left by b positions."""
    return BitVecRef(a._sort, f"(_ rotate_left {b})", (a,))


def RotateRight(a: BitVecRef, b: int) -> BitVecRef:
    """Rotate bits right by b positions."""
    return BitVecRef(a._sort, f"(_ rotate_right {b})", (a,))


def ZeroExt(n: int, a: BitVecRef) -> BitVecRef:
    """Zero-extend by n bits."""
    from ._sorts import BitVecSort
    new_sort = BitVecSort(a.size() + n)
    return BitVecRef(new_sort, f"(_ zero_extend {n})", (a,))


def SignExt(n: int, a: BitVecRef) -> BitVecRef:
    """Sign-extend by n bits."""
    from ._sorts import BitVecSort
    new_sort = BitVecSort(a.size() + n)
    return BitVecRef(new_sort, f"(_ sign_extend {n})", (a,))


def Extract(high: int, low: int, a: BitVecRef) -> BitVecRef:
    """Extract bits [high:low] from bitvector."""
    from ._sorts import BitVecSort
    new_sort = BitVecSort(high - low + 1)
    return BitVecRef(new_sort, f"(_ extract {high} {low})", (a,))


def Concat(*args: BitVecRef) -> BitVecRef:
    """Concatenate bitvectors."""
    if len(args) < 2:
        raise ValueError("Concat requires at least 2 arguments")
    from ._sorts import BitVecSort
    total_size = sum(a.size() for a in args)
    result_sort = BitVecSort(total_size)
    if len(args) == 2:
        return BitVecRef(result_sort, "concat", (args[0], args[1]))
    # Chain: (concat a (concat b c))
    result = args[-1]
    running_size = result.size()
    for a in reversed(args[:-1]):
        running_size += a.size()
        result = BitVecRef(BitVecSort(running_size), "concat", (a, result))
    return result


def RepeatBitVec(n: int, a: BitVecRef) -> BitVecRef:
    """Repeat bitvector n times."""
    from ._sorts import BitVecSort
    new_sort = BitVecSort(a.size() * n)
    return BitVecRef(new_sort, f"(_ repeat {n})", (a,))


def ULT(a: BitVecRef, b) -> BoolRef:
    """Unsigned less than."""
    b = _coerce_bv(b, a._sort)
    return BoolRef(op="bvult", children=(a, b))


def ULE(a: BitVecRef, b) -> BoolRef:
    """Unsigned less than or equal."""
    b = _coerce_bv(b, a._sort)
    return BoolRef(op="bvule", children=(a, b))


def UGT(a: BitVecRef, b) -> BoolRef:
    """Unsigned greater than."""
    b = _coerce_bv(b, a._sort)
    return BoolRef(op="bvugt", children=(a, b))


def UGE(a: BitVecRef, b) -> BoolRef:
    """Unsigned greater than or equal."""
    b = _coerce_bv(b, a._sort)
    return BoolRef(op="bvuge", children=(a, b))


def BV2Int(a: BitVecRef, is_signed: bool = False) -> ArithRef:
    """Convert bitvector to integer."""
    if is_signed:
        # SMT-LIB2 doesn't have a direct signed bv2int, emulate it
        return ArithRef(IntSort(), "bv2int", (a,))
    return ArithRef(IntSort(), "bv2int", (a,))


def Int2BV(a: ArithRef, size: int) -> BitVecRef:
    """Convert integer to bitvector."""
    from ._sorts import BitVecSort
    return BitVecRef(BitVecSort(size), f"(_ int2bv {size})", (a,))


def is_bv(a) -> bool:
    """Check if expression is a bitvector."""
    return isinstance(a, BitVecRef)


def is_bv_value(a) -> bool:
    """Check if expression is a bitvector literal."""
    return isinstance(a, BitVecNumRef)


# --- Array constructors and operations ---

def Array(name: str, domain: SortRef, range_: SortRef, ctx=None) -> ArrayRef:
    """Create an array variable."""
    sort = ArraySort(domain, range_)
    return ArrayRef(sort, smtlib_name=name, ctx=ctx)


def Select(a: ArrayRef, index) -> ExprRef:
    """Array select: Select(a, i) is equivalent to a[i]."""
    return a[index]


def Store(a: ArrayRef, index, value) -> ArrayRef:
    """Array store: returns new array with a[index] = value."""
    return a.store(index, value)


def K(sort: SortRef, value) -> ArrayRef:
    """Create a constant array where every element is value.

    K(IntSort(), 0) creates an array where all elements are 0.
    """
    value = _coerce(value, sort)
    arr_sort = ArraySort(sort, value._sort) if not isinstance(sort, ArraySortRef) else sort
    # For constant arrays, we need: ((as const (Array D R)) value)
    if isinstance(sort, ArraySortRef):
        domain = sort.domain()
        range_ = sort.range()
    else:
        domain = sort
        range_ = value._sort
        arr_sort = ArraySort(domain, range_)
    return ArrayRef(arr_sort, f"(as const {arr_sort.sexpr()})", (value,))


def is_array(a) -> bool:
    """Check if expression is an array."""
    return isinstance(a, ArrayRef)


# --- Logical combinators ---

def And(*args: BoolRef) -> BoolRef:
    """Logical AND of multiple boolean expressions."""
    # Flatten single-list argument
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(args[0])
    if len(args) == 0:
        return BoolValRef(True)
    if len(args) == 1:
        return _coerce_bool(args[0])
    coerced = tuple(_coerce_bool(a) for a in args)
    return BoolRef(op="and", children=coerced)


def Or(*args: BoolRef) -> BoolRef:
    """Logical OR of multiple boolean expressions."""
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(args[0])
    if len(args) == 0:
        return BoolValRef(False)
    if len(args) == 1:
        return _coerce_bool(args[0])
    coerced = tuple(_coerce_bool(a) for a in args)
    return BoolRef(op="or", children=coerced)


def Not(a: BoolRef) -> BoolRef:
    """Logical NOT."""
    a = _coerce_bool(a)
    return BoolRef(op="not", children=(a,))


def Implies(a: BoolRef, b: BoolRef) -> BoolRef:
    """Logical implication: a => b."""
    a = _coerce_bool(a)
    b = _coerce_bool(b)
    return BoolRef(op="=>", children=(a, b))


def Xor(a: BoolRef, b: BoolRef) -> BoolRef:
    """Logical XOR."""
    a = _coerce_bool(a)
    b = _coerce_bool(b)
    return BoolRef(op="xor", children=(a, b))


def If(cond: BoolRef, then_val: ExprRef, else_val: ExprRef) -> ExprRef:
    """If-then-else expression."""
    cond = _coerce_bool(cond)
    # Determine result sort
    if isinstance(then_val, (int, float)):
        then_val = _coerce(then_val, else_val._sort if isinstance(else_val, ExprRef) else IntSort())
    if isinstance(else_val, (int, float)):
        else_val = _coerce(else_val, then_val._sort if isinstance(then_val, ExprRef) else IntSort())
    result_sort = then_val._sort if isinstance(then_val, ExprRef) else IntSort()

    if isinstance(result_sort, type(BoolSort())) or result_sort.name() == "Bool":
        return BoolRef(op="ite", children=(cond, then_val, else_val))
    return ArithRef(result_sort, op="ite", children=(cond, then_val, else_val))


def Distinct(*args: ExprRef) -> BoolRef:
    """All arguments are pairwise distinct."""
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(args[0])
    if len(args) <= 1:
        return BoolValRef(True)
    return BoolRef(op="distinct", children=tuple(args))


def Sum(*args: ArithRef) -> ArithRef:
    """Sum of arithmetic expressions."""
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(args[0])
    if len(args) == 0:
        return IntNumRef(0)
    if len(args) == 1:
        return args[0]
    result = args[0]
    for a in args[1:]:
        result = result + a
    return result


def Product(*args: ArithRef) -> ArithRef:
    """Product of arithmetic expressions."""
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        args = tuple(args[0])
    if len(args) == 0:
        return IntNumRef(1)
    if len(args) == 1:
        return args[0]
    result = args[0]
    for a in args[1:]:
        result = result * a
    return result


# --- Conversions ---

def ToReal(a: ArithRef) -> ArithRef:
    """Convert an integer expression to real."""
    if isinstance(a, (int,)):
        return RatNumRef(a)
    return ArithRef(RealSort(), "to_real", (a,))


def ToInt(a: ArithRef) -> ArithRef:
    """Convert a real expression to integer (floor)."""
    return ArithRef(IntSort(), "to_int", (a,))


def IsInt(a: ArithRef) -> BoolRef:
    """Check if a real expression has an integer value."""
    return BoolRef(op="is_int", children=(a,))


# --- Abs ---

def Abs(a: ArithRef) -> ArithRef:
    """Absolute value."""
    return ArithRef(a._sort, "abs", (a,))


# --- Type checking predicates ---

def is_bool(a) -> bool:
    return isinstance(a, BoolRef)


def is_int(a) -> bool:
    return isinstance(a, ArithRef) and a._sort.name() == "Int"


def is_real(a) -> bool:
    return isinstance(a, ArithRef) and a._sort.name() == "Real"


def is_int_value(a) -> bool:
    return isinstance(a, IntNumRef)


def is_rational_value(a) -> bool:
    return isinstance(a, RatNumRef)
