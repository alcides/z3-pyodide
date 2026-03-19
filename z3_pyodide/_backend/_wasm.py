"""WASM backend: communicates with z3-solver npm package via Pyodide JS interop."""

from __future__ import annotations

from ._base import Backend


class WasmBackend(Backend):
    """Backend that communicates with Z3 via the z3-solver npm WASM build.

    Uses Pyodide's JavaScript interop to call the z3-solver npm package's
    low-level API (Z3.eval_smtlib2_string).

    Requirements:
    - Running in Pyodide environment
    - z3-solver npm package initialized and exposed via globalThis.__z3_low_level
    - SharedArrayBuffer available (requires COOP/COEP headers)

    The host HTML page should initialize z3-solver and expose the low-level API:

        const { Z3 } = await init();
        const cfg = Z3.mk_config();
        const ctx = Z3.mk_context(cfg);
        Z3.del_config(cfg);
        globalThis.__z3_low_level = Z3;
        globalThis.__z3_context = ctx;

    Alternatively, set globalThis.__z3_init to the init function and the backend
    will call it (requires JSPI / run_sync support).
    """

    def __init__(self):
        self._z3 = None  # Low-level Z3 API object
        self._ctx_handle = None  # Z3_context handle
        self._initialized = False

    def _ensure_init(self) -> None:
        """Lazily initialize the Z3 WASM module."""
        if self._initialized:
            return

        try:
            import js  # type: ignore[import-not-found]
        except ImportError:
            raise RuntimeError(
                "WasmBackend requires Pyodide. "
                "Use SubprocessBackend for non-browser environments."
            )

        # Option 1: Pre-initialized Z3 exposed by the host page (recommended)
        z3_api = getattr(js.globalThis, "__z3_low_level", None)
        z3_ctx = getattr(js.globalThis, "__z3_context", None)

        if z3_api is not None and z3_ctx is not None:
            self._z3 = z3_api
            self._ctx_handle = z3_ctx
            self._initialized = True
            return

        # Option 2: Host page provides init function, use run_sync (needs JSPI)
        init_func = getattr(js.globalThis, "__z3_init", None)
        if init_func is not None:
            try:
                from pyodide.ffi import run_sync  # type: ignore[import-not-found]
                result = run_sync(init_func())
                self._z3 = result.Z3
                cfg = self._z3.mk_config()
                self._ctx_handle = self._z3.mk_context(cfg)
                self._z3.del_config(cfg)
                self._initialized = True
                return
            except ImportError:
                pass

        raise RuntimeError(
            "Z3 WASM not initialized. The host page must initialize z3-solver "
            "and set globalThis.__z3_low_level and globalThis.__z3_context "
            "before using z3_pyodide."
        )

    def eval_smtlib2(self, commands: str) -> str:
        """Send SMT-LIB2 commands to Z3 WASM and return the output."""
        self._ensure_init()
        return str(self._z3.eval_smtlib2_string(self._ctx_handle, commands))

    def reset(self) -> None:
        """Reset by sending (reset) command."""
        if self._initialized:
            self.eval_smtlib2("(reset)")

    def close(self) -> None:
        """Release Z3 context resources."""
        if self._initialized and self._ctx_handle is not None:
            try:
                self._z3.del_context(self._ctx_handle)
            except Exception:
                pass
            self._ctx_handle = None
            self._initialized = False
