"""Zero-LP hygiene census: ERCOT DAM-site membership against the keeper fleet.

Close-out wave 1, step 6 (``docs/backcast-closeout-plan-2026-10.md`` §3.5).
The Fusco class of miss (R-ERCOT-8: Jack Fusco 55357, 676 MW CC, EIA-860 BA
MISO, absent from the ERCOT fleet until the DAM crosswalk admitted it) is a
DAM resource with a real ERCOT HSL and no modelled EIA plant. For every year
2019–2025 this joins each thermal DAM site's p98 HSL (the crosswalk's own
rating construction, ``derive_ercot_thermal_dam_availability``) to the
reviewed crosswalk (``data/raw/reference/ercot-dam-plant-crosswalk.csv``) and
to the keeper's fleet for that year (plant codes carrying capacity in
``unit_marginal_<Y>.parquet``), and labels each site with p98 >= 50 MW:

* ``ok``           accepted site, plant in the year's fleet
* ``miss_accepted`` accepted site, plant NOT in the year's fleet (definite miss)
* ``unaccepted_in_fleet`` proposed plant is in the fleet (identity unresolved,
  energy covered; class-hour fallback)
* ``candidate``    no proposal, or the proposed plant is absent from the year's
  fleet, or the site is not in the crosswalk at all (Fusco-class candidate,
  needs adjudication)

Usage::

    uv run python scripts/probes/_ercot_closeout_hygiene_membership_census.py --out <dir>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import ERCOT_DAM_DISCLOSURE_DIRS  # noqa: E402

from scripts.data.derive_ercot_thermal_dam_availability import (  # noqa: E402
    RESTYPE_TO_CLASS,
    _RATING_QUANTILE,
    _site,
)

XWALK = REPO / "data/raw/reference/ercot-dam-plant-crosswalk.csv"
MIN_MW = 50.0
YEARS = tuple(range(2019, 2026))
COLS = [
    "Delivery Date",
    "Hour Ending",
    "Resource Name",
    "Resource Type",
    "HSL",
    "Resource Status",
    "Settlement Point Name",
]


def dam_sites(year: int) -> pd.DataFrame:
    """Per (class, site) p98 HSL for ``year`` across every disclosure dir."""
    frames = []
    for d in ERCOT_DAM_DISCLOSURE_DIRS:
        for p in sorted(Path(d).rglob(f"*60d_DAM_Gen_Resource_Data_{year}_*.parquet")):
            df = pd.read_parquet(p, columns=COLS)
            df = df[df["Resource Type"].isin(RESTYPE_TO_CLASS)]
            df = df[pd.to_datetime(df["Delivery Date"]).dt.year == year]
            frames.append(df)
    df = pd.concat(frames, ignore_index=True).drop_duplicates(
        ["Delivery Date", "Hour Ending", "Resource Name"]
    )
    df["cls"] = df["Resource Type"].map(RESTYPE_TO_CLASS)
    df["site"] = [_site(n, t) for n, t in zip(df["Resource Name"], df["Resource Type"])]
    ok = df[df["Resource Status"].ne("OUT") & (df["HSL"] > 0)]
    sh = ok.groupby(["cls", "site", "Delivery Date", "Hour Ending"])["HSL"].max()
    r = (
        sh.groupby(["cls", "site"])
        .quantile(_RATING_QUANTILE)
        .rename("p98_mw")
        .reset_index()
    )
    sp = ok.groupby("site")["Settlement Point Name"].first().rename("sp")
    days = ok.groupby("site")["Delivery Date"].nunique().rename("days_online")
    return r.merge(sp, on="site").merge(days, on="site")


def fleet_plants(year: int) -> set[int]:
    """Plant codes carrying capacity in the keeper's year-``year`` fleet."""
    d = pd.read_parquet(
        REPO
        / f"results/calibration/r_ercot24_span/hourly/unit_marginal_{year}.parquet",
        columns=["plant_code", "cap_mw"],
    )
    return set(d.loc[d["cap_mw"] > 0, "plant_code"].astype(int).unique()) - {0}


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    xw = pd.read_csv(XWALK)[["site", "plant_code", "plant_name", "accepted"]]
    rows = []
    for y in YEARS:
        s = dam_sites(y)
        s = s[s["p98_mw"] >= MIN_MW].merge(xw, on="site", how="left")
        fp = fleet_plants(y)
        pc = s["plant_code"]
        inf = pc.notna() & pc.fillna(-1).astype(int).isin(fp)
        acc = s["accepted"].fillna(0).astype(int).eq(1)
        s["label"] = "candidate"
        s.loc[acc & inf, "label"] = "ok"
        s.loc[acc & ~inf, "label"] = "miss_accepted"
        s.loc[~acc & inf, "label"] = "unaccepted_in_fleet"
        s.loc[s["accepted"].isna(), "label"] = "candidate"
        s.insert(0, "year", y)
        rows.append(s)
        print(
            y,
            s.groupby("label")["p98_mw"].agg(["size", "sum"]).round(0).to_dict("index"),
        )
    t = pd.concat(rows, ignore_index=True)
    t.to_csv(a.out / "hygiene_dam_membership.csv", index=False)
    flag = t[t["label"].isin(["miss_accepted", "candidate"])]
    piv = flag.pivot_table(
        index=["cls", "site", "plant_code", "plant_name", "label"],
        columns="year",
        values="p98_mw",
        aggfunc="first",
    )
    print(piv.round(0).to_string())


if __name__ == "__main__":
    main()
