"""Context management and backend auto-detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._backend._base import Backend


class Context:
    """Z3 context: manages a backend connection."""

    _backend: Backend | None

    def __init__(self, backend: Backend | None = None):
        self._backend = backend

    def backend(self) -> Backend:
        if self._backend is None:
            self._backend = _create_default_backend()
        return self._backend

    def close(self) -> None:
        if self._backend is not None:
            self._backend.close()
            self._backend = None


_default_context: Context | None = None


def get_default_context() -> Context:
    global _default_context
    if _default_context is None:
        _default_context = Context()
    return _default_context


def set_default_context(ctx: Context) -> None:
    global _default_context
    _default_context = ctx


def reset_default_context() -> None:
    global _default_context
    if _default_context is not None:
        _default_context.close()
    _default_context = None


def _create_default_backend() -> Backend:
    """Auto-detect and create the appropriate backend."""
    # Check if running in Pyodide
    try:
        import pyodide  # type: ignore[import-not-found]
        from ._backend._wasm import WasmBackend
        return WasmBackend()
    except ImportError:
        pass

    # Fall back to subprocess backend
    from ._backend._subprocess import SubprocessBackend
    return SubprocessBackend()
