"""NYISO rows of ``seam-neighbour-price``: DA LBMP at proxy buses and zones.

Raw: ``NYISO_dam_proxy_lbmp_<year>.csv.gz`` (``fetch_seam_neighbour_price_nyiso``).
``seam_group`` names the NYISO seam a proxy bus prices (the NEXT-10 PRECOMMIT §2
table); internal load zones carry ``seam_group = <NA>``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.seam_neighbour_price import IsoSpec, local_seq_to_utc, register

#: NYISO proxy name -> seam group (PRECOMMIT-nyiso-next10 §2).
PROXY_SEAM_GROUP: dict[str, str] = {
    "O H": "IESO",
    "H Q": "HQ",
    "HQ_GEN_CEDARS_PROXY": "HQ",
    "HQ_GEN_IMPORT": "HQ",
    "PJM": "PJM_AC",
    "PJM_GEN_KEYSTONE": "PJM_AC",
    "PJM_GEN_HTP_PROXY": "PJM_HTP",
    "PJM_GEN_VFT_PROXY": "PJM_VFT",
    "PJM_GEN_NEPTUNE_PROXY": "PJM_NEPTUNE",
    "NPX": "NE_AC",
    "NPX_GEN_CSC": "NE_CSC",
    "NPX_GEN_1385_PROXY": "NE_1385",
}


def parse(raw_dir: Path, year: int) -> pd.DataFrame:
    """One year of NYISO DA LBMP rows in canonical (pre-finalize) shape."""
    d = pd.read_csv(raw_dir / f"NYISO_dam_proxy_lbmp_{year}.csv.gz")
    return pd.DataFrame(
        {
            "iso": "NYISO",
            "node": d["name"],
            "market": "DA",
            "interval_start_utc": local_seq_to_utc(
                d["date"], d["seq"], "America/New_York"
            ),
            "home_iso": "NYISO",
            "seam_group": d["name"].map(PROXY_SEAM_GROUP),
            "currency": "USD",
            "price": d["lbmp"].astype(float),
            "price_usd": d["lbmp"].astype(float),
        }
    )


SPEC = register(
    IsoSpec(
        iso="NYISO",
        parse=parse,
        years=(2021, 2022, 2023, 2024, 2025),
        source="NYISO MIS damlbmp zone + gen monthly zips",
    )
)
