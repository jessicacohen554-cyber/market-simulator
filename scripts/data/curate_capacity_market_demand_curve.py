"""Curate the ``capacity-market-demand-curve`` clean datatype.

Reconciles each capacity-market ISO's published demand-curve parameters (PJM
VRR points + Net CONE + IRM, NYISO ICAP demand curves, ISO-NE FCA/MRI
parameters, MISO PRA seasonal reliability-based curve + seasonal CONE, CAISO's
CPM/CPUC-RA fixed proxy) onto the single tidy schema in
``data/dictionary/schema/capacity-market-demand-curve.schema.yaml`` and writes
each ISO partition through the frozen :func:`scripts.lib.clean_io.write_clean`
seam.

Per-ISO parsing lives in ``scripts/lib/capacity_market_demand_curve/<iso>.py``
(each registers an
:class:`~scripts.lib.capacity_market_demand_curve.IsoSpec`); this script is a
thin dispatcher over the registry, so adding an ISO never touches it. The
delivery year is a *column* (each ISO spans several years in one file), so
each ISO writes one partition
``data/clean/capacity-market-demand-curve/<ISO>/…parquet`` (``year=None``).
Reads only ``data/raw``; idempotent. Run
``python scripts/data/curate_capacity_market_demand_curve.py [--isos PJM NYISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import capacity_market_demand_curve as dc
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
    """Curate and write every requested ISO's demand-curve partition.

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
    registry = dc.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = dc.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw rows under {_rel(dc.raw_dir_for(iso, raw_root))}"
            )
            continue
        source = _rel(dc.raw_dir_for(iso, raw_root))
        path = clean_io.write_clean(df, dc.DATATYPE, iso=iso, year=None, source=source)
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
