"""SPP ``flowgate-limits-at-bind`` spec (RTBM effective-limit files).

Reads the committed reduced raw form
``data/raw/spp-effective-limits/rtbm_efflimit_bound_<year>.csv.gz`` — the
BINDING and BREACHED rows of SPP's ``RTBM-EFFLIMIT-YYYYMMDD.csv`` day files,
verbatim, header once (built by ``scripts/data/fetch_spp_effective_limits.py
--reduce``) — and collapses the 5-minute intervals to UTC hour-beginning.

Timestamp basis: ``GMTIntervalEnd`` is the interval END in UTC
(``MM/DD/YYYY HH:MM:SS``), so the interval's hour is ``end - 5 min`` floored.
The header's limit columns carry a leading space (`` Source Limit``); they are
stripped on read. Exact repeated lines are counted once.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, finalize, register

# SPP RTBM interval length (minutes): the hour of an interval is its end stamp
# minus one interval, floored (SPP Markets Public Data Guide v35, RTBM files).
_INTERVAL_MINUTES = 5
_BOUND_STATES = ("BINDING", "BREACHED")


def raw_name(year: int) -> str:
    """File name of one year's reduced raw extraction."""
    return f"rtbm_efflimit_bound_{year}.csv.gz"


def parse(raw_dir: Path, year: int) -> pd.DataFrame:
    """Parse one year's reduced raw file to the canonical hourly frame."""
    path = Path(raw_dir) / raw_name(year)
    if not path.exists():
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    # SPP occasionally posts the same constraint-interval line twice (~1 % of
    # 2023's bound rows are exact repeats); a repeat is one interval, not two.
    df = df[df["State"].isin(_BOUND_STATES)].drop_duplicates().copy()
    end = pd.to_datetime(df["GMTIntervalEnd"], format="%m/%d/%Y %H:%M:%S", utc=True)
    df["hour_start_utc"] = (end - pd.Timedelta(minutes=_INTERVAL_MINUTES)).dt.floor("h")
    for src in (
        "Shadow Price",
        "Source Limit",
        "Realtime Effective Limit",
        "Initial Effective Limit",
    ):
        df[src] = pd.to_numeric(df[src].str.strip().replace("", None), errors="coerce")
    df["is_binding"] = df["State"].eq("BINDING").astype("int64")
    df["is_breached"] = df["State"].eq("BREACHED").astype("int64")
    keys = [
        "Constraint Name",
        "Monitored Facility",
        "Contingent Facility",
        "hour_start_utc",
    ]
    g = df.groupby(keys, sort=False)
    out = g.agg(
        constraint_type=("Constraint Type", "first"),
        n_binding_intervals=("is_binding", "sum"),
        n_breached_intervals=("is_breached", "sum"),
        shadow_price_mean_usd_mwh=("Shadow Price", "mean"),
        source_limit_mw=("Source Limit", "median"),
        effective_limit_mw=("Realtime Effective Limit", "median"),
        effective_limit_min_mw=("Realtime Effective Limit", "min"),
        initial_effective_limit_mw=("Initial Effective Limit", "median"),
    ).reset_index()
    out = out.rename(
        columns={
            "Constraint Name": "constraint_name",
            "Monitored Facility": "monitored_facility",
            "Contingent Facility": "contingent_facility",
        }
    )
    out["iso"] = "SPP"
    out["market"] = "rt"
    return finalize(out)


register(IsoSpec(iso="SPP", raw_subdir="spp-effective-limits", parse=parse))
