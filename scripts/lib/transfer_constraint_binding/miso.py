"""MISO transfer-constraint-binding spec (RDT sub-regional PBC record).

Parses the consolidated raw files
``data/raw/transfer-constraint-binding/MISO/miso_pbc_<market>_<year>.csv.gz``
(verbatim ``{da,rt}_pbc`` market-report rows; see the raw README for
provenance and layout) into the canonical tidy frame.

Timestamp basis: the source ``MARKET_HOUR_EST`` column is MISO market time —
EST year-round, no DST (UTC-5 fixed). DA rows are hour-beginning (labels
00-23, verified across the archive); RT rows are 5-minute interval starts.

Direction is parsed from the posted constraint name's parenthetical
(``RDT_SO_MW (South_North)`` -> ``S_to_N``; ``RDT_MW_SO (North_South)`` ->
``N_to_S``); an unrecognized name fails loud rather than guessing.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, register

# MISO market time is EST year-round (no DST): fixed UTC-5.
_EST_UTC_OFFSET_HOURS = 5

_RAW_COLUMNS = [
    "MARKET_HOUR_EST",
    "CONSTRAINT_NAME",
    "PRELIMINARY_SHADOW_PRICE",
    "CURVETYPE",
    "BP1",
    "PC1",
    "BP2",
    "PC2",
    "BP3",
    "PC3",
    "BP4",
    "PC4",
    "OVERRIDE",
    "REASON",
]

_DIRECTION_BY_TAG = {"South_North": "S_to_N", "North_South": "N_to_S"}


def _direction(name: str) -> str:
    """Map a posted constraint name to the canonical direction (fail loud)."""
    for tag, direction in _DIRECTION_BY_TAG.items():
        if tag in name:
            return direction
    raise ValueError(
        f"unrecognized MISO pbc constraint name {name!r} — extend "
        "_DIRECTION_BY_TAG deliberately, never guess"
    )


def _empty() -> pd.DataFrame:
    """Canonical empty frame for an absent (market, year) raw file."""
    return pd.DataFrame(columns=list(CANONICAL_COLUMNS))


def parse(raw_dir: Path, market: str, year: int) -> pd.DataFrame:
    """Parse one (market, year) consolidated raw file to the canonical frame."""
    path = raw_dir / f"miso_pbc_{market}_{year}.csv.gz"
    if not path.exists():
        return _empty()
    df = pd.read_csv(
        path,
        names=_RAW_COLUMNS,
        header=0,
        # Source rows carry a trailing comma (15 fields for 14 columns);
        # select the 14 named fields positionally.
        usecols=range(len(_RAW_COLUMNS)),
        index_col=False,
        skipinitialspace=True,
        dtype=str,
        keep_default_na=False,
    )
    est = pd.to_datetime(df["MARKET_HOUR_EST"], format="%m/%d/%Y %H:%M:%S")
    out = pd.DataFrame(
        {
            "iso": "MISO",
            "market": market,
            "constraint": df["CONSTRAINT_NAME"].str.strip(),
            "direction": df["CONSTRAINT_NAME"].map(_direction),
            "interval_start_utc": (
                est + pd.Timedelta(hours=_EST_UTC_OFFSET_HOURS)
            ).dt.tz_localize("UTC"),
            "interval_start_est": est,
            "shadow_price_usd_mwh": pd.to_numeric(
                df["PRELIMINARY_SHADOW_PRICE"]
            ).astype("float64"),
            "curvetype": df["CURVETYPE"].str.strip().replace("", None),
            "override": df["OVERRIDE"].str.strip().isin(("1", "1.0", "true")),
            "override_reason": df["REASON"].str.strip().replace("", None),
        }
    )
    for i in (1, 2, 3, 4):
        out[f"bp{i}_pct"] = pd.to_numeric(df[f"BP{i}"].replace("", None)).astype(
            "float64"
        )
        out[f"pc{i}_usd_mwh"] = pd.to_numeric(df[f"PC{i}"].replace("", None)).astype(
            "float64"
        )
    out = out[list(CANONICAL_COLUMNS)]
    # De-duplicate on the schema key (publish-window edge files can overlap)
    # and keep a deterministic order.
    out = (
        out.drop_duplicates(
            subset=["iso", "market", "constraint", "interval_start_utc"]
        )
        .sort_values(["constraint", "interval_start_utc"])
        .reset_index(drop=True)
    )
    return out


register(IsoSpec(iso="MISO", raw_subdir="MISO", parse=parse))
