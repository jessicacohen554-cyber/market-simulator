"""NWPP-NEXT-10 phase 0 (ZERO LP): coal-plant AVAILABLE energy vs measured generation.

A plant cannot generate more than it is available to generate, so a plant-year
whose model available energy ``sum_t pmax[g] * availability[g, t]`` sits below
its own EIA-923 net generation is an input defect by physics, with no residual
and no benchmark fit involved (rule 14 [R-ACCURATE]).

Rebuilds keeper #15's fleet with ``run_year(fleet_only=True)`` on its own recipe
(``replay_keeper.run_year_kwargs`` over the committed bundle meta, as the NEXT-9
probe does) and, per variant, with ONE existing default-off outage-accounting
repair armed on top. Reports each coal plant's available TWh and pmax beside its
EIA-923 net generation.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/_nwppnext10_coal_availability_census.py \
        --years 2020 --variants base fleet_status_scope --out OUT.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

BUNDLE = REPO / "results/calibration/nwppnext8mp_span"
GEN = REPO / "data/raw/eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv"
VARIANTS = {
    "base": {},
    "fleet_status_scope": {"unit_outage_fleet_status_scope": True},
    "dispatched_bin_denominator": {"unit_outage_dispatched_bin_denominator": True},
    "per_unit_clip": {"unit_outage_per_unit_clip": True},
    "coal_extract_basis_share": {"unit_outage_coal_extract_basis_share": True},
    "exit_ym_from_eia860": {"unit_outage_exit_ym_from_eia860": True},
}


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=list(range(2019, 2026)))
    ap.add_argument("--variants", nargs="+", default=list(VARIANTS))
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    from scripts import run_calibration_full as rcf
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    from market_sim.config.paths import set_eia860_vintage
    from market_sim.data.coal_fuel_inventory import coal_gen_idx
    from market_sim.pipeline.reference import henry_hub_actual

    gen = pd.read_csv(GEN)
    meta = json.loads((BUNDLE / "meta.json").read_text())
    out = []
    for y in args.years:
        g923 = gen[gen.year == y].groupby("plant_id")["net_generation_mwh"].sum()
        for v in args.variants:
            kw = run_year_kwargs(meta)
            kw.update(derived_run_year_inputs(BUNDLE, y))
            kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **VARIANTS[v]}
            if y <= 2022:
                kw["prb_overrides"]["hydro_backfill_year"] = None
            gas = henry_hub_actual(rcf._load_reference(), y)
            st = run_year(y, "NWPP", 8760, gas, {}, fleet_only=True, **kw)
            fa = st["fleet_arrays"]
            cfg = st.get("config")
            armed = {k: getattr(cfg, k) for k in VARIANTS[v]} if cfg is not None else {}
            gi = coal_gen_idx(fa)
            codes = np.asarray(fa.plant_code)[gi]
            pmax = np.asarray(fa.pmax, float)[gi]
            av = np.asarray(fa.availability, float)[gi]
            e = pmax * av.sum(axis=1)
            rows = {}
            for c in np.unique(codes):
                s = codes == c
                rows[int(c)] = {
                    "pmax_mw": round(float(pmax[s].sum()), 1),
                    "avail_twh": round(float(e[s].sum()) / 1e6, 3),
                    "eia923_net_twh": round(float(g923.get(int(c), 0.0)) / 1e6, 3),
                }
            short = {
                c: r for c, r in rows.items() if r["avail_twh"] < r["eia923_net_twh"]
            }
            rec = {
                "year": y,
                "variant": v,
                "armed": armed,
                "coal_avail_twh": round(sum(r["avail_twh"] for r in rows.values()), 3),
                "n_short": len(short),
                "short_twh": round(
                    sum(r["eia923_net_twh"] - r["avail_twh"] for r in short.values()), 3
                ),
                "short": short,
                "rows": rows,
            }
            print(json.dumps({k: rec[k] for k in rec if k != "rows"}), flush=True)
            set_eia860_vintage(None)
            out.append(rec)
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
