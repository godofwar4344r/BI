from __future__ import annotations

import hashlib
import math
import re
from typing import Protocol


TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_+-]{1,}")


class EmbeddingProvider(Protocol):
    dimensions: int

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class HashEmbeddingProvider:
    """Deterministic local embeddings for a zero-key MVP and testability."""

    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        vector = [0.0 for _ in range(self.dimensions)]
        tokens = TOKEN_RE.findall(text.lower())
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]
