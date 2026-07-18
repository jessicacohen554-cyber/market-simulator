"""Curate the ``capacity-market-auction-price`` clean datatype.

Reconciles each capacity-market ISO's published auction/spot clearing-price
history (PJM BRA, NYISO spot, ISO-NE FCA, MISO PRA seasonal) onto the single
tidy schema in
``data/dictionary/schema/capacity-market-auction-price.schema.yaml`` and
writes each ISO partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam. This is a VALIDATION
OBSERVABLE (CR-2 / T3.1) — never a fit target (CLAUDE.md rules 1/13).

Per-ISO parsing lives in ``scripts/lib/capacity_market_auction_price/<iso>.py``
(each registers an
:class:`~scripts.lib.capacity_market_auction_price.IsoSpec`); this script is a
thin dispatcher over the registry. Delivery year is a *column*, so each ISO
writes one partition
``data/clean/capacity-market-auction-price/<ISO>/…parquet`` (``year=None``).
:func:`~scripts.lib.capacity_market_auction_price.validate_tidy` enforces the
delivery-year <= 2026/27 quarantine cutoff. Reads only ``data/raw``;
idempotent. Run
``python scripts/data/curate_capacity_market_auction_price.py [--isos PJM NYISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import capacity_market_auction_price as ap
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
    """Curate and write every requested ISO's auction-price partition.

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
    registry = ap.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = ap.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw rows under {_rel(ap.raw_dir_for(iso, raw_root))}"
            )
            continue
        source = _rel(ap.raw_dir_for(iso, raw_root))
        path = clean_io.write_clean(df, ap.DATATYPE, iso=iso, year=None, source=source)
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
