"""API integration tests — real HTTP calls via FastAPI TestClient, no mocks."""

import os

# Test-only credentials — not real secrets
TEST_PASSWORD = os.environ.get("TEST_PASSWORD", "test-only-placeholder")


# ── Auth: Register ────────────────────────────────────────────


def test_register_success(db_client):
    resp = db_client.post(
        "/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["username"] == "alice"
    assert data["email"] == "alice@example.com"
    assert "id" in data
    assert "password" not in data and "hashed_password" not in data


def test_register_duplicate_username(db_client):
    payload = {"username": "bob", "email": "bob@example.com", "password": TEST_PASSWORD}
    db_client.post("/auth/register", json=payload)
    resp = db_client.post(
        "/auth/register",
        json={"username": "bob", "email": "other@example.com", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_register_duplicate_email(db_client):
    db_client.post(
        "/auth/register",
        json={"username": "user1", "email": "same@example.com", "password": TEST_PASSWORD},
    )
    resp = db_client.post(
        "/auth/register",
        json={"username": "user2", "email": "same@example.com", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 400


def test_register_invalid_email(db_client):
    resp = db_client.post(
        "/auth/register",
        json={"username": "bad", "email": "not-an-email", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 422


def test_register_missing_fields(db_client):
    resp = db_client.post("/auth/register", json={"username": "only"})
    assert resp.status_code == 422


# ── Auth: Login ───────────────────────────────────────────────


def _register_and_login(client, username="testuser", password=None):
    """Helper: register a user and return the Bearer token."""
    if password is None:
        password = TEST_PASSWORD
    client.post(
        "/auth/register",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    resp = client.post(
        "/auth/login",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    return resp.json()["access_token"]


def test_login_success(db_client):
    db_client.post(
        "/auth/register",
        json={"username": "carol", "email": "carol@example.com", "password": TEST_PASSWORD},
    )
    resp = db_client.post(
        "/auth/login",
        json={"username": "carol", "email": "carol@example.com", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(db_client):
    db_client.post(
        "/auth/register",
        json={"username": "dave", "email": "dave@example.com", "password": TEST_PASSWORD},
    )
    resp = db_client.post(
        "/auth/login",
        json={"username": "dave", "email": "dave@example.com", "password": "wrong-password"},
    )
    assert resp.status_code == 401
    assert "Invalid credentials" in resp.json()["detail"]


def test_login_nonexistent_user(db_client):
    resp = db_client.post(
        "/auth/login",
        json={"username": "ghost", "email": "ghost@example.com", "password": TEST_PASSWORD},
    )
    assert resp.status_code == 401


# ── Devices: Auth required (401) ─────────────────────────────


def test_devices_list_requires_auth(db_client):
    resp = db_client.get("/devices/")
    assert resp.status_code == 401


def test_devices_create_requires_auth(db_client):
    resp = db_client.post("/devices/", json={"hostname": "h", "ip_address": "1.2.3.4"})
    assert resp.status_code == 401


def test_devices_get_requires_auth(db_client):
    resp = db_client.get("/devices/1")
    assert resp.status_code == 401


def test_devices_update_requires_auth(db_client):
    resp = db_client.put("/devices/1", json={"hostname": "new"})
    assert resp.status_code == 401


def test_devices_delete_requires_auth(db_client):
    resp = db_client.delete("/devices/1")
    assert resp.status_code == 401


# ── Devices: CRUD ─────────────────────────────────────────────


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def test_create_device(db_client):
    token = _register_and_login(db_client)
    resp = db_client.post(
        "/devices/",
        json={"hostname": "router-1", "ip_address": "10.0.0.1", "mac_address": "AA:BB:CC:DD:EE:FF"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["hostname"] == "router-1"
    assert data["ip_address"] == "10.0.0.1"
    assert data["mac_address"] == "AA:BB:CC:DD:EE:FF"
    assert data["device_type"] == "unknown"
    assert data["status"] == "online"
    assert "id" in data
    assert "owner_id" in data


def test_create_device_minimal(db_client):
    token = _register_and_login(db_client)
    resp = db_client.post(
        "/devices/",
        json={"hostname": "switch-1", "ip_address": "10.0.0.2"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 201
    assert resp.json()["mac_address"] is None


def test_create_device_invalid_body(db_client):
    token = _register_and_login(db_client)
    resp = db_client.post(
        "/devices/",
        json={"hostname": "no-ip"},
        headers=_auth_header(token),
    )
    assert resp.status_code == 422


def test_list_devices(db_client):
    token = _register_and_login(db_client)
    headers = _auth_header(token)
    db_client.post(
        "/devices/", json={"hostname": "d1", "ip_address": "10.0.0.1"}, headers=headers
    )
    db_client.post(
        "/devices/", json={"hostname": "d2", "ip_address": "10.0.0.2"}, headers=headers
    )
    resp = db_client.get("/devices/", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_list_devices_empty(db_client):
    token = _register_and_login(db_client)
    resp = db_client.get("/devices/", headers=_auth_header(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_device(db_client):
    token = _register_and_login(db_client)
    headers = _auth_header(token)
    create_resp = db_client.post(
        "/devices/", json={"hostname": "ap-1", "ip_address": "10.0.1.1"}, headers=headers
    )
    device_id = create_resp.json()["id"]
    resp = db_client.get(f"/devices/{device_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["hostname"] == "ap-1"


def test_get_device_not_found(db_client):
    token = _register_and_login(db_client)
    resp = db_client.get("/devices/9999", headers=_auth_header(token))
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


def test_update_device(db_client):
    token = _register_and_login(db_client)
    headers = _auth_header(token)
    create_resp = db_client.post(
        "/devices/",
        json={"hostname": "old-name", "ip_address": "10.0.2.1", "status": "online"},
        headers=headers,
    )
    device_id = create_resp.json()["id"]

    resp = db_client.put(
        f"/devices/{device_id}",
        json={"hostname": "new-name", "status": "offline"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["hostname"] == "new-name"
    assert data["status"] == "offline"
    assert data["ip_address"] == "10.0.2.1"  # unchanged


def test_update_device_partial(db_client):
    token = _register_and_login(db_client)
    headers = _auth_header(token)
    create_resp = db_client.post(
        "/devices/",
        json={"hostname": "keep", "ip_address": "10.0.3.1", "device_type": "router"},
        headers=headers,
    )
    device_id = create_resp.json()["id"]

    resp = db_client.put(
        f"/devices/{device_id}",
        json={"device_type": "switch"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["hostname"] == "keep"
    assert resp.json()["device_type"] == "switch"


def test_update_device_not_found(db_client):
    token = _register_and_login(db_client)
    resp = db_client.put(
        "/devices/9999", json={"hostname": "x"}, headers=_auth_header(token)
    )
    assert resp.status_code == 404


def test_delete_device(db_client):
    token = _register_and_login(db_client)
    headers = _auth_header(token)
    create_resp = db_client.post(
        "/devices/", json={"hostname": "bye", "ip_address": "10.0.4.1"}, headers=headers
    )
    device_id = create_resp.json()["id"]

    resp = db_client.delete(f"/devices/{device_id}", headers=headers)
    assert resp.status_code == 204

    # Confirm it's gone
    resp = db_client.get(f"/devices/{device_id}", headers=headers)
    assert resp.status_code == 404


def test_delete_device_not_found(db_client):
    token = _register_and_login(db_client)
    resp = db_client.delete("/devices/9999", headers=_auth_header(token))
    assert resp.status_code == 404


# ── Cross-user isolation ─────────────────────────────────────


def test_user_cannot_see_other_users_devices(db_client):
    token_a = _register_and_login(db_client, "userA")
    token_b = _register_and_login(db_client, "userB")

    db_client.post(
        "/devices/",
        json={"hostname": "private", "ip_address": "10.1.0.1"},
        headers=_auth_header(token_a),
    )
    resp = db_client.get("/devices/", headers=_auth_header(token_b))
    assert resp.status_code == 200
    assert len(resp.json()) == 0


def test_user_cannot_update_other_users_device(db_client):
    token_a = _register_and_login(db_client, "ownerA")
    token_b = _register_and_login(db_client, "ownerB")

    create_resp = db_client.post(
        "/devices/",
        json={"hostname": "mine", "ip_address": "10.2.0.1"},
        headers=_auth_header(token_a),
    )
    device_id = create_resp.json()["id"]

    resp = db_client.put(
        f"/devices/{device_id}",
        json={"hostname": "stolen"},
        headers=_auth_header(token_b),
    )
    assert resp.status_code == 404


def test_user_cannot_delete_other_users_device(db_client):
    token_a = _register_and_login(db_client, "delA")
    token_b = _register_and_login(db_client, "delB")

    create_resp = db_client.post(
        "/devices/",
        json={"hostname": "safe", "ip_address": "10.3.0.1"},
        headers=_auth_header(token_a),
    )
    device_id = create_resp.json()["id"]

    resp = db_client.delete(f"/devices/{device_id}", headers=_auth_header(token_b))
    assert resp.status_code == 404


# ── Invalid token ─────────────────────────────────────────────


def test_invalid_token_rejected(db_client):
    resp = db_client.get("/devices/", headers={"Authorization": "Bearer garbage.token.here"})
    assert resp.status_code == 401
