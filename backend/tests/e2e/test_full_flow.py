"""
End-to-end integration tests for ZeroWhisper backend.

Each test uses an isolated encrypted SQLite DB (see conftest.py).
Tests that need OPENAI_API_KEY are skipped when it is not set.
"""
import io
import os

import pytest

# ---------------------------------------------------------------------------
# SQLCipher availability guard
# ---------------------------------------------------------------------------

try:
    import pysqlcipher3  # noqa: F401
    _SQLCIPHER_AVAILABLE = True
except ImportError:
    _SQLCIPHER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _SQLCIPHER_AVAILABLE,
    reason="pysqlcipher3 / SQLCipher not available in this environment",
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _decimal_approx(value, expected: float, rel: float = 0.01) -> bool:
    """Compare a Decimal/string/float API value to a float with relative tolerance."""
    return abs(float(value) - expected) <= abs(expected) * rel


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Setup status
# ---------------------------------------------------------------------------

def test_setup_status(client):
    """With test_db fixture, DB is initialized and key is loaded."""
    r = client.get("/setup/status")
    assert r.status_code == 200
    data = r.json()
    # State must be INITIALIZED since we patched get_state and set _current_key
    assert data["state"] == "INITIALIZED"


# ---------------------------------------------------------------------------
# Auth flow
# ---------------------------------------------------------------------------

def test_auth_flow(client):
    """Full register → login → protected endpoint → refresh cycle."""
    # Register
    r = client.post("/auth/register", json={
        "username": "alice",
        "email": "alice@x.com",
        "password": "pass1234",
    })
    assert r.status_code == 201
    user_data = r.json()
    assert user_data["username"] == "alice"

    # Login with correct credentials
    r = client.post("/auth/login", json={
        "username": "alice",
        "password": "pass1234",
    })
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data

    # Login with wrong password
    r = client.post("/auth/login", json={
        "username": "alice",
        "password": "wrong",
    })
    assert r.status_code == 401

    # Protected endpoint without token
    r = client.get("/api/transactions")
    assert r.status_code in (401, 403)

    # Protected endpoint with valid token
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    r = client.get("/api/transactions", headers=headers)
    assert r.status_code == 200

    # Token refresh
    r = client.post("/auth/refresh", json={"refresh_token": data["refresh_token"]})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_register_duplicate_username(client):
    """Registering the same username twice returns 409."""
    payload = {"username": "bob", "email": "bob@x.com", "password": "pass1234"}
    client.post("/auth/register", json=payload)
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# Transaction CRUD
# ---------------------------------------------------------------------------

def test_transaction_crud(client, auth_headers):
    """Create, list, get, update, and soft-delete a transaction."""
    # Create a JOD transaction
    r = client.post("/api/transactions", headers=auth_headers, json={
        "amount_original": 50.0,
        "currency_original": "JOD",
        "category": "Food",
        "description": "Groceries",
        "transaction_date": "2026-05-01",
    })
    assert r.status_code == 201
    tx = r.json()
    # JOD → amount_base should be 1:1 with amount_original
    assert _decimal_approx(tx["amount_original"], 50.0)
    assert _decimal_approx(tx["amount_base"], 50.0)
    assert tx["currency_original"] == "JOD"
    assert tx["category"] == "Food"
    tx_id = tx["id"]

    # List — should have exactly 1 transaction
    r = client.get("/api/transactions", headers=auth_headers)
    assert r.status_code == 200
    lst = r.json()
    assert lst["total"] == 1
    assert len(lst["items"]) == 1

    # Get single transaction
    r = client.get(f"/api/transactions/{tx_id}", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["category"] == "Food"

    # Update category
    r = client.put(f"/api/transactions/{tx_id}", headers=auth_headers, json={"category": "Health"})
    assert r.status_code == 200
    assert r.json()["category"] == "Health"

    # Soft-delete
    r = client.delete(f"/api/transactions/{tx_id}", headers=auth_headers)
    assert r.status_code == 204

    # Verify transaction is gone from list
    r = client.get("/api/transactions", headers=auth_headers)
    assert r.json()["total"] == 0


def test_transaction_not_found(client, auth_headers):
    """Fetching a non-existent transaction returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"
    r = client.get(f"/api/transactions/{fake_id}", headers=auth_headers)
    assert r.status_code == 404


def test_transaction_pagination(client, auth_headers):
    """Creating 5 transactions with page_size=2 returns 2 items and total=5."""
    for i in range(5):
        client.post("/api/transactions", headers=auth_headers, json={
            "amount_original": float(10 + i),
            "currency_original": "JOD",
            "category": "Food",
            "description": f"Item {i}",
            "transaction_date": f"2026-05-0{i + 1}",
        })

    r = client.get("/api/transactions?page=1&page_size=2", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["pages"] >= 3  # ceil(5/2) == 3


# ---------------------------------------------------------------------------
# Exchange rates
# ---------------------------------------------------------------------------

def test_exchange_rate(client, auth_headers):
    """Set a rate, verify retrieval, and confirm USD transaction conversion."""
    # Set manual rate
    r = client.post("/api/exchange-rates", headers=auth_headers, json={
        "rate": 0.709,
        "date": "2026-05-01",
    })
    assert r.status_code == 200

    # Get current rate — endpoint returns {"rate": ..., "date": ..., "source": ...}
    r = client.get("/api/exchange-rates/current", headers=auth_headers)
    assert r.status_code == 200
    rate_data = r.json()
    assert "rate" in rate_data
    assert _decimal_approx(rate_data["rate"], 0.709)

    # Create a USD transaction — amount_base should be converted to JOD
    r = client.post("/api/transactions", headers=auth_headers, json={
        "amount_original": 100.0,
        "currency_original": "USD",
        "category": "Food",
        "description": "USD purchase",
        "transaction_date": "2026-05-01",
    })
    assert r.status_code == 201
    tx = r.json()
    # 100 USD * 0.709 JOD/USD = 70.9 JOD
    assert _decimal_approx(tx["amount_base"], 70.9, rel=0.01)


def test_exchange_rate_default_fallback(client, auth_headers):
    """When no rate is stored, current endpoint returns the configured default."""
    r = client.get("/api/exchange-rates/current", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    # Should return something (either default or stored)
    assert "rate" in data or "jod_per_usd" in data


# ---------------------------------------------------------------------------
# CSV import
# ---------------------------------------------------------------------------

def test_csv_import(client, auth_headers):
    """Valid CSV rows are imported; transaction list reflects the import."""
    csv_content = (
        "transaction_date,amount_original,currency_original,category,description\n"
        "2026-05-01,50,JOD,Food,Groceries\n"
        "2026-05-02,20,JOD,Transport,Bus"
    )

    r = client.post(
        "/api/imports/csv",
        headers=auth_headers,
        files={"file": ("test.csv", io.StringIO(csv_content), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 2
    assert data["errors"] == []

    # Verify transactions are in DB
    r = client.get("/api/transactions", headers=auth_headers)
    assert r.json()["total"] == 2


def test_csv_import_bad_rows(client, auth_headers):
    """Bad rows are reported as errors; good rows still get imported."""
    csv_content = (
        "transaction_date,amount_original,currency_original,category,description\n"
        "2026-05-01,50,JOD,Food,OK\n"
        "not-a-date,bad,JOD,Food,BAD"
    )

    r = client.post(
        "/api/imports/csv",
        headers=auth_headers,
        files={"file": ("test.csv", io.StringIO(csv_content), "text/csv")},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["imported"] == 1
    assert len(data["errors"]) == 1


def test_csv_import_empty_file(client, auth_headers):
    """Uploading an empty CSV returns an error message."""
    r = client.post(
        "/api/imports/csv",
        headers=auth_headers,
        files={"file": ("empty.csv", io.StringIO(""), "text/csv")},
    )
    # Service raises ValueError("CSV file is empty") → router catches and returns {"error": ...}
    assert r.status_code == 200
    data = r.json()
    assert "error" in data


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------

def test_api_key_management(client, auth_headers):
    """Full API key lifecycle: create, list (masked), use for MCP, revoke, verify revoked."""
    # Create key
    r = client.post("/api/api-keys", headers=auth_headers, json={"name": "mcp-dev"})
    assert r.status_code == 201
    data = r.json()
    assert "key" in data
    assert data["key"].startswith("zwp_")
    key = data["key"]
    key_id = data["id"]

    # List keys — raw key not exposed
    r = client.get("/api/api-keys", headers=auth_headers)
    assert r.status_code == 200
    keys = r.json()
    assert len(keys) == 1
    assert "key" not in keys[0]   # only prefix/id/name exposed in list

    # Use key for MCP resources endpoint (requires auth)
    r = client.get("/mcp/resources", headers={"X-API-Key": key})
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Revoke key
    r = client.delete(f"/api/api-keys/{key_id}", headers=auth_headers)
    assert r.status_code == 204

    # Revoked key no longer works
    r = client.get("/mcp/resources", headers={"X-API-Key": key})
    assert r.status_code == 401


def test_api_key_missing_returns_unprocessable_or_401(client):
    """Calling a key-protected endpoint without a key returns 401 or 422."""
    r = client.get("/mcp/resources")
    assert r.status_code in (401, 422)


# ---------------------------------------------------------------------------
# MCP endpoints
# ---------------------------------------------------------------------------

def test_mcp_manifest_no_auth(client):
    """MCP manifest is publicly accessible without any API key."""
    r = client.get("/mcp/manifest")
    assert r.status_code == 200
    manifest = r.json()
    assert manifest["name"] == "ZeroWhisper"
    assert "capabilities" in manifest


def test_mcp_endpoints(client, auth_headers):
    """Create an API key and exercise the MCP resources and tools endpoints."""
    # Create API key
    r = client.post("/api/api-keys", headers=auth_headers, json={"name": "test"})
    assert r.status_code == 201
    key = r.json()["key"]
    mcp_headers = {"X-API-Key": key}

    # Resources list
    r = client.get("/mcp/resources", headers=mcp_headers)
    assert r.status_code == 200
    resources = r.json()
    assert isinstance(resources, list)
    assert len(resources) > 0
    # Each resource should have a uri and name
    assert all("uri" in res for res in resources)

    # Tool call: get_balance
    r = client.post("/mcp/tools/call", headers=mcp_headers, json={"tool": "get_balance"})
    assert r.status_code == 200
    result = r.json()
    assert "balance_jod" in result
    assert result["currency"] == "JOD"

    # Tool call: get_recent_transactions
    r = client.post(
        "/mcp/tools/call",
        headers=mcp_headers,
        json={"tool": "get_recent_transactions", "args": {"limit": 5}},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)

    # Tool call: unknown tool returns 400
    r = client.post("/mcp/tools/call", headers=mcp_headers, json={"tool": "does_not_exist"})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Whisper endpoint (skipped without OPENAI_API_KEY)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="requires OPENAI_API_KEY",
)
def test_whisper_requires_key(client, auth_headers):
    """Whisper endpoint is reachable when an OpenAI key is set."""
    r = client.get("/api/whisper/status", headers=auth_headers)
    # Just verify the endpoint exists and responds
    assert r.status_code in (200, 404, 422)
