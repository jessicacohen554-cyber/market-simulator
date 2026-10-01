"""SPP-102 phase 0 (zero LP), part 3: the PERFECT-COMMITMENT-PHYSICS bound.

What is the most a commitment-state engine could add to SPP CC in low-price hours, using only
admissible unit physics? Per SPP CC_REGULAR plant, a binary price-taker unit-commitment schedule is
solved by dynamic programming against the KEEPER'S OWN P1 zonal price (no LP, no market re-clear):

  max  sum_t u_t * [ (p_t - mc_t) * q_t ]  -  S * Pnp * starts
  s.t. q_t = avail_t if p_t >= mc_t else pmin_t      (on)
       min-up U hours, min-down D hours, pmin_t = 0.209 * avail_t (SPP-44)

mc_t / avail_t come from the keeper's rebuilt offer stack (`_spp102_stack_dump.py`, zero LP).
Two admissible physics sets, both fixed before this probe was run:
  * ASOM:  U = 21 h, D = 8 h (SPP MMU ASOM 2024 gas, FINDING-spp-83 §2), S = 50 $/MW (keeper CC
           committed-tranche start cost, SPP-73 M4)
  * NREL:  the CC_COMMITMENT_PARAMS row for the plant's offer heat rate (constants.py, NREL 55433)
Because the price is held at the keeper's (commitment at pmin would only depress it further), the
DP's added low-price on-hours are an UPPER BOUND on what an engine with these parameters could add.

Scored inside actual-RT <= $15 hours against CEMS online (CF >= 5 %):
  added_twh      DP on & keeper off, at the DP's output (pmin in-the-money-negative hours)
  removed_twh    keeper on & DP off (short keeper blips a start cost no longer pays for)
  precision      share of DP-added low-price plant-hours in which CEMS was online
  recall         share of the CEMS-on / keeper-off low-price gap the DP recovers
and over ALL hours: net delta CC TWh (the C1 CC_REGULAR reach).
Writes docs/records/spp/spp102/commit_dp.json. Usage:
  uv run python scripts/probes/_spp102_commit_dp.py <decoded payload.json> <stack dir>
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from market_sim.config.constants import CC_COMMITMENT_PARAMS  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from scripts.probes._spp102_cc_commitment_drivers import (
    LOW,
    MIN_LOAD,
    ON_CEMS,
    ON_MODEL,
    YEARS,
    dec,
)  # noqa: E402

ASOM = {"U": 21, "D": 8, "S": 50.0}


def nrel(hr: float) -> dict:
    """CC_COMMITMENT_PARAMS row for an offer heat rate."""
    for cut, d in CC_COMMITMENT_PARAMS:
        if hr <= cut:
            return {
                "U": int(d["min_run_hours"]),
                "D": int(d["min_down_hours"]),
                "S": float(d["startup_per_mw"]),
            }
    raise ValueError(hr)


def dp_schedule(margin_on: np.ndarray, start_cost: float, U: int, D: int) -> np.ndarray:
    """Binary price-taker UC by DP. margin_on[t] = profit if online in t. Returns u[t] in {0,1}.

    States: on_k (k = 1..U, U = "at least U") and off_k (k = 1..D, D = "at least D").
    """
    T = len(margin_on)
    NEG = -1e18
    ns = U + D
    V = np.full(ns, NEG)
    V[U + D - 1] = 0.0  # start offline, free to start
    back = np.zeros((T, ns), np.int16)
    for t in range(T):
        nv = np.full(ns, NEG)
        nb = np.zeros(ns, np.int16)
        m = margin_on[t]
        # on_1 from off_D (start)
        nv[0] = V[U + D - 1] - start_cost + m
        nb[0] = U + D - 1
        # on_{k+1} from on_k
        nv[1:U] = V[0 : U - 1] + m
        nb[1:U] = np.arange(0, U - 1)
        # on_U from on_U (stay)
        if V[U - 1] + m > nv[U - 1]:
            nv[U - 1] = V[U - 1] + m
            nb[U - 1] = U - 1
        # off_1 from on_U (stop)
        nv[U] = V[U - 1]
        nb[U] = U - 1
        # off_{k+1} from off_k
        nv[U + 1 : U + D] = V[U : U + D - 1]
        nb[U + 1 : U + D] = np.arange(U, U + D - 1)
        if V[U + D - 1] > nv[U + D - 1]:
            nv[U + D - 1] = V[U + D - 1]
            nb[U + D - 1] = U + D - 1
        V = nv
        back[t] = nb
    s = int(np.argmax(V))
    u = np.zeros(T, bool)
    for t in range(T - 1, -1, -1):
        u[t] = s < U
        s = back[t, s]
    return u


def main() -> int:
    """Run the DP bound for every keeper year and both physics sets."""
    pay = json.load(open(sys.argv[1]))
    sd = Path(sys.argv[2])
    lmp = pd.read_parquet(
        RAW_DATA_DIR / "_validation-source/actual_lmp_hourly_SPP.parquet"
    )
    out = {}
    for y in YEARS:
        f = sd / f"stack_{y}.npz"
        if not f.exists():
            print("missing", f)
            continue
        z = np.load(f, allow_pickle=False)
        rt = (
            lmp[lmp.year == int(y)]
            .set_index("hour")
            .reindex(range(8760))["rt"]
            .to_numpy(float)
        )
        low = rt <= LOW
        sysf = pd.read_parquet(
            REPO / f"results/calibration/spp100_arm_span/hourly/system_{y}.parquet"
        )
        sysf = sysf[sysf["pass"] == "P1"]
        zp = {
            zn: g.set_index("hour")["price"].reindex(range(8760)).to_numpy(float)
            for zn, g in sysf.groupby("zone")
        }
        b = json.load(
            gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{y}.json.gz")
        )["bench"]["plants"]
        mp = pay["years"][y]["plants"]
        klass, codes = z["klass"].astype(str), z["codes"]
        res = {}
        for tag in ("ASOM", "NREL"):
            acc = dict(
                added_low_twh=0.0,
                removed_low_twh=0.0,
                added_low_h=0,
                added_low_cems_on_h=0,
                gap_low_h=0,
                gap_recovered_h=0,
                net_all_twh=0.0,
                net_low_twh=0.0,
                plants=0,
            )
            for k, v in b.items():
                if (
                    v["group"] != "CC_REGULAR"
                    or v.get("nodata") in (True, "True")
                    or not v.get("campd")
                ):
                    continue
                key = k if k in mp else f"{k}:CC_REGULAR"
                code = int(k.split(":")[0])
                rows = np.flatnonzero((codes == code) & (klass == "CC_REGULAR"))
                if key not in mp or not len(rows):
                    continue
                cap = z["cap"][rows].astype(float)  # (r, T)
                avail = cap.sum(0)
                mc = (z["mc"][rows].astype(float) * cap).sum(0) / np.maximum(
                    avail, 1e-9
                )
                mc = np.where(avail > 0, mc, 1e6)
                p = zp.get(v["zone"], next(iter(zp.values())))
                pmin = MIN_LOAD * avail
                q = np.where(p >= mc, avail, pmin)
                margin = np.where(avail > 0, (p - mc) * q, -1e9)
                npl = float(v["npl"])
                ph = ASOM if tag == "ASOM" else nrel(float(np.median(z["hr"][rows])))
                u = dp_schedule(margin, ph["S"] * npl, ph["U"], ph["D"])
                c, m = dec(v["campd"]), dec(mp[key]["m"])
                on_c, on_m = c >= ON_CEMS, m >= ON_MODEL
                keeper_mw = m / 100 * npl
                dp_mw = np.where(u, q, 0.0)
                add = u & ~on_m
                rem = on_m & ~u
                acc["plants"] += 1
                acc["added_low_twh"] += float(dp_mw[add & low].sum() / 1e6)
                acc["removed_low_twh"] += float(keeper_mw[rem & low].sum() / 1e6)
                acc["added_low_h"] += int((add & low).sum())
                acc["added_low_cems_on_h"] += int((add & low & on_c).sum())
                gap = on_c & ~on_m & low
                acc["gap_low_h"] += int(gap.sum())
                acc["gap_recovered_h"] += int((gap & u).sum())
                # net change if the keeper's schedule became the DP's, holding keeper output where both on
                delta = np.where(add, dp_mw, 0.0) - np.where(rem, keeper_mw, 0.0)
                acc["net_all_twh"] += float(delta.sum() / 1e6)
                acc["net_low_twh"] += float(delta[low].sum() / 1e6)
            acc["precision_added_low"] = (
                round(acc["added_low_cems_on_h"] / acc["added_low_h"], 3)
                if acc["added_low_h"]
                else None
            )
            acc["recall_gap_low"] = (
                round(acc["gap_recovered_h"] / acc["gap_low_h"], 3)
                if acc["gap_low_h"]
                else None
            )
            res[tag] = {
                k2: (round(v2, 3) if isinstance(v2, float) else v2)
                for k2, v2 in acc.items()
            }
        out[y] = res
        print(y, json.dumps(res))
    (REPO / "docs/records/spp/spp102/commit_dp.json").write_text(
        json.dumps(out, indent=1)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
