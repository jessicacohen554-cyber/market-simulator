#!/usr/bin/env python3
"""miso-268 phase 0: does the POOLED coal budget hide yard-level infeasibility?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). ``coal_fuel_inventory`` caps coal energy
input against ONE fleet pile — the sum of every yard's Dec(Y-1) stock and
prior-years receipts. Coal cannot move between yards, so the physically
correct partition is per yard. This measures, on the keeper's own solved
dispatch, how much coal energy the keeper burns at yards beyond that yard's
own supply — the quantity ``coal_fuel_inventory_plant_grain`` would bind on.

Inputs, all committed or rebuilt without a solve:

* the keeper's per-unit P1 dispatch (``dispatch/<Y>_P1.parquet`` from the
  miso-267 per-year shard commits, pinned by full SHA below — the composite
  bundle on ``main`` carries only the slim set);
* a ``run_year(fleet_only=True)`` rebuild on the keeper's own recipe for the
  LP's heat rates and unit ids;
* :func:`build_coal_plant_budget` — the exact rows the arm would add.

The static excess is an UPPER BOUND on the arm's removal: the LP can move coal
to yards with slack. Reported, never tuned.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.coal_fuel_inventory import (  # noqa: E402
    build_coal_fuel_budget,
    build_coal_plant_budget,
    coal_gen_idx,
    coal_yard_groups,
)
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402

KEEPER = REPO / "results/calibration/miso267_dbd_span"
#: miso-267 per-year shard commits carrying the keeper's full per-unit dispatch
#: (provenance per rule 33 (d); fetchable by SHA while the objects survive).
LEG_SHA = {
    2020: "b14d04407995df14db17ea63a6ac2e2eed81747c",
    2021: "856c2a0828d6632088178c593273e926bbd922d9",
    2022: "f70fac80af0dd06789cc6e1318051b2ecc23ccd9",
    2023: "2aa8a9c50da3a6de9a98b73b77336387cd8f24b8",
    2024: "80036e25f34b201af9dc6d1a6934c376ab088470",
    2025: "034dadb290009aa0ebf14629eb1d903c480bc1a5",
}


def keeper_dispatch(year: int) -> tuple[pd.Series, pd.Series]:
    """Per-unit annual P1 MWh, and each unit's scored class, from the keeper's leg commit."""
    sha = LEG_SHA[year]
    subprocess.run(["git", "fetch", "-q", "origin", sha], cwd=REPO, check=False)
    blob = subprocess.run(
        ["git", "show", f"{sha}:results/calibration/miso267_dbd_{year}/dispatch/{year}_P1.parquet"],
        cwd=REPO, check=True, capture_output=True,
    ).stdout
    d = pd.read_parquet(io.BytesIO(blob), columns=["unit_id", "fuel", "klass", "mw"])
    d = d[d["fuel"] == "coal"]
    g = d.groupby("unit_id", observed=True)
    return g["mw"].sum(), g["klass"].first().astype(str)


def measure(year: int) -> dict:
    """Yard-level budget vs the keeper's yard-level coal burn for one year."""
    meta = json.loads((KEEPER / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(KEEPER, year))
    cfg = json.loads((KEEPER / f"run_config_{year}.json").read_text())
    sc = cfg.get("scenario_config", cfg)
    gas = sc.get("gas_price_override", meta.get("gas_price"))
    fa = run_year(year, "MISO", 8760, gas, {}, fleet_only=True, **kw)["fleet_arrays"]

    built = build_coal_plant_budget(fa, year, hours=8760)
    pooled = build_coal_fuel_budget(fa, year, hours=8760)
    gidx, budget, _m, coeff, grp, prov = built
    mwh, klass = keeper_dispatch(year)
    ids = np.asarray(fa.unit_ids, dtype=object)
    unit_mwh = np.array([float(mwh.get(ids[g], 0.0)) for g in gidx])
    burn = np.bincount(grp, weights=coeff * unit_mwh, minlength=budget.shape[0])
    energy = np.bincount(grp, weights=unit_mwh, minlength=budget.shape[0])
    hr_y = np.where(energy > 0, burn / np.maximum(energy, 1e-9), 10.5)
    over = np.clip(burn - budget[:, 0], 0.0, None)
    all_idx = coal_gen_idx(fa)
    all_mwh = sum(float(mwh.get(ids[g], 0.0)) for g in all_idx)
    yards = coal_yard_groups(fa)
    keys = sorted(
        {k for k in yards}, key=lambda k: k
    )
    top = np.argsort(-over)[:8]
    pg = np.array([str(klass.get(ids[g], "COAL")) for g in gidx], dtype=object)
    cls_e: dict[str, np.ndarray] = {}
    for c in sorted(set(pg)):
        cls_e[c] = np.bincount(grp, weights=unit_mwh * (pg == c), minlength=budget.shape[0])
    share = {c: np.where(energy > 0, v / np.maximum(energy, 1e-9), 0.0) for c, v in cls_e.items()}
    excess_by_class = {
        c: round(float((over / hr_y * share[c]).sum()) / 1e6, 3) for c in share
    }
    return {
        "year": year,
        "n_yards_rowed": prov.n_entities,
        "n_gens_rowed": prov.n_generators,
        "n_gens_unrowed": prov.n_unrowed_generators,
        "coal_twh_model": round(all_mwh / 1e6, 3),
        "coal_twh_rowed": round(float(unit_mwh.sum()) / 1e6, 3),
        "yard_budget_twh_eq": round(float(budget.sum() / (burn.sum() / max(unit_mwh.sum(), 1))) / 1e6, 2),
        "pooled_annual_budget_mmbtu": round(float(pooled[1].sum()), 0) if pooled else None,
        "yard_budget_sum_mmbtu": round(float(budget.sum()), 0),
        "model_burn_mmbtu": round(float(burn.sum()), 0),
        "yards_over": int((over > 0).sum()),
        "excess_twh_eq": round(float((over / hr_y).sum()) / 1e6, 3),
        "excess_by_class_twh_eq": excess_by_class,
        "slack_twh_eq_at_unbound_yards": round(float((np.clip(budget[:, 0] - burn, 0, None) / hr_y).sum()) / 1e6, 2),
        "top_yards_twh_eq": [
            {"yard_pos": int(i), "excess_twh": round(float(over[i] / hr_y[i]) / 1e6, 3),
             "model_twh": round(float(energy[i]) / 1e6, 3),
             "budget_twh_eq": round(float(budget[i, 0] / hr_y[i]) / 1e6, 3)}
            for i in top if over[i] > 0
        ],
        "_n_yard_keys": len(keys),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=list(LEG_SHA))
    ap.add_argument("--out", type=Path, default=REPO / "results/calibration/_miso268_plant_grain_phase0.json")
    a = ap.parse_args()
    out = [measure(y) for y in a.years]
    for r in out:
        print(json.dumps({k: v for k, v in r.items() if k != "top_yards_twh_eq"}))
    a.out.write_text(json.dumps(out, indent=1) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
