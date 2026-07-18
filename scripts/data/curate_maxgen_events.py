"""Curate the ``maxgen-events`` clean datatype.

Declared capacity-emergency event windows (the M-1 registry of the MISO
price-formation lane, ``docs/handoffs/miso-price-formation-design-2026-07.md``
§3/M-1) — one row per (ISO, declaration, region), transcribed from primary
IMM/SOM documents into ``data/raw/maxgen-events/<iso>/<iso>.csv`` and written
through the frozen :func:`scripts.lib.clean_io.write_clean` seam against
``data/dictionary/schema/maxgen-events.schema.yaml``.

Per-ISO facts live in ``scripts/lib/maxgen_events/<iso>.py`` (each registers an
:class:`~scripts.lib.maxgen_events.IsoSpec`); this script is a thin dispatcher
over the registry, so adding an ISO never touches it. Windows span multiple
years in one file, so each ISO writes one partition (``year=None``). Reads only
``data/raw``; idempotent. Run
``python scripts/data/curate_maxgen_events.py [--isos MISO ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import maxgen_events as mge
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
    """Curate and write every requested ISO's maxgen-events partition.

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
    registry = mge.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = mge.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw rows under {_rel(mge.raw_dir_for(iso, raw_root))}"
            )
            continue
        source = _rel(mge.raw_dir_for(iso, raw_root))
        path = clean_io.write_clean(df, mge.DATATYPE, iso=iso, year=None, source=source)
        clean_io.validate_clean(path)
        written.append(path)
        print(f"wrote {path}  ({len(df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: curate the requested ISOs and report paths written."""
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
