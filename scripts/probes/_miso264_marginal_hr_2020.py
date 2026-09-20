#!/usr/bin/env python3
"""miso-264 phase 0, §E: the 2020 bulk price-setter's IMPLIED MARGINAL HEAT RATE.

ZERO LP (rule 32 ``[R-SHARD]`` (a)).  A companion to
``_miso264_bulk_price_setter_phase0.py``: that probe says WHICH (class, band)
sets MISO's 2020 bulk price; this one says WHAT THE OFFER IS MADE OF, and sets
it beside the same hours' measured RT price expressed on the same basis.

The instrument is the implied marginal heat rate, ``price / delivered gas``:
the one comparison that is scale-free in the fuel level, so a model-vs-market
gap in it is a statement about the OFFER, not about the fuel input the model
and the market share.  It is the same instrument ``FINDING-caiso270`` §4 used
(a system-wide +1 implied-marginal-HR bias) and ``miso-214`` used on MISO's
CT_INTERMEDIATE cohort (offered 12.465 against a measured burn of 11.07).

Reported, never tuned: no mechanism is armed, no parameter moves, nothing is
swept (rule 1 ``[R-STRUCT]``; rule 21 ``[R-DOF]``).
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

from scripts.probes._miso264_bulk_price_setter_phase0 import (  # noqa: E402
    BUNDLE,
    INTERNAL,
    TOL,
    build_state,
    family,
)

YEAR = 2020
OUT = REPO / "results/calibration/_miso264_marginal_hr_2020.json"


def main() -> None:
    st = build_state(YEAR, armed=False)
    fa, fleet = st["fleet_arrays"], st["fleet"]
    mc = np.asarray(st["mc_base"], float)
    fuel = np.asarray(st["fuel_prices"], float)
    hr = np.asarray(fa.heat_rate, float)
    vom = np.asarray(fa.vom, float)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    raw = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    ft = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    binned = raw != ""
    klass = np.where(binned, raw, ft)
    band = np.where(binned, [str(u).rsplit("_", 1)[-1] for u in fa.unit_ids], "")
    fams = np.array([family(k, b) for k, b in zip(klass, band)])
    zone = np.array([str(getattr(g, "zone", "") or "") for g in fleet])
    markup = np.array(
        [float(getattr(g, "offer_markup_hr", 0.0) or 0.0) for g in fleet]
    )

    s = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    s = s[s["pass"] == "P1"]
    pr = s.pivot(index="hour", columns="zone", values="price")[list(INTERNAL)]
    dm = s.pivot(index="hour", columns="zone", values="demand")[list(INTERNAL)]
    price = pr.to_numpy(float).T
    demand = dm.to_numpy(float).T
    act = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_MISO.parquet")
    act = act[act["year"] == YEAR].sort_values("hour")
    rt = act["rt"].to_numpy(float)

    # Per-family accumulators over the POOLED census (any MISO row may price a
    # congested zone).
    acc: dict[str, dict[str, float]] = {}
    for zi in range(len(INTERNAL)):
        hit = (cap > 1e-6) & (np.abs(mc - price[zi][None, :]) <= TOL)
        n = hit.sum(axis=0)
        ok = n > 0
        if not ok.any():
            continue
        w = np.where(hit, 1.0, 0.0) / np.maximum(n, 1)[None, :] * demand[zi][None, :]
        for f in np.unique(fams):
            m = fams == f
            ww = w[m]
            tot = float(ww.sum())
            if tot <= 0:
                continue
            a = acc.setdefault(
                f,
                dict(mwh=0.0, mc=0.0, fuel=0.0, hr=0.0, vom=0.0, mk=0.0, rt=0.0, mp=0.0),
            )
            a["mwh"] += tot
            a["mc"] += float((ww * mc[m]).sum())
            a["fuel"] += float((ww * fuel[m]).sum())
            a["hr"] += float((ww * hr[m][:, None]).sum())
            a["vom"] += float((ww * vom[m][:, None]).sum())
            a["mk"] += float((ww * markup[m][:, None]).sum())
            a["rt"] += float((ww * rt[None, :]).sum())
            a["mp"] += float((ww * price[zi][None, :]).sum())

    rows = []
    for f, a in sorted(acc.items(), key=lambda kv: -kv[1]["mwh"]):
        w = a["mwh"]
        r = dict(
            family=f,
            share=w / sum(v["mwh"] for v in acc.values()),
            mc=a["mc"] / w,
            fuel=a["fuel"] / w,
            hr=a["hr"] / w,
            vom=a["vom"] / w,
            markup_hr=a["mk"] / w,
            model_price=a["mp"] / w,
            rt_price=a["rt"] / w,
        )
        r["implied_hr_model"] = r["mc"] / r["fuel"] if r["fuel"] else float("nan")
        r["implied_hr_market"] = r["rt_price"] / r["fuel"] if r["fuel"] else float("nan")
        r["d_implied_hr"] = r["implied_hr_model"] - r["implied_hr_market"]
        r["fuel_leg"] = r["hr"] * r["fuel"]
        r["above_fuel"] = r["mc"] - r["fuel_leg"]
        rows.append(r)

    print(
        f"{'family':18s}{'share':>7}{'mc':>8}{'fuelleg':>8}{'above':>7}"
        f"{'physHR':>8}{'mkHR':>7}{'$/MMBtu':>9}{'imHRmod':>9}{'imHRmkt':>9}{'dHR':>7}"
    )
    for r in rows:
        if r["share"] < 0.005:
            continue
        print(
            f"{r['family']:18s}{100 * r['share']:6.1f}%{r['mc']:8.2f}{r['fuel_leg']:8.2f}"
            f"{r['above_fuel']:7.2f}{r['hr']:8.3f}{r['markup_hr']:7.3f}"
            f"{r['fuel']:9.3f}{r['implied_hr_model']:9.3f}"
            f"{r['implied_hr_market']:9.3f}{r['d_implied_hr']:7.3f}"
        )
    OUT.write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
