"""Curate the ``nyiso-downstate-gas`` clean datatype.

Builds the daily delivered-gas index a non-firm downstate NYISO gas peaker faces
(measured Transco Zone 6 NY pipeline-hub daily spot + measured monthly LDC
city-gate premium) onto the schema in
``data/dictionary/schema/nyiso-downstate-gas.schema.yaml`` and writes each
ISO-year partition through the frozen :func:`scripts.lib.clean_io.write_clean`
seam. Every input is a measured, forward-native series (rule-13 admissible);
nothing is fitted to a residual.

The construction lives in ``scripts/lib/nyiso_downstate_gas.py`` (shared with the
model's raw-fallback reader); this script is a thin dispatcher over its
per-ISO :data:`~scripts.lib.nyiso_downstate_gas.REGISTRY`, so adding an ISO never
touches it. Rows are per-year (daily), so each ISO-year writes its own partition
``data/clean/nyiso-downstate-gas/<ISO>/<year>/…parquet``. Reads only
``data/raw``; idempotent. Run
``python scripts/data/curate_nyiso_downstate_gas.py [--isos NYISO] [--years 2023 ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import nyiso_downstate_gas as dg
from scripts.lib.clean_io import paths


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _years_for(spec: dg.DownstateGasSpec, raw_root: Path) -> list[int]:
    """Return the calendar years the ISO's monthly transport-rate file covers."""
    import pandas as pd

    frame = pd.read_csv(raw_root / spec.transport_monthly_file)
    return sorted({int(y) for y in frame["year"].dropna().unique()})


def curate(
    raw_root: Path | None = None,
    isos: Iterable[str] | None = None,
    years: Iterable[int] | None = None,
) -> list[Path]:
    """Curate and write every requested ISO-year downstate-gas partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO).
    years:
        Subset of years (default: every year the ISO's monthly premium file
        covers).

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    wanted = [s.upper() for s in isos] if isos else sorted(dg.REGISTRY)

    written: list[Path] = []
    for iso in wanted:
        spec = dg.REGISTRY[iso]
        iso_years = list(years) if years else _years_for(spec, raw_root)
        source = (
            f"{_rel(raw_root / spec.hub_daily_file)} (daily hub) + "
            f"{_rel(raw_root / spec.transport_monthly_file)} "
            "(monthly per-LDC non-firm transport rate)"
        )
        for year in iso_years:
            df = dg.build_daily_frame(iso, year, raw_root)
            path = clean_io.write_clean(
                df, dg.DATATYPE, iso=iso, year=year, source=source
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
        help="subset of years (default: every year the monthly premium file covers)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos, years=args.years)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
