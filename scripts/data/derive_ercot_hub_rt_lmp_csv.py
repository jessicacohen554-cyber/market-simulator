#!/usr/bin/env python3
"""Cut a per-settlement-point ERCOT real-time price CSV out of the raw archives.

Reads the committed ERCOT RTM Load-Zone-&-Hub Settlement Point Price archives
(``data/raw/lmp-data/**/RTMLZHBSPP_<year>.zip`` — one ``.xlsx`` per year, 12
monthly sheets, 15-minute prices in $/MWh) and writes, per year and per
settlement point, two human-facing CSVs:

* ``<POINT>_rt_15min_<year>.csv``  — the native 15-minute series, as published.
* ``<POINT>_rt_hourly_<year>.csv`` — the simple mean of the four intervals in
  each delivery hour, the same hourly convention
  ``scripts/data/derive_ercot_zonal_lmp.py`` uses for the validation parquet.

This is a hand-off extract, not a model input: it writes under
``paths.EXPORTS_DIR`` and nothing in ``src/market_sim/`` reads it. The
model's own ERCOT price series is the validation parquet that
``derive_ercot_zonal_lmp.py`` builds from these same zips.

**Published calendar, not the model's 8760 clock.** Unlike the validation
parquet — which drops Feb 29 and folds DST onto a fixed non-leap 8760-hour
grid — this export preserves ERCOT's own delivery calendar: a leap year keeps
Feb 29, the spring-forward delivery hour is absent, and the fall-back hour
appears twice, distinguished by ``Repeated Hour Flag``. That is what makes the
CSV a faithful copy of the source rather than a model-aligned one.

Usage::

    python3 scripts/data/derive_ercot_hub_rt_lmp_csv.py \
        --settlement-point HB_NORTH --years 2023 2024 2025
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import EXPORTS_DIR, LMP_DATA_DIR  # noqa: E402

#: ERCOT publishes real-time prices on 15-minute Settlement Point Price
#: intervals, four to a delivery hour (ERCOT Nodal Protocols §6.6.1).
MINUTES_PER_INTERVAL = 15
INTERVALS_PER_HOUR = 4

#: Default output tree; one subdirectory of ``EXPORTS_DIR`` per export family.
DEFAULT_OUT_DIR = EXPORTS_DIR / "ercot-hub-lmp"


def find_archive(year: int) -> Path:
    """Return the RTM archive for ``year``.

    The 2023-2025 archives sit at the ``lmp-data/`` top level and the
    2018-2022 + 2026 ones under ``lmp-data/ERCOT/``, so both are searched.
    """
    matches = sorted(LMP_DATA_DIR.glob(f"**/RTMLZHBSPP_{year}.zip"))
    if not matches:
        raise FileNotFoundError(
            f"no RTMLZHBSPP_{year}.zip under {LMP_DATA_DIR} — the ERCOT SPP "
            "archives are a manual ERCOT MIS download (see its README)"
        )
    return matches[0]


def load_intervals(year: int, settlement_point: str) -> pd.DataFrame:
    """Read one year's 15-minute series for ``settlement_point``."""
    archive = find_archive(year)
    with zipfile.ZipFile(archive) as z:
        sheets = pd.read_excel(
            io.BytesIO(z.read(z.namelist()[0])), engine="openpyxl", sheet_name=None
        )
    df = pd.concat(sheets.values(), ignore_index=True)
    df.columns = [c.strip() for c in df.columns]

    # Some RTM workbook vintages end in a fully-blank row, which makes the
    # hour cast raise IntCastingNaNError. A blank row carries no price, so
    # dropping it cannot change any year whose workbook is clean.
    df = df[df["Delivery Hour"].notna()]
    df = df[df["Settlement Point Name"] == settlement_point].copy()
    if df.empty:
        raise ValueError(
            f"{settlement_point} not present in {archive.name}; the workbook "
            f"carries {sorted(pd.concat(sheets.values())['Settlement Point Name'].unique())}"
        )

    df["delivery_date"] = pd.to_datetime(df["Delivery Date"]).dt.strftime("%Y-%m-%d")
    df["delivery_hour"] = df["Delivery Hour"].astype(int)  # hour ending, 1-24
    df["delivery_interval"] = df["Delivery Interval"].astype(int)  # 1-4 in hour
    df["repeated_hour_flag"] = df["Repeated Hour Flag"].astype(str).str.strip()
    df["settlement_point"] = settlement_point
    df["price_usd_per_mwh"] = df["Settlement Point Price"].astype(float)

    # Interval-ENDING local (Central Prevailing Time) stamp, as ERCOT labels
    # it: hour ending H, interval I ends (H-1)*60 + I*15 minutes after
    # midnight. On the fall-back day the repeated hour's two passes carry the
    # same stamp and are told apart by ``repeated_hour_flag``.
    minutes = (
        df["delivery_hour"] - 1
    ) * INTERVALS_PER_HOUR * MINUTES_PER_INTERVAL + df[
        "delivery_interval"
    ] * MINUTES_PER_INTERVAL
    df["interval_ending_cpt"] = (
        pd.to_datetime(df["delivery_date"]) + pd.to_timedelta(minutes, unit="m")
    ).dt.strftime("%Y-%m-%d %H:%M")

    df = df.sort_values(
        ["delivery_date", "delivery_hour", "repeated_hour_flag", "delivery_interval"],
        kind="stable",
    )
    return df[
        [
            "delivery_date",
            "delivery_hour",
            "delivery_interval",
            "interval_ending_cpt",
            "repeated_hour_flag",
            "settlement_point",
            "price_usd_per_mwh",
        ]
    ].reset_index(drop=True)


def to_hourly(intervals: pd.DataFrame) -> pd.DataFrame:
    """Average the 15-minute series onto delivery hours.

    ``n_intervals`` is carried so a reader can see at a glance that every hour
    is a full four-interval mean rather than a partial one.
    """
    keys = ["delivery_date", "delivery_hour", "repeated_hour_flag"]
    hourly = intervals.groupby(keys, as_index=False, sort=False).agg(
        price_usd_per_mwh=("price_usd_per_mwh", "mean"),
        n_intervals=("price_usd_per_mwh", "size"),
    )
    hourly["settlement_point"] = intervals["settlement_point"].iloc[0]
    hourly["hour_ending_cpt"] = (
        pd.to_datetime(hourly["delivery_date"])
        + pd.to_timedelta(hourly["delivery_hour"], unit="h")
    ).dt.strftime("%Y-%m-%d %H:%M")
    hourly["price_usd_per_mwh"] = hourly["price_usd_per_mwh"].round(4)
    return hourly[
        [
            "delivery_date",
            "delivery_hour",
            "hour_ending_cpt",
            "repeated_hour_flag",
            "settlement_point",
            "price_usd_per_mwh",
            "n_intervals",
        ]
    ]


def main() -> None:
    """Write the per-year and combined CSVs for one settlement point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--settlement-point",
        default="HB_NORTH",
        help="ERCOT settlement point name, e.g. HB_NORTH (the North hub, "
        "quoted as 'ERCOTN' in the trade press) or LZ_HOUSTON",
    )
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    point = args.settlement_point
    args.out_dir.mkdir(parents=True, exist_ok=True)

    every_interval, every_hour = [], []
    for year in args.years:
        intervals = load_intervals(year, point)
        hourly = to_hourly(intervals)
        intervals.to_csv(
            args.out_dir / f"ERCOT_{point}_rt_15min_{year}.csv", index=False
        )
        hourly.to_csv(args.out_dir / f"ERCOT_{point}_rt_hourly_{year}.csv", index=False)
        every_interval.append(intervals)
        every_hour.append(hourly)
        print(
            f"{year}: {len(intervals):>6} intervals -> {len(hourly):>5} hours | "
            f"mean ${hourly.price_usd_per_mwh.mean():8.2f} | "
            f"min ${intervals.price_usd_per_mwh.min():9.2f} | "
            f"max ${intervals.price_usd_per_mwh.max():9.2f} | "
            f"days {intervals.delivery_date.nunique()}"
        )

    if len(args.years) > 1:
        span = f"{min(args.years)}-{max(args.years)}"
        pd.concat(every_interval, ignore_index=True).to_csv(
            args.out_dir / f"ERCOT_{point}_rt_15min_{span}.csv", index=False
        )
        pd.concat(every_hour, ignore_index=True).to_csv(
            args.out_dir / f"ERCOT_{point}_rt_hourly_{span}.csv", index=False
        )
    print(f"wrote {args.out_dir}")


if __name__ == "__main__":
    main()
