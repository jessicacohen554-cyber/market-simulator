"""R-ERCOT-17 phase 0 (zero LP): per-year fuel/mc delta of the pooled South-Texas basis.

Rebuilds the designated keeper's fleet for each year (``run_year(fleet_only=True)``
through the sanctioned ``replay_keeper.run_year_kwargs`` path, with the year's own
``config_partition_overrides`` overlay applied) twice — flag off and
``ercot_south_texas_pooled_basis=True`` — and reports, per zone, the gas units'
mean delivered-fuel and mc_base deltas and which rows move. No LP.

Usage: PYTHONPATH=.:src:scripts python3 scripts/probes/_r_ercot17_south_pool_delta.py \
    results/calibration/r_ercot16_span 2019 [2020 ...]
"""

from __future__ import annotations

import copy
import inspect
import json
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [".", "src", "scripts"]

from scripts.lib.bundle_fleet import bundle_gas_price, clear_fleet_caches  # noqa: E402
from scripts.replay_keeper import (  # noqa: E402
    RUN_YEAR_NON_RECIPE,
    RUN_YEAR_REMAP,
    apply_config_overlay,
    build_kwargs,
    config_partition_overlay,
    derived_run_year_inputs,
)
from scripts.run_calibration import run_year  # noqa: E402

FLAG = "ercot_south_texas_pooled_basis"


def _kwargs(meta: dict, year: int, arm: bool) -> dict:
    """Keeper recipe for ``year`` (partition overlay applied), optionally armed."""
    full = build_kwargs(copy.deepcopy(meta))
    apply_config_overlay(full, config_partition_overlay(meta, year))
    if arm:
        full = dict(full)
        full["prb_overrides"] = dict(full.get("prb_overrides") or {})
        full["prb_overrides"][FLAG] = True
    params = set(inspect.signature(run_year).parameters)
    out = {
        RUN_YEAR_REMAP.get(k, k): v
        for k, v in full.items()
        if RUN_YEAR_REMAP.get(k, k) in params
        and RUN_YEAR_REMAP.get(k, k) not in RUN_YEAR_NON_RECIPE
    }
    out["ttc_overrides"] = {}
    out["fleet_only"] = True
    return out


def _state(bundle: Path, meta: dict, year: int, arm: bool) -> dict:
    """One fleet-only rebuild."""
    clear_fleet_caches()
    return run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        bundle_gas_price(meta, year),
        **_kwargs(meta, year, arm),
        **derived_run_year_inputs(bundle, year),
    )


def main() -> None:
    """Report per-year, per-zone gas deltas (arm - keeper)."""
    bundle = Path(sys.argv[1])
    meta = json.loads((bundle / "meta.json").read_text())
    report = {}
    for year in [int(y) for y in sys.argv[2:]]:
        off = _state(bundle, meta, year, False)
        on = _state(bundle, meta, year, True)
        assert getattr(on["config"], FLAG) and not getattr(off["config"], FLAG)
        fa = off["fleet_arrays"]
        ids_off = list(fa.unit_ids)
        assert ids_off == list(on["fleet_arrays"].unit_ids), "row sets differ"
        d_fuel = on["fuel_prices"] - off["fuel_prices"]
        d_mc = on["mc_base"] - off["mc_base"]
        moved = np.nonzero(np.abs(d_mc).max(axis=1) > 1e-9)[0]
        from market_sim.config.iso_configs import get_iso_config

        zn = list(get_iso_config("ERCOT").zone_names)
        yr = {"rows_moved": int(moved.size), "n_rows": len(ids_off), "by_zone": {}}
        tranche = np.array([str(u).rsplit("_", 1)[-1] for u in ids_off], dtype=object)
        for zi, name in enumerate(zn):
            rows = np.nonzero(fa.zone_idx == zi)[0]
            rows_m = np.intersect1d(rows, moved)
            if rows_m.size == 0:
                yr["by_zone"][name] = {"moved": 0}
                continue
            w = fa.pmax[rows_m]
            z = {
                "moved": int(rows_m.size),
                "mw_moved": round(float(w.sum()), 1),
                "fuel_delta_mw_mean": round(
                    float((d_fuel[rows_m].mean(axis=1) * w).sum() / w.sum()), 4
                ),
                "mc_delta_by_tranche_median": {},
            }
            for tr in sorted(set(tranche[rows_m])):
                r = rows_m[tranche[rows_m] == tr]
                z["mc_delta_by_tranche_median"][tr] = [
                    int(r.size),
                    round(float(np.median(d_mc[r].mean(axis=1))), 3),
                ]
            yr["by_zone"][name] = z
        report[year] = yr
        print(json.dumps({year: yr}), flush=True)
    out = Path("docs/handoffs/r-ercot/r_ercot17_south_pool_delta.json")
    prev = json.loads(out.read_text()) if out.exists() else {}
    prev.update({str(k): v for k, v in report.items()})
    out.write_text(json.dumps(prev, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
