#!/usr/bin/env python3
"""Curate the ``gas-ofo-events`` clean datatype.

Reconciles each declaring gas utility's published Operational Flow Order event
ledger onto the single tidy schema in
``data/dictionary/schema/gas-ofo-events.schema.yaml`` and writes each ISO
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/gas_ofo_events/<iso>.py`` (each
registers an :class:`~scripts.lib.gas_ofo_events.IsoSpec` naming its
``OfoSource`` snapshots); this script is a thin dispatcher over the registry,
so adding an ISO or a second utility never touches it. Gas days span the
publisher's whole history in one ledger, so the year rides in ``gas_day`` as a
*column* and each ISO writes ONE partition
``data/clean/gas-ofo-events/<ISO>/gas-ofo-events.parquet`` (``year=None``).

Reads only ``data/raw`` (the immutable snapshots retrieved by
``scripts/data/fetch_socalgas_ofo_events.py``); needs no network; idempotent.

Usage:
    uv run python scripts/data/curate_gas_ofo_events.py [--isos CAISO ...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import gas_ofo_events as ofo
from scripts.lib.clean_io import paths

#: Retrieval manifest written beside the snapshots by the fetch script.
SNAPSHOT_MANIFEST = "_snapshot.json"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _snapshot_provenance(raw_dir: Path) -> dict[str, str]:
    """Retrieval metadata for the ISO's snapshots, for the parquet footer.

    Reads the fetch script's ``_snapshot.json`` so a clean file records the
    exact URL, retrieval timestamp and SHA-256 of every document behind it.
    Returns an empty dict when the manifest is absent (a hand-placed snapshot),
    which is not an error — the per-row ``source_doc`` still names the file.
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
    """Curate and write every requested ISO's OFO-event partition.

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
    registry = ofo.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        raw_dir = ofo.raw_dir_for(iso, raw_root)
        df = ofo.parse_iso(iso, raw_root)
        if df.empty:
            print(f"[skip] {iso}: no raw rows under {_rel(raw_dir)}")
            continue
        path = clean_io.write_clean(
            df,
            ofo.DATATYPE,
            iso=iso,
            year=None,
            source=_rel(raw_dir),
            extra_provenance=_snapshot_provenance(raw_dir),
        )
        clean_io.validate_clean(path)
        written.append(path)
        span = f"{df['gas_day'].min():%Y-%m-%d}..{df['gas_day'].max():%Y-%m-%d}"
        sides = ", ".join(
            f"{side}={int(count)}"
            for side, count in df["side"].value_counts().sort_index().items()
        )
        print(f"wrote {path}  ({len(df)} rows; {span}; {sides})")
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
