"""CAISO storage-soc-bounds spec: OASIS ``PUB_RTM_GRP`` end-of-hour SOC bid bounds.

Source: the committed compact extract ``data/raw/caiso-rtm-eoh-soc/``
(``caiso_rtm_eoh_soc_<year>.parquet`` + ``caiso_rtm_storage_universe_<year>.parquet``),
written by ``scripts/data/extract_caiso_rtm_eoh_soc.py`` from the gitignored
OASIS RTM public-bid zips. The EOH bound row is joined to the same trade
date's storage-universe row for the resource's energy-bid MW range.

Clock: ``interval_start_utc`` is the published GMT bid-interval start;
``interval_start_local`` its Pacific prevailing wall clock. Rows are
partitioned by Pacific TRADE-DATE year, so a year file is complete.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, register

#: Raw drop location under the shared raw root (immutable, never edited).
RAW_SUBDIR = Path("caiso-rtm-eoh-soc")

_TZ = "America/Los_Angeles"


def years(raw_root: Path) -> list[int]:
    """Trade-date years with a committed EOH extract."""
    return sorted(
        int(p.stem.rsplit("_", 1)[1])
        for p in (raw_root / RAW_SUBDIR).glob("caiso_rtm_eoh_soc_*.parquet")
    )


def parse(raw_root: Path, year: int) -> pd.DataFrame:
    """Return the canonical tidy frame for one trade-date year (empty if absent)."""
    d = raw_root / RAW_SUBDIR
    eoh_path = d / f"caiso_rtm_eoh_soc_{year}.parquet"
    uni_path = d / f"caiso_rtm_storage_universe_{year}.parquet"
    if not eoh_path.exists():
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    eoh = pd.read_parquet(eoh_path)
    uni = pd.read_parquet(uni_path)[
        ["trade_date", "resourcebid_seq", "en_min_mw", "en_max_mw", "is_storage_s1"]
    ]
    df = eoh.merge(
        uni, on=["trade_date", "resourcebid_seq"], how="left", validate="m:1"
    )
    if df["is_storage_s1"].isna().any():
        raise ValueError(f"{eoh_path.name}: EOH rows without a universe row")
    utc = pd.to_datetime(df["interval_start_utc"], utc=True)
    out = pd.DataFrame(
        {
            "interval_start_utc": utc,
            "interval_start_local": utc.dt.tz_convert(_TZ).dt.tz_localize(None),
            "iso": "CAISO",
            "market": "RTM",
            "resource_id": df["resourcebid_seq"].astype("int64").astype(str),
            "sc_id": df["sc_seq"].astype("int64").astype(str),
            "min_eoh_soc_mwh": df["min_eoh_soc_mwh"].astype("float64"),
            "max_eoh_soc_mwh": df["max_eoh_soc_mwh"].astype("float64"),
            "en_min_mw": df["en_min_mw"].astype("float64"),
            "en_max_mw": df["en_max_mw"].astype("float64"),
            "is_storage_s1": df["is_storage_s1"].astype(bool),
        }
    )
    return out.sort_values(["resource_id", "interval_start_utc"]).reset_index(drop=True)


register(
    IsoSpec(
        iso="CAISO",
        parse=parse,
        years=years,
        source=(
            "CAISO OASIS PUB_RTM_GRP MINEOHSTATEOFCHARGE/MAXEOHSTATEOFCHARGE via "
            "data/raw/caiso-rtm-eoh-soc (scripts/data/extract_caiso_rtm_eoh_soc.py); "
            "report-only diagnostic, never a solve input (rule 13)"
        ),
    )
)
