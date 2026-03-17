# Conquer 2026 — Comprehensive Project Guide

**Version:** 2026-03-16.1
**Status:** PROTOTYPE
**Stack:** Python / FastAPI / React / TypeScript / PostgreSQL / Redis / Docker

---

## Table of Contents

1. [Origins and History](#1-origins-and-history)
2. [What Is Conquer?](#2-what-is-conquer)
3. [The World: Hex Maps and Sectors](#3-the-world-hex-maps-and-sectors)
4. [Terrain and Vegetation](#4-terrain-and-vegetation)
5. [Nations, Races, and Player Classes](#5-nations-races-and-player-classes)
6. [Resources and the Economy](#6-resources-and-the-economy)
7. [Cities and Infrastructure](#7-cities-and-infrastructure)
8. [Caravans and Trade](#8-caravans-and-trade)
9. [Military: Armies and Unit Types](#9-military-armies-and-unit-types)
10. [Naval Combat](#10-naval-combat)
11. [Magic and Spells](#11-magic-and-spells)
12. [NPC Nations and Monsters](#12-npc-nations-and-monsters)
13. [Turn Processing](#13-turn-processing)
14. [God Powers and Game Administration](#14-god-powers-and-game-administration)
15. [The 2026 Port: Architecture Overview](#15-the-2026-port-architecture-overview)
16. [Backend: FastAPI and Python](#16-backend-fastapi-and-python)
17. [Database Schema](#17-database-schema)
18. [Game Engine Modules](#18-game-engine-modules)
19. [Frontend: React and TypeScript](#19-frontend-react-and-typescript)
20. [REST API Reference](#20-rest-api-reference)
21. [Authentication and Security](#21-authentication-and-security)
22. [Celery Task Queue](#22-celery-task-queue)
23. [Docker Deployment](#23-docker-deployment)
24. [Development Setup](#24-development-setup)
25. [Configuration Reference](#25-configuration-reference)
26. [Running and Administering the Game](#26-running-and-administering-the-game)
27. [Gameplay Walkthrough: Your First Five Turns](#27-gameplay-walkthrough-your-first-five-turns)
28. [Mapping the C Source to Python](#28-mapping-the-c-source-to-python)
29. [Changelog and Development History](#29-changelog-and-development-history)
30. [License, Credits, and Appendices](#30-license-credits-and-appendices)

---

## 1. Origins and History

### 1987: The USENET Era

Conquer was written by Adam Bryant in 1987 and distributed across USENET — the pre-web global discussion network where programmers and university students shared software by posting source code directly to newsgroups. In that era, distributing a game meant posting C source code that recipients would download, compile, and run on their own Unix workstations or VAX minicomputers.

The game was designed for multi-player play in an environment where real-time interaction was impossible: players submitted their moves by running a terminal program, the server queued those commands, and then the game administrator ran a batch process to advance the game world by one turn. The results — troop movements, economic production, combat outcomes — were available the next time each player logged in. This "play-by-mail over a terminal" design shaped every aspect of the game's architecture, and it is an architecture that holds up remarkably well even in the context of a modern web application.

Conquer was designed around the Roman era as a thematic anchor: time is measured in Julian months (Martius through Februarius), populations are divided into civilians and legionaries, and the political units are called nations rather than corporations or kingdoms. But the fantasy layer sits on top of this Roman substrate — Elves, Dwarves, and Orcs compete alongside Human nations, magical creatures wander the map, spells can be cast to heal armies or devastate enemies, and artifacts of great power lie scattered across the world waiting to be discovered.

### The GPL Release

In 2025, the original Conquer v5 codebase was re-licensed under GPL-3.0-or-later, making it fully open-source. The canonical C source now lives in `gpl-release/` and compiles cleanly on Linux with gcc or clang using standard make-based build tools. This version retains 100% compatibility with the original game mechanics — it is the authoritative reference for what the game does.

### Conquer 2026

This project is a ground-up reimplementation of the game mechanics in Python, with a React web front-end replacing the original ncurses terminal interface. The goals are:

- **Accessibility**: any browser can play, no terminal required
- **Persistence**: PostgreSQL replaces the original binary flat-file data store
- **Scalability**: multiple simultaneous game worlds, async turn processing via Celery
- **Fidelity**: all original game mechanics preserved by referencing `gpl-release/` as the ground truth

The 2026 port was developed through a series of phases, with Phase 1 (foundation, models, Docker, auth) complete and subsequent phases progressively re-implementing the game engine subsystems.

---

## 2. What Is Conquer?

Conquer is a turn-based multi-player strategy game set on a procedurally generated hex map. Each player controls a **nation**: a territory on the map populated by civilians, governed by a capital city, sustained by an economy, defended by armies, and empowered by magic.

### The Core Loop

Each turn represents one month of in-game time. During a turn:

1. Players issue orders — move armies, adjust tax rates, build structures, cast spells, send diplomatic messages, dispatch caravans
2. The game administrator (or the Celery scheduler) runs turn processing
3. The engine resolves all movement, combat, production, consumption, and magical effects simultaneously
4. Results are written back to the database and become visible to all players

There is no real-time component. You submit orders; you wait for the turn to process; you read the results. This model is identical to play-by-mail board games and is intentional.

### Victory Conditions

Different player classes have different victory conditions (see Section 5), but in general a nation wins by:

- Accumulating sufficient magic power in the right categories
- Controlling a sufficient fraction of the world's sectors
- Eliminating rival human nations
- Achieving class-specific goals (e.g., a Merchant might win by accumulating talons; a Warlord by military conquest)

### Scale

A typical Conquer world contains 30–80 human player slots and dozens of NPC (computer-controlled) nations. The hex map is large enough that early-game expansion rarely brings players into immediate conflict, but mid-to-late game sees intense competition for productive sectors and strategic chokepoints.

---

## 3. The World: Hex Maps and Sectors

### Hexagonal Grid

The game world is a hexagonal grid. Each cell is a **sector** — the smallest addressable unit of land. A sector is roughly 100–250 square miles. All movement, ownership, combat, and resource production is resolved at the sector level.

Hexagonal grids are used because they eliminate the diagonal-movement asymmetry of square grids: every adjacent sector is equidistant, movement costs are consistent, and line-of-sight calculations are straightforward.

### Sectors

A sector has the following fundamental properties:

| Property | Description |
|----------|-------------|
| Coordinates | (x, y) position on the hex grid |
| Elevation/Terrain | water, valley, clear, hill, mountain, peak |
| Vegetation | one of 12 types (barren, desert, forest, good, ice, jungle, light vegetation, none, swamp, tundra, volcano, wood) |
| Special deposits | metal deposit type, jewel deposit type, special tree type |
| Ownership | the nation that controls it (or unclaimed) |
| Designation | how the nation is using the sector (farm, mine, lumberyard, city, fort, etc.) |
| Population | number of civilians living in the sector |
| Fortification level | defensive multiplier for military combat |

### Sector Ownership

A sector is claimed by a nation when that nation's troops are present in it and no rival troops contest the claim. Once owned, the nation can designate the sector for economic production. If troops are withdrawn and a rival enters, the sector changes hands.

### World Generation

When a new game world is created, the engine (`backend/app/engine/world_gen.py`, ported from `gpl-release/Src/hexmapX.c`) procedurally generates:

1. The terrain heightmap using an elevation algorithm
2. Vegetation distribution correlated with elevation and latitude
3. Special resource deposits scattered across productive terrain
4. Initial NPC nation starting positions
5. Human player starting sectors (capitals)

The generation algorithm ensures that:
- Water separates continents into islands and peninsulas, creating naval strategic interest
- Mountain ranges create natural choke points
- Fertile regions with "good" vegetation are distributed widely enough that early expansion is rewarding
- Metal and jewel deposits are sparse, making mining sectors strategically valuable

---

## 4. Terrain and Vegetation

### Terrain (Elevation)

There are six terrain types, from lowest to highest elevation:

| Terrain | Symbol | Effect |
|---------|--------|--------|
| Water | `~` | Impassable to land units; requires navy |
| Valley | `v` | Easy movement, low defense bonus |
| Clear | ` ` | Standard movement and defense |
| Hill | `h` | Moderate movement penalty, good defense |
| Mountain | `m` | High movement cost, excellent defense |
| Peak | `^` | Nearly impassable; extreme defense if held |

### Vegetation (12 Types)

Vegetation determines food and wood production potential, as well as racial affinity:

| Vegetation | Symbol | Food | Wood | Notes |
|-----------|--------|------|------|-------|
| Barren | `b` | Low | 0 | Marginal; Elves cannot farm here |
| Desert | `.` | 0 | 0 | Worthless for most nations |
| Forest | `f` | Low | High | Good wood, poor food |
| Good | `g` | Very High | Low | Best farmland in the game |
| Ice | `i` | 0 | 0 | Hostile environment |
| Jungle | `j` | 0 | Very High | Hostile; maximum wood output |
| Light Vegetation | `l` | Moderate | Minimal | All-purpose mediocre land |
| None (Water) | `~` | 0 | 0 | Sea sectors |
| Swamp | `"` | 0 | Low | Uninhabitable to most |
| Tundra | `,` | 0 | 0 | Hostile to all nations |
| Volcano | `!` | 0 | 0 | Inaccessible |
| Wood | `w` | High | Moderate | Balanced food and wood |

Racial bonuses apply: Elves thrive in forest and wood sectors; Dwarves in mountains; Orcs in hostile terrains. Human nations are the generalists.

Some hostile terrain types (swamp, tundra, desert) become usable once a nation acquires sufficient magical power in relevant categories. This creates a long-term magic investment payoff.

---

## 5. Nations, Races, and Player Classes

### Races

Every nation belongs to one of four races, each with distinct strengths:

**Humans** — Generalists. Balanced in all areas. No special bonuses or penalties. The default choice for new players.

**Elves** — Excel in forest terrain and magical development. Weaker militarily than other races. Best at civilian and wizardry powers. Elves cannot farm barren terrain.

**Dwarves** — Masters of mining and metalworking. High military power development. Poor at sea; strong in mountains. Best at extracting metals and jewels.

**Orcs** — Aggressive militarists. High military power and army morale. Poor civilian management. Thrive in otherwise inhospitable terrain. Low magical development capacity.

### Player Classes

Within each race, a player selects a class that determines available army units, victory conditions, and special abilities. The original game defines eight classes:

| Class | Race(s) | Primary Goal | Special Ability |
|-------|---------|--------------|-----------------|
| Warlord | Human, Orc | Military conquest | Superior combat units; bonus morale |
| Merchant | Human | Accumulate wealth | Caravan bonuses; reduced taxation revolt risk |
| Wizard | Elf | Max wizardry power | Exclusive high-tier spells; magic research bonus |
| Ranger | Elf, Human | Expand territory | Reduced movement cost; forest combat bonus |
| Berserker | Orc | Destroy enemies | Units gain strength from kills; no surrender |
| Engineer | Dwarf, Human | Build and fortify | Faster construction; cheaper fortifications |
| Sailor | Human | Naval dominance | Fast ships; sea sector control bonuses |
| Priest | Elf, Human | Civilian power | Morale bonus; plague resistance; healing spells |

Each class has a unique victory condition registered in the database. The turn processor checks these conditions at the end of each turn.

---

## 6. Resources and the Economy

### The Five Resources

Conquer's economy revolves around five raw materials:

**Talons** — The monetary unit of the game. Gold talons are generated through taxation of the civilian population. Tax rate is player-controlled: high taxes generate more talons but increase discontent and rebellion risk. Sector types (farms, mines, lumberyards, cities) also generate talons based on their output.

**Metals** — Required for construction of fortifications and buildings, and for supplying certain military units. Produced by mining iron, copper, adamantine, or mithril deposits. A nation's mining ability and metalworking ability determine which deposit types can be exploited. Better metal types require higher combined ability scores.

**Jewels** — Used to summon and employ monsters (magical creatures), and to invest in magical power development. Jewels (rubies, gold, silver, platinum, etc.) are mined from jewel deposits. Jewelworking ability determines accessible deposit types.

**Wood** — Required for naval vessel construction, defensive fortifications, and siege equipment. Produced by lumberyards on forest or wood-vegetation sectors. Each vegetation type has a wood yield value; for each unit of wood value, one worker produces 10 units of wood per turn.

**Food** — The most fundamental resource. Soldiers and civilians both require food every turn. Armies that run out of food suffer attrition; civilians that starve die and reduce the nation's population base. Food is produced by farming sectors designated as farmland.

### Production

Production happens automatically each turn. For each owned sector:

1. The engine reads the sector's designation (farm, mine, lumberyard, etc.)
2. Applies the terrain and vegetation modifiers
3. Applies the nation's racial and class bonuses
4. Computes output based on worker population in the sector
5. Adds the output to the nation's stockpile

### Consumption

Every turn, resources are consumed:

- Each civilian consumes food (amount varies by season and morale)
- Each army unit consumes food and may consume metals
- Building maintenance consumes metals and wood
- Naval vessels require wood for ongoing maintenance

If consumption exceeds production plus stockpile, the shortfall causes:
- Civilian deaths (food shortage)
- Army attrition (supply shortage)
- Defensive structure decay (material shortage)

### Seasonal Variation

The Julian calendar creates seasonal variation in production and consumption:

- **Spring** (Martius–Maius): Planting season; food production begins ramping up
- **Summer** (Junius–Quintilis–Sextilis): Peak production; armies move most efficiently
- **Fall** (Septembre–Octobre–Novembre): Harvest; highest food production
- **Winter** (Decembre–Januarius–Februarius): Low production; increased food consumption; movement penalties

Players must manage stockpiles across seasons. A nation that enters winter with depleted food stores faces severe penalties.

### Taxation and Morale

Tax rate is set per nation (0–100%). Higher taxes increase talon income linearly but decrease morale non-linearly. At very high tax rates, morale collapses, risking civilian revolt. Revolt destroys civilian population and structures in affected sectors.

Morale is also affected by:
- Military victories and defeats
- Foreign occupation of owned sectors
- Food shortages
- Magical blessings (civilian power)
- Priest class bonuses

---

## 7. Cities and Infrastructure

### Sector Designations

Once a sector is owned, it can be designated for a specific purpose. The designation determines what the sector produces and what it costs to maintain. Key designations:

| Designation | Produces | Requires | Notes |
|------------|---------|---------|-------|
| Farm | Food | Workers, good vegetation | Core food source |
| Mine | Metals | Workers, metal deposit | Must have qualifying deposit |
| Jewel Mine | Jewels | Workers, jewel deposit | Rare; high strategic value |
| Lumberyard | Wood | Workers, wood vegetation | Critical for naval/construction |
| City (Supply Center) | Talons, food distribution | Metals, wood | Hub of logistics network |
| Fortress | Defense bonus | Metals, wood | Must be garrisoned |
| Port | Naval access | Must be coastal | Required for fleet basing |
| Capital | Population center | One per nation | Cannot be razed |

### Cities as Supply Centers

Cities are not just population centers — they are the logistical backbone of the nation. Resources produced in surrounding sectors flow through the city and are redistributed to armies and other sectors. A nation whose cities are captured loses its ability to supply remote sectors, causing rapid economic collapse even if raw production sectors remain intact.

### Construction

Building a new designation in a sector costs materials (metals, wood) and takes multiple turns. The Engineer class reduces build time and material costs. Fortifications take the longest and cost the most but provide the greatest military benefit.

---

## 8. Caravans and Trade

### Internal Caravans

Caravans are economic units that transport resources between owned sectors. They are essential because resources do not automatically flow between distant sectors — a nation with farms in the south and armies in the north must run caravans to keep those armies supplied.

Each caravan has:
- A source sector (where it picks up goods)
- A destination sector (where it delivers)
- A cargo type and quantity
- A route (determined each turn by pathfinding through owned territory)

Caravans move one sector per turn and can be raided by enemy armies along their route.

### Inter-Nation Trade

Players can also trade with other nations by establishing trade routes. Trade requires a city at each end and diplomatic agreement (or simply uncontested caravan passage through neutral territory). Trade gives both parties resources they may lack, and the Merchant class gets bonus income from trade volume.

---

## 9. Military: Armies and Unit Types

### Army Structure

An army is a group of military units stationed in a sector. A nation can have multiple armies. Each army has:
- Location (sector coordinates)
- Unit composition (a mix of unit types with quantities)
- Strength (aggregate combat power)
- Supply level (food + metals remaining before attrition)
- Efficiency (percentage of full combat effectiveness, degraded by damage and low supply)
- Morale (affects combat bonus/penalty)

### Unit Types

Conquer defines 40 unit types across five broad categories:

**Infantry** — The backbone. Footsoldiers, heavy infantry, pikemen, and elite guards. Cheap to raise and supply; moderate combat effectiveness.

**Cavalry** — Mobile strike units. Fast movement bonus; high attack power. Expensive to feed and supply. Excellent for raids and flanking.

**Siege Equipment** — Catapults, ballistae, siege towers. Devastating against fortified sectors but useless in open-field combat. Cannot move quickly.

**Magical Units** — Summoned creatures, warlocks, battle-mages. Require jewels to maintain. Very powerful but expensive.

**Naval Units** — Galleys, triremes, warships, transports. Can only operate in water sectors and from ports. See Section 10.

Not all unit types are available to all player classes and races. Warlords have access to elite infantry; Wizards can field magical units unavailable to others; Sailors have superior naval unit options.

### Combat Resolution

Combat occurs when armies from different nations occupy the same sector, or when an army moves into a sector occupied by a rival army.

The engine (`backend/app/engine/combat.py`, ported from `gpl-release/Src/combatA.c`) resolves combat as:

1. Compute attacker strength: sum of unit combat values × efficiency × morale bonus × terrain attack modifier
2. Compute defender strength: sum of unit combat values × efficiency × morale bonus × terrain defense modifier × fortification multiplier
3. Apply random variance (±15%)
4. Proportional casualties on both sides based on the combat outcome ratio
5. Winner is the side with remaining troops; loser retreats or is destroyed
6. Fortification level of the sector is damaged on attacker victory

Terrain has a large effect: attacking into mountain sectors with fortifications is extremely costly; attacking across valleys with cavalry is highly effective.

### Army Orders

Each turn, players can issue orders to each army:
- **Move**: move to an adjacent sector (subject to terrain movement cost)
- **Attack**: declare combat intent against a specific army
- **Patrol**: defend all adjacent sectors automatically
- **Rest**: recover efficiency
- **Garrison**: remain in sector contributing to defense
- **Raze**: destroy structures in owned sector (scorched earth)
- **Pillage**: loot resources from conquered sector

---

## 10. Naval Combat

### Fleets

Naval units operate in water sectors and require port facilities for basing. A fleet is an army-equivalent group of ships. Ships can:
- Transport land armies across water sectors (transport vessels)
- Blockade enemy ports (denying resupply)
- Engage enemy fleets in naval combat
- Bombard coastal sectors

Naval combat uses the same engine as land combat with naval-specific unit stats. The Sailor class has access to faster, more powerful ships and additional naval-specific spells.

### Strategic Importance

In worlds with significant ocean coverage, naval power is a force multiplier. A nation with strong navies can:
- Project power to distant continents
- Cut off island nations from mainland supply
- Raid enemy coastal production sectors
- Establish port colonies in unclaimed island territory

---

## 11. Magic and Spells

### Three Power Types

Magic in Conquer is organized around three power categories, each representing a domain of development:

**Military Power** — Increases army effectiveness, unlocks military unit types, enables offensive spells. Represented as a numeric score. Higher military power: better unit training, siege capability, and access to battle spells.

**Civilian Power** — Governs population management, morale, economic efficiency, and the ability to inhabit hostile terrain types. High civilian power allows a nation to farm swamps, reduce the impact of harsh winters, and maintain higher morale even under heavy taxation.

**Wizardry Power** — Determines the nation's magical research capability and spell repertoire. High wizardry enables the most powerful spells, monster summoning, artifact creation, and the ability to counter enemy magic.

### Developing Powers

Powers are developed by investing jewels and talons each turn into the relevant category. Development is slow and cumulative — a nation that neglects magic early game will be at a severe disadvantage when rivals with high wizardry power start casting devastating spells. The Wizard class develops wizardry power at double the normal rate.

### Spells

Spells are cast by expending magical energy (an amount determined by spell tier). Spell categories:

**Healing Spells** — Restore army strength; reduce disease casualties; raise civilian morale.

**Attack Spells** — Deal direct damage to enemy armies or sectors; cause plague, drought, or blight in enemy territory.

**Reconnaissance Spells** — Reveal enemy sector information; scout hidden troops; detect artifact locations.

**Terrain Alteration** — Change vegetation type of a sector (make desert farmable, drain a swamp, raise a forest).

**Summoning** — Bring monsters into service (costs jewels per turn to maintain); create golem armies; summon weather events.

**Protection** — Shield owned sectors from attack spells; cancel enemy reconnaissance; ward armies against damage.

Spell availability is gated by wizardry power level. Tier-1 spells are accessible from the beginning; Tier-5 spells require near-maximum wizardry development and are game-changing.

---

## 12. NPC Nations and Monsters

### Computer-Controlled Nations

When a world is created, it is populated with NPC (non-player character) nations. These are computer-controlled factions that:
- Own territory and run economies like human players
- Build armies and expand into unclaimed sectors
- React to perceived threats by mobilizing military forces
- Can be diplomatically engaged (trade, non-aggression pacts) — or conquered

NPC nations fill strategic space in the early game, ensuring the map is not empty even when few human players have joined. They also serve as resources: a human player who defeats an NPC nation inherits its developed sectors and stockpiles.

The NPC AI (`backend/app/engine/npc_ai.py`, ported from `gpl-release/Src/npcA.c`) evaluates:
1. Expansion priority (unclaimed adjacent sectors)
2. Threat response (army mobilization when neighbors grow powerful)
3. Economic balance (ensuring production sectors are designated and resourced)
4. Diplomatic posture (aggression level varies by NPC class)

### Monsters

Monsters are independent creatures that roam the map. Unlike NPC nations, monsters do not own territory — they wander and attack whoever they encounter. Monsters:
- Are generated at world creation and appear from events during play
- Range from minor nuisances (wolves, bandits) to world-threatening entities (dragons, undead hordes)
- Can be hired and employed by nations that pay in jewels
- Drop artifacts when defeated

Monsters add unpredictability to the mid-game and can shift the balance of power dramatically when a powerful creature appears in a strategically important region.

---

## 13. Turn Processing

### The Turn Cycle

Turn processing is the heart of the game engine. When triggered (manually by an administrator or automatically by the Celery beat scheduler), the turn processor (`backend/app/engine/turn_processor.py`, ported from `gpl-release/Src/executeX.c` and `computeX.c`) runs through these phases in order:

**Phase 1: Order Validation**
All player orders submitted since the last turn are validated. Invalid orders (insufficient resources, illegal targets) are rejected and logged as failed commands.

**Phase 2: Movement Resolution**
All army and naval movement orders are executed simultaneously. Where movements conflict (two armies moving into the same sector from different directions), the engine resolves precedence based on arrival time (movement cost) and combat rules.

**Phase 3: Combat Resolution**
All combat — including auto-combat from patrol orders and from armies occupying the same sector after movement — is resolved. Each engagement is processed once. Results update army strengths, sector ownership, and fortification levels.

**Phase 4: Economic Production**
For every owned sector, production is computed and added to the owning nation's stockpiles. Farms produce food; mines produce metals; lumberyards produce wood; cities collect taxes.

**Phase 5: Consumption**
Resources are consumed by armies, civilians, and building maintenance. Deficits are applied: food shortages kill civilians, supply shortages weaken armies.

**Phase 6: Construction**
Building projects that were ordered advance by one turn. Projects that complete this turn create new sector designations.

**Phase 7: Magic Effects**
Spells with ongoing effects (terrain alteration, disease, blessings) are applied. New spells are not cast here — they were submitted as orders and resolved in Phase 1.

**Phase 8: NPC Actions**
All NPC nations take their AI-computed turns. This includes movement, combat, economic decisions, and (for high-power NPCs) spell casting.

**Phase 9: Monster Movement**
Monsters wander according to their AI behavior. Combat between monsters and armies is resolved.

**Phase 10: Calendar Advance**
The Julian calendar advances by one month. Seasonal modifiers update.

**Phase 11: Event Generation**
Random world events (drought, earthquake, plague, magical surge, monster spawning) may be triggered based on probability tables.

**Phase 12: Victory Check**
For each human nation, the engine checks whether victory conditions have been met.

**Phase 13: Notifications**
Turn results are written to the database. Players see combat reports, economic summaries, and event notifications on their next login.

---

## 14. God Powers and Game Administration

### The God Account

The game administrator logs in as a special "god" nation with administrative powers not available to normal players. The god account can:

- View all nations' private information
- Adjust any resource stockpile
- Delete or create sectors
- Move armies
- Force nations into maintenance mode (block turns)
- Trigger world events manually
- Add or remove human players
- Process a turn manually at any time
- Inspect and correct any database records

### World Lifecycle

A game world goes through these lifecycle states:

1. **Created**: World generated, NPC nations placed, no human players
2. **Open**: Accepting new players; first turns begin
3. **Active**: All player slots filled; regular turn schedule running
4. **Maintenance**: Temporarily blocked for admin operations
5. **Closed**: Game concluded; world archived

### The Admin API

The backend exposes admin-only REST endpoints (`backend/app/routers/admin.py`):

```
POST   /admin/worlds              Create new game world
DELETE /admin/worlds/{id}         Archive and soft-delete world
POST   /admin/worlds/{id}/turn    Process one game turn
POST   /admin/worlds/{id}/maintenance  Toggle maintenance mode
GET    /admin/nations/{id}        Full nation detail (bypasses privacy)
POST   /admin/nations/{id}/resources  Adjust resource stockpiles
```

All admin endpoints require a JWT token with the `is_admin=true` claim.

---

## 15. The 2026 Port: Architecture Overview

The project structure at the root level:

```
conquer_2026/
├── backend/            FastAPI Python game server
├── frontend/           React + TypeScript web client
├── gpl-release/        Reference C implementation
├── doc/                Documentation (this guide + original 1987 docs)
├── bin/                Runnable scripts
│   ├── common.sh       Shared functions for all scripts
│   ├── start.sh        Start the full Docker stack
│   ├── stop.sh         Stop the stack
│   └── build.sh        Rebuild Docker images
├── data/               Persistent data (world archives, backups)
├── logs/               Log files (gitignored)
├── docker-compose.yml  Full service definitions
├── .env.sample         Environment variable template
├── METADATA.md         Project identity
├── AGENTS.md           Development context
└── UPDATES.md          Changelog
```

### Design Principles

**Preserve mechanics, modernize interface.** Every game mechanic is implemented to match `gpl-release/` behavior. Where the C source and the 1987 documentation agree, that is the specification. Where they conflict, the running C binary is authoritative.

**Database as single source of truth.** PostgreSQL replaces the original binary flat files. SQLAlchemy ORM models map closely to the C struct definitions in `gpl-release/Include/`. The Alembic migration history is the schema changelog.

**Async throughout.** FastAPI with asyncpg handles concurrent player requests without blocking. Turn processing is offloaded to Celery workers so the API stays responsive during the computationally intensive turn phase.

**Stateless API, stateful database.** The API server holds no in-memory game state. All state lives in PostgreSQL. This means the backend can be restarted, scaled horizontally, or replaced without losing game state.

---

## 16. Backend: FastAPI and Python

### Entry Point

`backend/app/main.py` creates the FastAPI application, registers routers, and configures CORS. The application is served by `uvicorn` in development (with `--reload`) and in production containers.

```python
# backend/app/main.py (simplified)
from fastapi import FastAPI
from app.routers import auth, worlds, nations, sectors, armies, messages, admin

app = FastAPI(title="Conquer 2026", version="1.0.0")
app.include_router(auth.router, prefix="/auth")
app.include_router(worlds.router, prefix="/worlds")
app.include_router(nations.router, prefix="/nations")
# ... etc
```

### Configuration

`backend/app/config.py` uses pydantic-settings to load configuration from environment variables:

```python
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    secret_key: str
    debug: bool = False
    access_token_expire_minutes: int = 60 * 24  # 24 hours
```

All configuration is provided via environment variables — never hardcoded. See Section 25 for the full reference.

### Database Session

`backend/app/database.py` configures SQLAlchemy's async engine. Every API endpoint that touches the database receives an async session via FastAPI dependency injection:

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

---

## 17. Database Schema

The database is PostgreSQL 16. Alembic manages migrations. The core tables:

### `users`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| username | VARCHAR(50) | Unique; used for login |
| email | VARCHAR | Unique |
| hashed_password | VARCHAR | bcrypt hash |
| is_admin | BOOLEAN | Admin access flag |
| created_at | TIMESTAMP | Registration time |

### `worlds`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | World display name |
| width, height | INTEGER | Map dimensions |
| current_month | INTEGER | 0–11 Julian month |
| current_year | INTEGER | In-game year |
| is_active | BOOLEAN | Soft-delete flag |
| turn_number | INTEGER | Total turns processed |
| max_nations | INTEGER | Player cap |
| created_at | TIMESTAMP | World creation time |

### `nations`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| world_id | UUID | FK → worlds |
| user_id | UUID | FK → users (NULL for NPC) |
| name | VARCHAR(100) | Nation name |
| race | ENUM | human/elf/dwarf/orc |
| player_class | ENUM | warlord/merchant/wizard/… |
| talons, metals, jewels, wood, food | BIGINT | Resource stockpiles |
| power_military, power_civilian, power_wizardry | INTEGER | Magic power levels |
| attr_morale | INTEGER | Current morale (0–100) |
| is_npc | BOOLEAN | Computer-controlled flag |
| capital_x, capital_y | INTEGER | Starting sector |

### `sectors`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| world_id | UUID | FK → worlds |
| x, y | INTEGER | Hex grid coordinates |
| terrain | ENUM | water/valley/clear/hill/mountain/peak |
| vegetation | ENUM | 12 vegetation types |
| owner_id | UUID | FK → nations (NULL if unclaimed) |
| designation | ENUM | farm/mine/city/fort/port/… |
| population | INTEGER | Civilian count |
| fortification | INTEGER | Defense multiplier |
| metal_deposit | VARCHAR | Deposit type or NULL |
| jewel_deposit | VARCHAR | Deposit type or NULL |

### `armies`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| world_id | UUID | FK → worlds |
| nation_id | UUID | FK → nations |
| sector_x, sector_y | INTEGER | Current location |
| name | VARCHAR(100) | Army label |
| strength | INTEGER | Aggregate combat power |
| unit_type | INTEGER | Unit type code (1–40) |
| supply | INTEGER | Remaining supply |
| efficiency | INTEGER | % of full combat capability |
| morale | INTEGER | Current morale |

### `cities`
Cities are a specialized sector designation tracked in a separate table with supply-network edges.

### `caravans`
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| nation_id | UUID | Owner |
| source_sector_id | UUID | Pickup sector |
| dest_sector_id | UUID | Delivery sector |
| cargo_type | ENUM | talons/metals/jewels/wood/food |
| cargo_amount | INTEGER | Load per trip |
| is_active | BOOLEAN | Active/suspended flag |

### `navies`
Parallel to armies; `unit_type` values are naval (galleys, triremes, etc.); `sector_x/y` must be water or port sectors.

### `messages`
In-game mail between nations. Supports diplomatic notes, trade offers, and declarations of war.

### `commands`
Pending orders submitted by players for the next turn. Each command has a `type` (MOVE_ARMY, CAST_SPELL, etc.), a `target_id`, and a JSON `parameters` blob.

### `world_events`
Log of significant events that occurred during each turn (combat results, natural disasters, monster attacks, diplomatic changes).

---

## 18. Game Engine Modules

All engine modules live in `backend/app/engine/`. They are pure Python functions that take SQLAlchemy session + game state objects and return updated state. They do not talk to the API layer directly.

### `world_gen.py`

Generates new worlds. Key functions:

- `generate_map(width, height)` → list of sector records
- `place_nations(sectors, npc_count)` → starting positions for NPC nations
- `generate_deposits(sectors)` → scatter metal/jewel deposits
- `assign_vegetation(heightmap)` → correlated vegetation from elevation

Implements a multi-pass heightmap algorithm (ported from `hexmapX.c`) that produces realistic terrain with connected water bodies, mountain ranges, and fertile valleys.

### `economy.py`

Computes one turn of economic activity for a nation:

- `compute_production(nation, owned_sectors)` → resource deltas
- `compute_consumption(nation, armies, navies)` → resource costs
- `apply_seasonal_modifier(resource_type, julian_month)` → seasonal factor
- `check_shortfall(nation)` → returns list of deficit events

### `combat.py`

Resolves military engagements:

- `resolve_combat(attacker_army, defender_army, sector)` → `CombatResult`
- `apply_terrain_modifier(army, sector)` → strength multiplier
- `compute_casualties(attacker_strength, defender_strength)` → `(att_loss, def_loss)`
- `check_rout(army, casualty_pct)` → boolean (army flees if over rout threshold)

### `magic.py`

Processes spell effects:

- `cast_spell(nation, spell_type, target, session)` → `SpellResult`
- `apply_ongoing_effects(world, session)` → resolve persistent spells
- `check_spell_availability(nation, spell_type)` → boolean
- `compute_energy_cost(spell_type, nation)` → energy required

### `npc_ai.py`

NPC nation decision-making:

- `compute_npc_turn(nation, world, session)` → list of orders
- `evaluate_expansion(nation, sectors)` → target unclaimed sector
- `evaluate_threat(nation, neighbor_nations)` → mobilization decision
- `set_economic_designations(nation, owned_sectors)` → farm/mine balance

### `turn_processor.py`

Orchestrates all phases in sequence. Called by the Celery task:

```python
async def process_turn(world_id: UUID, session: AsyncSession):
    world = await get_world(world_id, session)
    await validate_commands(world, session)
    await resolve_movement(world, session)
    await resolve_combat(world, session)
    await compute_economy(world, session)
    await apply_consumption(world, session)
    await advance_construction(world, session)
    await apply_magic_effects(world, session)
    await process_npc_turns(world, session)
    await move_monsters(world, session)
    await advance_calendar(world, session)
    await generate_events(world, session)
    await check_victory_conditions(world, session)
    await write_turn_notifications(world, session)
    world.turn_number += 1
    await session.commit()
```

### `events.py`

Random world events:

- `generate_events(world, session)` → list of `WorldEvent` records
- Each event type has a base probability, modifiers based on world state, and an effect function
- Event types: drought (food penalty), earthquake (sector damage), plague (civilian deaths), magical surge (power boost), monster spawn, rebellion (high-tax sectors)

---

## 19. Frontend: React and TypeScript

### Tech Stack

- **React 19** with TypeScript
- **Vite 7** for fast development builds
- **Zustand 5** for global state management
- **Axios** for HTTP requests to the backend API
- **react-router-dom v7** for client-side routing

### Application Structure

```
frontend/src/
├── main.tsx           React entry point; router setup
├── App.tsx            Root component; auth guard
├── api/
│   ├── auth.ts        Login, register, token refresh
│   ├── worlds.ts      World listing, world detail
│   ├── nations.ts     Nation detail, join world
│   ├── sectors.ts     Sector info, designation changes
│   ├── armies.ts      Army orders, army movement
│   └── admin.ts       Admin operations
├── components/
│   ├── HexMap.tsx     SVG hex map renderer
│   ├── ArmyPanel.tsx  Army management sidebar
│   ├── SectorPanel.tsx  Sector info and designation
│   ├── NationDashboard.tsx  Resource and power summary
│   ├── JoinWorldPanel.tsx   New player onboarding
│   └── ...
├── pages/
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── WorldList.tsx
│   └── Game.tsx       Main game view
├── store/
│   ├── authStore.ts   Auth token, current user
│   ├── worldStore.ts  Active world state
│   └── gameStore.ts   Selected sector, army, turn state
└── types/
    └── index.ts       TypeScript interfaces matching backend schemas
```

### The Hex Map

`HexMap.tsx` renders the game world as an SVG element. Each sector is a hexagon. Rendering details:

- Hex fill color encodes terrain type
- Border color encodes owning nation (deterministic palette from nation ID hash)
- Selected sector: bright white border
- Reachable hexes (BFS from selected army): green highlight
- Player armies: gold; enemy armies: red; NPC armies: gray

The map supports pan (click-drag) and zoom (scroll wheel). Clicking a hex selects it and updates the sector panel and army panel in the sidebar.

### Army Panel

The army panel (`ArmyPanel.tsx`) shows:
- All armies owned by the player in the current world
- For each army: unit type name, strength bar, supply level, efficiency percentage
- "Find" button to center the map on the army
- Movement order submission (click target hex after selecting army)
- Collapsible first-steps guide (7-step new player tutorial, persisted in localStorage)

### Nation Dashboard

`NationDashboard.tsx` renders:
- Current resource stockpiles (talons, metals, jewels, wood, food)
- Per-turn production rate for each resource (+N per turn)
- Magic power bars (Military, Civilian, Wizardry) with current level and development rate
- Morale indicator

---

## 20. REST API Reference

### Authentication

```
POST   /auth/register     { username, email, password } → { access_token }
POST   /auth/login        { username, password } → { access_token }
GET    /auth/me           → current user profile
```

### Worlds

```
GET    /worlds            → list of active worlds
POST   /worlds            → create world (admin only)
GET    /worlds/{id}       → world detail (map summary)
GET    /worlds/{id}/sectors  → all sectors for map rendering
GET    /worlds/{id}/nations  → all nations in world
```

### Nations

```
GET    /worlds/{id}/nations/mine  → player's nation in this world (or 404)
POST   /nations           { world_id, name, race, class } → create nation
GET    /nations/{id}      → nation detail
PUT    /nations/{id}      → update orders (tax rate, etc.)
```

### Armies

```
GET    /armies?nation_id={id}     → list armies
GET    /armies/{id}               → army detail
POST   /armies/{id}/orders        { type: "MOVE", target_x, target_y } → queue order
```

### Sectors

```
GET    /sectors/{id}              → sector detail + owning nation
POST   /sectors/{id}/designate    { designation: "FARM" } → change designation
```

### Messages

```
GET    /messages?nation_id={id}   → inbox
POST   /messages                  { to_nation_id, body } → send message
```

### Admin

```
POST   /admin/worlds/{id}/turn         → process one turn
POST   /admin/worlds/{id}/maintenance  → toggle maintenance
DELETE /admin/worlds/{id}              → archive world
GET    /admin/nations/{id}             → full nation detail
```

---

## 21. Authentication and Security

### JWT Tokens

The API uses JWT (JSON Web Tokens) for stateless authentication. On login, the server issues a signed access token containing:

```json
{
  "sub": "user-uuid",
  "username": "playerone",
  "is_admin": false,
  "exp": 1234567890
}
```

The token is signed with `SECRET_KEY` using the HS256 algorithm (`python-jose`). Clients include it in every request as `Authorization: Bearer <token>`.

### Password Storage

Passwords are hashed with bcrypt at registration. The raw password is never stored or logged. Login compares the provided password against the stored hash using `bcrypt.checkpw()`.

### Authorization

FastAPI dependency functions enforce authorization:
- `get_current_user` — validates token; returns user or raises 401
- `get_current_admin` — additionally asserts `is_admin == True` or raises 403
- Nation ownership is checked in routers: a player can only issue orders for nations they own

---

## 22. Celery Task Queue

### Why Celery?

Turn processing is CPU and I/O intensive — it touches every army, every sector, every nation in the world. Running it synchronously in an API handler would block all other requests for potentially minutes. Celery offloads this work to a dedicated worker process.

### Setup

Three services in `docker-compose.yml`:
- **backend** — API server (no Celery)
- **worker** — `celery -A app.tasks.celery_app:celery_app worker` (processes tasks)
- **beat** — `celery -A app.tasks.celery_app:celery_app beat` (schedules recurring tasks)

### Turn Scheduling

Celery beat runs a periodic task to check whether any worlds are due for a turn. Turn frequency is configurable per world (e.g., every 24 hours, every 48 hours). When a world's turn is due:

1. Beat enqueues a `process_world_turn` task
2. Worker picks it up from the Redis queue
3. Worker runs `turn_processor.process_turn(world_id)`
4. Results are committed to PostgreSQL

This design means the API remains responsive during a 60-second turn processing job.

---

## 23. Docker Deployment

### Services

`docker-compose.yml` defines six services:

| Service | Image | Host Port | Purpose |
|---------|-------|-----------|---------|
| db | postgres:16-alpine | 5432 | Game database |
| redis | redis:7-alpine | 6379 | Celery broker + cache |
| backend | ./backend | 8001 | FastAPI API server |
| worker | ./backend | — | Celery turn worker |
| beat | ./backend | — | Celery turn scheduler |
| frontend | ./frontend | 5174 | React web client |

### Startup Order

The `depends_on` conditions ensure:
1. `db` and `redis` start first (with healthchecks)
2. `backend`, `worker`, and `beat` start only when `db` and `redis` are healthy
3. `frontend` starts when `backend` is running

### Database Migrations

The `backend` container runs `alembic upgrade head` before starting uvicorn. This means migrations are applied automatically on every startup, keeping the schema in sync with the code.

### Volume Persistence

`postgres_data` is a named Docker volume — database data persists across container restarts. To completely reset the game state:

```bash
docker compose down -v  # -v removes volumes
```

---

## 24. Development Setup

### Prerequisites

- Docker Desktop (Windows/macOS) or Docker Engine + Compose plugin (Linux)
- Git

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/webcloudstudio/conquer_2026
cd conquer_2026

# 2. Start everything
./bin/start.sh

# 3. Open the game
# Frontend:  http://localhost:5174
# API docs:  http://localhost:8001/docs
```

`bin/start.sh` automatically copies `.env.sample` to `backend/.env` if no `.env` exists. For production, edit `backend/.env` to set a strong `SECRET_KEY`.

### Backend-Only Development (no Docker)

```bash
cd backend
pip install -e ".[dev]" aiosqlite
# In-memory SQLite mode — no Postgres needed
pytest               # run tests
ruff check .         # lint
uvicorn app.main:app --reload --port 8000
```

### Frontend-Only Development

```bash
cd frontend
npm install
npm run dev          # Vite dev server at http://localhost:5173
```

The Vite config proxies `/api` requests to `http://localhost:8001` during development.

### C Reference Build

If you need to consult the original game behavior:

```bash
cd gpl-release
cp Include/header.h.dist Include/header.h
# Edit header.h to set OWNER and LOGIN
make Makefiles
make build
./Src/conqrun -m   # Create a test world
./Src/conquer -n godname  # Login as god
```

---

## 25. Configuration Reference

All backend configuration is via environment variables. The canonical template is `.env.sample`:

| Variable | Default (sample) | Description |
|----------|-----------------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://conquer:conquer@localhost:5432/conquer` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `SECRET_KEY` | `change-me-before-deploying` | JWT signing secret — **must be changed in production** |
| `DEBUG` | `true` | Enables uvicorn reload and verbose logging |

In Docker Compose, these are set in the `environment:` stanza of `docker-compose.yml`. For local development outside Docker, copy `.env.sample` to `backend/.env`.

Frontend configuration (Vite):

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8001` | Backend API base URL |

---

## 26. Running and Administering the Game

### Starting a New World

1. Start the stack: `./bin/start.sh`
2. Register an admin account at `http://localhost:5174`
3. Access the admin panel or use the API directly:

```bash
curl -X POST http://localhost:8001/admin/worlds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "World I", "width": 60, "height": 40, "max_nations": 20}'
```

4. The world is generated; NPC nations are placed automatically.
5. Human players register accounts and join the world.

### Processing Turns

Turns can be processed manually:

```bash
curl -X POST http://localhost:8001/admin/worlds/{world_id}/turn \
  -H "Authorization: Bearer $TOKEN"
```

Or automatically by the Celery beat scheduler (configured in `backend/app/tasks/celery_app.py`).

### Maintenance Mode

To temporarily block players from submitting orders (e.g., for server maintenance or game balance corrections):

```bash
curl -X POST http://localhost:8001/admin/worlds/{world_id}/maintenance \
  -H "Authorization: Bearer $TOKEN"
```

This sets the world's `is_maintenance` flag. Players see a maintenance notice.

### Archiving a World

When a game concludes, archive it:

```bash
curl -X DELETE http://localhost:8001/admin/worlds/{world_id} \
  -H "Authorization: Bearer $TOKEN"
```

This exports all nations, sectors, armies, messages, and commands to a JSON archive in `data/`, then sets `is_active=False`. The world remains in the database for historical reference.

---

## 27. Gameplay Walkthrough: Your First Five Turns

This walkthrough assumes a new player joining an active world.

### Before Turn 1: Setup

1. Register at the login screen
2. Choose a world from the world browser
3. Click "Join World" in the game UI
4. Enter your nation name, choose race (recommend Human for beginners), choose class (recommend Merchant or Ranger)
5. Your nation is created with starting resources: 5,000 talons, 2,000 food, 500 metals, 500 wood, 100 jewels
6. A 2,000-strength army is placed at your capital sector
7. Four adjacent sectors are designated as farms

### Turn 1: Survey and Stabilize

- Open the Nation Dashboard. Check your production rates. You should be producing +food from your farms and +talons from your capital.
- Open the Army Panel. Find your starting army.
- On the hex map, identify adjacent unclaimed sectors. Look for `g` (good vegetation) for more farms, or mineral deposits.
- Issue no combat orders yet. Focus on designating 1–2 more farms in adjacent unclaimed sectors.
- Adjust tax rate to 20–30% to maintain morale while generating some talons.

### Turn 2: Expand

- After turn processing, your new farm designations are complete.
- Identify the nearest unclaimed sectors with mineral deposits.
- Move your starting army to claim an adjacent sector (army movement order: select army, click target hex, submit).
- Designate that sector as a mine if it has metal deposits.

### Turn 3: Economic Foundation

- Check your resource levels. You should now have food surplus building.
- Begin saving metals for your first fortification (build a fort at your capital if any enemy NPC nations are nearby).
- Invest a small amount (50–100 jewels) into civilian power development to start building magic capacity.

### Turn 4: Military Expansion

- Your army's efficiency should be near 100% after resting.
- Scout surrounding territory. Are any NPC nations close to your capital?
- Begin a second army if your talons and metals allow (use the admin create-army endpoint or the army creation UI).
- Consider claiming 2–3 more sectors; designate a lumberyard if you find a forest sector.

### Turn 5: First Combat

- If you've encountered an NPC nation with weak forces, consider an attack. Issue a MOVE order to an adjacent NPC-owned sector.
- If the NPC has more strength than your army, do not attack — focus on building up over 2–3 more turns first.
- Read your turn notification after processing. Combat reports detail casualties on both sides.

---

## 28. Mapping the C Source to Python

For developers working on the game engine, this table maps original C files to their Python equivalents:

| C Source File | Purpose | Python Equivalent |
|--------------|---------|-----------------|
| `gpl-release/Src/dataX.c` | Core data structures, memory management | `backend/app/models/` (SQLAlchemy models) |
| `gpl-release/Include/dataX.h` | C struct definitions | `backend/app/models/` + `schemas/` |
| `gpl-release/Src/economyA.c` | Production and consumption calculations | `backend/app/engine/economy.py` |
| `gpl-release/Src/combatA.c` | Military combat resolution | `backend/app/engine/combat.py` |
| `gpl-release/Src/magicA.c` | Spell casting and effects (admin side) | `backend/app/engine/magic.py` |
| `gpl-release/Src/magicX.c` | Shared magic computation | `backend/app/engine/magic.py` |
| `gpl-release/Include/spellsX.h` | Spell definitions and constants | `backend/app/engine/magic.py` (inline) |
| `gpl-release/Src/hexmapX.c` | Hex grid math and world generation | `backend/app/engine/world_gen.py` |
| `gpl-release/Src/hexmapG.c` | Display-side hex rendering | `frontend/src/components/HexMap.tsx` |
| `gpl-release/Src/npcA.c` | NPC nation AI | `backend/app/engine/npc_ai.py` |
| `gpl-release/Src/monsterA.c` | Monster behavior | `backend/app/engine/npc_ai.py` |
| `gpl-release/Include/nclassX.h` | NPC class definitions | `backend/app/engine/npc_ai.py` (inline) |
| `gpl-release/Src/executeX.c` | Turn execution orchestration | `backend/app/engine/turn_processor.py` |
| `gpl-release/Src/computeX.c` | Auxiliary computation | `backend/app/engine/turn_processor.py` |
| `gpl-release/Src/caravanG.c` | Caravan movement and trade | `backend/app/routers/nations.py` + engine |
| `gpl-release/Src/navyG.c` | Naval movement | `backend/app/engine/combat.py` (naval branch) |
| `gpl-release/Src/armyG.c` | Army orders (player side) | `backend/app/routers/armies.py` |
| `gpl-release/Src/moveG.c` | Movement pathfinding | `backend/app/engine/world_gen.py` (BFS) |
| `gpl-release/Src/mainA.c` | `conqrun` entry point | `backend/app/main.py` + admin router |
| `gpl-release/Src/mainG.c` | `conquer` entry point | `frontend/src/pages/Game.tsx` |
| `gpl-release/Src/displayG.c` | ncurses display | `frontend/src/components/` |
| `gpl-release/Src/iodataX.c` | Binary file I/O | SQLAlchemy ORM (implicit) |
| `gpl-release/Src/dataA.c` | Admin data management | `backend/app/routers/admin.py` |
| `gpl-release/Src/mailG.c` / `mailA.c` | In-game messaging | `backend/app/routers/messages.py` |

---

## 29. Changelog and Development History

### 2026-03-16 — Repository Reorganization

- Moved `new/` application to project root (backend/, frontend/, doc/, docker-compose.yml)
- Created `bin/` directory with `start.sh`, `stop.sh`, `build.sh`, `common.sh`
- Created `.env.sample`
- Updated `METADATA.md` to reflect current stack (FastAPI/React/PostgreSQL/Redis)
- Updated `AGENTS.md` with correct dev commands and service endpoints
- Wrote comprehensive project guide (`doc/project_guide.md`)

### 2026-02 — Game UI and Player Initialization

- Manage Worlds: delete world archives data to `data/`, then soft-deletes
- Manage Worlds: process turn (green button), maintenance (yellow button)
- Backend: `DELETE /admin/worlds/{id}` archives to JSON before soft-delete
- Fixed new player join: `initialize_player_nation()` provides starting resources (5k talons, 2k food, 500 metals/wood, 100 jewels), capital army (2000 strength), farm ring (4 adjacent sectors)
- Game UI: ArmyPanel collapsible "First Steps" guide (7 steps)
- Fixed player nation detection: `GET /worlds/{id}/nations/mine`
- NationOut schema: returns `user_id`, `attr_morale`, `power_*`, `*_produced` fields
- Game UI: NationDashboard renders production rates
- Game UI: magic power bars labeled Military / Civilian / Wizardry
- Game UI: player armies gold, enemies red, NPCs gray
- Game UI: hex borders colored per owning nation
- Game UI: reachable hex highlighting (green BFS from selected army)
- Game UI: army panel "Find" button centers map on army
- Game UI: SectorPanel ownership badge (Your sector / Enemy / Unclaimed)
- Game UI: JoinWorldPanel in sidebar when player has not joined
- Converted all 15 original 1987 nroff docs to HTML (doc/original/)
- docs/style.css: navigation and styling for all 12 documentation pages

### Phase 1 (2025) — Foundation

- Docker Compose stack: PostgreSQL, Redis, FastAPI, Celery, React
- SQLAlchemy ORM: 14 models matching C struct definitions
- Alembic migration history
- JWT authentication (python-jose + bcrypt)
- FastAPI routers: auth, worlds, nations, sectors, armies, messages, admin
- Pydantic schemas for all request/response types
- pytest suite with in-memory SQLite fixtures
- Vite + React 19 + TypeScript frontend scaffolding
- Zustand state management
- CI/CD: GitHub Actions (build, test, lint)

---

## 30. License, Credits, and Appendices

### License

Conquer 2026 is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

The original 1987 Conquer game was written by Adam Bryant. The GPL-3.0-or-later re-license was granted in 2025, making this project possible.

Full license text: `LICENSES/GPL-3.0-or-later.txt`
License notice: `LICENSE-NOTICE.md`
REUSE compliance: `REUSE.toml`

### Credits

- **Original Author**: Adam Bryant (1987)
- **GPL Re-license**: 2025
- **Modern Port**: Conquer 2026 project

### Appendix A: Julian Calendar Reference

| Julian Month | Modern Equivalent | Season |
|-------------|------------------|--------|
| Martius | March | Spring |
| Aprillis | April | Spring |
| Maius | May | Spring |
| Junius | June | Summer |
| Quintilis | July | Summer |
| Sextilis | August | Summer |
| Septembre | September | Fall |
| Octobre | October | Fall |
| Novembre | November | Fall |
| Decembre | December | Winter |
| Januarius | January | Winter |
| Februarius | February | Winter |

### Appendix B: Vegetation Quick Reference

| Symbol | Type | Food | Wood | Best Race |
|--------|------|------|------|-----------|
| `g` | Good | 9 | 2 | All |
| `w` | Wood | 7 | 4 | All |
| `l` | Light Vegetation | 6 | 1 | All |
| `f` | Forest | 4 | 8 | Elf |
| `b` | Barren | 4 | 0 | Dwarf, Human |
| `j` | Jungle | 0 | 10 | Orc |
| `"` | Swamp | 0 | 2 | Orc |
| `.` | Desert | 0 | 0 | — |
| `i` | Ice | 0 | 0 | — |
| `,` | Tundra | 0 | 0 | — |
| `!` | Volcano | 0 | 0 | — |
| `~` | Water (none) | 0 | 0 | — |

### Appendix C: Terrain Modifier Reference

| Terrain | Symbol | Movement Cost | Defense Bonus |
|---------|--------|--------------|--------------|
| Water | `~` | Impassable (land) | — |
| Valley | `v` | 1 | None |
| Clear | ` ` | 1 | +10% |
| Hill | `h` | 2 | +30% |
| Mountain | `m` | 4 | +60% |
| Peak | `^` | 8 | +100% |

### Appendix D: Unit Type Summary (40 Types)

Unit types 1–40 map to the `UnitTypeName` lookup in `frontend/src/types/index.ts`. Broad categories:

- **1–10**: Standard infantry (footsoldiers through elite guards)
- **11–18**: Cavalry (light to heavy horse)
- **19–24**: Siege (ballista, catapult, siege tower)
- **25–32**: Magical units (warlocks, golems, summoned creatures)
- **33–40**: Naval units (scout galley through heavy warship)

### Appendix E: API Port Reference

| Service | Internal Port | Exposed Port |
|---------|-------------|-------------|
| PostgreSQL | 5432 | 5432 |
| Redis | 6379 | 6379 |
| FastAPI backend | 8000 | 8001 |
| React frontend | 80 (nginx) | 5174 |

---

*This document was written from the combined source of the original 1987 game documentation (doc/original/) and the Python/React reimplementation (backend/, frontend/). For the most up-to-date API reference, consult the live Swagger docs at http://localhost:8001/docs when the stack is running.*
