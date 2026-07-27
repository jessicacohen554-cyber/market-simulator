"""pjm-130 gate 1 — is C1-2023 CC_REGULAR's volume FAIL its own miss, or displacement?

**No LP, no solve.** Reads only committed artifacts: the two arms' ``hourly/
class_hourly_<year>.parquet`` sidecars and the committed
``frontend/data/backcast/bench/PJM/<year>.json.gz``.

Charter question (pjm-129 §7 item 3, the cheapest of the three re-tune gates):
A1 (`2026-07-26-pjm-129-meritguard-a1`) fails C1-2023 CC_REGULAR at **-8.10 TWh**
against the ``min(2 % load, 8 TWh)`` = **8.00 TWh** volume band -- a 0.10 TWh /
1.2 %-of-band breach on a class the guard barely moved (-0.23 TWh); the keeper
(`2026-07-25-pjm-121-cc-belt`) sat at -7.87 TWh, already 98 % of band. So the
question is NOT "why is CC_REGULAR 8 TWh low" (that is the standing structure,
present in the keeper) but "who took the marginal 0.23 TWh, and is that
re-assignment structurally correct or misallocated?"

PRE-REGISTERED, committed before the probe was run.

Measurements
------------
M1  C1 class table, both arms, all three years: model (from the sidecar's own P1
    class energy) vs bench ``classFull`` actual, with the volume band and share
    test applied. Establishes which rows breach and by how much.
M2  Guard-attributable annual class deltas (A1 - keeper) from the sidecars.
    Sanity: they should ~sum to zero (demand is identical between arms).
M3  Hourly displacement test. Define the guard's *returned supply* as the
    classes the guard put back (ST_GAS + COAL_BIT + CC_CHP -- the >99 % of the
    removed layup GW-days per pjm-129 §3). Over the 8760 hours of 2023:
      (a) the share of CC_REGULAR's annual MWh *loss* that falls in hours where
          d(returned) > 0;
      (b) Pearson r(d CC_REGULAR, d returned) across all hours;
      (c) the same pair against each returned class individually.
M4  Misallocation test. For each returned class, does A1's model volume now
    *overshoot* its metered actual, while CC_REGULAR undershoots? An overshoot
    on the returned side co-occurring with an undershoot on CC_REGULAR is a
    structural target (the returned capacity is dispatching past what the meter
    saw). No overshoot means the re-assignment landed inside both classes'
    measured envelopes.

Pre-registered decision rule
----------------------------
On M3, for 2023:
  DISPLACEMENT-CONFIRMED  iff >= 60 % of CC_REGULAR's annual loss falls in hours
                          with d(returned) > 0 AND r(dCC_REGULAR, dreturned) <= -0.30.
  OWN-MISS                iff < 40 % of the loss falls in those hours AND
                          r >= -0.10.
  AMBIGUOUS               otherwise. Reported as such; no mechanism is built on
                          an ambiguous read.

On M4 -- and this is the kill criterion for the whole route:
  A structural lever exists ONLY IF at least one returned class's A1 model
  volume exceeds its metered actual while CC_REGULAR is below its own. If NO
  returned class overshoots its actual, then the guard moved energy between two
  classes that both remain inside their measured envelopes, gate 1 has **no
  admissible structural lever from this route**, and the correct outcome is to
  say so and ledger it -- NOT to build a mechanism that pushes 0.10 TWh back
  (that would be residual-fitting, rule 26 [R-DELETE] / rule 1 [R-STRUCT]).

Usage
-----
    PYTHONPATH=. .venv/bin/python scripts/probes/pjm130_c1_ccregular_displacement.py \
        --keeper results/calibration/pjm121_ccbelt \
        --arm results/calibration/pjm129_meritguard_a1 \
        --json-out results/calibration/pjm130_c1_displacement.json
"""

from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]

# C1 bands -- mirrored from scripts/calibration_verdict.py (FUELMIX_VOL_CAP_TWH,
# FUELMIX_VOL_LOAD_FRAC, FUELMIX_SHARE_PP). Cited, not re-derived.
VOL_CAP_TWH = 8.0
VOL_LOAD_FRAC = 0.020
SHARE_PP = 3.0

# The classes the pjm-129 guard returned to the envelope (§3 class mix of the
# removed layup windows: ST_GAS 54.7 %, COAL 21.3 %, CC_REGULAR 18.2 %,
# CC_CHP 4.1 %, CT_CHP 1.7 %). "Returned supply" for the displacement test is
# the returned set MINUS CC_REGULAR itself (which is the class under test).
RETURNED = ("ST_GAS", "COAL_BIT", "COAL_PRB", "COAL_WC", "CC_CHP", "CT_CHP")
UNDER_TEST = "CC_REGULAR"


def load_class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hourly MW pivot (hour x class) from a bundle's committed sidecar."""
    p = bundle / "hourly" / f"class_hourly_{year}.parquet"
    df = pd.read_parquet(p)
    df = df[df["pass"] == "P1"]
    piv = df.pivot_table(
        index="hour", columns="klass", values="mw", aggfunc="sum", observed=True
    )
    return piv.fillna(0.0)


def load_bench(year: int) -> dict:
    """Committed benchmark ``classFull`` (TWh, grid-delivered) for PJM."""
    p = REPO / f"frontend/data/backcast/bench/PJM/{year}.json.gz"
    with gzip.open(p) as fh:
        return json.load(fh)["bench"]


def c1_table(piv: pd.DataFrame, bench: dict, load_twh: float) -> list[dict]:
    """C1 rows: model TWh (from the sidecar), actual TWh, band verdicts."""
    actual = bench.get("classFull") or {}
    model = {k: float(piv[k].sum()) / 1e6 for k in piv.columns}  # MWh -> TWh
    m_gen = sum(model.get(k, 0.0) for k in actual)
    a_gen = sum(float(v) for v in actual.values())
    band = min(VOL_LOAD_FRAC * load_twh, VOL_CAP_TWH)
    rows = []
    for k in sorted(actual):
        m = model.get(k, 0.0)
        a = float(actual[k])
        d = m - a
        share_pp = (100.0 * m / m_gen - 100.0 * a / a_gen) if m_gen and a_gen else None
        rows.append(
            {
                "class": k,
                "model_twh": round(m, 4),
                "actual_twh": round(a, 4),
                "delta_twh": round(d, 4),
                "band_twh": round(band, 4),
                "band_util": round(abs(d) / band, 4) if band else None,
                "share_pp": round(share_pp, 3) if share_pp is not None else None,
                "vol_ok": bool(abs(d) <= band),
                "share_ok": bool(share_pp is None or abs(share_pp) <= SHARE_PP),
            }
        )
    return rows


def displacement(keeper: pd.DataFrame, arm: pd.DataFrame) -> dict:
    """M3 -- hourly displacement of CC_REGULAR against the returned supply."""
    classes = sorted(set(keeper.columns) | set(arm.columns))
    k = keeper.reindex(columns=classes, fill_value=0.0)
    a = arm.reindex(columns=classes, fill_value=0.0)
    d = a - k  # MW per hour, A1 minus keeper

    ret_cols = [c for c in RETURNED if c in d.columns]
    d_ret = d[ret_cols].sum(axis=1).to_numpy()
    d_cc = d[UNDER_TEST].to_numpy() if UNDER_TEST in d.columns else np.zeros(len(d))

    loss = np.where(d_cc < 0.0, -d_cc, 0.0)  # MWh of CC_REGULAR lost, per hour
    total_loss = float(loss.sum())
    up = d_ret > 0.0
    share_in_up = float(loss[up].sum() / total_loss) if total_loss > 0 else None

    def _r(x: np.ndarray, y: np.ndarray) -> float | None:
        if x.std() == 0 or y.std() == 0:
            return None
        return float(np.corrcoef(x, y)[0, 1])

    per_class = {}
    for c in ret_cols:
        dc = d[c].to_numpy()
        upc = dc > 0.0
        per_class[c] = {
            "annual_delta_twh": round(float(dc.sum()) / 1e6, 4),
            "r_with_cc_regular": (
                round(v, 4) if (v := _r(d_cc, dc)) is not None else None
            ),
            "cc_loss_share_in_up_hours": (
                round(float(loss[upc].sum() / total_loss), 4) if total_loss > 0 else None
            ),
        }

    r_ret = _r(d_cc, d_ret)
    verdict = "AMBIGUOUS"
    if share_in_up is not None and r_ret is not None:
        if share_in_up >= 0.60 and r_ret <= -0.30:
            verdict = "DISPLACEMENT-CONFIRMED"
        elif share_in_up < 0.40 and r_ret >= -0.10:
            verdict = "OWN-MISS"
    return {
        "returned_classes": ret_cols,
        "cc_regular_annual_delta_twh": round(float(d_cc.sum()) / 1e6, 4),
        "cc_regular_gross_loss_twh": round(total_loss / 1e6, 4),
        "returned_annual_delta_twh": round(float(d_ret.sum()) / 1e6, 4),
        "cc_loss_share_in_returned_up_hours": (
            round(share_in_up, 4) if share_in_up is not None else None
        ),
        "r_dcc_dreturned": round(r_ret, 4) if r_ret is not None else None,
        "per_class": per_class,
        "verdict": verdict,
    }


def misallocation(rows_arm: list[dict]) -> dict:
    """M4 -- does any returned class overshoot its meter while CC_REGULAR is short?"""
    by = {r["class"]: r for r in rows_arm}
    cc = by.get(UNDER_TEST)
    cc_short = bool(cc and cc["delta_twh"] < 0.0)
    over = {
        c: {
            "delta_twh": by[c]["delta_twh"],
            "band_util": by[c]["band_util"],
            "vol_ok": by[c]["vol_ok"],
        }
        for c in RETURNED
        if c in by and by[c]["delta_twh"] > 0.0
    }
    return {
        "cc_regular_short": cc_short,
        "cc_regular_delta_twh": cc["delta_twh"] if cc else None,
        "returned_classes_overshooting_meter": over,
        "structural_lever_exists": bool(cc_short and over),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--keeper", default="results/calibration/pjm121_ccbelt")
    ap.add_argument("--arm", default="results/calibration/pjm129_meritguard_a1")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--json-out")
    args = ap.parse_args()

    keeper_dir = REPO / args.keeper
    arm_dir = REPO / args.arm
    out: dict = {
        "keeper_bundle": args.keeper,
        "arm_bundle": args.arm,
        "bands": {
            "vol_cap_twh": VOL_CAP_TWH,
            "vol_load_frac": VOL_LOAD_FRAC,
            "share_pp": SHARE_PP,
        },
        "years": {},
    }

    for year in args.years:
        kp = load_class_hourly(keeper_dir, year)
        ap_ = load_class_hourly(arm_dir, year)
        bench = load_bench(year)
        # ISO load for the band: the bundles' own system sidecar demand.
        sysp = pd.read_parquet(arm_dir / "hourly" / f"system_{year}.parquet")
        load_twh = float(sysp["demand"].sum()) / 1e6
        rows_k = c1_table(kp, bench, load_twh)
        rows_a = c1_table(ap_, bench, load_twh)
        disp = displacement(kp, ap_)
        mis = misallocation(rows_a)
        out["years"][str(year)] = {
            "load_twh": round(load_twh, 3),
            "c1_keeper": rows_k,
            "c1_arm": rows_a,
            "displacement": disp,
            "misallocation": mis,
        }

        print(f"\n===== {year}  (ISO load {load_twh:,.1f} TWh, "
              f"band {min(VOL_LOAD_FRAC*load_twh, VOL_CAP_TWH):.2f} TWh) =====")
        print(f"{'class':<14}{'actual':>10}{'keeper':>10}{'arm':>10}"
              f"{'d_keep':>9}{'d_arm':>9}{'util':>7}  vol")
        bk = {r["class"]: r for r in rows_k}
        for r in rows_a:
            c = r["class"]
            print(
                f"{c:<14}{r['actual_twh']:>10.2f}{bk[c]['model_twh']:>10.2f}"
                f"{r['model_twh']:>10.2f}{bk[c]['delta_twh']:>9.2f}"
                f"{r['delta_twh']:>9.2f}{(r['band_util'] or 0):>7.2f}"
                f"  {'ok' if r['vol_ok'] else 'FAIL'}"
            )
        print(f"\nM3 displacement: {disp['verdict']}")
        print(f"  d CC_REGULAR = {disp['cc_regular_annual_delta_twh']:+.3f} TWh "
              f"(gross loss {disp['cc_regular_gross_loss_twh']:.3f} TWh)")
        print(f"  d returned   = {disp['returned_annual_delta_twh']:+.3f} TWh")
        print(f"  loss share in returned-up hours = "
              f"{disp['cc_loss_share_in_returned_up_hours']}")
        print(f"  r(dCC, dreturned) = {disp['r_dcc_dreturned']}")
        for c, v in disp["per_class"].items():
            print(f"    {c:<12} d={v['annual_delta_twh']:+7.3f} TWh  "
                  f"r={v['r_with_cc_regular']}  lossshare={v['cc_loss_share_in_up_hours']}")
        print(f"\nM4 misallocation: structural_lever_exists="
              f"{mis['structural_lever_exists']}")
        for c, v in mis["returned_classes_overshooting_meter"].items():
            print(f"    {c:<12} OVERSHOOTS meter by {v['delta_twh']:+.3f} TWh "
                  f"(band util {v['band_util']:.2f}, vol_ok={v['vol_ok']})")

    if args.json_out:
        p = REPO / args.json_out
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=1))
        print(f"\nwrote {p}")


if __name__ == "__main__":
    main()
