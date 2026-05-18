from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


TraitName = Literal[
    "long_term_thinking",
    "risk_tolerance",
    "speed_of_action",
    "leverage_orientation",
    "discipline",
    "frugality",
    "hiring_instinct",
    "market_intuition",
    "resilience",
    "contrarian_judgment",
    "simplicity",
    "capital_efficiency",
    "narrative_power",
    "execution_intensity",
]

SUPPORTED_TRAITS: tuple[str, ...] = (
    "long_term_thinking",
    "risk_tolerance",
    "speed_of_action",
    "leverage_orientation",
    "discipline",
    "frugality",
    "hiring_instinct",
    "market_intuition",
    "resilience",
    "contrarian_judgment",
    "simplicity",
    "capital_efficiency",
    "narrative_power",
    "execution_intensity",
)

SourceType = Literal[
    "biography",
    "interview",
    "letter",
    "talk",
    "filing",
    "public_writing",
    "shareholder_letter",
    "annual_report",
]


class TraitScore(BaseModel):
    name: TraitName
    score: int = Field(ge=1, le=5)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    evidence: str | None = None


class DecisionCase(BaseModel):
    id: str = Field(min_length=3, max_length=120)
    person: str = Field(min_length=2, max_length=120)
    domain: str = Field(min_length=2, max_length=80)
    context: str = Field(min_length=10)
    decision: str = Field(min_length=5)
    reasoning: str = Field(min_length=10)
    traits: list[TraitScore] = Field(default_factory=list)
    tradeoffs: list[str] = Field(default_factory=list)
    outcome: str = Field(min_length=5)
    lesson: str = Field(min_length=5)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    source_type: SourceType
    source_reference: str = Field(min_length=3)
    timestamp: datetime | None = None

    @field_validator("domain", "person")
    @classmethod
    def strip_names(cls, value: str) -> str:
        return value.strip()

    @field_validator("tradeoffs")
    @classmethod
    def strip_tradeoffs(cls, values: list[str]) -> list[str]:
        return [value.strip() for value in values if value.strip()]


class DecisionCaseFilters(BaseModel):
    person: str | None = None
    domain: str | None = None
    traits: list[TraitName] | None = None
    source_type: SourceType | None = None


class ScoredDecisionCase(BaseModel):
    case: DecisionCase
    score: float = Field(ge=0.0)
    matched_traits: list[TraitName] = Field(default_factory=list)
