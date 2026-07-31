"""ERCOT-144 pre-solve verification: capture the ARMED coal offer surface (no LP).

Replays the keeper's kwargs with coal_perplant_offer_level=True, spies on
apply_coal_tranches, and prints every coal row's final bid so the rule-19
replacement can be verified against the measured registry BEFORE any solve.
"""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import numpy as np

import os

os.environ["MARKET_SIM_WARMSTART_XYEAR"] = "0"
from scripts import replay_keeper as rk
from scripts import run_calibration as rc
from scripts import run_calibration_full as rcf

BUNDLE = REPO / "results/calibration/ercot140_coal_peak_arm"
SCRATCH = REPO / "results/calibration/_ercot144_scratch/armed_capture"
YEAR = int(sys.argv[1]) if len(sys.argv) > 1 else 2023


class _Captured(Exception):
    pass


meta = json.loads((BUNDLE / "meta.json").read_text())
kwargs = rk.build_kwargs(meta)
kwargs["years"] = [YEAR]
kwargs["iso"] = meta["iso"]
kwargs["hours"] = int(meta.get("hours", 8760))
kwargs["reference"] = rcf._load_reference()
kwargs["run_dir"] = SCRATCH / str(YEAR)
kwargs["coal_perplant_offer_level"] = True

real = rc.apply_coal_tranches
box = {}


def _spy(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config=None):
    real(mc, generators, fleet_arrays, fuel_fracs, fuel_prices, config)
    rows = [
        i
        for i, g in enumerate(generators)
        if str(getattr(g, "fuel_type", "")) == "coal"
    ]
    arr = np.asarray(mc, dtype=float)
    box["rows"] = [
        {
            "plant": int(getattr(generators[i], "plant_code", 0) or 0),
            "unit": str(fleet_arrays.unit_ids[i]),
            "pmax": float(fleet_arrays.pmax[i]),
            "bid_mean": float(arr[i].mean()),
            "bid_std": float(arr[i].std()),
        }
        for i in rows
    ]
    box["cfg"] = {
        "perplant": bool(getattr(config, "coal_perplant_offer_level", False)),
        "sig_prb": bool(getattr(config, "coal_prb_passthrough_sigmoid", None)),
        "sig_lig": bool(getattr(config, "coal_lignite_passthrough_sigmoid", None)),
        "hr_bound": bool(getattr(config, "coal_econ_marginal_hr_bound", None)),
        "coal_groups": [
            g
            for g in (getattr(config, "offer_curve_by_group", {}) or {})
            if g.startswith("COAL")
        ],
    }
    raise _Captured


rc.apply_coal_tranches = _spy
SCRATCH.mkdir(parents=True, exist_ok=True)
try:
    rcf.solve_and_persist(**kwargs)
except _Captured:
    pass
finally:
    rc.apply_coal_tranches = real

print("config state:", box["cfg"])
byp = {}
for r in box["rows"]:
    byp.setdefault(r["plant"], []).append(r)
for code in sorted(byp):
    rs = sorted(byp[code], key=lambda r: r["bid_mean"])
    tot = sum(r["pmax"] for r in rs)
    parts = " | ".join(
        f"{r['unit'].rpartition('_')[2]} {r['pmax'] / tot * 100:.0f}%@{r['bid_mean']:.2f}"
        + (f"±{r['bid_std']:.2f}" if r["bid_std"] > 0.01 else "")
        for r in rs
    )
    print(f"  {code:>6} {parts}")
