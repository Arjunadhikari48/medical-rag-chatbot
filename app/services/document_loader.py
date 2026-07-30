"""Text extraction utilities for supported medical knowledge files."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader


SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx"}


def extract_text(path: Path) -> str:
    """Extract normalized text from a PDF, DOCX, TXT, or Markdown file."""

    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {suffix}")

    if suffix == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        document = Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")

    return "\n".join(line.strip() for line in text.splitlines() if line.strip())
