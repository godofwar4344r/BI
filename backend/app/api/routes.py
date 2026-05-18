from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from app.models.chat import ChatRequest, ChatResponse
from app.models.decision_case import DecisionCase, DecisionCaseFilters

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    services = request.app.state.services
    return {
        "status": "ok",
        "app": services.settings.app_name,
        "environment": services.settings.environment,
        "cases": services.repository.count(),
        "vector_store": services.settings.vector_store,
    }


@router.get("/cases", response_model=list[DecisionCase])
def list_cases(
    request: Request,
    person: str | None = None,
    domain: str | None = None,
    trait: str | None = None,
    source_type: str | None = None,
) -> list[DecisionCase]:
    filters = DecisionCaseFilters(
        person=person,
        domain=domain,
        traits=[trait] if trait else None,
        source_type=source_type,
    )
    return request.app.state.services.repository.list_cases(filters=filters, limit=200)


@router.post("/ingest/demo")
def ingest_demo(request: Request) -> dict[str, int]:
    services = request.app.state.services
    count = services.ingestion.ingest_jsonl(services.settings.sample_dataset_path)
    return {"ingested": count}


@router.post("/ingest/cases")
def ingest_cases(request: Request, cases: list[DecisionCase]) -> dict[str, int]:
    if not cases:
        raise HTTPException(status_code=400, detail="Provide at least one decision case.")
    request.app.state.services.ingestion.ingest_cases(cases)
    return {"ingested": len(cases)}


@router.post("/chat", response_model=ChatResponse)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    return request.app.state.services.engine.answer(payload)
