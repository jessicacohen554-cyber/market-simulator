#!/usr/bin/env python
"""Derive the PJM CT_PEAKER net-load-driven reliability-deployment floor.

PJM's simple-cycle gas peakers (CT_PEAKER) run far more energy than an
energy-only merit order clears for them: reserve deployments, RUC-style
supplemental commitments and local reliability calls put ~27.8 TWh through the
real 2024 CT fleet (~10.6% fleet CF) while the model clears ~19 TWh — the
diagnosed 2024 CT under-run whose freed energy spills onto the cheaper
combined-cycle fleet (CC_REGULAR over-runs, the pjm-74 C1 gap). The offer axis
cannot close it: offer-multiplier moves shift all three years uniformly
(run-74), while the gap is deployment energy the merit order never sees.

This script derives the **forward-native** floor that replaces that missing
commitment for PJM — the same mechanism already validated as the ERCOT keeper
(``docs/ercot-ct-netload-drag-2026-06.md``, keeper 2026-07-01-24-ct-drag-v1)
and the CAISO keeper default (``scripts/derive_caiso_ct_reliability_floor.py``):

  1. Build PJM hourly net-load = EIA-930 ``PJM`` Demand − solar − wind, on the
     model's naive local-standard 8760-hour clock (UTC − 5 h, EST, no DST) —
     the same operational reserve-tightness proxy the ERCOT/CAISO drags use and
     the same net-load convention the runner feeds
     ``fleet.apply_ct_netload_drag_floor``.
  2. Regress measured PJM CT_PEAKER ramp-window capacity factor (EPA CAMPD
     units summed over exactly the model fleet's CT_PEAKER plant codes,
     2023-2025) on that net-load. CF = measured CT MW ÷ the model CT_PEAKER
     nameplate, so the fraction reproduces the right MW when the floor
     multiplies it back onto the model fleet's available capacity. The
     relationship is a clipped line ``frac = clip(slope*netGW + intercept, 0,
     cap)`` gated to the afternoon-evening ramp window, applied via
     ``ct_drag_overrides`` in the pjm-75 driver.

Both the trigger (net-load: a forecast year has a load forecast and a
wind/solar build) and the magnitude (a physical min-gen commitment) regenerate
for a forward year and respond to changed conditions (more VRE lowers net-load
and therefore the drag), so the mechanism is admissible in backcast AND
forecast (CLAUDE.md #12/#13) — explicitly NOT the measured-actuals
``ct_mustrun_per_plant`` / ``ct_deployment_overlay`` pins, which force observed
generation and have no forward analogue.

Run with no arguments to re-derive from the committed CAMPD + EIA-930 archives;
the script prints the per-time-block CF-vs-net-load tables and Spearman rho per
year (the honesty checks: the fit is only usable if the ramp-window
relationship is monotonic and year-stable) before the pooled fit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

# Afternoon-evening local hours over which the reliability/deployment CT
# commitment binds — the net-load ramp. Half-open [start, end) so the
# regression window is byte-for-byte the application window
# (ScenarioConfig.ct_drag_ramp_start / _end). Same window as the ERCOT keeper
# (docs/ercot-ct-netload-drag-2026-06.md) and the CAISO keeper; the printed
# per-block tables verify it is also PJM's high-CF block.
CT_EVENING_HOURS: tuple[int, int] = (15, 22)

HOURS = 8760
_PJM_HOURLY: Path = RAW_DIR / "eia-930-hourly" / "PJM hourly.parquet"
# PJM model dispatch clock is local STANDARD time: EST = UTC - 5, no DST.
_UTC_TO_LST_HOURS = 5

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


# Only plants whose model capacity is >= this share CT_PEAKER enter the
# regression sample. CAMPD's PJM extracts are plant-summed by ORIS code, so a
# mixed site (CT units co-located with a CC or coal plant, e.g. ORIS 1571:
# 390 MW CT at a 1.6 GW plant) would contribute its NON-CT units' generation
# to the "CT" signature and inflate it by several TWh/yr. The pure-play subset
# (110 of 121 plants, 23.5 of 25.6 GW) keeps the CF numerator and denominator
# on the same units; the fitted fraction then applies to the whole class.
_PURE_PLAY_CT_SHARE = 0.90

# CAMPD reports gross load; the model dispatches net. Simple-cycle parasitic
# load is ~1% (campd._CLASS_PARASITIC_LOAD_PCT["CT_PEAKER"] = 0.010), and the
# C1 benchmark the floor must not overshoot is EIA-923 NET by class.
_CT_NET_OF_GROSS = 0.99


def model_ct_peaker_plants(year: int) -> tuple[dict[int, float], float]:
    """Return the model's pure-play PJM CT_PEAKER plants + class nameplate (MW).

    The floor multiplies its fraction onto the model fleet's available
    CT_PEAKER capacity, so the capacity factor it is regressed from must use
    the *same* nameplate denominator (not a CEMS-coverage proxy) for the
    fraction to reproduce the measured MW when applied. The returned dict is
    restricted to pure-play plants (>= ``_PURE_PLAY_CT_SHARE`` of the plant's
    model capacity is CT_PEAKER) so the plant-summed CAMPD series measures CT
    units only; the CF denominator is the pure-play subset's own nameplate.
    """
    cfg = get_iso_config("PJM")
    gens = load_fleet_from_csv("PJM", cfg, year=year)
    plant_cap: dict[int, float] = {}
    ct_cap: dict[int, float] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group == "CT_PEAKER":
            ct_cap[pc] = ct_cap.get(pc, 0.0) + float(g.pmax_mw)
    plants = {
        pc: cap
        for pc, cap in ct_cap.items()
        if cap / plant_cap[pc] >= _PURE_PLAY_CT_SHARE
    }
    return plants, float(sum(plants.values()))


def measured_ct_mw(year: int, plant_codes: set[int]) -> np.ndarray:
    """Measured PJM CT_PEAKER fleet net MW per hour (8760), from CAMPD CEMS.

    CAMPD hourly gross for the pure-play CT_PEAKER plant codes, summed per
    hour-of-year on the model's local-standard clock (the CAMPD extracts are
    already on local standard time), netted by the simple-cycle parasitic
    factor so the regression target is on the same net basis as the model
    dispatch and the EIA-923 C1 benchmark.
    """
    states = campd.states_for_iso("PJM")
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: _CT_NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    fleet = np.zeros(HOURS)
    for pid, series in net.items():
        if pid in plant_codes:
            fleet[: series.shape[0]] += series[:HOURS]
    return fleet


def pjm_net_load_mw(year: int) -> np.ndarray:
    """PJM hourly net-load = EIA-930 PJM Demand − solar − wind (MW, 8760).

    The EIA-930 ``UTC time`` stamps are shifted by a fixed −5 h to local
    standard time (EST, no DST) and laid on the model's non-leap 8760-hour
    grid, so the CT capacity factor and the net-load it is regressed on are
    time-aligned (same convention as the CAISO derive script; the ERCOT doc
    shows the fit washes out without this alignment).
    """
    df = pd.read_parquet(_PJM_HOURLY)
    utc = pd.to_datetime(df["UTC time"])
    lst = utc - pd.Timedelta(hours=_UTC_TO_LST_HOURS)
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


def main() -> None:
    """CLI entry: re-derive and print the PJM CT net-load floor coefficients."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    hod = pd.date_range("2023-01-01", periods=HOURS, freq="h").hour.to_numpy()
    start, end = CT_EVENING_HOURS
    evening = (hod >= start) & (hod < end)

    enl, ecf = [], []
    per_year = {}
    for year in years:
        plants, nameplate = model_ct_peaker_plants(year)
        mw = measured_ct_mw(year, set(plants))
        nl = pjm_net_load_mw(year)
        cf = mw / nameplate
        rho = pd.Series(nl[evening]).corr(pd.Series(cf[evening]), method="spearman")
        rho_all = pd.Series(nl).corr(pd.Series(cf), method="spearman")
        print(
            f"\n=== {year}: {len(plants)} CT_PEAKER plants, nameplate "
            f"{nameplate / 1000:.2f} GW, measured {mw.sum() / 1e6:.2f} TWh "
            f"(CF {mw.mean() / nameplate:.3f}); Spearman(netload,CF) "
            f"evening rho={rho:.2f}, all-hours rho={rho_all:.2f} ==="
        )
        # Diurnal-block honesty check: the window gate is only right if the
        # ramp block carries the commitment and overnight does not.
        edges5 = np.arange(40, 145, 10)
        for label, mask in [
            ("overnight 00-05", hod < 6),
            ("morning 06-09", (hod >= 6) & (hod < 10)),
            ("midday 10-14", (hod >= 10) & (hod < 15)),
            (f"ramp {start}-{end}", evening),
            ("late 22-23", hod >= 22),
        ]:
            rows = _binned_median(nl[mask] / 1000.0, cf[mask], edges5)
            s = "  ".join(f"{int(c)}:{m:.3f}" for c, m in rows)
            print(f"  {label:<16} CFbyNL(GW)  {s}")
        enl.append(nl[evening] / 1000.0)
        ecf.append(cf[evening])
        per_year[year] = (mw, nl, nameplate)

    # Pooled median-per-2GW-bin fit on the ramp-window block. ERCOT/CAISO fit
    # an unclipped least-squares line through every bin because their curves
    # are linear over the whole observed net-load range, so the line IS the
    # clipped line's active segment. PJM's curve is two-regime — flat
    # ~0.07-0.09 CF below ~100 GW (routine economic peaking the merit order
    # already prices), then a clean linear reliability-deployment rise — so an
    # unclipped line through all bins misfits BOTH regimes (it over-floors
    # 85-105 GW by ~2x and under-floors the top). The applied mechanism is
    # ``clip(slope*netGW + intercept, 0, cap)`` — a hinge — so we fit that
    # exact functional form: grid-search the hinge knee over the bin centers,
    # least-squares line on the bins at/above the knee, and keep the
    # (knee, slope, intercept) minimizing SSE of the CLIPPED prediction over
    # ALL bins. Same estimand as ERCOT (the clipped line), correctly fit to a
    # curve whose lower regime sits below the hinge. No scipy.optimize
    # (forbidden): the knee grid is exact over the 2-GW bin centers.
    enl_all = np.concatenate(enl)
    ecf_all = np.concatenate(ecf)
    edges = np.arange(40, 145, 2)
    binned = _binned_median(enl_all, ecf_all, edges)
    cap = float(np.percentile(ecf_all, 95))

    best = None
    for knee_i in range(len(binned) - 3):  # >= 4 bins in the active segment
        seg = binned[knee_i:]
        s, b = np.polyfit(seg[:, 0], seg[:, 1], 1)
        if s <= 0.0:
            continue
        pred = np.clip(s * binned[:, 0] + b, 0.0, cap)
        sse = float(((pred - binned[:, 1]) ** 2).sum())
        if best is None or sse < best[0]:
            best = (sse, float(s), float(b))
    sse_hinge, slope, intercept = best

    # The ERCOT-recipe unclipped line, for the record (printed, not used).
    s_lin, b_lin = np.polyfit(binned[:, 0], binned[:, 1], 1)
    pred_lin = np.clip(s_lin * binned[:, 0] + b_lin, 0.0, cap)
    sse_lin = float(((pred_lin - binned[:, 1]) ** 2).sum())

    print("\n=== POOLED ramp-window fit (median per 2-GW bin) ===")
    print("Binned CF vs net-load (GW: median CF):")
    print("  " + "  ".join(f"{c:.0f}:{m:.3f}" for c, m in binned))
    print(
        f"unclipped-line fit (ERCOT recipe): slope {s_lin:.5f}, intercept "
        f"{b_lin:+.4f}, SSE(clipped pred) {sse_lin:.4f}"
    )
    print(f"hinge fit (functional form of the applied floor): SSE {sse_hinge:.4f}")
    coeffs = {
        "ct_drag_slope_per_gw": round(float(slope), 5),
        "ct_drag_intercept": round(float(intercept), 4),
        "ct_drag_cap": round(cap, 2),
        "ct_drag_ramp_start": start,
        "ct_drag_ramp_end": end,  # ScenarioConfig ct_drag_ramp_end is EXCLUSIVE
        "zero_crossing_gw": round(float(-intercept / slope), 1),
    }
    print(json.dumps(coeffs, indent=2))

    # Energy cross-check: the floor should reproduce the measured annual CT
    # total as a minimum the LP exceeds economically, not overshoot it.
    win = evening
    print("\nPer-year floor energy vs measured (ramp window [start, end)):")
    for year, (mw, nl, nameplate) in per_year.items():
        base = np.clip(slope * nl / 1000.0 + intercept, 0, cap)
        floor_mw = np.where(win, base, 0.0) * nameplate
        print(
            f"  {year}: floor-energy {floor_mw.sum() / 1e6:.2f} TWh, "
            f"floored-total {np.maximum(floor_mw, mw).sum() / 1e6:.2f} "
            f"vs measured {mw.sum() / 1e6:.2f} TWh"
        )


if __name__ == "__main__":
    main()
