"""Curate ``seam-neighbour-price``: raw per-market seam prices -> clean Parquet.

Reads only ``data/raw/seam-neighbour-price/<iso>/`` (each market's parser is
registered in ``scripts/lib/seam_neighbour_price/<iso>.py``) and writes one
clean file per (iso, year) through ``clean_io.write_clean``.  A year whose raw
file is absent is skipped with a note (PJM is gitignored and must be re-fetched;
see the raw README).

Usage:
    uv run python scripts/data/curate_seam_neighbour_price.py [--isos NYISO PJM]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

from scripts.lib import clean_io  # noqa: E402
from scripts.lib.seam_neighbour_price import (  # noqa: E402
    DATATYPE,
    finalize,
    load_registry,
    raw_dir_for,
)


def curate(raw_root: Path | None = None, isos: list[str] | None = None) -> list[Path]:
    """Curate every registered market-year present on disk; return paths written."""
    raw_root = RAW_DATA_DIR if raw_root is None else Path(raw_root)
    written: list[Path] = []
    for iso, spec in sorted(load_registry().items()):
        if isos and iso not in {i.upper() for i in isos}:
            continue
        raw_dir = raw_dir_for(iso, raw_root)
        for year in spec.years:
            try:
                df = finalize(spec.parse(raw_dir, year))
            except FileNotFoundError as exc:
                print(f"skip {iso} {year}: {exc.filename} absent")
                continue
            path = clean_io.write_clean(
                df,
                DATATYPE,
                iso=iso,
                year=year,
                source=f"{raw_dir.name}/ ({spec.source})",
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(f"wrote {path} ({len(df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--isos", nargs="*", default=None)
    args = p.parse_args(argv)
    curate(isos=args.isos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
