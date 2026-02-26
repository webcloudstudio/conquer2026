"""
Economy engine — translates economyA.c / computeX.c logic to Python.

Reference: gpl-release/Src/economyA.c, gpl-release/Src/computeX.c

Phase 1: stub with type signatures.
Phase 2: full implementation cross-referenced against the C originals.
"""

from dataclasses import dataclass


@dataclass
class Resources:
    talons: int = 0
    jewels: int = 0
    metals: int = 0
    food: int = 0
    wood: int = 0

    def __add__(self, other: "Resources") -> "Resources":
        return Resources(
            talons=self.talons + other.talons,
            jewels=self.jewels + other.jewels,
            metals=self.metals + other.metals,
            food=self.food + other.food,
            wood=self.wood + other.wood,
        )

    def __mul__(self, factor: float) -> "Resources":
        return Resources(
            talons=int(self.talons * factor),
            jewels=int(self.jewels * factor),
            metals=int(self.metals * factor),
            food=int(self.food * factor),
            wood=int(self.wood * factor),
        )


def compute_sector_production(
    designation: int,
    efficiency: int,
    population: int,
    altitude: int,
    vegetation: int,
    tradegood: int,
) -> Resources:
    """
    Compute one turn's resource output for a single sector.

    Reference: economyA.c :: compute_sector_production()
    Phase 2 TODO: implement production tables matching the C original.
    """
    raise NotImplementedError("Phase 2")


def compute_army_upkeep(unit_type: int, strength: int, supply: int) -> Resources:
    """
    Compute food/talon cost to maintain an army unit for one turn.

    Reference: economyA.c :: army_support()
    """
    raise NotImplementedError("Phase 2")


def compute_caravan_value(
    cargo: Resources,
    source_x: int,
    source_y: int,
    dest_x: int,
    dest_y: int,
    efficiency: int,
    trader_class_bonus: float = 1.0,
) -> int:
    """
    Compute the talon value of a caravan delivery.

    Value scales with distance and cargo rarity.
    Trader class gets a bonus multiplier (default 1.0, Trader class = 2.0).

    Reference: caravanG.c :: caravan_deliver()
    """
    raise NotImplementedError("Phase 2")


def apply_tax_rate(population: int, tax_rate: int, morale: int) -> int:
    """
    Compute talon income from a civilian population.
    High tax + low morale increases revolt risk.

    Reference: economyA.c :: tax_income()
    """
    raise NotImplementedError("Phase 2")
