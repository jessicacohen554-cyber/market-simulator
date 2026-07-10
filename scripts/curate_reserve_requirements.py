"""Curate the ``reserve-requirements`` clean datatype.

Measured as-enforced hourly reserve requirements per (ISO, reserve location,
product), written through the frozen :func:`scripts.lib.clean_io.write_clean`
seam against ``data/dictionary/schema/reserve-requirements.schema.yaml``.

Per-ISO parsing lives in ``scripts/lib/reserve_requirements/<iso>.py`` (each
registers an :class:`~scripts.lib.reserve_requirements.IsoSpec`); this script
is a thin dispatcher over the registry, so adding an ISO never touches it.
Rows are per calendar year, so each (ISO, year) writes one partition
``data/clean/reserve-requirements/<ISO>/<year>/…parquet``. Reads only
``data/raw``; idempotent. An ISO/year whose raw windows have not landed is
skipped (the NEISO raw window CSVs are gitignored — regenerate with
``python scripts/fetch_neiso_reserve_requirements.py``).

Run ``python scripts/curate_reserve_requirements.py [--isos NEISO] [--years 2023 ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import reserve_requirements as rr
from scripts.lib.clean_io import paths


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def curate(
    raw_root: Path | None = None,
    isos: Iterable[str] | None = None,
    years: Iterable[int] | None = None,
) -> list[Path]:
    """Curate and write every requested (ISO, year) partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.
    isos:
        Subset of ISOs (default: every registered ISO).
    years:
        Subset of calendar years (default: every year the ISO's raw drop zone
        covers).

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = rr.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        iso_years = list(years) if years else spec.years(raw_root)
        if not iso_years:
            print(
                f"[skip] {iso}: no raw windows under {_rel(rr.raw_dir_for(iso, raw_root))}"
            )
            continue
        for year in iso_years:
            df = spec.parse(raw_root, int(year))
            if df.empty:
                print(f"[skip] {iso} {year}: no raw rows")
                continue
            source = _rel(rr.raw_dir_for(iso, raw_root))
            path = clean_io.write_clean(
                df, rr.DATATYPE, iso=iso, year=int(year), source=source
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
    parser.add_argument(
        "--years",
        nargs="*",
        type=int,
        default=None,
        help="subset of calendar years (default: every year present in raw)",
    )
    args = parser.parse_args(argv)
    curate(isos=args.isos, years=args.years)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
