"""caiso-246 — G-STRUCT + price-leg envelope for ``caiso_citygate_spot_coverage``. ZERO LP.

Pre-registered in ``PRECOMMIT-caiso246-spot-coverage-2026-09-04.md`` §1.
Rebuilds the keeper recipe ON-RECIPE (``replay_keeper.run_year_kwargs``) twice
per year — flag OFF (the keeper) and flag ON (the arm) — and diffs the
delivered fuel-price and assembled-offer arrays cell by cell:

  G-STRUCT  only gas rows move, only in months the survey left uncovered
            (2025: Sep/Oct/Nov), ZERO rows in 2023 and 2024; the Nov-2025
            capacity-weighted CA gas price and plant 55077's own November row
            are reported;
  envelope  the caiso-243 price-leg envelope (``_caiso243_price_envelope
            .envelope``: lower limb = every live-month zone-hour where the
            keeper's price exceeds the cheapest repriced tranche's NEW offer
            falls to it; upper limb = the largest positive offer move),
            computed on the arm's ``mc_base`` against the CURRENT keeper's
            committed zonal duals — registered as the G-C3a envelope leg.

Writes ``results/calibration/_caiso246_coverage_footprint.json``; caches both
variants' arrays under ``$C246_CACHE`` (scratch) in the caiso-243 npz schema.

Usage:
    PYTHONPATH=.:src uv run python scripts/probes/_caiso246_coverage_footprint.py
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

BUNDLE = REPO / "results/calibration/caiso243_b1_f923_fallback_guard"
OUT = REPO / "results/calibration/_caiso246_coverage_footprint.json"
CACHE = Path(os.environ.get("C246_CACHE", "/tmp/c246_cache"))
YEARS = (2023, 2024, 2025)
HOURS = 8760
GAS_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_OF_HOUR = np.concatenate([np.full(d * 24, m) for m, d in enumerate(_DAYS)])[:HOURS]
D3_PLANT = 55077


def rebuild(year: int, coverage: bool) -> dict:
    """On-recipe fleet-only rebuild with the flag OFF (keeper) or ON (arm)."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.model.interchange.caiso import split_caiso_import_node_per_hub
    from run_calibration import run_year
    from replay_keeper import run_year_kwargs
    from scripts.lib.bundle_fleet import clear_fleet_caches
    from market_sim.data.fuel import hubs as _hubs

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs = run_year_kwargs(meta)
    kwargs["caiso_citygate_spot_coverage"] = coverage
    clear_fleet_caches()
    # the daily-print cache is keyed by path and the overlay reads it per call;
    # nothing to clear, but the monthly cache must not carry a stale year
    for name in dir(_hubs):
        fn = getattr(_hubs, name, None)
        if callable(fn) and hasattr(fn, "cache_clear"):
            fn.cache_clear()
    buf = io.StringIO()
    with contextlib.redirect_stderr(buf):
        st = run_year(
            year, meta["iso"], HOURS, float(meta["gas_prices"][str(year)]), {}, fleet_only=True, **kwargs
        )
    fa = st["fleet_arrays"]
    gens = st.get("fleet") or []
    fp = np.asarray(st["fuel_prices"], dtype=float)
    if fp.ndim == 1:
        fp = np.tile(fp[:, None], (1, HOURS))
    mc = np.asarray(st["mc_base"], dtype=float)
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    zone_names = list(split_caiso_import_node_per_hub(get_iso_config("CAISO")).zone_names)
    out = {
        "fuel": fp,
        "mc": mc,
        "pmax": np.asarray(fa.pmax, float),
        "heat_rate": np.asarray(fa.heat_rate, float),
        "plant_code": np.asarray(fa.plant_code, int),
        "zone_idx": np.asarray(fa.zone_idx, int),
        "fuel_type_idx": np.asarray(fa.fuel_type_idx, int),
        "group": np.array([str(getattr(g, "plant_group", "")) for g in gens], dtype=object),
        "unit": np.array([str(u) for u in fa.unit_ids], dtype=object),
    }
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(CACHE / f"{'arm' if coverage else 'keeper'}_{year}.npz", **out)
    (CACHE / f"{'arm' if coverage else 'keeper'}_{year}.log").write_text(buf.getvalue())
    out["log"] = buf.getvalue()
    out["zone_names"] = zone_names
    return out


def footprint(base: dict, arm: dict) -> dict:
    """Cell-by-cell fuel-price diff, keeper -> arm."""
    assert (base["unit"] == arm["unit"]).all(), "fleet identity"
    d = arm["fuel"] - base["fuel"]
    moved = ~np.isclose(d, 0.0, atol=1e-9)
    rows = moved.any(axis=1)
    gas = np.isin(base["group"], GAS_GROUPS)
    months = sorted(int(m) + 1 for m in np.unique(MONTH_OF_HOUR[moved.any(axis=0)]))
    out = {
        "rows_moved": int(rows.sum()),
        "rows_moved_nongas": int((rows & ~gas).sum()),
        "gas_rows_total": int(gas.sum()),
        "mw_moved": round(float(base["pmax"][rows].sum()), 1),
        "months_moved": months,
        "cells_moved_outside_months_9_10_11": int(moved[:, ~np.isin(MONTH_OF_HOUR + 1, (9, 10, 11))].sum()),
        "by_month": {},
    }
    for m in months:
        hm = MONTH_OF_HOUR == m - 1
        r = moved[:, hm].any(axis=1)
        w = base["pmax"][r]
        b = (base["fuel"][r][:, hm] * w[:, None]).sum() / max(w.sum() * hm.sum(), 1e-9)
        a = (arm["fuel"][r][:, hm] * w[:, None]).sum() / max(w.sum() * hm.sum(), 1e-9)
        hr = base["heat_rate"][r]
        dmc = ((arm["fuel"][r][:, hm] - base["fuel"][r][:, hm]) * hr[:, None] * w[:, None]).sum() / max(w.sum() * hm.sum(), 1e-9)
        d3 = (base["plant_code"] == D3_PLANT) & r
        out["by_month"][m] = {
            "rows": int(r.sum()),
            "mw": round(float(w.sum()), 1),
            "capwt_usd_mmbtu_keeper": round(float(b), 4),
            "capwt_usd_mmbtu_arm": round(float(a), 4),
            "d_fuel_mc_usd_mwh_capwt": round(float(dmc), 3),
            "plant_55077_keeper_mean": round(float(base["fuel"][d3][:, hm].mean()), 3) if d3.any() else None,
            "plant_55077_arm_mean": round(float(arm["fuel"][d3][:, hm].mean()), 3) if d3.any() else None,
        }
    return out


def main() -> None:
    os.environ["C243_CACHE"] = str(CACHE)
    spec = importlib.util.spec_from_file_location("_c243env", REPO / "scripts/probes/_caiso243_price_envelope.py")
    c243 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(c243)
    c243.BUNDLE = BUNDLE  # the CURRENT keeper's committed duals
    c243.CACHE = CACHE
    out: dict = {
        "_provenance": {
            "session": "caiso-246",
            "precommit": "PRECOMMIT-caiso246-spot-coverage-2026-09-04.md §1",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "recipe": "replay_keeper.run_year_kwargs (on-recipe) + caiso_citygate_spot_coverage=True",
            "note": "ZERO LP; footprint and price-leg envelope only",
        },
        "years": {},
    }
    for y in YEARS:
        base = rebuild(y, False)
        arm = rebuild(y, True)
        fp = footprint(base, arm)
        env = c243.envelope(y, "arm", base["zone_names"]) if fp["rows_moved"] else {"rows": 0, "lower": 0.0, "upper": 0.0}
        overlay_lines = [ln for ln in arm["log"].splitlines() if "hub-basis overlay" in ln]
        out["years"][y] = {"footprint": fp, "envelope": env, "arm_overlay_log": overlay_lines[:2]}
        print(f"--- {y}: rows moved {fp['rows_moved']} (non-gas {fp['rows_moved_nongas']}), MW {fp['mw_moved']}, months {fp['months_moved']}, cells outside Sep-Nov {fp['cells_moved_outside_months_9_10_11']}")
        for m, r in fp["by_month"].items():
            print(f"      month {m}: {r['rows']} rows {r['mw']} MW capwt {r['capwt_usd_mmbtu_keeper']} -> {r['capwt_usd_mmbtu_arm']} $/MMBtu (d mc {r['d_fuel_mc_usd_mwh_capwt']:+.2f} $/MWh); 55077 {r['plant_55077_keeper_mean']} -> {r['plant_55077_arm_mean']}")
        print(f"      envelope [{env.get('lower')}, {env.get('upper')}] rows {env.get('rows')}; overlay log: {overlay_lines[:1]}")
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
