"""Function declarations, uninterpreted functions, and quantifiers."""

from __future__ import annotations

from ._ast import SortRef
from ._exprs import ExprRef, BoolRef, ArithRef, Z3Exception


class FuncDeclRef:
    """Represents a function declaration (uninterpreted or interpreted)."""

    def __init__(self, name: str, domain: tuple[SortRef, ...], range_: SortRef):
        self._name = name
        self._domain = domain
        self._range = range_

    def name(self) -> str:
        return self._name

    def arity(self) -> int:
        return len(self._domain)

    def domain(self, i: int) -> SortRef:
        return self._domain[i]

    def range(self) -> SortRef:
        return self._range

    def __call__(self, *args) -> ExprRef:
        """Apply this function to arguments."""
        if len(args) != self.arity():
            raise Z3Exception(
                f"Function '{self._name}' expects {self.arity()} arguments, "
                f"got {len(args)}"
            )
        from ._exprs import _coerce
        coerced = tuple(
            _coerce(a, self._domain[i]) if not isinstance(a, ExprRef) else a
            for i, a in enumerate(args)
        )
        return _make_func_app(self, coerced)

    def sexpr(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return self._name

    def smtlib2_declare(self) -> str:
        """Return the SMT-LIB2 declaration for this function."""
        domain_str = " ".join(s.sexpr() for s in self._domain)
        return f"(declare-fun {self._name} ({domain_str}) {self._range.sexpr()})"


class _FuncAppMixin:
    """Mixin for function application expressions."""

    _func: FuncDeclRef
    _args: tuple[ExprRef, ...]

    def _init_func_app(self, func: FuncDeclRef, args: tuple[ExprRef, ...]):
        self._func = func
        self._args = args

    def decl(self) -> FuncDeclRef:
        return self._func

    def sexpr(self) -> str:
        if len(self._args) == 0:
            return self._func.name()
        arg_sexprs = " ".join(a.sexpr() for a in self._args)
        return f"({self._func.name()} {arg_sexprs})"


class _FuncAppRef(_FuncAppMixin, ExprRef):
    """Function application with generic sort."""

    def __init__(self, func: FuncDeclRef, args: tuple[ExprRef, ...]):
        ExprRef.__init__(self, sort=func.range(), op=func.name(), children=args)
        self._init_func_app(func, args)


class _FuncAppBoolRef(_FuncAppMixin, BoolRef):
    """Function application returning Bool."""

    def __init__(self, func: FuncDeclRef, args: tuple[ExprRef, ...]):
        BoolRef.__init__(self, op=func.name(), children=args)
        self._init_func_app(func, args)


class _FuncAppArithRef(_FuncAppMixin, ArithRef):
    """Function application returning Int or Real."""

    def __init__(self, func: FuncDeclRef, args: tuple[ExprRef, ...]):
        ArithRef.__init__(self, sort=func.range(), op=func.name(), children=args)
        self._init_func_app(func, args)


def _make_func_app(func: FuncDeclRef, args: tuple[ExprRef, ...]) -> ExprRef:
    """Create the appropriate FuncApp subclass based on range sort."""
    range_name = func.range().name()
    if range_name == "Bool":
        return _FuncAppBoolRef(func, args)
    if range_name in ("Int", "Real"):
        return _FuncAppArithRef(func, args)
    return _FuncAppRef(func, args)


def Function(name: str, *sig: SortRef) -> FuncDeclRef:
    """Create an uninterpreted function.

    The last argument is the range sort, the rest are domain sorts.

    Example:
        f = Function('f', IntSort(), IntSort(), BoolSort())
        # f: Int x Int -> Bool
    """
    if len(sig) < 2:
        raise Z3Exception(
            "Function requires at least 2 sort arguments "
            "(domain sorts + range sort)"
        )
    domain = tuple(sig[:-1])
    range_ = sig[-1]
    return FuncDeclRef(name, domain, range_)


# --- Quantifiers ---

class QuantifierRef(BoolRef):
    """Quantified expression (ForAll or Exists)."""

    _quantifier: str  # "forall" or "exists"
    _vars: tuple[ExprRef, ...]
    _body: ExprRef

    def __init__(self, quantifier: str, vars_: tuple[ExprRef, ...], body: ExprRef):
        super().__init__()
        self._quantifier = quantifier
        self._vars = vars_
        self._body = body

    def sexpr(self) -> str:
        bindings = " ".join(
            f"({v._smtlib_name} {v._sort.sexpr()})" for v in self._vars
        )
        return f"({self._quantifier} ({bindings}) {self._body.sexpr()})"

    def is_leaf(self) -> bool:
        return False


def ForAll(vs, body: ExprRef, **kwargs) -> QuantifierRef:
    """Universal quantifier.

    Usage:
        x = Int('x')
        ForAll(x, x > 0)
        # or
        ForAll([x, y], x + y > 0)
    """
    if isinstance(vs, ExprRef):
        vs = (vs,)
    elif isinstance(vs, list):
        vs = tuple(vs)
    return QuantifierRef("forall", vs, body)


def Exists(vs, body: ExprRef, **kwargs) -> QuantifierRef:
    """Existential quantifier.

    Usage:
        x = Int('x')
        Exists(x, x > 0)
        # or
        Exists([x, y], x + y > 0)
    """
    if isinstance(vs, ExprRef):
        vs = (vs,)
    elif isinstance(vs, list):
        vs = tuple(vs)
    return QuantifierRef("exists", vs, body)
