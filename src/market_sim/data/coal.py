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

from market_sim.config.paths import EIA_860_DIR, PROCESSED_DIR
from market_sim.config.plant_taxonomy import (
    COAL_CODE_TO_SUPPLY,
    COAL_SUPPLY_TO_CLASS,
    classify_plant,
    coal_code_to_class,
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
    """
    base = COAL_PLANT_SUPPLY.get(int(plant_code))
    if base:
        return base
    derived = _derived_coal_supply().get(int(plant_code))
    if derived:
        return derived
    return _eia860_retiree_coal_supply().get(int(plant_code), "")


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
    code and finally the bare ``COAL`` class. Mirrors the calibration
    benchmark's coal resolver so the model and benchmark split coal identically.
    """
    return (
        COAL_SUPPLY_TO_CLASS.get(coal_supply_class(int(plant_code)))
        or coal_code_to_class(fuel_code)
        or "COAL"
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
def coal_sync_online_frac(iso: str) -> dict[int, float]:
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
    path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    if not path.exists():
        return {}
    df = pd.read_csv(path)
    if "online_frac" not in df.columns:
        return {}
    out: dict[int, float] = {}
    for r in df.itertuples(index=False):
        if str(getattr(r, "status", "ok")) != "ok" or str(r.plant_group) != "COAL":
            continue
        if pd.isna(r.online_frac):
            continue
        out[int(r.plant_code)] = float(r.online_frac)
    return out
