"""pjm-h14 phase 0f — read PJM's ACTUAL model coal tranches out of the fleet builder.

ZERO LP (rule 29 ``[R-SCREEN]`` clause (0), surviving as practice):
``run_year(..., fleet_only=True)`` over the designated keeper pair's own committed
recipes. This removes every inference from the census: it reports, per coal plant
and per solve year, the must-run / committed / economic / peak tranche capacities
the LP is actually handed, and whether that plant's shares came from the CAMPD
artifact or from ``campd_bins._DEFAULT_TRANCHE_PCT_BY_GROUP``.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

CACHE = Path("/tmp/claude-0/h14/fleet")
BUNDLES = {
    2020: "results/calibration/pjm_h13_meritalloc_touchpoint",
    2021: "results/calibration/pjm_h13_meritalloc_touchpoint",
    2022: "results/calibration/pjm_h13_meritalloc_touchpoint",
    2023: "results/calibration/pjm_h13_meritalloc_span",
    2024: "results/calibration/pjm_h13_meritalloc_span",
    2025: "results/calibration/pjm_h13_meritalloc_span",
}
BENCH = REPO / "frontend/data/backcast/bench/PJM"
POOLED = REPO / "data/raw/_processed-legacy/thermal_tranches_PJM.csv"


def fleet_rows(year: int) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"coal_tranches_{year}.parquet"
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
        grp = getattr(g, "plant_group", "") or ""
        if not str(grp).startswith("COAL"):
            continue
        uid = str(getattr(g, "unit_id", getattr(g, "id", "")))
        rows.append(dict(
            year=year,
            plant_code=int(getattr(g, "plant_code", 0) or 0),
            name=str(getattr(g, "name", "")),
            group=str(grp),
            unit_id=uid,
            suffix=uid.rpartition("_")[2],
            pmax=float(getattr(g, "pmax_mw", 0.0) or 0.0),
            pmin=float(getattr(g, "pmin_mw", 0.0) or 0.0),
            hr=float(getattr(g, "heat_rate", 0.0) or 0.0),
            vom=float(getattr(g, "vom", 0.0) or 0.0),
            zone=str(getattr(g, "zone", "")),
        ))
    df = pd.DataFrame(rows)
    df.to_parquet(path)
    return df


def main() -> None:
    pooled = pd.read_csv(POOLED)
    covered = set(pooled[pooled["plant_group"].astype(str) == "COAL"]["plant_code"].astype(int))

    for year in sorted(BUNDLES):
        df = fleet_rows(year)
        if not len(df):
            print(f"{year}: NO COAL ROWS")
            continue
        df["band"] = df["suffix"].str.replace(r"\d+$", "", regex=True)
        piv = df.pivot_table(index="plant_code", columns="band", values="pmax", aggfunc="sum").fillna(0.0)
        cap = df.groupby("plant_code")["pmax"].sum()
        nm = df.groupby("plant_code")["name"].first()
        piv["total"] = cap
        piv["covered"] = [c in covered for c in piv.index]
        piv["mr_pct"] = 100.0 * piv.get("mustrun", 0.0) / piv["total"].replace(0, np.nan)
        piv["name"] = nm
        bench = json.load(gzip.open(BENCH / f"{year}.json.gz"))["bench"]["plants"]
        piv["campd_TWh"] = [float((bench.get(str(c)) or {}).get("c_ann") or 0.0) for c in piv.index]
        piv["mustrun_TWh"] = piv.get("mustrun", 0.0) * 8760 / 1e6
        print(f"\n=== {year}  ({len(piv)} coal plants, {piv['total'].sum():,.0f} MW model capacity)")
        agg = piv.groupby("covered")[["total", "mustrun_TWh", "campd_TWh"]].sum()
        agg["n"] = piv.groupby("covered").size()
        agg["mean_mr_pct"] = piv.groupby("covered")["mr_pct"].mean()
        print(agg.to_string(float_format=lambda v: f"{v:12.3f}"))
        if year in (2020, 2021):
            worst = piv[~piv["covered"]].sort_values("mustrun_TWh", ascending=False).head(10)
            print("  uncovered cohort, by asserted must-run block:")
            print(worst[["name", "total", "mr_pct", "mustrun_TWh", "campd_TWh"]]
                  .to_string(float_format=lambda v: f"{v:9.2f}"))


if __name__ == "__main__":
    main()
