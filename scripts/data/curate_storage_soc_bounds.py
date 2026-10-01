"""Curate the ``storage-soc-bounds`` clean datatype.

Reconciles each ISO's participant-submitted storage end-of-hour SOC bid bounds
onto the tidy schema in ``data/dictionary/schema/storage-soc-bounds.schema.yaml``
and writes per-(ISO, trade-date year) partitions through the frozen
:func:`scripts.lib.clean_io.write_clean` seam. REPORT-ONLY: no model reader
exists and none may treat the bound as a solve input (rule 13).

Per-ISO parsing lives in ``scripts/lib/storage_soc_bounds/<iso>.py``; this
script is a thin dispatcher over the registry. Reads only ``data/raw``;
idempotent. Run ``python scripts/data/curate_storage_soc_bounds.py [--isos CAISO]``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.lib import clean_io  # noqa: E402
from scripts.lib import storage_soc_bounds as ssb  # noqa: E402
from scripts.lib.clean_io import paths  # noqa: E402


def curate(
    raw_root: Path | None = None, isos: Iterable[str] | None = None
) -> list[Path]:
    """Curate and write every requested ISO's storage-SOC-bound partitions.

    ``raw_root`` defaults to ``paths.RAW_DIR`` (tests point it at a fixture);
    ``isos`` defaults to every registered ISO. Returns the paths written.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = ssb.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        yrs = spec.years(raw_root)
        if not yrs:
            print(f"[skip] {iso}: no raw storage-SOC-bound files under {raw_root}")
            continue
        for year in yrs:
            part = spec.parse(raw_root, year)
            if part.empty:
                continue
            path = clean_io.write_clean(
                part, ssb.DATATYPE, iso=iso, year=int(year), source=spec.source
            )
            clean_io.validate_clean(path)
            written.append(path)
            print(f"[ok  ] {iso} {year}: {len(part)} rows -> {path}")
    return written


def main() -> None:
    """CLI entrypoint: curate the requested ISOs (default: all registered)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="+", default=None, help="ISO subset")
    args = ap.parse_args()
    curate(isos=args.isos)


if __name__ == "__main__":
    main()
