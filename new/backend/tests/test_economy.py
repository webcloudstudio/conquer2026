"""
Unit tests for the economy engine.

Cross-reference expected values against gpl-release/Src/economyA.c,
gpl-release/Src/sectorX.c, gpl-release/Src/dataX.c.
"""

from app.engine.economy import (
    Resources,
    adjust_production,
    apply_tax_rate,
    compute_army_upkeep,
    compute_caravan_value,
    compute_sector_consumption,
    compute_sector_production,
)

# ---------------------------------------------------------------------------
# Resources arithmetic
# ---------------------------------------------------------------------------

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


def test_resources_subtract():
    a = Resources(talons=100, food=50)
    b = Resources(talons=30, food=20)
    c = a - b
    assert c.talons == 70
    assert c.food == 30


# ---------------------------------------------------------------------------
# Sector production
# ---------------------------------------------------------------------------

def test_farm_sector_produces_food():
    """Farm sector with grassland should produce food."""
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.FARM,
        efficiency=100,
        population=10000,
        altitude=4,       # flat/hill (maps to ELE_CLEAR)
        vegetation=Vegetation.GRASSLAND,
        tradegood=0,
        turn=0,           # spring
    )
    assert result.food > 0
    assert result.metals == 0


def test_mine_sector_produces_metals():
    """Mine sector in mountain terrain should produce metals."""
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.MINE,
        efficiency=80,
        population=5000,
        altitude=8,       # mountain
        vegetation=Vegetation.NONE,
        tradegood=0,
        minerals=5,       # mineral deposits
        turn=1,           # summer (peak mine season)
    )
    assert result.metals > 0


def test_winter_farm_zero_production():
    """Farm has zero production in winter (season index 3)."""
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.FARM,
        efficiency=100,
        population=10000,
        altitude=3,
        vegetation=Vegetation.GRASSLAND,
        tradegood=0,
        turn=3,  # winter
    )
    assert result.food == 0
    assert result.wood == 0
    assert result.metals == 0
    assert result.talons == 0


def test_zero_population_no_output():
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.FARM,
        efficiency=100,
        population=0,
        altitude=3,
        vegetation=Vegetation.GRASSLAND,
        tradegood=0,
    )
    assert result.food == 0
    assert result.talons == 0


def test_forest_sector_produces_wood():
    """Forest designation with forest vegetation should produce wood."""
    from app.models.sector import Designation, Vegetation
    result = compute_sector_production(
        designation=Designation.FOREST,
        efficiency=100,
        population=5000,
        altitude=3,
        vegetation=Vegetation.FOREST,
        tradegood=0,
        turn=1,  # summer
    )
    assert result.wood > 0


def test_tradegood_adds_talons():
    """Sectors with trade goods earn extra talons."""
    from app.models.sector import Designation, Vegetation
    result_no_tg = compute_sector_production(
        designation=Designation.TRADE_POST,
        efficiency=100,
        population=5000,
        altitude=3,
        vegetation=Vegetation.GRASSLAND,
        tradegood=0,
        turn=0,
    )
    result_with_tg = compute_sector_production(
        designation=Designation.TRADE_POST,
        efficiency=100,
        population=5000,
        altitude=3,
        vegetation=Vegetation.GRASSLAND,
        tradegood=5,
        turn=0,
    )
    assert result_with_tg.talons >= result_no_tg.talons


# ---------------------------------------------------------------------------
# Tax income
# ---------------------------------------------------------------------------

def test_tax_rate_income():
    """Standard tax rate should produce positive talon income."""
    income = apply_tax_rate(population=10000, tax_rate=30, morale=70)
    assert income > 0


def test_zero_population_no_income():
    income = apply_tax_rate(population=0, tax_rate=30, morale=70)
    assert income == 0


def test_zero_tax_rate_no_income():
    income = apply_tax_rate(population=10000, tax_rate=0, morale=70)
    assert income == 0


def test_low_morale_reduces_income():
    """Low morale reduces tax income below nominal."""
    high_morale = apply_tax_rate(population=10000, tax_rate=30, morale=100)
    low_morale = apply_tax_rate(population=10000, tax_rate=30, morale=10)
    assert low_morale < high_morale


# ---------------------------------------------------------------------------
# Sector consumption
# ---------------------------------------------------------------------------

def test_sector_consumption_positive():
    from app.models.sector import Designation
    consumed = compute_sector_consumption(
        designation=Designation.CITY,
        population=10000,
        eatrate=1,   # 1 food per 1000 people → 10 food for 10000 pop
    )
    assert consumed.food >= 0   # may be small; support costs may dominate


def test_zero_population_no_consumption():
    from app.models.sector import Designation
    consumed = compute_sector_consumption(
        designation=Designation.CITY,
        population=0,
    )
    assert consumed.food == 0
    assert consumed.talons == 0


# ---------------------------------------------------------------------------
# Magic production adjustments
# ---------------------------------------------------------------------------

def test_farming_magic_boosts_food():
    """MC_FARMING magic power should increase food by 20%."""
    base = Resources(food=1000, metals=500)
    _MC_FARMING = 0x01
    adjusted = adjust_production(base, taxrate=100, civ_magic=_MC_FARMING)
    assert adjusted.food == 1200
    assert adjusted.metals == 500  # unaffected


def test_druidism_boosts_wood():
    """MW_DRUIDISM magic should increase wood by 20%."""
    base = Resources(wood=500)
    _MW_DRUIDISM = 0x08
    adjusted = adjust_production(base, taxrate=100, wiz_magic=_MW_DRUIDISM)
    assert adjusted.wood == 600


# ---------------------------------------------------------------------------
# Army upkeep
# ---------------------------------------------------------------------------

def test_army_upkeep_normal():
    """Normal army requires food proportional to strength."""
    cost = compute_army_upkeep(unit_type=0, strength=1000, supply=1)
    assert cost.food > 0
    assert cost.jewels == 0


def test_monster_upkeep_uses_jewels():
    """Monster units consume jewels."""
    cost = compute_army_upkeep(unit_type=2, strength=10, supply=1)
    assert cost.jewels > 0


def test_out_of_supply_doubles_cost():
    """Out-of-supply units (supply=0) cost double."""
    in_supply = compute_army_upkeep(unit_type=0, strength=1000, supply=1)
    out_supply = compute_army_upkeep(unit_type=0, strength=1000, supply=0)
    assert out_supply.food > in_supply.food


# ---------------------------------------------------------------------------
# Caravan value
# ---------------------------------------------------------------------------

def test_caravan_value_scales_with_distance():
    cargo = Resources(jewels=100)
    close = compute_caravan_value(cargo, 0, 0, 2, 0, efficiency=100)
    far = compute_caravan_value(cargo, 0, 0, 15, 0, efficiency=100)
    assert far > close


def test_caravan_zero_distance_returns_zero():
    cargo = Resources(jewels=100)
    val = compute_caravan_value(cargo, 5, 5, 5, 5, efficiency=100)
    assert val == 0


def test_trader_class_bonus_doubles_value():
    cargo = Resources(food=500)
    normal = compute_caravan_value(cargo, 0, 0, 10, 0, efficiency=100, trader_class_bonus=1.0)
    trader = compute_caravan_value(cargo, 0, 0, 10, 0, efficiency=100, trader_class_bonus=2.0)
    assert trader == normal * 2
