#!/usr/bin/env python
"""Derive the CAISO CT_PEAKER net-load-driven reliability-commitment floor.

CAISO commits its simple-cycle gas peakers (CT_PEAKER) for **local Resource
Adequacy** during the afternoon-evening net-load ramp: as the duck-curve neck
forms (cooling load climbs while solar collapses at sunset), fast-start CTs in
the LA Basin / Big-Creek-Ventura / Bay-Area local capacity areas are committed
for local reliability regardless of whether they are in-the-money on system
energy.  An energy-only LP never dispatches them (they sit at the top of the
merit order), so the backcast under-runs CT_PEAKER and the freed energy spills
onto the cheaper combined-cycle fleet (CC_REGULAR over-runs).

This script derives the **forward-native** floor that replaces that missing
commitment.  It is the simple-cycle analog of the ERCOT CT_PEAKER net-load drag
(``docs/ercot-ct-netload-drag-2026-06.md``) and **supersedes** the earlier
TMAX-keyed CAISO floor (``inject_caiso_ct_reliability_floor``), whose flat
year-round baseline made a flat h15-22 rectangle instead of the real sharp h18
evening peak (audit ``docs/caiso-lever-audit-2026-06.md``, Lever B).  The fix is
to key the commitment to system **net-load** rather than a daily-constant TMAX,
because net-load *varies within the day* — it peaks in the evening ramp — so the
floor it drives peaks in the evening too, reproducing the diurnal shape a flat
band destroys:

  1. Build CAISO hourly net-load = EIA-930 ``CISO`` Demand − solar − wind, on
     the model's naive local-standard 8760-hour clock (UTC − 8 h, no DST), the
     same operational reserve-tightness proxy the ERCOT drag uses and the same
     net-load the runner feeds ``fleet.apply_ct_netload_drag_floor``.
  2. Regress measured CAISO CT_PEAKER evening (15-22 local) capacity factor
     (EPA CAMPD simple-cycle units routed to the model CT_PEAKER class via the
     canonical :func:`classify_plant` dominant-class map, 2023-2025) on that
     net-load.  CF = routed CT MW ÷ the model CT_PEAKER nameplate (so the
     fraction reproduces the right MW when the floor multiplies it back onto the
     model fleet's available capacity).  The relationship is a clipped line:
     ``frac = clip(slope*netGW + intercept, 0, cap)``.  These coefficients become
     the CAISO ``ScenarioConfig`` defaults in ``run_calibration._calibration_
     config`` — a measured net-load->commitment rule, NOT a fit to a generation
     /TWh residual, and forward-derivable (a forecast year has a load forecast +
     a wind/solar build, hence a net-load) and condition-responsive (more VRE
     lowers net-load and so the drag), admissible in backcast AND forecast
     (CLAUDE.md #10/#11).

Both the trigger (net-load) and the magnitude (a physical min-gen) regenerate
for a forward year, so nothing here pins the backcast to a measured outcome.
Run with no arguments to re-derive from the committed CAMPD + EIA-930 archives.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    eia923_dominant_class_by_plant,
    load_fleet_from_csv,
)

# Afternoon-evening local hours over which the local-RA CT commitment binds —
# the net-load ramp / duck-curve neck.  Half-open ``[start, end)`` so the
# regression window is byte-for-byte the application window
# (ScenarioConfig.ct_drag_ramp_start / _end, h15-21): the floor over-floors the
# h22 tail (net-load peaks late while measured CT tails off), so h22 is dropped
# from both.  Outside this window the peakers dispatch purely on price.
CT_EVENING_HOURS: tuple[int, int] = (15, 22)

HOURS = 8760
_CISO_HOURLY: Path = RAW_DIR / "eia-930-hourly" / "CISO hourly.parquet"
_CAMPD_DIR: Path = RAW_DIR / "campd-unit-level"

# Cumulative hours at the start of each month (non-leap year), for the
# date+hour -> hour-of-year mapping shared by the CAMPD and EIA-930 paths.
_MONTH_START_HOUR: list[int] = [
    0,
    744,
    1416,
    2160,
    2880,
    3624,
    4344,
    5088,
    5832,
    6552,
    7296,
    8016,
]


def _hoy_from_date_hour(date: pd.Series, hour: pd.Series) -> np.ndarray:
    """Convert (date, 0-based hour) to non-leap hour-of-year index (0-8759).

    Feb 29 in a leap year returns -1 so callers can drop it; all other dates map
    into [0, 8760) on the model's naive local-standard clock.
    """
    m = date.dt.month.to_numpy(dtype=int)
    d = date.dt.day.to_numpy(dtype=int)
    h = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR)[m - 1]
    idx = base + (d - 1) * 24 + h
    return np.where((m == 2) & (d == 29), -1, idx)


def model_ct_peaker_nameplate(year: int) -> float:
    """Return the model CAISO CT_PEAKER total nameplate (MW) for ``year``.

    The floor multiplies its fraction onto the model fleet's available CT_PEAKER
    capacity, so the capacity factor it is regressed from must use the *same*
    nameplate denominator (not a CEMS-coverage proxy) for the fraction to
    reproduce the measured MW when applied.
    """
    cfg = get_iso_config("CAISO")
    gens = load_fleet_from_csv("CAISO", cfg, year=year)
    return float(sum(g.pmax_mw for g in gens if g.plant_group == "CT_PEAKER"))


def routed_ct_peaker_mw(year: int) -> np.ndarray:
    """Measured CAISO CT_PEAKER fleet MW per hour (8760), from CAMPD CEMS.

    Each CA CAMPD unit is routed to its model dispatch class via the canonical
    :func:`classify_plant` EIA-923 dominant-class map (after the AES/HB split
    remap), and only CT_PEAKER units are summed — the same class assignment the
    dispatch fleet uses, so the regression target matches the shape-probe gate's
    measured CT_PEAKER.
    """
    dom = eia923_dominant_class_by_plant(year)
    path = _CAMPD_DIR / f"CA_{year}.parquet"
    raw = pd.read_parquet(
        path, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
    )
    raw = raw.dropna(subset=["grossLoad"])
    raw["fac"] = pd.to_numeric(raw["facilityId"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["fac"])
    eff = [
        CAMPD_UNIT_PLANT_REMAP.get((int(f), str(u)), int(f))
        for f, u in zip(raw["fac"], raw["unitId"])
    ]
    raw["klass"] = [dom.get(pc) for pc in eff]
    raw = raw[raw["klass"] == "CT_PEAKER"]
    hoy = _hoy_from_date_hour(pd.to_datetime(raw["date"]), raw["hour"].astype(int))
    ok = (hoy >= 0) & (hoy < HOURS)
    raw = raw[ok].copy()
    raw["hoy"] = hoy[ok]
    return (
        raw.groupby("hoy")["grossLoad"]
        .sum()
        .reindex(range(HOURS), fill_value=0.0)
        .to_numpy()
    )


def ciso_net_load_mw(year: int) -> np.ndarray:
    """CAISO hourly net-load = EIA-930 CISO Demand − solar − wind (MW, 8760).

    The EIA-930 ``UTC time`` stamps are shifted by a fixed −8 h to local standard
    time (PST, no DST) and laid on the model's non-leap 8760-hour grid, so the CT
    capacity factor and the net-load it is regressed on are time-aligned (same
    convention as ``scripts/caiso_shape_probe.py``).  Gaps (Feb 29 / missing
    stamps) are filled by interpolation.
    """
    df = pd.read_parquet(_CISO_HOURLY)
    utc = pd.to_datetime(df["UTC time"], utc=True)
    lst = utc.dt.tz_convert(None) - pd.Timedelta(hours=8)
    mask = lst.dt.year == year
    df = df[mask].reset_index(drop=True)
    lst = lst[mask].reset_index(drop=True)
    hoy = _hoy_from_date_hour(lst.dt.normalize(), lst.dt.hour)
    ok = (hoy >= 0) & (hoy < HOURS)
    dem = pd.to_numeric(df["Demand"], errors="coerce").to_numpy()[ok]
    sun = pd.to_numeric(df.get("NG: SUN"), errors="coerce").to_numpy()[ok]
    wnd = pd.to_numeric(df.get("NG: WND"), errors="coerce").to_numpy()[ok]
    out = np.full(HOURS, np.nan)
    out[hoy[ok]] = dem - np.nan_to_num(sun) - np.nan_to_num(wnd)
    return pd.Series(out).interpolate(limit_direction="both").to_numpy()


def _binned_median(
    x: np.ndarray, y: np.ndarray, edges: np.ndarray, min_n: int = 30
) -> np.ndarray:
    """Median ``y`` per ``x`` bin (rows with >= ``min_n`` samples)."""
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (x >= lo) & (x < hi)
        if int(sel.sum()) >= min_n:
            rows.append((0.5 * (lo + hi), float(np.median(y[sel]))))
    return np.array(rows)


def derive_curve(years: tuple[int, ...]) -> dict[str, float]:
    """Regress measured CT_PEAKER evening CF on net-load -> floor coefficients.

    Pools the evening-window (CT_EVENING_HOURS) hours across ``years``, fits a
    median-per-2-GW-bin least-squares line of capacity factor vs net-load (GW),
    and caps at the 95th-percentile evening CF (the hottest-ramp ceiling) — the
    same recipe as the ERCOT CT drag fit (``scripts/probes/_ct_netload_drag_
    fit.py``).
    """
    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    start, end = CT_EVENING_HOURS
    evening = (hod >= start) & (hod < end)

    enl, ecf = [], []
    per_year = {}
    for year in years:
        nameplate = model_ct_peaker_nameplate(year)
        mw = routed_ct_peaker_mw(year)
        nl = ciso_net_load_mw(year)
        cf = mw / nameplate
        enl.append(nl[evening] / 1000.0)
        ecf.append(cf[evening])
        per_year[year] = (mw, nl, nameplate)

    enl_all = np.concatenate(enl)
    ecf_all = np.concatenate(ecf)
    edges = np.arange(10, 46, 2)
    binned = _binned_median(enl_all, ecf_all, edges)
    slope, intercept = np.polyfit(binned[:, 0], binned[:, 1], 1)
    cap = float(np.percentile(ecf_all, 95))

    return {
        "slope_per_gw": round(float(slope), 5),
        "intercept": round(float(intercept), 4),
        "cap": round(cap, 2),
        "zero_crossing_gw": round(float(-intercept / slope), 1),
        "ramp_start": start,
        "ramp_end": end,  # ScenarioConfig ct_drag_ramp_end is EXCLUSIVE
        "_per_year": per_year,
        "_slope": float(slope),
        "_intercept": float(intercept),
        "_cap": cap,
        "_binned": binned,
    }


def main() -> None:
    """CLI entry: re-derive and print the CAISO CT net-load floor coefficients."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    coeffs = derive_curve(years)
    binned = coeffs.pop("_binned")
    per_year = coeffs.pop("_per_year")
    slope, intercept, cap = (
        coeffs.pop("_slope"),
        coeffs.pop("_intercept"),
        coeffs.pop("_cap"),
    )

    print("Binned evening CF vs net-load (GW: median CF):")
    print("  " + "  ".join(f"{c:.0f}:{m:.3f}" for c, m in binned))
    print(
        "\nDerived CT net-load reliability-floor curve "
        "(frac = clip(slope*netGW + intercept, 0, cap)):"
    )
    print(json.dumps(coeffs, indent=2))

    # Energy + diurnal cross-check: how much the floor would force per year and
    # whether its evening shape rises (vs the old flat rectangle).
    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    start, end = CT_EVENING_HOURS
    win = (hod >= start) & (hod < end)  # [start, end) — the application window
    print("\nPer-year floor energy vs measured (ramp window [start, end)):")
    for year, (mw, nl, nameplate) in per_year.items():
        base = np.clip(slope * nl / 1000.0 + intercept, 0, cap)
        floor_mw = np.where(win, base, 0.0) * nameplate
        print(
            f"  {year}: nameplate {nameplate / 1000:.2f} GW, "
            f"floor-energy {floor_mw.sum() / 1e6:.2f} TWh, "
            f"floored-total {np.maximum(floor_mw, mw).sum() / 1e6:.2f} "
            f"vs measured {mw.sum() / 1e6:.2f} TWh"
        )


if __name__ == "__main__":
    main()
