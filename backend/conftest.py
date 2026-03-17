"""Root-level pytest configuration and shared fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _use_db(db):
    """Ensure all tests have database access by default."""
