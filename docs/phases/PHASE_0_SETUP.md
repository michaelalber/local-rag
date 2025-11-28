# Phase 0: Project Setup

## Objective

Initialize repository structure, dependencies, and tooling. No application code yet.

## Files to Create

```
localbookchat/
├── src/
│   ├── __init__.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── entities/
│   │   │   └── __init__.py
│   │   ├── interfaces/
│   │   │   └── __init__.py
│   │   └── exceptions.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── parsers/
│   │   │   └── __init__.py
│   │   ├── embeddings/
│   │   │   └── __init__.py
│   │   ├── vectorstore/
│   │   │   └── __init__.py
│   │   └── llm/
│   │       └── __init__.py
│   ├── application/
│   │   ├── __init__.py
│   │   └── services/
│   │       └── __init__.py
│   └── api/
│       ├── __init__.py
│       └── routes/
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── __init__.py
│   └── integration/
│       └── __init__.py
├── frontend/
│   └── .gitkeep
├── data/
│   ├── uploads/
│   │   └── .gitkeep
│   └── chroma/
│       └── .gitkeep
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

## pyproject.toml

```toml
[project]
name = "localbookchat"
version = "0.1.0"
description = "Local eBook RAG application"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",
    "ollama>=0.4.0",
    "pypdf>=5.0.0",
    "ebooklib>=0.18",
    "pydantic-settings>=2.6.0",
    "python-multipart>=0.0.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=6.0.0",
    "httpx>=0.28.0",
    "ruff>=0.8.0",
    "black>=24.0.0",
]

[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]
include = ["src*"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = "test_*.py"
python_functions = "test_*"

[tool.ruff]
target-version = "py311"
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]

[tool.black]
line-length = 100
target-version = ["py311"]
```

## .env.example

```
UPLOAD_DIR=./data/uploads
CHROMA_PERSIST_DIR=./data/chroma
MAX_FILE_SIZE_MB=50
MAX_BOOKS_PER_SESSION=5
CHUNK_SIZE=512
CHUNK_OVERLAP=50
EMBEDDING_MODEL=all-MiniLM-L6-v2
LLM_MODEL=mistral:7b-instruct-q4_K_M
OLLAMA_BASE_URL=http://localhost:11434
TOP_K_CHUNKS=5
```

## .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/
dist/
build/

# Environment
.env

# Data
data/uploads/*
data/chroma/*
!data/**/.gitkeep

# IDE
.vscode/
.idea/
*.swp

# Testing
.coverage
htmlcov/
.pytest_cache/

# OS
.DS_Store
Thumbs.db
```

## tests/conftest.py

```python
"""Shared pytest fixtures."""

import pytest
from pathlib import Path

@pytest.fixture
def sample_data_dir() -> Path:
    """Path to test sample data."""
    return Path(__file__).parent / "sample_data"

@pytest.fixture
def temp_upload_dir(tmp_path: Path) -> Path:
    """Temporary directory for upload tests."""
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    return upload_dir
```

## src/domain/exceptions.py

```python
"""Domain-level exceptions."""


class BookChatError(Exception):
    """Base exception for LocalBookChat application."""

    pass
```

## Verification

Run these commands—all must succeed:

```bash
# Create and activate venv
python -m venv .venv
source .venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify pytest runs (no tests yet, should show "no tests ran")
pytest

# Verify linting passes
ruff check src/ tests/
black --check src/ tests/

# Verify imports work
python -c "from src.domain.exceptions import BookChatError; print('OK')"
```

## Commit

```bash
git init
git add .
git commit -m "feat: initialize project structure and dependencies"
```

## Next Phase

Proceed to `docs/phases/PHASE_1_DOMAIN.md`
