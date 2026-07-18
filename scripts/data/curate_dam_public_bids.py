"""Curate raw ISO DAM public-bid disclosures into the clean tree.

Reads each registered ISO's raw daily files (CAISO: OASIS ``PUB_DAM_GRP``
zips under ``data/raw/caiso-public-bids/zips/``, fetched by
``scripts/data/fetch_caiso_public_bids.py``) and writes one schema-validated
long-format Parquet per (ISO, market, year) through the frozen
``scripts.lib.clean_io.write_clean`` seam:

    data/clean/dam-public-bids/<ISO>/<MARKET>/dam-public-bids_<year>.parquet

Idempotent: re-running overwrites the same partitions from the same raw
inputs. Per-ISO parsing lives in ``scripts/lib/dam_public_bids/<iso>.py``
registry modules — this dispatcher never branches on the ISO name.

Usage:
    python scripts/data/curate_dam_public_bids.py                 # all ISOs/years
    python scripts/data/curate_dam_public_bids.py --isos CAISO --years 2024
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import clean_io  # noqa: E402
from lib.dam_public_bids import DATATYPE, IsoSpec, load_specs  # noqa: E402


def _curate_spec(
    spec: IsoSpec,
    raw_root: Path | None,
    years: list[int] | None,
) -> list[Path]:
    """Curate one ISO spec: parse daily files, write one Parquet per year."""
    raw_dir = spec.raw_dir if raw_root is None else raw_root
    day_files = sorted(raw_dir.glob(spec.file_glob))
    if not day_files:
        print(f"  {spec.iso}: no raw files under {raw_dir} — skipped")
        return []

    by_year: dict[int, list[Path]] = defaultdict(list)
    for f in day_files:
        # Daily file stems start with the trade date: <YYYYMMDD>_...
        year = int(f.name[:4])
        if years is None or year in years:
            by_year[year].append(f)

    written: list[Path] = []
    for year in sorted(by_year):
        files = by_year[year]
        frames = [spec.parse_day(f) for f in files]
        df = pd.concat(frames, ignore_index=True)
        out = clean_io.write_clean(
            df,
            DATATYPE,
            iso=spec.iso,
            year=year,
            market=spec.market,
            source=(
                f"{raw_dir} ({len(files)} daily files, "
                f"{files[0].name} .. {files[-1].name}) "
                f"via scripts/data/curate_dam_public_bids.py"
            ),
        )
        clean_io.validate_clean(out)
        written.append(out)
        print(f"  {spec.iso} {year}: {len(df):,} rows from {len(files)} days -> {out}")
    return written


def curate(
    raw_root: Path | None = None,
    isos: list[str] | None = None,
    years: list[int] | None = None,
) -> list[Path]:
    """Curate all (or the named) ISOs; returns the clean paths written.

    ``raw_root`` overrides every spec's raw directory (tests point it at a
    tmp fixture dir).
    """
    written: list[Path] = []
    for spec in load_specs(isos):
        written.extend(_curate_spec(spec, raw_root, years))
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="+", default=None, help="ISOs (default: all)")
    ap.add_argument(
        "--years", nargs="+", type=int, default=None, help="years (default: all)"
    )
    ap.add_argument(
        "--raw-root", type=Path, default=None, help="override raw directory"
    )
    args = ap.parse_args(argv)
    written = curate(raw_root=args.raw_root, isos=args.isos, years=args.years)
    print(f"done: {len(written)} clean file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
