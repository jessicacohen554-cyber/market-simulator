#!/usr/bin/env python3
"""pjm-145 ex-ante ADDENDUM — decompose the measured restore by unit state.

The PREREG §3 instrument measured a +19–24 GW mean-availability RESTORE
(`_pjm145_damavail_exante.json`), concentrated in COAL/ST_GAS — the classes
carrying the model's deep unit-grain derates. This addendum decomposes each
year's restore MW into:

* **structural-zero resurrection** — units whose pre-overlay day-mean
  availability is ~0 (COD-masked mid-year entrants, retiree/layup windows,
  full outage days): the water-fill's ``_flat`` branch lifts them 0 → λ, the
  ERCOT-135 §7.2 "destroyed unit resurrected" defect (whose pmax-ceiling fix
  was applied to the ERCOT plant-grain path only);
* **living-unit lift** — units already partially available lifted
  λ·(1 − ad) toward 1.0.

Same fleet path as the main probe (one control build per year; the arm-side
restore is computed analytically from the water-fill's own algebra: for
restore days ``λ = (t − cur)/(1 − cur)``, per-unit lift = ``λ·(1 − ad)``,
zero-unit lift = ``λ``). No LP.

    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm145_damavail_decompose.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/pjm143_hy_level_B"
OUT_PATH = REPO / "results/calibration/_pjm145_damavail_decompose.json"
YEARS = (2023, 2024, 2025)
ZERO_AD = 1e-9


def main() -> None:
    from market_sim.data.pjm_outages import (
        PJM_OUTAGE_COVERED_GROUPS,
        pjm_dam_availability_series,
    )
    from scripts.probes._pjm145_damavail_exante import _run_year_kwargs
    from scripts.run_calibration import run_year

    meta = json.loads((KEEPER / "meta.json").read_text())
    base_kwargs = _run_year_kwargs(meta)
    gas_prices = meta.get("gas_prices", {})

    out: dict = {}
    for yr in YEARS:
        gas = float(gas_prices.get(str(yr), gas_prices.get(yr, 0.0)))
        state = run_year(yr, "PJM", 8760, gas, {}, fleet_only=True, **dict(base_kwargs))
        fa = state["fleet_arrays"]
        groups = np.array([str(g) for g in fa.plant_group])
        pmax = np.asarray(fa.pmax, dtype=float)
        av = np.asarray(fa.availability, dtype=float)
        n_days = av.shape[1] // 24
        meas = pjm_dam_availability_series(yr)
        yr_rows: dict = {}
        for cls in sorted(PJM_OUTAGE_COVERED_GROUPS):
            idx = np.where(groups == cls)[0]
            if idx.size == 0 or cls not in meas:
                continue
            cap = pmax[idx]
            cap_sum = float(cap.sum())
            ad = av[idx, : n_days * 24].reshape(idx.size, n_days, 24).mean(axis=2)
            t = meas[cls][: n_days * 24].reshape(n_days, 24).mean(axis=1)
            covered = np.isfinite(t)
            cur = (ad * cap[:, None]).sum(axis=0) / cap_sum
            restore = covered & (t >= cur)
            lam = np.clip((t - cur) / np.maximum(1.0 - cur, 1e-9), 0.0, 1.0)
            zero = ad <= ZERO_AD  # (n, days) structural-zero unit-days
            # Restore-day MW decomposition (mean over restore days).
            lift_zero = (zero[:, restore] * cap[:, None] * lam[None, restore]).sum(axis=0)
            lift_live = (
                (~zero[:, restore]) * cap[:, None] * lam[None, restore] * (1.0 - ad[:, restore])
            ).sum(axis=0)
            # Which units are EVER structurally zero on a restore day, and how
            # much capacity do they carry?
            zero_units = zero[:, restore].any(axis=1)
            yr_rows[cls] = {
                "cap_mw": round(cap_sum, 1),
                "restore_days": int(restore.sum()),
                "mean_lift_zero_mw": round(float(lift_zero.mean()), 1) if restore.any() else 0.0,
                "mean_lift_live_mw": round(float(lift_live.mean()), 1) if restore.any() else 0.0,
                "zero_share_of_lift": (
                    round(float(lift_zero.sum() / max(lift_zero.sum() + lift_live.sum(), 1e-9)), 4)
                    if restore.any()
                    else 0.0
                ),
                "units_ever_zero_on_restore_days": int(zero_units.sum()),
                "cap_of_those_units_mw": round(float(cap[zero_units].sum()), 1),
                "n_units": int(idx.size),
                "model_capw_avail_mean": round(float(cur[covered].mean()), 4),
                "target_mean": round(float(t[covered].mean()), 4),
            }
        pooled_zero = sum(r["mean_lift_zero_mw"] for r in yr_rows.values())
        pooled_live = sum(r["mean_lift_live_mw"] for r in yr_rows.values())
        out[str(yr)] = {
            "classes": yr_rows,
            "pooled": {
                "mean_lift_zero_mw": round(pooled_zero, 1),
                "mean_lift_live_mw": round(pooled_live, 1),
                "zero_share_of_lift": round(pooled_zero / max(pooled_zero + pooled_live, 1e-9), 4),
            },
        }
        del state, fa, av
    OUT_PATH.write_text(json.dumps(out, indent=1))
    print(json.dumps({y: out[y]["pooled"] for y in out}, indent=1))
    for y in out:
        for cls, r in out[y]["classes"].items():
            print(
                f"{y} {cls:11s} model {r['model_capw_avail_mean']:.3f} -> t {r['target_mean']:.3f}"
                f" | lift zero/live {r['mean_lift_zero_mw']:8.1f}/{r['mean_lift_live_mw']:8.1f} MW"
                f" | zero-units {r['units_ever_zero_on_restore_days']:4d} ({r['cap_of_those_units_mw']:.0f} MW)"
            )
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
