"""Tests for the world events engine."""

import random

from app.engine.events import (
    ActiveEvent,
    EventNationState,
    EventSectorState,
    process_events,
)


def _sectors(n: int = 10):
    return [EventSectorState(x=i, y=0, designation=1, efficiency=70, population=5000)
            for i in range(n)]


def _nations(n: int = 2):
    return [EventNationState(id=f"n{i}", food=2000, attr_morale=70, attr_spell_pts=50,
                             victory_points=0, power_military=30)
            for i in range(n)]


def test_process_events_returns_result():
    result = process_events(_sectors(), _nations(), [], rng=random.Random(0))
    assert result is not None
    assert isinstance(result.messages, list)


def test_perfect_harvest_gives_farm_bonus():
    ev = ActiveEvent("perfect_harvest", turns_remaining=1, severity=1)
    result = process_events(_sectors(), _nations(), [ev], event_rate=0, rng=random.Random(42))
    farm_bonuses = [c for c in result.sector_changes if c.get("field") == "food_bonus"]
    assert len(farm_bonuses) > 0


def test_harsh_winter_reduces_morale():
    ev = ActiveEvent("harsh_winter", turns_remaining=1, severity=1)
    result = process_events(_sectors(), _nations(3), [ev], event_rate=0, rng=random.Random(42))
    morale_changes = [c for c in result.nation_changes if c["field"] == "attr_morale"]
    assert len(morale_changes) == 3  # all 3 nations affected
    assert all(c["delta"] < 0 for c in morale_changes)


def test_ley_surge_gives_spell_pts():
    ev = ActiveEvent("ley_surge", turns_remaining=1, severity=1)
    result = process_events(_sectors(), _nations(2), [ev], event_rate=0, rng=random.Random(42))
    spell_changes = [c for c in result.nation_changes if c["field"] == "attr_spell_pts"]
    assert len(spell_changes) == 2
    assert all(c["delta"] > 0 for c in spell_changes)


def test_ruins_creates_artifact():
    ev = ActiveEvent("ruins", turns_remaining=1, severity=1)
    result = process_events(_sectors(), _nations(), [ev], event_rate=0, rng=random.Random(42))
    assert len(result.new_artifacts) == 1
    assert "rarity" in result.new_artifacts[0]


def test_event_expires():
    """Event with 1 turn remaining expires after process_events."""
    ev = ActiveEvent("blizzard", turns_remaining=1, severity=1)
    result = process_events(_sectors(), _nations(), [ev], event_rate=0, rng=random.Random(42))
    remaining = [e for e in result.active_events if e.event_type == "blizzard"]
    assert len(remaining) == 0


def test_event_persists_multi_turn():
    """Multi-turn event stays active."""
    ev = ActiveEvent("plague", turns_remaining=3, severity=1)
    result = process_events(_sectors(), _nations(), [ev], event_rate=0, rng=random.Random(42))
    remaining = [e for e in result.active_events if e.event_type == "plague"]
    assert len(remaining) == 1
    assert remaining[0].turns_remaining == 2


def test_zero_event_rate_fires_nothing():
    """event_rate=0 should fire no new events."""
    result = process_events(_sectors(), _nations(), [], event_rate=0.0, rng=random.Random(42))
    assert len(result.active_events) == 0


def test_high_event_rate_fires_events():
    """event_rate=100 (extreme) should fire many events."""
    result = process_events(_sectors(30), _nations(4), [], event_rate=100.0, rng=random.Random(1))
    assert len(result.active_events) > 0
