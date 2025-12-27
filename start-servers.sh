#!/bin/bash

# LocalBookChat Server Startup Script
# Starts/restarts: Ollama, FastAPI backend, Vue.js frontend

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=5173

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Kill existing processes
cleanup() {
    log_info "Stopping existing servers..."

    # Kill FastAPI/uvicorn on port 8000
    if lsof -ti:$BACKEND_PORT >/dev/null 2>&1; then
        log_warn "Killing process on port $BACKEND_PORT"
        kill $(lsof -ti:$BACKEND_PORT) 2>/dev/null || true
    fi

    # Kill Vite dev server on port 5173
    if lsof -ti:$FRONTEND_PORT >/dev/null 2>&1; then
        log_warn "Killing process on port $FRONTEND_PORT"
        kill $(lsof -ti:$FRONTEND_PORT) 2>/dev/null || true
    fi

    sleep 1
}

# Check if Ollama is running
check_ollama() {
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Start Ollama if not running
start_ollama() {
    if check_ollama; then
        log_info "Ollama is already running"
    else
        log_info "Starting Ollama..."
        ollama serve &>/dev/null &

        # Wait for Ollama to be ready
        for i in {1..30}; do
            if check_ollama; then
                log_info "Ollama started successfully"
                return 0
            fi
            sleep 1
        done
        log_error "Failed to start Ollama"
        return 1
    fi
}

# Start FastAPI backend
start_backend() {
    log_info "Starting FastAPI backend on port $BACKEND_PORT..."
    cd "$PROJECT_DIR"
    source .venv/bin/activate
    uvicorn src.api.main:app --reload --port $BACKEND_PORT &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_DIR/.backend.pid"
    log_info "Backend started (PID: $BACKEND_PID)"
}

# Start Vue.js frontend
start_frontend() {
    log_info "Starting Vue.js frontend on port $FRONTEND_PORT..."
    cd "$PROJECT_DIR/frontend"
    npm run dev &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_DIR/.frontend.pid"
    log_info "Frontend started (PID: $FRONTEND_PID)"
}

# Main
main() {
    echo ""
    echo "=========================================="
    echo "   LocalBookChat Server Startup"
    echo "=========================================="
    echo ""

    cleanup
    start_ollama
    start_backend
    start_frontend

    echo ""
    log_info "All servers started!"
    echo ""
    echo "  Backend:  http://localhost:$BACKEND_PORT"
    echo "  Frontend: http://localhost:$FRONTEND_PORT"
    echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
    echo ""
    echo "Press Ctrl+C to stop all servers"
    echo ""

    # Wait for interrupt
    trap cleanup EXIT
    wait
}

main "$@"
