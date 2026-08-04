"""nyiso-122 PHASE 0 — no-LP decomposition of NYISO's 2025 C3a mean-LMP miss.

The keeper ``2026-08-04-nyiso-120-c119-scope`` reads a system load-weighted mean
LMP of 59.84 $/MWh against an actual RT of 66.53 in 2025 (**-10.1 %**, a C3a
FAIL), while 2023 (**+7.2 %**) and 2024 (**-0.9 %**) sit comfortably inside the
+/-10 % band. nyiso-120 measured that only ~6 % of that gap came from its own
input correction, so ~94 % is pre-existing and is this lane's target.

This probe answers ONE question before any lever is proposed (rule 19
``[R-ONE-MECH]``): **is the 2025 miss a LEVEL problem, a SCARCITY problem, or
the SHAPE/compression object nyiso-110 already diagnosed?**  It reads only
COMMITTED artifacts -- the keeper bundle's ``hourly/system_<year>.parquet``
sidecars (rule 15) and the committed hourly actual
``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet`` -- and runs no
LP, no derive and no solve.

Rule 22: TRAINING YEARS ONLY.  The committed actual parquet also carries 2018,
2019, 2020, 2021, 2022 and H1-2026, every one of which is out-of-training for
NYISO (validation ladder or locked test).  ``YEARS`` is a hard filter and the
loader asserts no other year is ever materialized.

Outputs ``results/calibration/_nyiso122_c3a_2025_decomp.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Training years only -- rule 22 [R-HOLDOUT].  NYISO holds a `complete` marker
# (validation ladder) but NOT `final`; the holdout spend freeze is ACTIVE.  No
# year outside this tuple may be read, and _actual() asserts it.
YEARS: tuple[int, ...] = (2023, 2024, 2025)
HOURS = 8760

REPO = Path(__file__).resolve().parents[2]
KEEPER_BUNDLE = REPO / "results/calibration/nyiso120_c119_scopegate"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
OUT = REPO / "results/calibration/_nyiso122_c3a_2025_decomp.json"

# Band edges on the ACTUAL RT price, $/MWh.  The split is chosen to separate the
# three candidate explanations rather than to flatter any of them: everything
# below the annual median is "trough", the 300 cap is the ISO's own C3c scarcity
# threshold (rubric section 5, NYISO/NEISO = $300), and the intermediate rungs
# resolve the peak half that nyiso-110 measured as compressed.
BAND_EDGES = (-np.inf, 0.0, 25.0, 50.0, 100.0, 200.0, 300.0, np.inf)
TAIL_THRESHOLD = 300.0  # rubric section 5 -- NYISO's own C3c threshold


def _model_hourly(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(price, demand)`` demand-weighted system hourly series for ``year``.

    Mirrors the payload's own ``lmpDeltaHr`` construction (``render_calibration_
    html._b64_i16``): the model system price in hour t is the zonal dual weighted
    by that zone-hour's demand, which is the same basis C3a scores on.
    """
    df = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
    if df["pass"].nunique() > 1:  # P1 is the scored pass (spec section 1.6)
        df = df[df["pass"] == df["pass"].max()]
    p = df.pivot_table(index="hour", columns="zone", values="price").reindex(
        range(HOURS)
    )
    d = df.pivot_table(index="hour", columns="zone", values="demand").reindex(
        range(HOURS)
    )
    w = d.to_numpy(float)
    price = np.nansum(p.to_numpy(float) * w, axis=1) / np.nansum(w, axis=1)
    return price, np.nansum(w, axis=1)


def _actual(year: int) -> np.ndarray:
    """Committed hourly actual RT LMP for ``year``, NaN-padded to 8760 hours."""
    if year not in YEARS:  # rule 22 -- fail closed, never widen the window
        raise SystemExit(f"REFUSED: {year} is out-of-training for NYISO (rule 22)")
    df = pd.read_parquet(ACTUAL_HOURLY)
    df = df[df["year"] == year]
    out = np.full(HOURS, np.nan)
    hr = df["hour"].to_numpy(int)
    keep = hr < HOURS
    out[hr[keep]] = df["rt"].to_numpy(float)[keep]
    return out


def _bands(actual: np.ndarray) -> list[tuple[str, np.ndarray]]:
    """Label/mask pairs binning hours by the ACTUAL price band."""
    out = []
    for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:]):
        lab = f"{'-inf' if lo == -np.inf else f'{lo:g}'}..{'inf' if hi == np.inf else f'{hi:g}'}"
        out.append((lab, (actual >= lo) & (actual < hi)))
    return out


def decompose(year: int) -> dict:
    """Decompose ``year``'s C3a mean-LMP gap by actual-price band."""
    model, dem = _model_hourly(year)
    act = _actual(year)
    ok = np.isfinite(model) & np.isfinite(act) & np.isfinite(dem) & (dem > 0)
    m, a, w = model[ok], act[ok], dem[ok]
    wn = w / w.sum()

    mean_m, mean_a = float(np.sum(wn * m)), float(np.sum(wn * a))
    rows = []
    for lab, mask in _bands(act):
        k = mask[ok]
        if not k.any():
            continue
        rows.append(
            {
                "band": lab,
                "hours": int(k.sum()),
                "load_share_pct": round(100 * float(wn[k].sum()), 3),
                "model_mean": round(float(np.average(m[k], weights=w[k])), 2),
                "actual_mean": round(float(np.average(a[k], weights=w[k])), 2),
                # contribution of this band to the ANNUAL load-weighted gap
                "gap_contrib": round(float(np.sum(wn[k] * (m[k] - a[k]))), 3),
            }
        )

    tail = act[ok] > TAIL_THRESHOLD
    # Counterfactual: what would C3a read if the model matched the actual EXACTLY
    # in every scarcity hour and changed nowhere else?  This is a diagnostic
    # bound, never an input (rule 13) -- it isolates how much of the miss the
    # scarcity tail can possibly explain.
    cf_tail = float(np.sum(wn * np.where(tail, a, m)))
    # ... and the mirror: matched exactly in every NON-tail hour.
    cf_base = float(np.sum(wn * np.where(~tail, a, m)))

    return {
        "year": year,
        "model_mean_lw": round(mean_m, 2),
        "actual_mean_lw": round(mean_a, 2),
        "gap": round(mean_m - mean_a, 3),
        "err_pct": round(100 * (mean_m - mean_a) / mean_a, 2),
        "bands": rows,
        "tail": {
            "threshold": TAIL_THRESHOLD,
            "actual_tail_hours": int(tail.sum()),
            "model_tail_hours": int((m > TAIL_THRESHOLD).sum()),
            "actual_tail_load_share_pct": round(100 * float(wn[tail].sum()), 3),
            "gap_in_tail_hours": round(float(np.sum(wn[tail] * (m[tail] - a[tail]))), 3),
            "gap_outside_tail_hours": round(
                float(np.sum(wn[~tail] * (m[~tail] - a[~tail]))), 3
            ),
            "cf_err_pct_if_tail_exact": round(100 * (cf_tail - mean_a) / mean_a, 2),
            "cf_err_pct_if_nontail_exact": round(100 * (cf_base - mean_a) / mean_a, 2),
        },
        "spread": {
            # nyiso-110's compression object, restated on this keeper: the ratio
            # of the model's trough->peak swing to the actual's.
            "model_p90_over_p10": round(
                float(np.percentile(m, 90) / np.percentile(m, 10)), 3
            ),
            "actual_p90_over_p10": round(
                float(np.percentile(a, 90) / np.percentile(a, 10)), 3
            ),
            "model_p10": round(float(np.percentile(m, 10)), 2),
            "actual_p10": round(float(np.percentile(a, 10)), 2),
            "model_p90": round(float(np.percentile(m, 90)), 2),
            "actual_p90": round(float(np.percentile(a, 90)), 2),
        },
    }


def main() -> None:
    res = {
        "probe": "nyiso-122 phase 0 -- C3a 2025 decomposition (no LP, no derive)",
        "keeper": "2026-08-04-nyiso-120-c119-scope",
        "bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "years": list(YEARS),
        "years_note": "rule 22 [R-HOLDOUT]: training years only; 2018-2022 and 2026 present in the committed actual parquet are NEVER read",
        "results": [decompose(y) for y in YEARS],
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    for r in res["results"]:
        print(
            f"=== {r['year']}  model {r['model_mean_lw']:.2f}  actual "
            f"{r['actual_mean_lw']:.2f}  gap {r['gap']:+.2f} ({r['err_pct']:+.2f}%)"
        )
        print(
            "  band            hours  load%   model   actual   gap-contrib $/MWh"
        )
        for b in r["bands"]:
            print(
                f"  {b['band']:>14} {b['hours']:6d} {b['load_share_pct']:6.2f} "
                f"{b['model_mean']:8.2f} {b['actual_mean']:8.2f} {b['gap_contrib']:+11.3f}"
            )
        t = r["tail"]
        print(
            f"  TAIL >${t['threshold']:.0f}: actual {t['actual_tail_hours']} h / model "
            f"{t['model_tail_hours']} h | gap in tail {t['gap_in_tail_hours']:+.3f}, "
            f"outside {t['gap_outside_tail_hours']:+.3f}"
        )
        print(
            f"  counterfactual C3a: tail-exact {t['cf_err_pct_if_tail_exact']:+.2f}% | "
            f"nontail-exact {t['cf_err_pct_if_nontail_exact']:+.2f}%"
        )
        s = r["spread"]
        print(
            f"  spread p90/p10: model {s['model_p90_over_p10']:.3f} "
            f"({s['model_p10']:.2f}->{s['model_p90']:.2f}) vs actual "
            f"{s['actual_p90_over_p10']:.3f} ({s['actual_p10']:.2f}->{s['actual_p90']:.2f})"
        )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
