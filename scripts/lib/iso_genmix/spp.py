"""SPP ``iso-genmix`` spec: SPP's 5-minute generation mix, aggregated hourly.

Source: SPP portal ``generation-mix-historical`` root files
``data/raw/spp-genmix/GenMix_<year>.csv`` (2019-2025; raw README). Columns:
``GMT MKT Interval`` then MW by fuel split Market / Self, then ``Load``
(STLF-sourced, not read). The 2024-02 v35 sample-folder files
(``GenMix_2024_SPP.csv``, ``GenMixYTD_SPP.csv``) are a different, gappier
publication superseded under rule 14 (README) and are NOT read.

Clock: every year's ``GMT MKT Interval`` is the UTC interval END. Measured
(UC-SPP-DATAFIX): assigning each 5-minute value to the hour containing its
interval end, the hourly wind matches EIA-930 ``NG: WND`` to a median
29-71 MW/h in 2019-2025 against >= 346 MW/h one hour either side; the
2019-2021 files simply start one interval earlier (06:00Z, the previous local
year's last interval, dropped by the year split). Market + Self are summed per
fuel; an all-blank interval (the 2025 file's empty final row) is dropped.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from . import IsoSpec, register

SPP_TZ = "America/Chicago"
SPP_AREA = "SPP"

_FILE = re.compile(r"^GenMix_(\d{4})\.csv$")
_STAMP = "GMT MKT Interval"

#: Source column -> fuel family (Market and Self both map to the family).
COLUMN_FUEL: dict[str, str] = {
    "Coal Market": "coal",
    "Coal Self": "coal",
    "Diesel Fuel Oil Market": "oil",
    "Diesel Fuel Oil Self": "oil",
    "Hydro Market": "hydro",
    "Hydro Self": "hydro",
    "Natural Gas Market": "gas",
    "Gas Self": "gas",
    "Nuclear Market": "nuclear",
    "Nuclear Self": "nuclear",
    "Solar Market": "solar",
    "Solar Self": "solar",
    "Waste Disposal Services Market": "waste",
    "Waste Disposal Services Self": "waste",
    "Wind Market": "wind",
    "Wind Self": "wind",
    "Waste Heat Market": "waste_heat",
    "Waste Heat Self": "waste_heat",
    "Other Market": "other",
    "Other Self": "other",
}


def _read_intervals(path: Path) -> pd.DataFrame:
    """5-minute rows of one GenMix file: interval-end stamp + MW by fuel family."""
    raw = pd.read_csv(path, skipinitialspace=True)
    raw.columns = [c.strip() for c in raw.columns]
    missing = [c for c in [_STAMP, *COLUMN_FUEL] if c not in raw.columns]
    if missing:
        raise ValueError(f"{path.name}: missing GenMix column(s) {missing}")
    vals = raw[list(COLUMN_FUEL)].apply(pd.to_numeric, errors="coerce")
    keep = vals.notna().any(axis=1)
    by_fuel = vals[keep].T.groupby(COLUMN_FUEL).sum(min_count=1).T
    by_fuel.insert(
        0, "end", pd.to_datetime(raw.loc[keep, _STAMP], utc=True, format="ISO8601")
    )
    return by_fuel


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """All SPP hourly generation-by-fuel rows under ``raw_dir`` as one tidy frame.

    The files are concatenated at 5-minute grain BEFORE the hourly mean, so an
    hour straddling two year files (2019-2021 start one interval early) is
    averaged over all its intervals rather than split into two partial rows.
    """
    files = sorted(p for p in raw_dir.glob("GenMix_*.csv") if _FILE.match(p.name))
    cols = ["iso", "area", "fuel", "interval_end_utc", "generation_mw", "n_intervals"]
    if not files:
        return pd.DataFrame(columns=cols)
    five = pd.concat([_read_intervals(p) for p in files], ignore_index=True)
    five = five.drop_duplicates("end", keep="first")
    five["interval_end_utc"] = five.pop("end").dt.ceil("h")
    # Keep only hours of the files' own local years (the 2019 file's first
    # interval closes the previous local year's last hour).
    years = {int(_FILE.match(p.name).group(1)) for p in files}
    start = (five["interval_end_utc"] - pd.Timedelta(hours=1)).dt.tz_convert(spec.tz)
    five = five[start.dt.year.isin(years)]
    grouped = five.groupby("interval_end_utc")
    mean = grouped.mean().reset_index()
    count = grouped.count().reset_index()
    ids = ["interval_end_utc"]
    long = mean.melt(id_vars=ids, var_name="fuel", value_name="generation_mw")
    n = count.melt(id_vars=ids, var_name="fuel", value_name="n_intervals")
    long = long.merge(n, on=["interval_end_utc", "fuel"]).dropna(
        subset=["generation_mw"]
    )
    return long.assign(iso=spec.iso, area=SPP_AREA)


SPEC = register(
    IsoSpec(
        iso="SPP",
        raw_subdir="spp-genmix",
        tz=SPP_TZ,
        parse=parse,
        description="SPP 5-minute generation mix by fuel, hourly mean",
    )
)
