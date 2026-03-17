#!/bin/bash
# CommandCenter Operation
# Category: service
source "$(cd "$(dirname "$0")" && pwd)/common.sh"

log "Starting Conquer 2026 stack via docker compose..."

if ! command -v docker &>/dev/null; then
    log "ERROR: docker not found. Install Docker Desktop and try again."
    exit 1
fi

# Ensure .env exists for backend
if [[ ! -f "$PROJECT_DIR/backend/.env" ]]; then
    if [[ -f "$PROJECT_DIR/.env.sample" ]]; then
        cp "$PROJECT_DIR/.env.sample" "$PROJECT_DIR/backend/.env"
        log "Copied .env.sample → backend/.env (edit secrets before production use)"
    fi
fi

docker compose up --build -d
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    log "Stack started."
    log "  Frontend:  http://localhost:$PORT"
    log "  Backend:   http://localhost:8001"
    log "  API docs:  http://localhost:8001/docs"
else
    log "ERROR: docker compose up failed (exit $EXIT_CODE)"
    exit $EXIT_CODE
fi
