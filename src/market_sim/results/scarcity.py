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
    PJM_PRIMARY_RESERVE_LSC_FACTOR,
)
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

# Fuel types whose headroom counts toward operating reserves. Renewables
# hold nothing back (their headroom is curtailment, not reserve), hydro is
# energy-budget-limited (552 MW in ERCOT — immaterial), imports and
# must-run injections are not dispatchable reserve.
RESERVE_FUEL_TYPES: frozenset[str] = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "coal", "nuclear", "oil"}
)

# Quick-start subset of the reserve fleet: units that can synchronize and reach
# output within ERCOT's 30-minute non-spin window from cold (simple-cycle gas
# turbines and oil peakers, ~10-30 min start). When OFFLINE these still back the
# *off-line* (second-half) ORDC reserve term. A cold slow-start unit (coal,
# combined-cycle, gas/CHP steam, nuclear — hours to start) backs NEITHER term:
# the perfect-foresight LP otherwise counts its idle capacity as responsive
# reserve, the documented overstatement that drove the fitted RTORDPA offset
# (docs/ercot-backcast-audit-2026-06 B3/B5a).
QUICK_START_FUEL_TYPES: frozenset[str] = frozenset({"gas_ct", "oil"})

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
    reserves_online_mw: np.ndarray | None = None,
) -> np.ndarray:
    """Hourly ORDC price adder ($/MWh) for a reserve and price series.

    Implements RTORPA's two half-hour LOLP terms — the full-hour curve
    ``LOLP(R_online + R_offline; mu, sigma)`` and the first-half curve
    ``LOLP(R_online; mu/2, sigma/sqrt(2))`` (off-line 30-minute reserve only
    helps the second half) — each weighted 0.5 and multiplied by
    ``max(VOLL - lambda, 0)``. ``reserves_mw`` is the full-hour reserve
    (online + offline); ``reserves_online_mw`` is the online (spinning) tier
    that backs the first half. When ``reserves_online_mw`` is ``None`` both
    terms use ``reserves_mw`` (the legacy RTOFFCAP = 0 behaviour). The OBDRR048
    multi-step floor is keyed to the online reserve (ERCOT's physical
    responsive capability) where ``floor_active``, then the total is capped so
    lambda + adder never exceeds VOLL.

    Args:
        reserves_mw: Hourly full-hour reserves (online + offline) in MW.
        system_lambda: Hourly system energy price in $/MWh.
        voll: Value of lost load / system-wide offer cap in $/MWh.
        mcl_mw: Minimum contingency level in MW.
        mu_mw: Reserve-error mean (scalar or hourly), MW.
        sigma_mw: Reserve-error standard deviation (scalar or hourly), MW.
        shift_sigma: LOLP curve shift in sigma units (see :func:`lolp`).
        multistep_floor: Apply the OBDRR048 RTORPA floor steps.
        floor_active: Boolean or hourly mask gating the floor (it took
            effect 2023-11-01; pass a mask for 2023 backcasts).
        reserves_online_mw: Hourly online (spinning) reserves in MW; defaults
            to ``reserves_mw``.

    Returns:
        ``(T,)`` adder array in $/MWh, >= 0.
    """
    lam = np.asarray(system_lambda, dtype=float)
    headroom_to_cap = np.maximum(voll - lam, 0.0)

    r_full = np.asarray(reserves_mw, dtype=float)
    r_online = (
        r_full if reserves_online_mw is None
        else np.asarray(reserves_online_mw, dtype=float)
    )
    mu = np.asarray(mu_mw, dtype=float)
    sigma = np.asarray(sigma_mw, dtype=float)
    lolp_full = lolp(r_full, mu, sigma, mcl_mw, shift_sigma)
    lolp_half = lolp(
        r_online, mu / 2.0, sigma / np.sqrt(2.0), mcl_mw, shift_sigma)
    adder = 0.5 * headroom_to_cap * (lolp_full + lolp_half)

    if multistep_floor:
        floor = np.zeros_like(adder)
        # Steps are (threshold, floor) sorted descending so the tightest
        # (lowest-reserve) step wins; keyed to online responsive reserve.
        for threshold, value in sorted(ORDC_FLOOR_STEPS, reverse=True):
            floor = np.where(r_online <= threshold, value, floor)
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


def _online_plant_mask(
    fleet_arrays: FleetArrays, dispatch: np.ndarray, threshold_mw: float
) -> np.ndarray:
    """Return an ``(n_gen, T)`` bool mask of units belonging to an online plant.

    A unit is "online" in hour *t* when its plant is producing — needed because
    per-plant binning splits one physical plant into several LP units (must-run
    / committed / economic / peaking tranches sharing a ``plant_code``). The
    upper tranche of a running plant carries spinning headroom even at zero
    dispatch, so online status is decided at the **plant** level: every tranche
    of a plant whose summed dispatch exceeds ``threshold_mw`` is online. Units
    with no ``plant_code`` (code 0 / absent) fall back to their own dispatch.
    """
    disp = np.asarray(dispatch, dtype=float)
    online = disp > threshold_mw
    codes = getattr(fleet_arrays, "plant_code", None)
    if codes is None:
        return online
    codes = np.asarray(codes)
    for code in np.unique(codes[codes > 0]):
        rows = np.flatnonzero(codes == code)
        online[rows] = disp[rows].sum(axis=0) > threshold_mw
    return online


def reserve_headroom(
    fleet_arrays: FleetArrays,
    dispatch: np.ndarray,
    storage_power_cap: np.ndarray,
    storage_charge: np.ndarray | None,
    storage_discharge: np.ndarray | None,
    as_plan_mw: float | np.ndarray,
    renewable_headroom: np.ndarray | None = None,
    online_threshold_mw: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Hourly online/offline reserve split (MW) from solved-dispatch arrays.

    Splits operating reserve into the two tiers ERCOT's ORDC prices against:

    * **online (spinning)** — headroom on thermal units whose plant is running,
      plus storage headroom (ESR telemetry: power cap - discharge + charge) and
      curtailed-renewable headroom, **minus** the ancillary-service plan held
      out of energy (``as_plan_mw``, scalar or ``(T,)``);
    * **offline (30-minute non-spin)** — available capacity on quick-start units
      (:data:`QUICK_START_FUEL_TYPES`) whose plant is *not* running.

    A cold slow-start unit (coal / combined-cycle / steam / nuclear that is not
    running) contributes to **neither** tier — it cannot respond within the
    operating hour — which removes the perfect-foresight LP's phantom reserve.
    Curtailed renewables count toward online reserve (ERCOT telemetry is
    HSL - output); in real scarcity hours renewables run at potential so that
    term is ~0 exactly where the adder matters.

    Args:
        fleet_arrays: The fleet the LP solved against (availability incl.
            the outage overlay and derates).
        dispatch: ``(n_gen, T)`` solved generation in MW.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` MW caps.
        storage_charge: ``(n_storage, T)`` charge MW (``None`` = none).
        storage_discharge: ``(n_storage, T)`` discharge MW.
        as_plan_mw: Ancillary-service plan netting in MW (scalar or ``(T,)``).
        renewable_headroom: Optional ``(T,)`` curtailed wind+solar MW
            (potential cf x cap minus dispatched).
        online_threshold_mw: Plant dispatch above which it counts as online.

    Returns:
        Tuple ``(r_online, r_offline)`` of ``(T,)`` MW arrays. ``r_online`` may
        go negative under deep scarcity; the LOLP pins to 1 below the MCL.
    """
    fuel_names = np.array(
        [FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    thermal = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))

    disp = np.asarray(dispatch, dtype=float)
    avail_cap = fleet_arrays.pmax[:, None] * fleet_arrays.availability
    headroom = np.maximum(avail_cap - disp, 0.0)
    online_unit = _online_plant_mask(fleet_arrays, disp, online_threshold_mw)

    online_thermal = thermal[:, None] & online_unit
    offline_quick = thermal[:, None] & quick[:, None] & ~online_unit
    r_online_thermal = np.where(online_thermal, headroom, 0.0).sum(axis=0)
    r_offline = np.where(offline_quick, headroom, 0.0).sum(axis=0)

    cap = np.asarray(storage_power_cap, dtype=float)
    storage_headroom = (
        cap.sum(axis=0) if cap.ndim == 2
        else np.full(r_online_thermal.shape, cap.sum())
    )
    if storage_discharge is not None and np.size(storage_discharge):
        storage_headroom = (
            storage_headroom
            - np.asarray(storage_discharge, dtype=float).sum(axis=0)
            + np.asarray(storage_charge, dtype=float).sum(axis=0)
        )
    as_arr = np.broadcast_to(
        np.asarray(as_plan_mw, dtype=float), r_online_thermal.shape)
    r_online = r_online_thermal + storage_headroom - as_arr
    if renewable_headroom is not None:
        r_online = r_online + np.asarray(renewable_headroom, dtype=float)
    return r_online, r_offline


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


def ercot_reserve_eligible(fleet_arrays: FleetArrays) -> np.ndarray:
    """Boolean ``(n_gen,)`` mask of ORDC-reserve-eligible generators.

    The same dispatchable thermal classes the post-solve overlay counts toward
    operating reserve (:data:`RESERVE_FUEL_TYPES` — gas/coal/nuclear/oil);
    wind, solar, hydro and imports hold nothing responsive back. In the
    energy+reserve co-optimization LP the shared-headroom row lets only these
    units split capacity between energy and upward reserve, so a unit must be
    eligible to part-load against the reserve requirement.
    """
    fuel_names = np.array(
        [FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    return np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))


def ercot_ordc_demand_steps(
    *,
    voll: float,
    mcl_mw: float,
    mu_mw: float,
    sigma_mw: float,
    shift_sigma: float,
    n_steps: int = 40,
    sigma_span: float = 5.0,
    multistep_floor: bool = True,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Discretize the VOLL-anchored ORDC reserve demand curve into LP shortfall steps.

    The co-optimization analogue of the post-solve :func:`ordc_adder`. ERCOT's
    ORDC *is* a reserve demand curve: the marginal value of the R-th MW of
    operating reserve is the loss-of-load probability at that reserve level
    times the value of lost load. Co-optimized inside SCED (the RTC+B design,
    live 2025-12-05) the curve clears against the units' opportunity cost of
    holding energy headroom, and the reserve clearing price lifts the energy
    LMP through the shared-headroom constraint — reproducing RTSPP = LMP +
    reserve price *endogenously*, rather than the post-solve ``(VOLL - lambda)``
    adder the energy-only LP needs.

    The curve is **VOLL-anchored**, not ``(VOLL - lambda)``-anchored: an LP
    objective coefficient must be a constant, and lambda (the energy price) is
    endogenous here. This is the co-optimization-correct form and matches the
    published RTC+B AS demand curves (fixed price-vs-MW schedules anchored at
    the offer cap); the energy price the reserve dual lifts already carries
    lambda, so the cleared total reproduces the LMP + reserve value the
    ``(VOLL - lambda)`` overlay approximates. The two LOLP terms mirror RTORPA's
    two half-hour curves (full-hour ``mu/sigma`` and first-half ``mu/2,
    sigma/sqrt(2)``), so the demand price at reserve ``R`` is
    ``0.5 * VOLL * (LOLP_full(R) + LOLP_half(R))`` — capped at VOLL by
    construction (both LOLP -> 1 as R -> 0).

    Returns ``(req_total_mw, penalties, widths)`` in the contract
    :func:`pjm_ordc_shortfall_steps` produces and ``model.dispatch`` consumes:
    the reserve-balance RHS and the per-step penalty ($/MWh) and width (MW)
    arrays, ordered cheapest band (highest reserve) first.
    """
    mu_eff = mu_mw + shift_sigma * sigma_mw
    # Reserve level above which the ORDC value is negligible — the top of the
    # demand curve and the reserve-balance requirement. Past mcl + mu_eff +
    # sigma_span*sigma the LOLP (hence the price) is ~0, so demand stops there.
    req_total = float(mcl_mw + mu_eff + sigma_span * sigma_mw)
    # Descending reserve grid req_total -> 0; band j spans (grid[j+1], grid[j]]
    # of reserve, priced at the ORDC value at its lower reserve edge (the level
    # at which that band starts clearing), so penalties ascend as reserves fall
    # — cheapest (outermost, highest-reserve) band first.
    grid = np.linspace(req_total, 0.0, int(n_steps) + 1)
    widths = grid[:-1] - grid[1:]            # (n_steps,), positive
    r_edge = grid[1:]                        # lower reserve edge of each band
    lolp_full = lolp(r_edge, mu_mw, sigma_mw, mcl_mw, shift_sigma)
    lolp_half = lolp(
        r_edge, mu_mw / 2.0, sigma_mw / np.sqrt(2.0), mcl_mw, shift_sigma)
    penalties = 0.5 * float(voll) * (lolp_full + lolp_half)
    if multistep_floor:
        # OBDRR048 RTORPA floor (>= $20 at reserves <= 6,500 MW, >= $10 at
        # 6,500-7,000 MW). In the forward RTC+B regime the floor applies
        # unconditionally; the date-gating the post-solve overlay does for the
        # 2023 backcast is not modeled here (co-opt is primarily forward).
        floor = np.zeros_like(penalties)
        for threshold, value in sorted(ORDC_FLOOR_STEPS, reverse=True):
            floor = np.where(r_edge <= threshold, value, floor)
        penalties = np.maximum(penalties, floor)
    return req_total, penalties.astype(float), widths.astype(float)


_ERCOT_AS_DIR = RAW_DATA_DIR / "ercot-AS"


def ercot_load_resource_reserve_mw(year: int, hours: int) -> np.ndarray:
    """ERCOT's measured hourly Load-Resource responsive-reserve MW for ``year``.

    Reads the ``rrsufr_mw`` column of ``ercot_<year>_as_up_mw.parquet`` (built by
    ``scripts/build_ercot_as_withholding.py`` from the NP3-911 cleared-DAM-AS
    reports): RRS-UFR is the Responsive Reserve provided by **Load Resources**
    via high-set under-frequency relays — by ERCOT protocol an exclusively
    load-side service (~0.8–0.9 GW mean, capped ~1.4 GW). This is reserve supply
    the co-opt LP otherwise omits (it counts only thermal headroom + storage),
    so the model clears reserve lower on the ORDC curve than reality and prices a
    scarcity adder in non-scarce hours.

    Returns ``(hours,)`` MW, zero-padded if short and **all-zero when the file is
    absent** — the cleared-AS archive begins 2023-12-10, so 2023 gets no credit
    and its genuine scarcity tail is left untouched.
    """
    path = _ERCOT_AS_DIR / f"ercot_{year}_as_up_mw.parquet"
    if not path.exists():
        return np.zeros(int(hours), dtype=float)
    import pandas as pd

    series = pd.read_parquet(path)["rrsufr_mw"].to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(int(hours) - len(series))])
    return series[: int(hours)]


def ercot_storage_as_reserve_mw(year: int, hours: int) -> np.ndarray:
    """ERCOT's measured hourly storage-provided AS-up MW for ``year``.

    Reads the ``storage`` column of ``ercot_<year>_as_by_restype_hourly.parquet``
    (the per-resource-type 60-Day DAM AS awards): the RegUp/RRS/ECRS cleared by
    **batteries** (~0.8 GW in 2023 → ~2.0 GW 2024 → ~2.8 GW 2025 as the fleet
    grew). This is responsive reserve ERCOT's RTOLCAP/RTOFFCAP count toward the
    ORDC adder, but which the co-opt LP drops when ``storage_as_commitment`` is
    on: that flag subtracts this same MW from the storage *power cap*, and the
    reserve block computes a unit's reserve room off that reduced cap — so the
    AS-committed battery capacity is removed from energy (correct, it can't also
    arbitrage) *and* from reserve supply (incorrect, it is held reserve). The
    model then clears reserve lower on the ORDC curve than reality and prices a
    scarcity adder in non-scarce hours — biggest in 2025, where the battery AS
    fleet is largest.

    Returns ``(hours,)`` MW, zero-padded if short and **all-zero when the file is
    absent**. Same non-leap 8760-hour clock as the fleet.
    """
    path = _ERCOT_AS_DIR / f"ercot_{year}_as_by_restype_hourly.parquet"
    if not path.exists():
        return np.zeros(int(hours), dtype=float)
    import pandas as pd

    series = pd.read_parquet(path)["storage"].to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(int(hours) - len(series))])
    return series[: int(hours)]


def ercot_reserve_coopt_inputs(
    config, fleet_arrays: FleetArrays, hours: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the ERCOT energy+reserve co-optimization inputs for ``solve_dispatch``.

    Returns ``(reserve_requirement, reserve_eligible, ordc_penalties,
    ordc_step_widths)``: the hourly reserve-balance RHS (flat at the demand
    curve's top), the reserve-eligible generator mask, and the VOLL-anchored
    ORDC shortfall-step penalties and widths. The demand curve is constant
    across hours — the hourly scarcity *incidence* comes from the hourly
    availability in the shared-headroom RHS (a tight fleet clears reserve lower
    on the curve, at a higher price), not from a time-varying curve shape — so a
    seasonal/TOD ``ordc_lolp_params_path`` table is reduced to its mean here.
    """
    mu, sigma = resolve_lolp_params(config, hours)
    mu_s = float(np.mean(mu))
    sigma_s = float(np.mean(sigma))
    req_total, penalties, widths = ercot_ordc_demand_steps(
        voll=config.ordc_voll,
        mcl_mw=config.ordc_mcl_mw,
        mu_mw=mu_s,
        sigma_mw=sigma_s,
        shift_sigma=config.ordc_lolp_shift_sigma,
        multistep_floor=config.ordc_multistep_floor,
    )
    requirement = np.full(int(hours), req_total, dtype=float)
    if getattr(config, "ercot_load_resource_reserve", False):
        # Credit ERCOT's measured Load-Resource responsive reserve (RRS-UFR) the
        # co-opt LP otherwise omits. Lowering the balance-RHS by load_mw(t) is
        # equivalent to adding load_mw of $0 reserve supply: because the ORDC
        # steps are priced by absolute reserve level, the marginal step then
        # prices at total reserve R_gen + load_mw — physically exact, no double
        # count. Clipped to the MCL floor so the curve's steep tail is preserved.
        load_mw = ercot_load_resource_reserve_mw(int(config.weather_year), hours)
        requirement = np.maximum(requirement - load_mw, float(config.ordc_mcl_mw))
    if (getattr(config, "ercot_storage_as_reserve", False)
            and getattr(config, "storage_as_commitment", False)
            and int(config.weather_year)
            >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))):
        # Credit the measured battery-provided AS (RegUp/RRS/ECRS) back into the
        # reserve balance. storage_as_commitment subtracts this same MW from the
        # storage power cap, and the reserve block derives a unit's reserve room
        # from that reduced cap — so without this credit the committed battery AS
        # is dropped from both energy (correct) and reserve supply (incorrect: it
        # IS held responsive reserve, counted in ERCOT's RTOLCAP/RTOFFCAP). As a
        # fixed AS commitment it is held in every committed hour regardless of the
        # battery's energy dispatch, so it credits the balance RHS unconditionally
        # — exactly like the load-resource credit, and with no double count (the
        # reserve room from the reduced cap is the disjoint arbitrage headroom).
        # GUARDED on storage_as_commitment: with it off the full cap is already in
        # the reserve block and crediting here would double-count.
        #
        # SCOPED to weather_year >= ercot_storage_as_reserve_from_year (default
        # 2025), which is a *modeling* choice, not a measured one (say so): the
        # credit is physically correct in every year (~0.8 GW 2023 → ~2.8 GW
        # 2025), but in 2023/2024 the model can only reach the year's *genuine*
        # scarcity tail THROUGH the reserve over-fire, so crediting the battery
        # AS makes reserves look adequate on days that were actually tight and the
        # model loses the real tail. 2023's tail is documented *out-of-market*
        # scarcity (ERCOT's RTORDPA / ECRS-conservatism, IMM >$12B; the >$200
        # hours are 47% of the year's $) an ORDC model can't reproduce, so it
        # collapses (Aug model $74 vs actual $217). 2024's is real tight-day
        # scarcity (53 h >$200, 8 h >$1000); a single-year probe crediting 2024
        # cooled avg 29.0→21.2 (actual 26.8), WORSENED MAE 10.5→12.7 and
        # collapsed the tail 49→7 h >$200 — measured, not "lower penetration".
        # 2025 is the lone year whose residual is *purely* this reserve over-fire
        # (tail = 4% of $, reserves genuinely fat), so the measured credit closes
        # it cleanly (2025 LMP MAE 11.3 → 2.7; gas/coal split unchanged).
        # The physically-pure global path needs 2023/2024 scarcity modeled by a
        # genuine ORDC scarcity-price mechanism — NOT the reliability-deployment
        # overlay, which is an energy/congestion min-gen floor (a credit+overlay
        # 2024 probe was indistinguishable from credit-only, ~$0.1 on system LMP).
        # Here the credit is gated to the year the residual is reserve-accounting
        # only.
        storage_as_mw = ercot_storage_as_reserve_mw(
            int(config.weather_year), hours)
        requirement = np.maximum(
            requirement - storage_as_mw, float(config.ordc_mcl_mw))
    eligible = ercot_reserve_eligible(fleet_arrays)
    return requirement, eligible, penalties, widths


def scarcity_prices(
    config,
    year: int,
    reserves_mw: np.ndarray,
    system_lambda: np.ndarray,
    reserves_online_mw: np.ndarray | None = None,
) -> dict[str, np.ndarray]:
    """Convenience wrapper: hourly LOLP + adder for a config and year.

    ``reserves_mw`` is the full-hour reserve (online + offline);
    ``reserves_online_mw`` is the online tier backing the first-half LOLP term
    (defaults to ``reserves_mw`` for the legacy RTOFFCAP = 0 behaviour). Returns
    a dict with ``reserves_mw``, ``reserves_online_mw``, ``lolp`` (full-hour
    curve) and ``scarcity_adder`` arrays. The caller adds the adder to its price
    series (every zone sees the same system-wide adder, matching ERCOT, where
    the reserve price adder is a system-level component of every settlement
    point price).
    """
    hours = len(np.asarray(reserves_mw))
    online = (
        reserves_mw if reserves_online_mw is None else reserves_online_mw
    )
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
        reserves_online_mw=online,
    )
    return {
        "reserves_mw": np.asarray(reserves_mw, dtype=float),
        "reserves_online_mw": np.asarray(online, dtype=float),
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


def largest_single_contingency_mw(
    pmax: np.ndarray,
    availability: np.ndarray | None = None,
    reserve_mask: np.ndarray | None = None,
    plant_code: np.ndarray | None = None,
) -> float:
    """Most-Severe Single Contingency proxy: the largest single resource (MW).

    The reserve requirement's reliability basis (PJM Manual 13): the largest
    single resource whose loss the system must cover. The physical contingency
    is a common-mode loss of a *plant* (units sharing a station/bus), not one
    LP row — a binned/per-plant fleet splits a station across many tranches and
    units, so the bare per-row maximum badly understates the MSSC. When
    ``plant_code`` is supplied, deliverable capacity is summed per plant first
    and the largest *plant* is the MSSC; rows with ``plant_code <= 0`` (imports,
    aggregated pseudo-units) are treated individually. Fleet-responsive by
    construction — retire the largest plant and the MSSC, hence the requirement,
    falls — which is what makes the requirement forecast-valid rather than a
    replay of the measured series.

    Args:
        pmax: ``(n_gen,)`` per-unit nameplate MW.
        availability: ``(n_gen, T)`` availability, used to take peak deliverable
            MW per unit. ``None`` uses bare nameplate.
        reserve_mask: ``(n_gen,)`` boolean of reserve-eligible units. ``None``
            considers every unit.
        plant_code: ``(n_gen,)`` EIA plant code per unit. When given, capacity
            is aggregated to the plant (common-mode contingency) before the max.

    Returns:
        Largest single-resource MW (0.0 for an empty/zero fleet).
    """
    pmax = np.asarray(pmax, dtype=float)
    if pmax.size == 0:
        return 0.0
    if availability is not None:
        deliverable = pmax * np.asarray(availability, dtype=float).max(axis=1)
    else:
        deliverable = pmax.copy()
    if reserve_mask is not None:
        deliverable = deliverable * np.asarray(reserve_mask, dtype=bool)
    if deliverable.max(initial=0.0) <= 0.0:
        return 0.0
    if plant_code is None:
        return float(deliverable.max())
    # Aggregate to the plant (common-mode loss). Rows with no real plant code
    # (imports / aggregated pseudo-units) each count as their own contingency.
    pc = np.asarray(plant_code)
    by_plant: dict[object, float] = {}
    for i, cap in enumerate(deliverable):
        if cap <= 0.0:
            continue
        key = int(pc[i]) if int(pc[i]) > 0 else ("_row", i)
        by_plant[key] = by_plant.get(key, 0.0) + float(cap)
    return max(by_plant.values()) if by_plant else 0.0


_PJM_AS_DIR = RAW_DATA_DIR / "PJM-AS"


def load_pjm_measured_reserve_requirement(
    year: int, hours: int = 8760, data_dir: Path = _PJM_AS_DIR,
) -> np.ndarray | None:
    """Return the measured PJM_RTO Primary Reserve requirement (MW), hourly.

    The published reserve requirement (``pr_req_mw`` in
    ``inputs/raw-data/PJM-AS/pjm_<year>_as_up_mw.parquet``, derived by
    ``scripts/build_pjm_as_withholding.py`` from PJM Data Miner) is a measured
    *reliability* quantity — the capacity PJM holds against its most-severe
    single contingency, set by a published market-design formula (Manual 13),
    not a price actual. Using it as the co-optimization requirement in a
    backcast is the reserve analogue of the historic outage / fuel-price
    overlays: a measured physical input, not a fit to the LMP residual. The
    forecast path uses :func:`pjm_primary_reserve_requirement` (the fleet-
    responsive 1.5x-MSSC formula) instead.

    Returns ``None`` when the parquet is absent (caller falls back to the
    formula).
    """
    path = Path(data_dir) / f"pjm_{year}_as_up_mw.parquet"
    if not path.exists():
        return None
    import pandas as pd

    req = pd.read_parquet(path)["pr_req_mw"].to_numpy(dtype=float)
    # Data holes (documented ~24 h) read as 0; forward/back-fill so the
    # requirement is never spuriously zero.
    if (req <= 0.0).any():
        good = req > 0.0
        if good.any():
            idx = np.where(good, np.arange(len(req)), -1)
            np.maximum.accumulate(idx, out=idx)
            idx[idx < 0] = np.flatnonzero(good)[0]
            req = req[idx]
    if len(req) >= hours:
        return req[:hours]
    # Tile up to the requested horizon (defensive; series is normally 8760).
    return np.resize(req, hours)


def pjm_primary_reserve_requirement(
    lsc_mw: float,
    hours: int,
    factor: float = PJM_PRIMARY_RESERVE_LSC_FACTOR,
) -> np.ndarray:
    """Hourly PJM Primary Reserve requirement (MW) = ``factor x MSSC``.

    The structural, forecast-applicable requirement for the energy+reserve
    co-optimization: PJM holds Primary Reserve at ~1.5x the most-severe single
    contingency (PJM Manual 13 / Manual 11 sec 4.4). Returned as a flat hourly
    array because the requirement is a near-constant reliability quantity (the
    measured PJM_RTO ``pr_req_mw`` varies only ~+/-15% around its mean and RT/DA
    agree within ~3%). ``lsc_mw`` from :func:`largest_single_contingency_mw`
    keeps it fleet-responsive; the measured series
    (``inputs/raw-data/PJM-AS``) is a backcast honesty gate only, never an LP
    input.

    Args:
        lsc_mw: Most-severe single contingency (largest single unit) MW.
        hours: Horizon length (typically 8760).
        factor: Requirement / MSSC ratio (PJM_PRIMARY_RESERVE_LSC_FACTOR).

    Returns:
        ``(hours,)`` reserve requirement in MW.
    """
    return np.full(int(hours), max(0.0, factor * float(lsc_mw)), dtype=float)


def pjm_ordc_shortfall_steps(
    ordc_steps: list[tuple[float, float]],
    requirement_mw: float,
) -> tuple[float, np.ndarray, np.ndarray]:
    """Convert the published ORDC demand curve into LP reserve-shortfall steps.

    The published curve (``load_pjm_ordc_curve``) is a *descending* demand: at
    reserves below the requirement the top penalty applies, and each breakpoint
    ``requirement + offset`` above it steps the price down (to $0 past the last
    breakpoint). The co-optimization LP instead needs *ascending* shortfall
    steps for the reserve-balance row ``sum R + sum shortfall_k >= req_total``,
    each ``shortfall_k in [0, width_k]`` priced at ``penalties_k``. Being short
    by the cheapest band first reproduces the demand curve, so the balance-row
    dual equals the binding step's penalty — the ORDC reserve clearing price.

    For PJM's two-step curve ``[(0, 850), (190, 300)]`` at requirement ``REQ``
    this returns ``req_total = REQ + 190`` and steps ``([300, 850], [190, REQ])``:
    the first 190 MW of shortfall (reserves between ``REQ`` and ``REQ+190``)
    costs $300, the rest (reserves below ``REQ``) costs $850.

    Args:
        ordc_steps: ``[(offset_mw, penalty_factor), ...]`` from
            :func:`load_pjm_ordc_curve`.
        requirement_mw: The reserve requirement REQ in MW (scalar).

    Returns:
        ``(req_total_mw, penalties, widths)``: the balance RHS and the per-step
        penalty ($/MWh) and width (MW) arrays, ordered cheapest band first.
    """
    steps = sorted(ordc_steps)  # ascending offset
    offsets = [o for o, _ in steps]
    penalties = [p for _, p in steps]
    req = float(requirement_mw)
    req_total = req + offsets[-1]
    pens: list[float] = []
    widths: list[float] = []
    # Outer bands between consecutive breakpoints, cheapest (outermost) first.
    for k in range(len(steps) - 1, 0, -1):
        widths.append(offsets[k] - offsets[k - 1])
        pens.append(penalties[k])
    # Inner band [0, requirement): being short below the requirement, top price.
    widths.append(req)
    pens.append(penalties[0])
    return req_total, np.array(pens, dtype=float), np.array(widths, dtype=float)


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
