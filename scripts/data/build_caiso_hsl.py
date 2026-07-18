"""Build CAISO uncurtailed renewable potential (HSL-analogue) hourly profiles.

Reads CAISO's published *Production and Curtailments* workbooks
(``data/raw/caiso-curtailment/productionandcurtailmentsdata_<year>.xlsx``,
5-minute interval data from the daily curtailment reports) and combines the
reported wind/solar curtailment with the EIA-930 ``CISO hourly`` delivered
generation into the HSL analogue the playbook (doc 05 §8.3) calls for:

    uncurtailed potential (HSL) = EIA-930 delivered + reported curtailment

so the GEN/HSL pair mirrors ERCOT's NP6 dataset (see
scripts/data/build_ercot_hsl.py) and the dispatch can *re-curtail* CAISO solar
under the modeled transmission limits instead of inheriting the historical
curtailment baked into delivered output. One parquet per year is written to
``data/raw/caiso-hsl/caiso_<year>_hsl_hourly.parquet`` with the same
schema as the ERCOT file.

Both inputs are on the model's chronological clock: the EIA-930 series is the
BA's local hourly year (Feb 29 dropped in leap years) and the curtailment rows
are stamped with CAISO local date / hour-of-day, mapped here onto the same
non-leap 8760-hour index.

A year whose curtailment sheet does not reach December is SKIPPED rather than
built: filling the uncovered months with zero curtailment would fabricate an
uncurtailed series equal to delivered exactly where (summer) curtailment is
largest. Such a year keeps the EIA-930 delivered-profile fallback in
``market_sim.data.renewables`` until CAISO's full-year workbook is uploaded.

Source dataset:
    CAISO, "Production and curtailments data" (5-minute), published with the
    daily Renewables and Curtailments reports:
    https://www.caiso.com/library/managing-oversupply
    Reported totals cross-check: CAISO curtailed ~2.7 TWh of wind+solar in
    2023 and ~3.4 TWh in 2024 (this script prints the computed totals).

Run:
    python scripts/data/build_caiso_hsl.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.constants import HOURS_PER_YEAR  # noqa: E402
from market_sim.config.paths import (  # noqa: E402
    CAISO_CURTAILMENT_DIR,
    CAISO_HSL_DIR,
)
from market_sim.data.eia_loader import (  # noqa: E402
    load_eia_hourly_renewable_gen,
)

# Source workbooks and output HSL parquets resolve through config/paths.py
# (the single raw root under data/raw/ after the W1 relocation).
RAW_DIR = CAISO_CURTAILMENT_DIR
OUT_DIR = CAISO_HSL_DIR

INTERVALS_PER_HOUR = 12  # 5-minute report intervals

# Cumulative hours before the first of each 1-based month on the model's
# fixed non-leap calendar (Feb 29 dropped), matching eia_loader's clock.
_MONTH_DAYS: tuple[int, ...] = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum(_MONTH_DAYS[:m]) * 24) for m in range(12)
)


def load_reported_curtailment_hourly(
    path: Path,
) -> tuple[np.ndarray, np.ndarray, int]:
    """Read one workbook's Curtailments sheet as hourly-average MW series.

    The sheet lists only the 5-minute intervals in which curtailment was
    observed, one row per (interval, reason); absent intervals are zero by
    construction. Rows are summed per local (month, day, hour-of-day) and
    divided by the 12 intervals per hour, giving the hourly-average curtailed
    MW (numerically MWh per hour). The ``Date`` column's time-of-day is a
    serialization artifact (some exports stamp UTC-midnight 08:00); only the
    date part is used, with ``Hour`` (1-24, hour-beginning index) supplying
    the hour of day. A leap year's Feb 29 is dropped to stay on the model's
    fixed 8760-hour clock.

    Args:
        path: The ``productionandcurtailmentsdata_<year>.xlsx`` workbook.

    Returns:
        A tuple ``(wind, solar, last_month)`` where ``wind`` and ``solar``
        are ``(HOURS_PER_YEAR,)`` hourly-average curtailed MW and
        ``last_month`` is the latest 1-based month with any rows (12 means
        the sheet spans the full year).

    Raises:
        AssertionError: if an Hour or Interval value falls outside the
            1-24 / 1-12 ranges the mapping assumes.
    """
    df = pd.read_excel(
        path,
        sheet_name="Curtailments",
        usecols=["Date", "Hour", "Interval", "Wind Curtailment", "Solar Curtailment"],
    )
    df = df.dropna(subset=["Date"])
    dates = pd.to_datetime(df["Date"])
    month = dates.dt.month.to_numpy()
    day = dates.dt.day.to_numpy()
    hour = pd.to_numeric(df["Hour"]).to_numpy(dtype=int)
    interval = pd.to_numeric(df["Interval"]).to_numpy(dtype=int)
    assert hour.min() >= 1 and hour.max() <= 24, (
        f"{path.name}: Hour outside 1-24 ({hour.min()}..{hour.max()})"
    )
    assert interval.min() >= 1 and interval.max() <= INTERVALS_PER_HOUR, (
        f"{path.name}: Interval outside 1-{INTERVALS_PER_HOUR}"
    )

    last_month = int(month.max())
    keep = ~((month == 2) & (day == 29))
    month, day, hour = month[keep], day[keep], hour[keep]
    hoy = np.array(_MONTH_START_HOUR)[month - 1] + (day - 1) * 24 + (hour - 1)

    out = {}
    for column in ("Wind Curtailment", "Solar Curtailment"):
        mw = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
        series = np.zeros(HOURS_PER_YEAR, dtype=float)
        np.add.at(series, hoy, mw.to_numpy(dtype=float)[keep])
        out[column] = series / INTERVALS_PER_HOUR
    return out["Wind Curtailment"], out["Solar Curtailment"], last_month


def build_year(year: int, path: Path) -> pd.DataFrame | None:
    """Assemble one year's hourly GEN/HSL frame, or ``None`` when not buildable.

    ``None`` (with a printed data-needed marker) when the curtailment sheet
    does not span the full year or no full-year EIA-930 delivered series is
    available — the renewable loader then keeps its delivered-profile
    fallback for the year rather than consuming a fabricated potential.
    """
    wind_curt, solar_curt, last_month = load_reported_curtailment_hourly(path)
    if last_month < 12:
        print(
            f"SKIP {year}: curtailment sheet ends in month {last_month} — "
            "building a full-year HSL would fabricate zero curtailment for "
            "the uncovered months. DATA NEEDED: upload CAISO's full-year "
            f"productionandcurtailmentsdata_{year}.xlsx."
        )
        return None
    delivered = load_eia_hourly_renewable_gen("CAISO", year)
    if delivered is None or not {"wind", "solar"} <= set(delivered):
        print(
            f"SKIP {year}: no full-year EIA-930 'CISO hourly' wind/solar "
            "series to anchor the delivered side."
        )
        return None
    return pd.DataFrame(
        {
            "hour": np.arange(HOURS_PER_YEAR, dtype="int64"),
            "wind_gen_mw": delivered["wind"],
            "wind_hsl_mw": delivered["wind"] + wind_curt,
            "solar_gen_mw": delivered["solar"],
            "solar_hsl_mw": delivered["solar"] + solar_curt,
        }
    )


def print_validation(year: int, df: pd.DataFrame) -> None:
    """Print annual totals and the monthly curtailment shape for one year."""
    print(f"\n=== CAISO {year} uncurtailed renewable potential ===")
    print(f"Rows: {len(df)} (expected {HOURS_PER_YEAR})")
    for fuel in ("wind", "solar"):
        gen = df[f"{fuel}_gen_mw"]
        hsl = df[f"{fuel}_hsl_mw"]
        curt_twh = (hsl.sum() - gen.sum()) / 1e6
        curt_pct = 100.0 * (1.0 - gen.sum() / hsl.sum())
        print(
            f"\n{fuel.capitalize()}:"
            f"\n  delivered (EIA-930)  = {gen.sum() / 1e6:7.2f} TWh"
            f"\n  uncurtailed (HSL)    = {hsl.sum() / 1e6:7.2f} TWh"
            f"\n  reported curtailment = {curt_twh:7.3f} TWh"
            f"  ({curt_pct:.2f}% of potential)"
        )

    month_of_hour = np.repeat(np.arange(1, 13), np.array(_MONTH_DAYS) * 24)
    print("\nMonthly reported curtailment (GWh):")
    print(f"  {'month':>5} {'wind':>8} {'solar':>8}")
    for month in range(1, 13):
        m = df[month_of_hour == month]
        w = (m["wind_hsl_mw"].sum() - m["wind_gen_mw"].sum()) / 1e3
        s = (m["solar_hsl_mw"].sum() - m["solar_gen_mw"].sum()) / 1e3
        print(f"  {month:>5} {w:>8.1f} {s:>8.1f}")


def main() -> None:
    """Build every coverable year's CAISO HSL parquet from the workbooks."""
    workbooks = sorted(RAW_DIR.glob("productionandcurtailmentsdata_*.xlsx"))
    if not workbooks:
        print(f"No CAISO curtailment workbooks under {RAW_DIR}")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in workbooks:
        year = int(path.stem.rsplit("_", 1)[1])
        df = build_year(year, path)
        if df is None:
            continue
        print_validation(year, df)
        table = pa.Table.from_pandas(df, preserve_index=False)
        table = table.replace_schema_metadata(
            {
                "source": (
                    "CAISO Production and Curtailments data (5-minute) + "
                    "EIA-930 CISO hourly delivered generation"
                ),
                "description": (
                    "CAISO system-wide hourly wind/solar uncurtailed "
                    "potential (delivered + reported curtailment, the HSL "
                    "analogue) and delivered generation."
                ),
                "units": ("MW (hourly-average; numerically equal to MWh per hour)"),
                "year": str(year),
            }
        )
        out_file = OUT_DIR / f"caiso_{year}_hsl_hourly.parquet"
        pq.write_table(table, out_file)
        print(
            f"\nWrote {out_file.relative_to(REPO_ROOT)} "
            f"({out_file.stat().st_size / 1024:.1f} KiB)"
        )


if __name__ == "__main__":
    sys.exit(main())
