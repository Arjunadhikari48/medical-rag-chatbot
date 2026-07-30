"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import BASE_DIR, get_settings
from app.core.logging import configure_logging
from app.services.vector_store import LocalVectorStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize shared services once at startup."""

    configure_logging()
    settings = get_settings()
    app.state.vector_store = LocalVectorStore(
        index_dir=settings.index_dir,
        model_name=settings.embedding_model,
    )
    yield


settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version="1.1.0",
    description="No-login medical-topic RAG chatbot with FastAPI WebSocket streaming and Groq.",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
app.include_router(router)
