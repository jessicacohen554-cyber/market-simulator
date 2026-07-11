#!/usr/bin/env python3
"""Fetch NREL ATB 2024 electricity cost/performance data (OEDI data lake).

Downloads the public ``ATBe.csv`` (NREL Annual Technology Baseline,
electricity module, 2024 edition v3.0.0 -- ~572k rows / ~94MB, every
technology x resource-class x parameter x financial-case x cost-case x
cost-recovery-period x year combination NREL publishes) from the OEDI S3
data lake and filters it down to the technologies and parameters this
model's ``NEW_ENTRY_COSTS`` / ``STORAGE_TECH_COSTS`` taxonomy needs, writing
the filtered extract as the committed raw artifact.

Why filtered, not the full file: the source is ~94MB, most of it techs and
finance-case/R&D rows this model never consumes (CSP, hydrokinetic,
distributed PV classes, every one of ATB's ~30 wind/solar resource classes,
etc.). Landing the full file would make this the largest file in the repo
for no benefit. The filter keeps every row needed to reconstruct this
model's technology set at every published year/cost-case/cost-recovery-
period, and is fully documented (see ``TECH_TECHDETAIL``/``PARAMETERS``
below and ``data/raw/nrel-atb/README.md``) so it is exactly reproducible
from the original source -- a technology-scoped extract, not a lossy
summary (CLAUDE.md rule 13: reproducible from a forward-regenerating
source).

NOTE: ``atb.nrel.gov`` (and the whole ``nrel.gov``/``docs.nrel.gov`` domain)
is blocked by this environment's outbound network policy (proxy CONNECT
failures). The OEDI S3 data lake (``oedi-data-lake.s3.amazonaws.com``, a
separate AWS-hosted domain) is NOT blocked and is NREL's own recommended
machine-readable distribution channel for ATB data
(https://data.openei.org/submissions/4129, the "Annual Technology Baseline"
OEDI submission) -- this script uses that, not a scrape of the site.

Output (raw, immutable, never hand-edited):
  data/raw/nrel-atb/atb_2024_electricity_filtered.csv

Usage:
    python scripts/fetch_nrel_atb.py
    python scripts/fetch_nrel_atb.py --atb-year 2024 --atb-version v3.0.0
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve

import pandas as pd

REPO = Path(__file__).resolve().parent.parent
OUT_DIR = REPO / "data" / "raw" / "nrel-atb"
OUT_CSV = OUT_DIR / "atb_2024_electricity_filtered.csv"

OEDI_BASE = "https://oedi-data-lake.s3.amazonaws.com/ATB/electricity/csv"

# (technology, techdetail) pairs matching this model's NEW_ENTRY_COSTS /
# STORAGE_TECH_COSTS taxonomy. Selected via each tech's own ATB `default`=1
# representative resource class where one exists (verified against the
# source file, not guessed); explicit techdetail strings (also verified
# present) where ATB carries no default flag (NaturalGas_FE). See
# data/raw/nrel-atb/README.md for the tech -> model-tech mapping.
TECH_TECHDETAIL: list[tuple[str, str]] = [
    ("LandbasedWind", "Class4"),
    ("UtilityPV", "Class5"),
    ("NaturalGas_FE", "NG 2-on-1 Combined Cycle (F-Frame)"),
    ("NaturalGas_FE", "NG Combustion Turbine (F-Frame)"),
    ("NaturalGas_FE", "NG 2-on-1 Combined Cycle (F-Frame) 95% CCS"),
    ("NaturalGas_FE", "NG 2-on-1 Combined Cycle (F-Frame) 97% CCS"),
    ("Nuclear", "Nuclear - Large"),
    ("Nuclear", "Nuclear - Small"),
    ("Utility-Scale Battery Storage", "2Hr Battery Storage"),
    ("Utility-Scale Battery Storage", "4Hr Battery Storage"),
    ("Utility-Scale Battery Storage", "6Hr Battery Storage"),
    ("Utility-Scale Battery Storage", "8Hr Battery Storage"),
    ("Utility-Scale Battery Storage", "10Hr Battery Storage"),
    ("Coal_FE", "Coal-new"),
    ("Biopower", "Dedicated"),
    ("Hydropower", "NPD1"),
    ("Geothermal", "HydroFlash"),
    ("OffShoreWind", "Class3"),
    ("OffShoreWind", "Class12"),
]

# core_metric_parameter values to keep. Scoped to exactly what the D4
# calendar-year cost trajectories need -- capex/FOM by tech x year x case
# (forecast-driver-capacity-revenue-audit-plan-2026-07.md Sec.4 N8). Excludes
# ATB's finance-internals parameters (WACC, CRF, FCR, debt fraction,
# interest/tax rates) as well as Variable O&M/CF/Heat Rate: those aren't
# consumed by this model's cost tables (VOM/CF/heat-rate inputs come from
# the fleet/offer-curve pipeline, not ATB), and excluding them keeps the
# filter's intent legible and the committed extract small. A future session
# needing ATB's VOM/CF/Heat Rate series can re-add them here and re-run
# against a fresh OEDI download.
PARAMETERS: list[str] = ["CAPEX", "Fixed O&M"]

KEEP_COLUMNS = [
    "atb_year",
    "technology",
    "techdetail",
    "display_name",
    "core_metric_parameter",
    "core_metric_case",
    "tax_credit_case",
    "scenario",
    "crpyears",
    "default",
    "core_metric_variable",
    "value",
]


def download_source(atb_year: int, atb_version: str, dest: Path) -> None:
    """Download the full ATBe.csv for one ATB edition/version to ``dest``."""
    url = f"{OEDI_BASE}/{atb_year}/{atb_version}/ATBe.csv"
    print(f"downloading {url} ...")
    try:
        urlretrieve(url, dest)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"NREL ATB OEDI download failed ({url}): {exc}") from exc
    print(f"  {dest.stat().st_size / 1e6:.1f} MB")


def filter_atb(source_csv: Path) -> pd.DataFrame:
    """Filter the full ATB electricity CSV down to :data:`TECH_TECHDETAIL`.

    Also drops the ``crpyears`` (cost-recovery-period) axis: verified against
    the full source that CAPEX/Fixed O&M/Variable O&M/CF/Heat Rate never
    differ across crpyears for the same (technology, techdetail, parameter,
    case, tax_credit_case, scenario, year) -- ATB's crpyears choice only
    affects derived LCOE/finance metrics this extract doesn't carry, so
    keeping it would triple the row count for zero information. Keeps the
    first (smallest) crpyears row per key; a consumer that also wants the
    original crpyears axis can re-run this filter against a fresh OEDI
    download with the dedup step removed.
    """
    df = pd.read_csv(source_csv, low_memory=False)

    mask = pd.Series(False, index=df.index)
    for tech, detail in TECH_TECHDETAIL:
        mask |= (df["technology"] == tech) & (df["techdetail"] == detail)

    out = df[
        mask
        & df["core_metric_parameter"].isin(PARAMETERS)
        & (df["core_metric_case"] == "Market")
    ][KEEP_COLUMNS].copy()

    out = out.sort_values(
        [
            "technology",
            "techdetail",
            "core_metric_parameter",
            "scenario",
            "crpyears",
            "core_metric_variable",
        ]
    )
    dedup_key = [
        "technology",
        "techdetail",
        "core_metric_parameter",
        "core_metric_case",
        "tax_credit_case",
        "scenario",
        "core_metric_variable",
    ]
    out = out.drop_duplicates(subset=dedup_key, keep="first")
    out = out.drop(columns=["crpyears"]).reset_index(drop=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--atb-year", type=int, default=2024)
    ap.add_argument("--atb-version", default="v3.0.0")
    ap.add_argument(
        "--source-csv",
        default=None,
        help="path to an already-downloaded full ATBe.csv (skip the download)",
    )
    args = ap.parse_args(argv)

    if args.source_csv:
        source = Path(args.source_csv)
    else:
        tmp_dir = Path(tempfile.mkdtemp(prefix="nrel_atb_"))
        source = tmp_dir / "ATBe.csv"
        download_source(args.atb_year, args.atb_version, source)

    print(
        f"filtering to {len(TECH_TECHDETAIL)} technology/techdetail combos, "
        f"{len(PARAMETERS)} parameters, Market financial case ..."
    )
    filtered = filter_atb(source)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    filtered.to_csv(OUT_CSV, index=False)
    print(f"wrote {len(filtered)} rows -> {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
