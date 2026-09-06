"""Curate the ``load-forecast`` clean datatype.

Reconciles each ISO's PUBLISHED long-term load forecast — ERCOT's LTLF, the CEC's
California Energy Demand forms, PJM's Load Forecast Report (including Table
B-9b), the NYISO Gold Book, the ISO-NE CELT and MISO's LTLF — onto the single
tidy schema in ``data/dictionary/schema/load-forecast.schema.yaml`` and writes
each ISO partition through the frozen :func:`scripts.lib.clean_io.write_clean`
seam.

Per-ISO parsing lives in ``scripts/lib/load_forecast/<iso>.py`` (each registers
an :class:`~scripts.lib.load_forecast.IsoSpec`); this script is a thin dispatcher
over the registry, so adding an ISO or a vintage never touches it. The forecast
year is a *column* (every edition spans two decades), so each ISO writes one
partition ``data/clean/load-forecast/<ISO>/…parquet`` (``year=None``). Reads only
``data/raw``; idempotent.

    python scripts/data/curate_load_forecast.py [--isos ERCOT PJM ...]

Opened 2026-09-06 by lane SCN-LOAD under owner ruling S4 (card D-4), to make the
model's load-growth, data-centre and electrification constants **derived from a
tracked series** rather than hand-transcribed into a comment
(``docs/handoffs/FINDING-scn-load-2026-09-06.md``).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import load_forecast as lf
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
    """Curate and write every requested ISO's load-forecast partition.

    Args:
        raw_root: root of the raw tree (defaults to ``paths.RAW_DIR``); tests
            point it at a fixture directory.
        isos: subset of ISOs to curate (default: every registered ISO). An ISO
            whose raw inputs have not landed yields an empty frame and is
            skipped rather than raising.

    Returns:
        The list of partition paths written. Reads only ``data/raw``; safe to
        re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = lf.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = lf.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw rows under {_rel(lf.raw_dir_for(iso, raw_root))}"
            )
            continue
        source = _rel(lf.raw_dir_for(iso, raw_root))
        path = clean_io.write_clean(df, lf.DATATYPE, iso=iso, year=None, source=source)
        clean_io.validate_clean(path)
        written.append(path)
        editions = ", ".join(sorted(set(df["edition"].dropna())))
        print(
            f"wrote {path}  ({len(df)} rows, {df['year'].min()}-{df['year'].max()}, "
            f"editions: {editions})"
        )
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
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
