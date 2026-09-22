"""xiso phase 0, reserve leg — is the "idle" thermal block actually HELD FOR RESERVE?

ZERO LP, and ZERO fleet rebuild: reads only the keeper's COMMITTED
``hourly/reserve_family_<year>.parquet`` and ``hourly/system_<year>.parquet``.

WHY THIS EXISTS. ``_xiso_stack_climb_phase0.py`` measures idle thermal as
``available - dispatched``, where "dispatched" is ENERGY dispatch from
``class_band_hourly``. Capacity a co-optimized LP holds for an ancillary product
is not producing energy, so it reads as "idle" there while being fully committed.
ERCOT 2021 is the case that forces the question: 29.4 % idle with 0.0 % of
capacity offered ABOVE the clearing price — i.e. a large in-the-money,
undispatched block, in Winter Storm Uri, with the price at cap.

THE FAMILIES ARE NESTED, NOT DISJOINT, and summing them double-counts badly.
Measured here: ERCOT's ``ercot_ordc_total`` (8,955 MW mean, 2021) is EXACTLY
``ECRS + NonSpin + RRS_withheld + RegUp_withheld`` (1,513 + 3,503 + 2,241 +
1,698); NEISO's ``ne_10min_spin`` equals ``ne_10min_total``; NYISO's
``nyca_10min_spin`` equals ``nyca_10min_total`` and both sit inside
``nyca_30min_total``; PJM's ``pjm_primary_mad`` sits inside ``pjm_primary``;
MISO's ``miso_rbdc_regspin`` sits inside ``miso_rbdc``.

SO TWO BOUNDS ARE REPORTED, AND THE HOSTILE ONE IS THE ONE THE VERDICT IS
TESTED AGAINST:

  * ``max_family``  — the largest single family's held MW. A LOWER bound on
    total reserve holding (the binding envelope of a cascading requirement).
  * ``sum_families`` — every family added. A gross UPPER bound that knowingly
    double-counts every nesting, AND attributes 100 % of reserve holding to
    THERMAL when storage, hydro and demand response also supply it.

``sum_families`` is the most hostile assumption available to this lane's own
hypothesis. If the signature survives subtracting it, it survives the reserve
explanation outright.

Four ISOs (CAISO, NWPP, SOCO, SPP) commit no ``reserve_family`` sidecar; they
are reported UNAVAILABLE rather than assumed zero.

Run: python3 scripts/probes/_xiso_reserve_leg.py --out <dir>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    rows = [json.loads(p.read_text()) for p in sorted(out.glob("*.json"))
            if not p.name.startswith("_")]

    res = {}
    print(f"{'ISO':6s} {'yr':>5s} {'idle GW':>8s} {'idle %':>7s} "
          f"{'maxfam GW':>10s} {'sumfam GW':>10s} {'idle-sumfam %':>14s}")
    for r in sorted(rows, key=lambda x: (x["iso"], x["year"])):
        iso, y, T = r["iso"], r["year"], r["hours"]
        p = REPO / r["bundle"] / f"hourly/reserve_family_{y}.parquet"
        t = r["thermal_top1pct"]
        if not p.exists():
            res[f"{iso}_{y}"] = {"reserve_sidecar": False}
            print(f"{iso:6s} {y:>5d} {t['idle_mw']/1000:8.1f} {t['idle_pct']:7.1f} "
                  f"{'n/a':>10s} {'n/a':>10s} {'(no sidecar)':>14s}")
            continue
        d = pd.read_parquet(p)
        d = d[d["pass"] == "P1"]
        piv = (d.pivot_table(index="hour", columns="family", values="held_mw",
                             aggfunc="sum", observed=True)
               .reindex(range(T)).fillna(0.0).sort_index())
        # Re-derive the SAME window this ISO-year used, from committed data.
        ap_ = REPO / f"data/raw/_validation-source/actual_lmp_hourly_{iso}.parquet"
        if ap_.exists():
            ad = pd.read_parquet(ap_)
            ad = ad[ad["year"] == y]
            rank = np.full(T, -np.inf)
            h = ad["hour"].to_numpy(int)
            m = (h >= 0) & (h < T)
            rank[h[m]] = np.nan_to_num(ad["rt"].to_numpy(float)[m], nan=-np.inf)
        else:
            sysf = pd.read_parquet(REPO / r["bundle"] / f"hourly/system_{y}.parquet")
            sysf = sysf[sysf["pass"] == "P1"]
            rank = sysf.groupby("hour")["demand"].sum().reindex(range(T)).to_numpy(float)
        hi = np.argsort(rank)[-r["window_hours"]:]

        mx = float(piv.to_numpy()[hi].max(axis=1).mean())
        sm = float(piv.to_numpy()[hi].sum(axis=1).mean())
        av = t["available_mw"]
        net = 100.0 * max(0.0, t["idle_mw"] - sm) / av if av else None
        res[f"{iso}_{y}"] = {"reserve_sidecar": True, "max_family_mw": mx,
                             "sum_families_mw": sm, "idle_net_sum_pct": net,
                             "families": [str(c) for c in piv.columns]}
        print(f"{iso:6s} {y:>5d} {t['idle_mw']/1000:8.1f} {t['idle_pct']:7.1f} "
              f"{mx/1000:10.1f} {sm/1000:10.1f} {net:14.1f}")

    (out / "_reserve.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
