# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Conquer v5 is a GPL-relicensed (2025) classic multi-player turn-based strategy game originally written in C for USENET distribution in 1987. The `gpl-release/` directory contains the actively maintained version; `original/` is historical preservation only.

## Build Commands

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
