from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from cache import l1
from mesh import ingest_vectors, next_llm, route_country, topology_summary
from rate_limit import limiter

router = APIRouter(prefix="/ops", tags=["ops"])


class VectorBatch(BaseModel):
    vectors: list[list[float]] = Field(..., min_length=1)


@router.get("/status")
def ops_status(request: Request):
    colo = request.headers.get("cf-ray", "").split("-")[-1] or None
    country = request.headers.get("cf-ipcountry")
    return {
        "isolate": {
            "ready": True,
            "cold_start_budget_ms": 15,
            "cache": l1.stats(),
            "rate_limit_per_minute": limiter.limit_per_minute,
            "colo": colo,
            "country": country,
        },
        "topology": topology_summary(),
    }


@router.get("/route")
def ops_route(country: str = Query(..., min_length=2, max_length=2)):
    return route_country(country)


@router.get("/llm")
def ops_llm(failed: str | None = Query(default=None)):
    skipped = [part.strip() for part in failed.split(",")] if failed else []
    result = next_llm(skipped)
    if result.get("provider") is None:
        raise HTTPException(status_code=503, detail=result)
    return result


@router.post("/vectorize")
def ops_vectorize(batch: VectorBatch):
    try:
        return ingest_vectors(batch.vectors)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None
