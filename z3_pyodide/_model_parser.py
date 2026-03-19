"""Parse Z3 model output into Python objects."""

from __future__ import annotations

from ._sexpr_parser import parse_sexpr
from ._exprs import ExprRef, IntNumRef, RatNumRef, BoolValRef, BitVecNumRef, ArithRef
from ._sorts import IntSort, RealSort, BoolSort


class FuncInterpEntry:
    """A single entry in a function interpretation."""

    def __init__(self, args: tuple, value: ExprRef):
        self.args = args
        self.value = value

    def __repr__(self) -> str:
        args_str = ", ".join(str(a) for a in self.args)
        return f"[{args_str} -> {self.value}]"


class FuncInterp:
    """Interpretation of an uninterpreted function in a model."""

    def __init__(self, entries: list[FuncInterpEntry], else_value: ExprRef | None = None):
        self._entries = entries
        self._else_value = else_value

    def num_entries(self) -> int:
        return len(self._entries)

    def entry(self, i: int) -> FuncInterpEntry:
        return self._entries[i]

    def else_value(self) -> ExprRef | None:
        return self._else_value

    def as_list(self) -> list:
        result = list(self._entries)
        if self._else_value is not None:
            result.append(self._else_value)
        return result

    def __repr__(self) -> str:
        parts = [str(e) for e in self._entries]
        if self._else_value is not None:
            parts.append(f"else -> {self._else_value}")
        return "[" + ", ".join(parts) + "]"


def parse_model_string(text: str) -> dict[str, ExprRef | FuncInterp]:
    """Parse a (model ...) S-expression string into a dict of name -> value.

    Example input:
        (model
          (define-fun x () Int 42)
          (define-fun y () Int (- 5))
          (define-fun p () Bool true)
          (define-fun f ((x!0 Int)) Int (ite (= x!0 1) 10 0))
        )
    """
    parsed = parse_sexpr(text.strip())
    if not isinstance(parsed, list):
        return {}
    return _interpret_model(parsed)


def _interpret_model(sexpr: list) -> dict[str, ExprRef | FuncInterp]:
    """Interpret a parsed model S-expression."""
    result: dict[str, ExprRef | FuncInterp] = {}

    entries = sexpr
    # Skip "model" header if present
    if entries and entries[0] == "model":
        entries = entries[1:]

    for entry in entries:
        if not isinstance(entry, list):
            continue
        if len(entry) < 5 or entry[0] != "define-fun":
            continue
        name = entry[1]
        params = entry[2]  # parameter list (empty list for constants)
        sort_sexpr = entry[3]
        value_sexpr = entry[4]

        if isinstance(params, list) and len(params) > 0:
            # Function interpretation - try to parse as ite chain
            interp = _parse_func_interp(value_sexpr, sort_sexpr)
            if interp is not None:
                result[name] = interp
        else:
            # Constant value
            value = _interpret_value(value_sexpr, sort_sexpr)
            if value is not None:
                result[name] = value

    return result


def _interpret_value(value_sexpr, sort_sexpr) -> ExprRef | None:
    """Interpret a value S-expression given its sort."""
    # Handle BitVec sort: could be a list like ["_", "BitVec", "8"]
    bv_size = _extract_bv_sort_size(sort_sexpr)
    if bv_size is not None:
        return _parse_bv_value(value_sexpr, bv_size)

    sort_name = sort_sexpr if isinstance(sort_sexpr, str) else str(sort_sexpr)
    if sort_name == "Int":
        return _parse_int_value(value_sexpr)
    elif sort_name == "Real":
        return _parse_real_value(value_sexpr)
    elif sort_name == "Bool":
        return _parse_bool_value(value_sexpr)
    return None


def _extract_bv_sort_size(sort_sexpr) -> int | None:
    """Extract BitVec size from sort S-expression.

    Handles: ["_", "BitVec", "8"] or "(_ BitVec 8)"
    """
    if isinstance(sort_sexpr, list) and len(sort_sexpr) == 3:
        if sort_sexpr[0] == "_" and sort_sexpr[1] == "BitVec":
            try:
                return int(sort_sexpr[2])
            except (ValueError, TypeError):
                pass
    if isinstance(sort_sexpr, str) and "BitVec" in sort_sexpr:
        # Try to parse "(_ BitVec N)"
        parts = sort_sexpr.strip("()_ ").split()
        for i, p in enumerate(parts):
            if p == "BitVec" and i + 1 < len(parts):
                try:
                    return int(parts[i + 1])
                except ValueError:
                    pass
    return None


def _parse_bv_value(v, size: int) -> BitVecNumRef | None:
    """Parse a bitvector value from S-expression.

    Handles:
      - "#b0101" (binary literal)
      - "#x1F" (hex literal)
      - ["_", "bv42", "8"] (indexed literal)
      - "42" (plain numeral, rare)
    """
    if isinstance(v, str):
        if v.startswith("#b"):
            return BitVecNumRef(int(v[2:], 2), size)
        if v.startswith("#x"):
            return BitVecNumRef(int(v[2:], 16), size)
        try:
            return BitVecNumRef(int(v), size)
        except ValueError:
            return None
    if isinstance(v, list) and len(v) == 3 and v[0] == "_":
        # (_ bvN size)
        bv_str = v[1]
        if isinstance(bv_str, str) and bv_str.startswith("bv"):
            try:
                return BitVecNumRef(int(bv_str[2:]), size)
            except ValueError:
                pass
    return None


def _parse_func_interp(value_sexpr, sort_sexpr) -> FuncInterp | None:
    """Parse a function interpretation from an ite-chain or simple value."""
    entries: list[FuncInterpEntry] = []
    else_val = _interpret_value(value_sexpr, sort_sexpr)

    # For now, just store the else value (full ite parsing is complex)
    # Future: parse (ite (= x!0 val) result (ite ...)) chains
    if else_val is not None:
        return FuncInterp(entries, else_val)
    return FuncInterp(entries, None)


def _parse_int_value(v) -> IntNumRef | None:
    """Parse an integer value from S-expression."""
    if isinstance(v, str):
        try:
            return IntNumRef(int(v))
        except ValueError:
            return None
    if isinstance(v, list) and len(v) == 2 and v[0] == "-":
        try:
            return IntNumRef(-int(v[1]))
        except (ValueError, TypeError):
            return None
    return None


def _parse_real_value(v) -> RatNumRef | None:
    """Parse a real/rational value from S-expression."""
    if isinstance(v, str):
        # Could be "1.0" or just "1"
        try:
            if "." in v:
                from fractions import Fraction
                f = Fraction(v)
                return RatNumRef(f.numerator, f.denominator)
            return RatNumRef(int(v))
        except (ValueError, ZeroDivisionError):
            return None
    if isinstance(v, list):
        if len(v) == 3 and v[0] == "/":
            # (/ num den)
            num = _extract_int(v[1])
            den = _extract_int(v[2])
            if num is not None and den is not None:
                return RatNumRef(num, den)
        if len(v) == 2 and v[0] == "-":
            inner = _parse_real_value(v[1])
            if inner is not None:
                return RatNumRef(-inner._num, inner._den)
    return None


def _parse_bool_value(v) -> BoolValRef | None:
    if isinstance(v, str):
        if v == "true":
            return BoolValRef(True)
        if v == "false":
            return BoolValRef(False)
    return None


def _extract_int(v) -> int | None:
    """Extract an integer from an S-expression atom or (- N)."""
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            # Handle decimal like "1.0"
            try:
                f = float(v)
                if f == int(f):
                    return int(f)
            except ValueError:
                pass
            return None
    if isinstance(v, list) and len(v) == 2 and v[0] == "-":
        n = _extract_int(v[1])
        if n is not None:
            return -n
    return None
