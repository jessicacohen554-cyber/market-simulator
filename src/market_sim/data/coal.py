"""Coal supply classification, take-or-pay shares, and coal-CHP overrides.

Extracted from :mod:`market_sim.data.fleet` — coal-specific data functions
that classify coal plants by supply chain (PRB / lignite / bituminous / waste),
derive take-or-pay contract shares from EIA-923, and identify coal-CHP cogens
for behind-the-meter routing.
"""

from __future__ import annotations

import logging
from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.paths import EIA_860_DIR, PROCESSED_DIR, REFERENCE_DIR
from market_sim.config.plant_taxonomy import (
    COAL_ARTIFACT_FAMILY,
    COAL_CODE_TO_SUPPLY,
    COAL_SUPPLY_TO_CLASS,
    classify_plant,
    coal_code_to_class,
    is_coal_class,
)
from market_sim.utils.hour_calendar import DAYS_IN_MONTH_NOLEAP

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Coal plant supply classification
# ---------------------------------------------------------------------------

# ERCOT coal fuel-supply type by EIA plant code. Mine-mouth lignite plants
# ("lignite") bid into SCED at the marginal extraction cost — fixed mine
# costs are sunk on a dispatch-hour basis. PRB-by-rail plants ("prb") bid
# at the delivered contract price (mine-gate plus rail freight). The two
# differ by ~$13/MWh in fuel cost, enough to swing merit order against gas
# CC when gas is cheap. Drives fuel.apply_coal_supply_pricing.
COAL_PLANT_SUPPLY: dict[int, str] = {
    6180: "lignite",  # Oak Grove — Kosse mine
    298: "prb",  # Limestone — now PRB by rail (switched off local lignite)
    6146: "prb",  # Martin Lake — now PRB by rail (was East Texas lignite)
    6183: "lignite",  # San Miguel — adjacent lignite mine
    7030: "lignite",  # Major Oak Power
    6178: "prb",  # Coleto Creek — PRB by rail
    6179: "prb",  # Fayette / Sam Seymour — PRB by rail
    7097: "prb",  # J K Spruce — PRB by rail
    56611: "prb",  # Sandy Creek — PRB by rail (EIA-923 plant id 56611)
    3470: "prb",  # W A Parish (coal units 5-8, subbituminous) — PRB by rail
}


@lru_cache(maxsize=1)
def _derived_coal_supply() -> dict[int, str]:
    """Return ``{plant_code: supply_class}`` from derived per-ISO CSVs.

    Loads every ``data/raw/_processed-legacy/coal_supply_<ISO>.csv`` written by
    ``scripts/data/derive_coal_supply.py`` (EIA-923 fuel-receipt coal ranks:
    ``bituminous`` / ``subbituminous`` / ``waste`` / ``lignite``). EIA plant
    codes are national so the per-ISO files never collide. This generalises the
    ERCOT-only :data:`COAL_PLANT_SUPPLY` to any ISO whose coal ranks have been
    derived — see :func:`coal_supply_class`.
    """
    out: dict[int, str] = {}
    for path in sorted(PROCESSED_DIR.glob("coal_supply_*.csv")):
        df = pd.read_csv(path)
        for code, cls in zip(df["plant_code"], df["supply_class"]):
            out[int(code)] = str(cls)
    return out


@lru_cache(maxsize=16)
def coal_supply_by_iso(iso: str) -> dict[int, str]:
    """Return ``{plant_code: supply_class}`` for ONE ISO's derived coal ranks.

    Reads that ISO's own ``data/raw/_processed-legacy/coal_supply_<ISO>.csv``
    alone, where :func:`_derived_coal_supply` unions every ISO's file into one
    national map. The union is right for *resolving a plant* — EIA plant codes
    are national, so the files never collide — but wrong for *pooling a
    population*, which is what the measured PRB delivered-cost proxy does
    (:func:`market_sim.data.fuel.coal._prb_monthly_actuals`): a proxy pooled
    across ISOs prices one market's plants on another market's receipts, which
    rule 25 ``[R-ISO-SCOPE]`` forbids.

    Returns an empty dict when the ISO has no derived file (ERCOT, whose ranks
    are the curated :data:`COAL_PLANT_SUPPLY`, and any ISO not yet derived), so
    a caller falls back to whatever it did before rather than to an empty
    population.
    """
    path = PROCESSED_DIR / f"coal_supply_{str(iso).upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    return {int(c): str(s) for c, s in zip(df["plant_code"], df["supply_class"])}


@lru_cache(maxsize=1)
def _eia860_retiree_coal_supply() -> dict[int, str]:
    """Return ``{plant_code: supply_class}`` for mid-backcast coal retirees.

    The narrow tertiary coal-rank fallback (after the curated and EIA-923-receipt
    maps): a retiring plant's coal rank read from its EIA-860 ``energy_source``
    code (``BIT`` → bituminous, ``SUB`` → PRB, ``LIG`` → lignite, ``WC`` →
    waste), via :data:`plant_taxonomy.COAL_CODE_TO_SUPPLY`. This is the same
    fuel-code fallback the EIA-923 calibration benchmark already applies
    (``classify_plant``'s ``coal_code_to_class``), so the model resolves these
    plants to the SAME class the benchmark does instead of leaving them in the
    unranked ``COAL`` bucket.

    Scope is deliberately limited to the **retired-within-window** EIA-860
    vintage (:data:`EIA_860_RETIRED_WINDOW_PARQUET_NAME`) — the structural gap
    the receipt-based :func:`_derived_coal_supply` map cannot cover, because a
    plant that retired mid-backcast (e.g. W H Sammis, Homer City, AES Warrior
    Run — all bituminous) has no recent burned-fuel receipts to derive a rank
    from. Operable coal is intentionally NOT read here: an unresolved operable
    plant means its ISO's receipt map was never derived (e.g. MISO), a
    separate, deliberate piece of work — not something a retiree fallback should
    silently reprice. The model rank sets the dispatch coal-supply passthrough
    and the reporting class, so an unranked retiree otherwise bids generic
    full-cost fuel AND shows up as a spurious generic ``COAL`` row the EIA-923
    benchmark never has.
    """
    from market_sim.data.fleet import EIA_860_RETIRED_WINDOW_PARQUET_NAME

    path = EIA_860_DIR / EIA_860_RETIRED_WINDOW_PARQUET_NAME
    if not path.exists():
        return {}
    df = pd.read_parquet(path, columns=["plant_id", "energy_source"])
    out: dict[int, str] = {}
    for code, src in zip(df["plant_id"], df["energy_source"]):
        supply = COAL_CODE_TO_SUPPLY.get(str(src).strip().upper())
        if supply:
            out.setdefault(int(code), supply)  # first coal energy_source wins
    return out


# Flag-gated registry of the partial-plant exit carry's injected coal units
# (miso-190, ScenarioConfig.partial_plant_exit_carry,
# PREREG-miso190-partial-plant-exit-carry-2026-08-30). Populated ONLY by
# data/fleet/eia860.py::_register_partial_exit_coal_supply when that gated
# channel injects units, from each unit's own committed EIA-860
# ``Energy Source 1`` code through the canonical COAL_CODE_TO_SUPPLY — the
# identical fallback the whole-plant retiree parquet bakes in at build time
# and the EIA-923 benchmark applies at class time. Consulted LAST in
# coal_supply_class so it can never override an existing resolution, and
# empty (every path byte-identical) while the flag is off. Deliberately NOT
# an ambient read of the retired-and-canceled sheet: an ungated fallback
# would change classification (and so offers) for any unresolved fleet plant
# with an old retired coal row — measured EMPTY at the 2026-08-30 vintage
# (`_miso190_partial_exit_phase0.json`), but gated on principle (rule 25).
_PARTIAL_EXIT_COAL_SUPPLY: dict[int, str] = {}


def register_partial_exit_coal_supply(mapping: dict[int, str]) -> None:
    """Register injected partial-plant exit units' coal supply classes.

    Called by the gated partial-plant exit carry
    (``data/fleet/eia860.py::load_retired_within_window`` with
    ``partial_plant_exit_carry=True``) so an injected coal unit whose plant
    no other source resolves (A B Brown 6137 → bituminous, Dan E Karn 1702
    → prb) reports in its bench-matched ``COAL_*`` class instead of a bare
    ``COAL`` row the EIA-923 benchmark never has. Lowest-priority source —
    see :func:`coal_supply_class`.
    """
    _PARTIAL_EXIT_COAL_SUPPLY.update({int(k): str(v) for k, v in mapping.items()})


# COAL-SUB (owner instruction 2026-09-25, verbatim: "we need to completely
# eliminate the class Coal From the model altogether all coal should be sorted
# into its subclass"). The FINAL fallback of the coal-rank chain: the EIA-860
# ``Energy Source 1`` code of the coal unit itself, read off the row the fleet
# loader is building (so it is the unit's OWN vintage — a coal-to-gas
# conversion carries its coal code only in the vintages in which it burned
# coal), mapped through the canonical COAL_CODE_TO_SUPPLY — the identical map
# the EIA-923 benchmark classifies by, so the fleet and the benchmark bucket a
# plant the same way by construction. Populated ONLY by
# ``data/fleet/eia860.py::_rows_to_generators`` through
# :func:`register_unit_coal_supply`, and consulted LAST in
# :func:`coal_supply_class`, so it can never override any existing resolution:
# the only plants it reaches are the ones that previously fell into the deleted
# generic ``COAL`` bucket. Plant-grained (first registered code wins) because
# every per-plant artifact join and the plant's offer curve are plant-grained —
# one plant, one subclass.
_UNIT_ENERGY_SOURCE_COAL_SUPPLY: dict[int, str] = {}


def register_unit_coal_supply(plant_code: int, energy_source: object) -> str:
    """Register a coal unit's EIA-860 energy-source rank as its plant's last-resort supply.

    Args:
        plant_code: EIA plant code of the unit.
        energy_source: The unit's EIA-860 ``Energy Source 1`` code.

    Returns:
        The supply class registered for the plant (the pre-existing one when
        the plant already carries a registration), or ``""`` when the code is
        not a coal code.
    """
    supply = COAL_CODE_TO_SUPPLY.get(str(energy_source or "").strip().upper(), "")
    if not supply:
        return _UNIT_ENERGY_SOURCE_COAL_SUPPLY.get(int(plant_code), "")
    return _UNIT_ENERGY_SOURCE_COAL_SUPPLY.setdefault(int(plant_code), supply)


def coal_subclass(plant_code: int, energy_source: object = "") -> str:
    """Return the model coal class (``COAL_LIGNITE`` / ``COAL_PRB`` / ``COAL_BIT`` / ``COAL_WC``).

    The ONE resolver every coal generator's ``plant_group`` comes from: the
    :func:`coal_supply_class` chain, whose last link is the unit's own EIA-860
    energy-source code (registered here first when ``energy_source`` is given).
    There is no generic coal class, so a unit none of the links reaches is an
    error, never a guess.

    Raises:
        ValueError: when no link resolves the plant.
    """
    if not int(plant_code):
        # No plant identity to resolve at plant grain (and nothing to register
        # without colliding every code-less row onto plant 0): the unit's own
        # energy-source code is the only evidence.
        cls = coal_code_to_class(str(energy_source or "")) or ""
    else:
        if energy_source:
            register_unit_coal_supply(plant_code, energy_source)
        cls = COAL_SUPPLY_TO_CLASS.get(coal_supply_class(int(plant_code)), "")
    if not cls:
        raise ValueError(
            f"coal plant {int(plant_code)} resolves to NO coal subclass (curated "
            "map, EIA-923 receipts, EIA-860 retiree rank, partial-exit registry "
            f"and its own EIA-860 energy_source {energy_source!r} all empty); "
            "COAL-SUB forbids inventing one — add its rank to the curated map "
            "or derive its receipts"
        )
    return cls


def coal_supply_class(plant_code: int) -> str:
    """Return a plant's coal supply class, or ``""`` if unclassified.

    Resolution order, most authoritative first:

    1. The hand-curated ERCOT :data:`COAL_PLANT_SUPPLY` (encodes contract
       knowledge EIA-923 ranks miss, e.g. Limestone burning PRB despite its
       lignite history).
    2. The EIA-923 fuel-receipt-derived per-ISO map (:func:`_derived_coal_supply`).
    3. The EIA-860 ``energy_source`` rank of a mid-backcast retiree
       (:func:`_eia860_retiree_coal_supply`) — the fuel-code fallback the
       EIA-923 benchmark already applies, covering coal plants that retired
       with no recent receipts so they are ranked rather than left in the
       generic ``COAL`` bucket.
    4. The flag-gated partial-plant exit registry
       (:data:`_PARTIAL_EXIT_COAL_SUPPLY`) — the same energy-source-code
       fallback for units the gated miso-190 channel injects; empty while
       ``partial_plant_exit_carry`` is off.
    5. The coal unit's OWN EIA-860 energy-source code
       (:data:`_UNIT_ENERGY_SOURCE_COAL_SUPPLY`, COAL-SUB) — registered by the
       fleet loader, so every coal plant in a loaded fleet resolves; ``""``
       only for a plant no fleet row has registered.
    """
    base = COAL_PLANT_SUPPLY.get(int(plant_code))
    if base:
        return base
    derived = _derived_coal_supply().get(int(plant_code))
    if derived:
        return derived
    retiree = _eia860_retiree_coal_supply().get(int(plant_code))
    if retiree:
        return retiree
    partial = _PARTIAL_EXIT_COAL_SUPPLY.get(int(plant_code))
    if partial:
        return partial
    return _UNIT_ENERGY_SOURCE_COAL_SUPPLY.get(int(plant_code), "")


# ---------------------------------------------------------------------------
# Coal take-or-pay contract shares
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _derived_coal_takeorpay() -> dict[int, float]:
    """Return ``{plant_code: contract_share}`` from derived per-ISO CSVs.

    Loads every ``data/raw/_processed-legacy/coal_takeorpay_<ISO>.csv`` written
    by ``scripts/data/derive_coal_takeorpay.py`` (EIA-923 Schedule-5 Purchase Type:
    the contracted / take-or-pay share of each coal plant's delivered tonnage).
    EIA plant codes are national so the per-ISO files never collide.
    """
    out: dict[int, float] = {}
    for path in sorted(PROCESSED_DIR.glob("coal_takeorpay_*.csv")):
        df = pd.read_csv(path)
        for code, share in zip(df["plant_code"], df["contract_share"]):
            out[int(code)] = float(share)
    return out


def coal_takeorpay_share(plant_code: int) -> float | None:
    """Return a coal plant's measured take-or-pay (contract) share, or ``None``.

    The contracted (sunk, must-burn) fraction of delivered tonnage from
    EIA-923 Schedule-5 Purchase Type (:func:`_derived_coal_takeorpay`). ``None``
    when the plant filed no classifiable coal Purchase Type — the caller then
    keeps the model's default 100%-sunk must-run treatment. Consumed by
    :func:`campd_tranche_fuel_frac` when ``ScenarioConfig.coal_takeorpay_from_data``
    is set: the coal must-run tranche's sunk fraction becomes this share instead
    of the hardcoded 1.0, so the spot remainder ``1 - share`` bids full fuel.
    """
    return _derived_coal_takeorpay().get(int(plant_code))


# ---------------------------------------------------------------------------
# Coal class resolver
# ---------------------------------------------------------------------------


def _coal_class_for(plant_code: int, fuel_code: str = "") -> str:
    """Return the model coal class (``COAL_LIGNITE`` / ``COAL_PRB`` /
    ``COAL_BIT`` / ``COAL_WC``) for a coal plant.

    The coal-rank resolver :func:`classify_plant` uses: the authoritative model
    supply map (:func:`coal_supply_class`, curated ERCOT lignite/PRB plus the
    EIA-923-derived per-ISO ranks), falling back to the EIA-923 receipt fuel
    code. Mirrors the calibration benchmark's coal resolver so the model and
    benchmark split coal identically. Returns ``""`` only for a non-coal
    ``fuel_code`` on an unresolved plant (the caller's fuel-code map then
    decides); there is no generic ``COAL`` class (COAL-SUB, 2026-09-25).
    """
    return (
        COAL_SUPPLY_TO_CLASS.get(coal_supply_class(int(plant_code)))
        or coal_code_to_class(fuel_code)
        or ""
    )


# ---------------------------------------------------------------------------
# Coal CHP overrides
# ---------------------------------------------------------------------------

# EIA-860 "Sector" numbers that designate a combined-heat-and-power host: IPP
# CHP (3), Commercial CHP (5), Industrial CHP (7). A coal plant in one of these
# sectors burns coal to follow a host STEAM contract, not the LMP, so it is
# routed through the same behind-the-meter / steam-following must-run holdout as
# the gas cogens rather than dispatched as an economic COAL_BIT/WC tranche. The
# non-CHP coal sectors -- Electric Utility (1) and IPP Non-CHP (2) -- stay
# economic grid generators (Seward, Virginia City, the merchant culm fleet, and
# the Spurlock-class utility coal that EIA-923 also flags chp=Y). The class each
# maps to sizes the host pull-out via :data:`CHP_BTM_PCT_BY_SECTOR`.
_EIA860_CHP_SECTORS: dict[int, str] = {3: "merchant", 5: "commercial", 7: "industrial"}

_COAL_CHP_FLOOR_FACTOR: float = 0.85
_COAL_CHP_FLOOR_CAP_PCT: float = 75.0

# Non-leap month lengths — the shared calendar constant, aliased locally.
_DAYS_IN_MONTH_NONLEAP = DAYS_IN_MONTH_NOLEAP


@lru_cache(maxsize=8)
def coal_chp_overrides(iso: str, year: int) -> dict[int, tuple[float, str]]:
    """Return ``{plant_code: (steam_floor_min_avg_mw, sector_class)}`` for an
    ISO's coal cogens for ``year``.

    A coal cogen is a plant whose EIA-923 combustion net generation is
    predominantly coal (>= :data:`_COAL_CHP_MIN_SHARE`) and whose EIA-860
    "Sector" is a CHP host (:data:`_EIA860_CHP_SECTORS`). ``steam_floor_min_avg_mw``
    is the minimum monthly coal-class average MW over the pooled EIA-923 window
    (the measured floor the host always holds, the same EIA-923-CF measure
    derive_thermal_tranches uses for CEMS-invisible cogens); the caller divides
    it by the coal bin nameplate to get a steam-following grid floor. The sector
    class sizes the behind-the-meter pull-out via :data:`CHP_BTM_PCT_BY_SECTOR`.

    PJM and CAISO scope: empty for any other ISO. The coal-cogen routing was
    identified and validated on PJM's CFB / culm / chemical-host coal units;
    CAISO carries one such plant -- Argus Cogen (code 10684, Searles Valley
    Minerals' Trona soda-ash host), EIA-860 Sector 7 (Industrial CHP), ~0.21-
    0.25 TWh/yr predominantly bituminous in EIA-923. CAISO grid coal is retired;
    this lone behind-the-meter industrial cogen burns coal to follow its host
    steam load, not the LMP, so it routes through the same BTM steam-following
    holdout rather than dispatching as an economic grid COAL tranche (CLAUDE.md
    #11: the accurate EIA-860 representation).
    """
    if iso.upper() not in ("PJM", "CAISO"):
        return {}
    from market_sim.data.campd import _COAL_EIA_FUELS, _NON_COMBUSTION_FUELS
    from market_sim.data.eia923 import load_monthly_generation, monthly_netgen_columns
    from market_sim.data.fleet import _eia860_plant_sector
    from market_sim.data.zone_assignment import build_zone_lookup

    try:
        gen = load_monthly_generation()
    except FileNotFoundError:
        return {}
    iso_plants = set(build_zone_lookup(iso))
    if iso_plants:
        gen = gen[gen["plant_id"].isin(iso_plants)]
    if gen.empty:
        return {}

    # Plant sector from EIA-860; only the CHP-host sectors qualify.
    sector_num = _eia860_plant_sector()
    fuels = gen["fuel_type"].astype(str).str.upper()
    combustion = gen[~fuels.isin(_NON_COMBUSTION_FUELS)].copy()
    combustion["is_coal"] = (
        combustion["fuel_type"].astype(str).str.upper().isin(_COAL_EIA_FUELS)
    )
    # Any CHP-sector plant that generated coal in ``year`` qualifies: its coal
    # bin is the COAL_BIT/WC tranche that should follow host steam (the
    # gas/other bins of a multi-fuel chemical host -- Eastman, Covington -- take
    # the gas CHP path separately). The non-CHP coal sectors are filtered below.
    yr = combustion[combustion["year"] == year]
    coal = yr[yr["is_coal"]].groupby("plant_id")["netgen_annual_mwh"].sum()
    # Pooled minimum monthly coal-class average MW (the steam floor numerator).
    mcols = monthly_netgen_columns()
    coal_rows = combustion[combustion["is_coal"]]
    coal_rows["klass"] = [
        classify_plant(f, pm, str(c).upper().startswith("Y"), int(pid))
        for f, pm, c, pid in zip(
            coal_rows["fuel_type"],
            coal_rows["prime_mover"],
            coal_rows["chp"],
            coal_rows["plant_id"],
        )
    ]
    monthly = coal_rows.groupby(["plant_id", "year"])[mcols].sum()
    hours_per_month = np.array(_DAYS_IN_MONTH_NONLEAP, dtype=float) * 24.0

    out: dict[int, tuple[float, str]] = {}
    for pid in coal.index:
        pid = int(pid)
        if float(coal.get(pid, 0.0)) <= 0.0:
            continue
        sec = sector_num.get(pid)
        sector_class = _EIA860_CHP_SECTORS.get(int(sec)) if sec is not None else None
        if sector_class is None:
            continue
        # Minimum monthly average MW across the pooled window (months with no
        # reported class generation are skipped -- the host stood down, not a
        # binding floor).
        min_avg_mw = np.inf
        for (mpid, _y), row in monthly.iterrows():
            if int(mpid) != pid:
                continue
            avg = row.to_numpy(dtype=float) / hours_per_month
            avg = avg[avg > 0.0]
            if avg.size:
                min_avg_mw = min(min_avg_mw, float(avg.min()))
        if not np.isfinite(min_avg_mw):
            min_avg_mw = 0.0
        out[pid] = (min_avg_mw, sector_class)
    return out


# ---------------------------------------------------------------------------
# Coal synchronization fraction
# ---------------------------------------------------------------------------


@lru_cache(maxsize=8)
def coal_sync_online_frac(
    iso: str, per_unit: bool = False, merit_guard: bool = False
) -> dict[int, float]:
    """Return ``{plant_code: online_frac}`` for an ISO's coal plants.

    The CAMPD-derived plant-level synchronization fraction from
    ``data/raw/_processed-legacy/thermal_tranches_<ISO>.csv`` (``online_frac``,
    written by ``scripts/data/derive_thermal_tranches.py`` for COAL): the measured
    share of the year the plant has any unit synchronized. Empty when the ISO
    has no artifact or it predates the column. Consumed by :func:`bins_to_fleet`
    under ``config.coal_sync_srmc_tranche`` to scale the step-3a min-load
    forcing — a unit synchronized ~all year (~1.0) is held on all 8760 hours; a
    two-shifting cycler is forced only in the top ``online_frac`` fraction of
    hours by system load. Plants absent from the map keep the force-all default
    (1.0).
    """
    from market_sim.data.fleet.campd_bins import thermal_tranche_csv_for_iso

    path = thermal_tranche_csv_for_iso(iso, per_unit, merit_guard)
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "online_frac" not in df.columns:
        return {}
    out: dict[int, float] = {}
    for r in df.itertuples(index=False):
        # The artifact's coal-family token (plant_taxonomy.COAL_ARTIFACT_FAMILY).
        if (
            str(getattr(r, "status", "ok")) != "ok"
            or str(r.plant_group) != COAL_ARTIFACT_FAMILY
        ):
            continue
        if pd.isna(r.online_frac):
            continue
        out[int(r.plant_code)] = float(r.online_frac)
    return out


# ---------------------------------------------------------------------------
# Measured CAMPD marginal (incremental) heat rate — coal econ-ramp floor
# ---------------------------------------------------------------------------

# The coal offer-curve bands whose heat-rate multiplier is bounded below by the
# measured incremental burn, and the summary-table column each reads. Only the
# ECONOMIC ramp endpoints are in scope: ``committed`` / ``mustrun`` carry the
# take-or-pay sunk-contract discount (a real contractual driver, not a physical
# burn claim) and ``peak`` is a scarcity wall ABOVE the physical basis, so
# neither is floored here (rule 19 — one mechanism per phenomenon).
COAL_ECON_MARGINAL_HR_BANDS: dict[str, str] = {
    "econ_low": "marg_econ_low_p50",
    "econ_high": "marg_econ_high_p50",
}


@lru_cache(maxsize=None)
def coal_marginal_hr_bounds(iso: str) -> dict[str, float]:
    """Return the ISO's measured coal incremental-heat-rate band floors.

    Reads the committed CAMPD marginal-heat-rate summary
    (``data/raw/reference/<iso>_campd_marginal_hr_summary.csv``, written by
    ``scripts/data/derive_campd_marginal_hr.py``) and returns
    ``{band: multiple_of_base_hr}`` for the bands in
    :data:`COAL_ECON_MARGINAL_HR_BANDS`, taken from the ``COAL`` row.

    The artifact's ``marg_*`` columns are the **incremental** heat rate — the
    slope ``d(heatInput)/d(grossLoad)`` of each unit's own CEMS input-output
    curve at the band-representative load, capacity-weighted across units and
    pooled over the available years — expressed as a multiple of the same class
    ``base_HR`` the offer curve multiplies against. That is the physical short-run
    marginal energy basis of an already-committed unit's next MWh, so it is the
    natural LOWER bound on that band's offer multiplier.

    Returns an empty dict when the ISO has no artifact or no ``COAL`` row, so
    the caller leaves the registered curve untouched.
    """
    path = REFERENCE_DIR / f"{iso.lower()}_campd_marginal_hr_summary.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    # The summary's coal row carries the artifact family token.
    row = df[df["class"].astype(str).str.upper() == COAL_ARTIFACT_FAMILY]
    if row.empty:
        return {}
    r = row.iloc[0]
    out: dict[str, float] = {}
    for band, column in COAL_ECON_MARGINAL_HR_BANDS.items():
        if column not in row.columns or pd.isna(r[column]):
            continue
        out[band] = float(r[column])
    return out


def apply_coal_econ_marginal_hr_floor(
    offer_curve_by_group: dict[str, dict], iso: str
) -> tuple[dict[str, dict], list[tuple[str, str, float, float]]]:
    """Floor every coal class's econ-ramp band at the measured incremental HR.

    Applies :func:`coal_marginal_hr_bounds` to the RESOLVED offer curve — after
    the base registry, any ``--offer-curve-json`` absolute override and any
    ``--offer-curve-delta-json`` relative nudge — so the floor bounds whatever
    the calibration path produced, not the registry default.

    Only ``COAL*`` classes and only the bands in
    :data:`COAL_ECON_MARGINAL_HR_BANDS` are touched; a band already at or above
    its measured basis (a genuine markup) passes through unchanged, as does a
    class whose band is missing or non-numeric. ``ScenarioConfig.offer_curve_by_group``
    values may be lists (the ``peak_ladder`` rungs), so non-float bands are skipped.

    Args:
        offer_curve_by_group: The resolved ``{class: {band: multiplier}}`` curve.
        iso: ISO whose measured artifact supplies the floors.

    Returns:
        ``(curve, lifted)`` — a new curve dict, and the list of
        ``(class, band, before, after)`` tuples that were actually raised (empty
        when the ISO has no artifact or every band already clears its basis), for
        the caller to log.
    """
    floors = coal_marginal_hr_bounds(iso)
    if not floors:
        return offer_curve_by_group, []
    merged = {cls: dict(bands) for cls, bands in offer_curve_by_group.items()}
    lifted: list[tuple[str, str, float, float]] = []
    for cls, bands in merged.items():
        if not is_coal_class(cls):
            continue
        for band, floor in floors.items():
            cur = bands.get(band)
            if not isinstance(cur, (int, float)) or isinstance(cur, bool):
                continue
            if float(cur) < floor:
                lifted.append((cls, band, float(cur), floor))
                bands[band] = floor
    return merged, lifted
