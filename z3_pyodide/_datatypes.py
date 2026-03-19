"""Algebraic datatype declarations."""

from __future__ import annotations

from ._ast import SortRef
from ._exprs import ExprRef, BoolRef, DatatypeRef, _make_expr_for_sort


class DatatypeSortRef(SortRef):
    """Sort reference for a declared datatype."""

    _type_name: str
    _constructors: list[_ConstructorDecl]

    def __init__(self, name: str, constructors: list[_ConstructorDecl] | None = None, ctx=None):
        super().__init__(ctx)
        self._type_name = name
        self._constructors = constructors or []

    def name(self) -> str:
        return self._type_name

    def sexpr(self) -> str:
        return self._type_name

    def num_constructors(self) -> int:
        return len(self._constructors)

    def constructor(self, i: int) -> _ConstructorDecl:
        return self._constructors[i]


class _ConstructorDecl:
    """A constructor for a datatype."""

    def __init__(self, name: str, accessors: list[tuple[str, SortRef | str]]):
        self._name = name
        self._accessors = accessors  # list of (accessor_name, sort_or_self_ref)

    def name(self) -> str:
        return self._name


class _ConstructorFunc:
    """Callable constructor for creating datatype values."""

    def __init__(self, name: str, sort: DatatypeSortRef,
                 accessors: list[tuple[str, SortRef]]):
        self._name = name
        self._sort = sort
        self._accessors = accessors

    def __call__(self, *args) -> DatatypeRef:
        from ._exprs import _coerce
        if len(args) != len(self._accessors):
            raise ValueError(
                f"Constructor '{self._name}' expects {len(self._accessors)} "
                f"arguments, got {len(args)}"
            )
        coerced = tuple(
            _coerce(a, acc_sort) if not isinstance(a, ExprRef) else a
            for a, (_, acc_sort) in zip(args, self._accessors)
        )
        if len(coerced) == 0:
            return DatatypeRef(self._sort, smtlib_name=self._name)
        return DatatypeRef(self._sort, self._name, coerced)

    def __repr__(self) -> str:
        return self._name


class _AccessorFunc:
    """Callable accessor for extracting fields from datatype values."""

    def __init__(self, name: str, result_sort: SortRef):
        self._name = name
        self._result_sort = result_sort

    def __call__(self, expr: ExprRef) -> ExprRef:
        return _make_expr_for_sort(self._result_sort, self._name, (expr,))

    def __repr__(self) -> str:
        return self._name


class _RecognizerFunc:
    """Callable recognizer (is-Constructor) for testing datatype values."""

    def __init__(self, name: str):
        self._name = name

    def __call__(self, expr: ExprRef) -> BoolRef:
        return BoolRef(op=self._name, children=(expr,))

    def __repr__(self) -> str:
        return self._name


class Datatype:
    """Builder for algebraic datatypes.

    Usage:
        Color = Datatype('Color')
        Color.declare('Red')
        Color.declare('Green')
        Color.declare('Blue')
        Color = Color.create()
        # Color is now a DatatypeSortRef
        # Color.Red, Color.Green, Color.Blue are constructors
    """

    def __init__(self, name: str):
        self._name = name
        self._constructors: list[tuple[str, list[tuple[str, SortRef | str]]]] = []

    def declare(self, name: str, *accessors: tuple[str, SortRef | str]) -> None:
        """Declare a constructor with optional accessors.

        Each accessor is a (name, sort) pair.
        Use the datatype name as sort for recursive references.
        """
        self._constructors.append((name, list(accessors)))

    def create(self) -> DatatypeSortRef:
        """Create the datatype sort. Returns a DatatypeSortRef with constructors."""
        return CreateDatatypes(self)[0]


def CreateDatatypes(*datatypes: Datatype) -> tuple[DatatypeSortRef, ...]:
    """Create one or more (possibly mutually recursive) datatypes.

    Returns a tuple of DatatypeSortRef, each enriched with:
    - Constructor functions as attributes (e.g., sort.Cons, sort.Nil)
    - Accessor functions as attributes (e.g., sort.head, sort.tail)
    - Recognizer functions as attributes (e.g., sort.is_Cons, sort.is_Nil)

    Also generates the SMT-LIB2 declare-datatypes command.
    """
    # First pass: create sort refs
    sorts: list[DatatypeSortRef] = []
    sort_map: dict[str, DatatypeSortRef] = {}
    for dt in datatypes:
        s = DatatypeSortRef(dt._name)
        sorts.append(s)
        sort_map[dt._name] = s

    # Second pass: resolve sort references and build constructors
    for dt, sort_ref in zip(datatypes, sorts):
        constructor_decls = []
        for cname, accessors in dt._constructors:
            resolved_accessors: list[tuple[str, SortRef]] = []
            for acc_name, acc_sort in accessors:
                if isinstance(acc_sort, str):
                    if acc_sort in sort_map:
                        resolved_accessors.append((acc_name, sort_map[acc_sort]))
                    else:
                        raise ValueError(f"Unknown sort: {acc_sort}")
                else:
                    resolved_accessors.append((acc_name, acc_sort))

            cdecl = _ConstructorDecl(cname, resolved_accessors)
            constructor_decls.append(cdecl)

            # Attach constructor function
            setattr(sort_ref, cname, _ConstructorFunc(cname, sort_ref, resolved_accessors))

            # Attach recognizer
            setattr(sort_ref, f"is_{cname}", _RecognizerFunc(f"(_ is {cname})"))

            # Attach accessor functions
            for acc_name, acc_sort in resolved_accessors:
                setattr(sort_ref, acc_name, _AccessorFunc(acc_name, acc_sort))

        sort_ref._constructors = constructor_decls

    # Build SMT-LIB2 declaration and store it on each sort
    smtlib = _build_declare_datatypes(datatypes, sorts)
    for s in sorts:
        s._smtlib2_declare = smtlib

    return tuple(sorts)


def _build_declare_datatypes(datatypes: tuple[Datatype, ...],
                              sorts: list[DatatypeSortRef]) -> str:
    """Build the (declare-datatypes ...) SMT-LIB2 command."""
    if len(datatypes) == 1:
        dt = datatypes[0]
        sort = sorts[0]
        # Use declare-datatype (singular) for non-recursive simple case
        # But declare-datatypes works universally
        pass

    # (declare-datatypes ((Name1 0) (Name2 0)) ((cons1 ...) (cons2 ...)))
    sort_decls = " ".join(f"({dt._name} 0)" for dt in datatypes)
    bodies = []
    for dt in datatypes:
        constructors = []
        for cname, accessors in dt._constructors:
            if not accessors:
                constructors.append(f"({cname})")
            else:
                acc_str = " ".join(
                    f"({aname} {asort.sexpr() if isinstance(asort, SortRef) else asort})"
                    for aname, asort in accessors
                )
                constructors.append(f"({cname} {acc_str})")
        body = "(" + " ".join(constructors) + ")"
        bodies.append(body)

    return f"(declare-datatypes ({sort_decls}) ({' '.join(bodies)}))"
