from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Environment-driven application settings."""

    app_name: str = "BI"
    environment: str = "development"
    database_url: str = Field(
        default=f"sqlite:///{(ROOT_DIR / 'backend' / 'data' / 'bi.db').as_posix()}"
    )
    sample_dataset_path: Path = ROOT_DIR / "data" / "sample_decision_cases.jsonl"

    vector_store: Literal["local", "qdrant"] = "local"
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "bi_decision_cases"

    embedding_provider: Literal["hash"] = "hash"
    embedding_dimensions: int = Field(default=384, ge=64, le=4096)
    retrieval_top_k: int = Field(default=6, ge=1, le=20)

    rate_limit_per_minute: int = Field(default=60, ge=1, le=600)
    allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_prefix="BI_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
