"""NYISO SCR/EDRP emergency demand response as price-responsive supply blocks.

NYISO registers ~1.2-1.5 GW (summer) of demand-side reliability capability in
two programs — Special Case Resources (SCR, the large ICAP program) and the
Emergency Demand Response Program (EDRP, small) — dispatched *only* when NYISO
declares a reliability event (reserve pickup / Energy Emergency Alert), which
in practice falls on summer heat-driven peaks. The registered capability is
published per NYISO zone (A-K) and capability period (summer / winter) in the
Gold Book (``data/raw/nyiso-demand-response/nyiso_scr_edrp_enrollment.csv``,
built by ``scripts/data/build_nyiso_scr_edrp.py``).

This module represents that capability as **price-responsive supply blocks**:
one pseudo-generator per model zone with capacity = the zone's registered
DR MW and marginal cost = the DR strike price (``ScenarioConfig`` field,
default the published EDRP compensation floor). The block clears through the
ordinary energy balance and only dispatches when the zone's LBMP would exceed
the strike — an ENDOGENOUS scarcity trigger, never pinned to observed event
dates. This satisfies the forecast-legitimacy test (CLAUDE.md rule 13/17): the
capacity re-derives from the next Gold Book, the strike is a market-design
constant, and deployment responds to whatever scarcity a forward year produces.
The activation window is the physical NYISO summer/winter capability period
(seasonal availability, :func:`nyiso_dr_seasonal_availability`).

Zone crosswalk (A-K -> the five NYISO model zones, matching
``config.iso_configs._nyiso_config``): Upstate_West = A+B+C+D+E,
Capital_Hudson = F+G, Lower_Hudson = H+I, NYC = J, Long_Island = K.
"""

from __future__ import annotations

import csv
from collections import defaultdict

import numpy as np

from market_sim.config.paths import RAW_DIR
from market_sim.data.fleet import Generator

# NYISO zone (A-K) -> model zone. The Gold Book reports SCR/EDRP by the
# eleven load zones; the model aggregates them into five (see module docstring).
_ZONE_TO_MODEL: dict[str, str] = {
    "A": "Upstate_West",
    "B": "Upstate_West",
    "C": "Upstate_West",
    "D": "Upstate_West",
    "E": "Upstate_West",
    "F": "Capital_Hudson",
    "G": "Capital_Hudson",
    "H": "Lower_Hudson",
    "I": "Lower_Hudson",
    "J": "NYC",
    "K": "Long_Island",
}

# The DR programs are dispatched only in NYISO-declared reliability events. In
# reality those are summer heat peaks, but a merchant-idle winter cold snap is
# also possible, so both capability periods carry their registered MW. The
# summer capability period is the ICAP convention May 1 - Oct 31; the winter
# period is the balance of the year.
_SUMMER_MONTHS: frozenset[int] = frozenset({5, 6, 7, 8, 9, 10})

# Latest Gold Book year on disk; a solve year beyond it holds enrollment flat
# (the Gold Book itself projects SCR constant forward), and a year before the
# earliest uses the earliest.
_MIN_GB_YEAR = 2023
_MAX_GB_YEAR = 2025

_DAYS_PER_MONTH = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


def _enrollment_path():
    return RAW_DIR / "nyiso-demand-response" / "nyiso_scr_edrp_enrollment.csv"


def load_scr_edrp_enrollment(year: int) -> dict[str, dict[str, float]]:
    """Return per-model-zone summer/winter DR MW (SCR + EDRP) for ``year``.

    Reads the Gold Book enrollment CSV and aggregates the A-K rows onto the
    five model zones, summing the SCR and EDRP programs (both are dispatched
    on the same reliability-event trigger). ``year`` selects the matching Gold
    Book vintage, clamped to the on-disk range.

    Returns ``{model_zone: {"summer": mw, "winter": mw}}`` for every zone with
    non-zero registered capability. Raises ``FileNotFoundError`` if the CSV is
    absent (the flag must never silently solve without the measured input).
    """
    gb_year = min(max(int(year), _MIN_GB_YEAR), _MAX_GB_YEAR)
    path = _enrollment_path()
    if not path.exists():
        raise FileNotFoundError(
            f"NYISO SCR/EDRP enrollment CSV missing: {path} "
            "(build with scripts/data/build_nyiso_scr_edrp.py)"
        )
    agg: dict[str, dict[str, float]] = defaultdict(
        lambda: {"summer": 0.0, "winter": 0.0}
    )
    with path.open(newline="") as f:
        for row in csv.DictReader(f):
            if int(row["gold_book_year"]) != gb_year:
                continue
            model_zone = _ZONE_TO_MODEL[row["nyiso_zone"]]
            agg[model_zone][row["season"]] += float(row["enrolled_mw"])
    return {z: v for z, v in agg.items() if v["summer"] > 0.0 or v["winter"] > 0.0}


def build_nyiso_dr_generators(config, year: int) -> list[Generator]:
    """Return NYISO SCR/EDRP demand-response pseudo-generators for ``year``.

    One block per model zone, capacity = the zone's registered SUMMER DR MW
    (the binding capability period; winter is applied as a seasonal derate by
    :func:`nyiso_dr_seasonal_availability`), marginal cost = the DR strike
    (``config.nyiso_scr_edrp_strike``) carried in ``vom``. ``fuel_type`` is
    ``"demand_response"`` so the block gets clean pseudo-gen treatment (flat
    availability, no outage overlay, excluded from generation-mix scoring) and
    never evolves. Empty list when the gate is off.
    """
    if not getattr(config, "nyiso_scr_edrp", False):
        return []
    strike = float(getattr(config, "nyiso_scr_edrp_strike", 500.0))
    enrollment = load_scr_edrp_enrollment(year)
    gens: list[Generator] = []
    for zone, mw in sorted(enrollment.items()):
        cap = float(mw["summer"])
        if cap <= 0.0:
            continue
        gens.append(
            Generator(
                unit_id=f"NYISO_DR_{zone}",
                name=f"SCR/EDRP {zone}",
                zone=zone,
                fuel_type="demand_response",
                pmax_mw=cap,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=strike,
                eford=0.0,
            )
        )
    return gens


def nyiso_dr_seasonal_availability(year: int, hours: int) -> dict[str, np.ndarray]:
    """Return a per-model-zone seasonal availability profile (fraction of pmax).

    The DR generator's ``pmax`` is the summer capability; this profile is 1.0
    in the summer capability period (May-Oct) and ``winter_mw / summer_mw`` in
    the winter period, so the effective cap tracks the registered capability of
    whichever period each hour falls in. A zone with zero summer capability is
    omitted (its generator was never built).
    """
    enrollment = load_scr_edrp_enrollment(year)
    month_idx = _hour_to_month(hours)
    is_summer = np.isin(month_idx, list(_SUMMER_MONTHS))
    out: dict[str, np.ndarray] = {}
    for zone, mw in enrollment.items():
        summer = float(mw["summer"])
        if summer <= 0.0:
            continue
        winter_frac = float(mw["winter"]) / summer
        prof = np.where(is_summer, 1.0, winter_frac).astype(float)
        out[zone] = prof
    return out


def inject_nyiso_dr_availability(
    fleet_arrays, config, iso: str, year: int, zone_names: list[str]
) -> None:
    """Overwrite DR pseudo-gen availability with the seasonal profile, in place.

    Runs after :func:`~market_sim.data.fleet.generators_to_fleet_arrays` (which
    builds flat availability) — the mirror of
    :func:`~market_sim.data.renewables.inject_offshore_wind_availability`. A
    no-op unless the gate is on, the ISO is NYISO, and DR generators are
    present. Identifies the DR rows by the ``demand_response`` fuel code and
    maps each (via ``zone_names``) to its zone's seasonal profile.
    """
    if iso != "NYISO" or not getattr(config, "nyiso_scr_edrp", False):
        return
    from market_sim.data.fleet import FUEL_TYPE_MAP

    dr_code = FUEL_TYPE_MAP["demand_response"]
    dr_idx = np.flatnonzero(fleet_arrays.fuel_type_idx == dr_code)
    if dr_idx.size == 0:
        return
    profiles = nyiso_dr_seasonal_availability(year, fleet_arrays.availability.shape[1])
    for g_idx in dr_idx:
        zone = zone_names[int(fleet_arrays.zone_idx[g_idx])]
        prof = profiles.get(zone)
        if prof is not None:
            fleet_arrays.availability[g_idx, :] = prof


def _hour_to_month(hours: int) -> np.ndarray:
    """Return a length-``hours`` array of 1-based month index (non-leap)."""
    month_start = np.cumsum((0,) + _DAYS_PER_MONTH) * 24
    idx = np.zeros(hours, dtype=int)
    for m in range(12):
        s, e = int(month_start[m]), int(month_start[m + 1])
        idx[s:e] = m + 1
    if hours > int(month_start[12]):
        idx[int(month_start[12]) :] = 12
    return idx
