"""Zonal-report library helpers (thermal classes + bin-sheet zone map).

The CLI that prints the zonal net-export / thermal-miss-by-zone report for a
calibration bundle lives in ``reldeploy_zonal_report.py (retired CLI, deleted 2026-09-05)``; this module
holds the reusable pieces (``THERMAL`` and ``_zone_map``) that the CLI and the
probes share.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# CEMS-covered thermal classes (the dispatch klass / bin-sheet Plant_Group).
THERMAL = {
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    # The four coal subclasses (COAL-SUB, 2026-09-25: no bare COAL class).
    "COAL_LIGNITE",
    "COAL_PRB",
    "COAL_BIT",
    "COAL_WC",
}


def _zone_map(bins_path: Path) -> tuple[dict[int, str], dict[int, str]]:
    """Return ``({plant_code: zone}, {plant_code: class})`` from the bin sheet."""
    df = pd.read_csv(bins_path)
    zone: dict[int, str] = {}
    klass: dict[int, str] = {}
    for r in df.itertuples(index=False):
        pc = int(r.Plant_Code)
        zone.setdefault(pc, r.ERCOT_Zone)
        klass.setdefault(pc, r.Plant_Group)
    return zone, klass
