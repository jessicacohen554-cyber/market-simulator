"""Curate the ``transfer-constraint-binding`` clean datatype.

Parses each ISO's consolidated transfer-constraint binding record (MISO RDT
``{da,rt}_pbc`` rows; see the raw README) onto the tidy schema in
``data/dictionary/schema/transfer-constraint-binding.schema.yaml`` and writes
each (ISO, market, year) partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/transfer_constraint_binding/<iso>.py``
(each registers an :class:`~scripts.lib.transfer_constraint_binding.IsoSpec`);
this script is a thin dispatcher over the registry, so adding an ISO never
touches it. Rows are per (market, market-date year), so partitions carry both
``year`` and ``market``. Reads only ``data/raw``; idempotent. Run
``python scripts/data/curate_transfer_constraint_binding.py [--isos MISO]
[--years 2023 2024 2025]``.

This datatype is a backcast VALIDATION series (model-vs-measured binding
anchors), never an LP input — when a constraint binds is a dispatch outcome
(CLAUDE.md rule 13).
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import transfer_constraint_binding as tcb
from scripts.lib.clean_io import paths

# Market-date years curated by default — the calibration train window
# (CLAUDE.md rule 22; the fetch script enforces the same boundary).
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)


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
    """Curate and write every requested (ISO, market, year) partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.
    isos:
        Subset of ISOs (default: every registered ISO).
    years:
        Market-date years (default: :data:`DEFAULT_YEARS`).

    Returns the list of paths written. A (market, year) whose raw file has
    not landed yields an empty frame and is skipped. Reads only ``data/raw``;
    safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = tcb.load_specs()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)
    years = list(years) if years is not None else list(DEFAULT_YEARS)

    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        raw_dir = raw_root / tcb.DATATYPE / spec.raw_subdir
        for year in years:
            for market in tcb.MARKETS:
                df = spec.parse(raw_dir, market, year)
                if df.empty:
                    continue
                path = clean_io.write_clean(
                    df,
                    tcb.DATATYPE,
                    iso=iso,
                    year=year,
                    market=market,
                    source=_rel(raw_dir / f"{iso.lower()}_pbc_{market}_{year}.csv.gz"),
                )
                clean_io.validate_clean(path)
                written.append(path)
                print(f"{iso} {market} {year}: {len(df)} rows -> {_rel(path)}")
    return written


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="+", default=None, help="subset of ISOs")
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help=f"market-date years (default {DEFAULT_YEARS})",
    )
    ap.add_argument(
        "--raw-root", type=Path, default=None, help="override the raw tree root"
    )
    args = ap.parse_args()
    written = curate(raw_root=args.raw_root, isos=args.isos, years=args.years)
    if not written:
        raise SystemExit("nothing curated — no raw files found")


if __name__ == "__main__":
    main()
