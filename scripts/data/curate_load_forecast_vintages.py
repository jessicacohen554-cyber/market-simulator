"""Curate the ``load-forecast-vintages`` clean datatype.

Every issued vintage of an ISO's own short-term hourly load forecast (SPP's
MTLF archive first; lane UC-DF-AUDIT, owner ruling UC-DESK r14), reconciled
onto ``data/dictionary/schema/load-forecast-vintages.schema.yaml`` and written
through :func:`scripts.lib.clean_io.write_clean`, one partition per ISO and
issue year: ``data/clean/load-forecast-vintages/<ISO>/load-forecast-vintages_<year>.parquet``.

Per-ISO parsing lives in ``scripts/lib/load_forecast_vintages/<iso>.py``; this
script is a thin dispatcher over the registry. Reads only ``data/raw``;
idempotent. Run ``python scripts/data/curate_load_forecast_vintages.py [--isos SPP]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import load_forecast_vintages as lfv
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
    """Curate and write every requested ISO's vintage partitions (one per issue year).

    ``raw_root`` defaults to ``paths.RAW_DIR`` (tests point it at a fixture);
    ``isos`` defaults to every registered ISO. An ISO with no raw files is
    skipped. Returns the paths written.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = lfv.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        source = _rel(lfv.raw_dir_for(iso, raw_root))
        parts = lfv.parse_iso(iso, raw_root)
        if not parts:
            print(f"[skip] {iso}: no raw vintages under {source}")
            continue
        for year, df in sorted(parts.items()):
            path = clean_io.write_clean(
                df, lfv.DATATYPE, iso=iso, year=year, source=source
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(
                f"wrote {path}  ({len(df)} rows, "
                f"{df['issue_time_utc'].nunique()} vintages)"
            )
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos", nargs="*", default=None, help="subset of ISOs (default: all)"
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
