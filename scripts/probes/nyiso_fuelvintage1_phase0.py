"""Phase-0 (zero-LP) census for session nyiso-fuelvintage-1.

Rebuilds the NYISO keeper's fleet via ``run_year(fleet_only=True)`` and answers,
without spending a single LP:

* **A** — the footprint of ``_apply_simple_cycle_hr_floor`` (SPP-49, UNCONDITIONAL
  and new since the keeper's ``git_sha``), i.e. whether the G-DRIFT hunk is LIVE.
* **B** — the footprint of the ``f923_gas_price_plausibility_screen`` (default ON
  since 2026-09-08, reached by this keeper because ``mode == "backcast"`` and
  ``gas_plant_monthly_fuel_pricing`` is on).
* **C** — the written-cell mask of ``apply_plant_monthly_fuel_prices`` (handoff
  ADDENDUM A2): what share of NYISO gas capacity-hours are already priced from a
  plant's own F923 print, and therefore unreachable by the EP-level seam.
* **D** — a FleetArrays fingerprint per year, so the retiree window's 2023-2025
  inertness (charter task 3) is provable by array identity rather than sampled by
  a dispatch comparison.

Usage:
    python scripts/probes/nyiso_fuelvintage1_phase0.py --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

BUNDLE = REPO / "results/calibration/nyiso213_summer_seam"
ISO = "NYISO"


def _kwargs_from_meta(meta: dict) -> tuple[dict, float | dict]:
    """Return the ``run_year`` kwargs a bundle's ``meta.json`` implies."""
    from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES
    from scripts.run_calibration import run_year

    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {}
    for k, v in meta.items():
        k2 = REBUILD_META_RENAMES.get(k, k)
        if k2 in params and k2 not in skip:
            kwargs[k2] = v
    return kwargs, meta.get("gas_prices", {})


def _fa_fingerprint(fa) -> dict:
    """Hash every array on a FleetArrays, so identity is provable not sampled."""
    out: dict[str, str] = {}
    for name in sorted(dir(fa)):
        if name.startswith("_"):
            continue
        try:
            v = getattr(fa, name)
        except Exception:
            continue
        if isinstance(v, np.ndarray):
            out[name] = hashlib.sha256(
                np.ascontiguousarray(v).tobytes()
            ).hexdigest()[:16] + f"|{v.shape}|{v.dtype}"
        elif isinstance(v, (list, tuple)) and v and isinstance(v[0], str):
            out[name] = hashlib.sha256(
                "\x00".join(map(str, v)).encode()
            ).hexdigest()[:16] + f"|len={len(v)}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    import market_sim.data.fleet.eia860 as eia860
    import market_sim.data.fuel.plant_prices as pp
    from market_sim.data.fuel.resolve import _GAS_FUEL_IDX
    from scripts.run_calibration import run_year

    meta = json.loads((BUNDLE / "meta.json").read_text())
    kwargs, gas_prices = _kwargs_from_meta(meta)

    census: dict = {"iso": ISO, "bundle": BUNDLE.name, "years": {}}

    # --- A: instrument the unconditional simple-cycle heat-rate floor ---------
    hr_hits: dict = {}
    _orig_hr = eia860._apply_simple_cycle_hr_floor

    def _spy_hr(df):
        import pandas as pd

        before = (
            pd.to_numeric(df["heat_rate"], errors="coerce").copy()
            if "heat_rate" in df.columns
            else None
        )
        out = _orig_hr(df)
        if before is not None and "heat_rate" in out.columns:
            after = pd.to_numeric(out["heat_rate"], errors="coerce")
            moved = (before != after) & before.notna()
            if moved.any():
                rows = out.loc[moved]
                for pid, grp in rows.groupby(rows["plant_id"]):
                    key = str(int(pid))
                    hr_hits.setdefault(key, {
                        "plant_name": str(grp.get("plant_name", grp.index).iloc[0])
                        if "plant_name" in grp.columns else "",
                        "rows": int(len(grp)),
                        "hr_before": round(float(before[grp.index].iloc[0]), 4),
                        "hr_after": round(float(after[grp.index].iloc[0]), 4),
                        "pmax_sum_mw": round(
                            float(grp["capacity_mw"].sum())
                            if "capacity_mw" in grp.columns else float("nan"), 2),
                    })
        return out

    eia860._apply_simple_cycle_hr_floor = _spy_hr

    # --- B: instrument the F923 plausibility screen ---------------------------
    screen_hits: dict = {}
    _orig_screen = getattr(pp, "screen_gas_plant_month_prices", None)
    if _orig_screen is not None:
        def _spy_screen(*a, **kw):
            import pandas as pd

            frame = a[0] if a else kw.get("frame")
            col = None
            before = None
            if isinstance(frame, pd.DataFrame):
                for c in ("price_per_mmbtu", "fuel_cost_per_mmbtu", "price"):
                    if c in frame.columns:
                        col, before = c, pd.to_numeric(frame[c], errors="coerce").copy()
                        break
            out = _orig_screen(*a, **kw)
            res = out[0] if isinstance(out, tuple) else out
            if before is not None and isinstance(res, pd.DataFrame) and col in res.columns:
                after = pd.to_numeric(res[col], errors="coerce")
                if len(after) == len(before):
                    moved = (before.values != after.values) & ~np.isnan(before.values)
                    screen_hits.setdefault("rows_in", 0)
                    screen_hits["rows_in"] += int(len(before))
                    screen_hits.setdefault("rows_moved", 0)
                    screen_hits["rows_moved"] += int(moved.sum())
                    if moved.any():
                        d = np.abs(after.values[moved] - before.values[moved])
                        screen_hits["max_abs_delta_usd_mmbtu"] = round(
                            max(float(d.max()),
                                screen_hits.get("max_abs_delta_usd_mmbtu", 0.0)), 4)
            return out

        pp.screen_gas_plant_month_prices = _spy_screen

    # --- C: the plant-monthly overwrite's written-cell mask (ADDENDUM A2) ----
    # apply_plant_monthly_fuel_prices RETURNS the (n_gen, T) boolean mask of the
    # cells it wrote, so the census is the return value -- no reconstruction.
    write_mask: dict = {}
    _orig_apply = pp.apply_plant_monthly_fuel_prices

    def _spy_apply(fuel_prices, fleet, config, year, *a, **kw):
        written = _orig_apply(fuel_prices, fleet, config, year, *a, **kw)
        m = np.asarray(written, dtype=bool)
        gas_idx = np.flatnonzero(
            np.isin(np.asarray(fleet.fuel_type_idx), list(_GAS_FUEL_IDX))
        )
        pmax = np.asarray(fleet.pmax, dtype=float)
        write_mask["cells_total"] = int(m.size)
        write_mask["cells_written"] = int(m.sum())
        write_mask["cells_written_pct"] = round(100.0 * m.sum() / m.size, 3)
        if gas_idx.size:
            gm = m[gas_idx]
            gp = pmax[gas_idx]
            ch = float(gp.sum() * m.shape[1])
            wch = float((gp[:, None] * gm).sum())
            write_mask["gas_units"] = int(gas_idx.size)
            write_mask["gas_capacity_hours"] = round(ch, 1)
            write_mask["gas_capacity_hours_written"] = round(wch, 1)
            write_mask["gas_capacity_hours_written_pct"] = (
                round(100.0 * wch / ch, 3) if ch else None
            )
            write_mask["gas_units_with_any_written"] = int((gm.any(axis=1)).sum())
        return written

    pp.apply_plant_monthly_fuel_prices = _spy_apply
    # resolve.py does `from .plant_prices import apply_plant_monthly_fuel_prices`,
    # so the module-attribute patch above never reaches its call site.
    import market_sim.data.fuel.resolve as _resolve

    _resolve.apply_plant_monthly_fuel_prices = _spy_apply
    # ...and the keeper's own path calls it from run_calibration directly:
    # resolve_fuel_prices is invoked with apply_monthly=False whenever a
    # coal-supply base (lignite/PRB) is set first, which this recipe does.
    import scripts.run_calibration as _rc

    _rc.apply_plant_monthly_fuel_prices = _spy_apply

    for year in args.years:
        hr_hits.clear()
        screen_hits.clear()
        write_mask.clear()
        gp = float(gas_prices.get(str(year), gas_prices.get(year, 0.0)))
        state = run_year(year, ISO, int(meta.get("hours", 8760)), gp, {},
                         fleet_only=True, **kwargs)
        fa = state["fleet_arrays"]
        fleet = state["fleet"]
        avail = np.asarray(fa.availability)
        pmax = np.asarray(fa.pmax)
        zero_avail = np.flatnonzero(avail.max(axis=1) <= 0.0)
        census["years"][str(year)] = {
            "n_gen": int(len(fleet)),
            "fleet_arrays_fingerprint": _fa_fingerprint(fa),
            "zero_availability_units": int(zero_avail.size),
            "zero_availability_pmax_mw": round(float(pmax[zero_avail].sum()), 3),
            "total_pmax_mw": round(float(pmax.sum()), 3),
            "A_simple_cycle_hr_floor_hits": json.loads(json.dumps(hr_hits)),
            "B_f923_plausibility_screen": json.loads(json.dumps(screen_hits)),
            "C_plant_monthly_write_mask": json.loads(json.dumps(write_mask)),
        }
        print(f"[{year}] n_gen={len(fleet)} "
              f"zero-avail={zero_avail.size} ({pmax[zero_avail].sum():.1f} MW) "
              f"A_hits={len(hr_hits)} B={screen_hits} C={write_mask}")

    out = Path(args.out) if args.out else (
        REPO / "results/calibration/_nyiso_fuelvintage1_phase0.json")
    out.write_text(json.dumps(census, indent=1))
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
