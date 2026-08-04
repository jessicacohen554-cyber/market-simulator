"""caiso-164 §0 follow-on — is the model's CAISO renewable surplus SITED south?

NO LP.  Loads the same zonal renewable CF profiles and capacities the
calibration lane builds (``data.renewables.load_renewable_profiles`` on the
keeper's own recipe) plus the keeper's committed zonal demand, and asks the one
question section H of ``caiso164_ns_basis_decomp.py`` leaves open.

Section H measured that the model's five CAISO zones price identically through
the entire solar belly, while the real market's south collapses $15-22/MWh
below the north.  A zone can only decouple downward if it is in genuine local
surplus, so either (a) the model's renewable energy is not concentrated in the
south the way the real fleet is, or (b) it is, and the N-S corridor carries the
surplus away too cheaply.  This probe separates those: it reports, per zone,
renewable ENERGY as a share of that zone's own demand — the local surplus ratio
— hour by hour through the belly.

Reported against; never applied to a solve (rules 1 / 13).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import fields as dc_fields
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.renewables import load_renewable_profiles

REPO = Path(__file__).resolve().parents[2]
KEEPER = REPO / "results/calibration/caiso163_asym_path_ratings"
YEARS = (2023, 2024, 2025)
ZONES_SOUTH = ("ZP26", "SP15_rest", "LA_BASIN", "SDGE")


def main() -> int:
    """Print the per-zone surplus decomposition; returns 0 (diagnostic)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    iso_config = get_iso_config("CAISO")
    zone_names = [z.name for z in iso_config.zones]
    report: dict = {}

    # Rebuild the keeper's own recipe from its COMMITTED run_config.json rather
    # than re-deriving one, so the profiles read here are the profiles the
    # keeper solved on (only the fields ScenarioConfig still declares are
    # replayed; the solve year is overridden per year).
    recorded = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    valid = {f.name for f in dc_fields(ScenarioConfig)}
    base = {k: v for k, v in recorded.items() if k in valid}
    dropped = sorted(set(recorded) - valid)
    if dropped:
        print(f"note: {len(dropped)} recorded field(s) no longer on ScenarioConfig")

    for year in YEARS:
        cfg = ScenarioConfig(**{**base, "start_year": year, "end_year": year})
        wind_cf, wind_cap, solar_cf, solar_cap = load_renewable_profiles(
            "CAISO", year, iso_config, cfg
        )
        # wind_cf / solar_cf are (n_zones, T); *_cap are (n_zones,) MW.
        wind_mwh = wind_cf * wind_cap[:, None]
        solar_mwh = solar_cf * solar_cap[:, None]
        ren = wind_mwh + solar_mwh

        d = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        d = d[d["pass"] == "P1"]
        dem = d.pivot_table(index="hour", columns="zone", values="demand")
        t = min(ren.shape[1], len(dem))
        hod = np.arange(t) % 24
        belly = (hod >= 9) & (hod <= 16)

        print("=" * 79)
        print(f"{year} — model CAISO zonal renewable capacity and local surplus")
        print("=" * 79)
        print(
            f"{'zone':>10} {'wind MW':>9} {'solar MW':>9} {'ren TWh':>9} "
            f"{'load TWh':>9} {'ren/load':>9} {'belly ren/load':>15} "
            f"{'belly h surplus':>16}"
        )
        rows = {}
        for i, z in enumerate(zone_names):
            if z not in dem.columns or float(dem[z].sum()) <= 0:
                continue
            r = ren[i, :t]
            ld = dem[z].to_numpy()[:t]
            ratio = float(r.sum() / ld.sum())
            bratio = float(r[belly].sum() / ld[belly].sum())
            surplus_h = int((r[belly] > ld[belly]).sum())
            rows[z] = {
                "wind_mw": round(float(wind_cap[i]), 1),
                "solar_mw": round(float(solar_cap[i]), 1),
                "ren_twh": round(float(r.sum()) / 1e6, 3),
                "load_twh": round(float(ld.sum()) / 1e6, 3),
                "ren_over_load": round(ratio, 4),
                "belly_ren_over_load": round(bratio, 4),
                "belly_hours_local_surplus": surplus_h,
                "belly_hours": int(belly.sum()),
            }
            print(
                f"{z:>10} {wind_cap[i]:>9,.0f} {solar_cap[i]:>9,.0f} "
                f"{r.sum() / 1e6:>9.2f} {ld.sum() / 1e6:>9.2f} "
                f"{ratio:>9.3f} {bratio:>15.3f} "
                f"{surplus_h:>10} / {int(belly.sum())}"
            )
        # The aggregate that matters for a corridor: does the SOUTH as a block
        # run a belly surplus the north must absorb?
        south = [z for z in ZONES_SOUTH if z in rows]
        si = [zone_names.index(z) for z in south]
        sr = ren[si, :t].sum(axis=0)
        sl = dem[south].to_numpy()[:t].sum(axis=1)
        ni = zone_names.index("NP15")
        nr = ren[ni, :t]
        nl = dem["NP15"].to_numpy()[:t]
        agg = {
            "south_belly_ren_over_load": round(
                float(sr[belly].sum() / sl[belly].sum()), 4
            ),
            "north_belly_ren_over_load": round(
                float(nr[belly].sum() / nl[belly].sum()), 4
            ),
            "south_belly_hours_surplus": int((sr[belly] > sl[belly]).sum()),
            "north_belly_hours_surplus": int((nr[belly] > nl[belly]).sum()),
            "south_belly_mean_net_export_mw": round(
                float((sr[belly] - sl[belly]).mean()), 1
            ),
            "north_belly_mean_net_import_mw": round(
                float((nl[belly] - nr[belly]).mean()), 1
            ),
        }
        print()
        print(
            f"  SOUTH block (ZP26+SP15_rest+LA_BASIN+SDGE) belly ren/load = "
            f"{agg['south_belly_ren_over_load']:.3f}, local surplus in "
            f"{agg['south_belly_hours_surplus']} of {int(belly.sum())} belly h"
        )
        print(
            f"  NORTH (NP15)                              belly ren/load = "
            f"{agg['north_belly_ren_over_load']:.3f}, local surplus in "
            f"{agg['north_belly_hours_surplus']} of {int(belly.sum())} belly h"
        )
        print(
            f"  mean belly south net renewable export "
            f"{agg['south_belly_mean_net_export_mw']:,.0f} MW vs the Path-15 "
            f"S->N rating 5,400 MW + Path-26 S->N 3,000 MW"
        )
        print()
        report[str(year)] = {"zones": rows, "aggregate": agg}

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
