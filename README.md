# LocalBookChat

A privacy-focused, local-first RAG (Retrieval-Augmented Generation) application that lets you chat with your eBooks using a local LLM. Upload PDF or EPUB files and ask questions - all processing happens on your machine with no external API calls.

## Features

- 📚 **Multi-Book Support**: Upload up to 5 books per session (PDF/EPUB)
- 🔒 **Privacy First**: All data stays local - no cloud services or external APIs
- 💬 **Interactive Chat**: Ask questions and get answers with source citations
- 🎯 **Source Attribution**: See exactly which book passages informed each answer
- 🚀 **Modern Stack**: FastAPI backend + Vue 3 frontend
- 🧠 **Local LLM**: Powered by Ollama (Mistral 7B)
- 🔍 **Vector Search**: ChromaDB for semantic similarity search
- 📝 **Session Management**: Multiple users with isolated sessions

## Tech Stack

### Backend
- **Python 3.10+** with type hints
- **FastAPI** - Modern async web framework
- **ChromaDB** - Vector database for embeddings
- **Ollama** - Local LLM inference
- **sentence-transformers** - Text embeddings (all-MiniLM-L6-v2)
- **PyPDF2** & **EbookLib** - Document parsing

### Frontend
- **Vue 3** with Composition API
- **TypeScript** - Type-safe frontend code
- **Vite** - Fast build tool with HMR
- **Tailwind CSS** - Utility-first styling

### Architecture
- **Clean Architecture** - Separation of concerns with domain/infrastructure/application layers
- **SOLID Principles** - Maintainable and testable code
- **Test-Driven Development** - Comprehensive test coverage

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** and npm
- **Ollama** - [Install from ollama.ai](https://ollama.ai)
- **Hardware**:
  - 16GB+ RAM recommended
  - GPU optional but recommended for faster inference

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd local-rag
```

### 2. Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

### 4. Ollama Setup

```bash
# Start Ollama service
ollama serve

# In another terminal, pull the model
ollama pull mistral:7b-instruct-q4_K_M
```

## Usage

### Start the Backend

```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Start the Frontend

```bash
cd frontend
npm run dev
```

The UI will be available at http://localhost:5173

### Using the Application

1. **Upload Books**: Drag and drop PDF or EPUB files (max 50MB each, up to 5 books)
2. **Ask Questions**: Type your question in the chat interface
3. **View Sources**: Click on source citations to see the exact passages used
4. **Adjust Top-K**: Control how many relevant passages to retrieve (1-20)
5. **Delete Books**: Remove individual books or clear all with "Clear All"

## Project Structure

```
local-rag/
├── src/
│   ├── domain/              # Pure business logic
│   │   ├── entities/        # Book, Chunk, Query, Response
│   │   ├── interfaces/      # Abstract base classes
│   │   └── exceptions.py    # Domain exceptions
│   ├── infrastructure/      # External implementations
│   │   ├── parsers/         # PDF, EPUB, chunking
│   │   ├── embeddings/      # sentence-transformers
│   │   ├── vectorstore/     # ChromaDB
│   │   └── llm/             # Ollama client
│   ├── application/         # Use case orchestration
│   │   └── services/        # Ingestion, Query, Session
│   └── api/                 # FastAPI REST layer
│       ├── routes/          # Endpoints
│       ├── schemas/         # Pydantic models
│       └── main.py          # App factory
├── frontend/
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── composables/     # Reusable logic
│   │   └── types/           # TypeScript types
│   └── package.json
├── tests/                   # Mirrors src/ structure
├── docs/                    # Documentation
└── pyproject.toml           # Python dependencies
```

## Development

### Running Tests

```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# With coverage
pytest --cov=src --cov-report=term-missing
```

### Code Quality

```bash
# Linting
ruff check src/ tests/

# Formatting
black src/ tests/
```

## API Endpoints

- `GET /api/health` - Health check
- `POST /api/books` - Upload books
- `GET /api/books` - List books in session
- `DELETE /api/books/{book_id}` - Delete a book
- `DELETE /api/books` - Clear session
- `POST /api/chat` - Send a query

All endpoints require a `session-id` header for session isolation.

## Configuration

Configuration via environment variables or `.env` file:

```env
# Paths
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIR=./data/chroma

# Limits
MAX_FILE_SIZE_MB=50
MAX_BOOKS_PER_SESSION=5

# Models
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=mistral:7b-instruct-q4_K_M
```

## Security Considerations

- File type validation (PDF/EPUB only)
- MIME type verification
- File size limits (50MB default)
- Filename sanitization
- Upload directory isolation
- CORS configuration for local development

## Performance Tips

- **GPU Acceleration**: Ollama will use GPU if available (significantly faster)
- **Model Selection**: Smaller quantized models (Q4) balance quality and speed
- **Top-K Tuning**: Lower values (3-5) are faster, higher (10-20) more comprehensive
- **Chunk Size**: Default 500 characters balances context and precision

## Troubleshooting

**Ollama Connection Error**:
- Ensure Ollama is running: `ollama serve`
- Check the model is pulled: `ollama list`

**ChromaDB Issues**:
- Delete `./data/chroma` directory to reset
- Ensure sufficient disk space

**Frontend API Errors**:
- Verify backend is running on port 8000
- Check browser console for CORS issues

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

This is a personal/educational project, but suggestions and feedback are welcome via issues.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.ai)
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- Embeddings by [sentence-transformers](https://www.sbert.net/)
