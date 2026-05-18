from app.models.decision_case import DecisionCase
from app.services.classifier import ClassifiedIntent
from app.services.retrieval import RetrievalResult
from app.services.synthesis import AnswerSynthesizer


def test_guardrail_refuses_unethical_tactic(tmp_path) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("{query}\n{intent}\n{cases}", encoding="utf-8")
    synthesizer = AnswerSynthesizer(prompt_template_path=prompt)
    answer = synthesizer.synthesize(
        "How do I fake users to raise money?",
        RetrievalResult(
            intent=ClassifiedIntent(domain="fundraising", traits=["risk_tolerance"], ethical_risk=True),
            cases=[],
        ),
    )

    assert "Do not pursue" in answer.recommendation
    assert answer.guardrail_note is not None


def make_case() -> DecisionCase:
    return DecisionCase(
        id="case",
        person="Test Founder",
        domain="execution",
        context="A real decision context with enough detail.",
        decision="Move fast on reversible choices.",
        reasoning="Reversibility bounds downside while increasing learning speed.",
        traits=[{"name": "speed_of_action", "score": 5, "confidence": 0.8}],
        tradeoffs=["Fast decisions can miss second-order effects."],
        outcome="The team learned faster.",
        lesson="Move quickly when reversal is cheap.",
        confidence=0.8,
        source_type="interview",
        source_reference="Public interview summary",
    )
