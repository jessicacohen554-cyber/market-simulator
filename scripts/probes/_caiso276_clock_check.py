"""caiso-276 phase 0 part 3: is the diurnal residual signature REAL, or is it an
artifact of my own instrument's clock? ZERO LP.

Part 2 measured, ex-December, that 2022's C3a residual concentrates in the RAMP
SHOULDERS (hod 6-9 +2.32, hod 19-22 +2.46 of a +6.90 within-subset total) while
the belly CORE (hod 10-16) carries almost none (+0.241/+0.113/-0.003/+0.191/
-0.049 at hod 12-16), and that hod 17 carries a LARGE NEGATIVE (-0.699, model
100.67 against an actual 115.31). Model evening peak hod 18-19, actual hod 17.

A ONE-HOUR misalignment between the committed hourly actual LMP series and the
model's own hour index would MANUFACTURE exactly that signature. This probe
falsifies-or-confirms the alignment three independent ways, none of which reads
the price residual:

  C-1  DEMAND CLOCK IDENTITY. The model dispatches the measured CAISO demand
       (``caiso_supply_consistent_demand`` + ``caiso_demand_clock_realign``
       armed). Compare the model's own hourly demand against the measured
       EIA-930 CAISO demand hour-for-hour. A zero-lag maximum here proves the
       MODEL's clock is the measured clock.
  C-2  ACTUAL-PRICE vs MEASURED-DEMAND CLOCK. Cross-correlate the committed
       hourly actual RT LMP against that same measured demand. Real RT price
       and real demand share a clock, so a zero-lag maximum proves the ACTUAL
       PRICE series is on the measured clock too. C-1 and C-2 together put both
       sides of the comparison on one clock with no reference to the model's
       price.
  C-3  SHIFT SWEEP, reported for completeness. The load-weighted MAE and
       Pearson of model price against the actual under shifts -3..+3 h. This is
       REPORTED, never used to choose an alignment: choosing the shift that
       minimizes the residual would be fitting the instrument to the answer.
       Its only job is to show the size of the effect a one-hour error would
       have had.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results/calibration/caiso275_B_gascoupling_2022"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
OUT = REPO / "results/calibration/_caiso276_clock_check.json"
YEAR = 2022
T = 8760
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")


def lw(v, w) -> float:
    return float((np.asarray(v, float) * np.asarray(w, float)).sum() / np.sum(w))


def xcorr(a: np.ndarray, b: np.ndarray, lags=range(-3, 4)) -> dict:
    """Pearson of ``a`` against ``b`` rolled by each lag (positive = b later)."""
    a = (a - a.mean()) / a.std()
    return {
        int(k): round(float(np.corrcoef(a, (b - b.mean()) / b.std())[0, 1]), 5)
        for k, b in ((k, np.roll(b, k)) for k in lags)
    }


def main() -> None:
    out: dict = {"session": "caiso-276", "year": YEAR, "phase": "0c"}
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")
    zones = [z for z in CA_ZONES if z in pr.columns]
    P = pr[zones].to_numpy(float).T
    D = dm[zones].to_numpy(float).T
    lam = (P * D).sum(axis=0) / D.sum(axis=0)
    model_dem = D.sum(axis=0)

    act = pd.read_parquet(ACTUAL)
    act = act[act["year"] == YEAR].sort_values("hour")
    rt = act["rt"].to_numpy(float)

    from market_sim.data.eia930.demand import _load_caiso_hourly_demand

    md = _load_caiso_hourly_demand(YEAR)
    meas_dem = None
    if md is not None:
        arr = md[0] if isinstance(md, tuple) else md
        arr = np.asarray(arr, float)
        meas_dem = arr.ravel() if arr.ndim == 1 else arr.sum(axis=0)
        if meas_dem.size != T:
            out["meas_dem_size"] = int(meas_dem.size)
            meas_dem = meas_dem[:T] if meas_dem.size > T else None
    out["measured_demand_available"] = meas_dem is not None

    # ---- C-1: model demand vs measured demand ----
    if meas_dem is not None:
        c1 = xcorr(model_dem, meas_dem)
        best1 = max(c1, key=c1.get)
        out["C1_model_demand_vs_measured_demand"] = {
            "xcorr": c1,
            "argmax_lag_h": best1,
            "verdict": "PASS (model clock == measured clock)"
            if best1 == 0
            else f"FAIL (model demand leads/lags by {best1} h)",
        }
        print("=== C-1  model demand  vs  measured EIA-930 demand ===")
        for k, v in c1.items():
            print(
                f"   lag {k:>+3d} h : {v:>8.5f}{'   <= ARGMAX' if k == best1 else ''}"
            )
        print(f"   VERDICT: {out['C1_model_demand_vs_measured_demand']['verdict']}")

        # ---- C-2: committed actual RT price vs measured demand ----
        c2 = xcorr(rt, meas_dem)
        best2 = max(c2, key=c2.get)
        out["C2_actual_price_vs_measured_demand"] = {
            "xcorr": c2,
            "argmax_lag_h": best2,
            "verdict": "PASS (actual-price clock == measured clock)"
            if best2 == 0
            else f"FAIL (actual price off by {best2} h)",
        }
        print("\n=== C-2  committed actual RT LMP  vs  measured EIA-930 demand ===")
        for k, v in c2.items():
            print(
                f"   lag {k:>+3d} h : {v:>8.5f}{'   <= ARGMAX' if k == best2 else ''}"
            )
        print(f"   VERDICT: {out['C2_actual_price_vs_measured_demand']['verdict']}")

    # ---- C-3: shift sweep, REPORTED ONLY ----
    w = model_dem
    sweep = []
    for k in range(-3, 4):
        r = np.roll(rt, k)
        sweep.append(
            {
                "shift_h": k,
                "lw_mae": round(lw(np.abs(lam - r), w), 3),
                "lw_bias": round(lw(lam - r, w), 3),
                "pearson": round(float(np.corrcoef(lam, r)[0, 1]), 5),
            }
        )
    out["C3_shift_sweep_reported_only"] = sweep
    print("\n=== C-3  shift sweep (REPORTED, never used to choose alignment) ===")
    print("  shift   lw_MAE  lw_bias  pearson")
    for r in sweep:
        print(
            f"  {r['shift_h']:>+5d} {r['lw_mae']:>8.3f} {r['lw_bias']:>+8.3f}"
            f" {r['pearson']:>8.5f}"
        )
    best = max(sweep, key=lambda r: r["pearson"])
    print(
        f"   pearson argmax at shift {best['shift_h']:+d} h"
        f" (bias there {best['lw_bias']:+.3f}, at 0 h"
        f" {sweep[3]['lw_bias']:+.3f})"
    )
    out["C3_pearson_argmax_shift_h"] = best["shift_h"]

    # ---- the diurnal profiles side by side, ex-December ----
    _MD = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    _CUM = np.cumsum((0,) + tuple(d * 24 for d in _MD))[:12]
    midx = np.clip(np.searchsorted(_CUM, np.arange(T), side="right") - 1, 0, 11)
    hod = np.arange(T) % 24
    ex = midx != 11
    prof = []
    for h in range(24):
        m = (hod == h) & ex
        ww = w[m]
        prof.append(
            {
                "hod": h,
                "model": round(lw(lam[m], ww), 2),
                "actual": round(lw(rt[m], ww), 2),
                "model_dem_mw": round(float(model_dem[m].mean()), 0),
                "meas_dem_mw": (
                    round(float(meas_dem[m].mean()), 0)
                    if meas_dem is not None
                    else None
                ),
            }
        )
    out["diurnal_profile_ex_december"] = prof
    print("\n=== diurnal profile, EX-DECEMBER (the shape the shift would move) ===")
    print("  hod   model  actual   modelDem   measDem")
    for r in prof:
        md_s = "      n/a" if r["meas_dem_mw"] is None else f"{r['meas_dem_mw']:>9.0f}"
        print(
            f"  {r['hod']:>3d} {r['model']:>7.2f} {r['actual']:>7.2f}"
            f" {r['model_dem_mw']:>10.0f} {md_s}"
        )
    am = max(prof, key=lambda r: r["model"])["hod"]
    aa = max(prof, key=lambda r: r["actual"])["hod"]
    dm_pk = max(prof, key=lambda r: r["model_dem_mw"])["hod"]
    out["peak_hours_ex_december"] = {
        "model_price_peak_hod": am,
        "actual_price_peak_hod": aa,
        "model_demand_peak_hod": dm_pk,
        "meas_demand_peak_hod": (
            max(prof, key=lambda r: r["meas_dem_mw"])["hod"]
            if meas_dem is not None
            else None
        ),
    }
    print(
        f"\n   model price peaks hod {am}; actual price peaks hod {aa};"
        f" model demand peaks hod {dm_pk}"
        + (
            f"; measured demand peaks hod {out['peak_hours_ex_december']['meas_demand_peak_hod']}"
            if meas_dem is not None
            else ""
        )
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
