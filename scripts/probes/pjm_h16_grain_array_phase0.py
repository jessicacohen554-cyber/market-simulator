"""pjm-h16 G2 + G3 — the floor ARRAY A/B. ZERO LP.

pjm-h15's generalizable lesson, verbatim: *"a bar on another mechanism's D-2
forced energy is a DISPLACEMENT test, not a STACKING test — in absolute TWh
just as much as in share. The only instrument that separates them is the
floor-ARRAY comparison ... A successor should gate scope on the array, not on
D-2."* This is that instrument.

**G2 — WINDOW ONLY.** On a ``fleet_only`` build of the keeper's own recipe with
``coal_sync_window_commitment_grain`` armed, in every year:
  (a) every generator's ``pmax_mw`` and ``coal_sync_pmin_mw`` move by < 1e-6 MW;
  (b) the ONLY mechanism id whose ``min_gen`` cells move is
      ``MECH_COAL_MUSTRUN``.

There is deliberately NO bar on the floored-CELL COUNT (PRECOMMIT §5). The
coal mechanism id is stamped only where the floor RAISES ``min_gen``, so moving
hours legitimately changes which cells the mechanism owns — another floor may
already dominate a peak hour, nothing may occupy a trough hour. A bar on that
count would fail for a reason that is not a defect, which is the
charter-scoping error pjm-h12 and pjm-h15 each made and disclosed. The cell
count and the asserted floor ENERGY are REPORTED, not gated.

**G3 — RULE 18 [R-PHYSICS] THROUGH THE REALIZED ARRAY.** The implied starts of
the armed coal floor array (contiguous binding blocks per generator, summed
fleet-wide) are <= 2.0x the fleet's own metered starts, in every year. This is
NOT the pre-solve day count: the array is clipped by ``pmax*availability`` and
max-composed with every other floor, so a day block can fragment. The bar is
set against the same CAMPD start count phase 0 measured (238 / 290 / 303 / 302
/ 302 / 334 for 2020-2025) and is a genuine bar — the control reads 13.0x-18.3x.

Also REPORTED (no bar, prediction input only): the asserted coal floor ENERGY
change, which pjm-h15 measured as running ~20x ahead of the dispatch response.

Usage:
    python3 scripts/probes/pjm_h16_grain_array_phase0.py --json-out PATH
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
    2020: "results/calibration/pjm_h15_coalwindow_touchpoint",
    2021: "results/calibration/pjm_h15_coalwindow_touchpoint",
    2022: "results/calibration/pjm_h15_coalwindow_touchpoint",
    2023: "results/calibration/pjm_h15_coalwindow_span",
    2024: "results/calibration/pjm_h15_coalwindow_span",
    2025: "results/calibration/pjm_h15_coalwindow_span",
}

# Fleet-wide metered coal starts, from pjm-h16 phase 0 (CAMPD, the 29 covered
# plants, off -> on transitions on the plant's own net series). Frozen here so
# the G3 bar is the number the charter declared and cannot drift.
METERED_STARTS = {2020: 238, 2021: 290, 2022: 303, 2023: 302, 2024: 302, 2025: 334}
G3_BAR = 2.0


def build(year: int, armed: bool):
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if armed:
        ov = dict(kw.get("prb_overrides") or {})
        ov["coal_sync_window_commitment_grain"] = True
        kw["prb_overrides"] = ov
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)
    gens = (
        payload["fleet"]
        if isinstance(payload, dict) and "fleet" in payload
        else payload
    )
    arrays = payload.get("fleet_arrays") if isinstance(payload, dict) else None
    if hasattr(gens, "generators"):
        arrays = arrays or gens
        gens = gens.generators
    return gens, arrays


def block_starts(mask2d: np.ndarray) -> int:
    """Contiguous binding blocks, summed over generators.

    A row's blocks are its off -> on transitions along the hour axis. This is
    the number of synchronizations the floor array ASSERTS, which is what rule
    18 [R-PHYSICS] tests against the meter.
    """
    m = np.asarray(mask2d, dtype=bool)
    if m.size == 0:
        return 0
    first = m[:, :1]
    rise = m[:, 1:] & ~m[:, :-1]
    return int(first.sum() + rise.sum())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=sorted(BUNDLES))
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    from market_sim.data.fleet.arrays import MECH_COAL_MUSTRUN

    out: list[dict] = []
    for year in args.years:
        c_gens, c_fa = build(year, armed=False)
        a_gens, a_fa = build(year, armed=True)
        assert len(c_gens) == len(a_gens), f"{year}: generator count moved"

        d_pmax = d_pmin = 0.0
        coal_units = 0
        for cg, ag in zip(c_gens, a_gens):
            assert str(getattr(cg, "unit_id", "")) == str(getattr(ag, "unit_id", ""))
            d_pmax = max(
                d_pmax,
                abs(
                    float(getattr(cg, "pmax_mw", 0.0) or 0.0)
                    - float(getattr(ag, "pmax_mw", 0.0) or 0.0)
                ),
            )
            cp = float(getattr(cg, "coal_sync_pmin_mw", 0.0) or 0.0)
            apm = float(getattr(ag, "coal_sync_pmin_mw", 0.0) or 0.0)
            d_pmin = max(d_pmin, abs(cp - apm))
            if cp > 0.0:
                coal_units += 1

        row = dict(
            year=year,
            generators=len(c_gens),
            coal_sync_units=coal_units,
            max_abs_d_pmax_mw=d_pmax,
            max_abs_d_coal_sync_pmin_mw=d_pmin,
        )

        dm = np.abs(a_fa.min_gen - c_fa.min_gen)
        moved = dm > 1e-9
        row["min_gen_cells_moved"] = int(moved.sum())
        row["min_gen_max_abs_d_mw"] = float(dm.max())
        mech = np.where(
            moved, np.maximum(c_fa.min_gen_mechanism, a_fa.min_gen_mechanism), -1
        )
        ids = sorted({int(v) for v in np.unique(mech[moved])}) if moved.any() else []
        row["moved_mech_ids"] = ids
        row["only_coal_mech_moved"] = ids in ([], [int(MECH_COAL_MUSTRUN)])

        c_coal = (c_fa.min_gen_mechanism == MECH_COAL_MUSTRUN) & (c_fa.min_gen > 0.0)
        a_coal = (a_fa.min_gen_mechanism == MECH_COAL_MUSTRUN) & (a_fa.min_gen > 0.0)
        row["coal_cells_ctl"] = int(c_coal.sum())
        row["coal_cells_arm"] = int(a_coal.sum())
        row["coal_cells_pct"] = round(
            100.0 * (int(a_coal.sum()) - int(c_coal.sum())) / max(1, int(c_coal.sum())),
            4,
        )
        row["coal_floor_twh_ctl"] = round(float(c_fa.min_gen[c_coal].sum()) / 1e6, 5)
        row["coal_floor_twh_arm"] = round(float(a_fa.min_gen[a_coal].sum()) / 1e6, 5)
        row["coal_floor_pct"] = round(
            100.0
            * (row["coal_floor_twh_arm"] - row["coal_floor_twh_ctl"])
            / max(1e-12, row["coal_floor_twh_ctl"]),
            3,
        )

        row["starts_ctl"] = block_starts(c_coal)
        row["starts_arm"] = block_starts(a_coal)
        row["starts_meter"] = METERED_STARTS[year]
        row["starts_x_ctl"] = round(row["starts_ctl"] / METERED_STARTS[year], 2)
        row["starts_x_arm"] = round(row["starts_arm"] / METERED_STARTS[year], 2)
        out.append(row)
        print(json.dumps(row))

    print("\n### G2 — WINDOW ONLY (pmax / floor level / mechanism scope)")
    g2a = max(
        max(r["max_abs_d_pmax_mw"], r["max_abs_d_coal_sync_pmin_mw"]) for r in out
    )
    g2b = all(r["only_coal_mech_moved"] for r in out)
    print(
        f"  (a) max |d pmax_mw| / |d coal_sync_pmin_mw| : {g2a:.3e} MW  "
        f"(bar < 1e-6)  -> {'PASS' if g2a < 1e-6 else 'FAIL'}"
    )
    print(
        f"  (b) only MECH_COAL_MUSTRUN min_gen cells moved: {g2b}  -> "
        f"{'PASS' if g2b else 'FAIL'}"
    )
    print(f"  G2: {'PASS' if (g2a < 1e-6 and g2b) else 'FAIL'}")
    print("\n  REPORTED, NOT GATED — floored MECH_COAL_MUSTRUN cell count:")
    for r in out:
        print(
            f"    {r['year']}  ctl {r['coal_cells_ctl']:>8}  arm "
            f"{r['coal_cells_arm']:>8}  {r['coal_cells_pct']:+.4f} %"
        )

    print("\n### G3 — RULE 18 [R-PHYSICS]: implied starts of the realized floor array")
    print(f"  {'year':>6} {'meter':>7} {'ctl':>7} {'x':>7} {'arm':>7} {'x':>7}")
    for r in out:
        print(
            f"  {r['year']:>6} {r['starts_meter']:>7} {r['starts_ctl']:>7} "
            f"{r['starts_x_ctl']:>7.2f} {r['starts_arm']:>7} {r['starts_x_arm']:>7.2f}"
        )
    g3 = max(r["starts_x_arm"] for r in out)
    print(
        f"  worst arm multiple: {g3:.2f}x  (bar <= {G3_BAR})  -> "
        f"{'PASS' if g3 <= G3_BAR else 'FAIL'}"
    )

    print("\n### REPORTED ONLY — the asserted coal floor ENERGY footprint")
    print(f"  {'year':>6} {'ctl_TWh':>10} {'arm_TWh':>10} {'pct':>8}")
    for r in out:
        print(
            f"  {r['year']:>6} {r['coal_floor_twh_ctl']:>10.5f} "
            f"{r['coal_floor_twh_arm']:>10.5f} {r['coal_floor_pct']:>8.3f}"
        )

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
