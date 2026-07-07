"""Shared builder for the ``nyiso-downstate-gas`` clean datatype (schema v2, per zone).

Builds the daily delivered-gas index a non-firm downstate NYISO gas peaker faces,
per downstate zone (see ``data/dictionary/schema/nyiso-downstate-gas.schema.yaml``):

    delivered_gas[zone][day] = transco_z6_ny[day]              (measured pipeline-hub daily spot)
                             + ldc_transport_adder[zone][month] (measured LDC non-firm transport rate)

The peakers are interruptible TRANSPORTATION customers: they buy their commodity
at the market hub (Transco Zone 6 NY daily spot, captures cold-snap blowouts on
the exact days they run) and pay their local LDC a **non-firm transportation
delivery charge** to move it from the city gate to the plant. That delivery rate
is the measured "Total Monthly Tier 1 Transportation Service" rate each downstate
LDC publishes every month (KEDNY SC-22 for NYC zone J, KEDLI SC-19 for Long
Island zone K; ``data/raw/gas-prices/nyiso_downstate_ldc_transport_monthly.csv``,
see the sidecar ``SOURCES_nyiso_downstate_ldc_transport.md``). Every input is a
measured, forward-native market/tariff series (rule-13 admissible); nothing is
fitted to a price or volume residual.

v2 (per-zone LDC transport adder) supersedes v1 (a single statewide EIA-N3050NY3
firm-citygate premium): the interruptible peakers are transport customers, so the
LDC transport rate is their correct delivered-fuel boundary, and the LI gas island
(KEDLI) and NYC system (KEDNY) carry materially different delivery costs
(CLAUDE.md rules #11/#12; gap register G-13).

The one place the construction lives, imported by both
``scripts/curate_nyiso_downstate_gas.py`` (to write clean Parquet) and the model
reader (``src/market_sim/data/nyiso_downstate_gas.py``, as a raw fallback when the
clean partition is absent) so the daily series is identical either way.

Per-ISO input specs live in :data:`REGISTRY` keyed by ISO — shared code never
branches on the ISO name (``docs/adding-new-data-types.md``). Only NYISO has a
downstate LDC-island peaker construct today; a second ISO is a new
:class:`DownstateGasSpec` entry, additive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

DATATYPE = "nyiso-downstate-gas"

# Canonical clean column order (matches the schema key + value columns).
CANONICAL_COLUMNS: tuple[str, ...] = (
    "iso",
    "zone",
    "date",
    "henry_hub_usd_per_mmbtu",
    "transco_z6_ny_usd_per_mmbtu",
    "ldc_transport_adder_usd_per_mmbtu",
    "delivered_gas_usd_per_mmbtu",
)


@dataclass(frozen=True)
class DownstateGasSpec:
    """One ISO's downstate delivered-gas input file layout (all under data/raw).

    Attributes:
        iso: ISO identifier written into the clean frame.
        hub_daily_file: CSV of the pipeline-hub daily spot the peakers price their
            commodity off (columns ``date`` + ``hub_daily_col``).
        hub_daily_col: Column in ``hub_daily_file`` carrying the hub $/MMBtu.
        hh_daily_file: EIA Henry Hub daily spot CSV (``date, price_usd_mmbtu``),
            carried as a provenance component.
        transport_monthly_file: Monthly per-LDC non-firm transportation delivery
            rate CSV (``ldc, zone, year, month, rate_usd_per_mmbtu``).
        zone_ldc: Map of model downstate zone -> the LDC whose transport rate it
            takes (e.g. ``{"NYC": "KEDNY", "Long_Island": "KEDLI"}``).
    """

    iso: str
    hub_daily_file: str
    hub_daily_col: str
    hh_daily_file: str
    transport_monthly_file: str
    zone_ldc: dict[str, str] = field(default_factory=dict)


# Registry: ISO -> input spec. NYISO is the only downstate-LDC-island market.
REGISTRY: dict[str, DownstateGasSpec] = {
    "NYISO": DownstateGasSpec(
        iso="NYISO",
        hub_daily_file="gas-prices/transco_z6_ny_daily.csv",
        hub_daily_col="transco_z6_ny_usd_mmbtu",
        hh_daily_file="gas-prices/henry_hub_daily.csv",
        transport_monthly_file="gas-prices/nyiso_downstate_ldc_transport_monthly.csv",
        zone_ldc={"NYC": "KEDNY", "Long_Island": "KEDLI"},
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


def _transport_by_month(
    spec: DownstateGasSpec, raw_root: Path, ldc: str, year: int
) -> dict[int, float]:
    """Return ``{month: transport_adder_$/MMBtu}`` for one LDC-year."""
    frame = pd.read_csv(raw_root / spec.transport_monthly_file)
    sub = frame[(frame["ldc"] == ldc) & (frame["year"] == year)]
    return {int(r.month): float(r.rate_usd_per_mmbtu) for r in sub.itertuples()}


def build_daily_frame(iso: str, year: int, raw_root: Path) -> pd.DataFrame:
    """Build the schema-shaped daily delivered-gas frame for one ISO-year.

    Reads only ``data/raw`` (via the ISO's :class:`DownstateGasSpec`), returns a
    frame with :data:`CANONICAL_COLUMNS` — one row per (downstate zone, calendar
    day of ``year``). Non-trading days are interpolated; the monthly LDC
    transport adder is broadcast to every day of its month.
    ``delivered_gas = transco_z6_ny + ldc_transport_adder``.

    Raises:
        KeyError: ``iso`` has no registered spec.
        ValueError: the hub daily file has no prints overlapping ``year``, or a
            zone's LDC has no transport rows for ``year``.
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
    cal = hub_daily.index

    frames: list[pd.DataFrame] = []
    for zone, ldc in spec.zone_ldc.items():
        transport = _transport_by_month(spec, raw_root, ldc, year)
        if not transport:
            raise ValueError(
                f"{spec.transport_monthly_file} has no {ldc} rows for {year}"
            )
        adder = pd.Series([transport.get(d.month, 0.0) for d in cal], index=cal)
        delivered = hub_daily + adder
        frames.append(
            pd.DataFrame(
                {
                    "iso": iso,
                    "zone": zone,
                    "date": cal.values.astype("datetime64[ns]"),
                    "henry_hub_usd_per_mmbtu": hh_daily.to_numpy().round(4),
                    "transco_z6_ny_usd_per_mmbtu": hub_daily.to_numpy().round(4),
                    "ldc_transport_adder_usd_per_mmbtu": adder.to_numpy().round(4),
                    "delivered_gas_usd_per_mmbtu": delivered.to_numpy().round(4),
                },
                columns=list(CANONICAL_COLUMNS),
            )
        )
    return pd.concat(frames, ignore_index=True)
