"""caiso-217 — the SPLIT WITNESS: the caiso-215 zonal decomposition re-run
on the crosswalk solve bundle.

Pre-registered by the caiso-216 packet's §G gate table ("split witness:
re-run ``_caiso215_c3a_zonal_decomp.py``: model NP15−SP15 > $15 hours 0 →
reported; the per-zone C3a table re-printed"). Runs the committed caiso-215
instrument unchanged, pointed at the caiso-217 bundle
(``results/calibration/caiso217_crosswalk``), writing to a caiso-217 output
so the committed caiso-215 record (the keeper's own decomposition its FINDING
quotes) is never overwritten.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso217_zonal_decomp.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _caiso202_c3a_decomp as c202  # noqa: E402  (committed instrument)
import _caiso215_c3a_zonal_decomp as c215  # noqa: E402  (committed instrument)

BUNDLE = REPO / "results/calibration/caiso217_crosswalk"

c202.BUNDLE = BUNDLE
c215.OUT_JSON = REPO / "results/calibration/_caiso217_zonal_decomp.json"


def main() -> None:
    if not (BUNDLE / "hourly").exists():
        raise SystemExit(f"{BUNDLE}/hourly absent — solve the bundle first")
    c215.main()


if __name__ == "__main__":
    main()
