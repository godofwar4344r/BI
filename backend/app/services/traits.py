from __future__ import annotations

from app.models.decision_case import ScoredDecisionCase, TraitName


def case_trait_map(case_traits: list) -> dict[str, int]:
    return {trait.name: trait.score for trait in case_traits}


def score_trait_match(case_traits: list, desired_traits: list[TraitName]) -> float:
    if not desired_traits:
        return 0.0
    by_name = {trait.name: trait for trait in case_traits}
    matched = [
        (by_name[trait].score / 5.0) * by_name[trait].confidence
        for trait in desired_traits
        if trait in by_name
    ]
    return sum(matched) / len(desired_traits) if matched else 0.0


def aggregate_trait_scores(cases: list[ScoredDecisionCase]) -> dict[str, float]:
    totals: dict[str, float] = {}
    weights: dict[str, float] = {}
    for scored in cases:
        retrieval_weight = max(scored.score, 0.05)
        for trait in scored.case.traits:
            weight = trait.confidence * retrieval_weight
            totals[trait.name] = totals.get(trait.name, 0.0) + trait.score * weight
            weights[trait.name] = weights.get(trait.name, 0.0) + weight
    return {
        name: round(totals[name] / weights[name], 2)
        for name in sorted(totals)
        if weights[name] > 0
    }
