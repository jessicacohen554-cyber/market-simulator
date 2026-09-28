"""PJM rows of ``seam-neighbour-price``: DA / RT LMP at the NY interface pnodes.

Raw: ``PJM_ny_interface_lmp_<year>.csv`` (``fetch_seam_neighbour_price_pjm``;
gitignored under the DataMiner2 non-member restriction, ``docs/data-licensing.md`` §4).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.seam_neighbour_price import IsoSpec, register

#: PJM interface pnode name -> the NYISO seam group it prices.
PNODE_SEAM_GROUP: dict[str, str] = {
    "NYIS": "PJM_AC",
    "HUDSONTP": "PJM_HTP",
    "LINDENVFT": "PJM_VFT",
    "NEPTUNE": "PJM_NEPTUNE",
}


def parse(raw_dir: Path, year: int) -> pd.DataFrame:
    """One year of PJM interface rows in canonical (pre-finalize) shape."""
    d = pd.read_csv(raw_dir / f"PJM_ny_interface_lmp_{year}.csv")
    return pd.DataFrame(
        {
            "iso": "PJM",
            "node": d["pnode_name"],
            "market": d["market"],
            "interval_start_utc": pd.to_datetime(d["datetime_beginning_utc"], utc=True),
            "home_iso": "NYISO",
            "seam_group": d["pnode_name"].map(PNODE_SEAM_GROUP),
            "currency": "USD",
            "price": d["total_lmp"].astype(float),
            "price_usd": d["total_lmp"].astype(float),
        }
    )


SPEC = register(
    IsoSpec(
        iso="PJM",
        parse=parse,
        years=(2021, 2022, 2023, 2024, 2025),
        source="PJM DataMiner2 da_hrl_lmps / rt_hrl_lmps, type=INTERFACE",
    )
)
