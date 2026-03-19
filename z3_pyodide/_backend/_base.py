"""Abstract backend interface for Z3 communication."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Backend(ABC):
    """Abstract base class for Z3 backends.

    A backend handles sending SMT-LIB2 commands to a Z3 instance
    and returning the output.
    """

    @abstractmethod
    def eval_smtlib2(self, commands: str) -> str:
        """Send SMT-LIB2 commands and return the output string.

        The commands string may contain multiple SMT-LIB2 commands
        separated by newlines. The return value is the concatenated
        output from Z3.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset the solver state."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Release resources."""
        ...

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
