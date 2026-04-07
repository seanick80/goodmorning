"""Root-level pytest configuration and shared fixtures."""

import socket

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Fail fast if the database is unreachable."""
    import django
    from django.conf import settings

    django.setup()
    db = settings.DATABASES["default"]
    host = db.get("HOST", "localhost") or "localhost"
    port = int(db.get("PORT", 5432) or 5432)

    if db["ENGINE"] == "django.db.backends.postgresql":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        try:
            sock.connect((host, port))
        except (ConnectionRefusedError, socket.timeout, OSError):
            pytest.exit(
                f"PostgreSQL is not reachable at {host}:{port}. "
                "Start it with: ./deploy.sh --services",
                returncode=1,
            )
        finally:
            sock.close()


@pytest.fixture(autouse=True)
def _use_db(db):
    """Ensure all tests have database access by default."""
