"""FFR-4A: measured EIA-860 annual-build record per ISO x entry tech.

Reproduces data.build_throughput.max_annual_build_gw_by_tech's construction but
returns the FULL annual COD series, so the ladder's own identifying statistic
(how often a tech sets a NEW annual-build maximum, and by what ratio) can be
measured from the same source the seed comes from.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, "src")

from market_sim.data.build_throughput import _THROUGHPUT_THERMAL_TECHS  # noqa: E402
from market_sim.data.fleet import BA_CODE_TO_ISO, _map_fuel_type  # noqa: E402

ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]


def annual_build_mw(vintage_dir: Path) -> pd.DataFrame:
    """Annual COD nameplate MW by (iso, tech, operating year)."""
    plants = pd.read_parquet(vintage_dir / "eia860_plant.parquet")[
        ["Plant Code", "Balancing Authority Code"]
    ].drop_duplicates("Plant Code")
    frames = []
    gens = pd.read_parquet(vintage_dir / "eia860_generator_operable.parquet")
    gens = gens.assign(
        tech=[
            _map_fuel_type(None, es, pm)
            for es, pm in zip(gens["Energy Source 1"], gens["Prime Mover"])
        ]
    )
    gens = gens[gens["tech"].isin(_THROUGHPUT_THERMAL_TECHS)]
    frames.append(gens[["Plant Code", "Nameplate Capacity (MW)", "Operating Year", "tech"]])
    for sheet, tech in (
        ("eia860_solar_operable.parquet", "solar"),
        ("eia860_wind_operable.parquet", "wind"),
    ):
        p = vintage_dir / sheet
        if not p.exists():
            continue
        frames.append(
            pd.read_parquet(p).assign(tech=tech)[
                ["Plant Code", "Nameplate Capacity (MW)", "Operating Year", "tech"]
            ]
        )
    df = pd.concat(frames, ignore_index=True).merge(plants, on="Plant Code", how="left")
    df["iso"] = df["Balancing Authority Code"].map(BA_CODE_TO_ISO)
    df["year"] = pd.to_numeric(df["Operating Year"], errors="coerce")
    df["mw"] = pd.to_numeric(df["Nameplate Capacity (MW)"], errors="coerce")
    df = df.dropna(subset=["iso", "year", "mw"])
    return (
        df.groupby(["iso", "tech", "year"])["mw"].sum().reset_index().sort_values("year")
    )


def ratchet_stats(series: dict[int, float], lo: int, hi: int) -> dict:
    """Empirical ladder statistics over the closed COD-year window [lo, hi].

    For each year Y in the window with at least one prior year of record, the
    'ladder ratio' r_Y = D_Y / max(D_{<Y}) is the quantity the growth ladder
    bounds by K. A NEW MAXIMUM is r_Y > 1.
    """
    years = [y for y in range(lo, hi + 1)]
    vals = [float(series.get(y, 0.0)) for y in years]
    ratios = []
    new_max = 0
    running = vals[0]
    for i in range(1, len(vals)):
        if running > 0:
            ratios.append(vals[i] / running)
            if vals[i] > running:
                new_max += 1
        running = max(running, vals[i])
    return {
        "annual_mw": {y: round(v, 1) for y, v in zip(years, vals)},
        "n_eligible_years": len(ratios),
        "n_new_max": new_max,
        "ratios": [round(r, 3) for r in ratios],
        "max_ratio": round(max(ratios), 3) if ratios else None,
        "seed_gw": round(max(vals) / 1000.0, 3),
    }


def main() -> None:
    out = {}
    for vintage in (2020, 2024):
        vdir = Path("data/raw/eia-860") / f"vintage_{vintage}"
        if not vdir.exists():
            continue
        df = annual_build_mw(vdir)
        lo, hi = vintage - 9, vintage  # ENTRY_THROUGHPUT_WINDOW_YEARS = 10
        v_out = {}
        for iso in ISOS:
            sub = df[df["iso"] == iso]
            per_tech = {}
            for tech in ("wind", "solar", "gas_cc", "gas_ct", "coal", "nuclear"):
                s = sub[sub["tech"] == tech]
                if s.empty:
                    continue
                per_tech[tech] = ratchet_stats(
                    dict(zip(s["year"].astype(int), s["mw"])), lo, hi
                )
            v_out[iso] = per_tech
        out[f"vintage_{vintage}"] = {"window": [lo, hi], "isos": v_out}
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
