# LocalBookChat

A privacy-focused, local-first RAG (Retrieval-Augmented Generation) application that lets you chat with your eBooks using a local LLM. Upload PDF or EPUB files and ask questions - all processing happens on your machine with no external API calls.

## Features

- 📚 **Multi-Book Support**: Upload up to 5 books per session (PDF/EPUB, up to 150MB each)
- 🔒 **Privacy First**: All data stays local - no cloud services or external APIs
- 💬 **Interactive Chat**: Ask questions and get answers with source citations
- 🎯 **Source Attribution**: See exactly which book passages informed each answer
- 🤖 **Model Switcher**: Choose the best Ollama model for your content type
- 🚀 **Modern Stack**: FastAPI backend + Vue 3 frontend
- 🧠 **Local LLM**: Powered by Ollama (multiple models supported)
- 🔍 **Vector Search**: ChromaDB for semantic similarity search
- 📝 **Session Management**: Multiple users with isolated sessions
- 📖 **Hierarchical Chunking**: Optimized for large technical books
- 🔗 **Contextual Retrieval**: Neighboring chunks for better continuity

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

#### Install Ollama

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**
```bash
# Download from https://ollama.ai/download/mac
# Or use Homebrew
brew install ollama
```

**Windows:**
Download the installer from https://ollama.ai/download/windows

#### Start Ollama Service

```bash
ollama serve
```

#### Pull Models

**Default Model (General Purpose):**
```bash
ollama pull mistral:7b-instruct-q4_K_M
```

**Recommended Models for Different Content:**
```bash
# For programming/code books
ollama pull codellama:7b

# For legal/political documents
ollama pull llama3:8b

# For complex reasoning and large documents
ollama pull mixtral:8x7b-instruct-q4_K_M

# For multilingual content
ollama pull yi:34b-chat-q4_K_M
```

See the [Models Guide](#ollama--models) section below for detailed model recommendations.

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

1. **Upload Books**: Drag and drop PDF or EPUB files (max 150MB each, up to 5 books)
2. **Select Model**: Click the model selector to choose the best LLM for your content
3. **Ask Questions**: Type your question in the chat interface
4. **View Sources**: Click on source citations to see the exact passages used
5. **Adjust Top-K**: Control how many relevant passages to retrieve (1-20)
6. **Delete Books**: Remove individual books or clear all with "Clear All"

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

## Ollama & Models

### Model Selection Guide

LocalBookChat includes a built-in model switcher that lets you choose the best LLM for your content type. Click the chip icon in the chat header to open the model selector.

#### Recommended Models by Content Type

| Model | Size | Best For | Description |
|-------|------|----------|-------------|
| **Mistral 7B** | 4.1GB | General texts, business, history, literature | Balanced performance for most content. Fast and accurate. |
| **Code Llama 7B** | 3.8GB | Programming books, technical docs, code examples | Specialized for code understanding and technical content. |
| **Llama 3 8B** | 4.7GB | Legal documents, political texts, formal writing | Strong reasoning for complex legal and political analysis. |
| **Mixtral 8x7B** | 26GB | Large documents, complex reasoning, research papers | Most powerful option, requires more RAM/VRAM. |
| **Yi 34B Chat** | 19GB | Multilingual content, academic papers | Excellent for non-English texts and mixed languages. |

### Installing Additional Models

```bash
# List installed models
ollama list

# Pull a specific model
ollama pull <model-name>

# Remove a model
ollama rm <model-name>

# Check model details
ollama show <model-name>
```

### Model Switching in UI

The application automatically detects all installed Ollama models and displays them in the model selector. Each model card shows:
- Model name and description
- Recommended use cases
- Model size
- Current selection status

Your model preference persists across the browser session.

### System Requirements by Model

- **7B models** (Mistral, CodeLlama): 8GB RAM minimum, 16GB recommended
- **8B models** (Llama3): 16GB RAM minimum, 24GB recommended
- **Mixtral 8x7B**: 32GB RAM minimum, 64GB recommended
- **Yi 34B**: 48GB RAM minimum, 64GB+ recommended

GPU acceleration significantly improves performance for all models.

## Configuration

Configuration via environment variables or `.env` file:

```env
# Paths
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIR=./data/chroma

# Limits
MAX_FILE_SIZE_MB=150
MAX_BOOKS_PER_SESSION=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Models
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=mistral:7b-instruct-q4_K_M
OLLAMA_BASE_URL=http://localhost:11434

# RAG Settings
TOP_K_CHUNKS=5
NEIGHBOR_WINDOW=1
```

## Security Considerations

- File type validation (PDF/EPUB only)
- MIME type verification
- File size limits (150MB default, configurable)
- Filename sanitization
- Upload directory isolation
- CORS configuration for local development
- Session-based data isolation

## Performance Tips

- **GPU Acceleration**: Ollama will use GPU if available (significantly faster)
- **Model Selection**:
  - 7B models (Mistral, CodeLlama): Fast, good for most content
  - 8B models (Llama3): Balanced performance and quality
  - Large models (Mixtral, Yi): Best quality, slower, requires more resources
- **Top-K Tuning**:
  - Lower values (3-5): Faster, more focused answers
  - Medium values (10-15): Balanced comprehensiveness
  - Higher values (15-20): Most comprehensive, best for complex queries
- **Chunking Strategy**:
  - Hierarchical chunking optimizes for large technical books
  - Contextual retrieval includes neighboring chunks for continuity
- **Batch Processing**: Automatically batches large document uploads (1000 chunks per batch)

## Troubleshooting

**Ollama Connection Error**:
- Ensure Ollama is running: `ollama serve`
- Check the model is pulled: `ollama list`
- Verify Ollama is on port 11434: `curl http://localhost:11434/api/tags`

**Model Not Showing in Selector**:
- Refresh the page after pulling new models
- Ensure Ollama service is running
- Check backend logs for Ollama connection errors

**ChromaDB Issues**:
- Delete `./data/chroma` directory to reset
- Ensure sufficient disk space
- For large documents, ensure 5GB+ free space

**Large Document Upload Failures**:
- Check file size limit in config (MAX_FILE_SIZE_MB)
- Ensure sufficient RAM for document processing
- Monitor backend logs for batch processing progress

**Frontend API Errors**:
- Verify backend is running on port 8000
- Check browser console for CORS issues
- Ensure session-id header is being sent

**Slow Query Performance**:
- Reduce Top-K value for faster queries
- Use smaller models (7B) for better speed
- Enable GPU acceleration in Ollama
- Consider reducing NEIGHBOR_WINDOW in config

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

This is a personal/educational project, but suggestions and feedback are welcome via issues.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.ai)
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- Embeddings by [sentence-transformers](https://www.sbert.net/)
