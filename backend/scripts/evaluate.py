from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / "backend"))

from app.core.config import Settings  # noqa: E402
from app.models.chat import ChatRequest  # noqa: E402
from app.main import build_services  # noqa: E402


@dataclass(frozen=True)
class Scenario:
    name: str
    query: str
    expected_terms: tuple[str, ...]


SCENARIOS = (
    Scenario(
        name="bootstrap_vs_raise",
        query="Should I bootstrap longer or raise money now?",
        expected_terms=("capital", "cash", "dilution", "long-term", "risk"),
    ),
    Scenario(
        name="hire_vs_automate",
        query="Should I hire a senior operator or automate the workflow first?",
        expected_terms=("hire", "automate", "bottleneck", "leverage", "team"),
    ),
    Scenario(
        name="spend_vs_conserve",
        query="Should we spend aggressively for growth or conserve cash?",
        expected_terms=("cash", "downside", "budget", "compound", "risk"),
    ),
    Scenario(
        name="build_vs_buy",
        query="Should we build this capability internally or buy a vendor?",
        expected_terms=("bottleneck", "leverage", "cost", "speed", "risk"),
    ),
    Scenario(
        name="expand_vs_consolidate",
        query="Should we expand into a new market or consolidate the core product?",
        expected_terms=("market", "customer", "focus", "trade", "risk"),
    ),
    Scenario(
        name="acquire_vs_organic",
        query="Should we acquire a small competitor or grow organically?",
        expected_terms=("acquire", "price", "integration", "organic", "risk"),
    ),
)


def main() -> None:
    eval_db = ROOT / "backend" / "data" / "bi_eval.db"
    services = build_services(Settings(database_url=f"sqlite:///{eval_db.as_posix()}"))
    services.ingestion.seed_if_empty(ROOT / "data" / "sample_decision_cases.jsonl")

    results = []
    for scenario in SCENARIOS:
        response = services.engine.answer(ChatRequest(query=scenario.query))
        text = json.dumps(response.answer.model_dump()).lower()
        term_hits = sum(1 for term in scenario.expected_terms if term.lower() in text)
        support_count = len(response.answer.supporting_cases)
        risk_count = len(response.answer.risks)
        scores = {
            "clarity": score_between(bool(response.answer.recommendation), 3, 5),
            "leverage": score_terms(text, ("leverage", "compound", "platform", "bottleneck")),
            "realism": score_between(support_count >= 2, 3, 5),
            "risk_awareness": min(5, 2 + risk_count),
            "usefulness": score_between(bool(response.answer.next_step), 3, 5),
            "decision_quality": min(5, 2 + term_hits),
        }
        results.append(
            {
                "scenario": scenario.name,
                "query": scenario.query,
                "scores": scores,
                "retrieved_cases": [case.id for case in response.answer.supporting_cases],
                "recommendation": response.answer.recommendation,
            }
        )

    print(json.dumps(results, indent=2))


def score_terms(text: str, terms: tuple[str, ...]) -> int:
    hits = sum(1 for term in terms if term in text)
    return min(5, 2 + hits)


def score_between(condition: bool, low: int, high: int) -> int:
    return high if condition else low


if __name__ == "__main__":
    main()
