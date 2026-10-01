"""neiso-114 G-DRIFT (rule 29(b)), mechanical half: does HEAD rebuild the keeper's LP inputs?

Runs the NEISO keeper recipe (``results/calibration/rneiso_span/meta.json``)
through ``run_year(fleet_only=True)`` with THIS tree's own code (the script
imports ``src`` / ``scripts`` relative to its own location, so a copy placed in
a worktree at the keeper's basis SHA runs the basis code) and writes, per year,
the per-unit LP input arrays keyed by unit id: pmax, pmin, heat rate,
availability, min_gen, mc_base (the assembled P0 objective), plus demand and
the renewable potentials. Comparing the basis dump to the HEAD dump answers
"did any solve-path change since the keeper's basis move this ISO's inputs",
unit by unit, at zero LP.

Usage::

    python <tree>/docs/handoffs/neiso114/gdrift_fleet_probe.py --bundle-meta <meta.json> --out <dir> --tag <basis|head>
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

RENAMES = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_sigmoid_overrides": "bit_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
}
SKIP = {
    "year",
    "iso",
    "hours",
    "gas_price",
    "ttc_overrides",
    "fleet_only",
    "xyear_cache",
    "must_run_mw",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle-meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    args = ap.parse_args()
    import os

    os.chdir(REPO)
    from scripts import run_calibration_full as rcf
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads(Path(args.bundle_meta).read_text())
    params = inspect.signature(run_year).parameters
    kw = {
        RENAMES.get(k, k): v
        for k, v in meta.items()
        if RENAMES.get(k, k) in params and RENAMES.get(k, k) not in SKIP
    }
    kw["inject_biomass_mustrun"] = True
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for y in args.years:
        gas = henry_hub_actual(rcf._load_reference(), y)
        st = run_year(y, "NEISO", 8760, gas, {}, fleet_only=True, **kw)
        fa = st["fleet_arrays"]
        arr = {
            "unit_ids": np.array(fa.unit_ids, dtype=object),
            "plant_group": np.asarray(fa.plant_group).astype(str),
            "pmax": np.asarray(fa.pmax, float),
            "pmin": np.asarray(fa.pmin, float),
            "heat_rate": np.asarray(fa.heat_rate, float),
            "availability": np.asarray(fa.availability, np.float32),
            "min_gen": np.asarray(
                fa.min_gen
                if fa.min_gen is not None
                else np.zeros_like(fa.availability),
                np.float32,
            ),
            "mc_base": np.asarray(st["mc_base"], np.float32),
            "demand": np.asarray(st["demand"], np.float32),
            "wind": np.asarray(st["wind_cf"], np.float32)
            * np.asarray(st["wind_cap"], np.float32)[..., None]
            if np.ndim(st["wind_cap"]) == 1
            else np.asarray(st["wind_cf"], np.float32),
            "solar": np.asarray(st["solar_cf"], np.float32)
            * np.asarray(st["solar_cap"], np.float32)[..., None]
            if np.ndim(st["solar_cap"]) == 1
            else np.asarray(st["solar_cf"], np.float32),
        }
        np.savez_compressed(out / f"{args.tag}_{y}.npz", **arr)
        set_eia860_vintage(None)
        print(y, len(fa.unit_ids), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
