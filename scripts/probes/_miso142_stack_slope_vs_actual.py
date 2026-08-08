"""miso-142 gate G-B/G-C2 — the model's supply curve vs the MEASURED one.

No solve.  This is the session's decisive instrument.  G-B measured the slope of
the model's own summer-afternoon stack from the keeper's committed P1 output;
the question that settles the lane is whether MISO's REAL stack has the same
shape.  Both curves are built the same way -- bin the window's hours by the
thermal MW that had to be served, take the median clearing price per bin -- so
the comparison is like-for-like:

* **model side:** keeper P1 price + P1 class dispatch (committed sidecars).
* **actual side:** measured RT LMP (``actual_lmp_hourly_MISO.parquet``) +
  EIA-930 measured generation by fuel, on the repo's own clock (PREREG §2.3).

**The x-axes are NOT on the same instrument** -- EIA-930 hourly BA generation and
the model's grid-delivered dispatch differ by a level offset (measured: EIA-930's
MISO coal total runs ~6 % under EIA-923's, and the model's grid basis excludes
BTM CHP host supply).  So the curves are ALSO reported on a **self-centred**
x-axis (thermal minus that side's own window median), which removes any constant
offset and leaves the shape.  A slope in $/MWh per GW is invariant to that
offset; a raw intercept is not, and none is quoted.

**What this distinguishes** -- the whole point:
* *Right curve, wrong point* -> the two curves overlie and the model simply sits
  lower on it.  A QUANTITY repair (H1) could then work.
* *Wrong curve* -> the model's curve is flatter, so no quantity displacement
  reaches the measured price.  A quantity repair cannot work at any size, and the
  object is price formation.

Probe hygiene (miso-140b §6): REPO ROOT on ``sys.path``, ``load_zonal_shares``
asserted non-None.

Usage::

    .venv/bin/python scripts/probes/_miso142_stack_slope_vs_actual.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso137_c3a_gap_decomposition import (  # noqa: E402
    HOURS,
    actual_hourly,
    model_hourly,
    month_of_hour,
)
from _miso142_marginal_and_slope import THERMAL_COLS, classes  # noqa: E402

OUT = REPO / "results/calibration/_miso142_stack_slope_vs_actual.json"
YEARS = (2023, 2024, 2025)  # rule 22

W1_MONTHS, W1_HOD = (6, 7), (8, 21)
SUMMER_JJA, AFT_HOD = (6, 7, 8), (12, 13, 14, 15, 16, 17)
N_BINS = 10
# Quantile band the slope is fitted over -- the central 80 % of the window's own
# hours, so a handful of extreme hours on either side cannot set the slope.
FIT_LO, FIT_HI = 0.10, 0.90


def curve(q: np.ndarray, p: np.ndarray, n: int = N_BINS) -> dict:
    """Median price by thermal-requirement decile, plus a self-centred x."""
    med = float(np.median(q))
    edges = np.quantile(q, np.linspace(0, 1, n + 1))
    rows = []
    for i in range(n):
        lo, hi = edges[i], edges[i + 1]
        sel = (q >= lo) & (q <= hi) if i == n - 1 else (q >= lo) & (q < hi)
        if sel.sum() < 5:
            continue
        rows.append(
            {
                "n": int(sel.sum()),
                "thermal_gw": round(float(np.median(q[sel])) / 1000.0, 4),
                "thermal_gw_centred": round(float(np.median(q[sel]) - med) / 1000.0, 4),
                "price_median": round(float(np.median(p[sel])), 3),
                "price_p90": round(float(np.quantile(p[sel], 0.90)), 3),
            }
        )
    return {"median_thermal_gw": round(med / 1000.0, 3), "bins": rows}


def robust_slope(q: np.ndarray, p: np.ndarray) -> dict:
    """OLS slope of price on thermal GW over the window's central 80 % of hours.

    Fitted on the hours themselves (not the binned medians) so the standard
    error is meaningful, and restricted to the central band so the estimate is
    a slope of the BODY of the stack rather than of its two endpoints.
    """
    lo, hi = np.quantile(q, FIT_LO), np.quantile(q, FIT_HI)
    sel = (q >= lo) & (q <= hi)
    x, y = q[sel] / 1000.0, p[sel]
    if len(x) < 20:
        return {"n": int(len(x)), "slope_usd_per_gw": None}
    xc = x - x.mean()
    b = float((xc * (y - y.mean())).sum() / (xc * xc).sum())
    a = float(y.mean() - b * x.mean())
    resid = y - (a + b * x)
    se = float(np.sqrt((resid**2).sum() / max(1, len(x) - 2) / (xc * xc).sum()))
    return {
        "n": int(len(x)),
        "slope_usd_per_gw": round(b, 4),
        "se": round(se, 4),
        "band_gw": [round(lo / 1000.0, 2), round(hi / 1000.0, 2)],
        "r2": round(
            float(1.0 - (resid**2).sum() / ((y - y.mean()) ** 2).sum()), 4
        ),
    }


def main() -> None:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zs = load_zonal_shares("MISO", 2025, [z.name for z in get_iso_config("MISO").zones])
    assert zs is not None, "load_zonal_shares None -- repo root off sys.path"

    hr = np.arange(HOURS)
    mon, hod = month_of_hour(hr), hr % 24
    wins = {
        "W1_jun_jul_h8_20": np.isin(mon, W1_MONTHS)
        & (hod >= W1_HOD[0])
        & (hod < W1_HOD[1]),
        "JJA_h12_17": np.isin(mon, SUMMER_JJA) & np.isin(hod, AFT_HOD),
    }

    out: dict = {
        "prereg": "results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md",
        "gate": "G-B / G-C2 -- model supply curve vs measured supply curve",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "note": "x-axes sit on different instruments (EIA-930 hourly BA vs model "
        "grid-delivered); slopes in $/MWh per GW are offset-invariant and a "
        "self-centred x is reported. No intercept is quoted.",
        "years": {},
    }

    for year in YEARS:
        piv = classes(year)
        _, p_mdl, _, _ = model_hourly(year)
        rt, _ = actual_hourly(year)
        f = _eia_hourly_frame_filled("MISO", year)
        assert f is not None and len(f) == HOURS
        f = f.reset_index(drop=True)

        q_mdl = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)
        # Measured thermal = the dispatchable fuels EIA-930 reports.
        q_act = (
            f["NG: COL"].to_numpy(float)
            + f["NG: NG"].to_numpy(float)
            + f["NG: OTH"].to_numpy(float)
        )

        yr: dict = {}
        for wname, sel in wins.items():
            okm = sel & np.isfinite(p_mdl) & np.isfinite(q_mdl)
            oka = sel & np.isfinite(rt) & np.isfinite(q_act)
            cm = curve(q_mdl[okm], p_mdl[okm])
            ca = curve(q_act[oka], rt[oka])
            sm = robust_slope(q_mdl[okm], p_mdl[okm])
            sa = robust_slope(q_act[oka], rt[oka])
            ratio = (
                round(sa["slope_usd_per_gw"] / sm["slope_usd_per_gw"], 2)
                if sm.get("slope_usd_per_gw")
                else None
            )
            yr[wname] = {
                "n_model_hours": int(okm.sum()),
                "n_actual_hours": int(oka.sum()),
                "model": {
                    "curve": cm,
                    "slope": sm,
                    "price_min_median_max": [
                        round(float(np.min(p_mdl[okm])), 2),
                        round(float(np.median(p_mdl[okm])), 2),
                        round(float(np.max(p_mdl[okm])), 2),
                    ],
                    "price_p90_p99": [
                        round(float(np.quantile(p_mdl[okm], 0.90)), 2),
                        round(float(np.quantile(p_mdl[okm], 0.99)), 2),
                    ],
                },
                "actual": {
                    "curve": ca,
                    "slope": sa,
                    "price_min_median_max": [
                        round(float(np.min(rt[oka])), 2),
                        round(float(np.median(rt[oka])), 2),
                        round(float(np.max(rt[oka])), 2),
                    ],
                    "price_p90_p99": [
                        round(float(np.quantile(rt[oka], 0.90)), 2),
                        round(float(np.quantile(rt[oka], 0.99)), 2),
                    ],
                },
                "slope_ratio_actual_over_model": ratio,
            }
        out["years"][str(year)] = yr

    OUT.write_text(json.dumps(out, indent=1))

    print("=" * 78)
    print("miso-142 -- MODEL supply curve vs MEASURED supply curve (MISO summer)")
    print("=" * 78)
    for year in YEARS:
        for wname in ("W1_jun_jul_h8_20", "JJA_h12_17"):
            w = out["years"][str(year)][wname]
            m, a = w["model"], w["actual"]
            print(f"\n{year} {wname}")
            print(
                f"   SLOPE  model {m['slope']['slope_usd_per_gw']:+.3f} "
                f"(se {m['slope']['se']:.3f}, R2 {m['slope']['r2']:.3f})   "
                f"actual {a['slope']['slope_usd_per_gw']:+.3f} "
                f"(se {a['slope']['se']:.3f}, R2 {a['slope']['r2']:.3f})   "
                f"-> actual is {w['slope_ratio_actual_over_model']}x steeper"
            )
            print(
                f"   price   model min/med/max {m['price_min_median_max']}  "
                f"p90/p99 {m['price_p90_p99']}"
            )
            print(
                f"           actual min/med/max {a['price_min_median_max']}  "
                f"p90/p99 {a['price_p90_p99']}"
            )
            print("   curve (centred GW -> median price):")
            print(
                "     model  "
                + "  ".join(
                    f"{b['thermal_gw_centred']:+.1f}:{b['price_median']:.0f}"
                    for b in m["curve"]["bins"]
                )
            )
            print(
                "     actual "
                + "  ".join(
                    f"{b['thermal_gw_centred']:+.1f}:{b['price_median']:.0f}"
                    for b in a["curve"]["bins"]
                )
            )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
