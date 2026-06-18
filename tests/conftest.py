"""Shared pytest fixtures for the EX04 test suite."""

import pytest


@pytest.fixture
def sample_python_source():
    """Minimal valid Python source for parser tests."""
    return "def hello():\n    pass\n"


@pytest.fixture
def broken_python_source():
    """Python 2 source that triggers SyntaxError under Python 3."""
    return 'print "hello"\nif x = 1:\n    pass\n'
