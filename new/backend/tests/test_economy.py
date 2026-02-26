"""
Unit tests for the economy engine.

These are written against the Phase 2 implementation expectations.
Phase 1: all marked xfail until engine is implemented.
Cross-reference expected values against gpl-release/Src/economyA.c.
"""

import pytest
from app.engine.economy import Resources, compute_sector_production, apply_tax_rate


def test_resources_add():
    a = Resources(talons=100, food=50)
    b = Resources(talons=50, metals=20)
    c = a + b
    assert c.talons == 150
    assert c.food == 50
    assert c.metals == 20


def test_resources_multiply():
    r = Resources(talons=100, food=200, metals=50)
    r2 = r * 0.5
    assert r2.talons == 50
    assert r2.food == 100
    assert r2.metals == 25


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_farm_sector_produces_food():
    """A farm sector at 100% efficiency should produce food proportional to population."""
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.FARM,
        efficiency=100,
        population=10000,
        altitude=5,
        vegetation=Vegetation.GRASSLAND,
        tradegood=0,
    )
    assert result.food > 0
    assert result.metals == 0


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_mine_sector_produces_metals():
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.MINE,
        efficiency=80,
        population=5000,
        altitude=8,
        vegetation=Vegetation.NONE,
        tradegood=0,
    )
    assert result.metals > 0


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_tax_rate_income():
    """Standard tax rate should produce positive talon income."""
    income = apply_tax_rate(population=10000, tax_rate=30, morale=70)
    assert income > 0


@pytest.mark.xfail(reason="Phase 2: engine not yet implemented", strict=True)
def test_zero_population_no_income():
    income = apply_tax_rate(population=0, tax_rate=30, morale=70)
    assert income == 0
