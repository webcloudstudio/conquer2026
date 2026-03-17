"""
World events engine — random events that fire each turn.

Implements the events defined in the plan:
  - Weather (drought, blizzard, flood, perfect growing season)
  - Geological (earthquake, treasure strike)
  - Social (plague, mercenary arrival, trade fair, peasant uprising)
  - Magical (ley line surge, ancient ruins, wandering dragon)
  - Chained events

Each event is represented by an EventDef that specifies:
  - fire_chance: probability per turn (0-100) that it fires
  - duration: how many turns the effect lasts
  - category: for chain-trigger filtering
  - apply(): modifies the NationState / SectorState list in-place
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# State stubs — the events engine works on lightweight dicts so it doesn't
# import the full ORM.  The turn service maps ORM objects to these.
# ---------------------------------------------------------------------------

@dataclass
class EventSectorState:
    x: int
    y: int
    designation: int
    efficiency: int
    population: int
    food_modifier: float = 1.0   # multiplier applied to food production this turn
    is_passable: bool = True


@dataclass
class EventNationState:
    id: str
    food: int
    attr_morale: int
    attr_spell_pts: int
    victory_points: int
    power_military: int
    owned_sector_count: int = 0


@dataclass
class ActiveEvent:
    event_type: str
    turns_remaining: int
    affected_sectors: list[tuple[int, int]] = field(default_factory=list)
    severity: int = 1
    icon: str = ""


@dataclass
class EventResult:
    active_events: list[ActiveEvent] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    sector_changes: list[dict] = field(default_factory=list)   # {x,y,field,delta}
    nation_changes: list[dict] = field(default_factory=list)   # {nation_id,field,delta}
    new_artifacts: list[dict] = field(default_factory=list)    # {x,y,rarity}


# ---------------------------------------------------------------------------
# Event definitions
# ---------------------------------------------------------------------------

@dataclass
class EventDef:
    name: str
    event_type: str
    category: str
    fire_chance: int        # % chance per turn this fires
    duration: tuple[int, int]  # (min, max) turns
    severity: tuple[int, int]  # (min, max) severity level
    icon: str
    chains_to: list[str] = field(default_factory=list)


_EVENT_DEFS: list[EventDef] = [
    # Weather
    EventDef("Blizzard", "blizzard", "weather", 8, (2, 4), (1, 3), "❄️"),
    EventDef("Drought", "drought", "weather", 10, (3, 6), (1, 3), "☀️", chains_to=["famine"]),
    EventDef("Flood", "flood", "weather", 7, (2, 3), (1, 2), "🌊"),
    EventDef("Perfect Growing Season", "perfect_harvest", "weather", 12, (1, 1), (1, 1), "🌿"),
    EventDef("Harsh Winter", "harsh_winter", "weather", 6, (3, 5), (1, 2), "🌨️"),
    # Geological
    EventDef("Earthquake", "earthquake", "geological", 4, (1, 2), (1, 3), "💥"),
    EventDef("Treasure Strike", "treasure_strike", "geological", 6, (1, 1), (1, 2), "💰"),
    # Social
    EventDef("Plague", "plague", "social", 5, (4, 8), (1, 3), "💀"),
    EventDef("Peasant Uprising", "uprising", "social", 4, (2, 3), (1, 2), "⚔️"),
    EventDef("Mercenary Band Arrives", "mercenary", "social", 8, (1, 1), (1, 1), "🗡️"),
    EventDef("Trade Fair", "trade_fair", "social", 10, (2, 2), (1, 1), "🛒"),
    # Magical
    EventDef("Ley Line Surge", "ley_surge", "magical", 5, (1, 1), (1, 1), "✨"),
    EventDef("Ancient Ruins Discovered", "ruins", "magical", 4, (1, 1), (1, 1), "🏛️"),
    EventDef("Wandering Dragon", "dragon", "magical", 3, (1, 5), (2, 4), "🐉"),
    EventDef("Curse of the Ancients", "curse", "magical", 4, (3, 3), (1, 2), "💀"),
    EventDef("Magical Storm", "magic_storm", "magical", 5, (2, 3), (1, 2), "⛈️"),
]

_EVENT_BY_TYPE = {e.event_type: e for e in _EVENT_DEFS}


# ---------------------------------------------------------------------------
# Chain event triggers (derived from EventDef.chains_to)
# ---------------------------------------------------------------------------

_CHAIN_PROBS: dict[str, int] = {
    "famine": 60,       # drought → famine (60% chance)
    "uprising": 40,     # famine / plague → uprising
    "desertion": 50,    # uprising → desertion
}


# ---------------------------------------------------------------------------
# Effect application
# ---------------------------------------------------------------------------

def _pick_random_sectors(
    sectors: list[EventSectorState],
    n: int,
    rng: random.Random,
    land_only: bool = True,
) -> list[EventSectorState]:
    candidates = [s for s in sectors if not land_only or s.is_passable]
    return rng.sample(candidates, min(n, len(candidates)))


def _sc(result: EventResult, s: EventSectorState, field: str, delta: int) -> None:
    result.sector_changes.append({"x": s.x, "y": s.y, "field": field, "delta": delta})


def _nc(result: EventResult, n: EventNationState, field: str, delta: int) -> None:
    result.nation_changes.append({"nation_id": n.id, "field": field, "delta": delta})


def _apply_event(
    event_type: str,
    severity: int,
    sectors: list[EventSectorState],
    nations: list[EventNationState],
    rng: random.Random,
    result: EventResult,
) -> None:
    """Compute sector/nation deltas for an event and append to result."""

    if event_type == "perfect_harvest":
        for s in sectors:
            if s.designation == 1:  # FARM
                _sc(result, s, "food_bonus", 50)
        result.messages.append("Perfect growing season! Farm production +50% this turn.")

    elif event_type == "drought":
        affected = _pick_random_sectors(sectors, 5 * severity, rng)
        for s in affected:
            if s.designation == 1:
                _sc(result, s, "efficiency", -15)
        result.messages.append(f"Drought! {len(affected)} farm sectors suffer reduced production.")

    elif event_type == "blizzard":
        affected = _pick_random_sectors(sectors, 8, rng)
        for s in affected:
            _sc(result, s, "efficiency", -10)
        result.messages.append(f"Blizzard! Movement slowed, {len(affected)} sectors affected.")

    elif event_type == "flood":
        affected = _pick_random_sectors(sectors, 4, rng)
        for s in affected:
            if s.designation in (1, 11):  # FARM, GRANARY
                _sc(result, s, "efficiency", -20)
        result.messages.append("Flooding disrupts farm sectors.")

    elif event_type == "harsh_winter":
        for nation in nations:
            _nc(result, nation, "attr_morale", -10)
        result.messages.append("Harsh winter grips the land. All nations: -10 morale.")

    elif event_type == "earthquake":
        affected = _pick_random_sectors(sectors, 3, rng)
        for s in affected:
            _sc(result, s, "efficiency", -(10 * severity))
        result.messages.append(f"Earthquake! {len(affected)} sectors damaged.")

    elif event_type == "treasure_strike":
        passable = [s for s in sectors if s.is_passable]
        target = rng.choice(passable) if passable else None
        if target:
            _sc(result, target, "minerals", 3)
            result.messages.append(f"Treasure strike at ({target.x},{target.y})! Minerals +3.")

    elif event_type == "plague":
        affected = _pick_random_sectors(sectors, 4, rng)
        for s in affected:
            _sc(result, s, "population", -(s.population // 4))
        result.messages.append(f"Plague! {len(affected)} sectors lose 25% population.")

    elif event_type == "mercenary":
        result.messages.append(
            "A mercenary band has been spotted! First army to reach them may hire at half cost."
        )

    elif event_type == "trade_fair":
        result.messages.append("Trade Fair! Caravans deliver double value this turn.")

    elif event_type == "ley_surge":
        for nation in nations:
            _nc(result, nation, "attr_spell_pts", 20)
        result.messages.append("Ley Line Surge! All nations gain +20 magic power.")

    elif event_type == "ruins":
        candidates = [s for s in sectors if s.is_passable]
        if candidates:
            target = rng.choice(candidates)
            weights = [60, 25, 12, 3]
            rarity = rng.choices(["common", "uncommon", "rare", "legendary"], weights=weights)[0]
            result.new_artifacts.append({"x": target.x, "y": target.y, "rarity": rarity})
            result.messages.append(
                f"Ancient ruins discovered at ({target.x},{target.y})! An artifact awaits."
            )

    elif event_type == "dragon":
        result.messages.append(
            "A wandering dragon terrorises the land! Find and defeat it for glory."
        )

    elif event_type == "curse":
        if nations:
            victim = rng.choice(nations)
            _nc(result, victim, "attr_morale", -20)
            result.messages.append("A curse descends upon a nation! Morale and production suffer.")

    elif event_type == "magic_storm":
        result.messages.append("Magical storm! Spellcasting unreliable this turn.")

    elif event_type == "famine":
        for nation in nations:
            _nc(result, nation, "attr_morale", -15)
        result.messages.append("Famine! All nations suffer -15 morale.")

    elif event_type == "uprising":
        affected = [s for s in sectors if s.designation not in (0, 4)][:3]
        for s in affected:
            _sc(result, s, "efficiency", -25)
        result.messages.append("Peasant uprisings! Sector efficiency falls.")

    elif event_type == "desertion":
        for nation in nations:
            _nc(result, nation, "attr_morale", -5)
        result.messages.append("Desertion wave! Morale -5 across all nations.")


# ---------------------------------------------------------------------------
# Main event processing function
# ---------------------------------------------------------------------------

def process_events(
    sectors: list[EventSectorState],
    nations: list[EventNationState],
    active_events: list[ActiveEvent],
    event_rate: float = 1.0,
    rng: random.Random | None = None,
) -> EventResult:
    """
    Called once per turn. Processes active events and potentially fires new ones.

    event_rate: multiplier on fire_chance (0.0 = no events, 2.0 = double rate)
    Returns an EventResult with all changes to apply.
    """
    if rng is None:
        rng = random.Random()

    result = EventResult()
    still_active: list[ActiveEvent] = []

    # Process ongoing events
    for ev in active_events:
        defn = _EVENT_BY_TYPE.get(ev.event_type)
        if defn:
            _apply_event(ev.event_type, ev.severity, sectors, nations, rng, result)

        ev.turns_remaining -= 1
        if ev.turns_remaining > 0:
            still_active.append(ev)
        else:
            result.messages.append(f"The {ev.event_type.replace('_', ' ')} has ended.")
            # Chain events
            if defn and defn.chains_to:
                for chain_type in defn.chains_to:
                    prob = _CHAIN_PROBS.get(chain_type, 30)
                    if rng.randint(1, 100) <= prob:
                        chain_def = _EVENT_BY_TYPE.get(chain_type)
                        if chain_def:
                            dur = rng.randint(*chain_def.duration)
                            sev = rng.randint(*chain_def.severity)
                            ev_new = ActiveEvent(
                                chain_type, dur, severity=sev, icon=chain_def.icon
                            )
                            still_active.append(ev_new)
                            result.messages.append("The drought has caused a famine!")

    # Try to fire new events
    for defn in _EVENT_DEFS:
        adjusted_chance = int(defn.fire_chance * event_rate)
        if rng.randint(1, 100) <= adjusted_chance:
            # Don't stack the same event type
            if not any(e.event_type == defn.event_type for e in still_active):
                dur = rng.randint(*defn.duration)
                sev = rng.randint(*defn.severity)
                ev = ActiveEvent(
                    event_type=defn.event_type,
                    turns_remaining=dur,
                    severity=sev,
                    icon=defn.icon,
                )
                still_active.append(ev)
                result.active_events.append(ev)
                _apply_event(defn.event_type, sev, sectors, nations, rng, result)
                result.messages.append(f"New event: {defn.name} {defn.icon} (lasts {dur} turns)")

    result.active_events = still_active
    return result
