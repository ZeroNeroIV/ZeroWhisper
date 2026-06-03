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

# Must import database helpers before the app to avoid circular issues
from app.database import initialize_engine, _db_manager

# Attempt to import SQLCipher; skip gracefully if unavailable.
try:
    from app.main import app
    from app.database import get_session
    _SQLCIPHER_AVAILABLE = True
except Exception as _import_exc:
    _SQLCIPHER_AVAILABLE = False
    _import_exc_msg = str(_import_exc)

TEST_KEY = "testkey123"

pytestmark = pytest.mark.skipif(
    not _SQLCIPHER_AVAILABLE,
    reason="pysqlcipher3 / SQLCipher not available in this environment",
)


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh encrypted test database for each test."""
    if not _SQLCIPHER_AVAILABLE:
        pytest.skip("SQLCipher not available")

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    # Remove so SQLCipher creates it fresh
    os.unlink(db_path)

    initialize_engine(db_path, TEST_KEY)

    yield db_path

    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def client(test_db):
    """TestClient with overridden session dependency."""
    if not _SQLCIPHER_AVAILABLE:
        pytest.skip("SQLCipher not available")

    from app.main import app
    from app.database import get_session

    def get_test_session():
        for session in _db_manager.get_session():
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app, raise_server_exceptions=True) as c:
        # Sync Container vault state with test DB state so the
        # setup-guard middleware doesn't block requests
        from app.main import _CONTAINER
        if _CONTAINER:
            _CONTAINER.vault_manager._active_vault_id = "test"
            _CONTAINER.vault_manager._current_key = TEST_KEY
            _CONTAINER.vault_manager._db_ready = True
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register a test user and return Bearer auth headers."""
    client.post("/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
    })
    resp = client.post("/auth/login", json={
        "username": "testuser",
        "password": "testpass123",
    })
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
