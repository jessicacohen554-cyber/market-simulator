"""Canonical plant-class ↔ EIA-930 fuel taxonomy — the single source of truth.

Repo rule: no scattered hardcoded fuel/class lists. Every report and dashboard
grouping (which classes are coal, which are gas, which are fossil, their display
labels) and the EIA-923 coal-rank classification chain derive from the tables
here. Adding a model plant class — e.g. a new EIA-923-derived coal rank — is a
one-line edit to :data:`PLANT_CLASSES` (or the coal maps) and the whole
pipeline (dispatch reporting, the fuel-vs-EIA-930 table, capture metrics, the
offer-curve routing) picks it up.

Three axes are unified here:

* **Model plant class** (``PlantClass.key``) — the dispatch ``klass`` /
  ``Plant_Group`` string a generator carries (CC_REGULAR, COAL_BIT, nuclear …).
* **EIA-930 fuel bucket** (``PlantClass.fuel930``) — the reporting fuel each
  class rolls up to, so model totals compare against EIA-930's
  net-generation-by-energy-source series.
* **EIA-923 coal rank** (:data:`COAL_CODE_TO_SUPPLY`, :data:`COAL_SUPPLY_TO_CLASS`)
  — the Schedule-5 ``ENERGY_SOURCE`` code → supply class → model coal class
  chain used to assign per-plant coal classes and offer curves.
"""

from __future__ import annotations

from dataclasses import dataclass

# EIA-930 "net generation by energy source" reporting buckets. Model classes
# roll up to exactly one of these (PlantClass.fuel930).
EIA930_FUELS: tuple[str, ...] = (
    "coal", "gas", "nuclear", "hydro", "wind", "solar", "oil", "other",
    "storage",
)


@dataclass(frozen=True)
class PlantClass:
    """One model plant class and how it maps to reporting and display."""

    key: str        # dispatch klass / Plant_Group string
    fuel930: str    # EIA-930 bucket it rolls up to (must be in EIA930_FUELS)
    label: str      # dashboard / report display label
    fossil: bool    # shown in the fossil class tables and capture metrics


# Canonical class list. Tuple order is the canonical display / iteration order
# (coal ranks, then gas classes, then non-fossil). Add a class here and every
# consumer that derives from the helpers below updates automatically.
PLANT_CLASSES: tuple[PlantClass, ...] = (
    # Coal — generic, ERCOT supply classes, and EIA-923-derived ranks.
    PlantClass("COAL",          "coal",    "Coal",            True),
    PlantClass("COAL_LIGNITE",  "coal",    "Coal Lignite",    True),
    PlantClass("COAL_PRB",      "coal",    "Coal PRB",        True),
    PlantClass("COAL_BIT",      "coal",    "Coal Bituminous", True),
    PlantClass("COAL_WC",       "coal",    "Coal Waste",      True),
    # Gas — combined cycle / combustion turbine / steam, merchant and CHP.
    PlantClass("CC_REGULAR",    "gas",     "CC Regular",      True),
    PlantClass("CC_CHP",        "gas",     "CC CHP",          True),
    PlantClass("CT_PEAKER",     "gas",     "CT Peaker",       True),
    PlantClass("CT_CHP",        "gas",     "CT CHP",          True),
    PlantClass("ST_GAS",        "gas",     "Steam Gas",       True),
    PlantClass("ST_CHP",        "gas",     "Steam CHP",       True),
    # Non-fossil.
    PlantClass("nuclear",       "nuclear", "Nuclear",         False),
    PlantClass("hydro",         "hydro",   "Hydro",           False),
    PlantClass("wind",          "wind",    "Wind",            False),
    PlantClass("offshore_wind", "wind",    "Offshore Wind",   False),
    PlantClass("solar",         "solar",   "Solar",           False),
    PlantClass("oil",           "oil",     "Oil",             False),
    PlantClass("biomass",       "other",   "Biomass",         False),
    PlantClass("geothermal",    "other",   "Geothermal",      False),
    PlantClass("storage",       "storage", "Storage",         False),
    PlantClass("OTHER",         "other",   "Other",           False),
)

_BY_KEY: dict[str, PlantClass] = {c.key: c for c in PLANT_CLASSES}

# Convenience: {class key -> label} for the canonical classes.
LABELS: dict[str, str] = {c.key: c.label for c in PLANT_CLASSES}


def class_label(key: str) -> str:
    """Display label for a class — canonical name, else humanized fallback.

    Unknown keys (a class not yet in :data:`PLANT_CLASSES`) become ``Foo Bar``
    rather than being dropped, so a new classification still renders.
    """
    c = _BY_KEY.get(key)
    return c.label if c else str(key).replace("_", " ").title()


def fuel930_of(key: str) -> str:
    """EIA-930 bucket a class rolls up to (``other`` for unknown keys)."""
    c = _BY_KEY.get(key)
    return c.fuel930 if c else "other"


def is_fossil(key: str) -> bool:
    """Whether a class is a fossil class (shown in the fossil tables)."""
    c = _BY_KEY.get(key)
    return bool(c and c.fossil)


def fossil_classes() -> tuple[str, ...]:
    """Fossil class keys in canonical display order."""
    return tuple(c.key for c in PLANT_CLASSES if c.fossil)


def nonfossil_classes() -> frozenset[str]:
    """Non-fossil class keys (nuclear, wind, solar, oil, storage, …)."""
    return frozenset(c.key for c in PLANT_CLASSES if not c.fossil)


def classes_for_fuel930(fuel: str) -> tuple[str, ...]:
    """All model class keys that roll up to an EIA-930 fuel bucket."""
    return tuple(c.key for c in PLANT_CLASSES if c.fuel930 == fuel)


# --- EIA-923 coal-rank classification chain --------------------------------
# Schedule-5 fuel-receipt ENERGY_SOURCE code -> model supply class. Anthracite,
# refined and synthetic coal fold into the closest dispatch analogue.
# Sub-bituminous coal is Powder River Basin in practice, so SUB maps to the
# ``prb`` supply class (model class COAL_PRB) — one PRB name across all ISOs,
# rather than a separate COAL_SUB. ERCOT names PRB-by-rail and PJM/MISO
# sub-bituminous receipts now resolve to the same COAL_PRB class and offer curve.
COAL_CODE_TO_SUPPLY: dict[str, str] = {
    "BIT": "bituminous",
    "SUB": "prb",
    "LIG": "lignite",
    "WC": "waste",       # waste coal: culm, gob, mine refuse
    "RC": "bituminous",  # refined coal
    "ANT": "bituminous",
    "SC": "bituminous",
    "SGC": "bituminous",
}

# Supply class -> model coal class (the COAL_* offer-curve / dispatch key).
COAL_SUPPLY_TO_CLASS: dict[str, str] = {
    "lignite": "COAL_LIGNITE",
    "prb": "COAL_PRB",
    "subbituminous": "COAL_PRB",  # PRB == sub-bituminous; one name across ISOs
    "bituminous": "COAL_BIT",
    "waste": "COAL_WC",
}


def coal_code_to_class(code: str) -> str | None:
    """Map an EIA-923 coal ENERGY_SOURCE code straight to its model class."""
    return COAL_SUPPLY_TO_CLASS.get(COAL_CODE_TO_SUPPLY.get(str(code).upper()))
