"""Derive the ``load-forecast-error`` clean datatype (lane UC-1-FIX-7, frozen derive, rule 23).

The forward half of the UC commitment demand
(``ScenarioConfig.uc_commitment_demand_source = "da_forecast"`` in forecast
mode; owner ruling UC-DESK r13, 2026-10-15): each ISO's measured day-ahead
load-forecast error, ``(DF - actual) / actual``, averaged by meteorological
season x local hour of day over every complete year of its EIA-930 BA
extract, on the ISO's own forecast-error basis
(:func:`market_sim.data.commitment_demand.forecast_error_basis`; lane
UC-DA-BASIS, owner rulings R17, R19): SPP's DF is its MTLF vintage in force at
the DA-RUC (``load-forecast-vintages``, so its profile pools the years with an
intaked vintage partition, 2019-2025), CAISO's actual is net of battery
charging; every other ISO is the EIA-930 DF vs metered Demand. Hours failing
the data-QA cut (``COMMITMENT_DF_DATA_ERROR_FRACTION``;
a missing forecast) are excluded by the same
:func:`market_sim.data.commitment_demand.qa_forecast_error` the backcast path
applies, and the frame is the same filled frame the demand loader reads, so
the forward profile and the backcast series are one measurement.

Schema: ``data/dictionary/schema/load-forecast-error.schema.yaml``. One
partition per ISO, ``data/clean/load-forecast-error/<ISO>/`` (``year=None``),
through :func:`scripts.lib.clean_io.write_clean`. Reads only ``data/raw``;
idempotent; re-run only when the EIA-930 extract or the SPP vintage intake
updates, or an owner ruling changes an ISO's basis definition (the commit
cites the data change).

Usage:
    PYTHONPATH=. .venv/bin/python scripts/data/derive_load_forecast_error.py --isos SPP
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data import eia930
from market_sim.data.commitment_demand import (
    FORECAST_ERROR_DATATYPE,
    MissingForecastVintages,
    forecast_and_actual_mw,
    forecast_error_basis,
    model_hour_season_hod,
    qa_forecast_error,
)
from scripts.lib import clean_io

#: The ISOs whose solve demand rides an EIA-930 hourly frame (the demand
#: loader's own BA map, ``eia930.frames._ISO_TO_HOURLY_BA``).
ISOS: tuple[str, ...] = tuple(sorted(eia930._ISO_TO_HOURLY_BA))

#: EIA-930 hourly data begins 2015-07-01 (EIA Form 930 launch), so 2015 is
#: the first year scanned; an incomplete year is rejected by the frame loader.
FIRST_SCAN_YEAR = 2015


def load_registry() -> tuple[str, ...]:
    """The partition ISOs this derive can build (``clean_profiles`` resolver)."""
    return ISOS


def _years_with_frames(ba: str, last_year: int) -> list[int]:
    """Complete years the BA's filled frame returns, ``FIRST_SCAN_YEAR..last_year``."""
    return [
        y
        for y in range(FIRST_SCAN_YEAR, last_year + 1)
        if eia930._eia_hourly_frame_filled(ba, y) is not None
    ]


def derive_iso(iso: str, last_year: int) -> pd.DataFrame:
    """The ISO's (season x hour) error profile; empty when no year has a forecast."""
    ba = eia930._ISO_TO_HOURLY_BA[iso]
    season, hod = model_hour_season_hod()
    parts: list[pd.DataFrame] = []
    years: list[int] = []
    for y in _years_with_frames(ba, last_year):
        try:
            forecast, actual = forecast_and_actual_mw(iso, y)
        except MissingForecastVintages:
            continue  # SPP: a year before its MTLF vintage intake (2019)
        except ValueError:
            continue  # no 'Demand forecast' column in this year's extract
        err, valid = qa_forecast_error(forecast, actual)
        if not valid.any():
            continue
        years.append(y)
        parts.append(
            pd.DataFrame(
                {
                    "season": season[valid],
                    "hour_of_day": hod[valid],
                    "rel": err[valid] / actual[valid],
                    "err": err[valid],
                }
            )
        )
    if not parts:
        return pd.DataFrame()
    pooled = pd.concat(parts, ignore_index=True)
    out = (
        pooled.groupby(["season", "hour_of_day"], as_index=False)
        .agg(
            bias_frac=("rel", "mean"),
            mean_error_mw=("err", "mean"),
            n_hours=("rel", "size"),
        )
        .sort_values(["season", "hour_of_day"], ignore_index=True)
    )
    out["season"] = out["season"].astype("string")
    out["hour_of_day"] = out["hour_of_day"].astype("int64")
    out["n_hours"] = out["n_hours"].astype("int64")
    out["ba"] = pd.Series([ba] * len(out), dtype="string")
    out["basis"] = pd.Series(
        [forecast_error_basis(iso).label] * len(out), dtype="string"
    )
    out["years"] = pd.Series([f"{min(years)}-{max(years)}"] * len(out), dtype="string")
    return out


def curate(
    isos: Iterable[str] | None = None, last_year: int | None = None
) -> list[Path]:
    """Derive and write every requested ISO's partition; returns the paths written."""
    last = int(last_year) if last_year is not None else pd.Timestamp.now().year
    wanted = [s.upper() for s in isos] if isos else list(ISOS)
    written: list[Path] = []
    for iso in wanted:
        if iso not in ISOS:
            raise SystemExit(f"{iso}: no EIA-930 hourly BA frame registered")
        frame = derive_iso(iso, last)
        if frame.empty:
            print(f"  {iso}: no year with a day-ahead forecast — skipped")
            continue
        out = clean_io.write_clean(
            frame,
            FORECAST_ERROR_DATATYPE,
            iso=iso,
            source=(
                f"data/raw/eia-930-hourly ({frame['ba'].iloc[0]}) "
                f"{frame['years'].iloc[0]} via scripts/data/derive_load_forecast_error.py"
            ),
        )
        clean_io.validate_clean(out)
        print(
            f"  {iso}: {len(frame)} cells, years {frame['years'].iloc[0]}, "
            f"mean bias {float(np.average(frame['bias_frac'], weights=frame['n_hours'])):+.4f} -> {out}"
        )
        written.append(out)
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI entry: ``--isos`` subset (default every registered ISO)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="*", default=None, help="ISO subset (default: all)")
    ap.add_argument(
        "--last-year",
        type=int,
        default=None,
        help="Last year scanned (default: this year)",
    )
    args = ap.parse_args(argv)
    written = curate(isos=args.isos, last_year=args.last_year)
    print(f"wrote {len(written)} partition(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
