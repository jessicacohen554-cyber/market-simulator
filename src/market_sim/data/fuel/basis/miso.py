"""MISO zonal gas basis + the winter Chicago-citygate daily shape overlay.

Split out of ``data/fuel.py`` (W-D3; refactor-consolidation plan §5 item 3) as
pure code motion. Rule 25: MISO's measured per-zone basis rows live in
``miso_zonal_gas_hub.csv`` and apply only under ``config.miso_zonal_gas_basis``
+ ``config.iso == "MISO"``. ``_miso_citygate_daily_dated`` is resolved through
the package namespace at call time (:func:`.._shared._pkg_ns`) because tests
patch it on the facade.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FleetArrays

from .._shared import (
    _DAYS_IN_MONTH,
    _GAS_FUEL_IDX,
    _GAS_PRICE_FLOOR,
    _month_index,
    _pkg_ns,
    logger,
)
from ..hubs import _flow_date_staircase, gas_daily_shape_factors
from .meanzero import (
    MISO_ZONAL_GAS_HUB_PATH,
    _apply_meanzero_zonal_gas_basis,
    _load_zonal_gas_hub,
    _zonal_gas_basis_by_zone,
)


def miso_zonal_gas_basis_by_zone(
    year: int, path: Path | None = None
) -> dict[str, float] | None:
    """Return ``{zone: basis vs Henry Hub ($/MMBtu)}`` for MISO, or None.

    Same format and semantics as :func:`pjm_zonal_gas_basis_by_zone` but reads
    :data:`MISO_ZONAL_GAS_HUB_PATH`.
    """
    return _zonal_gas_basis_by_zone(
        Path(path) if path else MISO_ZONAL_GAS_HUB_PATH, year
    )


def apply_miso_zonal_gas_basis(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
) -> None:
    """Shift each MISO gas unit's price by its zone's measured regional gas basis.

    Delegates to :func:`_apply_meanzero_zonal_gas_basis` — the same
    capacity-weighted mean-zero core used by PJM. MISO-West/MISO-Plains sit
    on MidCon / Northern Natural (IA), the eastern Midwest zones (Illinois/
    Indiana/East) on Chicago Citygate (IL),
    and MISO-South on Gulf Coast (LA); the spread opens while the
    fleet-aggregate gas level is preserved.

    Gated on ``config.miso_zonal_gas_basis`` and ``config.iso == "MISO"``.
    Default-off; the calibration harness enables it for MISO.
    """
    _apply_meanzero_zonal_gas_basis(
        fuel_prices,
        fleet,
        config,
        year,
        iso="MISO",
        config_field="miso_zonal_gas_basis",
        hub_path=MISO_ZONAL_GAS_HUB_PATH,
        path_override=Path(path) if path else None,
    )


# MISO winter fuel-security season: the pipeline-scarcity heating months in which
# the Chicago Citygate daily overlay supersedes the national Henry-Hub gas_daily_
# shape. The meteorological-winter convention (Dec/Jan/Feb); every measured MISO
# 2023-2025 winter gas event (Heather Jan-2024, the Jan-17-2025 / Feb-18-19-2025
# cold snaps) falls inside it. A structural scope, not a fitted knob (miso-72
# design §3.4).
_MISO_WINTER_MONTHS: tuple[int, ...] = (12, 1, 2)


def _miso_chicago_hub_zones(year: int, path: Path | None = None) -> set[str]:
    """Return the MISO zone names the published hub table maps to Chicago Citygate.

    Reads the SAME ``miso_zonal_gas_hub.csv`` (:data:`MISO_ZONAL_GAS_HUB_PATH`)
    :func:`apply_miso_zonal_gas_basis` uses and selects the zones whose ``hub``
    column names the Chicago Citygate (the eastern-Midwest zones MISO-Illinois /
    MISO-Indiana / MISO-East). This is the identification source for which zones
    the winter Chicago daily shape applies to — no new magic mapping (rule 5). An
    absent file or year, or a table without the ``hub`` column, yields an empty
    set (the overlay stays inert).
    """
    frame = _load_zonal_gas_hub(Path(path) if path else MISO_ZONAL_GAS_HUB_PATH)
    if frame is None or "hub" not in frame.columns:
        return set()
    sub = frame[frame["year"] == year]
    return {
        str(r.zone)
        for r in sub.itertuples()
        if str(r.hub).strip().lower().startswith("chicago")
    }


def miso_chicago_daily_shape_factors(
    year: int, hours: int, path: Path | None = None
) -> np.ndarray:
    """Return ``(hours,)`` within-month Chicago Citygate daily gas-price shape.

    The MISO analogue of :func:`gas_daily_shape_factors`, built from the measured
    Chicago Citygate daily spot (:func:`_miso_citygate_daily_dated`) placed on its
    gas **FLOW** days (trade + 1, weekend/holiday packages forward-filled —
    :func:`_flow_date_staircase`, the caiso-90 precedent), then renormalized so the
    calendar-day factors average to EXACTLY 1.0 within every month. Multiplying a
    (correctly-levelled) monthly gas series by these adds the real regional
    cold-snap swing while leaving the monthly mean — and hence the annual burn and
    mix — unchanged.

    Flow-date placement is REQUIRED, not cosmetic: the daily citygate is a
    next-day-delivery index, so the Winter Storm Heather Friday 2024-01-12 print
    ($25.82/MMBtu) prices the whole Sat-Mon-holiday weekend package — gas flowing
    Jan-13/14/15/16, including the record-peak Tuesday. The pre-§3.7-fix
    even-spread resampling in :func:`gas_daily_shape_factors` instead mislocated
    it to Jan-13 and dropped the true tail days to 0.88-0.96×; the flow-date
    staircase lands it on Jan-13-16 at 4.67× (verified monthly-mean factor
    1.000). (The national Henry Hub shape now uses the TRADE-date staircase —
    :func:`_trade_date_staircase` — because the HH daily spot prints the price
    of its own trading day, unlike this next-day-delivery citygate index.)
    Returns all-ones for a year with no Chicago quotes (the caller stays inert).
    """
    factors = np.ones(hours, dtype=float)
    dated = _pkg_ns()._miso_citygate_daily_dated(path).get(year, {})
    if not dated:
        return factors
    flow = _flow_date_staircase(dated, year)  # 365-day flow-date staircase
    if flow is None:
        return factors
    hour = 0
    day0 = 0  # cumulative day-of-year offset of month m on the non-leap clock
    for _m, n_days in enumerate(_DAYS_IN_MONTH):
        if hour >= hours:
            break
        seg = flow[day0 : day0 + n_days]
        mean = float(seg.mean())
        if mean > 0:
            f = seg / mean
            fbar = float(f.mean())
            if fbar > 0:
                f = f / fbar  # renormalize: mean-preserving within the month
            rep = np.repeat(f, 24)[: max(0, hours - hour)]
            factors[hour : hour + len(rep)] = rep
        hour += n_days * 24
        day0 += n_days
    return factors


def apply_miso_winter_citygate_daily(
    fuel_prices: np.ndarray,
    fleet: FleetArrays,
    config: ScenarioConfig,
    year: int,
    path: Path | None = None,
    citygate_path: Path | None = None,
) -> None:
    """Reprice MISO Chicago-hub gas units at the measured Chicago winter daily shape.

    The miso-72 winter fuel-security overlay (design
    ``docs/handoffs/miso-winter-fuel-security-design-2026-07.md``). In the winter
    months (:data:`_MISO_WINTER_MONTHS`, Dec/Jan/Feb) only, for the MISO gas units
    in the Chicago-hub zones only (:func:`_miso_chicago_hub_zones`), it **replaces
    the national Henry-Hub ``gas_daily_shape`` within-month daily shape with the
    measured Chicago Citygate daily shape** (:func:`miso_chicago_daily_shape_factors`,
    flow-date-placed and mean-preserving). Every other cell — non-winter months,
    non-Chicago zones (MISO-West/Plains on MidCon, MISO-South on Gulf), the
    off-state — is byte-identical.

    This runs in :func:`resolve_fuel_prices` **immediately before**
    :func:`apply_miso_zonal_gas_basis`, so each Chicago-hub gas row is still
    ``level × national_shape`` (the additive mean-zero zonal spread not yet
    applied). The correction ``chicago_shape / national_shape`` divides out the
    national shape and multiplies in the Chicago shape — leaving ``level ×
    chicago_shape``, mean-preserving within month (the monthly gas level, and hence
    the already-correct monthly LMP, unchanged). The subsequent zonal-basis pass
    then adds its annual per-zone spread un-shaped, and dual-fuel oil parity
    (:func:`apply_dual_fuel_pricing`) still caps any winter blowout (rule 14).

    Rule-19 reconciliation (supersede, never stack): the national ``gas_daily_shape``
    is REPLACED for the Chicago-zone winter cells (not added to); the mean-zero
    ``miso_zonal_gas_basis`` spread is orthogonal (spatial/annual vs temporal/
    mean-1) and unperturbed because this overlay preserves every zone's annual mean.

    Gated on ``config.miso_winter_citygate_daily`` (tier 3, off by default) and
    ``config.iso == "MISO"``; zero fitted scalars (the measured daily series + the
    published Chicago-zone assignment). Backcast-only by construction (no forward
    Chicago daily rows). Mutates ``fuel_prices`` in place; idempotent.

    Args:
        fuel_prices: The ``(n_gen, T)`` delivered fuel-price array, updated in
            place for Chicago-hub gas generators in winter months.
        fleet: Vectorized fleet attributes; ``fuel_type_idx`` selects gas,
            ``zone_idx`` selects the Chicago-hub zones.
        config: Scenario configuration supplying ``miso_winter_citygate_daily``,
            ``gas_daily_shape``, ``iso`` and ``hours``.
        year: Calendar year keying the Chicago daily series and zone assignment.
        path: Optional override for the MISO zonal-hub CSV (zone selector).
        citygate_path: Optional override for the Chicago daily CSV.
    """
    if not getattr(config, "miso_winter_citygate_daily", False):
        return
    if config.iso.upper() != "MISO":
        return
    T = fuel_prices.shape[1]
    chicago = miso_chicago_daily_shape_factors(year, T, citygate_path)
    if not np.any(chicago != 1.0):
        return  # no Chicago daily quotes this year: inert (R4)
    national = (
        gas_daily_shape_factors(year, T)
        if getattr(config, "gas_daily_shape", False)
        else np.ones(T, dtype=float)
    )
    # Winter months only (the pipeline-scarcity heating season): swap the national
    # HH daily shape for the measured Chicago daily shape. Safe divide (national is
    # strictly positive shape factors; guard anyway).
    month0 = _month_index(T)  # 0-based month per hour
    winter = np.isin(month0, [m - 1 for m in _MISO_WINTER_MONTHS])
    correction = np.ones(T, dtype=float)
    valid = winter & (national > 0)
    correction[valid] = chicago[valid] / national[valid]
    if not np.any(correction != 1.0):
        return

    from market_sim.config.iso_configs import get_iso_config

    zone_names = get_iso_config(config.iso).zone_names
    chicago_zones = _miso_chicago_hub_zones(year, path)
    if not chicago_zones:
        return
    zone_is_chicago = np.array([zn in chicago_zones for zn in zone_names], dtype=bool)
    gas_rows = np.nonzero(np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX))[0]
    if gas_rows.size == 0:
        return
    sel = gas_rows[zone_is_chicago[fleet.zone_idx[gas_rows]]]
    if sel.size == 0:
        return
    fuel_prices[sel, :] = np.maximum(
        fuel_prices[sel, :] * correction[np.newaxis, :], _GAS_PRICE_FLOOR
    )
    logger.info(
        "MISO winter citygate daily (%d): %d Chicago-hub gas units (zones %s) "
        "repriced at the measured Chicago daily shape in %d winter days; "
        "correction %.2f..%.2f (winter peak on the cold-snap flow days)",
        year,
        sel.size,
        ",".join(sorted(chicago_zones)),
        int(np.unique(np.nonzero(correction != 1.0)[0] // 24).size),
        float(correction.min()),
        float(correction.max()),
    )
