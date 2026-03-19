"""Subprocess backend: communicates with a local z3 binary via stdin/stdout."""

from __future__ import annotations

import subprocess
import shutil

from ._base import Backend


class SubprocessBackend(Backend):
    """Backend that communicates with a local z3 binary.

    Spawns `z3 -in` as a subprocess and sends SMT-LIB2 commands
    via stdin, reading results from stdout.
    """

    _process: subprocess.Popen | None

    def __init__(self, z3_path: str | None = None):
        if z3_path is None:
            z3_path = shutil.which("z3")
            if z3_path is None:
                # Try to find z3 from z3-solver Python package
                z3_path = self._find_z3_from_package()
            if z3_path is None:
                raise RuntimeError(
                    "z3 binary not found. Install z3-solver: pip install z3-solver"
                )
        self._z3_path = z3_path
        self._process = None

    def _find_z3_from_package(self) -> str | None:
        """Try to find the z3 binary from the z3-solver Python package."""
        try:
            import z3
            import os
            z3_dir = os.path.dirname(z3.__file__)
            # z3-solver installs the binary alongside the Python package
            for name in ("z3", "z3.exe"):
                candidate = os.path.join(z3_dir, "lib", name)
                if os.path.isfile(candidate):
                    return candidate
            # Also check parent bin
            parent = os.path.dirname(z3_dir)
            for name in ("z3", "z3.exe"):
                candidate = os.path.join(parent, "bin", name)
                if os.path.isfile(candidate):
                    return candidate
        except ImportError:
            pass
        return None

    def _ensure_process(self) -> subprocess.Popen:
        if self._process is None or self._process.poll() is not None:
            self._process = subprocess.Popen(
                [self._z3_path, "-in"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        return self._process

    def eval_smtlib2(self, commands: str) -> str:
        """Send SMT-LIB2 commands and return the output.

        Uses echo sentinel to delimit responses.
        """
        proc = self._ensure_process()
        assert proc.stdin is not None
        assert proc.stdout is not None

        sentinel = "---Z3_PYODIDE_END---"
        full_input = commands.strip() + f'\n(echo "{sentinel}")\n'
        proc.stdin.write(full_input)
        proc.stdin.flush()

        lines: list[str] = []
        while True:
            line = proc.stdout.readline()
            if not line:
                break
            line = line.rstrip("\n")
            if line == sentinel:
                break
            lines.append(line)

        return "\n".join(lines)

    def reset(self) -> None:
        """Reset by sending (reset) command."""
        if self._process is not None and self._process.poll() is None:
            self.eval_smtlib2("(reset)")

    def close(self) -> None:
        """Terminate the z3 subprocess."""
        if self._process is not None:
            try:
                if self._process.poll() is None:
                    self._process.stdin.write("(exit)\n")
                    self._process.stdin.flush()
                    self._process.wait(timeout=5)
            except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
                self._process.kill()
            finally:
                self._process = None
