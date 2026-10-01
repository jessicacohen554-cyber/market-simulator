"""NWPP-NEXT-15 zero-LP census: coal_captive_marginal_fuel_price on keeper #18.

Fleet-only rebuilds (``run_year(..., fleet_only=True)``, no LP) of NWPP keeper #18
(``results/calibration/nwppnext13pu_span``) on its own recipe (``off``) and with
``coal_captive_marginal_fuel_price`` armed (``on``). For every coal row whose
fully-assembled fuel-price array moves it reports, per plant-year and tranche
family, the annual-mean price delta ($/MMBtu) and the implied offer delta
($/MWh = delta x the row's heat rate). Must-run / committed rows are listed only
if they move (they must not). 2025 has no EIA-923 Page 5 file: the flag must
leave it untouched (and the seam logs that it did).

Expected from ``docs/records/nwpp/PHASE0-nwppnext15-captive-mine-2026-09-30.md`` §2:
essentially Jim Bridger 8066 (2023 ~ -0.9 $/MMBtu, 2022 ~ +0.13) plus small
Hunter / Huntington moves.

Usage::

    python scripts/probes/_nwppnext15_captive_price_census.py --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import sys

import numpy as np
import pandas as pd

from market_sim.config.paths import REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

BUNDLE = REPO_ROOT / "results/calibration/nwppnext13pu_span"
FLAG = "coal_captive_marginal_fuel_price"


def _family(unit_id: str) -> str:
    """Tranche family of a CAMPD row: econ / peak / other (must-run, committed)."""
    tail = str(unit_id).rsplit("_", 1)[-1]
    if tail.startswith("econ"):
        return "econ"
    if tail.startswith("peak"):
        return "peak"
    return "other"


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.fleet import FUEL_TYPE_MAP
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    rows: list[dict] = []
    for y in args.years:
        gas = henry_hub_actual(rcf._load_reference(), y)
        out = {}
        for v, flag in (("off", False), ("on", True)):
            kw = run_year_kwargs(meta)
            kw.update(derived_run_year_inputs(BUNDLE, y))
            kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), FLAG: flag}
            if y <= 2022:
                kw["prb_overrides"]["hydro_backfill_year"] = None
            st = run_year(y, "NWPP", 8760, gas, {}, fleet_only=True, **kw)
            out[v] = st
            set_eia860_vintage(None)
        fa = out["off"]["fleet_arrays"]
        assert list(fa.unit_ids) == list(out["on"]["fleet_arrays"].unit_ids)
        fp0 = np.asarray(out["off"]["fuel_prices"], float)
        fp1 = np.asarray(out["on"]["fuel_prices"], float)
        coal = np.asarray(fa.fuel_type_idx) == FUEL_TYPE_MAP["coal"]
        non_coal_moved = int(((fp1 != fp0).any(axis=1) & ~coal).sum())
        assert non_coal_moved == 0, f"{y}: {non_coal_moved} non-coal rows moved"
        moved = np.nonzero((fp1 != fp0).any(axis=1))[0]
        df = pd.DataFrame(
            {
                "unit_id": [fa.unit_ids[g] for g in moved],
                "plant": np.asarray(fa.plant_code)[moved].astype(int),
                "hr": np.asarray(fa.heat_rate, float)[moved],
                "p_off": fp0[moved].mean(axis=1),
                "p_on": fp1[moved].mean(axis=1),
            }
        )
        if df.empty:
            print(f"{y}: no coal row moved")
            continue
        df["family"] = df["unit_id"].map(_family)
        df["d_mmbtu"] = df["p_on"] - df["p_off"]
        df["d_mwh"] = df["d_mmbtu"] * df["hr"]
        for (p, fam), g in df.groupby(["plant", "family"]):
            rows.append(
                {
                    "year": y,
                    "plant": int(p),
                    "family": fam,
                    "rows": int(len(g)),
                    "p_off": round(float(g["p_off"].mean()), 3),
                    "p_on": round(float(g["p_on"].mean()), 3),
                    "d_mmbtu": round(float(g["d_mmbtu"].mean()), 3),
                    "hr_min": round(float(g["hr"].min()), 3),
                    "hr_max": round(float(g["hr"].max()), 3),
                    "d_mwh_min": round(float(g["d_mwh"].min()), 2),
                    "d_mwh_max": round(float(g["d_mwh"].max()), 2),
                }
            )
    res = pd.DataFrame(rows)
    pd.set_option("display.width", 250)
    print(res.to_string(index=False) if not res.empty else "no moves")
    if args.out:
        with open(args.out, "w") as f:
            json.dump(
                {"bundle": str(BUNDLE.name), "flag": FLAG, "rows": rows}, f, indent=1
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
