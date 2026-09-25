#!/usr/bin/env python3
"""Build the NWPP conventional-hydro monthly energy budget and power envelope (NWPP-32).

The rule-13 ``[R-MEASURED]`` / rule-14 ``[R-ACCURATE]`` artifact behind the first
NWPP keeper's hydro object and the measured input NWPP-36 (Columbia mainstem
hydraulic coupling, owner ruling N3) is built against. Everything here is a
**join, a reconciliation and a flag** — no modelling, no gap-filling, no
rescaling, no fitted scalar. Charter: ``docs/multi-iso/nwpp-addition-plan-2026-09.md``
§2.7 / §5 row NWPP-32; pre-registration ``docs/handoffs/PRECOMMIT-nwpp-32-2026-09-14.md``.

Inputs (all committed):

* ``data/raw/nwpp-hydro/nwpp_hydro_monthly_923.parquet`` — NWPP-11's pure EIA-923
  extract (7,212 plant-months, 2023-2025, prime mover ``HY`` in the 17 BAs; pumped
  storage excluded by design — the footprint's one PS plant, 314.0 MW in BPAT, is
  the storage block's object, never inflow).
* EIA-860 hydro nameplate through the loader's own reader
  (``market_sim.data.hydro._load_hydro_nameplate``) so the envelope is byte-for-byte
  what ``load_hydro_budget`` will stamp.
* ``data/raw/ornl-eha/ORNL_EHAHydroPlant_PublicFY2024.xlsx`` — the published federal
  inventory whose ``Water`` (river), ``Mode``, ``Dam_Own``, ``HUC`` and ``FC_Dock``
  fields identify the hydraulic chains and the storage-vs-run-of-river split.
* ``data/raw/hilarri/HILARRI_v4.csv`` — plant→dam→reservoir linkage (NID / GRanD /
  HydroLAKES ids, USGS gage), the documented completion source for EHA Mode-NaN.
* ``data/raw/nwpp-hydro/nwpp_hydro_chain_published.csv`` — a hand transcription of
  published chain facts (BPA "The Columbia River System Inside Story" pp. 14-15
  storage volumes and average discharges; the HRFCPPA 2004 seven-project
  definition), every row carrying its source.
* the 17 per-BA EIA-930 hourly extracts through the registered NWPP pool frame
  (``market_sim.data.eia930.frames._eia_hourly_frame_filled``), for the within-month
  shaping statistics the monthly budget cannot see (§2.7 constraint b).

Outputs (``data/raw/nwpp-hydro/``):

* ``nwpp_hydro_budget.parquet`` — one row per (plant, year) over the union of the
  EIA-860 population and each year's EIA-923 reporters: the twelve raw monthly
  budgets (MWh, negatives RETAINED — the loader clips them and that clip is
  reported, not pre-applied), the annual reconciliation, the envelope
  (``max_mw`` = EIA-860 nameplate, ``min_mw`` = 0 — no floor is stamped by this
  lane), zone, river, mode, chain membership and the gate status.
* ``nwpp_hydro_reconciliation.csv`` — the per-plant-year gate table, human-readable.
* ``nwpp_hydro_chain.csv`` — the published chain transcription joined to nameplate,
  energy, EHA mode and reservoir linkage: NWPP-36's reach table.
* ``nwpp_hydro_within_month_930.csv`` — per (BA, year, month) within-month shaping
  statistics off the EIA-930 ``NG: WAT`` series (pool + every member BA).

Gate (PRECOMMIT §2): every plant-year's ``sum(12 months)`` must equal the extract's
``netgen_annual_mwh`` to within 1.0 MWh; a miss is ``MISMATCH`` and is flagged, never
adjusted. A plant absent from a year's EIA-923 is ``NO_923_SERIES`` and is never
filled. The loader cross-check re-reads ``load_hydro_budget("NWPP", year)`` and
asserts it equals the clipped artifact for every kept plant.

Usage:
    python scripts/data/build_nwpp_hydro_budget.py
    python scripts/data/build_nwpp_hydro_budget.py --skip-930   # budget + chain only
    python scripts/data/build_nwpp_hydro_budget.py --years 2019 2020 2021 2022 2023 2024 2025 --skip-930

The budget year set defaults to every year the NWPP-11 extract carries; each
year is an independent filter of that extract, so extending it (NWPP-NEXT-2:
2019-2022) leaves every existing year's rows value-identical.
"""

from __future__ import annotations

import argparse
import logging
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

HYDRO_DIR = RAW_DATA_DIR / "nwpp-hydro"
EXTRACT_PATH = HYDRO_DIR / "nwpp_hydro_monthly_923.parquet"
CHAIN_PUBLISHED_PATH = HYDRO_DIR / "nwpp_hydro_chain_published.csv"
EHA_PATH = RAW_DATA_DIR / "ornl-eha" / "ORNL_EHAHydroPlant_PublicFY2024.xlsx"
HILARRI_PATH = RAW_DATA_DIR / "hilarri" / "HILARRI_v4.csv"

OUT_BUDGET = HYDRO_DIR / "nwpp_hydro_budget.parquet"
OUT_RECON = HYDRO_DIR / "nwpp_hydro_reconciliation.csv"
OUT_CHAIN = HYDRO_DIR / "nwpp_hydro_chain.csv"
OUT_930 = HYDRO_DIR / "nwpp_hydro_within_month_930.csv"

ISO = "NWPP"
# The NWPP-32 build years. The DEFAULT year set is every year the NWPP-11 extract
# carries (``--years`` overrides); NWPP-NEXT-2 extended the extract to 2019-2022
# so the NWPP-36 cascade builder has an EIA-923 series for those years. Each
# year is built independently (a per-year filter of the same extract), so adding
# a year never moves another year's rows.
YEARS: tuple[int, ...] = (2023, 2024, 2025)
# The NWPP-36 reach table (``nwpp_hydro_chain.csv``) is a FROZEN input to the
# cascade-link derivation (rule 23 ``[R-FROZEN-DERIVE]``): its per-year energy
# columns stay the three years it was built on, whatever ``--years`` builds.
CHAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)
# EIA files whole MWh; 1 MWh is the rounding tolerance and nothing else (PRECOMMIT §2).
RECONCILE_TOL_MWH = 1.0
# EHA `Water` values that place a plant on the U.S. Columbia mainstem (PRECOMMIT §5a).
MAINSTEM_WATER = (
    "Columbia River",
    "Columbia And Snake Rivers",
    "Snake And Columbia Rivers",
)
# The 17-member pool plus each member, for the within-month statistics.
BA_SERIES = (
    "NWPP",
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

MONTH_COLS = [f"m{m:02d}" for m in range(1, 13)]


def _log() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    return logging.getLogger("nwpp-32")


def load_extract() -> pd.DataFrame:
    """Return NWPP-11's long-form EIA-923 monthly extract."""
    if not EXTRACT_PATH.exists():
        raise FileNotFoundError(f"NWPP-11 extract missing: {EXTRACT_PATH}")
    return pd.read_parquet(EXTRACT_PATH)


def load_eha() -> pd.DataFrame:
    """Return the ORNL EHA FY2024 ``Operational`` sheet keyed on EIA plant id."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        op = pd.read_excel(EHA_PATH, sheet_name="Operational")
    op["EIA_PtID"] = pd.to_numeric(op["EIA_PtID"], errors="coerce")
    op = op.dropna(subset=["EIA_PtID"]).drop_duplicates("EIA_PtID")
    op["EIA_PtID"] = op["EIA_PtID"].astype(int)
    cols = [
        "Water",
        "Mode",
        "Dam_Own",
        "HUC",
        "FC_Dock",
        "Lat",
        "Lon",
        "CH_MW",
        "BACode",
    ]
    return op.set_index("EIA_PtID")[cols].rename(
        columns={
            "Water": "river_eha",
            "Mode": "mode_eha",
            "Dam_Own": "dam_owner_eha",
            "HUC": "huc_eha",
            "FC_Dock": "ferc_docket_eha",
            "Lat": "lat_eha",
            "Lon": "lon_eha",
            "CH_MW": "ch_mw_eha",
            "BACode": "ba_eha",
        }
    )


def load_hilarri() -> pd.DataFrame:
    """Return per-EIA-plant reservoir linkage flags from HILARRI v4."""
    hil = pd.read_csv(HILARRI_PATH, low_memory=False)
    hil["eia_ptid"] = pd.to_numeric(hil["eia_ptid"], errors="coerce")
    hil = hil.dropna(subset=["eia_ptid"])
    hil["eia_ptid"] = hil["eia_ptid"].astype(int)
    return hil.groupby("eia_ptid").agg(
        hilarri_grand_reservoir=(
            "grand_id",
            lambda s: bool((s.fillna(-9999) > 0).any()),
        ),
        hilarri_hydrolakes=("hylake_id", lambda s: bool((s.fillna(-9999) > 0).any())),
        hilarri_nid=("nidid", lambda s: bool(s.notna().any())),
        hilarri_dam_name=("dam_name", "first"),
        hilarri_usgs_gage=("usgs_gage", "first"),
    )


def chain_membership(row: pd.Series, published: pd.DataFrame) -> str:
    """Return the chain label for a plant: the published table first, then EHA river."""
    pid = (
        int(row.name)
        if isinstance(row.name, (int, np.integer))
        else int(row["plant_id"])
    )
    if pid in published.index:
        return str(published.loc[pid, "chain"])
    water = str(row.get("river_eha", "") or "")
    if water in MAINSTEM_WATER:
        return "COLUMBIA_MAINSTEM"
    if water.startswith("Snake River"):
        return "SNAKE_UPSTREAM"
    return "INDEPENDENT_OR_TRIBUTARY"


def extract_years() -> tuple[int, ...]:
    """Return every year the NWPP-11 extract carries, ascending."""
    return tuple(sorted(int(y) for y in load_extract()["year"].unique()))


def build_budget(
    log: logging.Logger, years: tuple[int, ...] = YEARS
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build the per-plant-year budget + envelope table and its reconciliation."""
    from market_sim.data.fleet import EIA_860_DIR, EIA_860_PARQUET_NAME
    from market_sim.data.hydro import (
        _load_hydro_nameplate,
        hours_per_month,
        load_hydro_budget,
    )
    from market_sim.data.zone_assignment import build_zone_lookup

    ext = load_extract()
    nameplate = pd.Series(_load_hydro_nameplate(ISO), name="max_mw_eia860")
    nameplate.index = nameplate.index.astype(int)
    g860 = pd.read_parquet(Path(EIA_860_DIR) / EIA_860_PARQUET_NAME)
    name860 = g860.groupby("plant_id")["plant_name"].first()
    ba860 = g860.groupby("plant_id")["balancing_authority_code"].first()
    zones = {int(k): v for k, v in build_zone_lookup(ISO).items()}
    eha = load_eha()
    hil = load_hilarri()
    published = pd.read_csv(CHAIN_PUBLISHED_PATH).set_index("plant_id")
    hpm = hours_per_month().astype(float)

    p860 = set(nameplate.index)
    rows: list[pd.DataFrame] = []
    missing_years = sorted(set(years) - set(int(y) for y in ext["year"].unique()))
    if missing_years:
        raise ValueError(
            f"years {missing_years} are not in the NWPP-11 extract {EXTRACT_PATH} — "
            "rebuild it with scripts/data/build_nwpp_hydro_monthly.py --year ...; "
            "nothing is filled here"
        )
    for year in years:
        e = ext[ext["year"] == year]
        piv = e.pivot_table(
            index="plant_id", columns="month", values="netgen_mwh", aggfunc="sum"
        )
        piv.index = piv.index.astype(int)
        piv = piv.reindex(columns=range(1, 13))
        annual923 = e.groupby("plant_id")["netgen_annual_mwh"].first()
        annual923.index = annual923.index.astype(int)
        meta = e.groupby("plant_id").agg(
            plant_name=("plant_name", "first"), ba_code=("ba_code", "first")
        )
        meta.index = meta.index.astype(int)
        p923 = set(piv.index)

        # Loader cross-check: what the LP will actually see for this year.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            hb = load_hydro_budget(ISO, year)
        loader = pd.DataFrame(
            hb.monthly_energy, index=hb.plant_ids.astype(int), columns=range(1, 13)
        )
        loader_max = pd.Series(hb.max_mw, index=hb.plant_ids.astype(int))

        ids = sorted(p860 | p923)
        t = pd.DataFrame(index=pd.Index(ids, name="plant_id"))
        t["year"] = year
        t["plant_name"] = meta["plant_name"].reindex(ids)
        t["plant_name"] = t["plant_name"].fillna(
            pd.Series(name860.reindex(ids).values, index=ids)
        )
        t["ba_code"] = meta["ba_code"].reindex(ids)
        t["ba_code"] = t["ba_code"].fillna(
            pd.Series(ba860.reindex(ids).values, index=ids)
        )
        t["zone"] = [zones.get(i, "") for i in ids]
        for m in range(1, 13):
            t[f"m{m:02d}"] = piv[m].reindex(ids)
        t["budget_annual_mwh"] = t[MONTH_COLS].sum(axis=1, min_count=1)
        t["netgen_annual_mwh_923"] = annual923.reindex(ids)
        t["delta_mwh"] = (t["budget_annual_mwh"] - t["netgen_annual_mwh_923"]).abs()
        t["in_eia860"] = [i in p860 for i in ids]
        t["in_eia923"] = [i in p923 for i in ids]

        # Envelope: EIA-860 nameplate; the loader's peak-monthly-average fallback where absent.
        t["max_mw_eia860"] = nameplate.reindex(ids)
        peak_avg = t[MONTH_COLS].to_numpy(dtype=float) / hpm[np.newaxis, :]
        peak_avg = np.nanmax(np.where(np.isnan(peak_avg), -np.inf, peak_avg), axis=1)
        peak_avg = np.where(np.isfinite(peak_avg), peak_avg, np.nan)
        t["max_mw"] = t["max_mw_eia860"].fillna(pd.Series(peak_avg, index=ids))
        t["max_mw_source"] = np.where(
            t["max_mw_eia860"].notna(),
            "eia860_nameplate",
            "peak_monthly_average_fallback",
        )
        t["min_mw"] = 0.0  # no floor stamped by this lane (PRECOMMIT §3)
        t["cf_annual"] = t["budget_annual_mwh"] / (t["max_mw"] * hpm.sum())
        with np.errstate(divide="ignore", invalid="ignore"):
            cf_m = t[MONTH_COLS].to_numpy(dtype=float) / (
                t["max_mw"].to_numpy()[:, None] * hpm[None, :]
            )
            t["cf_max_month"] = np.nanmax(
                np.where(np.isnan(cf_m), -np.inf, cf_m), axis=1
            )
        t.loc[~np.isfinite(t["cf_max_month"]), "cf_max_month"] = np.nan
        t["cf_over_1_months"] = (cf_m > 1.0).sum(axis=1)
        t["negative_months"] = (t[MONTH_COLS] < 0).sum(axis=1)

        # Gate status (PRECOMMIT §2).
        status = np.full(len(ids), "RECONCILED", dtype=object)
        status[~t["in_eia923"].to_numpy()] = "NO_923_SERIES"
        mism = t["in_eia923"].to_numpy() & (
            t["delta_mwh"].to_numpy() > RECONCILE_TOL_MWH
        )
        status[mism] = "MISMATCH"
        nonpos = t["in_eia923"].to_numpy() & (
            t["budget_annual_mwh"].fillna(1).to_numpy() <= 0
        )
        status[nonpos & (t["budget_annual_mwh"].fillna(1).to_numpy() == 0)] = "ALL_ZERO"
        status[nonpos & (t["budget_annual_mwh"].fillna(1).to_numpy() < 0)] = (
            "NON_POSITIVE"
        )
        t["status"] = status
        t["no_860_nameplate"] = t["in_eia923"] & ~t["in_eia860"]

        # Loader cross-check columns.
        t["loader_kept"] = [i in loader.index for i in ids]
        clipped = t[MONTH_COLS].clip(lower=0)
        t["loader_clip_mwh"] = np.where(
            t["loader_kept"], clipped.sum(axis=1) - t["budget_annual_mwh"], np.nan
        )
        common = loader.index.intersection(t.index)
        diff = (
            loader.loc[common].to_numpy() - clipped.loc[common, MONTH_COLS].to_numpy()
        )
        max_abs = float(np.nanmax(np.abs(diff))) if len(common) else 0.0
        max_mw_diff = (
            float((loader_max.loc[common] - t.loc[common, "max_mw"]).abs().max())
            if len(common)
            else 0.0
        )
        if max_abs > 1e-6 or max_mw_diff > 1e-6:
            raise AssertionError(
                f"{year}: loader budget differs from clipped artifact "
                f"(energy {max_abs:.6f} MWh, max_mw {max_mw_diff:.6f} MW)"
            )
        rows.append(t.reset_index())
        log.info(
            "%d: P923=%d P860=%d union=%d | RECONCILED=%d MISMATCH=%d NO_923_SERIES=%d "
            "ALL_ZERO=%d NON_POSITIVE=%d no_860=%d | loader kept %d, clip %.0f MWh over %d plants | "
            "max|loader-artifact| %.2e MWh",
            year,
            len(p923),
            len(p860),
            len(ids),
            int((t.status == "RECONCILED").sum()),
            int((t.status == "MISMATCH").sum()),
            int((t.status == "NO_923_SERIES").sum()),
            int((t.status == "ALL_ZERO").sum()),
            int((t.status == "NON_POSITIVE").sum()),
            int(t.no_860_nameplate.sum()),
            len(loader),
            float(np.nansum(t.loader_clip_mwh)),
            int((t.loader_clip_mwh > 0).sum()),
            max_abs,
        )

    budget = pd.concat(rows, ignore_index=True)
    budget = budget.join(eha, on="plant_id").join(hil, on="plant_id")
    budget["chain"] = [
        chain_membership(r, published)
        for _, r in budget.set_index("plant_id").iterrows()
    ]
    budget["chain_order"] = budget["plant_id"].map(
        published["order_upstream_to_downstream"]
    )
    recon = budget[
        [
            "plant_id",
            "plant_name",
            "ba_code",
            "zone",
            "year",
            "budget_annual_mwh",
            "netgen_annual_mwh_923",
            "delta_mwh",
            "status",
            "max_mw",
            "max_mw_source",
            "cf_annual",
            "cf_max_month",
            "cf_over_1_months",
            "negative_months",
            "loader_kept",
            "loader_clip_mwh",
            "river_eha",
            "mode_eha",
            "chain",
        ]
    ].sort_values(["year", "plant_id"])
    return budget, recon


def build_chain(budget: pd.DataFrame) -> pd.DataFrame:
    """Join the published chain transcription to nameplate, energy and mode: NWPP-36's reach table."""
    published = pd.read_csv(CHAIN_PUBLISHED_PATH)
    if not set(CHAIN_YEARS) <= set(budget.year.unique()):
        raise ValueError(f"the chain reach table needs budget years {CHAIN_YEARS}")
    b23 = budget[budget.year == 2023].set_index("plant_id")
    b24 = budget[budget.year == 2024].set_index("plant_id")
    b25 = budget[budget.year == 2025].set_index("plant_id")
    out = published.copy()
    out["ba_code"] = out.plant_id.map(b23["ba_code"])
    out["zone"] = out.plant_id.map(b23["zone"])
    out["max_mw_eia860"] = out.plant_id.map(b23["max_mw_eia860"])
    out["mwh_2023"] = out.plant_id.map(b23["budget_annual_mwh"])
    out["mwh_2024"] = out.plant_id.map(b24["budget_annual_mwh"])
    out["mwh_2025"] = out.plant_id.map(b25["budget_annual_mwh"])
    out["cf_2023"] = out.plant_id.map(b23["cf_annual"])
    out["cf_2024"] = out.plant_id.map(b24["cf_annual"])
    out["mode_eha"] = out.plant_id.map(b23["mode_eha"])
    out["river_eha"] = out.plant_id.map(b23["river_eha"])
    out["huc_eha"] = out.plant_id.map(b23["huc_eha"])
    out["ferc_docket_eha"] = out.plant_id.map(b23["ferc_docket_eha"])
    out["lat_eha"] = out.plant_id.map(b23["lat_eha"])
    out["lon_eha"] = out.plant_id.map(b23["lon_eha"])
    out["hilarri_grand_reservoir"] = out.plant_id.map(b23["hilarri_grand_reservoir"])
    out["hilarri_usgs_gage"] = out.plant_id.map(b23["hilarri_usgs_gage"])
    missing = out[out.max_mw_eia860.isna()]
    if not missing.empty:
        raise AssertionError(
            f"chain rows not in the EIA-860 population: {missing.plant_id.tolist()}"
        )
    return out.sort_values(["chain", "order_upstream_to_downstream"])


def build_within_month_930(
    log: logging.Logger, years: tuple[int, ...] = YEARS
) -> pd.DataFrame:
    """Per (BA, year, month) within-month shaping statistics off EIA-930 ``NG: WAT``."""
    from market_sim.data.eia930.frames import _eia_hourly_frame_filled

    rows: list[dict] = []
    for ba in BA_SERIES:
        for year in years:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                f = _eia_hourly_frame_filled(ba, year)
            if f is None or "NG: WAT" not in f.columns:
                continue
            w = pd.to_numeric(f["NG: WAT"], errors="coerce")
            date = pd.to_datetime(f["Local date"]).dt.normalize()
            df = pd.DataFrame({"w": w.to_numpy(), "date": date.to_numpy()}).dropna()
            if df.empty or df.w.max() <= 0:
                continue
            df["month"] = df.date.dt.month
            daily = df.groupby("date").agg(
                e=("w", "sum"), mx=("w", "max"), mn=("w", "min"), n=("w", "size")
            )
            daily = daily[daily.n >= 23]
            daily["month"] = daily.index.month
            for m, g in daily.groupby("month"):
                hours = df[df.month == m].w.to_numpy(dtype=float)
                mean_mw = float(g.e.sum() / g.n.sum())
                rows.append(
                    dict(
                        ba=ba,
                        year=year,
                        month=int(m),
                        days=int(len(g)),
                        mean_mw=mean_mw,
                        energy_mwh=float(g.e.sum()),
                        diurnal_amplitude=float(((g.mx - g.mn) / mean_mw).mean())
                        if mean_mw > 0
                        else np.nan,
                        daily_energy_cv=float(g.e.std() / g.e.mean())
                        if g.e.mean() > 0
                        else np.nan,
                        first_week_over_last_week=float(
                            g.e.iloc[:7].mean() / g.e.iloc[-7:].mean()
                        )
                        if g.e.iloc[-7:].mean() > 0
                        else np.nan,
                        p5_mw=float(np.percentile(hours, 5)),
                        p50_mw=float(np.percentile(hours, 50)),
                        p95_mw=float(np.percentile(hours, 95)),
                        min_mw=float(hours.min()),
                        max_mw=float(hours.max()),
                    )
                )
    out = pd.DataFrame(rows)
    log.info(
        "within-month 930 stats: %d (ba, year, month) rows over %d series",
        len(out),
        out.ba.nunique(),
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Build every artifact and print the gate summary."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument(
        "--skip-930",
        action="store_true",
        help="skip the EIA-930 within-month statistics",
    )
    ap.add_argument(
        "--years",
        type=int,
        nargs="+",
        default=None,
        help="budget years to build (default: every year the NWPP-11 extract "
        "carries). The chain reach table always uses 2023-2025.",
    )
    ap.add_argument(
        "--years-930",
        type=int,
        nargs="+",
        default=None,
        help="years for the EIA-930 within-month statistics (default: the "
        "original 2023-2025 set, so a budget-year extension does not re-derive "
        "the 930 table)",
    )
    args = ap.parse_args(argv)
    log = _log()
    years = tuple(sorted(args.years)) if args.years else extract_years()
    log.info("budget years: %s", list(years))

    budget, recon = build_budget(log, years)
    chain = build_chain(budget)
    budget.to_parquet(OUT_BUDGET, index=False)
    recon.to_csv(OUT_RECON, index=False)
    chain.to_csv(OUT_CHAIN, index=False)
    log.info(
        "wrote %s (%d rows), %s, %s (%d rows)",
        OUT_BUDGET.name,
        len(budget),
        OUT_RECON.name,
        OUT_CHAIN.name,
        len(chain),
    )
    if not args.skip_930:
        wm = build_within_month_930(
            log, tuple(sorted(args.years_930)) if args.years_930 else YEARS
        )
        wm.to_csv(OUT_930, index=False)
        log.info("wrote %s", OUT_930.name)

    # Gate verdict, in numbers.
    bad = recon[recon.status == "MISMATCH"]
    tot860 = budget[(budget.year == 2023) & budget.in_eia860].max_mw_eia860.sum()
    ms = chain[chain.chain == "COLUMBIA_MAINSTEM"]
    log.info(
        "GATE A: MISMATCH plant-years = %d (tolerance %.1f MWh) -> %s",
        len(bad),
        RECONCILE_TOL_MWH,
        "PASS" if bad.empty else "FAIL",
    )
    log.info(
        "CHAIN: Columbia mainstem %d plants, %.1f MW = %.2f%% of %.1f MW hydro; energy share 2023 %.2f%% / 2024 %.2f%%",
        len(ms),
        ms.max_mw_eia860.sum(),
        100 * ms.max_mw_eia860.sum() / tot860,
        tot860,
        100 * ms.mwh_2023.sum() / budget[budget.year == 2023].budget_annual_mwh.sum(),
        100 * ms.mwh_2024.sum() / budget[budget.year == 2024].budget_annual_mwh.sum(),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
