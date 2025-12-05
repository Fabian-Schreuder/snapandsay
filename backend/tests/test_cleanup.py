import os
import tomllib
import pytest
import subprocess

def test_fastapi_users_removed():
    """Verify fastapi-users is not in dependencies and not used in code."""
    # Check pyproject.toml
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    
    deps = pyproject.get("project", {}).get("dependencies", [])
    for dep in deps:
        assert "fastapi-users" not in dep, "fastapi-users should not be in dependencies"

    # Check codebase for imports
    # We use grep via subprocess to be thorough
    result = subprocess.run(
        ["grep", "-r", "fastapi_users", "."], 
        capture_output=True, 
        text=True
    )
    # The grep should fail (return non-zero) or return empty string
    # grep returns 0 if match found, 1 if no match.
    # We WANT it to return 1 (no match).
    # However, this test file itself contains "fastapi_users", so we need to exclude it.
    
    matches = result.stdout.splitlines()
    filtered_matches = [m for m in matches if "test_cleanup.py" not in m]
    
    assert len(filtered_matches) == 0, f"Found traces of fastapi-users: {filtered_matches}"

def test_alembic_removed():
    """Verify alembic is removed from dev dependencies and config."""
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    
    dev_deps = pyproject.get("dependency-groups", {}).get("dev", [])
    for dep in dev_deps:
        assert "alembic" not in dep, "alembic should not be in dev-dependencies"

    assert not os.path.exists("alembic.ini"), "alembic.ini should be removed"
    assert not os.path.exists("migrations"), "migrations folder should be removed"
