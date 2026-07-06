"""Shared builder for the ``nyiso-downstate-gas`` clean datatype.

Builds the daily delivered-gas index a non-firm downstate NYISO gas peaker
faces (see ``data/dictionary/schema/nyiso-downstate-gas.schema.yaml`` and the
free-data memo §1.4, ``docs/handoffs/free-data-sourcing-2026-07.md``):

    delivered_gas[day] = transco_z6_ny[day]      (measured pipeline-hub daily spot)
                       + ldc_premium[month]       (measured monthly LDC city-gate premium)

Every input is a measured, forward-native market/tariff series (rule-13
admissible); nothing is fitted to a price or volume residual. The one place the
construction lives, imported by both ``scripts/curate_nyiso_downstate_gas.py``
(to write clean Parquet) and the model reader
(``src/market_sim/data/nyiso_downstate_gas.py``, as a raw fallback when the
clean partition is absent) so the daily series is identical either way.

Per-ISO input specs live in :data:`REGISTRY` keyed by ISO — shared code never
branches on the ISO name (``docs/adding-new-data-types.md``). Only NYISO has a
downstate LDC-island peaker construct today; a second ISO is a new
:class:`DownstateGasSpec` entry, additive.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

DATATYPE = "nyiso-downstate-gas"

# Canonical clean column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "date",
    "henry_hub_usd_per_mmbtu",
    "transco_z6_ny_usd_per_mmbtu",
    "ldc_premium_usd_per_mmbtu",
    "delivered_gas_usd_per_mmbtu",
)


@dataclass(frozen=True)
class DownstateGasSpec:
    """One ISO's downstate delivered-gas input file layout (all under data/raw).

    Attributes:
        iso: ISO identifier written into the clean frame.
        hub_daily_file: CSV of the pipeline-hub daily spot the peakers price off
            (columns ``date`` + ``hub_daily_col``).
        hub_daily_col: Column in ``hub_daily_file`` carrying the hub $/MMBtu.
        hh_daily_file: EIA Henry Hub daily spot CSV (``date, price_usd_mmbtu``),
            carried as a provenance component.
        premium_monthly_file: Monthly LDC city-gate premium CSV
            (``year, month, premium_usd_mmbtu``, floored 0).
    """

    iso: str
    hub_daily_file: str
    hub_daily_col: str
    hh_daily_file: str
    premium_monthly_file: str


# Registry: ISO -> input spec. NYISO is the only downstate-LDC-island market.
REGISTRY: dict[str, DownstateGasSpec] = {
    "NYISO": DownstateGasSpec(
        iso="NYISO",
        hub_daily_file="gas-prices/transco_z6_ny_daily.csv",
        hub_daily_col="transco_z6_ny_usd_mmbtu",
        hh_daily_file="gas-prices/henry_hub_daily.csv",
        premium_monthly_file="gas-prices/nyiso_downstate_ct_gas_basis_monthly.csv",
    ),
}


def _daily_series(frame: pd.DataFrame, value_col: str) -> pd.Series:
    """Return a date-indexed float Series of measured prints, sorted, deduped."""
    sub = frame[["date", value_col]].dropna()
    sub = sub.assign(date=pd.to_datetime(sub["date"]))
    sub = sub.sort_values("date").drop_duplicates("date", keep="last")
    return pd.Series(
        sub[value_col].astype(float).to_numpy(), index=pd.DatetimeIndex(sub["date"])
    )


def _interp_to_calendar(prints: pd.Series, year: int) -> pd.Series:
    """Interpolate sparse trading-day prints onto every calendar day of ``year``.

    Linear interpolation between measured prints, forward/back-filled at the
    year edges — the same gap-fill the daily fuel overlays use for non-trading
    days. Returns a Series indexed by every day in ``year``.
    """
    cal = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    # Union the print index (which may hold prior/later-year context) then
    # interpolate on the time axis so gaps near Jan/Dec resolve from real
    # neighbouring prints before the calendar restriction.
    union = prints.reindex(prints.index.union(cal)).sort_index()
    filled = union.interpolate(method="time").ffill().bfill()
    return filled.reindex(cal)


def _premium_by_month(
    spec: DownstateGasSpec, raw_root: Path, year: int
) -> dict[int, float]:
    """Return ``{month: ldc_premium_$/MMBtu}`` for ``year`` from the monthly file."""
    frame = pd.read_csv(raw_root / spec.premium_monthly_file)
    sub = frame[frame["year"] == year]
    return {int(r.month): float(r.premium_usd_mmbtu) for r in sub.itertuples()}


def build_daily_frame(iso: str, year: int, raw_root: Path) -> pd.DataFrame:
    """Build the schema-shaped daily delivered-gas frame for one ISO-year.

    Reads only ``data/raw`` (via the ISO's :class:`DownstateGasSpec`), returns a
    frame with :data:`CANONICAL_COLUMNS` — one row per calendar day of ``year``.
    Non-trading days are interpolated; the monthly LDC premium is broadcast to
    every day of its month. ``delivered_gas = transco_z6_ny + ldc_premium``.

    Raises:
        KeyError: ``iso`` has no registered spec.
        ValueError: the hub daily file has no prints overlapping ``year``.
    """
    spec = REGISTRY[iso]
    hub_raw = pd.read_csv(raw_root / spec.hub_daily_file)
    hub_prints = _daily_series(hub_raw, spec.hub_daily_col)
    if hub_prints.empty or hub_prints.index.year.isin([year]).sum() == 0:
        raise ValueError(
            f"{spec.hub_daily_file} has no {spec.hub_daily_col} prints for {year}"
        )
    hh_raw = pd.read_csv(raw_root / spec.hh_daily_file)
    hh_prints = _daily_series(hh_raw, "price_usd_mmbtu")

    hub_daily = _interp_to_calendar(hub_prints, year)
    hh_daily = _interp_to_calendar(hh_prints, year)
    premium = _premium_by_month(spec, raw_root, year)

    cal = hub_daily.index
    ldc = pd.Series([premium.get(d.month, 0.0) for d in cal], index=cal)
    delivered = hub_daily + ldc

    return pd.DataFrame(
        {
            "iso": iso,
            "date": cal.values.astype("datetime64[ns]"),
            "henry_hub_usd_per_mmbtu": hh_daily.to_numpy().round(4),
            "transco_z6_ny_usd_per_mmbtu": hub_daily.to_numpy().round(4),
            "ldc_premium_usd_per_mmbtu": ldc.to_numpy().round(4),
            "delivered_gas_usd_per_mmbtu": delivered.to_numpy().round(4),
        },
        columns=list(CANONICAL_COLUMNS),
    )
