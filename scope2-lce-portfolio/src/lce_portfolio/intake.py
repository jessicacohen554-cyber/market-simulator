"""Load-intake ingestion, aggregation, and growth scaling.

The tool accepts an 8760 load dataset that may be facility-level and/or
multi-ISO. This module collapses it to one hourly vector per ISO (summing
facilities within an hour and ISO), then optionally applies a compound
load-growth factor. The aggregation rule and growth application are finalized in
``docs/planning-sessions/PS-07``; this implementation is the minimal default.

Accepted input schema (CSV or Parquet), long form:
    hour   : int in [0, 8759]      (or a timestamp column, see load_intake)
    iso    : str
    load_mwh : float
    facility : str (optional; summed away by aggregation)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig


def load_intake(path: str | Path) -> pd.DataFrame:
    """Read a load-intake file (``.csv`` or ``.parquet``) into a long DataFrame.

    Requires columns ``hour``, ``iso``, ``load_mwh`` (``facility`` optional).
    ``hour`` must be an integer in ``[0, 8759]``.
    """
    path = Path(path)
    if path.suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path)

    required = {"hour", "iso", "load_mwh"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"intake file missing columns: {sorted(missing)}")
    if df["hour"].min() < 0 or df["hour"].max() >= HOURS_PER_YEAR:
        raise ValueError("hour column must be integers in [0, 8759]")
    return df


def aggregate_by_hour_iso(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Aggregate a long intake DataFrame to ``{iso: load[8760]}``.

    Sums ``load_mwh`` across facilities within each (iso, hour). Hours with no
    rows are filled with zero. Returns a dict keyed by ISO name.
    """
    grouped = df.groupby(["iso", "hour"], as_index=False)["load_mwh"].sum()
    out: dict[str, np.ndarray] = {}
    for iso, sub in grouped.groupby("iso"):
        vec = np.zeros(HOURS_PER_YEAR, dtype=float)
        vec[sub["hour"].to_numpy()] = sub["load_mwh"].to_numpy()
        out[str(iso)] = vec
    return out


def apply_load_growth(load: np.ndarray, rate: float, years: int) -> np.ndarray:
    """Scale an 8760 load vector by a compound growth factor ``(1+rate)**years``.

    A single uniform multiplier (shape-preserving). Shape-shifting growth
    (e.g. electrification changing the load curve) is a PS-07 decision.
    """
    if years < 0:
        raise ValueError("load_growth_years must be non-negative")
    return load * (1.0 + rate) ** years


def prepare_load(
    path: str | Path,
    iso: str,
    config: PortfolioConfig,
) -> np.ndarray:
    """End-to-end intake for one ISO: read, aggregate, apply growth.

    Returns the final 8760 hourly load vector (MWh) for ``iso``.
    """
    df = load_intake(path)
    by_iso = aggregate_by_hour_iso(df)
    if iso not in by_iso:
        raise KeyError(f"ISO {iso!r} not present in intake; have {sorted(by_iso)}")
    return apply_load_growth(
        by_iso[iso], config.load_growth_rate, config.load_growth_years
    )
