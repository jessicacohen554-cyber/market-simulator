#!/usr/bin/env python
"""Derive MISO's OWN CT_PEAKER net-load reliability-deployment floor.

MISO's simple-cycle gas peakers run far more energy than the energy-only merit
order clears for them: the keeper under-runs CT_PEAKER by 5.4-8.0 TWh in every
scored year (2023 9.05 vs 17.04, 2024 13.12 vs 19.23, 2025 13.89 vs 19.29 TWh),
and miso-228 established that the cause is NOT a hold — the LP already
dispatches everything in merit and leaves 0.020 TWh of in-merit headroom, while
the real market cleared $10-20 in 1,765 hours of 2023 with the CT fleet
running. Real MISO CTs run far below their own delivered incremental cost, which
is self-commitment / RA / local-reliability / reserve-deployment duty, not an
energy-merit outcome.

This script derives the **forward-native** floor that represents that missing
commitment for MISO — the mechanism already validated as the ERCOT and PJM
keeper (``ct_netload_drag`` / ``data.fleet.apply_ct_netload_drag_floor``), and
explicitly NOT the ``ct_mustrun_per_plant`` actuals pin, which floors each plant
at its **observed EIA-923 net generation** (rule 13 ``[R-MEASURED]``'s named
forbidden case) and is D-9 QUARANTINED in ``scripts/legitimacy_diagnostics.py``.

**Rule 25 ``[R-ISO-SCOPE]`` bites twice here, and this script is built around
it.** ERCOT's and PJM's coefficients are theirs, and so is their 15-22h window:
ERCOT/CAISO justify that window by *solar collapse* producing a sharp evening
ramp, while MISO carries far less solar and its **midday block is as strongly
driven as its evening** (miso-229: rho 0.743/0.691/0.734 midday vs
0.706/0.636/0.743 evening, CF 0.113-0.134 vs 0.124-0.146). MISO's CT commitment
is a broad high-net-load DAYTIME phenomenon, not an evening-ramp one. So this
script derives BOTH:

  1. **The window**, from MISO's own diurnal CF profile, by a rule with **no
     free parameter**: the window is the maximal contiguous run of local hours
     whose pooled mean CF is at or above the fleet's OWN 24-hour mean CF and
     whose net-load relationship is positive. The threshold is the data's own
     daily average — nothing is chosen, and the per-year windows are re-derived
     by the identical rule and printed as the year-stability check.
  2. **The curve**, by the PJM script's estimator applied to MISO data: measured
     CT_PEAKER window capacity factor (EPA CAMPD units summed over exactly the
     model fleet's pure-play CT_PEAKER plant codes) regressed on contemporaneous
     EIA-930 net load, fit in the applied functional form
     ``clip(slope*netGW + intercept, 0, cap)`` — a hinge, fit by exact grid
     search over the 2-GW bin centres (no scipy.optimize, which is FORBIDDEN).
     The cap is the 95th percentile of window CF; the unclipped ERCOT-recipe
     line is printed for the record but never applied.

Both the trigger (net load: a forecast year has a load forecast and a wind/solar
build) and the magnitude (a physical min-gen commitment) regenerate for a
forward year and respond to changed conditions, so the mechanism is admissible
in backcast AND forecast (rules 13 ``[R-MEASURED]`` / 17 ``[R-FLOOR-WINDOW]``).

Rule 23 ``[R-FROZEN-DERIVE]``: this script is FROZEN against residuals. Its
coefficients re-derive only when the CAMPD or EIA-930 source data updates, never
because a price or volume residual moved; a re-derivation commit must cite the
data change.

Run with no arguments to re-derive from the committed CAMPD + EIA-930 archives.
Writes ``data/raw/reference/miso_ct_netload_drag.json`` (the frozen record, ISO-
stamped per rule 25) and prints the diurnal window derivation, the per-year
honesty checks and the pooled fit.
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
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

ISO = "MISO"
HOURS = 8760
_MISO_HOURLY: Path = RAW_DIR / "eia-930-hourly" / "MISO hourly.parquet"
OUT_JSON: Path = RAW_DIR / "reference" / "miso_ct_netload_drag.json"

# MISO model dispatch clock is local STANDARD time: CST = UTC - 6, no DST
# (PJM's derive uses EST = UTC - 5; the clock is the one thing that MUST change
# with the ISO or the CF and the net-load it is regressed on are misaligned).
_UTC_TO_LST_HOURS = 6

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

# Only plants whose model capacity is >= this share CT_PEAKER enter the
# regression sample. CAMPD extracts are plant-summed by ORIS code, so a mixed
# site (CT units co-located with a CC or coal plant) would contribute its
# NON-CT units' generation to the "CT" signature and inflate it by several
# TWh/yr. The pure-play subset keeps the CF numerator and denominator on the
# same units; the fitted fraction then applies to the whole class. Carried
# unchanged from the PJM/ERCOT derives — a METHOD, not a coefficient (rule 25
# forbids carrying another ISO's fitted numbers, not its estimator).
_PURE_PLAY_CT_SHARE = 0.90

# CAMPD reports gross load; the model dispatches net. Simple-cycle parasitic
# load is ~1% (campd._CLASS_PARASITIC_LOAD_PCT["CT_PEAKER"] = 0.010), and the
# C1 benchmark the floor must not overshoot is EIA-923 NET by class.
_CT_NET_OF_GROSS = 0.99


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


def model_ct_peaker_plants(year: int) -> tuple[dict[int, float], float, float]:
    """Return the model's pure-play MISO CT_PEAKER plants, their nameplate, class total.

    The floor multiplies its fraction onto the model fleet's available
    CT_PEAKER capacity, so the capacity factor it is regressed from must use the
    *same* nameplate denominator (not a CEMS-coverage proxy) for the fraction to
    reproduce the measured MW when applied. The returned dict is restricted to
    pure-play plants (>= ``_PURE_PLAY_CT_SHARE`` of the plant's model capacity is
    CT_PEAKER) so the plant-summed CAMPD series measures CT units only; the CF
    denominator is the pure-play subset's own nameplate.

    Args:
        year: Fleet vintage year.

    Returns:
        ``(plants, pure_play_nameplate_mw, class_nameplate_mw)``.
    """
    cfg = get_iso_config(ISO)
    gens = load_fleet_from_csv(ISO, cfg, year=year)
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
    return plants, float(sum(plants.values())), float(sum(ct_cap.values()))


def measured_ct_mw(year: int, plant_codes: set[int]) -> np.ndarray:
    """Measured MISO CT_PEAKER fleet net MW per hour (8760), from CAMPD CEMS.

    CAMPD hourly gross for the pure-play CT_PEAKER plant codes, summed per
    hour-of-year on the model's local-standard clock (the CAMPD extracts are
    already on local standard time), netted by the simple-cycle parasitic factor
    so the regression target is on the same net basis as the model dispatch and
    the EIA-923 C1 benchmark.

    Args:
        year: Calendar year to load.
        plant_codes: Pure-play CT_PEAKER ORIS codes.

    Returns:
        Fleet net MW per hour-of-year, shape ``(8760,)``.
    """
    states = campd.states_for_iso(ISO)
    df = campd.load_campd_hourly(states, [year])
    net = campd.plant_hourly_net(
        df, {pid: _CT_NET_OF_GROSS for pid in plant_codes}, year, hours=HOURS
    )
    fleet = np.zeros(HOURS)
    for pid, series in net.items():
        if pid in plant_codes:
            fleet[: series.shape[0]] += series[:HOURS]
    return fleet


def miso_net_load_mw(year: int) -> np.ndarray:
    """MISO hourly net load = EIA-930 MISO Demand - solar - wind (MW, 8760).

    The EIA-930 ``UTC time`` stamps are shifted by a fixed -6 h to local standard
    time (CST, no DST) and laid on the model's non-leap 8760-hour grid, so the CT
    capacity factor and the net load it is regressed on are time-aligned — the
    same convention the runner feeds ``apply_ct_netload_drag_floor``.

    Args:
        year: Calendar year to extract.

    Returns:
        Net load MW per hour-of-year, shape ``(8760,)``, gaps interpolated.
    """
    df = pd.read_parquet(_MISO_HOURLY)
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


def _spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation of two equal-length series."""
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    return float(np.corrcoef(rx, ry)[0, 1])


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


def derive_window(cf: np.ndarray, nl: np.ndarray) -> tuple[int, int, dict]:
    """Derive the commitment window from MISO's own diurnal CF profile.

    Rule 17 ``[R-FLOOR-WINDOW]`` clause (b) requires a floor to state the hours it
    may bind and why; rule 25 ``[R-ISO-SCOPE]`` forbids carrying ERCOT's/PJM's
    15-22h answer, which is justified by a solar-collapse evening ramp MISO does
    not have. So the window is derived, by a rule that has **no free parameter**
    to choose:

      * threshold = the fleet's OWN 24-hour mean capacity factor (the data's own
        daily average — not a fitted level, not a percentile someone picked);
      * a candidate hour is one whose mean CF is at or above that threshold AND
        whose CF rises with net load (Spearman rho > 0, so the floor's driver is
        actually present in the hour it would bind);
      * the window is the maximal CONTIGUOUS run of candidate hours containing
        the peak-CF hour, so the applied ``[start, end)`` gate is a single block
        exactly as ``ScenarioConfig.ct_drag_ramp_start`` / ``_end`` express it.

    The construction regenerates for a forward year from a forward CT diurnal
    profile and responds to changed conditions (more solar shifts the profile and
    the window with it), so the window itself is forward-native, not a constant
    lifted from a backcast.

    Args:
        cf: Pooled hourly capacity factor, shape ``(N*8760,)``.
        nl: Pooled hourly net load in GW, aligned with *cf*.

    Returns:
        ``(start, end, detail)`` with ``end`` EXCLUSIVE (the ScenarioConfig
        convention), and *detail* carrying the per-hour profile and the rule's
        own inputs for the record.
    """
    hod = np.tile(np.arange(HOURS) % 24, cf.shape[0] // HOURS)
    mean_cf = np.array([float(cf[hod == h].mean()) for h in range(24)])
    rho = np.array([_spearman(nl[hod == h], cf[hod == h]) for h in range(24)])
    threshold = float(cf.mean())  # the fleet's own 24-h mean — zero DOF
    ok = (mean_cf >= threshold) & (rho > 0.0)

    # Maximal contiguous run containing the peak-CF hour. The scan is cyclic so
    # a window that wrapped midnight would still be found as one block; MISO's
    # does not wrap (its overnight CF is the daily minimum), and a wrapping
    # result would be reported rather than silently truncated.
    peak = int(np.argmax(mean_cf))
    if not ok[
        peak
    ]:  # pragma: no cover - the peak hour is above the mean by construction
        raise RuntimeError("peak-CF hour failed the window rule; inspect the profile")
    start = peak
    while ok[(start - 1) % 24]:
        start = (start - 1) % 24
        if start == peak:
            break
    end = peak
    while ok[(end + 1) % 24]:
        end = (end + 1) % 24
        if end == peak:
            break
    detail = {
        "rule": (
            "maximal contiguous hours with mean CF >= the fleet's own 24-h mean "
            "CF and Spearman rho(CF, net load) > 0; zero free parameters"
        ),
        "threshold_mean_cf": round(threshold, 5),
        "peak_cf_hour": peak,
        "hour_of_day_mean_cf": [round(v, 4) for v in mean_cf.tolist()],
        "hour_of_day_rho": [round(v, 3) for v in rho.tolist()],
        "hours_selected": [h for h in range(24) if ok[h]],
    }
    return int(start), int((end + 1) % 24), detail


def fit_hinge(
    nl_win: np.ndarray, cf_win: np.ndarray
) -> tuple[float, float, float, dict]:
    """Fit ``clip(slope*netGW + intercept, 0, cap)`` on the window sample.

    The applied mechanism is a clipped line, so the estimator fits that exact
    functional form rather than an unclipped least-squares line that would
    misfit both regimes of a two-regime curve (the PJM derive's finding). The
    knee is grid-searched exactly over the 2-GW bin centres and the active
    segment is a least-squares line; ``scipy.optimize`` is FORBIDDEN by the stack
    rules and is not used. The cap is the 95th percentile of window CF — the
    hottest ramp hours the fleet actually reaches.

    Args:
        nl_win: Window-hour net load in GW (pooled over years).
        cf_win: Window-hour capacity factor, aligned with *nl_win*.

    Returns:
        ``(slope, intercept, cap, detail)``; *detail* carries the binned curve,
        both fits' SSE and the unclipped ERCOT-recipe line for the record.
    """
    lo = float(np.floor(np.percentile(nl_win, 0.5) / 2.0) * 2.0)
    hi = float(np.ceil(np.percentile(nl_win, 99.5) / 2.0) * 2.0) + 2.0
    edges = np.arange(lo, hi, 2.0)
    binned = _binned_median(nl_win, cf_win, edges)
    cap = float(np.percentile(cf_win, 95))

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
    if (
        best is None
    ):  # pragma: no cover - a non-positive slope everywhere refutes the driver
        raise RuntimeError("no positive-slope hinge exists; the driver is absent")
    sse_hinge, slope, intercept = best

    s_lin, b_lin = np.polyfit(binned[:, 0], binned[:, 1], 1)
    pred_lin = np.clip(s_lin * binned[:, 0] + b_lin, 0.0, cap)
    detail = {
        "binned_cf_by_netload_gw": [
            {"netload_gw": round(c, 1), "median_cf": round(m, 4)} for c, m in binned
        ],
        "sse_hinge": round(sse_hinge, 5),
        "unclipped_line_for_the_record": {
            "slope": round(float(s_lin), 5),
            "intercept": round(float(b_lin), 4),
            "sse": round(float(((pred_lin - binned[:, 1]) ** 2).sum()), 5),
        },
    }
    return slope, intercept, cap, detail


def main() -> int:
    """CLI entry: re-derive and record MISO's CT net-load drag window + curve."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args()
    years = tuple(args.years)

    per_year: dict[int, tuple[np.ndarray, np.ndarray, float, float, int]] = {}
    cf_all, nl_all = [], []
    for year in years:
        plants, pure_mw, class_mw = model_ct_peaker_plants(year)
        mw = measured_ct_mw(year, set(plants))
        nl = miso_net_load_mw(year) / 1000.0  # GW
        cf = mw / max(pure_mw, 1e-9)
        per_year[year] = (mw, nl, pure_mw, class_mw, len(plants))
        cf_all.append(cf)
        nl_all.append(nl)
        print(
            f"\n=== {year}: {len(plants)} pure-play CT_PEAKER plants, nameplate "
            f"{pure_mw / 1000:.2f} GW ({pure_mw / max(class_mw, 1e-9):.2f} of class), "
            f"measured {mw.sum() / 1e6:.3f} TWh (CF {cf.mean():.4f})"
        )

    cf_pool = np.concatenate(cf_all)
    nl_pool = np.concatenate(nl_all)
    start, end, wdetail = derive_window(cf_pool, nl_pool)

    print(
        "\n=== WINDOW DERIVATION (MISO's own diurnal profile; zero free parameters) ==="
    )
    print(f"  threshold = fleet 24-h mean CF = {wdetail['threshold_mean_cf']:.4f}")
    print("  hour: meanCF (rho)")
    for h in range(24):
        mark = "*" if h in wdetail["hours_selected"] else " "
        print(
            f"   {mark}{h:02d}: {wdetail['hour_of_day_mean_cf'][h]:.4f} "
            f"({wdetail['hour_of_day_rho'][h]:+.3f})"
        )
    print(f"  -> DERIVED WINDOW [{start}, {end}) local standard (CST)")

    # Year-stability honesty check: re-derive the window per year by the same
    # rule. A window that moves year to year is not a structural driver.
    per_year_windows = {}
    for i, year in enumerate(years):
        s_y, e_y, _ = derive_window(cf_all[i], nl_all[i])
        per_year_windows[str(year)] = [s_y, e_y]
        print(f"  year-stability: {year} -> [{s_y}, {e_y})")

    hod = np.tile(np.arange(HOURS) % 24, len(years))
    win = (hod >= start) & (hod < end) if start < end else (hod >= start) | (hod < end)
    slope, intercept, cap, fdetail = fit_hinge(nl_pool[win], cf_pool[win])

    print("\n=== POOLED WINDOW FIT (median per 2-GW bin, applied functional form) ===")
    print(
        "  "
        + "  ".join(
            f"{r['netload_gw']:.0f}:{r['median_cf']:.3f}"
            for r in fdetail["binned_cf_by_netload_gw"]
        )
    )
    lin = fdetail["unclipped_line_for_the_record"]
    print(
        f"  unclipped line (ERCOT recipe, NOT applied): slope {lin['slope']:.5f}, "
        f"intercept {lin['intercept']:+.4f}, SSE {lin['sse']:.5f}"
    )
    print(f"  hinge fit (the applied form): SSE {fdetail['sse_hinge']:.5f}")

    coeffs = {
        "ct_drag_slope_per_gw": round(float(slope), 5),
        "ct_drag_intercept": round(float(intercept), 4),
        "ct_drag_cap": round(float(cap), 4),
        "ct_drag_ramp_start": int(start),
        "ct_drag_ramp_end": int(end),  # ScenarioConfig ct_drag_ramp_end is EXCLUSIVE
    }
    print(json.dumps(coeffs, indent=2))

    # Energy cross-check: the floor is a MINIMUM the LP exceeds economically, so
    # it must sit UNDER the measured annual CT total, not reproduce it. A floor
    # energy at or above measured would be an actuals pin in disguise.
    energy = {}
    print("\nPer-year floor energy vs measured (window [start, end)):")
    for i, year in enumerate(years):
        mw, nl, pure_mw, _, _ = per_year[year]
        h24 = np.arange(HOURS) % 24
        w = (
            (h24 >= start) & (h24 < end)
            if start < end
            else (h24 >= start) | (h24 < end)
        )
        base = np.clip(slope * nl + intercept, 0.0, cap)
        floor_mw = np.where(w, base, 0.0) * pure_mw
        energy[str(year)] = {
            "floor_twh_on_pure_play": round(float(floor_mw.sum()) / 1e6, 3),
            "measured_twh_pure_play": round(float(mw.sum()) / 1e6, 3),
            "floored_total_twh": round(float(np.maximum(floor_mw, mw).sum()) / 1e6, 3),
        }
        e = energy[str(year)]
        print(
            f"  {year}: floor-energy {e['floor_twh_on_pure_play']:.3f} TWh, "
            f"floored-total {e['floored_total_twh']:.3f} vs measured "
            f"{e['measured_twh_pure_play']:.3f} TWh"
        )

    record = {
        "iso": ISO,  # rule 25 [R-ISO-SCOPE]: the artifact records what it was fitted on
        "derive_script": "scripts/data/derive_miso_ct_netload_drag.py",
        "mechanism": "ct_netload_drag / data.fleet.apply_ct_netload_drag_floor",
        "years": list(years),
        "clock": "local standard CST = UTC-6, no DST",
        "sources": {
            "cf_numerator": "EPA CAMPD hourly CEMS, pure-play model CT_PEAKER plants",
            "cf_denominator": "model fleet pure-play CT_PEAKER nameplate (MW)",
            "net_load": "EIA-930 MISO Demand - NG:SUN - NG:WND",
        },
        "coefficients": coeffs,
        "window_derivation": wdetail,
        "window_per_year": per_year_windows,
        "fit": fdetail,
        "energy_cross_check": energy,
        "fleet_by_year": {
            str(y): {
                "pure_play_plants": per_year[y][4],
                "pure_play_nameplate_mw": round(per_year[y][2], 0),
                "class_nameplate_mw": round(per_year[y][3], 0),
                "measured_twh_pure_play": round(float(per_year[y][0].sum()) / 1e6, 3),
            }
            for y in years
        },
        "frozen": (
            "rule 23 [R-FROZEN-DERIVE]: re-derive only when CAMPD or EIA-930 "
            "source data updates, never because a residual moved"
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(record, indent=1))
    print(f"\n-> {OUT_JSON.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
