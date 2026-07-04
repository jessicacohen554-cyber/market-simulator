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
