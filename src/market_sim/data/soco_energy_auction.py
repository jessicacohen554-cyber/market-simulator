"""Southern Company Energy Auction clearing prices — a REPORTED-ONLY reference series.

Southern Company runs a voluntary hour-ahead and day-ahead energy auction
(``https://www.southerngeneration.com/auctionpub/``); the committed files under
``data/raw/soco-energy-auction/`` are its published clearing prices, 2019-2025,
exactly as downloaded (``scripts/data/fetch_soco_energy_auction.py``; README there).

REPORTED-ONLY (owner ruling 2026-09-28, "Yes, reported-only"; lane soco-84): it is
shown on the SOCO status panel beside the FERC-714 system lambda and feeds no gate,
no scorer and no LP. It is a measured market *outcome* for a thin voluntary auction
that clears only in some hours, so rule 13 [R-MEASURED] forbids pinning it into a
solve, and its sparse coverage (hours with a clearing) makes it a spot check, not a
price benchmark.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from market_sim.config.paths import SOCO_ENERGY_AUCTION_DIR

#: Hour-ahead file columns (auctionpub/FileSpecification.doc; verified on every file).
HOURLY_COLUMNS: tuple[str, ...] = (
    "UTC_FLOW_HOUR",
    "CPT_FLOW_HOUR",
    "CPT_HOUR_END",
    "PRICE",
    "TLU",
)
#: Day-ahead file columns.
DAILY_COLUMNS: tuple[str, ...] = (
    "CLEARING_DATE",
    "FLOW_DATE",
    "PRODUCT",
    "HEATRATE",
    "PRICE",
    "TLU",
)


def load_soco_energy_auction_hourly(raw_dir: Path | None = None) -> pd.Series:
    """Return the hour-ahead clearing price ($/MWh) on a naive-UTC hour-beginning index.

    Only hours in which the auction cleared appear. ``UTC_FLOW_HOUR`` is the flow
    hour's beginning in UTC (``CPT_FLOW_HOUR`` is the same instant on Central
    prevailing time and ``CPT_HOUR_END`` its hour-ending label).

    Raises:
        FileNotFoundError: no hour-ahead files under ``raw_dir``.
        ValueError: a file departs from :data:`HOURLY_COLUMNS` or an hour repeats.
    """
    base = (SOCO_ENERGY_AUCTION_DIR if raw_dir is None else Path(raw_dir)) / "hourly"
    files = sorted(base.glob("*_HOURLY_CLEARING_PRICES.CSV"))
    if not files:
        raise FileNotFoundError(base)
    frames = []
    for f in files:
        d = pd.read_csv(f)
        if tuple(d.columns) != HOURLY_COLUMNS:
            raise ValueError(f"{f.name}: columns {list(d.columns)}")
        frames.append(d)
    d = pd.concat(frames, ignore_index=True)
    idx = pd.DatetimeIndex(pd.to_datetime(d["UTC_FLOW_HOUR"]), name="datetime_utc")
    if idx.has_duplicates:
        raise ValueError("duplicate UTC_FLOW_HOUR across hour-ahead files")
    return pd.Series(
        d["PRICE"].to_numpy(float), index=idx, name="price_usd_mwh"
    ).sort_index()


def load_soco_energy_auction_daily(raw_dir: Path | None = None) -> pd.DataFrame:
    """Return the day-ahead clearing records (one row per cleared product and flow date)."""
    base = (SOCO_ENERGY_AUCTION_DIR if raw_dir is None else Path(raw_dir)) / "daily"
    files = sorted(base.glob("*_DAILY_CLEARING_PRICES.CSV"))
    if not files:
        raise FileNotFoundError(base)
    frames = []
    for f in files:
        d = pd.read_csv(f)
        if tuple(d.columns) != DAILY_COLUMNS:
            raise ValueError(f"{f.name}: columns {list(d.columns)}")
        frames.append(d)
    return pd.concat(frames, ignore_index=True)
