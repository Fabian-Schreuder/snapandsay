import os

import pytest


def test_directories_exist():
    """Verify backend structure exists."""
    dirs = [
        "app/agent",
        "app/services",
        "app/core",
        "app/db"
    ]
    for d in dirs:
        assert os.path.exists(d), f"Directory {d} should exist"
        init_file = os.path.join(d, "__init__.py")
        assert os.path.exists(init_file), f"{d}/__init__.py should exist"

def test_langgraph_installed():
    """Verify langgraph is installed."""
    try:
        import langgraph
        assert langgraph is not None
    except ImportError:
        pytest.fail("langgraph not installed")
