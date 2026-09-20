#!/usr/bin/env python3
"""caiso-288 — score every candidate construction for the EIA publication
blackout against the prints EIA ACTUALLY PUBLISHED. ZERO LP.

Two caiso-288 lanes independently found the same defect: EIA issues no Natural
Gas Weekly Update over Thanksgiving and the Christmas/New Year weeks, so the
committed CA-composite citygate daily series carries a multi-day hole in Nov and
Dec of every year, and ``_flow_date_staircase`` constant-extends the last print
across it — in Dec-2022 that print is $53.59/MMBtu, the year's maximum, held for
ten flow days while the western gas crisis collapsed.

The lanes diverge on the REMEDY, and this probe adjudicates it on evidence:

* the sibling lane (`caiso_citygate_blackout_bridge`, branch
  `claude/caiso-288-c3a-tuning-2jo6s1`) ESTIMATES the interior from the measured
  Henry Hub daily spot plus the basis at the two bracketing citygate prints;
* this lane RECOVERS the interior, because the prints were published all along —
  on the catch-up page's extra live tables, which `fetch_caiso_citygate_daily`'s
  ``re.search`` discarded (see that file's ``parse_spot_table`` docstring).

The comparison is only possible BECAUSE the prints were recovered: before that,
the blackout interior was unobserved and the bridge could not be scored at all.
That is the point — a measurement adjudicates an estimator (rule 14
`[R-ACCURATE]`), and this probe is the adjudication, not an argument.

Usage:
    python scripts/probes/caiso288_blackout_estimator_scoreboard.py \
        --prerepair /tmp/citygate_prerepair.csv
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

CITYGATE = REPO / "data/raw/gas-prices/caiso_citygate_daily.csv"
HH_DAILY = REPO / "data/raw/gas-prices/henry_hub_daily.csv"
OUT = REPO / "results/calibration/_caiso288_blackout_scoreboard.json"

#: CAISO CC_REGULAR cap-weighted base heat rate, MMBtu/MWh — converts a
#: $/MMBtu fuel error into the $/MWh marginal-cost error it causes. Nothing is
#: fitted with it (see caiso288_phase0.CC_HR).
CC_HR = 7.44


def score_blackout(pre: pd.DataFrame, truth: pd.DataFrame, hh: pd.Series,
                   lo: pd.Timestamp, hi: pd.Timestamp) -> pd.DataFrame:
    """One blackout: staircase vs HH-basis bridge vs the published print.

    ``lo``/``hi`` are the bracketing days that the PRE-REPAIR series carries a
    print for — i.e. the blackout as the unrepaired model sees it.
    """
    ca = pre["ca_composite_usd_mmbtu"]
    hh_pre = pre["henry_hub_usd_mmbtu"]
    b_lo, b_hi = ca[lo] - hh_pre[lo], ca[hi] - hh_pre[hi]
    span = (hi - lo).days
    filled = hh.reindex(pd.date_range(lo, hi)).interpolate()
    rows = []
    for day in pd.date_range(lo + pd.Timedelta(days=1), hi - pd.Timedelta(days=1)):
        if day not in truth.index:
            continue  # EIA published no print that day either (holiday/weekend)
        w = (day - lo).days / span
        rows.append(
            {
                "day": day.date().isoformat(),
                "published": float(truth.loc[day, "ca_composite_usd_mmbtu"]),
                "bridge": float(b_lo + (b_hi - b_lo) * w + filled.loc[day]),
                "staircase": float(ca[lo]),
            }
        )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["bridge_err"] = out.bridge - out.published
    out["staircase_err"] = out.staircase - out.published
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--prerepair", required=True)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    pre = pd.read_csv(args.prerepair, parse_dates=["date"]).set_index("date")
    truth = pd.read_csv(CITYGATE, parse_dates=["date"]).set_index("date")
    hh = pd.read_csv(HH_DAILY, parse_dates=["date"]).set_index("date").iloc[:, 0]

    # Every blackout the PRE-REPAIR series carries that the repair now fills.
    recovered = truth.index.difference(pre.index)
    doc: dict = {"run": "caiso-288 blackout estimator scoreboard",
                 "cc_heat_rate_mmbtu_per_mwh": CC_HR, "blackouts": []}
    frames = []
    for lo in sorted(pre.index):
        nxt = pre.index[pre.index > lo]
        if not len(nxt):
            break
        hi = nxt[0]
        if (hi - lo).days < 6:          # a 1-4 day trading package, not a blackout
            continue
        if not len(recovered[(recovered > lo) & (recovered < hi)]):
            continue                     # nothing was recovered inside it
        t = score_blackout(pre, truth, hh, lo, hi)
        if t.empty:
            continue
        frames.append(t)
        doc["blackouts"].append({
            "from": lo.date().isoformat(), "to": hi.date().isoformat(),
            "days_scored": len(t),
            "bracket_ca": [float(pre.loc[lo, "ca_composite_usd_mmbtu"]),
                           float(pre.loc[hi, "ca_composite_usd_mmbtu"])],
            "staircase_mae": round(float(t.staircase_err.abs().mean()), 4),
            "staircase_bias": round(float(t.staircase_err.mean()), 4),
            "bridge_mae": round(float(t.bridge_err.abs().mean()), 4),
            "bridge_bias": round(float(t.bridge_err.mean()), 4),
            "rows": t.round(4).to_dict("records"),
        })
    allt = pd.concat(frames) if frames else pd.DataFrame()
    if not allt.empty:
        doc["overall"] = {
            "days_scored": int(len(allt)),
            "staircase_mae": round(float(allt.staircase_err.abs().mean()), 4),
            "staircase_bias": round(float(allt.staircase_err.mean()), 4),
            "bridge_mae": round(float(allt.bridge_err.abs().mean()), 4),
            "bridge_bias": round(float(allt.bridge_err.mean()), 4),
            "recovered_mae": 0.0,
            "recovered_bias": 0.0,
            "staircase_mc_bias_usd_mwh": round(
                float(allt.staircase_err.mean()) * CC_HR, 2),
            "bridge_mc_bias_usd_mwh": round(float(allt.bridge_err.mean()) * CC_HR, 2),
        }
    args.out.write_text(json.dumps(doc, indent=1) + "\n")
    print(json.dumps(doc.get("overall", {}), indent=1))
    for b in doc["blackouts"]:
        print(f"  {b['from']} -> {b['to']}  n={b['days_scored']:2d}  "
              f"staircase MAE {b['staircase_mae']:7.2f} / bridge MAE {b['bridge_mae']:7.2f}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
