# Phase 8: Polish & Hardening

## Objective

Production-ready touches: logging, error handling, documentation, and optional Docker setup.

## Tasks Overview

1. Structured logging
2. Improved error messages
3. Health check with Ollama status
4. README with setup instructions
5. Optional: Docker Compose setup

## Files to Create/Modify

```
localbookchat/
├── src/
│   ├── logging_config.py      # New: logging setup
│   └── api/
│       ├── routes/
│       │   └── health.py      # Modify: add detailed health
│       └── middleware.py      # New: request logging
├── docker-compose.yml         # Optional
├── Dockerfile                 # Optional
└── README.md                  # New: documentation
```

## Implementation

### src/logging_config.py

```python
"""Logging configuration."""

import logging
import sys
from datetime import datetime, UTC


class UTCFormatter(logging.Formatter):
    """Formatter that uses UTC timestamps."""
    
    converter = lambda *args: datetime.now(UTC).timetuple()
    
    def formatTime(self, record, datefmt=None):
        ct = datetime.now(UTC)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.isoformat()


def setup_logging(level: str = "INFO") -> None:
    """Configure application logging."""
    
    # Create formatter
    formatter = UTCFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(console_handler)
    
    # Reduce noise from libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    
    # Application logger
    app_logger = logging.getLogger("localbookchat")
    app_logger.setLevel(getattr(logging, level.upper()))
    
    return app_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a module."""
    return logging.getLogger(f"localbookchat.{name}")
```

### src/api/middleware.py

```python
"""API middleware."""

import time
import logging
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("localbookchat.api")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests with timing."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid4())[:8]
        start_time = time.perf_counter()
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"session={request.headers.get('session-id', 'none')[:8] if request.headers.get('session-id') else 'none'}"
        )
        
        try:
            response = await call_next(request)
            
            # Log response
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info(
                f"[{request_id}] {response.status_code} completed in {elapsed:.1f}ms"
            )
            
            # Add timing header
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-Ms"] = f"{elapsed:.1f}"
            
            return response
            
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"[{request_id}] Error after {elapsed:.1f}ms: {type(e).__name__}: {e}"
            )
            raise
```

### Update src/api/routes/health.py

```python
"""Health check endpoints."""

from fastapi import APIRouter, Depends

from src.api.dependencies import get_llm_client
from src.domain.interfaces import LLMClient

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    llm_client: LLMClient = Depends(get_llm_client),
) -> dict:
    """
    Check API and service health.
    
    Returns status of:
    - API server
    - Ollama LLM service
    """
    ollama_ok = await llm_client.health_check()
    
    return {
        "status": "ok" if ollama_ok else "degraded",
        "version": "0.1.0",
        "services": {
            "api": "ok",
            "ollama": "ok" if ollama_ok else "unavailable",
        },
    }


@router.get("/health/ready")
async def readiness_check(
    llm_client: LLMClient = Depends(get_llm_client),
) -> dict:
    """
    Readiness probe for orchestration.
    
    Returns 200 only if all services are available.
    """
    ollama_ok = await llm_client.health_check()
    
    if not ollama_ok:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Ollama service unavailable",
        )
    
    return {"ready": True}
```

### Update src/api/main.py

```python
"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.domain.exceptions import BookChatError
from src.logging_config import setup_logging

from .config import get_settings
from .exception_handlers import book_chat_error_handler
from .middleware import RequestLoggingMiddleware
from .routes import health_router, books_router, chat_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    # Setup logging
    setup_logging(level="INFO")
    
    app = FastAPI(
        title="LocalBookChat",
        description="Chat with your eBooks using local LLM",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Middleware (order matters - first added = outermost)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Exception handlers
    app.add_exception_handler(BookChatError, book_chat_error_handler)
    
    # Routes
    app.include_router(health_router, prefix=settings.api_prefix)
    app.include_router(books_router, prefix=settings.api_prefix)
    app.include_router(chat_router, prefix=settings.api_prefix)
    
    return app


# Application instance for uvicorn
app = create_app()
```

### Add logging to services

Update `src/application/services/ingestion_service.py`:

```python
"""Book ingestion service."""

import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Callable
from uuid import uuid4

from src.domain.entities import Book, Chunk
from src.domain.interfaces import DocumentParser, EmbeddingService, VectorStore
from src.infrastructure.parsers import FileValidator, TextChunker

logger = logging.getLogger("localbookchat.ingestion")


class BookIngestionService:
    """Orchestrates book ingestion: parse, chunk, embed, store."""

    def __init__(
        self,
        parser_factory: Callable[[Path], DocumentParser],
        chunker: TextChunker,
        embedder: EmbeddingService,
        vector_store: VectorStore,
        validator: FileValidator,
    ):
        self.parser_factory = parser_factory
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.validator = validator

    async def ingest_book(self, file_path: Path, session_id: str) -> Book:
        """Ingest a book: validate, parse, chunk, embed, and store."""
        logger.info(f"Starting ingestion: {file_path.name}")
        
        # Validate
        file_size = file_path.stat().st_size
        self.validator.validate_file(file_path, file_size)
        logger.debug(f"Validation passed: {file_size} bytes")

        # Parse
        parser = self.parser_factory(file_path)
        title, author = parser.parse(file_path)
        text_segments = parser.extract_text(file_path)
        logger.info(f"Parsed '{title}': {len(text_segments)} segments")

        # Chunk all segments
        all_chunks_data = []
        for text, metadata in text_segments:
            chunk_dicts = self.chunker.chunk(text, metadata)
            all_chunks_data.extend(chunk_dicts)
        logger.info(f"Created {len(all_chunks_data)} chunks")

        # Create book entity
        book_id = uuid4()
        book = Book(
            id=book_id,
            title=title,
            author=author,
            file_path=file_path,
            file_type=file_path.suffix.lstrip(".").lower(),
            created_at=datetime.now(UTC),
            chunk_count=len(all_chunks_data),
        )

        # Embed chunks
        logger.info("Generating embeddings...")
        texts = [c["text"] for c in all_chunks_data]
        embeddings = self.embedder.embed(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # Create Chunk entities
        chunks = []
        for chunk_data, embedding in zip(all_chunks_data, embeddings):
            chunk = Chunk(
                id=uuid4(),
                book_id=book_id,
                content=chunk_data["text"],
                page_number=chunk_data["metadata"].get("page_number"),
                chapter=chunk_data["metadata"].get("chapter"),
                embedding=embedding,
            )
            chunks.append(chunk)

        # Store in vector database
        logger.info(f"Storing {len(chunks)} chunks in vector DB...")
        await self.vector_store.add_chunks(chunks, session_id)
        
        logger.info(f"Ingestion complete: {book.title} ({book.chunk_count} chunks)")
        return book
```

Update `src/application/services/query_service.py`:

```python
"""Query service for RAG-based question answering."""

import logging
import time

from src.domain.entities import QueryRequest, QueryResponse
from src.domain.interfaces import VectorStore, EmbeddingService, LLMClient

logger = logging.getLogger("localbookchat.query")


class QueryService:
    """Handles RAG queries against loaded books."""

    def __init__(
        self,
        vector_store: VectorStore,
        embedder: EmbeddingService,
        llm_client: LLMClient,
    ):
        self.vector_store = vector_store
        self.embedder = embedder
        self.llm_client = llm_client

    async def query(self, request: QueryRequest) -> QueryResponse:
        """Process a RAG query."""
        start_time = time.perf_counter()
        logger.info(f"Query: '{request.query[:50]}...' (top_k={request.top_k})")

        # Embed the query
        embed_start = time.perf_counter()
        query_embedding = self.embedder.embed_query(request.query)
        embed_time = (time.perf_counter() - embed_start) * 1000
        logger.debug(f"Embedding took {embed_time:.1f}ms")

        # Retrieve relevant chunks
        search_start = time.perf_counter()
        chunks = await self.vector_store.search(
            query_embedding=query_embedding,
            collection_id=request.session_id,
            top_k=request.top_k,
        )
        search_time = (time.perf_counter() - search_start) * 1000
        logger.info(f"Retrieved {len(chunks)} chunks in {search_time:.1f}ms")

        # Build context from chunks
        context = [chunk.content for chunk in chunks]

        # Generate answer
        llm_start = time.perf_counter()
        answer = await self.llm_client.generate(
            prompt=request.query,
            context=context,
        )
        llm_time = (time.perf_counter() - llm_start) * 1000
        logger.info(f"LLM generation took {llm_time:.1f}ms")

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.info(f"Total query time: {elapsed_ms:.1f}ms")

        return QueryResponse(
            answer=answer,
            sources=chunks,
            latency_ms=elapsed_ms,
        )
```

### README.md

```markdown
# LocalBookChat

Chat with your eBooks using a local LLM. Upload PDF or EPUB files and ask questions about their content.

## Features

- **Local & Private**: All processing happens on your machine
- **RAG Pipeline**: Semantic search + LLM for accurate answers
- **Source Citations**: See which parts of your books informed each answer
- **Multiple Books**: Load up to 5 books per session

## Requirements

- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.ai/) for local LLM
- ~4GB disk space for models
- 8GB+ RAM recommended

## Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd localbookchat

# Backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Frontend
cd frontend
npm install
cd ..
```

### 2. Start Ollama

```bash
# Install Ollama from https://ollama.ai/

# Pull the model (one-time, ~4GB download)
ollama pull mistral:7b-instruct-q4_K_M

# Start Ollama server
ollama serve
```

### 3. Run the Application

```bash
# Terminal 1: Backend
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:5173 in your browser.

## Configuration

Copy `.env.example` to `.env` and customize:

```bash
# File limits
MAX_FILE_SIZE_MB=50
MAX_BOOKS_PER_SESSION=5

# Models
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=mistral:7b-instruct-q4_K_M
OLLAMA_BASE_URL=http://localhost:11434

# RAG settings
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_CHUNKS=5
```

## API Documentation

With the server running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Development

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Skip slow integration tests
pytest -m "not integration and not slow"
```

### Linting

```bash
ruff check src/ tests/
black src/ tests/
```

## Architecture

```
src/
├── domain/           # Core business logic, no dependencies
├── infrastructure/   # External services (parsers, DB, LLM)
├── application/      # Use case orchestration
└── api/              # FastAPI REST layer
```

Key design principles:
- Clean Architecture with dependency inversion
- Test-driven development
- OWASP security guidelines for file handling

## Troubleshooting

**"Ollama service unavailable"**
- Ensure Ollama is running: `ollama serve`
- Check the model is pulled: `ollama list`

**Upload fails with "File type not supported"**
- Only `.pdf` and `.epub` files are allowed

**Slow responses**
- First query loads the embedding model (~5s)
- LLM generation depends on your hardware
- Reduce `TOP_K_CHUNKS` for faster (less thorough) responses

## License

MIT
```

### Optional: Docker Compose

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy application
COPY src/ src/

# Create data directories
RUN mkdir -p data/uploads data/chroma

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
      - CHROMA_PERSIST_DIR=/app/data/chroma
      - UPLOAD_DIR=/app/data/uploads
    depends_on:
      - ollama
    restart: unless-stopped

  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    # Pull model on first run:
    # docker exec -it localbookchat-ollama-1 ollama pull mistral:7b-instruct-q4_K_M

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  ollama_data:
```

#### frontend/Dockerfile

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

#### frontend/nginx.conf

```nginx
server {
    listen 80;
    
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Verification

```bash
# Run all tests
pytest tests/ -v

# Check logging output
uvicorn src.api.main:app --reload --port 8000
# Make a request and observe structured logs

# Test health endpoints
curl http://localhost:8000/api/health
curl http://localhost:8000/api/health/ready

# Optional: Test Docker setup
docker-compose up --build
```

## Final Commit

```bash
git add .
git commit -m "feat: add logging, health checks, and documentation"
```

## 🎉 Project Complete!

You now have a fully functional local eBook RAG application with:

- ✅ Clean Architecture
- ✅ Test-driven development
- ✅ OWASP-compliant file handling
- ✅ Structured logging
- ✅ REST API with OpenAPI docs
- ✅ Vue.js frontend
- ✅ Optional Docker deployment

### Next Steps (Optional Enhancements)

1. **Streaming responses**: Use Server-Sent Events for real-time LLM output
2. **Conversation history**: Maintain chat context across queries
3. **Book metadata**: Extract and display table of contents
4. **Export**: Save conversations as markdown
5. **Multiple models**: Support different Ollama models
6. **Authentication**: Add user accounts for persistent sessions
