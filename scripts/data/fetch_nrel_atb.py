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

Output (raw, immutable, never hand-edited), one file per ATB edition/version:
  data/raw/nrel-atb/atb_2024_electricity_filtered.csv     (2024 v3.0.0)
  data/raw/nrel-atb/atb_2024v4_electricity_filtered.csv   (2024 v4.0.0)

Usage:
    python scripts/data/fetch_nrel_atb.py
    python scripts/data/fetch_nrel_atb.py --atb-year 2024 --atb-version v4.0.0
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlretrieve

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import NREL_ATB_DIR  # noqa: E402

OUT_DIR = NREL_ATB_DIR

# Output filename stem per (edition year, version). NREL re-releases an ATB
# edition under successive point versions when it corrects it, so the stem
# carries the version too -- otherwise a refreshed edition would silently
# overwrite the extract earlier constants were derived from. The original
# 2024 v3.0.0 extract keeps its historical unsuffixed name (committed, and
# referenced by data/raw/nrel-atb/README.md and the derive scripts); every
# other version gets an explicit "<year>v<major>" stem.
_OUT_STEM = {
    (2024, "v3.0.0"): "atb_2024_electricity_filtered",
    (2024, "v4.0.0"): "atb_2024v4_electricity_filtered",
}


def out_csv_path(atb_year: int, atb_version: str) -> Path:
    """Return the raw extract path for one ATB edition/version.

    Falls back to a "<year>v<major>" stem for an edition/version this script
    has not seen before, so a newly released ATB lands under a distinct name
    rather than overwriting an existing extract.
    """
    stem = _OUT_STEM.get(
        (atb_year, atb_version),
        f"atb_{atb_year}v{atb_version.lstrip('v').split('.')[0]}_electricity_filtered",
    )
    return OUT_DIR / f"{stem}.csv"


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
    # ATB's four EGS (enhanced geothermal) classes — added 2026-07-19 for the
    # new-build cost benchmarking session (capacity-cost-grounding), closing
    # the FF-1E gap ("ATB's EGS classes are not in the committed CAPEX/FOM
    # extract"). NF = near-field (adjacent to an existing hydrothermal field,
    # ATB's first-mover EGS class); Deep = deep greenfield EGS. These rows are
    # committed as APPENDED part files (part11+) after the original extract
    # parts, NOT interleaved in this script's sort order — see
    # data/raw/nrel-atb/README.md for the append convention and the source
    # 1-ulp float-repr drift note (a from-scratch regeneration reproduces
    # every value but reorders rows and re-serializes 9/3162 floats'
    # last digit).
    ("Geothermal", "NFEGSFlash"),
    ("Geothermal", "NFEGSBinary"),
    ("Geothermal", "DeepEGSFlash"),
    ("Geothermal", "DeepEGSBinary"),
]

# core_metric_parameter values to keep for EVERY technology. Scoped to
# exactly what the D4 calendar-year cost trajectories need -- capex/FOM by
# tech x year x case (forecast-driver-capacity-revenue-audit-plan-2026-07.md
# Sec.4 N8). Excludes ATB's finance-internals parameters (WACC, CRF, FCR,
# debt fraction, interest/tax rates), which no consumer in this repo reads.
PARAMETERS: list[str] = ["CAPEX", "Fixed O&M"]

# Additional core_metric_parameter values kept for ONE technology only, so
# widening the extract for a named consumer does not balloon it for every
# tech. Applied as a union with :data:`PARAMETERS`.
#
# WIDENED 2026-09-06 (capx D65-B item 1, executing D64 STOP 6 / D65 §9 item 1).
# ``ScenarioConfig.ccs_retrofit_vom_adder`` is the capture island's VOM
# increment, and until this widening it could not be read off the pinned
# basis at all: the extract carried only CAPEX and Fixed O&M for
# ``NaturalGas_FE``, which is precisely why that field shipped at an
# uncited 8.0 $/MWh (2.7-3.6x every published basis; D64 Sec.2.4). ATB
# publishes the increment directly -- NG 2-on-1 CC (F-Frame) 95% CCS 4.8
# minus NG 2-on-1 CC (F-Frame) 2.1 = 2.7 2022$/MWh -- from the SAME source
# bytes this filter already reads (OEDI ATBe.csv 2024 v4.0.0, sha256
# 567dde9d85caa759bc3f2e42c9aa14a5f85e471ca4133ccc522e7a92e020297a), so no
# new source, no new download and no new vintage is involved.
#
# ``Heat Rate`` rides along for the same technology because it is the
# physical companion of that VOM increment and the cross-check on the
# reference host the retrofit seam is sized against: ATB's own NG 2-on-1 CC
# (F-Frame) heat rate @2026 is 6.3 MMBtu/MWh, which is exactly
# ``min(HEAT_RATE_BINS["gas_cc"])`` -- the ``hr_ref`` in
# ``ccs.ccs_retrofit_captured_ref_t_per_mwh``. Landing it makes that
# identity assertable from the pinned bytes rather than by coincidence.
# Consumers: scripts/data/derive_entry_costs_from_atb.py
# (``derive_ccs_retrofit_vom_adder`` / ``derive_gas_cc_heat_rate``) and
# tests/unit/config/test_ccs_retrofit_fixed_cost_basis.py.
EXTRA_PARAMETERS_BY_TECHNOLOGY: dict[str, list[str]] = {
    "NaturalGas_FE": ["Variable O&M", "Heat Rate"],
}


def parameters_for(technology: str) -> list[str]:
    """Return the core_metric_parameter values kept for one ATB technology."""
    return PARAMETERS + EXTRA_PARAMETERS_BY_TECHNOLOGY.get(technology, [])


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

    # The parameter scope is PER TECHNOLOGY (see EXTRA_PARAMETERS_BY_TECHNOLOGY):
    # every tech keeps CAPEX/Fixed O&M, and NaturalGas_FE additionally keeps
    # Variable O&M/Heat Rate. Building the mask per (tech, detail) pair rather
    # than as one global `isin` is what keeps the widening scoped.
    mask = pd.Series(False, index=df.index)
    for tech, detail in TECH_TECHDETAIL:
        mask |= (
            (df["technology"] == tech)
            & (df["techdetail"] == detail)
            & df["core_metric_parameter"].isin(parameters_for(tech))
        )

    out = df[mask & (df["core_metric_case"] == "Market")][KEEP_COLUMNS].copy()

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
    # Defaults track the latest ATB edition/version published on OEDI as of
    # 2026-07-31 (2024 v4.0.0, mirrored 2026-07-28). 2024 is still the
    # current EDITION -- no 2025/2026 ATB exists (verified against the ATB
    # site itself, atb.nlr.gov, and the OEDI listing; see the raw README).
    # Each version writes its own file, so re-running with an older
    # --atb-version never overwrites a newer extract.
    ap.add_argument("--atb-version", default="v4.0.0")
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

    all_params = sorted(
        set(PARAMETERS).union(*EXTRA_PARAMETERS_BY_TECHNOLOGY.values())
        if EXTRA_PARAMETERS_BY_TECHNOLOGY
        else PARAMETERS
    )
    print(
        f"filtering to {len(TECH_TECHDETAIL)} technology/techdetail combos, "
        f"parameters {all_params} (per-technology scope), "
        "Market financial case ..."
    )
    filtered = filter_atb(source)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_csv = out_csv_path(args.atb_year, args.atb_version)
    filtered.to_csv(out_csv, index=False)
    print(f"wrote {len(filtered)} rows -> {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
