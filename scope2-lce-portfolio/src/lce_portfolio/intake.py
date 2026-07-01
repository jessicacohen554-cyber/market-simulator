"""Load and LMP intake: ingestion, aggregation, growth, and zonal reconciliation.

The tool accepts an 8760 load dataset that may be facility-level and/or
multi-ISO. This module collapses it to one hourly vector per ISO (summing
facilities within an hour and ISO), then optionally applies a compound
load-growth factor. It also reads the BAU LMP file the portfolio LP prices
against. The aggregation rule, growth application, and LMP contract are
decided in ``docs/decisions/0010-load-intake-growth.md`` (ADR 0010) and
``docs/decisions/0011-lmp-coupling-scenario-selection.md`` (ADR 0011); this
module is their implementation.

Calendar convention (ADR 0010): every hourly vector is indexed ``0..8759``,
local standard time, non-leap year (a single representative year — no DST,
no leap day). Load and LMP files must share this convention; both are
validated for full coverage of the 8760-hour calendar. **Missing hours are a
hard error**, not a zero-fill — a silently zero-filled hour would understate
load/price without warning.

Accepted load-intake schema (CSV or Parquet), long form:
    hour     : int in [0, 8759]
    iso      : str
    load_mwh : float
    facility : str (optional; summed away by aggregation)

Accepted LMP schema (CSV or Parquet), long form (ADR 0011 export contract):
    hour : int in [0, 8759]
    iso  : str
    lmp  : float ($/MWh)

The LMP file is expected to be the calibrated market-sim **forecast-year**
BAU export for the modeled year (ADR 0011); this module never applies price
escalation and never reads market-sim files directly — it only consumes the
DataFrames/file paths handed to it, so the tool stays a price-taker with no
``market_sim`` module coupling.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig


def _read_table(path: str | Path) -> pd.DataFrame:
    """Read a CSV or Parquet file by extension (``.parquet`` vs. everything else)."""
    path = Path(path)
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    return pd.read_csv(path)


def _validate_hour_range(df: pd.DataFrame) -> None:
    """Raise if ``hour`` is not an integer in ``[0, 8759]``."""
    if df["hour"].min() < 0 or df["hour"].max() >= HOURS_PER_YEAR:
        raise ValueError("hour column must be integers in [0, 8759]")


def _check_no_duplicates(df: pd.DataFrame, key_cols: list[str], context: str) -> None:
    """Raise if any combination of ``key_cols`` repeats, naming one example."""
    dup_mask = df.duplicated(subset=key_cols, keep=False)
    if dup_mask.any():
        example = df.loc[dup_mask, key_cols].iloc[0].to_dict()
        n_dup = int(dup_mask.sum())
        raise ValueError(
            f"{context}: {n_dup} duplicate row(s) on {key_cols}, e.g. {example}"
        )


def _require_full_calendar(present_hours: set[int], iso: str, kind: str) -> None:
    """Raise unless ``present_hours`` covers exactly ``0..8759``.

    The error names the ISO, the count of missing hours, and one example
    missing index, per ADR 0010 (missing hours are an error, not a zero-fill).
    """
    missing = sorted(set(range(HOURS_PER_YEAR)) - present_hours)
    if missing:
        raise ValueError(
            f"{kind} for iso {iso!r} is missing {len(missing)} of {HOURS_PER_YEAR} "
            f"hour(s) (local standard time, non-leap calendar), "
            f"e.g. missing hour {missing[0]}"
        )


def load_intake(path: str | Path) -> pd.DataFrame:
    """Read a load-intake file (``.csv`` or ``.parquet``) into a long DataFrame.

    Requires columns ``hour``, ``iso``, ``load_mwh`` (``facility`` optional).
    ``hour`` must be an integer in ``[0, 8759]``.
    """
    df = _read_table(path)

    required = {"hour", "iso", "load_mwh"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"intake file missing columns: {sorted(missing)}")
    _validate_hour_range(df)
    return df


def aggregate_by_hour_iso(df: pd.DataFrame) -> dict[str, np.ndarray]:
    """Aggregate a long intake DataFrame to ``{iso: load[8760]}``.

    Sums ``load_mwh`` across facilities within each (iso, hour) (ADR 0010:
    aggregate-then-match). A repeated ``(facility, hour)`` row within an ISO
    (or a repeated ``(iso, hour)`` row when ``facility`` is absent) is a data
    error, not a legitimate second facility, and is rejected. Every ISO must
    cover the full ``0..8759`` calendar after aggregation; a missing hour
    raises rather than silently zero-filling.
    """
    key_cols = (
        ["iso", "facility", "hour"] if "facility" in df.columns else ["iso", "hour"]
    )
    _check_no_duplicates(df, key_cols, context="load intake")

    grouped = df.groupby(["iso", "hour"], as_index=False)["load_mwh"].sum()
    out: dict[str, np.ndarray] = {}
    for iso, sub in grouped.groupby("iso"):
        iso = str(iso)
        present = set(sub["hour"].astype(int))
        _require_full_calendar(present, iso, kind="load intake")
        vec = np.zeros(HOURS_PER_YEAR, dtype=float)
        vec[sub["hour"].to_numpy()] = sub["load_mwh"].to_numpy()
        out[iso] = vec
    return out


def apply_load_growth(load: np.ndarray, rate: float, years: int) -> np.ndarray:
    """Scale an 8760 load vector by a compound growth factor ``(1+rate)**years``.

    A single uniform multiplier (shape-preserving). Shape-shifting growth
    (e.g. electrification changing the load curve) is deferred past ADR 0010.
    """
    if years < 0:
        raise ValueError("load_growth_years must be non-negative")
    if rate <= -1.0:
        raise ValueError(f"load_growth_rate must be > -1.0, got {rate}")
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


def lmp_intake(path: str | Path) -> pd.DataFrame:
    """Read an LMP file (``.csv`` or ``.parquet``) into a long DataFrame.

    Requires columns ``hour``, ``iso``, ``lmp`` (ADR 0011 export contract:
    one row per ISO-hour, already reconciled to a single per-ISO price — see
    :func:`collapse_zonal_lmp` if the source export is still zonal).
    """
    df = _read_table(path)

    required = {"hour", "iso", "lmp"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"LMP file missing columns: {sorted(missing)}")
    _validate_hour_range(df)
    return df


def prepare_lmp(path: str | Path, iso: str) -> np.ndarray:
    """End-to-end LMP intake for one ISO: read, validate, return an 8760 vector.

    Applies the same validation standard as :func:`prepare_load`: a
    duplicated ``(iso, hour)`` row and a missing hour both raise (naming the
    ISO, the count, and an example) rather than being silently resolved. No
    price escalation is applied (ADR 0011) — the returned series is the LMP
    vintage in the file, as-is.
    """
    df = lmp_intake(path)
    sub = df[df["iso"] == iso]
    if sub.empty:
        raise KeyError(
            f"ISO {iso!r} not present in LMP file; have {sorted(df['iso'].unique())}"
        )

    _check_no_duplicates(sub, ["iso", "hour"], context="LMP intake")
    present = set(sub["hour"].astype(int))
    _require_full_calendar(present, iso, kind="LMP intake")
    return sub.sort_values("hour")["lmp"].to_numpy(dtype=float)


def collapse_zonal_lmp(
    zonal_lmp_df: pd.DataFrame, zonal_load_df: pd.DataFrame
) -> pd.DataFrame:
    """Collapse zonal LMPs to one per-ISO hourly price (ADR 0011 reconciliation seam).

    This is the seam for reconciling a market-sim zonal export down to the
    single-node-per-ISO price this tool consumes; it reads only the
    DataFrames handed to it (never a market-sim file directly). Per
    ``(iso, hour)``, the result is the **load-weighted average** of
    ``zonal_lmp_df["lmp"]`` across zones, weighted by ``zonal_load_df["load_mwh"]``
    for that same ``(iso, hour, zone)``. If total zonal load in an
    ``(iso, hour)`` is zero, the weighted average is undefined, so that hour
    falls back to the simple (unweighted) mean of the zonal LMPs.

    Parameters
    ----------
    zonal_lmp_df : columns ``(hour, iso, zone, lmp)``
    zonal_load_df : columns ``(hour, iso, zone, load_mwh)``

    Returns
    -------
    DataFrame with columns ``(hour, iso, lmp)`` — the ADR 0011 export
    contract, ready for :func:`prepare_lmp` (a zone present in the LMP file
    with no matching load row is excluded from that hour's average).
    """
    merged = zonal_lmp_df.merge(zonal_load_df, on=["hour", "iso", "zone"], how="inner")
    merged["_weighted"] = merged["lmp"] * merged["load_mwh"]
    grouped = merged.groupby(["iso", "hour"], as_index=False).agg(
        _weighted_sum=("_weighted", "sum"),
        _load_sum=("load_mwh", "sum"),
        _lmp_mean=("lmp", "mean"),
    )
    grouped["lmp"] = np.where(
        grouped["_load_sum"] > 0,
        grouped["_weighted_sum"] / grouped["_load_sum"],
        grouped["_lmp_mean"],
    )
    return (
        grouped[["iso", "hour", "lmp"]]
        .sort_values(["iso", "hour"])
        .reset_index(drop=True)
    )
