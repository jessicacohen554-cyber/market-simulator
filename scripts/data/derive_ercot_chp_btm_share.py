"""Derive the measured ERCOT per-plant CHP behind-the-meter electric share.

The ERCOT leg of the closeout-CAISO-w6 identification (rule 13 [R-MEASURED] /
rule 14 [R-ACCURATE]), with ONE definition and ONE derive function shared
across ISOs: this script calls
:func:`scripts.data.derive_caiso_chp_btm_share.derive` unchanged on the same
EIA-923 Schedules 6/7 filing (``data/raw/eia-923-disposition/``),

    grid_share = (sales for resale + tolling + outgoing) / (gross - station use)
    btm_pct    = 100 x clip(1 - grid_share, 0, 1)

pooled CY2022-2024, retail sales counted as host supply. Only the plant scope
differs: plants whose EIA-860 balancing authority is ERCO. A plant absent from
Schedules 6/7 (utility-owned) gets no row and keeps the sector default.

It replaces ``constants.CHP_BTM_PCT_BY_SECTOR`` defaults (merchant 35 %,
self-described residual-identified) that the closeout-chp-transfer census
(docs/records/governance/closeout-2026-10/FINDING-closeout-chp-transfer-2026-10-05.md)
found overstate host self-use at the large Houston merchant cogens by
+3.9 to +5.1 TWh/yr (Deer Park 55464 35 % -> 2.9 %, Pasadena 55047 35 % -> 0 %).

Output: ``data/raw/_processed-legacy/chp_btm_share_measured_ERCOT.csv``,
consumed by the fleet capacity carve and the BTM add-back under
``ScenarioConfig.ercot_chp_btm_measured`` (default off; ERCOT-only, rule 25)
and by the benchmark subtrahend whenever it exists (nyiso-149).

Rule 23 [R-FROZEN-DERIVE]: re-run only when a new EIA-923 Schedules 6/7
vintage lands — never against a residual.

Usage:
    PYTHONPATH=.:src python scripts/data/derive_ercot_chp_btm_share.py
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

OUT = PROCESSED_DIR / "chp_btm_share_measured_ERCOT.csv"
SOURCE = (
    "EIA-923 Schedules 6/7 non-utility source & disposition "
    "(eia923_disposition_2019_2025.csv), CY2022-2024 pooled; grid = sales for "
    "resale + tolling + outgoing; derive_caiso_chp_btm_share.derive via "
    "derive_ercot_chp_btm_share.py (closeout-ERCOT-w6)"
)


def ercot_plants() -> set[int]:
    """Return the EIA plant codes whose EIA-860 balancing authority is ERCO."""
    plant = pd.read_parquet(EIA_860_DIR / "eia860_plant.parquet")
    ba = plant["Balancing Authority Code"].astype(str).str.upper()
    return set(plant.loc[ba == "ERCO", "Plant Code"].astype(int))


def main() -> None:
    """Write the ERCOT measured CHP BTM share artifact."""
    out = derive(pd.read_csv(EIA_923_DISPOSITION_PATH), ercot_plants())
    out["source"] = SOURCE
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} plants)")


if __name__ == "__main__":
    main()
