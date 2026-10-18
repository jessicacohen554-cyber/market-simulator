"""SPP ``iso-area-load`` spec: SPP's HOURLY_LOAD monthly roll-ups.

Source: SPP portal file-browser ``hourly-load`` (raw README and SOURCES.md in
``data/raw/spp-hourly-load``). Monthly files ``HOURLY_LOAD-YYYYMM.csv`` are
WIDE: ``MarketHour`` then one MW column per legacy control area — the 17
EIA-930 SWPP sub-BA tokens. ``MarketHour`` is the UTC interval END despite its
name (README "Timezone confirmed on the files"; first January row
``01/01/YYYY 07:00:00`` = HE01 CST).

Layout read here: 2019-2024 from SPP's yearly archives
``hourly-load-<year>.zip`` (members ``<year>/HOURLY_LOAD-<year>MM.csv``; the
``DAILY_*`` members are the same data unrolled and are not read); a year with
no archive (2025) from the extracted ``HOURLY_LOAD-<year>MM.csv`` files. The
extracted 2023-2024 monthlies are byte-identical to the archive members
(README "MERGE RECONCILIATION"), so a year is read from exactly ONE of the two
shapes — never both, which would double count.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import pandas as pd

from . import IsoSpec, register

#: SPP's market clock (Central prevailing time).
SPP_TZ = "America/Chicago"

_MONTHLY = re.compile(r"HOURLY_LOAD-(\d{4})(\d{2})\.csv$")
_TS_FMTS = ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M")


def _parse_ts(values: pd.Series) -> pd.Series:
    """Parse ``MarketHour`` (UTC) with the first matching layout; raise if any fail."""
    out = pd.to_datetime(values, format=_TS_FMTS[0], errors="coerce")
    for fmt in _TS_FMTS[1:]:
        miss = out.isna()
        if miss.any():
            out[miss] = pd.to_datetime(values[miss], format=fmt, errors="coerce")
    if out.isna().any():
        bad = values[out.isna()].iloc[0]
        raise ValueError(f"spp hourly-load: unparseable MarketHour {bad!r}")
    return out.dt.tz_localize("UTC")


def _read_monthly(buf: bytes | Path) -> pd.DataFrame:
    """Tidy ``(area, interval_end_utc, load_mw)`` rows from one wide monthly file."""
    src = io.BytesIO(buf) if isinstance(buf, bytes) else buf
    wide = pd.read_csv(src, skipinitialspace=True, dtype=str)
    wide.columns = [c.strip() for c in wide.columns]
    if "MarketHour" not in wide.columns:
        raise ValueError("spp hourly-load: no MarketHour column")
    ts = _parse_ts(wide["MarketHour"].str.strip())
    long = (
        wide.drop(columns=["MarketHour"])
        .assign(interval_end_utc=ts)
        .melt(id_vars="interval_end_utc", var_name="area", value_name="load_mw")
    )
    long["load_mw"] = pd.to_numeric(long["load_mw"].str.strip(), errors="coerce")
    return long.dropna(subset=["load_mw"])


def _monthly_sources(raw_dir: Path) -> list[tuple[str, bytes | Path]]:
    """Every monthly file to read: archive members where a year zip exists, else CSVs."""
    out: list[tuple[str, bytes | Path]] = []
    zipped: set[str] = set()
    for zpath in sorted(raw_dir.glob("hourly-load-*.zip")):
        with zipfile.ZipFile(zpath) as zf:
            for name in sorted(zf.namelist()):
                m = _MONTHLY.search(name)
                if m and "DAILY" not in name:
                    out.append((name, zf.read(name)))
                    zipped.add(m.group(1))
    for path in sorted(raw_dir.glob("HOURLY_LOAD-*.csv")):
        m = _MONTHLY.search(path.name)
        if m and m.group(1) not in zipped:
            out.append((path.name, path))
    return out


def parse(raw_dir: Path, spec: IsoSpec) -> pd.DataFrame:
    """All SPP hourly area-load rows under ``raw_dir`` as one tidy frame."""
    sources = _monthly_sources(raw_dir)
    if not sources:
        return pd.DataFrame(columns=["iso", "area", "interval_end_utc", "load_mw"])
    df = pd.concat([_read_monthly(src) for _, src in sources], ignore_index=True)
    # A month file can repeat its boundary hour; the archive is one series.
    df = df.drop_duplicates(["area", "interval_end_utc"], keep="first")
    return df.assign(iso=spec.iso)


SPEC = register(
    IsoSpec(
        iso="SPP",
        raw_subdir="spp-hourly-load",
        tz=SPP_TZ,
        parse=parse,
        description="SPP HOURLY_LOAD monthly roll-ups by legacy control area",
    )
)
