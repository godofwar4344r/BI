from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import DecisionCaseRow
from app.models.decision_case import DecisionCase, DecisionCaseFilters, TraitName


class SqlAlchemyDecisionCaseRepository:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def count(self) -> int:
        with self._session_factory() as session:
            return int(session.scalar(select(func.count()).select_from(DecisionCaseRow)) or 0)

    def upsert_many(self, cases: Iterable[DecisionCase]) -> None:
        with self._session_factory() as session:
            for case in cases:
                row = session.get(DecisionCaseRow, case.id)
                payload = self._to_payload(case)
                if row is None:
                    session.add(DecisionCaseRow(**payload))
                else:
                    for key, value in payload.items():
                        setattr(row, key, value)
            session.commit()

    def list_cases(
        self,
        filters: DecisionCaseFilters | None = None,
        limit: int = 200,
    ) -> list[DecisionCase]:
        with self._session_factory() as session:
            statement = select(DecisionCaseRow)
            if filters:
                if filters.person:
                    statement = statement.where(
                        func.lower(DecisionCaseRow.person).contains(filters.person.lower())
                    )
                if filters.domain:
                    statement = statement.where(
                        func.lower(DecisionCaseRow.domain).contains(filters.domain.lower())
                    )
                if filters.source_type:
                    statement = statement.where(DecisionCaseRow.source_type == filters.source_type)

            rows = list(session.scalars(statement.limit(limit)).all())
            cases = [self._from_row(row) for row in rows]
            if filters and filters.traits:
                wanted = set(filters.traits)
                cases = [
                    case
                    for case in cases
                    if wanted.intersection({trait.name for trait in case.traits})
                ]
            return cases

    def get_many(self, ids: Iterable[str]) -> dict[str, DecisionCase]:
        wanted = list(dict.fromkeys(ids))
        if not wanted:
            return {}
        with self._session_factory() as session:
            rows = list(
                session.scalars(select(DecisionCaseRow).where(DecisionCaseRow.id.in_(wanted))).all()
            )
            return {row.id: self._from_row(row) for row in rows}

    def get(self, case_id: str) -> DecisionCase | None:
        with self._session_factory() as session:
            row = session.get(DecisionCaseRow, case_id)
            return self._from_row(row) if row else None

    def people(self) -> list[str]:
        with self._session_factory() as session:
            rows = session.scalars(select(DecisionCaseRow.person).distinct()).all()
            return sorted(rows)

    def trait_matches(
        self,
        traits: list[TraitName],
        filters: DecisionCaseFilters | None = None,
        limit: int = 20,
    ) -> list[DecisionCase]:
        if not traits:
            return []
        narrowed = self.list_cases(filters=filters, limit=500)
        wanted = set(traits)
        matches = [
            case
            for case in narrowed
            if wanted.intersection({trait.name for trait in case.traits})
        ]
        return matches[:limit]

    @staticmethod
    def _to_payload(case: DecisionCase) -> dict[str, object]:
        return {
            "id": case.id,
            "person": case.person,
            "domain": case.domain,
            "context": case.context,
            "decision": case.decision,
            "reasoning": case.reasoning,
            "traits": [trait.model_dump() for trait in case.traits],
            "tradeoffs": case.tradeoffs,
            "outcome": case.outcome,
            "lesson": case.lesson,
            "confidence": case.confidence,
            "source_type": case.source_type,
            "source_reference": case.source_reference,
            "timestamp": case.timestamp,
        }

    @staticmethod
    def _from_row(row: DecisionCaseRow) -> DecisionCase:
        return DecisionCase(
            id=row.id,
            person=row.person,
            domain=row.domain,
            context=row.context,
            decision=row.decision,
            reasoning=row.reasoning,
            traits=row.traits,
            tradeoffs=row.tradeoffs,
            outcome=row.outcome,
            lesson=row.lesson,
            confidence=row.confidence,
            source_type=row.source_type,
            source_reference=row.source_reference,
            timestamp=row.timestamp,
        )
