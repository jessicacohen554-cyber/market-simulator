"""EPA CAMPD (CEMS) hourly emissions and gross-generation loader.

The uploaded ``inputs/raw-data/{STATE}_{YEAR}.parquet`` files are EPA Clean
Air Markets Program Data hourly extracts, one row per
``(facility, unit-hour)`` with columns:

* ``facilityId`` — the ORISPL / EIA plant code (a string), which joins to
  the EIA-923 ``plant_id`` and the master registry ``plantid``.
* ``grossLoad`` — gross electrical output for the hour, MW (≈ MWh/h).
* ``steamLoad`` — process-steam load, 1000 lb/hr (CHP host steam).
* ``co2Mass`` — CO2 mass, **short tons**.
* ``so2Mass`` / ``noxMass`` — SO2 / NOx mass, **pounds**.
* ``heatInput`` — fuel heat input, MMBtu.

This module is ISO-agnostic. It loads the raw extracts, normalizes units to
kg, builds an 8760-hour calendar index aligned with the model's dispatch
clock (Feb 29 is dropped, matching ``run_calibration_full._hour_to_month``),
and exposes the three derivations the calibration pipeline needs:

* :func:`annual_plant_totals` — annual gross/heat/emissions per plant, the
  numerator/denominator inputs to the parasitic-load and emission-rate work.
* :func:`compute_parasitic_factors` — given annual CAMPD gross and EIA-923
  net generation per plant, the net/gross scale factor used to convert
  measured gross output to net output.
* :func:`plant_emission_rates` — per-plant kg CO2/NOx/SO2 per MWh **net**,
  marginal/no-load decomposition, and start/stop emission factors.
* :func:`plant_hourly_net` — per-plant 8760-hour **net** generation series,
  the observed benchmark for the per-plant hourly dispatch correlation.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Default location of the raw CAMPD state-year extracts.
RAW_DATA_DIR: Path = Path(__file__).parents[3] / "inputs" / "raw-data"

# Unit conversions to kilograms (the canonical mass unit for derived rates).
SHORT_TON_TO_KG: float = 907.18474
LB_TO_KG: float = 0.45359237
# The dispatch model carries emission rates in metric tonnes per MWh and
# prices in $/tonne; divide kg by this to reach the model's internal unit.
KG_PER_TONNE: float = 1000.0

# Hours in the model's fixed (non-leap) dispatch calendar.
HOURS_PER_YEAR: int = 8760
_DAYS_IN_MONTH: tuple[int, ...] = (
    31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
)
# Cumulative hours before the first of each 1-based month, non-leap calendar.
_MONTH_START_HOUR: tuple[int, ...] = tuple(
    int(sum(_DAYS_IN_MONTH[:m]) * 24) for m in range(12)
)

# States feeding each ISO, for the convenience ISO → state lookup. ERCOT is
# approximated by Texas (the EIA-923 ``ERCO`` balancing-authority footprint);
# extend as more ISOs are calibrated.
ISO_STATES: dict[str, tuple[str, ...]] = {
    "ERCOT": ("TX",),
    "CAISO": ("CA",),
    "NYISO": ("NY",),
    "ISONE": ("ME", "NH", "MA", "CT", "RI", "VT"),
    "PJM": ("PA", "NJ", "MD", "DE", "IL"),
    "MISO": ("IL",),
    "SPP": (),
}

# EIA-923 ``fuel_type`` codes burned by coal-class units.
_COAL_EIA_FUELS: frozenset[str] = frozenset(
    {"SUB", "BIT", "LIG", "ANT", "RC", "WC", "SC"}
)

# EIA-923 ``fuel_type`` codes that are NOT stack-monitored combustion fuels,
# excluded when summing the net generation that CAMPD's gross output should
# reconcile against (renewables, nuclear, hydro, storage, purchases).
_NON_COMBUSTION_FUELS: frozenset[str] = frozenset({
    "WND", "SUN", "WAT", "NUC", "MWH", "GEO", "PUR", "OTH", "WH", "HPS",
})

# Plausible band for a net/gross parasitic factor. Outside this, the CAMPD
# gross and EIA-923 net almost certainly cover different unit sets at the
# plant; such plants fall back to a class default.
_PARASITIC_MIN: float = 0.80
_PARASITIC_MAX: float = 1.00

# Class-default parasitic-load fractions (1 − net/gross) keyed by the
# registry ``plant_group``, used when a plant's measured factor is missing
# or implausible. Sources: EPRI / EIA station-service typicals by technology.
DEFAULT_PARASITIC_LOAD_PCT: dict[str, float] = {
    "COAL": 0.070,
    "ST_GAS": 0.050,
    "ST_CHP": 0.050,
    "CC_REGULAR": 0.025,
    "CC_CHP": 0.025,
    "CT_PEAKER": 0.010,
    "CT_CHP": 0.010,
    "OTHER": 0.030,
}
# Fallback when even the plant_group is unknown.
_DEFAULT_PARASITIC_LOAD_PCT: float = 0.03

# Minimum gross load (MW) treated as "online" when detecting start/stop
# events, to ignore sensor noise around zero.
_ONLINE_MW: float = 1.0

# EPA default CO2 emission factor for natural gas, kg CO2 per MMBtu (117.0
# lb/MMBtu). Used to backfill CO2 mass for units that report NOx and heat
# input but not CO2 — common for gas peakers in CEMS. A plant that reports
# CO2 for *some* hours is instead backfilled at its own measured intensity.
DEFAULT_CO2_KG_PER_MMBTU: float = 53.06


def states_for_iso(iso: str) -> tuple[str, ...]:
    """Return the CAMPD state codes feeding an ISO (see :data:`ISO_STATES`)."""
    return ISO_STATES.get(iso.upper(), ())


def _hour_index_8760(month: np.ndarray, day: np.ndarray, hour: np.ndarray) -> np.ndarray:
    """Map ``(month, day, hour)`` to a non-leap hour-of-year index.

    Returns an int array in ``[0, 8760)``; Feb 29 maps to ``-1`` so callers
    can drop it, keeping the CAMPD clock aligned with the model's fixed
    8760-hour calendar.
    """
    month = np.asarray(month, dtype=int)
    day = np.asarray(day, dtype=int)
    hour = np.asarray(hour, dtype=int)
    base = np.array(_MONTH_START_HOUR, dtype=int)[month - 1]
    idx = base + (day - 1) * 24 + hour
    leap_day = (month == 2) & (day == 29)
    idx = np.where(leap_day, -1, idx)
    return idx


def _read_one(state: str, year: int, raw_dir: Path) -> pd.DataFrame | None:
    """Load and normalize one ``{STATE}_{YEAR}.parquet`` extract, or ``None``."""
    path = raw_dir / f"{state}_{year}.parquet"
    if not path.exists():
        logger.warning("CAMPD extract not found: %s", path)
        return None
    raw = pd.read_parquet(path)
    out = pd.DataFrame({
        "plant_id": pd.to_numeric(raw["facilityId"], errors="coerce"),
        "facility_name": raw["facilityName"].astype(str),
        "state": raw["stateCode"].astype(str),
        "year": np.int16(year),
        "date": pd.to_datetime(raw["date"]),
        "hour": pd.to_numeric(raw["hour"], errors="coerce").astype("Int64"),
        "gross_mw": pd.to_numeric(raw["grossLoad"], errors="coerce"),
        "steam_load": pd.to_numeric(raw["steamLoad"], errors="coerce"),
        "co2_kg": pd.to_numeric(raw["co2Mass"], errors="coerce") * SHORT_TON_TO_KG,
        "nox_kg": pd.to_numeric(raw["noxMass"], errors="coerce") * LB_TO_KG,
        "so2_kg": pd.to_numeric(raw["so2Mass"], errors="coerce") * LB_TO_KG,
        "heat_mmbtu": pd.to_numeric(raw["heatInput"], errors="coerce"),
    })
    out = out.dropna(subset=["plant_id", "hour"])
    out["plant_id"] = out["plant_id"].astype(int)
    out["hour"] = out["hour"].astype(int)
    return out


def load_campd_hourly(
    states: list[str] | tuple[str, ...],
    years: list[int] | tuple[int, ...],
    raw_dir: str | Path | None = None,
) -> pd.DataFrame:
    """Load and normalize CAMPD hourly extracts for states and years.

    Args:
        states: CAMPD ``stateCode`` values, e.g. ``["TX"]`` for ERCOT.
        years: Calendar years, e.g. ``[2023, 2024, 2025]``.
        raw_dir: Directory holding ``{STATE}_{YEAR}.parquet``; ``None`` uses
            :data:`RAW_DATA_DIR`.

    Returns:
        One row per ``(plant, unit-hour)`` with masses in kg, gross load in
        MW, heat input in MMBtu, plus an ``hour_of_year`` column in
        ``[0, 8760)`` (Feb 29 rows are dropped). Empty when no extract is
        found.
    """
    base = Path(raw_dir) if raw_dir is not None else RAW_DATA_DIR
    frames = [
        df
        for state in states
        for year in years
        if (df := _read_one(state, int(year), base)) is not None
    ]
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    idx = _hour_index_8760(df["date"].dt.month, df["date"].dt.day, df["hour"])
    df["hour_of_year"] = idx
    return df[idx >= 0].reset_index(drop=True)


def annual_plant_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Return annual gross / heat / emissions per ``(plant_id, year)``.

    Args:
        df: A frame from :func:`load_campd_hourly`.

    Returns:
        One row per ``(plant_id, year)`` with ``gross_mwh`` (sum of hourly
        gross MW), ``heat_mmbtu``, ``co2_kg``, ``nox_kg``, ``so2_kg``,
        ``op_hours`` (hours with gross load > 0) and ``facility_name``.
    """
    if df.empty:
        return pd.DataFrame()
    g = df.groupby(["plant_id", "year"], observed=True)
    out = g.agg(
        gross_mwh=("gross_mw", "sum"),
        heat_mmbtu=("heat_mmbtu", "sum"),
        co2_kg=("co2_kg", "sum"),
        nox_kg=("nox_kg", "sum"),
        so2_kg=("so2_kg", "sum"),
        facility_name=("facility_name", "first"),
    ).reset_index()
    op = (
        df[df["gross_mw"] > 0.0]
        .groupby(["plant_id", "year"], observed=True)["gross_mw"]
        .size()
        .rename("op_hours")
        .reset_index()
    )
    return out.merge(op, on=["plant_id", "year"], how="left").fillna(
        {"op_hours": 0}
    )


def compute_parasitic_factors(
    campd_annual: pd.DataFrame,
    eia923_net_by_plant_year: pd.DataFrame,
    plant_groups: dict[int, str] | None = None,
) -> pd.DataFrame:
    """Reconcile CAMPD gross against EIA-923 net to get parasitic factors.

    The parasitic-load factor is annual net generation divided by annual
    gross generation — the fraction of gross output delivered after station
    service. The dispatch model and the hourly correlation use it to scale
    CAMPD's measured gross down to net.

    Per ``(plant_id, year)`` the factor is ``net/gross``; a plant's pooled
    factor sums net and gross across years before dividing, so high-output
    years dominate. Factors outside :data:`_PARASITIC_MIN`..\
    :data:`_PARASITIC_MAX` (where the gross and net unit sets clearly differ)
    are flagged and replaced by the plant-group class default from
    :data:`DEFAULT_PARASITIC_LOAD_PCT`.

    Args:
        campd_annual: Output of :func:`annual_plant_totals`.
        eia923_net_by_plant_year: Columns ``plant_id``, ``year`` and
            ``net_mwh`` — EIA-923 net generation summed over the plant's
            combustion units (see :func:`eia923_combustion_net`).
        plant_groups: Optional ``{plant_id: plant_group}`` for class-default
            fallback.

    Returns:
        One row per ``(plant_id, year)`` plus a pooled ``year == 0`` summary
        row per plant, with ``gross_mwh``, ``net_mwh``, ``parasitic_factor``
        (net/gross, used for scaling), ``parasitic_load_pct`` (``1 −
        factor``), ``source`` (``measured`` / ``class_default``) and
        ``flag``.
    """
    groups = plant_groups or {}
    merged = campd_annual.merge(
        eia923_net_by_plant_year, on=["plant_id", "year"], how="left"
    )
    rows: list[dict] = []

    def _resolve(plant_id: int, gross: float, net: float) -> dict:
        raw = net / gross if gross > 0.0 and net > 0.0 else float("nan")
        group = groups.get(int(plant_id), "")
        if np.isnan(raw) or raw < _PARASITIC_MIN or raw > _PARASITIC_MAX:
            pct = DEFAULT_PARASITIC_LOAD_PCT.get(
                group, _DEFAULT_PARASITIC_LOAD_PCT
            )
            factor = 1.0 - pct
            source = "class_default"
            flag = "no_net" if np.isnan(raw) else "out_of_band"
        else:
            factor = raw
            pct = 1.0 - factor
            source = "measured"
            flag = "ok"
        return {
            "gross_mwh": round(float(gross), 3),
            "net_mwh": round(float(net), 3) if net == net else 0.0,
            "parasitic_factor": round(float(factor), 6),
            "parasitic_load_pct": round(float(pct), 6),
            "source": source,
            "flag": flag,
        }

    for _, r in merged.iterrows():
        rec = {"plant_id": int(r["plant_id"]), "year": int(r["year"])}
        rec.update(_resolve(r["plant_id"], r["gross_mwh"], r.get("net_mwh", np.nan)))
        rows.append(rec)

    # Pooled per-plant factor (year == 0): sum net and gross across years.
    pooled = merged.groupby("plant_id", observed=True).agg(
        gross_mwh=("gross_mwh", "sum"), net_mwh=("net_mwh", "sum")
    )
    for plant_id, p in pooled.iterrows():
        rec = {"plant_id": int(plant_id), "year": 0}
        rec.update(_resolve(plant_id, p["gross_mwh"], p["net_mwh"]))
        rows.append(rec)

    cols = [
        "plant_id", "year", "gross_mwh", "net_mwh", "parasitic_factor",
        "parasitic_load_pct", "source", "flag",
    ]
    return pd.DataFrame(rows, columns=cols).sort_values(
        ["plant_id", "year"]
    ).reset_index(drop=True)


def pooled_factor_map(parasitic: pd.DataFrame) -> dict[int, float]:
    """Return ``{plant_id: parasitic_factor}`` from the pooled (year 0) rows."""
    pooled = parasitic[parasitic["year"] == 0]
    return dict(
        zip(pooled["plant_id"].astype(int), pooled["parasitic_factor"].astype(float))
    )


def _ols_intercept_slope(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """Return ``(intercept, slope)`` of ``y = a + b·x`` by least squares.

    Returns ``(nan, nan)`` when ``x`` has no spread (a slope is undefined).
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if x.size < 3 or x.std() < 1e-9:
        return float("nan"), float("nan")
    b, a = np.polyfit(x, y, 1)
    return float(a), float(b)


def _full_hourly_grid(sub: pd.DataFrame) -> pd.DataFrame:
    """Return one plant-year's unit-summed hourly series on a gap-free clock.

    CAMPD omits non-operating hours, so off-hours are reconstructed as zeros
    over the contiguous hourly span the plant reported in, giving a series
    where ``gross_mw == 0`` marks genuine downtime (needed for start/stop
    detection). Multiple units at the plant are summed per hour.
    """
    by_hour = (
        sub.assign(ts=sub["date"] + pd.to_timedelta(sub["hour"], unit="h"))
        .groupby("ts", as_index=True)[["gross_mw", "co2_kg", "nox_kg", "so2_kg", "heat_mmbtu"]]
        .sum()
        .sort_index()
    )
    full = pd.date_range(by_hour.index.min(), by_hour.index.max(), freq="h")
    return by_hour.reindex(full, fill_value=0.0)


def plant_hourly_grid(
    df: pd.DataFrame, plant_id: int, year: int
) -> pd.DataFrame:
    """Return one plant-year's unit-summed hourly series on a gap-free clock.

    Off-hours that CAMPD omits are reconstructed as zeros over the contiguous
    span the plant reported in, indexed by actual timestamps — the input to
    capacity-factor and outage analyses that need real calendar dates.

    Args:
        df: A frame from :func:`load_campd_hourly`.
        plant_id: EIA plant code to extract.
        year: Calendar year to extract.

    Returns:
        A ``DatetimeIndex``-ed frame with ``gross_mw``, ``co2_kg``, ``nox_kg``,
        ``so2_kg`` and ``heat_mmbtu``; empty when the plant-year is absent.
    """
    sub = df[(df["plant_id"] == int(plant_id)) & (df["year"] == int(year))]
    if sub.empty:
        return pd.DataFrame()
    return _full_hourly_grid(sub)


def _startup_factors(grid: pd.DataFrame) -> dict[str, float]:
    """Return start counts and per-start incremental emission adders.

    A start is an off→on transition (``gross_mw`` crossing
    :data:`_ONLINE_MW`). For each pollutant and heat input, the per-start
    adder is the mean over starts of the start hour's mass minus the
    steady-state mass predicted by the no-load + marginal fit on the
    plant's non-start operating hours — i.e. the extra burned warming the
    unit up. Negative residuals are clipped to zero.
    """
    gross = grid["gross_mw"].to_numpy()
    online = gross > _ONLINE_MW
    if online.sum() < 3:
        return {
            "starts": 0,
            "startup_co2_kg": 0.0, "startup_nox_kg": 0.0,
            "startup_so2_kg": 0.0, "startup_heat_mmbtu": 0.0,
        }
    prev = np.concatenate([[False], online[:-1]])
    start_mask = online & ~prev
    non_start_op = online & ~start_mask

    out: dict[str, float] = {"starts": int(start_mask.sum())}
    for col, key in (
        ("co2_kg", "startup_co2_kg"), ("nox_kg", "startup_nox_kg"),
        ("so2_kg", "startup_so2_kg"), ("heat_mmbtu", "startup_heat_mmbtu"),
    ):
        mass = grid[col].to_numpy()
        a, b = _ols_intercept_slope(gross[non_start_op], mass[non_start_op])
        if np.isnan(a):
            out[key] = 0.0
            continue
        predicted = a + b * gross[start_mask]
        residual = np.clip(mass[start_mask] - predicted, 0.0, None)
        out[key] = round(float(residual.mean()), 4) if residual.size else 0.0
    return out


def plant_emission_rates(
    df: pd.DataFrame, factors: dict[int, float]
) -> pd.DataFrame:
    """Return per-plant emission rates and start/stop factors.

    For each ``(plant_id, year)`` and a pooled ``year == 0`` row:

    * ``*_kg_per_mwh_net`` — average emission rate per MWh **net** generation
      (gross scaled by the plant's parasitic factor): the headline figure for
      tuning per-MWh emission prices.
    * ``*_marginal_kg_per_mwh_gross`` / ``*_noload_kg_per_hr`` — the
      least-squares decomposition of hourly mass against gross load, so the
      marginal (load-following) and fixed (committed) emissions are separable.
    * ``starts`` and ``startup_*`` — the per-start incremental emissions, for
      tuning cycling-emission penalties.

    Args:
        df: A frame from :func:`load_campd_hourly`.
        factors: ``{plant_id: parasitic_factor}`` (net/gross), e.g. from
            :func:`pooled_factor_map`.

    Returns:
        One row per ``(plant_id, year)`` plus the pooled ``year == 0`` row.
    """
    if df.empty:
        return pd.DataFrame()

    def _co2_total(sub: pd.DataFrame, heat_total: float) -> tuple[float, str]:
        """Return ``(co2_kg_total, source)``, backfilling unmonitored hours.

        A plant reporting CO2 for some hours is scaled up to its full heat
        input at its own measured kg/MMBtu; one reporting none uses the EPA
        natural-gas default factor.
        """
        measured = float(sub["co2_kg"].sum())
        heat_with_co2 = float(sub.loc[sub["co2_kg"].notna(), "heat_mmbtu"].sum())
        if heat_with_co2 <= 0.0:
            return DEFAULT_CO2_KG_PER_MMBTU * heat_total, "heat_backfilled"
        if heat_with_co2 >= 0.999 * heat_total:
            return measured, "measured"
        factor = measured / heat_with_co2
        return factor * heat_total, "partial_backfill"

    def _rates(sub: pd.DataFrame, plant_id: int) -> dict:
        gross_mwh = float(sub["gross_mw"].sum())
        factor = float(factors.get(int(plant_id), 1.0))
        net_mwh = gross_mwh * factor
        heat_total = float(sub["heat_mmbtu"].sum())
        co2_total, co2_source = _co2_total(sub, heat_total)
        rec: dict = {
            "gross_mwh": round(gross_mwh, 3),
            "net_mwh": round(net_mwh, 3),
            "parasitic_factor": round(factor, 6),
            "heat_mmbtu": round(heat_total, 3),
            "heat_rate_mmbtu_per_mwh_net": (
                round(heat_total / net_mwh, 4) if net_mwh > 0 else 0.0
            ),
            "co2_kg_per_mwh_net": (
                round(co2_total / net_mwh, 6) if net_mwh > 0 else 0.0
            ),
            "co2_source": co2_source,
        }
        op = sub[sub["gross_mw"] > 0.0]
        a, b = _ols_intercept_slope(
            op["gross_mw"].to_numpy(), op["co2_kg"].to_numpy()
        )
        rec["co2_marginal_kg_per_mwh_gross"] = round(b, 6) if not np.isnan(b) else 0.0
        rec["co2_noload_kg_per_hr"] = round(a, 4) if not np.isnan(a) else 0.0
        for col, mwh_key, marg_key, nl_key in (
            ("nox_kg", "nox_kg_per_mwh_net", "nox_marginal_kg_per_mwh_gross",
             "nox_noload_kg_per_hr"),
            ("so2_kg", "so2_kg_per_mwh_net", "so2_marginal_kg_per_mwh_gross",
             "so2_noload_kg_per_hr"),
        ):
            total = float(sub[col].sum())
            rec[mwh_key] = round(total / net_mwh, 6) if net_mwh > 0 else 0.0
            a, b = _ols_intercept_slope(
                op["gross_mw"].to_numpy(), op[col].to_numpy()
            )
            rec[marg_key] = round(b, 6) if not np.isnan(b) else 0.0
            rec[nl_key] = round(a, 4) if not np.isnan(a) else 0.0
        return rec

    rows: list[dict] = []
    for (plant_id, year), sub in df.groupby(["plant_id", "year"], observed=True):
        rec = {
            "plant_id": int(plant_id), "year": int(year),
            "facility_name": str(sub["facility_name"].iloc[0]),
        }
        rec.update(_rates(sub, plant_id))
        rec.update(_startup_factors(_full_hourly_grid(sub)))
        rows.append(rec)

    for plant_id, sub in df.groupby("plant_id", observed=True):
        rec = {
            "plant_id": int(plant_id), "year": 0,
            "facility_name": str(sub["facility_name"].iloc[0]),
        }
        rec.update(_rates(sub, plant_id))
        # Pool starts across years; emission adders averaged over years seen.
        per_year = [
            _startup_factors(_full_hourly_grid(s))
            for _, s in sub.groupby("year", observed=True)
        ]
        rec["starts"] = int(sum(p["starts"] for p in per_year))
        for k in ("startup_co2_kg", "startup_nox_kg", "startup_so2_kg",
                  "startup_heat_mmbtu"):
            vals = [p[k] for p in per_year if p["starts"] > 0]
            rec[k] = round(float(np.mean(vals)), 4) if vals else 0.0
        rows.append(rec)

    return pd.DataFrame(rows).sort_values(["plant_id", "year"]).reset_index(
        drop=True
    )


def plant_hourly_net(
    df: pd.DataFrame,
    factors: dict[int, float],
    year: int,
    hours: int = HOURS_PER_YEAR,
) -> dict[int, np.ndarray]:
    """Return per-plant 8760-hour **net** generation series for one year.

    Each plant's hourly gross load is summed across its units, placed on the
    model's fixed hour-of-year clock, and scaled by the plant's parasitic
    factor to net. Hours the plant did not report are zero (offline).

    Args:
        df: A frame from :func:`load_campd_hourly`.
        factors: ``{plant_id: parasitic_factor}`` (net/gross).
        year: Calendar year to extract.
        hours: Length of the output series (model dispatch horizon).

    Returns:
        ``{plant_id: (hours,) net MW}`` for every plant operating that year.
    """
    out: dict[int, np.ndarray] = {}
    if df.empty:
        return out
    yr = df[df["year"] == year]
    for plant_id, sub in yr.groupby("plant_id", observed=True):
        series = np.zeros(hours, dtype=float)
        hoy = sub["hour_of_year"].to_numpy()
        gross = sub["gross_mw"].to_numpy()
        valid = (hoy >= 0) & (hoy < hours)
        np.add.at(series, hoy[valid], gross[valid])
        out[int(plant_id)] = series * float(factors.get(int(plant_id), 1.0))
    return out


def coal_share_by_plant(
    generation: pd.DataFrame, years: list[int] | None = None
) -> dict[int, float]:
    """Return ``{plant_id: coal share of net generation}`` from EIA-923.

    The share flags plants whose facility-level CEMS gross blends coal and gas
    units: a plant with ``0.1 < coal_share < 0.9`` cannot have a single
    facility emission rate cleanly assigned to its (separate) coal and gas
    dispatch bins. Plants near 0 or 1 burn effectively one fuel.

    Args:
        generation: The EIA-923 Page-1 frame.
        years: Optional subset of years to pool; ``None`` uses all.

    Returns:
        ``{plant_id: coal_share}`` for every plant with positive generation.
    """
    g = generation if years is None else generation[generation["year"].isin(years)]
    is_coal = g["fuel_type"].astype(str).str.upper().isin(_COAL_EIA_FUELS)
    total = g.groupby("plant_id")["netgen_annual_mwh"].sum()
    coal = (
        g[is_coal].groupby("plant_id")["netgen_annual_mwh"].sum()
        .reindex(total.index).fillna(0.0)
    )
    return {
        int(p): float(coal[p] / total[p])
        for p in total.index if total[p] > 0
    }


def eia923_combustion_net(generation: pd.DataFrame) -> pd.DataFrame:
    """Return EIA-923 net generation summed over combustion units per plant.

    Filters out non-stack-monitored fuels (renewables, nuclear, hydro,
    storage; see :data:`_NON_COMBUSTION_FUELS`) so the net generation lines
    up with what CAMPD's gross output covers, then sums over the plant's
    prime movers and fuels.

    Args:
        generation: The EIA-923 Page-1 frame from
            :func:`market_sim.data.eia923.load_monthly_generation`.

    Returns:
        Columns ``plant_id``, ``year``, ``net_mwh``.
    """
    fuels = generation["fuel_type"].astype(str).str.upper()
    combustion = generation[~fuels.isin(_NON_COMBUSTION_FUELS)]
    out = (
        combustion.groupby(["plant_id", "year"], observed=True)[
            "netgen_annual_mwh"
        ]
        .sum()
        .rename("net_mwh")
        .reset_index()
    )
    out["plant_id"] = out["plant_id"].astype(int)
    out["year"] = out["year"].astype(int)
    return out
