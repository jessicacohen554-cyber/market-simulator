"""Build ERCOT hourly ancillary-service (up-reserve) withholding MW series.

For each requested year, sums ERCOT's cleared Day-Ahead Market *upward*
ancillary-service quantities into a single system-wide hourly MW series and
writes it to ``data/raw/ercot-AS/ercot_<year>_as_up_mw.parquet``.

This series is the capacity that thermal/storage units clear as AS and so
hold *out* of the energy market. The backcast's AS-reserve-withholding probe
(``ScenarioConfig.as_reserve_withholding``) removes it from thermal headroom
before the supply curve clears — an upper bound that books all AS to thermal,
with no storage/load split (the per-resource DAM Gen Resource Data needed for
a true split is not available across the backcast window; see the AS data
notes). Down-regulation (Reg-Down) is excluded: it does not remove an upward
energy offer.

Source: ERCOT 2-Day Cleared DAM Ancillary Service reports (NP3-911-ER), one
zip per service, already uploaded under ``data/raw/ercot-AS/``. Each
zip holds a single JSON with ``fields`` + ``data`` (rows of
``[deliveryDate, hourEnding, totalClearedAS<SVC>]``).

Up-reserve services summed:
    REGUP                          regulation up
    RRSPFR + RRSFFR + RRSUFR       responsive reserve (PFR/FFR/UFR components)
    ECRSS + ECRSM                  ERCOT contingency reserve
    NSPIN + NSPNM                  non-spinning reserve

The series sits on the model's fixed non-leap 8760-hour clock keyed to
ERCOT-local **standard** time (CST, UTC-6, no DST — the EIA-930 demand clock).
The reports label hours in Central *Prevailing* Time with SEQUENTIAL hour
numbering on the DST transition days (23 rows skipping HE 3 at spring-forward;
25 rows HE 1-25 at fall-back), so the labels are converted CPT -> CST before
placement (:func:`prevailing_he_to_cst`, reusing
``build_ercot_hsl._prevailing_to_standard``); the CST clock is then covered
gapless through both transitions. (The pre-2026-07-07 build placed the labels
unconverted — the naive ``date + (HE-1)``, leaving the whole mid-Mar–early-Nov
series one hour late, the same placement defect class as the NP4-732/737 HSL
intake; ``docs/handoffs/ercot-g22-demand-side-design-2026-07.md`` §7.) Feb 29
of a leap year is dropped. A service with no coverage in a year (e.g. NSPNM
before Dec 2025) contributes zeros rather than fabricated data.

Run:
    python scripts/build_ercot_as_withholding.py                # 2024 2025
    python scripts/build_ercot_as_withholding.py --year 2024
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

HOURS_PER_YEAR = 8760
REPO_ROOT = Path(__file__).resolve().parents[1]
AS_DIR = REPO_ROOT / "data" / "raw" / "ercot-AS"

sys.path.insert(0, str(REPO_ROOT / "scripts"))
from build_ercot_hsl import _prevailing_to_standard  # noqa: E402

# Years built when --year is not given. The NP3-911 *2-Day* cleared-DAM-AS
# reports under data/raw/ercot-AS/ only reach back to 2023-12-10, so THIS
# builder cannot produce a full-year 2023 series — full-year 2023 AS is built by
# the sibling ``scripts/build_ercot_as_2023.py`` from the 60-Day DAM Disclosure
# (Gen Resource Data per-resource awards + ASPLANNP433 + the NP3-911 Dec tail),
# which writes the same ``ercot_2023_as_up_mw.parquet`` /
# ``ercot_2023_as_by_restype_hourly.parquet``. Run that script for 2023; this one
# covers 2024/2025 (and any later year the 2-Day feed fully spans).
#
# 2018-2022 holdout-intake note (2026-07-10,
# scripts/fetch_ercot_as_reports.py): confirmed live that ERCOT's free MIS
# doc list for NP3-911-ER is a *rolling* ~31-day window that always ends
# "today" (ERCOT's own ``misDisplayDuration_i`` catalog field) -- it is not a
# fixed 2023-12-10 start date that will ever extend further back in time.
# 2018-2022 (and, going forward, most of any year outside the last ~31 days)
# is therefore structurally unreachable via this feed and always will be;
# only the credentialed data.ercot.com/api.ercot.com archive reaches that far,
# and the repo owner has declined to procure it (see fetch script docstring).
DEFAULT_YEARS: tuple[int, ...] = (2024, 2025)

# Up-reserve service report tags (the ``2d_cleared_dam_as_<tag>`` suffix).
# Reg-Down (regdn) is deliberately excluded — see module docstring.
_UP_SERVICE_TAGS: tuple[str, ...] = (
    "regup",
    "rrspfr",
    "rrsffr",
    "rrsufr",
    "ecrss",
    "ecrsm",
    "nspin",
    "nspnm",
)

# Largest hole (hours) interpolated when placing a service on the 8760-hour
# clock. The DST spring-forward gap is 1 hour; a service present in the year
# but missing more than a day of hours signals an incomplete upload.
_MAX_GAP_HOURS = 24

# (month, day, hour) calendar of the fixed non-leap 8760-hour clock, shared
# by every model year (matches build_ercot_hsl and the ERCO demand clock).
_CALENDAR = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")
_FULL_INDEX = pd.MultiIndex.from_arrays(
    [_CALENDAR.month, _CALENDAR.day, _CALENDAR.hour],
    names=["month", "day", "hour"],
)


def prevailing_he_to_cst(date: pd.Series, he: pd.Series) -> pd.Series:
    """Convert sequential prevailing (delivery-date, hour-ending) labels to CST.

    ERCOT's DAM-family reports (NP3-911 cleared AS, the 60-Day Gen Resource
    Data, DAMASAGG, ...) label hours in Central Prevailing Time with
    SEQUENTIAL hour-ending numbering across the DST transitions: the
    spring-forward day carries 23 rows (HE 3 absent — the 02:00 wall-clock
    hour does not exist in prevailing time), the fall-back day 25 rows
    (HE 1-25, where HE 3 is the repeated 01:00-02:00 hour, already back on
    CST). This maps each (date, HE) label to its prevailing hour-beginning
    stamp — on a 25-row day HE >= 3 sits one wall-clock hour earlier than the
    naive ``HE - 1`` — synthesizes the fall-back disambiguator ('Y' on the
    HE 3 repeat), and hands off to ``build_ercot_hsl._prevailing_to_standard``
    for the CPT -> CST conversion. The CST clock is covered gapless through
    both transitions (the spring day's missing CST 23:00 arrives from the
    next day's HE 1).

    Args:
        date: normalized delivery-date datetimes (one per row).
        he: integer hour-ending labels (1-24, 25 on the fall-back day).

    Returns:
        Hour-beginning timestamps on the fixed CST (UTC-6) clock.
    """
    date = pd.to_datetime(date)
    he = pd.Series(np.asarray(he, dtype=int), index=date.index)
    # Sequentially-numbered fall-back days are exactly the 25-label days.
    max_he = he.groupby(date).transform("max")
    is_fall_back = max_he == 25
    hb = (he - 1).where(~(is_fall_back & (he >= 3)), he - 2)
    ts = date + pd.to_timedelta(hb, unit="h")
    flag = pd.Series(np.where(is_fall_back & (he == 3), "Y", "N"), index=date.index)
    return _prevailing_to_standard(ts, flag)


def _service_zip(tag: str) -> Path | None:
    """Return the NP3-911 zip for service ``tag`` (newest if several)."""
    matches = sorted(AS_DIR.glob(f"*2d_cleared_dam_as_{tag}.*.zip"))
    return matches[-1] if matches else None


def _read_service(tag: str) -> pd.DataFrame:
    """Read one service zip into ``(ts, mw)`` rows (hour-beginning ts).

    Returns an empty frame when the service zip is absent.
    """
    path = _service_zip(tag)
    if path is None:
        print(f"  {tag:7s}: no zip found — contributing zeros")
        return pd.DataFrame({"ts": pd.to_datetime([]), "mw": []})
    with zipfile.ZipFile(path) as zf:
        member = next(m for m in zf.namelist() if m.lower().endswith(".json"))
        obj = json.loads(zf.read(member))
    data = obj["data"]
    if not data:
        return pd.DataFrame({"ts": pd.to_datetime([]), "mw": []})
    arr = pd.DataFrame(data)  # columns 0=deliveryDate, 1=hourEnding, 2=value
    date = pd.to_datetime(arr[0])
    # Prevailing sequential HE labels (1-24; 25 on the fall-back day) -> CST.
    ts = prevailing_he_to_cst(date, arr[1].astype(int))
    return pd.DataFrame({"ts": ts, "mw": pd.to_numeric(arr[2], errors="coerce")})


def _to_model_clock(rows: pd.DataFrame, year: int) -> np.ndarray:
    """Place ``(ts, mw)`` rows on the non-leap 8760-hour clock for ``year``.

    Filters to ``year`` (Feb 29 dropped), averages by CST ``(month, day,
    hour)`` — timestamps are already on the fixed CST clock, so DST needs no
    handling here — and reindexes onto the fixed non-leap calendar,
    interpolating any scattered telemetry holes. An empty input (service
    absent in the year) yields zeros.
    """
    if rows.empty:
        return np.zeros(HOURS_PER_YEAR, dtype=float)
    ts = rows["ts"]
    keep = (ts.dt.year == year) & ~((ts.dt.month == 2) & (ts.dt.day == 29))
    rows = rows[keep]
    if rows.empty:
        return np.zeros(HOURS_PER_YEAR, dtype=float)
    grouped = rows.groupby(
        [rows["ts"].dt.month, rows["ts"].dt.day, rows["ts"].dt.hour]
    )["mw"].mean()
    grouped.index.names = ["month", "day", "hour"]
    aligned = grouped.reindex(_FULL_INDEX)
    missing = int(aligned.isna().sum())
    if 0 < missing <= _MAX_GAP_HOURS:
        aligned = aligned.interpolate(limit_direction="both")
    elif missing > _MAX_GAP_HOURS:
        # Partial-year coverage (e.g. a service that started mid-year): fill
        # the uncovered hours with zero rather than interpolating across a
        # multi-month hole, which would fabricate reserve where none cleared.
        aligned = aligned.fillna(0.0)
    return aligned.to_numpy(dtype=float)


def build_year(year: int) -> bool:
    """Build and write one year's AS up-reserve withholding parquet."""
    print(f"\n=== ERCOT {year} cleared DAM up-AS (withholding MW) ===")
    per_service: dict[str, np.ndarray] = {}
    for tag in _UP_SERVICE_TAGS:
        series = _to_model_clock(_read_service(tag), year)
        per_service[tag] = series
        if series.any():
            print(
                f"  {tag:7s}: mean {series.mean():7.1f} MW   "
                f"peak {series.max() / 1000:5.2f} GW"
            )
    total = np.sum(list(per_service.values()), axis=0)
    if not total.any():
        print(f"  {year}: no up-AS coverage — skipping.")
        return False

    print(
        f"\n  TOTAL up-AS: mean {total.mean() / 1000:5.2f} GW   "
        f"peak {total.max() / 1000:5.2f} GW   "
        f"min {total.min() / 1000:5.2f} GW"
    )

    frame = pd.DataFrame({"hour": np.arange(HOURS_PER_YEAR, dtype="int64")})
    for tag, series in per_service.items():
        frame[f"{tag}_mw"] = series
    frame["as_up_mw"] = total

    table = pa.Table.from_pandas(frame, preserve_index=False)
    table = table.replace_schema_metadata(
        {
            "source": "ERCOT 2-Day Cleared DAM Ancillary Service reports "
            "(NP3-911-ER), data/raw/ercot-AS/",
            "description": f"ERCOT {year} system-wide hourly cleared DAM upward "
            "ancillary-service MW (RegUp + RRS + ECRS + NonSpin; "
            "Reg-Down excluded), on the non-leap 8760-hour "
            "ERCOT-local clock.",
            "units": "MW (cleared capacity per hour)",
            "clock": "Fixed non-leap 8760h ERCOT-local STANDARD time (CST, "
            "UTC-6): the reports' Central-Prevailing sequential HE labels "
            "(HE 1-25 on the fall-back day) are converted CPT->CST before "
            "placement, matching the EIA-930 demand clock.",
            "year": str(year),
        }
    )
    out = AS_DIR / f"ercot_{year}_as_up_mw.parquet"
    pq.write_table(table, out)
    print(f"  Wrote {out.relative_to(REPO_ROOT)} ({out.stat().st_size / 1024:.1f} KiB)")
    return True


def main(argv: list[str] | None = None) -> int:
    """Build the requested ERCOT AS up-reserve withholding parquets."""
    parser = argparse.ArgumentParser(
        prog="build_ercot_as_withholding",
        description="Build ERCOT hourly cleared DAM up-AS (withholding MW) "
        "parquets from the NP3-911 cleared-AS reports.",
    )
    parser.add_argument(
        "--year",
        type=int,
        nargs="+",
        default=list(DEFAULT_YEARS),
        help="Years to build (default: %(default)s).",
    )
    args = parser.parse_args(argv)
    built = [year for year in args.year if build_year(year)]
    skipped = sorted(set(args.year) - set(built))
    if skipped:
        print(f"\nSkipped (no source data): {skipped}")
    return 0 if built else 1


if __name__ == "__main__":
    sys.exit(main())
