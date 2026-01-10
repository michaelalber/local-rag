# KnowledgeHub

![CI](https://github.com/michaelalber/local-rag/actions/workflows/ci.yml/badge.svg?branch=main)

A privacy-focused, local-first RAG (Retrieval-Augmented Generation) application for chatting with your documents and external knowledge sources using a local LLM. Upload PDFs, eBooks, Markdown, or text files and ask questions - all processing happens on your machine.

Connect to external knowledge via [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers like Microsoft Learn or security compliance frameworks (NIST, OWASP, DOE).

## Features

- 📚 **Multi-Book Support**: Upload up to 5 books per session (PDF/EPUB/MD/TXT/RST/HTML, up to 100MB each)
- 📄 **Enhanced Parsing**: Optional [Docling](https://github.com/DS4SD/docling) integration for better PDF parsing and Office document support (DOCX/PPTX/XLSX)
- 🔌 **MCP Integration**: Connect to external knowledge sources via [Model Context Protocol](https://modelcontextprotocol.io/)
  - **Aegis MCP**: Security compliance frameworks (NIST 800-53, OWASP, DOE)
  - **Microsoft Learn MCP**: Microsoft documentation and training content
- 🔒 **Privacy First**: All data stays local - no cloud services or external APIs (MCP sources optional)
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
- **Python 3.11+** with type hints
- **FastAPI** - Modern async web framework
- **ChromaDB** - Vector database for embeddings
- **Ollama** - Local LLM inference and embeddings
- **sentence-transformers** - Alternative CPU-based embeddings
- **MCP SDK** - Model Context Protocol for external knowledge sources
- **pypdf** & **EbookLib** - PDF/EPUB parsing
- **Docling** (optional) - Enhanced PDF parsing, Office docs, OCR
- **Markdown, HTML, RST, TXT** - Text format support

### Frontend
- **Vue 3** with Composition API
- **TypeScript** - Type-safe frontend code
- **Vite** - Fast build tool with HMR
- **Tailwind CSS** - Utility-first styling

### Architecture
- **Flat Structure** - No layers, add abstractions only after Rule of Three
- **TDD** - Test business logic and edge cases
- **Security by Design** - OWASP guidelines built in from the start

## Prerequisites

- **Python 3.11+**
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

# Optional: Install enhanced parsing (adds ~2GB for Docling + dependencies)
pip install -e ".[enhanced]"
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

**Recommended Setup:**
```bash
# LLM Model - Best for RAG chat
ollama pull deepseek-r1:14b

# Embedding Model - High quality semantic search
ollama pull mxbai-embed-large
```

**Alternative Models:**
```bash
# Good alternatives
ollama pull llama3.1:8b
ollama pull mistral:7b-instruct

# For code-heavy technical books
ollama pull codellama:7b

# Alternative embedding model (smaller)
ollama pull nomic-embed-text
```

See the [Models Guide](#ollama--models) section below for detailed recommendations.

## Usage

### Quick Start (Recommended)

```bash
./start-servers.sh
```

This script starts all services (Ollama, backend, frontend) and shows:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Press `Ctrl+C` to stop all servers.

### Manual Start

**Backend:**
```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### Using the Application

1. **Upload Books**: Drag and drop files (PDF, EPUB, MD, TXT, RST, HTML - max 100MB each, up to 5 books). With enhanced parsing enabled: also DOCX, PPTX, XLSX, and images (PNG/JPG/TIFF with OCR).
2. **Select Model**: Click the model selector to choose the best LLM for your content
3. **Ask Questions**: Type your question in the chat interface
4. **View Sources**: Click on source citations to see the exact passages used
5. **Adjust Retrieval %**: Control how much of the book to search (0.5-10%)
   - **1-2%**: Best for specific questions ("What is encapsulation?")
   - **5-10%**: Better for broad questions ("What is this book about?")
6. **Delete Books**: Remove individual books or clear all with "Clear All"

## Project Structure

```
local-rag/
├── src/
│   ├── models/          # Book, Chunk, Query, Response, exceptions
│   ├── parsers/         # PDF, EPUB, MD, TXT, HTML, RST + DocumentParser + chunker
│   ├── embeddings/      # Ollama, SentenceTransformer
│   ├── vectorstore/     # ChromaDB
│   ├── llm/             # Ollama client + prompt builder
│   ├── mcp/             # MCP client, adapters (Aegis, MSLearn), manager
│   ├── services/        # Ingestion, Query, Session
│   └── api/             # FastAPI (routes/, schemas/, middleware/)
├── tests/               # Mirrors src/ structure
├── frontend/
│   ├── src/
│   │   ├── components/  # Vue components
│   │   ├── composables/ # Reusable logic
│   │   └── types/       # TypeScript types
│   └── package.json
├── docs/                # Documentation
└── pyproject.toml       # Python dependencies
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

- `GET /api/health` - Health check (includes MCP source status)
- `POST /api/books` - Upload books
- `GET /api/books` - List books in session
- `DELETE /api/books/{book_id}` - Delete a book
- `DELETE /api/books` - Clear session
- `POST /api/chat` - Send a query
- `POST /api/chat/stream` - Stream chat responses (SSE)

All endpoints require a `session-id` header for session isolation.

### Query Sources

When sending a chat query, you can specify which knowledge source to use:

| Source | Description |
|--------|-------------|
| `books` | Search only your uploaded books (default) |
| `compliance` | Search Aegis MCP (NIST, OWASP, DOE frameworks) |
| `mslearn` | Search Microsoft Learn documentation |
| `all` | Search all available sources |

## Ollama & Models

### Recommended Configuration

For the best RAG experience, we recommend:

| Component | Model | Size | Why |
|-----------|-------|------|-----|
| **LLM** | `deepseek-r1:14b` | 9GB | Excellent reasoning and context understanding |
| **Embeddings** | `mxbai-embed-large` | 669MB | High-quality 1024-dim embeddings |

### LLM Models for RAG

| Model | Size | Best For | Notes |
|-------|------|----------|-------|
| **deepseek-r1:14b** | 9GB | General RAG (recommended) | Excellent reasoning, great with technical content |
| **llama3.1:8b** | 4.9GB | Balanced option | Great instruction following, good with context |
| **mistral:7b-instruct** | 4.4GB | Fast responses | Good quality, faster inference |
| **codellama:7b** | 3.8GB | Technical/code books | Specialized for programming content |
| **gemma3:12b** | 8.1GB | Higher quality | Better answers, slower, needs more VRAM |

### Embedding Models

| Model | Dimensions | Size | Notes |
|-------|------------|------|-------|
| **mxbai-embed-large** | 1024 | 669MB | Best quality (recommended) |
| **nomic-embed-text** | 768 | 274MB | Good quality, smaller |
| **all-MiniLM-L6-v2** | 384 | - | CPU-based, no Ollama needed |

**Important:** If you change embedding models, you must re-upload your books. Embeddings are not compatible across different dimensions.

### Model Commands

```bash
# List installed models
ollama list

# Pull a model
ollama pull deepseek-r1:14b

# Remove a model
ollama rm <model-name>
```

### System Requirements

- **8B models**: 8GB RAM minimum, 16GB recommended, GPU helps significantly
- **12B models**: 16GB RAM, benefits greatly from GPU
- **70B models**: 64GB+ RAM, runs on CPU (slow) or needs 48GB+ VRAM

## Configuration

Configuration via environment variables or `.env` file:

```env
# Paths
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIR=./data/chroma

# Limits
MAX_FILE_SIZE_MB=100
MAX_BOOKS_PER_SESSION=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50

# Models (recommended settings)
EMBEDDING_MODEL=mxbai-embed-large
LLM_MODEL=deepseek-r1:14b
OLLAMA_BASE_URL=http://localhost:11434

# RAG Settings
TOP_K_CHUNKS=5
NEIGHBOR_WINDOW=1

# Enhanced Parsing (requires pip install -e ".[enhanced]")
USE_DOCLING_PARSER=false

# MCP Integration (optional)
# Aegis MCP - Security compliance frameworks
AEGIS_MCP_TRANSPORT=http              # 'http' or 'stdio'
AEGIS_MCP_URL=http://localhost:8765/mcp

# Microsoft Learn MCP
MSLEARN_MCP_ENABLED=true
MSLEARN_MCP_URL=https://learn.microsoft.com/api/mcp
```

## Enhanced Parsing with Docling

For better document parsing quality and additional format support, you can enable [Docling](https://github.com/DS4SD/docling):

### Installation

```bash
pip install -e ".[enhanced]"
```

### Enable Docling

```bash
export USE_DOCLING_PARSER=true
```

Or add to your `.env` file:
```env
USE_DOCLING_PARSER=true
```

### What Docling Adds

| Feature | Standard | With Docling |
|---------|----------|--------------|
| **PDF parsing** | Basic text extraction | Structure-aware with headings, tables |
| **Table extraction** | Often garbled | High-accuracy preservation |
| **Chunking** | Character-based | Token-based, semantic boundaries |
| **DOCX support** | Not available | Full support |
| **PPTX support** | Not available | Full support |
| **XLSX support** | Not available | Full support |
| **Image OCR** | Not available | PNG, JPG, TIFF with text extraction |

### Supported Formats

**Standard (always available):**
- PDF, EPUB, Markdown, TXT, RST, HTML

**With Docling enabled:**
- All standard formats (PDF uses enhanced parsing)
- Microsoft Office: DOCX, PPTX, XLSX
- Images with OCR: PNG, JPG, JPEG, TIFF

### Trade-offs

- **Slower processing**: Docling performs deeper analysis (first upload only)
- **Larger install**: Adds ~2GB for PyTorch and model dependencies
- **Better quality**: Significantly improved results for complex PDFs with tables, figures, and structured content

**Note:** Changing `EMBEDDING_MODEL` requires clearing ChromaDB (`rm -rf ./data/chroma/*`) and re-uploading books.

## MCP Integration

KnowledgeHub supports the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to connect to external knowledge sources alongside your local documents.

### Available MCP Sources

| Source | Description | Configuration |
|--------|-------------|---------------|
| **Aegis MCP** | Security compliance (NIST 800-53, OWASP, DOE) | Requires local Aegis server |
| **Microsoft Learn** | Microsoft documentation and training | Public endpoint, no setup needed |

### Enabling Microsoft Learn

Microsoft Learn MCP provides access to Microsoft's documentation. To enable:

```bash
export MSLEARN_MCP_ENABLED=true
```

Or add to `.env`:
```env
MSLEARN_MCP_ENABLED=true
```

The frontend will automatically show "MS Learn" as a source option.

### Enabling Aegis MCP

Aegis MCP provides security compliance frameworks. You'll need to run an Aegis MCP server:

```bash
# HTTP transport (recommended)
export AEGIS_MCP_TRANSPORT=http
export AEGIS_MCP_URL=http://localhost:8765/mcp

# Or stdio transport
export AEGIS_MCP_TRANSPORT=stdio
export AEGIS_MCP_COMMAND=aegis-mcp
```

### How It Works

1. **Source Selection**: Choose your knowledge source in the chat interface (Books, Compliance, MS Learn, or All)
2. **Health Check**: The `/api/health` endpoint reports which MCP sources are available
3. **Combined Queries**: Select "All" to search books and all configured MCP sources together
4. **Streaming**: All sources support real-time streaming responses

### Architecture

```
┌─────────────────────────────────────────┐
│              QueryService               │
│  Routes queries based on source         │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│              MCPManager                 │
│  Registers and routes to adapters       │
└────────┬─────────────────┬──────────────┘
         │                 │
┌────────▼────────┐ ┌──────▼───────┐
│  AegisAdapter   │ │MSLearnAdapter│
│  (compliance)   │ │  (mslearn)   │
└────────┬────────┘ └──────┬───────┘
         │                 │
┌────────▼─────────────────▼──────────────┐
│            BaseMCPClient                │
│  Handles stdio/HTTP transport           │
└─────────────────────────────────────────┘
```

## Security Considerations

- File type validation (PDF, EPUB, MD, TXT, RST, HTML; with Docling: DOCX, PPTX, XLSX, PNG, JPG, TIFF)
- MIME type verification via magic bytes (PDF: `%PDF`, EPUB/Office: `PK`, images: format headers) or UTF-8 validation (text files)
- File size limits (100MB default, configurable)
- Filename sanitization (path traversal prevention, special chars removed)
- Upload directory isolation
- CORS configuration for local development
- Session-based data isolation

## Performance Tips

- **GPU Acceleration**: Ollama will use GPU if available (significantly faster)
- **Model Selection**:
  - `deepseek-r1:14b`: Recommended for RAG, excellent reasoning
  - `llama3.1:8b`: Good balance of speed and quality
  - `mistral:7b-instruct`: Fastest inference
- **Retrieval Percentage**:
  - **1-2%**: Fast, focused answers for specific questions
  - **5%**: Good for topic summaries
  - **10%**: Comprehensive, best for "what is this book about" questions
- **Embedding Model**: `mxbai-embed-large` provides better semantic matching than smaller models
- **Chunking**: Hierarchical chunking with neighbor window provides better context continuity

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

**Embedding Dimension Mismatch Error**:
- This happens when you change embedding models after uploading books
- Clear ChromaDB: `rm -rf ./data/chroma/*`
- Clear browser session storage (F12 → Application → Session Storage → Clear)
- Re-upload your books

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

**MCP Source Not Available**:
- Check `/api/health` endpoint for MCP source status
- Verify environment variables are set correctly
- For Aegis: ensure the MCP server is running
- For MS Learn: check network connectivity
- Review backend logs for MCP connection errors

## License

MIT License - see [LICENSE](LICENSE) file for details

## Contributing

This is a personal/educational project, but suggestions and feedback are welcome via issues.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [Ollama](https://ollama.ai)
- Vector storage by [ChromaDB](https://www.trychroma.com/)
- Embeddings by [sentence-transformers](https://www.sbert.net/)
- External knowledge via [Model Context Protocol](https://modelcontextprotocol.io/)
