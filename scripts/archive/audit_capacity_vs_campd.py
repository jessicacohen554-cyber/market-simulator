#!/usr/bin/env python3
"""Audit EIA-860 capacity vs CAMPD observed generation across ISOs.

Compares CAMPD facility-level peak gross generation against the EIA-860
capacity of CAMPD-monitored generators at each plant.  Identifies where
the LP's implied pmax is too tight and classifies root causes:

  Cat 1 — CC summer derate: nameplate > summer, model uses summer.
  Cat 2 — CAMPD exceeds nameplate: cold-weather over-rating / data issue.
  Cat 3 — Multi-technology facility: model splits, CAMPD sums.
  Cat 4 — Within nameplate, above summer.

Usage:
    python scripts/archive/audit_capacity_vs_campd.py [--year 2023] [--iso CAISO]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.paths import RAW_DATA_DIR, active_eia860_dir

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ISO -> US states
ISO_STATES: dict[str, list[str]] = {
    "ERCOT": ["TX"],
    "CAISO": ["CA"],
    "PJM": [
        "PA",
        "NJ",
        "MD",
        "DE",
        "VA",
        "WV",
        "OH",
        "IN",
        "IL",
        "MI",
        "KY",
        "NC",
        "DC",
    ],
    "MISO": [
        "IA",
        "IL",
        "IN",
        "MI",
        "MN",
        "MO",
        "WI",
        "AR",
        "MS",
        "LA",
        "TX",
        "MT",
        "ND",
        "SD",
        "KY",
    ],
    "NYISO": ["NY"],
    "NEISO": ["CT", "MA", "ME", "NH", "RI", "VT"],
}

CAMPD_UNIT_PLANT_REMAP: dict[tuple[int, str], int] = {
    (315, "CT1"): 62115,
    (315, "CT2"): 62115,
    (335, "CT1"): 62116,
    (335, "CT2"): 62116,
}

# Prime movers monitored by CAMPD (fossil combustion only)
CAMPD_PRIME_MOVERS = {"ST", "GT", "CT", "CA", "CS", "CE", "IC", "CC", "OT"}

# Non-CAMPD energy sources (renewables, nuclear, storage, hydro)
NON_CAMPD_ENERGY = {
    "SUN",
    "WND",
    "WAT",
    "NUC",
    "MWH",
    "GEO",
    "PUR",
    "HPS",
}


def load_eia860_all() -> pd.DataFrame:
    """Load all EIA-860 operable generators."""
    path = active_eia860_dir() / "eia860_generator_operable.parquet"
    df = pd.read_parquet(path)
    rename = {
        "Plant Code": "plant_code",
        "Plant Name": "plant_name",
        "Generator ID": "generator_id",
        "Technology": "technology",
        "Prime Mover": "prime_mover",
        "Nameplate Capacity (MW)": "nameplate_mw",
        "Summer Capacity (MW)": "summer_mw",
        "Winter Capacity (MW)": "winter_mw",
        "State": "state",
        "Energy Source 1": "energy_source",
        "Status": "status",
    }
    for old, new in rename.items():
        if old in df.columns:
            df = df.rename(columns={old: new})
    df["plant_code"] = pd.to_numeric(df["plant_code"], errors="coerce")
    df = df[df["plant_code"].notna()].copy()
    df["plant_code"] = df["plant_code"].astype(int)
    for col in ("nameplate_mw", "summer_mw", "winter_mw"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    return df


def classify_generator(row: pd.Series) -> str:
    """Classify a generator into a model-relevant group."""
    tech = str(row.get("technology", "")).lower()
    pm = str(row.get("prime_mover", "")).upper()
    es = str(row.get("energy_source", "")).upper()
    if "combined cycle" in tech:
        return "CC"
    if pm in ("GT", "CT") or "combustion turbine" in tech:
        return "CT"
    if pm == "ST":
        if es in ("BIT", "SUB", "LIG", "RC", "WC", "ANT", "SC") or "coal" in tech:
            return "COAL"
        if es in ("NG", "BFG", "OG"):
            return "ST_GAS"
        if es in ("DFO", "RFO", "JF", "KER", "PC", "WO"):
            return "ST_OIL"
        return "ST_OTHER"
    if pm == "IC":
        return "IC"
    if pm == "CA":
        return "CC"  # combined cycle steam portion
    return "OTHER"


def is_campd_monitored(row: pd.Series) -> bool:
    """Whether this generator is likely monitored by CAMPD."""
    pm = str(row.get("prime_mover", "")).upper()
    es = str(row.get("energy_source", "")).upper()
    if es in NON_CAMPD_ENERGY:
        return False
    if pm in CAMPD_PRIME_MOVERS:
        return True
    return False


def load_campd_hourly_for_states(
    states: list[str],
    year: int,
) -> pd.DataFrame:
    """Load CAMPD unit-level hourly data for the given states and year."""
    unit_dir = RAW_DATA_DIR / "campd-unit-level"
    frames = []
    for st in states:
        path = unit_dir / f"{st}_{year}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        col_map = {}
        for c in df.columns:
            lc = c.lower().replace(" ", "_")
            if "facility" in lc and "id" in lc:
                col_map[c] = "facility_id"
            elif "unit" in lc and "id" in lc:
                col_map[c] = "unit_id"
            elif "gross" in lc and "load" in lc:
                col_map[c] = "gross_mw"
        df = df.rename(columns=col_map)
        if "facility_id" not in df.columns or "gross_mw" not in df.columns:
            continue
        if "unit_id" not in df.columns:
            df["unit_id"] = "ALL"
        df["facility_id"] = pd.to_numeric(df["facility_id"], errors="coerce")
        df["gross_mw"] = pd.to_numeric(df["gross_mw"], errors="coerce").fillna(0.0)
        frames.append(df[["facility_id", "unit_id", "gross_mw"]].copy())
    if not frames:
        return pd.DataFrame(columns=["facility_id", "unit_id", "gross_mw"])
    return pd.concat(frames, ignore_index=True)


def remap_campd_to_plant(campd: pd.DataFrame) -> pd.DataFrame:
    """Apply split-facility remap."""
    fac = campd["facility_id"].values
    uid = campd["unit_id"].astype(str).values
    plant_ids = np.array(
        [
            CAMPD_UNIT_PLANT_REMAP.get(
                (int(f) if not pd.isna(f) else 0, u), int(f) if not pd.isna(f) else 0
            )
            for f, u in zip(fac, uid)
        ]
    )
    campd = campd.copy()
    campd["plant_id"] = plant_ids
    return campd


def run_audit(year: int, iso_filter: str | None = None) -> pd.DataFrame:
    """Run the capacity vs CAMPD audit."""
    eia = load_eia860_all()
    eia["gen_class"] = eia.apply(classify_generator, axis=1)
    eia["campd_monitored"] = eia.apply(is_campd_monitored, axis=1)

    # Plant-level: ALL CAMPD-monitored capacity
    campd_gens = eia[eia["campd_monitored"]].copy()
    plant_all_cap = (
        campd_gens.groupby("plant_code")
        .agg(
            plant_name=("plant_name", "first"),
            state=("state", "first"),
            total_nameplate_mw=("nameplate_mw", "sum"),
            total_summer_mw=("summer_mw", "sum"),
            total_winter_mw=("winter_mw", "sum"),
            n_campd_gens=("generator_id", "count"),
            technologies=("technology", lambda x: "|".join(sorted(set(x.dropna())))),
            gen_classes=("gen_class", lambda x: "|".join(sorted(set(x.dropna())))),
        )
        .reset_index()
    )

    # Per-class capacity at each plant (for identifying dominant class)
    class_cap = (
        campd_gens.groupby(["plant_code", "gen_class"])
        .agg(
            class_nameplate=("nameplate_mw", "sum"),
            class_summer=("summer_mw", "sum"),
        )
        .reset_index()
    )
    dominant = (
        class_cap.sort_values("class_nameplate", ascending=False)
        .groupby("plant_code")
        .first()
        .reset_index()
        .rename(columns={"gen_class": "dominant_class"})
    )

    plant_all_cap = plant_all_cap.merge(
        dominant[["plant_code", "dominant_class", "class_nameplate", "class_summer"]],
        on="plant_code",
        how="left",
    )

    # CC capacity at each plant (for summer derate analysis)
    cc_cap = (
        campd_gens[campd_gens["gen_class"] == "CC"]
        .groupby("plant_code")
        .agg(
            cc_nameplate=("nameplate_mw", "sum"),
            cc_summer=("summer_mw", "sum"),
            cc_winter=("winter_mw", "sum"),
        )
        .reset_index()
    )
    plant_all_cap = plant_all_cap.merge(cc_cap, on="plant_code", how="left")
    for c in ("cc_nameplate", "cc_summer", "cc_winter"):
        plant_all_cap[c] = plant_all_cap[c].fillna(0.0)

    # Model capacity: the model uses net_summer per generator (fleet.py:3154)
    # and sums per plant. For CC plants with cc_nameplate_summer_derate=True,
    # winter capacity = nameplate, summer = derated. Without it, year-round = summer.
    plant_all_cap["model_capacity_mw"] = plant_all_cap["total_summer_mw"].where(
        plant_all_cap["total_summer_mw"] > 0,
        plant_all_cap["total_nameplate_mw"],
    )

    # Multi-class flag
    plant_all_cap["is_multi_class"] = plant_all_cap["gen_classes"].str.contains(r"\|")

    isos = [iso_filter] if iso_filter else list(ISO_STATES.keys())
    all_results = []

    for iso in isos:
        states = ISO_STATES.get(iso)
        if not states:
            continue

        print(f"\n{'=' * 80}")
        print(f"  ISO: {iso}  |  Year: {year}  |  States: {', '.join(states)}")
        print(f"{'=' * 80}")

        campd = load_campd_hourly_for_states(states, year)
        if campd.empty:
            print(f"  No CAMPD data for {iso} {year}")
            continue

        campd = remap_campd_to_plant(campd)

        # Hourly plant totals (sum across units within the same hour)
        # CAMPD has one row per (facility, unit, hour). We need to first
        # determine the hour index. Since we don't have explicit hour cols
        # in all files, use the row order within each (facility,unit) group
        # as a proxy for "hour index". Instead, just aggregate per plant.
        #
        # Actually: sum all unit gross_mw at same plant to get plant-hour total,
        # then take stats across those plant-hour totals.
        # But we don't have an explicit hour column reliably. So let's just
        # compute: for each plant, what is the maximum SINGLE UNIT gross_mw
        # and what is total gross_mwh. The peak issue is about individual
        # hours where plant total exceeds capacity.
        #
        # Since the unit-level files have one row per unit per hour, we need
        # a row index to identify hours. Let's check the columns.

        # Simpler approach: use facility-level data which is already hourly.
        fac_dir = RAW_DATA_DIR / "campd-facility-level"
        fac_frames = []
        for st in states:
            fpath = fac_dir / f"{st}_{year}.parquet"
            if not fpath.exists():
                continue
            fdf = pd.read_parquet(fpath)
            col_map = {}
            for c in fdf.columns:
                lc = c.lower().replace(" ", "_")
                if "facility" in lc and "id" in lc:
                    col_map[c] = "facility_id"
                elif "gross" in lc and "load" in lc:
                    col_map[c] = "gross_mw"
            fdf = fdf.rename(columns=col_map)
            if "facility_id" not in fdf.columns or "gross_mw" not in fdf.columns:
                continue
            fdf["facility_id"] = pd.to_numeric(fdf["facility_id"], errors="coerce")
            fdf["gross_mw"] = pd.to_numeric(fdf["gross_mw"], errors="coerce").fillna(
                0.0
            )
            fac_frames.append(fdf[["facility_id", "gross_mw"]].copy())

        if not fac_frames:
            print("  No facility-level CAMPD data")
            continue

        fac_data = pd.concat(fac_frames, ignore_index=True)
        # Facility-level is already summed across units at the facility
        # Just need to handle the split-plant remap: for split facilities,
        # the facility-level data includes ALL units. We cannot split it.
        # Flag split plants and use unit-level data for them instead.

        # For non-split facilities: use facility-level directly
        split_facs = set(f for f, _ in CAMPD_UNIT_PLANT_REMAP)
        fac_nonsplit = fac_data[~fac_data["facility_id"].isin(split_facs)]

        plant_stats_nonsplit = (
            fac_nonsplit.groupby("facility_id")["gross_mw"]
            .agg(
                peak_gross_mw="max",
                p999_gross_mw=lambda x: x.quantile(0.999),
                p99_gross_mw=lambda x: x.quantile(0.99),
                p95_gross_mw=lambda x: x.quantile(0.95),
                mean_gross_mw="mean",
                hours_positive=lambda x: (x > 0).sum(),
                total_hours="count",
            )
            .reset_index()
            .rename(columns={"facility_id": "plant_id"})
        )

        # For split facilities: use unit-level, remap, and aggregate by hour
        # We already have unit-level campd loaded. Filter to split plants.
        campd_split = campd[campd["facility_id"].isin(split_facs)].copy()
        if not campd_split.empty:
            # group by plant_id and compute stats on gross_mw
            # (each row is one unit-hour, so we need to sum units first)
            # Without hour index, take max per unit then note this is approximate
            split_stats = (
                campd_split.groupby("plant_id")["gross_mw"]
                .agg(
                    peak_gross_mw="max",
                    p999_gross_mw=lambda x: x.quantile(0.999),
                    p99_gross_mw=lambda x: x.quantile(0.99),
                    p95_gross_mw=lambda x: x.quantile(0.95),
                    mean_gross_mw="mean",
                    hours_positive=lambda x: (x > 0).sum(),
                    total_hours="count",
                )
                .reset_index()
            )
            plant_stats = pd.concat(
                [plant_stats_nonsplit, split_stats], ignore_index=True
            )
        else:
            plant_stats = plant_stats_nonsplit

        # Merge with EIA-860
        merged = plant_stats.merge(
            plant_all_cap, left_on="plant_id", right_on="plant_code", how="inner"
        )
        if merged.empty:
            print("  No matching plants")
            continue

        # Parasitic factors by class (~0.95 gas, ~0.90 coal)
        PARASITIC = {
            "CC": 0.95,
            "CT": 0.97,
            "COAL": 0.90,
            "ST_GAS": 0.94,
            "ST_OIL": 0.94,
            "IC": 0.97,
            "OTHER": 0.95,
        }
        merged["parasitic"] = merged["dominant_class"].map(PARASITIC).fillna(0.95)
        merged["est_peak_net_mw"] = merged["peak_gross_mw"] * merged["parasitic"]
        merged["est_p99_net_mw"] = merged["p99_gross_mw"] * merged["parasitic"]

        # Over-capacity ratios
        merged["peak_vs_total_nameplate"] = merged["est_peak_net_mw"] / merged[
            "total_nameplate_mw"
        ].clip(lower=1)
        merged["peak_vs_model"] = merged["est_peak_net_mw"] / merged[
            "model_capacity_mw"
        ].clip(lower=1)
        merged["nameplate_summer_gap_pct"] = (
            (merged["total_nameplate_mw"] - merged["total_summer_mw"])
            / merged["total_nameplate_mw"].clip(lower=1)
            * 100
        )
        merged["cc_summer_derate_pct"] = np.where(
            merged["cc_nameplate"] > 0,
            (merged["cc_nameplate"] - merged["cc_summer"])
            / merged["cc_nameplate"]
            * 100,
            0.0,
        )

        # Genuine over-model plants
        over = merged[merged["peak_vs_model"] > 1.01].sort_values(
            "peak_vs_model", ascending=False
        )

        print(f"\n  Thermal plants matched: {len(merged)}")
        print(
            f"  Over model capacity (peak*parasitic > model_cap): "
            f"{len(over)} ({len(over) / max(len(merged), 1) * 100:.1f}%)"
        )

        # Classify root causes
        causes = []
        for _, r in over.iterrows():
            if r["peak_vs_total_nameplate"] > 1.05:
                # CAMPD grossly exceeds nameplate -> likely CAMPD data issue
                # or facility ID summing wrong plant
                cause = "CAMPD_DATA_MISMATCH"
            elif r["is_multi_class"] and r["peak_vs_total_nameplate"] <= 1.0:
                cause = "MULTI_TECH_CORRECT"
            elif r["cc_nameplate"] > 0 and r["cc_summer_derate_pct"] > 5:
                cause = "CC_SUMMER_DERATE"
            elif r["peak_vs_total_nameplate"] > 1.0:
                cause = "COLD_WEATHER_OVERRATING"
            else:
                cause = "SUMMER_CAP_ONLY"
            causes.append(cause)
        if not over.empty:
            over = over.copy()
            over["root_cause"] = causes

        if not over.empty:
            print("\n  --- Plants exceeding model capacity (sorted by ratio) ---")
            show_cols = [
                "plant_id",
                "plant_name",
                "dominant_class",
                "gen_classes",
                "total_nameplate_mw",
                "total_summer_mw",
                "peak_gross_mw",
                "est_peak_net_mw",
                "model_capacity_mw",
                "peak_vs_model",
                "peak_vs_total_nameplate",
                "root_cause",
            ]
            top = over.head(25)[show_cols].copy()
            top["plant_name"] = top["plant_name"].str[:35]
            top["peak_vs_model"] = top["peak_vs_model"].map("{:.3f}".format)
            top["peak_vs_total_nameplate"] = top["peak_vs_total_nameplate"].map(
                "{:.3f}".format
            )
            for c in (
                "total_nameplate_mw",
                "total_summer_mw",
                "peak_gross_mw",
                "est_peak_net_mw",
                "model_capacity_mw",
            ):
                top[c] = top[c].map("{:.0f}".format)
            print(top.to_string(index=False))

        # CC analysis
        cc_plants = merged[
            (merged["cc_nameplate"] > 0) & (merged["cc_summer_derate_pct"] > 3)
        ].sort_values("cc_summer_derate_pct", ascending=False)
        if not cc_plants.empty:
            print(
                f"\n  --- CC plants with >3% nameplate-to-summer gap "
                f"({len(cc_plants)} plants, {cc_plants['cc_nameplate'].sum():.0f} MW NP) ---"
            )
            cc_show = cc_plants.head(15)[
                [
                    "plant_id",
                    "plant_name",
                    "cc_nameplate",
                    "cc_summer",
                    "cc_summer_derate_pct",
                    "peak_vs_model",
                ]
            ].copy()
            cc_show["plant_name"] = cc_show["plant_name"].str[:35]
            cc_show["cc_summer_derate_pct"] = cc_show["cc_summer_derate_pct"].map(
                "{:.1f}%".format
            )
            cc_show["peak_vs_model"] = cc_show["peak_vs_model"].map("{:.3f}".format)
            for c in ("cc_nameplate", "cc_summer"):
                cc_show[c] = cc_show[c].map("{:.0f}".format)
            print(cc_show.to_string(index=False))

        # Root cause summary
        if not over.empty:
            print("\n  Root cause summary:")
            for cause, grp in over.groupby("root_cause"):
                mw_gap = (grp["est_peak_net_mw"] - grp["model_capacity_mw"]).sum()
                print(
                    f"    {cause:30s}  {len(grp):3d} plants  "
                    f"total excess: {mw_gap:+,.0f} MW"
                )

        merged["iso"] = iso
        all_results.append(merged)

    if not all_results:
        return pd.DataFrame()

    full = pd.concat(all_results, ignore_index=True)

    # Cross-ISO summary
    print(f"\n{'=' * 80}")
    print("  CROSS-ISO SUMMARY")
    print(f"{'=' * 80}")

    over_all = full[full["peak_vs_model"] > 1.01]
    by_iso = (
        over_all.groupby("iso")
        .agg(
            n_over=("plant_id", "count"),
            total_excess_mw=(
                "est_peak_net_mw",
                lambda x: (x - over_all.loc[x.index, "model_capacity_mw"]).sum(),
            ),
        )
        .reset_index()
    )
    print("\n  Over-capacity plants by ISO:")
    print(by_iso.to_string(index=False))

    if not over_all.empty:
        by_cause = over_all.groupby(
            over_all.apply(lambda r: _classify_cause(r), axis=1)
        ).agg(
            n_plants=("plant_id", "count"),
            total_excess_mw=(
                "est_peak_net_mw",
                lambda x: (x - over_all.loc[x.index, "model_capacity_mw"]).sum(),
            ),
        )
        print("\n  Over-capacity plants by root cause:")
        for cause, row in by_cause.iterrows():
            print(
                f"    {cause:35s}  {int(row['n_plants']):3d} plants  "
                f"excess: {row['total_excess_mw']:+,.0f} MW"
            )

    # Alamitos specifically
    alam = full[full["plant_id"] == 62115]
    if not alam.empty:
        r = alam.iloc[0]
        print("\n  --- ALAMITOS (62115) DETAIL ---")
        print(f"  CC nameplate: {r.get('cc_nameplate', 0):.0f} MW")
        print(f"  CC summer:    {r.get('cc_summer', 0):.0f} MW")
        print(f"  CC winter:    {r.get('cc_winter', 0):.0f} MW")
        print(f"  Model cap:    {r['model_capacity_mw']:.0f} MW (net_summer)")
        print(f"  CAMPD peak:   {r['peak_gross_mw']:.0f} MW gross")
        print(f"  Est net peak: {r['est_peak_net_mw']:.0f} MW")
        print(f"  Peak/model:   {r['peak_vs_model']:.3f}")
        print(f"  Summer derate:{r.get('cc_summer_derate_pct', 0):.1f}%")

    return full


def _classify_cause(row: pd.Series) -> str:
    """Classify root cause for a single over-capacity plant."""
    if row["peak_vs_total_nameplate"] > 1.05:
        return "CAMPD_DATA_MISMATCH"
    if row.get("is_multi_class", False) and row["peak_vs_total_nameplate"] <= 1.0:
        return "MULTI_TECH_CORRECT"
    if row.get("cc_nameplate", 0) > 0 and row.get("cc_summer_derate_pct", 0) > 5:
        return "CC_SUMMER_DERATE"
    if row["peak_vs_total_nameplate"] > 1.0:
        return "COLD_WEATHER_OVERRATING"
    return "SUMMER_CAP_ONLY"


def main():
    parser = argparse.ArgumentParser(
        description="Audit EIA-860 capacity vs CAMPD observed generation"
    )
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--iso", type=str, default=None)
    parser.add_argument("--out", type=str, default=None)
    args = parser.parse_args()

    result = run_audit(args.year, args.iso)

    if args.out and not result.empty:
        result.to_csv(args.out, index=False)
        print(f"\nResults written to {args.out}")


if __name__ == "__main__":
    main()
