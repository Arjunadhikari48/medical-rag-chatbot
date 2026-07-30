"""Application configuration loaded from environment variables."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Strongly typed application settings."""

    app_name: str = "Medical RAG Chatbot"
    app_env: str = "development"
    groq_api_key: str = Field(default="", repr=False)
    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    top_k: int = 5
    chunk_size: int = 900
    chunk_overlap: int = 150
    max_history_messages: int = 8
    min_relevance_score: float = 0.25
    documents_dir: Path = BASE_DIR / "data" / "documents"
    index_dir: Path = BASE_DIR / "data" / "index"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings object."""

    settings = Settings()
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    settings.index_dir.mkdir(parents=True, exist_ok=True)
    return settings
