# Medical RAG Chatbot — FastAPI + Groq

A no-login Retrieval-Augmented Generation chatbot for medical-topic education. It indexes trusted PDF, DOCX, TXT, and Markdown documents, retrieves semantically relevant chunks, and asks a Groq-hosted LLM to answer only from that context.

## Important safety notice

This project is an educational starter. It is **not** a medical device, diagnostic system, prescription service, or emergency service. Validate the source documents, add clinical review, privacy controls, audit logging, rate limits, and regulatory controls before any real-world healthcare deployment.

## Features

- No login or authentication flow
- FastAPI REST ingestion API and Swagger UI
- Persistent WebSocket chatbot with token-by-token Groq streaming
- Browser chat interface with automatic reconnect
- PDF, DOCX, TXT, and Markdown ingestion
- Local sentence-transformer embeddings
- Persistent NumPy + JSON vector index
- Groq streaming Chat Completions integration
- Source chunks and relevance scores in responses
- Limited client-provided conversation history
- Emergency-language interception
- Docker support and basic tests

## Project structure

```text
medical-rag-chatbot/
├── app/
│   ├── api/routes.py
│   ├── core/config.py
│   ├── schemas/chat.py
│   ├── services/
│   │   ├── document_loader.py
│   │   ├── llm.py
│   │   ├── safety.py
│   │   ├── text_chunker.py
│   │   └── vector_store.py
│   ├── static/
│   ├── templates/
│   └── main.py
├── data/documents/
├── data/index/
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Local setup

Python 3.11–3.13 is recommended.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and set:

```env
GROQ_API_KEY=your_real_key
```

Start the application:

```bash
uvicorn app.main:app --reload
```

Open:

- Web UI: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/v1/health`

The first startup downloads the embedding model from Hugging Face, so internet access is required once.

## API examples

Upload a document:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/documents" \
  -F "file=@medical_reference.pdf"
```

Chat over WebSocket:

```javascript
const ws = new WebSocket("ws://127.0.0.1:8000/api/v1/chat/ws");

ws.onopen = () => {
  ws.send(JSON.stringify({
    question: "What are the documented symptoms of iron deficiency?",
    history: []
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message);
};
```

Server event sequence:

```text
connected -> start -> token (repeated) -> sources -> complete
```

Emergency questions return `warning -> complete`; validation or provider failures return an `error` event. The older `POST /api/v1/chat` endpoint remains available for compatibility, but the included browser UI uses WebSocket only.

Clear the index:

```bash
curl -X DELETE "http://127.0.0.1:8000/api/v1/documents"
```

## Tests

```bash
pytest -q
```

## Docker

```bash
cp .env.example .env
# Add GROQ_API_KEY to .env
docker compose up --build
```

## Production hardening checklist

Even though the requested version has no login, a public deployment should add rate limiting, upload malware scanning, restricted CORS, HTTPS, maximum request sizes at the proxy, secret management, observability, data-retention policies, source approval workflows, prompt-injection defenses, and human clinical review.
