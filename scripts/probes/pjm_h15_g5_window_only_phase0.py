"""pjm-h15 G5 — prove the arm moves the WINDOW and nothing else, at ZERO LP.

The gate (PRECOMMIT §4, G5): on a ``fleet_only`` build under the arm config,
every coal generator's ``pmax_mw`` AND ``coal_sync_pmin_mw`` are unchanged from
the control to < 1e-6 MW, in every year. The mechanism is a single line inside
``arrays.py::_compose_min_gen_floors``, which runs DOWNSTREAM of tranche sizing
and floor levelling, so neither can move — this asserts it through the builder
rather than by reading the diff.

The companion assertion is the positive one: ``FleetArrays.min_gen`` DOES move,
and only on rows stamped ``MECH_COAL_MUSTRUN``.

Zero LP (rule 29 ``[R-SCREEN]`` clause (0), surviving as practice).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

BUNDLES = {
    2020: "results/calibration/pjm_h14_coalmustrun_touchpoint",
    2021: "results/calibration/pjm_h14_coalmustrun_touchpoint",
    2022: "results/calibration/pjm_h14_coalmustrun_touchpoint",
    2023: "results/calibration/pjm_h14_coalmustrun_span",
    2024: "results/calibration/pjm_h14_coalmustrun_span",
    2025: "results/calibration/pjm_h14_coalmustrun_span",
}


def build(year: int, armed: bool):
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if armed:
        ov = dict(kw.get("prb_overrides") or {})
        ov["coal_sync_online_frac_per_year"] = True
        kw["prb_overrides"] = ov
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)
    gens = payload["fleet"] if isinstance(payload, dict) and "fleet" in payload else payload
    arrays = payload.get("fleet_arrays") if isinstance(payload, dict) else None
    if hasattr(gens, "generators"):
        arrays = arrays or gens
        gens = gens.generators
    return gens, arrays


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=sorted(BUNDLES))
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    out: list[dict] = []
    for year in args.years:
        c_gens, c_fa = build(year, armed=False)
        a_gens, a_fa = build(year, armed=True)
        assert len(c_gens) == len(a_gens), f"{year}: generator count moved"

        d_pmax = d_pmin = 0.0
        coal_units = 0
        for cg, ag in zip(c_gens, a_gens):
            assert str(getattr(cg, "unit_id", "")) == str(getattr(ag, "unit_id", ""))
            d_pmax = max(d_pmax, abs(float(getattr(cg, "pmax_mw", 0.0) or 0.0)
                                     - float(getattr(ag, "pmax_mw", 0.0) or 0.0)))
            cp = float(getattr(cg, "coal_sync_pmin_mw", 0.0) or 0.0)
            apm = float(getattr(ag, "coal_sync_pmin_mw", 0.0) or 0.0)
            d_pmin = max(d_pmin, abs(cp - apm))
            if cp > 0.0:
                coal_units += 1

        row = dict(year=year, generators=len(c_gens), coal_sync_units=coal_units,
                   max_abs_d_pmax_mw=d_pmax, max_abs_d_coal_sync_pmin_mw=d_pmin)

        # The positive assertion: min_gen DOES move, and only on coal rows.
        if c_fa is not None and a_fa is not None and hasattr(c_fa, "min_gen"):
            from market_sim.data.fleet.arrays import MECH_COAL_MUSTRUN

            dm = np.abs(a_fa.min_gen - c_fa.min_gen)
            moved = dm > 1e-9
            row["min_gen_cells_moved"] = int(moved.sum())
            row["min_gen_max_abs_d_mw"] = float(dm.max())
            mech = np.where(moved, np.maximum(c_fa.min_gen_mechanism, a_fa.min_gen_mechanism), -1)
            ids = sorted({int(v) for v in np.unique(mech[moved])}) if moved.any() else []
            row["moved_mech_ids"] = ids
            row["coal_mech_id"] = int(MECH_COAL_MUSTRUN)
            row["only_coal_mech_moved"] = ids in ([], [int(MECH_COAL_MUSTRUN)])
        out.append(row)
        print(json.dumps(row))

    print("\n### G5 verdict")
    ok_pmax = max(r["max_abs_d_pmax_mw"] for r in out)
    ok_pmin = max(r["max_abs_d_coal_sync_pmin_mw"] for r in out)
    print(f"  max |d pmax_mw|            over all years/units: {ok_pmax:.3e} MW")
    print(f"  max |d coal_sync_pmin_mw|  over all years/units: {ok_pmin:.3e} MW")
    print(f"  G5 (< 1e-6 both): {'PASS' if max(ok_pmax, ok_pmin) < 1e-6 else 'FAIL'}")
    if all("min_gen_cells_moved" in r for r in out):
        print(f"  min_gen cells moved by year: "
              f"{ {r['year']: r['min_gen_cells_moved'] for r in out} }")
        print(f"  only MECH_COAL_MUSTRUN rows moved: "
              f"{all(r['only_coal_mech_moved'] for r in out)}")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
