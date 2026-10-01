from app.services.text_chunker import chunk_text


def test_chunk_text_returns_overlapping_chunks() -> None:
    text = "A" * 1200
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    assert len(chunks) >= 3
    assert all(len(chunk) <= 500 for chunk in chunks)


def test_chunk_text_keeps_chunks_within_limit_after_paragraph_boundary() -> None:
    text = "First paragraph.\n" + "B" * 490
    chunks = chunk_text(text, chunk_size=500, overlap=100)
    assert len(chunks) == 2
    assert all(len(chunk) <= 500 for chunk in chunks)
