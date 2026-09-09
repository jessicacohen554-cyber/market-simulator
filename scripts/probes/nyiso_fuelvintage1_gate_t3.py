"""GATE T3 + CARD 1 for session nyiso-fuelvintage-1 — both at ZERO LP cost.

**GATE T3 (charter task 3).** The charter asks that the 2019-2022 retiree window
be provably inert in 2023-2025. Its stated worry is that the COD ramp does not
touch ``pmax``, so the added units still enter ``FleetArrays`` and anything
reading CAPACITY rather than availability can move -- fleet totals, per-class
denominators, CAMPD binning and tranche construction, the eGRID heat-rate join,
the plant-group/outage crosswalks and the LP column count. **Every one of those
is a FleetArrays array or a count of one**, so this compares the arrays directly:
the shipped 1,094-row artifact against the same artifact filtered to
``planned_retirement_year >= 2023`` (which reproduces the pre-change 477-row /
141-plant window exactly), at IDENTICAL code, and requires every array to hash
identically. Array identity FORCES identical dispatch; matching dispatch could
merely coincide, which is why this is the stronger instrument -- and it needs no
control solve (rule 29(b)).

The swap is done on the ARTIFACT, not on one call site, because
``load_retired_within_window`` is reached from ``runner``, ``outages`` and the
COD map, and a per-call patch would let those three disagree.

**CARD 1 (the fuel ordering check).** ``resolve.py`` applies the EP-level seam at
:151 and ``apply_hub_basis_overlay`` at :229, and phase 0 measured the NYISO hub
overlay covering 12/12 months in every year -- so the seam's level should not
survive into a single month. The assembled ``fuel_prices`` array IS the LP's
input, and the ``fleet_only`` exit returns it, so the prediction is settled by an
array comparison rather than by a solve (rule 29 clause (0)).

Usage:
    python scripts/probes/nyiso_fuelvintage1_gate_t3.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import shutil
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/nyiso213_summer_seam"
ISO = "NYISO"
ARTIFACT = REPO / "data/raw/eia-860/eia860_generator_retired_within_window.parquet"
PRE_CHANGE_WINDOW_START = 2023


def _kwargs_from_meta(meta: dict) -> tuple[dict, dict]:
    from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES
    from scripts.run_calibration import run_year

    params = inspect.signature(run_year).parameters
    skip = {
        "year", "iso", "hours", "gas_price", "ttc_overrides",
        "fleet_only", "xyear_cache", "must_run_mw",
    }
    kwargs = {
        REBUILD_META_RENAMES.get(k, k): v
        for k, v in meta.items()
        if REBUILD_META_RENAMES.get(k, k) in params
        and REBUILD_META_RENAMES.get(k, k) not in skip
    }
    return kwargs, meta.get("gas_prices", {})


def _h(v) -> str:
    return hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest()[:16]


def _state_fingerprint(state) -> dict:
    """Hash every LP-input array the fleet_only exit exposes."""
    fa = state["fleet_arrays"]
    out: dict[str, str] = {}
    for name in sorted(dir(fa)):
        if name.startswith("_"):
            continue
        try:
            v = getattr(fa, name)
        except Exception:
            continue
        if isinstance(v, np.ndarray):
            out[f"fa.{name}"] = f"{_h(v)}|{v.shape}|{v.dtype}"
        elif isinstance(v, (list, tuple)) and v and isinstance(v[0], str):
            out[f"fa.{name}"] = (
                hashlib.sha256("\x00".join(map(str, v)).encode()).hexdigest()[:16]
                + f"|len={len(v)}"
            )
    for key in ("mc_base", "fuel_prices", "demand", "wind_cf", "wind_cap",
                "solar_cf", "solar_cap", "wind_mc", "solar_mc",
                "storage_power_cap"):
        v = state.get(key)
        if isinstance(v, np.ndarray):
            out[key] = f"{_h(v)}|{v.shape}|{v.dtype}"
    out["n_gen"] = str(len(state["fleet"]))
    return out


def _run(year: int, meta: dict, kwargs: dict, gas_prices: dict, extra: dict | None):
    from scripts.run_calibration import run_year

    kw = dict(kwargs)
    if extra:
        # The generic override channel replay_keeper uses for --set.
        kw.setdefault("prb_overrides", {})
        kw["prb_overrides"] = {**(kw.get("prb_overrides") or {}), **extra}
    gp = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
    return run_year(year, ISO, int(meta.get("hours", 8760)), gp, {},
                    fleet_only=True, **kw)


def _diff(a: dict, b: dict) -> dict:
    keys = sorted(set(a) | set(b))
    return {k: {"control": a.get(k), "arm": b.get(k)} for k in keys
            if a.get(k) != b.get(k)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--skip-card1", action="store_true")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import pandas as pd

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs, gas_prices = _kwargs_from_meta(meta)

    backup = ARTIFACT.with_suffix(".parquet.shipped")
    filtered = ARTIFACT.with_suffix(".parquet.pre2023")
    shutil.copy2(ARTIFACT, backup)
    full = pd.read_parquet(ARTIFACT)
    pre = full[full.planned_retirement_year >= PRE_CHANGE_WINDOW_START].copy()
    pre.to_parquet(filtered, index=False)
    print(f"artifact: shipped {len(full)} rows / {full.plant_id.nunique()} plants; "
          f"pre-change reconstruction {len(pre)} rows / {pre.plant_id.nunique()} plants")

    report: dict = {
        "iso": ISO,
        "keeper_bundle": BUNDLE.name,
        "artifact_shipped_rows": int(len(full)),
        "artifact_pre_change_rows": int(len(pre)),
        "gate_T3": {},
        "card1_ordering": {},
    }
    ok = True
    try:
        for year in args.years:
            # ---- CONTROL: the pre-change 477-row window -------------------
            shutil.copy2(filtered, ARTIFACT)
            _reset_caches()
            ctl = _state_fingerprint(_run(year, meta, kwargs, gas_prices, None))
            # ---- ARM: the shipped 1,094-row window ------------------------
            shutil.copy2(backup, ARTIFACT)
            _reset_caches()
            arm_state = _run(year, meta, kwargs, gas_prices, None)
            arm = _state_fingerprint(arm_state)

            d = _diff(ctl, arm)
            report["gate_T3"][str(year)] = {
                "identical": not d,
                "n_arrays_compared": len(set(ctl) | set(arm)),
                "differing": d,
            }
            print(f"[T3 {year}] arrays compared={len(set(ctl)|set(arm))} "
                  f"IDENTICAL={not d}" + ("" if not d else f" DIFFERING={list(d)}"))
            ok = ok and not d

            # ---- CARD 1: the EP-level seam on the same year ---------------
            if not args.skip_card1:
                _reset_caches()
                on = _run(year, meta, kwargs, gas_prices,
                          {"gas_electric_power_monthly_level": True})
                fp_off = np.asarray(arm_state["fuel_prices"])
                fp_on = np.asarray(on["fuel_prices"])
                mc_off = np.asarray(arm_state["mc_base"])
                mc_on = np.asarray(on["mc_base"])
                same_shape = fp_off.shape == fp_on.shape
                rec = {
                    "fuel_prices_byte_identical": bool(
                        same_shape and _h(fp_off) == _h(fp_on)),
                    "fuel_prices_max_abs_delta": (
                        float(np.nanmax(np.abs(fp_on - fp_off))) if same_shape else None),
                    "mc_base_byte_identical": bool(
                        mc_off.shape == mc_on.shape and _h(mc_off) == _h(mc_on)),
                    "mc_base_max_abs_delta": (
                        float(np.nanmax(np.abs(mc_on - mc_off)))
                        if mc_off.shape == mc_on.shape else None),
                }
                report["card1_ordering"][str(year)] = rec
                print(f"[C1 {year}] fuel_prices identical={rec['fuel_prices_byte_identical']} "
                      f"max|d|={rec['fuel_prices_max_abs_delta']} ; "
                      f"mc_base identical={rec['mc_base_byte_identical']} "
                      f"max|d|={rec['mc_base_max_abs_delta']}")
    finally:
        shutil.copy2(backup, ARTIFACT)
        backup.unlink(missing_ok=True)
        filtered.unlink(missing_ok=True)
        print("artifact restored to the shipped 1,094-row window")

    report["gate_T3_PASS"] = ok
    out = Path(args.out) if args.out else (
        REPO / "results/calibration/_nyiso_fuelvintage1_gate_t3.json")
    out.write_text(json.dumps(report, indent=1))
    print(f"\nGATE T3 {'PASS' if ok else 'FAIL'} — wrote {out}")
    return 0 if ok else 1


def _reset_caches() -> None:
    """Drop every module-level cache the fleet/fuel path memoizes."""
    import importlib

    for mod, fn in (
        ("market_sim.data.fleet.eia860", None),
        ("market_sim.data.cod_ramp", None),
        ("market_sim.data.outages", None),
        ("market_sim.data.fuel.hubs", None),
        ("market_sim.data.fuel.plant_prices", None),
    ):
        try:
            m = importlib.import_module(mod)
        except Exception:
            continue
        for name, val in list(vars(m).items()):
            if name.startswith("_") and name.endswith("CACHE") and isinstance(val, dict):
                val.clear()
            if hasattr(val, "cache_clear"):
                try:
                    val.cache_clear()
                except Exception:
                    pass


if __name__ == "__main__":
    raise SystemExit(main())
