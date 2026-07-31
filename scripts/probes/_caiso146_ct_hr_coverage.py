"""caiso-146 STEP 1 probe: coverage and exclusion audit of the CAISO measured
CT loaded-heat-rate artifact.

No LP. Answers the four questions the session prompt requires before any arm is
armed:

1. **Plant-row count** and how many the loader applies (``flag == "ok"``).
2. **Class capacity covered**, and — the number that actually matters for an
   offer swap — the covered share of the class's own **measured CAMPD energy**.
3. **The excluded rows and WHY**, partitioned into the three mechanically
   distinct causes: the plant has no CAMPD account at all (below the Part-75
   reporting boundary), it has one but no ``unitType == 'Combustion turbine'``
   unit, or its turbines never cleared the loaded-window screen.
4. **The measured-vs-model distribution in BOTH directions**, so a one-sided
   result is reported as one-sided rather than assumed to mirror NYISO's.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_caiso146_ct_hr_coverage.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import PROCESSED_DIR, RAW_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
TARGET_CLASS = "CT_PEAKER"
CT_UNIT_TYPE = "combustion turbine"
UNIT_DIR = RAW_DIR / "campd-unit-level"


def model_class_plants() -> pd.DataFrame:
    """Per-plant CT_PEAKER capacity and capacity-weighted eGRID heat rate."""
    fleet = load_fleet_from_csv(ISO, get_iso_config(ISO))
    rows: list[dict] = []
    for gen in fleet:
        if gen.plant_group != TARGET_CLASS:
            continue
        rows.append(
            {
                "plant_code": int(gen.plant_code or 0),
                "name": gen.name,
                "pmax_mw": float(gen.pmax_mw),
                "heat_rate": float(gen.heat_rate),
            }
        )
    df = pd.DataFrame(rows)
    df["hr_mw"] = df["heat_rate"] * df["pmax_mw"]
    out = df.groupby("plant_code", as_index=False).agg(
        pmax_mw=("pmax_mw", "sum"), hr_mw=("hr_mw", "sum"), name=("name", "first")
    )
    out["model_hr"] = out["hr_mw"] / out["pmax_mw"]
    return out.drop(columns="hr_mw").sort_values("pmax_mw", ascending=False)


def campd_ct_universe() -> tuple[pd.DataFrame, set[int]]:
    """Pooled CAMPD CT-unit energy per plant, and every plant id in the extracts."""
    frames: list[pd.DataFrame] = []
    all_ids: set[int] = set()
    for state in campd.states_for_iso(ISO):
        for year in YEARS:
            path = UNIT_DIR / f"{state}_{year}.parquet"
            if not path.exists():
                continue
            df = pd.read_parquet(
                path,
                columns=["facilityId", "unitId", "unitType", "grossLoad", "heatInput"],
            )
            df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
            all_ids |= set(df["facilityId"].dropna().astype(int).tolist())
            df = df[
                df["unitType"].astype(str).str.strip().str.casefold() == CT_UNIT_TYPE
            ]
            if not df.empty:
                frames.append(df)
    pooled = pd.concat(frames, ignore_index=True)
    pooled = pooled.dropna(subset=["grossLoad"])
    pooled = pooled[pooled["grossLoad"] > 0.0]
    energy = (
        pooled.groupby("facilityId", as_index=False)["grossLoad"]
        .sum()
        .rename(columns={"facilityId": "plant_code", "grossLoad": "campd_gross_mwh"})
    )
    energy["plant_code"] = energy["plant_code"].astype(int)
    return energy, all_ids


def main() -> int:
    art = pd.read_csv(PROCESSED_DIR / f"campd_ct_heat_rates_{ISO}.csv")
    units = pd.read_csv(PROCESSED_DIR / f"campd_ct_heat_rates_{ISO}_units.csv")
    fleet = model_class_plants()
    ct_energy, campd_ids = campd_ct_universe()

    ok = art[art["flag"] == "ok"]
    print("=" * 78)
    print(
        f"1. ARTIFACT — {len(art)} plant rows, {len(ok)} applied (flag=='ok'), "
        f"{len(art) - len(ok)} flagged out"
    )
    print(f"   per-unit detail rows: {len(units)}")
    if len(art) != len(ok):
        print(art[art["flag"] != "ok"].to_string(index=False))

    total_mw = float(fleet["pmax_mw"].sum())
    cov_mw = float(ok["class_capacity_mw"].sum())
    print("=" * 78)
    print(
        f"2. COVERAGE — capacity {cov_mw:,.0f} / {total_mw:,.0f} MW "
        f"({100 * cov_mw / total_mw:.1f} %), plants {len(ok)} / {len(fleet)}"
    )

    # Energy basis: covered share of the class's own metered CAMPD CT energy.
    merged = fleet.merge(ct_energy, on="plant_code", how="left")
    merged["campd_gross_mwh"] = merged["campd_gross_mwh"].fillna(0.0)
    merged["covered"] = merged["plant_code"].isin(set(ok["plant_code"]))
    e_tot = float(merged["campd_gross_mwh"].sum())
    e_cov = float(merged.loc[merged["covered"], "campd_gross_mwh"].sum())
    print(
        f"   metered CAMPD CT energy {e_cov / 1e6:,.3f} / {e_tot / 1e6:,.3f} TWh "
        f"({100 * e_cov / e_tot:.1f} % of the class's own measured energy)"
    )

    print("=" * 78)
    print("3. EXCLUSIONS — why each uncovered plant is uncovered")
    unc = merged[~merged["covered"]].copy()

    def _cause(r: pd.Series) -> str:
        if int(r["plant_code"]) not in campd_ids:
            return "A_no_campd_account"
        if float(r["campd_gross_mwh"]) <= 0.0:
            return "B_campd_but_no_CT_unit"
        return "C_no_loaded_window"

    unc["cause"] = unc.apply(_cause, axis=1)
    grp = unc.groupby("cause").agg(
        plants=("plant_code", "size"),
        mw=("pmax_mw", "sum"),
        campd_gwh=("campd_gross_mwh", lambda s: s.sum() / 1e3),
        model_hr_capwt=("model_hr", "mean"),
    )
    grp["pct_class_mw"] = 100 * grp["mw"] / total_mw
    print(grp.to_string())
    print()
    print("   uncovered plants > 20 MW (largest 20):")
    big = unc.sort_values("pmax_mw", ascending=False).head(20)
    print(
        big[
            ["plant_code", "name", "pmax_mw", "model_hr", "campd_gross_mwh", "cause"]
        ].to_string(index=False)
    )
    print(
        f"   uncovered size profile: median {unc['pmax_mw'].median():.1f} MW, "
        f"p90 {unc['pmax_mw'].quantile(0.9):.1f} MW, max {unc['pmax_mw'].max():.1f} MW"
    )
    print(
        f"   covered   size profile: median "
        f"{merged.loc[merged['covered'], 'pmax_mw'].median():.1f} MW"
    )
    # Selection check: is the uncovered set systematically dearer/cheaper on paper?
    print(
        f"   model eGRID HR — covered cap-wt "
        f"{np.average(merged.loc[merged['covered'], 'model_hr'], weights=merged.loc[merged['covered'], 'pmax_mw']):.3f}"
        f" vs uncovered cap-wt "
        f"{np.average(unc['model_hr'], weights=unc['pmax_mw']):.3f} MMBtu/MWh"
    )

    print("=" * 78)
    print("4. DISTRIBUTION — measured vs model, BOTH directions")
    d = ok.copy()
    d["delta"] = d["heat_rate"] - d["model_heat_rate_egrid"]
    cheaper = d[d["delta"] < 0]
    dearer = d[d["delta"] > 0]
    print(
        f"   cheaper (measured < model): {len(cheaper)} plants, "
        f"{cheaper['class_capacity_mw'].sum():,.0f} MW"
    )
    print(
        f"   dearer  (measured > model): {len(dearer)} plants, "
        f"{dearer['class_capacity_mw'].sum():,.0f} MW"
    )
    print(
        f"   |delta| > 0.5 MMBtu/MWh: {(d['delta'].abs() > 0.5).sum()} plants; "
        f"> 1.0: {(d['delta'].abs() > 1.0).sum()}"
    )
    w = d["class_capacity_mw"].to_numpy(float)
    print(
        f"   capacity-weighted delta {np.average(d['delta'], weights=w):+.3f} "
        f"MMBtu/MWh ({100 * np.average(d['delta'], weights=w) / np.average(d['model_heat_rate_egrid'], weights=w):+.1f} %)"
    )
    g = d["gross_mwh"].to_numpy(float)
    print(
        f"   generation-weighted delta {np.average(d['delta'], weights=g):+.3f} "
        f"MMBtu/MWh"
    )
    print(
        f"   ratio model/measured: min {d['model_over_measured'].min():.3f}, "
        f"p25 {d['model_over_measured'].quantile(0.25):.3f}, "
        f"median {d['model_over_measured'].median():.3f}, "
        f"p75 {d['model_over_measured'].quantile(0.75):.3f}, "
        f"max {d['model_over_measured'].max():.3f}"
    )
    print()
    print("   largest 8 moves by |delta| x capacity:")
    d["impact"] = d["delta"].abs() * d["class_capacity_mw"]
    print(
        d.sort_values("impact", ascending=False)
        .head(8)[
            [
                "plant_code",
                "plant_name",
                "class_capacity_mw",
                "heat_rate",
                "model_heat_rate_egrid",
                "delta",
            ]
        ]
        .to_string(index=False)
    )
    print()
    print("   the two DEARER rows in full:")
    print(
        dearer[
            [
                "plant_code",
                "plant_name",
                "class_capacity_mw",
                "n_units",
                "loaded_hours",
                "heat_rate",
                "model_heat_rate_egrid",
            ]
        ].to_string(index=False)
    )
    print()
    print("   band-edge rows (measured < 7.0 or > 15.0 MMBtu/MWh):")
    edge = d[(d["heat_rate"] < 7.0) | (d["heat_rate"] > 15.0)]
    print(
        edge[
            [
                "plant_code",
                "plant_name",
                "class_capacity_mw",
                "n_units",
                "loaded_hours",
                "gross_mwh",
                "heat_rate",
                "model_heat_rate_egrid",
            ]
        ].to_string(index=False)
    )
    for code in edge["plant_code"]:
        u = units[units["plant_code"] == code]
        print(f"   -- plant {code} units --")
        print(u.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
