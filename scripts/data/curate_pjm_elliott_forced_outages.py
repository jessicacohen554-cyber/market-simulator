"""Curate the PJM Winter Storm Elliott hourly forced-outage series into ``data/clean``.

Reads only ``data/raw/pjm-elliott-forced-outages/figure30_digitised.csv`` (the
digitised Figure 30 of PJM's Elliott Event Analysis report; README in that folder),
builds the hourly tidy frame with ``market_sim.data.pjm_elliott_outages.build_hourly_frame``
(the same builder the runtime loader falls back to, so clean and raw paths agree
byte for byte) and writes it through ``clean_io.write_clean`` as datatype
``pjm-elliott-forced-outages`` (PJM, year 2022). Idempotent.

Run: ``uv run python scripts/data/curate_pjm_elliott_forced_outages.py``
"""

from __future__ import annotations

import argparse
from pathlib import Path

from market_sim.data.pjm_elliott_outages import (
    DATATYPE,
    EVENT_YEAR,
    RAW_CSV,
    build_hourly_frame,
)
from scripts.lib import clean_io


def curate(raw_root: Path | None = None, isos: list[str] | None = None) -> list[Path]:
    """Write the clean partition and return its path (empty when PJM is not requested)."""
    if isos is not None and "PJM" not in [i.upper() for i in isos]:
        return []
    raw_csv = (
        Path(raw_root) / "pjm-elliott-forced-outages" / RAW_CSV.name
        if raw_root
        else RAW_CSV
    )
    df = build_hourly_frame(raw_csv)
    path = clean_io.write_clean(
        df, DATATYPE, iso="PJM", year=EVENT_YEAR, source=str(raw_csv.name)
    )
    clean_io.validate_clean(path)
    return [path]


def main() -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw-root", type=Path, default=None)
    ap.add_argument("--isos", nargs="*", default=None)
    args = ap.parse_args()
    for p in curate(args.raw_root, args.isos):
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
