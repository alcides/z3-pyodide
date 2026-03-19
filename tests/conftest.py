"""Test configuration and fixtures."""

import pytest
from z3_pyodide._context import reset_default_context


@pytest.fixture(autouse=True)
def clean_context():
    """Reset the default context between tests."""
    yield
    reset_default_context()
