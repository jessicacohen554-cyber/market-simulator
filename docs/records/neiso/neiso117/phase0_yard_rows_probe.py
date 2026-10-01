"""neiso-117 phase 0 (ZERO LP): does the ARMED code path build the census's yard rows?

For each year 2019-2025, rebuild the NEISO keeper's fleet with
``run_year(fleet_only=True)`` on the keeper recipe (``replay_keeper.run_year_kwargs``,
the sanctioned reconstruction) with ``coal_fuel_inventory_plant_grain`` armed,
call ``build_coal_plant_budget`` exactly as ``run_year`` does, and compare each
yard's budget (TBtu) to ``docs/handoffs/neiso116/phase0_coal_budget_census.json``.
Also asserts the gate resolves to annual-rows-only for the armed NEISO config.

Usage::

    uv run python docs/handoffs/neiso117/phase0_yard_rows_probe.py --out docs/handoffs/neiso117/phase0_yard_rows_probe.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/neiso114b_span"
CENSUS = REPO / "docs/handoffs/neiso116/phase0_coal_budget_census.json"


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import resolve_coal_budget_arms, run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.coal_fuel_inventory import (
        build_coal_plant_budget,
        coal_yard_groups,
    )
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    census = json.loads(CENSUS.read_text())
    out = []
    for y in args.years:
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["prb_overrides"] = {
            **(kw.get("prb_overrides") or {}),
            "coal_fuel_inventory_plant_grain": True,
        }
        gas = henry_hub_actual(rcf._load_reference(), y)
        st = run_year(y, "NEISO", 8760, gas, {}, fleet_only=True, **kw)
        fa = st["fleet_arrays"]
        cfg = st.get("config")
        if cfg is not None:
            assert resolve_coal_budget_arms(cfg, "NEISO") == (False, True), "gate"
        res = build_coal_plant_budget(fa, y, hours=8760)
        yards = coal_yard_groups(fa)
        rowed_keys = []
        if res is not None:
            g_rows, budget, _mi, coeff, grp, prov = res
            from market_sim.data.coal_fuel_inventory import (
                reconcile_floors_to_yard_budget,
            )

            scaled = reconcile_floors_to_yard_budget(
                np.array(fa.min_gen, dtype=float, copy=True), g_rows, budget, coeff, grp
            )
            codes = np.asarray(fa.plant_code)
            for i in range(budget.shape[0]):
                plants = sorted(
                    {int(codes[g]) for g, gi in zip(g_rows, grp) if gi == i}
                )
                rowed_keys.append(
                    {
                        "row": i,
                        "plants": plants,
                        "budget_tbtu": round(float(budget[i, 0]) / 1e6, 3),
                    }
                )
        cen = {r["plant"]: r["budget_tbtu"] for r in census if r["year"] == y}
        for rk in rowed_keys:
            rk["census_tbtu"] = [cen.get(p) for p in rk["plants"]]
        rec = {
            "floor_scaled_rows": [
                {"row": r, "floor_tbtu": round(e / 1e6, 3), "scale": round(sc, 6)}
                for r, e, sc in (scaled if res is not None else [])
            ],
            "year": y,
            "yards": {str(k): sorted(v) for k, v in yards.items()},
            "rows": rowed_keys,
            "config_seen": cfg is not None,
        }
        print(json.dumps(rec), flush=True)
        set_eia860_vintage(None)
        out.append(rec)
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
