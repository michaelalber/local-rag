# AGENTS.md

## Build/Lint/Test Commands

### Setup
```bash
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run unit tests
pytest tests/unit/ -v

# Run a single test file
pytest tests/unit/test_chunker.py

# Run a specific test
pytest -k "test_upload_book" --show-capture=all

# Run with coverage
pytest --cov=src --cov-report=term-missing
```

### Linting and Type Checking
```bash
ruff check src/ tests/
mypy src/
bandit -r src/ -c pyproject.toml
```

## Code Style Guidelines

### Imports
- Follow standard Python import ordering (stdlib, third-party, local)
- Separate groups with blank lines
- Prefer absolute imports over relative imports

### Formatting
- Follow PEP 8 style guidelines
- 4-space indentation
- 79-character line limit
- No trailing whitespace

### Types
- Type hints on all function parameters and return types
- Use Pydantic models for request/response schemas
- Use dataclasses for simple data containers
- Use `pathlib.Path` over string paths

### Naming
- `snake_case` for variables/functions
- `PascalCase` for classes
- `UPPER_CASE` for constants
- Use descriptive names; avoid unnecessary abbreviations

### Error Handling
- Use specific exception types, never bare `except:`
- Use `raise RuntimeError(...)` instead of bare `assert` for runtime checks (bandit S101)
- Provide helpful error messages
- Log errors appropriately

### Documentation
- Google-style docstrings for all public functions and classes
- Include parameter descriptions with types
- Include return value descriptions

### Testing
- Arrange-Act-Assert pattern for all tests
- Use fixtures for test data setup
- Test business logic and edge cases
- Use `@pytest.mark.asyncio` for async tests

### Async
- Use async/await for I/O-bound operations
- Follow existing async patterns in the codebase

## Security Guidelines (OWASP Top 10:2025)

### File Uploads (OWASP A06:2025)
- Only accept: `.pdf`, `.epub`, `.md`, `.txt`, `.rst`, `.html`
- Validate MIME types via magic bytes (PDF: `%PDF`, EPUB: `PK`) or UTF-8 validation
- Max size: 100MB
- Sanitize filenames (remove path traversal, special chars)
- Store uploads outside web root

### Input Validation (OWASP A05:2025)
- Validate/sanitize all user inputs at system boundaries
- Use parameterized queries for database operations
- Never trust client-side validation

### Secrets
- Never include secrets in source code
- Use environment variables for sensitive data

## Development Principles

### TDD
1. **Never write production code without a failing test first**
2. Cycle: RED (write failing test) → GREEN (minimal code to pass) → REFACTOR
3. Test business logic and edge cases
4. Run tests before committing

### Security-By-Design
- Validate all inputs at system boundaries
- Validate file types via magic bytes (PDF: `%PDF`, EPUB: `PK`) and extension allowlist
- Enforce upload size limits (100MB) and sanitize filenames against path traversal
- Set security headers on all HTTP responses (CSP, X-Frame-Options, X-Content-Type-Options)
- Lock CORS to specific origins and HTTP methods
- Store uploaded files outside the web root
- Never include secrets in source code — use environment variables
- All rules align with [OWASP Top 10 (2025)](https://owasp.org/Top10/2025/) guidance

### YAGNI (You Aren't Gonna Need It)
- Start with direct implementations
- Add abstractions only when complexity demands it
- Create interfaces only when multiple implementations exist
- No dependency injection containers
- No repository pattern — direct JSON read/write
- No plugin architecture — simple match/case on file extension

### Quality Gates
- **Cyclomatic Complexity**: Methods <10, classes <20
- **Code Coverage**: 80% minimum for business logic, 95% for security-critical code
- **Maintainability Index**: Target 70+
- **Code Duplication**: Maximum 3%

## Git Workflow

- Commit after each GREEN phase
- Commit message format: `feat|fix|test|refactor: brief description`
- Don't commit failing tests (RED phase is local only)

## Tools

- **Bash**: Use for running tests, linters, and formatters
- **Read/Write/Edit**: For file operations
- **Grep/Glob**: For code search
- **Task**: For complex, multi-step operations

## Example Workflow

1. Write a failing test for the new feature
2. Run `pytest -k <test_name>` to confirm it fails (RED)
3. Write minimal code to make the test pass (GREEN)
4. Run full test suite: `pytest`
5. Run linters: `ruff check src/ tests/ && mypy src/`
6. Refactor if needed while keeping tests green (REFACTOR)
7. Commit: `git commit -m "feat: <description>"`
