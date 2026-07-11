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
* Reserves are split into an on-line (spinning) and an off-line (30-minute
  non-spin, RTOFFCAP) tier by :func:`reserve_headroom` (the legacy "all
  on-line / RTOFFCAP = 0" shortcut is gone): on-line = headroom on running
  plants + storage + curtailed renewables, off-line = available capacity on
  *quick-start* (gas-CT / oil) units whose plant is idle; a cold slow-start
  unit backs neither. :func:`ordc_adder` evaluates the full-hour LOLP term on
  ``online + offline`` and the first-half term on ``online`` alone, the
  published RTOLCAP / RTOFFCAP structure. (Off by default in the co-opt keeper,
  which prices scarcity in the LP instead — see the co-opt section in
  docs/ordc-overlay.md.)
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
    ERCOT_LR_RRS_AVAILABILITY_HOD,
    ERCOT_ONLINE_CAP_DELIV_COEF,
    ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME,
    ERCOT_ONLINE_CAP_DELIV_PROFILE_MEASURED,
    ERCOT_ONLINE_CAP_MEASURED_AVAIL_CLASSES,
    ERCOT_ONLINE_CAP_SHARE,
    ERCOT_ONLINE_CAP_SHARE_EXTREME,
    ERCOT_ONLINE_CAP_SHARE_MEASURED,
    ERCOT_RTOLCAP_FWD_DELIV_COEF,
    ERCOT_RTOLCAP_FWD_N_DECILE,
    ERCOT_RTOLCAP_FWD_OFFLINE_CLASSES,
    ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF,
    ERCOT_RTOLCAP_FWD_OFFLINE_SHARE,
    ERCOT_RTOLCAP_FWD_ONLINE_CLASSES,
    ERCOT_RTOLCAP_FWD_ONLINE_SHARE,
    ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH,
    ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC,
)
from market_sim.config.reserve_config import (
    ERCOT_AS_ECRS_BASE_MW,
    ERCOT_AS_ECRS_MAX_MW,
    ERCOT_AS_ECRS_MIN_MW,
    ERCOT_AS_ECRS_RAMP_COEF,
    ERCOT_AS_ECRS_SIGMA_COEF,
    ERCOT_AS_FE_FRAC_LOAD,
    ERCOT_AS_FE_FRAC_SOLAR,
    ERCOT_AS_FE_FRAC_WIND,
    ERCOT_AS_NSPIN_BASE_MW,
    ERCOT_AS_NSPIN_LOAD_COEF,
    ERCOT_AS_NSPIN_MAX_MW,
    ERCOT_AS_NSPIN_MIN_MW,
    ERCOT_AS_NSPIN_RAMP_COEF,
    ERCOT_AS_PRODUCTS,
    ERCOT_AS_RAMP_WINDOW_HOURS,
    ERCOT_AS_REGUP_FLOOR_MW,
    ERCOT_AS_REGUP_MAX_MW,
    ERCOT_AS_REGUP_MIN_MW,
    ERCOT_AS_REGUP_SIGMA_COEF,
    ERCOT_AS_RRS_FLOOR_MW,
    ERCOT_AS_RRS_INERTIA_COEF_MW,
    ERCOT_AS_RRS_MAX_MW,
    ERCOT_LR_RRS_ENROLL_BASE_MW,
    ERCOT_LR_RRS_ENROLL_BASE_YEAR,
    ERCOT_LR_RRS_ENROLL_CAP_MW,
    ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR,
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

# NYISO synchronised (spinning) reserve fraction: the 10-minute SPINNING
# requirement is one half of the 10-minute total (the published NYISO rule —
# 10-min spinning = 1/2 largest contingency; the same 1/2 that fixes
# ``nyca_10min_spin = 655 = 1/2 nyca_10min_total 1310`` in NYISO_RCPF_PRODUCTS).
# A measured market-design constant, NOT fitted to any price residual
# (CLAUDE.md rule #12). Applied to the NYC 10-min total (500 MW) -> 250 MW NYC
# spin. Used by the path-B commitment-gated synchronised-reserve route
# (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md).
NYISO_SPIN_FRACTION: float = 0.5

# Zones whose quick-start fleet may supply the NYC locational synchronised-reserve
# requirement. The NYC spinning family is a balance row over the NYC zone only
# (NYISO_RCPF_LOCATIONAL["NYC"]["zones"] == ("NYC",)), and reserve is per-zone
# deliverable (dispatch._build_reserve_rows; handoff Finding 5: out-of-pocket
# headroom cannot satisfy a downstate family). So only NYC-zone quick-start units
# can back R[quick-start, NYC] — the reserve-adequacy commit force-commits this
# subset. The "downstate / NYC-SENY pocket" language in the handoff refers to the
# import-constrained region; its binding locational spinning family is NYC.
NYISO_DOWNSTATE_SPIN_ZONES: frozenset[str] = frozenset({"NYC"})

# ERCOT ORDC seasons (calendar quarters of the LOLP statistics): winter =
# Dec-Feb, spring = Mar-May, summer = Jun-Aug, fall = Sep-Nov.
_SEASON_OF_MONTH: tuple[str, ...] = (
    "winter",
    "winter",
    "spring",
    "spring",
    "spring",
    "summer",
    "summer",
    "summer",
    "fall",
    "fall",
    "fall",
    "winter",
)

# Non-leap dispatch calendar (matches market_sim.data.campd conventions).
_DAYS_IN_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR = np.cumsum([0] + [d * 24 for d in _DAYS_IN_MONTH])


def _month_of_hour(hours: np.ndarray) -> np.ndarray:
    """Map non-leap hour-of-year indices to months 1-12."""
    return np.searchsorted(_MONTH_START_HOUR, hours, side="right").clip(1, 12)


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
        raise ValueError(f"LOLP params CSV {path} must have columns {sorted(need)}")
    key = {
        (str(r.season).lower(), int(r.tod_block)): (r.mu_mw, r.sigma_mw)
        for r in df.itertuples()
    }
    hour_idx = np.arange(hours)
    seasons = season_of_hour(hour_idx)
    blocks = tod_block_of_hour(hour_idx)
    missing = {(s, int(b)) for s, b in zip(seasons, blocks)} - set(key)
    if missing:
        raise ValueError(
            f"LOLP params CSV {path} missing (season, block) pairs: {sorted(missing)}"
        )
    mu = np.array([key[(s, int(b))][0] for s, b in zip(seasons, blocks)], dtype=float)
    sigma = np.array(
        [key[(s, int(b))][1] for s, b in zip(seasons, blocks)], dtype=float
    )
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
        sigma_mw, dtype=float
    )
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
        r_full
        if reserves_online_mw is None
        else np.asarray(reserves_online_mw, dtype=float)
    )
    mu = np.asarray(mu_mw, dtype=float)
    sigma = np.asarray(sigma_mw, dtype=float)
    lolp_full = lolp(r_full, mu, sigma, mcl_mw, shift_sigma)
    lolp_half = lolp(r_online, mu / 2.0, sigma / np.sqrt(2.0), mcl_mw, shift_sigma)
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
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
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
        cap.sum(axis=0) if cap.ndim == 2 else np.full(r_online_thermal.shape, cap.sum())
    )
    if storage_discharge is not None and np.size(storage_discharge):
        storage_headroom = (
            storage_headroom
            - np.asarray(storage_discharge, dtype=float).sum(axis=0)
            + np.asarray(storage_charge, dtype=float).sum(axis=0)
        )
    as_arr = np.broadcast_to(
        np.asarray(as_plan_mw, dtype=float), r_online_thermal.shape
    )
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

# Non-leap hour-of-year index of 2025-12-05 00:00 (RTC+B go-live), the end of
# the ORDC/RTORPA/RTORDPA regime. Jan-Nov = 334 days, so Dec 5 00:00 = 338*24
# = 8112 — exactly where the measured 2025 reserves series stops (its tail is
# preserved NaN past go-live, not fabricated). On the fixed non-leap clock this
# index is the same calendar instant in every year, so the within-2025 cut is a
# calendar gate, not a hard-coded 2025 special case.
RTCB_GOLIVE_HOUR: int = 338 * 24  # 8112

# Per-year measured ORDC / reserves series (scripts/fetch_ercot_ordc_reserves.py).
_ERCOT_ORDC_RESERVES_TMPL = "ercot_{year}_ordc_reserves_hourly.parquet"


def ercot_rtordpa_overlay_series(year: int, hours: int, config=None) -> np.ndarray:
    """Measured RTORDPA, regime-gated, as a post-solve $/MWh system-price overlay.

    RTORDPA is ERCOT's published **Real-Time ORDC + Reliability-Deployment Price
    Adder** — the reliability-deployment component of the real-time reserve
    price the co-opt LP has no mechanism for (it endogenously produces an ORDC
    adder ≈ RTORPA via the reserve-balance dual, but not the out-of-market
    reliability-deployment slice ERCOT ran conservatively in 2023-H2). Adding
    the measured ``rtordpa`` to the model system price is therefore **additive,
    not double-counting RTORPA**; verify against the run's ``reserve_price``
    (≈ RTORPA) before/after.

    Read **per year** from
    ``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet`` (the ``rtordpa``
    column) — never a 2023 hard-code, which is exactly what makes the overlay
    backcast-able on any year incl. 2022. It is an **exogenous measured series,
    never fit to LMP**.

    Regime gate (pre-RTC+B only; RTC+B retired the adders on 2025-12-05):
      * year <= 2024 — fully pre-RTC+B, the whole-year measured series applies;
      * year == 2025 — pre-RTC+B only through Dec 4: hours >= RTCB_GOLIVE_HOUR
        zeroed (the measured series is already NaN there);
      * year >= 2026 (or an explicit ``ercot_market_design='rtcb'``) — RTC+B,
        the overlay is inert (zeros).
    Missing files and NaN adder hours map to 0 (no overlay), never fabricated.
    """
    out = np.zeros(int(hours), dtype=float)
    regime_ordc = (
        ercot_market_regime(year, config) == "ordc"
        if config is not None
        else year < _RTCB_FIRST_FULL_YEAR
    )
    if not regime_ordc:
        return out
    path = RAW_DATA_DIR / "ercot" / _ERCOT_ORDC_RESERVES_TMPL.format(year=year)
    if not path.exists():
        return out
    import pandas as pd

    df = pd.read_parquet(path, columns=["hour", "rtordpa"])
    s = df.set_index("hour")["rtordpa"].reindex(range(int(hours)))
    vals = np.nan_to_num(s.to_numpy(dtype=float), nan=0.0)
    n = min(len(vals), len(out))
    out[:n] = vals[:n]
    # Within-2025 calendar cut at the RTC+B go-live (belt-and-suspenders: the
    # measured 2025 series is already NaN from this hour onward).
    if year == _RTCB_FIRST_FULL_YEAR - 1:
        out[RTCB_GOLIVE_HOUR:] = 0.0
    return out


# Per-year measured DAM AS clearing-price series (scripts/build_ercot_dam_as_mcpc.py).
_ERCOT_DAM_AS_MCPC_TMPL = "ercot_{year}_dam_as_mcpc_hourly.parquet"

# Default first year the DAM-AS overlay applies. The 2023 stress year's day-ahead
# AS scarcity is the SAME scarcity the RTORDPA reliability-deployment overlay
# already represents (RTORDPA is material in 2023, near-inert in 2024/25), so
# applying both in 2023 double-counts one event through two measured channels and
# over-fires 2023-H2 (Aug binding-MCPC scarce-hour mean ~$222 >> actual DA ~$147).
# The DAM-AS overlay is therefore scoped to 2024+, where RTORDPA is inert and the
# day-ahead AS co-optimization is the *unrepresented* binding price-formation
# channel — the same year-scoping logic as ercot_storage_as_reserve_from_year.
_ERCOT_DAM_AS_OVERLAY_FROM_YEAR: int = 2024

# AS clearing price ($/MWh) above which the DAM cleared into scarcity rather than
# competitive AS. ERCOT's competitive DAM AS clears in the single-to-low-double
# digits (measured 2024 product means: RegUp $6.5, RRS $5.6, ECRS $12.6, NonSpin
# $10.0); a binding MCPC above this level is the AS scarcity demand curve
# (ASDC/ORDC) pricing, not competitive offers. Not fitted to a price residual —
# the May-2024 monthly lift is robust to the exact level (binding-MCPC overlay
# mean ~$18-23 across thresholds $75-200), and the gate's job is only to keep the
# overlay inert in non-scarce hours (so it does not lift the broad mid-range and
# re-break Aug 2024 / 2025, the failure mode of the rejected flat-ECRS probe).
_ERCOT_DAM_AS_SCARCITY_THRESHOLD: float = 150.0


def ercot_dam_as_overlay_series(
    year: int,
    hours: int,
    *,
    scarcity_threshold: float = _ERCOT_DAM_AS_SCARCITY_THRESHOLD,
    from_year: int = _ERCOT_DAM_AS_OVERLAY_FROM_YEAR,
    config=None,
) -> np.ndarray:
    """Measured DAM AS-scarcity overlay as a post-solve $/MWh system-price adder.

    The day-ahead analogue of :func:`ercot_rtordpa_overlay_series`. ERCOT's DAM
    co-optimizes energy and ancillary services; on hours where AS cleared into
    scarcity the AS clearing price (MCPC) jumps from competitive single-digits to
    hundreds/thousands, and that scarcity rent lifts the day-ahead *energy* price
    through the shared co-optimization (settled DAM SPP = energy LMP + the binding
    reserve/AS price). The energy+reserve LP forms only the energy dual (plus an
    endogenous ORDC reserve adder); in hours that are not physically reserve-thin
    in the model — the grounded May-2024 case (May 8/24/26), where load is elevated
    but headroom is ample — it cannot form this DAM co-optimization scarcity, so it
    under-prices those acute days. Adding the measured **binding AS MCPC** (the
    per-hour max across RegUp/RRS/ECRS/NonSpin, the product whose scarcity a
    marginal energy unit's opportunity cost tracks) on the scarce hours is the
    published additive co-optimization identity — additive to, not a re-pricing of,
    the energy dual.

    Read **per year** from
    ``data/raw/ercot/ercot_<year>_dam_as_mcpc_hourly.parquet`` (the ``binding_mcpc``
    column), built by ``scripts/build_ercot_dam_as_mcpc.py`` from the 60-Day DAM
    Disclosure — an exogenous ERCOT-published quantity, backcast-able on any year
    from the same forward driver (next year's published DAM AS MCPCs), responsive
    to changed conditions (a tighter/looser AS market reprices), never fit to LMP.

    Gating, all of which keep the overlay inert outside genuine DAM AS scarcity:
      * **scarcity threshold** — hours with ``binding_mcpc <= scarcity_threshold``
        (competitive AS clearing) add 0; the overlay equals ``binding_mcpc`` only
        where the AS demand curve priced into scarcity, so incidence lands on the
        acute days and the broad mid-range is untouched;
      * **regime gate** — pre-RTC+B only (RTC+B retired the adders 2025-12-05),
        identical to the RTORDPA overlay (2025 hours >= ``RTCB_GOLIVE_HOUR``
        zeroed; year >= 2026 / ``ercot_market_design='rtcb'`` inert);
      * **from-year scope** — inert before ``from_year`` (default 2024) so the
        2023 day-ahead AS scarcity, already carried by the RTORDPA overlay, is not
        double-counted (see :data:`_ERCOT_DAM_AS_OVERLAY_FROM_YEAR`).
    Missing files / uncovered hours (the 60-day-lag Nov-Dec tail) and NaN map to 0.
    """
    out = np.zeros(int(hours), dtype=float)
    if int(year) < int(from_year):
        return out
    regime_ordc = (
        ercot_market_regime(year, config) == "ordc"
        if config is not None
        else year < _RTCB_FIRST_FULL_YEAR
    )
    if not regime_ordc:
        return out
    path = RAW_DATA_DIR / "ercot" / _ERCOT_DAM_AS_MCPC_TMPL.format(year=year)
    if not path.exists():
        return out
    import pandas as pd

    df = pd.read_parquet(path, columns=["hour", "binding_mcpc"])
    s = df.set_index("hour")["binding_mcpc"].reindex(range(int(hours)))
    vals = np.nan_to_num(s.to_numpy(dtype=float), nan=0.0)
    # Apply only the scarcity-priced rent; competitive AS clearing adds nothing.
    vals = np.where(vals > float(scarcity_threshold), vals, 0.0)
    n = min(len(vals), len(out))
    out[:n] = vals[:n]
    # Within-2025 calendar cut at the RTC+B go-live (the measured series is already
    # NaN past it, but mirror the RTORDPA belt-and-suspenders gate).
    if year == _RTCB_FIRST_FULL_YEAR - 1:
        out[RTCB_GOLIVE_HOUR:] = 0.0
    return out


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
            f"ercot_market_design must be 'auto', 'ordc' or 'rtcb', got {design!r}"
        )
    return "ordc" if year < _RTCB_FIRST_FULL_YEAR else "rtcb"


def effective_reliability_deployment_mw(year: int, config) -> float:
    """Return the reliability-deployment reserve offset (MW) for the regime.

    The ORDC regime carries **no** offset: the formulaic online/offline
    reserve split plus measured AS-plan netting sets the reserve requirement
    directly. Under RTC+B the forward scenario offset is
    ``rtcb_reliability_deployment_mw`` (default 0 — price to fundamentals),
    which a scenario can raise to model 2023-style conservatism recurring.
    """
    if ercot_market_regime(year, config) == "ordc":
        return 0.0
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
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
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
    widths = grid[:-1] - grid[1:]  # (n_steps,), positive
    r_edge = grid[1:]  # lower reserve edge of each band
    lolp_full = lolp(r_edge, mu_mw, sigma_mw, mcl_mw, shift_sigma)
    lolp_half = lolp(r_edge, mu_mw / 2.0, sigma_mw / np.sqrt(2.0), mcl_mw, shift_sigma)
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

    Returns ``(hours,)`` MW, zero-padded if short and **all-zero when the file
    is absent**. ``ercot_2023_as_up_mw.parquet`` is built by
    ``scripts/build_ercot_as_2023.py`` from the 60-Day DAM Disclosure: its
    ``rrsufr_mw`` is the measured 2023 load-side RRS *shape* (RRS_req minus
    cleared generator PFR/FFR), level-anchored to the measured cleared RRS-UFR
    (NP3-911 Dec-2023 = 896 MW; 2024/2025 = 904 / 787 MW), with the Dec tail
    taken directly from the NP3-911 2-Day feed. The 60-Day Load_Resource file is
    *offers* (~1.5 GW, ~2x cleared), so the cleared level is cross-source
    calibrated rather than read directly — see that script's docstring.
    """
    path = _ERCOT_AS_DIR / f"ercot_{year}_as_up_mw.parquet"
    if not path.exists():
        return np.zeros(int(hours), dtype=float)
    import pandas as pd

    series = pd.read_parquet(path)["rrsufr_mw"].to_numpy(dtype=float)
    if len(series) < hours:
        series = np.concatenate([series, np.zeros(int(hours) - len(series))])
    return series[: int(hours)]


def ercot_lr_rrs_enrolled_mw(year: int) -> float:
    """Forecast Load-Resource RRS-UFR enrolled MW for ``year`` (enrollment trend).

    The forward analogue of the measured cleared RRS-UFR *level*: a forecast of how
    much demand-response capacity is enrolled to provide ERCOT's load-side
    Responsive Reserve (RRS-UFR), a growing market/policy trend. Linear growth off
    the present ~0.9 GW anchor (:data:`ERCOT_LR_RRS_ENROLL_BASE_MW` at
    :data:`ERCOT_LR_RRS_ENROLL_BASE_YEAR`) at
    :data:`ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR`, saturating at the protocol-bounded
    :data:`ERCOT_LR_RRS_ENROLL_CAP_MW` (~1.4 GW). A forward-reproducible enrollment
    trajectory — it regenerates for any forecast year and responds to changed
    conditions — never the measured cleared MW pinned to a price (CLAUDE.md #12).
    """
    enrolled = ERCOT_LR_RRS_ENROLL_BASE_MW + ERCOT_LR_RRS_ENROLL_GROWTH_MW_PER_YR * (
        int(year) - ERCOT_LR_RRS_ENROLL_BASE_YEAR
    )
    return float(np.clip(enrolled, 0.0, ERCOT_LR_RRS_ENROLL_CAP_MW))


def ercot_lr_rrs_availability_shape(hours: int) -> np.ndarray:
    """``(hours,)`` hour-of-day availability shape for load-resource RRS-UFR, mean 1.

    The deterministic calendar shape (:data:`ERCOT_LR_RRS_AVAILABILITY_HOD`)
    normalized to a mean of exactly 1 so it redistributes — never rescales — the
    enrolled annual-mean level: Load Resources are large industrial facilities most
    available to be tripped during weekday daytime/evening operating hours and
    modestly less so in the deep overnight. Tiled across the non-leap 8760-hour
    fleet clock with no Python loop over hours (CLAUDE.md: vectorize the hour axis).
    """
    hod = np.asarray(ERCOT_LR_RRS_AVAILABILITY_HOD, dtype=float)
    hod = hod / hod.mean()  # conserve the enrolled annual-mean level exactly
    T = int(hours)
    return np.tile(hod, T // hod.size + 1)[:T]


def ercot_load_resource_reserve_forward_mw(year: int, hours: int) -> np.ndarray:
    """Forward enrollment-driven load-resource RRS-UFR supply, ``(hours,)`` MW.

    ``lr_rrs(t) = enrolled_MW(year) x availability_shape(t)`` — the forecast branch
    of the load-resource credit (G4). ``enrolled_MW`` is the forward DR-enrollment
    trajectory (:func:`ercot_lr_rrs_enrolled_mw`) and ``availability_shape`` the
    mean-1 hour-of-day shape (:func:`ercot_lr_rrs_availability_shape`), so the
    annual-mean credited MW equals the enrolled level and the hourly profile follows
    industrial operating hours. Replaces the read of the measured NP3-911 series in
    forecast mode; the measured series stays the backcast realization to validate
    against. Forward response: DR enrollment grows -> more load-side reserve supply
    -> fewer scarcity hours. Fully vectorized.
    """
    return ercot_lr_rrs_enrolled_mw(year) * ercot_lr_rrs_availability_shape(hours)


def ercot_load_resource_reserve_credit_mw(
    config, hours: int, year: int | None = None
) -> np.ndarray:
    """Mode-aware load-resource RRS-UFR reserve credit, ``(hours,)`` MW.

    The single seam both co-opt input builders read for the load-resource (RRS-UFR)
    reserve-supply credit (G4). **Backcast** returns the measured NP3-911 realization
    (:func:`ercot_load_resource_reserve_mw`) — byte-identical to the legacy path, the
    validation target. **Forecast** returns the enrollment-driven forward forecast
    (:func:`ercot_load_resource_reserve_forward_mw`), so the dispatch validated in
    backcast is the dispatch forecast (rule #10) and the credit regenerates and grows
    with DR enrollment forward. ``year`` is the simulation year (defaults to
    ``config.weather_year``; in backcast the two coincide, in forecast the runner
    threads the evolving simulated year so enrollment grows year over year).
    """
    yr = int(config.weather_year if year is None else year)
    if str(getattr(config, "mode", "forecast")) == "backcast":
        return ercot_load_resource_reserve_mw(yr, int(hours))
    return ercot_load_resource_reserve_forward_mw(yr, int(hours))


def ercot_storage_as_reserve_mw(year: int, hours: int) -> np.ndarray:
    """ERCOT's measured hourly storage-provided AS-up MW for ``year``.

    (the per-resource-type 60-Day DAM AS awards): the RegUp/RRS/ECRS cleared by
    **batteries** (~1.25 GW in 2023 → ~2.0 GW 2024 → ~2.8 GW 2025 as the fleet
    grew; all three measured from the Gen Resource Data awards, the 2023 series
    built by ``scripts/build_ercot_as_by_restype_from_60day.py``, save an
    Oct-2023 disclosure-file gap that zero-fills). This is responsive reserve
    ERCOT's RTOLCAP/RTOFFCAP count toward the
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


_ERCOT_ASPLAN_DIR = RAW_DATA_DIR / "ercot"


def ercot_ecrs_requirement_mw(year: int, hours: int) -> np.ndarray:
    """ERCOT's measured hourly **ECRS** reserve-plan MW for ``year``.

    ECRS (ERCOT Contingency Reserve Service) launched **2023-06-10** and procures
    ~2 GW of additional responsive reserve that is held *out of the energy stack*
    every hour it is active. The co-opt LP models a single contingency-reserve
    product (the ORDC demand curve from ``ordc_mcl_mw`` + LOLP); it never grew
    when ECRS was introduced, so it under-states the reserve the market actually
    holds in every hour from mid-2023 on and under-prices the broad
    "tight-but-not-scarce" mid-range (2023-H2 + all of 2024/25). Adding this MW to
    the reserve-balance RHS is the demand-side mirror of the load/storage *supply*
    credits: it raises the absolute reserve level the ORDC steps are priced at, so
    the marginal step prices higher across moderate-headroom hours.

    The series is the ``ECRS`` rows of the measured ERCOT AS plan
    ``data/raw/ercot/ASPLANNP433_<year>.parquet`` (``AncillaryType``/``Quantity``
    by ``DeliveryDate``/``HourEnding``) — an ERCOT-published procurement quantity,
    **not** fitted to any price target. The file's real June-2023 onset is
    preserved automatically (pre-onset hours have no ECRS rows → 0 MW), so no
    start date is hard-coded. Mapped onto the fleet's non-leap 8760-hour calendar
    clock (Feb-29 dropped); DST fall-back duplicate hours are averaged. Returns
    ``(hours,)`` MW, **all-zero when the file is absent** (no-op).
    """
    return ercot_as_plan_requirement_mw(year, hours, "ECRS")


def ercot_as_plan_requirement_mw(year: int, hours: int, as_type: str) -> np.ndarray:
    """ERCOT's measured hourly AS-plan procurement MW for one ``as_type``.

    Generalizes :func:`ercot_ecrs_requirement_mw` to any AncillaryType in the
    published AS Plan ``data/raw/ercot/ASPLANNP433_<year>.parquet`` — the upward
    products ``REGUP`` / ``RRS`` / ``ECRS`` / ``NSPIN`` (and ``REGDN``, the
    downward product the upward co-opt ignores). This is the **measured
    realization** of each product's requirement, used to validate the forward
    requirement-setting formula (P1b) against; it is an ERCOT-published
    procurement quantity, never fitted to a price. A product not yet launched in
    ``year`` (e.g. ECRS before 2023-06-10) simply has no rows → all-zero, so the
    onset is carried by the data with no hard-coded start date.

    Mapped onto the fleet's non-leap 8760-hour calendar clock (Feb-29 dropped);
    DST fall-back duplicate hours are averaged. Returns ``(hours,)`` MW,
    **all-zero when the file or the product is absent** (no-op).
    """
    path = _ERCOT_ASPLAN_DIR / f"ASPLANNP433_{year}.parquet"
    if not path.exists():
        return np.zeros(int(hours), dtype=float)
    import pandas as pd

    df = pd.read_parquet(path)
    df = df[df["AncillaryType"] == str(as_type)].copy()
    if df.empty:
        return np.zeros(int(hours), dtype=float)
    dt = pd.to_datetime(df["DeliveryDate"])
    df = df[dt.dt.year == int(year)]  # the file spills a few days into year+1
    if df.empty:
        return np.zeros(int(hours), dtype=float)
    dt = pd.to_datetime(df["DeliveryDate"])
    hod = df["HourEnding"].str.slice(0, 2).astype(int) - 1  # HE 01:00→0 … 24:00→23
    key = df.groupby([dt.dt.month, dt.dt.day, hod])["Quantity"].mean().to_dict()
    out = np.zeros(int(hours), dtype=float)
    i = 0
    for day in pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D"):
        if day.month == 2 and day.day == 29:
            continue  # fleet clock is non-leap
        for h in range(24):
            if i >= hours:
                break
            out[i] = float(key.get((day.month, day.day, h), 0.0))
            i += 1
    return out


def ercot_as_forward_drivers(
    system_load: np.ndarray, wind_gen: np.ndarray, solar_gen: np.ndarray
) -> dict[str, np.ndarray]:
    """Compute the forward ERCOT AS-requirement drivers from forecast profiles.

    The forward requirement formulas (:func:`ercot_as_forward_requirement_mw`) are
    functions of forecast net-load, the net-load up-ramp, VRE share, and the
    net-load day-ahead forecast-error standard deviation. All four derive from the
    same three forecast series the dispatch already builds — total system load and
    total wind / solar generation — so the requirement regenerates for a forecast
    year and grows automatically as VRE capacity (hence ``wind_gen`` / ``solar_gen``)
    grows.

    Args:
        system_load: ``(T,)`` total served load MW per hour.
        wind_gen: ``(T,)`` total wind generation MW per hour (cap x CF).
        solar_gen: ``(T,)`` total solar generation MW per hour (cap x CF).

    Returns:
        A dict of ``(T,)`` driver arrays: ``net_load``, ``vre_share``,
        ``sigma_fe`` (net-load DA forecast-error std), ``ramp_up`` (forward
        net-load up-ramp over ``ERCOT_AS_RAMP_WINDOW_HOURS``), plus the raw
        ``load`` / ``wind`` / ``solar``.
    """
    load = np.asarray(system_load, dtype=float)
    wind = np.asarray(wind_gen, dtype=float)
    solar = np.asarray(solar_gen, dtype=float)
    net_load = load - wind - solar
    vre_share = (wind + solar) / np.maximum(load, 1.0)
    # Net-load DA forecast-error std: independent load/wind/solar errors in
    # quadrature (solar's relative error dominates the VRE-driven growth).
    sigma_fe = np.sqrt(
        (ERCOT_AS_FE_FRAC_LOAD * load) ** 2
        + (ERCOT_AS_FE_FRAC_WIND * wind) ** 2
        + (ERCOT_AS_FE_FRAC_SOLAR * solar) ** 2
    )
    # Forward net-load up-ramp over the deployment window: the largest positive
    # net-load swing within the next W hours of t (the solar-evening ramp ECRS is
    # sized to cover). Cyclic (np.roll) so the 8760 horizon has no edge gap; no
    # Python loop over hours (CLAUDE.md rule: vectorize the hour axis).
    w = int(ERCOT_AS_RAMP_WINDOW_HOURS)
    swings = [np.roll(net_load, -k) - net_load for k in range(1, w + 1)]
    ramp_up = np.clip(np.maximum.reduce(swings), 0.0, None)
    return {
        "load": load,
        "wind": wind,
        "solar": solar,
        "net_load": net_load,
        "vre_share": vre_share,
        "sigma_fe": sigma_fe,
        "ramp_up": ramp_up,
    }


def ercot_as_forward_requirement_mw(
    config,
    product_code: str,
    hours: int,
    drivers: dict[str, np.ndarray] | None = None,
) -> np.ndarray | None:
    """Forward AS requirement for one product, or ``None`` to use the measured one.

    The forward analogue of reading ``ASPLANNP433`` — ERCOT sizes each AS product
    from forward drivers it publishes (net-load forecast-error quantiles, net-load
    ramp risk, largest-contingency / load-ratio shares; NP3-160-CD "Methodology for
    Setting Day-Ahead and Real-Time Ancillary Service Requirements"). When
    ``config.ercot_as_forward_requirement`` is set **and** the forecast ``drivers``
    are supplied (:func:`ercot_as_forward_drivers`), this returns
    ``req_product(t) = f(net_load, ramp, VRE_share, sigma_fe)`` for the product;
    otherwise it returns ``None`` so the caller falls back to the measured
    ASPLANNP433 realization (the validation target — the keeper/backcast path).

    The per-product forms (coefficients in ``constants.py``, calibrated to the
    published requirement MW — a procurement quantity, never a price, CLAUDE.md
    #12):

    * **REGUP** = floor + sigma_coef x sigma_fe — regulation covers the within-hour
      net-load variability (a sub-hourly slice of the DA forecast-error std).
    * **RRS** = largest-contingency floor + inertia_coef x VRE_share — the
      frequency-response floor plus a low-inertia adder that rises with VRE.
    * **ECRS** = base + sigma_coef x sigma_fe + ramp_coef x ramp_up — the ~2 GW
      ramp-risk product (forecast-error plus the forward net-load up-ramp).
    * **NSPIN** = base + load_coef x load + ramp_coef x ramp_up — the
      longer-horizon net-load uncertainty reserve, sized as a load-ratio share of
      system load plus the forward net-load up-ramp it covers.

    All clipped to published min/max bands. **Forward response:** more VRE → larger
    ``sigma_fe`` / ``ramp_up`` / ``vre_share`` → larger requirement, automatically.

    Returns ``(hours,)`` MW, or ``None`` to defer to the measured requirement.
    """
    if not getattr(config, "ercot_as_forward_requirement", False):
        return None
    if drivers is None:
        # Forward requested but the forecast drivers were not threaded through —
        # defer to the measured requirement rather than guess.
        return None
    sigma = drivers["sigma_fe"]
    code = str(product_code).upper()
    if code == "REGUP":
        req = ERCOT_AS_REGUP_FLOOR_MW + ERCOT_AS_REGUP_SIGMA_COEF * sigma
        req = np.clip(req, ERCOT_AS_REGUP_MIN_MW, ERCOT_AS_REGUP_MAX_MW)
    elif code == "RRS":
        req = (
            ERCOT_AS_RRS_FLOOR_MW + ERCOT_AS_RRS_INERTIA_COEF_MW * drivers["vre_share"]
        )
        req = np.clip(req, ERCOT_AS_RRS_FLOOR_MW, ERCOT_AS_RRS_MAX_MW)
    elif code == "ECRS":
        req = (
            ERCOT_AS_ECRS_BASE_MW
            + ERCOT_AS_ECRS_SIGMA_COEF * sigma
            + ERCOT_AS_ECRS_RAMP_COEF * drivers["ramp_up"]
        )
        req = np.clip(req, ERCOT_AS_ECRS_MIN_MW, ERCOT_AS_ECRS_MAX_MW)
    elif code == "NSPIN":
        req = (
            ERCOT_AS_NSPIN_BASE_MW
            + ERCOT_AS_NSPIN_LOAD_COEF * drivers["load"]
            + ERCOT_AS_NSPIN_RAMP_COEF * drivers["ramp_up"]
        )
        req = np.clip(req, ERCOT_AS_NSPIN_MIN_MW, ERCOT_AS_NSPIN_MAX_MW)
    else:
        # Unknown product (e.g. REGDN, which the upward co-opt ignores): defer.
        return None
    out = np.asarray(req, dtype=float)
    if out.size >= int(hours):
        return out[: int(hours)]
    return np.concatenate([out, np.zeros(int(hours) - out.size)])


_ERCOT_ORDC_RESERVES_DIR = RAW_DATA_DIR / "ercot"

# Sentinel "no cap" MW for the reserve-supply-cap rows: larger than any ERCOT
# reserve-eligible fleet (~70-90 GW), so an uncapped hour's row never binds.
_RESERVE_SUPPLY_CAP_UNCAPPED_MW = 1.0e9


def _ercot_rtolcap_fwd_month() -> np.ndarray:
    """Calendar month (1-12) for each of the 8760 non-leap hour-of-year slots."""
    import pandas as pd

    return pd.date_range("2023-01-01", periods=8760, freq="h").month.to_numpy()


def _ercot_rtolcap_fwd_decile(net_load: np.ndarray) -> np.ndarray:
    """Within-year net-load percentile bin (0..N_DECILE-1) per hour, vectorized.

    Rank the year's net-load and bucket into equal-count bins — the driver axis
    the derived on-line share conditions on. A forecast year ranks its OWN
    net-load, so the mapping regenerates and a changed VRE build shifts which
    hours fall in which bin (rule #10). No per-hour Python loop.
    """
    n = len(net_load)
    order = np.argsort(np.argsort(net_load))  # ascending rank per hour
    return np.minimum(
        (order * ERCOT_RTOLCAP_FWD_N_DECILE) // max(n, 1),
        ERCOT_RTOLCAP_FWD_N_DECILE - 1,
    )


def ercot_online_cap_extreme_bin(net_load: np.ndarray) -> np.ndarray:
    """Extreme-peak-resolved net-load percentile bin (0..13) per hour, vectorized.

    The G-22 extreme-peak refinement of :func:`_ercot_rtolcap_fwd_decile`
    (``docs/handoffs/ercot-online-capacity-envelope-2026-07.md`` §5): bins 0–8
    are the bottom nine deciles unchanged; the TOP decile is resolved into five
    equal-count 2-percentile sub-bins (bins 9–13 = ranks [90,92) … [98,100)), so
    the on-line-capacity share/deliverability can carry the measured commitment
    saturation in the extreme tail instead of collapsing it to the decile-9
    median (the ercot41 top-2% room collapse). The 2-pp grain is the finest
    equal-count refinement with ≥~500 pooled hours per cell across the three
    source years (~175 h/yr), and bin 13 is exactly the top-2% regime where the
    measured room-collapse was diagnosed — a uniform refinement of the existing
    axis, not a bespoke threshold (rules #11/#13). Within-year ranking: a
    forecast year ranks its OWN net-load, so the mapping regenerates (rule #10).
    """
    n = max(len(net_load), 1)
    order = np.argsort(np.argsort(net_load))  # ascending rank per hour
    dec = np.minimum((order * 10) // n, 9)
    # 2-pp sub-bins: rank fifties 45..49 → sub 0..4 within the top decile.
    sub = np.minimum((order * 50) // n - 45, 4)
    return np.where(dec < 9, dec, 9 + np.maximum(sub, 0))


def ercot_online_storage_reserve_mw(config, hours: int) -> np.ndarray:
    """Mode-aware ERCOT on-line storage responsive-reserve MW, ``(hours,)``.

    The storage term of the forward RTOLCAP supply cap
    (:func:`ercot_rtolcap_forward_supply_cap_mw`). Mode-aware exactly like the G4
    load-resource credit: **backcast** returns the measured storage-AS series
    (:func:`ercot_storage_as_reserve_mw`, an admissible measured procurement
    quantity, never a price), so the one-delta probe holds the storage term at its
    measured value and isolates the thermal supply formula as the single change.
    **Forecast** returns the model storage fleet's installed discharge power ×
    :data:`ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC` (ERCOT's observed AS-award /
    installed-storage ratio), so the storage reserve grows as the fleet grows.
    """
    if str(getattr(config, "mode", "forecast")) == "backcast":
        return ercot_storage_as_reserve_mw(int(config.weather_year), int(hours))
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.storage import build_default_storage

    units = build_default_storage(get_iso_config("ERCOT"), config)
    power = float(sum(u.power_cap_mw for u in units))
    return np.full(int(hours), power * ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)


def ercot_rtolcap_forward_supply_cap_mw(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    *,
    net_load: np.ndarray,
    storage_reserve: np.ndarray | None = None,
) -> np.ndarray | None:
    """ERCOT's FORWARD online-responsive reserve-supply cap, ``(n_rows, hours)`` MW.

    The WS-A forward analogue of the measured
    :func:`ercot_rtolcap_supply_cap_mw` — the last AS-path lever with no forward
    analogue (``docs/handoffs/ercot-rtolcap-forward-2026-07.md``). Rebuilt entirely
    from the model's own forecast net-load, the derived per-class on-line
    headroom-realization shares and the fleet's evolving reserve-eligible
    capacity, so the cap regenerates for a forecast year and responds to changed
    conditions:

        RTOLCAP_fwd(t)  = deliv × Σ_c online_share_c(nl_bin(t), season(t)) × cap_c(t)
                          + online_storage_power(t)
        RTOFFCAP_fwd(t) = deliv × Σ_{c∈quick} offline_share_c(nl_bin(t), season(t)) × cap_c(t)

    * ``online_share_c`` / ``offline_share_c`` — the derived
      (:data:`ERCOT_RTOLCAP_FWD_ONLINE_SHARE` /
      :data:`~market_sim.config.constants.ERCOT_RTOLCAP_FWD_OFFLINE_SHARE`) median
      class reserve-realization fraction, conditioned on the net-load percentile
      bin and season (``scripts/derive_ercot_rtolcap_forward.py``). RTOLCAP is the
      on-line *headroom* (HSL − basepoint) an ORDC deployment can call, so the
      share is a headroom fraction of installed capacity (a rule-#11 finding — the
      measured series is ~1.8× the fleet's 10-min ramp; the ramp physics still
      gates the RTOFFCAP quick-start eligibility). Higher net-load ⇒ lower share ⇒
      lower cap, so reserves tighten on the tight evenings scarcity actually fires.
    * ``cap_c(t)`` — the class's installed reserve-eligible capacity from
      ``fleet_arrays`` (summer-derated per hour, matching the derive base);
      regenerates as the fleet evolves.
    * ``deliv`` — :data:`ERCOT_RTOLCAP_FWD_DELIV_COEF`, fit to the measured RTOLCAP
      MW quantity (never a price).

    The formula NEVER reads the LP's own commitment/output state and never couples
    reserve to dispatch ``P`` (anti-F3/F4). Row shape mirrors the measured cap:
    two rows (fast/spinning at RTOLCAP, all tier at RTOLCAP+RTOFFCAP) under the
    multi-product stack, else one. Returns ``None`` when the fleet has no
    ``plant_group`` (the forward base cannot be built; caller runs uncapped).
    """
    from market_sim.data.fleet import _SUMMER_CLASS_DERATE

    T = int(hours)
    plant_group = getattr(fleet_arrays, "plant_group", None)
    if plant_group is None:
        return None
    plant_group = np.asarray(plant_group)
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)

    nl = np.asarray(net_load, dtype=float)
    if nl.size < T:
        nl = np.concatenate([nl, np.full(T - nl.size, nl.mean() if nl.size else 0.0)])
    nl = nl[:T]

    month = _ercot_rtolcap_fwd_month()[:T]
    season = np.asarray(ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH, dtype=int)[month - 1]
    decile = _ercot_rtolcap_fwd_decile(nl)
    summer = np.isin(month, [6, 7, 8, 9])  # Jun-Sep ambient-derate window

    def _tier_mw(share_tbl: dict, classes) -> np.ndarray:
        """Σ_c share_c[season,decile] × summer-derated class capacity, ``(T,)``."""
        out = np.zeros(T, dtype=float)
        for cls in classes:
            cap = float(pmax[plant_group == cls].sum())
            if cap <= 0.0:
                continue
            tbl = np.asarray(share_tbl[cls], dtype=float)  # (N_SEASON, N_DECILE)
            share_t = tbl[season, decile]  # (T,), vectorized gather
            derate = _SUMMER_CLASS_DERATE.get(cls, 0.0)
            cap_t = cap * (1.0 - np.where(summer, derate, 0.0))
            out += share_t * cap_t
        return out

    deliv = float(ERCOT_RTOLCAP_FWD_DELIV_COEF)
    if storage_reserve is None:
        storage_reserve = np.zeros(T, dtype=float)
    storage = np.asarray(storage_reserve, dtype=float)[:T]
    if storage.size < T:
        storage = np.concatenate([storage, np.zeros(T - storage.size)])

    rtolcap = deliv * _tier_mw(
        ERCOT_RTOLCAP_FWD_ONLINE_SHARE, ERCOT_RTOLCAP_FWD_ONLINE_CLASSES
    )
    rtolcap = rtolcap + storage
    if getattr(config, "ercot_multiproduct_as_coopt", False):
        rtoffcap = float(ERCOT_RTOLCAP_FWD_OFFLINE_DELIV_COEF) * _tier_mw(
            ERCOT_RTOLCAP_FWD_OFFLINE_SHARE, ERCOT_RTOLCAP_FWD_OFFLINE_CLASSES
        )
        cap = np.vstack([rtolcap, rtolcap + rtoffcap])  # (2, T)
    else:
        cap = rtolcap.reshape(1, T)  # (1, T)
    return cap.astype(float)


def ercot_online_capacity_envelope_mw(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    *,
    net_load: np.ndarray,
    headroom_eligible: np.ndarray,
    headroom_products: np.ndarray,
) -> np.ndarray | None:
    """ERCOT's committed on-line-CAPACITY envelope, ``(n_hr, hours)`` MW.

    The G-22 commitment-thinness structure (``config.ercot_online_capacity_envelope``;
    ``docs/FINDING-ercot-priceshape-2026-07.md`` §3, structural conclusion #2). The
    multi-product co-opt's shared-headroom rows bound
    ``Σ_{elig thermal} P + Σ_prod R ≤ cap(full fleet)`` — the RHS is every
    reserve-eligible thermal unit's *full availability-derated* capacity, so a
    perfect-foresight P1 LP can serve energy (or hold reserve) from cold
    slow-start MW the real system never had on-line. ``ercot_reserve_supply_cap``
    caps only the cleared RESERVE (``Σ R ≤ RTOLCAP``); the ENERGY term still draws
    on the fat RHS, leaving ~3.2 GW of phantom sub-$200 spare beyond the measured
    on-line capability in the missed 2023 tail hours — so the energy dual sits at
    ~$45 where SCED cleared $600+.

    This returns, per shared-headroom tier, a **system-wide** MW cap
        ``online_cap_env(t) = deliv × Σ_c online_cap_share_c(nl,season) × cap_c(t)``
    the committed on-line HSL of the tier's responsive classes
    (:data:`~market_sim.config.constants.ERCOT_ONLINE_CAP_SHARE` /
    :data:`~market_sim.config.constants.ERCOT_ONLINE_CAP_DELIV_COEF`, derived from
    the committed CAMPD extracts, ``scripts/derive_ercot_rtolcap_forward.py
    --emit online-cap-constant``). ``model.dispatch._build_reserve_rows`` imposes
    ``Σ_z Σ_{g∈E_h∩z} P[g] + Σ_z Σ_{p∈Prod_h} R[p,z] ≤ online_cap_env[h,t]`` on the
    envelope tiers, so the LP cannot dispatch OR reserve more thermal than the
    committed on-line capacity. Because the ENERGY term is on the LHS the cap is
    **condition-responsive**: in slack hours the cap sits well above the low
    dispatch and never binds; in the high-energy tight hours it binds, forcing
    reserve into shortage → the ORDC/co-opt reserve-shortage channel prices the
    hour up (the same channel that already prices the caught hours) with **no
    offer-height change** (rule #1). The cap is anchored to the measured RTOLCAP
    series (``online_cap_env − dispatch`` reproduces its level/band/coverage; the
    anti-F1 identification gate ``scripts/validate_ercot_online_capacity.py``),
    never to the price residual (rules #13/#14/#23).

    Applied to the **all-responsive tier(s) only** — a tier whose
    ``headroom_products`` bounds every AS product (the total online-thermal
    constraint that carries the wedge). Non-all tiers (the fast/spinning tier,
    already bounded by the RTOLCAP reserve-supply cap) return the uncapped
    sentinel :data:`_RESERVE_SUPPLY_CAP_UNCAPPED_MW`, so they add a (harmless)
    always-slack row and never over-constrain the spinning fleet. The formula
    NEVER reads the LP's own commitment/output state (anti-F3/F4) and never a
    price. Returns ``None`` (uncapped) when the gate is off or the fleet has no
    ``plant_group``.

    **Extreme-peak-resolved variant** (``config.ercot_online_capacity_envelope_
    extreme``, the filed G-22 §5 path after the ercot41 rejection): identical LP
    row, but the driver resolution changes — the share table is resolved on 14
    net-load bins (:func:`ercot_online_cap_extreme_bin`; the top decile at
    2-percentile grain, carrying the measured CAMPD commitment saturation the
    decile-9 median collapsed) and the scalar deliverability becomes a per-bin
    profile fit to the measured thermal on-line HSL identity (CAMPD gross +
    RTOLCAP − storage AS − LR credit), so the envelope reproduces the measured
    on-line capability in the extreme tail (top-2%) instead of collapsing the
    room there (:data:`~market_sim.config.constants.ERCOT_ONLINE_CAP_SHARE_EXTREME`
    / :data:`~market_sim.config.constants.ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME`,
    ``--emit online-cap-extreme-constant``). Mutually exclusive with the base
    flag (``ScenarioConfig.__post_init__`` hard error).
    """
    from market_sim.data.fleet import _SUMMER_CLASS_DERATE

    extreme = bool(getattr(config, "ercot_online_capacity_envelope_extreme", False))
    measured = bool(getattr(config, "ercot_online_capacity_envelope_measured", False))
    if not (
        getattr(config, "ercot_online_capacity_envelope", False) or extreme or measured
    ):
        return None
    T = int(hours)
    plant_group = getattr(fleet_arrays, "plant_group", None)
    if plant_group is None:
        return None
    plant_group = np.asarray(plant_group)
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)
    elig = np.atleast_2d(np.asarray(headroom_eligible, dtype=bool))  # (n_hr, n_gen)
    prod = np.atleast_2d(np.asarray(headroom_products, dtype=bool))  # (n_hr, n_prod)
    n_hr = elig.shape[0]
    n_prod = prod.shape[1]

    nl = np.asarray(net_load, dtype=float)
    if nl.size < T:
        nl = np.concatenate([nl, np.full(T - nl.size, nl.mean() if nl.size else 0.0)])
    nl = nl[:T]
    month = _ercot_rtolcap_fwd_month()[:T]
    season = np.asarray(ERCOT_RTOLCAP_FWD_SEASON_BY_MONTH, dtype=int)[month - 1]
    summer = np.isin(month, [6, 7, 8, 9])  # Jun-Sep ambient-derate window
    if measured:
        # Measured-fleet-basis variant (the ercot57 joint-round re-identification):
        # same 14-bin extreme driver axis, but for the measured-availability
        # classes the share is committed-HSL ÷ AVAILABLE capacity and the basis is
        # the fleet's finished availability (measured under
        # ercot_thermal_dam_availability in backcast, statistical forward), so
        # commitment choice and outage state are no longer conflated — the
        # decomposition that removes the extreme-tail room collapse (ercot43
        # 2023 top-2% ledger −23%: reality musters near-max availability there,
        # which a share-of-installed pooled median cannot see).
        nl_bin = ercot_online_cap_extreme_bin(nl)
        share_tables = ERCOT_ONLINE_CAP_SHARE_MEASURED
        deliv_t = np.asarray(ERCOT_ONLINE_CAP_DELIV_PROFILE_MEASURED, dtype=float)[
            nl_bin
        ]  # (T,)
    elif extreme:
        # G-22 §5 extreme-peak-resolved variant: 14-bin driver axis + per-bin
        # deliverability, so the envelope carries the measured commitment
        # saturation / capability margin in the extreme tail instead of the
        # decile-9 median that collapsed the top-2% room (ercot41).
        nl_bin = ercot_online_cap_extreme_bin(nl)
        share_tables = ERCOT_ONLINE_CAP_SHARE_EXTREME
        deliv_t = np.asarray(ERCOT_ONLINE_CAP_DELIV_PROFILE_EXTREME, dtype=float)[
            nl_bin
        ]  # (T,)
    else:
        nl_bin = _ercot_rtolcap_fwd_decile(nl)
        share_tables = ERCOT_ONLINE_CAP_SHARE
        deliv_t = float(ERCOT_ONLINE_CAP_DELIV_COEF)  # scalar broadcast

    avail = np.asarray(fleet_arrays.availability, dtype=float)  # (n_gen, T)
    cap = np.full((n_hr, T), _RESERVE_SUPPLY_CAP_UNCAPPED_MW, dtype=float)
    for h in range(n_hr):
        # Only the ALL-responsive tier (bounds every product) carries the energy
        # envelope; the fast/spinning tier stays uncapped (RTOLCAP reserve cap
        # already bounds it) to avoid over-constraining the baseload fleet.
        if not prod[h].all() or n_prod == 0:
            continue
        tier_classes = set(np.unique(plant_group[elig[h]]).tolist())
        out = np.zeros(T, dtype=float)
        for cls in tier_classes:
            tbl = share_tables.get(cls)
            if tbl is None:
                continue
            share_t = np.asarray(tbl, dtype=float)[season, nl_bin]  # (T,), vectorized
            mask = (plant_group == cls) & elig[h]
            if measured and cls in ERCOT_ONLINE_CAP_MEASURED_AVAIL_CLASSES:
                # AVAILABLE-capacity basis: Σ_g pmax × availability(t) over the
                # tier's class members — the same finished availability the LP's
                # generator bounds carry (ambient/outage state included; no
                # separate summer-derate, which the measured HSL fraction
                # already embeds). Matches the deriver's share denominator
                # (measured class-day disclosure fraction × installed).
                cap_ct = (pmax[mask, None] * avail[mask, :T]).sum(axis=0)  # (T,)
            else:
                cap_c = float(pmax[mask].sum())
                if cap_c <= 0.0:
                    continue
                derate = _SUMMER_CLASS_DERATE.get(cls, 0.0)
                cap_ct = cap_c * (1.0 - np.where(summer, derate, 0.0))
            out += share_t * cap_ct
        cap[h] = deliv_t * out
    return cap.astype(float)


def ercot_rtolcap_supply_cap_mw(
    config,
    hours: int,
    fleet_arrays: FleetArrays | None = None,
    *,
    system_load: np.ndarray | None = None,
    wind_gen: np.ndarray | None = None,
    solar_gen: np.ndarray | None = None,
) -> np.ndarray | None:
    """ERCOT's online-responsive reserve-supply cap, ``(n_rows, hours)`` MW.

    Mode-aware seam (like :func:`ercot_load_resource_reserve_credit_mw`, G4):
    **backcast with ``config.ercot_reserve_supply_forward`` off** returns the
    MEASURED series below byte-identical (the validation target); **forecast, or
    the ``ercot_reserve_supply_forward`` probe flag on**, returns the WS-A forward
    formula (:func:`ercot_rtolcap_forward_supply_cap_mw`) built from ``fleet_arrays``
    and the forecast net-load (``system_load − wind_gen − solar_gen``). The forward
    branch falls back to ``None`` (uncapped) when those inputs are not threaded in.

    The reserve-supply re-scope (Finding 1 / G1, the broad-month phantom-headroom
    fix). The ERCOT co-opt's shared-headroom rows count every reserve-eligible
    thermal unit's *full installed* headroom as reserve supply — including cold
    slow-start units a perfect-foresight LP leaves idle but still scores as
    "available" — so modeled reserve never tightens into the ~8-12 GW band where
    ERCOT's ORDC adder actually fires. This caps each headroom row's cleared
    reserve at the **measured** ERCOT on-line responsive reserve capability so
    modeled reserve tracks the real series rather than the over-counted fleet
    headroom. Pre-RTC+B (ORDC regime) the capped reserve dual is then the ORDC
    price adder (RTORPA) added to the energy SPP — the energy-only-SCED-plus-adder
    design of 2023-2025; the measured series is the exogenous supply, the published
    ORDC curve the demand, neither the LMP, RTSPP nor MCPC, so this is a
    supply-definition re-scope, not a price fit (CLAUDE.md #11/#12).

    Shape matches the co-opt's headroom rows:

    * **Single lumped product** (``ercot_multiproduct_as_coopt`` off): one row,
      capped at ``RTOLCAP`` (drives the published on-line ORDC adder, RTORPA).
    * **Multi-product stack** (on): two rows — fast/spinning at ``RTOLCAP`` and the
      all tier (adding quick-start offline peakers) at ``RTOLCAP + RTOFFCAP``.

    Columns come from
    ``data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet``. Returns ``None``
    when the cap is gated off, the weather year predates
    ``ercot_reserve_supply_cap_from_year``, or the file is absent (the co-opt then
    runs uncapped, unchanged). Hours with no measured RTOLCAP (the 2025 RTC+B
    go-live tail after 2025-12-05, preserved as NaN) are left **uncapped** (a
    sentinel large MW), so the cap applies only where the ORDC regime — and the
    measured series — were in force.
    """
    if not getattr(config, "ercot_reserve_supply_cap", False):
        return None
    # Mode-aware source selection (G4 pattern). Forward formula when in forecast
    # mode OR the one-delta probe flag is set; measured parquet otherwise.
    forward = str(getattr(config, "mode", "forecast")) == "forecast" or getattr(
        config, "ercot_reserve_supply_forward", False
    )
    if forward:
        if fleet_arrays is None or system_load is None:
            return None  # forward inputs not threaded in — run uncapped
        wind = (
            np.zeros_like(np.asarray(system_load, dtype=float))
            if wind_gen is None
            else np.asarray(wind_gen, dtype=float)
        )
        solar = (
            np.zeros_like(np.asarray(system_load, dtype=float))
            if solar_gen is None
            else np.asarray(solar_gen, dtype=float)
        )
        net_load = np.asarray(system_load, dtype=float) - wind - solar
        storage = ercot_online_storage_reserve_mw(config, int(hours))
        return ercot_rtolcap_forward_supply_cap_mw(
            config, fleet_arrays, int(hours), net_load=net_load, storage_reserve=storage
        )
    year = int(config.weather_year)
    if year < int(getattr(config, "ercot_reserve_supply_cap_from_year", 2023)):
        return None
    path = _ERCOT_ORDC_RESERVES_DIR / f"ercot_{year}_ordc_reserves_hourly.parquet"
    if not path.exists():
        return None
    import pandas as pd

    df = pd.read_parquet(path)
    T = int(hours)

    def _series(col: str) -> np.ndarray:
        arr = df[col].to_numpy(dtype=float) if col in df.columns else np.array([])
        if len(arr) < T:
            arr = np.concatenate([arr, np.full(T - len(arr), np.nan)])
        return arr[:T]

    rtolcap = _series("rtolcap")  # on-line responsive (spinning) capability
    rtoffcap = _series("rtoffcap")  # off-line quick-start responsive capability
    if getattr(config, "ercot_multiproduct_as_coopt", False):
        # Two headroom tiers: fast/spinning at RTOLCAP, all (+ offline quick-start
        # the Non-Spin product can reach) at RTOLCAP + RTOFFCAP.
        cap = np.vstack([rtolcap, rtolcap + rtoffcap])  # (2, T)
    else:
        # Single lumped product: the on-line responsive capability (RTOLCAP) that
        # drives the published on-line ORDC adder (RTORPA).
        cap = rtolcap.reshape(1, T)  # (1, T)
    # Uncapped where the measured series is NaN (the 2025 RTC+B tail) — the ORDC
    # regime ended, so no reserve-supply cap applies there.
    cap = np.where(np.isnan(cap), _RESERVE_SUPPLY_CAP_UNCAPPED_MW, cap)
    return cap.astype(float)


def pjm_reserve_deliverable_supply_cap_mw(
    config, fleet_arrays: FleetArrays, hours: int
) -> np.ndarray | None:
    """PJM's deliverable (10-min ramp) reserve-supply cap, ``(1, hours)`` MW.

    The PJM analogue of :func:`ercot_rtolcap_supply_cap_mw`, but built from the
    fleet's **10-minute deliverable ramp** capability
    (:attr:`FleetArrays.ramp10` = :data:`~market_sim.data.fleet.RAMP10_FRAC_BY_GROUP`
    × ``pmax``) rather than a measured ERCOT RTOLCAP series — PJM has no such
    published online-capability parquet, but the deliverable slice is the physical
    quantity that can actually be offered into the reserve-deployment window.

    The bare PJM co-opt's single shared-headroom row counts every reserve-eligible
    thermal unit's *full* availability-derated headroom as reserve supply (~38 GW),
    far above the ~3.4 GW Primary requirement, so the published vertical ORDC step
    never fires (``docs/multi-iso/pjm-reserve-ordc.md`` honesty gate). This caps the
    co-opt's single reserve class's cleared reserve at the deliverable 10-min ramp
    of the reserve-eligible fleet, so modeled reserve can tighten toward the
    requirement instead of drawing on idle full-fleet headroom.

    Availability-scaled per hour (an out-of-service unit delivers no reserve). A
    physical deliverability definition (ramp rate × capacity), regenerable for a
    forecast year and responsive to the fleet — never fitted to the LMP residual
    (claude.md #11). Returns ``(1, hours)`` (one row, the single PJM reserve
    class) or ``None`` when gated off (``config.pjm_reserve_supply_cap`` false) or
    ``FleetArrays.ramp10`` is unpopulated (the co-opt then runs uncapped).
    """
    if not getattr(config, "pjm_reserve_supply_cap", False):
        return None
    ramp10 = getattr(fleet_arrays, "ramp10", None)
    if ramp10 is None:
        return None
    eligible = ercot_reserve_eligible(fleet_arrays)  # ISO-agnostic thermal mask
    ramp10 = np.asarray(ramp10, dtype=float)
    avail = np.asarray(fleet_arrays.availability, dtype=float)  # (n_gen, T)
    T = int(hours)
    # Deliverable reserve per hour = Σ over eligible units of their 10-min ramp,
    # availability-scaled. (n_gen,1)*(n_gen,T) -> mask eligible rows -> sum.
    cap = (ramp10[:, None] * avail)[eligible].sum(axis=0)  # (T,)
    return cap.reshape(1, T).astype(float)


def ercot_as_aware_unit_value(
    fleet_arrays: FleetArrays,
    p1_dispatch: np.ndarray,
    reserve_price_by_family: np.ndarray,
    hours: int,
) -> np.ndarray:
    """Return the ``(n_gen, T)`` per-unit-hour AS revenue estimate for commitment.

    The AS-aware commitment screen (``config.ercot_as_aware_commitment``,
    :func:`market_sim.model.commitment.compute_commitment`) values a unit's
    *ancillary-service* revenue, not its energy margin alone, when deciding which
    units stay online. This estimates that revenue from the P1 co-optimization:

        ``as_value[g, t] = reserve_price_proxy[g, t] x headroom[g, t]``

    where ``headroom = pmax x availability - P1_dispatch`` (the MW the unit could
    offer up as reserve, clipped at 0) and ``reserve_price_proxy`` is the binding
    AS clearing price for the products the unit can supply, taken from the model's
    OWN P1 balance-row dual ``reserve_price_by_family`` (shape ``(T, n_prod)``,
    products ordered as :data:`~market_sim.config.constants.ERCOT_AS_PRODUCTS`) —
    never the measured MCPC, so nothing here is fitted to a price.

    The product-eligibility cascade mirrors the co-opt's two shared-headroom rows
    (:func:`ercot_multiproduct_reserve_coopt_inputs`): a synchronized/spinning unit
    (:data:`RESERVE_FUEL_TYPES` minus :data:`QUICK_START_FUEL_TYPES`) can clear
    every product, so its proxy is the per-hour max across ALL products; an
    offline-capable quick-start peaker (gas-CT/oil) can only back a 30-minute
    Non-Spin award, so its proxy is the max across the non-fast (Non-Spin) products
    alone. Units that hold no responsive reserve (wind/solar/hydro/imports) earn
    zero AS value.

    Args:
        fleet_arrays: The P1 vectorized fleet, for ``pmax``, ``availability`` and
            ``fuel_type_idx``.
        p1_dispatch: The P1 dispatch result, ``(n_gen, T)``.
        reserve_price_by_family: The P1 per-product reserve clearing price,
            ``(T, n_prod)`` (``DispatchResult.reserve_price_by_family``).
        hours: Number of hours ``T`` (for shape validation / a no-op fallback).

    Returns:
        The AS-value array, shape ``(n_gen, T)``, in ``$`` per MW-hour committed.
        All-zero when ``reserve_price_by_family`` is missing (co-opt off).
    """
    T = int(hours)
    n_gen = int(fleet_arrays.pmax.shape[0])
    if reserve_price_by_family is None:
        return np.zeros((n_gen, T), dtype=float)
    rp = np.asarray(reserve_price_by_family, dtype=float)  # (T, n_prod)
    if rp.ndim != 2 or rp.shape[0] != T:
        return np.zeros((n_gen, T), dtype=float)
    products = list(ERCOT_AS_PRODUCTS)
    n_prod = rp.shape[1]
    # Per-hour binding price over all products, and over the non-fast (Non-Spin)
    # subset only — the two tiers of the eligibility cascade.
    slow_cols = [
        p for p in range(min(n_prod, len(products))) if products[p][2] != "fast"
    ]
    price_all = rp.max(axis=1) if n_prod else np.zeros(T)  # (T,)
    price_slow = rp[:, slow_cols].max(axis=1) if slow_cols else np.zeros(T)  # (T,)

    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    responsive = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    fast_unit = responsive & ~quick  # spinning set: every product
    # Per-unit price proxy row (T,) broadcast per unit class.
    pmax = np.asarray(fleet_arrays.pmax, dtype=float)
    avail = np.asarray(fleet_arrays.availability, dtype=float)  # (n_gen, T)
    headroom = np.maximum(
        pmax[:, None] * avail - np.asarray(p1_dispatch, dtype=float), 0.0
    )

    as_value = np.zeros((n_gen, T), dtype=float)
    if fast_unit.any():
        as_value[fast_unit] = headroom[fast_unit] * price_all[None, :]
    quick_only = quick & responsive
    if quick_only.any():
        as_value[quick_only] = headroom[quick_only] * price_slow[None, :]
    return as_value


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
    online = reserves_mw if reserves_online_mw is None else reserves_online_mw
    mu, sigma = resolve_lolp_params(config, hours)
    adder = ordc_adder(
        reserves_mw,
        system_lambda,
        voll=config.ordc_voll,
        mcl_mw=config.ordc_mcl_mw,
        mu_mw=mu,
        sigma_mw=sigma,
        shift_sigma=config.ordc_lolp_shift_sigma,
        multistep_floor=config.ordc_multistep_floor,
        floor_active=(
            floor_active_mask(year, hours) if config.mode == "backcast" else True
        ),
        reserves_online_mw=online,
    )
    return {
        "reserves_mw": np.asarray(reserves_mw, dtype=float),
        "reserves_online_mw": np.asarray(online, dtype=float),
        "lolp": lolp(
            reserves_mw, mu, sigma, config.ordc_mcl_mw, config.ordc_lolp_shift_sigma
        ),
        "scarcity_adder": adder,
    }


def ercot_ordc_realized_adder(
    config,
    year: int,
    *,
    design,
    dispatch: np.ndarray,
    prices: np.ndarray,
    demand: np.ndarray,
) -> np.ndarray | None:
    """Post-solve RTORPA on the REALIZED envelope room (ercot57 joint round v2).

    The market-faithful form of ``ercot_ordc_only_scarcity``: pre-RTC+B SCED
    dispatches energy only — reserve beyond the DAM AS plan is never withheld
    by the RT market, and the ORDC prices the REALIZED total online reserves
    post-hoc as an adder (RTSPP = SCED SPP + RTORPA, Nodal Protocols
    §6.5.7.5). The v1 probe (in-LP ORDC total-reserve family + envelope)
    reproduced the ercot43 §7.4 defect on the honest measured fleet: the
    VOLL-floored sub-MCL steps make holding reserve exactly as valuable as
    serving load, so the LP withheld up the full span inside the envelope,
    parked 12.8 GW of coal at the Aug-2023 peak and shed 62 GWh — dispatch and
    prices reality never produced. Here the LP carries only the plan
    withholding (epsilon-held product families + the rigid pre-reform
    ECRS_withheld) and the ORDC values what is left:

        online(t)  = max(env_all(t) − Σ_{g∈elig_all} P[g,t], 0)
                     + measured storage-AS award + LR RRS-UFR credit
        offline(t) = forward RTOFFCAP (supply-cap row 1 − row 0)
        RTORPA(t)  = ordc_adder(online + offline, λ; online) — the published
                     two-half-hour LOLP construction with the OBDRR048 floor.

    ``env_all − ΣP`` is the committed on-line capability headroom the
    measured-fleet-basis envelope was IDENTIFIED to reproduce against measured
    RTOLCAP (``validate_ercot_online_capacity.py --measured``: binding regime
    +4/+0/−3%, pooled top-2% exact), so the reserve level the curve prices is
    the measured quantity's model analogue — and it regenerates for a forecast
    year (envelope basis = the fleet's finished availability; forward RTOFFCAP
    formula; λ from the solve). The storage-AS and LR series count TOWARD the
    level exactly as they count toward measured RTOLCAP (they are netted out
    of nothing here — RTORPA's total online reserves include them). λ is the
    demand-weighted energy dual (the system lambda every settlement point
    shares). Rule 19: mutually exclusive with the in-LP ORDC total-reserve
    family (``ScenarioConfig.__post_init__`` hard error) and with the cap-dual
    adder path in the frame writer — one mechanism prices RT reserve scarcity.

    Returns ``(T,)`` $/MWh, or ``None`` when the design carries no envelope
    (the room quantity is then undefined and the caller must not price).
    """
    # v3: the envelope arrives as the PRICING-ONLY basis (never an LP row —
    # reserve_config moves it to online_capacity_pricing_mw under
    # ercot_ordc_only_scarcity); the online_capacity_cap fallback keeps the
    # function usable on a design that did install the row (diagnostics).
    oc = getattr(design, "online_capacity_pricing_mw", None)
    if oc is None:
        oc = getattr(design, "online_capacity_cap", None)
    if oc is None:
        return None
    oc = np.atleast_2d(np.asarray(oc, dtype=float))
    hp = np.atleast_2d(np.asarray(design.headroom_products, dtype=bool))
    he = np.atleast_2d(np.asarray(design.headroom_eligible, dtype=bool))
    # The all-products tier with a finite (capped) row carries the envelope.
    h_all = None
    for h in range(hp.shape[0]):
        if hp[h].all() and np.all(oc[h] < _RESERVE_SUPPLY_CAP_UNCAPPED_MW):
            h_all = h
            break
    if h_all is None:
        return None
    env = oc[h_all]
    T = env.size
    P = np.asarray(dispatch, dtype=float)[he[h_all], :T].sum(axis=0)
    online = np.clip(env - P, 0.0, None)

    if (
        getattr(config, "ercot_storage_as_reserve", False)
        and getattr(config, "storage_as_commitment", False)
        and not getattr(config, "ercot_storage_as_endogenous", False)
        and year >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))
    ):
        online = online + ercot_storage_as_reserve_mw(year, T)
    if getattr(config, "ercot_load_resource_reserve", False) and year >= int(
        getattr(config, "ercot_load_resource_reserve_from_year", 2023)
    ):
        online = online + ercot_load_resource_reserve_credit_mw(config, T, year=year)

    offline = np.zeros(T, dtype=float)
    sc = getattr(design, "supply_cap", None)
    if sc is not None:
        sc = np.atleast_2d(np.asarray(sc, dtype=float))
        if sc.shape[0] >= 2:
            offline = np.clip(sc[1, :T] - sc[0, :T], 0.0, None)

    d = np.asarray(demand, dtype=float)[:, :T]
    p = np.asarray(prices, dtype=float)[:, :T]
    d_tot = d.sum(axis=0)
    lam = np.where(
        d_tot > 0, (p * d).sum(axis=0) / np.where(d_tot > 0, d_tot, 1.0), p.mean(axis=0)
    )
    return scarcity_prices(
        config, year, online + offline, lam, reserves_online_mw=online
    )["scarcity_adder"]


# ===========================================================================
# CAISO power-balance scarcity pricing overlay
# ===========================================================================
#
# CAISO's scarcity pricing derives from the graduated penalty prices for
# power-balance constraint relaxation (CAISO Tariff §27.4.3.2, BPM for
# Market Operations §6.6.4) and the Flexible Ramping Product (FRP) demand
# curve that prices net-load uncertainty (CAISO FRP Phase 1 stakeholder
# process, 2016; enhanced FRP §27.10). In the real-time market, when
# operating reserves fall below the contingency requirement plus the FRP
# withholding, the market software's penalty prices activate and lift the
# LMP. The perfect-foresight LP structurally misses this: it clears all
# hours with ample headroom and zero scarcity rent.
#
# This post-solve overlay replicates the scarcity rent using the same
# LOLP × (VOLL - λ) functional form as the ERCOT ORDC (proven in this
# codebase), but with CAISO-specific parameters:
#
#     VOLL    = $2,000/MWh — CAISO Tariff §39.6.1 hard energy bid cap
#               (FERC Order 831 compliance, $1,000 soft / $2,000 cost-based).
#     MCL     = 1,400 MW  — Diablo Canyon Unit 1/2 (~1,150 MW nameplate,
#               the largest CAISO generating single contingency per BAL-002-
#               WECC-3; rounded up for the PDCI import contingency backup).
#     sigma   = 2,500 MW  — CAISO net-load forecast error std dev (solar
#               forecast error ~1,500-2,000 MW at 20+ GW installed solar +
#               load forecast error ~500-1,000 MW, combined ~2,000-2,500 MW;
#               CAISO FRP Uncertainty Calculation whitepaper, bounded by the
#               95th-percentile upward FRP requirement 3,500-4,500 MW).
#     shift   = 0.0       — no administrative curve shift (ERCOT's PUCT
#               orders §48551 do not apply to CAISO).
#
# The overlay is $0 in hours where reserves clear comfortably (the vast
# majority), fires during the evening net-load ramp (solar decline drives
# high uncertainty) and heat-wave/import-constraint events, and has a
# forward analogue: VOLL is tariff, MCL tracks the largest contingency,
# sigma scales with renewable penetration. Nothing is fitted to a price
# residual. Mutually exclusive with caiso_reserve_coopt (rule 19).

CAISO_SCARCITY_VOLL: float = 2000.0
CAISO_SCARCITY_MCL_MW: float = 1400.0
CAISO_SCARCITY_SIGMA_MW: float = 2500.0
CAISO_SCARCITY_SHIFT_SIGMA: float = 0.0


def caiso_scarcity_overlay(
    fleet_arrays: FleetArrays,
    dispatch: np.ndarray,
    storage_power_cap: np.ndarray,
    storage_charge: np.ndarray | None,
    storage_discharge: np.ndarray | None,
    renewable_headroom: np.ndarray | None,
    system_lambda: np.ndarray,
) -> np.ndarray:
    """CAISO post-solve scarcity price adder ($/MWh).

    Computes the probabilistic reserve-scarcity adder from the solved
    dispatch, using CAISO tariff-backed parameters. The LOLP is evaluated
    on the same online/offline reserve split as the ERCOT ORDC overlay
    (``reserve_headroom``), and the adder is ``LOLP × (VOLL - λ)`` with
    CAISO's $2,000 cap. Returns a ``(T,)`` array.
    """
    r_online, r_offline = reserve_headroom(
        fleet_arrays,
        dispatch,
        storage_power_cap,
        storage_charge,
        storage_discharge,
        as_plan_mw=0.0,
        renewable_headroom=renewable_headroom,
    )
    return ordc_adder(
        r_online + r_offline,
        system_lambda,
        voll=CAISO_SCARCITY_VOLL,
        mcl_mw=CAISO_SCARCITY_MCL_MW,
        mu_mw=0.0,
        sigma_mw=CAISO_SCARCITY_SIGMA_MW,
        shift_sigma=CAISO_SCARCITY_SHIFT_SIGMA,
        multistep_floor=False,
        reserves_online_mw=r_online,
    )


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
# Parameters live in data/raw/_validation-source/pjm_ordc_curve.csv (cited in
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
    "SR": ("Synchronized", "Primary", "Secondary"),  # SRMCP  = SP_SR+SP_PR+SP_30
    "PR": ("Primary", "Secondary"),  # NSRMCP =       SP_PR+SP_30
    "30MIN": ("Secondary",),  # SecMCP =             SP_30
}


def load_pjm_ordc_curve(
    path: str | Path,
) -> dict[tuple[str, str], list[tuple[float, float]]]:
    """Load the cited PJM ORDC step curve keyed by (service, locale).

    Reads data/raw/_validation-source/pjm_ordc_curve.csv (columns ``service``,
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
        raise ValueError(f"PJM ORDC curve {path} must have columns {sorted(need)}")
    out: dict[tuple[str, str], list[tuple[float, float]]] = {}
    for (svc, loc), grp in df.groupby(["service", "locale"]):
        steps = sorted(
            (float(r.breakpoint_offset_mw), float(r.penalty_factor))
            for r in grp.itertuples()
        )
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
            reserves_by_product[prod],
            requirements_by_product[prod],
            curve_by_product[prod],
        )
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
    year: int,
    hours: int = 8760,
    data_dir: Path = _PJM_AS_DIR,
) -> np.ndarray | None:
    """Return the measured PJM_RTO Primary Reserve requirement (MW), hourly.

    The published reserve requirement (``pr_req_mw`` in
    ``data/raw/PJM-AS/pjm_<year>_as_up_mw.parquet``, derived by
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


def load_pjm_measured_mad_reserve_requirement(
    year: int,
    hours: int = 8760,
    data_dir: Path = _PJM_AS_DIR,
) -> np.ndarray | None:
    """Return the measured MAD-subzone Primary Reserve requirement (MW), hourly.

    The Mid-Atlantic/Dominion Reserve Subzone requirement (Manual 11 sec 4.2:
    the RTO Reserve Zone's one Reserve Subzone) — column ``mad_pr_req_mw`` in
    ``data/raw/PJM-AS/pjm_<year>_as_up_mw.parquet``, built by
    ``scripts/build_pjm_as_withholding.py`` from PJM Data Miner RT reserve
    market results (``locale == "MAD"``, ``service == "PR"``). Like the RTO
    series it is a measured *reliability* quantity (the subzone's contingency
    + deliverability need), not a price actual — admissible per CLAUDE.md #12.
    The per-gen reserve co-optimization uses it as the locational balance
    family's RHS (docs/multi-iso/pjm-reserve-ordc.md Phase 2).

    Returns ``None`` when the parquet is absent or predates the MAD column
    (caller then builds the RTO family only).
    """
    path = Path(data_dir) / f"pjm_{year}_as_up_mw.parquet"
    if not path.exists():
        return None
    import pandas as pd

    df = pd.read_parquet(path)
    if "mad_pr_req_mw" not in df.columns:
        return None
    req = df["mad_pr_req_mw"].to_numpy(dtype=float)
    # Same defensive fill as the RTO loader: holes read as 0; forward/back-fill
    # so the requirement is never spuriously zero.
    if (req <= 0.0).any():
        good = req > 0.0
        if good.any():
            idx = np.where(good, np.arange(len(req)), -1)
            np.maximum.accumulate(idx, out=idx)
            idx[idx < 0] = np.flatnonzero(good)[0]
            req = req[idx]
    if len(req) >= hours:
        return req[:hours]
    return np.resize(req, hours)


def _load_pjm_req_column(
    year: int,
    hours: int,
    column: str,
    data_dir: Path = _PJM_AS_DIR,
) -> np.ndarray | None:
    """Load one hourly requirement column from ``pjm_<year>_as_up_mw.parquet``.

    Shared reader for the measured PJM reserve-requirement series (the
    Synchronized sub-product columns ``sr_req_mw`` / ``mad_sr_req_mw``, built
    by ``scripts/build_pjm_as_withholding.py`` from the same PJM Data Miner
    reserve-market results as the Primary columns). Applies the same
    defensive forward/back-fill as :func:`load_pjm_measured_reserve_requirement`
    (documented ~24 h data holes read as 0 and must never yield a spuriously
    zero requirement). Returns ``None`` when the parquet or column is absent.
    """
    path = Path(data_dir) / f"pjm_{year}_as_up_mw.parquet"
    if not path.exists():
        return None
    import pandas as pd

    df = pd.read_parquet(path)
    if column not in df.columns:
        return None
    req = df[column].to_numpy(dtype=float)
    if (req <= 0.0).any():
        good = req > 0.0
        if good.any():
            idx = np.where(good, np.arange(len(req)), -1)
            np.maximum.accumulate(idx, out=idx)
            idx[idx < 0] = np.flatnonzero(good)[0]
            req = req[idx]
    if len(req) >= hours:
        return req[:hours]
    return np.resize(req, hours)


def load_pjm_measured_sync_reserve_requirement(
    year: int,
    hours: int = 8760,
    data_dir: Path = _PJM_AS_DIR,
) -> np.ndarray | None:
    """Return the measured PJM_RTO SYNCHRONIZED Reserve requirement (MW), hourly.

    The Synchronized sub-product's published requirement (SR ⊆ Primary,
    Manual 11 sec 4.2/4.4.1: the 10-minute reserve that must come from
    *synchronized* resources; requirement ≈ the largest single contingency,
    Manual 13) — column ``sr_req_mw`` in
    ``data/raw/PJM-AS/pjm_<year>_as_up_mw.parquet`` (PJM Data Miner RT
    reserve market results, ``service == "SR"``, ``locale == "PJM_RTO"``).
    Like the Primary series it is a measured *reliability* quantity set by a
    published market-design formula, never a price actual — the rule-13
    admissibility basis is identical to
    :func:`load_pjm_measured_reserve_requirement`. The forecast analogue is
    the Manual-11 rule SR requirement = LSC
    (:func:`largest_single_contingency_mw`).

    Returns ``None`` when the parquet or column is absent.
    """
    return _load_pjm_req_column(year, hours, "sr_req_mw", data_dir)


def load_pjm_measured_mad_sync_reserve_requirement(
    year: int,
    hours: int = 8760,
    data_dir: Path = _PJM_AS_DIR,
) -> np.ndarray | None:
    """Return the measured MAD-subzone SYNCHRONIZED Reserve requirement (MW).

    The Mid-Atlantic/Dominion Reserve Subzone's Synchronized requirement —
    column ``mad_sr_req_mw`` in ``pjm_<year>_as_up_mw.parquet`` (PJM Data
    Miner RT reserve market results, ``service == "SR"``, ``locale ==
    "MAD"``). Same measured-reliability-quantity basis as the RTO series.
    Returns ``None`` when absent (caller builds the RTO sync family only).
    """
    return _load_pjm_req_column(year, hours, "mad_sr_req_mw", data_dir)


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
    (``data/raw/PJM-AS``) is a backcast honesty gate only, never an LP
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


def nyiso_rcpf_product_shortfall_steps(
    requirement_mw: float,
    critical_mw: float,
    max_penalty: float,
    n_ramp: int = 8,
) -> tuple[np.ndarray, np.ndarray]:
    """Discretize one NYISO RCPF reserve demand curve into LP shortfall steps.

    The co-optimization analogue of :func:`rcpf.reserve_demand_price`. The
    published curve is a piecewise-linear ramp: $0 at reserves ``>= requirement``,
    rising linearly to ``max_penalty`` at ``critical``, then flat at
    ``max_penalty`` for reserves below ``critical`` (``critical = 0`` for the
    locational products, so the ramp runs all the way to zero reserve). A
    reserve "shortfall" variable measures the unmet requirement; band ``j``
    covers a slice of shortfall and is priced at the demand-curve value over
    that slice, ascending cheapest band (smallest shortfall, highest reserve)
    first — the contract :func:`pjm_ordc_shortfall_steps` produces and
    ``model.dispatch`` consumes. Total step width is exactly ``requirement_mw``
    so the balance row stays feasible even at zero reserve.

    Args:
        requirement_mw: Reserve requirement (curve is $0 at/above it).
        critical_mw: Reserve level at/below which the maximum penalty applies.
        max_penalty: Maximum reserve shadow price ($/MWh).
        n_ramp: Number of equal-width steps discretizing the linear ramp.

    Returns:
        ``(penalties, widths)`` ascending cheapest-first, each ``(n_steps,)``.
    """
    span = float(requirement_mw) - float(critical_mw)
    if span < 0:
        raise ValueError(
            f"requirement_mw ({requirement_mw}) must be >= critical_mw ({critical_mw})"
        )
    pens: list[float] = []
    wids: list[float] = []
    if span > 0:
        # Ramp region [critical, requirement]: descending reserve grid so the
        # shortfall (requirement - reserve) ascends; price each band at the
        # demand curve evaluated at its lower reserve edge (where it starts to
        # bind), so penalties ascend toward max_penalty.
        grid = np.linspace(float(requirement_mw), float(critical_mw), int(n_ramp) + 1)
        r_edge = grid[1:]  # lower reserve edge of each band
        pens.extend((max_penalty * (float(requirement_mw) - r_edge) / span).tolist())
        wids.extend((grid[:-1] - grid[1:]).tolist())
    if float(critical_mw) > 0:
        # Flat tail: reserves below critical price at the full penalty.
        pens.append(float(max_penalty))
        wids.append(float(critical_mw))
    return np.asarray(pens, dtype=float), np.asarray(wids, dtype=float)


def caiso_reserve_demand_steps(
    requirement_mw: float,
    curve: tuple[tuple[float, float], ...],
    bid_cap: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Discretize a CAISO scarcity reserve demand curve into LP shortfall steps.

    The CAISO analogue of :func:`nyiso_rcpf_product_shortfall_steps`, for the
    published tariff §27.1.2.3.5 scarcity reserve demand curves
    (``reserve_config.CAISO_SPIN_DEMAND_CURVE`` /
    ``CAISO_NONSPIN_DEMAND_CURVE``). Unlike NYISO's linear-ramp-to-VOLL curve,
    CAISO's are STEPPED at published shortage magnitudes: spinning is flat at
    10% of the bid cap; non-spinning steps 50 → 60 → 70% at the 70 MW / 210 MW
    shortage tiers. A reserve "shortfall" variable measures the unmet
    requirement; band ``j`` covers a slice of shortfall priced at the demand
    curve over that slice, ascending cheapest (shallowest shortage) first — the
    contract :func:`model.dispatch` consumes.

    Tier edges are ABSOLUTE shortage MW (a tariff fact, not a fraction of the
    requirement), so they are the same in every hour; passing the pool's
    maximum hourly requirement as ``requirement_mw`` sizes the total step width
    to keep the balance row feasible at zero reserve in the tightest hour while
    the tier boundaries stay fixed. The final tier's edge is ``inf`` (extends to
    the requirement).

    Args:
        requirement_mw: Total shortfall width to span (the pool's requirement,
            or its hourly maximum when the requirement varies by hour).
        curve: Ascending ``(fraction_of_bid_cap, cumulative_shortage_upper_mw)``
            tiers; the last ``upper`` is ``inf``.
        bid_cap: The energy bid cap the fractions are quoted against ($/MWh).

    Returns:
        ``(penalties, widths)`` ascending cheapest-first, each ``(n_steps,)``;
        ``widths`` sums to ``requirement_mw``.
    """
    req = float(requirement_mw)
    pens: list[float] = []
    wids: list[float] = []
    if req <= 0.0:
        return np.zeros(0, dtype=float), np.zeros(0, dtype=float)
    prev_upper = 0.0
    for frac, upper in curve:
        tier_upper = min(float(upper), req)
        width = tier_upper - prev_upper
        if width > 0.0:
            pens.append(float(frac) * float(bid_cap))
            wids.append(width)
        prev_upper = tier_upper
        if tier_upper >= req:
            break
    return np.asarray(pens, dtype=float), np.asarray(wids, dtype=float)


def nyiso_spin_requirement_mw(config) -> float:
    """Return the NYC synchronised (spinning) reserve requirement in MW.

    :data:`NYISO_SPIN_FRACTION` (1/2, a published market-design constant) times
    the NYC locational 10-minute total requirement (``nyc_10min_total`` in
    :data:`NYISO_RCPF_LOCATIONAL`, 500 MW) -> 250 MW. The single source of truth
    shared by the LP spinning family (:func:`~market_sim.config.reserve_config._nyiso_design`) and the
    runner's reserve-adequacy commit, so both target the same MEASURED quantity.

    Args:
        config: The scenario config, read for any ``nyiso_rcpf_locational``
            override; otherwise the default :data:`NYISO_RCPF_LOCATIONAL`.

    Returns:
        The NYC spinning-reserve requirement in MW.
    """
    from market_sim.config.reserve_config import NYISO_RCPF_LOCATIONAL

    locational = getattr(config, "nyiso_rcpf_locational", None) or NYISO_RCPF_LOCATIONAL
    nyc10 = next(
        (
            req
            for region in locational.values()
            for name, req, _c, _p in region["products"]
            if "nyc_10min_total" in name
        ),
        500.0,
    )
    return NYISO_SPIN_FRACTION * float(nyc10)


def nyiso_spin_eligible(fleet_arrays: FleetArrays, zone_names: list[str]) -> np.ndarray:
    """Return the ``(n_gen,)`` boolean mask of NYC quick-start spin-eligible units.

    A unit may back the NYC synchronised-reserve requirement only if it is a
    quick-start type (:data:`QUICK_START_FUEL_TYPES`) *and* sits in a
    :data:`NYISO_DOWNSTATE_SPIN_ZONES` zone (NYC) — reserve is per-zone
    deliverable, so out-of-pocket headroom cannot satisfy the NYC family. The
    runner's :func:`market_sim.model.commitment.reserve_adequacy_commit`
    force-commits this subset until its committed capacity covers the spinning
    requirement.

    Args:
        fleet_arrays: The vectorized fleet, for ``fuel_type_idx`` and ``zone_idx``.
        zone_names: The ISO's zone names, ordered to match ``zone_idx``.

    Returns:
        A ``(n_gen,)`` boolean mask: ``True`` = NYC-zone quick-start unit.
    """
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    spin_zone_idx = {
        i for i, name in enumerate(zone_names) if name in NYISO_DOWNSTATE_SPIN_ZONES
    }
    in_zone = np.array(
        [int(z) in spin_zone_idx for z in fleet_arrays.zone_idx], dtype=bool
    )
    return quick & in_zone
