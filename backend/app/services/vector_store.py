from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from typing import Protocol

from app.core.config import Settings
from app.models.decision_case import DecisionCaseFilters


@dataclass(slots=True)
class VectorSearchResult:
    case_id: str
    score: float
    metadata: dict[str, object]


class VectorStore(Protocol):
    def upsert(self, case_id: str, vector: list[float], metadata: dict[str, object]) -> None:
        raise NotImplementedError

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: DecisionCaseFilters | None = None,
    ) -> list[VectorSearchResult]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError


class LocalVectorStore:
    def __init__(self) -> None:
        self._vectors: dict[str, tuple[list[float], dict[str, object]]] = {}

    def upsert(self, case_id: str, vector: list[float], metadata: dict[str, object]) -> None:
        self._vectors[case_id] = (vector, metadata)

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: DecisionCaseFilters | None = None,
    ) -> list[VectorSearchResult]:
        results: list[VectorSearchResult] = []
        for case_id, (vector, metadata) in self._vectors.items():
            if not metadata_matches(metadata, filters):
                continue
            results.append(
                VectorSearchResult(
                    case_id=case_id,
                    score=cosine_similarity(query_vector, vector),
                    metadata=metadata,
                )
            )
        return sorted(results, key=lambda result: result.score, reverse=True)[:top_k]

    def clear(self) -> None:
        self._vectors.clear()


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        from qdrant_client import QdrantClient

        self._settings = settings
        self._client = QdrantClient(url=settings.qdrant_url)
        self._collection = settings.qdrant_collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        from qdrant_client.models import Distance, VectorParams

        existing = {collection.name for collection in self._client.get_collections().collections}
        if self._collection not in existing:
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(
                    size=self._settings.embedding_dimensions,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(self, case_id: str, vector: list[float], metadata: dict[str, object]) -> None:
        from qdrant_client.models import PointStruct

        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"bi:{case_id}"))
        self._client.upsert(
            collection_name=self._collection,
            points=[PointStruct(id=point_id, vector=vector, payload={"case_id": case_id, **metadata})],
        )

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        filters: DecisionCaseFilters | None = None,
    ) -> list[VectorSearchResult]:
        hits = self._client.search(
            collection_name=self._collection,
            query_vector=query_vector,
            limit=max(top_k * 3, top_k),
        )
        results: list[VectorSearchResult] = []
        for hit in hits:
            payload = dict(hit.payload or {})
            if metadata_matches(payload, filters):
                results.append(
                    VectorSearchResult(
                        case_id=str(payload["case_id"]),
                        score=float(hit.score),
                        metadata=payload,
                    )
                )
            if len(results) >= top_k:
                break
        return results

    def clear(self) -> None:
        existing = {collection.name for collection in self._client.get_collections().collections}
        if self._collection in existing:
            self._client.delete_collection(self._collection)
        self._ensure_collection()


def build_vector_store(settings: Settings) -> VectorStore:
    if settings.vector_store == "qdrant":
        return QdrantVectorStore(settings)
    return LocalVectorStore()


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def metadata_matches(metadata: dict[str, object], filters: DecisionCaseFilters | None) -> bool:
    if filters is None:
        return True
    if filters.person and filters.person.lower() not in str(metadata.get("person", "")).lower():
        return False
    if filters.domain and filters.domain.lower() not in str(metadata.get("domain", "")).lower():
        return False
    if filters.source_type and filters.source_type != metadata.get("source_type"):
        return False
    if filters.traits:
        metadata_traits = set(metadata.get("traits", []))
        if not metadata_traits.intersection(filters.traits):
            return False
    return True
