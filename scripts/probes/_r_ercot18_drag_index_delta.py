"""R-ERCOT-18 phase 0 (zero LP): drag-floor allocation delta of the prior-year index.

Rebuilds the designated keeper's fleet for each year (``run_year(fleet_only=True)``
through the sanctioned ``replay_keeper.run_year_kwargs`` path, the year's own
``config_partition_overrides`` applied) with ``netload_drag_prior_year_commitment_index``
off vs on, asserts that every LP input other than the drag rows' ``min_gen`` is
byte-identical, and reports each plant's nominal drag-floor energy both ways.

Usage: python scripts/probes/_r_ercot18_drag_index_delta.py results/calibration/r_ercot17_span 2019 ... 2025
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path[:0] = [".", "src", "scripts"]

from scripts.probes._r_ercot17_south_pool_delta import _kwargs as _k17  # noqa: E402
from scripts.lib.bundle_fleet import bundle_gas_price, clear_fleet_caches  # noqa: E402
from scripts.replay_keeper import derived_run_year_inputs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402

from market_sim.data.floor_mechanisms import MECH_ST_NETLOAD_DRAG  # noqa: E402

FLAG = "netload_drag_prior_year_commitment_index"


def _state(bundle: Path, meta: dict, year: int, arm: bool) -> dict:
    """One fleet-only rebuild of the keeper recipe, optionally armed."""
    kw = _k17(meta, year, False)
    if arm:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        kw["prb_overrides"][FLAG] = True
    clear_fleet_caches()
    return run_year(
        year,
        meta["iso"],
        int(meta["hours"]),
        bundle_gas_price(meta, year),
        **kw,
        **derived_run_year_inputs(bundle, year),
    )


def main() -> None:
    """Report per-year, per-plant nominal drag-floor TWh (off vs on)."""
    bundle = Path(sys.argv[1])
    meta = json.loads((bundle / "meta.json").read_text())
    report = {}
    for year in [int(y) for y in sys.argv[2:]]:
        off, on = _state(bundle, meta, year, False), _state(bundle, meta, year, True)
        assert getattr(on["config"], FLAG) and not getattr(off["config"], FLAG)
        fa, fb = off["fleet_arrays"], on["fleet_arrays"]
        assert list(fa.unit_ids) == list(fb.unit_ids), "row sets differ"
        for name in ("pmax", "availability"):
            assert np.array_equal(getattr(fa, name), getattr(fb, name)), name
        assert np.array_equal(off["mc_base"], on["mc_base"]), "mc moved"
        drag_a = (fa.min_gen_mechanism == MECH_ST_NETLOAD_DRAG).any(axis=1)
        drag_b = (fb.min_gen_mechanism == MECH_ST_NETLOAD_DRAG).any(axis=1)
        other = ~(drag_a | drag_b)
        assert np.array_equal(fa.min_gen[other], fb.min_gen[other]), (
            "non-drag min_gen moved"
        )
        pc = np.array([int(getattr(g, "plant_code", 0) or 0) for g in off["fleet"]])
        rows = np.flatnonzero(drag_a | drag_b)
        yr = {}
        for p in sorted(set(pc[rows])):
            r = rows[pc[rows] == p]
            a = (
                float(
                    np.where(
                        fa.min_gen_mechanism[r] == MECH_ST_NETLOAD_DRAG,
                        fa.min_gen[r],
                        0,
                    ).sum()
                )
                / 1e6
            )
            b = (
                float(
                    np.where(
                        fb.min_gen_mechanism[r] == MECH_ST_NETLOAD_DRAG,
                        fb.min_gen[r],
                        0,
                    ).sum()
                )
                / 1e6
            )
            yr[str(p)] = [round(a, 4), round(b, 4)]
        tot = [
            round(sum(v[0] for v in yr.values()), 4),
            round(sum(v[1] for v in yr.values()), 4),
        ]
        report[year] = {
            "plants_off_on_twh": yr,
            "total_off_on_twh": tot,
            "byte_identical": bool(np.array_equal(fa.min_gen, fb.min_gen)),
        }
        print(json.dumps({year: report[year]}), flush=True)
    out = Path("docs/handoffs/r-ercot/r_ercot18_drag_index_delta.json")
    prev = json.loads(out.read_text()) if out.exists() else {}
    prev.update({str(k): v for k, v in report.items()})
    out.write_text(json.dumps(prev, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
