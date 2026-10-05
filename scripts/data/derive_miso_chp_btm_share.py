"""Derive the measured MISO per-plant CHP behind-the-meter electric share.

The MISO leg of the closeout-CAISO-w6 identification (rule 13 [R-MEASURED] /
rule 14 [R-ACCURATE]), with ONE definition and ONE derive function shared
across ISOs: this script calls
:func:`scripts.data.derive_caiso_chp_btm_share.derive` unchanged on the same
EIA-923 Schedules 6/7 filing (``data/raw/eia-923-disposition/``),

    grid_share = (sales for resale + tolling + outgoing) / (gross - station use)
    btm_pct    = 100 x clip(1 - grid_share, 0, 1)

pooled CY2022-2024, retail sales counted as host supply. Only the plant scope
differs: plants whose EIA-860 balancing authority is MISO. A plant absent from
Schedules 6/7 (utility-owned) gets no row and keeps the sector default.

It replaces ``constants.CHP_BTM_PCT_BY_SECTOR`` defaults the miso-192 census
found had no MISO source (the CAMPD steam-load construction covered 5.8 % of
MISO CHP MW); Schedules 6/7 covers 94 of the 110 MISO CHP plants
(closeout-MISO-w3d census).

Output: ``data/raw/_processed-legacy/chp_btm_share_measured_MISO.csv``,
consumed by the fleet capacity carve and the BTM add-back under
``ScenarioConfig.miso_chp_btm_measured`` (default off; MISO-only, rule 25)
and by the benchmark subtrahend whenever it exists (nyiso-149).

Rule 23 [R-FROZEN-DERIVE]: re-run only when a new EIA-923 Schedules 6/7
vintage lands — never against a residual.

Usage:
    PYTHONPATH=.:src python scripts/data/derive_miso_chp_btm_share.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    EIA_860_DIR,
    EIA_923_DISPOSITION_PATH,
    PROCESSED_DIR,
)
from scripts.data.derive_caiso_chp_btm_share import derive  # noqa: E402

OUT = PROCESSED_DIR / "chp_btm_share_measured_MISO.csv"
SOURCE = (
    "EIA-923 Schedules 6/7 non-utility source & disposition "
    "(eia923_disposition_2019_2025.csv), CY2022-2024 pooled; grid = sales for "
    "resale + tolling + outgoing; derive_caiso_chp_btm_share.derive via "
    "derive_miso_chp_btm_share.py (closeout-MISO-w3e)"
)


def miso_plants() -> set[int]:
    """Return the EIA plant codes whose EIA-860 balancing authority is MISO."""
    plant = pd.read_parquet(EIA_860_DIR / "eia860_plant.parquet")
    ba = plant["Balancing Authority Code"].astype(str).str.upper()
    return set(plant.loc[ba == "MISO", "Plant Code"].astype(int))


def main() -> None:
    """Write the MISO measured CHP BTM share artifact."""
    out = derive(pd.read_csv(EIA_923_DISPOSITION_PATH), miso_plants())
    out["source"] = SOURCE
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} plants)")


if __name__ == "__main__":
    main()
