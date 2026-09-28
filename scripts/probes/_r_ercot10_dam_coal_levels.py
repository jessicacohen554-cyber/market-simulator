"""R-ERCOT-10 phase-0 probe: per-plant PRB coal DAM energy-offer LEVELS by delivery year.

Zero LP. Reads the on-disk 60-Day DAM Gen Resource Data disclosures
(``data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_<posting>*.parquet`` for
2018-2022 postings, ``data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*``
for 2023+) and reports, per PRB plant and delivery year:

* ``hsl_twh``   : sum over hours of HSL for ONLINE-status rows (available energy proxy)
* ``offered_share`` : mean(max curve MW) / mean(HSL) over online rows with any curve
* ``p50_price`` : MW-increment-weighted median price of curve segments above LSL
                  (points <= -249 excluded: self-schedule floor)
* ``p75_price`` : same, 75th pct

Diagnostic only; nothing registered, no config touched.
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
PLANTS = {"WAP": "W A Parish", "FPPYD": "Fayette", "MLSES": "Martin Lake", "SCES": "Sandy Creek",
          "LEG": "Limestone", "OGSES": "Oak Grove", "COLETO": "Coleto", "SANMIGL": "San Miguel",
          "TNP_ONE": "Major Oak", "CALAVERS": "JK Spruce"}
MW = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
PR = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]
COLS = ["Delivery Date", "Hour Ending", "Resource Name", "Resource Type", "HSL", "LSL",
        "Resource Status", "Awarded Quantity"] + MW + PR


def files() -> list[str]:
    """All on-disk DAM Gen Resource Data parquets."""
    a = glob.glob(str(REPO / "data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_*.parquet"))
    b = glob.glob(str(REPO / "data/raw/ercot/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_*.parquet"))
    return sorted(a + b)


def load() -> pd.DataFrame:
    """Load CLLIG rows from every disclosure file."""
    out = []
    for f in files():
        t = pq.read_table(f, columns=COLS, filters=[("Resource Type", "=", "CLLIG")]).to_pandas()
        out.append(t)
    d = pd.concat(out, ignore_index=True)
    d["date"] = pd.to_datetime(d["Delivery Date"], format="%m/%d/%Y")
    d["year"] = d["date"].dt.year
    d["plant"] = d["Resource Name"].map(lambda r: next((v for k, v in PLANTS.items() if r.startswith(k)), None))
    return d.drop_duplicates(["Delivery Date", "Hour Ending", "Resource Name"])


def seg_stats(g: pd.DataFrame) -> tuple[float, float, float]:
    """MW-weighted p50/p75 of curve segment prices, and offered share."""
    M = g[MW].to_numpy(float)
    P = g[PR].to_numpy(float)
    lo = np.nan_to_num(g["LSL"].to_numpy(float))
    prev = np.maximum(np.concatenate([np.zeros((len(M), 1)), M[:, :-1]], axis=1), lo[:, None])
    inc = np.clip(np.nan_to_num(M) - prev, 0, None)
    ok = np.isfinite(P) & (P > -249) & (inc > 0)
    w, p = inc[ok], P[ok]
    if w.sum() == 0:
        return np.nan, np.nan, 0.0
    o = np.argsort(p)
    cw = np.cumsum(w[o]) / w.sum()
    share = np.nanmax(np.nan_to_num(M), axis=1).mean() / max(g["HSL"].mean(), 1e-9)
    return p[o][np.searchsorted(cw, 0.5)], p[o][np.searchsorted(cw, 0.75)], share


def main() -> None:
    """Print the per-plant, per-year table."""
    d = load()
    d = d[d["plant"].notna() & d["year"].between(2018, 2025)]
    on = d[d["Resource Status"].isin(["ON", "ONRUC", "ONREG", "ONDSR", "ONOPTOUT", "ONTEST", "ONEMR", "ONRR", "ONDSRREG", "FRRSUP"])]
    rows = []
    for (pl, y), g in on.groupby(["plant", "year"]):
        hrs = d[(d.plant == pl) & (d.year == y)]
        p50, p75, sh = seg_stats(g)
        rows.append(dict(plant=pl, year=y, hsl_online_twh=g["HSL"].sum() / 1e6,
                         hsl_all_twh=hrs["HSL"].fillna(0).sum() / 1e6,
                         awarded_twh=g["Awarded Quantity"].fillna(0).sum() / 1e6,
                         offered_share=round(sh, 3), p50=p50, p75=p75,
                         days=hrs["date"].nunique()))
    t = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print(t.round(3).to_string(index=False))
    print(on["Resource Status"].value_counts().head(10))


if __name__ == "__main__":
    sys.exit(main())
