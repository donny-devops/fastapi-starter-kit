from __future__ import annotations

LLM_FAILOVER = (
    "gemini",
    "claude",
    "gpt",
    "deepseek",
    "grok",
    "mistral",
)

POPS: tuple[dict, ...] = (
    {
        "colo": "NRT",
        "region": "APAC",
        "p99_ms": 14,
        "rps": 240_000,
        "cache_hit": 0.994,
        "shard": "shard_apac_01",
    },
    {
        "colo": "SIN",
        "region": "APAC",
        "p99_ms": 18,
        "rps": 180_000,
        "cache_hit": 0.991,
        "shard": "shard_apac_02",
    },
    {
        "colo": "FRA",
        "region": "EMEA",
        "p99_ms": 12,
        "rps": 320_000,
        "cache_hit": 0.998,
        "shard": "shard_emea_01",
    },
    {
        "colo": "LHR",
        "region": "EMEA",
        "p99_ms": 15,
        "rps": 290_000,
        "cache_hit": 0.996,
        "shard": "shard_emea_02",
    },
    {
        "colo": "IAD",
        "region": "AMER",
        "p99_ms": 9,
        "rps": 450_000,
        "cache_hit": 0.999,
        "shard": "shard_amer_01",
    },
    {
        "colo": "SJC",
        "region": "AMER",
        "p99_ms": 11,
        "rps": 380_000,
        "cache_hit": 0.997,
        "shard": "shard_amer_02",
    },
    {
        "colo": "GRU",
        "region": "LATAM",
        "p99_ms": 24,
        "rps": 95_000,
        "cache_hit": 0.987,
        "shard": "shard_latam_01",
    },
    {
        "colo": "DXB",
        "region": "MEA",
        "p99_ms": 22,
        "rps": 85_000,
        "cache_hit": 0.989,
        "shard": "shard_mea_01",
    },
)

TENANTS: tuple[dict, ...] = (
    {
        "tenant": "tenant_fintech_uk",
        "country": "GB",
        "shard": "shard_emea_01",
        "primary": "EMEA",
        "backup": "AMER",
    },
    {
        "tenant": "tenant_tokyo_retail",
        "country": "JP",
        "shard": "shard_apac_01",
        "primary": "APAC",
        "backup": "EMEA",
    },
    {
        "tenant": "tenant_bank_ny",
        "country": "US",
        "shard": "shard_amer_01",
        "primary": "AMER",
        "backup": "EMEA",
    },
    {
        "tenant": "tenant_saopaulo_logistics",
        "country": "BR",
        "shard": "shard_latam_01",
        "primary": "LATAM",
        "backup": "AMER",
    },
    {
        "tenant": "tenant_dubai_trade",
        "country": "AE",
        "shard": "shard_mea_01",
        "primary": "MEA",
        "backup": "EMEA",
    },
)

_COUNTRY_TO_SHARD = {row["country"]: row for row in TENANTS}
_SHARD_INDEX = {row["shard"]: row for row in POPS}

VECTOR_DIM = 768
VECTOR_BATCH_MAX = 1_000
GLOBAL_RPS = sum(pop["rps"] for pop in POPS)
GLOBAL_CACHE_HIT = 0.9939


def route_country(country: str) -> dict:
    code = country.strip().upper()
    tenant = _COUNTRY_TO_SHARD.get(code)
    if tenant:
        pop = _SHARD_INDEX[tenant["shard"]]
        return {
            "country": code,
            "shard": tenant["shard"],
            "primary": tenant["primary"],
            "backup": tenant["backup"],
            "colo": pop["colo"],
            "matched_tenant": tenant["tenant"],
        }
    fallback = _SHARD_INDEX["shard_amer_01"]
    return {
        "country": code,
        "shard": "shard_amer_01",
        "primary": "AMER",
        "backup": "EMEA",
        "colo": fallback["colo"],
        "matched_tenant": None,
    }


def next_llm(failed: list[str] | None = None) -> dict:
    skipped = {name.lower() for name in (failed or [])}
    for index, name in enumerate(LLM_FAILOVER, start=1):
        if name not in skipped:
            return {
                "provider": name,
                "priority": index,
                "failover": list(LLM_FAILOVER),
                "skipped": sorted(skipped),
            }
    return {
        "provider": None,
        "priority": None,
        "failover": list(LLM_FAILOVER),
        "skipped": sorted(skipped),
        "error": "all providers exhausted",
    }


def ingest_vectors(vectors: list[list[float]]) -> dict:
    if len(vectors) > VECTOR_BATCH_MAX:
        raise ValueError(f"batch exceeds {VECTOR_BATCH_MAX} vectors")
    for index, vector in enumerate(vectors):
        if len(vector) != VECTOR_DIM:
            raise ValueError(
                f"vector {index} has dim {len(vector)}, expected {VECTOR_DIM}"
            )
    return {
        "accepted": len(vectors),
        "dimensions": VECTOR_DIM,
        "batch_limit": VECTOR_BATCH_MAX,
    }


def topology_summary() -> dict:
    return {
        "source": "configured_topology",
        "global_edge_rps": GLOBAL_RPS,
        "connected_pops_claim": "330+",
        "d1_shards_active": len(POPS),
        "global_cache_hit_ratio": GLOBAL_CACHE_HIT,
        "failover": "cross-region mesh",
        "tenants_catalogued": len(TENANTS),
        "tenants_scaled_claim": 10_000,
        "pops": list(POPS),
        "tenants": list(TENANTS),
        "llm_failover": list(LLM_FAILOVER),
        "vectorize": {"dimensions": VECTOR_DIM, "batch_max": VECTOR_BATCH_MAX},
        "rate_limit_per_minute": 50_000,
    }
