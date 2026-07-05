"""Quick per-class TWh + monthly CA-zone LMP for a CAISO bundle dispatch parquet.

Usage: python scripts/_caiso_class_lmp.py BUNDLE_DIR YEAR [PASS]
"""

import sys
import json
import pandas as pd
import numpy as np

bundle, year = sys.argv[1], int(sys.argv[2])
pas = sys.argv[3] if len(sys.argv) > 3 else "P1"
df = pd.read_parquet(f"{bundle}/dispatch/{year}_{pas}.parquet")

ref = json.load(open("data/raw/_validation-source/calibration_reference.json"))
g = ref["isos"]["CAISO"][str(year)]["generation_twh"]

twh = df.groupby("klass").mw.sum() / 1e6
cc = sum(twh.get(k, 0) for k in twh.index if k.startswith("CC"))
ct = sum(twh.get(k, 0) for k in twh.index if k.startswith("CT"))
st = twh.get("ST_GAS", 0)
print(f"== {bundle} {year} {pas} ==")
print(
    f"gas_cc model {cc:6.2f} | EIA923 {g['gas_cc']:6.2f} | err {cc - g['gas_cc']:+6.2f}"
)
print(
    f"gas_ct model {ct:6.2f} | EIA923 {g['gas_ct']:6.2f} | err {ct - g['gas_ct']:+6.2f}"
)
print(
    f"gas_st model {st:6.2f} | EIA923 {g['gas_st']:6.2f} | err {st - g['gas_st']:+6.2f}"
)
print(
    f"  CC_REGULAR {twh.get('CC_REGULAR', 0):.2f}  CC_CHP {twh.get('CC_CHP', 0):.2f}"
    f"  CT_PEAKER {twh.get('CT_PEAKER', 0):.2f}  CT_CHP {twh.get('CT_CHP', 0):.2f}"
)

# CA-zone (NP15/ZP26/SP15) demand-weighted monthly LMP
ca = df[df.zone.isin(["NP15", "ZP26", "SP15"])].copy()
# one price per zone-hour; weight by zone load (use mw sum per zone-hour as proxy weight)
zh = (
    ca.groupby(["zone", "hour"])
    .agg(lmp=("lmp", "first"), load=("mw", "sum"))
    .reset_index()
)
zh["month"] = (zh.hour // (8760 // 12)).clip(upper=11) + 1
# better month mapping via timestamp
hours = np.arange(8760)
mon = pd.to_datetime("2024-01-01") + pd.to_timedelta(hours, "h")
month_of = dict(zip(hours, mon.month))
zh["month"] = zh.hour.map(month_of)
m = zh.groupby("month").apply(
    lambda x: np.average(x.lmp, weights=x.load.clip(lower=1)), include_groups=False
)
ann = np.average(zh.lmp, weights=zh.load.clip(lower=1))
print(f"CA-zone annual LMP (load-wt): {ann:.2f}")
print("monthly:", " ".join(f"{mm}:{v:.0f}" for mm, v in m.items()))
