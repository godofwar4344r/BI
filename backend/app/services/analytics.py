from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(slots=True)
class AnalyticsEvent:
    id: str
    query: str
    domain: str
    retrieved_count: int
    created_at: datetime


@dataclass
class InMemoryAnalytics:
    events: list[AnalyticsEvent] = field(default_factory=list)

    def record_chat(self, query: str, domain: str, retrieved_count: int) -> str:
        event = AnalyticsEvent(
            id=str(uuid4()),
            query=query,
            domain=domain,
            retrieved_count=retrieved_count,
            created_at=datetime.now(timezone.utc),
        )
        self.events.append(event)
        return event.id
