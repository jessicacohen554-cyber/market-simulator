"""R-ERCOT-8 record: Jack Fusco (55357) rows of campd_cc_heat_rates_ERCOT.csv.

Runs scripts/data/derive_campd_cc_heat_rates.py's OWN estimator (same
functions, same gates) on the ERCOT backcast union PLUS plant 55357's
combined-cycle generators, which the EIA-860 BA filter drops (EIA BA field
"MISO"; the plant is ERCOT DAM resource BVE_CC1). Only the 55357 rows are
kept: every other row of the committed artifact stays frozen (rule 23), since
a whole-file re-derive at HEAD does not reproduce it (drift recorded in the
R-ERCOT-8 PRECOMMIT). Prints the rows; --append writes them to the artifact.
"""
import sys

sys.path[:0] = [".", "src", "scripts"]
import pandas as pd  # noqa: E402

import scripts.data.derive_campd_cc_heat_rates as d  # noqa: E402
from scripts.lib.heat_rate_years import BACKCAST_YEARS, backcast_fleets, union_fleet  # noqa: E402

PLANT = 55357
iso, years = "ERCOT", sorted(BACKCAST_YEARS)
fleets = backcast_fleets(iso, years)
miso = backcast_fleets("MISO", years)
for y in years:
    fleets[y] = fleets[y] + [g for g in miso[y] if int(g.plant_code) == PLANT]
union = union_fleet(fleets)
caps = d.class_capacity(union, d.TARGET_CLASS)
assert PLANT in caps, "Fusco CC generators not found in the MISO-BA EIA-860 fleet"
pooled = d._campd_cc_hours(iso, years, {PLANT})
by_year = d.boundary_ratios_by_year(iso, pooled, years)
units = d.unit_operating_heat_rates(pooled)
factors = d.parasitic_factors()
table = d.plant_table(units, iso, years, {PLANT: caps[PLANT]},
                      d.class_heat_rates(union, d.TARGET_CLASS), factors, d.boundary_ratios(by_year))


def _yt(year):
    yu = d.unit_operating_heat_rates(pooled[pooled["year"] == year])
    if yu.empty:
        return None
    return d.plant_table(yu, iso, [year], {PLANT: caps[PLANT]},
                         d.class_heat_rates(fleets.get(year, []), d.TARGET_CLASS), factors, by_year.get(year, {}))


table = d.stack_year_tables(table, d.per_year_tables(years, _yt))
table = d.apply_eia923_identity(table, d.eia923_identity_rates({PLANT}, years))
table = table[table["plant_code"] == PLANT]
print(caps[PLANT], "MW")
print(table.drop(columns=["source"]).to_string())
if "--append" in sys.argv:
    path = d.PROCESSED_DIR / f"campd_cc_heat_rates_{iso}.csv"
    base = pd.read_csv(path)
    assert not (base["plant_code"] == PLANT).any()
    with open(path, "a") as fh:
        table[base.columns].to_csv(fh, header=False, index=False)
    print("appended", len(table), "rows to", path)
