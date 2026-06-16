"""ERCOT ORDC scarcity-pricing overlay (post-solve price adder).

Replicates ERCOT's published Operating Reserve Demand Curve (ORDC)
real-time on-line reserve price adder (RTORPA) as a *post-solve* overlay on
the dispatch LP's energy-balance duals. The LP is untouched: volumes,
dispatch and emissions are identical with the overlay on or off. This
mirrors actual ERCOT price formation, where the adder is computed outside
SCED's dispatch optimization and added to the energy price afterwards
(Real-Time Settlement Point Price = LMP + RTORPA-based reserve price).

Published formula (ERCOT Other Binding Document "Methodology for
Implementing Operating Reserve Demand Curve (ORDC) to Calculate Real-Time
Reserve Price Adder", NPRR568, in force Jun 2014 - Dec 4 2025; restated in
the 2024 Biennial ERCOT Report on the ORDC):

    LOLP(R; mu, sigma)  = 1                                  if R <= X
                        = 1 - NormCDF(R - X; mu_eff, sigma)  if R >  X
    mu_eff              = mu + shift * sigma     (PUCT Project 48551 curve
                                                  shift: 2 x 0.25 sigma,
                                                  Mar 2019 / Mar 2020)
    RTORPA = 0.5 * (VOLL - lambda) * LOLP(R_online + R_offline; mu, sigma)
           + 0.5 * (VOLL - lambda) * LOLP(R_online; mu/2, sigma/sqrt(2))

where X is the minimum contingency level, the two terms are the two
30-minute halves of the operating hour (off-line 30-minute reserves only
help in the second half; the first-half curve carries half the reserve
uncertainty, hence mu/2 and sigma/sqrt(2)), and the total of lambda plus
adders is capped at VOLL (the system-wide offer cap). Since Nov 1 2023 a
multi-step floor applies to RTORPA (OBDRR048): >= $20/MWh at reserves
<= 6,500 MW, >= $10/MWh at 6,500-7,000 MW.

Model mapping (documented approximations, see docs/ordc-overlay.md):

* Reserves R = thermal available capacity (incl. outage overlay/derates)
  minus thermal dispatch, plus storage headroom (power cap - discharge +
  charge), minus ERCOT's ancillary-service plan (``ordc_as_plan_mw``). The
  AS netting stands in for capacity the real market withholds from energy
  but the energy-only LP dispatches freely.
* All netted reserves are treated as on-line (RTOFFCAP = 0): the LP has no
  commitment state, so the on-line/off-line split is unobservable. Both
  LOLP terms are evaluated at the same R, which *understates* the adder
  relative to a real split (the first-half term would see fewer reserves).
* lambda = the hourly demand-weighted system price (the LP's energy dual),
  the model analogue of ERCOT's system lambda.

Parameters (VOLL, X, sigma/mu, curve shift, floors, AS plan) are
ScenarioConfig fields with the published post-Uri values as defaults — a
PUCT cap change (e.g. pre-Uri $9,000 VOLL) is a runnable scenario, never a
code edit. Nothing here is fitted to price residuals.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.special import ndtr

from market_sim.config.constants import (
    ORDC_FLOOR_START_HOUR_2023,
    ORDC_FLOOR_STEPS,
)
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

# Fuel types whose headroom counts toward operating reserves. Renewables
# hold nothing back (their headroom is curtailment, not reserve), hydro is
# energy-budget-limited (552 MW in ERCOT — immaterial), imports and
# must-run injections are not dispatchable reserve.
RESERVE_FUEL_TYPES: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "coal", "nuclear", "oil"}
)

# ERCOT ORDC seasons (calendar quarters of the LOLP statistics): winter =
# Dec-Feb, spring = Mar-May, summer = Jun-Aug, fall = Sep-Nov.
_SEASON_OF_MONTH: tuple[str, ...] = (
    "winter", "winter", "spring", "spring", "spring", "summer",
    "summer", "summer", "fall", "fall", "fall", "winter",
)

# Non-leap dispatch calendar (matches market_sim.data.campd conventions).
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])


def _month_of_hour(hours: np.ndarray) -> np.ndarray:
    """Map non-leap hour-of-year indices to months 1-12."""
    return np.searchsorted(
        _MONTH_START_HOUR, hours, side="right").clip(1, 12)


def tod_block_of_hour(hours: np.ndarray) -> np.ndarray:
    """Return the ERCOT time-of-day block (1-6) for hour-of-year indices.

    The ORDC LOLP statistics partition each day into six 4-hour blocks
    (block 1 = hours beginning 00-03 local, ... block 6 = 20-23).
    """
    return (np.asarray(hours) % 24) // 4 + 1


def season_of_hour(hours: np.ndarray) -> np.ndarray:
    """Return the ORDC season name for hour-of-year indices."""
    months = _month_of_hour(np.asarray(hours))
    return np.array([_SEASON_OF_MONTH[m - 1] for m in months])


def load_lolp_params(
    path: str | Path, hours: int = 8760
) -> tuple[np.ndarray, np.ndarray]:
    """Resolve hourly (mu, sigma) arrays from a seasonal/TOD-block CSV.

    The CSV carries ERCOT's published LOLP normal-distribution statistics
    (NP6-576-ER "LOLP Distribution by Season and TOD Block") with columns
    ``season`` (winter/spring/summer/fall), ``tod_block`` (1-6), ``mu_mw``
    and ``sigma_mw``. Every (season, block) pair must be present.

    Returns:
        Tuple ``(mu, sigma)`` of ``(hours,)`` arrays in MW.
    """
    import pandas as pd

    df = pd.read_csv(path)
    need = {"season", "tod_block", "mu_mw", "sigma_mw"}
    if not need.issubset(df.columns):
        raise ValueError(
            f"LOLP params CSV {path} must have columns {sorted(need)}")
    key = {(str(r.season).lower(), int(r.tod_block)): (r.mu_mw, r.sigma_mw)
           for r in df.itertuples()}
    hour_idx = np.arange(hours)
    seasons = season_of_hour(hour_idx)
    blocks = tod_block_of_hour(hour_idx)
    missing = {(s, int(b)) for s, b in zip(seasons, blocks)} - set(key)
    if missing:
        raise ValueError(
            f"LOLP params CSV {path} missing (season, block) pairs: "
            f"{sorted(missing)}")
    mu = np.array([key[(s, int(b))][0] for s, b in zip(seasons, blocks)],
                  dtype=float)
    sigma = np.array([key[(s, int(b))][1] for s, b in zip(seasons, blocks)],
                     dtype=float)
    return mu, sigma


def lolp(
    reserves_mw: np.ndarray,
    mu_mw: np.ndarray | float,
    sigma_mw: np.ndarray | float,
    mcl_mw: float,
    shift_sigma: float = 0.0,
) -> np.ndarray:
    """Loss-of-load probability at each reserve level (published form).

    ``LOLP = 1 - NormCDF(R - X; mu + shift*sigma, sigma)`` for ``R > X``,
    administratively 1.0 at ``R <= X`` (the minimum contingency level).

    Args:
        reserves_mw: Hourly reserves R in MW.
        mu_mw: Reserve-error mean, scalar or hourly array.
        sigma_mw: Reserve-error standard deviation, scalar or hourly array.
        mcl_mw: Minimum contingency level X in MW.
        shift_sigma: PUCT-ordered rightward curve shift in units of sigma
            (0.5 since March 2020; 0.0 reproduces the pre-2019 curve).

    Returns:
        ``(T,)`` array of probabilities in [0, 1].
    """
    r = np.asarray(reserves_mw, dtype=float)
    mu_eff = np.asarray(mu_mw, dtype=float) + shift_sigma * np.asarray(
        sigma_mw, dtype=float)
    sigma = np.broadcast_to(np.asarray(sigma_mw, dtype=float), r.shape)
    z = (r - mcl_mw - mu_eff) / np.where(sigma > 0, sigma, 1.0)
    out = 1.0 - ndtr(z)
    return np.where(r <= mcl_mw, 1.0, out)


def ordc_adder(
    reserves_mw: np.ndarray,
    system_lambda: np.ndarray,
    *,
    voll: float,
    mcl_mw: float,
    mu_mw: np.ndarray | float,
    sigma_mw: np.ndarray | float,
    shift_sigma: float = 0.5,
    multistep_floor: bool = True,
    floor_active: np.ndarray | bool = True,
) -> np.ndarray:
    """Hourly ORDC price adder ($/MWh) for a reserve and price series.

    Implements RTORPA with the model's whole netted headroom treated as
    on-line reserves (RTOFFCAP = 0, see module docstring): two half-hour
    LOLP terms — the full-hour curve (mu, sigma) and the first-half curve
    (mu/2, sigma/sqrt(2)) — each weighted 0.5 and multiplied by
    ``max(VOLL - lambda, 0)``. The OBDRR048 multi-step floor is applied
    where ``floor_active``, then the total is capped so lambda + adder
    never exceeds VOLL.

    Args:
        reserves_mw: Hourly netted reserves in MW.
        system_lambda: Hourly system energy price in $/MWh.
        voll: Value of lost load / system-wide offer cap in $/MWh.
        mcl_mw: Minimum contingency level in MW.
        mu_mw: Reserve-error mean (scalar or hourly), MW.
        sigma_mw: Reserve-error standard deviation (scalar or hourly), MW.
        shift_sigma: LOLP curve shift in sigma units (see :func:`lolp`).
        multistep_floor: Apply the OBDRR048 RTORPA floor steps.
        floor_active: Boolean or hourly mask gating the floor (it took
            effect 2023-11-01; pass a mask for 2023 backcasts).

    Returns:
        ``(T,)`` adder array in $/MWh, >= 0.
    """
    lam = np.asarray(system_lambda, dtype=float)
    headroom_to_cap = np.maximum(voll - lam, 0.0)

    mu = np.asarray(mu_mw, dtype=float)
    sigma = np.asarray(sigma_mw, dtype=float)
    lolp_full = lolp(reserves_mw, mu, sigma, mcl_mw, shift_sigma)
    lolp_half = lolp(
        reserves_mw, mu / 2.0, sigma / np.sqrt(2.0), mcl_mw, shift_sigma)
    adder = 0.5 * headroom_to_cap * (lolp_full + lolp_half)

    if multistep_floor:
        floor = np.zeros_like(adder)
        r = np.asarray(reserves_mw, dtype=float)
        # Steps are (threshold, floor) sorted descending so the tightest
        # (lowest-reserve) step wins.
        for threshold, value in sorted(ORDC_FLOOR_STEPS, reverse=True):
            floor = np.where(r <= threshold, value, floor)
        adder = np.maximum(adder, np.where(floor_active, floor, 0.0))

    # Protocol cap: lambda + adders <= VOLL (the system-wide offer cap).
    return np.minimum(adder, headroom_to_cap)


def floor_active_mask(year: int, hours: int) -> np.ndarray:
    """Hourly mask for the OBDRR048 floor's 2023-11-01 effective date."""
    hour_idx = np.arange(hours)
    if year > 2023:
        return np.ones(hours, dtype=bool)
    if year < 2023:
        return np.zeros(hours, dtype=bool)
    return hour_idx >= ORDC_FLOOR_START_HOUR_2023


def reserve_headroom(
    fleet_arrays: FleetArrays,
    dispatch: np.ndarray,
    storage_power_cap: np.ndarray,
    storage_charge: np.ndarray | None,
    storage_discharge: np.ndarray | None,
    as_plan_mw: float,
    renewable_headroom: np.ndarray | None = None,
) -> np.ndarray:
    """Hourly netted reserve headroom (MW) from solved-dispatch arrays.

    ``R = sum_thermal(pmax x availability - dispatch) + storage headroom
    + renewable curtailment headroom - AS plan``. Storage headroom follows
    ERCOT's ESR telemetry convention (capability minus net output): power
    cap - discharge + charge. Curtailed renewables count (ERCOT telemetry
    is HSL - output); in real scarcity hours renewables run at potential,
    so the term is ~0 exactly where the adder matters.

    Args:
        fleet_arrays: The fleet the LP solved against (availability incl.
            the outage overlay and derates).
        dispatch: ``(n_gen, T)`` solved generation in MW.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` MW caps.
        storage_charge: ``(n_storage, T)`` charge MW (``None`` = none).
        storage_discharge: ``(n_storage, T)`` discharge MW.
        as_plan_mw: Ancillary-service plan netting in MW.
        renewable_headroom: Optional ``(T,)`` curtailed wind+solar MW
            (potential cf x cap minus dispatched).

    Returns:
        ``(T,)`` reserves array in MW (may go negative under deep
        scarcity; the LOLP pins to 1 below the MCL regardless).
    """
    fuel_names = np.array(
        [FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    thermal = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    avail = (
        fleet_arrays.pmax[thermal, None] * fleet_arrays.availability[thermal]
    ).sum(axis=0)
    served = np.asarray(dispatch, dtype=float)[thermal].sum(axis=0)

    cap = np.asarray(storage_power_cap, dtype=float)
    storage_headroom = (
        cap.sum(axis=0) if cap.ndim == 2
        else np.full(avail.shape, cap.sum())
    )
    if storage_discharge is not None and np.size(storage_discharge):
        storage_headroom = (
            storage_headroom
            - np.asarray(storage_discharge, dtype=float).sum(axis=0)
            + np.asarray(storage_charge, dtype=float).sum(axis=0)
        )
    reserves = avail - served + storage_headroom - as_plan_mw
    if renewable_headroom is not None:
        reserves = reserves + np.asarray(renewable_headroom, dtype=float)
    return reserves


def resolve_lolp_params(
    config, hours: int
) -> tuple[np.ndarray | float, np.ndarray | float]:
    """Return (mu, sigma) for the config: seasonal CSV when set, else flat."""
    if getattr(config, "ordc_lolp_params_path", None):
        return load_lolp_params(config.ordc_lolp_params_path, hours)
    return config.ordc_lolp_mu_mw, config.ordc_lolp_sigma_mw


# RTC+B (Real-Time Co-optimization + Batteries) replaced ERCOT's ORDC reserve
# price adders with co-optimized AS demand curves at go-live on 2025-12-05, so
# years from 2026 are RTC+B; 2023-2025 are the ORDC + RTORDPA design.
_RTCB_FIRST_FULL_YEAR: int = 2026


def ercot_market_regime(year: int, config) -> str:
    """Return the ERCOT scarcity-pricing regime for a year: 'ordc' or 'rtcb'.

    Honors an explicit ``config.ercot_market_design`` of ``"ordc"`` / ``"rtcb"``;
    ``"auto"`` (default) is year-gated at the RTC+B go-live (ORDC through 2025,
    RTC+B from 2026). This is what keeps the erroneous 2023 reserve-withholding
    conservatism contained to the design that actually produced it, rather than
    carried into the forward design.
    """
    design = getattr(config, "ercot_market_design", "auto")
    if design == "ordc":
        return "ordc"
    if design == "rtcb":
        return "rtcb"
    if design != "auto":
        raise ValueError(
            f"ercot_market_design must be 'auto', 'ordc' or 'rtcb', "
            f"got {design!r}")
    return "ordc" if year < _RTCB_FIRST_FULL_YEAR else "rtcb"


def effective_reliability_deployment_mw(year: int, config) -> float:
    """Return the reliability-deployment reserve offset (MW) for the regime.

    The RTORDPA analogue applies under the ORDC regime
    (``ordc_reliability_deployment_mw`` — calibrated to the 2023 stress year);
    under RTC+B the conservatism was reformed, so the forward offset is
    ``rtcb_reliability_deployment_mw`` (default 0 — price to fundamentals),
    which a scenario can raise to model 2023-style conservatism recurring.
    """
    if ercot_market_regime(year, config) == "ordc":
        return float(getattr(config, "ordc_reliability_deployment_mw", 0.0))
    return float(getattr(config, "rtcb_reliability_deployment_mw", 0.0))


def scarcity_prices(
    config,
    year: int,
    reserves_mw: np.ndarray,
    system_lambda: np.ndarray,
) -> dict[str, np.ndarray]:
    """Convenience wrapper: hourly LOLP + adder for a config and year.

    Returns a dict with ``reserves_mw``, ``lolp`` (full-hour curve) and
    ``scarcity_adder`` arrays. The caller adds the adder to its price
    series (every zone sees the same system-wide adder, matching ERCOT,
    where the reserve price adder is a system-level component of every
    settlement point price).
    """
    hours = len(np.asarray(reserves_mw))
    mu, sigma = resolve_lolp_params(config, hours)
    adder = ordc_adder(
        reserves_mw, system_lambda,
        voll=config.ordc_voll,
        mcl_mw=config.ordc_mcl_mw,
        mu_mw=mu, sigma_mw=sigma,
        shift_sigma=config.ordc_lolp_shift_sigma,
        multistep_floor=config.ordc_multistep_floor,
        floor_active=(
            floor_active_mask(year, hours) if config.mode == "backcast"
            else True
        ),
    )
    return {
        "reserves_mw": np.asarray(reserves_mw, dtype=float),
        "lolp": lolp(
            reserves_mw, mu, sigma, config.ordc_mcl_mw,
            config.ordc_lolp_shift_sigma),
        "scarcity_adder": adder,
    }


# ===========================================================================
# PJM stepped ORDC reserve-scarcity overlay
# ===========================================================================
#
# PJM's scarcity mechanism is structurally different from ERCOT's smooth LOLP.
# PJM co-optimizes energy and three nested reserve products against *vertical
# step* Operating Reserve Demand Curves (Manual 11 sec 4.3.3), established by
# the Reserve Price Formation reform (FERC EL19-58/ER19-1486, order 2020-05-21,
# implemented 2022-10-01). Each product/zone curve is two steps:
#
#     reserves R, requirement REQ:
#       R <  REQ           -> $850/MWh   (Step 1)
#       REQ <= R < REQ+190 -> $300/MWh   (Step 2)
#       R >= REQ+190       ->   $0       (no shortage)
#
# The penalty factor enters the energy LMP because energy and reserves are
# co-optimized: relieving the reserve constraint by backing down a marginal
# energy unit transfers the constraint's shadow price into the price of energy.
# Parameters live in inputs/calibration/pjm_ordc_curve.csv (cited in
# docs/multi-iso/pjm-reserve-curve-source.md); nothing here is fitted to a
# price residual.
#
# HONESTY GATE (see docs/multi-iso/pjm-reserve-ordc.md). The step is vertical,
# so the adder is *exactly $0* unless measured reserves drop below REQ+190
# (~3.2 GW). On TOTAL fleet headroom the perfect-foresight LP carries ~39 GW and
# never goes short; on per-tranche online headroom it carries ~0 (the LP runs
# each tranche bang-bang). The only defensible measure is PLANT-LEVEL online
# (synchronized) reserve — a plant is synchronized when any of its tranches
# dispatch, and its reserve is the unused headroom across all its tranches. Even
# that sits ~5x above the requirement (~16 GW vs ~3 GW) in the hours reality was
# short, so the published curve bites in only a handful of hours/yr and cannot
# self-target the $75-200 afternoon residual. That residual is the sub-shortage
# *opportunity-cost* reserve price (the marginal unit's lost energy margin) plus
# congestion, which is the AS co-optimization this overlay — like the ERCOT one
# — explicitly does not attempt. We report the gate result; we do not fudge the
# curve or the reserve measure to manufacture scarcity (claude.md #11).

# Cascade weights: how each published reserve-product clearing price sums the
# nested requirement shadow prices (Manual 11 sec 4.4.1). Keys are the data
# `service` codes in reserve_market_results_*.parquet.
PJM_RESERVE_CASCADE: dict[str, tuple[str, ...]] = {
    "SR": ("Synchronized", "Primary", "Secondary"),   # SRMCP  = SP_SR+SP_PR+SP_30
    "PR": ("Primary", "Secondary"),                    # NSRMCP =       SP_PR+SP_30
    "30MIN": ("Secondary",),                           # SecMCP =             SP_30
}


def load_pjm_ordc_curve(
    path: str | Path,
) -> dict[tuple[str, str], list[tuple[float, float]]]:
    """Load the cited PJM ORDC step curve keyed by (service, locale).

    Reads inputs/calibration/pjm_ordc_curve.csv (columns ``service``,
    ``locale``, ``step``, ``breakpoint_offset_mw``, ``penalty_factor``) and
    returns, per (service, locale), the step list ``[(offset_mw, penalty), ...]``
    sorted by ascending offset. ``offset_mw`` is measured from the reserve
    requirement (so the requirement itself supplies the X-axis position).

    Returns:
        Mapping ``(service, locale) -> [(offset_mw, penalty_factor), ...]``.
    """
    import pandas as pd

    df = pd.read_csv(path, comment="#")
    need = {"service", "locale", "breakpoint_offset_mw", "penalty_factor"}
    if not need.issubset(df.columns):
        raise ValueError(
            f"PJM ORDC curve {path} must have columns {sorted(need)}")
    out: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for (svc, loc), grp in df.groupby(["service", "locale"]):
        steps = sorted(
            (float(r.breakpoint_offset_mw), float(r.penalty_factor))
            for r in grp.itertuples())
        out[(str(svc), str(loc))] = steps
    return out


def pjm_reserve_demand_price(
    reserves_mw: np.ndarray | float,
    requirement_mw: np.ndarray | float,
    ordc_steps: list[tuple[float, float]],
) -> np.ndarray:
    """Shadow price ($/MWh) of one PJM reserve requirement, stepped curve.

    PJM's reserve demand curve is a descending step function of cleared
    reserves: at reserves below the requirement the top penalty factor applies;
    each subsequent step (requirement + offset) lowers the price; beyond the
    last breakpoint the price is $0 (Manual 11 sec 4.3.3). This is the marginal
    value of the reserve constraint — what is added to the co-optimized energy
    price when the constraint binds.

    Args:
        reserves_mw: Cleared/available reserves R, scalar or hourly array (MW).
        requirement_mw: Reserve Requirement REQ, scalar or hourly array (MW).
        ordc_steps: ``[(offset_mw, penalty_factor), ...]`` from
            :func:`load_pjm_ordc_curve`, e.g. ``[(0, 850), (190, 300)]``.

    Returns:
        Step price array ($/MWh), >= 0, broadcast over reserves/requirement.
    """
    r = np.asarray(reserves_mw, dtype=float)
    req = np.asarray(requirement_mw, dtype=float)
    price = np.zeros(np.broadcast(r, req).shape, dtype=float)
    # Apply widest offset first so the tightest (lowest-offset, highest-penalty)
    # binding step wins — mirrors the ERCOT floor-step logic.
    for offset, penalty in sorted(ordc_steps, reverse=True):
        price = np.where(r < req + offset, penalty, price)
    return price


def pjm_reserve_cascade_mcp(
    reserves_by_product: dict[str, np.ndarray],
    requirements_by_product: dict[str, np.ndarray],
    curve_by_product: dict[str, list[tuple[float, float]]],
) -> dict[str, np.ndarray]:
    """Cascaded PJM reserve clearing prices from nested requirement shadows.

    Computes each product's step shadow price ``SP_x`` with
    :func:`pjm_reserve_demand_price`, then sums them per the product/locational
    substitution cascade (Manual 11 sec 4.4.1, :data:`PJM_RESERVE_CASCADE`):
    Synchronized clears against SR+PR+30, Primary (non-sync) against PR+30,
    Secondary against 30 only.

    Args:
        reserves_by_product: ``{"Synchronized": R_sr, "Primary": R_pr,
            "Secondary": R_30}`` hourly reserve arrays (MW).
        requirements_by_product: same keys, hourly requirement arrays (MW).
        curve_by_product: same keys, each a step list ``[(offset, penalty)]``.

    Returns:
        ``{"SR": SRMCP, "PR": NSRMCP, "30MIN": SecRMCP, "energy_adder": ...}``
        in $/MWh. ``energy_adder`` is the binding reserve price transferred to
        the energy LMP — the richest (Synchronized) cascade, i.e. ``SR``.
    """
    sp = {
        prod: pjm_reserve_demand_price(
            reserves_by_product[prod], requirements_by_product[prod],
            curve_by_product[prod])
        for prod in ("Synchronized", "Primary", "Secondary")
    }
    out: dict[str, np.ndarray] = {}
    for service, products in PJM_RESERVE_CASCADE.items():
        out[service] = sum(sp[p] for p in products)
    # The energy LMP picks up the binding reserve shadow price; the synchronized
    # cascade is the most complete (it includes every nested constraint that a
    # marginal online MW could relieve).
    out["energy_adder"] = out["SR"]
    return out


def pjm_online_reserve(
    avail_mw: np.ndarray,
    dispatch_mw: np.ndarray,
    plant_id: np.ndarray,
    thermal_mask: np.ndarray,
    as_plan_mw: np.ndarray | float = 0.0,
) -> np.ndarray:
    """Plant-level online (synchronized-basis) thermal reserve, MW.

    The PJM analogue of the ERCOT online-reserve primitive. A plant is
    *synchronized* in an hour when any of its thermal tranches dispatch; its
    reserve is the unused headroom summed across all that plant's thermal
    tranches (``pmax*availability - dispatch``). Headroom MUST be aggregated at
    the plant, not the tranche: the binned LP runs each tranche bang-bang, so
    per-tranche online headroom is ~0 and would falsely price every hour. Only
    the headroom of *online* plants counts (an idle plant's capacity is not
    synchronized and cannot meet a 10-/30-minute reserve in PJM's clearing).
    The PJM ancillary-service plan (the reserve MW the market withholds from
    energy) is netted off, mirroring the ERCOT AS-withholding primitive.

    Args:
        avail_mw: ``(n_unit, T)`` available MW (pmax × availability).
        dispatch_mw: ``(n_unit, T)`` solved dispatch MW.
        plant_id: ``(n_unit,)`` plant identifier shared by a plant's tranches.
        thermal_mask: ``(n_unit,)`` bool, reserve-providing thermal units.
        as_plan_mw: scalar or ``(T,)`` AS-plan netting (MW).

    Returns:
        ``(T,)`` plant-level online thermal reserve (MW), >= 0 before netting.
    """
    avail = np.asarray(avail_mw, dtype=float)[thermal_mask]
    disp = np.asarray(dispatch_mw, dtype=float)[thermal_mask]
    pid = np.asarray(plant_id)[thermal_mask]
    T = avail.shape[1]

    # Group tranches by plant: codes -> dense indices for np.add.at.
    codes, inv = np.unique(pid, return_inverse=True)
    plant_avail = np.zeros((len(codes), T))
    plant_disp = np.zeros((len(codes), T))
    np.add.at(plant_avail, inv, avail)
    np.add.at(plant_disp, inv, disp)

    online = plant_disp > 0.5  # plant synchronized this hour
    reserve = np.where(online, plant_avail - plant_disp, 0.0).sum(axis=0)
    return reserve - np.asarray(as_plan_mw, dtype=float)
