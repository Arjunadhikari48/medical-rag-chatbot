"""Overlapping text chunking for retrieval."""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into readable overlapping chunks, preferring paragraph boundaries."""

    if not text.strip():
        return []
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    paragraphs = [item.strip() for item in text.split("\n") if item.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n{paragraph}".strip()
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = current[-overlap:] + "\n" + paragraph
        else:
            start = 0
            while start < len(paragraph):
                end = start + chunk_size
                chunks.append(paragraph[start:end])
                start = max(end - overlap, start + 1)
            current = ""

    if current.strip():
        chunks.append(current.strip())

    return chunks
