"""miso-220 S-1/S-2 liveness — the arm lifts exactly the non-steam fossil bands.

Zero-solve. Assembles the keeper's own fleet THREE ways per year and checks the
three properties the PREREG freezes BEFORE the solve:

* **S-1 (the baseline identity, and the one that can void the arm).** The keeper's
  ``run_config`` carries an ``offer_curve_by_group`` with a SINGLE entry
  (``ST_GAS_INTERMEDIATE``); every other class resolves from the per-ISO curves
  ``backcast_config`` merges in. The arm must pass a FULL explicit table through
  ``--set``, so the arm is a single delta ONLY IF the explicit table's unlifted
  half reproduces the keeper's implicit resolution EXACTLY. This probe builds the
  full baseline table and asserts ``mc`` is byte-identical to the keeper's own
  construction. **A non-zero diff here voids the arm before any LP is spent** —
  it would mean the table carries an undeclared second delta.
* **S-2 (liveness and scope).** Turning the lift on moves ``mc`` on the
  non-steam fossil tranches and NOWHERE else. ``ST_GAS`` and
  ``ST_GAS_INTERMEDIATE`` tranches are byte-identical across the arm, per the
  owner's 2026-09-05 ruling; ``phys_*`` keys and the structural shares
  (``econ_low_share``, ``pct_peaking``) are untouched in every class.
* **S-3 (merit-order effect, reported not gated).** The owner's ruling names
  merit-order adjustment as an intended effect, so the probe MEASURES the
  reordering rather than treating it as a defect: how many (class, band) pairs
  change rank against ST_GAS, and the resulting offer gap.

Record: ``results/calibration/_miso220_liveness.json``. Rule 22 — 2023/2024/2025
only. No LP is solved.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

KEEPER = REPO / "results/calibration/miso217_intermphys_B"
_m134.BUNDLE = KEEPER

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso214_ct_peaker_conduct_phase0 import _band, _r  # noqa: E402
from _miso220_offer_table import ARM_TABLE, BASELINE_TABLE, HELD_CLASSES, LIFT  # noqa: E402

OUT = REPO / "results/calibration/_miso220_liveness.json"
YEARS = tuple(int(v) for v in os.environ.get("MISO220_YEARS", "2023,2024,2025").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
EPS = 1e-9


def _mc_for(table: dict | None, year: int):
    """Build the keeper's fleet with ``table`` as ``offer_curve_by_group`` (None = as-is)."""
    cfg = keeper_config()
    if table is not None:
        cfg = dataclasses.replace(cfg, offer_curve_by_group=table)
    _, fleet, arrays, _, mc, _ = build_year(cfg, year)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    band = np.array([_band(g.unit_id) for g in fleet])
    pmax = np.asarray(arrays.pmax, float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    return mc, klass, band, pmax


def analyse(year: int) -> dict:
    """S-1 baseline identity, S-2 liveness/scope and S-3 merit reordering for one year."""
    mc_keep, klass, band, pmax = _mc_for(None, year)
    mc_base, klass_b, _, _ = _mc_for(BASELINE_TABLE, year)
    mc_arm, klass_a, band_a, pmax_a = _mc_for(ARM_TABLE, year)

    assert klass.tolist() == klass_b.tolist() == klass_a.tolist(), "tranche set moved"

    # ---- S-1: the explicit baseline table must reproduce the keeper exactly
    d1 = np.abs(mc_base - mc_keep)
    s1_max = float(d1.max())
    s1_rows = int((d1.max(axis=1) > EPS).sum())
    s1_by_class = {
        str(k): _r(float(d1[klass == k].max()), 12)
        for k in sorted(set(klass))
        if float(d1[klass == k].max()) > EPS
    }

    # ---- S-2: the lift moves exactly the non-steam fossil tranches
    d2 = np.abs(mc_arm - mc_base)
    moved = d2.max(axis=1) > EPS
    held = np.isin(klass, list(HELD_CLASSES))
    covered = np.isin(klass, list(ARM_TABLE))
    return_ = {
        "year": year,
        "n_tranches": int(klass.size),
        "S1_baseline_identity": {
            "max_abs_mc_diff": _r(s1_max, 12),
            "tranches_differing": s1_rows,
            "by_class": s1_by_class,
            "PASS": bool(s1_max <= EPS),
        },
        "S2_liveness_scope": {
            "tranches_moved": int(moved.sum()),
            "held_class_tranches": int(held.sum()),
            "held_tranches_moved": int((moved & held).sum()),
            "moved_outside_covered_classes": int((moved & ~covered).sum()),
            "max_move_on_held_usd": _r(float(d2[held].max()) if held.any() else 0.0, 12),
            "moved_cap_mw": _r(float(pmax[moved].sum()), 1),
            "PASS": bool((moved & held).sum() == 0 and (moved & ~covered).sum() == 0
                         and moved.sum() > 0),
        },
        "by_class": {},
    }
    for k in sorted(set(klass)):
        sel = klass == k
        if not sel.any():
            continue
        cap = float(pmax[sel].sum())
        return_["by_class"][str(k)] = {
            "held": bool(k in HELD_CLASSES),
            "cap_mw": _r(cap, 1),
            "tranches": int(sel.sum()),
            "tranches_moved": int((moved & sel).sum()),
            "cap_w_mc_base_usd": _r(float((mc_base[sel].mean(axis=1) * pmax[sel]).sum()
                                          / max(cap, EPS)), 3),
            "cap_w_mc_arm_usd": _r(float((mc_arm[sel].mean(axis=1) * pmax[sel]).sum()
                                         / max(cap, EPS)), 3),
        }

    # ---- S-3: measured merit reordering against the held steam-gas classes
    h = 8760 // 2
    st = np.isin(klass, ["ST_GAS", "ST_GAS_INTERMEDIATE"])
    if st.any():
        st_med = float(np.median(mc_base[st, h]))
        below_before = int(((mc_base[:, h] < st_med) & ~st).sum())
        below_after = int(((mc_arm[:, h] < st_med) & ~st).sum())
        return_["S3_merit_reordering_midyear_hour"] = {
            "hour": h,
            "steam_gas_median_mc_usd": _r(st_med, 3),
            "non_steam_tranches_below_steam_before": below_before,
            "non_steam_tranches_below_steam_after": below_after,
            "net_tranches_crossing_above_steam": below_before - below_after,
            "note": "reordering is an INTENDED effect under the owner's 2026-09-05 ruling; measured, not gated",
        }
    del mc_keep, mc_base, mc_arm
    gc.collect()
    return return_


def main() -> int:
    """Run every requested year and write the record; exit non-zero if a gate fails."""
    rec = {
        "probe": "miso-220 S-1/S-2 liveness - the non-steam fossil x1.10 lift",
        "keeper": "2026-09-05-miso-217-intermphys",
        "bundle": str(KEEPER.relative_to(REPO)),
        "solved": False,
        "lift": LIFT,
        "held_classes": sorted(HELD_CLASSES),
        "owner_ruling_2026_09_05": (
            "offer-curve multipliers are the intended channel for tuning on price and "
            "adjusting merit order; one config across 2023-2025; steam gas held as is"
        ),
        "by_year": {},
    }
    ok = True
    for y in YEARS:
        r = analyse(y)
        rec["by_year"][str(y)] = r
        ok &= r["S1_baseline_identity"]["PASS"] and r["S2_liveness_scope"]["PASS"]
        print(f"  {y}: S1 {'PASS' if r['S1_baseline_identity']['PASS'] else 'FAIL'} "
              f"(max diff {r['S1_baseline_identity']['max_abs_mc_diff']}), "
              f"S2 {'PASS' if r['S2_liveness_scope']['PASS'] else 'FAIL'} "
              f"({r['S2_liveness_scope']['tranches_moved']} moved, "
              f"{r['S2_liveness_scope']['held_tranches_moved']} held moved)", flush=True)
    rec["ALL_PASS"] = bool(ok)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}  ALL_PASS={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
