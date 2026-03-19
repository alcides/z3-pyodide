"""Base AST classes for Z3 expressions."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._context import Context

_id_counter = itertools.count()


class AstRef:
    """Base class for all Z3 AST nodes."""

    __slots__ = ("_id", "_ctx")

    def __init__(self, ctx: Context | None = None):
        from ._context import get_default_context

        self._id = next(_id_counter)
        self._ctx = ctx or get_default_context()

    def ctx(self) -> Context:
        return self._ctx

    def sexpr(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return self.sexpr()

    def __str__(self) -> str:
        return self.sexpr()

    def __hash__(self) -> int:
        return self._id

    def eq(self, other: AstRef) -> bool:
        return self._id == other._id


class SortRef(AstRef):
    """Base class for sorts."""

    def name(self) -> str:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SortRef):
            return NotImplemented
        return self.name() == other.name()

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, SortRef):
            return NotImplemented
        return self.name() != other.name()

    def __hash__(self) -> int:
        return hash(self.name())
