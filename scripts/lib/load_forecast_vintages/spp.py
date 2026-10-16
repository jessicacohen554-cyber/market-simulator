"""SPP ``load-forecast-vintages`` spec: the Mid-Term Load Forecast (MTLF) archive.

Source: SPP portal file-browser ``mtlf-vs-actual`` (anonymous HTTPS, no login),
one CSV per hour named ``OP-MTLF-YYYYMMDDHH00.csv``. Closed years are archived
as one zip ``/<year>/<year>.zip`` holding ``<year>/MM/DD/OP-MTLF-*.csv``; the
current year is live as ``/<year>/MM/DD/`` folders. Raw layout here:
``data/raw/load-forecast-vintages/spp/<year>.zip`` with that same member
layout (see the directory README for the 2025 repack).

Each file: ``Interval, GMTIntervalEnd, MTLF, Averaged Actual[, BAA]``. The
``Interval`` column is the local (Central prevailing) interval end and
``GMTIntervalEnd`` the same instant in UTC; rows run from the stamp + 168 h back
to the stamp - 24 h, the past rows carrying SPP's averaged actual (the
in-progress hour a partial average). The file-name stamp is the local issue
hour; the portal posts the file at about HH:05.

Issue time (UTC) is ``max(GMTIntervalEnd) - 168 h``, cross-checked against the
stamp localized to ``America/Chicago``; a disagreement raises unless it falls
within :data:`DST_TOLERANCE` of a DST transition, where SPP's stamps do not
follow the tz database (the repeated fall-back hour is ``...0200d.csv``). The ``BAA`` column appears with the April 2026 RTO West
expansion (SPP, SWPW); earlier files are the SPP balancing authority alone.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from . import IsoSpec, register

#: The forward horizon of every MTLF vintage (SPP: "rolling hourly basis for
#: the next seven days", Integrated Marketplace Protocols Rev 119 glossary).
MTLF_HORIZON_HOURS = 168

#: SPP's market clock (Central prevailing time).
SPP_TZ = "America/Chicago"

#: Window either side of a DST transition inside which the file-name stamp
#: may disagree with the horizon-derived issue time (the transition hour's
#: own relabelling, observed in the 2019-2025 archive).
DST_TOLERANCE = pd.Timedelta(hours=2)

#: Area label for files that carry no BAA column (the SPP BA, 2013-2025).
DEFAULT_AREA = "SPP"

#: File name; SPP labels the repeated fall-back hour's vintage ``...0200d.csv``.
_STAMP = re.compile(r"OP-MTLF-(\d{12}d?)\.csv$")
#: Timestamp layouts seen in the archive (some 2020 files drop the seconds).
_TS_FMTS = ("%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M")


def _parse_ts(values: pd.Series) -> pd.Series:
    """Parse ``values`` with the first matching archive layout; raise if any fail."""
    out = pd.to_datetime(values, format=_TS_FMTS[0], errors="coerce")
    for fmt in _TS_FMTS[1:]:
        miss = out.isna()
        if not miss.any():
            break
        out[miss] = pd.to_datetime(values[miss], format=fmt, errors="coerce")
    if out.isna().any():
        raise ValueError(
            f"SPP MTLF: unparsed timestamps {values[out.isna()].iloc[:3].tolist()}"
        )
    return out


def _utc_offset(ts: pd.Series) -> pd.Series:
    """Local UTC offset (hours) of each UTC instant on the SPP clock."""
    loc = ts.dt.tz_convert(SPP_TZ)
    return (loc.dt.tz_localize(None) - ts.dt.tz_localize(None)) // pd.Timedelta(hours=1)


def _member_rows(name: str, raw: bytes) -> list[bytes]:
    """The member's data lines, each prefixed with its stamp and padded to 5 fields."""
    stamp = _STAMP.search(name).group(1).encode()
    lines = raw.replace(b"\r", b"").split(b"\n")
    out = []
    for line in lines[1:]:
        if not line.strip():
            continue
        if line.count(b",") == 3:
            line = line + b"," + DEFAULT_AREA.encode()
        out.append(stamp + b"," + line)
    return out


def parse_members(members: dict[str, bytes]) -> pd.DataFrame:
    """Tidy rows from ``{member name: csv bytes}`` of ``OP-MTLF-*.csv`` files."""
    rows: list[bytes] = []
    for name in sorted(members):
        if _STAMP.search(name):
            rows.extend(_member_rows(name, members[name]))
    if not rows:
        return pd.DataFrame(columns=["iso"])
    raw = pd.read_csv(
        io.BytesIO(b"\n".join(rows)),
        header=None,
        names=["stamp", "interval_local", "gmt_end", "mtlf", "actual", "area"],
        dtype={"stamp": str, "interval_local": str, "gmt_end": str, "area": str},
    )
    end = _parse_ts(raw["gmt_end"]).dt.tz_localize("UTC")
    # The issue time is the forward horizon's end less 168 elapsed hours. The
    # stamp is cross-checked against it; SPP's DST-day stamps do not follow
    # the tz database (fall-back: 07 UTC is "0200", 08 UTC "0200d"), so a
    # disagreement is tolerated only within DST_TOLERANCE of a transition.
    issue = end.groupby(raw["stamp"]).transform("max") - pd.Timedelta(
        hours=MTLF_HORIZON_HOURS
    )
    per_file = pd.DataFrame({"stamp": raw["stamp"], "issue": issue}).drop_duplicates(
        "stamp"
    )
    stamp_utc = (
        pd.to_datetime(per_file["stamp"].str[:12], format="%Y%m%d%H%M")
        .dt.tz_localize(SPP_TZ, ambiguous="NaT", nonexistent="NaT")
        .dt.tz_convert("UTC")
    )
    near_dst = _utc_offset(per_file["issue"] - DST_TOLERANCE) != _utc_offset(
        per_file["issue"] + DST_TOLERANCE
    )
    bad = (stamp_utc != per_file["issue"]) & ~near_dst
    if bad.any():
        stamps = sorted(per_file.loc[bad, "stamp"])[:5]
        raise ValueError(f"SPP MTLF: issue-time cross-check failed for {stamps}")
    df = pd.DataFrame(
        {
            "iso": "SPP",
            "area": raw["area"].str.strip(),
            "issue_time_utc": issue,
            "interval_end_utc": end,
            "lead_hours": ((end - issue) // pd.Timedelta(hours=1)).astype("int64"),
            "forecast_mw": pd.to_numeric(raw["mtlf"], errors="coerce"),
            "actual_mw": pd.to_numeric(raw["actual"], errors="coerce"),
        }
    )
    # A re-posted file can repeat an interval; keep the last row as published.
    df = df.drop_duplicates(["area", "issue_time_utc", "interval_end_utc"], keep="last")
    return df[df["forecast_mw"].notna()].reset_index(drop=True)


def read_year_zip(path: Path) -> dict[str, bytes]:
    """``{member: bytes}`` for every ``OP-MTLF-*.csv`` in one year zip."""
    with zipfile.ZipFile(path) as z:
        return {n: z.read(n) for n in z.namelist() if _STAMP.search(n)}


def parse(raw_dir: Path, spec: IsoSpec) -> dict[int, pd.DataFrame]:
    """``{issue year: frame}`` from every ``<year>.zip`` under ``raw_dir``."""
    out: dict[int, pd.DataFrame] = {}
    for path in sorted(Path(raw_dir).glob("*.zip")):
        df = parse_members(read_year_zip(path))
        if df.empty:
            continue
        years = df["issue_time_utc"].dt.year.to_numpy()
        for y in np.unique(years):
            part = df[years == y]
            out[int(y)] = (
                pd.concat([out[int(y)], part], ignore_index=True)
                if int(y) in out
                else part.reset_index(drop=True)
            )
    return out


SPEC = register(
    IsoSpec(
        iso="SPP",
        parse=parse,
        description="SPP portal mtlf-vs-actual hourly MTLF vintages",
    )
)
