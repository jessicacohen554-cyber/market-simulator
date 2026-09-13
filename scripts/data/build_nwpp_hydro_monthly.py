#!/usr/bin/env python3
"""Extract the NWPP footprint's EIA-923 monthly hydro net generation.

The input for NWPP-32's monthly hydro budget and the evidence for card N3
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §2.7, §6 row 6).  **Pure
extract** — a filter, a reshape and one EIA-860 nameplate join, no modelling,
no gap-filling, no rescaling (rules 13 ``[R-MEASURED]`` / 14 ``[R-ACCURATE]``).

Sources, both already committed:

* ``data/raw/_processed-legacy/eia923_monthly_generation.parquet`` — the wide
  twelve-month EIA-923 net-generation extract the model already reads
  (``market_sim.data.hydro.load_hydro_budget``).
* ``data/raw/eia-860/eia860_plant.parquet`` +
  ``eia860_generator_operable.parquet`` — the nameplate envelope and the
  ``Balancing Authority Code`` the footprint is defined on.

Population: ``prime_mover == "HY"`` (conventional hydro, fuel ``WAT``) in one of
the 17 NWPP balancing authorities.  **Pumped storage (``PS``) is excluded by
design**, matching ``load_hydro_budget``'s own population — the footprint holds
exactly one PS plant (314.0 MW, BPAT), reported separately by ``--include-ps``
for the record but never mixed into the budget population.

**The 2025 vintage is an EARLY RELEASE and this script does not hide that.**
EIA publishes the monthly EIA-923 (``M_12_<year>``) months after the year ends
and the full annual census the following autumn; at this pin
``EIA923_LATEST_FINAL_VINTAGE`` is 2024 and the committed 2025 rows carry only
the monthly-survey reporters — **25 of ~290 footprint hydro plants**.  Verified
2026-09-13 to be the newest 2025 vintage that exists: EIA's own
``archive/xls/f923_2025.zip`` (``EIA923_Schedules_2_3_4_5_M_12_2025_20FEB2026
.xlsx``) carries the identical 7,653 rows / 3,427 plants / 139 national HY
plants / 25 footprint HY plants.  The shortfall is therefore a **source**
state, not a repo gap, and the same one ``load_hydro_budget``'s ``backfill_year``
and ``monthly_target_mwh`` arguments document for CAISO/NEISO 2025.  Choosing
between those is NWPP-32's call; this script reports and never fills.

Usage:
    python scripts/data/build_nwpp_hydro_monthly.py
    python scripts/data/build_nwpp_hydro_monthly.py --year 2023 --year 2024
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

EIA923_PATH = RAW_DATA_DIR / "_processed-legacy" / "eia923_monthly_generation.parquet"
EIA860_PLANT = RAW_DATA_DIR / "eia-860" / "eia860_plant.parquet"
EIA860_GEN = RAW_DATA_DIR / "eia-860" / "eia860_generator_operable.parquet"
OUT_DIR = RAW_DATA_DIR / "nwpp-hydro"

NWPP_BAS: tuple[str, ...] = (
    "BPAT",
    "PACE",
    "PACW",
    "PGE",
    "PSEI",
    "AVA",
    "IPCO",
    "NWMT",
    "CHPD",
    "DOPD",
    "GCPD",
    "SCL",
    "TPWR",
    "AVRN",
    "GRID",
    "WAUW",
    "NEVP",
)

MONTHS: tuple[str, ...] = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)

# Hours per month, non-leap / leap — used ONLY to express a reported monthly
# energy as a capacity factor for the implausibility FLAGS below. No value in
# the committed extract is divided, scaled or reconstructed by it.
_HOURS = (744, 672, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)
_HOURS_LEAP = (744, 696, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744)


def _nameplate_by_plant() -> pd.DataFrame:
    """Conventional-hydro nameplate MW per plant, from EIA-860 operable gens."""
    gen = pd.read_parquet(
        EIA860_GEN, columns=["Plant Code", "Prime Mover", "Nameplate Capacity (MW)"]
    )
    hy = gen[gen["Prime Mover"] == "HY"]
    out = (
        hy.groupby("Plant Code")["Nameplate Capacity (MW)"]
        .sum()
        .rename("nameplate_mw_860")
        .reset_index()
        .rename(columns={"Plant Code": "plant_id"})
    )
    return out


def _plant_meta() -> pd.DataFrame:
    """Per-plant EIA-860 state / BA / name, for the footprint definition."""
    p = pd.read_parquet(
        EIA860_PLANT,
        columns=["Plant Code", "Plant Name", "State", "Balancing Authority Code"],
    )
    return p.rename(
        columns={
            "Plant Code": "plant_id",
            "Plant Name": "plant_name_860",
            "State": "state",
            "Balancing Authority Code": "ba_code_860",
        }
    ).drop_duplicates(subset="plant_id")


def build(years: tuple[int, ...], prime_movers: tuple[str, ...]) -> pd.DataFrame:
    """Return the long per-plant per-month extract for the footprint."""
    wide = pd.read_parquet(EIA923_PATH)
    sel = wide[
        wide["ba_code"].isin(NWPP_BAS)
        & wide["prime_mover"].isin(prime_movers)
        & wide["year"].isin(years)
    ].copy()

    long = sel.melt(
        id_vars=[
            "plant_id",
            "plant_name",
            "ba_code",
            "prime_mover",
            "fuel_type",
            "year",
            "netgen_annual_mwh",
        ],
        value_vars=[f"netgen_{m}_mwh" for m in MONTHS],
        var_name="month_col",
        value_name="netgen_mwh",
    )
    long["month"] = long["month_col"].map(
        {f"netgen_{m}_mwh": i + 1 for i, m in enumerate(MONTHS)}
    )
    long = long.drop(columns=["month_col"])

    long = long.merge(_nameplate_by_plant(), on="plant_id", how="left")
    long = long.merge(_plant_meta(), on="plant_id", how="left")

    hrs = long.apply(
        lambda r: (_HOURS_LEAP if int(r["year"]) % 4 == 0 else _HOURS)[
            int(r["month"]) - 1
        ],
        axis=1,
    )
    long["hours_in_month"] = hrs.astype("int64")
    long["capacity_factor"] = long["netgen_mwh"] / (
        long["nameplate_mw_860"] * long["hours_in_month"]
    )
    return long.sort_values(["year", "plant_id", "month"]).reset_index(drop=True)


def flag(long: pd.DataFrame) -> pd.DataFrame:
    """Flag missing or implausible monthly series — reported, NEVER filled.

    Four flags, each a statement about the SOURCE, applied per plant-year:

    * ``missing_months``   — months with a null ``netgen_mwh``.
    * ``all_zero``         — every month reported exactly 0 MWh.
    * ``cf_over_1``        — a month whose energy exceeds nameplate × hours
      (so the 923 and 860 records disagree, or the 860 nameplate is stale).
    * ``negative_months``  — months reporting negative net generation, which is
      physically real for a hydro plant with station service exceeding output
      but is worth surfacing.
    """
    rows = []
    for (year, pid), g in long.groupby(["year", "plant_id"]):
        v = pd.to_numeric(g["netgen_mwh"], errors="coerce")
        cf = pd.to_numeric(g["capacity_factor"], errors="coerce")
        rows.append(
            {
                "year": int(year),
                "plant_id": int(pid),
                "plant_name": g["plant_name"].iloc[0],
                "ba_code": g["ba_code"].iloc[0],
                "nameplate_mw_860": g["nameplate_mw_860"].iloc[0],
                "annual_mwh": float(v.sum()),
                "missing_months": int(v.isna().sum()),
                "all_zero": bool((v.fillna(0) == 0).all()),
                "cf_over_1": int((cf > 1.0).sum()),
                "max_cf": float(cf.max()) if cf.notna().any() else float("nan"),
                "negative_months": int((v < 0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["year", "plant_id"]).reset_index(drop=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", action="append", type=int, dest="years", default=None)
    ap.add_argument(
        "--include-ps",
        action="store_true",
        help="also extract pumped storage (PS) — reported separately, never "
        "part of the conventional-hydro budget population",
    )
    args = ap.parse_args()
    years = tuple(args.years) if args.years else (2023, 2024, 2025)
    pms = ("HY", "PS") if args.include_ps else ("HY",)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    long = build(years, pms)
    flags = flag(long)

    long_path = OUT_DIR / "nwpp_hydro_monthly_923.parquet"
    flag_path = OUT_DIR / "nwpp_hydro_monthly_923_flags.csv"
    long.to_parquet(long_path, index=False)
    flags.to_csv(flag_path, index=False)

    print(f"wrote {long_path} — {len(long):,} plant-months")
    for year in years:
        g = long[long["year"] == year]
        print(
            f"  {year}: {g['plant_id'].nunique():>3} plants, "
            f"{g['netgen_mwh'].sum() / 1e6:>7.3f} TWh, "
            f"{g['nameplate_mw_860'].groupby(g['plant_id']).first().sum():>9,.1f} MW "
            f"nameplate (860 join)"
        )
    bad = flags[
        flags["missing_months"].gt(0)
        | flags["all_zero"]
        | flags["cf_over_1"].gt(0)
        | flags["negative_months"].gt(0)
    ]
    print(f"wrote {flag_path} — {len(bad)} of {len(flags)} plant-years flagged")


if __name__ == "__main__":
    sys.exit(main())
