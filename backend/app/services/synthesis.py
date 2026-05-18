from __future__ import annotations

from pathlib import Path

from app.models.chat import BIAnswer, SupportingCase
from app.models.decision_case import ScoredDecisionCase
from app.services.classifier import ClassifiedIntent
from app.services.retrieval import RetrievalResult
from app.services.traits import aggregate_trait_scores, case_trait_map


DOMAIN_RECOMMENDATIONS = {
    "build_vs_buy": "Build or own the capability when it is a strategic bottleneck; buy a vendor when it is commodity work that does not compound your advantage.",
    "fundraising": "Raise only if outside capital clearly accelerates a validated advantage; otherwise use constraints to sharpen the model first.",
    "hiring": "Hire for the highest-leverage bottleneck only after simplifying the work and proving it cannot be automated or outsourced cleanly.",
    "capital_allocation": "Protect downside, keep cash flexible, and concentrate spending only where the payoff can compound.",
    "execution": "Move fast on reversible choices, but slow down on one-way decisions that can permanently damage trust, cash, or focus.",
    "market_strategy": "Follow durable customer pull and build a narrative around a real wedge, not around vanity momentum.",
    "m_and_a": "Acquire only when price, integration, and strategic control improve the moat more than organic execution would.",
    "risk_management": "Use inversion: define how this fails first, then size the bet so survival and reputation are never at risk.",
    "general_strategy": "Choose the move that compounds advantage while preserving integrity, cash flexibility, and learning speed.",
}

NEXT_STEPS = {
    "build_vs_buy": "Write a build-vs-buy memo: strategic control, switching cost, speed, integration risk, total cost, and what learning you would lose by outsourcing.",
    "fundraising": "Write a one-page capital memo: exact use of funds, milestone unlocked, dilution cost, fallback bootstrap path, and the kill criteria.",
    "hiring": "Map the bottleneck, automate one repetitive step, then run a two-week trial project before committing to a full-time hire.",
    "capital_allocation": "Create three budgets: default conserve, focused bet, and aggressive bet; pick the smallest one that can prove the thesis.",
    "execution": "Classify the decision as one-way or two-way, ship the reversible test within 72 hours, and set a review metric now.",
    "market_strategy": "Interview five target customers, extract the repeated pain language, and test one positioning claim before scaling spend.",
    "m_and_a": "Build a buy-vs-build memo with integration risk, retention risk, price discipline, and the organic alternative side by side.",
    "risk_management": "Pre-mortem the decision, name the top three failure modes, and cap exposure before action.",
    "general_strategy": "Draft a decision memo with upside, downside, reversibility, evidence, and the next measurable action.",
}

WEAK_ALTERNATIVES = {
    "build_vs_buy": "Buy a vendor to avoid hard product thinking, or build internally because ownership feels impressive rather than strategically necessary.",
    "fundraising": "Raise because it feels prestigious, then let a larger bank balance hide weak unit economics.",
    "hiring": "Hire headcount to feel momentum without clarifying the bottleneck or manager capacity.",
    "capital_allocation": "Spend broadly across many plausible ideas instead of concentrating on one compounding edge.",
    "execution": "Wait for certainty on reversible choices, then rush irreversible ones under pressure.",
    "market_strategy": "Copy a famous company's narrative without matching its customer evidence or distribution position.",
    "m_and_a": "Buy growth to avoid hard execution work, while underestimating integration and culture risk.",
    "risk_management": "Treat boldness as wisdom and ignore survival, legality, and reputation.",
    "general_strategy": "Copy a billionaire anecdote without checking context, constraints, or ethical boundaries.",
}


class AnswerSynthesizer:
    def __init__(self, prompt_template_path: Path) -> None:
        self.prompt_template_path = prompt_template_path
        self.prompt_template = prompt_template_path.read_text(encoding="utf-8")

    def synthesize(self, query: str, retrieval: RetrievalResult) -> BIAnswer:
        intent = retrieval.intent
        cases = retrieval.cases
        if intent.ethical_risk:
            return self._guardrailed_answer(query=query, intent=intent, cases=cases)
        if not cases:
            return self._empty_answer(query=query, intent=intent)

        top_cases = cases[:3]
        recommendation = DOMAIN_RECOMMENDATIONS.get(intent.domain, DOMAIN_RECOMMENDATIONS["general_strategy"])
        reasoning = build_reasoning(top_cases)
        tradeoffs = unique_lines([line for scored in top_cases for line in scored.case.tradeoffs])[:5]
        if not tradeoffs:
            tradeoffs = ["The pattern may not transfer if your market, timing, or resources differ."]
        risks = build_risks(intent, top_cases)
        return BIAnswer(
            recommendation=recommendation,
            reasoning=reasoning,
            tradeoffs=tradeoffs,
            risks=risks,
            weak_thinker_alternative=WEAK_ALTERNATIVES.get(
                intent.domain, WEAK_ALTERNATIVES["general_strategy"]
            ),
            next_step=NEXT_STEPS.get(intent.domain, NEXT_STEPS["general_strategy"]),
            supporting_cases=[to_supporting_case(scored) for scored in cases],
            trait_scores=aggregate_trait_scores(cases),
            guardrail_note="This is decision support, not a claim that wealth equals wisdom.",
        )

    def build_prompt(self, query: str, retrieval: RetrievalResult) -> str:
        case_blocks = "\n\n".join(
            f"- {item.case.person} / {item.case.domain}: {item.case.decision}\n"
            f"  Reasoning: {item.case.reasoning}\n"
            f"  Lesson: {item.case.lesson}\n"
            f"  Source: {item.case.source_type} - {item.case.source_reference}"
            for item in retrieval.cases
        )
        return self.prompt_template.format(
            query=query,
            intent=retrieval.intent.model_dump(),
            cases=case_blocks or "No supporting cases retrieved.",
        )

    def _empty_answer(self, query: str, intent: ClassifiedIntent) -> BIAnswer:
        return BIAnswer(
            recommendation="I do not have enough supporting cases in the current knowledge base to make a confident BI recommendation.",
            reasoning=[
                f"The query was classified as {intent.domain}, but retrieval returned no evidence-backed cases.",
                "Add or ingest relevant decision cases before relying on a strategic answer.",
            ],
            tradeoffs=["Answering anyway would risk hallucinating specifics not present in the corpus."],
            risks=["A thin knowledge base can overfit to generic advice."],
            weak_thinker_alternative="Pretend confidence and manufacture a famous-founder answer without evidence.",
            next_step="Ingest three to five sourced cases for this domain, then ask again.",
            supporting_cases=[],
            trait_scores={},
            guardrail_note="BI avoids unsupported specifics when retrieval is empty.",
        )

    def _guardrailed_answer(
        self,
        query: str,
        intent: ClassifiedIntent,
        cases: list[ScoredDecisionCase],
    ) -> BIAnswer:
        return BIAnswer(
            recommendation="Do not pursue illegal, deceptive, fraudulent, or manipulative tactics. Reframe the decision around lawful advantage, transparency, customer value, and downside control.",
            reasoning=[
                "The query contains terms associated with unethical or illegal conduct.",
                "BI can analyze risk, incentives, and strategic alternatives, but it will not glorify or operationalize misconduct.",
            ],
            tradeoffs=[
                "Ethical constraints may slow some shortcuts, but they preserve trust, optionality, and enterprise value.",
                "Transparent tactics are easier to defend with employees, investors, customers, and regulators.",
            ],
            risks=[
                "Fraud or manipulation can create legal exposure, reputational damage, and permanent loss of trust.",
                "Short-term wins from deception usually destroy compounding advantage.",
            ],
            weak_thinker_alternative="Seek a clever loophole instead of building a durable, legal edge.",
            next_step="State the legitimate business objective, list compliant paths to reach it, and choose the path with the best risk-adjusted upside.",
            supporting_cases=[to_supporting_case(scored) for scored in cases],
            trait_scores=aggregate_trait_scores(cases),
            guardrail_note="Guardrail triggered: BI refuses to assist illegal or unethical conduct.",
        )


def build_reasoning(cases: list[ScoredDecisionCase]) -> list[str]:
    lines: list[str] = []
    for scored in cases:
        case = scored.case
        lines.append(
            f"{case.person}: {case.lesson} This supports the move because {case.reasoning.lower()}"
        )
    return lines


def build_risks(intent: ClassifiedIntent, cases: list[ScoredDecisionCase]) -> list[str]:
    risks = [
        "Do not transfer a famous decision mechanically; match the original constraints before copying the move.",
        "The retrieved cases are evidence inputs, not guarantees of outcome.",
    ]
    if intent.domain in {"fundraising", "capital_allocation"}:
        risks.append("Mis-sizing the bet can turn a good thesis into a cash-flow problem.")
    if intent.domain == "hiring":
        risks.append("A great hire still fails if the role, ownership, and operating cadence are unclear.")
    if any(scored.case.confidence < 0.7 for scored in cases):
        risks.append("At least one supporting case has lower confidence and should be treated as directional.")
    return risks


def to_supporting_case(scored: ScoredDecisionCase) -> SupportingCase:
    case = scored.case
    return SupportingCase(
        id=case.id,
        person=case.person,
        domain=case.domain,
        decision=case.decision,
        lesson=case.lesson,
        source_type=case.source_type,
        source_reference=case.source_reference,
        confidence=case.confidence,
        retrieval_score=scored.score,
        traits=case_trait_map(case.traits),
    )


def unique_lines(lines: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        normalized = line.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(line.strip())
    return output
