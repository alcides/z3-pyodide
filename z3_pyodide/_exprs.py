"""Expression classes with operator overloading."""

from __future__ import annotations

from ._ast import AstRef, SortRef


class ExprRef(AstRef):
    """Base class for all Z3 expressions."""

    _sort: SortRef
    _op: str
    _children: tuple[ExprRef, ...]
    _smtlib_name: str  # for leaf nodes (variables/constants)

    def __init__(self, sort: SortRef, op: str = "",
                 children: tuple[ExprRef, ...] = (),
                 smtlib_name: str = "", ctx=None):
        super().__init__(ctx)
        self._sort = sort
        self._op = op
        self._children = children
        self._smtlib_name = smtlib_name

    def sort(self) -> SortRef:
        return self._sort

    def is_leaf(self) -> bool:
        return len(self._children) == 0

    def sexpr(self) -> str:
        if self.is_leaf():
            return self._smtlib_name
        if len(self._children) == 1 and self._op == "not":
            return f"(not {self._children[0].sexpr()})"
        child_sexprs = " ".join(c.sexpr() for c in self._children)
        return f"({self._op} {child_sexprs})"

    def __eq__(self, other) -> BoolRef:  # type: ignore[override]
        other = _coerce(other, self._sort)
        return BoolRef(op="=", children=(self, other))

    def __ne__(self, other) -> BoolRef:  # type: ignore[override]
        eq = self.__eq__(other)
        return BoolRef(op="not", children=(eq,))

    def __hash__(self) -> int:
        return self._id


class BoolRef(ExprRef):
    """Boolean expression."""

    def __init__(self, op: str = "", children: tuple[ExprRef, ...] = (),
                 smtlib_name: str = "", ctx=None):
        from ._sorts import BoolSort
        super().__init__(BoolSort(ctx), op, children, smtlib_name, ctx)

    def __and__(self, other: BoolRef) -> BoolRef:
        other = _coerce_bool(other)
        return BoolRef(op="and", children=(self, other))

    def __rand__(self, other: BoolRef) -> BoolRef:
        other = _coerce_bool(other)
        return BoolRef(op="and", children=(other, self))

    def __or__(self, other: BoolRef) -> BoolRef:
        other = _coerce_bool(other)
        return BoolRef(op="or", children=(self, other))

    def __ror__(self, other: BoolRef) -> BoolRef:
        other = _coerce_bool(other)
        return BoolRef(op="or", children=(other, self))

    def __invert__(self) -> BoolRef:
        return BoolRef(op="not", children=(self,))

    def __bool__(self) -> bool:
        raise Z3Exception(
            "Symbolic expressions cannot be used as Python booleans. "
            "Use And(), Or(), Not() for logical operations."
        )


class ArithRef(ExprRef):
    """Arithmetic expression (Int or Real)."""

    def __init__(self, sort: SortRef | None = None, op: str = "",
                 children: tuple[ExprRef, ...] = (),
                 smtlib_name: str = "", ctx=None):
        from ._sorts import IntSort
        super().__init__(sort or IntSort(ctx), op, children, smtlib_name, ctx)

    def __add__(self, other) -> ArithRef:
        sort = _arith_result_sort(self, other)
        other = _coerce(other, self._sort)
        return ArithRef(sort, "+", (self, other))

    def __radd__(self, other) -> ArithRef:
        sort = _arith_result_sort(self, other)
        other = _coerce(other, self._sort)
        return ArithRef(sort, "+", (other, self))

    def __sub__(self, other) -> ArithRef:
        sort = _arith_result_sort(self, other)
        other = _coerce(other, self._sort)
        return ArithRef(sort, "-", (self, other))

    def __rsub__(self, other) -> ArithRef:
        sort = _arith_result_sort(self, other)
        other = _coerce(other, self._sort)
        return ArithRef(sort, "-", (other, self))

    def __mul__(self, other) -> ArithRef:
        sort = _arith_result_sort(self, other)
        other = _coerce(other, self._sort)
        return ArithRef(sort, "*", (self, other))

    def __rmul__(self, other) -> ArithRef:
        sort = _arith_result_sort(self, other)
        other = _coerce(other, self._sort)
        return ArithRef(sort, "*", (other, self))

    def __truediv__(self, other) -> ArithRef:
        from ._sorts import RealSort
        other = _coerce(other, self._sort)
        return ArithRef(RealSort(), "div" if self._sort.name() == "Int" else "/", (self, other))

    def __rtruediv__(self, other) -> ArithRef:
        from ._sorts import RealSort
        other = _coerce(other, self._sort)
        return ArithRef(RealSort(), "div" if self._sort.name() == "Int" else "/", (other, self))

    def __mod__(self, other) -> ArithRef:
        other = _coerce(other, self._sort)
        return ArithRef(self._sort, "mod", (self, other))

    def __rmod__(self, other) -> ArithRef:
        other = _coerce(other, self._sort)
        return ArithRef(self._sort, "mod", (other, self))

    def __neg__(self) -> ArithRef:
        return ArithRef(self._sort, "-", (self,))

    def __lt__(self, other) -> BoolRef:
        other = _coerce(other, self._sort)
        return BoolRef(op="<", children=(self, other))

    def __le__(self, other) -> BoolRef:
        other = _coerce(other, self._sort)
        return BoolRef(op="<=", children=(self, other))

    def __gt__(self, other) -> BoolRef:
        other = _coerce(other, self._sort)
        return BoolRef(op=">", children=(self, other))

    def __ge__(self, other) -> BoolRef:
        other = _coerce(other, self._sort)
        return BoolRef(op=">=", children=(self, other))


class IntNumRef(ArithRef):
    """Integer literal value."""

    _value: int

    def __init__(self, value: int, ctx=None):
        from ._sorts import IntSort
        smtlib = str(value) if value >= 0 else f"(- {abs(value)})"
        super().__init__(IntSort(ctx), smtlib_name=smtlib, ctx=ctx)
        self._value = value

    def as_long(self) -> int:
        return self._value

    def as_string(self) -> str:
        return str(self._value)

    def sexpr(self) -> str:
        if self._value >= 0:
            return str(self._value)
        return f"(- {abs(self._value)})"


class RatNumRef(ArithRef):
    """Rational literal value."""

    _num: int
    _den: int

    def __init__(self, num: int, den: int = 1, ctx=None):
        from ._sorts import RealSort
        if den == 1:
            smtlib = f"{num}.0" if num >= 0 else f"(- {abs(num)}.0)"
        else:
            smtlib = f"(/ {num} {den})" if num >= 0 else f"(/ (- {abs(num)}) {den})"
        super().__init__(RealSort(ctx), smtlib_name=smtlib, ctx=ctx)
        self._num = num
        self._den = den

    def numerator_as_long(self) -> int:
        return self._num

    def denominator_as_long(self) -> int:
        return self._den

    def as_string(self) -> str:
        if self._den == 1:
            return str(self._num)
        return f"{self._num}/{self._den}"

    def as_fraction(self):
        from fractions import Fraction
        return Fraction(self._num, self._den)

    def as_decimal(self, prec: int = 10) -> str:
        from decimal import Decimal, getcontext
        getcontext().prec = prec
        return str(Decimal(self._num) / Decimal(self._den))


class BitVecRef(ExprRef):
    """BitVector expression."""

    def __init__(self, sort=None, op: str = "",
                 children: tuple[ExprRef, ...] = (),
                 smtlib_name: str = "", ctx=None):
        from ._sorts import BitVecSortRef
        if sort is None:
            from ._sorts import BitVecSort
            sort = BitVecSort(32, ctx)
        super().__init__(sort, op, children, smtlib_name, ctx)

    def size(self) -> int:
        from ._sorts import BitVecSortRef
        assert isinstance(self._sort, BitVecSortRef)
        return self._sort.size()

    def _bv(self, op: str, other) -> BitVecRef:
        other = _coerce_bv(other, self._sort)
        return BitVecRef(self._sort, op, (self, other))

    def _rbv(self, op: str, other) -> BitVecRef:
        other = _coerce_bv(other, self._sort)
        return BitVecRef(self._sort, op, (other, self))

    # Arithmetic
    def __add__(self, other) -> BitVecRef:
        return self._bv("bvadd", other)

    def __radd__(self, other) -> BitVecRef:
        return self._rbv("bvadd", other)

    def __sub__(self, other) -> BitVecRef:
        return self._bv("bvsub", other)

    def __rsub__(self, other) -> BitVecRef:
        return self._rbv("bvsub", other)

    def __mul__(self, other) -> BitVecRef:
        return self._bv("bvmul", other)

    def __rmul__(self, other) -> BitVecRef:
        return self._rbv("bvmul", other)

    def __neg__(self) -> BitVecRef:
        return BitVecRef(self._sort, "bvneg", (self,))

    # Bitwise
    def __and__(self, other) -> BitVecRef:
        return self._bv("bvand", other)

    def __rand__(self, other) -> BitVecRef:
        return self._rbv("bvand", other)

    def __or__(self, other) -> BitVecRef:
        return self._bv("bvor", other)

    def __ror__(self, other) -> BitVecRef:
        return self._rbv("bvor", other)

    def __xor__(self, other) -> BitVecRef:
        return self._bv("bvxor", other)

    def __rxor__(self, other) -> BitVecRef:
        return self._rbv("bvxor", other)

    def __invert__(self) -> BitVecRef:
        return BitVecRef(self._sort, "bvnot", (self,))

    def __lshift__(self, other) -> BitVecRef:
        return self._bv("bvshl", other)

    def __rlshift__(self, other) -> BitVecRef:
        return self._rbv("bvshl", other)

    def __rshift__(self, other) -> BitVecRef:
        return self._bv("bvashr", other)

    def __rrshift__(self, other) -> BitVecRef:
        return self._rbv("bvashr", other)

    # Signed comparisons
    def __lt__(self, other) -> BoolRef:
        other = _coerce_bv(other, self._sort)
        return BoolRef(op="bvslt", children=(self, other))

    def __le__(self, other) -> BoolRef:
        other = _coerce_bv(other, self._sort)
        return BoolRef(op="bvsle", children=(self, other))

    def __gt__(self, other) -> BoolRef:
        other = _coerce_bv(other, self._sort)
        return BoolRef(op="bvsgt", children=(self, other))

    def __ge__(self, other) -> BoolRef:
        other = _coerce_bv(other, self._sort)
        return BoolRef(op="bvsge", children=(self, other))


class BitVecNumRef(BitVecRef):
    """BitVector literal value."""

    _value: int

    def __init__(self, value: int, size: int, ctx=None):
        from ._sorts import BitVecSort
        sort = BitVecSort(size, ctx)
        # Normalize to unsigned range for SMT-LIB2
        self._value = value & ((1 << size) - 1)
        smtlib = f"(_ bv{self._value} {size})"
        super().__init__(sort, smtlib_name=smtlib, ctx=ctx)

    def as_long(self) -> int:
        return self._value

    def as_signed_long(self) -> int:
        sz = self.size()
        if self._value >= (1 << (sz - 1)):
            return self._value - (1 << sz)
        return self._value

    def as_string(self) -> str:
        return str(self._value)

    def sexpr(self) -> str:
        return f"(_ bv{self._value} {self.size()})"


class ArrayRef(ExprRef):
    """Array expression."""

    def __init__(self, sort=None, op: str = "",
                 children: tuple[ExprRef, ...] = (),
                 smtlib_name: str = "", ctx=None):
        from ._sorts import ArraySortRef
        super().__init__(sort, op, children, smtlib_name, ctx)

    def domain(self):
        from ._sorts import ArraySortRef
        assert isinstance(self._sort, ArraySortRef)
        return self._sort.domain()

    def range(self):
        from ._sorts import ArraySortRef
        assert isinstance(self._sort, ArraySortRef)
        return self._sort.range()

    def __getitem__(self, index) -> ExprRef:
        """Array select: a[i] -> (select a i)"""
        from ._sorts import ArraySortRef
        index = _coerce(index, self.domain())
        range_sort = self.range()
        return _make_expr_for_sort(range_sort, "select", (self, index))

    def store(self, index, value) -> ArrayRef:
        """Array store: returns a new array with a[index] = value."""
        index = _coerce(index, self.domain())
        value = _coerce(value, self.range())
        return ArrayRef(self._sort, "store", (self, index, value))


def _make_expr_for_sort(sort, op: str, children: tuple) -> ExprRef:
    """Create an expression with the appropriate subclass based on sort."""
    from ._sorts import BoolSortRef, ArithSortRef, BitVecSortRef, ArraySortRef
    sort_name = sort.name()
    if sort_name == "Bool":
        return BoolRef(op=op, children=children)
    if isinstance(sort, ArithSortRef):
        return ArithRef(sort, op, children)
    if isinstance(sort, BitVecSortRef):
        return BitVecRef(sort, op, children)
    if isinstance(sort, ArraySortRef):
        return ArrayRef(sort, op, children)
    return ExprRef(sort, op, children)


class DatatypeRef(ExprRef):
    """Datatype expression."""

    def __init__(self, sort=None, op: str = "",
                 children: tuple[ExprRef, ...] = (),
                 smtlib_name: str = "", ctx=None):
        super().__init__(sort, op, children, smtlib_name, ctx)


class BoolValRef(BoolRef):
    """Boolean literal (true/false)."""

    _value: bool

    def __init__(self, value: bool, ctx=None):
        smtlib = "true" if value else "false"
        super().__init__(smtlib_name=smtlib, ctx=ctx)
        self._value = value

    def sexpr(self) -> str:
        return "true" if self._value else "false"


# --- Helper functions ---

class Z3Exception(Exception):
    pass


def _coerce(val, target_sort: SortRef) -> ExprRef:
    """Coerce a Python value to an ExprRef matching target_sort."""
    if isinstance(val, ExprRef):
        return val
    if isinstance(val, bool):
        return BoolValRef(val)
    if isinstance(val, int):
        from ._sorts import BitVecSortRef
        if isinstance(target_sort, BitVecSortRef):
            return BitVecNumRef(val, target_sort.size())
        if target_sort.name() == "Real":
            return RatNumRef(val)
        return IntNumRef(val)
    if isinstance(val, float):
        from fractions import Fraction
        f = Fraction(val).limit_denominator()
        return RatNumRef(f.numerator, f.denominator)
    raise Z3Exception(f"Cannot coerce {type(val).__name__} to Z3 expression")


def _coerce_bv(val, target_sort: SortRef) -> BitVecRef:
    """Coerce a value to a BitVecRef."""
    if isinstance(val, BitVecRef):
        return val
    if isinstance(val, int):
        from ._sorts import BitVecSortRef
        assert isinstance(target_sort, BitVecSortRef)
        return BitVecNumRef(val, target_sort.size())
    raise Z3Exception(f"Cannot coerce {type(val).__name__} to BitVec")


def _coerce_bool(val) -> BoolRef:
    if isinstance(val, BoolRef):
        return val
    if isinstance(val, bool):
        return BoolValRef(val)
    raise Z3Exception(f"Cannot coerce {type(val).__name__} to Bool")


def _arith_result_sort(a, b) -> SortRef:
    """Determine result sort for arithmetic operations."""
    from ._sorts import RealSort
    if isinstance(b, ExprRef) and b._sort.name() == "Real":
        return RealSort()
    if isinstance(a, ExprRef) and a._sort.name() == "Real":
        return RealSort()
    return a._sort
