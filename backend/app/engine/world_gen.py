"""
World generation engine — translates hexmapG.c / hexmapX.c / elevegX.h logic to Python.

Reference: gpl-release/Src/hexmapG.c, gpl-release/Src/hexmapX.c,
           gpl-release/Include/elevegX.h

Generation pipeline (mirrors C original):
  1. Seed random altitude grid
  2. Smooth N times (each cell averaged with its 6 hex neighbours)
  3. Water threshold: lowest pwater% cells become ocean (altitude 0)
  4. Mountain threshold: highest pmount% land cells become mountains (altitude 8–10)
  5. Assign vegetation based on altitude + latitude position
  6. Scatter minerals and trade goods across land sectors
  7. Find player/NPC spawn points (separated by min_separation hexes)

Hex coordinate system (offset grid from hexmapX.c):
  - Odd columns are shifted up by 0.5 in display
  - Hex neighbours of (x, y): depends on whether x is even or odd
  - Hex distance: map_within() in hexmapX.c using ycount calculation
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class SectorData:
    x: int
    y: int
    altitude: int = 0     # 0=water, 1–5=valley/flat/hill, 6–7=mountain, 8–10=peak
    designation: int = 0  # Designation enum value
    vegetation: int = 0   # Vegetation enum value
    owner_nation_id: object = None
    population: int = 0
    minerals: int = 0     # jewel/metal deposit value
    tradegood: int = 0    # exotic trade good value
    efficiency: int = 50


@dataclass
class GeneratedWorld:
    mapx: int
    mapy: int
    sectors: list[SectorData] = field(default_factory=list)
    npc_spawn_points: list[tuple[int, int]] = field(default_factory=list)
    player_spawn_points: list[tuple[int, int]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hex neighbour calculation — from hexmapX.c
# ---------------------------------------------------------------------------

def hex_neighbours(x: int, y: int, mapx: int, mapy: int) -> list[tuple[int, int]]:
    """
    Return the (up to 6) valid neighbours of hex (x, y).

    Reference: hexmapX.c offset-coordinate adjacency.
    Even columns: neighbours are (x-1,y-1),(x,y-1),(x+1,y-1),(x-1,y),(x+1,y),(x,y+1)
    Odd columns shift the vertical neighbours.
    """
    if x % 2 == 0:
        candidates = [
            (x - 1, y - 1), (x, y - 1), (x + 1, y - 1),
            (x - 1, y),                   (x + 1, y),
            (x - 1, y + 1), (x, y + 1), (x + 1, y + 1),
        ]
        # For a hex grid (even col), drop the 2 corner diagonals
        candidates = [
            (x - 1, y - 1), (x, y - 1),
            (x - 1, y),     (x + 1, y),
            (x - 1, y + 1), (x, y + 1),
        ]
    else:
        candidates = [
            (x, y - 1),     (x + 1, y - 1),
            (x - 1, y),     (x + 1, y),
            (x, y + 1),     (x + 1, y + 1),
        ]

    return [
        (nx, ny)
        for nx, ny in candidates
        if 0 <= nx < mapx and 0 <= ny < mapy
    ]


def hex_distance(x1: int, y1: int, x2: int, y2: int) -> int:
    """
    Approximate hex distance using the ycount formula from hexmapX.c.

    Reference: hexmapX.c :: map_within()
      ycount = 2 * range - abs(xcent - xloc)
      if ycount > 0: check y within [ycent - ycount/2, ycent + ycount/2]
    This implements the inverse: given two points, return the min range
    such that map_within would return true.
    """
    dx = abs(x2 - x1)
    # Adjusted vertical component: hex columns shift vertically
    dy = abs(y2 - y1)
    # Hex distance formula for offset coordinates
    return max(dx, dy, (dx + dy + 1) // 2)


# ---------------------------------------------------------------------------
# Altitude / smoothing
# ---------------------------------------------------------------------------

def _smooth_once(
    grid: list[list[float]],
    mapx: int,
    mapy: int,
    rng: random.Random,
) -> list[list[float]]:
    """One pass of hex-neighbour smoothing (mirrors the C smooth_map loop)."""
    new_grid = [[0.0] * mapy for _ in range(mapx)]
    for x in range(mapx):
        for y in range(mapy):
            neighbours = hex_neighbours(x, y, mapx, mapy)
            total = grid[x][y]
            for nx, ny in neighbours:
                total += grid[nx][ny]
            new_grid[x][y] = total / (1 + len(neighbours))
    return new_grid


def _build_altitude_grid(
    mapx: int,
    mapy: int,
    pwater: int,
    pmount: int,
    smoothings: int,
    rng: random.Random,
) -> list[list[int]]:
    """
    Generate smoothed altitude grid; returns int altitude values 0–10.

    Water threshold: bottom pwater% by altitude become ocean (0).
    Mountain threshold: top pmount% of land become mountains (8–10).
    Mid range land: 1–7 (valley, flat, hill).
    """
    # Seed random values 0–100
    grid: list[list[float]] = [
        [float(rng.randint(0, 100)) for _ in range(mapy)]
        for _ in range(mapx)
    ]

    # Smooth
    for _ in range(smoothings):
        grid = _smooth_once(grid, mapx, mapy, rng)

    # Collect all values and compute thresholds
    values = sorted(grid[x][y] for x in range(mapx) for y in range(mapy))
    total_cells = mapx * mapy

    water_cutoff = values[int(total_cells * pwater / 100)]
    # Mountain threshold is top pmount% of land cells
    land_values = [v for v in values if v > water_cutoff]
    if land_values:
        mount_cutoff = land_values[max(0, len(land_values) - int(len(land_values) * pmount / 100))]
    else:
        mount_cutoff = float("inf")

    # Convert to integer altitude
    alt_grid: list[list[int]] = [[0] * mapy for _ in range(mapx)]
    for x in range(mapx):
        for y in range(mapy):
            v = grid[x][y]
            if v <= water_cutoff:
                alt = 0   # WATER
            elif v >= mount_cutoff:
                # Peaks at very top, mountains below
                peak_cutoff = water_cutoff + (mount_cutoff - water_cutoff) * 0.9
                alt = 10 if v >= peak_cutoff else 8
            else:
                # Interpolate land altitude 1–7
                land_range = mount_cutoff - water_cutoff
                pos = (v - water_cutoff) / land_range if land_range > 0 else 0.5
                alt = 1 + int(pos * 6)   # 1 (valley) to 7 (high hill)
            alt_grid[x][y] = max(0, min(10, alt))

    return alt_grid


# ---------------------------------------------------------------------------
# Vegetation assignment
# ---------------------------------------------------------------------------

# Vegetation enum values from app/models/sector.py:
# NONE=0, SPARSE=1, GRASSLAND=2, FOREST=3, JUNGLE=4, SWAMP=5,
# DESERT=6, TUNDRA=7, TAIGA=8, WETLAND=9, MEADOW=10, SCRUB=11
_VEG_NONE = 0
_VEG_SPARSE = 1
_VEG_GRASSLAND = 2
_VEG_FOREST = 3
_VEG_JUNGLE = 4
_VEG_SWAMP = 5
_VEG_DESERT = 6
_VEG_TUNDRA = 7
_VEG_TAIGA = 8
_VEG_WETLAND = 9
_VEG_MEADOW = 10
_VEG_SCRUB = 11


def _assign_vegetation(
    x: int,
    y: int,
    altitude: int,
    mapy: int,
    rng: random.Random,
) -> int:
    """
    Assign vegetation type based on altitude and latitude.

    Reference: hexmapX.c terrain assignment.
    Latitude proxy: y position on the map (north=0, south=mapy-1).
    """
    if altitude == 0:
        return _VEG_NONE  # ocean

    # Normalised latitude 0.0 (equator-ish) to 1.0 (polar)
    lat = abs(2 * y / mapy - 1.0)  # 0 at centre, 1 at edges

    if altitude >= 10:   # peak
        return _VEG_TUNDRA if lat > 0.5 else _VEG_SPARSE

    if altitude >= 8:    # mountain
        return rng.choice([_VEG_SPARSE, _VEG_TAIGA, _VEG_TUNDRA])

    if altitude >= 6:    # high hill
        if lat > 0.7:
            return rng.choice([_VEG_TUNDRA, _VEG_TAIGA])
        return rng.choice([_VEG_FOREST, _VEG_SCRUB, _VEG_GRASSLAND])

    if altitude >= 4:    # mid hill
        if lat > 0.6:
            return rng.choice([_VEG_TAIGA, _VEG_SCRUB])
        return rng.choice([_VEG_FOREST, _VEG_GRASSLAND, _VEG_MEADOW])

    # Lowland (1–3)
    if lat > 0.7:
        return rng.choice([_VEG_TUNDRA, _VEG_SCRUB, _VEG_SPARSE])
    if lat > 0.4:
        return rng.choice([_VEG_GRASSLAND, _VEG_MEADOW, _VEG_WETLAND, _VEG_FOREST])
    # Tropical belt
    roll = rng.randint(0, 9)
    if roll < 3:
        return _VEG_JUNGLE
    if roll < 5:
        return _VEG_SWAMP
    if roll < 8:
        return _VEG_GRASSLAND
    return _VEG_DESERT


# ---------------------------------------------------------------------------
# Mineral / trade good placement
# ---------------------------------------------------------------------------

def _scatter_minerals(
    sectors: dict[tuple[int, int], SectorData],
    ptrade: int,
    rng: random.Random,
) -> None:
    """
    Randomly assign mineral deposits and trade goods to land sectors.

    ptrade: percentage of land sectors that carry a trade good (0–100).
    Mountains have higher mineral probability; good vegetation has trade goods.
    """
    land = [s for s in sectors.values() if s.altitude > 0]

    for s in land:
        # Mineral deposits: more likely in mountains
        if s.altitude >= 6:
            if rng.randint(0, 99) < 40:
                s.minerals = rng.randint(1, 10)
        elif s.altitude >= 3:
            if rng.randint(0, 99) < 15:
                s.minerals = rng.randint(1, 5)

        # Trade goods
        if rng.randint(0, 99) < ptrade:
            s.tradegood = rng.randint(1, 5)


# ---------------------------------------------------------------------------
# Spawn point finder — from createA.c :: find_start_location()
# ---------------------------------------------------------------------------

def find_spawn_points(
    world: GeneratedWorld,
    count: int,
    min_separation: int = 5,
    require_land: bool = True,
) -> list[tuple[int, int]]:
    """
    Find valid spawn points for nations, separated by at least min_separation hexes.

    Reference: createA.c :: find_start_location()
    Prefer moderate-altitude sectors (not mountains, not coast) with good vegetation.
    """
    # Candidate sectors: land, not ocean or peak
    candidates = [
        s for s in world.sectors
        if (not require_land or s.altitude > 0)
        and s.altitude < 9
        and s.vegetation not in (_VEG_SWAMP, _VEG_JUNGLE)
    ]

    # Score candidates: prefer mid-altitude, good vegetation
    def _score(s: SectorData) -> int:
        score = 0
        if 2 <= s.altitude <= 5:
            score += 3
        if s.vegetation in (_VEG_GRASSLAND, _VEG_MEADOW, _VEG_FOREST):
            score += 2
        return score

    candidates.sort(key=_score, reverse=True)

    chosen: list[tuple[int, int]] = []
    for s in candidates:
        pt = (s.x, s.y)
        # Check separation from already chosen points
        if all(hex_distance(pt[0], pt[1], cx, cy) >= min_separation for cx, cy in chosen):
            chosen.append(pt)
            if len(chosen) >= count:
                break

    return chosen


# ---------------------------------------------------------------------------
# Main world generation entry point
# ---------------------------------------------------------------------------

def generate_world(
    mapx: int = 79,
    mapy: int = 49,
    pwater: int = 35,
    pmount: int = 20,
    smoothings: int = 3,
    ptrade: int = 15,
    seed: int | None = None,
) -> GeneratedWorld:
    """
    Generate a complete world map.

    Reference: hexmapX.c :: generate_map(), smooth_map(), assign_terrain()

    Returns a GeneratedWorld with all sectors populated and spawn points identified.
    """
    rng = random.Random(seed)

    # Step 1–4: Generate altitude grid
    alt_grid = _build_altitude_grid(mapx, mapy, pwater, pmount, smoothings, rng)

    # Step 5: Build sector list with terrain
    sectors: dict[tuple[int, int], SectorData] = {}
    for x in range(mapx):
        for y in range(mapy):
            alt = alt_grid[x][y]
            veg = _assign_vegetation(x, y, alt, mapy, rng)
            sectors[(x, y)] = SectorData(
                x=x,
                y=y,
                altitude=alt,
                vegetation=veg,
                efficiency=rng.randint(40, 80) if alt > 0 else 0,
            )

    # Step 6: Scatter minerals and trade goods
    _scatter_minerals(sectors, ptrade, rng)

    # Build GeneratedWorld
    world = GeneratedWorld(
        mapx=mapx,
        mapy=mapy,
        sectors=list(sectors.values()),
    )

    # Step 7: Find spawn points
    player_spawns = find_spawn_points(world, count=16, min_separation=8)
    npc_spawns = find_spawn_points(world, count=32, min_separation=4)

    world.player_spawn_points = player_spawns
    world.npc_spawn_points = npc_spawns

    return world
