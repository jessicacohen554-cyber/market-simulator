"""closeout-SOCO-3 phase 1 (R-49 step 2), zero LP: the take-or-pay pile on SOCO with full yard history, scored.

Bars and construction are fixed in docs/records/soco/closeout-soco-3/PRECOMMIT-phase1-closeout-soco-3-2026-10-03.md.
Reach per plant-year comes from _closeout_soco3_pile_reach.reach_table("prior") (the field's construction: S_max over
every curated year <= Y-1, now 2015 onward). A fraction f of each year's net coal leaves (or refills) CC_REGULAR; the
rest is shared by CT_PEAKER and ST_GAS pro rata to their keeper model energy. C1 is re-scored with score_fuelmix.
Outputs: phase1_reach_plant_year.csv, phase1_c1.csv, phase1_bars.json.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts/probes"))
import calibration_verdict as cv  # noqa: E402
from _closeout_soco3_pile_reach import PRB, reach_table  # noqa: E402

OUT = REPO / "docs/records/soco/closeout-soco-3"
YEARS = range(2019, 2026)


def score(P: dict, d: pd.DataFrame, f: float | None) -> dict[tuple[int, str], dict]:
    """Return C1 rows keyed (year, class); ``f`` None scores the keeper unedited."""
    out = {}
    for y in YEARS:
        yb = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SOCO/{y}.json.gz")
        )["bench"]
        yp = json.loads(json.dumps(P["years"][str(y)]))
        if f is not None:
            dy = d[d.year == y]
            prb = dy[dy.plant.isin(PRB)].net_gwh.sum() / 1e3
            bit = dy[~dy.plant.isin(PRB)].net_gwh.sum() / 1e3
            net = prb + bit
            gm = yp["gmModel"]
            gm["COAL_PRB"] = gm.get("COAL_PRB", 0) + prb
            gm["COAL_BIT"] = gm.get("COAL_BIT", 0) + bit
            gm["CC_REGULAR"] = gm["CC_REGULAR"] - f * net
            rest = {k: gm.get(k, 0.0) for k in ("CT_PEAKER", "ST_GAS")}
            tot = sum(rest.values())
            for k, v in rest.items():
                gm[k] = v - (1 - f) * net * (v / tot if tot > 0 else 0.5)
        for row in cv.score_fuelmix(y, yp, yb, iso="SOCO"):
            out[(y, row["key"])] = row
    return out


def main() -> None:
    """Compute the phase-1 reach, score it at f = 1.0 / 0.5 and the f grid, and evaluate B1-B3."""
    d = reach_table("prior")
    d.to_csv(OUT / "phase1_reach_plant_year.csv", index=False)
    t = (
        REPO / "frontend/data/backcast/runs/2026-10-03-closeout-soco-2-nuclear.js"
    ).read_text()
    P = json.loads(
        gzip.decompress(
            base64.b64decode(re.search(r'="([A-Za-z0-9+/=]+)"', t).group(1))
        )
    )
    base = score(P, d, None)
    rows, flips = [], {}
    for f in (1.0, 0.5):
        s = score(P, d, f)
        flips[f] = [
            k
            for k, r in s.items()
            if base[k]["status"] == "PASS" and r["status"] == "FAIL"
        ]
        for k, r in s.items():
            rows.append(
                dict(
                    f=f,
                    year=k[0],
                    cls=k[1],
                    keeper=base[k]["status"],
                    keeper_pp=base[k].get("share_pp"),
                    status=r["status"],
                    share_pp=r.get("share_pp"),
                    model=r.get("model"),
                    actual=r.get("actual"),
                )
            )
    pd.DataFrame(rows).to_csv(OUT / "phase1_c1.csv", index=False)
    grid = {}
    for f in np.round(np.arange(0.0, 1.0001, 0.05), 2):
        grid[float(f)] = score(P, d, float(f))[(2019, "CC_REGULAR")]["status"]
    fmin = min((f for f, s in grid.items() if s == "PASS"), default=None)
    b1 = grid[0.5] == "PASS"
    worst = d.floor_over_actual_gwh.fillna(0).max() / 1e3
    b2 = worst <= 0.5
    b3 = not flips[1.0] and not flips[0.5]
    bars = dict(
        B1=b1,
        B1_min_f=fmin,
        B1_grid=grid,
        B2=b2,
        B2_worst_twh=round(worst, 3),
        B2_worst_row=d.loc[
            d.floor_over_actual_gwh.fillna(0).idxmax(), ["plant", "year"]
        ].tolist(),
        B3=b3,
        B3_flips={str(k): [list(x) for x in v] for k, v in flips.items()},
        coal_bit_2019={
            str(f): next(
                r["status"] + f" {r['share_pp']}"
                for r in rows
                if r["f"] == f and r["year"] == 2019 and r["cls"] == "COAL_BIT"
            )
            for f in (1.0, 0.5)
        },
    )
    (OUT / "phase1_bars.json").write_text(json.dumps(bars, indent=1, default=str))
    pd.set_option("display.width", 250)
    print(d.round(2).to_string(index=False))
    print(
        d.groupby("year")[["add_gwh", "cut_gwh", "net_gwh", "floor_over_actual_gwh"]]
        .sum()
        .round(0)
        .to_string()
    )
    c = pd.DataFrame(rows)
    c = c[c.cls.isin(["CC_REGULAR", "COAL_BIT", "COAL_PRB", "CT_PEAKER", "ST_GAS"])]
    c["v"] = c.share_pp.round(2).astype(str) + " " + c.status.str[0]
    print(
        c.pivot_table(index=["year", "cls"], columns="f", values="v", aggfunc="first")
        .join(c[c.f == 1.0].set_index(["year", "cls"])[["keeper_pp", "keeper"]])
        .to_string()
    )
    print(json.dumps(bars, indent=1, default=str))


if __name__ == "__main__":
    main()
