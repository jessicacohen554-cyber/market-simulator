"""The UC commitment demand: what the MILP window commits against (lanes UC-1-FIX-7, FIX-8).

Owner ruling UC-DESK r13 (2026-10-15): the unit-commitment window
(``unit_commitment_milp``, ``model/uc``) commits against a COMMITMENT DEMAND
separate from the P1 demand. Real day-ahead / RUC commitment is made on the
operator's load forecast, not on the load that later materialises; committing
on realised load is perfect foresight (cause 2 of
``docs/records/governance/uc-milp-2026-10/FINDING-ucmilp-diag-undercommit-2026-10-14.md``).
P1 still clears on actual load, so prices stay the P1 duals (rule 4).

``ScenarioConfig.uc_commitment_demand_source``:

* ``"actual"`` (default) -- the commitment demand IS the P1 demand (the same
  object; byte-identical to uc-1.6).
* ``"da_forecast"`` -- the P1 demand plus a measured forecast increment:

  - **backcast**: the BA's own day-ahead forecast (the EIA-930 ``Demand
    forecast`` unless the ISO's basis below says otherwise) minus its metered
    ``Demand``, hour by hour, on the same ``<BA> hourly`` frame (and
    therefore the same local model clock) the demand loader reads, split
    across zones by the loader's own weights
    (:func:`market_sim.data.eia930.load_zone_weights`) and grossed up by the
    same ``td_loss_factor``. So the commitment demand is exactly what
    :func:`~market_sim.data.eia930.load_demand` would return with the forecast
    in place of the metered load; everything the solve adds to or nets from
    the demand downstream (interchange, must-run residuals) is unchanged.
    Admissible under rule 13 by the owner's ruling: the same quantity exists
    forward (below) and responds to the forward load.
  - **forecast**: the realised (forecast-year) load times one plus the
    measured multi-year mean relative error ``(DF - actual) / actual`` by
    season x hour of day (the frozen ``load-forecast-error`` clean partition,
    ``scripts/data/derive_load_forecast_error.py``, rule 23).

Per-ISO forecast-error basis (lane UC-DA-BASIS, owner rulings R16, R17, R19,
2026-10-18; :data:`FORECAST_ERROR_BASES`, default :data:`EIA930_BASIS`; record
``docs/records/governance/uc-milp-2026-10/FINDING-ucmilp-df-audit-2026-10-16.md``
section 4):

* **SPP** -- the forecast is SPP's own MTLF vintage in force at the DA-RUC (the
  latest issued at or before 13:00 CPT on D-1, Protocols section 4.3.2), read
  from ``load-forecast-vintages`` and placed on the frame rows by their
  ``UTC time`` (hour end = the MTLF ``GMTIntervalEnd``). The EIA-930 SWPP DF
  is NOT read: it carries a reporting uplift outside 2023-09-02 .. 2025-05-06.
  A missing vintage partition raises (:class:`MissingForecastVintages`), never
  a fallback to EIA-930; an hour with no vintage in force (only the first
  hours of the earliest intaked year) gets no increment and is counted as
  QA-dropped. The actual stays the EIA-930 SWPP Demand.
* **CAISO** -- the forecast is the EIA-930 CISO DF (= CAISO's DAM forecast);
  the actual is the metered Demand net of battery charging ``max(-NG: OTH,
  0)``, the basis the DAM forecast is on (charging stays an LP decision).

The RUC load basis ``uc_ruc_load_basis="iso_intraday_forecast"``
(:func:`intraday_commitment_demand`) is the same construction at the intraday
horizon: SPP's MTLF in force at the last 4-h ID-RUC cycle at least one cycle
before the hour (Protocols section 4.4.1). Backcast, SPP only.

Data QA (not a tunable): an hour whose ``|DF - actual|`` exceeds
:data:`~market_sim.config.constants.COMMITMENT_DF_DATA_ERROR_FRACTION` of the
actual, or whose forecast is missing, is a reporting error and contributes no
increment (the commitment demand is the actual there).

Rule 14 misalignment, documented: EIA-930 reports the forecast for the whole
BA. Where the model's demand is the same BA series (SPP, MISO, PJM, NEISO,
NYISO, ERCOT, SOCO) the increment is on the same basis. NWPP is a pool frame
(the members' summed forecast). CAISO's armed demand corrections
(``caiso_demand_clock_realign`` / ``caiso_supply_consistent_demand``) re-clock
or replace the metered series; the increment stays on the EIA-930 frame clock
(a one-hour misalignment where the realign is armed), and the increment is
split by the default TAC shares even where ``caiso_tac_shares_standard_time``
re-clocks them for the P1 demand (a backcast-only CAISO flag this module does
not read; the zonal split moves, the system total does not). The UC-DIAG reading
measured the bias as material only for SPP and MISO.

Row mapping (lane UC-1-FIX-8): the P1 demand's rows are the SOLVE's runtime
zones, which carry the interchange zones the orchestrator appends to the ISO
config (``extend_with_import_node``: ``NYISO_external``, ``PJM_external``,
``MISO_external``, the NWPP seam zones; CAISO's per-hub corridor split and
the NYISO NE-AC node split). The increment is therefore mapped onto the
demand rows BY ZONE NAME (:func:`load_row_index`): each configured zone of
``get_iso_config(iso)`` lands on its own runtime row; every other row gets no
increment and, in forecast mode, is not scaled. A configured zone absent from
the runtime list is admissible only when it carries no load (it was replaced
by the topology, e.g. CAISO's ``WECC_import`` by its corridors); otherwise the
mapping raises. Where the runtime zones ARE the configured zones (ERCOT, SPP,
NEISO, SOCO) the mapping is the identity and the result is unchanged.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    COMMITMENT_DF_DATA_ERROR_FRACTION,
    COMMITMENT_DF_SEASON_OF_MONTH,
    HOURS_PER_YEAR,
    SPP_DA_RUC_FORECAST_CUTOFF_HOUR_LOCAL,
    SPP_ID_RUC_CYCLE_HOURS,
    SPP_MARKET_TIMEZONE,
)

logger = logging.getLogger(__name__)

#: Admissible values of ``ScenarioConfig.uc_commitment_demand_source``.
COMMITMENT_DEMAND_SOURCES: tuple[str, ...] = ("actual", "da_forecast")

#: The clean datatype holding the forward error profile.
FORECAST_ERROR_DATATYPE = "load-forecast-error"

#: A non-leap calendar year: model row ``k`` is local hour ``k`` of the year
#: with Feb 29 dropped (``eia930.frames._eia_hourly_frame_filled``), so every
#: year's row-to-(month, hour) map is this one.
_MODEL_CALENDAR = pd.date_range("2023-01-01", periods=HOURS_PER_YEAR, freq="h")

_HOUR = pd.Timedelta(hours=1)


@dataclass(frozen=True)
class CommitmentDemand:
    """The commitment demand and what built it (for the UC solve log).

    Attributes:
        demand: ``(n_zones, T)`` MW the UC window balances against.
        source: ``"actual"`` or ``"da_forecast"``.
        basis: ``"actual"``, ``"eia930_da_forecast"`` (backcast) or
            ``"error_profile"`` (forecast).
        qa_dropped_hours: Backcast hours whose forecast was missing or failed
            the data-QA cut (no increment there); 0 otherwise.
    """

    demand: np.ndarray
    source: str
    basis: str
    qa_dropped_hours: int = 0

    def log_row(self, p1_demand: np.ndarray) -> dict:
        """Summary for ``uc_solve_log``: the increment over the P1 demand."""
        inc = np.asarray(self.demand, dtype=float).sum(axis=0) - np.asarray(
            p1_demand, dtype=float
        ).sum(axis=0)
        sys_load = np.asarray(p1_demand, dtype=float).sum(axis=0)
        top = np.argsort(sys_load)[::-1][: min(100, sys_load.size)]
        return {
            "source": self.source,
            "basis": self.basis,
            "qa_dropped_hours": int(self.qa_dropped_hours),
            "increment_mean_mw": round(float(inc.mean()), 1) if inc.size else 0.0,
            "increment_top100_median_mw": (
                round(float(np.median(inc[top])), 1) if inc.size else 0.0
            ),
            "increment_max_mw": round(float(inc.max()), 1) if inc.size else 0.0,
            "increment_min_mw": round(float(inc.min()), 1) if inc.size else 0.0,
        }


def model_hour_season_hod() -> tuple[np.ndarray, np.ndarray]:
    """``(season, hour_of_day)`` of each model row (``HOURS_PER_YEAR`` each)."""
    season = np.array(
        [COMMITMENT_DF_SEASON_OF_MONTH[int(m)] for m in _MODEL_CALENDAR.month],
        dtype=object,
    )
    return season, np.asarray(_MODEL_CALENDAR.hour, dtype=int)


def qa_forecast_error(
    forecast: np.ndarray, actual: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """``(DF - actual, valid mask)``; invalid hours carry a 0 error.

    An hour is valid iff both values are finite, the actual is positive and
    ``|DF - actual| <= COMMITMENT_DF_DATA_ERROR_FRACTION * actual``.
    """
    df = np.asarray(forecast, dtype=float)
    act = np.asarray(actual, dtype=float)
    err = df - act
    with np.errstate(invalid="ignore"):
        valid = (
            np.isfinite(df)
            & np.isfinite(act)
            & (act > 0.0)
            & (np.abs(err) <= COMMITMENT_DF_DATA_ERROR_FRACTION * act)
        )
    return np.where(valid, err, 0.0), valid


class MissingForecastVintages(FileNotFoundError):
    """An ISO's forecast-vintage basis has no partition for the year (never a fallback)."""


def _eia930_day_ahead(iso: str, year: int, frame: pd.DataFrame) -> np.ndarray:
    """The BA's EIA-930 ``Demand forecast`` (its own day-ahead forecast)."""
    return frame["Demand forecast"].to_numpy(dtype=float)


def _eia930_demand(frame: pd.DataFrame) -> np.ndarray:
    """The BA's metered EIA-930 ``Demand``."""
    return frame["Demand"].to_numpy(dtype=float)


def storage_charging_mw(frame: pd.DataFrame) -> np.ndarray:
    """``max(-NG: OTH, 0)`` MW, 0 where unreported (CAISO battery charging).

    EIA-930 CISO ``NG: OTH`` is CAISO's battery net output (FINDING-ucmilp-df-
    audit-2026-10-16 section 3); its negative part is charging. Raises when
    the column is absent: the netted basis is never silently the raw one.
    """
    if "NG: OTH" not in frame.columns:
        raise ValueError(
            "storage-charging-netted actual needs the EIA-930 'NG: OTH' column"
        )
    chg = np.clip(-frame["NG: OTH"].to_numpy(dtype=float), 0.0, None)
    return np.nan_to_num(chg, nan=0.0)


def _eia930_demand_net_storage_charging(frame: pd.DataFrame) -> np.ndarray:
    """Metered ``Demand`` less battery charging (the basis CAISO's DAM forecast is on).

    Owner ruling R17: CAISO's DAM load forecast (= EIA-930 CISO ``Demand
    forecast``) excludes storage charging, a bid-in market-dispatched
    resource; the metered actual includes it. Netting it keeps the increment
    genuine load-forecast error and leaves charging an LP decision.
    """
    return _eia930_demand(frame) - storage_charging_mw(frame)


def _frame_interval_end_utc(frame: pd.DataFrame) -> pd.DatetimeIndex:
    """The frame's ``UTC time`` (hour END, = SPP ``GMTIntervalEnd``) as tz-aware UTC."""
    t = pd.DatetimeIndex(pd.to_datetime(frame["UTC time"]))
    return t.tz_localize("UTC") if t.tz is None else t.tz_convert("UTC")


def da_ruc_cutoff_utc(
    interval_end_utc: pd.DatetimeIndex, tz: str, cutoff_hour_local: int
) -> pd.DatetimeIndex:
    """Per operating hour, ``cutoff_hour_local``:00 local on the day before its operating day.

    The operating day is the local calendar date of the hour's START. The
    cutoff is built on the wall clock (a DST day is 23 or 25 h, so it is not
    a fixed UTC lead) and localized; a mid-day hour is never ambiguous.
    """
    start_local = (interval_end_utc - _HOUR).tz_convert(tz)
    day = start_local.tz_localize(None).normalize()
    wall = day - pd.Timedelta(days=1) + pd.Timedelta(hours=int(cutoff_hour_local))
    return wall.tz_localize(tz, ambiguous="raise", nonexistent="raise").tz_convert(
        "UTC"
    )


def cycle_cutoff_utc(
    interval_end_utc: pd.DatetimeIndex, tz: str, cycle_hours: int
) -> pd.DatetimeIndex:
    """Per operating hour, the last cycle at least one cycle before its start.

    Cycles sit on a ``cycle_hours`` grid of the local wall clock from 00:00
    (grid points never fall in a US DST fold or gap). The cutoff is the wall
    floor of ``start - cycle_hours`` onto that grid, so it is always at or
    before ``start - cycle_hours`` in absolute time.
    """
    c = int(cycle_hours)
    if c <= 0 or 24 % c:
        raise ValueError(f"cycle_hours must divide 24, got {cycle_hours}")
    wall = (
        (interval_end_utc - _HOUR - pd.Timedelta(hours=c))
        .tz_convert(tz)
        .tz_localize(None)
        .floor("h")
    )
    wall = wall - pd.to_timedelta(wall.hour % c, unit="h")
    return wall.tz_localize(tz, ambiguous="raise", nonexistent="raise").tz_convert(
        "UTC"
    )


def vintage_in_force(
    vintages: pd.DataFrame,
    interval_end_utc: pd.DatetimeIndex,
    cutoff_utc: pd.DatetimeIndex,
) -> np.ndarray:
    """``(len(interval_end_utc),)`` MW: per hour, the latest vintage issued at or before its cutoff.

    ``vintages`` is one area's ``load-forecast-vintages`` frame. NaN where no
    vintage issued by the cutoff covers the hour. Vectorized (rule 2 spirit):
    one filter, one sort, one de-duplication.
    """
    cut = pd.Series(np.asarray(cutoff_utc), index=interval_end_utc)
    if not cut.index.is_unique:
        raise ValueError("vintage_in_force: interval_end_utc must be unique")
    v = vintages[vintages["interval_end_utc"].isin(cut.index)]
    ok = v["issue_time_utc"].to_numpy() <= cut.reindex(v["interval_end_utc"]).to_numpy()
    pick = (
        v.loc[ok, ["interval_end_utc", "issue_time_utc", "forecast_mw"]]
        .sort_values(["interval_end_utc", "issue_time_utc"])
        .drop_duplicates("interval_end_utc", keep="last")
        .set_index("interval_end_utc")["forecast_mw"]
    )
    return pick.reindex(interval_end_utc).to_numpy(dtype=float)


@dataclass(frozen=True)
class VintageClock:
    """When an ISO's reliability commitments read its own forecast vintages.

    Attributes:
        area: The ``load-forecast-vintages`` area label on the model's footprint.
        tz: The market timezone the deadlines are stated in.
        da_cutoff_hour_local: DA commitment vintage: the latest issued at or
            before this local hour of D-1.
        id_cycle_hours: Intraday commitment cycle (hours, a divisor of 24).
    """

    area: str
    tz: str
    da_cutoff_hour_local: int
    id_cycle_hours: int


def _vintage_frame(iso: str, year: int, area: str) -> pd.DataFrame:
    """The ``iso`` vintages covering model ``year`` (issue years ``year - 1 .. year``).

    Raises :class:`MissingForecastVintages` when the issue-``year`` partition
    is absent (never a fallback to EIA-930). The ``year - 1`` partition is
    read where present: without it, the first hours of the earliest intaked
    year have no vintage in force (counted as QA-dropped, logged).
    """
    from market_sim.data import load_forecast_vintages as lfv

    if int(year) not in lfv.available_years(iso):
        raise MissingForecastVintages(
            f"{iso} {year}: the commitment forecast basis reads SPP's own "
            f"{lfv.DATATYPE} vintages and partition {year} is absent; run "
            "scripts/regenerate_clean.py load-forecast-vintages (no EIA-930 "
            "fallback)"
        )
    return lfv.load_vintages(iso, (int(year) - 1, int(year)), area=area)


def _vintage_forecast(
    iso: str, year: int, frame: pd.DataFrame, horizon: str
) -> np.ndarray:
    """The ISO's own forecast in force at its DA or intraday commitment, on the frame rows."""
    clock = VINTAGE_CLOCKS[iso]
    ends = _frame_interval_end_utc(frame)
    if horizon == "day_ahead":
        cut = da_ruc_cutoff_utc(ends, clock.tz, clock.da_cutoff_hour_local)
    else:
        cut = cycle_cutoff_utc(ends, clock.tz, clock.id_cycle_hours)
    fc = vintage_in_force(_vintage_frame(iso, year, clock.area), ends, cut)
    uncovered = int(np.isnan(fc).sum())
    if uncovered:
        logger.warning(
            "%s %d %s: %d hour(s) have no %s vintage in force (no increment there)",
            iso,
            year,
            horizon,
            uncovered,
            clock.area,
        )
    return fc


def _spp_da_ruc(iso: str, year: int, frame: pd.DataFrame) -> np.ndarray:
    """SPP's MTLF vintage in force at the DA-RUC (owner ruling R16)."""
    return _vintage_forecast(iso, year, frame, "day_ahead")


def _spp_id_ruc(iso: str, year: int, frame: pd.DataFrame) -> np.ndarray:
    """SPP's MTLF vintage in force at the last ID-RUC cycle a cycle before the hour."""
    return _vintage_forecast(iso, year, frame, "intraday")


#: Per-ISO vintage clocks (values from ``constants.py``, cited there).
VINTAGE_CLOCKS: dict[str, VintageClock] = {
    "SPP": VintageClock(
        area="SPP",
        tz=SPP_MARKET_TIMEZONE,
        da_cutoff_hour_local=SPP_DA_RUC_FORECAST_CUTOFF_HOUR_LOCAL,
        id_cycle_hours=SPP_ID_RUC_CYCLE_HOURS,
    ),
}


@dataclass(frozen=True)
class ForecastErrorBasis:
    """How an ISO's load-forecast error ``forecast - actual`` is measured.

    Attributes:
        label: ``CommitmentDemand.basis`` of a backcast built on it.
        forecast: ``(iso, year, frame) -> (HOURS_PER_YEAR,)`` MW, the DA
            commitment forecast on the filled EIA-930 frame's rows.
        actual: ``frame -> (HOURS_PER_YEAR,)`` MW, the actual on the
            forecast's basis.
        intraday_forecast: As ``forecast``, at the intraday commitment
            (``uc_ruc_load_basis="iso_intraday_forecast"``); ``None`` = none.
    """

    label: str
    forecast: Callable[[str, int, pd.DataFrame], np.ndarray]
    actual: Callable[[pd.DataFrame], np.ndarray]
    intraday_forecast: Callable[[str, int, pd.DataFrame], np.ndarray] | None = None


#: The default basis: the BA's own EIA-930 day-ahead forecast vs its metered
#: demand (uc-1.7 .. uc-1.9 for every ISO).
EIA930_BASIS = ForecastErrorBasis(
    label="eia930_da_forecast", forecast=_eia930_day_ahead, actual=_eia930_demand
)

#: ISOs whose forecast error is NOT the default (owner rulings R16, R17;
#: FINDING-ucmilp-df-audit-2026-10-16 section 4). Every other ISO reads
#: :data:`EIA930_BASIS`.
FORECAST_ERROR_BASES: dict[str, ForecastErrorBasis] = {
    # R16: SPP's own MTLF at the DA-RUC (the EIA-930 SWPP DF carries a
    # reporting uplift in 2019 .. 2023-09-01 and from 2025-05-07); the actual
    # stays the EIA-930 SWPP Demand (footprint Table A: ratio 0.996-1.003).
    "SPP": ForecastErrorBasis(
        label="spp_mtlf_da_ruc",
        forecast=_spp_da_ruc,
        actual=_eia930_demand,
        intraday_forecast=_spp_id_ruc,
    ),
    # R17: CAISO's DAM forecast vs the metered demand net of battery charging.
    "CAISO": ForecastErrorBasis(
        label="eia930_da_forecast_net_storage_charging",
        forecast=_eia930_day_ahead,
        actual=_eia930_demand_net_storage_charging,
    ),
}

#: Forecast horizons :func:`ba_forecast_error_mw` reads.
FORECAST_HORIZONS: tuple[str, ...] = ("day_ahead", "intraday")


def forecast_error_basis(iso: str) -> ForecastErrorBasis:
    """The ISO's :class:`ForecastErrorBasis` (registry, default :data:`EIA930_BASIS`)."""
    return FORECAST_ERROR_BASES.get(str(iso), EIA930_BASIS)


def intraday_forecast_isos() -> tuple[str, ...]:
    """ISOs with a measured intraday commitment forecast."""
    return tuple(
        sorted(i for i, b in FORECAST_ERROR_BASES.items() if b.intraday_forecast)
    )


def forecast_and_actual_mw(
    iso: str, year: int, horizon: str = "day_ahead"
) -> tuple[np.ndarray, np.ndarray]:
    """``((HOURS_PER_YEAR,) forecast MW, actual MW)`` on the ISO's basis.

    Read off the same filled EIA-930 frame the ISO's demand loader reads
    (``eia930.frames._ISO_TO_HOURLY_BA``), so row ``k`` is the model's hour
    ``k``; the forecast and the actual are the ISO's
    :func:`forecast_error_basis`. Raises when the ISO has no hourly BA frame
    for the year, when ``horizon`` has no forecast for the ISO, or when the
    basis' own data is missing (an armed source never silently no-ops). The
    actual's EIA-930 stale-snapshot hours carry the ISO's own measured load
    (:func:`market_sim.data.stale_snapshot.repair_system_demand`).
    """
    from market_sim.data import eia930

    if horizon not in FORECAST_HORIZONS:
        raise ValueError(f"unknown forecast horizon {horizon!r}")
    basis = forecast_error_basis(iso)
    read = basis.forecast if horizon == "day_ahead" else basis.intraday_forecast
    if read is None:
        raise ValueError(
            f"{iso}: no measured {horizon} commitment forecast (registered for "
            f"{list(intraday_forecast_isos())})"
        )
    ba = eia930._ISO_TO_HOURLY_BA.get(iso)
    frame = None if ba is None else eia930._eia_hourly_frame_filled(ba, year)
    if frame is None or (
        read is _eia930_day_ahead and "Demand forecast" not in frame.columns
    ):
        raise ValueError(
            f"uc_commitment_demand_source='da_forecast': no EIA-930 hourly frame "
            f"with a 'Demand forecast' column for {iso} {year}"
        )
    # EIA-930 stale-snapshot hours: the actual is the ISO's own measured load,
    # the same repair the solve's demand carries (owner ruling R22; identity
    # for an ISO without a stale_snapshot spec), so the increment never pairs
    # a repaired P1 load with a frozen actual.
    from market_sim.data.stale_snapshot import repair_system_demand

    actual = repair_system_demand(iso, int(year), basis.actual(frame))
    return read(iso, int(year), frame), actual


def ba_forecast_error_mw(
    iso: str, year: int, horizon: str = "day_ahead"
) -> tuple[np.ndarray, int]:
    """``((HOURS_PER_YEAR,) forecast - actual MW, QA-dropped hours)`` for an ISO-year.

    :func:`forecast_and_actual_mw` through the data-QA cut
    (:func:`qa_forecast_error`); an hour with no forecast is QA-dropped.
    """
    forecast, actual = forecast_and_actual_mw(iso, year, horizon)
    err, valid = qa_forecast_error(forecast, actual)
    return err, int((~valid).sum())


def load_row_index(
    config_zone_names: Sequence[str], zone_names: Sequence[str] | None
) -> np.ndarray:
    """``(n_config_zones,)`` runtime row of each configured zone, ``-1`` if absent.

    ``config_zone_names`` are ``get_iso_config(iso).zone_names`` (the rows the
    loader's weights are on); ``zone_names`` are the solve's runtime zones (the
    P1 demand's rows, in its order). The orders need not match. Raises when
    the runtime list is unavailable or names a zone twice.
    """
    if zone_names is None:
        raise ValueError(
            "uc_commitment_demand_source='da_forecast' needs the solve's runtime "
            "zone list to map the forecast increment onto the P1 demand rows"
        )
    pos = {str(z): i for i, z in enumerate(zone_names)}
    if len(pos) != len(zone_names):
        raise ValueError(f"runtime zone list names a zone twice: {list(zone_names)}")
    return np.array([pos.get(str(z), -1) for z in config_zone_names], dtype=int)


def _absent_load_zones(
    config_zone_names: Sequence[str], rows: np.ndarray, carries_load: np.ndarray
) -> list[str]:
    """Configured zones absent from the runtime list that carry load."""
    return [
        str(z)
        for z, r, load in zip(config_zone_names, rows, carries_load)
        if r < 0 and load
    ]


def backcast_commitment_increment(
    iso: str,
    year: int,
    iso_config,
    zone_names: Sequence[str] | None,
    td_loss_factor: float = 0.0,
    caiso_tac_shares_standard_time: bool = False,
    horizon: str = "day_ahead",
) -> tuple[np.ndarray, int]:
    """``((len(zone_names), HOURS_PER_YEAR) MW increment, QA-dropped hours)`` (backcast).

    The BA forecast error at ``horizon`` (:func:`ba_forecast_error_mw`) split
    by the demand loader's zone weights and grossed up by the loader's
    ``td_loss_factor`` -- the forecast mapped to zones exactly as the actual
    is. The weights (on ``iso_config``'s zones) are placed on the runtime rows
    by name (:func:`load_row_index`); a row no configured zone maps to gets 0.
    Raises when a configured zone with a nonzero weight in any hour is absent
    from ``zone_names``.
    """
    from market_sim.data import eia930

    err, dropped = ba_forecast_error_mw(iso, year, horizon=horizon)
    weights = np.asarray(
        eia930.load_zone_weights(
            iso,
            year,
            iso_config,
            caiso_tac_shares_standard_time=caiso_tac_shares_standard_time,
        ),
        dtype=float,
    )
    config_zones = list(iso_config.zone_names)
    rows = load_row_index(config_zones, zone_names)
    absent = _absent_load_zones(config_zones, rows, (weights != 0.0).any(axis=1))
    if absent:
        raise ValueError(
            f"commitment increment: load zone(s) {absent} of the {iso} config are "
            f"absent from the solve's zones {list(zone_names)}"
        )
    present = rows >= 0
    row_weights = np.zeros((len(zone_names), weights.shape[1]), dtype=float)
    row_weights[rows[present]] = weights[present]
    inc = row_weights * err[None, :]
    if td_loss_factor > 0.0:
        inc = inc * (1.0 + td_loss_factor)
    return inc, dropped


def forward_load_row_mask(iso_config, zone_names: Sequence[str] | None) -> np.ndarray:
    """``(len(zone_names),)`` True on the runtime rows of configured zones (forecast).

    The forward bias scales only these rows; an appended interchange row (an
    export sink) is left as is. Raises when a configured zone with a positive
    ``load_share`` is absent from ``zone_names``.
    """
    config_zones = list(iso_config.zone_names)
    rows = load_row_index(config_zones, zone_names)
    shares = np.array([float(z.load_share) for z in iso_config.zones]) > 0.0
    absent = _absent_load_zones(config_zones, rows, shares)
    if absent:
        raise ValueError(
            f"commitment demand: load zone(s) {absent} of the {iso_config.name} "
            f"config are absent from the solve's zones {list(zone_names)}"
        )
    mask = np.zeros(len(zone_names), dtype=bool)
    mask[rows[rows >= 0]] = True
    return mask


def load_forecast_error_profile(iso: str) -> pd.DataFrame:
    """The ISO's frozen ``load-forecast-error`` partition (season x hour)."""
    from scripts.lib.clean_io import clean_exists, read_clean

    if not clean_exists(FORECAST_ERROR_DATATYPE, iso=str(iso).upper()):
        raise ValueError(
            "uc_commitment_demand_source='da_forecast' in forecast mode needs the "
            f"load-forecast-error partition for {iso}: run "
            "scripts/regenerate_clean.py load-forecast-error"
        )
    return read_clean(FORECAST_ERROR_DATATYPE, iso=str(iso).upper())


def forward_bias_fraction(profile: pd.DataFrame) -> np.ndarray:
    """``(HOURS_PER_YEAR,)`` mean relative forecast error of each model row."""
    lut = {
        (str(s), int(h)): float(b)
        for s, h, b in zip(
            profile["season"], profile["hour_of_day"], profile["bias_frac"]
        )
    }
    season, hod = model_hour_season_hod()
    missing = {(s, int(h)) for s, h in zip(season, hod)} - set(lut)
    if missing:
        raise ValueError(
            f"load-forecast-error profile lacks {len(missing)} season x hour cells"
        )
    return np.array([lut[(s, int(h))] for s, h in zip(season, hod)], dtype=float)


def commitment_demand(
    config, demand: np.ndarray, zone_names: Sequence[str] | None = None
) -> CommitmentDemand:
    """The UC window's commitment demand for ``config`` over the P1 ``demand``.

    ``"actual"`` returns ``demand`` itself (the same object). ``"da_forecast"``
    adds the backcast or forward increment (module docstring), sliced to the
    solve horizon ``demand.shape[1]``, on the rows ``zone_names`` (the solve's
    runtime zones, ``demand``'s row order) names; required there.
    """
    source = str(getattr(config, "uc_commitment_demand_source", "actual"))
    if source == "actual":
        return CommitmentDemand(demand=demand, source=source, basis="actual")
    if source != "da_forecast":
        raise ValueError(f"unknown uc_commitment_demand_source {source!r}")
    demand = np.asarray(demand, dtype=float)
    T = int(demand.shape[1])
    iso = str(config.iso)
    if zone_names is None:
        raise ValueError(
            "uc_commitment_demand_source='da_forecast' needs the solve's runtime "
            "zone list (run_energy_solve(zone_names=...)) to map the increment "
            "onto the P1 demand rows"
        )
    if len(zone_names) != demand.shape[0]:
        raise ValueError(
            f"runtime zone list has {len(zone_names)} zones, demand {demand.shape[0]}"
        )
    from market_sim.config.iso_configs import get_iso_config

    if getattr(config, "mode", "forecast") == "backcast":
        inc, dropped = backcast_commitment_increment(
            iso,
            int(config.weather_year),
            get_iso_config(iso),
            zone_names,
            td_loss_factor=float(getattr(config, "td_loss_factor", 0.0) or 0.0),
        )
        if inc.shape[0] != demand.shape[0]:
            raise ValueError(
                f"commitment increment has {inc.shape[0]} zones, demand {demand.shape[0]}"
            )
        out = demand + inc[:, :T]
        basis = forecast_error_basis(iso).label
    else:
        mask = forward_load_row_mask(get_iso_config(iso), zone_names)
        frac = forward_bias_fraction(load_forecast_error_profile(iso))
        out = np.where(mask[:, None], demand * (1.0 + frac[None, :T]), demand)
        dropped = 0
        basis = "error_profile"
    logger.info(
        "UC commitment demand (%s, %s): %+.0f MW mean increment, %d QA-dropped hours",
        source,
        basis,
        float((out - demand).sum(axis=0).mean()),
        dropped,
    )
    return CommitmentDemand(
        demand=out, source=source, basis=basis, qa_dropped_hours=dropped
    )


def intraday_commitment_demand(
    config, demand: np.ndarray, zone_names: Sequence[str] | None
) -> np.ndarray:
    """``(n_zones, T)`` the RUC load basis ``"iso_intraday_forecast"`` (backcast).

    The P1 ``demand`` plus the ISO's intraday forecast error (its own forecast
    vintage in force at the last intraday commitment cycle at least one cycle
    before each hour; SPP: the MTLF at the 4-h ID-RUC,
    :data:`~market_sim.config.constants.SPP_ID_RUC_CYCLE_HOURS`), mapped to
    the runtime rows exactly as the DA increment is
    (:func:`backcast_commitment_increment`). Raises outside backcast mode
    (no forward intraday profile is derived) and for an ISO with no
    registered intraday forecast.
    """
    iso = str(config.iso)
    if iso not in intraday_forecast_isos():
        raise ValueError(
            f"uc_ruc_load_basis='iso_intraday_forecast': {iso} has no measured "
            f"intraday forecast (registered for {list(intraday_forecast_isos())})"
        )
    if getattr(config, "mode", "forecast") != "backcast":
        raise ValueError(
            "uc_ruc_load_basis='iso_intraday_forecast' reads measured forecast "
            "vintages: backcast only (no forward intraday error profile)"
        )
    demand = np.asarray(demand, dtype=float)
    if zone_names is None or len(zone_names) != demand.shape[0]:
        raise ValueError(
            "uc_ruc_load_basis='iso_intraday_forecast' needs the solve's runtime "
            "zone list, one name per demand row"
        )
    from market_sim.config.iso_configs import get_iso_config

    inc, dropped = backcast_commitment_increment(
        iso,
        int(config.weather_year),
        get_iso_config(iso),
        zone_names,
        td_loss_factor=float(getattr(config, "td_loss_factor", 0.0) or 0.0),
        horizon="intraday",
    )
    out = demand + inc[:, : demand.shape[1]]
    logger.info(
        "UC RUC load basis (iso_intraday_forecast): %+.0f MW mean increment, "
        "%d QA-dropped hours",
        float((out - demand).sum(axis=0).mean()),
        dropped,
    )
    return out
