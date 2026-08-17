"""ERCOT-98 measurement probe: attribute the 2023 scarcity-tail miss.

Reproduces every measured comparison behind
``docs/DIAGNOSIS-ercot-2023-summer-tail-attribution-2026-07.md`` from a
keeper bundle's committed hourly sidecars plus committed raw actuals — no
LP solve. Sections:

  [1] Baseline: actual RT>-threshold tail vs the bundle's demand-weighted hub
      price — caught / missed / phantom hour sets, by month and hour-of-day.
  [2] Reserve reality at the missed hours: measured RTORPA / PRC / SCED
      system lambda (NP6-905 curation) — is the miss reserve-priced or
      offer-priced in reality?
  [3] Physical balance at the missed hours: model gas/coal/nuclear/RE/demand
      vs EIA-930 ERCO actuals (fuel-type extract, UTC->CST).
  [4] Zonal deliverability: model zonal price spread vs actual RT LZ spread
      (RTMLZHBSPP workbook, CPT->CST) on the named event days, plus
      West+Panhandle wind delivered-vs-COP-potential from the zonal HSL
      sidecar (curtailment at the event evenings).
  [5] AS-plan named-day check: the co-opt requirement path
      (``ercot_as_plan_requirement_mw``) vs the raw ASPLANNP433 rows —
      level fidelity (duplicate-posting dedup) and clock placement.

Usage:
    python -m scripts.probes.ercot98_tail_attribution_measure \\
        [--bundle results/calibration/ercot97_plant_grain_fullspan] [--year 2023]

Diagnostic only; never registered. Reads committed inputs only.
"""

from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

TAIL_THRESHOLD = 200.0  # rubric §5 ERCOT scarcity threshold, $/MWh
NAMED_DAYS = ("2023-08-17", "2023-08-30", "2023-09-06")
EVENING = slice(16, 21)  # CST hours 16-20, the event-evening window


def _hub_price(bundle: Path, year: int) -> tuple[pd.Series, pd.DataFrame]:
    """Demand-weighted hub price + the P1 system frame from a bundle."""
    sysdf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    p1 = sysdf[sysdf["pass"] == "P1"]
    price = p1.pivot(index="hour", columns="zone", values="price")
    demand = p1.pivot(index="hour", columns="zone", values="demand")
    return (price * demand).sum(axis=1) / demand.sum(axis=1), p1


def _actual_rt(year: int) -> pd.Series:
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    return lmp[lmp["year"] == year].set_index("hour")["rt"]


def _model_calendar(year: int) -> pd.DatetimeIndex:
    """Real CST hour-beginning stamps for the model's fixed non-leap clock.

    Rule 8 ``[R-8760]``: every model year is 8760 hours, so a LEAP year skips
    Feb 29 (the same fact the ercot-214 probe's ``MONTH_DAYS`` table encodes).
    A naive ``date_range(periods=8760)`` therefore mis-dates every model hour
    from March 1 on by -24 h in 2024, which mis-joins that year's actuals
    entirely. Repaired 2026-08-17 (ercot-216).
    """
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    hours = np.arange(8760)
    offset = hours + (24 * (hours >= 1416) if leap else 0)  # 1416 h = Jan 1-Feb 28
    return pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(offset, unit="h")


def _eia930_by_fuel(year: int, calendar: pd.DatetimeIndex) -> pd.DataFrame:
    """EIA-930 ERCO net generation on the model's hour index.

    Clock (repaired 2026-08-17, ercot-216; measured, not assumed — the probe
    ``ercot216_c3c_lane_phase0.py`` §5 correlates model demand against the 930
    generation sum at four offsets and reads 1.00000 / 0.99933 / 0.94335 at
    +1 h for 2023/2024/2025, the maximum in every year): EIA-930's ``period``
    is the hour-**ENDING** stamp, while the model's hour index is hour-
    **beginning** CST, so model hour ``h`` joins the CST stamp ``h + 1``.
    Joining them naively lags the actuals one hour, which at a steep evening
    ramp is a GW-scale error (2023 missed-hour reads moved gas -349 -> -1,412
    and renewables -1,771 -> +504 MW on repair).
    """
    eia = pd.read_parquet(REPO / "data/raw/ERCO_fueltype.parquet")
    ts = (
        pd.to_datetime(eia["period"], utc=True)
        .dt.tz_convert("Etc/GMT+6")  # fixed UTC-6 == CST, the fleet clock
        .dt.tz_localize(None)
    )
    frame = eia.assign(ts=ts)
    piv = frame[frame["ts"].dt.year.isin([year, year + 1])].pivot_table(
        index="ts", columns="fueltype", values="value_mwh", aggfunc="sum"
    )
    for col in ("BAT", "OTH", "WAT", "SUN", "WND"):
        if col not in piv:
            piv[col] = 0.0
    piv = piv.reindex(calendar + pd.Timedelta(hours=1))
    out = pd.DataFrame(
        {
            "gas": piv["NG"],
            "coal": piv["COL"],
            "nuc": piv["NUC"],
            "re": piv["SUN"] + piv["WND"],
            "bat": piv["BAT"],
            "other": piv["OTH"] + piv["WAT"],
        }
    ).fillna(0.0)
    out.index = np.arange(len(calendar))
    return out


def _actual_lz_hourly(months: tuple[str, ...] = ("Jul", "Aug", "Sep")) -> pd.DataFrame:
    """Hourly-mean actual RT settlement point prices (CPT HE index)."""
    with zipfile.ZipFile(REPO / "data/raw/lmp-data/RTMLZHBSPP_2023.zip") as zf:
        with zf.open(zf.namelist()[0]) as fh:
            book = pd.ExcelFile(io.BytesIO(fh.read()))
    frame = pd.concat([book.parse(m) for m in months], ignore_index=True)
    points = ["LZ_WEST", "LZ_NORTH", "LZ_HOUSTON", "LZ_SOUTH", "HB_PAN", "HB_BUSAVG"]
    frame = frame[frame["Settlement Point Name"].isin(points)]
    hourly = (
        frame.groupby(["Delivery Date", "Delivery Hour", "Settlement Point Name"])[
            "Settlement Point Price"
        ]
        .mean()
        .reset_index()
    )
    return hourly.pivot_table(
        index=["Delivery Date", "Delivery Hour"],
        columns="Settlement Point Name",
        values="Settlement Point Price",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ercot98_tail_attribution_measure")
    parser.add_argument(
        "--bundle",
        default="results/calibration/ercot97_plant_grain_fullspan",
        help="keeper bundle with committed hourly/ sidecars",
    )
    parser.add_argument("--year", type=int, default=2023)
    args = parser.parse_args(argv)

    bundle = REPO / args.bundle
    year = args.year
    calendar = _model_calendar(year)

    hub, p1 = _hub_price(bundle, year)
    rt = _actual_rt(year)
    tail = rt > TAIL_THRESHOLD
    caught = (tail & (hub > TAIL_THRESHOLD)).to_numpy()
    missed = (tail & (hub <= TAIL_THRESHOLD)).to_numpy()
    phantom = (~tail & (hub > TAIL_THRESHOLD)).to_numpy()

    print(f"[1] actual RT>{TAIL_THRESHOLD:.0f}: {int(tail.sum())} h | model "
          f"caught {caught.sum()} | missed {missed.sum()} | phantom {phantom.sum()}")
    for label, mask in (("missed", missed), ("caught", caught)):
        months = pd.Series(calendar.month[mask]).value_counts().sort_index()
        print(f"    {label} by month: {months.to_dict()}")

    ordc = pd.read_parquet(
        REPO / f"data/raw/ercot/ercot_{year}_ordc_reserves_hourly.parquet"
    ).set_index("hour")
    for label, mask in (("missed", missed), ("caught", caught)):
        sub = ordc.iloc[mask.nonzero()[0]]
        lam = sub["system_lambda"]
        share = (lam > 0.8 * rt.to_numpy()[mask]).mean()
        print(
            f"[2] {label}: RTORPA p50 ${sub['rtorpa'].median():.1f} "
            f"(max ${sub['rtorpa'].max():.0f}) | PRC p50 {sub['prc'].median():.0f} MW "
            f"| lambda p50 ${lam.median():.0f} | lambda>0.8*RT share {share:.0%}"
        )

    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    klass = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    klass = klass.fillna(0.0)
    gas_klasses = ["CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS"]
    model = pd.DataFrame(
        {
            "gas": klass[[k for k in gas_klasses if k in klass]].sum(axis=1),
            "coal": klass[["COAL_LIGNITE", "COAL_PRB"]].sum(axis=1),
            "nuc": klass["nuclear"],
            "re": klass["wind"] + klass["solar"],
            "dem": p1.pivot(index="hour", columns="zone", values="demand").sum(axis=1),
        }
    )
    actual = _eia930_by_fuel(year, calendar)
    print("[3] missed-hour physical balance, mean MW (model - actual):")
    sub_m, sub_a = model[missed], actual[missed]
    for col in ("gas", "coal", "nuc", "re"):
        print(
            f"    {col:>4}: model {sub_m[col].mean():7.0f} vs actual "
            f"{sub_a[col].mean():7.0f} -> {sub_m[col].mean() - sub_a[col].mean():+6.0f}"
        )
    gen_sum = sub_a.sum(axis=1).mean()
    print(f"    dem : model {sub_m['dem'].mean():7.0f} vs actual gen-sum "
          f"{gen_sum:7.0f} -> {sub_m['dem'].mean() - gen_sum:+6.0f}")

    zonal_path = REPO / f"data/raw/ercot-hsl/ercot_{year}_hsl_zonal_hourly.parquet"
    price = p1.pivot(index="hour", columns="zone", values="price")
    spread = price.max(axis=1) - price.min(axis=1)
    tail_rows = tail.to_numpy().nonzero()[0]
    print(
        f"[4] model zonal spread on the {len(tail_rows)} tail hours: "
        f"p50 ${spread.iloc[tail_rows].median():.1f} max ${spread.iloc[tail_rows].max():.1f}"
    )
    lz = _actual_lz_hourly()
    lz_spread = (
        lz[["LZ_WEST", "LZ_NORTH", "LZ_HOUSTON", "LZ_SOUTH"]].max(axis=1)
        - lz[["LZ_WEST", "LZ_NORTH", "LZ_HOUSTON", "LZ_SOUTH"]].min(axis=1)
    )
    print(
        f"    actual RT LZ spread (Jul-Sep, all hours): p50 ${lz_spread.median():.1f} "
        f"p90 ${lz_spread.quantile(0.9):.1f} max ${lz_spread.max():.1f}"
    )
    if zonal_path.exists():
        zonal = pd.read_parquet(zonal_path)
        wind = zonal[zonal["fuel"] == "wind"]
        gen = wind.pivot(index="hour", columns="region", values="gen_mw")
        hsl = wind.pivot(index="hour", columns="region", values="hsl_mw")
        if {"west", "panhandle"}.issubset(gen.columns):
            for day in NAMED_DAYS:
                rows = (
                    (calendar >= day)
                    & (calendar < pd.Timestamp(day) + pd.Timedelta(days=1))
                ).nonzero()[0][EVENING]
                delivered = gen[["west", "panhandle"]].iloc[rows].sum(axis=1)
                potential = hsl[["west", "panhandle"]].iloc[rows].sum(axis=1)
                curtailed = (potential - delivered).round(0).tolist()
                print(f"    {day} h16-20 W+P wind curtailed MW: {curtailed}")

    from market_sim.results.scarcity import ercot_as_plan_requirement_mw

    asplan = pd.read_parquet(REPO / f"data/raw/ercot/ASPLANNP433_{year}.parquet")
    ecrs = ercot_as_plan_requirement_mw(year, 8760, "ECRS")
    for day in NAMED_DAYS:
        rows = (
            (calendar >= day) & (calendar < pd.Timestamp(day) + pd.Timedelta(days=1))
        ).nonzero()[0][EVENING]
        raw = asplan[
            (asplan["DeliveryDate"] == pd.Timestamp(day).strftime("%m/%d/%Y"))
            & (asplan["AncillaryType"] == "ECRS")
        ]
        he = raw["HourEnding"].str.slice(0, 2).astype(int)
        # CPT HE h+2 covers CST hour-beginning h in the DST window.
        raw_cst = raw.assign(h=he - 2).groupby("h")["Quantity"].mean()
        expect = raw_cst.reindex(range(16, 21)).to_numpy()
        got = ecrs[rows]
        tag = "OK" if np.allclose(got, expect, equal_nan=True) else "MISMATCH"
        print(f"[5] {day} ECRS loader vs raw (CST h16-20): {tag} "
              f"loader {got.round(0).tolist()} raw {np.round(expect, 0).tolist()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
