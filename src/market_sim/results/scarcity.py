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
    ERCOT_AS_PRODUCTS,
    MISO_REGULATING_RESERVE_MW,
    MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW,
    MISO_RESERVE_DEMAND_CURVE_MAX,
    NYISO_RCPF_LOCATIONAL,
    NYISO_RCPF_PRODUCTS,
    ORDC_FLOOR_START_HOUR_2023,
    ORDC_FLOOR_STEPS,
    PJM_ORDC_CURVE_PATH,
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
    if getattr(config, "ercot_ecrs_requirement", False) and int(
        config.weather_year
    ) >= int(getattr(config, "ercot_ecrs_requirement_from_year", 2023)):
        # ADD ERCOT's measured ECRS procurement (~2 GW from 2023-06-10) to the
        # reserve-balance RHS. The co-opt models one contingency-reserve product
        # and never grew when ECRS launched, so it holds too little reserve and
        # under-prices the broad mid-range from mid-2023 on (the demand-side
        # mirror of the load/storage *supply* credits below, which subtract).
        # Exogenous ERCOT-published quantity (ASPLANNP433), not a price fit; its
        # June-2023 onset is carried by the data, so 2023-H1 is unaffected.
        requirement = requirement + ercot_ecrs_requirement_mw(
            int(config.weather_year), hours
        )
    if getattr(config, "ercot_load_resource_reserve", False) and int(
        config.weather_year
    ) >= int(getattr(config, "ercot_load_resource_reserve_from_year", 2023)):
        # Credit ERCOT's measured Load-Resource responsive reserve (RRS-UFR) the
        # co-opt LP otherwise omits. Lowering the balance-RHS by load_mw(t) is
        # equivalent to adding load_mw of $0 reserve supply: because the ORDC
        # steps are priced by absolute reserve level, the marginal step then
        # prices at total reserve R_gen + load_mw — physically exact, no double
        # count. Clipped to the MCL floor so the curve's steep tail is preserved.
        # Credited every year by default (ercot_load_resource_reserve_from_year
        # = 2023): on the measured-storage baseline (storage_as_commitment over-
        # tightens 2023) the measured 2023 load credit corrects the 2023 MAE
        # 16.0->12.1 (run139) — unlike the storage-AS *reserve* credit, which
        # stays scoped off 2023/2024 (it would double-relax, run137).
        load_mw = ercot_load_resource_reserve_mw(int(config.weather_year), hours)
        requirement = np.maximum(requirement - load_mw, float(config.ordc_mcl_mw))
    if (
        getattr(config, "ercot_storage_as_reserve", False)
        and getattr(config, "storage_as_commitment", False)
        and int(config.weather_year)
        >= int(getattr(config, "ercot_storage_as_reserve_from_year", 2025))
    ):
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
        storage_as_mw = ercot_storage_as_reserve_mw(int(config.weather_year), hours)
        requirement = np.maximum(requirement - storage_as_mw, float(config.ordc_mcl_mw))
    eligible = ercot_reserve_eligible(fleet_arrays)
    return requirement, eligible, penalties, widths


def ercot_as_forward_requirement_mw(
    config, product_code: str, hours: int
) -> np.ndarray | None:
    """Forward AS requirement for one product, or ``None`` to use the measured one.

    The forward analogue of reading ``ASPLANNP433`` — ERCOT sizes each AS product
    from forward drivers it publishes (net-load ramp risk, forecast-error
    quantiles, largest-contingency / load-ratio shares). That requirement-setting
    methodology is **P1b**; until it lands this returns ``None`` so the caller
    falls back to the measured ASPLANNP433 realization (the validation target).
    Wiring it here keeps the forward seam explicit: when P1b lands it returns
    ``req_product(t) = f(net_load(t), ramp(t), VRE_share(t))`` and the co-opt is
    forward-native with no code change at the call site.
    """
    # P1b not yet implemented — fall back to the measured requirement.
    return None


def ercot_multiproduct_reserve_coopt_inputs(
    config, fleet_arrays: FleetArrays, hours: int
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Assemble ERCOT's MULTI-PRODUCT energy+AS co-optimization inputs.

    The forward analogue of the measured DAM-AS MCPC overlay
    (:func:`ercot_dam_as_overlay_series`). Replaces the one lumped
    contingency-reserve product of :func:`ercot_reserve_coopt_inputs` with a
    co-optimization demand curve **per AS product** (RegUp / RRS / ECRS /
    NonSpin, :data:`~market_sim.config.constants.ERCOT_AS_PRODUCTS`). Each
    product is one reserve *family* — its own per-zone reserve variable, its own
    requirement, and its own VOLL-anchored demand curve — so the binding
    product's balance-row dual is that product's clearing price (MCPC), and the
    per-hour MAX across products reproduces the ``binding_mcpc`` the overlay
    reads from disk, formed **endogenously** from the LP rather than added.

    **Additive, not nested.** Unlike NYISO's nested products (one MW counts for
    both the 10- and 30-minute requirement), ERCOT holds the four products as
    *separate* capacity — ~7-8 GW total out of the energy stack every hour. The
    products therefore SHARE one headroom pool ADDITIVELY: the sum of all four
    products' reserve plus the eligible units' energy must fit under the
    responsive headroom. That additivity (vs the single ~3 GW lumped product) is
    most of the extra scarcity the overlay carried.

    **Quality cascade (higher-quality substitutes down).** Two nested
    shared-headroom rows encode the substitution cascade:

    * a "fast" row over the synchronized/spinning responsive set
      (:data:`RESERVE_FUEL_TYPES` minus the offline-capable
      :data:`QUICK_START_FUEL_TYPES` peakers) bounding the three fast products
      (RegUp/RRS/ECRS), and
    * an "all" row over the full responsive set (adding the gas-CT/oil
      quick-start peakers a 30-minute Non-Spin award can come from) bounding all
      four products.

    Because the fast products appear in BOTH rows while Non-Spin appears only in
    the "all" row, a Non-Spin MW can be supplied by a quick-start peaker the fast
    products cannot reach — the correct cascade — while the fast products price
    up first when spinning headroom is scarce (the binding-MCPC days). Storage
    backs both rows (batteries respond in seconds → every product).

    **Requirements** are the ERCOT-published per-product procurement quantities
    (``ASPLANNP433``) for the weather year — the measured realization the forward
    requirement-setting formula (:func:`ercot_as_forward_requirement_mw`, P1b)
    validates against, never fitted to a price. **Demand-curve prices** are
    VOLL-anchored (``config.ordc_voll``, the AS offer cap) market-design
    schedules, so the hourly scarcity *incidence* comes from the responsive
    headroom in the shared-headroom RHS — a tighter fleet clears AS lower on the
    curve at a higher price — not from any tuned per-product level. The
    phantom-headroom fix (a perfect-foresight LP leaving cold slow-start units
    idle yet counted as reserve) is delivered by running this co-opt in the P2
    commitment-screened solve, whose ``availability`` zeroes the decommitted
    idle capacity out of the shared-headroom RHS.

    Returns the nine-tuple ``model.dispatch`` consumes for the additive
    multi-product co-opt: ``(reserve_requirement (n_prod, T), reserve_eligible
    (n_prod, n_gen), ordc_penalties, ordc_step_widths, balance_zone_mask
    (n_prod, n_zones), balance_ordc_counts (n_prod,), balance_reserve_class
    (n_prod,), headroom_eligible (2, n_gen), headroom_products (2, n_prod))``.
    """
    T = int(hours)
    n_zones = int(np.max(fleet_arrays.zone_idx)) + 1
    products = list(ERCOT_AS_PRODUCTS)
    n_prod = len(products)
    voll = float(config.ordc_voll)
    crit_frac = float(getattr(config, "ercot_as_critical_frac", 0.0))
    n_ramp = int(getattr(config, "ercot_as_n_ramp", 12))
    year = int(config.weather_year)

    requirement = np.zeros((n_prod, T), dtype=float)
    pen_list: list[np.ndarray] = []
    wid_list: list[np.ndarray] = []
    counts = np.zeros(n_prod, dtype=int)
    for p, (_name, code, _tier) in enumerate(products):
        # Forward requirement formula (P1b) when available, else the measured
        # ASPLANNP433 realization for the weather year (the validation target).
        req_t = ercot_as_forward_requirement_mw(config, code, T)
        if req_t is None:
            req_t = ercot_as_plan_requirement_mw(year, T, code)
        requirement[p, :] = req_t
        # VOLL-anchored AS demand curve, sized to the product's PEAK requirement
        # so the shortfall steps span the full requirement and the balance stays
        # feasible at zero reserve in every hour (the PJM ORDC-step convention).
        req_peak = float(req_t.max())
        if req_peak <= 0.0:  # product not active this year (e.g. pre-2023 ECRS)
            pen_list.append(np.zeros(0))
            wid_list.append(np.zeros(0))
            counts[p] = 0
            continue
        crit = crit_frac * req_peak
        pen, wid = nyiso_rcpf_product_shortfall_steps(
            req_peak, crit, voll, n_ramp=n_ramp
        )
        pen_list.append(pen)
        wid_list.append(wid)
        counts[p] = pen.size

    ordc_penalties = np.concatenate(pen_list) if pen_list else np.zeros(0)
    ordc_step_widths = np.concatenate(wid_list) if wid_list else np.zeros(0)

    # Each product is its own reserve class (own per-zone R, own balance dual),
    # so n_reserve_classes == n_prod. Per-class eligibility is the responsive
    # thermal set (the actual product-vs-unit restriction is enforced by the
    # headroom-row membership below); a system-wide family per product.
    full_elig = ercot_reserve_eligible(fleet_arrays)  # (n_gen,)
    reserve_eligible = np.tile(full_elig, (n_prod, 1))  # (n_prod, n_gen)
    balance_zone_mask = np.ones((n_prod, n_zones), dtype=bool)
    balance_reserve_class = np.arange(n_prod, dtype=int)

    # Nested shared-headroom rows for the quality cascade. Row 0 "fast" = the
    # synchronized responsive set (excludes offline-capable quick-start peakers)
    # bounding the fast products; row 1 "all" = the full responsive set bounding
    # every product. Fast products sit in both rows; Non-Spin only in "all".
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    responsive = np.isin(fuel_names, sorted(RESERVE_FUEL_TYPES))
    quick = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    fast_elig = responsive & ~quick  # spinning set (CC/ST/coal/nuclear)
    headroom_eligible = np.vstack([fast_elig, responsive])  # (2, n_gen)
    headroom_products = np.zeros((2, n_prod), dtype=bool)
    for p, (_name, _code, tier) in enumerate(products):
        headroom_products[1, p] = True  # every product draws on the "all" row
        if tier == "fast":
            headroom_products[0, p] = True  # fast products also on the "fast" row
    return (
        requirement,
        reserve_eligible,
        ordc_penalties.astype(float),
        ordc_step_widths.astype(float),
        balance_zone_mask,
        counts,
        balance_reserve_class,
        headroom_eligible,
        headroom_products,
    )


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


def pjm_reserve_coopt_inputs(
    config, fleet_arrays: FleetArrays, hours: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble the PJM energy+reserve co-optimization inputs for ``solve_dispatch``.

    The PJM analogue of :func:`ercot_reserve_coopt_inputs`, but built on PJM's
    *published vertical two-step ORDC* (``data/raw/_validation-source/
    pjm_ordc_curve.csv``, the ``(Primary, RTO)`` curve ``[(0, 850), (190, 300)]``)
    rather than a VOLL-anchored LOLP curve, and on the **measured** PJM_RTO
    Primary Reserve requirement (``pr_req_mw``, ~3.4 GW) rather than a derived
    demand-curve top. Nothing here is fitted to the LMP residual — the
    requirement is a measured reliability quantity and the curve is the cited
    market design (``docs/multi-iso/pjm-reserve-ordc.md``).

    Returns ``(reserve_requirement, reserve_eligible, ordc_penalties,
    ordc_step_widths)``:

    * ``reserve_requirement`` — the hourly reserve-balance RHS = measured Primary
      requirement ``REQ(t)`` + 190 MW (the curve's outer breakpoint), so the
      balance row reads ``sum_z R_z + sum_k shortfall_k >= REQ(t) + 190``.
    * ``reserve_eligible`` — the generic :data:`RESERVE_FUEL_TYPES` thermal mask
      (:func:`ercot_reserve_eligible`, ISO-agnostic).
    * ``ordc_penalties`` / ``ordc_step_widths`` — the published step curve as
      ascending shortfall steps, cheapest band first: penalties ``[300, 850]``
      $/MWh with widths ``[190, REQ_max]``. The first 190 MW of shortfall
      (reserves between ``REQ`` and ``REQ+190``) prices at $300, the rest
      (reserves below ``REQ``) at $850. The inner $850 band's width is the
      requirement itself (``REQ``, which varies hourly), but the LP layout needs
      a **constant** width vector, so it is set to ``max_t REQ(t)`` — large enough
      to absorb the full shortfall in the tightest hour, while the hourly balance
      RHS (``REQ(t)+190``) caps how much shortfall the LP can actually use.

    The forecast path (no measured parquet) falls back to the structural
    1.5×-MSSC formula (:func:`pjm_primary_reserve_requirement` on
    :func:`largest_single_contingency_mw`).
    """
    year = int(config.weather_year)
    req = load_pjm_measured_reserve_requirement(year, hours)
    if req is None:
        # Forecast / no measured series: the fleet-responsive 1.5×-MSSC formula.
        lsc = largest_single_contingency_mw(
            fleet_arrays.pmax,
            availability=fleet_arrays.availability,
            reserve_mask=ercot_reserve_eligible(fleet_arrays),
            plant_code=fleet_arrays.plant_code,
        )
        req = pjm_primary_reserve_requirement(lsc, hours)
    req = np.asarray(req, dtype=float)

    steps = load_pjm_ordc_curve(PJM_ORDC_CURVE_PATH)[("Primary", "RTO")]
    outer_offset = float(max(o for o, _ in steps))  # 190 MW (Step-2 breakpoint)
    # Convert the published curve to ascending shortfall steps. Only the
    # penalties and the OUTER band width (the constant breakpoint offset) are
    # requirement-independent; the INNER band width returned here is the nominal
    # requirement, which we overwrite with max_t REQ(t) so the constant width
    # vector covers the tightest hour.
    _req_total_nom, penalties, widths = pjm_ordc_shortfall_steps(
        steps, float(np.mean(req))
    )
    widths = np.asarray(widths, dtype=float).copy()
    widths[-1] = float(np.max(req))  # inner ($850) band spans [0, REQ_max)

    requirement = req + outer_offset
    eligible = ercot_reserve_eligible(fleet_arrays)
    return requirement, eligible, penalties.astype(float), widths.astype(float)


def miso_reserve_coopt_inputs(
    config, fleet_arrays: FleetArrays, hours: int, n_ramp: int = 8
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Assemble MISO's market-wide energy+reserve co-optimization inputs.

    The MISO analogue of :func:`pjm_reserve_coopt_inputs`. MISO co-optimizes
    energy with its market-wide operating reserves (Regulating + Contingency)
    against a VOLL-anchored Reliability-Based Demand Curve; when cleared
    market-wide reserves fall below the requirement the demand curve sets the
    reserve clearing price, and through co-optimization that dual lifts the
    energy LMP (the scarcity tail the perfect-foresight energy-only LP cannot
    produce). A **single market-wide reserve family** — footprint-wide clearing
    like PJM's RTO-wide reserve, not locational.

    Requirement = MSSC (most severe single contingency, fleet-derived via
    :func:`largest_single_contingency_mw`, so it is forecast-responsive and not a
    measured replay) + :data:`MISO_REGULATING_RESERVE_MW`. The demand curve ramps
    linearly from $0 at the requirement to :data:`MISO_RESERVE_DEMAND_CURVE_MAX`
    at the critical reserve level (:data:`MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW`),
    discretized into ascending shortfall steps (the same demand-curve
    discretizer the NYISO/NEISO families use). Nothing is fitted to the LMP
    residual — the requirement basis and curve anchors trace to MISO BPM-002 /
    Schedule 28.

    Returns ``(reserve_requirement, reserve_eligible, ordc_penalties,
    ordc_step_widths)`` — the PJM signature (single system-wide family):

    * ``reserve_requirement`` — ``(T,)`` hourly reserve-balance RHS (MW),
      ``MSSC + regulation`` (flat: a near-constant reliability quantity).
    * ``reserve_eligible`` — the generic :data:`RESERVE_FUEL_TYPES` thermal mask
      (:func:`ercot_reserve_eligible`, ISO-agnostic).
    * ``ordc_penalties`` / ``ordc_step_widths`` — the demand curve as ascending
      shortfall steps (cheapest band first), summing in width to the requirement
      so the balance row stays feasible even at zero cleared reserve.
    """
    eligible = ercot_reserve_eligible(fleet_arrays)
    mssc = largest_single_contingency_mw(
        fleet_arrays.pmax,
        availability=fleet_arrays.availability,
        reserve_mask=eligible,
        plant_code=fleet_arrays.plant_code,
    )
    req = float(mssc) + MISO_REGULATING_RESERVE_MW
    penalties, widths = nyiso_rcpf_product_shortfall_steps(
        req,
        MISO_RESERVE_DEMAND_CURVE_CRITICAL_MW,
        MISO_RESERVE_DEMAND_CURVE_MAX,
        n_ramp=n_ramp,
    )
    requirement = np.full(int(hours), req, dtype=float)
    return requirement, eligible, penalties.astype(float), widths.astype(float)


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


def nyiso_spin_requirement_mw(config) -> float:
    """Return the NYC synchronised (spinning) reserve requirement in MW.

    :data:`NYISO_SPIN_FRACTION` (1/2, a published market-design constant) times
    the NYC locational 10-minute total requirement (``nyc_10min_total`` in
    :data:`NYISO_RCPF_LOCATIONAL`, 500 MW) -> 250 MW. The single source of truth
    shared by the LP spinning family (:func:`nyiso_reserve_coopt_inputs`) and the
    runner's reserve-adequacy commit, so both target the same MEASURED quantity.

    Args:
        config: The scenario config, read for any ``nyiso_rcpf_locational``
            override; otherwise the default :data:`NYISO_RCPF_LOCATIONAL`.

    Returns:
        The NYC spinning-reserve requirement in MW.
    """
    from market_sim.config.constants import NYISO_RCPF_LOCATIONAL

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


def nyiso_reserve_coopt_inputs(
    config,
    fleet_arrays: FleetArrays,
    hours: int,
    zone_names: list[str],
    n_ramp: int = 8,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray | None,
    float,
]:
    """Assemble NYISO's *locational* energy+reserve co-optimization inputs.

    The NYISO analogue of :func:`ercot_reserve_coopt_inputs` /
    :func:`pjm_reserve_coopt_inputs`, but NYISO's reserve market is *nested and
    locational*: the system NYCA tier (:data:`NYISO_RCPF_PRODUCTS`) plus the
    East ⊃ SENY ⊃ NYC regional tiers (:data:`NYISO_RCPF_LOCATIONAL`) each carry
    their own requirement and demand curve. Each (region, product) pair becomes
    one *reserve family* — a balance row over that region's member zones,
    sourced from the published Rate Schedule 4 / FERC ER21-502 anchors (nothing
    fitted to the LMP residual). Holding the import-constrained downstate pocket
    (NYC, SENY) to its locational reserve requirement keeps the NYC peaker /
    quick-start fleet's headroom in reserve, so in tight hours those units clear
    on energy and the reserve shortfall stacks a scarcity price into the
    downstate zonal LMP — the locational tail the NYCA-aggregate energy LP and
    the post-solve RCPF adder cannot dispatch.

    **Per-product eligibility (reserve classes).** NYISO's reserve products
    differ in *response speed*, and that bounds which units can supply them.
    The 10-minute products (10-minute spinning / non-synchronized: a unit must
    reach output within 10 minutes) can only be met by the **quick-start**
    fleet — gas combustion turbines and oil peakers that synchronize within ~10
    minutes (:data:`QUICK_START_FUEL_TYPES`), plus fast storage. The 30-minute
    products draw on the full dispatchable thermal fleet
    (:data:`RESERVE_FUEL_TYPES`), which can ramp/start within 30 minutes. This
    is a *capability* constraint grounded in unit physics, not a fitted
    requirement: feeding a 10-minute family the same all-thermal mask would let
    slow combined-cycle headroom satisfy it, understating downstate scarcity.
    Each family is therefore tagged with a reserve *class* (0 = full
    dispatchable / 30-minute, 1 = quick-start / 10-minute), and the LP carries a
    separate per-zone reserve pool per class. The classes are nested (quick-start
    units are also dispatchable), so a quick-start MW counts toward both its
    10-minute family and the larger 30-minute requirement — the correct reserve
    cascade.

    The demand curves are constant across hours; the hourly scarcity *incidence*
    comes from the hourly fleet availability in the shared-headroom RHS (a tight
    downstate fleet clears reserve lower on the curve, at a higher price), the
    same design as the ERCOT/PJM co-opt.

    Returns ``(reserve_requirement, reserve_eligible, ordc_penalties,
    ordc_step_widths, balance_zone_mask, balance_ordc_counts,
    balance_reserve_class)``:

    * ``reserve_requirement`` — ``(n_families, T)`` per-family hourly RHS (MW).
    * ``reserve_eligible`` — ``(n_classes, n_gen)`` boolean: row 0 the full
      :data:`RESERVE_FUEL_TYPES` thermal mask (30-minute products), row 1 the
      :data:`QUICK_START_FUEL_TYPES` subset (10-minute products).
    * ``ordc_penalties`` / ``ordc_step_widths`` — the family-major concatenated
      shortfall-step penalties ($/MWh) and widths (MW).
    * ``balance_zone_mask`` — ``(n_families, n_zones)`` boolean of each family's
      member zones (which zones' reserve feeds the family's balance row).
    * ``balance_ordc_counts`` — ``(n_families,)`` ORDC steps per family.
    * ``balance_reserve_class`` — ``(n_families,)`` int: each family's reserve
      class (0 full dispatchable, 1 quick-start), keyed off whether the product
      name marks a 10-minute product.
    """
    T = int(hours)
    zone_index = {name: i for i, name in enumerate(zone_names)}
    n_zones = len(zone_names)

    # Build the (region zones, product name, product params) family list: the
    # system NYCA tier over every zone, then each locational region over its
    # member zones. A region with several nested products (e.g. NYC 30-min and
    # 10-min) contributes one family per product (different requirement ->
    # different balance row). The product *name* is retained to assign each
    # family its reserve class (10-minute -> quick-start).
    families: list[tuple[tuple[int, ...], str, tuple[float, float, float]]] = []
    nyca_products = tuple(
        getattr(config, "nyiso_rcpf_products", None) or NYISO_RCPF_PRODUCTS
    )
    all_zones = tuple(range(n_zones))
    for name, req, crit, pen in nyca_products:
        families.append((all_zones, str(name), (float(req), float(crit), float(pen))))
    locational = getattr(config, "nyiso_rcpf_locational", None) or NYISO_RCPF_LOCATIONAL
    for region in locational.values():
        member_idx = tuple(zone_index[z] for z in region["zones"] if z in zone_index)
        if not member_idx:
            continue
        for name, req, crit, pen in region["products"]:
            families.append(
                (member_idx, str(name), (float(req), float(crit), float(pen)))
            )

    # Synchronised (spinning) reserve (default-off behind
    # config.nyiso_synchronised_reserve). NYISO 10-minute SPINNING reserve must
    # come from ONLINE (synchronised) units, but the idle-allowed headroom rows
    # let an OFFLINE downstate peaker count its full pmax as deliverable reserve
    # -- so the locational families never bind, the RCPF never prices, and the
    # NYC peakers stay economically idle (docs/handoffs/
    # nyiso-downstate-reserve-incidence-2026-06.md, root cause). This adds a NYC
    # locational spinning family. Requirement = NYISO_SPIN_FRACTION (1/2) of the
    # NYC 10-minute total (the published NYISO spinning = 1/2-of-total ratio,
    # NYISO_RCPF_PRODUCTS: nyca_10min_spin 655 = 1/2 nyca_10min_total 1310),
    # applied to the NYC 10-min total (500 MW) -> 250 MW; penalty the same $500
    # NYC ceiling. NOT fitted to the residual.
    #
    # Two routes, selected by whether the P2 commitment screen is enabled:
    #   * PATH B (commit_gated, the real tail lever): commitment is ON. The
    #     spinning family rides the ORDINARY idle-allowed quick-start class (1).
    #     In the P2 re-solve apply_commitment_with_coal_pin zeroes the
    #     availability of decommitted units, so the class-1 NYC headroom row
    #     (Sum P + R <= Sum cap) — restricted to the committed set — equals
    #     Sum_online(pmax - P), the physically-correct synchronised headroom, with
    #     no online binary and no rho*Sum-P subsidy. Commitment does the gating;
    #     the runner's reserve_adequacy_commit force-commits enough NYC quick-start
    #     to back the requirement. (The 250 MW spin family is nested under the
    #     existing 500 MW nyc_10min_total on the same class-1 pool — both prices
    #     against the now-online-only headroom; kept per the path-B design.)
    #   * PATH A (online-gated scaffold): commitment is OFF. The spinning family
    #     rides a separate ONLINE-GATED class (2) whose headroom is bounded by
    #     online quick-start GENERATION (R <= rho*Sum P), an LP-linear proxy for
    #     the missing online indicator. Confirmed-but-insufficient for the tail
    #     (it subsidises output rather than charging scarcity); kept as a default-
    #     off scaffold. See the handoff "Path A — IMPLEMENTED & TESTED".
    synch = bool(getattr(config, "nyiso_synchronised_reserve", False))
    commit_gated = synch and bool(getattr(config, "commitment_enabled", False))
    if synch:
        nyc_idx = tuple(i for z, i in zone_index.items() if z == "NYC")
        spin_req = nyiso_spin_requirement_mw(config)
        if nyc_idx:
            spin_name = "nyc_spin_commit" if commit_gated else "nyc_spin_online"
            families.append((nyc_idx, spin_name, (spin_req, 0.0, 500.0)))

    n_fam = len(families)
    balance_zone_mask = np.zeros((n_fam, n_zones), dtype=bool)
    balance_reserve_class = np.zeros(n_fam, dtype=int)
    requirement = np.zeros((n_fam, T), dtype=float)
    pen_list: list[np.ndarray] = []
    wid_list: list[np.ndarray] = []
    counts = np.zeros(n_fam, dtype=int)
    for f, (member_idx, name, (req, crit, pen)) in enumerate(families):
        balance_zone_mask[f, list(member_idx)] = True
        # Reserve class per family: the path-A online-gated spinning family
        # (name "nyc_spin_online") draws on the ONLINE-GATED quick-start class
        # (2); the path-B commit-gated spinning family ("nyc_spin_commit") and
        # all 10-minute products on the idle-allowed quick-start class (1);
        # 30-minute / total products on the full dispatchable class (0). NOTE:
        # the published NYCA "nyca_10min_spin" product stays class 1 — it carries
        # "spin" but not "spin_online".
        balance_reserve_class[f] = (
            2
            if "spin_online" in name
            else (1 if "10min" in name or "spin" in name else 0)
        )
        requirement[f, :] = req
        p, w = nyiso_rcpf_product_shortfall_steps(req, crit, pen, n_ramp=n_ramp)
        pen_list.append(p)
        wid_list.append(w)
        counts[f] = p.size

    ordc_penalties = np.concatenate(pen_list) if pen_list else np.zeros(0)
    ordc_step_widths = np.concatenate(wid_list) if wid_list else np.zeros(0)
    # Nested eligibility classes: full dispatchable (30-minute, class 0) and the
    # quick-start subset (10-minute, class 1). With the synchronised flag a third
    # ONLINE-GATED quick-start class (2) is appended (same eligibility as class 1,
    # but its headroom row counts only online generation — see dispatch.
    # _build_reserve_rows online_gated). Stack so row index == reserve class.
    full_elig = ercot_reserve_eligible(fleet_arrays)
    fuel_names = np.array([FUEL_TYPE_NAMES[i] for i in fleet_arrays.fuel_type_idx])
    quick_elig = np.isin(fuel_names, sorted(QUICK_START_FUEL_TYPES))
    if synch and not commit_gated:
        # PATH A only: append the third ONLINE-GATED quick-start class (2).
        eligible = np.vstack([full_elig, quick_elig, quick_elig])
        online_gated = np.array([False, False, True], dtype=bool)
        # rho = the online-headroom ratio (pmax-pmin)/pmin of the quick-start
        # fleet at min load: how much synchronised spinning reserve an online
        # peaker backs per MW of its output. Capacity-weighted over quick-start
        # units with a positive min-load, clipped to a physical [0.5, 4] band
        # (a peaker that minimal-loads at ~25-50% of pmax has rho ~ 1-3).
        q_idx = np.flatnonzero(quick_elig)
        pmin_q = np.asarray(fleet_arrays.pmin, dtype=float)[q_idx]
        pmax_q = np.asarray(fleet_arrays.pmax, dtype=float)[q_idx]
        valid = (pmin_q > 0) & (pmax_q > pmin_q)
        if valid.any():
            ratio = (pmax_q[valid] - pmin_q[valid]) / pmin_q[valid]
            online_rho = float(
                np.clip(np.average(ratio, weights=pmax_q[valid]), 0.5, 4.0)
            )
        else:
            online_rho = 1.0
    else:
        eligible = np.vstack([full_elig, quick_elig])
        online_gated = None
        online_rho = 1.0
    return (
        requirement,
        eligible,
        ordc_penalties.astype(float),
        ordc_step_widths.astype(float),
        balance_zone_mask,
        counts,
        balance_reserve_class,
        online_gated,
        online_rho,
    )
