"""A lightweight persistent vector store using NumPy files and JSON metadata."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass(slots=True)
class SearchResult:
    """One semantic search result."""

    source: str
    chunk_id: str
    score: float
    text: str


class LocalVectorStore:
    """Persist embeddings locally without requiring an external vector database."""

    def __init__(self, index_dir: Path, model_name: str) -> None:
        self.index_dir = index_dir
        self.embeddings_path = index_dir / "embeddings.npy"
        self.metadata_path = index_dir / "metadata.json"
        self.model = SentenceTransformer(model_name)
        self._lock = threading.Lock()
        self._embeddings = self._load_embeddings()
        self._metadata = self._load_metadata()

    def _load_embeddings(self) -> np.ndarray:
        if self.embeddings_path.exists():
            return np.load(self.embeddings_path)
        return np.empty((0, 0), dtype=np.float32)

    def _load_metadata(self) -> list[dict[str, str]]:
        if self.metadata_path.exists():
            return json.loads(self.metadata_path.read_text(encoding="utf-8"))
        return []

    def _persist(self) -> None:
        np.save(self.embeddings_path, self._embeddings)
        self.metadata_path.write_text(
            json.dumps(self._metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @property
    def count(self) -> int:
        """Return the number of indexed chunks."""

        return len(self._metadata)

    def add(self, texts: list[str], source: str) -> int:
        """Embed and store text chunks from one source document."""

        if not texts:
            return 0

        vectors = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        ).astype(np.float32)

        metadata = [
            {"source": source, "chunk_id": str(uuid4()), "text": text}
            for text in texts
        ]

        with self._lock:
            if self._embeddings.size == 0:
                self._embeddings = vectors
            else:
                self._embeddings = np.vstack([self._embeddings, vectors])
            self._metadata.extend(metadata)
            self._persist()
        return len(texts)

    def search(self, query: str, top_k: int) -> list[SearchResult]:
        """Return top semantic matches using cosine similarity."""

        if self.count == 0 or self._embeddings.size == 0:
            return []

        query_vector = self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )[0].astype(np.float32)

        scores = self._embeddings @ query_vector
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            SearchResult(
                source=self._metadata[index]["source"],
                chunk_id=self._metadata[index]["chunk_id"],
                score=float(scores[index]),
                text=self._metadata[index]["text"],
            )
            for index in top_indices
        ]

    def clear(self) -> None:
        """Remove all indexed chunks."""

        with self._lock:
            self._embeddings = np.empty((0, 0), dtype=np.float32)
            self._metadata = []
            self._persist()
