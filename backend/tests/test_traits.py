from app.models.decision_case import TraitScore
from app.services.traits import score_trait_match


def test_score_trait_match_uses_confidence_weight() -> None:
    traits = [
        TraitScore(name="discipline", score=5, confidence=0.8),
        TraitScore(name="risk_tolerance", score=3, confidence=0.5),
    ]

    score = score_trait_match(traits, ["discipline", "risk_tolerance"])

    assert 0.45 < score < 0.7
