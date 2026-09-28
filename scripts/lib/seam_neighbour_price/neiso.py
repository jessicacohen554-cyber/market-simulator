"""ISO-NE rows of ``seam-neighbour-price``: DA / RT LMP at the NY external nodes.

Raw: ``NEISO_ny_ext_node_lmp_<year>.csv`` (``fetch_seam_neighbour_price_neiso``),
one row per (day, hour position, location) with DA and RT-final side by side.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.seam_neighbour_price import IsoSpec, local_seq_to_utc, register

#: ISO-NE location id -> the NYISO seam group it prices (hub: none).
LOCATION_SEAM_GROUP: dict[str, str] = {
    "4011": "NE_AC",
    "4014": "NE_CSC",
    "4017": "NE_1385",
}


def parse(raw_dir: Path, year: int) -> pd.DataFrame:
    """One year of ISO-NE external-node rows (DA and RT) in canonical shape."""
    d = pd.read_csv(
        raw_dir / f"NEISO_ny_ext_node_lmp_{year}.csv", dtype={"location_id": str}
    )
    t = local_seq_to_utc(d["date"], d["seq"], "America/New_York")
    parts = []
    for market, col in (("DA", "da_lmp"), ("RT", "rt_lmp")):
        parts.append(
            pd.DataFrame(
                {
                    "iso": "NEISO",
                    "node": d["location"].str.strip(),
                    "market": market,
                    "interval_start_utc": t,
                    "home_iso": "NYISO",
                    "seam_group": d["location_id"].map(LOCATION_SEAM_GROUP),
                    "currency": "USD",
                    "price": d[col].astype(float),
                    "price_usd": d[col].astype(float),
                }
            )
        )
    return pd.concat(parts, ignore_index=True)


SPEC = register(
    IsoSpec(
        iso="NEISO",
        parse=parse,
        years=(2021, 2022, 2023, 2024, 2025),
        source="ISO-NE static histRpts da-lmp / rt-lmp (final) daily CSVs",
    )
)
