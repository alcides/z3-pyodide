"""Solver class: orchestrates SMT-LIB2 generation and backend communication."""

from __future__ import annotations

import itertools

from ._context import Context, get_default_context
from ._exprs import ExprRef, BoolRef, ArithRef
from ._smtlib2 import collect_declarations
from ._model import ModelRef
from ._model_parser import parse_model_string
from ._sexpr_parser import parse_sexpr

_named_counter = itertools.count()


class CheckSatResult:
    """Represents sat, unsat, or unknown."""

    _value: str

    def __init__(self, value: str):
        self._value = value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, CheckSatResult):
            return self._value == other._value
        return NotImplemented

    def __ne__(self, other: object) -> bool:
        if isinstance(other, CheckSatResult):
            return self._value != other._value
        return NotImplemented

    def __bool__(self) -> bool:
        return self._value == "sat"

    def __repr__(self) -> str:
        return self._value

    def __str__(self) -> str:
        return self._value

    def __hash__(self) -> int:
        return hash(self._value)


sat = CheckSatResult("sat")
unsat = CheckSatResult("unsat")
unknown = CheckSatResult("unknown")


class Solver:
    """Z3 Solver that generates SMT-LIB2 and communicates via a backend."""

    def __init__(self, ctx: Context | None = None):
        self._ctx = ctx or get_default_context()
        self._assertions: list[BoolRef] = []
        self._assertion_names: list[str | None] = []  # for unsat cores
        self._declared: set[str] = set()
        self._stack: list[int] = []  # push/pop: saved assertion counts
        self._last_result: CheckSatResult | None = None
        self._last_model: ModelRef | None = None
        self._unsat_core_enabled: bool = False
        # Each solver gets a fresh backend for isolation
        self._backend = self._ctx.backend()

    def add(self, *args: BoolRef) -> None:
        """Add constraints to the solver."""
        for arg in args:
            if not isinstance(arg, ExprRef):
                from ._exprs import _coerce_bool
                arg = _coerce_bool(arg)
            self._assertions.append(arg)
            self._assertion_names.append(None)
        self._last_result = None
        self._last_model = None

    def assert_and_track(self, constraint: BoolRef, name: BoolRef) -> None:
        """Add a named constraint for unsat core tracking.

        The name should be a Bool variable used to track this assertion.
        """
        self._unsat_core_enabled = True
        if not isinstance(constraint, ExprRef):
            from ._exprs import _coerce_bool
            constraint = _coerce_bool(constraint)
        track_name = name._smtlib_name if isinstance(name, ExprRef) else str(name)
        self._assertions.append(constraint)
        self._assertion_names.append(track_name)
        self._last_result = None
        self._last_model = None

    def check(self, *assumptions: BoolRef) -> CheckSatResult:
        """Check satisfiability of the current assertions."""
        commands: list[str] = []

        # Reset backend state for a fresh check
        commands.append("(reset)")

        if self._unsat_core_enabled:
            commands.append("(set-option :produce-unsat-cores true)")

        # Collect all declarations from all assertions
        for assertion in self._assertions:
            decls = collect_declarations(assertion, self._declared)
            commands.extend(decls)

        # Mark tracking names as declared so they don't get declare-const
        for name in self._assertion_names:
            if name is not None:
                self._declared.add(name)

        # Add all assertions
        for assertion, name in zip(self._assertions, self._assertion_names):
            if name is not None:
                commands.append(f"(assert (! {assertion.sexpr()} :named {name}))")
            else:
                commands.append(f"(assert {assertion.sexpr()})")

        if assumptions:
            # Declare assumption variables
            for a in assumptions:
                decls = collect_declarations(a, self._declared)
                commands.extend(decls)
            assumption_str = " ".join(a.sexpr() for a in assumptions)
            commands.append(f"(check-sat-assuming ({assumption_str}))")
        else:
            commands.append("(check-sat)")

        # Eagerly request model/unsat-core so everything is in one backend call.
        # This is essential for backends where each call is a fresh Z3 instance
        # (e.g., the single-threaded WASM build).
        commands.append("(get-model)")
        if self._unsat_core_enabled:
            commands.append("(get-unsat-core)")

        command_str = "\n".join(commands)
        result = self._backend.eval_smtlib2(command_str)

        # Parse the result: first line is sat/unsat/unknown,
        # then (model ...) or (error ...), then optionally unsat core
        lines = result.strip()
        first_line_end = lines.find("\n")
        if first_line_end == -1:
            result_line = lines.strip()
            rest = ""
        else:
            result_line = lines[:first_line_end].strip()
            rest = lines[first_line_end + 1:]

        if result_line == "sat":
            self._last_result = sat
        elif result_line == "unsat":
            self._last_result = unsat
        else:
            self._last_result = unknown

        self._last_model = None
        self._last_unsat_core = None

        if self._last_result == sat and rest:
            # Parse model from the remaining output
            self._last_model = ModelRef(parse_model_string(rest))
        elif self._last_result == unsat and self._unsat_core_enabled and rest:
            # Parse unsat core from remaining output
            # Skip any error lines (e.g., from get-model failing)
            for line in rest.split("\n"):
                line = line.strip()
                if line.startswith("(") and not line.startswith("(error"):
                    parsed = parse_sexpr(line)
                    if isinstance(parsed, list):
                        self._last_unsat_core = [str(x) for x in parsed]
                    elif isinstance(parsed, str) and parsed:
                        self._last_unsat_core = [parsed]
                    break

        return self._last_result

    def model(self) -> ModelRef:
        """Get the model from the last satisfiable check.

        Must be called after check() returns sat.
        """
        if self._last_result != sat:
            raise RuntimeError("Cannot get model: last check was not sat")

        if self._last_model is not None:
            return self._last_model

        # Fallback: try a separate call (works with persistent backends like subprocess)
        result = self._backend.eval_smtlib2("(get-model)")
        self._last_model = ModelRef(parse_model_string(result))
        return self._last_model

    def unsat_core(self) -> list[str]:
        """Get the unsat core from the last unsatisfiable check.

        Returns a list of assertion names that form the unsat core.
        Must be called after check() returns unsat with tracked assertions.
        """
        if self._last_result != unsat:
            raise RuntimeError("Cannot get unsat core: last check was not unsat")

        if self._last_unsat_core is not None:
            return self._last_unsat_core

        # Fallback: try a separate call
        result = self._backend.eval_smtlib2("(get-unsat-core)")
        parsed = parse_sexpr(result.strip())
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
        if isinstance(parsed, str) and parsed:
            return [parsed]
        return []

    def push(self) -> None:
        """Create a backtracking point."""
        self._stack.append(len(self._assertions))

    def pop(self, n: int = 1) -> None:
        """Backtrack n levels."""
        for _ in range(n):
            if not self._stack:
                raise RuntimeError("Cannot pop: no push on stack")
            count = self._stack.pop()
            self._assertions = self._assertions[:count]
            self._assertion_names = self._assertion_names[:count]
        self._last_result = None
        self._last_model = None
        # Reset declared set since we reset on each check anyway
        self._declared.clear()

    def reset(self) -> None:
        """Reset the solver to its initial state."""
        self._assertions.clear()
        self._assertion_names.clear()
        self._stack.clear()
        self._declared.clear()
        self._last_result = None
        self._last_model = None
        self._unsat_core_enabled = False

    def assertions(self) -> list[BoolRef]:
        """Return the current list of assertions."""
        return list(self._assertions)

    def num_assertions(self) -> int:
        return len(self._assertions)

    def sexpr(self) -> str:
        """Return the SMT-LIB2 representation of the solver state."""
        commands: list[str] = []
        declared: set[str] = set()
        for assertion in self._assertions:
            decls = collect_declarations(assertion, declared)
            commands.extend(decls)
            commands.append(f"(assert {assertion.sexpr()})")
        return "\n".join(commands)

    def __repr__(self) -> str:
        return self.sexpr()

    def set(self, **kwargs) -> None:
        """Set solver options (e.g., timeout)."""
        for key, value in kwargs.items():
            key_smt = key.replace("_", ".")
            if isinstance(value, bool):
                val_str = "true" if value else "false"
            else:
                val_str = str(value)
            self._backend.eval_smtlib2(f"(set-option :{key_smt} {val_str})")

    def reason_unknown(self) -> str:
        """Get the reason for the last 'unknown' result."""
        if self._last_result != unknown:
            return ""
        result = self._backend.eval_smtlib2("(get-info :reason-unknown)")
        return result.strip()


class Optimize:
    """Z3 Optimizer: extends Solver with minimize/maximize objectives."""

    def __init__(self, ctx: Context | None = None):
        self._ctx = ctx or get_default_context()
        self._assertions: list[BoolRef] = []
        self._declared: set[str] = set()
        self._objectives: list[tuple[str, ExprRef]] = []  # ("minimize"|"maximize", expr)
        self._last_result: CheckSatResult | None = None
        self._last_model: ModelRef | None = None
        self._backend = self._ctx.backend()

    def add(self, *args: BoolRef) -> None:
        """Add constraints to the optimizer."""
        for arg in args:
            if not isinstance(arg, ExprRef):
                from ._exprs import _coerce_bool
                arg = _coerce_bool(arg)
            self._assertions.append(arg)
        self._last_result = None
        self._last_model = None

    def minimize(self, expr: ExprRef) -> OptimizeObjective:
        """Add a minimization objective."""
        obj = OptimizeObjective("minimize", expr, len(self._objectives))
        self._objectives.append(("minimize", expr))
        return obj

    def maximize(self, expr: ExprRef) -> OptimizeObjective:
        """Add a maximization objective."""
        obj = OptimizeObjective("maximize", expr, len(self._objectives))
        self._objectives.append(("maximize", expr))
        return obj

    def check(self) -> CheckSatResult:
        """Check satisfiability and optimize objectives."""
        commands: list[str] = []
        commands.append("(reset)")

        # Collect declarations
        for assertion in self._assertions:
            decls = collect_declarations(assertion, self._declared)
            commands.extend(decls)
        for _, expr in self._objectives:
            decls = collect_declarations(expr, self._declared)
            commands.extend(decls)

        # Add assertions
        for assertion in self._assertions:
            commands.append(f"(assert {assertion.sexpr()})")

        # Add objectives
        for kind, expr in self._objectives:
            commands.append(f"({kind} {expr.sexpr()})")

        commands.append("(check-sat)")
        commands.append("(get-model)")

        command_str = "\n".join(commands)
        result = self._backend.eval_smtlib2(command_str)

        lines = result.strip()
        first_line_end = lines.find("\n")
        if first_line_end == -1:
            result_line = lines.strip()
            rest = ""
        else:
            result_line = lines[:first_line_end].strip()
            rest = lines[first_line_end + 1:]

        if result_line == "sat":
            self._last_result = sat
        elif result_line == "unsat":
            self._last_result = unsat
        else:
            self._last_result = unknown

        self._last_model = None
        if self._last_result == sat and rest:
            self._last_model = ModelRef(parse_model_string(rest))

        return self._last_result

    def model(self) -> ModelRef:
        """Get the optimized model."""
        if self._last_result != sat:
            raise RuntimeError("Cannot get model: last check was not sat")

        if self._last_model is not None:
            return self._last_model

        result = self._backend.eval_smtlib2("(get-model)")
        self._last_model = ModelRef(parse_model_string(result))
        return self._last_model

    def sexpr(self) -> str:
        """Return the SMT-LIB2 representation."""
        commands: list[str] = []
        declared: set[str] = set()
        for assertion in self._assertions:
            decls = collect_declarations(assertion, declared)
            commands.extend(decls)
            commands.append(f"(assert {assertion.sexpr()})")
        for kind, expr in self._objectives:
            commands.append(f"({kind} {expr.sexpr()})")
        return "\n".join(commands)

    def __repr__(self) -> str:
        return self.sexpr()


class OptimizeObjective:
    """Handle for an optimization objective."""

    def __init__(self, kind: str, expr: ExprRef, index: int):
        self._kind = kind
        self._expr = expr
        self._index = index

    def value(self) -> ExprRef:
        """Return the expression being optimized."""
        return self._expr

    def __repr__(self) -> str:
        return f"{self._kind}({self._expr.sexpr()})"


def simplify(expr: ExprRef) -> ExprRef:
    """Simplify an expression using Z3.

    Sends the expression to Z3 via (simplify ...) and parses the result.
    Note: returns the original expression if simplification fails,
    since parsing simplified results back to AST is complex.
    """
    from ._context import get_default_context
    backend = get_default_context().backend()

    commands: list[str] = ["(reset)"]
    declared: set[str] = set()
    decls = collect_declarations(expr, declared)
    commands.extend(decls)
    commands.append(f"(simplify {expr.sexpr()})")

    result = backend.eval_smtlib2("\n".join(commands))
    result = result.strip()

    # Try to parse the result back
    if not result:
        return expr

    # For simple cases, return the appropriate literal
    from ._exprs import IntNumRef, BoolValRef, RatNumRef, BitVecNumRef
    from ._sorts import ArithSortRef, BoolSortRef, BitVecSortRef

    if result == "true":
        return BoolValRef(True)
    if result == "false":
        return BoolValRef(False)

    try:
        val = int(result)
        if isinstance(expr._sort, BoolSortRef):
            return expr
        if isinstance(expr._sort, ArithSortRef):
            if expr._sort.name() == "Real":
                return RatNumRef(val)
            return IntNumRef(val)
        return IntNumRef(val)
    except ValueError:
        pass

    # For complex results, return original (full parsing is complex)
    return expr
