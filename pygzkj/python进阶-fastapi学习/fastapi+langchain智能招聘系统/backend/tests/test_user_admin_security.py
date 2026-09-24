from __future__ import annotations

import secrets

import pytest
from fastapi.testclient import TestClient


def create_user(
    client: TestClient,
    admin_headers: dict[str, str],
    *,
    role_code: str,
) -> tuple[int, str, str]:
    suffix = secrets.token_hex(4)
    username = f"{role_code.lower()}_{suffix}"
    password = secrets.token_urlsafe(18)
    response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": username,
            "password": password,
            "real_name": f"{role_code} 测试用户",
            "role_codes": [role_code],
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["id"], username, password


def login(
    client: TestClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_current_admin_cannot_disable_delete_or_remove_own_admin_role(
    client: TestClient,
    auth_headers: dict[str, str],
):
    current = client.get("/api/v1/auth/me", headers=auth_headers).json()["data"]
    current_id = current["id"]

    disable = client.patch(
        f"/api/v1/users/{current_id}",
        headers=auth_headers,
        json={"status": "INACTIVE"},
    )
    assert disable.status_code == 409

    demote = client.patch(
        f"/api/v1/users/{current_id}",
        headers=auth_headers,
        json={"role_codes": ["VIEWER"]},
    )
    assert demote.status_code == 409

    delete = client.delete(f"/api/v1/users/{current_id}", headers=auth_headers)
    assert delete.status_code == 409

    unchanged = client.get(f"/api/v1/users/{current_id}", headers=auth_headers)
    assert unchanged.status_code == 200
    assert unchanged.json()["data"]["status"] == "ACTIVE"
    assert "ADMIN" in unchanged.json()["data"]["roles"]


def test_admin_role_cannot_be_disabled_or_removed(
    client: TestClient,
    auth_headers: dict[str, str],
):
    roles = client.get(
        "/api/v1/roles?page=1&page_size=100",
        headers=auth_headers,
    ).json()["data"]["items"]
    admin_role = next(item for item in roles if item["code"] == "ADMIN")

    disabled = client.patch(
        f"/api/v1/roles/{admin_role['id']}",
        headers=auth_headers,
        json={"status": "INACTIVE"},
    )
    assert disabled.status_code == 409

    deleted = client.delete(
        f"/api/v1/roles/{admin_role['id']}",
        headers=auth_headers,
    )
    assert deleted.status_code == 409


def test_password_reset_revokes_old_access_and_refresh_tokens(
    client: TestClient,
    auth_headers: dict[str, str],
):
    user_id, username, old_password = create_user(
        client,
        auth_headers,
        role_code="VIEWER",
    )
    old_tokens = login(client, username, old_password)
    old_access_headers = {
        "Authorization": f"Bearer {old_tokens['access_token']}"
    }
    new_password = secrets.token_urlsafe(20)

    reset = client.patch(
        f"/api/v1/users/{user_id}",
        headers=auth_headers,
        json={"password": new_password},
    )
    assert reset.status_code == 200, reset.text

    old_me = client.get("/api/v1/auth/me", headers=old_access_headers)
    assert old_me.status_code == 401
    old_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_tokens["refresh_token"]},
    )
    assert old_refresh.status_code == 401
    assert login(client, username, new_password)["access_token"]


def test_self_password_change_revokes_old_tokens(
    client: TestClient,
    auth_headers: dict[str, str],
):
    admin_id, username, old_password = create_user(
        client,
        auth_headers,
        role_code="ADMIN",
    )
    old_tokens = login(client, username, old_password)
    old_access_headers = {
        "Authorization": f"Bearer {old_tokens['access_token']}"
    }
    new_password = secrets.token_urlsafe(20)

    changed = client.patch(
        f"/api/v1/users/{admin_id}",
        headers=old_access_headers,
        json={"password": new_password},
    )
    assert changed.status_code == 200, changed.text

    assert (
        client.get("/api/v1/auth/me", headers=old_access_headers).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_tokens["refresh_token"]},
        ).status_code
        == 401
    )
    assert login(client, username, new_password)["access_token"]
