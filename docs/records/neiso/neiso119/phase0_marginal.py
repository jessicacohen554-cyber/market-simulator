"""neiso-119 phase 0 (d)+(a), zero LP: what is price-setting in the keeper's cheap hours?

Rebuilds a year with ``run_year(fleet_only=True)`` on the keeper recipe
(``replay_keeper.run_year_kwargs(neiso118_span/meta.json)``), then for every hour
takes the keeper's committed P1 zonal price and lists the thermal units whose
offer (``mc_base[g, t]``) sits within $0.50 of it (the price-setting candidates).
Reports, by actual-RT price bucket, the class mix of those candidates, and the
class-mean gas fuel price by month. Writes ``phase0_marginal_<Y>.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
BUNDLE = REPO / "results/calibration/neiso118_span"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2019)
    y = ap.parse_args().year
    os.chdir(REPO)
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = rk.run_year_kwargs(meta)
    kw.update(rk.derived_run_year_inputs(BUNDLE, y))
    st = run_year(
        y,
        "NEISO",
        8760,
        henry_hub_actual(rcf._load_reference(), y),
        {},
        fleet_only=True,
        **kw,
    )
    set_eia860_vintage(None)
    fa = st["fleet_arrays"]
    grp = np.asarray(fa.plant_group).astype(str)
    from market_sim.config.iso_configs import get_iso_config

    zn = list(get_iso_config("NEISO").zone_names)
    zone = np.array([zn[i] for i in np.asarray(fa.zone_idx, int)])
    plant = np.asarray(fa.plant_code).astype(int)
    mc = np.asarray(st["mc_base"], float)
    if mc.ndim == 1:
        mc = np.repeat(mc[:, None], 8760, 1)
    print("keys", sorted(st.keys()))
    s = pd.read_parquet(BUNDLE / f"hourly/system_{y}.parquet")
    s = s[s["pass"] == "P1"]
    price = s.pivot(index="zone", columns="hour", values="price")
    a = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet"
    )
    a = a[a.year == y].set_index("hour")["rt"].reindex(range(8760))
    bins = [-1e9, 20, 25, 30, 40, 60, 100, 1e9]
    lab = pd.cut(a, bins).astype(str)
    counts: dict[str, Counter] = {}
    plants: dict[str, Counter] = {}
    for t in range(8760):  # diagnostic, not LP construction (rule 2 n/a)
        if np.isnan(a.iloc[t]):
            continue
        cand = np.zeros(len(grp), bool)
        for z in price.index:
            m = zone == z
            cand |= m & (np.abs(mc[:, t] - price.loc[z, t]) <= 0.5)
        c = counts.setdefault(lab.iloc[t], Counter())
        pc = plants.setdefault(lab.iloc[t], Counter())
        for g in set(grp[cand]):
            c[g] += 1
        for pid, g in set(zip(plant[cand], grp[cand])):
            pc[f"{pid}:{g}"] += 1
        c["_hours"] += 1
    # gas fuel price by class (mean over gas units) by month
    fp = st.get("fuel_prices")
    gas = {}
    if fp is not None:
        fp = np.asarray(fp, float)
        mon = (pd.Timestamp(f"{y}-01-01") + pd.to_timedelta(np.arange(8760), "h")).month
        for g in ("CC_REGULAR", "CT_PEAKER", "ST_GAS"):
            m = grp == g
            if m.any() and fp.ndim == 2:
                gas[g] = [
                    round(float(fp[m][:, mon == k].mean()), 3) for k in range(1, 13)
                ]
    out = {
        "year": y,
        "candidates_by_actual_bucket": {
            k: dict(v.most_common()) for k, v in counts.items()
        },
        "top_plants_by_bucket": {k: dict(v.most_common(12)) for k, v in plants.items()},
        "gas_price_by_class_month": gas,
    }
    Path(__file__).with_name(f"phase0_marginal_{y}.json").write_text(
        json.dumps(out, indent=1)
    )
    for k in sorted(counts, key=lambda s: float(s.split(",")[0].strip("("))):
        print(k, dict(counts[k].most_common(8)))
        print("   ", dict(plants[k].most_common(8)))
    print(gas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
