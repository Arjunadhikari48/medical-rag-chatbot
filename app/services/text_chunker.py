"""Overlapping text chunking for retrieval."""


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Split text into readable overlapping chunks, preferring paragraph boundaries."""

    if not text.strip():
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    paragraphs = [item.strip() for item in text.split("\n") if item.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        remaining = paragraph
        while remaining:
            separator = "\n" if current else ""
            available = chunk_size - len(current) - len(separator)

            if len(remaining) <= available:
                current = f"{current}{separator}{remaining}"
                break

            if available > 0:
                current = f"{current}{separator}{remaining[:available]}"
                remaining = remaining[available:]

            if current:
                chunks.append(current)
                current = current[-overlap:] if overlap else ""

    if current.strip():
        chunks.append(current.strip())

    return chunks
