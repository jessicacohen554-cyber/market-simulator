"""NEISO (ISO-NE) parser for the ``reserve-requirements`` datatype.

Raw source: ISO Express "Hourly Reserve Requirements" report
(ancillary-hourly-rr), archived as fixed 15-day window CSVs under
``data/raw/NEISO-AS/requirements/requirements_<start>_<end>.csv`` by
``scripts/fetch_neiso_reserve_requirements.py`` (which documents the endpoint
and the rule-13 admissibility argument).

Raw row format (report ``D`` rows)::

    D,<YYYY-MM-DD>,<HE>,<location id>,<TMSR MW>,<TMR MW>,<TOTAL MW>

``HE`` is the local hour-ending label (``01``..``24``). Each local day's rows
are aligned to UTC against the day's TRUE hour sequence (24 hours; 23 on the
spring-forward day, where HE ``03`` does not exist; 25 on the fall-back day,
where HE ``02`` legitimately repeats — file order disambiguates the repeat).
A published hour missing from the report (the source has occasional single-
hour holes, e.g. 2023-03-14 HE 15) becomes a gap that is step-filled from the
previous published hour (a requirement is a step series; forward-fill is the
faithful bridge), with the total filled hours per (year, location) bounded by
:data:`MAX_GAP_HOURS` — the ``eia_loader`` hourly-frame gap-budget precedent
— beyond which parsing hard-errors instead of silently reconstructing.

Location vocabulary (ISO-NE Web Services reserve locations): 7000=ROS (the
system-wide requirement row the model consumes), 7001=SWCT, 7002=CT,
7003=NEMABSTN. The three CSV value columns map to the canonical products
``10min_spin`` / ``10min_total`` / ``30min_total``.
"""

from __future__ import annotations

import csv
import datetime as dt
import re
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

from . import CANONICAL_COLUMNS, IsoSpec, finalize, register

ISO = "NEISO"
RAW_DIR = "NEISO-AS/requirements"

#: ISO-NE reserve-location vocabulary (Web Services API reserve locations).
LOCATION_BY_ID: dict[int, str] = {
    7000: "ROS",
    7001: "SWCT",
    7002: "CT",
    7003: "NEMABSTN",
}

#: CSV value columns (after date/HE/location) -> canonical product, in order:
#: Ten-Minute Spinning, Ten-Minute, TOTAL.
PRODUCTS: tuple[str, ...] = ("10min_spin", "10min_total", "30min_total")

#: Max source-hole hours step-filled per (year, location) before parsing
#: hard-errors. Mirrors ``eia_loader._HOURLY_FRAME_MAX_GAP``: a few missing
#: hours are a publication hiccup; more signals a structurally incomplete
#: archive that must be re-fetched, never silently reconstructed.
MAX_GAP_HOURS = 72

_TZ = ZoneInfo("America/New_York")
_FNAME = re.compile(r"^requirements_(\d{8})_(\d{8})\.csv$")


def _window_files(raw_root: Path) -> list[tuple[dt.date, dt.date, Path]]:
    """Discover the window CSVs in the drop zone, sorted by start date."""
    out = []
    root = Path(raw_root) / RAW_DIR
    if not root.is_dir():
        return []
    for path in sorted(root.iterdir()):
        m = _FNAME.match(path.name)
        if m:
            s = dt.datetime.strptime(m.group(1), "%Y%m%d").date()
            e = dt.datetime.strptime(m.group(2), "%Y%m%d").date()
            out.append((s, e, path))
    return out


def years(raw_root: Path) -> list[int]:
    """Calendar years the raw drop zone currently covers (by window start)."""
    return sorted({s.year for s, _, _ in _window_files(raw_root)})


def _day_utc_hours(day: dt.date) -> pd.DatetimeIndex:
    """The local day's true UTC hour-beginnings (24; 23/25 on DST days)."""
    start = pd.Timestamp(day).tz_localize(_TZ).tz_convert("UTC")
    end = pd.Timestamp(day + dt.timedelta(days=1)).tz_localize(_TZ).tz_convert("UTC")
    return pd.date_range(start, end, freq="h", inclusive="left")


def _norm_he(label: str) -> str:
    """Normalize an hour-ending label (strip a fall-back ``X`` suffix)."""
    return label.strip().upper().rstrip("X").zfill(2)


def _align_day(
    day: dt.date,
    rows: list[tuple[str, tuple[float, float, float]]],
    context: str,
) -> list[tuple[pd.Timestamp, tuple[float, float, float] | None]]:
    """Align one local day's (HE label, values) rows onto its true UTC hours.

    Expected labels come from the day's true local hour sequence (HE =
    local hour-beginning + 1), so the fall-back repeat and the spring-forward
    skip are generated, not special-cased. Rows must appear in published
    order; a missing hour yields ``None`` (a gap for the caller to fill);
    an unmatched leftover row is a hard error.
    """
    hours_utc = _day_utc_hours(day)
    expected = [f"{ts.tz_convert(_TZ).hour + 1:02d}" for ts in hours_utc]
    out: list[tuple[pd.Timestamp, tuple[float, float, float] | None]] = []
    ptr = 0
    for ts_utc, exp in zip(hours_utc, expected):
        if ptr < len(rows) and _norm_he(rows[ptr][0]) == exp:
            out.append((ts_utc, rows[ptr][1]))
            ptr += 1
        else:
            out.append((ts_utc, None))
    if ptr != len(rows):
        raise ValueError(
            f"{context} {day}: row with HE {rows[ptr][0]!r} does not fit the "
            f"day's hour sequence {expected}"
        )
    return out


def parse(raw_root: Path, year: int) -> pd.DataFrame:
    """Parse ``year``'s window CSVs into the canonical tidy frame.

    Returns an empty frame when no window file for the year is present.
    Raises ``ValueError`` on malformed rows, unknown locations, out-of-order
    hour labels, or more than :data:`MAX_GAP_HOURS` step-filled source holes
    per location.
    """
    # (day, location_id) -> ordered list of (HE label, (tmsr, tmr, total)).
    by_day_loc: dict[
        tuple[dt.date, int], list[tuple[str, tuple[float, float, float]]]
    ] = {}
    for s, _e, path in _window_files(raw_root):
        if s.year != year:
            continue
        with path.open(newline="") as fh:
            for row in csv.reader(fh):
                if not row or row[0] != "D":
                    continue
                if len(row) < 7:
                    raise ValueError(f"{path.name}: short D row {row!r}")
                day = dt.date.fromisoformat(row[1])
                loc_id = int(row[3])
                if loc_id not in LOCATION_BY_ID:
                    raise ValueError(
                        f"{path.name}: unknown location id {loc_id} "
                        f"(known: {sorted(LOCATION_BY_ID)})"
                    )
                by_day_loc.setdefault((day, loc_id), []).append(
                    (row[2], (float(row[4]), float(row[5]), float(row[6])))
                )
    if not by_day_loc:
        return pd.DataFrame(columns=list(CANONICAL_COLUMNS))

    # Per location: align each day, then step-fill source holes (bounded).
    records: list[dict] = []
    gaps_by_loc: dict[int, int] = {}
    for loc_id in sorted({loc for _, loc in by_day_loc}):
        aligned: list[tuple[pd.Timestamp, tuple[float, float, float] | None]] = []
        for day in sorted({d for d, loc in by_day_loc if loc == loc_id}):
            aligned.extend(
                _align_day(day, by_day_loc[(day, loc_id)], f"location {loc_id}")
            )
        vals = np.array(
            [v if v is not None else (np.nan,) * 3 for _, v in aligned], dtype=float
        )
        n_gap = int(np.isnan(vals[:, 0]).sum())
        gaps_by_loc[loc_id] = n_gap
        if n_gap > MAX_GAP_HOURS:
            raise ValueError(
                f"{year} location {loc_id}: {n_gap} missing source hours "
                f"> MAX_GAP_HOURS={MAX_GAP_HOURS}; re-fetch the raw windows "
                f"instead of reconstructing"
            )
        if n_gap:
            frame = pd.DataFrame(vals).ffill().bfill()  # step-hold; bfill only
            vals = frame.to_numpy()  # covers a leading-edge hole
        for (ts_utc, _), (tmsr, tmr, total) in zip(aligned, vals):
            local = ts_utc.tz_convert(_TZ).tz_localize(None)
            for product, mw in zip(PRODUCTS, (tmsr, tmr, total)):
                records.append(
                    {
                        "iso": ISO,
                        "location": LOCATION_BY_ID[loc_id],
                        "location_id": loc_id,
                        "product": product,
                        "interval_start_utc": ts_utc,
                        "interval_start_local": local,
                        "requirement_mw": float(mw),
                    }
                )
    total_gaps = sum(gaps_by_loc.values())
    if total_gaps:
        print(
            f"[gap ] NEISO {year}: step-filled {total_gaps} missing source "
            f"hour(s) {dict(sorted(gaps_by_loc.items()))}"
        )

    df = pd.DataFrame.from_records(records)
    df["interval_start_utc"] = pd.DatetimeIndex(df["interval_start_utc"])
    df["interval_start_local"] = pd.DatetimeIndex(df["interval_start_local"])
    df["location_id"] = df["location_id"].astype("int64")
    return finalize(df)


register(IsoSpec(iso=ISO, raw_dir=RAW_DIR, parse=parse, years=years))
