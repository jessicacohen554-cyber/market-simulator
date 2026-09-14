"""spp-42 phase 0 (ZERO LP): what selects the ST_GAS must-run floor's HOURS.

Card R-be's open half. Keeper 11 (`2026-09-13-spp-38-vintage-cache`) fails
D-4 off-window binding on 10 rows, every one ``st_gas_mustrun_per_plant`` x
ST_GAS, on plants 1230 / 1235 / 1271 / 3008: the floor forces the plant in
hours its own CEMS record says it was OFF. Rule 17 ``[R-FLOOR-WINDOW]`` makes
that a bug by definition, so this probe measures the SELECTION, never a
residual.

What it does, with NO solve:

* rebuilds keeper 11's own fleet on its own recipe through the sanctioned
  ``replay_keeper.run_year_kwargs`` + ``derived_run_year_inputs`` path
  (``run_year(..., fleet_only=True)``) and reads ``fleet_arrays.min_gen`` +
  ``min_gen_mechanism`` -- the floor array the LP is actually handed;
* puts each floored ST_GAS plant's floor mask beside the SAME measured series
  the D-4 rider reads (``frontend/data/backcast/bench/SPP/<year>.json.gz``,
  plant-level view), and reports the 2x2 confusion matrix
  floored^running / floored^off / unfloored^running / unfloored^off;
* decomposes the miss into its DAY half and its HOUR-OF-DAY half, because the
  keeper arms ``mustrun_window_commitment_grain`` (whole operating days ranked
  by day-mean system load) and the two halves have different repairs;
* reproduces the ``ct_only`` guard from the bench itself for every plant, so
  the four failures are confirmed to be plants the benchmark DOES trust.

Run: ``uv run python scripts/probes/_spp42_floor_hour_selection_phase0.py``
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

# Keeper 11 (2023-2025) and the SPP-40 holdout replay (2019-2022) carry the
# SAME recipe (spp-41 phase 0 diffed the two metas); a year drawn from either
# is the same configuration.
BUNDLES = {
    2019: "results/calibration/spp40_holdout",
    2020: "results/calibration/spp40_holdout",
    2021: "results/calibration/spp40_holdout",
    2022: "results/calibration/spp40_holdout",
    2023: "results/calibration/spp38_span",
    2024: "results/calibration/spp38_span",
    2025: "results/calibration/spp38_span",
}

MECH_ST_GAS = "st_gas_mustrun"  # resolved from floor_mechanisms at import time


def build(year: int) -> dict:
    """Build (or load) the per-row floor table for one year."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"floor_{year}.npz"
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
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)

    fa = payload["fleet_arrays"]
    fleet = payload["fleet"]
    min_gen = np.asarray(fa.min_gen, dtype=float)
    mech = np.asarray(fa.min_gen_mechanism)

    plant = np.array(
        [int(getattr(u, "plant_code", 0) or 0) for u in fleet], dtype=int
    )
    group = np.array(
        [str(getattr(u, "plant_group", "") or "") for u in fleet], dtype=object
    )
    pmax = np.asarray(fa.pmax, dtype=float)
    avail = np.asarray(fa.availability, dtype=float)

    st = group == "ST_GAS"
    codes = sorted({int(c) for c in plant[st] if c})
    n_h = min_gen.shape[1]
    floor_mw = np.zeros((len(codes), n_h), dtype=np.float32)
    cap_mw = np.zeros((len(codes), n_h), dtype=np.float32)
    for i, c in enumerate(codes):
        rows = np.flatnonzero(st & (plant == c))
        sel = mech[rows] == MECH_ST_GAS_MUSTRUN_PER_PLANT
        floor_mw[i] = np.where(sel, min_gen[rows], 0.0).sum(axis=0)
        cap_mw[i] = (pmax[rows, None] * avail[rows]).sum(axis=0)

    load = payload.get("demand")
    if load is None:
        load = payload.get("load_shape")
    sys_load = (
        np.asarray(load, dtype=float).sum(axis=0)
        if load is not None and np.ndim(load) == 2
        else (np.asarray(load, dtype=float) if load is not None else np.zeros(n_h))
    )

    out = {
        "year": np.array(year),
        "codes": np.asarray(codes, dtype=int),
        "floor_mw": floor_mw,
        "cap_mw": cap_mw,
        "sys_load": sys_load.astype(np.float32),
    }
    np.savez_compressed(path, **out)
    return out


def bench(year: int) -> dict[str, dict]:
    """The plant-level measured view the D-4 rider itself reads."""
    from scripts.legitimacy_diagnostics import bench_plant_view, load_bench

    return bench_plant_view(load_bench(REPO, "SPP", year))


def main() -> None:
    years = [int(a) for a in sys.argv[1:]] or [2023, 2024, 2025]
    report: dict[str, dict] = {}
    for year in years:
        f = build(year)
        b = bench(year)
        codes = [int(c) for c in f["codes"]]
        floor = f["floor_mw"]
        sys_load = np.asarray(f["sys_load"], dtype=float)
        n_h = floor.shape[1]
        day = np.arange(n_h) // 24
        hod = np.arange(n_h) % 24
        n_days = n_h // 24

        print(f"\n{'=' * 100}\n{year}   (SPP, keeper 11 recipe, fleet_only)\n{'=' * 100}")
        hdr = (
            f"{'plant':>6} {'ct_only':>7} {'flr_h':>6} {'on_h':>6} "
            f"{'F&on':>6} {'F&off':>6} {'U&on':>6} {'U&off':>6} "
            f"{'prec':>6} {'recall':>6} {'F&off%':>7} {'medF':>7}"
        )
        print(hdr)
        rows = []
        for i, c in enumerate(codes):
            fl = floor[i] > 0.0
            if not fl.any():
                continue
            rec = b.get(str(c))
            if rec is None:
                print(f"{c:>6} {'NOMETER':>7}")
                continue
            meas = np.asarray(rec["mw"], dtype=float)[:n_h]
            if meas.size < n_h:
                print(f"{c:>6} {'SHORT':>7}")
                continue
            on = meas > 0.0
            f_on = int((fl & on).sum())
            f_off = int((fl & ~on).sum())
            u_on = int((~fl & on).sum())
            u_off = int((~fl & ~on).sum())
            prec = f_on / max(1, f_on + f_off)
            rec_ = f_on / max(1, f_on + u_on)
            med_f = float(np.median(meas[fl]))
            print(
                f"{c:>6} {str(bool(rec.get('ct_only'))):>7} {int(fl.sum()):>6} "
                f"{int(on.sum()):>6} {f_on:>6} {f_off:>6} {u_on:>6} {u_off:>6} "
                f"{prec:>6.3f} {rec_:>6.3f} {f_off / max(1, int(fl.sum())):>7.3f} "
                f"{med_f:>7.1f}"
            )
            # DAY vs HOUR-OF-DAY decomposition.
            fl_d = fl.reshape(n_days, 24).any(axis=1)
            on_d = on.reshape(n_days, 24).any(axis=1)
            day_prec = float((fl_d & on_d).sum() / max(1, fl_d.sum()))
            # within a floored day that the plant DID run: how much of the
            # day's floored hours fall in hours the plant was actually on.
            both = fl_d & on_d
            if both.any():
                fl_hh = fl.reshape(n_days, 24)[both]
                on_hh = on.reshape(n_days, 24)[both]
                inday = float((fl_hh & on_hh).sum() / max(1, fl_hh.sum()))
            else:
                inday = float("nan")
            rows.append(
                {
                    "plant": c,
                    "ct_only": bool(rec.get("ct_only")),
                    "floored_h": int(fl.sum()),
                    "measured_on_h": int(on.sum()),
                    "F_on": f_on,
                    "F_off": f_off,
                    "U_on": u_on,
                    "U_off": u_off,
                    "precision": round(prec, 4),
                    "recall": round(rec_, 4),
                    "median_meas_over_floored": round(med_f, 3),
                    "day_precision": round(day_prec, 4),
                    "within_day_precision": (
                        None if inday != inday else round(inday, 4)
                    ),
                    "floored_days": int(fl_d.sum()),
                    "measured_on_days": int(on_d.sum()),
                    "mean_on_h_per_on_day": round(
                        float(on.reshape(n_days, 24).sum(axis=1)[on_d].mean())
                        if on_d.any()
                        else 0.0,
                        2,
                    ),
                    "floor_hod_hist": on.reshape(n_days, 24)[fl_d].mean(axis=0).round(3).tolist(),
                }
            )
        report[str(year)] = {
            "rows": rows,
            "sys_load_day_rank_top": np.argsort(
                -sys_load[: n_days * 24].reshape(n_days, 24).mean(axis=1), kind="stable"
            )[:20].tolist(),
        }
        del hod, day
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / "phase0.json").write_text(json.dumps(report, indent=1))
    print(f"\nwrote {CACHE / 'phase0.json'}")


if __name__ == "__main__":
    main()
