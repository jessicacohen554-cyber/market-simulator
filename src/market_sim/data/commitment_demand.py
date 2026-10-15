"""The UC commitment demand: what the MILP window commits against (lane UC-1-FIX-7).

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

  - **backcast**: the BA's own EIA-930 day-ahead ``Demand forecast`` minus its
    metered ``Demand``, hour by hour, on the same ``<BA> hourly`` frame (and
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
(a one-hour misalignment where the realign is armed). The UC-DIAG reading
measured the bias as material only for SPP and MISO.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from market_sim.config.constants import (
    COMMITMENT_DF_DATA_ERROR_FRACTION,
    COMMITMENT_DF_SEASON_OF_MONTH,
    HOURS_PER_YEAR,
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


def ba_forecast_error_mw(iso: str, year: int) -> tuple[np.ndarray, int]:
    """``((HOURS_PER_YEAR,) DF - actual MW, QA-dropped hours)`` for an ISO-year.

    Read off the same filled EIA-930 frame the ISO's demand loader reads
    (``eia930.frames._ISO_TO_HOURLY_BA``), so row ``k`` is the model's hour
    ``k``. Raises when the ISO has no hourly BA frame for the year (an armed
    source never silently no-ops).
    """
    from market_sim.data import eia930

    ba = eia930._ISO_TO_HOURLY_BA.get(iso)
    frame = None if ba is None else eia930._eia_hourly_frame_filled(ba, year)
    if frame is None or "Demand forecast" not in frame.columns:
        raise ValueError(
            f"uc_commitment_demand_source='da_forecast': no EIA-930 hourly frame "
            f"with a 'Demand forecast' column for {iso} {year}"
        )
    err, valid = qa_forecast_error(
        frame["Demand forecast"].to_numpy(dtype=float),
        frame["Demand"].to_numpy(dtype=float),
    )
    return err, int((~valid).sum())


def backcast_commitment_increment(
    iso: str,
    year: int,
    iso_config,
    td_loss_factor: float = 0.0,
    caiso_tac_shares_standard_time: bool = False,
) -> tuple[np.ndarray, int]:
    """``((n_zones, HOURS_PER_YEAR) MW increment, QA-dropped hours)`` (backcast).

    The BA forecast error split by the demand loader's zone weights and
    grossed up by the loader's ``td_loss_factor`` -- the forecast mapped to
    zones exactly as the actual is.
    """
    from market_sim.data import eia930

    err, dropped = ba_forecast_error_mw(iso, year)
    weights = eia930.load_zone_weights(
        iso,
        year,
        iso_config,
        caiso_tac_shares_standard_time=caiso_tac_shares_standard_time,
    )
    inc = np.asarray(weights, dtype=float) * err[None, :]
    if td_loss_factor > 0.0:
        inc = inc * (1.0 + td_loss_factor)
    return inc, dropped


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


def commitment_demand(config, demand: np.ndarray) -> CommitmentDemand:
    """The UC window's commitment demand for ``config`` over the P1 ``demand``.

    ``"actual"`` returns ``demand`` itself (the same object). ``"da_forecast"``
    adds the backcast or forward increment (module docstring), sliced to the
    solve horizon ``demand.shape[1]``.
    """
    source = str(getattr(config, "uc_commitment_demand_source", "actual"))
    if source == "actual":
        return CommitmentDemand(demand=demand, source=source, basis="actual")
    if source != "da_forecast":
        raise ValueError(f"unknown uc_commitment_demand_source {source!r}")
    demand = np.asarray(demand, dtype=float)
    T = int(demand.shape[1])
    iso = str(config.iso)
    if getattr(config, "mode", "forecast") == "backcast":
        from market_sim.config.iso_configs import get_iso_config

        inc, dropped = backcast_commitment_increment(
            iso,
            int(config.weather_year),
            get_iso_config(iso),
            td_loss_factor=float(getattr(config, "td_loss_factor", 0.0) or 0.0),
            caiso_tac_shares_standard_time=bool(
                getattr(config, "caiso_tac_shares_standard_time", False)
            ),
        )
        if inc.shape[0] != demand.shape[0]:
            raise ValueError(
                f"commitment increment has {inc.shape[0]} zones, demand {demand.shape[0]}"
            )
        out = demand + inc[:, :T]
        basis = "eia930_da_forecast"
    else:
        frac = forward_bias_fraction(load_forecast_error_profile(iso))
        out = demand * (1.0 + frac[None, :T])
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
