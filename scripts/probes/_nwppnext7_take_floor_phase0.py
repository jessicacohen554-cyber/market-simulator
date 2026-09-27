"""NWPP-NEXT-7 phase 0 (ZERO LP): what the armed coal take floor builds, per yard and year.

Rebuilds keeper #13's fleet with ``run_year(fleet_only=True)`` on its own recipe
(``replay_keeper.run_year_kwargs``) plus the arm — ``coal_fuel_inventory_plant_grain``
and ``coal_fuel_inventory_take_floor`` on, the two per-hour take-or-pay discounts
off (owner ruling Q5) — then calls ``build_coal_plant_budget`` and
``build_coal_take_floor`` exactly as ``run_year`` does. Reports, per yard, the
ceiling and the floor (TWh-equivalent at the yard's own fleet heat rate) beside
keeper #13's model coal and the NWPP-NEXT-5 census ``burn_floor_B_twh``.

Usage::

    python3 scripts/probes/_nwppnext7_take_floor_phase0.py \
        --out results/calibration/_nwppnext7_take_floor_phase0.json
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/nwppnext6ab_span"
KEEPER = "2026-09-26-nwppnext6-path76-ctrederive"
CENSUS = REPO / "results/calibration/_nwppnext5_coal_contract_census.json"
ARM = {
    "coal_fuel_inventory_plant_grain": True,
    "coal_fuel_inventory_take_floor": True,
    "coal_takeorpay_from_data": False,
    "coal_committed_takeorpay_regulated": False,
}


def _keeper_coal_twh(year: int) -> dict[int, float]:
    s = (REPO / "frontend/data/backcast/runs" / f"{KEEPER}.js").read_text()
    pay = json.loads(gzip.decompress(base64.b64decode(s.split('="', 1)[1].rsplit('"', 1)[0])))
    out: dict[int, float] = {}
    for k, p in pay["years"][str(year)]["plants"].items():
        if ":" in k and "COAL" not in k:
            continue
        out[int(k.split(":")[0])] = out.get(int(k.split(":")[0]), 0.0) + p["m_ann"]
    return out


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import (
        resolve_coal_budget_arms,
        resolve_coal_take_floor,
        run_year,
    )

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.coal_fuel_inventory import (
        build_coal_plant_budget,
        build_coal_take_floor,
        coal_yard_groups,
    )
    from market_sim.pipeline.reference import henry_hub_actual

    meta = json.loads((BUNDLE / "meta.json").read_text())
    census = json.loads(CENSUS.read_text())["per_year"]
    out = []
    for y in args.years:
        kw = run_year_kwargs(meta)
        kw.update(derived_run_year_inputs(BUNDLE, y))
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **ARM}
        if y <= 2022:
            kw["prb_overrides"]["hydro_backfill_year"] = None
        gas = henry_hub_actual(rcf._load_reference(), y)
        st = run_year(y, "NWPP", 8760, gas, {}, fleet_only=True, **kw)
        fa = st["fleet_arrays"]
        cfg = st.get("config")
        gate = None
        if cfg is not None:
            gate = [
                list(resolve_coal_budget_arms(cfg, "NWPP")),
                resolve_coal_take_floor(cfg, "NWPP", True),
                {k: getattr(cfg, k) for k in ARM},
            ]
        g_rows, budget, _mi, coeff, grp, prov = build_coal_plant_budget(fa, y, hours=8760)
        floor, tf = build_coal_take_floor(fa, y, g_rows, grp, coeff, budget, prov.yard_keys)
        yards = coal_yard_groups(fa)
        model = _keeper_coal_twh(y)
        rows = []
        codes = np.asarray(fa.plant_code)
        pmax = np.asarray(fa.pmax, dtype=float)
        av = np.asarray(fa.availability, dtype=float)
        from market_sim.data.coal_fuel_inventory import coal_gen_idx

        rowed = set(int(g) for g in g_rows)
        unrowed = sorted({int(codes[g]) for g in coal_gen_idx(fa) if int(g) not in rowed})
        for i, key in enumerate(prov.yard_keys):
            sel = grp == i
            hr = float(np.average(coeff[sel])) if sel.any() else float("nan")
            ids = sorted(yards.get(key, {key}))
            cen = sum(
                (census[str(y)]["plants"].get(str(p), {}).get("burn_floor_B_twh") or 0.0)
                for p in ids
            )
            rows.append(
                {
                    "yard": key,
                    "plants": ids,
                    "hr": round(hr, 3),
                    "ceiling_twh": round(float(budget[i, 0]) / hr / 1e6, 3),
                    "floor_twh": round(float(floor[i, 0]) / hr / 1e6, 3),
                    "census_Bnet_twh": round(cen, 3),
                    "keeper13_model_twh": round(sum(model.get(p, 0.0) for p in ids), 3),
                    "avail_twh": round(
                        float((pmax[g_rows[sel]] * av[g_rows[sel]].sum(axis=1)).sum()) / 1e6, 3
                    ),
                    "rowed_pmax_mw": round(float(pmax[g_rows[sel]].sum()), 1),
                }
            )
        rec = {
            "year": y,
            "gate": gate,
            "n_unrowed_generators": prov.n_unrowed_generators,
            "unrowed_coal_plants": unrowed,
            "clipped_to_budget": tf.clipped_to_budget,
            "clipped_to_capacity": tf.clipped_to_capacity,
            "floor_binding_vs_k13_twh": round(
                sum(max(0.0, r["floor_twh"] - r["keeper13_model_twh"]) for r in rows), 3
            ),
            "ceiling_binding_vs_k13_twh": round(
                sum(max(0.0, r["keeper13_model_twh"] - r["ceiling_twh"]) for r in rows), 3
            ),
            "rows": rows,
        }
        print(json.dumps({k: v for k, v in rec.items() if k != "rows"}), flush=True)
        for r in rows:
            print("   ", r, flush=True)
        set_eia860_vintage(None)
        out.append(rec)
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
