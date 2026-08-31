#!/usr/bin/env python3
"""Curate the ``ps-water-state`` clean datatype.

Reconciles each pumped-storage plant's published hourly operations record onto
the single tidy schema in ``data/dictionary/schema/ps-water-state.schema.yaml``
and writes each ISO partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/ps_water_state/<iso>.py`` (each
registers an :class:`~scripts.lib.ps_water_state.IsoSpec` naming its
``PsSource`` snapshots); this script is a thin dispatcher over the registry, so
adding a plant or an ISO never touches it. A plant record spans its whole
published history in one file, so the year rides in ``interval_end_local`` as
a *column* and each ISO writes ONE partition
``data/clean/ps-water-state/<ISO>/ps-water-state.parquet`` (``year=None``).

Reads only ``data/raw`` (the immutable snapshot retrieved by
``scripts/data/fetch_helms_ps_water_state.py``); needs no network; idempotent.

Usage:
    python scripts/data/curate_ps_water_state.py [--isos CAISO ...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import ps_water_state as ps
from scripts.lib.clean_io import paths

#: Retrieval manifest written beside the snapshots by the fetch script.
SNAPSHOT_MANIFEST = "_snapshot.json"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _snapshot_provenance(raw_dir: Path) -> dict[str, object]:
    """Retrieval metadata for the ISO's snapshots, for the parquet footer.

    Reads the fetch script's ``_snapshot.json`` so a clean file records the
    exact endpoint, request, retrieval timestamp and SHA-256 of every document
    behind it. Returns an empty dict when the manifest is absent (a hand-placed
    snapshot), which is not an error — the per-row ``source_doc`` still names
    the file.
    """
    manifest = raw_dir / SNAPSHOT_MANIFEST
    if not manifest.is_file():
        return {}
    try:
        return {"snapshots": json.loads(manifest.read_text())}
    except json.JSONDecodeError:
        return {}


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Curate and write every requested ISO's ps-water-state partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO whose
        snapshots have not landed yet yields an empty frame and is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = ps.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        raw_dir = ps.raw_dir_for(iso, raw_root)
        df = ps.parse_iso(iso, raw_root)
        if df.empty:
            print(f"[skip] {iso}: no raw rows under {_rel(raw_dir)}")
            continue
        path = clean_io.write_clean(
            df,
            ps.DATATYPE,
            iso=iso,
            year=None,
            source=_rel(raw_dir),
            extra_provenance=_snapshot_provenance(raw_dir),
        )
        clean_io.validate_clean(path)
        written.append(path)
        span = (
            f"{df['interval_end_local'].min():%Y-%m-%d}"
            f"..{df['interval_end_local'].max():%Y-%m-%d}"
        )
        plants = ", ".join(
            f"{plant}={int(count)}"
            for plant, count in df["plant"].value_counts().sort_index().items()
        )
        print(f"wrote {path}  ({len(df)} rows; {span}; {plants})")
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
