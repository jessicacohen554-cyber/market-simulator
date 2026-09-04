"""Curate the ``ra-import-allocations`` clean datatype.

Reconciles each ISO's published RA import capability HOLDINGS (MW held per
load-serving entity per intertie branch group per RA year) onto the tidy
schema in ``data/dictionary/schema/ra-import-allocations.schema.yaml`` and
writes per-(ISO, RA year) partitions through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/ra_import_allocations/<iso>.py`` (each
registers an ``IsoSpec``); this script is a thin dispatcher over the registry,
so adding an ISO never touches it. Reads only ``data/raw``; idempotent. Run
``python scripts/data/curate_ra_import_allocations.py [--isos CAISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import ra_import_allocations as ria
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
    """Curate and write every requested ISO's holdings partitions.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO whose
        raw workbooks have not landed yields an empty frame and is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = ria.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        df = ria.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw ra-import-allocations workbooks under {raw_root}"
            )
            continue
        for year in sorted(df["delivery_year"].unique()):
            part = df[df["delivery_year"] == year].reset_index(drop=True)
            path = clean_io.write_clean(
                part, ria.DATATYPE, iso=iso, year=int(year), source=spec.source
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(f"[ok  ] {iso} {year}: {len(part)} rows -> {_rel(path)}")
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry: curate the requested ISOs (default all registered)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--isos", nargs="*", default=None, help="ISO codes to curate")
    ap.add_argument("--raw-root", default=None, help="override the raw root (tests)")
    args = ap.parse_args(argv)
    written = curate(
        raw_root=Path(args.raw_root) if args.raw_root else None, isos=args.isos
    )
    return 0 if written else 1


if __name__ == "__main__":
    raise SystemExit(main())
