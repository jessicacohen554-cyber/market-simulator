"""SPP-46 phase 0.2 (zero-LP): dump the LP's OWN input arrays on keeper-3's recipe.

For each year, rebuild the keeper-3 (spp43_screened_B) fleet with
``run_year(fleet_only=True)`` — the identical assembly path the LP solved on
(``mc_base`` = fuel x HR + VOM + emissions, every overlay applied) — and write:

* ``rows_<year>.csv`` (committed, small): one row per LP generator with its
  identity (unit_id, plant_code, name, zone, plant_group, band, fuel_type), its
  physics (pmax, heat_rate, vom, startup_cost_per_mw, min_down_hours), the
  F923 provenance of its gas price (``own_months`` = months the plant's OWN
  EIA-923 report covers; 0 = fully gap-filled from the nearby zone pool),
  and the annual cap-weighted means of mc_base / fuel_price / availability.
* ``arrays_<year>.npz`` (scratch, NOT committed): mc_base, availability,
  fuel_prices as float32 (n_gen x 8760) for the re-clearing predictor.

No solve. Nothing here depends on any residual.
Usage: uv run python docs/handoffs/spp46/offer_arrays.py [scratch_dir]
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402
from market_sim.data.eia923 import plant_month_price_grid  # noqa: E402
from market_sim.data.fuel.plant_prices import _load_monthly_cache  # noqa: E402

BUNDLE = REPO / "results/calibration/spp43_screened_B"
OUT = REPO / "docs/handoffs/spp46"
SCRATCH = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "_scratch"
SCRATCH.mkdir(parents=True, exist_ok=True)


def main() -> None:
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    costs = _load_monthly_cache(None)
    for year in (2023, 2024, 2025):
        kw_y = dict(kw); kw_y.update(derived_run_year_inputs(BUNDLE, year))
        r = run_year(year, "SPP", 8760, float(meta["gas_prices"][str(year)]), {},
                     fleet_only=True, **kw_y)
        fleet, fa = r["fleet"], r["fleet_arrays"]
        mc, fp, av = r["mc_base"], r["fuel_prices"], fa.availability
        grid = plant_month_price_grid(costs, year, "Natural Gas") if costs is not None else {}
        rows = []
        for g, gen in enumerate(fleet):
            pc = int(gen.plant_code or 0)
            own = grid.get(pc)
            own_months = int((~np.isnan(own)).sum()) if own is not None else 0
            a = av[g]
            w = a.sum()
            rows.append(dict(
                g=g, unit_id=gen.unit_id, plant_code=pc, name=gen.name, zone=gen.zone,
                plant_group=gen.plant_group, band=gen.bin_label, fuel_type=gen.fuel_type,
                pmax=float(gen.pmax_mw), heat_rate=float(fa.heat_rate[g]), vom=float(fa.vom[g]),
                startup=float(gen.startup_cost_per_mw or 0), min_down=int(gen.min_down_hours or 0),
                own_months=own_months,
                mc_mean=float(mc[g].mean()), mc_avail_mean=float((mc[g]*a).sum()/w) if w else np.nan,
                fuel_mean=float(fp[g].mean()), avail_mean=float(a.mean()),
                **{f"mc_m{m+1:02d}": float(mc[g, (m*730):((m+1)*730)].mean()) for m in range(12)},
            ))
        df = pd.DataFrame(rows)
        df.to_csv(OUT / f"rows_{year}.csv", index=False)
        np.savez_compressed(SCRATCH / f"arrays_{year}.npz", mc=mc.astype(np.float32),
                            avail=av.astype(np.float32), fuel=fp.astype(np.float32),
                            demand=r["demand"].astype(np.float32))
        print(year, "rows", len(df), "gap-filled gas rows:",
              int(((df.fuel_type.str.startswith("gas")) & (df.own_months == 0)).sum()))


if __name__ == "__main__":
    main()
