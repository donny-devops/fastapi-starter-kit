from httpx import AsyncClient

from cache import l1


async def test_ops_status_includes_isolate_and_topology(client: AsyncClient):
    resp = await client.get("/ops/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["isolate"]["ready"] is True
    assert body["isolate"]["cold_start_budget_ms"] == 15
    assert body["topology"]["source"] == "configured_topology"
    assert body["topology"]["global_edge_rps"] == 2_040_000
    assert body["topology"]["d1_shards_active"] == 8
    assert len(body["topology"]["pops"]) == 8
    assert len(body["topology"]["llm_failover"]) == 6


async def test_ops_route_known_country(client: AsyncClient):
    resp = await client.get("/ops/route", params={"country": "JP"})
    assert resp.status_code == 200
    assert resp.json()["shard"] == "shard_apac_01"
    assert resp.json()["colo"] == "NRT"


async def test_ops_route_unknown_country_falls_back_to_amer(client: AsyncClient):
    resp = await client.get("/ops/route", params={"country": "ZZ"})
    assert resp.status_code == 200
    assert resp.json()["shard"] == "shard_amer_01"
    assert resp.json()["matched_tenant"] is None


async def test_ops_llm_failover_skips_failed_providers(client: AsyncClient):
    resp = await client.get("/ops/llm", params={"failed": "gemini,claude"})
    assert resp.status_code == 200
    assert resp.json()["provider"] == "gpt"
    assert resp.json()["priority"] == 3


async def test_ops_llm_exhausted_returns_503(client: AsyncClient):
    resp = await client.get(
        "/ops/llm",
        params={"failed": "gemini,claude,gpt,deepseek,grok,mistral"},
    )
    assert resp.status_code == 503


async def test_vectorize_accepts_768d_batch(client: AsyncClient):
    resp = await client.post(
        "/ops/vectorize",
        json={"vectors": [[0.1] * 768, [0.2] * 768]},
    )
    assert resp.status_code == 200
    assert resp.json()["accepted"] == 2
    assert resp.json()["dimensions"] == 768


async def test_vectorize_rejects_wrong_dimension(client: AsyncClient):
    resp = await client.post("/ops/vectorize", json={"vectors": [[1.0, 2.0]]})
    assert resp.status_code == 422


async def test_l1_cache_hits_on_second_user_get(client: AsyncClient, seeded_user: dict):
    first = await client.get(f"/users/{seeded_user['id']}")
    assert first.status_code == 200
    second = await client.get(f"/users/{seeded_user['id']}")
    assert second.status_code == 200
    assert l1.stats()["hits"] >= 1


async def test_l1_cache_invalidates_on_update(client: AsyncClient, seeded_user: dict):
    await client.get(f"/users/{seeded_user['id']}")
    await client.put(f"/users/{seeded_user['id']}", json={"name": "Cached-Out"})
    resp = await client.get(f"/users/{seeded_user['id']}")
    assert resp.json()["name"] == "Cached-Out"


async def test_rate_limit_headers_present(client: AsyncClient):
    resp = await client.get("/users/")
    assert resp.status_code == 200
    assert int(resp.headers["x-ratelimit-limit"]) == 50_000
    assert "x-ratelimit-remaining" in resp.headers
