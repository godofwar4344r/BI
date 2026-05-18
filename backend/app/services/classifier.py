from __future__ import annotations

import re

from pydantic import BaseModel

from app.models.decision_case import TraitName


DOMAIN_KEYWORDS: dict[str, set[str]] = {
    "build_vs_buy": {"build", "buy", "vendor", "internal", "outsource", "capability"},
    "fundraising": {"raise", "fundraise", "vc", "investor", "bootstrap", "dilution"},
    "hiring": {"hire", "talent", "team", "recruit", "people", "manager", "automate"},
    "capital_allocation": {"spend", "conserve", "cash", "budget", "allocate", "capex", "margin"},
    "execution": {"speed", "launch", "ship", "iterate", "deadline", "decision"},
    "market_strategy": {"market", "customer", "pricing", "position", "narrative", "category"},
    "m_and_a": {"acquire", "acquisition", "buy", "merge", "rollup"},
    "risk_management": {"risk", "downside", "fragile", "regulation", "compliance"},
}

PERSON_STOPWORDS = {"and", "the", "with", "for"}
WORD_RE = re.compile(r"\b[a-z][a-z0-9+-]{2,}\b")

TRAIT_KEYWORDS: dict[TraitName, set[str]] = {
    "long_term_thinking": {"long-term", "durable", "compound", "moat", "decade"},
    "risk_tolerance": {"risk", "bold", "bet", "uncertain", "downside"},
    "speed_of_action": {"fast", "speed", "quick", "ship", "iterate"},
    "leverage_orientation": {"leverage", "platform", "distribution", "software", "automation"},
    "discipline": {"discipline", "focus", "avoid", "say no", "constraint"},
    "frugality": {"frugal", "conserve", "bootstrap", "burn", "cash"},
    "hiring_instinct": {"hire", "talent", "team", "operator", "recruit"},
    "market_intuition": {"market", "customer", "demand", "timing", "category"},
    "resilience": {"resilience", "survive", "crisis", "hard", "failure"},
    "contrarian_judgment": {"contrarian", "against consensus", "non-obvious", "unpopular"},
    "simplicity": {"simple", "simplify", "clear", "focus"},
    "capital_efficiency": {"efficient", "roi", "cash", "margin", "bootstrap"},
    "narrative_power": {"story", "narrative", "positioning", "mission"},
    "execution_intensity": {"intensity", "execution", "operate", "cadence", "urgency"},
}

ETHICAL_RISK_KEYWORDS = {
    "fraud",
    "bribe",
    "insider trading",
    "manipulate",
    "fake users",
    "mislead",
    "illegal",
    "evade",
    "deceive",
    "pump and dump",
}


class ClassifiedIntent(BaseModel):
    domain: str
    traits: list[TraitName]
    ethical_risk: bool = False
    raw_intent: str = "decision_support"
    detected_person: str | None = None


def classify_intent(query: str, known_people: list[str] | None = None) -> ClassifiedIntent:
    normalized = query.lower()
    query_tokens = set(WORD_RE.findall(normalized))
    domain = "general_strategy"
    best_hits = 0
    for candidate, keywords in DOMAIN_KEYWORDS.items():
        hits = sum(1 for keyword in keywords if keyword in normalized)
        if hits > best_hits:
            best_hits = hits
            domain = candidate

    traits: list[TraitName] = []
    for trait, keywords in TRAIT_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            traits.append(trait)

    if not traits:
        traits = ["long_term_thinking", "discipline", "risk_tolerance"]

    detected_person = None
    for person in known_people or []:
        parts = [
            part.lower()
            for part in WORD_RE.findall(person.lower())
            if part.lower() not in PERSON_STOPWORDS
        ]
        if person.lower() in normalized or any(part in query_tokens for part in parts):
            detected_person = person
            break

    ethical_risk = any(keyword in normalized for keyword in ETHICAL_RISK_KEYWORDS)
    return ClassifiedIntent(
        domain=domain,
        traits=list(dict.fromkeys(traits)),
        ethical_risk=ethical_risk,
        detected_person=detected_person,
    )
