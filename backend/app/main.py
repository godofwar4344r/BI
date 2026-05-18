from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.core.rate_limit import InMemoryRateLimiter
from app.db.models import Base
from app.db.session import build_engine, build_session_factory
from app.repositories.cases import SqlAlchemyDecisionCaseRepository
from app.services.analytics import InMemoryAnalytics
from app.services.bi_engine import BIEngine
from app.services.embeddings import HashEmbeddingProvider
from app.services.ingestion import DecisionCaseIngestionService
from app.services.retrieval import RetrievalService
from app.services.synthesis import AnswerSynthesizer
from app.services.vector_store import build_vector_store


@dataclass(slots=True)
class AppServices:
    settings: Settings
    repository: SqlAlchemyDecisionCaseRepository
    ingestion: DecisionCaseIngestionService
    retrieval: RetrievalService
    synthesizer: AnswerSynthesizer
    analytics: InMemoryAnalytics
    engine: BIEngine


def build_services(settings: Settings) -> AppServices:
    engine = build_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    session_factory = build_session_factory(engine)
    repository = SqlAlchemyDecisionCaseRepository(session_factory)
    embeddings = HashEmbeddingProvider(dimensions=settings.embedding_dimensions)
    vector_store = build_vector_store(settings)
    ingestion = DecisionCaseIngestionService(repository, vector_store, embeddings)
    retrieval = RetrievalService(
        repository=repository,
        vector_store=vector_store,
        embeddings=embeddings,
        default_top_k=settings.retrieval_top_k,
    )
    prompt_path = Path(__file__).resolve().parent / "prompts" / "bi_answer_prompt.md"
    synthesizer = AnswerSynthesizer(prompt_template_path=prompt_path)
    analytics = InMemoryAnalytics()
    bi_engine = BIEngine(retrieval=retrieval, synthesizer=synthesizer, analytics=analytics)
    return AppServices(
        settings=settings,
        repository=repository,
        ingestion=ingestion,
        retrieval=retrieval,
        synthesizer=synthesizer,
        analytics=analytics,
        engine=bi_engine,
    )


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    configure_logging(active_settings.environment)
    services = build_services(active_settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.services.ingestion.seed_if_empty(active_settings.sample_dataset_path)
        yield

    app = FastAPI(
        title="BI API",
        description="Decision-pattern retrieval and synthesis for founder/investor decisions.",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.services = services
    app.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.middleware("http")(InMemoryRateLimiter(active_settings.rate_limit_per_minute))
    app.include_router(router)
    return app


app = create_app()
