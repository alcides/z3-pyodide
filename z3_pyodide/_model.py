"""Model representation for Z3 solver results."""

from __future__ import annotations

from ._exprs import ExprRef


class ModelRef:
    """Represents a Z3 model (satisfying assignment)."""

    _entries: dict[str, object]  # ExprRef or FuncInterp

    def __init__(self, entries: dict[str, object]):
        self._entries = entries

    def _resolve_name(self, key) -> str:
        from ._functions import FuncDeclRef
        if isinstance(key, ExprRef):
            return key._smtlib_name
        if isinstance(key, FuncDeclRef):
            return key.name()
        if isinstance(key, str):
            return key
        raise KeyError(f"Cannot look up {type(key).__name__} in model")

    def __getitem__(self, key) -> object:
        """Access model value by variable or function declaration.

        Usage: model[x] where x is a Z3 variable or FuncDeclRef.
        Returns ExprRef for constants, FuncInterp for functions.
        """
        name = self._resolve_name(key)
        if name not in self._entries:
            raise KeyError(f"'{name}' not found in model")
        return self._entries[name]

    def __contains__(self, key) -> bool:
        try:
            name = self._resolve_name(key)
            return name in self._entries
        except (KeyError, TypeError):
            return False

    def decls(self) -> list[str]:
        """Return the names of all declarations in the model."""
        return list(self._entries.keys())

    def __repr__(self) -> str:
        parts = []
        for name, val in self._entries.items():
            parts.append(f"{name} = {val}")
        return "[" + ", ".join(parts) + "]"

    def __str__(self) -> str:
        return self.__repr__()

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries.keys())

    def eval(self, expr: ExprRef, model_completion: bool = False) -> ExprRef:
        """Evaluate an expression in this model.

        For simple variables, this returns the model value.
        For complex expressions, this is not yet supported.
        """
        if expr.is_leaf() and expr._smtlib_name in self._entries:
            val = self._entries[expr._smtlib_name]
            if isinstance(val, ExprRef):
                return val
        raise NotImplementedError(
            "Complex expression evaluation in models is not yet supported. "
            "Use model[var] for individual variables."
        )
