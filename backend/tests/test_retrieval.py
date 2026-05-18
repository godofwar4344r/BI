from pathlib import Path

from app.core.config import Settings
from app.main import build_services
from app.models.chat import ChatRequest


ROOT = Path(__file__).resolve().parents[2]


def test_engine_returns_supporting_cases(tmp_path) -> None:
    db_path = tmp_path / "bi_test.db"
    services = build_services(Settings(database_url=f"sqlite:///{db_path.as_posix()}"))
    services.ingestion.ingest_jsonl(ROOT / "data" / "sample_decision_cases.jsonl")

    response = services.engine.answer(
        ChatRequest(query="Should we hire now or automate the workflow first?")
    )

    assert response.retrieved_count > 0
    assert response.answer.recommendation
    assert response.answer.supporting_cases
    assert "hire" in response.answer.weak_thinker_alternative.lower()
