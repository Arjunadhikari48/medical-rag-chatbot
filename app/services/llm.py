"""Groq-backed language model service."""

from collections.abc import Iterator

from groq import Groq

from app.core.config import Settings
from app.schemas.chat import HistoryMessage
from app.services.vector_store import SearchResult


SYSTEM_PROMPT = """You are a careful medical education assistant.
Use only the supplied KNOWLEDGE CONTEXT for factual medical claims.
If the context is insufficient, clearly say that the indexed documents do not contain enough information.
Never claim to diagnose a disease, prescribe medication, set a dose, or replace a clinician.
For urgent or potentially life-threatening symptoms, advise immediate professional emergency care.
Explain in clear language and preserve uncertainty.
At the end, add a brief line encouraging consultation with a qualified medical professional.
Do not fabricate citations. Cite sources inline using [Source: filename].
"""


class GroqLLMService:
    """Generate grounded answers through the official Groq Python client."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _messages(
        self,
        question: str,
        history: list[HistoryMessage],
        context_items: list[SearchResult],
    ) -> list[dict[str, str]]:
        """Build the grounded prompt shared by regular and streaming calls."""

        context = "\n\n".join(
            f"[Source: {item.source}]\n{item.text}" for item in context_items
        ) or "No relevant indexed context was found."

        messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
        for item in history[-self.settings.max_history_messages :]:
            messages.append({"role": item.role, "content": item.content})
        messages.append(
            {
                "role": "user",
                "content": f"KNOWLEDGE CONTEXT:\n{context}\n\nQUESTION:\n{question}",
            }
        )
        return messages

    def _client(self) -> Groq:
        """Create a configured Groq client."""

        if not self.settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is missing. Add it to the .env file.")
        return Groq(api_key=self.settings.groq_api_key)

    def answer(
        self,
        question: str,
        history: list[HistoryMessage],
        context_items: list[SearchResult],
    ) -> str:
        """Generate one complete answer (kept for REST compatibility)."""

        completion = self._client().chat.completions.create(
            model=self.settings.groq_model,
            messages=self._messages(question, history, context_items),
            temperature=0.2,
            max_tokens=900,
        )
        return completion.choices[0].message.content or "No answer was generated."

    def stream_answer(
        self,
        question: str,
        history: list[HistoryMessage],
        context_items: list[SearchResult],
    ) -> Iterator[str]:
        """Yield answer text incrementally from Groq's streaming response."""

        stream = self._client().chat.completions.create(
            model=self.settings.groq_model,
            messages=self._messages(question, history, context_items),
            temperature=0.2,
            max_tokens=900,
            stream=True,
        )
        for chunk in stream:
            text = chunk.choices[0].delta.content
            if text:
                yield text
