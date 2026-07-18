"""Curate the ``ramp-capability`` clean datatype.

Reconciles the two measured public ramp-capability sources — the EIA-860
``Time from Cold Shutdown to Full Load`` fast-start category (Schedule 3.1)
and the CAMPD CEMS maximum observed 1-hour plant gross-load up-ramp — onto
the single tidy per-plant schema in
``data/dictionary/schema/ramp-capability.schema.yaml`` and writes each ISO
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO scoping lives in ``scripts/lib/ramp_capability/<iso>.py`` (each
registers an :class:`~scripts.lib.ramp_capability.IsoSpec`); this script is a
thin dispatcher over the registry, so adding an ISO never touches it. The
vintage span (2023-2025, holdouts excluded per CLAUDE.md rule 22) is a
*column*, so each ISO writes one partition
``data/clean/ramp-capability/<ISO>/…parquet`` (``year=None``). Reads only
``data/raw``; idempotent. Run
``python scripts/data/curate_ramp_capability.py [--isos PJM MISO]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import ramp_capability as rc
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
    """Curate and write every requested ISO's ramp-capability partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO with
        no raw coverage yet yields an empty frame and is skipped.

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = rc.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        df = rc.derive_iso(iso, raw_root)
        if df.empty:
            eia_dir, campd_dir = rc.raw_dirs_for(raw_root)
            print(
                f"[skip] {iso}: no raw rows under {_rel(eia_dir)} / {_rel(campd_dir)}"
            )
            continue
        eia_dir, campd_dir = rc.raw_dirs_for(raw_root)
        source = f"{_rel(eia_dir)}; {_rel(campd_dir)}"
        path = clean_io.write_clean(df, rc.DATATYPE, iso=iso, year=None, source=source)
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
