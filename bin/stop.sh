#!/bin/bash
# CommandCenter Operation
# Category: service
source "$(cd "$(dirname "$0")" && pwd)/common.sh"

log "Stopping Conquer 2026 stack..."
docker compose down
log "Stack stopped."
