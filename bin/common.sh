#!/bin/bash
# Shared functions for all Conquer 2026 bin/ scripts
# Source this file at the top of every bin/*.sh script

SCRIPT_NAME="$(basename "$0")"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_DIR" || { echo "[$SCRIPT_NAME] ERROR: cannot cd to $PROJECT_DIR"; exit 1; }

# Parse identity from METADATA.md
PROJECT_NAME="$(grep '^name:' METADATA.md 2>/dev/null | head -1 | awk '{print $2}')"
PORT="$(grep '^port:' METADATA.md 2>/dev/null | head -1 | awk '{print $2}')"
PROJECT_NAME="${PROJECT_NAME:-conquer_2026}"
PORT="${PORT:-5174}"

# Load .env if present (never committed)
if [[ -f "$PROJECT_DIR/.env" ]]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

# Timestamped log file
mkdir -p "$PROJECT_DIR/logs"
LOG_FILE="$PROJECT_DIR/logs/${SCRIPT_NAME%.sh}_$(date +%Y%m%d).log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$PROJECT_NAME] $*" | tee -a "$LOG_FILE"; }

# Clean SIGTERM trap (override after sourcing if needed)
trap 'log "Interrupted."; exit 1' SIGTERM SIGINT

log "Starting: $SCRIPT_NAME (port $PORT)"
