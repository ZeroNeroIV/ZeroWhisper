"""
Shared pytest fixtures for ZeroWhisper backend tests.

Each test function gets a fresh encrypted SQLite database via the `test_db`
fixture so there is no shared state between tests.
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Set a test JWT secret before importing app modules so the Settings
# model_validator does not reject the insecure default.
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing-only-32ch")

from app.infrastructure.database import DatabaseManager

# Attempt to import SQLCipher; skip gracefully if unavailable.
try:
    import pysqlcipher3.dbapi2  # noqa: F401
    _SQLCIPHER_AVAILABLE = True
except Exception:
    _SQLCIPHER_AVAILABLE = False

# Must be valid hex — DatabaseManager validates keys before PRAGMA interpolation.
TEST_KEY = "a1b2c3d4e5f60718293a4b5c6d7e8f90"

pytestmark = pytest.mark.skipif(
    not _SQLCIPHER_AVAILABLE,
    reason="pysqlcipher3 / SQLCipher not available in this environment",
)


@pytest.fixture(scope="function")
def test_db_manager():
    """A DatabaseManager bound to a fresh encrypted database file."""
    if not _SQLCIPHER_AVAILABLE:
        pytest.skip("SQLCipher not available")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    # Remove so SQLCipher creates it fresh
    os.unlink(db_path)

    manager = DatabaseManager(tempfile.gettempdir())
    manager.initialize_encrypted(db_path, TEST_KEY)

    yield manager

    manager.dispose()
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def test_db(test_db_manager):
    """Backward-compatible alias yielding the manager (tests use sessions off it)."""
    yield test_db_manager


@pytest.fixture(scope="function")
def client(test_db_manager):
    """TestClient with the app's session dependency pointed at the test DB."""
    from app.main import app
    from app.api import deps
    from app.core.ratelimit import auth_rate_limit

    def get_test_session():
        yield from test_db_manager.get_session()

    app.dependency_overrides[deps.get_session] = get_test_session
    # The sliding-window limiter is process-wide; a full suite run would
    # exhaust it and make later logins fail spuriously.
    app.dependency_overrides[auth_rate_limit] = lambda: None
    with TestClient(app, raise_server_exceptions=True) as c:
        # Mark the container's vault as unlocked so the setup-guard
        # middleware lets requests through, and report INITIALIZED to
        # /setup/status (get_state reads the on-disk vault registry,
        # which tests never create).
        container = app.state.container
        container.vault_manager._active_vault_id = "test"
        container.vault_manager._current_key = TEST_KEY
        container.vault_manager._db_ready = True
        original_get_state = container.vault_manager.get_state
        container.vault_manager.get_state = lambda: "INITIALIZED"
        try:
            yield c
        finally:
            container.vault_manager.get_state = original_get_state
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register a test user and return Bearer auth headers."""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "password_confirm": "testpass123",
    })
    resp = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
