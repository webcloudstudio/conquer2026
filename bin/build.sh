#!/bin/bash
# CommandCenter Operation
# Category: build
source "$(cd "$(dirname "$0")" && pwd)/common.sh"

log "Building Conquer 2026 Docker images..."
docker compose build --no-cache
EXIT_CODE=$?

if [[ $EXIT_CODE -eq 0 ]]; then
    log "Build complete."
else
    log "ERROR: build failed (exit $EXIT_CODE)"
    exit $EXIT_CODE
fi
