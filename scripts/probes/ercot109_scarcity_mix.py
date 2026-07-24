"""ERCOT-109 — resource mix at the TRUE scarcity hours, model vs measured actuals.

Selects scarcity hours from the ACTUALS ONLY (load-weighted zonal settlement price
>= a threshold, default $300/MWh — the tail definition this lane uses throughout; the
model's own price plays no part in selecting the hours), then reports, for those hours,
the mean MW each fuel contributed in the model against what ERCOT actually delivered.

Answers the question the mean-only view hides: the averages flatten a skewed
distribution, so this also counts, hour by hour, how OFTEN each fuel over-runs and by
how much (>250 / >500 / >1000 MW, median, p90, max), plus the combined cheap-stack
surplus (wind+coal+solar+hydro) and its correlation against the gas deficit.

Finding at 2023 Jul-Sep on the ercot100 keeper (122 scarcity hours): the model serves
the same load with ~1.7 GW less gas, backfilled by coal (over in 58 % of hours, max
+1,943 MW) and wind (48 %, max +2,233 MW). The cheap stack runs a surplus in 118/122
hours (median +871 MW) and gas is under in 121/122; corr(cheap surplus, gas deficit)
= -0.77, i.e. near one-for-one merit-order displacement. Total generation matches
within 679 MW — a composition error, not a capacity shortfall.

CAVEATS (both structural, both stated in the emitted summary):
  * Load is a measured INPUT to the backcast, so the level matches by construction;
    what is compared here is which resources served it.
  * Storage is absent from BOTH sides — EIA-930 publishes no battery series for ERCOT
    in 2023, and the bundle's class hourlies carry generation classes only. Whether the
    model over-discharges batteries into scarcity hours is OPEN, not answered here.
  * EIA-930 reports a single natural-gas total, so the model's CC/CT/steam split has no
    measured counterpart at this grain and is emitted as model-side only.

No LP. Reads the committed keeper hourly sidecars + the committed zonal actual archive
+ the EIA-930 ``ERCO hourly`` extract on the model's own hour basis.

Usage: python -m scripts.probes.ercot109_scarcity_mix <bundle> [--year 2023]
       [--months 7 8 9] [--threshold 300] [--json OUT.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

# Model zone -> settlement LZ(s) (mirrors derive_actual_lmp.ERCOT_MODEL_ZONE_TO_LZ)
ZONE_TO_LZ: dict[str, tuple[str, ...]] = {
    "Houston": ("LZ_HOUSTON",),
    "North": ("LZ_NORTH",),
    "Northeast": ("LZ_RAYBN",),
    "South": ("LZ_SOUTH",),
    "South_Central": ("LZ_AEN", "LZ_CPS", "LZ_LCRA"),
    "West": ("LZ_WEST",),
    "Panhandle": ("LZ_WEST",),
}
# model class -> EIA-930 fuel bucket
CLASS_TO_FUEL: dict[str, list[str]] = {
    "gas": ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP"],
    "coal": ["COAL_PRB", "COAL_LIGNITE"],
    "nuclear": ["nuclear"],
    "wind": ["wind"],
    "solar": ["solar"],
    "hydro": ["hydro"],
    "other": ["OTHER", "biomass", "oil"],
}
GAS_SUBCLASSES = ["CC_REGULAR", "CC_CHP", "ST_GAS", "CT_PEAKER", "CT_CHP", "ST_CHP"]
FUELS = list(CLASS_TO_FUEL)


def _month_hours(year: int, months: list[int]) -> np.ndarray:
    """Boolean 8760 mask for the requested calendar months (non-leap hour basis)."""
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return np.isin(idx.month, months)


def _load_weighted_prices(bundle: Path, year: int) -> tuple[np.ndarray, ...]:
    """Return (actual_lw, model_lw, load) on the rubric-v2.4 rt_lw basis."""
    from market_sim.config.paths import CALIBRATION_DIR

    sysd = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = sysd[sysd["pass"] == "P1"]
    pmod = p1.pivot(index="hour", columns="zone", values="price")
    dem = p1.pivot(index="hour", columns="zone", values="demand")

    act = pd.read_parquet(CALIBRATION_DIR / "actual_lmp_zonal_ERCOT.parquet")
    act = act[act["year"] == year]
    by_sp = {
        str(sp): g.set_index("hour")["rt"].reindex(range(8760)).to_numpy()
        for sp, g in act.groupby("settlement_point")
    }
    A = np.full((8760, len(pmod.columns)), np.nan)
    for j, zone in enumerate(pmod.columns):
        stack = [by_sp[lz] for lz in ZONE_TO_LZ[str(zone)] if lz in by_sp]
        if stack:
            A[:, j] = np.nanmean(np.vstack(stack), axis=0)

    D = dem.to_numpy()
    valid = ~np.isnan(A)
    actual_lw = np.nansum(np.where(valid, A, 0.0) * D, axis=1) / np.where(
        valid, D, 0.0
    ).sum(axis=1)
    model_lw = (pmod.to_numpy() * D).sum(axis=1) / D.sum(axis=1)
    return actual_lw, model_lw, D.sum(axis=1)


def _model_mix(bundle: Path, year: int) -> tuple[dict[str, np.ndarray], pd.DataFrame]:
    """Model MW per fuel bucket (and the raw class frame) on the 8760 hour basis."""
    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    wide = (
        cls.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        .reindex(range(8760))
        .fillna(0.0)
    )
    mix = {
        fuel: wide[[c for c in cols if c in wide.columns]].sum(axis=1).to_numpy()
        for fuel, cols in CLASS_TO_FUEL.items()
    }
    return mix, wide


def run(bundle: Path, year: int, months: list[int], threshold: float) -> dict:
    """Score the scarcity-hour mix and emit the summary dict (also printed)."""
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    actual_lw, model_lw, load = _load_weighted_prices(bundle, year)
    model, wide = _model_mix(bundle, year)
    actual = load_eia_hourly_benchmark("ERCOT", year)
    if actual is None:
        raise SystemExit(f"no EIA-930 hourly benchmark for ERCOT {year}")

    win = _month_hours(year, months)
    scar = win & (actual_lw >= threshold)
    missed = scar & (model_lw < 200.0)
    n = int(scar.sum())
    if not n:
        raise SystemExit(f"no hours clear ${threshold:.0f} in months {months}")

    mlab = "".join(pd.Timestamp(f"{year}-{m:02d}-01").strftime("%b") + " " for m in months)
    print(f"\n=== ERCOT {year} {mlab.strip()} — actual load-weighted >= ${threshold:.0f} ===")
    print(f"  {n} scarcity hours of {int(win.sum())} in window "
          f"({100 * n / max(int((actual_lw >= threshold).sum()), 1):.0f}% of the year's "
          f"{int((actual_lw >= threshold).sum())})")
    print(f"  actual ${actual_lw[scar].mean():,.0f}  model ${model_lw[scar].mean():,.0f}  "
          f"| model >= ${threshold:.0f} in {int((model_lw[scar] >= threshold).sum())}/{n}, "
          f"< $200 in {int(missed.sum())}/{n}")
    print(f"  load {load[scar].mean():,.0f} MW (window mean {load[win].mean():,.0f})")

    print(f"\n  {'fuel':9s} {'actual':>9s} {'model':>9s} {'delta':>8s}")
    mix_rows = []
    for f in FUELS:
        av, mv = float(actual[f][scar].mean()), float(model[f][scar].mean())
        mix_rows.append({"fuel": f, "actual": av, "model": mv, "delta": mv - av})
        print(f"  {f:9s} {av:9,.0f} {mv:9,.0f} {mv - av:+8,.0f}")
    ta = sum(r["actual"] for r in mix_rows)
    tm = sum(r["model"] for r in mix_rows)
    print(f"  {'TOTAL':9s} {ta:9,.0f} {tm:9,.0f} {tm - ta:+8,.0f}   "
          f"(load is a measured INPUT — the level matches by construction)")

    print(f"\n  per-hour over-run frequency across the {n} hours")
    print(f"  {'fuel':9s} {'>250':>10s} {'>500':>6s} {'>1000':>6s} {'median':>8s} "
          f"{'p90':>8s} {'max':>8s}")
    per = {}
    for f in FUELS:
        d = model[f][scar] - actual[f][scar]
        per[f] = {
            "mean": float(d.mean()), "median": float(np.median(d)),
            "p90": float(np.percentile(d, 90)), "max": float(d.max()),
            "n_over_250": int((d > 250).sum()), "n_over_500": int((d > 500).sum()),
            "n_over_1000": int((d > 1000).sum()),
        }
        print(f"  {f:9s} {per[f]['n_over_250']:4d} ({100 * per[f]['n_over_250'] / n:3.0f}%) "
              f"{per[f]['n_over_500']:6d} {per[f]['n_over_1000']:6d} "
              f"{per[f]['median']:+8,.0f} {per[f]['p90']:+8,.0f} {per[f]['max']:+8,.0f}")

    cheap = sum(model[f][scar] - actual[f][scar] for f in ("wind", "coal", "solar", "hydro"))
    gas_d = model["gas"][scar] - actual["gas"][scar]
    corr = float(np.corrcoef(cheap, gas_d)[0, 1])
    print(f"\n  cheap stack (wind+coal+solar+hydro) surplus: positive in "
          f"{int((cheap > 0).sum())}/{n} hours, median {np.median(cheap):+,.0f} MW, "
          f"max {cheap.max():+,.0f}")
    print(f"    >1 GW in {int((cheap > 1000).sum())} hours, >1.5 GW in {int((cheap > 1500).sum())}")
    print(f"  gas deficit: under in {int((gas_d < 0).sum())}/{n} hours, "
          f"mean {gas_d.mean():+,.0f} MW")
    print(f"  corr(cheap surplus, gas deficit) = {corr:.3f}  "
          f"(near -1 => one-for-one merit-order displacement)")

    month_of = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month.to_numpy()
    monthly = []
    for m in months:
        sel = scar & (month_of == m)
        if not sel.any():
            monthly.append({"month": m, "n": 0, "actual": 0.0, "model": 0.0})
            continue
        monthly.append({"month": m, "n": int(sel.sum()),
                        "actual": float(actual_lw[sel].mean()),
                        "model": float(model_lw[sel].mean()),
                        "gas_actual": float(actual["gas"][sel].mean()),
                        "gas_model": float(model["gas"][sel].mean())})
    print("\n  by month")
    for r in monthly:
        nm = pd.Timestamp(f"{year}-{r['month']:02d}-01").strftime("%b")
        print(f"    {nm}: {r['n']:3d} h | actual ${r['actual']:7,.0f} | model ${r['model']:6,.0f}")

    gas_sub = {k: float(wide[k].to_numpy()[scar].mean()) for k in GAS_SUBCLASSES
               if k in wide.columns}
    print("\n  model gas composition at those hours (MODEL-SIDE ONLY — EIA-930 reports "
          "one gas total):")
    for k, v in sorted(gas_sub.items(), key=lambda kv: -kv[1]):
        print(f"    {k:12s} {v:9,.0f}")
    print("\n  NOTE: storage is absent from BOTH sides (no EIA-930 battery series for "
          "ERCOT 2023;\n        the bundle's class hourlies carry generation classes "
          "only) — that leg is OPEN.")

    return {
        "year": year, "months": months, "threshold": threshold,
        "n_scarcity": n, "n_window": int(win.sum()),
        "n_year": int((actual_lw >= threshold).sum()),
        "price": {"actual": float(actual_lw[scar].mean()),
                  "model": float(model_lw[scar].mean()),
                  "hit": int((model_lw[scar] >= threshold).sum()),
                  "missed": int(missed.sum())},
        "load": {"scarcity": float(load[scar].mean()), "window": float(load[win].mean())},
        "mix": mix_rows,
        "missed_mix": [{"fuel": f, "actual": float(actual[f][missed].mean()),
                        "model": float(model[f][missed].mean()),
                        "delta": float(model[f][missed].mean() - actual[f][missed].mean())}
                       for f in FUELS] if missed.any() else [],
        "perhour": per,
        "cheap": {"mean": float(cheap.mean()), "median": float(np.median(cheap)),
                  "max": float(cheap.max()), "n_pos": int((cheap > 0).sum()),
                  "n500": int((cheap > 500).sum()), "n1000": int((cheap > 1000).sum()),
                  "n1500": int((cheap > 1500).sum()), "corr": corr},
        "gas_sub": gas_sub,
        "monthly": monthly,
    }


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="bundle dir, e.g. results/calibration/<name>")
    ap.add_argument("--year", type=int, default=2023)
    ap.add_argument("--months", type=int, nargs="+", default=[7, 8, 9],
                    help="calendar months to scope the window (default Jul Aug Sep)")
    ap.add_argument("--threshold", type=float, default=300.0,
                    help="actual load-weighted $/MWh defining a scarcity hour")
    ap.add_argument("--json", default=None, help="also write the summary dict here")
    args = ap.parse_args()

    out = run(Path(args.bundle), args.year, args.months, args.threshold)
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1))
        print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()
