"""CAISO parser for the ``dam-public-bids`` datatype.

Parses one OASIS ``PUB_DAM_GRP`` daily zip (CSV result format, fetched by
``scripts/fetch_caiso_public_bids.py``) into the canonical tidy frame.

Raw row shapes (see the schema header): curve rows carry the operating hour
in ``SCH_BID_TIMEINTERVALSTART_GMT`` and one (MW, price) breakpoint; self-
schedule rows carry the hour in ``TIMEINTERVALSTART_GMT`` and ``SELFSCHEDMW``
with no curve. Rows with neither a breakpoint nor a self-schedule quantity
(none observed) are dropped.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config import paths

from . import CANONICAL_COLUMNS, IsoSpec, register

#: Columns read from the raw daily CSV (the rest are redundant renderings).
_RAW_COLS = [
    "STARTDATE",
    "MARKET_RUN_ID",
    "RESOURCE_TYPE",
    "SCHEDULINGCOORDINATOR_SEQ",
    "RESOURCEBID_SEQ",
    "TIMEINTERVALSTART_GMT",
    "MARKETPRODUCTTYPE",
    "SELFSCHEDMW",
    "SCH_BID_TIMEINTERVALSTART_GMT",
    "SCH_BID_XAXISDATA",
    "SCH_BID_Y1AXISDATA",
    "SCH_BID_CURVETYPE",
]


def parse_day(path: Path) -> pd.DataFrame:
    """Parse one daily PUB_BID_DAM zip (or bare CSV) to the canonical frame."""
    df = pd.read_csv(path, usecols=_RAW_COLS, low_memory=False)

    is_segment = df["SCH_BID_XAXISDATA"].notna()
    is_selfsched = ~is_segment & df["SELFSCHEDMW"].notna()
    df = df[is_segment | is_selfsched].copy()
    is_segment = df["SCH_BID_XAXISDATA"].notna()

    hour = np.where(
        is_segment,
        df["SCH_BID_TIMEINTERVALSTART_GMT"],
        df["TIMEINTERVALSTART_GMT"],
    )
    out = pd.DataFrame(
        {
            "iso": "CAISO",
            "trade_date": pd.to_datetime(df["STARTDATE"]).dt.normalize(),
            "interval_start_utc": pd.to_datetime(hour, utc=True),
            "resource_type": df["RESOURCE_TYPE"].astype("string"),
            "sc_seq": df["SCHEDULINGCOORDINATOR_SEQ"].astype("int64"),
            "resource_seq": df["RESOURCEBID_SEQ"].astype("int64"),
            "product": df["MARKETPRODUCTTYPE"].astype("string"),
            "row_kind": np.where(is_segment, "segment", "self_sched"),
            "self_sched_mw": df["SELFSCHEDMW"].where(~is_segment).astype("float64"),
            "segment_mw": df["SCH_BID_XAXISDATA"].astype("float64"),
            "segment_price_usd_per_mwh": df["SCH_BID_Y1AXISDATA"].astype("float64"),
            "curve_type": df["SCH_BID_CURVETYPE"].astype("string"),
        }
    )

    # step_idx: ascending segment_mw within each curve (stable for ties and
    # for self-schedule rows, which sort on NaN and keep file order).
    out = out.sort_values(
        ["resource_seq", "product", "interval_start_utc", "row_kind", "segment_mw"],
        kind="mergesort",
    )
    out["step_idx"] = (
        out.groupby(
            ["resource_seq", "product", "interval_start_utc", "row_kind"],
            sort=False,
        ).cumcount()
        + 1
    )
    return out[list(CANONICAL_COLUMNS)].reset_index(drop=True)


register(
    IsoSpec(
        iso="CAISO",
        market="DAM",
        raw_dir=paths.CAISO_PUBLIC_BIDS_DIR / "zips",
        file_glob="*_PUB_BID_DAM_v3_csv.zip",
        parse_day=parse_day,
    )
)
