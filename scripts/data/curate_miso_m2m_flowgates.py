"""Curate the ``miso-m2m-flowgates`` clean datatype.

Parses MISO's annual M2M/CMP flowgate settlement mirrors
(``data/raw/miso-m2m-flowgates/M2M_Settlement_srw_YYYY.csv.gz``, fetched by
``scripts/data/fetch_miso_m2m_flowgates.py``) onto the tidy schema in
``data/dictionary/schema/miso-m2m-flowgates.schema.yaml`` and writes one
clean partition per year through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Timestamp handling: the source stamps are hour-ENDING labels 1..24 on MISO
market time (EST, UTC-5 fixed year-round, no DST — every day carries the
full 24 labels and HE 24 is posted as "24:00:00"). Hour-beginning EST =
posted date + (HE-1) h; UTC = EST + 5 h. ``seam_rto`` is derived as the
non-MISO RTO of the (monitoring, counterparty) pair — the M2M seam the
flowgate's coordination belongs to.

RULE 13 (CLAUDE.md): the shadow-price / market-flow / credit columns are the
ANSWER class (validation only, never a solve input); the FFE columns are a
CMP market-design quantity, admissible in kind. The line is fixed in the
schema header.

Run ``python scripts/data/curate_miso_m2m_flowgates.py [--years 2023 2024]``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import clean_io  # noqa: E402
from scripts.lib.clean_io import paths  # noqa: E402

DATATYPE = "miso-m2m-flowgates"

# MISO market time is EST, UTC-5 fixed year-round (no DST) — the repo-wide
# convention for docs.misoenergy.org market reports (see e.g.
# data/raw/transfer-constraint-binding/MISO/README.md).
_EST_UTC_OFFSET_H = 5

# Years curated by default — the calibration train window (CLAUDE.md
# rule 22; the fetch script enforces the same boundary).
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# Source column -> schema column (order matters for the output frame).
_RENAME = {
    "FLOWGATE_ID": "flowgate_id",
    "FLOWGATE_NAME": "flowgate_name",
    "MONITORING_RTO": "monitoring_rto",
    "CP_RTO": "cp_rto",
    "MISO_SHADOW_PRICE": "miso_shadow_price_usd_mwh",
    "MISO_MKT_FLOW": "miso_mkt_flow_mw",
    "MISO_FFE": "miso_ffe_mw",
    "CP_SHADOW_PRICE": "cp_shadow_price_usd_mwh",
    "CP_MKT_FLOW": "cp_mkt_flow_mw",
    "CP_FFE": "cp_ffe_mw",
    "MISO_CREDIT": "miso_credit_usd",
    "CP_CREDIT": "cp_credit_usd",
}


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _raw_dir(raw_root: Path) -> Path:
    return raw_root / DATATYPE


def build_year_frame(csv_path: Path, year: int) -> pd.DataFrame:
    """Read one annual settlement mirror and shape it onto the schema."""
    df = pd.read_csv(csv_path)
    missing = [c for c in ("HOUR_ENDING", *_RENAME) if c not in df.columns]
    if missing:
        raise ValueError(f"{csv_path}: missing source columns {missing}")

    # Hour-ending label 1..24 on the posted date ("24:00:00" marks HE 24;
    # parse date and HE separately, never through a datetime parser).
    parts = df["HOUR_ENDING"].astype(str).str.split(" ", n=1, expand=True)
    date = pd.to_datetime(parts[0])
    he = parts[1].str.split(":", n=1, expand=True)[0].astype(int)
    if not ((he >= 1) & (he <= 24)).all():
        raise ValueError(f"{csv_path}: hour-ending labels outside 1..24")
    est = date + pd.to_timedelta(he - 1, unit="h")
    bad_year = est.dt.year != year
    if bad_year.any():
        raise ValueError(f"{csv_path}: {int(bad_year.sum())} rows dated outside {year}")

    out = df.rename(columns=_RENAME)[list(_RENAME.values())].copy()
    # Whole-valued source columns can parse as int64; the schema is float64.
    for col in _RENAME.values():
        if col not in ("flowgate_id", "flowgate_name", "monitoring_rto", "cp_rto"):
            out[col] = out[col].astype("float64")
    out.insert(0, "iso", "MISO")
    out.insert(
        1,
        "interval_start_utc",
        (est + pd.Timedelta(hours=_EST_UTC_OFFSET_H)).dt.tz_localize("UTC"),
    )
    out.insert(2, "interval_start_est", est)
    # The M2M seam: the non-MISO RTO of the (monitoring, counterparty) pair.
    out.insert(
        8,
        "seam_rto",
        out["cp_rto"].where(out["cp_rto"] != "MISO", out["monitoring_rto"]),
    )
    if not out["seam_rto"].isin(("PJM", "SWPP")).all():
        bad = sorted(
            out.loc[~out["seam_rto"].isin(("PJM", "SWPP")), "seam_rto"].unique()
        )
        raise ValueError(f"{csv_path}: unexpected seam_rto values {bad}")

    dupes = out.duplicated(["flowgate_id", "interval_start_utc"]).sum()
    if dupes:
        raise ValueError(f"{csv_path}: {dupes} duplicate (flowgate, hour) rows")
    return out.sort_values(["interval_start_utc", "flowgate_id"]).reset_index(drop=True)


def curate(
    raw_root: Path | None = None,
    years: Iterable[int] | None = None,
) -> list[Path]:
    """Curate and write every requested year's partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.
    years:
        Years (default: :data:`DEFAULT_YEARS`).

    Returns the list of paths written. A year whose mirror has not landed is
    skipped. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    years = list(years) if years is not None else list(DEFAULT_YEARS)
    raw_dir = _raw_dir(raw_root)

    written: list[Path] = []
    for year in years:
        src = raw_dir / f"M2M_Settlement_srw_{year}.csv.gz"
        if not src.is_file():
            print(
                f"MISO {year}: no mirror at {_rel(src)} — skipped "
                "(run scripts/data/fetch_miso_m2m_flowgates.py)"
            )
            continue
        df = build_year_frame(src, year)
        path = clean_io.write_clean(
            df, DATATYPE, iso="MISO", year=year, source=_rel(src)
        )
        clean_io.validate_clean(path)
        written.append(path)
        print(f"MISO {year}: {len(df)} rows -> {_rel(path)}")
    return written


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help=f"years (default {DEFAULT_YEARS})",
    )
    ap.add_argument(
        "--raw-root", type=Path, default=None, help="override the raw tree root"
    )
    args = ap.parse_args()
    written = curate(raw_root=args.raw_root, years=args.years)
    if not written:
        raise SystemExit("nothing curated — no raw mirrors found")


if __name__ == "__main__":
    main()
