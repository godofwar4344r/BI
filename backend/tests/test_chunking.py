from app.services.chunking import chunk_text


def test_chunk_text_uses_overlap() -> None:
    text = "Sentence one. " * 100
    chunks = chunk_text(text, chunk_size=120, overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 140 for chunk in chunks)


def test_chunk_text_rejects_invalid_overlap() -> None:
    try:
        chunk_text("hello", chunk_size=10, overlap=10)
    except ValueError as exc:
        assert "overlap" in str(exc)
    else:
        raise AssertionError("Expected invalid overlap to raise ValueError")
