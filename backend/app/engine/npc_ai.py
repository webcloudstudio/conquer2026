"""
NPC AI engine — goal-oriented behaviour for computer-controlled nations.

The original C npcA.c was entirely wrapped in #ifdef NOT_DONE and never
implemented. This is the completed version.

Strategy pipeline per NPC turn:
  1. Evaluate military strength vs. neighbours
  2. Assign sector designations for economic optimisation
  3. Move armies toward high-value unclaimed territory (BFS)
  4. Attack if adjacent enemy sector is weak enough
  5. Produce a turn log
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Data classes passed in from the turn service
# ---------------------------------------------------------------------------

@dataclass
class NpcSector:
    x: int
    y: int
    altitude: int
    designation: int          # mirrors Designation enum
    efficiency: int
    population: int
    minerals: int
    owner_nation_id: str | None


@dataclass
class NpcArmy:
    id: str
    nation_id: str
    strength: int
    efficiency: int
    movement: int
    x: int
    y: int
    is_active: bool = True


@dataclass
class NpcNation:
    id: str
    player_class: str
    attack_bonus: int = 0
    defense_bonus: int = 0
    food: int = 0
    talons: int = 0


@dataclass
class NpcOrder:
    """Emitted action for the turn service to apply."""
    kind: str          # "move" | "attack" | "designate" | "disband"
    army_id: str | None = None
    nation_id: str | None = None
    x: int = 0
    y: int = 0
    designation: int = 0
    message: str = ""


@dataclass
class NpcTurnResult:
    orders: list[NpcOrder] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Hex geometry helpers
# ---------------------------------------------------------------------------

def _hex_neighbours(x: int, y: int) -> list[tuple[int, int]]:
    """Even-row offset hex neighbours."""
    if y % 2 == 0:
        return [(x-1,y),(x+1,y),(x,y-1),(x,y+1),(x-1,y-1),(x-1,y+1)]
    return [(x-1,y),(x+1,y),(x,y-1),(x,y+1),(x+1,y-1),(x+1,y+1)]


def _bfs_nearest(
    start_x: int,
    start_y: int,
    max_dist: int,
    sector_map: dict[tuple[int, int], NpcSector],
    predicate,
) -> tuple[int, int] | None:
    """BFS to find the nearest sector matching predicate within max_dist steps."""
    visited: set[tuple[int, int]] = {(start_x, start_y)}
    q: deque[tuple[int, int, int]] = deque([(start_x, start_y, 0)])
    while q:
        cx, cy, d = q.popleft()
        if d > 0:
            sct = sector_map.get((cx, cy))
            if sct and predicate(sct):
                return cx, cy
        if d >= max_dist:
            continue
        for nx, ny in _hex_neighbours(cx, cy):
            if (nx, ny) not in visited and (nx, ny) in sector_map:
                visited.add((nx, ny))
                q.append((nx, ny, d + 1))
    return None


def _step_toward(
    start_x: int,
    start_y: int,
    goal_x: int,
    goal_y: int,
    sector_map: dict[tuple[int, int], NpcSector],
    movement: int,
) -> tuple[int, int]:
    """BFS path and return the sector reachable in `movement` steps."""
    if (start_x, start_y) == (goal_x, goal_y):
        return start_x, start_y

    # BFS up to movement range, prefer steps that reduce distance
    visited: set[tuple[int, int]] = {(start_x, start_y)}
    Step = tuple[int, int, int, tuple[int, int]]
    q: deque[Step] = deque([(start_x, start_y, 0, (start_x, start_y))])
    best: tuple[int, int] = (start_x, start_y)
    best_dist = _approx_dist(start_x, start_y, goal_x, goal_y)

    while q:
        cx, cy, steps, first_step = q.popleft()
        d = _approx_dist(cx, cy, goal_x, goal_y)
        if d < best_dist:
            best_dist = d
            best = first_step if steps > 0 else (cx, cy)
        if steps >= movement:
            continue
        for nx, ny in _hex_neighbours(cx, cy):
            sct = sector_map.get((nx, ny))
            if sct and (nx, ny) not in visited and sct.altitude > 0:
                visited.add((nx, ny))
                fs = (nx, ny) if steps == 0 else first_step
                q.append((nx, ny, steps + 1, fs))

    return best


def _approx_dist(x1: int, y1: int, x2: int, y2: int) -> int:
    return abs(x1 - x2) + abs(y1 - y2)


# ---------------------------------------------------------------------------
# Sector value scoring
# ---------------------------------------------------------------------------

def _sector_value(s: NpcSector) -> int:
    """Score an unclaimed sector — higher is more desirable."""
    if s.altitude == 0:
        return 0  # water — impassable
    score = s.efficiency
    score += s.minerals * 5
    score += s.population // 500
    return score


# ---------------------------------------------------------------------------
# Main NPC turn function
# ---------------------------------------------------------------------------

def run_npc_turn(
    nation: NpcNation,
    armies: list[NpcArmy],
    sectors: list[NpcSector],
    all_armies: list[NpcArmy],
    rng: random.Random | None = None,
) -> NpcTurnResult:
    """
    Run one turn of NPC AI for a single nation.
    Returns orders for the turn service to apply.
    """
    if rng is None:
        rng = random.Random()

    result = NpcTurnResult()
    sector_map: dict[tuple[int, int], NpcSector] = {(s.x, s.y): s for s in sectors}

    # Group all armies by hex for adjacency checks
    enemy_by_hex: dict[tuple[int, int], list[NpcArmy]] = {}
    for a in all_armies:
        if a.nation_id != nation.id and a.is_active:
            key = (a.x, a.y)
            enemy_by_hex.setdefault(key, []).append(a)

    my_armies = [a for a in armies if a.is_active and a.strength > 0]

    for army in my_armies:
        ax, ay = army.x, army.y

        # 1. Check if any adjacent hex has a weak enemy army → attack
        attacked = False
        for nx, ny in _hex_neighbours(ax, ay):
            enemies = enemy_by_hex.get((nx, ny), [])
            if not enemies:
                continue
            target = enemies[0]
            # Only attack if we have advantage (strength > 1.2× enemy)
            if army.strength > target.strength * 1.2:
                result.orders.append(NpcOrder(
                    kind="attack",
                    army_id=army.id,
                    nation_id=nation.id,
                    x=nx, y=ny,
                    message=f"NPC {nation.id[:8]} attacks ({nx},{ny})",
                ))
                result.messages.append(f"NPC army attacks ({nx},{ny})")
                attacked = True
                break

        if attacked:
            continue

        # 2. Claim adjacent unclaimed sectors
        claimed = False
        adjacent_unclaimed = [
            sector_map[(nx, ny)]
            for nx, ny in _hex_neighbours(ax, ay)
            if (nx, ny) in sector_map
            and sector_map[(nx, ny)].owner_nation_id is None
            and sector_map[(nx, ny)].altitude > 0
        ]
        if adjacent_unclaimed:
            # Pick the best adjacent unclaimed sector
            target_sct = max(adjacent_unclaimed, key=_sector_value)
            result.orders.append(NpcOrder(
                kind="move",
                army_id=army.id,
                nation_id=nation.id,
                x=target_sct.x, y=target_sct.y,
                message=f"NPC expands to ({target_sct.x},{target_sct.y})",
            ))
            claimed = True

        if claimed:
            continue

        # 3. BFS to nearest unowned land sector and move toward it
        goal = _bfs_nearest(
            ax, ay,
            max_dist=army.movement * 3,
            sector_map=sector_map,
            predicate=lambda s: s.owner_nation_id is None and s.altitude > 0,
        )
        if goal:
            tx, ty = _step_toward(ax, ay, goal[0], goal[1], sector_map, army.movement)
            if (tx, ty) != (ax, ay):
                result.orders.append(NpcOrder(
                    kind="move",
                    army_id=army.id,
                    nation_id=nation.id,
                    x=tx, y=ty,
                    message=f"NPC army ({ax},{ay}) → ({tx},{ty})",
                ))
        else:
            # 4. Random wander if nothing to do
            neighbours = [
                (nx, ny) for nx, ny in _hex_neighbours(ax, ay)
                if (nx, ny) in sector_map and sector_map[(nx, ny)].altitude > 0
            ]
            if neighbours:
                nx, ny = rng.choice(neighbours)
                result.orders.append(NpcOrder(
                    kind="move",
                    army_id=army.id,
                    nation_id=nation.id,
                    x=nx, y=ny,
                ))

    # 5. Designate owned sectors for economic benefit
    owned = [s for s in sectors if s.owner_nation_id == nation.id]
    for s in owned:
        if s.designation == 0:  # UNDESIGNATED
            if s.minerals > 3:
                result.orders.append(NpcOrder(
                    kind="designate",
                    nation_id=nation.id,
                    x=s.x, y=s.y,
                    designation=2,  # MINE
                ))
            elif s.altitude <= 3:
                result.orders.append(NpcOrder(
                    kind="designate",
                    nation_id=nation.id,
                    x=s.x, y=s.y,
                    designation=1,  # FARM
                ))

    return result
