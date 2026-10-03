"""closeout-nuclear-rows (zero LP): fallback vs derived nuclear monthly CF for
PJM / NWPP / SPP 2019-2022, the implied fleet energy of each, and EIA-923.

Implied TWh = sum over months of CF x online fleet pmax x hours, over exactly the
derive's fleet (``derive_nuclear_monthly_cf._nuclear_fleet``). The fallback CF is
what ``fleet.arrays._nuclear_monthly`` applies when a year has no table row:
``NUCLEAR_MONTHLY_CF[iso] x (1 - EFORD)`` per unit. EIA-923 is the same plants'
Page-1 net generation (uncapped), plus the ISO's other nuclear plants in EIA-923
that the derive's fleet excludes (dormant / not in the model roster).
"""

import calendar
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

import pandas as pd  # noqa: E402

from derive_nuclear_monthly_cf import _MONTH_COLS, _nuclear_fleet, derive_monthly_cf  # noqa: E402
from market_sim.config.constants import NUCLEAR_DORMANT_UNTIL, NUCLEAR_MONTHLY_CF  # noqa: E402
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

OUT = REPO / "docs/records/governance/closeout-2026-10/nuclear-rows/nuc_rows.csv"
# Keeper model nuclear TWh (payload gmModel) and bench classFull, from
# closeout-SOCO-2 FINDING §d (nuc_coverage.csv).
KEEPER = {
    ("PJM", 2019): (276.99, 277.92), ("PJM", 2020): (272.05, 275.75),
    ("PJM", 2021): (271.90, 271.69), ("PJM", 2022): (271.90, 270.59),
    ("NWPP", 2019): (8.53, 8.87), ("NWPP", 2020): (8.44, 9.43),
    ("NWPP", 2021): (8.44, 8.51), ("NWPP", 2022): (8.44, 9.85),
    ("SPP", 2019): (15.80, 16.20), ("SPP", 2020): (15.80, 16.77),
    ("SPP", 2021): (15.80, 15.46), ("SPP", 2022): (15.80, 14.60),
}

gen = load_monthly_generation()
rows = []
for iso in ("PJM", "NWPP", "SPP"):
    cfg = get_iso_config(iso)
    fleet_all = [g for g in load_fleet_from_csv(iso, cfg) if g.fuel_type == "nuclear" and g.pmax_mw > 0]
    for year in (2019, 2020, 2021, 2022):
        plants, online = _nuclear_fleet(iso, year)
        units = [g for g in fleet_all if year >= NUCLEAR_DORMANT_UNTIL.get(int(g.plant_code), 0)]
        hrs = [calendar.monthrange(year, m)[1] * 24 for m in range(1, 13)]
        derived = derive_monthly_cf(iso, year)
        pat = NUCLEAR_MONTHLY_CF[iso]
        # fallback: per-unit (1 - eford) x pattern
        fb_mwh = sum(
            (1.0 - g.eford) * pat[m] * g.pmax_mw * hrs[m] for g in units for m in range(12)
        )
        dv_mwh = sum(derived[m] * online[m] * hrs[m] for m in range(12))
        fleet_mwh_h = sum(online[m] * hrs[m] for m in range(12))
        r = gen[(gen["year"] == year) & (gen["plant_id"].isin(plants))]
        e923 = float(r[_MONTH_COLS].sum().sum())
        km, kb = KEEPER[(iso, year)]
        rows.append(dict(
            iso=iso, year=year, fleet_mw=round(online[0], 1),
            fallback_cf=round(fb_mwh / fleet_mwh_h, 3),
            derived_cf=round(dv_mwh / fleet_mwh_h, 3),
            fallback_twh=round(fb_mwh / 1e6, 2), derived_twh=round(dv_mwh / 1e6, 2),
            eia923_fleet_twh=round(e923 / 1e6, 2),
            derived_minus_e923=round((dv_mwh - e923) / 1e6, 2),
            keeper_model_twh=km, bench_twh=kb,
            keeper_gap=round(km - kb, 2),
            implied_gap_after=round(km + (dv_mwh - fb_mwh) / 1e6 - kb, 2),
            bench_minus_fleet_e923=round(kb - e923 / 1e6, 2),
        ))
d = pd.DataFrame(rows)
OUT.parent.mkdir(parents=True, exist_ok=True)
d.to_csv(OUT, index=False)
pd.set_option("display.width", 250)
print(d.to_string(index=False))
# EIA-923 nuclear plants outside the derive fleet, per ISO-year (diagnostic only)
for iso in ("PJM", "NWPP", "SPP"):
    for year in (2019, 2020, 2021, 2022):
        plants, _ = _nuclear_fleet(iso, year)
        ex = gen[(gen["year"] == year) & (gen["plant_id"].isin(list(NUCLEAR_DORMANT_UNTIL)))]
        if not ex.empty:
            print(iso, year, "dormant-listed plants in EIA-923:",
                  ex.groupby("plant_id")[_MONTH_COLS].sum().sum(axis=1).div(1e6).round(2).to_dict())
