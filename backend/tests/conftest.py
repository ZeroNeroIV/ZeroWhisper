"""
Shared pytest fixtures for ZeroWhisper backend tests.

Each test function gets a fresh encrypted SQLite database via the `test_db`
fixture so there is no shared state between tests.
"""
import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

# Set a test JWT secret before importing app modules so the Settings
# model_validator does not reject the insecure default.
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-for-testing-only-32ch")

# Must import database helpers before the app to avoid circular issues
from app.database import initialize_engine, create_db_and_tables, get_engine
import app.services.setup as setup_service

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
    create_db_and_tables()
    setup_service._current_key = TEST_KEY

    # Also mock get_state to return INITIALIZED so is_db_ready() works.
    # We monkeypatch the module-level function to avoid touching real state files.
    from app.services.setup import SetupState
    original_get_state = setup_service.get_state

    def _mock_get_state():
        return SetupState.INITIALIZED

    setup_service.get_state = _mock_get_state

    yield db_path

    # Restore
    setup_service.get_state = original_get_state
    setup_service._current_key = None

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
        with Session(get_engine()) as session:
            yield session

    app.dependency_overrides[get_session] = get_test_session
    with TestClient(app, raise_server_exceptions=True) as c:
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
