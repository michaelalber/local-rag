# CLAUDE.md - LocalBookChat

## Project Summary

Local eBook RAG app: upload 1-5 books (PDF/EPUB), chat with them using local LLM.

**Stack:** Python 3.11+, FastAPI, Vue.js 3, ChromaDB, Ollama, sentence-transformers  
**Hardware:** Intel i7-12700K, 64GB RAM, RTX 3080 10GB VRAM

## Architecture

```
src/
├── models/       # Book, Chunk, Query, Response, exceptions
├── parsers/      # PDF, EPUB, MD, TXT, HTML, RST + DocumentParser + chunker
├── embeddings/   # Ollama, SentenceTransformer
├── vectorstore/  # ChromaDB
├── llm/          # Ollama client + prompt builder
├── services/     # Ingestion, Query, Session
└── api/          # FastAPI (routes/, schemas/, middleware/)

tests/            # Mirrors src/ structure
```

**Principles:** Flat structure, no layers. DocumentParser is the only interface (6 implementations). Add abstractions only after Rule of Three.

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
ollama pull deepseek-r1:14b       # LLM (recommended)
ollama pull mxbai-embed-large     # Embeddings

# Lint
ruff check src/ tests/
black src/ tests/
```

## Development Principles

Three pillars: **TDD**, **Security by Design**, **YAGNI**

**Test-Driven Development (TDD):**
- Write tests before implementation for each module
- Tests define the contract, implementation fulfills it
- Test business logic and edge cases, not boilerplate
- Run tests before moving to next phase

**Security by Design (OWASP):**
- Security is not an afterthought - build it in from the start
- Validate all inputs at system boundaries
- Follow OWASP guidelines for file handling, auth, and data protection
- See Security Requirements section for specifics

**YAGNI (You Aren't Gonna Need It):**
- No abstract interfaces until needed
- No repository pattern - direct JSON read/write
- No dependency injection containers
- No plugin architecture - simple match/case on file extension
- Only apply abstractions after Rule of Three (3+ consumers)

## Code Standards

- Type hints on all signatures
- Google-style docstrings for public methods
- Arrange-Act-Assert test pattern
- `pathlib.Path` over string paths
- Specific exceptions, never bare `except:`
- Async for I/O-bound operations

## Security Requirements (OWASP)

All implementations must follow these security principles:

**File Upload (A04:2021 - Insecure Design):**
- Extensions: `.pdf`, `.epub`, `.md`, `.txt`, `.rst`, `.html`
- Verify MIME type via magic bytes (PDF: `%PDF`, EPUB: `PK`) or UTF-8 validation (text files)
- Max size: 100MB (configurable)
- Sanitize filenames (remove path traversal, special chars)
- Store uploads outside web root

**Input Validation (A03:2021 - Injection):**
- Validate and sanitize all user inputs
- Use parameterized queries for any database operations
- Never trust client-side validation alone

## Models

- **Embeddings:** `mxbai-embed-large` (1024 dim, Ollama-based)
- **LLM:** `deepseek-r1:14b` (recommended for RAG)
- **Alternatives:** `llama3.1:8b`, `mistral:7b-instruct` (faster), `nomic-embed-text` (smaller embeddings)

## Phase Execution

Phase files are in `docs/phases/`. Execute sequentially:

1. Read the phase file
2. Write tests first
3. Implement to pass tests
4. Verify completion criteria
5. Commit with meaningful message
6. Proceed to next phase

Start with: `docs/phases/PHASE_0_SETUP.md`
