# Conquer v5 — Python Reboot

This directory contains the modern rewrite of Conquer v5.
The original C code lives in `../gpl-release/` and is the **reference implementation**
for game mechanics during the rewrite.

## Quick Start

```bash
# Copy env template
cp backend/.env.example backend/.env

# Start PostgreSQL + Redis + API server
docker compose up

# API docs
open http://localhost:8000/docs
```

## Structure

```
new/
├── backend/          FastAPI + SQLAlchemy + Celery
│   ├── app/
│   │   ├── models/   SQLAlchemy ORM (maps to C structs)
│   │   ├── routers/  REST API endpoints
│   │   ├── engine/   Game logic (economy, combat, magic, world_gen)
│   │   └── core/     Security (JWT, password hashing)
│   ├── tests/        pytest test suite
│   └── alembic/      Database migrations
└── docker-compose.yml
```

## Development

```bash
cd backend
pip install -e ".[dev]" aiosqlite
pytest          # runs against in-memory SQLite, no DB needed
ruff check .    # lint
```

## Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Foundation: models, auth, Docker, CI |
| 2 | Pending | Game engine: economy, combat, magic, world gen |
| 3 | Pending | React frontend: hex map, nation dashboard |
| 4 | Pending | Multiplayer: turn scheduler, messaging, admin UI |
| 5 | Pending | NPC AI, magic, naval combat, scenario editor |

## Mapping: C → Python

| C file | Python equivalent |
|--------|-----------------|
| `dataX.h` structs | `app/models/` |
| `economyA.c` | `app/engine/economy.py` |
| `combatA.c` | `app/engine/combat.py` |
| `magicA.c`, `magicX.c` | `app/engine/magic.py` |
| `hexmapX.c` | `app/engine/world_gen.py` |
| `conqrun -x` (turn exec) | Celery task (Phase 4) |
| Binary flat files | PostgreSQL tables |
