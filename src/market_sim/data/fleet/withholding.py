"""Measured ancillary-service reserve withholding and DAM plant-hourly overlays.

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

import logging
import numpy as np
import pandas as pd

from functools import lru_cache
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.config.plant_taxonomy import COAL_CLASSES, artifact_class
from pathlib import Path
from market_sim.data.fleet.models import (
    Generator,
    _read_clean,
    _use_clean,
)

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")

# Dispatchable thermal plant groups that clear upward ancillary service and
# can therefore withhold energy when they do (gas CC/CT/ST + coal, incl. their
# CHP variants). Storage, renewables, nuclear and hydro are excluded from the
# AS-reserve-withholding pool.
_AS_THERMAL_GROUPS: frozenset[str] = frozenset(
    {
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
        *COAL_CLASSES,
    }
)

# AS-withholding pool: gas thermal only. Baseload coal is self-committed and
# runs flat for energy, carrying little upward AS in ERCOT (reserve sits on
# part-loaded gas headroom, peakers and — increasingly — storage/load), so it
# is excluded from the withdrawal so the probe does not strand baseload.
_AS_GAS_GROUPS: frozenset[str] = _AS_THERMAL_GROUPS - set(COAL_CLASSES)

# PJM AS-withholding pool: gas thermal + flexible oil (steam/CT). PJM's Primary
# Reserve sits on synchronized, part-loaded thermal headroom; the flexible oil
# steam/CT fleet carries the same quick-start reserve as gas. Coal and nuclear
# (baseload, self-committed, run flat) hold little upward reserve and are
# excluded, mirroring the ERCOT gas-only pool.
_AS_PJM_GROUPS: frozenset[str] = _AS_GAS_GROUPS | {"oil"}

# Per-ISO reserve-withholding configuration: (raw-data dir, file prefix,
# withdrawal pool of plant_groups). The measured system-wide hourly reserve
# held out of energy sits in ``<dir>/<prefix>_<year>_as_up_mw.parquet`` on the
# non-leap 8760-hour clock; built by scripts/build_{ercot,pjm}_as_withholding.
_AS_WITHHOLDING: dict[str, tuple[Path, str, frozenset[str]]] = {
    "ERCOT": (RAW_DATA_DIR / "ercot-AS", "ercot", _AS_GAS_GROUPS),
    "PJM": (RAW_DATA_DIR / "PJM-AS", "pjm", _AS_PJM_GROUPS),
}

# Back-compat alias (ERCOT default location; used by the per-type loader).
_AS_WITHHOLDING_DIR = _AS_WITHHOLDING["ERCOT"][0]

# Map each per-resource-type AS column (from the 60-Day DAM Gen Resource Data,
# aggregated by ERCOT Resource Type) to the fleet plant_groups that share it.
# Storage and load AS are not here: they do not withhold *thermal* energy.
_AS_RESTYPE_TO_GROUPS: dict[str, frozenset[str]] = {
    "gas_cc": frozenset({"CC_REGULAR", "CC_CHP"}),
    "gas_ct": frozenset({"CT_PEAKER", "CT_CHP"}),
    "gas_st": frozenset({"ST_GAS", "ST_CHP"}),
    "coal": frozenset(COAL_CLASSES),
}

# CAISO formula-based upward operating-reserve requirement (used by the
# default-off ``as_reserve_formula`` scaffold until OASIS cleared-AS data
# (AS_REQ/AS_RESULTS) can be pulled — outbound network is blocked in the remote
# env). R(t) = max(MSSC, MORC_LOAD_FRAC*load) + REG_UP_LOAD_FRAC*load, a
# published-standard WECC requirement carrying no fitted constants:
#   - contingency reserve = WECC MORC: the greater of the most-severe single
#     contingency (the largest single online unit nameplate) or 5% of
#     hydro-served + 7% of thermal-served load (~6.7% of load for CA's mix);
#   - regulation-up ~= 1% of load (CAISO Reg ~300-500 MW on 25-40 GW).
# Reg-Down is a downward product (it withholds no upward energy offer), excluded.
_CAISO_MORC_LOAD_FRAC = 0.067
_CAISO_REG_UP_LOAD_FRAC = 0.01

# The WECC most-severe single contingency (MSSC) is the largest single
# synchronous unit (for CAISO a Diablo Canyon unit, ~1.1 GW). Imports are
# aggregate tranches and wind/solar are many small inverters, so neither is a
# credible single-unit contingency; both are excluded when sizing the MSSC.
_CAISO_MSSC_EXCLUDE_FUELS: frozenset[str] = frozenset({"import", "wind", "solar"})


# Clean ``ancillary-services`` cleared-MW columns that make up the *upward*
# reserve held out of energy (Reg-Down is a downward product — it removes no
# upward energy offer — and is excluded, exactly as the raw withholding builders
# do). Their sum reproduces the raw ``as_up_mw`` series for ERCOT.
_CLEAN_AS_UP_MW_COLS: tuple[str, ...] = (
    "reg_up_mw",
    "spin_mw",
    "nonspin_mw",
    "supp_30min_mw",
)

# The fixed non-leap 8760-hour model calendar (representative year 2023), shared
# with :mod:`scripts.data.build_ercot_as_withholding`. Clean AS rows (UTC, with a
# wall-clock ``interval_start_local``) are folded onto this (month, day, hour)
# grid so the reconstructed series lands on the same clock as the fleet.
_AS_MODEL_CALENDAR = pd.date_range("2023-01-01", periods=8760, freq="h")
_AS_MODEL_INDEX = pd.MultiIndex.from_arrays(
    [_AS_MODEL_CALENDAR.month, _AS_MODEL_CALENDAR.day, _AS_MODEL_CALENDAR.hour],
    names=["month", "day", "hour"],
)
# Largest hole (hours) interpolated when placing a series on the 8760-hour clock
# (the DST spring-forward gap is 1h); bigger holes are partial-year coverage and
# are zero-filled rather than interpolated. Mirrors build_ercot_as_withholding.
_AS_MAX_GAP_HOURS = 24


def _clean_as_reserve_withholding_mw(
    year: int, hours: int, iso: str, market: str = "DAM"
) -> np.ndarray | None:
    """Reconstruct ``iso``'s hourly upward-AS withholding MW from data/clean.

    Reads the curated AS clearing table
    (``read_clean("ancillary-services", iso=iso, market=market, year=year)``),
    sums the system-wide (``zone == "SYSTEM"``) upward cleared-MW products
    (:data:`_CLEAN_AS_UP_MW_COLS`) and folds them onto the fleet's non-leap
    8760-hour clock by the local wall-clock ``(month, day, hour)`` — the same
    reduction :mod:`scripts.data.build_ercot_as_withholding` applies to the raw
    cleared-DAM-AS reports, so for ERCOT this reproduces the raw ``as_up_mw``
    series exactly (see ``tests/test_consume_fleet.py``). Returns ``None`` when
    the clean partition is absent or carries no cleared MW (the feature then
    no-ops, matching the raw "missing parquet -> None" behavior).

    NOTE: this is faithful for ERCOT (its raw withholding *is* the cleared DAM
    up-AS). PJM's raw withholding is a different quantity (the RT Primary Reserve
    requirement, which the clean AS schema intentionally does not carry), so the
    clean reconstruction is not a like-for-like substitute there — surfacing the
    PJM Primary Reserve through the clean seam would need an AS-schema contract
    change (raise one rather than editing the frozen YAML).
    """
    try:
        df = _read_clean("ancillary-services", iso=iso, market=market, year=year)
    except FileNotFoundError:
        logger.warning(
            "as_reserve_withholding(clean) on but no clean AS partition for "
            "%s %s %d; withholding skipped",
            iso,
            market,
            year,
        )
        return None
    if "zone" in df.columns:
        df = df[df["zone"].astype("string").str.strip() == "SYSTEM"]
    present = [c for c in _CLEAN_AS_UP_MW_COLS if c in df.columns]
    if df.empty or not present:
        return None
    up = df[present].sum(axis=1, min_count=1)
    covered = df.loc[df[present].notna().any(axis=1)].copy()
    if covered.empty:
        return None

    local = pd.to_datetime(covered["interval_start_local"])
    work = pd.DataFrame({"ts": local, "mw": up.loc[covered.index].to_numpy(float)})
    keep = (work["ts"].dt.year == year) & ~(
        (work["ts"].dt.month == 2) & (work["ts"].dt.day == 29)
    )
    work = work[keep]
    if work.empty:
        return None
    grouped = work.groupby(
        [work["ts"].dt.month, work["ts"].dt.day, work["ts"].dt.hour]
    )["mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    aligned = grouped.reindex(_AS_MODEL_INDEX)
    missing = int(aligned.isna().sum())
    if 0 < missing <= _AS_MAX_GAP_HOURS:
        aligned = aligned.interpolate(limit_direction="both")
    # A larger hole is partial-year coverage; leave it as 0 (no fabricated
    # reserve) so callers using the covered hours still get exact values.
    series = aligned.fillna(0.0).to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(hours - len(series))])
    return series[:hours]


@lru_cache(maxsize=8)
def load_as_reserve_withholding_mw(
    year: int, hours: int, iso: str = "ERCOT"
) -> np.ndarray | None:
    """Load ``iso``'s hourly system-wide reserve-withholding MW for ``year``.

    Returns the ``(hours,)`` reserve-held-out-of-energy MW series written by
    :mod:`scripts.data.build_ercot_as_withholding` (ERCOT: cleared DAM up-AS) or
    :mod:`scripts.data.build_pjm_as_withholding` (PJM: the RT Primary Reserve
    requirement), or ``None`` when the parquet is absent (the feature then
    silently no-ops, like a backcast year with no outage windows). The file
    sits on the same non-leap 8760-hour clock as the fleet, so it is returned
    as-is when ``hours == 8760``; other horizons take the leading ``hours``
    values.

    When the clean seam is on (:func:`_use_clean`), the series is instead
    reconstructed from the curated ``ancillary-services`` clearing table
    (:func:`_clean_as_reserve_withholding_mw`) — for ERCOT this matches the raw
    ``as_up_mw`` series exactly.
    """
    if _use_clean():
        return _clean_as_reserve_withholding_mw(year, hours, (iso or "ERCOT").upper())
    spec = _AS_WITHHOLDING.get((iso or "ERCOT").upper())
    if spec is None:
        return None
    as_dir, prefix, _ = spec
    path = as_dir / f"{prefix}_{year}_as_up_mw.parquet"
    if not path.exists():
        logger.warning(
            "as_reserve_withholding on but %s is missing; AS withholding "
            "skipped for %d",
            path,
            year,
        )
        return None
    series = pd.read_parquet(path)["as_up_mw"].to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(hours - len(series))])
    return series[:hours]


def load_as_thermal_withholding(year: int, hours: int) -> dict[str, np.ndarray] | None:
    """Load ERCOT's measured per-thermal-class hourly AS-up MW for ``year``.

    Reads ``ercot_<year>_as_by_restype_hourly.parquet`` — the per-resource
    60-Day DAM AS awards aggregated by ERCOT Resource Type (RegUp + RRS +
    ECRS; offline Non-Spin and the storage/load share are excluded, as those
    do not withhold *thermal* energy). Returns ``{restype_col: (hours,) MW}``
    for the thermal columns present (``gas_cc``/``gas_ct``/``gas_st``/
    ``coal``), or ``None`` when the file is absent (caller then falls back to
    the system-total upper bound). Same non-leap 8760-hour clock as the fleet.
    """
    path = _AS_WITHHOLDING_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    out: dict[str, np.ndarray] = {}
    for col in _AS_RESTYPE_TO_GROUPS:
        if col not in df.columns:
            continue
        series = df[col].to_numpy(dtype=float)
        if len(series) < hours:
            series = np.concatenate([series, np.zeros(hours - len(series))])
        out[col] = series[:hours]
    return out or None


def caiso_operating_reserve_mw(
    load_shape: np.ndarray, mssc_mw: float, hours: int
) -> np.ndarray:
    """Formula-based CAISO upward operating-reserve requirement (MW/hour).

    ``R(t) = max(MSSC, 0.067*load(t)) + 0.01*load(t)`` — a published-standard
    WECC requirement carrying no fitted constants:

    * **Contingency reserve** is the WECC Minimum Operating Reliability Criterion
      (MORC): the greater of the most-severe single contingency (``mssc_mw``, the
      largest single online unit nameplate — ~1,150 MW for a Diablo Canyon unit)
      or 5% of hydro-served + 7% of thermal-served load (~6.7% of load for
      California's generation mix; :data:`_CAISO_MORC_LOAD_FRAC`).
    * **Regulation-up** is ~1% of load (CAISO Reg ~300-500 MW on 25-40 GW of
      load; :data:`_CAISO_REG_UP_LOAD_FRAC`).

    Reg-Down is a downward product — it withholds no upward energy offer — and is
    excluded. ``load_shape`` is the hourly system load (MW) on the fleet's clock;
    a shorter series is zero-padded and a longer one truncated to ``hours``. This
    is the default-off scaffold to be replaced by measured OASIS AS_REQ/
    AS_RESULTS MW once the remote-env outbound-network block is lifted.
    """
    load = np.asarray(load_shape, dtype=float)
    if load.shape[0] < hours:
        load = np.concatenate([load, np.zeros(hours - load.shape[0])])
    load = load[:hours]
    contingency = np.maximum(float(mssc_mw), _CAISO_MORC_LOAD_FRAC * load)
    regulation = _CAISO_REG_UP_LOAD_FRAC * load
    return contingency + regulation


def _withdraw_top_of_merit(
    availability: np.ndarray,
    pmax: np.ndarray,
    heat_rate: np.ndarray,
    pool: np.ndarray,
    as_series: np.ndarray,
) -> tuple[float, float]:
    """Withdraw ``as_series`` MW/hour from ``pool``'s top-of-merit headroom.

    Removes the hourly reserve from the highest-heat-rate (most expensive,
    most peaking) available tranches in ``pool`` first, cascading down — the
    headroom that physically carries the AS award. Mutates ``availability`` in
    place and returns ``(GWh-equiv withdrawn, GWh-equiv unmet)`` for logging.
    """
    if pool.size == 0:
        return 0.0, 0.0
    order = pool[np.argsort(-heat_rate[pool], kind="stable")]
    caps = pmax[order, np.newaxis] * availability[order, :]  # (k, hours)
    cum_above = np.cumsum(caps, axis=0) - caps  # MW ranked above each tranche
    removed = np.clip(as_series[np.newaxis, :] - cum_above, 0.0, caps)
    with np.errstate(divide="ignore", invalid="ignore"):
        availability[order, :] = np.where(
            pmax[order, np.newaxis] > 0.0,
            (caps - removed) / pmax[order, np.newaxis],
            0.0,
        )
    unmet = float(np.maximum(as_series - caps.sum(axis=0), 0.0).sum())
    return float(removed.sum()), unmet


# Fraction of nameplate a unit can ramp within the 10-minute reserve window,
# by plant group — the cap on the upward operating reserve a synchronized unit
# can deliver (``FleetArrays.ramp10 = frac * pmax``; rebuild step 3b,
# docs/multi-iso/pjm-reserve-ordc.md Phase 2). Class ramp rates (% of capacity
# per minute, x10 min) from NREL "Western Wind and Solar Integration Study"
# Phase 2 (NREL/TP-5500-55588, App. H) and EIA generator ramp-rate ranges:
# subcritical/supercritical coal steam ~1.5 %/min, gas combined cycle ~4 %/min,
# simple-cycle CT / oil peakers fast-start (full output reachable in <10 min),
# legacy gas steam ~2 %/min. Nuclear runs baseload (no upward reserve). Keyed by
# the model plant group; the per-fuel fallback covers non-binned fleets. These
# depend only on capacity and class, so ramp10 regenerates for a forecast year.
RAMP10_FRAC_BY_GROUP: dict[str, float] = {
    # Coal steam, ~1.5 %/min — every coal subclass (COAL-SUB).
    "COAL_LIGNITE": 0.15,
    "COAL_PRB": 0.15,
    "COAL_BIT": 0.15,
    "COAL_WC": 0.15,
    "CC_REGULAR": 0.40,  # combined cycle, ~4 %/min
    "CC_CHP": 0.40,
    "CT_PEAKER": 1.00,  # simple-cycle fast-start, full in <10 min
    "CT_CHP": 1.00,
    "ST_GAS": 0.20,  # legacy gas steam, ~2 %/min
    "ST_CHP": 0.20,
}
# Per-fuel fallback (legacy aggregated fleets without a plant group). Nuclear and
# the renewables/hydro/storage classes carry no thermal upward reserve here.
RAMP10_FRAC_BY_FUEL: dict[str, float] = {
    "coal": 0.15,
    "gas_cc": 0.40,
    "gas_cc_ccs": 0.40,
    "gas_ct": 1.00,
    "gas_st": 0.20,
    "oil": 1.00,
}


def _ramp10_capability(
    generators: list[Generator],
    pmax: np.ndarray,
    measured: dict | None = None,
) -> np.ndarray:
    """Return the ``(n_gen,)`` 10-minute ramp capability (MW) for a fleet.

    ``RAMP10_FRAC_BY_GROUP[plant_group]`` (preferred, the per-plant CAMPD-bin
    fleets) or :data:`RAMP10_FRAC_BY_FUEL` (legacy aggregated fleets) times the
    unit's capacity. Generators in neither map (nuclear, hydro, wind, solar,
    storage, imports) get 0.0 — they provide no thermal upward operating
    reserve. See :attr:`FleetArrays.ramp10`.

    When ``measured`` is given (``ScenarioConfig.measured_ramp_capability`` —
    the ``ramp-capability`` clean datatype, plant_code →
    :class:`~market_sim.data.ramp_capability.PlantRampCapability`), each
    covered plant's class fraction is reconciled against its MEASURED EIA-860
    fast-start capacity (floor) and CAMPD CEMS hourly ramp envelope (ceiling)
    via :func:`market_sim.data.ramp_capability.measured_ramp10_frac`; uncovered
    plants keep the class estimate (rule 14: measured preferred, estimate only
    as fallback).
    """
    from market_sim.data.ramp_capability import measured_ramp10_frac

    fracs = np.zeros(len(generators), dtype=float)
    for g_idx, gen in enumerate(generators):
        frac = RAMP10_FRAC_BY_GROUP.get(getattr(gen, "plant_group", "") or "")
        if frac is None:
            frac = RAMP10_FRAC_BY_FUEL.get(gen.fuel_type, 0.0)
        if measured and frac > 0.0:
            cap = measured.get(int(getattr(gen, "plant_code", 0) or 0))
            if cap is not None:
                frac = measured_ramp10_frac(frac, cap)
        fracs[g_idx] = frac
    return fracs * pmax


# Coal synchronization online%-scaled forcing (step-3a): a plant whose measured
# online_frac is at or above this threshold is treated as synchronized ~all year
# and held at its min-load floor every hour (the always-online supercriticals);
# below it the floor is placed only in the top-online_frac fraction of hours by
# system load (a two-shifting cycler). 0.99 keeps the supercriticals on the
# force-all path (rounding to 8760) while letting the cyclers shed their cheap
# overnight hours. See generators_to_fleet_arrays / bins_to_fleet.
_COAL_SYNC_FORCE_ALL: float = 0.99


def _dam_waterfill(
    a: np.ndarray,
    cap: np.ndarray,
    target: np.ndarray,
    active: np.ndarray,
    ceil: "np.ndarray | None" = None,
) -> np.ndarray:
    """Bidirectional water-fill of an availability sub-block to a per-hour target.

    ``a`` is (m, H) unit availability, ``cap`` (m,) the units' pmax, ``target``
    (H,) the desired cap-weighted mean availability, ``active`` (H,) the hours
    to touch. Restore (target >= cur): ``a' = a + λ(ceil − a)`` with
    ``λ = (target − cur)/(ceil_mean − cur)``; remove (target < cur): ``a' = a·
    (target/cur)`` — both land the cap-weighted mean on ``target`` (where the
    ceiling permits) while keeping each unit's relative shape; tranches cap at
    their ceiling; inactive hours untouched. Identical semantics to the
    class-HOUR water-fill in :func:`generators_to_fleet_arrays`, factored so a
    mapped plant and the unmapped residual set share one implementation
    (ERCOT-97 plant grain).

    ``ceil`` (m,) is each unit's availability CEILING — 1.0 by default, and
    ``BIN_FORCED_DERATE_BY_YEAR``'s multiplier for units carrying a confirmed
    physical unit loss (ERCOT-137 correctness fix; ERCOT-135 §7.2): the
    measured plant fraction is live/rating over the DAM's OWN (post-loss)
    rating, so restoring toward a flat 1.0 of model pmax resurrects destroyed
    capacity — Martin Lake landed at 1.451× its own COP-declared max because
    the water-fill overrode the ``N_COAL4 {2025: 0.67}`` forced derate
    (unit 1 destroyed before the vintage; the CAMPD outage derive can never
    see it). With ``ceil`` at 1.0 everywhere the arithmetic is bit-identical
    to the previous form.
    """
    cap_sum = float(cap.sum())
    if cap_sum <= 0.0 or a.shape[0] == 0:
        return a
    if ceil is None:
        ceil = np.ones(a.shape[0])
    ceil_col = ceil[:, None]  # (m, 1)
    ceil_mean = float((ceil * cap).sum()) / cap_sum
    cur = (a * cap[:, None]).sum(axis=0) / cap_sum  # (H,)
    restore = active & np.isfinite(target) & (target >= cur)
    remove = active & np.isfinite(target) & (target < cur)
    new = a.copy()
    lam = np.clip((target - cur) / np.maximum(ceil_mean - cur, 1e-9), 0.0, 1.0)
    new[:, restore] = a[:, restore] + lam[None, restore] * np.maximum(
        ceil_col - a[:, restore], 0.0
    )
    mu = np.where(remove, target / np.maximum(cur, 1e-9), 1.0)
    new[:, remove] = a[:, remove] * mu[None, remove]
    return np.minimum(new, ceil_col)


def _ercot_dam_plant_hourly_apply(
    availability: np.ndarray,
    generators: "list[Generator]",
    pmax: np.ndarray,
    hours: int,
    year: int,
    meas_h: "dict[str, np.ndarray]",
    plant_series: "dict[int, np.ndarray]",
    logger: "logging.Logger",
    ceil_full: "np.ndarray | None" = None,
    plant_rating: "dict[int, np.ndarray] | None" = None,
) -> set:
    """Redistribute measured DAM availability to the PLANT grain (ERCOT-97).

    For each covered class, the crosswalked plants are pinned to their own
    measured site-hour fraction (``plant_series``) and the UNMAPPED remainder is
    water-filled so the class-HOUR cap-weighted mean still lands on the measured
    class fraction (``meas_h``). The class total is thus unchanged (measured);
    only WHICH plant carries the derate moves — the ~259 MW-mean per-plant
    misallocation the class grain smears (ERCOT-96 Finding). Zero fitted
    parameters. Returns the set of classes it handled (the caller skips them in
    the class-HOUR loop). A class with no crosswalked plant is left untouched so
    the class-HOUR grain handles it.

    ``ceil_full`` (n_gen,) is the fleet-wide per-unit availability ceiling
    (``BIN_FORCED_DERATE_BY_YEAR`` multipliers, 1.0 elsewhere; ERCOT-137
    correctness fix — see :func:`_dam_waterfill`). The residual target the
    UNMAPPED remainder chases is left on the raw ``pf`` accounting
    deliberately: a mapped plant saturating at its forced-derate ceiling must
    NOT push its destroyed capacity onto other plants — that would resurrect
    the loss elsewhere in the class.

    ``plant_rating`` (owner ruling #10, signature A1; ercot-149 §6.3,
    PRECOMMIT-ercot191 §1d) is ``{plant_code: (hours,) covered DAM rating
    MW}``. When provided, the REMOVE direction (``pf`` below the plant's
    current mean) is diluted to the plant's measured coverage::

        pf_eff = pf·cov + cur·(1 − cov),  cov = clip(covered_MW / Σ pmax, 0, 1)

    so the measured fraction governs exactly the share of the model plant the
    accepted DAM sites measure and the UNMEASURED remainder keeps its
    incumbent availability — V H Braunig 2025 must not be pinned to ~0.075 by
    VHB3's own outage when VHB1/2's status is unmeasured. The RESTORE
    direction is untouched (its collisions are owned by the armed event caps,
    rule 19), ``cov = 1`` reproduces the prior arithmetic exactly, and the
    residual accounting stays on the raw ``pf`` per the ERCOT-137 precedent
    above (an unmeasured share must not push its removal onto other plants).
    """
    done: set = set()
    # plant_code -> class-local unit indices, for plants that actually have
    # units in the fleet (a crosswalk row for a retired/absent plant is inert).
    plant_of_unit = {gi: int(g.plant_code) for gi, g in enumerate(generators)}
    for cls, t_full in meas_h.items():
        idx = np.array(
            # ``meas_h`` is keyed by the artifact's class token (the coal
            # family for coal), so the fleet side reads its artifact class.
            [
                gi
                for gi, g in enumerate(generators)
                if artifact_class(g.plant_group) == cls
            ],
            dtype=int,
        )
        if idx.size == 0:
            continue
        cap = pmax[idx]
        cap_sum = float(cap.sum())
        if cap_sum <= 0.0:
            continue
        t = t_full[:hours]
        covered = np.isfinite(t)
        if not covered.any():
            continue
        # Partition this class's units into mapped (crosswalked, present in
        # plant_series) and unmapped.
        mapped_plants: dict[int, np.ndarray] = {}
        for j, gi in enumerate(idx):
            pc = plant_of_unit[gi]
            if pc in plant_series:
                mapped_plants.setdefault(pc, []).append(j)
        if not mapped_plants:
            continue  # no plant grain for this class -> class-hour handles it
        mapped_plants = {pc: np.array(v, dtype=int) for pc, v in mapped_plants.items()}
        local_mapped = np.concatenate(list(mapped_plants.values()))
        unmapped = np.array(
            [j for j in range(idx.size) if j not in set(local_mapped.tolist())],
            dtype=int,
        )

        # Mapped MW per hour from the plants' own measured fractions, and pin
        # each plant's units to its fraction via the shared water-fill.
        mapped_mw = np.zeros(hours)
        nanhit = 0
        for pc, loc in mapped_plants.items():
            pf = plant_series[pc][:hours]
            pf_fin = np.isfinite(pf)
            active = covered & pf_fin
            nanhit += int((covered & ~pf_fin).sum())
            gidx = idx[loc]
            cap_p = pmax[gidx]
            cap_p_sum = float(cap_p.sum())
            # Ruling #10 (see docstring): dilute the REMOVE direction to the
            # plant's measured coverage; restore direction untouched.
            pf_eff = pf
            if plant_rating is not None and pc in plant_rating and cap_p_sum > 0.0:
                cov = np.clip(plant_rating[pc][:hours] / cap_p_sum, 0.0, 1.0)
                cur_p = (availability[gidx, :hours] * cap_p[:, None]).sum(
                    axis=0
                ) / cap_p_sum
                rem = active & np.isfinite(cov) & (pf < cur_p)
                if rem.any():
                    pf_eff = pf.copy()
                    pf_eff[rem] = pf[rem] * cov[rem] + cur_p[rem] * (1.0 - cov[rem])
            availability[gidx, :hours] = _dam_waterfill(
                availability[gidx, :hours],
                cap_p,
                pf_eff,
                active,
                ceil=None if ceil_full is None else ceil_full[gidx],
            )
            # Raw-pf accounting, deliberately (docstring: the ERCOT-137
            # precedent — an unmeasured share's removal is nobody else's).
            mapped_mw[active] += pf[active] * cap_p_sum

        # Residual target so the class-hour total still equals the measured
        # class fraction: (t·cap_sum − mapped_mw) spread over the unmapped cap.
        if unmapped.size > 0:
            res_gidx = idx[unmapped]
            res_cap = pmax[res_gidx]
            res_cap_sum = float(res_cap.sum())
            if res_cap_sum > 0.0:
                res_frac = np.full(hours, np.nan)
                res_frac[covered] = np.clip(
                    (t[covered] * cap_sum - mapped_mw[covered]) / res_cap_sum,
                    0.0,
                    1.0,
                )
                availability[res_gidx, :hours] = _dam_waterfill(
                    availability[res_gidx, :hours],
                    res_cap,
                    res_frac,
                    covered,
                    ceil=None if ceil_full is None else ceil_full[res_gidx],
                )
        done.add(cls)
        logger.info(
            "ERCOT measured thermal DAM availability (%d): %s plant-grain "
            "redistribution — %d crosswalked plant(s), %d unmapped tranche(s), "
            "median class target %.3f%s",
            year,
            cls,
            len(mapped_plants),
            int(unmapped.size),
            float(np.median(t[covered])),
            f" ({nanhit} covered plant-hour(s) fell back to class grain)"
            if nanhit
            else "",
        )
    return done
