from __future__ import annotations

from pydantic import BaseModel

from app.models.decision_case import DecisionCaseFilters, ScoredDecisionCase, TraitName
from app.repositories.cases import SqlAlchemyDecisionCaseRepository
from app.services.classifier import ClassifiedIntent, classify_intent
from app.services.embeddings import EmbeddingProvider
from app.services.traits import score_trait_match
from app.services.vector_store import VectorStore


class RetrievalResult(BaseModel):
    intent: ClassifiedIntent
    cases: list[ScoredDecisionCase]


class RetrievalService:
    def __init__(
        self,
        repository: SqlAlchemyDecisionCaseRepository,
        vector_store: VectorStore,
        embeddings: EmbeddingProvider,
        default_top_k: int,
    ) -> None:
        self.repository = repository
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.default_top_k = default_top_k

    def retrieve(
        self,
        query: str,
        filters: DecisionCaseFilters | None = None,
        top_k: int | None = None,
    ) -> RetrievalResult:
        intent = classify_intent(query, known_people=self.repository.people())
        effective_filters = merge_filters(filters, intent)
        limit = top_k or self.default_top_k
        query_text = " ".join([query, intent.domain, " ".join(intent.traits)])
        vector_hits = self.vector_store.search(
            self.embeddings.embed(query_text),
            top_k=limit * 4,
            filters=effective_filters,
        )
        case_lookup = self.repository.get_many(hit.case_id for hit in vector_hits)

        scores: dict[str, float] = {}
        matched_traits: dict[str, list[TraitName]] = {}
        for hit in vector_hits:
            case = case_lookup.get(hit.case_id)
            if not case:
                continue
            scores[case.id] = scores.get(case.id, 0.0) + max(hit.score, 0.0) * 0.65
            matched_traits[case.id] = [
                trait.name for trait in case.traits if trait.name in intent.traits
            ]

        for case in self.repository.trait_matches(intent.traits, filters=effective_filters, limit=limit * 4):
            trait_score = score_trait_match(case.traits, intent.traits)
            scores[case.id] = scores.get(case.id, 0.0) + trait_score * 0.25
            matched_traits[case.id] = [
                trait.name for trait in case.traits if trait.name in intent.traits
            ]
            case_lookup[case.id] = case

        if not scores:
            fallback_cases = self.repository.list_cases(filters=effective_filters, limit=limit)
            for case in fallback_cases:
                scores[case.id] = 0.1 + case.confidence * 0.05
                case_lookup[case.id] = case
                matched_traits[case.id] = []

        for case_id, case in case_lookup.items():
            if case_id not in scores:
                continue
            if case.domain == intent.domain:
                scores[case_id] += 0.08
            scores[case_id] += case.confidence * 0.05

        scored = [
            ScoredDecisionCase(
                case=case_lookup[case_id],
                score=round(score, 4),
                matched_traits=matched_traits.get(case_id, []),
            )
            for case_id, score in scores.items()
            if case_id in case_lookup
        ]
        scored.sort(key=lambda item: item.score, reverse=True)
        return RetrievalResult(intent=intent, cases=scored[:limit])


def merge_filters(
    requested: DecisionCaseFilters | None,
    intent: ClassifiedIntent,
) -> DecisionCaseFilters | None:
    if requested is None and intent.detected_person is None:
        return None
    return DecisionCaseFilters(
        person=requested.person if requested and requested.person else intent.detected_person,
        domain=requested.domain if requested else None,
        traits=requested.traits if requested else None,
        source_type=requested.source_type if requested else None,
    )
