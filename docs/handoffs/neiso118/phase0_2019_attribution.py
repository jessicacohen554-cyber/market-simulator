"""neiso-118 phase 0 (zero LP): who carries 2019's ST_GAS / CT_PEAKER / coal excess?

Rebuilds 2019 on the NEISO keeper's own recipe (``results/calibration/neiso117_span``)
with ``run_year(fleet_only=True)`` through ``replay_keeper.run_year_kwargs`` (the only
sanctioned fleet-only reconstruction), then joins, per plant x class:

* the keeper's P1 annual TWh (``m_ann`` from the registered run payload),
* EIA-923 net generation (the benchmark's actual basis) per plant,
* per-unit pmax, mean availability, mean floor MW (``min_gen``) and the floor mechanism
  (``min_gen_mechanism``), and floor energy = sum_t min_gen (the energy the floor forces
  if the unit is held at it all year; an upper bound on forced energy).

Writes ``phase0_2019_attribution.json`` next to itself.

Usage::

    uv run python docs/handoffs/neiso118/phase0_2019_attribution.py [--year 2019]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

BUNDLE = REPO / "results/calibration/neiso117_span"
RUN_ID = "2026-09-26-neiso-117-coal-yard"
FOCUS = ("ST_GAS", "CT_PEAKER", "COAL_BIT", "COAL_PRB", "CC_REGULAR")


def _payload_year(year: int) -> dict:
    s = (REPO / f"frontend/data/backcast/runs/{RUN_ID}.js").read_text()
    b = re.search(r'="([A-Za-z0-9+/=]+)"', s).group(1)
    return json.loads(gzip.decompress(base64.b64decode(b)))["years"][str(year)]


def _eia923(year: int) -> pd.Series:
    d = pd.read_csv(
        REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
    )
    d = d[d.year == year]
    return d.groupby("plant_id").net_generation_mwh.sum() / 1e6


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, default=2019)
    args = ap.parse_args()
    import os

    os.chdir(REPO)
    from scripts import replay_keeper as rk
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.floor_mechanisms import MECH_NAMES
    from market_sim.pipeline.reference import henry_hub_actual

    y = args.year
    meta = json.loads((BUNDLE / "meta.json").read_text())
    rc = json.loads((BUNDLE / f"run_config_{y}.json").read_text())
    kw = rk.run_year_kwargs(meta)
    kw.update(rk.derived_run_year_inputs(BUNDLE, y))
    gas = henry_hub_actual(rcf._load_reference(), y)
    st = run_year(y, "NEISO", 8760, gas, {}, fleet_only=True, **kw)
    set_eia860_vintage(None)
    fa = st["fleet_arrays"]
    uid = list(fa.unit_ids)
    grp = np.asarray(fa.plant_group).astype(str)
    pmax = np.asarray(fa.pmax, float)
    av = np.asarray(fa.availability, float)
    mg = np.asarray(fa.min_gen, float) if fa.min_gen is not None else np.zeros_like(av)
    mech = getattr(fa, "min_gen_mechanism", None)
    plant = np.asarray(fa.plant_code).astype(int).astype(str)
    mc = np.asarray(st["mc_base"], float)

    per = defaultdict(lambda: defaultdict(float))
    mechs = defaultdict(set)
    for i in range(len(uid)):
        g = grp[i]
        if g not in FOCUS:
            continue
        key = f"{plant[i]}:{g}"
        p = per[key]
        p["pmax_mw"] += pmax[i]
        p["avail_cap_twh"] += float((pmax[i] * av[i]).sum()) / 1e6
        p["floor_twh"] += float(mg[i].sum()) / 1e6
        p["n_units"] += 1
        p["mc_mean"] = max(
            p["mc_mean"], float(mc[i].mean()) if mc.ndim == 2 else float(mc[i])
        )
        if mech is not None:
            m = np.asarray(mech[i])
            for code in (
                np.unique(m[m != 0]) if m.dtype.kind in "iu" else np.unique(m[m != ""])
            ):
                mechs[key].add(str(code))

    pay = _payload_year(y)["plants"]
    act = _eia923(y)
    rows = []
    for key, p in per.items():
        pid, g = key.split(":")
        m_ann = pay.get(key, pay.get(pid, {})).get("m_ann")
        rows.append(
            {
                "plant": pid,
                "class": g,
                "n_units": int(p["n_units"]),
                "pmax_mw": round(p["pmax_mw"], 1),
                "avail_cap_twh": round(p["avail_cap_twh"], 3),
                "floor_twh": round(p["floor_twh"], 3),
                "floor_mechs": sorted(mechs[key]),
                "mc_base_mean": round(p["mc_mean"], 2),
                "model_twh": m_ann,
                "eia923_plant_twh": round(float(act.get(int(pid), 0.0)), 3)
                if pid.isdigit()
                else None,
            }
        )
    rows.sort(key=lambda r: (r["class"], -(r["model_twh"] or 0)))
    out = {
        "year": y,
        "keeper": RUN_ID,
        "mechanism_codes": {int(k): v for k, v in MECH_NAMES.items()},
        "recipe_flags": sorted(k for k, v in rc.items() if v is True)[:0],
        "rows": rows,
    }
    for g in FOCUS:
        rr = [r for r in rows if r["class"] == g]
        out[f"total_{g}"] = {
            "model_twh": round(sum(r["model_twh"] or 0 for r in rr), 3),
            "floor_twh": round(sum(r["floor_twh"] for r in rr), 3),
        }
    Path(__file__).with_name(f"phase0_{y}_attribution.json").write_text(
        json.dumps(out, indent=1, default=str)
    )
    for g in FOCUS[:4]:
        print(g, out[f"total_{g}"])
        for r in [r for r in rows if r["class"] == g][:15]:
            print("  ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
