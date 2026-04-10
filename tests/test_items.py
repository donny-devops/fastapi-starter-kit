from httpx import AsyncClient


# ---------------------------------------------------------------------------
# GET /items/
# ---------------------------------------------------------------------------
class TestListItems:
    async def test_empty_list(self, client: AsyncClient):
        resp = await client.get("/items/")
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_returns_existing_items(self, client: AsyncClient, seeded_item: dict):
        resp = await client.get("/items/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == seeded_item["id"]

    async def test_skip(self, client: AsyncClient, seeded_user: dict):
        for i in range(3):
            await client.post(
                "/items/",
                json={"title": f"Item {i}", "owner_id": seeded_user["id"]},
            )
        resp = await client.get("/items/?skip=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    async def test_limit(self, client: AsyncClient, seeded_user: dict):
        for i in range(3):
            await client.post(
                "/items/",
                json={"title": f"Item {i}", "owner_id": seeded_user["id"]},
            )
        resp = await client.get("/items/?limit=2")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    async def test_skip_beyond_total_returns_empty(
        self, client: AsyncClient, seeded_item: dict
    ):
        resp = await client.get("/items/?skip=100")
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# GET /items/{id}
# ---------------------------------------------------------------------------
class TestGetItem:
    async def test_returns_correct_item(self, client: AsyncClient, seeded_item: dict):
        resp = await client.get(f"/items/{seeded_item['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == seeded_item["id"]
        assert data["title"] == seeded_item["title"]
        assert data["description"] == seeded_item["description"]
        assert data["owner_id"] == seeded_item["owner_id"]

    async def test_not_found(self, client: AsyncClient):
        resp = await client.get("/items/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Item not found"

    async def test_invalid_id_type(self, client: AsyncClient):
        resp = await client.get("/items/abc")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /items/
# ---------------------------------------------------------------------------
class TestCreateItem:
    async def test_success_with_description(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.post(
            "/items/",
            json={
                "title": "Gadget",
                "description": "A shiny gadget",
                "owner_id": seeded_user["id"],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Gadget"
        assert data["description"] == "A shiny gadget"
        assert data["owner_id"] == seeded_user["id"]
        assert isinstance(data["id"], int)

    async def test_success_without_description(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.post(
            "/items/", json={"title": "Bare", "owner_id": seeded_user["id"]}
        )
        assert resp.status_code == 201
        assert resp.json()["description"] is None

    async def test_response_schema_has_all_fields(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.post(
            "/items/", json={"title": "Schema Test", "owner_id": seeded_user["id"]}
        )
        assert resp.status_code == 201
        data = resp.json()
        for field in ("id", "title", "description", "owner_id"):
            assert field in data

    async def test_nonexistent_owner_returns_404(self, client: AsyncClient):
        resp = await client.post("/items/", json={"title": "Orphan", "owner_id": 9999})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Owner user not found"

    async def test_missing_title_returns_422(
        self, client: AsyncClient, seeded_user: dict
    ):
        resp = await client.post("/items/", json={"owner_id": seeded_user["id"]})
        assert resp.status_code == 422

    async def test_missing_owner_id_returns_422(self, client: AsyncClient):
        resp = await client.post("/items/", json={"title": "No Owner"})
        assert resp.status_code == 422

    async def test_empty_body_returns_422(self, client: AsyncClient):
        resp = await client.post("/items/", json={})
        assert resp.status_code == 422

    async def test_multiple_items_same_owner(
        self, client: AsyncClient, seeded_user: dict
    ):
        for title in ("Alpha", "Beta", "Gamma"):
            resp = await client.post(
                "/items/", json={"title": title, "owner_id": seeded_user["id"]}
            )
            assert resp.status_code == 201
        resp = await client.get("/items/")
        assert len(resp.json()) == 3


# ---------------------------------------------------------------------------
# PUT /items/{id}
# ---------------------------------------------------------------------------
class TestUpdateItem:
    async def test_update_title(self, client: AsyncClient, seeded_item: dict):
        resp = await client.put(
            f"/items/{seeded_item['id']}", json={"title": "New Title"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Title"
        assert data["description"] == seeded_item["description"]  # unchanged

    async def test_update_description(self, client: AsyncClient, seeded_item: dict):
        resp = await client.put(
            f"/items/{seeded_item['id']}", json={"description": "Updated desc"}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Updated desc"
        assert resp.json()["title"] == seeded_item["title"]  # unchanged

    async def test_clear_description_to_null(
        self, client: AsyncClient, seeded_item: dict
    ):
        # Explicitly passing null should overwrite an existing description
        resp = await client.put(
            f"/items/{seeded_item['id']}", json={"description": None}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] is None

    async def test_empty_body_leaves_fields_unchanged(
        self, client: AsyncClient, seeded_item: dict
    ):
        resp = await client.put(f"/items/{seeded_item['id']}", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == seeded_item["title"]
        assert data["description"] == seeded_item["description"]

    async def test_update_persists(self, client: AsyncClient, seeded_item: dict):
        await client.put(f"/items/{seeded_item['id']}", json={"title": "Persisted"})
        resp = await client.get(f"/items/{seeded_item['id']}")
        assert resp.json()["title"] == "Persisted"

    async def test_owner_id_unchanged_after_update(
        self, client: AsyncClient, seeded_item: dict
    ):
        resp = await client.put(
            f"/items/{seeded_item['id']}", json={"title": "Check Owner"}
        )
        assert resp.json()["owner_id"] == seeded_item["owner_id"]

    async def test_not_found(self, client: AsyncClient):
        resp = await client.put("/items/9999", json={"title": "Ghost"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Item not found"


# ---------------------------------------------------------------------------
# DELETE /items/{id}
# ---------------------------------------------------------------------------
class TestDeleteItem:
    async def test_success_returns_204(self, client: AsyncClient, seeded_item: dict):
        resp = await client.delete(f"/items/{seeded_item['id']}")
        assert resp.status_code == 204
        assert resp.content == b""

    async def test_deleted_item_is_gone(self, client: AsyncClient, seeded_item: dict):
        await client.delete(f"/items/{seeded_item['id']}")
        resp = await client.get(f"/items/{seeded_item['id']}")
        assert resp.status_code == 404

    async def test_deleted_item_removed_from_list(
        self, client: AsyncClient, seeded_item: dict
    ):
        await client.delete(f"/items/{seeded_item['id']}")
        resp = await client.get("/items/")
        assert resp.json() == []

    async def test_not_found(self, client: AsyncClient):
        resp = await client.delete("/items/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Item not found"

    async def test_second_delete_returns_404(
        self, client: AsyncClient, seeded_item: dict
    ):
        await client.delete(f"/items/{seeded_item['id']}")
        resp = await client.delete(f"/items/{seeded_item['id']}")
        assert resp.status_code == 404

    async def test_owner_still_exists_after_item_delete(
        self, client: AsyncClient, seeded_user: dict, seeded_item: dict
    ):
        await client.delete(f"/items/{seeded_item['id']}")
        resp = await client.get(f"/users/{seeded_user['id']}")
        assert resp.status_code == 200
