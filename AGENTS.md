# AGENTS.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

Conquer 2026 is a modern Python/React web port of the classic 1987 USENET multi-player turn-based strategy game originally written in C by Adam Bryant. The project contains:

- **`backend/`** — FastAPI + SQLAlchemy + Celery game server (Python 3.10+)
- **`frontend/`** — React 19 + TypeScript + Vite web client
- **`gpl-release/`** — Reference C implementation (authoritative game mechanics)
- **`original_code/`** / **`original_packaging/`** / **`original_scripts/`** — Historical preservation
- **`doc/`** — Project documentation including converted 1987 original docs
- **`bin/`** — All runnable scripts (start, stop, build)

## Dev Commands

- **Start:** `./bin/start.sh` — builds and starts full Docker stack (postgres, redis, backend, worker, frontend)
- **Stop:** `./bin/stop.sh`
- **Build:** `./bin/build.sh` — rebuild Docker images without cache
- **Backend tests:** `cd backend && pip install -e ".[dev]" aiosqlite && pytest`
- **Backend lint:** `cd backend && ruff check .`
- **Frontend dev (local):** `cd frontend && npm install && npm run dev`

## Service Endpoints

- **Frontend:** http://localhost:5174
- **Backend API:** http://localhost:8001
- **API docs (Swagger):** http://localhost:8001/docs
- **API docs (ReDoc):** http://localhost:8001/redoc

## Architecture

### Backend (`backend/`)

FastAPI application with SQLAlchemy ORM, Celery task queue, JWT authentication.

```
backend/
├── app/
│   ├── main.py          FastAPI entry point
│   ├── config.py        Settings (ENV-based via pydantic-settings)
│   ├── database.py      SQLAlchemy async engine setup
│   ├── core/            Security: JWT tokens, bcrypt password hashing
│   ├── models/          SQLAlchemy ORM (14 models)
│   ├── routers/         REST API endpoints (auth, worlds, nations, sectors, armies, messages, admin)
│   ├── schemas/         Pydantic request/response models
│   ├── services/        Business logic layer
│   ├── engine/          Game simulation engine
│   │   ├── economy.py       Production, consumption, resource trade
│   │   ├── combat.py        Military engagement resolution
│   │   ├── magic.py         Spell system
│   │   ├── npc_ai.py        NPC nation behaviour
│   │   ├── turn_processor.py  Turn execution logic
│   │   ├── world_gen.py     Hex map generation
│   │   └── events.py        Game event system
│   └── tasks/           Celery async tasks (turn scheduling)
├── alembic/             Database migrations
└── tests/               pytest test suite
```

**Database models:** User, World, Nation, Sector, Army, City, Caravan, Navy, Artifact, Message, Command, WorldEvent

### Frontend (`frontend/`)

React 19 + TypeScript + Vite. State management via Zustand. HTTP via Axios.

```
frontend/src/
├── api/         Axios API clients
├── components/  Reusable UI components (HexMap, ArmyPanel, SectorPanel, NationDashboard, etc.)
├── pages/       Page-level components
├── store/       Zustand state stores
└── types/       TypeScript type definitions
```

### C Reference (`gpl-release/`)

The original 1987 C codebase is preserved as the authoritative game-mechanics reference. File suffix conventions:

| Suffix | Role |
|--------|------|
| `G` | Player game interface (`mainG.c`, `displayG.c`, `armyG.c`) |
| `A` | Admin/server interface (`mainA.c`, `economyA.c`, `npcA.c`) |
| `X` | Shared engine/execution (`dataX.c`, `executeX.c`, `hexmapX.c`) |

### Mapping: C → Python

| C source | Python equivalent |
|----------|-----------------|
| `dataX.h` structs | `backend/app/models/` |
| `economyA.c` | `backend/app/engine/economy.py` |
| `combatA.c` | `backend/app/engine/combat.py` |
| `magicA.c` + `magicX.c` | `backend/app/engine/magic.py` |
| `hexmapX.c` | `backend/app/engine/world_gen.py` |
| `npcA.c` + `monsterA.c` | `backend/app/engine/npc_ai.py` |
| `conqrun -x` turn exec | Celery task in `backend/app/tasks/` |
| Binary flat files | PostgreSQL tables |

## Docker Compose Stack

```yaml
services:
  db:        postgres:16-alpine   (port 5432)
  redis:     redis:7-alpine       (port 6379)
  backend:   FastAPI/uvicorn      (host:8001 → container:8000)
  worker:    Celery worker
  beat:      Celery beat scheduler
  frontend:  Nginx-served React   (host:5174 → container:80)
```

## Key Configuration

- **`.env.sample`** — template for environment variables (copy to `.env` or `backend/.env`)
- **`docker-compose.yml`** — full service definitions at project root
- **`backend/pyproject.toml`** — Python dependencies
- **`frontend/package.json`** — Node dependencies

Required env vars (see `.env.sample`):
```
DATABASE_URL   postgresql+asyncpg connection string
REDIS_URL      redis:// connection string
SECRET_KEY     JWT signing secret
DEBUG          true/false
```

## Testing

```bash
# Backend unit tests (uses in-memory SQLite, no running DB needed)
cd backend && pytest

# Frontend type check
cd frontend && npm run build

# Smoke test C reference build
cd gpl-release && make Makefiles && make build
ls gpl-release/Src/conquer gpl-release/Src/conqrun
```

## Update Log

After completing any functional change, append a brief entry to `UPDATES.md` (newest entries first).

## Bookmarks

- [GitHub Repo](https://github.com/webcloudstudio/conquer_2026)
- [API Docs](http://localhost:8001/docs)
- [Project Guide](doc/project_guide.md)
- [Original 1987 Docs](doc/original/)

## Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | Done | Foundation: models, auth, Docker, CI |
| 2 | In Progress | Game engine: economy, combat, magic, world gen |
| 3 | In Progress | React frontend: hex map, nation dashboard |
| 4 | Pending | Multiplayer: turn scheduler, messaging, admin UI |
| 5 | Pending | NPC AI, magic, naval combat, scenario editor |

# CLAUDE_RULES_START

# DEFAULT DEVELOPMENT RULES

**Version:** 2026-03-16.1

Full specification: `Specifications/CLAUDE_RULES.md`. This condensed version covers agent behavior only.

---

## Git Workflow

1. Commit immediately after completing a task with no errors.
2. Commit messages: descriptive text, no "Claude"/"Anthropic"/"AI" mentions.
3. DO NOT push — local commits only.
4. NO co-authored-by lines.

Web server changes: print "No restart needed — browser refresh is enough." (templates/CSS/static only) or "Restart required — `./bin/start.sh`." (Python/JS server files).

---

## Project Layout

```
ProjectName/
  METADATA.md       Identity (name, port, status, stack, etc.)
  AGENTS.md         AI context: dev commands, endpoints, architecture
  CLAUDE.md         Contains only: @AGENTS.md
  .env.sample       Required env vars (committed)
  .env              Actual env vars (never committed)
  bin/              All executable scripts
    common.sh       Shared functions — sourced by all bash scripts
    common.py       Shared OperationContext — imported by Python scripts
  doc/              Generated documentation
  logs/             Log files (gitignored)
  data/             Persistent data
  tests/            Test suite
```

---

## Scripts (`bin/`)

All scripts live in `bin/` — bash (`.sh`) or Python (`.py`). The `# CommandCenter Operation` marker in the first 20 lines registers a script with the platform.

**Standard script names** (only create what the project needs):

| Script | Purpose |
|--------|---------|
| `bin/start.sh` | Start service — service projects only |
| `bin/stop.sh` | Stop service — service projects only |
| `bin/build.sh` | Build / compile / package |
| `bin/daily.sh` | Daily maintenance |
| `bin/weekly.sh` | Weekly maintenance |
| `bin/build_documentation.sh` | Generate doc/ output |
| `bin/deploy.sh` | Deploy to environment |

**Bash** — source `common.sh` then add functionality:

```bash
#!/bin/bash
# CommandCenter Operation
# Category: service
source "$(cd "$(dirname "$0")" && pwd)/common.sh"

# your start command — use $PORT for the service port
# e.g. Flask: export FLASK_DEBUG=1 && flask run --port "$PORT"
```

`common.sh` handles everything: `SCRIPT_NAME`, `PROJECT_DIR`, `cd`, `PROJECT_NAME`, `PORT`, venv activation, `.secrets`/`.env` loading, timestamped log file, SIGTERM trap, and the `[$PROJECT_NAME] Starting:` message. Use `$PORT` as the service port — never hardcode a port number. Override the trap after sourcing if the script needs custom cleanup.

**Python** — import `common.py` then add functionality:

```python
#!/usr/bin/env python3
# CommandCenter Operation
# Category: maintenance
import sys, os; sys.path.insert(0, os.path.dirname(__file__)); from common import op

def main(ctx):
    # ctx.project_name, ctx.port, ctx.logger available — use ctx.port as the service port
    pass

if __name__ == '__main__':
    op(__file__).run(main)
```

`op(__file__).run(main)` handles the same concerns as `common.sh`: path setup, METADATA.md parsing, env loading, logging, SIGTERM, and status messages.

Use Linux line endings (no `\r`). Run `chmod +x bin/*.sh`.

---

## METADATA.md

**Authoritative source for project identity.** Always read `name`, `display_name`, `short_description`, and `git_repo` from this file — never infer them from directory names. Present in every set-up project.

Key-value format (not YAML):

```
# AUTHORITATIVE PROJECT METADATA - THE FIELDS IN THIS FILE SHOULD BE CURRENT

name: MyProject                              # machine slug, matches directory name
display_name: My Project                     # human-readable name for UI/display
git_repo: https://github.com/org/MyProject   # full HTTPS URL, for links only
port: 8000                                   # omit if not a service
short_description: One sentence.             # shown in dashboards and indexes
health: /health                              # omit if not a service
status: PROTOTYPE                            # IDEA|PROTOTYPE|ACTIVE|PRODUCTION|ARCHIVED
stack: Python/Flask/SQLite                   # slash-separated, used by generate_prompt.sh
version: 2026-03-16.1                        # YYYY-MM-DD.N, increment on releases
updated: 20260316_120000                     # set automatically by platform scripts
```

`port`, `health`, `stack`, and `status` are platform fields — managed by GAME and platform scripts, not needed for day-to-day agent work. `git_repo` SSH remotes are normalised to HTTPS automatically.

---

## AGENTS.md Required Sections

```markdown
## Dev Commands
- Start: `./bin/start.sh`   # service projects only
- Stop: `./bin/stop.sh`     # service projects only
- Test: `./bin/test.sh`     # if tests exist

## Service Endpoints        # omit if not a service
- Local: http://localhost:PORT

## Bookmarks
- [Documentation](doc/index.html)
```

Only include commands and endpoints that actually exist for the project.

# CLAUDE_RULES_END
