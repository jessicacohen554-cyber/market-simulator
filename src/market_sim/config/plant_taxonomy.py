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
    "coal",
    "gas",
    "nuclear",
    "hydro",
    "wind",
    "solar",
    "oil",
    "other",
    "storage",
)


@dataclass(frozen=True)
class PlantClass:
    """One model plant class and how it maps to reporting and display."""

    key: str  # dispatch klass / Plant_Group string
    fuel930: str  # EIA-930 bucket it rolls up to (must be in EIA930_FUELS)
    label: str  # dashboard / report display label
    fossil: bool  # shown in the fossil class tables and capture metrics


# Canonical class list. Tuple order is the canonical display / iteration order
# (coal ranks, then gas classes, then non-fossil). Add a class here and every
# consumer that derives from the helpers below updates automatically.
PLANT_CLASSES: tuple[PlantClass, ...] = (
    # Coal — generic, ERCOT supply classes, and EIA-923-derived ranks.
    PlantClass("COAL", "coal", "Coal", True),
    PlantClass("COAL_LIGNITE", "coal", "Coal Lignite", True),
    PlantClass("COAL_PRB", "coal", "Coal PRB", True),
    PlantClass("COAL_BIT", "coal", "Coal Bituminous", True),
    PlantClass("COAL_WC", "coal", "Coal Waste", True),
    # Gas — combined cycle / combustion turbine / steam, merchant and CHP.
    PlantClass("CC_REGULAR", "gas", "CC Regular", True),
    PlantClass("CC_CHP", "gas", "CC CHP", True),
    PlantClass("CT_PEAKER", "gas", "CT Peaker", True),
    PlantClass("CT_CHP", "gas", "CT CHP", True),
    PlantClass("ST_GAS", "gas", "Steam Gas", True),
    PlantClass("ST_CHP", "gas", "Steam CHP", True),
    # Non-fossil.
    PlantClass("nuclear", "nuclear", "Nuclear", False),
    PlantClass("hydro", "hydro", "Hydro", False),
    PlantClass("wind", "wind", "Wind", False),
    PlantClass("offshore_wind", "wind", "Offshore Wind", False),
    PlantClass("solar", "solar", "Solar", False),
    PlantClass("oil", "oil", "Oil", False),
    PlantClass("biomass", "other", "Biomass", False),
    PlantClass("geothermal", "other", "Geothermal", False),
    PlantClass("storage", "storage", "Storage", False),
    PlantClass("OTHER", "other", "Other", False),
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
    "WC": "waste",  # waste coal: culm, gob, mine refuse
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


# --- Per-plant model-class assignment (single source of truth) -------------
# A natural-gas unit's model class is read off its prime mover: a combined-cycle
# block reports CA/CS/CT/CC (the steam and combustion turbines of the train), a
# simple-cycle peaker reports GT or IC (gas/internal-combustion turbine), and a
# gas boiler reports ST (steam turbine). A CHP-flagged plant takes the cogen
# variant of the same class. These are the EIA prime-mover codes; one table so
# the ERCOT bin override, the non-ERCOT EIA-860 fleet and the EIA-923 benchmark
# can never drift on how they bucket a plant.
NG_CC_PRIME_MOVERS: frozenset[str] = frozenset({"CA", "CS", "CT", "CC"})
NG_CT_PRIME_MOVERS: frozenset[str] = frozenset({"GT", "IC"})

# EIA prime-mover code for the STEAM part of a combined-cycle block — the
# heat-recovery steam generator and its turbine, driven by the exhaust of the
# block's combustion turbines (which report ``CT``). See
# :data:`CC_STEAM_PART_REPAIR_ISOS` and ``classify_plant``'s ``cc_steam_part``
# argument for why this code needs its own handling: EIA-860's
# ``Energy Source 1`` on a ``CA`` row names the block's SUPPLEMENTARY / duct
# fuel, not its primary energy input, so a duct-fired steam part reports an
# exotic fuel code (blast-furnace gas ``BFG``, other gas ``OG``, distillate
# ``DFO``) and falls to the residual ``OTHER`` bucket even though it is half of
# an ordinary gas-fired combined cycle.
CC_STEAM_PART_PRIME_MOVER: str = "CA"

# ISOs whose fleet build repairs the dropped ``CA`` combined-cycle steam parts
# (``ScenarioConfig.cc_steam_part_capacity``). Rule 25 ``[R-ISO-SCOPE]``: an
# ISO enters this set only after its OWN session verifies, on its OWN market's
# data, that the capacity is measurably absent from its fleet and that the
# plant's joined heat rate is already a BLOCK rate — a verdict in one ISO never
# fills another ISO's cell. MISO's verification is
# ``results/calibration/FINDING-miso126-cc-steam-part-capacity-2026-08-04.md``
# (55088 Dearborn ``ST1``, 250.0 MW). Named but NOT entered: CAISO 54912
# Martinez ``STG1`` 20.0 MW and NEISO 6081 Stony Brook ``CA1`` 96.0 MW, each
# handed to its own lane unstamped.
CC_STEAM_PART_REPAIR_ISOS: frozenset[str] = frozenset({"MISO"})

# EIA energy-source codes for the non-coal/non-gas thermal classes — the single
# source of truth shared by the model fleet builder (``data.fleet``) and the
# EIA-923 benchmark, so the model and benchmark bucket a plant identically.
# Oil = distillate (DFO), residual (RFO), jet (JF), kerosene (KER), waste oil
# (WO). Petroleum coke (PC) is deliberately excluded so it falls to the residual
# OTHER must-run bucket rather than the dispatchable oil-peaker fleet.
OIL_ENERGY_SOURCES: frozenset[str] = frozenset({"DFO", "RFO", "JF", "KER", "WO"})
# Biomass = wood/refuse solids, landfill gas and the other biogenic streams.
BIOMASS_ENERGY_SOURCES: frozenset[str] = frozenset(
    {"WDS", "AB", "MSW", "LFG", "BLQ", "OBG", "OBL", "OBS", "WDL", "SLW", "DG"}
)
# Hydro: fuel code WAT or a hydraulic-turbine prime mover (HY / HA). Pumped
# storage (PS) is left to OTHER — it is a storage resource, not a generator.
HYDRO_PRIME_MOVERS: frozenset[str] = frozenset({"HY", "HA"})


def classify_plant(
    fuel: object,
    prime_mover: object,
    chp_flag: bool,
    plant_id: int,
    coal_class_resolver=None,
    cc_steam_part: bool = False,
) -> str:
    """Return the model plant class for one generator / EIA-923 Page-1 row.

    The single canonical classifier: given a plant's energy-source (fuel) code,
    prime mover, CHP flag and plant code, return its model ``Plant_Group`` /
    dispatch ``klass``. Every assignment path — the ERCOT bin override, the
    non-ERCOT EIA-860 fleet, and the EIA-923 benchmark — calls this, so a plant
    is bucketed identically by construction and the three can't drift.

    * Coal is split into its supply rank (``COAL_LIGNITE`` / ``COAL_PRB`` /
      ``COAL_BIT`` / ``COAL_WC``) via ``coal_class_resolver(plant_id, fuel)``
      when given — the model's curated-plus-EIA-923 coal map — else straight
      from the fuel code (:func:`coal_code_to_class`), falling back to the bare
      ``COAL`` class.
    * Natural gas (``NG``) is split by prime mover and CHP flag into the six
      gas classes (CC / CT / ST, merchant vs CHP).
    * Wind, solar, nuclear, oil, biomass and hydro are their own classes;
      everything else (other/process gas, purchased steam, waste heat, petcoke,
      batteries, …) falls through to the residual ``OTHER`` bucket.

    Args:
        fuel: EIA energy-source code (``NG``, ``BIT``, ``WND`` …).
        prime_mover: EIA prime-mover code (``CA``, ``GT``, ``ST`` …).
        chp_flag: Whether the plant is a combined-heat-and-power cogen.
        plant_id: EIA plant code, used by the coal-rank resolver.
        coal_class_resolver: Optional ``(plant_id, fuel_code) -> class`` callable
            that returns a plant's coal supply class; when it returns a falsy
            value the fuel-code map is used.
        cc_steam_part: When True this row is the STEAM part of a gas-fired
            combined-cycle block (prime mover :data:`CC_STEAM_PART_PRIME_MOVER`,
            sharing an EIA-860 ``Unit Code`` with ``NG`` ``CT`` siblings it is
            not older than), so it is classed with the gas combined-cycle
            classes regardless of its own energy-source code. EIA-860's
            ``Energy Source 1`` on such a row is the block's supplementary /
            duct fuel — ``BFG``, ``OG``, ``DFO`` — not the primary energy input,
            which arrives as turbine exhaust; without this the row falls to the
            residual ``OTHER`` bucket and its capacity is dropped. The caller
            resolves the predicate (it needs the plant's whole generator roster,
            which this function does not see) and gates it on
            :data:`CC_STEAM_PART_REPAIR_ISOS`. Default False, so every existing
            call site is byte-identical.
    """
    fuel = str(fuel).strip().upper()
    pm = str(prime_mover).strip().upper()
    chp = bool(chp_flag)
    if cc_steam_part and pm == CC_STEAM_PART_PRIME_MOVER:
        # The block's primary fuel is gas, burned in its CT siblings; this row's
        # own energy-source code describes duct firing only. Class it as the
        # combined cycle it is half of. An ``NG``-coded CA row never reaches
        # here differently — it already falls through to the NG branch below
        # and lands on the same class — so this is a strict widening.
        return "CC_CHP" if chp else "CC_REGULAR"
    if fuel in COAL_CODE_TO_SUPPLY:
        if coal_class_resolver is not None:
            resolved = coal_class_resolver(int(plant_id), fuel)
            if resolved:
                return resolved
        return coal_code_to_class(fuel) or "COAL"
    if fuel == "NG":
        if pm in NG_CC_PRIME_MOVERS:
            return "CC_CHP" if chp else "CC_REGULAR"
        if pm in NG_CT_PRIME_MOVERS:
            return "CT_CHP" if chp else "CT_PEAKER"
        if pm == "ST":
            return "ST_CHP" if chp else "ST_GAS"
        return "OTHER"
    if fuel == "WND" or pm == "WT":
        return "wind"
    if fuel == "SUN" or pm in {"PV", "CP"}:
        return "solar"
    if fuel == "NUC":
        return "nuclear"
    if fuel in OIL_ENERGY_SOURCES:
        return "oil"
    if fuel in BIOMASS_ENERGY_SOURCES:
        return "biomass"
    if fuel == "WAT" or pm in HYDRO_PRIME_MOVERS:
        return "hydro"
    return "OTHER"
