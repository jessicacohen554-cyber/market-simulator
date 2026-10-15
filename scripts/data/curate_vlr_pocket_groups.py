"""Curate the ``vlr-pocket-groups`` clean datatype.

Reads each registered ISO's transcription under
``data/raw/vlr-pocket-groups/<iso>/<iso>.csv``, derives each unit's
commitment-cluster family from its EIA-860 identity, and writes one partition
per ISO through :func:`scripts.lib.clean_io.write_clean` (``year=None``: the
groups are not per-year). Reads only ``data/raw``; idempotent. Run
``python scripts/data/curate_vlr_pocket_groups.py [--isos MISO]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import vlr_pocket_groups as vpg
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
    """Curate and write every requested ISO's partition; returns the paths written."""
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = vpg.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)
    written: list[Path] = []
    for iso in wanted:
        df = vpg.parse_iso(iso, raw_root)
        if df.empty:
            print(
                f"[skip] {iso}: no raw rows under {_rel(vpg.raw_dir_for(iso, raw_root))}"
            )
            continue
        source = _rel(vpg.raw_dir_for(iso, raw_root))
        path = clean_io.write_clean(df, vpg.DATATYPE, iso=iso, year=None, source=source)
        clean_io.validate_clean(path)
        written.append(path)
        print(f"wrote {path}  ({len(df)} rows)")
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--isos", nargs="*", default=None, help="subset of ISOs")
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
