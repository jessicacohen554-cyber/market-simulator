"""IESO rows of ``seam-neighbour-price``: HOEP and hourly-mean MCP, in CAD and USD.

Raw: ``IESO_hourly_price_<year>.csv`` + ``BOC_FXUSDCAD.csv``
(``fetch_seam_neighbour_price_ieso``).  Pre-Market-Renewal IESO ran a real-time
market only, so every row is ``market = RT``.  IESO hours are EST all year:
hour-ending ``h`` begins at ``(h-1):00`` EST = UTC-5.  CAD -> USD at the Bank of
Canada daily average for the operating date, carried forward over non-business
days.  Coverage ends 2025-04-30 (Market Renewal; README DATA GAP).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from scripts.lib.seam_neighbour_price import IsoSpec, register

#: IESO raw column -> (node label, seam group)
PRICE_COLUMNS: dict[str, tuple[str, str | None]] = {
    "hoep_cad": ("HOEP", "IESO"),
    "ontario_mcp_cad": ("ONTARIO_MCP", None),
    "new_york_mcp_cad": ("NEW_YORK_INTERTIE_MCP", "IESO"),
}
EST_UTC_OFFSET_H = 5  # EST = UTC-5 (IESO market clock, no DST)


def usd_cad_daily(raw_dir: Path) -> pd.Series:
    """Bank of Canada USD/CAD by calendar day, carried over non-business days."""
    fx = pd.read_csv(raw_dir / "BOC_FXUSDCAD.csv", parse_dates=["date"])
    return fx.set_index("date")["usd_cad"].asfreq("D").ffill()


def parse(raw_dir: Path, year: int) -> pd.DataFrame:
    """One year of IESO rows in canonical (pre-finalize) shape."""
    d = pd.read_csv(raw_dir / f"IESO_hourly_price_{year}.csv")
    day = pd.to_datetime(d["date"])
    t = (
        day + pd.to_timedelta(d["hour_ending_est"] - 1 + EST_UTC_OFFSET_H, unit="h")
    ).dt.tz_localize("UTC")
    rate = usd_cad_daily(raw_dir).reindex(day).to_numpy()
    parts = []
    for col, (node, group) in PRICE_COLUMNS.items():
        parts.append(
            pd.DataFrame(
                {
                    "iso": "IESO",
                    "node": node,
                    "market": "RT",
                    "interval_start_utc": t,
                    "home_iso": "NYISO",
                    "seam_group": group,
                    "currency": "CAD",
                    "price": d[col].astype(float),
                    "price_usd": d[col].astype(float) / rate,
                }
            )
        )
    out = pd.concat(parts, ignore_index=True)
    return out[out["price"].notna()]


SPEC = register(
    IsoSpec(
        iso="IESO",
        parse=parse,
        years=(2021, 2022, 2023, 2024, 2025),
        source="IESO reports-public PriceHOEPPredispOR + RealtimeMktPriceYear; BoC Valet FXUSDCAD",
    )
)
