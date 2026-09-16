"""spp-42 phase 0b (ZERO LP): does the measured LAY-UP record reach card R-be?

Companion to ``_spp42_floor_hour_selection_phase0.py``, which established that
``st_gas_mustrun_per_plant`` selects its hours by SYSTEM LOAD alone (top
``round(online_frac x 8760 / 24)`` whole days by day-mean load, identical
ranking for every plant; the plant's own record enters only through the COUNT
and the LEVEL) and that the four D-4 conduct failures split into a day-selection
miss (1230 / 1235 / 1271) and a within-day miss (3008).

This probe asks the rule-19 ``[R-ONE-MECH]`` question BEFORE any new mechanism
is proposed: the repo already carries ``mustrun_layup_window_mask`` (miso-173),
an EXISTING registered gate that subtracts the merit-order guard's measured
ECONOMIC LAY-UP share from the same floor's clip basis, with zero free
parameters and a committed SPP artifact
(``data/raw/campd-unit-outages-layup-SPP.csv``). Its SPP matrix cell is ``U``.

Measured here, with NO solve:

* the share of each failing plant's FLOORED-and-METERED-OFF hours that fall
  inside a detected lay-up window -- i.e. how much of card R-be the existing
  mechanism can even reach;
* the arm's floor array itself, rebuilt through the engine
  (``run_year(..., fleet_only=True)`` with ``mustrun_layup_window_mask`` added
  to the keeper's own override bag), so the delta is the engine's, not a
  re-implementation;
* the post-arm confusion matrix and median-over-floored-hours per plant, the
  pre-solve analogue of the D-4 rider's own statistic.

Run: ``uv run python scripts/probes/_spp42_layup_mask_phase0.py [years...]``
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

CACHE = Path(
    os.environ.get(
        "SPP42_CACHE",
        "/tmp/claude-0/-home-user-market-simulator/"
        "baa9bd1c-89bc-57a5-980d-a3cfad6ae39a/scratchpad/spp42",
    )
)

BUNDLES = {
    2019: "results/calibration/spp40_holdout",
    2020: "results/calibration/spp40_holdout",
    2021: "results/calibration/spp40_holdout",
    2022: "results/calibration/spp40_holdout",
    2023: "results/calibration/spp38_span",
    2024: "results/calibration/spp38_span",
    2025: "results/calibration/spp38_span",
}

FAILING = (1230, 1235, 1271, 3008)


def floors(year: int, arm: bool) -> dict:
    """Build (or load) the per-plant ST_GAS floor array for one year/leg."""
    CACHE.mkdir(parents=True, exist_ok=True)
    tag = "arm" if arm else "ctl"
    path = CACHE / f"layup_{tag}_{year}.npz"
    if path.exists():
        z = np.load(path, allow_pickle=True)
        return {k: z[k] for k in z.files}

    from market_sim.data.floor_mechanisms import MECH_ST_GAS_MUSTRUN_PER_PLANT
    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = Path(BUNDLES[year])
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    if arm:
        # The keeper's own generic override bag (meta ``coal_prb_sigmoid_overrides``
        # -> run_year ``prb_overrides``) is where its three structural gates
        # already live; adding the mask there is exactly how the solve would
        # receive it. EXACTLY ONE key changes.
        ov = dict(kw.get("prb_overrides") or {})
        ov["mustrun_layup_window_mask"] = True
        kw["prb_overrides"] = ov
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)

    fa = payload["fleet_arrays"]
    fleet = payload["fleet"]
    min_gen = np.asarray(fa.min_gen, dtype=float)
    mech = np.asarray(fa.min_gen_mechanism)
    plant = np.array([int(getattr(u, "plant_code", 0) or 0) for u in fleet], dtype=int)
    group = np.array(
        [str(getattr(u, "plant_group", "") or "") for u in fleet], dtype=object
    )
    st = group == "ST_GAS"
    codes = sorted({int(c) for c in plant[st] if c})
    n_h = min_gen.shape[1]
    floor_mw = np.zeros((len(codes), n_h), dtype=np.float32)
    for i, c in enumerate(codes):
        rows = np.flatnonzero(st & (plant == c))
        sel = mech[rows] == MECH_ST_GAS_MUSTRUN_PER_PLANT
        floor_mw[i] = np.where(sel, min_gen[rows], 0.0).sum(axis=0)
    out = {
        "year": np.array(year),
        "codes": np.asarray(codes, dtype=int),
        "floor_mw": floor_mw,
    }
    np.savez_compressed(path, **out)
    return out


def layup_shares(year: int) -> dict:
    """The engine's own lay-up share series, on the keeper's flag settings."""
    from market_sim.config.paths import CAMPD_BINS_CSV
    from market_sim.data.outages import unit_layup_removed_fractions

    meta = json.loads((Path(BUNDLES[year]) / "meta.json").read_text())
    return unit_layup_removed_fractions(
        year,
        8760,
        str(CAMPD_BINS_CSV),
        iso="SPP",
        cc_steam_part_reclass=False,
        cc_nameplate_basis=bool(meta.get("unit_outage_lp_capacity_basis", False)),
        st_capacity_basis=bool(meta.get("unit_outage_st_capacity_basis", False)),
        per_unit_clip=bool(meta.get("unit_outage_per_unit_clip", False)),
        extract_basis_share=False,
    )


def main() -> None:
    from scripts.legitimacy_diagnostics import bench_plant_view, load_bench

    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    report: dict[str, list] = {}
    for year in years:
        ctl = floors(year, arm=False)
        arm = floors(year, arm=True)
        lay = layup_shares(year)
        b = bench_plant_view(load_bench(REPO, "SPP", year))
        codes = [int(c) for c in ctl["codes"]]
        n_h = ctl["floor_mw"].shape[1]

        print(f"\n{'=' * 118}\n{year}   mustrun_layup_window_mask: control vs arm "
              f"(SPP, keeper 11 recipe, fleet_only, ZERO LP)\n{'=' * 118}")
        print(
            f"{'plant':>6} {'lay_h':>6} | {'C.flr':>6} {'C.F&on':>7} {'C.F&off':>7} "
            f"{'C.prec':>7} {'C.med':>7} | {'A.flr':>6} {'A.F&on':>7} {'A.F&off':>7} "
            f"{'A.prec':>7} {'A.med':>7} | {'dTWh':>8} {'off_in_lay':>10}"
        )
        rows = []
        for i, c in enumerate(codes):
            fc = ctl["floor_mw"][i] > 0.0
            fa_ = arm["floor_mw"][i] > 0.0
            if not fc.any():
                continue
            rec = b.get(str(c))
            if rec is None:
                continue
            meas = np.asarray(rec["mw"], dtype=float)[:n_h]
            if meas.size < n_h:
                continue
            on = meas > 0.0
            sh = lay.get((c, "ST_GAS"))
            lay_h = int((np.asarray(sh) > 0).sum()) if sh is not None else 0
            off_fl = fc & ~on
            off_in_lay = (
                float((off_fl & (np.asarray(sh) > 0)).sum() / max(1, off_fl.sum()))
                if sh is not None
                else 0.0
            )
            cp = int((fc & on).sum()) / max(1, int(fc.sum()))
            ap = int((fa_ & on).sum()) / max(1, int(fa_.sum()))
            cm = float(np.median(meas[fc])) if fc.any() else float("nan")
            am = float(np.median(meas[fa_])) if fa_.any() else float("nan")
            d_twh = float(
                (arm["floor_mw"][i].sum() - ctl["floor_mw"][i].sum()) / 1e6
            )
            star = "*" if c in FAILING else " "
            print(
                f"{c:>5}{star} {lay_h:>6} | {int(fc.sum()):>6} {int((fc & on).sum()):>7} "
                f"{int(off_fl.sum()):>7} {cp:>7.3f} {cm:>7.1f} | "
                f"{int(fa_.sum()):>6} {int((fa_ & on).sum()):>7} "
                f"{int((fa_ & ~on).sum()):>7} {ap:>7.3f} {am:>7.1f} | "
                f"{d_twh:>8.4f} {off_in_lay:>10.3f}"
            )
            rows.append(
                {
                    "plant": c,
                    "failing": c in FAILING,
                    "layup_hours": lay_h,
                    "ctl_floored_h": int(fc.sum()),
                    "ctl_precision": round(cp, 4),
                    "ctl_median_over_floored": round(cm, 3),
                    "arm_floored_h": int(fa_.sum()),
                    "arm_precision": round(ap, 4),
                    "arm_median_over_floored": round(am, 3),
                    "delta_floor_twh": round(d_twh, 6),
                    "offhours_inside_layup_share": round(off_in_lay, 4),
                }
            )
        tot_c = float(ctl["floor_mw"].sum() / 1e6)
        tot_a = float(arm["floor_mw"].sum() / 1e6)
        print(
            f"\nST_GAS floor energy (placed, pre-solve): control {tot_c:.4f} TWh -> "
            f"arm {tot_a:.4f} TWh  ({tot_a - tot_c:+.4f}, "
            f"{100 * (tot_a - tot_c) / max(1e-9, tot_c):+.2f} %)"
        )
        report[str(year)] = rows
    (CACHE / "phase0_layup.json").write_text(json.dumps(report, indent=1))
    print(f"\nwrote {CACHE / 'phase0_layup.json'}")


if __name__ == "__main__":
    main()
