"""pjm-h15 phase 0b — the coal synchronization floor's ACTUAL energy footprint,
pooled window vs own-year window, read off the model's OWN fleet.

ZERO LP (rule 29 ``[R-SCREEN]`` clause (0), surviving as practice):
``run_year(..., fleet_only=True)`` over the DESIGNATED KEEPER pair's committed
recipes (``pjm_h14_coalmustrun_{span,touchpoint}``, i.e. with
``coal_mustrun_requires_measured_row`` already armed), so the population here is
exactly the covered-and-floored cohort the card is chartered on -- not an
inference from the artifact.

For every generator carrying ``coal_sync_pmin_mw > 0`` it reports the asserted
floor ENERGY (``pmin_mw x window_hours``, before the pmax*availability clip and
before the LP) under the incumbent POOLED ``online_frac`` and under the solve
year's OWN measured fraction. Energy, not hours: pjm-h14 correction #6 -- scope
a footprint on ``forced_twh``, never on a share whose denominator moves.
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
sys.path.insert(0, str(REPO))

CACHE = Path("/tmp/claude-0/h15/fleet")
BUNDLES = {
    2020: "results/calibration/pjm_h14_coalmustrun_touchpoint",
    2021: "results/calibration/pjm_h14_coalmustrun_touchpoint",
    2022: "results/calibration/pjm_h14_coalmustrun_touchpoint",
    2023: "results/calibration/pjm_h14_coalmustrun_span",
    2024: "results/calibration/pjm_h14_coalmustrun_span",
    2025: "results/calibration/pjm_h14_coalmustrun_span",
}
FORCE_ALL = 0.99  # withholding._COAL_SYNC_FORCE_ALL


def sync_rows(year: int) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"coal_sync_{year}.parquet"
    if path.exists():
        return pd.read_parquet(path)

    from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs
    from scripts.run_calibration import run_year

    bundle = REPO / BUNDLES[year]
    meta = json.loads((bundle / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    kw.update(derived_run_year_inputs(bundle, year))
    gas = float(meta["gas_prices"][str(year)])
    payload = run_year(year, meta["iso"], 8760, gas, {}, fleet_only=True, **kw)
    gens = payload["fleet"] if isinstance(payload, dict) and "fleet" in payload else payload
    if hasattr(gens, "generators"):
        gens = gens.generators
    rows = []
    for g in gens:
        pmin = float(getattr(g, "coal_sync_pmin_mw", 0.0) or 0.0)
        if pmin <= 0.0:
            continue
        rows.append(dict(
            year=year,
            plant_code=int(getattr(g, "plant_code", 0) or 0),
            name=str(getattr(g, "name", "")),
            unit_id=str(getattr(g, "unit_id", getattr(g, "id", ""))),
            group=str(getattr(g, "plant_group", "") or ""),
            pmax=float(getattr(g, "pmax_mw", 0.0) or 0.0),
            sync_pmin=pmin,
            pooled_frac=float(getattr(g, "coal_sync_online_frac", 1.0) or 1.0),
        ))
    df = pd.DataFrame(rows)
    df.to_parquet(path)
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--by-year", required=True)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    by = pd.read_csv(args.by_year)
    by = by[by.plant_group == "COAL"]
    omap = {(int(r.plant_code), int(r.year)): float(r.online_frac)
            for r in by.itertuples(index=False)
            if float(r.online_frac) == float(r.online_frac)}

    out, missing = [], []
    for year in sorted(BUNDLES):
        df = sync_rows(year)
        if not len(df):
            print(f"{year}: NO coal_sync_pmin_mw ROWS")
            continue
        df["own_frac"] = [omap.get((int(c), year)) for c in df.plant_code]
        miss = df[df.own_frac.isna()]
        for r in miss.itertuples(index=False):
            missing.append(dict(year=year, plant=int(r.plant_code), name=r.name,
                                pmax=round(r.pmax, 1), pooled=round(r.pooled_frac, 3)))
        # A plant with no own-year row keeps the pooled fraction (fail-safe:
        # the arm can never REMOVE a floor for want of a measurement).
        df["own_frac"] = df.own_frac.fillna(df.pooled_frac)
        for col, src in (("k_pooled", "pooled_frac"), ("k_own", "own_frac")):
            df[col] = np.where(df[src] >= FORCE_ALL, 8760,
                               np.round(df[src] * 8760).astype(int))
        df["twh_pooled"] = df.sync_pmin * df.k_pooled / 1e6
        df["twh_own"] = df.sync_pmin * df.k_own / 1e6
        out.append(df)

    d = pd.concat(out, ignore_index=True)
    pd.set_option("display.width", 220)

    print("### 1. ASSERTED coal synchronization floor ENERGY by year (TWh, pre-clip, pre-LP)\n")
    agg = d.groupby("year").agg(
        units=("unit_id", "count"),
        plants=("plant_code", "nunique"),
        sync_pmin_mw=("sync_pmin", "sum"),
        twh_pooled=("twh_pooled", "sum"),
        twh_own=("twh_own", "sum"),
    )
    agg["d_twh"] = (agg.twh_own - agg.twh_pooled).round(4)
    agg["d_pct"] = (100 * agg.d_twh / agg.twh_pooled).round(2)
    print(agg.round(4).to_string())

    print("\n### 2. PER-PLANT, the largest |delta| in each year (TWh of asserted floor)\n")
    p = d.groupby(["year", "plant_code", "name"], as_index=False).agg(
        sync_pmin=("sync_pmin", "sum"), pooled=("pooled_frac", "first"),
        own=("own_frac", "first"), twh_pooled=("twh_pooled", "sum"),
        twh_own=("twh_own", "sum"))
    p["d_twh"] = (p.twh_own - p.twh_pooled).round(4)
    for y in sorted(p.year.unique()):
        s = p[p.year == y].reindex(p[p.year == y].d_twh.abs().sort_values(ascending=False).index)
        print(f"\n  {y}:")
        print(s.head(8)[["plant_code", "name", "sync_pmin", "pooled", "own",
                         "twh_pooled", "twh_own", "d_twh"]].round(3).to_string(index=False))

    print("\n### 3. COVERED-AND-FLOORED population, and plants with NO own-year row\n")
    print(f"    floored plant-years: {len(p)}   distinct plants: {p.plant_code.nunique()}")
    print(f"    plant-years with no own-year measurement (keep the pooled fraction): {len(missing)}")
    for m in missing:
        print("     ", m)

    print("\n### 4. THE SIGN TEST — can this be a level-tuning channel? (rule 1 [R-STRUCT])\n")
    print("    A tuning channel moves one way. A vintage repair does not.")
    print(agg[["d_twh", "d_pct"]].to_string())
    signs = np.sign(agg.d_twh.to_numpy())
    print(f"\n    signs by year: {list(signs.astype(int))}   "
          f"(+{int((signs > 0).sum())} / -{int((signs < 0).sum())})")
    print(f"    mean d_twh over the six years: {agg.d_twh.mean():+.4f} TWh "
          f"({100 * agg.d_twh.sum() / agg.twh_pooled.sum():+.2f} % of asserted)")

    if args.json_out:
        Path(args.json_out).write_text(json.dumps(dict(
            by_year=agg.reset_index().to_dict("records"),
            per_plant=p.to_dict("records"),
            no_own_year_row=missing), indent=1))
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
