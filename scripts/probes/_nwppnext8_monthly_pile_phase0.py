"""NWPP-NEXT-8 phase 0 (ZERO LP): what the monthly pile grain builds, per yard, month and year.

Adapted from ``_nwppnext7_take_floor_phase0.py`` (the NEXT-7 probe, whose
docstring follows). Rebuilds keeper #14's fleet on its own recipe plus
``coal_fuel_inventory_monthly_pile`` and calls ``build_coal_monthly_pile`` exactly
as ``run_year`` does, then sets each yard's cumulative month-end floor and
ceiling against keeper #14's per-plant monthly model coal (payload ``m_mon``).

NEXT-7 docstring:

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

BUNDLE = REPO / "results/calibration/nwppnext7sf_span"
KEEPER = "2026-09-27-nwppnext7-coal-take-floor"
CENSUS = REPO / "results/calibration/_nwppnext5_coal_contract_census.json"
ARM = {
    "coal_fuel_inventory_plant_grain": True,
    "coal_fuel_inventory_take_floor": True,
    "coal_takeorpay_from_data": False,
    "coal_committed_takeorpay_regulated": False,
    "coal_fuel_inventory_monthly_pile": True,
}


def _keeper_coal_twh(year: int) -> dict[int, float]:
    s = (REPO / "frontend/data/backcast/runs" / f"{KEEPER}.js").read_text()
    pay = json.loads(
        gzip.decompress(base64.b64decode(s.split('="', 1)[1].rsplit('"', 1)[0]))
    )
    out: dict[int, float] = {}
    for k, p in pay["years"][str(year)]["plants"].items():
        if ":" in k and "COAL" not in k:
            continue
        out[int(k.split(":")[0])] = out.get(int(k.split(":")[0]), 0.0) + p["m_ann"]
    return out


def _keeper_coal_mon_twh(year: int) -> dict[int, np.ndarray]:
    s = (REPO / "frontend/data/backcast/runs" / f"{KEEPER}.js").read_text()
    pay = json.loads(
        gzip.decompress(base64.b64decode(s.split('="', 1)[1].rsplit('"', 1)[0]))
    )
    out: dict[int, np.ndarray] = {}
    for k, p in pay["years"][str(year)]["plants"].items():
        if ":" in k and "COAL" not in k:
            continue
        code = int(k.split(":")[0])
        out[code] = out.get(code, np.zeros(12)) + np.asarray(p["m_mon"], float) / 1e3
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
        resolve_coal_monthly_pile,
        resolve_coal_take_floor,
        run_year,
    )

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.coal_fuel_inventory import (
        build_coal_monthly_pile,
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
                resolve_coal_monthly_pile(cfg, "NWPP", True),
                {k: getattr(cfg, k) for k in ARM},
            ]
        g_rows, budget, _mi, coeff, grp, prov = build_coal_plant_budget(
            fa, y, hours=8760
        )
        floor, tf = build_coal_take_floor(
            fa, y, g_rows, grp, coeff, budget, prov.yard_keys
        )
        ceil_m, floor_m, _mi_m, pile = build_coal_monthly_pile(
            fa, g_rows, grp, coeff, budget, prov.stock_mmbtu, tf.parts, 8760
        )
        assert np.allclose(ceil_m[:, -1], budget[:, 0])
        assert np.allclose(floor_m[:, -1], floor[:, 0])
        mon = _keeper_coal_mon_twh(y)
        yards = coal_yard_groups(fa)
        model = _keeper_coal_twh(y)
        rows = []
        codes = np.asarray(fa.plant_code)
        pmax = np.asarray(fa.pmax, dtype=float)
        av = np.asarray(fa.availability, dtype=float)
        from market_sim.data.coal_fuel_inventory import coal_gen_idx

        rowed = set(int(g) for g in g_rows)
        unrowed = sorted(
            {int(codes[g]) for g in coal_gen_idx(fa) if int(g) not in rowed}
        )
        for i, key in enumerate(prov.yard_keys):
            sel = grp == i
            hr = float(np.average(coeff[sel])) if sel.any() else float("nan")
            ids = sorted(yards.get(key, {key}))
            cen = sum(
                (
                    census[str(y)]["plants"].get(str(p), {}).get("burn_floor_B_twh")
                    or 0.0
                )
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
                    "keeper14_model_twh": round(sum(model.get(p, 0.0) for p in ids), 3),
                    "avail_twh": round(
                        float((pmax[g_rows[sel]] * av[g_rows[sel]].sum(axis=1)).sum())
                        / 1e6,
                        3,
                    ),
                    "rowed_pmax_mw": round(float(pmax[g_rows[sel]].sum()), 1),
                    "cum_floor_twh": [
                        round(float(v) / hr / 1e6, 3) for v in floor_m[i]
                    ],
                    "cum_ceiling_twh": [
                        round(float(v) / hr / 1e6, 3) for v in ceil_m[i]
                    ],
                    "cum_keeper14_twh": [
                        round(float(v), 3)
                        for v in np.cumsum(
                            sum((mon.get(p, np.zeros(12)) for p in ids), np.zeros(12))
                        )
                    ],
                }
            )
        rec = {
            "year": y,
            "gate": gate,
            "n_unrowed_generators": prov.n_unrowed_generators,
            "unrowed_coal_plants": unrowed,
            "clipped_to_budget": tf.clipped_to_budget,
            "clipped_to_capacity": tf.clipped_to_capacity,
            "pile_clipped_ceiling_cells": pile.floor_clipped_to_ceiling,
            "pile_clipped_capacity_cells": pile.floor_clipped_to_capacity,
            # Per month-end, summed over yards: how far keeper #14's cumulative
            # burn sits below the cumulative floor / above the cumulative ceiling.
            "floor_gap_by_month_twh": [
                round(
                    sum(
                        max(0.0, r["cum_floor_twh"][m] - r["cum_keeper14_twh"][m])
                        for r in rows
                    ),
                    3,
                )
                for m in range(12)
            ],
            "ceiling_excess_by_month_twh": [
                round(
                    sum(
                        max(0.0, r["cum_keeper14_twh"][m] - r["cum_ceiling_twh"][m])
                        for r in rows
                    ),
                    3,
                )
                for m in range(12)
            ],
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
