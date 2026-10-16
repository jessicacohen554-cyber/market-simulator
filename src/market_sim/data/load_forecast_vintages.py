"""ISO short-term load-forecast vintages: the forecast in force at a stated lead.

Reader over the ``load-forecast-vintages`` clean datatype (lane UC-DF-AUDIT,
owner ruling UC-DESK r14, 2026-10-16;
``data/dictionary/schema/load-forecast-vintages.schema.yaml``). Each partition
holds every issued vintage of the ISO's own hourly forecast (SPP: the MTLF,
one vintage an hour, seven days forward), keyed by issue time.

The question a reliability commitment asks is "what did the ISO forecast for
operating hour *h* at the cycle *L* hours before it?". :func:`forecast_at_lead`
answers it: for each operating hour (beginning ``interval_start_utc``) it
returns the forecast from the LATEST vintage issued at or before
``interval_start_utc - L``. Nothing here is wired into a solve; the RUC build
lane consumes it (DESIGN-ucmilp-ruc-stage-2026-10-16 §2.2).
"""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

#: The clean datatype read here.
DATATYPE = "load-forecast-vintages"

_HOUR = pd.Timedelta(hours=1)


def available_years(iso: str) -> list[int]:
    """Issue years with a clean partition on disk for ``iso``."""
    from scripts.lib.clean_io import paths

    base = paths.CLEAN_DIR / DATATYPE / str(iso).upper()
    stem = f"{DATATYPE}_"
    return sorted(
        int(p.stem[len(stem) :]) for p in base.glob(f"{stem}*.parquet") if p.is_file()
    )


def load_vintages(
    iso: str, years: Iterable[int], area: str | None = None, *, validate: bool = False
) -> pd.DataFrame:
    """Concatenate the ``iso`` partitions for the issue ``years`` present on disk.

    ``area`` filters the source area label (SPP: ``"SPP"`` / ``"SWPW"``).
    Raises ``FileNotFoundError`` when none of the years has a partition.
    """
    from scripts.lib.clean_io import clean_exists, read_clean

    iso = str(iso).upper()
    frames = [
        read_clean(DATATYPE, iso=iso, year=int(y), validate=validate)
        for y in sorted(set(int(y) for y in years))
        if clean_exists(DATATYPE, iso=iso, year=int(y))
    ]
    if not frames:
        raise FileNotFoundError(
            f"no {DATATYPE} partition for {iso} issue years {sorted(years)}: run "
            "scripts/regenerate_clean.py load-forecast-vintages"
        )
    df = pd.concat(frames, ignore_index=True)
    if area is not None:
        df = df[df["area"] == area]
    return df.reset_index(drop=True)


def select_at_lead(vintages: pd.DataFrame, lead_hours: int) -> pd.DataFrame:
    """Per operating hour, the latest vintage issued ``lead_hours`` before it begins.

    ``vintages`` is a ``load-forecast-vintages`` frame for one area. A vintage
    qualifies for the hour ending ``interval_end_utc`` iff
    ``issue_time_utc <= interval_end_utc - 1 h - lead_hours`` (the hour's
    start less the lead). Returns one row per covered hour, indexed by
    ``interval_end_utc``, with ``interval_start_utc``, ``forecast_mw``, the
    chosen ``issue_time_utc`` and its realised ``lead_hours`` (from the hour's
    start). Hours no vintage covers at that lead are absent.
    """
    if int(lead_hours) < 0:
        raise ValueError(f"lead_hours must be >= 0, got {lead_hours}")
    if vintages["area"].nunique() > 1:
        raise ValueError(
            "select_at_lead needs one area; filter with load_vintages(area=)"
        )
    start = vintages["interval_end_utc"] - _HOUR
    ok = vintages["issue_time_utc"] <= start - pd.Timedelta(hours=int(lead_hours))
    pick = (
        vintages.loc[ok, ["interval_end_utc", "issue_time_utc", "forecast_mw"]]
        .sort_values(["interval_end_utc", "issue_time_utc"])
        .drop_duplicates("interval_end_utc", keep="last")
        .set_index("interval_end_utc")
    )
    pick.insert(0, "interval_start_utc", pick.index - _HOUR)
    pick["lead_hours"] = (
        (pick["interval_start_utc"] - pick["issue_time_utc"]) // _HOUR
    ).astype("int64")
    return pick


def forecast_at_lead(
    iso: str, year: int, lead_hours: int, area: str | None = None
) -> pd.DataFrame:
    """:func:`select_at_lead` for the operating hours ending in UTC calendar ``year``.

    Reads issue years ``year - 1`` .. ``year`` (a vintage reaches seven days
    forward, so late-December vintages cover early-January hours). ``area``
    defaults to the ISO's only area; it is required where the partition
    carries several (SPP from 2026).
    """
    df = load_vintages(iso, (int(year) - 1, int(year)), area=area)
    if area is None and df["area"].nunique() > 1:
        raise ValueError(
            f"{iso} {year}: vintages carry areas {sorted(df['area'].unique())}; pass area="
        )
    out = select_at_lead(df, lead_hours)
    return out[out.index.year == int(year)]
