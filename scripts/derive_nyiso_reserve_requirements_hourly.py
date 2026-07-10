"""Derive the measured hourly NYISO reserve-requirement series (Ask B / #1344).

Reconstructs ``NYISO_reserve_requirements_{year}.csv`` — the loader contract of
``src/market_sim/data/nyiso_reserve_requirements.py`` (consumed when
``ScenarioConfig.nyiso_dynamic_reserve_requirements`` is on) — from the two
intaken measured sources of Ask B (``docs/handoffs/nyiso-data-asks-2026-07.md``):

* ``nyiso-reserve-requirements`` (clean) — the published dated "Locational
  Reserve Requirements" schedule, including the SENY 30-minute hourly step
  shape and the per-version Thunderstorm-Alert zeroing flags (Ask B3).
* ``nyiso-operating-events`` (clean) — the MIS message-log events (Ask B2);
  only the ``thunderstorm_alert`` start/end transitions are consumed here.

Construction, per hour-beginning ``h`` of the model's non-leap 8760 clock
(naive Eastern wall-clock, Feb 29 dropped — the ``process_nyiso_as.py``
convention shared by the AS price CSVs this file sits beside)::

    requirement(region, product, h) =
        published_base(region, product, HB(h)) * (1 - tsa_fraction(h))
            if the version flags the row TSA-reduced-to-zero, else
        published_base(region, product, HB(h))

``tsa_fraction(h)`` is the fraction of the wall-clock hour covered by a
logged Thunderstorm Alert window — the hourly time-weighted mean of the
sub-hourly enforcement, matching the loader's hour-mean aggregation rule.

Admissibility (rule 13): this is the deterministic published requirement
schedule plus the published TSA-zeroing rule applied to logged TSA windows —
a measured market-design *input* that regenerates for a forward year
(published base + condition rules applied to forward states) and responds to
changed conditions. It is deliberately NOT the full as-enforced series: the
condition-varying increments NYISO schedules into RTD/RTC (forecast-
uncertainty adders, largest-single-contingency changes) are not freely
published (Ask B1 — confirmed request-only, 2026-07-10) and are absent here;
the derived series is therefore a documented LOWER BOUND on the enforced
requirement in non-TSA hours. Rule 24: this derive re-runs only when its
source data updates — never against a residual.

Only (region, product) pairs with an in-LP reserve family are emitted
(``FAMILY_BY_REGION_PRODUCT`` — imported from the loader so the two can never
drift); every dropped published row (LI, EAST spin/30-min, zero-MW products)
is logged, never silently (no-silent-caps).

Run (after ``scripts/curate_nyiso_reserve_requirements.py``)::

    python scripts/derive_nyiso_reserve_requirements_hourly.py [--year 2023 2024 2025]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "src"))

from market_sim.data.nyiso_reserve_requirements import (  # noqa: E402
    FAMILY_BY_REGION_PRODUCT,
    NYISO_RESERVE_REQUIREMENTS_DIR,
)
from scripts.lib import clean_io  # noqa: E402

SCHEDULE_DATATYPE = "nyiso-reserve-requirements"
EVENTS_DATATYPE = "nyiso-operating-events"

#: Transcription vocabulary -> loader vocabulary. LI is deliberately absent —
#: it has no in-LP reserve family (reserve_config._nyiso_design); its published
#: rows are logged as dropped.
REGION_MAP: dict[str, str] = {
    "NYCA": "NYCA",
    "EAST": "East",
    "SENY": "SENY",
    "NYC": "NYC",
}
PRODUCT_MAP: dict[str, str] = {
    "spin_10": "10min_spin",
    "total_10": "10min_total",
    "total_30": "30min_total",
}

#: Training years (rule 22). Out-of-training derivation is possible from the
#: intaken 2018–H1-2026 sources but is not produced by default — the solve
#: quarantine makes the files unusable until an ISO's marker exists.
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)


def select_version(schedule: pd.DataFrame, year: int) -> pd.DataFrame:
    """Return the schedule rows of the single version in force all of ``year``.

    A version covers the year when its evidence window contains the whole
    calendar year (``evidence_start <= Jan 1`` and ``evidence_end`` null or
    ``>= Jan 1`` of the next year). Raises if no version — or more than one —
    covers the year: a mid-year requirement change must be handled explicitly,
    never averaged away.
    """
    year_start = pd.Timestamp(year=year, month=1, day=1)
    year_end = pd.Timestamp(year=year + 1, month=1, day=1)
    covering = []
    for version, grp in schedule.groupby("version", sort=True):
        start = grp["evidence_start"].min()
        end = grp["evidence_end"].max()  # NaT for the current version
        if start <= year_start and (pd.isna(end) or end >= year_end):
            covering.append(version)
    if len(covering) != 1:
        raise ValueError(
            f"{year}: expected exactly one LRR version covering the full year, "
            f"got {covering} — a partial/ambiguous evidence window needs an "
            f"explicit mid-year treatment, not this derive."
        )
    return schedule[schedule["version"] == covering[0]]


def build_tsa_windows(
    events: pd.DataFrame,
) -> tuple[list[tuple[pd.Timestamp, pd.Timestamp]], list[str]]:
    """Pair thunderstorm-alert transitions into [start, end) windows.

    State machine over the full corpus in ``(timestamp_local, seq)`` order.
    An explicit "no longer operating in thunderstorm alert" message ALWAYS
    closes the open window — it is an affirmative measurement, and genuine
    overnight TSAs exist whose spanned midnight carries no start-of-day
    ACTIVE row (e.g. 2025-03-31 21:00 -> 2025-04-01 02:15), so midnight
    attestation is corroborating, not required, for end-paired windows.

    The **midnight-attestation bound** repairs the opposite defect — a start
    whose end message is missing from the log entirely (e.g. 2025-06-19,
    2025-07-31, each followed only by a later start). When a NEW start (or
    the corpus edge) arrives with no intervening end, the open window cannot
    be allowed to swallow the gap: it closes at its first midnight NOT
    attested by a "Start of day thunderstorm alert state is ACTIVE" row
    (curated as ``action=start, start_of_day=True``). The true end time
    within that final day is unknown; the midnight close is a documented
    conservative upper bound. A start earlier than the open window's
    attestation bound is a same-span re-declaration and is ignored; an
    attested start-of-day continuation is the normal overnight case (not an
    anomaly); an ``end`` while inactive is a parse gap and is skipped (no
    window is invented). Returns ``(windows, anomaly_log)`` — every repair
    and ignored transition is itemized, never silent.
    """
    tsa = (
        events[events["event_type"] == "thunderstorm_alert"]
        .sort_values(["timestamp_local", "seq"])
        .reset_index(drop=True)
    )
    sod_active = set(
        tsa.loc[
            (tsa["action"] == "start") & tsa["start_of_day"].astype(bool),
            "timestamp_local",
        ]
    )
    one_day = pd.Timedelta(days=1)

    def _midnight_bound(start: pd.Timestamp) -> pd.Timestamp:
        """First midnight after ``start`` NOT attested ACTIVE — the latest
        instant the window opened at ``start`` is allowed to reach."""
        m = start.normalize() + one_day
        while m in sod_active:
            m += one_day
        return m

    windows: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    anomalies: list[str] = []
    open_start: pd.Timestamp | None = None
    bound: pd.Timestamp | None = None

    def _close_at_bound() -> None:
        nonlocal open_start
        assert open_start is not None and bound is not None
        anomalies.append(
            f"missing end for start at {open_start}: closed at unattested midnight {bound}"
        )
        windows.append((open_start, bound))
        open_start = None

    for row in tsa.itertuples():
        ts = row.timestamp_local
        if row.action == "start":
            # A start beyond the open window's attestation bound means the
            # previous start's end is missing. (A sod continuation row never
            # trips this: its own midnight is in the attestation set, so
            # bound > ts by construction.)
            if open_start is not None and ts > bound:
                _close_at_bound()
            if open_start is None:
                open_start = ts
                bound = _midnight_bound(ts)
            elif bool(row.start_of_day):
                pass  # attested overnight continuation — the normal case
            else:
                anomalies.append(
                    f"duplicate start ignored at {ts} (active since {open_start})"
                )
        elif row.action == "end":
            if open_start is None:
                anomalies.append(f"end without start skipped at {ts}")
            elif ts <= open_start:
                anomalies.append(
                    f"non-positive window skipped: start {open_start} end {ts}"
                )
                open_start = None
            else:
                if ts > bound:
                    anomalies.append(
                        f"note: window {open_start} -> {ts} spans midnight(s) "
                        f"without a start-of-day ACTIVE row (attestation missing, "
                        f"explicit end trusted)"
                    )
                windows.append((open_start, ts))
                open_start = None
        else:
            anomalies.append(f"unknown TSA action {row.action!r} at {ts}")
    if open_start is not None:
        corpus_end = min(events["timestamp_local"].max(), bound)
        anomalies.append(f"unclosed start at {open_start} closed at {corpus_end}")
        if corpus_end > open_start:
            windows.append((open_start, corpus_end))
    return windows, anomalies


def hourly_clock(year: int) -> pd.DatetimeIndex:
    """Naive Eastern wall-clock hour-beginning stamps for ``year``, Feb 29
    dropped — always exactly 8760 entries (the model's non-leap clock)."""
    idx = pd.date_range(
        start=pd.Timestamp(year=year, month=1, day=1),
        end=pd.Timestamp(year=year + 1, month=1, day=1),
        freq="h",
        inclusive="left",
    )
    idx = idx[~((idx.month == 2) & (idx.day == 29))]
    assert len(idx) == 8760, f"{year}: clock has {len(idx)} hours, expected 8760"
    return idx


def tsa_fraction(
    clock: pd.DatetimeIndex, windows: list[tuple[pd.Timestamp, pd.Timestamp]]
) -> np.ndarray:
    """Fraction of each wall-clock hour covered by a TSA window (0..1).

    Overlap is computed in naive local time — the same convention as the
    window timestamps and the output ``Time Stamp`` column. Feb 29 hours are
    absent from ``clock``, so leap-day TSA time drops with the day.
    """
    frac = np.zeros(len(clock), dtype=float)
    # Force ns resolution: pandas 2.x may build the clock as datetime64[us],
    # while Timestamp.value is always ns.
    hour_start = clock.as_unit("ns").asi8
    one_hour_ns = 3_600_000_000_000
    for start, end in windows:
        s, e = start.as_unit("ns").value, end.as_unit("ns").value
        overlap_ns = np.minimum(hour_start + one_hour_ns, e) - np.maximum(hour_start, s)
        frac += np.clip(overlap_ns, 0, one_hour_ns) / one_hour_ns
    return np.clip(frac, 0.0, 1.0)


def build_hourly_base(pair_rows: pd.DataFrame) -> np.ndarray:
    """(24,) published requirement by hour-beginning from one (region, product)'s
    period rows ('all' or 'hb_range'); every HB must be covered exactly once."""
    base = np.full(24, np.nan)
    for row in pair_rows.itertuples():
        if row.period_label == "all":
            lo, hi = 0, 23
        elif row.period_label == "hb_range":
            lo, hi = int(row.hb_start), int(row.hb_end)
        else:
            raise ValueError(
                f"{row.region}/{row.product}: period_label {row.period_label!r} has no "
                f"published hour definition — cannot derive an hourly series from it."
            )
        if not np.all(np.isnan(base[lo : hi + 1])):
            raise ValueError(
                f"{row.region}/{row.product}: overlapping period rows at HB{lo}-{hi}"
            )
        base[lo : hi + 1] = row.requirement_mw
    if np.any(np.isnan(base)):
        missing = [h for h in range(24) if np.isnan(base[h])]
        raise ValueError(f"hour-beginnings {missing} uncovered by period rows")
    return base


def derive_year(
    schedule: pd.DataFrame, events: pd.DataFrame, year: int
) -> tuple[pd.DataFrame, list[str]]:
    """Build the hourly requirement frame for ``year``.

    Returns ``(frame, log)`` where ``frame`` has the loader-contract columns
    (``Time Stamp``, ``region``, ``product``, ``requirement_mw``; 8760 rows
    per emitted (region, product)) and ``log`` itemizes dropped published
    rows and TSA pairing anomalies.
    """
    version_rows = select_version(schedule, year)
    windows, anomalies = build_tsa_windows(events)
    log = [f"TSA pairing: {a}" for a in anomalies]

    clock = hourly_clock(year)
    year_windows = [
        (max(s, clock[0]), min(e, clock[-1] + pd.Timedelta(hours=1)))
        for s, e in windows
        if e > clock[0] and s < clock[-1] + pd.Timedelta(hours=1)
    ]
    frac = tsa_fraction(clock, year_windows)
    hb = clock.hour.to_numpy()

    frames = []
    for (raw_region, raw_product), pair_rows in version_rows.groupby(
        ["region", "product"], sort=True
    ):
        region = REGION_MAP.get(str(raw_region))
        product = PRODUCT_MAP.get(str(raw_product))
        mw = float(pair_rows["requirement_mw"].max())
        if (region, product) not in FAMILY_BY_REGION_PRODUCT:
            log.append(
                f"dropped published row {raw_region}/{raw_product} "
                f"(max {mw:g} MW): no in-LP reserve family"
            )
            continue
        base = build_hourly_base(pair_rows)
        series = base[hb].astype(float)
        if bool(pair_rows["tsa_reduced_to_zero"].any()):
            series = series * (1.0 - frac)
        frames.append(
            pd.DataFrame(
                {
                    "Time Stamp": clock.strftime("%Y-%m-%d %H:%M:%S"),
                    "region": region,
                    "product": product,
                    "requirement_mw": np.round(series, 2),
                }
            )
        )
    if not frames:
        raise ValueError(f"{year}: no (region, product) pair mapped to an in-LP family")
    out = pd.concat(frames, ignore_index=True)
    n_tsa_hours = int((frac > 0).sum())
    log.append(
        f"{year}: {len(frames)} series x 8760 h; {len(year_windows)} TSA windows "
        f"touching {n_tsa_hours} hours ({frac.sum():.1f} equivalent full hours zeroed)"
    )
    return out, log


def main(argv: list[str] | None = None) -> None:
    """CLI: derive and write the per-year loader-contract CSVs."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        default=list(DEFAULT_YEARS),
        help="years to derive (default: the 2023-2025 training window)",
    )
    args = parser.parse_args(argv)

    schedule = clean_io.read_clean(SCHEDULE_DATATYPE, "NYISO")
    events = clean_io.read_clean(EVENTS_DATATYPE, "NYISO")

    for year in args.year:
        frame, log = derive_year(schedule, events, year)
        out_path = (
            NYISO_RESERVE_REQUIREMENTS_DIR / f"NYISO_reserve_requirements_{year}.csv"
        )
        frame.to_csv(out_path, index=False)
        for line in log:
            print(f"  {line}")
        print(f"wrote {out_path}  ({len(frame):,} rows)\n")


if __name__ == "__main__":
    main()
