from httpx import AsyncClient


# ---------------------------------------------------------------------------
# GET /users/
# ---------------------------------------------------------------------------
class TestListUsers:
    async def test_empty_list(self, client: AsyncClient):
        resp = await client.get("/users/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_existing_users(self, client: AsyncClient, seeded_user: dict):
        resp = await client.get("/users/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == seeded_user["id"]

    async def test_skip(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/users/", json={"name": f"User {i}", "email": f"u{i}@example.com"}
            )
        resp = await client.get("/users/?skip=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_limit(self, client: AsyncClient):
        for i in range(3):
            await client.post(
                "/users/", json={"name": f"User {i}", "email": f"u{i}@example.com"}
            )
        resp = await client.get("/users/?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_skip_beyond_total_returns_empty(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.get("/users/?skip=100")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /users/{id}
# ---------------------------------------------------------------------------
class TestGetUser:
    async def test_returns_correct_user(self, client: AsyncClient, seeded_user: dict):
        resp = await client.get(f"/users/{seeded_user['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == seeded_user["id"]
        assert data["name"] == "Alice"
        assert data["email"] == "alice@example.com"
        assert data["is_active"] is True
        assert "created_at" in data

    async def test_not_found(self, client: AsyncClient):
        resp = await client.get("/users/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "User not found"

    async def test_invalid_id_type(self, client: AsyncClient):
        resp = await client.get("/users/abc")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /users/
# ---------------------------------------------------------------------------
class TestCreateUser:
    async def test_success(self, client: AsyncClient):
        resp = await client.post(
            "/users/", json={"name": "Bob", "email": "bob@example.com"}
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Bob"
        assert data["email"] == "bob@example.com"
        assert data["is_active"] is True
        assert isinstance(data["id"], int)
        assert "created_at" in data

    async def test_response_schema_has_all_fields(self, client: AsyncClient):
        resp = await client.post(
            "/users/", json={"name": "Carol", "email": "carol@example.com"}
        )
        assert resp.status_code == 201
        data = resp.json()
        for field in ("id", "name", "email", "is_active", "created_at"):
            assert field in data

    async def test_duplicate_email_returns_409(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.post(
            "/users/", json={"name": "Dupe", "email": seeded_user["email"]}
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "Email already registered"

    async def test_missing_name_returns_422(self, client: AsyncClient):
        resp = await client.post("/users/", json={"email": "noname@example.com"})
        assert resp.status_code == 422

    async def test_missing_email_returns_422(self, client: AsyncClient):
        resp = await client.post("/users/", json={"name": "No Email"})
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self, client: AsyncClient):
        resp = await client.post("/users/", json={})
        assert resp.status_code == 422

    async def test_ids_are_unique(self, client: AsyncClient):
        r1 = await client.post("/users/", json={"name": "X", "email": "x@example.com"})
        r2 = await client.post("/users/", json={"name": "Y", "email": "y@example.com"})
        assert r1.json()["id"] != r2.json()["id"]


# ---------------------------------------------------------------------------
# PUT /users/{id}
# ---------------------------------------------------------------------------
class TestUpdateUser:
    async def test_update_name(self, client: AsyncClient, seeded_user: dict):
        resp = await client.put(
            f"/users/{seeded_user['id']}", json={"name": "Updated Name"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Updated Name"
        assert data["email"] == seeded_user["email"]  # unchanged

    async def test_update_email(self, client: AsyncClient, seeded_user: dict):
        resp = await client.put(
            f"/users/{seeded_user['id']}", json={"email": "new@example.com"}
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "new@example.com"
        assert resp.json()["name"] == seeded_user["name"]  # unchanged

    async def test_deactivate_user(self, client: AsyncClient, seeded_user: dict):
        resp = await client.put(
            f"/users/{seeded_user['id']}", json={"is_active": False}
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    async def test_reactivate_user(self, client: AsyncClient, seeded_user: dict):
        await client.put(f"/users/{seeded_user['id']}", json={"is_active": False})
        resp = await client.put(f"/users/{seeded_user['id']}", json={"is_active": True})
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    async def test_empty_body_leaves_fields_unchanged(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.put(f"/users/{seeded_user['id']}", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == seeded_user["name"]
        assert data["email"] == seeded_user["email"]
        assert data["is_active"] == seeded_user["is_active"]

    async def test_update_persists(self, client: AsyncClient, seeded_user: dict):
        await client.put(f"/users/{seeded_user['id']}", json={"name": "Persisted"})
        resp = await client.get(f"/users/{seeded_user['id']}")
        assert resp.json()["name"] == "Persisted"

    async def test_not_found(self, client: AsyncClient):
        resp = await client.put("/users/9999", json={"name": "Ghost"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "User not found"


# ---------------------------------------------------------------------------
# DELETE /users/{id}
# ---------------------------------------------------------------------------
class TestDeleteUser:
    async def test_success_returns_204(self, client: AsyncClient, seeded_user: dict):
        resp = await client.delete(f"/users/{seeded_user['id']}")
        assert resp.status_code == 204
        assert resp.content == b""

    async def test_deleted_user_is_gone(self, client: AsyncClient, seeded_user: dict):
        await client.delete(f"/users/{seeded_user['id']}")
        resp = await client.get(f"/users/{seeded_user['id']}")
        assert resp.status_code == 404

    async def test_deleted_user_removed_from_list(
        self, client: AsyncClient, seeded_user: dict
    ):
        await client.delete(f"/users/{seeded_user['id']}")
        resp = await client.get("/users/")
        assert resp.json() == []

    async def test_not_found(self, client: AsyncClient):
        resp = await client.delete("/users/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "User not found"

    async def test_second_delete_returns_404(
        self, client: AsyncClient, seeded_user: dict
    ):
        await client.delete(f"/users/{seeded_user['id']}")
        resp = await client.delete(f"/users/{seeded_user['id']}")
        assert resp.status_code == 404

    async def test_cascade_deletes_owned_items(
        self, client: AsyncClient, seeded_user: dict, seeded_item: dict
    ):
        await client.delete(f"/users/{seeded_user['id']}")
        resp = await client.get(f"/items/{seeded_item['id']}")
        assert resp.status_code == 404
