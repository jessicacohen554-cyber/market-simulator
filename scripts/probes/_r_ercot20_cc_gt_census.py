"""R-ERCOT-20 (zero LP): ERCOT CC_REGULAR plants that carry simple-cycle GT generators.

For every plant the keeper's leg bins as CC_REGULAR, reads EIA-860 operable
generators (solve-year vintage) by prime mover (CT/CA/CS = combined cycle,
GT = simple-cycle combustion turbine), the EIA-923 NG net generation by prime
mover, and the model's CC_REGULAR capacity and energy. A plant whose GT
nameplate the model bins inside its CC is priced on the CC offer ramp for
capacity that is really a simple-cycle peaker. Solves nothing.
Usage: python _r_ercot20_cc_gt_census.py <year> <unit_hourly path>
"""

from __future__ import annotations

import sys

import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR


def main(year: int, path: str, klass: str = "CC_REGULAR") -> None:
    """Print the census table and the GT-carrying subset."""
    u = pd.read_parquet(path, columns=["unit_id", "plant_group", "mw", "cap_mw"],
                        filters=[("plant_group", "=", klass)])
    u["plant"] = u.unit_id.astype(str).str.extract(r"_p(\d+)_")[0].astype(int)
    cap = u.groupby(["plant", "unit_id"]).cap_mw.mean().groupby("plant").sum()
    twh = u.groupby("plant").mw.sum() / 1e6
    g = pd.read_parquet(RAW_DATA_DIR / f"eia-860/vintage_{min(year, 2024)}/eia860_generator_operable.parquet")
    pc = next(c for c in g.columns if c.lower().replace(" ", "_") in ("plant_code", "plant_id"))
    pm = next(c for c in g.columns if "prime" in c.lower())
    npl = next(c for c in g.columns if "nameplate" in c.lower() and "capacity" in c.lower())
    g = g[g[pc].notna()]
    g = g[g[pc].astype(int).isin(cap.index)]
    by = g.groupby([g[pc].astype(int), pm])[npl].sum().unstack(fill_value=0.0)
    e = pd.read_csv(RAW_DATA_DIR / "eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv")
    e = e[(e.year == year) & (e.fuel_type == "NG") & e.plant_id.isin(cap.index)]
    eg = e.groupby(["plant_id", "prime_mover"]).net_generation_mwh.sum().unstack(fill_value=0.0) / 1e6
    t = pd.DataFrame({"model_cap": cap.round(0), "model_twh": twh.round(2)})
    for k in ("CT", "CA", "CS", "ST", "GT"):
        t[f"np_{k}"] = by.get(k, pd.Series(dtype=float)).reindex(t.index).fillna(0).round(0)
    t["e923_nonGT_twh"] = eg.reindex(t.index)[[c for c in ("CT", "CA", "CS", "ST") if c in eg]].sum(axis=1).round(3)
    t["e923_gt_twh"] = eg.get("GT", pd.Series(dtype=float)).reindex(t.index).fillna(0).round(3)
    gt = t[t.np_GT > 0]
    print(t.sort_values("np_GT", ascending=False).head(12).to_string())
    print(f"\n{year}: {len(gt)} {klass} plants carry GT nameplate {gt.np_GT.sum():.0f} MW; "
          f"their model {gt.model_twh.sum():.2f} TWh vs EIA-923 non-GT {gt.e923_nonGT_twh.sum():.2f} + GT {gt.e923_gt_twh.sum():.2f} TWh")


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], *(sys.argv[3:4]))
