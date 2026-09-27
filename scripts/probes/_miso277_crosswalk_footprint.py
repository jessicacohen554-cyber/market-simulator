#!/usr/bin/env python3
"""miso-277: footprint of the EPA CAMD-EIA Power Sector Data Crosswalk on MISO ST_GAS.

ZERO LP. Nothing is solved, nothing is re-derived, no committed artifact is
touched. This probe answers one question for the owner's "Wait for crosswalk"
ruling (``docs/FINDING-miso276-next-levers-phase0-2026-09-26.md`` §2 / §4):
**if the frozen thermal-tranche artifact attributed CAMPD conduct by UNIT
through the crosswalk instead of by FACILITY, how much gas-fired steam energy
would move into ST_GAS, and which coal energy would leave it?**

Inputs (all on disk, all read-only):

* ``data/raw/reference/camd-eia-crosswalk/epa_eia_crosswalk.csv`` — the
  crosswalk (v0.3, EIA-860 2018 basis). Maps a CAMPD ``(facility, unit)`` to
  its EIA ``(plant, generator)`` set.
* ``data/raw/eia-860/vintage_<year>/`` — the prime mover, energy source and
  CHP flag of each mapped generator AS OF THE SOLVE YEAR (the crosswalk's own
  EIA columns are 2018 codes and go stale on conversions, e.g. Burlington 1104).
* ``data/raw/campd-unit-level/<ST>_<year>.parquet`` via
  :func:`market_sim.data.campd.load_campd_hourly` (stack-duplicate masked) and
  the raw ``primaryFuelInfo`` column (CAMPD's own per-unit fuel, a second basis).
* ``data/raw/_processed-legacy/thermal_tranches_MISO.csv`` — the frozen
  artifact whose facility filing is being audited.

Legs:

a. Per-facility attribution table for the eight named facilities.
b. MISO-wide: gross (and parasitic-net) GWh of non-CHP gas-steam units at
   plants the artifact carries NO ST_GAS row for — the mis-attributed ST_GAS
   population — plus the reverse object (coal units inside ST_GAS-filed
   facilities), 2019-2023.
c. Riverside 55641 CT-03/CT-04 vs West Riverside 64020, and crosswalk coverage
   of MISO CAMPD units by gross load.
d. Sync-fraction hazard at 1702 / 1104: the frozen estimator's facility-summed
   statistic vs the same statistic over the crosswalk's gas-steam units only.

Rule 13 ``[R-MEASURED]``: the crosswalk is a static identifier map published by
EPA; the unit classes come from EIA-860 prime mover / energy source. No
statistic here responds to any price or volume residual.

Usage::

    uv run python scripts/probes/_miso277_crosswalk_footprint.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import CAMPD_UNIT_LEVEL_DIR, RAW_DATA_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

ISO = "MISO"
YEARS = [2019, 2020, 2021, 2022, 2023]
SYNC_YEARS = [2019, 2020, 2021, 2022]
FOCUS = [6190, 6055, 2050, 1400, 1702, 1104, 55641, 64020]
XWALK = RAW_DATA_DIR / "reference" / "camd-eia-crosswalk" / "epa_eia_crosswalk.csv"
ARTIFACT = RAW_DATA_DIR / "_processed-legacy" / "thermal_tranches_MISO.csv"
OUT = REPO / "results" / "calibration" / "_miso277_crosswalk_footprint.json"

# EIA-860 energy-source codes (EIA-860 instructions, Table 28). Gas family is the
# set the model's gas classes carry; coal family includes petroleum coke (PC),
# which the model files under a coal subclass.
GAS_CODES = {"NG", "OG", "BFG", "PG", "SGP"}
COAL_CODES = {"BIT", "SUB", "LIG", "RC", "WC", "ANT", "SGC", "PC"}
OIL_CODES = {"DFO", "RFO", "JF", "KER", "WO"}
CC_PRIME_MOVERS = {"CA", "CT", "CS"}
UNMATCHED_TAGS = ("CAMD Unmatched", "Manual CAMD Excluded")

# FINDING-miso276 §2 table, "plants with no ST_GAS tranche row" (TWh, model vs EIA-923).
FINDING_NO_ROW_GAP = {
    2019: {"model": 1.88, "eia923": 6.87, "gap": -4.99},
    2020: {"model": 2.31, "eia923": 6.36, "gap": -4.06},
    2021: {"model": 0.56, "eia923": 3.86, "gap": -3.31},
    2022: {"model": 1.03, "eia923": 3.79, "gap": -2.76},
    2023: {"model": 2.35, "eia923": 3.55, "gap": -1.19},
}


def load_crosswalk() -> pd.DataFrame:
    """Return the crosswalk with plant/unit keys normalized to (int, str)."""
    xw = pd.read_csv(XWALK, encoding="utf-8-sig", low_memory=False, dtype=str)
    xw["camd_plant"] = pd.to_numeric(xw["CAMD_PLANT_ID"], errors="coerce").astype(
        "Int64"
    )
    xw["eia_plant"] = pd.to_numeric(xw["EIA_PLANT_ID"], errors="coerce").astype("Int64")
    xw["matched"] = xw["EIA_GENERATOR_ID"].notna() & ~xw["MATCH_TYPE_GEN"].isin(
        UNMATCHED_TAGS
    )
    return xw


def load_eia_vintage(year: int) -> pd.DataFrame:
    """Return ``(plant_id, generator_id) -> pm, es, chp, nameplate, ba`` for a vintage."""
    vdir = RAW_DATA_DIR / "eia-860" / f"vintage_{year}"
    if not vdir.exists():
        vdir = RAW_DATA_DIR / "eia-860"
    gen = pd.read_parquet(vdir / "eia860_generators.parquet")
    gen = gen[
        [
            "plant_id",
            "generator_id",
            "plant_name",
            "prime_mover",
            "energy_source",
            "nameplate_capacity_mw",
            "balancing_authority_code",
            "status",
        ]
    ].copy()
    op = pd.read_parquet(
        vdir / "eia860_generator_operable.parquet",
        columns=[
            "Plant Code",
            "Generator ID",
            "Associated with Combined Heat and Power System",
        ],
    ).rename(
        columns={
            "Plant Code": "plant_id",
            "Generator ID": "generator_id",
            "Associated with Combined Heat and Power System": "chp",
        }
    )
    op["plant_id"] = pd.to_numeric(op["plant_id"], errors="coerce")
    gen["plant_id"] = pd.to_numeric(gen["plant_id"], errors="coerce")
    for df in (gen, op):
        df["generator_id"] = df["generator_id"].astype(str).str.strip()
    gen = gen.merge(op.drop_duplicates(["plant_id", "generator_id"]), how="left")
    gen["chp"] = gen["chp"].astype(str).str.upper().eq("Y")
    return gen.drop_duplicates(["plant_id", "generator_id"])


def classify_gens(pm: str, es: str, chp: bool) -> str:
    """Map one generator's (prime mover, energy source, CHP) to a model-family class."""
    pm = str(pm or "").upper()
    es = str(es or "").upper()
    if pm in CC_PRIME_MOVERS:
        return "CC_CHP" if chp else "CC_REGULAR"
    if pm == "ST":
        if es in COAL_CODES:
            return "COAL"
        if es in GAS_CODES:
            return "ST_CHP" if chp else "ST_GAS"
        if es in OIL_CODES:
            return "ST_OIL"
        return f"ST_{es or 'NA'}"
    if pm == "GT":
        return "CT_CHP" if chp else "CT_PEAKER"
    return f"{pm or 'NA'}_{es or 'NA'}"


def unit_class_table(xw: pd.DataFrame, eia: pd.DataFrame) -> pd.DataFrame:
    """Return one row per crosswalk CAMPD unit with its vintage-year class.

    A unit mapped to several generators takes the class holding the most
    nameplate. A mapped generator absent from the vintage (retired, or not yet
    built) falls back to the crosswalk's own 2018 EIA codes and is flagged.
    """
    m = xw[xw["matched"]].copy()
    m["generator_id"] = m["EIA_GENERATOR_ID"].astype(str).str.strip()
    m = m.merge(
        eia.rename(columns={"plant_id": "eia_plant"})[
            [
                "eia_plant",
                "generator_id",
                "prime_mover",
                "energy_source",
                "chp",
                "nameplate_capacity_mw",
            ]
        ],
        on=["eia_plant", "generator_id"],
        how="left",
    )
    m["in_vintage"] = m["prime_mover"].notna()
    m["pm"] = m["prime_mover"].fillna(m["EIA_UNIT_TYPE"])
    m["es"] = m["energy_source"].fillna(m["EIA_FUEL_TYPE"])
    m["chp"] = m["chp"].fillna(False).astype(bool)
    m["mw"] = pd.to_numeric(m["nameplate_capacity_mw"], errors="coerce").fillna(
        pd.to_numeric(m["EIA_NAMEPLATE_CAPACITY"], errors="coerce")
    )
    m["klass"] = [classify_gens(p, e, c) for p, e, c in zip(m["pm"], m["es"], m["chp"])]
    # Generators shared between two CAMPD units (a common steam turbine) would
    # double-count nameplate; the class vote only needs the relative weight.
    agg = (
        m.groupby(["camd_plant", "CAMD_UNIT_ID", "klass"], dropna=False)["mw"]
        .sum()
        .reset_index()
        .sort_values("mw", ascending=False)
        .drop_duplicates(["camd_plant", "CAMD_UNIT_ID"])
    )
    gens = (
        m.groupby(["camd_plant", "CAMD_UNIT_ID"])
        .apply(
            lambda g: [
                f"{int(p)}:{gid}:{pm}/{es}{'/CHP' if c else ''}"
                f"{'' if v else '(xw2018)'}"
                for p, gid, pm, es, c, v in zip(
                    g["eia_plant"],
                    g["generator_id"],
                    g["pm"],
                    g["es"],
                    g["chp"],
                    g["in_vintage"],
                )
            ],
            include_groups=False,
        )
        .rename("eia_gens")
        .reset_index()
    )
    eia_plants = (
        m.groupby(["camd_plant", "CAMD_UNIT_ID"])["eia_plant"]
        .agg(lambda s: sorted({int(x) for x in s.dropna()}))
        .rename("eia_plants")
        .reset_index()
    )
    out = agg.merge(gens).merge(eia_plants)
    return out.rename(columns={"camd_plant": "plant_id", "CAMD_UNIT_ID": "unit_id"})


def campd_unit_year(
    states: tuple[str, ...], year: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (normalized hourly frame, per-unit summary with CAMPD's own fuel)."""
    hourly = campd.load_campd_hourly(states, [year], prefer_unit_level=True)
    per_unit = (
        hourly.groupby(["plant_id", "unit_id"])["gross_mw"]
        .sum()
        .div(1e3)
        .rename("gross_gwh")
    ).reset_index()
    fuels = []
    for st in states:
        p = CAMPD_UNIT_LEVEL_DIR / f"{st}_{year}.parquet"
        if p.exists():
            f = pd.read_parquet(
                p, columns=["facilityId", "unitId", "primaryFuelInfo", "unitType"]
            )
            fuels.append(f.drop_duplicates(["facilityId", "unitId"]))
    fu = pd.concat(fuels, ignore_index=True)
    fu["plant_id"] = pd.to_numeric(fu["facilityId"], errors="coerce").astype("Int64")
    fu["unit_id"] = fu["unitId"].astype(str)
    fu = fu.dropna(subset=["plant_id"]).drop_duplicates(["plant_id", "unit_id"])
    fu["plant_id"] = fu["plant_id"].astype(int)
    per_unit = per_unit.merge(
        fu[["plant_id", "unit_id", "primaryFuelInfo", "unitType"]], how="left"
    )
    return hourly, per_unit


def campd_fuel_class(fuel: object, unit_type: object) -> str:
    """CAMPD-own basis: boiler + gas-first fuel -> gas steam; coal-first -> coal."""
    f = str(fuel or "")
    ut = str(unit_type or "").lower()
    boiler = any(
        k in ut for k in ("boiler", "stoker", "fluidized", "cyclone", "-fired")
    )
    first = f.split(",")[0].strip()
    if "Coal" in first or "Coke" in first:
        return "COAL"
    if boiler and (
        "Natural Gas" in first or "Other Gas" in first or "Process Gas" in first
    ):
        return "GAS_STEAM"
    if boiler and ("Oil" in first):
        return "OIL_STEAM"
    return "OTHER"


def main() -> None:
    """Run legs a-d and write the JSON footprint."""
    xw = load_crosswalk()
    art = pd.read_csv(ARTIFACT)
    art_groups = (
        art.groupby("plant_code")["plant_group"].agg(lambda s: sorted(set(s))).to_dict()
    )
    st_gas_rows = {int(c) for c, g in art_groups.items() if "ST_GAS" in g}
    cap, primary = dtt._fleet_nameplate_and_group(ISO)
    factors = dtt._parasitic_factor_map()
    states = campd.states_for_iso(ISO)

    result: dict = {
        "probe": "miso-277 crosswalk footprint (zero LP)",
        "crosswalk": {
            "file": str(XWALK.relative_to(REPO)),
            "rows": int(len(xw)),
            "eia860_basis_year": 2018,
            "version": "v0.3 (upstream master 3c7d672, 2022-10-03)",
        },
        "artifact": str(ARTIFACT.relative_to(REPO)),
        "finding_no_row_gap_twh": FINDING_NO_ROW_GAP,
        "per_facility": {},
        "misattributed_st_gas": {},
        "reverse_coal_in_st_gas": {},
        "coverage": {},
        "sync_hazard": {},
    }

    hourly_by_year: dict[int, pd.DataFrame] = {}
    for year in YEARS:
        eia = load_eia_vintage(year)
        miso_plants = set(
            eia.loc[eia["balancing_authority_code"].astype(str) == ISO, "plant_id"]
            .dropna()
            .astype(int)
        ) | set(int(c) for c in art_groups)
        ucls = unit_class_table(xw, eia)
        hourly, pu = campd_unit_year(states, year)
        if year in SYNC_YEARS:
            hourly_by_year[year] = hourly[hourly["plant_id"].isin([1702, 1104])].copy()
        pu = pu[pu["plant_id"].isin(miso_plants)]
        pu = pu.merge(ucls, on=["plant_id", "unit_id"], how="left")
        pu["klass"] = pu["klass"].fillna("UNMATCHED")
        pu["campd_class"] = [
            campd_fuel_class(f, u)
            for f, u in zip(pu["primaryFuelInfo"], pu["unitType"])
        ]
        pu["pf"] = pu["plant_id"].map(factors).fillna(1.0)
        pu["net_gwh"] = pu["gross_gwh"] * pu["pf"]
        pu["artifact_groups"] = pu["plant_id"].map(lambda c: art_groups.get(int(c), []))
        pu["has_st_gas_row"] = pu["plant_id"].isin(st_gas_rows)

        # --- leg c: coverage --------------------------------------------------
        tot = float(pu["gross_gwh"].sum())
        matched = float(pu.loc[pu["klass"] != "UNMATCHED", "gross_gwh"].sum())
        unm = (
            pu[pu["klass"] == "UNMATCHED"]
            .groupby(["plant_id", "unit_id"])["gross_gwh"]
            .sum()
            .sort_values(ascending=False)
        )
        result["coverage"][year] = {
            "miso_campd_units": int(len(pu)),
            "matched_units": int((pu["klass"] != "UNMATCHED").sum()),
            "gross_twh_total": round(tot / 1e3, 3),
            "gross_twh_matched": round(matched / 1e3, 3),
            "matched_share_by_gross": round(matched / tot, 4) if tot else None,
            "top_unmatched_gwh": {
                f"{int(p)}:{u}": round(float(v), 1)
                for (p, u), v in unm.head(12).items()
            },
        }

        # --- leg b: mis-attributed ST_GAS population ---------------------------
        gas_st = pu[(pu["klass"] == "ST_GAS") & ~pu["has_st_gas_row"]]
        by_plant = (
            gas_st.groupby("plant_id")
            .agg(
                gross_gwh=("gross_gwh", "sum"),
                net_gwh=("net_gwh", "sum"),
                units=("unit_id", lambda s: sorted(s)),
            )
            .sort_values("gross_gwh", ascending=False)
        )
        fleet_st_gas = {c for (c, g) in cap if g == "ST_GAS"}
        camp_basis = pu[
            (pu["campd_class"] == "GAS_STEAM")
            & ~pu["has_st_gas_row"]
            & ~pu["klass"].isin(["ST_CHP", "CC_CHP", "CT_CHP"])
        ]
        result["misattributed_st_gas"][year] = {
            "crosswalk_basis_gross_twh": round(
                float(gas_st["gross_gwh"].sum()) / 1e3, 3
            ),
            "crosswalk_basis_net_twh": round(float(gas_st["net_gwh"].sum()) / 1e3, 3),
            "of_which_at_plants_fleet_carries_st_gas_net_twh": round(
                float(
                    gas_st.loc[gas_st["plant_id"].isin(fleet_st_gas), "net_gwh"].sum()
                )
                / 1e3,
                3,
            ),
            "campd_fuel_basis_net_twh": round(
                float(camp_basis["net_gwh"].sum()) / 1e3, 3
            ),
            "finding_gap_twh": FINDING_NO_ROW_GAP[year]["gap"],
            "finding_eia923_twh": FINDING_NO_ROW_GAP[year]["eia923"],
            "by_plant": {
                int(p): {
                    "name": str(
                        eia.loc[eia["plant_id"] == p, "plant_name"].head(1).squeeze()
                    )
                    if (eia["plant_id"] == p).any()
                    else "",
                    "artifact_groups": art_groups.get(int(p), []),
                    "fleet_groups_now": sorted(g for (c, g) in cap if c == p),
                    "gross_gwh": round(float(r.gross_gwh), 1),
                    "net_gwh": round(float(r.net_gwh), 1),
                    "units": r.units,
                }
                for p, r in by_plant.iterrows()
                if r.gross_gwh > 1.0
            },
        }
        coal_in = pu[(pu["klass"] == "COAL") & pu["has_st_gas_row"]]
        result["reverse_coal_in_st_gas"][year] = {
            "net_twh": round(float(coal_in["net_gwh"].sum()) / 1e3, 3),
            "by_plant_net_gwh": {
                int(p): round(float(v), 1)
                for p, v in coal_in.groupby("plant_id")["net_gwh"].sum().items()
                if v > 1.0
            },
        }

        # --- leg a: per-facility table ----------------------------------------
        for fac in FOCUS:
            rows = pu[pu["plant_id"] == fac]
            entry = result["per_facility"].setdefault(
                str(fac),
                {
                    "artifact_groups": art_groups.get(fac, []),
                    "fleet_groups_now": {
                        g: round(m, 1) for (c, g), m in cap.items() if c == fac
                    },
                    "fleet_primary_now": primary.get(fac),
                    "crosswalk_units": sorted(
                        xw.loc[xw["camd_plant"] == fac, "CAMD_UNIT_ID"]
                        .astype(str)
                        .unique()
                    ),
                    "eia860_2023_generators": [],
                    "units": {},
                },
            )
            for _, r in rows.iterrows():
                u = entry["units"].setdefault(str(r.unit_id), {})
                u[str(year)] = {
                    "gross_gwh": round(float(r.gross_gwh), 1),
                    "campd_fuel": None
                    if pd.isna(r.primaryFuelInfo)
                    else str(r.primaryFuelInfo),
                    "campd_unit_type": None if pd.isna(r.unitType) else str(r.unitType),
                    "eia_gens": r.eia_gens if isinstance(r.eia_gens, list) else [],
                    "unit_class_via_crosswalk": r.klass,
                    "unit_class_campd_fuel": r.campd_class,
                }
            if year == 2023:
                g = eia[eia["plant_id"] == fac]
                entry["eia860_2023_generators"] = [
                    f"{gid}:{pm}/{es}:{mw}MW:{st}"
                    for gid, pm, es, mw, st in zip(
                        g["generator_id"],
                        g["prime_mover"],
                        g["energy_source"],
                        g["nameplate_capacity_mw"],
                        g["status"],
                    )
                ]
        print(
            f"{year}: coverage {result['coverage'][year]['matched_share_by_gross']}, "
            f"mis-attributed ST_GAS net {result['misattributed_st_gas'][year]['crosswalk_basis_net_twh']} TWh"
        )

    # --- leg c: Riverside ------------------------------------------------------
    riv = xw[xw["camd_plant"].isin([55641, 64020]) | xw["eia_plant"].isin([64020])]
    result["riverside"] = {
        "crosswalk_rows": riv[
            [
                "CAMD_PLANT_ID",
                "CAMD_UNIT_ID",
                "CAMD_GENERATOR_ID",
                "EIA_PLANT_ID",
                "EIA_GENERATOR_ID",
                "MATCH_TYPE_GEN",
            ]
        ]
        .astype(str)
        .to_dict("records"),
        "maps_ct03_ct04_to_64020": bool(
            (
                riv["CAMD_UNIT_ID"].isin(["CT-03", "CT-04"])
                & (riv["eia_plant"] == 64020)
            ).any()
        ),
        "crosswalk_has_ct03_ct04": bool(
            riv["CAMD_UNIT_ID"].isin(["CT-03", "CT-04"]).any()
        ),
        "crosswalk_has_eia_64020": bool((xw["eia_plant"] == 64020).any()),
    }

    # --- leg d: sync hazard ----------------------------------------------------
    for fac in (1702, 1104):
        nameplate = cap.get((fac, "ST_GAS"), 0.0)
        pfac = factors.get(fac, 1.0)
        out = {
            "st_gas_nameplate_mw_fleet_now": round(nameplate, 1),
            "parasitic_factor": pfac,
        }
        for year in SYNC_YEARS:
            h = hourly_by_year[year]
            h = h[h["plant_id"] == fac]
            eia = load_eia_vintage(year)
            ucls = unit_class_table(xw, eia)
            gas_units = set(
                ucls.loc[
                    (ucls["plant_id"] == fac) & (ucls["klass"] == "ST_GAS"), "unit_id"
                ]
            )
            fac_series = campd.plant_hourly_net(h, factors, year).get(fac)
            gas_h = h[h["unit_id"].isin(gas_units)]
            gas_series = campd.plant_hourly_net(gas_h, factors, year).get(fac)
            thr = dtt._SYNC_MW_NAMEPLATE_FRAC * nameplate

            def frac(s: np.ndarray | None) -> float | None:
                return None if s is None else round(float((s > thr).mean()), 3)

            out[str(year)] = {
                "facility_summed_online_frac": frac(fac_series),
                "gas_units_only_online_frac": frac(gas_series),
                "gas_units": sorted(gas_units),
                "facility_net_twh": None
                if fac_series is None
                else round(float(fac_series.sum()) / 1e6, 3),
                "gas_units_net_twh": None
                if gas_series is None
                else round(float(gas_series.sum()) / 1e6, 3),
            }
        result["sync_hazard"][str(fac)] = out

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, default=str))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
