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

import numpy as np

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
    # Coal — the four supply ranks. There is NO generic ``COAL`` class (owner
    # instruction 2026-09-25, "we need to completely eliminate the class Coal
    # From the model altogether all coal should be sorted into its subclass"):
    # every coal unit carries its rank, resolved at load by
    # :func:`market_sim.data.coal.coal_subclass`.
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


# --- The coal subclass family (COAL-SUB, owner instruction 2026-09-25) ------
# The four coal model classes, in canonical display order. A coal generator's
# ``plant_group`` is ALWAYS one of these; the bare ``COAL`` class is deleted,
# not aliased (rule 26 [R-DELETE]) — see :func:`assert_not_bare_coal`.
COAL_CLASSES: tuple[str, ...] = ("COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC")

# The coal FUEL-FAMILY token of the committed data artifacts — NEVER a
# generator class. The frozen derive scripts (rule 23 [R-FROZEN-DERIVE]) wrote
# ``plant_group`` / ``class`` / ``plant_class`` = ``"COAL"`` into the CAMPD
# outage, thermal-tranche, bin-assignment, reliability-floor, ERCOT DAM
# availability and marginal-HR artifacts, and several solve-path mechanisms
# compute ONE quantity across all coal and distribute it (the reliability
# floor's cheapest-first limb, the ERCOT class-availability water-fill, the
# online-capacity envelopes). Re-deriving those artifacts to rename a token is
# not a data change, and splitting an across-coal aggregate into four
# per-rank aggregates changes the answer. So every such join / aggregate reads
# the fleet's subclass through :func:`artifact_class`, which folds the four
# ranks onto this token: the artifacts stay byte-identical and the fleet never
# carries it.
COAL_ARTIFACT_FAMILY: str = "COAL"


def is_coal_class(key: object) -> bool:
    """True iff ``key`` is one of the four coal model classes (:data:`COAL_CLASSES`)."""
    return str(key) in COAL_CLASSES


def artifact_class(group: object) -> str:
    """Return the committed-artifact class token for a model ``plant_group``.

    A coal subclass maps to :data:`COAL_ARTIFACT_FAMILY` (the fuel-family token
    the derived artifacts and the across-coal aggregates are keyed on); every
    other class is returned unchanged. The ONE seam through which a model
    class meets artifact vocabulary, so a join can never drift.
    """
    g = str(group)
    return COAL_ARTIFACT_FAMILY if g in COAL_CLASSES else g


def artifact_class_array(groups) -> np.ndarray:
    """Vectorized :func:`artifact_class` over an array of ``plant_group`` values."""
    arr = np.asarray(groups).astype(object)
    out = arr.copy()
    out[np.isin(arr, COAL_CLASSES)] = COAL_ARTIFACT_FAMILY
    return out


def with_coal_subclasses(table: dict, value) -> dict:
    """Return ``table`` with ``value`` under every coal subclass key.

    The carry-over used where a per-unit parameter table was keyed by the
    deleted ``COAL`` class: each subclass receives the identical value, so a
    unit that was already subclass-resolved reads byte-identically.
    """
    out = dict(table)
    for cls in COAL_CLASSES:
        out[cls] = value
    return out


class BareCoalClassError(ValueError):
    """A configuration or fleet row names the deleted bare ``COAL`` class."""


def assert_not_bare_coal(key: object, where: str) -> None:
    """Refuse the deleted bare ``COAL`` class with a clear error.

    Raises:
        BareCoalClassError: when ``key == "COAL"``.
    """
    if str(key) == COAL_ARTIFACT_FAMILY:
        raise BareCoalClassError(
            f"{where}: the bare 'COAL' class no longer exists (owner instruction "
            "2026-09-25: every coal unit carries its subclass). Name the "
            f"subclass(es) instead: {', '.join(COAL_CLASSES)}. A legacy keeper "
            "recipe is translated by plant_taxonomy.fold_legacy_coal_key "
            "(replay_keeper does this); a NEW config may not carry the key."
        )


def fold_legacy_coal_key(mapping: dict | None, covered=()) -> dict | None:
    """Translate a legacy class-keyed mapping carrying a bare ``"COAL"`` key.

    Before COAL-SUB the ``"COAL"`` entry of a class-keyed table (an
    ``offer_curve_by_group`` curve, an ``offer_curve_overrides`` patch) reached
    exactly the coal units whose subclass had NO entry of its own (the
    subclass entry won whenever present). That semantics is preserved: the
    ``"COAL"`` value is carried to each coal subclass that has no entry in
    ``mapping`` AND is not in ``covered`` (the subclasses the base table the
    mapping is merged onto already carries), and the ``"COAL"`` key is dropped.

    Args:
        mapping: The class-keyed mapping (returned unchanged when it has no
            ``"COAL"`` key; ``None`` passes through).
        covered: Coal subclasses already carried by the table ``mapping`` is
            merged onto.

    Returns:
        A new mapping with no ``"COAL"`` key.
    """
    if not mapping or COAL_ARTIFACT_FAMILY not in mapping:
        return mapping
    out = {k: v for k, v in mapping.items() if k != COAL_ARTIFACT_FAMILY}
    legacy = mapping[COAL_ARTIFACT_FAMILY]
    skip = set(covered)
    for cls in COAL_CLASSES:
        if cls not in out and cls not in skip:
            out[cls] = legacy
    return out


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
# handed to its own lane unstamped. NEISO's ``CA1`` is NOT a member of this
# set's population at all — it is CARRIED, not dropped, so nothing is there to
# restore; its object is :data:`CC_STEAM_PART_RECLASS_ISOS` below.
CC_STEAM_PART_REPAIR_ISOS: frozenset[str] = frozenset({"MISO"})

# ISOs whose fleet build RE-CLASSES the ``CA`` combined-cycle steam parts the
# fuel map resolves to a NON-gas fuel from the row's own (stale / duct)
# ``Energy Source 1`` (``ScenarioConfig.cc_steam_part_reclass``).
#
# This is a DIFFERENT object from :data:`CC_STEAM_PART_REPAIR_ISOS`, on a
# disjoint population and with the opposite sign on capacity. The repair set
# RESTORES a steam part the fuel map DROPS (``_map_fuel_type`` returns ``None``
# for ``BFG`` / ``OG``), adding capacity that is missing. This set re-classes a
# steam part the fuel map CARRIES under the wrong fuel — a ``CA`` row coded
# ``DFO`` resolves to ``oil`` and is dispatched as a standalone distillate unit,
# burning a fuel the machine does not have while the block's whole metered heat
# input already sits on its ``CT`` siblings. Total capacity is unchanged; what
# moves is the class, the fuel price, the VOM, the CO2 rate and the forced-
# outage rate.
#
# The two sets are kept separate deliberately: the repair's ``fuel_type is
# None`` gate is load-bearing (miso-125 §6 — MISO 1004 Edwardsport's ``CA``/
# ``SGC`` row matches the steam-part predicate but is a real 555 MW IGCC
# machine the model carries as ``COAL``, and a capacity repair must never
# re-bucket a represented machine). Re-classing is exactly the operation that
# gate forbids, so it gets its own flag and its own ISO registry rather than
# widening the repair's.
#
# Rule 25 ``[R-ISO-SCOPE]``: an ISO enters only after its OWN session verifies,
# on its OWN market's data, that the row is a genuine fuel-less steam part.
# NEISO's verification is
# ``results/calibration/FINDING-neiso83-stonybrook-ca1-2026-08-05.md``
# (6081 Stony Brook ``CA1``, 96.0 MW — NEISO's ENTIRE population is that one
# row). MISO is deliberately absent: its only member would be Edwardsport.
CC_STEAM_PART_RECLASS_ISOS: frozenset[str] = frozenset({"NEISO"})

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
      from the fuel code (:func:`coal_code_to_class`). Every code in
      :data:`COAL_CODE_TO_SUPPLY` maps to a subclass, so there is no generic
      coal class (COAL-SUB, 2026-09-25).
    * Natural gas (``NG``) is split by prime mover and CHP flag into the six
      gas classes (CC / CT / ST, merchant vs CHP).
    * Wind, solar, nuclear, oil, biomass and hydro are their own classes;
      everything else (other/process gas, purchased steam, waste heat, petcoke,
      batteries, **pumped storage**, …) falls through to the residual ``OTHER``
      bucket. Pumped storage (prime mover ``PS``) is tested BEFORE hydro
      because every PS row also carries fuel code ``WAT``.

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
        # Every coal code maps to a subclass (COAL_CODE_TO_SUPPLY values are
        # all COAL_SUPPLY_TO_CLASS keys) — there is no generic coal class.
        return COAL_SUPPLY_TO_CLASS[COAL_CODE_TO_SUPPLY[fuel]]
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
    if pm == "PS":
        # Pumped storage is a STORAGE resource, not a generator — exactly what
        # the comment on :data:`HYDRO_PRIME_MOVERS` above asserts, and what the
        # code below did NOT do: every PS row also carries fuel code ``WAT``,
        # so the ``fuel == "WAT"`` short-circuit routed all of them to
        # ``hydro``. The model dispatches PS as an LP storage unit
        # (``model.storage`` / ``load_eia860_pumped_storage``) and its EIA-923
        # row is a NET, round-trip-loss quantity — negative in almost every
        # ISO-year — so folding it into ``hydro`` mixed a storage net into the
        # conventional-inflow class the LP's hydro units are scored against
        # (``data.hydro._load_hydro_generation`` filters prime mover ``HY``
        # alone, never through this classifier). Placed HERE rather than at the
        # top of the function so it intercepts only what would otherwise become
        # ``hydro``: measured over 2019-2026, all 366 moving EIA-923 rows are
        # ``WAT``/``PS`` and no row of any other kind moves, so the narrow
        # placement is inert on the real population and keeps the change
        # minimal. Zero dominant-class flips reach a gas class, so the ERCOT bin
        # override (``_override_bin_class_from_eia923``) and
        # ``mixed_fossil_plants`` are byte-identical, and the injected ``OTHER``
        # must-run is unchanged to 0.000000 MWh in all 42 scored ISO-years
        # because ``_pumped_storage_plant_ids`` holds these rows back out again
        # — the guard this repair makes live for the first time.
        # Rule 26 ``[R-DELETE]`` (fix it, do not flag it both ways);
        # gov-hydro-seam-1, docs/FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md §5.
        return "OTHER"
    if fuel == "WAT" or pm in HYDRO_PRIME_MOVERS:
        return "hydro"
    return "OTHER"
