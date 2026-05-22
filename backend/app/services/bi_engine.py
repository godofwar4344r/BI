from __future__ import annotations

from app.models.chat import ChatRequest, ChatResponse
from app.services.analytics import InMemoryAnalytics
from app.services.retrieval import RetrievalService
from app.services.synthesis import AnswerSynthesizer


class BIEngine:
    def __init__(
        self,
        retrieval: RetrievalService,
        synthesizer: AnswerSynthesizer,
        analytics: InMemoryAnalytics,
    ) -> None:
        self.retrieval = retrieval
        self.synthesizer = synthesizer
        self.analytics = analytics

    def answer(self, request: ChatRequest) -> ChatResponse:
        filters = request.filters
        if request.model == "elon_musk":
            from app.models.decision_case import DecisionCaseFilters
            if filters is None:
                filters = DecisionCaseFilters(person="Elon Musk")
            else:
                filters = filters.model_copy(update={"person": "Elon Musk"})

        retrieval_result = self.retrieval.retrieve(
            query=request.query,
            filters=filters,
            top_k=request.top_k,
        )
        answer = self.synthesizer.synthesize(request.query, retrieval_result, model=request.model)
        event_id = self.analytics.record_chat(
            query=request.query,
            domain=retrieval_result.intent.domain,
            retrieved_count=len(retrieval_result.cases),
        )
        return ChatResponse(
            answer=answer,
            intent=retrieval_result.intent.model_dump(),
            retrieved_count=len(retrieval_result.cases),
            analytics_event_id=event_id,
        )
