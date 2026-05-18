from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DecisionCaseRow(Base):
    __tablename__ = "decision_cases"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    person: Mapped[str] = mapped_column(String(120), index=True)
    domain: Mapped[str] = mapped_column(String(80), index=True)
    context: Mapped[str] = mapped_column(Text)
    decision: Mapped[str] = mapped_column(Text)
    reasoning: Mapped[str] = mapped_column(Text)
    traits: Mapped[list[dict[str, object]]] = mapped_column(JSON)
    tradeoffs: Mapped[list[str]] = mapped_column(JSON)
    outcome: Mapped[str] = mapped_column(Text)
    lesson: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    source_type: Mapped[str] = mapped_column(String(40), index=True)
    source_reference: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
