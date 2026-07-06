"""Winter fuel-inventory seasonal oil-burn budget (NEISO Component A).

Reader over the ``winter-fuel-inventory`` clean datatype that assembles the
inputs for the winter (Nov-Mar) seasonal oil-burn energy budget LP rows
(:func:`market_sim.model.dispatch._build_oil_budget_rows`), the first of the
two coupled mechanisms in the NEISO fuel-inventory / seasonal-reliability build
(``docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md``).

The mechanism is the hydro monthly-energy budget applied to oil: a limited
seasonal fuel *stock* is rationed across cold snaps, and when the budget binds
the constraint's dual is the endogenous winter scarcity rent that lifts the
persisted P1 LMP above the flat dual-fuel oil-parity cap (~$258/MWh). This
supersedes the rejected ``fuel.py:load_oil_burn_budget`` (F923 petroleum
*receipts*, a measured deliveries-to-tank OUTCOME inadmissible under CLAUDE.md
#13). Here the budget is DERIVED from forward-regenerable capacity/logistics
quantities — start-of-season tank fill, re-supply delivery rate, boiler firing
rate — read from ISO-NE fuel-security studies (OFSA / Winter Reliability
Program) and EIA-860, every one of which could be produced for a forward year
and responds to changed weather/fleet (rule #13 admissible).

Key modelling choices (see the plan doc + the session that set them):

- **Scope** is the oil-capable fleet: oil-primary units (``fuel_type_idx ==
  oil``) PLUS the dual-fuel gas units' oil limb (the ``dual_fuel_plant_groups``
  EIA-860 roster — the same units :func:`~market_sim.data.fuel.apply_dual_fuel_pricing`
  caps at oil parity). Budgeting the limb is the whole point: it is the coverage
  hole that killed the oil-primary-only F923 neiso-40 probe.
- **Oil-only via the switch mask.** A dual-fuel unit burns gas most of the year
  and oil only when its delivered gas price exceeds oil parity. The constraint
  therefore sums a dual-fuel unit's dispatch only over its *exogenous* oil-switch
  hours (:func:`~market_sim.data.fuel.dual_fuel_switch_mask`, price-driven and
  known pre-solve); gas-fired hours carry coefficient 0. Oil-primary units count
  all hours. So the row budgets *oil* energy, never a dual-fuel unit's gas
  generation.
- **Pooled fleet row.** ``start_fill`` is published as a fleet aggregate
  (WRP 2.8-3.8 M bbl), so one pooled row per winter month lets the LP ration the
  shared regional stock optimally rather than inventing a per-plant allocation.
- **MMBtu-correct.** The constraint sums ``heat_rate[g] * P[g,t]`` (energy
  input, MMBtu) against a MMBtu budget, so a heterogeneous-heat-rate pool is
  priced on the fuel it actually consumes. Dual-fuel units carry their gas heat
  rate on oil hours (a small known simplification — oil heat rates run slightly
  worse).
- **Monthly horizon, phased re-supply.** Each of the five winter months
  (Nov-Mar) gets ``start_fill/5`` of the opening tank amortized plus its uniform
  share of the ``delivery_rate`` re-supply (``fills`` tank-fills per season, each
  one tank capacity). The re-supply is spread uniformly — an average delivery
  rate, deliberately NOT timed to the coldest month, which would be tuning the
  mechanism to the residual (CLAUDE.md #1). Monthly-independent rows cannot carry
  stock across months (the tank-autonomy rolling window would; it was declined
  for scope), so a sustained snap can still outrun a month's budget.

Backcast-only, NEISO-only, default off (``config.neiso_winter_fuel_inventory``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from market_sim.config.constants import MMBTU_PER_BBL_DISTILLATE
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    FleetArrays,
    _hour_to_month_index,
    dual_fuel_plant_groups,
)

# Winter fuel-security horizon: November through March, as 0-based calendar
# month indices (matching :func:`_hour_to_month_index`). The plan's Nov-Mar
# window; the OFSA's own 90-day Dec-Feb figure is the delivery-rate basis and is
# recorded on the study rows but not the horizon used here.
WINTER_MONTH_INDICES: tuple[int, ...] = (10, 11, 0, 1, 2)  # Nov, Dec, Jan, Feb, Mar
_N_WINTER_MONTHS: int = len(WINTER_MONTH_INDICES)

# Gas-primary fuel codes whose units can carry a dual-fuel oil limb (EIA-860
# "Switch Between Oil and Natural Gas?" = Y). Mirrors fuel._GAS_FUEL_IDX.
_GAS_FUEL_IDX: tuple[int, ...] = (
    FUEL_TYPE_MAP["gas_cc"],
    FUEL_TYPE_MAP["gas_ct"],
    FUEL_TYPE_MAP["gas_cc_ccs"],
    FUEL_TYPE_MAP["gas_st"],
)
_OIL_FUEL_IDX: int = FUEL_TYPE_MAP["oil"]


@dataclass(frozen=True)
class WinterFuelStudy:
    """Scalar seasonal fuel-security parameters for one ISO.

    Read from the ``winter-fuel-inventory`` clean datatype's fleet/system study
    rows (ISO-NE OFSA + Winter Reliability Program). All are forward-derivable
    capacity/logistics quantities, never measured burn/receipt outcomes.
    """

    start_fill_low_bbl: float  # WRP low aggregate oil-inventory target (bbl)
    start_fill_high_bbl: float  # WRP high aggregate oil-inventory target (bbl)
    delivery_fills_per_season: float  # oil re-supply, tank fills per winter
    season_days: float  # study horizon length (days; informational)
    tank_capacity_days: float  # fleet oil autonomy (days; informational)
    annual_run_limit_days: float  # air-permit annual oil-run cap (days/yr)


def _import_clean_io():
    """Import the shared ``scripts.lib.clean_io`` reader seam, lazily.

    ``clean_io`` lives under ``scripts/`` (not an installed package), so the repo
    root is put on ``sys.path`` the way the curation scripts do. Done lazily so
    only the opt-in winter-fuel path pays the cost.
    """
    import sys

    from market_sim.config import paths

    root = str(paths.REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from scripts.lib import clean_io  # noqa: E402

    return clean_io


def _scalar(df, *, metric: str, unit: str, entity: str | None = None) -> float | None:
    """Return the single ``value`` for a metric/unit (optionally entity) row.

    Returns ``None`` when no such row exists so the caller can fall back or skip.
    """
    mask = (df["metric"] == metric) & (df["unit"] == unit)
    if entity is not None:
        mask = mask & (df["entity"] == entity)
    sub = df[mask]
    if sub.empty:
        return None
    return float(sub["value"].iloc[0])


def read_winter_fuel_study(
    iso: str, clean_dir: Path | None = None
) -> WinterFuelStudy | None:
    """Read the scalar seasonal fuel-security study parameters for ``iso``.

    Returns ``None`` when the ISO has no ``winter-fuel-inventory`` clean data
    (every non-NEISO ISO today), so the caller skips the constraint.

    Args:
        iso: ISO identifier (e.g. ``"ISONE"``/``"NEISO"``).
        clean_dir: Optional override of the clean-data root (tests).

    Returns:
        A :class:`WinterFuelStudy`, or ``None``.
    """
    clean_io = _import_clean_io()
    # The datatype is curated under the ISO-NE code ("ISONE").
    iso_key = "ISONE" if iso.upper() in ("NEISO", "ISONE", "ISO-NE") else iso.upper()
    if not clean_io.clean_exists("winter-fuel-inventory", iso=iso_key):
        return None
    df = clean_io.read_clean("winter-fuel-inventory", iso=iso_key)
    if df.empty:
        return None

    low = _scalar(df, metric="start_fill", unit="bbl", entity="OIL_WRP_target_low")
    high = _scalar(df, metric="start_fill", unit="bbl", entity="OIL_WRP_target_high")
    fills = _scalar(df, metric="delivery_rate", unit="fills_per_season")
    season_days = _scalar(df, metric="season_days", unit="days")
    tank_days = _scalar(df, metric="tank_capacity", unit="days")
    run_limit = _scalar(df, metric="annual_run_limit", unit="days")
    if low is None or high is None or fills is None:
        return None
    return WinterFuelStudy(
        start_fill_low_bbl=low,
        start_fill_high_bbl=high,
        delivery_fills_per_season=fills,
        season_days=season_days if season_days is not None else 90.0,
        tank_capacity_days=tank_days if tank_days is not None else 10.0,
        annual_run_limit_days=run_limit if run_limit is not None else 30.0,
    )


def oil_capable_gen_idx(
    fleet: FleetArrays, eia860_dir: Path | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(gen_idx, is_dual_fuel)`` for the oil-capable fleet.

    Scope is oil-primary units (``fuel_type_idx == oil``) plus switch-capable
    dual-fuel gas units — the EIA-860 ``dual_fuel_plant_groups`` roster keyed by
    ``(plant_code, plant_group)`` (the same roster
    :func:`~market_sim.data.fuel.apply_dual_fuel_pricing` uses), never a guessed
    per-plant dict (CLAUDE.md #24). ``is_dual_fuel`` marks which of the returned
    generators are dual-fuel gas units (so their budget coefficient gates on the
    oil-switch mask) versus oil-primary (all hours).

    Args:
        fleet: Vectorized fleet arrays carrying ``fuel_type_idx``, ``plant_code``,
            ``plant_group``.
        eia860_dir: Optional override for the EIA-860 vintage directory.

    Returns:
        ``(gen_idx, is_dual_fuel)``, both shape ``(n_oil,)``; ``gen_idx`` sorted.
    """
    fuel_idx = np.asarray(fleet.fuel_type_idx)
    is_oil_primary = fuel_idx == _OIL_FUEL_IDX

    is_dual = np.zeros(fuel_idx.shape, dtype=bool)
    groups = fleet.plant_group
    if groups is not None:
        capable = dual_fuel_plant_groups(eia860_dir)
        if capable:
            is_gas = np.isin(fuel_idx, _GAS_FUEL_IDX)
            plant_code = np.asarray(fleet.plant_code)
            for g in np.nonzero(is_gas)[0]:
                if (int(plant_code[g]), str(groups[g])) in capable:
                    is_dual[g] = True

    gen_idx = np.nonzero(is_oil_primary | is_dual)[0].astype(int)
    is_dual_fuel = is_dual[gen_idx]
    return gen_idx, is_dual_fuel


def build_winter_fuel_budget(
    iso: str,
    fleet: FleetArrays,
    oil_switch_mask: np.ndarray | None,
    *,
    start_fill_bbl: float | None = None,
    mmbtu_per_bbl: float = MMBTU_PER_BBL_DISTILLATE,
    hours: int | None = None,
    eia860_dir: Path | None = None,
    clean_dir: Path | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """Build the winter (Nov-Mar) seasonal oil-burn budget LP inputs.

    Returns the tuple consumed by
    :func:`market_sim.model.dispatch._build_oil_budget_rows` via the
    ``oil_monthly_budget`` / ``oil_gen_idx`` / ``oil_month_index`` /
    ``oil_gen_hour_coeff`` / ``oil_group_index`` solve kwargs. One pooled fleet
    row per winter month enforces::

        sum_{g in oil fleet, t in winter month m} HR[g] * mask[g,t] * P[g,t]
            <= 0.6 * start_fill * mmbtu_per_bbl        (MMBtu)

    with ``mask`` all-ones for oil-primary units and the exogenous oil-switch
    mask for dual-fuel units. Non-winter months are unconstrained (``inf``).

    Args:
        iso: ISO identifier.
        fleet: Vectorized fleet arrays (``fuel_type_idx``, ``heat_rate``,
            ``plant_code``, ``plant_group``).
        oil_switch_mask: ``(n_gen, T)`` bool mask of dual-fuel generator-hours
            burning oil (from
            :func:`~market_sim.data.fuel.dual_fuel_switch_mask`), or ``None`` to
            treat every dual-fuel hour as oil-eligible (fallback; over-broad).
        start_fill_bbl: Start-of-winter fleet oil inventory (barrels). ``None``
            uses the study's WRP low target (2.8 M bbl).
        mmbtu_per_bbl: Heat content per barrel; distillate (No. 2) by default.
        hours: LP horizon (defaults to the fleet availability width, else 8760).
        eia860_dir: Optional EIA-860 vintage override.
        clean_dir: Optional clean-data root override (tests).

    Returns:
        ``(oil_gen_idx, budget_mmbtu, month_index, gen_hour_coeff,
        group_index)`` or ``None`` when the ISO has no study data or no
        oil-capable generators.
    """
    study = read_winter_fuel_study(iso, clean_dir=clean_dir)
    if study is None:
        return None
    fill_bbl = (
        study.start_fill_low_bbl if start_fill_bbl is None else float(start_fill_bbl)
    )

    gen_idx, is_dual_fuel = oil_capable_gen_idx(fleet, eia860_dir=eia860_dir)
    if gen_idx.size == 0:
        return None

    if hours is None:
        avail = getattr(fleet, "availability", None)
        hours = int(avail.shape[1]) if avail is not None and avail.ndim == 2 else 8760
    T = int(hours)
    month_index = _hour_to_month_index(T)

    # Per-(generator, hour) coefficient = heat rate (MMBtu/MWh), so HR * P is the
    # oil energy INPUT. Dual-fuel units are gated to their oil-switch hours only.
    hr = np.asarray(fleet.heat_rate, dtype=float)[gen_idx]
    hr = np.where(hr > 0, hr, 10.0)  # guard degenerate zero heat rates
    coeff = np.broadcast_to(hr[:, None], (gen_idx.size, T)).astype(float, copy=True)
    if is_dual_fuel.any():
        if oil_switch_mask is not None:
            mask = np.asarray(oil_switch_mask, dtype=bool)[gen_idx]
            # Oil-primary rows stay all-hours; dual-fuel rows keep only oil hours.
            keep = np.where(is_dual_fuel[:, None], mask, True)
            coeff = coeff * keep
        # oil_switch_mask None -> leave dual-fuel coeff all-hours (fallback).

    # Monthly MMBtu budget: opening tank amortized over the winter months plus
    # the re-supply spread uniformly (fills tank-fills/season, each one tank).
    fills = study.delivery_fills_per_season
    monthly_cap_bbl = fill_bbl * (1.0 + fills) / _N_WINTER_MONTHS
    monthly_cap_mmbtu = monthly_cap_bbl * mmbtu_per_bbl

    budget_mmbtu = np.full((1, 12), np.inf, dtype=float)
    for m in WINTER_MONTH_INDICES:
        budget_mmbtu[0, m] = monthly_cap_mmbtu

    # Single pooled fleet row (shared regional stock).
    group_index = np.zeros(gen_idx.size, dtype=int)

    return gen_idx, budget_mmbtu, month_index, coeff, group_index


# --- Component B: winter fuel-security must-run (seasonal-reliability commitment) ---
#
# Fuel-secure steam classes ISO-NE postures for winter energy security: coal and
# the oil-capable gas-steam fleet (the units that hold on-site distillate and can
# run when pipeline gas is short). This is the class scope the WRP/IEP/OFSA
# posture targets, and it is exactly the classes the disabled reliability-floor
# tmin cold limbs named (NEISO North COAL, Connecticut ST_GAS) — Component B
# re-grounds that phenomenon on the program posture rather than a thin-sample
# temperature correlation. Both coal taxonomy labels are included: the NEISO
# fleet tags its (bituminous) coal fleet "COAL" (plant_taxonomy fallback), while
# "COAL_BIT" is carried where the CAMPD coal-class resolver fires — Component B
# must floor the fuel-secure coal fleet whichever label it wears.
_WINTER_FUELSEC_CLASSES: tuple[str, ...] = ("COAL", "COAL_BIT", "ST_GAS")

# Steam commitment spans a multi-day cold event (a committed boiler is not cycled
# on the single coldest calendar day). Mirrors the reliability engine's steam
# ``min_event_hours`` (iso_configs._STEAM_MIN_EVENT_HOURS = 48).
_WINTER_FUELSEC_MIN_EVENT_HOURS: int = 48


def apply_winter_fuelsec_mustrun(
    fleet_arrays,
    iso: str,
    year: int,
    zone_names: list[str],
    *,
    plant_classes: tuple[str, ...] = _WINTER_FUELSEC_CLASSES,
    min_stable_pct: float = 0.40,
    commit_frac: float = 1.0,
    tmin_threshold_c: float = -7.0,
    min_event_hours: int = _WINTER_FUELSEC_MIN_EVENT_HOURS,
    hours: int | None = None,
) -> bool:
    """Apply the NEISO winter fuel-security must-run floor (Component B).

    The seasonal-reliability commitment coupled to the Component-A inventory
    budget. ISO-NE retains and postures its fuel-secure steam fleet (coal + the
    oil-capable gas-steam units that hold on-site distillate) through winter for
    energy security *beyond* pure energy economics — the Winter Reliability
    Program (FERC ER14-2407, 2013-2018), its Inventoried Energy Program successor
    (ER19-1428), and the OFSA-driven operational posture. The perfect-foresight
    energy-only LP lacks this: it commits these units only in the few hours
    delivered gas/oil is dear enough, so their winter energy under-runs
    (COAL_BIT/ST_GAS C1 miss) AND their oil draw never reaches the seasonal
    inventory budget, leaving Component A's cap inert (the neiso-inventorycap
    probe finding). This floor supplies the missing commitment: it postures the
    fuel-secure classes at minimum-stable on winter cold days, at which point the
    dual-fuel oil limb burns on the acute snaps and the Component-A budget can
    bind, producing the endogenous winter scarcity rent (C3c tail) and the wider
    storage spread (C5b) as a *consequence* of the commitment, not a tuned adder.

    Rule-17 statement:
      (a) DRIVER — ISO-NE winter fuel-security posture (WRP / IEP / OFSA); an
          external program, not a price/volume residual.
      (b) HOURS — winter months only (Nov-Mar, the OFSA horizon) AND cold days
          (zone daily ``tmin_c < tmin_threshold_c``, default -7 C / ~20 F, the
          NERC cold-weather forced-outage onset). All 24 h of a flagged cold day
          (a committed boiler runs the whole day); multi-day cold events bridged
          to ``min_event_hours``. Never binds outside winter or on mild winter
          days.
      (c) FORWARD — the season gate is calendar; the cold gate regenerates from a
          forecast year's pinned/forecast zone TMIN (colder winter -> more
          binding hours); the depth is a physical boiler-turndown constant. Every
          input is forward-derivable and responds to changed weather/fleet.

    Rule 19: REPLACES the disabled COAL/ST_GAS ``tmin`` cold-limb reliability
    floors (``reliability_floor_coeffs_NEISO.csv``, ``enabled=False`` since the
    2026-06-30 rebuild disabled them for thin cold-day sample, n=7-8). Those limbs
    modelled the same phenomenon (winter steam commitment) via a temperature->
    commitment correlation that could not be identified from the sparse cold-day
    record; Component B grounds it in the program posture instead. It is the
    single winter-steam-commitment mechanism — the tmin limbs stay disabled, not
    re-enabled alongside. ``floor_pct = commit_frac x min_stable_pct`` (a
    structural commitment share times the physical minimum-stable level), never a
    measured-CF ceiling and never tuned to the C1/C3c/C5b residual (rules 1/24).

    The floor composes into ``FleetArrays.min_gen`` cheapest-first via the shared
    :func:`~market_sim.model.transmission._distribute_group_floor` kernel and tags
    the raised unit-hours ``MECH_WINTER_FUELSEC`` for the D-2 forced-energy
    attribution (a merchant reliability commitment — subject to the forced-share
    gate, ablated in the zero-forcing twin).

    Args:
        fleet_arrays: Vectorized fleet arrays (mutated in place). Needs
            ``plant_group``, ``zone_idx``, ``pmax``, ``availability``,
            ``heat_rate``, ``pmin``.
        iso: ISO identifier (NEISO).
        year: Weather year for the pinned zone temperature series.
        zone_names: Ordered model-zone names (index-aligned with ``zone_idx``).
        plant_classes: Fuel-secure classes to floor (default COAL_BIT + ST_GAS).
        min_stable_pct: Physical minimum-stable fraction of a committed steam
            boiler (default 0.40 — standard subcritical steam turndown).
        commit_frac: Fraction of each class under the winter program posture
            (default 1.0 — the NEISO fuel-secure steam fleet IS the program
            fleet).
        tmin_threshold_c: Cold-day gate on zone daily TMIN (default -7 C, NERC
            cold-weather onset).
        min_event_hours: Steam multi-day event bridging (default 48 h).
        hours: LP horizon (defaults to the fleet availability width, else 8760).

    Returns:
        ``True`` iff at least one unit-hour was floored, ``False`` (byte-identical)
        otherwise — e.g. a warm winter with no day below the threshold, a forecast
        year with no pinned weather, or a fleet with no fuel-secure units.
    """
    if fleet_arrays.plant_group is None:
        return False
    # Lazy imports: match the harness pattern and avoid a module-load cycle
    # (transmission imports dispatch/fleet; eia_loader is heavy).
    from market_sim.data.eia_loader import iso_zone_tmax
    from market_sim.data.floor_mechanisms import MECH_WINTER_FUELSEC
    from market_sim.model.transmission import (
        _bridge_flagged_runs,
        _distribute_group_floor,
    )

    if hours is None:
        avail = getattr(fleet_arrays, "availability", None)
        hours = int(avail.shape[1]) if avail is not None and avail.ndim == 2 else 8760
    T = int(hours)

    groups = np.asarray(fleet_arrays.plant_group)
    zone_idx = np.asarray(fleet_arrays.zone_idx)
    pmax = np.asarray(fleet_arrays.pmax)

    # Winter-month gate (hour -> 0-based calendar month in WINTER_MONTH_INDICES).
    month_of_hour = _hour_to_month_index(T)
    is_winter_hour = np.isin(month_of_hour, WINTER_MONTH_INDICES)
    if not is_winter_hour.any():
        return False

    floor_pct = float(commit_frac) * float(min_stable_pct)
    if floor_pct <= 0.0:
        return False

    applied = False
    # Per-zone cold-day gate: a committed steam boiler is a zone-local decision,
    # so the cold flag keys off each zone's own daily TMIN (unlike the pooled oil
    # budget). Classes present only in some zones are floored where they exist.
    for z_idx, zone in enumerate(zone_names):
        temp_result = iso_zone_tmax(iso, year, T, zone=zone)
        if temp_result is None:
            continue  # import node / unmapped / forecast year with no pinned wx
        _tmax, tmin = temp_result
        if tmin is None:
            continue
        tmin = np.asarray(tmin, dtype=float)
        # Cold winter hours: below the NERC cold-onset AND inside the season.
        flagged = (tmin < float(tmin_threshold_c)) & is_winter_hour
        if not flagged.any():
            continue
        # Bridge multi-day cold events, then re-apply the season gate so a snap
        # straddling the Mar/Apr boundary cannot leak a floor into spring.
        flagged = _bridge_flagged_runs(flagged, int(min_event_hours)) & is_winter_hour
        frac = np.where(flagged, floor_pct, 0.0)
        for cls in plant_classes:
            sel = (groups == cls) & (zone_idx == z_idx) & (pmax > 0.0)
            rows = np.flatnonzero(sel)
            if rows.size == 0:
                continue
            if fleet_arrays.min_gen is None:
                fleet_arrays.min_gen = np.broadcast_to(
                    fleet_arrays.pmin[:, np.newaxis],
                    (fleet_arrays.pmin.size, T),
                ).copy()
            _distribute_group_floor(
                fleet_arrays, rows, frac, T, mech_id=MECH_WINTER_FUELSEC
            )
            applied = True
    return applied
