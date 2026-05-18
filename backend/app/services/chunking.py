from __future__ import annotations

import re


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 120) -> list[str]:
    """Split text into readable overlapping chunks without cutting every sentence."""

    cleaned = re.sub(r"\s+", " ", text).strip()
    if not cleaned:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        target_end = min(start + chunk_size, len(cleaned))
        end = target_end
        if target_end < len(cleaned):
            sentence_break = cleaned.rfind(". ", start, target_end)
            if sentence_break > start + chunk_size // 2:
                end = sentence_break + 1
        chunk = cleaned[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(cleaned):
            break
        start = max(0, end - overlap)
    return chunks
