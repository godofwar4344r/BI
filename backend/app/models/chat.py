from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.decision_case import DecisionCaseFilters


class ChatRequest(BaseModel):
    query: str = Field(min_length=3, max_length=2000)
    filters: DecisionCaseFilters | None = None
    top_k: int | None = Field(default=None, ge=1, le=12)


class SupportingCase(BaseModel):
    id: str
    person: str
    domain: str
    decision: str
    lesson: str
    source_type: str
    source_reference: str
    confidence: float
    retrieval_score: float
    traits: dict[str, int]


class BIAnswer(BaseModel):
    recommendation: str
    reasoning: list[str]
    tradeoffs: list[str]
    risks: list[str]
    weak_thinker_alternative: str
    next_step: str
    supporting_cases: list[SupportingCase]
    trait_scores: dict[str, float]
    guardrail_note: str | None = None
    agentic_workflow: list[dict[str, str]] = Field(default_factory=list)
    billionaire_time_saver: str = ""


class ChatResponse(BaseModel):
    answer: BIAnswer
    intent: dict[str, object]
    retrieved_count: int
    analytics_event_id: str | None = None
