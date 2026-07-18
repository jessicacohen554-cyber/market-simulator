"""Curate the ``capacity-market-elcc`` clean datatype.

Reconciles each capacity-market ISO's published ELCC / accreditation study
(PJM ELCC class ratings, MISO wind/solar ELCC by penetration, NYISO/ISO-NE
equivalents) onto the single tidy schema in
``data/dictionary/schema/capacity-market-elcc.schema.yaml`` and writes each
ISO partition through the frozen :func:`scripts.lib.clean_io.write_clean`
seam.

Per-ISO parsing lives in ``scripts/lib/capacity_market_elcc/<iso>.py`` (each
registers an :class:`~scripts.lib.capacity_market_elcc.IsoSpec`); this script
is a thin dispatcher over the registry. There is no per-year partition (rows
carry ``study_vintage`` as a column since a study may cover several vintages),
so each ISO writes one partition
``data/clean/capacity-market-elcc/<ISO>/…parquet`` (``year=None``). Reads
only ``data/raw``; idempotent. Run
``python scripts/data/curate_capacity_market_elcc.py [--isos PJM MISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import capacity_market_elcc as elcc
from scripts.lib import clean_io
from scripts.lib.clean_io import paths


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Curate and write every requested ISO's ELCC partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO whose
        raw CSV has not landed yet yields an empty frame and is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = elcc.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = elcc.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw rows under {_rel(elcc.raw_dir_for(iso, raw_root))}"
            )
            continue
        source = _rel(elcc.raw_dir_for(iso, raw_root))
        path = clean_io.write_clean(
            df, elcc.DATATYPE, iso=iso, year=None, source=source
        )
        clean_io.validate_clean(path)
        written.append(path)
        print(f"wrote {path}  ({len(df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="*",
        default=None,
        help="subset of ISOs to curate (default: every registered ISO)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
