# CLAUDE.md - LocalBookChat

## Project Summary

Local eBook RAG app: upload 1-5 books (PDF/EPUB), chat with them using local LLM.

**Stack:** Python 3.11+, FastAPI, Vue.js 3, ChromaDB, Ollama, sentence-transformers  
**Hardware:** Intel i7-12700K, 64GB RAM, RTX 3080 10GB VRAM

## Architecture

```
src/
├── domain/           # Pure Python, no dependencies
│   ├── entities/     # Book, Chunk, Query, Response
│   ├── interfaces/   # ABCs for infrastructure
│   └── exceptions.py
├── infrastructure/   # External implementations
│   ├── parsers/      # PDF, EPUB, chunking
│   ├── embeddings/   # sentence-transformers
│   ├── vectorstore/  # ChromaDB
│   └── llm/          # Ollama client
├── application/      # Use case orchestration
│   └── services/     # Ingestion, Query, Session
├── api/              # FastAPI
│   ├── routes/
│   ├── dependencies.py
│   └── main.py
└── tests/            # Mirrors src/
```

**Principles:** Clean Architecture + SOLID applied pragmatically. Domain defines interfaces; infrastructure implements them. Don't over-abstract.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Test
pytest                              # All tests
pytest tests/unit/ -v               # Unit only
pytest --cov=src --cov-report=term-missing

# Run (all servers)
./start-servers.sh

# Run (manual)
uvicorn src.api.main:app --reload --port 8000
cd frontend && npm run dev

# Ollama
ollama serve
ollama pull llama3.1:8b           # LLM
ollama pull mxbai-embed-large     # Embeddings

# Lint
ruff check src/ tests/
black src/ tests/
```

## Code Standards

- Type hints on all signatures
- Google-style docstrings for public methods
- Arrange-Act-Assert test pattern
- `pathlib.Path` over string paths
- Specific exceptions, never bare `except:`
- Async for I/O-bound operations

## File Validation (OWASP)

- Extensions: `.pdf`, `.epub` only
- Verify MIME type, not just extension
- Max size: 50MB (configurable)
- Sanitize filenames
- Store uploads outside web root

## Models

- **Embeddings:** `mxbai-embed-large` (1024 dim, Ollama-based)
- **LLM:** `llama3.1:8b` (best for RAG)
- **Alternatives:** `mistral:7b-instruct` (faster), `nomic-embed-text` (smaller embeddings)

## Phase Execution

Phase files are in `docs/phases/`. Execute sequentially:

1. Read the phase file
2. Write tests first
3. Implement to pass tests
4. Verify completion criteria
5. Commit with meaningful message
6. Proceed to next phase

Start with: `docs/phases/PHASE_0_SETUP.md`
