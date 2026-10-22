"""Curate measured transmission-constraint limits-at-bind into ``data/clean``.

Reads each registered ISO's committed raw extraction (SPP:
``data/raw/spp-effective-limits/rtbm_efflimit_bound_<year>.csv.gz``) and writes
one ``flowgate-limits-at-bind`` partition per (ISO, year) through
``clean_io.write_clean``. Schema:
``data/dictionary/schema/flowgate-limits-at-bind.schema.yaml``.

Intake-only (UC-SPP-CORRIDOR, 2026-10-22): no mechanism consumes it. The
limits are admissible inputs (rule 13); the binding hours are evidence only.

Usage:
    python scripts/data/curate_flowgate_limits_at_bind.py
    python scripts/data/curate_flowgate_limits_at_bind.py --isos SPP --years 2023
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import flowgate_limits_at_bind as flb
from scripts.lib.clean_io import paths

# SPP serves effective limits from 2022-04-14; the backcast span ends 2025.
DEFAULT_YEARS: tuple[int, ...] = (2022, 2023, 2024, 2025)


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
    """Curate and write every requested (ISO, year) partition; return the paths.

    A year whose raw extraction has not landed is skipped. Reads only
    ``data/raw``; idempotent.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = flb.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)
    years = list(years) if years is not None else list(DEFAULT_YEARS)
    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        raw_dir = raw_root / spec.raw_subdir
        for year in years:
            df = spec.parse(raw_dir, year)
            if df.empty:
                continue
            src = sorted(raw_dir.glob(f"*_{year}.csv.gz"))
            path = clean_io.write_clean(
                df,
                flb.DATATYPE,
                iso=iso,
                year=year,
                market="rt",
                source=_rel(src[0]) if src else _rel(raw_dir),
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(f"{iso} {year}: {len(df)} constraint-hours -> {_rel(path)}")
    return written


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="+", default=None)
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument("--raw-root", type=Path, default=None)
    args = ap.parse_args()
    if not curate(raw_root=args.raw_root, isos=args.isos, years=args.years):
        raise SystemExit("nothing curated — no raw files found")


if __name__ == "__main__":
    main()
