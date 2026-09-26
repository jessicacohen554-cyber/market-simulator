"""neiso-119 phase 0 (a)+(b), zero LP: winter fuel-security floor conduct + heat rates.

fleet_only rebuild on the keeper recipe. For every unit carrying the
winter fuel-security floor (MECH_WINTER_FUELSEC = 14) reports the hours it is
floored, the floor MW, and the plant's CAMPD measured gross load over those same
hours (median and share at zero) — the per-unit conduct test D-4 would apply if the
mechanism had a D4_WINDOWS entry. Also reports the current per-tranche heat rate
of the plants the class-preserving re-derive would touch (1599, 6156, 8002, 10726).
Writes ``phase0_fuelsec_<Y>.json``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
BUNDLE = REPO / "results/calibration/neiso118_span"
STATES = ("CT", "MA", "ME", "NH", "RI", "VT")
WATCH = (1599, 6156, 8002, 10726)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2019)
    y = ap.parse_args().year
    os.chdir(REPO)
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.floor_mechanisms import MECH_WINTER_FUELSEC
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
    plant = np.asarray(fa.plant_code).astype(int)
    uid = np.asarray(fa.unit_ids).astype(str)
    mg = np.asarray(fa.min_gen, float)
    mech = np.asarray(fa.min_gen_mechanism)
    hr = np.asarray(fa.heat_rate, float)
    pmax = np.asarray(fa.pmax, float)
    fs = mech == MECH_WINTER_FUELSEC
    cems = pd.concat(
        [
            pd.read_parquet(
                REPO / f"data/raw/campd-unit-level/{s}_{y}.parquet",
                columns=["facilityId", "date", "hour", "grossLoad"],
            )
            for s in STATES
        ]
    )
    cems["facilityId"] = pd.to_numeric(cems["facilityId"], errors="coerce").astype(
        "Int64"
    )
    cems["t"] = (
        (pd.to_datetime(cems["date"]) - pd.Timestamp(f"{y}-01-01")).dt.days * 24
        + cems["hour"]
    ).astype(int)
    plant_hr = cems.groupby(["facilityId", "t"]).grossLoad.sum(min_count=1)
    rows = []
    for p in sorted(set(plant[fs.any(1)])):
        m = plant == p
        bind = fs[m].any(0)
        floor = (mg[m] * fs[m]).sum(0)
        meas = plant_hr.loc[p] if p in set(plant_hr.index.get_level_values(0)) else None
        meas = (
            meas.reindex(range(8760)).fillna(0.0).to_numpy()
            if meas is not None
            else np.zeros(8760)
        )
        h = np.nonzero(bind)[0]
        rows.append(
            {
                "plant": int(p),
                "classes": sorted(set(grp[m & fs.any(1)])),
                "floored_hours": int(bind.sum()),
                "floor_twh": round(float(floor.sum()) / 1e6, 4),
                "floor_mw_mean_when_bound": round(float(floor[h].mean()), 1)
                if h.size
                else 0.0,
                "cems_median_mw_when_bound": round(float(np.median(meas[h])), 1)
                if h.size
                else None,
                "cems_share_zero_when_bound": round(float((meas[h] <= 0).mean()), 3)
                if h.size
                else None,
                "cems_twh_when_bound": round(float(meas[h].sum()) / 1e6, 4),
                "cems_twh_year": round(float(meas.sum()) / 1e6, 4),
            }
        )
    hrs = []
    for p in WATCH:
        for i in np.nonzero(plant == p)[0]:
            hrs.append(
                {
                    "plant": int(p),
                    "unit": uid[i],
                    "class": grp[i],
                    "pmax": round(float(pmax[i]), 1),
                    "heat_rate": round(float(hr[i]), 3),
                }
            )
    out = {"year": y, "fuelsec": rows, "watch_heat_rates": hrs}
    Path(__file__).with_name(f"phase0_fuelsec_{y}.json").write_text(
        json.dumps(out, indent=1)
    )
    for r in rows:
        print(r)
    for r in hrs:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
