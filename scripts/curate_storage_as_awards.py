"""Curate the ``storage-as-awards`` clean datatype.

Reconciles each ISO's published storage ancillary-service AWARD series (the MW
of AS held by the battery/hybrid storage fleet) onto the tidy schema in
``data/dictionary/schema/storage-as-awards.schema.yaml`` and writes per-(ISO,
year) partitions through the frozen :func:`scripts.lib.clean_io.write_clean`
seam.

Per-ISO parsing lives in ``scripts/lib/storage_as_awards/<iso>.py`` (each
registers an :class:`~scripts.lib.storage_as_awards.IsoSpec`); this script is a
thin dispatcher over the registry, so adding an ISO never touches it. Rows are
per-hour, so partitions are per year (``write_clean(..., year=…)``). Reads only
``data/raw``; idempotent. Run
``python scripts/curate_storage_as_awards.py [--isos CAISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import storage_as_awards as saw
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
    """Curate and write every requested ISO's storage-AS-award partitions.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO whose
        raw files have not landed yields an empty frame and is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = saw.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        df = spec.parse(raw_root)
        if df.empty:
            print(f"[skip] {iso}: no raw storage-AS-award files under {raw_root}")
            continue
        # Partition by LOCAL year: trade dates are local days, so the local
        # year is complete per partition (a UTC-year split would strand the
        # last local evening's hours in the next year's file).
        local_year = df["interval_start_local"].dt.year
        for year in sorted(local_year.unique()):
            part = df[local_year == year].reset_index(drop=True)
            path = clean_io.write_clean(
                part,
                saw.DATATYPE,
                iso=iso,
                year=int(year),
                source=spec.source,
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(f"[ok  ] {iso} {year}: {len(part)} rows -> {_rel(path)}")
    return written


def main() -> None:
    """CLI entrypoint: curate the requested ISOs (default: all registered)."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--isos", nargs="+", default=None, help="ISO subset")
    args = ap.parse_args()
    curate(isos=args.isos)


if __name__ == "__main__":
    main()
