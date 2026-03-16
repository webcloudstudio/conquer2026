# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Conquer v5 is a GPL-relicensed (2025) classic multi-player turn-based strategy game originally written in C for USENET distribution in 1987. The `gpl-release/` directory contains the actively maintained version; `original/` is historical preservation only.

## Architecture

### Source Code Layout

`gpl-release/Src/` contains 69 C files organized by suffix convention:

| Suffix | Role | Examples |
|--------|------|---------|
| `G` | Player game interface | `mainG.c`, `displayG.c`, `armyG.c`, `moveG.c`, `magicG.c` |
| `A` | Admin/server interface | `mainA.c`, `createA.c`, `economyA.c`, `npcA.c` |
| `X` | Shared engine/execution | `dataX.c`, `executeX.c`, `hexmapX.c`, `magicX.c` |

### Executables

- **`conquer`** — player-facing game client (G + X modules)
- **`conqrun`** — server admin tool (A + X modules)
- **`conqsort`** — game data sort utility
- **`cextract`** — data extraction utility

### Key Subsystems

- **Game flow**: `mainG.c`, `executeX.c`, `computeX.c`
- **Display/UI**: `displayG.c`, `hexmapG.c`, `pagerG.c`, `ieditG.c`
- **Military**: `armyG.c`, `moveG.c`, `combatA.c`, `navyG.c`
- **Economy**: `economyA.c`, `caravanG.c`, `xferG.c`
- **Magic**: `magicG.c`, `magicA.c`, `magicX.c`, `spellsX.h`
- **Data I/O**: `dataX.c`, `iodataG.c`, `iodataX.c`, `convertX.c`
- **World gen**: `hexmapG.c`, `hexmapX.c`, `elevegX.h`
- **NPC/AI**: `npcA.c`, `monsterA.c`, `nclassX.h`

### Headers

`gpl-release/Include/` holds 49 headers. `header.h` (generated from `header.h.dist`) is the central configuration file for game parameters, paths, and compile-time flags. Do not edit `header.h.dist` for runtime config — edit the generated `header.h`.

## Dev Commands

All build commands run from `gpl-release/`:

```bash
cd gpl-release
make Makefiles    # Generate platform-specific Makefiles (required first time)
make build        # Compile all targets
make install      # Install to $HOME/conquerv5 (non-root) or /usr/local (root)
make docs         # Build nroff documentation
make clean        # Remove object files
make clobber      # Remove generated files including Makefiles
```

Initial setup requires copying the config template:
```bash
cp gpl-release/Include/header.h.dist gpl-release/Include/header.h
# Edit header.h to set OWNER, LOGIN (god account name), VERSION, and data paths
```

## Service Endpoints
<!-- Terminal-based game — no web server -->

## Bookmarks
### Code
- [GitHub Repo](https://github.com/webcloudstudio/conquer_2026)

## Testing

No unit test framework. Tests are build-and-smoke checks:

```bash
# Verify binaries exist after build
ls gpl-release/Src/conquer gpl-release/Src/conqrun

# Smoke test executables
./gpl-release/Src/conquer -h
./gpl-release/Src/conqrun -h
```

CI (`.github/workflows/ci.yml`) builds APK and DEB packages, verifies binary existence, and runs help-flag tests. A commit message containing `[release]` triggers automated release creation.

## Key Configuration

- **`Makefile.top`**: Platform detection (Linux/macOS/BSDs), compiler detection (gcc/clang), library detection (ncurses, crypt), build mode (`release`/`debug`)
- **`Include/header.h`**: Owner/god account, game balance constants, data directory paths, platform defines
- **`Src/nations`**: NPC nation definitions used when creating a new world (`conqrun -m`)

## Packaging

```bash
scripts/build-melange.sh   # Build Alpine APK
scripts/build-debian.sh    # Build Debian DEB (uses Docker)
```

Configuration: `packaging/melange/melange.yaml`, `packaging/debian/docker/Dockerfile`.

## Game Administration

```bash
conqrun -m    # Create new world
conqrun -a    # Add player
conqrun -x    # Execute turn (process one game turn)
conqrun -T    # Maintenance mode (block logins)
conqrun -E    # Convert data files from earlier versions
conquer -n god  # Login as god (admin) in the game client
```

## Code Style

The codebase follows late-1980s Unix C conventions. Modern additions use C99 (`-std=c99`). Platform conditionals use `#ifdef BSD`, `PLATFORM_LINUX`, etc. Compiler flags enforce `-Wall -Wextra -Wshadow -Wpointer-arith -Wcast-qual`. All files carry SPDX GPL-3.0-or-later headers per `REUSE.toml`.

## Update Log

After completing any functional change to the `new/` Python/React application, append a brief summary entry to `new/UPDATES.md` (newest entries first).
# CLAUDE_RULES_START

# DEFAULT DEVELOPMENT RULES STANDARDS

**Version:** 2026-03-13.4

This file should be a part of each project's CLAUDE.md (or AGENTS.md) text. 

The sections between the tag `CLAUDE_RULES_START` and the tag `CLAUDE_RULES_END` can always be replaced by the latest version from canonical source `Specifications/CLAUDE_RULES.md` in the git Specifications repository.

An AI agent conforming to these rules can build, operate, and maintain any project in the ecosystem. A project that follows these rules is automatically discovered and integrated by the platform.

---

## Development Workflow

If the project has a `.git` directory, follow these rules:

1. **Always commit changes immediately** after completing a task if the task has no errors.
2. **Commit messages** should have a descriptive text (no "Claude"/"Anthropic"/"AI" mentions).
3. **DO NOT push** — only commit to local git.
4. **NO co-authored-by lines** in commits.

**For any project that runs a web server**
   - If only templates/CSS/static files changed: print "No restart needed — browser refresh is enough."
   - If any Python/JS server files changed: "Restart required — `flask run --port 8080` (or equivalent)."
   - Flask's dev reloader auto-restarts on Python file saves when `FLASK_DEBUG=1` or `debug=True`; state otherwise.

---

## Project Structure

Standard directory layout for all projects:

```
ProjectName/
  METADATA.md              Project identity and configuration
  AGENTS.md                AI agent context (the real file)
  CLAUDE.md                Contains only: @AGENTS.md
  .env.sample              Required env vars with placeholders
  .env                     Actual env vars (never committed)
  .gitignore               Must exclude .env, logs/, venv/, __pycache__/
  bin/                     Executable scripts
    common.sh              Shared functions (sourced by other scripts)
    start.sh               Start services (optional)
    stop.sh                Stop services (optional)
    test.sh                Run tests (optional)
    build_documentation.sh Generate docs (optional)
  doc/                     Generated documentation output
  logs/                    Operation log files (gitignored)
  venv/                    Python virtual environment (gitignored)
  data/                    Persistent data (project-specific)
  tests/                   Test suite
```

**VIRTUAL ENVIRONMENT**: Python projects use `venv/` at the project root. Scripts that need Python must activate it:

```bash
source "$PROJECT_DIR/venv/bin/activate" 2>/dev/null || true
```

If `venv/` does not exist, `bin/start.sh` or `bin/build.sh` should create it:

```bash
if [ ! -d "$PROJECT_DIR/venv" ]; then
    python3 -m venv "$PROJECT_DIR/venv"
    source "$PROJECT_DIR/venv/bin/activate"
    pip install -r "$PROJECT_DIR/requirements.txt"
fi
```

---

## Agent Context Files

**AGENTS.md** is the primary AI context file for a project. It contains everything an AI agent needs: dev commands, endpoints, bookmarks, project-specific rules, and architecture notes.

**CLAUDE.md** exists only as a pointer: its entire content is `@AGENTS.md`. This keeps the actual context vendor-neutral while maintaining compatibility with tools that look for CLAUDE.md.

Required sections in AGENTS.md for ACTIVE+ projects:

```markdown
# ProjectName

One paragraph description.

## Dev Commands
- Start: `./bin/start.sh`
- Stop: `./bin/stop.sh`
- Test: `./bin/test.sh`

## Service Endpoints
- Local: http://localhost:PORT

## Bookmarks
- [Production](https://...)
- [Documentation](doc/index.html)
```

Additional sections as needed: `## Architecture`, `## Database`, `## Known Issues`.

---

## Script Rules

**LOCATION**: All user executable scripts live in `bin/`. Bash (`.sh`) or Python (`.py`).  In general a .py script will have a related .sh script.

**PURPOSE**: This standard provides observability for operations and therefore scheduled tasks and operations run manually such as server starts and data loads should have a bash script.  

**REGISTRATION**: Scripts with a `# CommandCenter Operation` marker in the first 20 lines are discovered as platform operations. The operation name is derived from the filename: `start.sh` → "Start", `build_documentation.sh` → "Build Documentation".

```bash
#!/bin/bash
# CommandCenter Operation
# Schedule: daily 02:00
# Timeout:  300
# Category: service
```

All header fields are optional. Only the `# CommandCenter Operation` marker is required for registration.

**STANDARD SCRIPTS**:

| Script | Purpose | Idempotent |
|--------|---------|-----------|
| `bin/start.sh` | Start services | No |
| `bin/stop.sh` | Stop services | Yes |
| `bin/build.sh` | Build / compile / package | Yes |
| `bin/test.sh` | Run tests | Yes |
| `bin/deploy.sh` | Deploy to environment | No |
| `bin/daily.sh` | Daily maintenance | Yes |
| `bin/weekly.sh` | Weekly maintenance | Yes |
| `bin/build_documentation.sh` | Generate doc/ output | Yes |

**PREAMBLE**: All bash scripts begin with:

```bash
#!/bin/bash
set -euo pipefail
SCRIPT_NAME="$(basename "$0" .sh)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
source "$SCRIPT_DIR/common.sh"
```

`SCRIPT_NAME` is derived from the filename with extension stripped. `basename "$0" .sh` turns `bin/start.sh` into `start`.

**USE LINUX not WINDOWS FORMAT** so remove trailing \r newlines 
**COMMON FUNCTIONS** (`bin/common.sh`): Shared utilities sourced by all scripts in the project.

```bash
#!/bin/bash
# Common functions — sourced by other scripts, never run directly.

# Read a field from METADATA.md. Usage: get_metadata "port"
get_metadata() {
    grep "^${1}:" "$PROJECT_DIR/METADATA.md" 2>/dev/null | head -1 | sed "s/^${1}:[[:space:]]*//"
}

PROJECT_NAME="$(get_metadata "name")"
PORT="$(get_metadata "port")"
DISPLAY_NAME="$(get_metadata "display_name")"

# Activate venv if present
[ -d "$PROJECT_DIR/venv" ] && source "$PROJECT_DIR/venv/bin/activate" 2>/dev/null
```

Scripts access PORT, PROJECT_NAME, and any metadata field through `common.sh`. No hardcoded values.

**LOGGING**: All operations log to `logs/{project}_{script}_{yyyymmdd_hhmmss}.log`. Project name is always prepended to the log filename for sorting.

```bash
LOG_FILE="logs/${PROJECT_NAME}_${SCRIPT_NAME}_$(date +%Y%m%d_%H%M%S).log"
mkdir -p logs
exec > >(tee -a "$LOG_FILE") 2>&1
```

**DATE FORMATS**: Always use sortable formats. Files and logs: `yyyymmdd` or `yyyymmdd_hhmmss`. Never `MM/DD/YYYY` or other non-sortable formats.

**STATUS MESSAGES**: Emit `[$PROJECT_NAME]` lines for state tracking. Parsed from log output by the platform:

```
[$PROJECT_NAME] Starting: $SCRIPT_NAME
[$PROJECT_NAME] Started: $SCRIPT_NAME
[$PROJECT_NAME] Stopped: $SCRIPT_NAME
[$PROJECT_NAME] Error: $SCRIPT_NAME: <message>
[$PROJECT_NAME] Warning: $SCRIPT_NAME: <message>
```

**EXIT CODES**: 0 = success, non-0 = failure. Long-running services trap SIGTERM:

```bash
cleanup() { echo "[$PROJECT_NAME] Stopped: $SCRIPT_NAME"; exit 0; }
trap cleanup SIGTERM SIGINT
```

**PERMISSIONS**: `chmod +x bin/*.sh`. Permission errors are not retried.

**WORKING DIRECTORY**: Scripts always run from project root. The preamble enforces this.

---

## Metadata Standard

**METADATA.md** is a markdown file at the project root. It uses line-based `key: value` format — not YAML. Parsed line-by-line with simple text matching (`grep "^key:" | cut`). This is the single source of truth for project identity, configuration, and discovery.

```markdown
# MyProject

A web dashboard for managing local development projects.

name: MyProject
display_name: My Project
title: My Project — Development Dashboard
git_repo: MyProject
short_description: Web dashboard for local project management
port: 8000
status: ACTIVE
version: 2026-03-13.1
updated: 20260313_142530
stack: Python,Flask,SQLite 
image: images/myproject.webp
health: /health
show_on_homepage: true
tags: web, tool, dashboard
desired_state: running
namespace: development

## Links

| Name | URL | Notes |
|------|-----|-------|
| Production | https://myproject.example.com | Live site |
| Docs | https://docs.example.com | API documentation |
```

### Field Definitions

**Identity fields** (required for all statuses):

| Field | Description |
|-------|-------------|
| `name` | Machine name. No spaces. Used in log filenames, URLs, script references. |
| `status` | Lifecycle stage. Controls which rules are enforced. See Status Values. |

**Display fields** (required at PROTOTYPE+):

| Field | Description |
|-------|-------------|
| `display_name` | Human-readable name. Default: derived from `name` by inserting a space before each uppercase letter after the first. `CommandCenter` → `Command Center`. `GAME` stays `GAME`. |
| `title` | Display name plus tagline for portfolio cards. |
| `short_description` | One sentence. Used in dashboard cards and portfolio. |
| `git_repo` | Repository name. Defaults to `name` if omitted. |

**Service fields** (required at ACTIVE+):

| Field | Description |
|-------|-------------|
| `port` | Primary port the service listens on. Read by `bin/common.sh`. The single source of truth for port assignment. To change a project's port, edit METADATA.md — all scripts pick it up via `common.sh`. The platform dashboard may provide a UI for editing this field directly. |
| `stack` | CSV list of technoloties to use - relates to specifiction files. Example: `Python,Flask,SQLite`. |
| `health` | Health check endpoint path. Default: `/health`. |
| `desired_state` | What should be running. Values: `running` (service stays up), `on-demand` (started manually, stops when done). Default: `on-demand`. |
| `namespace` | Logical environment. Values: `development`, `qa`, `production`, or a custom name. Default: `development`. |
| `tags` | Comma-separated. Used for dashboard filtering and portfolio badges. |

**Versioning fields** (auto-managed):

| Field | Description |
|-------|-------------|
| `version` | Format: `YYYY-MM-DD.N` where N increments per commit on that date. Example: `2026-03-13.3` means third commit on March 13. Updated automatically by commit hooks or manually. |
| `updated` | Timestamp of last meaningful change. Format: `yyyymmdd_hhmmss`. Example: `20260313_142530`. |

**Portfolio fields** (optional):

| Field | Description |
|-------|-------------|
| `show_on_homepage` | `true` to include in published portfolio. Default: `false`. |
| `image` | Relative path to portfolio card image. |

### Display Name Derivation

If `display_name` is not set, derive it from `name`:
- Insert a space before each uppercase letter after the first: `CommandCenter` → `Command Center`
- All-caps names stay as-is: `GAME` → `GAME`
- Hyphens and underscores become spaces: `my-project` → `my project`, `my_project` → `my project`

### Status Values and State Transitions

| Status | Meaning | What Must Exist |
|--------|---------|-----------------|
| `IDEA` | Concept only | METADATA.md with `name` and `status` |
| `PROTOTYPE` | Proof of concept | All METADATA.md fields populated. AGENTS.md created with default sections. |
| `ACTIVE` | Under development | Git initialized. AGENTS.md has Dev Commands, Service Endpoints, Bookmarks. bin/ scripts have headers. .env.example if env vars used. |
| `PRODUCTION` | Stable, deployed | All ACTIVE rules plus: health endpoint declared and responding. Git remote configured. .env.example complete. Documentation generated in doc/. |
| `ARCHIVED` | No longer maintained | METADATA.md only. No compliance checks. |

**State transitions are verified by `verify.py`**. To promote a project from PROTOTYPE to ACTIVE, run `python3 verify.py --projects /path/to/projects` and fix all reported gaps. verify.py is the single mechanism for validating readiness.

**Git is required for ACTIVE+**. The project must be under version control. A remote is preferred but not required for temporary or experimental projects. IDEA and PROTOTYPE projects may exist without git.

### Service Discovery

Projects discover each other by reading METADATA.md files. The platform scans all project directories and indexes their `name`, `port`, and `health` fields. Any script or project that needs to reach another service reads its port from the platform's project index or directly from `../OtherProject/METADATA.md`. No special `@project-name` syntax — just read the metadata file.

---

## Secrets and Environment

### Global Secrets

Shared secrets (API keys, tokens) live in a single file outside any project:

```
$PROJECTS_DIR/.secrets
```

Where `$PROJECTS_DIR` is the parent directory containing all projects (e.g., `~/projects`). Format is standard env file:

```bash
# $PROJECTS_DIR/.secrets — NEVER committed to git
ANTHROPIC_API_KEY=sk-ant-...
RAILWAY_TOKEN=...
GITHUB_TOKEN=ghp_...
OPENAI_API_KEY=sk-...
```

This file is gitignored globally. It is the single location for user-owned API keys and tokens.

### Per-Project Environment

Each project has `.env.example` (committed) and `.env` (gitignored):

```bash
# .env.example — committed to git, documents required variables
DATABASE_URL=sqlite:///./data/app.db   # Path to database
SECRET_KEY=change-me                    # Flask session key
PORT=8000                               # Service port
```

`.env` is created by copying `.env.example` and filling in real values. Never committed.

### How Scripts Access Secrets

`bin/common.sh` loads secrets in order (later files override earlier):

```bash
# Load global secrets, then project-specific overrides
[ -f "$PROJECTS_DIR/.secrets" ] && set -a && source "$PROJECTS_DIR/.secrets" && set +a
[ -f "$PROJECT_DIR/.env" ] && set -a && source "$PROJECT_DIR/.env" && set +a
```

Python projects load the same way via `python-dotenv` or equivalent, with `$PROJECTS_DIR/.secrets` loaded first.

---

## Documentation

Every project generates documentation into `doc/` using `bin/build_documentation.sh`.

**Standard behavior of `bin/build_documentation.sh`**:
1. If the project has custom documentation source files, render them into `doc/`
2. If no custom docs exist, generate a standard rendering of METADATA.md, AGENTS.md, and any important markdown files into `doc/index.html` using a shared template
3. Output must be self-contained HTML — no server dependencies, no external fetches
4. All assets (CSS, JS) embedded inline or relative within `doc/`

The `doc/` directory is the final project documentation. It is committed to git and may be copied to other tools, published to portfolio sites, or used as reference. It should represent the best available documentation for the project.

**Documentation is required for PRODUCTION status**. For ACTIVE projects it is recommended.

---

## Events and Heartbeats

### Events

All state transitions, operation runs, health changes, and deployments are events. Events follow this format in log output:

```
[$PROJECT_NAME] Event: <type>: <detail>
```

Event types: `starting`, `started`, `stopped`, `error`, `warning`, `deployed`, `health_changed`.

Python scripts should include `# TODO: emit event` placeholders for event integration points in new code. Existing projects do not need to be retrofitted.

Bash scripts emit events via the standard `[$PROJECT_NAME]` status messages defined in Script Rules.

### Heartbeats

Services that expose an HTTP port declare it in METADATA.md (`port:` and `health:`). The platform polls the health endpoint to determine UP/DOWN status. This is the heartbeat mechanism — no agent-side code required beyond having a responding HTTP endpoint.

---

## Governance

**GIT**: Required for ACTIVE+ projects. Must be initialized. Remote preferred but not required for experimental work. Working tree should not be persistently dirty.

**HEALTH**: PRODUCTION projects must declare `port:` and `health:` in METADATA.md and have a responding endpoint at that path.

**COMPLIANCE**: `verify.py` is the single mechanism for checking project compliance against these rules. It scans all projects, checks rules calibrated to declared status, and reports pass/fail. Run:

```bash
python3 verify.py --projects /path/to/projects
```

verify.py is also the gatekeeper for status transitions. A project cannot be promoted to ACTIVE or PRODUCTION if verify.py reports failures for that status level.

**SCHEDULING**: Scripts with `# Schedule:` in their header are candidates for time-based execution. Format: `daily HH:MM`, `weekly DAY HH:MM`, or cron expression. The platform reads these headers and runs the script at the declared time. Missed runs are retried once on next platform startup.

**RESOURCE LIMITS**: Scripts may declare `# Timeout: N` (seconds) and `# MaxMemory: NM` (megabytes) in their headers. The platform enforces these limits and kills processes that exceed them.

---

## Roadmap

Features defined in FEATURES.md but not yet covered by rules:

| Feature | Status |
|---------|--------|
| Scheduling execution | Headers defined, platform enforcement not built |
| Job Pipelines | Not defined |
| Resource limit enforcement | Headers defined, enforcement not built |
| Rolling Restarts | Not defined |
| Workflow States (Kanban) | Data model defined, UI not built |
| Event Log retention/query | Format defined, storage not built |

# CLAUDE_RULES_END
