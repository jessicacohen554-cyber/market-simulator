"""Derive the measured CAISO per-plant CHP behind-the-meter electric share.

The identification (closeout-CAISO-w6, rule 13 [R-MEASURED] / rule 14
[R-ACCURATE]): a non-utility plant files its own annual electricity balance on
EIA-923 Schedules 6/7 (``data/raw/eia-923-disposition/``,
:mod:`scripts.data.fetch_eia923_disposition`). Its wholesale (grid)
dispositions are sales for resale, tolling agreements and outgoing
electricity; everything else it generates net of station use stays with the
plant or its host:

    grid_share = (sales for resale + tolling + outgoing) / (gross - station use)
    btm_pct    = 100 x clip(1 - grid_share, 0, 1)

Retail sales count as host supply, not grid delivery: a non-utility cogen's
retail customer is its co-located host (Watson 50216 -> the Carson refinery,
Los Medanos 55217 -> the Pittsburg steel works), served on the plant side of
the ISO meter. This is the conservative reading (it gives the larger BTM
share, the smaller move from the sector default).

This is the CAISO analogue of the nyiso-147 meter pair
(``derive_nyiso_chp_btm_share.py``): the filing regenerates every year and
responds to changed host arrangements, and it replaces
``constants.CHP_BTM_PCT_BY_SECTOR`` defaults whose own comment declares them
residual-identified. Pooled CY2022-2024 (the NYISO window): numerator and
denominator are summed over the years the plant filed, so a thin year cannot
skew the share. Scope: plants whose EIA-860 balancing authority is CISO. A
plant absent from Schedules 6/7 (utility-owned) gets no row and keeps the
default; absence is weaker evidence than a filing.

Output: ``data/raw/_processed-legacy/chp_btm_share_measured_CAISO.csv``,
consumed by the fleet capacity carve and the BTM add-back under
``ScenarioConfig.caiso_chp_btm_measured`` (default off; CAISO-only, rule 25)
and by the benchmark subtrahend whenever it exists (nyiso-149).

Rule 23 [R-FROZEN-DERIVE]: re-run only when a new EIA-923 Schedules 6/7
vintage lands — never against a residual.

Usage:
    PYTHONPATH=.:src python scripts/data/derive_caiso_chp_btm_share.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import (  # noqa: E402
    EIA_860_DIR,
    EIA_923_DISPOSITION_PATH,
    PROCESSED_DIR,
)

OUT = PROCESSED_DIR / "chp_btm_share_measured_CAISO.csv"
POOL_YEARS: tuple[int, ...] = (2022, 2023, 2024)
SOURCE = (
    "EIA-923 Schedules 6/7 non-utility source & disposition "
    "(eia923_disposition_2019_2025.csv), CY2022-2024 pooled; grid = sales for "
    "resale + tolling + outgoing; derive_caiso_chp_btm_share.py "
    "(closeout-CAISO-w6)"
)


def ciso_plants() -> set[int]:
    """Return the EIA plant codes whose EIA-860 balancing authority is CISO."""
    plant = pd.read_parquet(EIA_860_DIR / "eia860_plant.parquet")
    ba = plant["Balancing Authority Code"].astype(str).str.upper()
    return set(plant.loc[ba == "CISO", "Plant Code"].astype(int))


def derive(disposition: pd.DataFrame, plants: set[int]) -> pd.DataFrame:
    """Return the per-plant pooled BTM share table for ``plants``."""
    d = disposition[
        disposition["plant_id"].isin(plants) & disposition["year"].isin(POOL_YEARS)
    ].copy()
    d["net_mwh"] = d["gross_mwh"] - d["station_use_mwh"]
    d["grid_mwh"] = d["sales_for_resale_mwh"] + d["tolling_mwh"] + d["outgoing_mwh"]
    g = d.groupby("plant_id").agg(
        plant_name=("plant_name", "last"),
        years_pooled=("year", lambda y: "-".join(str(v) for v in sorted(set(y)))),
        net_gwh_pooled=("net_mwh", lambda v: v.sum() / 1e3),
        grid_gwh_pooled=("grid_mwh", lambda v: v.sum() / 1e3),
        retail_gwh_pooled=("retail_sales_mwh", lambda v: v.sum() / 1e3),
    )
    g = g[g["net_gwh_pooled"] > 0.0]
    g["grid_share"] = g["grid_gwh_pooled"] / g["net_gwh_pooled"]
    g["btm_pct"] = (100.0 * (1.0 - g["grid_share"])).clip(0.0, 100.0)
    g["source"] = SOURCE
    out = g.reset_index().rename(columns={"plant_id": "plant_code"})
    for col in ("net_gwh_pooled", "grid_gwh_pooled", "retail_gwh_pooled"):
        out[col] = out[col].round(1)
    out["grid_share"] = out["grid_share"].round(4)
    out["btm_pct"] = out["btm_pct"].round(2)
    return out.sort_values("plant_code").reset_index(drop=True)


def main() -> None:
    """Write the CAISO measured CHP BTM share artifact."""
    out = derive(pd.read_csv(EIA_923_DISPOSITION_PATH), ciso_plants())
    out.to_csv(OUT, index=False)
    print(f"wrote {OUT} ({len(out)} plants)")


if __name__ == "__main__":
    main()
