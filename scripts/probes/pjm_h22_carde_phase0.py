"""pjm-h22 Card E phase 0 — per-zone predicted move of RGGI across six years. ZERO LP.

Reads, all from committed artifacts:

1. KEEPER: per-zone, per-class model minus actual TWh for all six years, from the
   keeper payloads (``runs/2026-09-23-pjm-h19-dbs-{span,touchpoint}.js``) against the
   bench (EIA-923 net level, ``frontend/data/backcast/bench/PJM``).
2. RESPONSE: pjm-146's registered pair (``runs/2026-08-02-pjm-146{a,b}-*.js``, read
   from git ``25dd3b3d676764e926b93693bc5f1e26b5bc19bf``) gives the per-zone,
   per-class energy move RGGI caused in 2023-2025. That is the only solved
   measurement of this lever in PJM.
3. SCALING to 2020-2022 (a stated linear approximation, not a fit): the response
   is scaled by the allowance-price ratio against the reference year with the SAME
   membership pattern — 2021/2022 (VA a member) against 2023; 2020 (VA not yet a
   member) against the mean of the 2024/2025 per-dollar response. 2023-2025 use the
   pjm-146 response directly. Every scaled number is a prediction band centre, not a
   point claim; the band is the spread of the per-dollar response across its
   reference years.

Run: ``python scripts/probes/pjm_h22_carde_phase0.py <dir holding the two pjm-146 .js>``
Writes ``results/calibration/_pjm_h22_carde_phase0.json``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts/probes"))
import pjm_h21_cardd_phase0 as P  # noqa: E402

from market_sim.config.fuel_trajectories import (  # noqa: E402
    PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE as PRICE,
)

BENCH = REPO / "frontend/data/backcast/bench/PJM"
GROUPS = ("CC_REGULAR", "COAL_BIT", "COAL_WC", "CT_PEAKER", "ST_GAS")
FOCUS = ("EMAAC", "SWMAAC", "Dominion")
# Reference years with the same RGGI membership pattern (VA in / VA out).
REF = {2020: (2024, 2025), 2021: (2023,), 2022: (2023,)}


def _table(y: int, runs: dict[str, dict]) -> pd.DataFrame:
    """Per (zone, group) actual and each run's model TWh over bench plants."""
    b = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    rows = []
    for k, v in b.items():
        if v.get("group") not in GROUPS or v.get("nodata"):
            continue
        r = dict(
            zone=v["zone"].replace("PJM_", ""),
            group=v["group"],
            act=float(v.get("e_ann") or v.get("c_ann") or 0.0),
        )
        for tag, plants in runs.items():
            rec = plants.get(k)
            r[tag] = float(rec.get("m_ann") or 0.0) if isinstance(rec, dict) else 0.0
        rows.append(r)
    return pd.DataFrame(rows).groupby(["group", "zone"]).sum()


def main(p146: Path) -> None:
    """Build the keeper table, the pjm-146 response, and the scaled prediction."""
    keep = {}
    for p in P.RUNS.values():
        for y, rec in P._payload(p)["years"].items():
            keep[int(y)] = rec["plants"]
    ctl = P._payload(p146 / "2026-08-02-pjm-146a-control-zerodelta.js")["years"]
    arm = P._payload(p146 / "2026-08-02-pjm-146b-rggi-allowance.js")["years"]

    resp: dict[int, pd.Series] = {}
    for y in (2023, 2024, 2025):
        t = _table(y, {"c": ctl[str(y)]["plants"], "a": arm[str(y)]["plants"]})
        resp[y] = t["a"] - t["c"]
    per_dollar = {y: resp[y] / PRICE[y] for y in resp}

    out: dict = {"what": __doc__.splitlines()[0], "price": PRICE, "years": {}}
    for y in P.YEARS:
        t = _table(y, {"keeper": keep[y]})
        err = t["keeper"] - t["act"]
        if y in resp:
            d = resp[y]
            lo = hi = d
        else:
            refs = [per_dollar[r] * PRICE[y] for r in REF[y]]
            if y == 2020:
                # VA-out pattern; band = the two reference years.
                d = sum(refs) / len(refs)
                lo = pd.concat(refs, axis=1).min(axis=1)
                hi = pd.concat(refs, axis=1).max(axis=1)
            else:
                d = refs[0]
                # VA-in pattern has one reference year; band = +-30 % of centre,
                # the spread of the 2023-25 per-dollar EMAAC CC response
                # (reported below), declared rather than fitted.
                lo, hi = d * 0.7, d * 1.3
        yr: dict = {}
        for g in GROUPS:
            if g not in err.index.get_level_values(0):
                continue
            rows = {}
            for z in err.loc[g].index:
                key = (g, z)
                rows[z] = dict(
                    keeper_err=round(float(err.get(key, 0.0)), 2),
                    delta=round(float(d.get(key, 0.0)), 2),
                    delta_lo=round(float(min(lo.get(key, 0.0), hi.get(key, 0.0))), 2),
                    delta_hi=round(float(max(lo.get(key, 0.0), hi.get(key, 0.0))), 2),
                    pred_err=round(float(err.get(key, 0.0) + d.get(key, 0.0)), 2),
                )
            tot_e = float(err.loc[g].sum())
            tot_d = float(sum(d.get((g, z), 0.0) for z in err.loc[g].index))
            rows["_class"] = dict(
                keeper_err=round(tot_e, 2),
                delta=round(tot_d, 2),
                pred_err=round(tot_e + tot_d, 2),
                actual=round(float(t.loc[g, "act"].sum()), 2),
            )
            yr[g] = rows
        out["years"][str(y)] = yr
    out["emaac_cc_per_dollar"] = {
        str(y): round(float(per_dollar[y].get(("CC_REGULAR", "EMAAC"), 0.0)), 3)
        for y in per_dollar
    }
    dst = REPO / "results/calibration/_pjm_h22_carde_phase0.json"
    dst.write_text(json.dumps(out, indent=1))
    for y in P.YEARS:
        cc = out["years"][str(y)]["CC_REGULAR"]
        print(
            y,
            {
                z: (cc[z]["keeper_err"], cc[z]["delta"], cc[z]["pred_err"])
                for z in FOCUS
            },
            "class",
            cc["_class"],
        )
    print("per-$ EMAAC CC", out["emaac_cc_per_dollar"])
    print("wrote", dst)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
