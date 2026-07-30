"""Pydantic models for chatbot requests and responses."""

from pydantic import BaseModel, Field


class HistoryMessage(BaseModel):
    """One previous turn supplied by the client."""

    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=6000)


class ChatRequest(BaseModel):
    """Question payload for the RAG chatbot."""

    question: str = Field(min_length=2, max_length=4000)
    history: list[HistoryMessage] = Field(default_factory=list)


class SourceItem(BaseModel):
    """A retrieved source chunk used to build the answer."""

    source: str
    chunk_id: str
    score: float
    text: str


class ChatResponse(BaseModel):
    """Grounded chatbot response."""

    answer: str
    sources: list[SourceItem]
    emergency_warning: bool = False
    disclaimer: str


class IngestResponse(BaseModel):
    """Result returned after document ingestion."""

    filename: str
    chunks_added: int
    total_chunks: int
    message: str
