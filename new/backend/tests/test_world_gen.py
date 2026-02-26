"""
Unit tests for world generation.

Cross-reference: gpl-release/Src/hexmapX.c, gpl-release/Include/elevegX.h
"""

from app.engine.world_gen import (
    find_spawn_points,
    generate_world,
    hex_distance,
    hex_neighbours,
)

# ---------------------------------------------------------------------------
# Hex geometry
# ---------------------------------------------------------------------------

def test_hex_distance_same_point():
    assert hex_distance(5, 5, 5, 5) == 0


def test_hex_distance_adjacent():
    """Adjacent hexes should have distance 1."""
    assert hex_distance(0, 0, 1, 0) == 1
    assert hex_distance(0, 0, 0, 1) == 1


def test_hex_distance_symmetric():
    assert hex_distance(3, 7, 10, 2) == hex_distance(10, 2, 3, 7)


def test_hex_neighbours_count():
    """Interior hexes have 6 neighbours; edge hexes have fewer."""
    mapx, mapy = 20, 20
    interior = hex_neighbours(10, 10, mapx, mapy)
    assert len(interior) == 6

    corner = hex_neighbours(0, 0, mapx, mapy)
    assert len(corner) < 6


def test_hex_neighbours_in_bounds():
    mapx, mapy = 10, 10
    for nx, ny in hex_neighbours(5, 5, mapx, mapy):
        assert 0 <= nx < mapx
        assert 0 <= ny < mapy


# ---------------------------------------------------------------------------
# World generation
# ---------------------------------------------------------------------------

def test_generate_world_sector_count():
    """Generated world must have exactly mapx * mapy sectors."""
    world = generate_world(mapx=20, mapy=15, seed=42)
    assert len(world.sectors) == 20 * 15


def test_generate_world_dimensions():
    world = generate_world(mapx=30, mapy=20, seed=1)
    assert world.mapx == 30
    assert world.mapy == 20


def test_generate_world_has_water_and_land():
    """World must have both water (altitude=0) and land sectors."""
    world = generate_world(mapx=40, mapy=25, pwater=30, seed=7)
    altitudes = [s.altitude for s in world.sectors]
    assert 0 in altitudes            # water exists
    assert any(a > 0 for a in altitudes)  # land exists


def test_generate_world_pwater_controls_ocean():
    """Higher pwater should produce more ocean sectors."""
    world_wet = generate_world(mapx=30, mapy=20, pwater=60, seed=42)
    world_dry = generate_world(mapx=30, mapy=20, pwater=10, seed=42)

    ocean_wet = sum(1 for s in world_wet.sectors if s.altitude == 0)
    ocean_dry = sum(1 for s in world_dry.sectors if s.altitude == 0)
    assert ocean_wet > ocean_dry


def test_generate_world_reproducible():
    """Same seed must produce identical worlds."""
    w1 = generate_world(mapx=20, mapy=15, seed=99)
    w2 = generate_world(mapx=20, mapy=15, seed=99)
    for s1, s2 in zip(w1.sectors, w2.sectors):
        assert s1.altitude == s2.altitude
        assert s1.vegetation == s2.vegetation


def test_generate_world_spawn_points():
    """World should have at least some spawn points identified."""
    world = generate_world(mapx=40, mapy=30, seed=5)
    assert len(world.player_spawn_points) > 0
    assert len(world.npc_spawn_points) > 0


def test_generate_world_sectors_have_valid_fields():
    world = generate_world(mapx=15, mapy=10, seed=3)
    for s in world.sectors:
        assert 0 <= s.x < 15
        assert 0 <= s.y < 10
        assert s.altitude >= 0
        assert s.vegetation >= 0
        assert 0 <= s.efficiency <= 100


# ---------------------------------------------------------------------------
# Spawn points
# ---------------------------------------------------------------------------

def test_find_spawn_points_count():
    world = generate_world(mapx=40, mapy=30, seed=11)
    spawns = find_spawn_points(world, count=5, min_separation=4)
    assert len(spawns) <= 5  # may be fewer if map doesn't have enough land


def test_find_spawn_points_separation():
    """Returned spawn points must be separated by at least min_separation."""
    world = generate_world(mapx=50, mapy=35, seed=22)
    min_sep = 6
    spawns = find_spawn_points(world, count=8, min_separation=min_sep)
    for i, (x1, y1) in enumerate(spawns):
        for x2, y2 in spawns[i + 1:]:
            assert hex_distance(x1, y1, x2, y2) >= min_sep
