"""API and web routes."""

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import BASE_DIR, get_settings
from app.schemas.chat import ChatRequest, ChatResponse, IngestResponse, SourceItem
from app.services.document_loader import SUPPORTED_EXTENSIONS, extract_text
from app.services.llm import GroqLLMService
from app.services.safety import DISCLAIMER, EMERGENCY_MESSAGE, has_emergency_language
from app.services.text_chunker import chunk_text

router = APIRouter()
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request) -> HTMLResponse:
    """Render the no-login chat interface."""

    return templates.TemplateResponse(request=request, name="index.html")


@router.get("/api/v1/health")
def health(request: Request) -> dict[str, object]:
    """Return service and index health information."""

    return {
        "status": "ok",
        "indexed_chunks": request.app.state.vector_store.count,
        "groq_configured": bool(get_settings().groq_api_key),
    }


@router.post("/api/v1/documents", response_model=IngestResponse)
async def upload_document(
    request: Request,
    file: Annotated[UploadFile, File(description="PDF, DOCX, TXT, or Markdown file")],
) -> IngestResponse:
    """Upload, extract, chunk, embed, and index one document."""

    settings = get_settings()
    original_name = Path(file.filename or "document").name
    suffix = Path(original_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Supported types: PDF, DOCX, TXT, MD")

    saved_name = f"{uuid4().hex}_{original_name}"
    saved_path = settings.documents_dir / saved_name
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Maximum file size is 15 MB")
    saved_path.write_bytes(content)

    try:
        text = extract_text(saved_path)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError("No readable text was found in the document")
        added = request.app.state.vector_store.add(chunks, original_name)
    except Exception as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return IngestResponse(
        filename=original_name,
        chunks_added=added,
        total_chunks=request.app.state.vector_store.count,
        message="Document indexed successfully.",
    )


@router.post("/api/v1/chat", response_model=ChatResponse)
def chat(request: Request, payload: ChatRequest) -> ChatResponse:
    """Retrieve relevant chunks and generate a grounded medical answer."""

    settings = get_settings()
    emergency = has_emergency_language(payload.question)
    if emergency:
        return ChatResponse(
            answer=EMERGENCY_MESSAGE,
            sources=[],
            emergency_warning=True,
            disclaimer=DISCLAIMER,
        )

    matches = request.app.state.vector_store.search(payload.question, settings.top_k)
    matches = [item for item in matches if item.score >= settings.min_relevance_score]

    try:
        answer = GroqLLMService(settings).answer(payload.question, payload.history, matches)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Groq request failed: {exc}") from exc

    return ChatResponse(
        answer=answer,
        sources=[
            SourceItem(
                source=item.source,
                chunk_id=item.chunk_id,
                score=round(item.score, 4),
                text=item.text,
            )
            for item in matches
        ],
        emergency_warning=False,
        disclaimer=DISCLAIMER,
    )


@router.delete("/api/v1/documents")
def clear_documents(request: Request) -> dict[str, str]:
    """Clear the local index. Intended for development or trusted deployments."""

    request.app.state.vector_store.clear()
    return {"message": "Knowledge index cleared."}


@router.websocket("/api/v1/chat/ws")
async def chat_websocket(websocket: WebSocket) -> None:
    """Stream grounded RAG answers over one persistent WebSocket connection.

    Client payload:
    {"question": "...", "history": [{"role": "user", "content": "..."}]}

    Server events: connected, start, token, sources, complete, warning, error.
    """

    await websocket.accept()
    await websocket.send_json({"type": "connected", "message": "WebSocket connected."})
    settings = get_settings()

    try:
        while True:
            raw_payload = await websocket.receive_json()
            try:
                payload = ChatRequest.model_validate(raw_payload)
            except Exception as exc:
                await websocket.send_json(
                    {"type": "error", "message": f"Invalid chat payload: {exc}"}
                )
                continue

            if has_emergency_language(payload.question):
                await websocket.send_json(
                    {
                        "type": "warning",
                        "answer": EMERGENCY_MESSAGE,
                        "emergency_warning": True,
                        "disclaimer": DISCLAIMER,
                    }
                )
                await websocket.send_json({"type": "complete"})
                continue

            matches = websocket.app.state.vector_store.search(
                payload.question, settings.top_k
            )
            matches = [
                item for item in matches if item.score >= settings.min_relevance_score
            ]
            source_payload = [
                SourceItem(
                    source=item.source,
                    chunk_id=item.chunk_id,
                    score=round(item.score, 4),
                    text=item.text,
                ).model_dump()
                for item in matches
            ]

            await websocket.send_json({"type": "start"})
            answer_parts: list[str] = []
            try:
                # Groq's SDK iterator is synchronous. Iterating here keeps the
                # protocol simple; deploy multiple workers for high concurrency.
                for token in GroqLLMService(settings).stream_answer(
                    payload.question, payload.history, matches
                ):
                    answer_parts.append(token)
                    await websocket.send_json({"type": "token", "content": token})
            except RuntimeError as exc:
                await websocket.send_json({"type": "error", "message": str(exc)})
                continue
            except Exception as exc:
                await websocket.send_json(
                    {"type": "error", "message": f"Groq streaming failed: {exc}"}
                )
                continue

            await websocket.send_json({"type": "sources", "items": source_payload})
            await websocket.send_json(
                {
                    "type": "complete",
                    "answer": "".join(answer_parts),
                    "disclaimer": DISCLAIMER,
                    "emergency_warning": False,
                }
            )
    except WebSocketDisconnect:
        return
