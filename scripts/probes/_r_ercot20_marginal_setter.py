"""R-ERCOT-20 phase 0 (zero LP): which class/tranche sets the 2024 P1 dual, by actual-price band.

Reads the keeper's own 2024 leg (``unit_hourly_2024.parquet`` of the arm-A leg,
provenance SHA adfb6b34, whose ``system_2024.parquet`` is byte-identical to the
keeper bundle's) and the committed zonal RT actual. Per hour, the price-setter
is the partially-loaded unit (0 < mw < cap) whose mc is nearest the hour's
North-zone P1 price, within $0.50; otherwise the hour is labelled
``non-thermal`` (storage/renewable/reserve-coupled dual). Solves nothing.
Usage: python _r_ercot20_marginal_setter.py <unit_hourly_2024.parquet>
"""

from __future__ import annotations

import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts/probes")
from _r_ercot20_c3a_decomp import load_year  # noqa: E402

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

TOL = 0.50  # $/MWh: mc-to-price match tolerance for a partially-loaded unit


def main(path: str, year: int = 2024) -> None:
    """Print the setter mix per band and the setter's measured-HR cohort."""
    u = pd.read_parquet(path, columns=["unit_id", "plant_group", "fuel", "zone", "hour", "mw", "cap_mw", "mc"])
    u = u[(u.mw > 0.5) & (u.mw < u.cap_mw - 0.5)]
    zact = pd.read_parquet(RAW_DATA_DIR / "_validation-source/actual_lmp_zonal_ERCOT.parquet")
    df = load_year(year, zact)
    dh = df.demand.groupby(df.hour).sum()
    ms = (df.demand * df.price).groupby(df.hour).sum() / dh
    as_ = (df.demand * df.actual).groupby(df.hour).sum() / dh
    pz = df[df.zone == "North"].set_index("hour").price
    u = u.assign(p=u.hour.map(pz))
    u["dist"] = (u.mc - u.p).abs()
    best = u[u.dist < TOL].sort_values("dist").drop_duplicates("hour").set_index("hour")
    tr = best.unit_id.astype(str).str.rsplit("_", n=1).str[-1].str.replace(r"\d+$", "", regex=True)
    setter = (best.plant_group.astype(str).replace("", "other") + ":" + tr).reindex(dh.index).fillna("non-thermal")
    lvl = pd.cut(as_, [-np.inf, 15, 25, 40, 100, np.inf],
                 labels=["trough<=15", "15-25", "25-40", "40-100", "tight>100"])
    t = pd.DataFrame({"band": lvl, "setter": setter, "d": dh, "gap": (ms - as_) * dh})
    D = dh.sum()
    top = t.setter.value_counts().head(8).index
    t["s"] = t.setter.where(t.setter.isin(top), "other")
    mix = pd.crosstab(t.band, t.s, normalize="index").round(3)
    print(mix.to_string())
    g = t.groupby("s").agg(hours=("d", "size"), contrib=("gap", "sum"))
    g["contrib_usd"] = (g.contrib / D).round(3)
    print(g.drop(columns="contrib").sort_values("contrib_usd").to_string())
    rec = {"tol": TOL, "mix_by_band": json.loads(mix.to_json(orient="index")),
           "contrib_by_setter": json.loads(g.drop(columns="contrib").to_json(orient="index"))}
    with open("docs/records/ercot/r-ercot/r_ercot20_marginal_setter.json", "w") as f:
        json.dump(rec, f, indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
