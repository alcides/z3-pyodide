"""Sort definitions: Bool, Int, Real, BitVec, Array."""

from __future__ import annotations

from ._ast import SortRef


class BoolSortRef(SortRef):
    def name(self) -> str:
        return "Bool"

    def sexpr(self) -> str:
        return "Bool"


class ArithSortRef(SortRef):
    _name: str

    def __init__(self, name: str, ctx=None):
        super().__init__(ctx)
        self._name = name

    def name(self) -> str:
        return self._name

    def sexpr(self) -> str:
        return self._name

    def is_int(self) -> bool:
        return self._name == "Int"

    def is_real(self) -> bool:
        return self._name == "Real"


class BitVecSortRef(SortRef):
    _size: int

    def __init__(self, size: int, ctx=None):
        super().__init__(ctx)
        self._size = size

    def name(self) -> str:
        return f"(_ BitVec {self._size})"

    def sexpr(self) -> str:
        return self.name()

    def size(self) -> int:
        return self._size


class ArraySortRef(SortRef):
    _domain: SortRef
    _range: SortRef

    def __init__(self, domain: SortRef, range_: SortRef, ctx=None):
        super().__init__(ctx)
        self._domain = domain
        self._range = range_

    def name(self) -> str:
        return f"(Array {self._domain.sexpr()} {self._range.sexpr()})"

    def sexpr(self) -> str:
        return self.name()

    def domain(self) -> SortRef:
        return self._domain

    def range(self) -> SortRef:
        return self._range


# Singleton sort instances
_BOOL_SORT = None
_INT_SORT = None
_REAL_SORT = None


def BoolSort(ctx=None) -> BoolSortRef:
    global _BOOL_SORT
    if _BOOL_SORT is None:
        _BOOL_SORT = BoolSortRef(ctx)
    return _BOOL_SORT


def IntSort(ctx=None) -> ArithSortRef:
    global _INT_SORT
    if _INT_SORT is None:
        _INT_SORT = ArithSortRef("Int", ctx)
    return _INT_SORT


def RealSort(ctx=None) -> ArithSortRef:
    global _REAL_SORT
    if _REAL_SORT is None:
        _REAL_SORT = ArithSortRef("Real", ctx)
    return _REAL_SORT


def BitVecSort(sz: int, ctx=None) -> BitVecSortRef:
    return BitVecSortRef(sz, ctx)


def ArraySort(domain: SortRef, range_: SortRef) -> ArraySortRef:
    return ArraySortRef(domain, range_)
