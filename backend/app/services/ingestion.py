from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.models.decision_case import DecisionCase, DecisionCaseFilters
from app.repositories.cases import SqlAlchemyDecisionCaseRepository
from app.services.chunking import chunk_text
from app.services.embeddings import EmbeddingProvider
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)


class DecisionCaseIngestionService:
    def __init__(
        self,
        repository: SqlAlchemyDecisionCaseRepository,
        vector_store: VectorStore,
        embeddings: EmbeddingProvider,
    ) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.embeddings = embeddings

    def seed_if_empty(self, dataset_path: Path) -> int:
        if self.repository.count() > 0:
            self.rebuild_index()
            return 0
        return self.ingest_jsonl(dataset_path)

    def ingest_jsonl(self, path: Path) -> int:
        cases = load_cases_from_jsonl(path)
        self.ingest_cases(cases)
        logger.info("Ingested %s decision cases from %s", len(cases), path)
        return len(cases)

    def ingest_cases(self, cases: list[DecisionCase]) -> None:
        self.repository.upsert_many(cases)
        for case in cases:
            self.index_case(case)

    def rebuild_index(self, filters: DecisionCaseFilters | None = None) -> int:
        self.vector_store.clear()
        cases = self.repository.list_cases(filters=filters, limit=1000)
        for case in cases:
            self.index_case(case)
        return len(cases)

    def index_case(self, case: DecisionCase) -> None:
        self.vector_store.upsert(
            case_id=case.id,
            vector=self.embeddings.embed(case_to_search_text(case)),
            metadata={
                "person": case.person,
                "domain": case.domain,
                "source_type": case.source_type,
                "traits": [trait.name for trait in case.traits],
                "confidence": case.confidence,
            },
        )

    def chunk_document(self, text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
        return chunk_text(text, chunk_size=chunk_size, overlap=overlap)


def load_cases_from_jsonl(path: Path) -> list[DecisionCase]:
    if not path.exists():
        raise FileNotFoundError(f"Decision case dataset not found: {path}")

    cases: list[DecisionCase] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload: dict[str, Any] = json.loads(stripped)
                cases.append(DecisionCase.model_validate(payload))
            except Exception as exc:
                raise ValueError(f"Invalid decision case at {path}:{line_number}") from exc
    return cases


def case_to_search_text(case: DecisionCase) -> str:
    trait_text = " ".join(
        f"{trait.name} {trait.score} {trait.evidence or ''}" for trait in case.traits
    )
    tradeoff_text = " ".join(case.tradeoffs)
    return " ".join(
        [
            case.person,
            case.domain,
            case.context,
            case.decision,
            case.reasoning,
            trait_text,
            tradeoff_text,
            case.outcome,
            case.lesson,
            case.source_type,
            case.source_reference,
        ]
    )
