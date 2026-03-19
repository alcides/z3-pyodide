"""SMT-LIB2 serializer: converts AST expressions to SMT-LIB2 text."""

from __future__ import annotations

from ._exprs import ExprRef


def collect_declarations(expr: ExprRef, declared: set[str]) -> list[str]:
    """Collect all variable declarations needed for an expression.

    Returns a list of SMT-LIB2 declaration commands for undeclared symbols.
    Handles both constants (declare-const) and uninterpreted functions (declare-fun).
    """
    decls: list[str] = []
    _collect_decls_recursive(expr, declared, decls)
    return decls


def _collect_decls_recursive(expr: ExprRef, declared: set[str],
                              decls: list[str]) -> None:
    from ._functions import _FuncAppMixin, QuantifierRef

    # Handle function applications: declare the function
    if isinstance(expr, _FuncAppMixin):
        func = expr._func
        if func.name() not in declared:
            declared.add(func.name())
            decls.append(func.smtlib2_declare())
        # Also collect declarations from the function arguments
        for child in expr._children:
            _collect_decls_recursive(child, declared, decls)
        return

    # Handle quantifiers: don't declare bound variables
    if isinstance(expr, QuantifierRef):
        # The bound variables should NOT be declared as constants
        bound_names = {v._smtlib_name for v in expr._vars}
        # Temporarily mark them as declared
        was_declared = {n for n in bound_names if n in declared}
        declared.update(bound_names)
        _collect_decls_recursive(expr._body, declared, decls)
        # Restore: remove names that weren't previously declared
        for n in bound_names - was_declared:
            declared.discard(n)
        return

    # Always ensure the sort is declared (for datatypes, arrays of datatypes, etc.)
    _ensure_sort_declared(expr._sort, declared, decls)

    if expr.is_leaf() and expr._smtlib_name and expr._op == "":
        name = expr._smtlib_name
        # Skip literals (numbers, true/false)
        if _is_literal(name):
            return
        # Skip datatype constructor names (they're declared via declare-datatypes)
        if _is_datatype_constructor(name):
            return
        if name not in declared:
            declared.add(name)
            sort_str = expr._sort.sexpr()
            decls.append(f"(declare-const {name} {sort_str})")
    for child in expr._children:
        _collect_decls_recursive(child, declared, decls)


def _is_literal(name: str) -> bool:
    """Check if a name is a literal value (not a variable)."""
    if name in ("true", "false"):
        return True
    # Negative number: (- N), rational (/ N D)
    if name.startswith("(- ") or name.startswith("(/ "):
        return True
    # BitVector literal: (_ bvN M)
    if name.startswith("(_ bv"):
        return True
    # Hex/binary bitvector literals
    if name.startswith("#b") or name.startswith("#x"):
        return True
    # Positive integer or decimal
    try:
        int(name)
        return True
    except ValueError:
        pass
    try:
        float(name)
        return True
    except ValueError:
        pass
    return False


def _is_datatype_constructor(name: str) -> bool:
    """Check if a name is a datatype constructor (not a variable)."""
    # Datatype constructors are declared via declare-datatypes,
    # not declare-const. We detect them by checking if the name
    # starts with "(_ is " (recognizer).
    if name.startswith("(_ is "):
        return True
    return False


def _ensure_sort_declared(sort, declared: set[str], decls: list[str]) -> None:
    """Ensure that any datatype sorts are declared before use."""
    from ._datatypes import DatatypeSortRef
    from ._sorts import ArraySortRef

    if isinstance(sort, DatatypeSortRef):
        dt_key = f"__dt__{sort.name()}"
        if dt_key not in declared:
            declared.add(dt_key)
            if hasattr(sort, '_smtlib2_declare'):
                decls.append(sort._smtlib2_declare)
    elif isinstance(sort, ArraySortRef):
        _ensure_sort_declared(sort.domain(), declared, decls)
        _ensure_sort_declared(sort.range(), declared, decls)


def expr_to_smtlib2(expr: ExprRef) -> str:
    """Convert an expression to its SMT-LIB2 string representation."""
    return expr.sexpr()
