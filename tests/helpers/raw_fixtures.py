"""Per-source raw-fixture writers.

The suite carries ~79 ad-hoc ``_write_*`` fixture builders. This module homes
the genuinely reusable ones — the raw source shapes that more than one test
needs — so a new curation/loader test writes ``write_eia860(dir, ...)`` instead
of re-deriving the column names. Each writer returns the path(s) it wrote.

These are deliberately *minimal* shapes: just the columns the loaders read.
Source-specific one-offs (a single curation script's bespoke sheet) stay local
to their test file; promote one here only when a second caller appears.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def write_parquet(df: pd.DataFrame, path: str | Path) -> Path:
    """Write ``df`` to ``path`` as index-less Parquet, making parents."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    """Write ``df`` to ``path`` as index-less CSV, making parents."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def write_eia860(
    data_dir: str | Path,
    generators: pd.DataFrame | None = None,
    plants: pd.DataFrame | None = None,
    solar: pd.DataFrame | None = None,
    wind: pd.DataFrame | None = None,
) -> dict[str, Path]:
    """Write a minimal EIA-860 vintage directory (generator + plant [+ RE]).

    Column shapes match what the fleet / build-throughput loaders read:
    ``eia860_generator_operable.parquet`` (Plant Code, Nameplate Capacity (MW),
    Energy Source 1, Prime Mover, Operating Year), ``eia860_plant.parquet``
    (Plant Code, Balancing Authority Code), and — when given — the
    ``eia860_solar_operable`` / ``eia860_wind_operable`` sheets (Plant Code,
    Nameplate Capacity (MW), Operating Year).

    Passing ``None`` for a frame writes a small default; pass a DataFrame to
    control the rows. Returns ``{sheet: path}`` for what was written.
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    if generators is None:
        generators = pd.DataFrame(
            {
                "Plant Code": [100, 200],
                "Nameplate Capacity (MW)": [500.0, 250.0],
                "Energy Source 1": ["NG", "NG"],
                "Prime Mover": ["CA", "GT"],
                "Operating Year": [2021, 2022],
            }
        )
    if plants is None:
        plants = pd.DataFrame(
            {
                "Plant Code": [100, 200],
                "Balancing Authority Code": ["ERCO", "ERCO"],
            }
        )

    written = {
        "generator": write_parquet(
            generators, data_dir / "eia860_generator_operable.parquet"
        ),
        "plant": write_parquet(plants, data_dir / "eia860_plant.parquet"),
    }
    if solar is not None:
        written["solar"] = write_parquet(
            solar, data_dir / "eia860_solar_operable.parquet"
        )
    if wind is not None:
        written["wind"] = write_parquet(wind, data_dir / "eia860_wind_operable.parquet")
    return written


def campd_unit_extract(
    facility_id: str = "1001",
    year: int = 2023,
    state: str = "TX",
) -> pd.DataFrame:
    """Return a tiny raw CAMPD unit-level frame: two days, one unit.

    Mirrors the CAMPD API extract shape the loader parses (date/hour grid,
    grossLoad, heatInput, so2/co2/nox mass columns). Day 1 starts off then runs
    from hour 6; day 2 runs all 24 hours.
    """
    dates = pd.to_datetime([f"{year}-01-01"] * 24 + [f"{year}-01-02"] * 24)
    hours = list(range(24)) * 2
    gross = np.concatenate([np.zeros(6), np.full(18, 100.0), np.full(24, 100.0)])
    return pd.DataFrame(
        {
            "stateCode": state,
            "facilityName": "Test Plant",
            "facilityId": facility_id,
            "date": dates,
            "hour": hours,
            "grossLoad": gross,
            "steamLoad": np.nan,
            "so2Mass": np.where(gross > 0, 2.0, 0.0),
            "co2Mass": np.where(gross > 0, 60.0, 0.0),
            "noxMass": np.where(gross > 0, 1.0, 0.0),
            "heatInput": np.where(gross > 0, 1000.0, 0.0),
        }
    )


def eia930_hourly(
    ba: str = "ERCO",
    start: str = "2024-03-01 00:00",
    hours: int = 3,
) -> pd.DataFrame:
    """Return a tiny EIA-930 hourly frame (Demand + wind/solar generation).

    The shape ``curate_load`` / the EIA-930 loaders read: a UTC timestamp
    column, ``Demand``, ``Demand forecast`` and the ``NG: WND`` / ``NG: SUN``
    generation columns. ``ba`` is carried for the caller to name the file
    (``f"{ba} hourly.parquet"``).
    """
    ts = pd.to_datetime(pd.date_range(start, periods=hours, freq="h"))
    base = 500.0 + 100.0 * np.arange(hours)
    return pd.DataFrame(
        {
            "UTC time": ts,
            "Demand": base,
            "Demand forecast": base + 10.0,
            "NG: WND": 50.0 + 10.0 * np.arange(hours),
            "NG: SUN": 20.0 + 5.0 * np.arange(hours),
        }
    )
