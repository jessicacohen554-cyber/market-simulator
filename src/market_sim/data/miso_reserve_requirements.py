"""Measured MISO hourly operating-reserve requirement series (Lane-2, miso-56).

The condition-varying requirement channel for the MISO in-LP energy+reserve
co-optimization (``config.reserve_config._miso_design``), the MISO analogue of
the NYISO issue-#1344 intake (``data.nyiso_reserve_requirements``): when
``ScenarioConfig.miso_measured_reserve_requirements`` is on, the market-wide
RBDC family's flat fleet-MSSC + regulating estimate and the South zonal
family's static within-zone-MSSC estimate are replaced by the MEASURED hourly
reserve MW MISO actually cleared, from the masked real-time cleared-offers
market report (``data/raw/MISO-AS/asm_rt_cleared_mw_<year>.parquet``,
``scripts/fetch_miso_asm.py``).

The loader also emits a ``"MISO-Midwest"`` leg (cleared sum over the two
Midwest ASM regions {North, Central}) — the measured basis of the Midwest
sub-regional reserve-holding family (``ScenarioConfig.
miso_midwest_subregional_reserves``, the engagement-depth lane, miso-71). It is
the same measured-cleared construction, clock, and admissibility as the
market-wide and South legs; measured Midwest + measured South = measured
market by construction (the sum over regions IS the market leg).

Admissibility (CLAUDE.md rule #13): the cleared reserve MW is a measured
ancillary-service power reservation — a procurement *quantity*, never a
price — with a forward analogue: forecast years keep the existing
MSSC + regulating formula (the flag is backcast-only by construction, like
every measured overlay). Rule #14 makes the swap mandatory: the measured
series shows the flat market-wide estimate (fleet MSSC + 400 MW ≈ 3.4 GW)
overstates real procurement (~2.3-3.1 GW, hourly-varying with event-evening
increases), and the South static (within-zone MSSC ≈ 2.2 GW) overstates the
measured South reservation (~0.3-0.5 GW) several-fold — the within-zone-MSSC
reading of BPM-002 §3.3.2 fabricates ~1.8 GW of South withholding the real
market never held.

Known basis caveats (documented, not hidden):

* The series is *cleared* MW, not the requirement itself: in a genuine
  shortage interval cleared < requirement, so the requirement is understated
  in exactly those (rare — the IMM counts a handful of intervals per year)
  hours. MISO does not publish the historical hourly requirement series; the
  cleared series is the closest measured quantity. Quantified on the Midwest
  leg (miso-71 design §3): the cleared series dips to 957 MW (Jun-23/24-2025)
  and 851 MW (Jul-28/29-2025) against a ~2,165 MW 2025 mean — the deep-window
  event hours where cleared understates the true requirement. Any construction
  that undoes the dip (trailing-max smoothing, window-scoped floors) would be
  residual-fitting around a shortage and is refused (rules 1/13); the
  understatement is a ledgered lower-bound caveat, not "fixed" here.
* The report is real-time (the adopted basis). MISO DOES publish a day-ahead
  cleared-offers report at hourly grain (``YYYYMMDD_asm_da_co.zip``, per-unit
  RegMW/SpinMW/SuppMW/STRMW + MCPs by region, EST) — correcting the stale
  miso-56 caveat that claimed no hourly DA series exists. A DA-basis intake is
  a possible future refinement of the SAME cleared-basis family; the RT basis
  is retained as adopted (switching it is out of the miso-71 lane's scope — it
  would re-litigate miso-56 and change all three legs at once).
* Products summed are ``reg + spin + supp`` — the Market-wide Operating
  Reserve construct (regulating + contingency, BPM-002). Short-Term Reserve
  (``str``) is a separate 30-minute product outside the OR requirement and is
  deliberately excluded.

Clock: the source files are Hour-Ending 1-24, Eastern Standard Time
year-round (MISO market reports never observe DST) — the model's fixed
non-leap 8760 local-standard-time clock. A leap year's Feb 29 is dropped
(``data.eia_loader`` convention); small posting gaps (single missing
hours) are forward-filled and the loader hard-errors when coverage is
worse than ``_MAX_MISSING_HOURS``.
"""

from __future__ import annotations

import calendar
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

#: Source directory of the fetched ASM rollups (fetch_miso_asm.py).
MISO_AS_DIR: Path = RAW_DATA_DIR / "MISO-AS"

#: Products summed into the Market-wide Operating Reserve requirement
#: (regulating + contingency = reg + spin + supp; STR deliberately excluded —
#: a separate 30-minute product outside the OR construct).
OR_PRODUCTS: tuple[str, ...] = ("reg", "spin", "supp")

#: Model zone name of the MISO-South zonal reserve family
#: (reserve_config.MISO_ZONAL_RESERVE_DEFAULT_ZONES) and its source region
#: label in the cleared-offers report.
SOUTH_ZONE: str = "MISO-South"
SOUTH_REGION: str = "South"

#: The two ASM cleared-offers regions that make up the Midwest sub-region
#: (reserve_config.MISO_MIDWEST_ZONES): North + Central. The Midwest leg's
#: measured OR reservation is their cleared reg+spin+supp sum — the basis of
#: the miso_midwest_subregional_reserves family (miso-71 design §2a).
MIDWEST_REGIONS: tuple[str, ...] = ("North", "Central")
MIDWEST_ZONE: str = "MISO-Midwest"

#: Hard error above this many missing hours per series (posting gaps in the
#: source are 1-2 hours/year; anything larger is a data problem, not a gap).
_MAX_MISSING_HOURS: int = 168


def cleared_mw_path(year: int) -> Path:
    """Return the on-disk path of the cleared-reserve parquet for ``year``."""
    return MISO_AS_DIR / f"asm_rt_cleared_mw_{year}.parquet"


def _to_model_hour(dates: pd.Series, hour_end: pd.Series, year: int) -> np.ndarray:
    """Map (date, HE 1-24 EST) rows onto the fixed non-leap 8760 clock.

    Returns the hour-of-year index per row; a leap year's Feb 29 rows map to
    ``-1`` (dropped), matching the ``data.eia_loader`` non-leap convention.
    """
    ts = pd.to_datetime(dates)
    doy = ts.dt.dayofyear.to_numpy(dtype=int)
    if calendar.isleap(year):
        feb29 = (ts.dt.month == 2) & (ts.dt.day == 29)
        # Days after Feb 29 shift back one slot on the non-leap clock.
        doy = np.where(ts.dt.dayofyear.to_numpy() > 60, doy - 1, doy)
        doy = np.where(feb29.to_numpy(), 0, doy)  # sentinel, dropped below
    idx = (doy - 1) * 24 + (hour_end.to_numpy(dtype=int) - 1)
    if calendar.isleap(year):
        idx = np.where(feb29.to_numpy(), -1, idx)
    return idx


def load_miso_reserve_requirements(
    year: int,
    hours: int,
    path: Path | None = None,
) -> dict[str, np.ndarray]:
    """Load the measured hourly reserve series for ``year``.

    Args:
        year: Backcast year (the fleet-clock year the solve runs on).
        hours: LP horizon length T; each returned series covers exactly this
            many hours of the fixed non-leap clock.
        path: Optional explicit parquet path (tests); defaults to
            :func:`cleared_mw_path`.

    Returns:
        ``{"market": (hours,) array, "MISO-South": (hours,) array,
        "MISO-Midwest": (hours,) array}`` — the measured market-wide (all
        regions summed), South-region, and Midwest (North+Central summed) OR
        reservation MW (``reg + spin + supp``). By construction
        ``MISO-Midwest + MISO-South == market`` in every fully-covered hour.

    Raises:
        FileNotFoundError: The intake parquet is absent — the
            ``miso_measured_reserve_requirements`` flag hard-errors rather
            than silently reverting to the static estimates it replaces.
        ValueError: Missing columns/products, or coverage gaps larger than
            the posting-gap tolerance.
    """
    src = path if path is not None else cleared_mw_path(year)
    if not src.exists():
        raise FileNotFoundError(
            f"miso_measured_reserve_requirements=True but the measured cleared-"
            f"reserve series is absent: {src}. Regenerate with "
            f"scripts/fetch_miso_asm.py --years {year}; the flag must not solve "
            f"on the static estimates it claims to replace."
        )

    df = pd.read_parquet(src)
    required_cols = {"date", "hour_end_est", "region", "product", "cleared_mw"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"{src}: missing column(s) {sorted(missing)}; expected "
            f"{sorted(required_cols)}"
        )
    df = df[df["product"].isin(OR_PRODUCTS)].copy()
    if df.empty:
        raise ValueError(f"{src}: no OR product rows ({OR_PRODUCTS}) present")

    df["_hour"] = _to_model_hour(df["date"], df["hour_end_est"], year)
    df = df[df["_hour"] >= 0]  # drop a leap year's Feb 29

    out: dict[str, np.ndarray] = {}
    for key, sub in (
        ("market", df),
        (SOUTH_ZONE, df[df["region"] == SOUTH_REGION]),
        (MIDWEST_ZONE, df[df["region"].isin(MIDWEST_REGIONS)]),
    ):
        series = np.full(int(hours), np.nan)
        hourly = sub.groupby("_hour")["cleared_mw"].sum()
        idx = hourly.index.to_numpy(dtype=int)
        keep = idx < int(hours)
        series[idx[keep]] = hourly.to_numpy(dtype=float)[keep]
        n_missing = int(np.isnan(series).sum())
        if n_missing > _MAX_MISSING_HOURS:
            raise ValueError(
                f"{src}: {key} series missing {n_missing} hours "
                f"(> {_MAX_MISSING_HOURS} tolerance) — a present series must "
                f"cover the year up to posting gaps."
            )
        if n_missing:
            # Forward/backward fill single posting gaps (pandas limit-free
            # ffill then bfill for a leading gap) — documented tolerance.
            s = pd.Series(series).ffill().bfill()
            series = s.to_numpy(dtype=float)
        if not np.all(np.isfinite(series)) or np.any(series < 0):
            raise ValueError(f"{src}: {key} series non-finite or negative")
        out[key] = series
    return out
