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

AGENTIC_WORKFLOWS = {
    "build_vs_buy": [
        {"phase": "Phase 1: The Bottleneck Assessor", "agent": "Core Moat Auditor", "action": "Map core capabilities. Determine if this system is a strategic competitive advantage. Veto internal building if it is a commodity utility function."},
        {"phase": "Phase 2: The Cost-of-Learning Auditor", "agent": "Friction Architect", "action": "Calculate switching and integration overhead. Compute the rate of developer learning lost by outsourcing vs internal execution speed."},
        {"phase": "Phase 3: The 48-Hour Pilot Agent", "agent": "Speed Catalyst", "action": "Launch a manual pilot (using existing third-party tools or mocks) in under 48 hours to establish a baseline performance benchmark."}
    ],
    "fundraising": [
        {"phase": "Phase 1: The Bootstrap Stress-Tester", "agent": "Capital Guardian", "action": "Audit current operational expenses. Determine if cost constraints or workflow optimizations can prolong runway by 6 months without external dilution."},
        {"phase": "Phase 2: The Dilution Auditor", "agent": "Sovereignty Protector", "action": "Project ownership dilution over 3 funding cycles. Weigh equity dilution cost against the clear acceleration factor of venture funds."},
        {"phase": "Phase 3: The Narrative Builder", "agent": "Wedge Pitcher", "action": "Draft a one-page capital milestone memo. Target 3 major customers to secure written Letters of Intent (LOIs) before pitching investors."}
    ],
    "hiring": [
        {"phase": "Phase 1: The Friction Isolator", "agent": "Bottleneck Analyst", "action": "Perform a task audit on the bottlenecked workflow. Prove the role cannot be automated, outsourced, or eliminated through simplified requirements."},
        {"phase": "Phase 2: The Trial Project Director", "agent": "Peer Assessor", "action": "Design a paid 2-week contract project representing real work. Bypass standard multi-stage whiteboard interviews to evaluate candidate execution directly."},
        {"phase": "Phase 3: The Talent Compounder", "agent": "Bar Keeper", "action": "Require a unanimous yes from the immediate peers of the candidate. Keep technical density high by preventing manager-only hiring decisions."}
    ],
    "capital_allocation": [
        {"phase": "Phase 1: The Downside Capper", "agent": "Inversion Auditor", "action": "Pre-mortem the bet: write the post-mortem of complete loss. Size the capital tranche so that total failure does not threaten corporate survival or brand reputation."},
        {"phase": "Phase 2: The Compounding Assessor", "agent": "Lease-Time Auditor", "action": "Rank all current initiatives by ROI. Veto projects with non-compounding returns. Consolidate cash for high-leverage bets."},
        {"phase": "Phase 3: The Exit Criteria Monitor", "agent": "Automated Veto Guard", "action": "Set strict kill triggers. De-allocate capital if the project does not hit its milestones in the first 3 tranches."}
    ],
    "execution": [
        {"phase": "Phase 1: The Door Classifier", "agent": "Reversibility Scout", "action": "Classify the choice: is it a One-Way door (irreversible, high cost) or a Two-Way door (reversible, low cost)?"},
        {"phase": "Phase 2: The 72-Hour Prototyper", "agent": "Tempo Enforcer", "action": "If reversible, enforce a 10-minute decision constraint. Launch a simplified prototype within 72 hours with 70% of necessary data."},
        {"phase": "Phase 3: The Feedback Loop Auditor", "agent": "Metric Evaluator", "action": "Monitor day 7 conversion metrics. Kill the experiment immediately if user engagement does not match standard baseline thresholds."}
    ],
    "market_strategy": [
        {"phase": "Phase 1: The Wedge Investigator", "agent": "Pain Auditor", "action": "Interview 5 target customers. Isolate their exact vocabulary for describing their main problem, and use this word-for-word in the headline copy."},
        {"phase": "Phase 2: The Customer Pull Monitor", "agent": "Retention Guardian", "action": "Validate organic referral. Check if early cohorts are recommending the service without artificial marketing spend."},
        {"phase": "Phase 3: The Scale Accelerator", "agent": "Distribution Architect", "action": "Only scale distribution budgets after retention loops are stable and referral loops exceed a factor of 1.0."}
    ],
    "m_and_a": [
        {"phase": "Phase 1: The Pre-Mortem Integration Agent", "agent": "Culture Assessor", "action": "Assume the integration fails immediately. Estimate the total cost of key employee attrition and product codebase rewrite."},
        {"phase": "Phase 2: The Moat Validator", "agent": "Synergy Inspector", "action": "Verify if acquiring the asset boosts pricing power or cost advantages faster than organic developer building."},
        {"phase": "Phase 3: The Price Cap Guard", "agent": "Negotiation Referee", "action": "Enforce a hard walk-away ceiling. Prevent bidder's ego and transaction momentum from inflating the price."}
    ],
    "risk_management": [
        {"phase": "Phase 1: The Inversion Specialist", "agent": "Doom Analyst", "action": "Identify the top 3 ways this decision results in bankruptcy or catastrophic loss. Focus on leverage traps and legal compliance."},
        {"phase": "Phase 2: The Redundancy Architect", "agent": "Systemic Shield", "action": "Set up independent backups and capital reserves to ensure survival even in a 1-in-100 year market shock."},
        {"phase": "Phase 3: The Reputation Gatekeeper", "agent": "Ethics Auditor", "action": "Vet the decision against core reputation. Veto the opportunity if it has regulatory, legal, or ethical vulnerabilities."}
    ],
    "general_strategy": [
        {"phase": "Phase 1: The First Principles Auditor", "agent": "Core Strategist", "action": "Strip away analogies. Break the problem down into its fundamental physics/economic components and build the solution from there."},
        {"phase": "Phase 2: The Leverage Inspector", "agent": "Scale Architect", "action": "Evaluate the leverage coefficient. Ensure the effort has non-linear upside and compounds over a multi-year horizon."},
        {"phase": "Phase 3: The Walk-Away Designer", "agent": "Discipline Guard", "action": "Set the explicit boundary conditions for exit before beginning, preventing emotional sunk-cost traps."}
    ]
}

BILLIONAIRE_TIME_SAVERS = {
    "build_vs_buy": "Run a 1-week manual prototype (using simple email or Mechanical Turk) to validate the workflow before coding or buying any software. You will save 90% of development overhead.",
    "fundraising": "Secure 3 signed customer Letters of Intent (LOIs) showing willingness to pay before pitching a single investor. Genuine customer demand is the ultimate leverage.",
    "hiring": "Bypass multiple rounds of abstract interviews. Hire candidates for a paid, 3-day contract project simulating the actual role. You will immediately see their real cadence and peer compatibility.",
    "capital_allocation": "Set micro-budgets that double only when a project meets its explicit customer metrics. Never allocate full project funding upfront.",
    "execution": "Determine if the decision can be undone. If it is a reversible 'two-way door' decision, make it in under 10 minutes with 70% data and iterate immediately based on feedback.",
    "market_strategy": "Record customer calls and find the exact words they use to describe their biggest pain. Replace all marketing copy with their direct quotes.",
    "m_and_a": "Agree on a hard walk-away price in writing with your board BEFORE negotiations begin, and commit to ending the meeting the second the counter-party crosses it.",
    "risk_management": "Use inversion: write a detailed post-mortem of how the project went bankrupt. Veto the project immediately if any of these failure modes cannot be mitigated.",
    "general_strategy": "Draft a single-page decision memo detailing the Upside, Downside, Reversibility, and Walk-Away criteria. If it cannot fit on one page, the strategy is too complex."
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
            agentic_workflow=AGENTIC_WORKFLOWS.get(
                intent.domain, AGENTIC_WORKFLOWS["general_strategy"]
            ),
            billionaire_time_saver=BILLIONAIRE_TIME_SAVERS.get(
                intent.domain, BILLIONAIRE_TIME_SAVERS["general_strategy"]
            ),
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
            agentic_workflow=[],
            billionaire_time_saver="Ingest relevant decision cases to synthesize a billionaire workflow."
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
            agentic_workflow=[],
            billionaire_time_saver="Veto the unethical plan entirely. Build a lawful, high-trust model."
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
