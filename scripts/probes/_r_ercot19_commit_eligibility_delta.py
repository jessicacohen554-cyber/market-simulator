"""R-ERCOT-19 phase 0 (zero LP): delta of the two prior-year commitment-profile sub-gates.

Rebuilds the designated keeper's fleet per year (``run_year(fleet_only=True)``
through ``replay_keeper``'s recipe path, the year's own
``config_partition_overrides`` applied) with
``cc_committed_prior_year_commitment_eligibility`` +
``netload_drag_prior_year_hour_profile`` off vs on, asserts that pmax,
availability, every non-CC-committed ``mc`` row and every non-drag
``min_gen`` row are byte-identical, and reports the CC committed-block mean
bid by plant and each plant's nominal drag-floor energy both ways.

Usage: python scripts/probes/_r_ercot19_commit_eligibility_delta.py results/calibration/r_ercot18_span 2019 ... 2025
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

FLAGS = (
    "cc_committed_prior_year_commitment_eligibility",
    "netload_drag_prior_year_hour_profile",
)


def _state(bundle: Path, meta: dict, year: int, arm: bool) -> dict:
    """One fleet-only rebuild of the keeper recipe, optionally armed."""
    kw = _k17(meta, year, False)
    if arm:
        kw["prb_overrides"] = dict(kw.get("prb_overrides") or {})
        for f in FLAGS:
            kw["prb_overrides"][f] = True
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
    """Report per-year CC committed-bid and drag-floor deltas (off vs on)."""
    bundle = Path(sys.argv[1])
    meta = json.loads((bundle / "meta.json").read_text())
    report = {}
    for year in [int(y) for y in sys.argv[2:]]:
        off, on = _state(bundle, meta, year, False), _state(bundle, meta, year, True)
        for f in FLAGS:
            assert getattr(on["config"], f) and not getattr(off["config"], f)
        fa, fb = off["fleet_arrays"], on["fleet_arrays"]
        assert list(fa.unit_ids) == list(fb.unit_ids), "row sets differ"
        for name in ("pmax", "availability"):
            assert np.array_equal(getattr(fa, name), getattr(fb, name)), name
        gens = off["fleet"]
        ids = list(fa.unit_ids)
        cc = np.array(
            [
                g.plant_group == "CC_REGULAR"
                and str(g.unit_id).rpartition("_")[2].startswith("committed")
                for g in gens
            ]
        )
        assert np.array_equal(off["mc_base"][~cc], on["mc_base"][~cc]), "non-CC mc moved"
        drag = (fa.min_gen_mechanism == MECH_ST_NETLOAD_DRAG).any(axis=1) | (
            fb.min_gen_mechanism == MECH_ST_NETLOAD_DRAG
        ).any(axis=1)
        assert np.array_equal(fa.min_gen[~drag], fb.min_gen[~drag]), "non-drag min_gen moved"
        pc = np.array([int(getattr(g, "plant_code", 0) or 0) for g in gens])
        cc_rows = {}
        for i in np.flatnonzero(cc):
            cc_rows[f"{pc[i]}:{ids[i].rpartition('_')[2]}"] = [
                round(float(off["mc_base"][i].mean()), 3),
                round(float(on["mc_base"][i].mean()), 3),
            ]
        drag_rows = {}
        for p in sorted(set(pc[drag])):
            r = np.flatnonzero(drag & (pc == p))

            def _twh(a, rr=r):
                return round(
                    float(
                        np.where(
                            a.min_gen_mechanism[rr] == MECH_ST_NETLOAD_DRAG,
                            a.min_gen[rr],
                            0,
                        ).sum()
                    )
                    / 1e6,
                    4,
                )

            drag_rows[str(p)] = [_twh(fa), _twh(fb)]
        report[year] = {
            "cc_committed_mean_bid_off_on": cc_rows,
            "drag_floor_twh_off_on": drag_rows,
            "mc_byte_identical": bool(np.array_equal(off["mc_base"], on["mc_base"])),
            "min_gen_byte_identical": bool(np.array_equal(fa.min_gen, fb.min_gen)),
        }
        print(
            json.dumps(
                {
                    year: {
                        k: v
                        for k, v in report[year].items()
                        if k.endswith("identical")
                    }
                }
            ),
            flush=True,
        )
    out = Path("docs/records/ercot/r-ercot/r_ercot19_commit_eligibility_delta.json")
    prev = json.loads(out.read_text()) if out.exists() else {}
    prev.update({str(k): v for k, v in report.items()})
    out.write_text(json.dumps(prev, indent=1, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
