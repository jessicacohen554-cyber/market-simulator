"""Forward-admissible ERCOT West Texas Export corridor VRE curtailment-share driver.

The ERCOT 8-zone reduction collapses the West/Panhandle wind corridor's
chronically-binding **nodal** transmission (dozens of internal 138/345 kV lines
in the Permian / CREZ, below zonal resolution) into one wide West->North pipe
that almost never binds, so the LP dispatches West/Panhandle wind and solar well
above what ERCOT's real grid delivered (the C2 / [3e] under-curtailment gap;
docs/handoffs/ercot-vre-curtailment-topology-scope-2026-07.md, WP-B).

This module supplies the reduced-form stand-in for that missing sub-zonal
structure: a curtailment ceiling on the West and Panhandle zones' wind (and
solar) dispatch,

    ceiling_frac(t) = 1 - depth * congestion_share(net_load_decile(t),
                                                   hour_of_day(t), season(t))

applied as a multiplier on the CF upper bound. Two pieces, derived separately:

* ``congestion_share`` — the **SHAPE**: the measured fraction of SCED executions
  with the West Texas Export corridor congested, binned by within-year net-load
  percentile decile x hour-of-day x season. Read from the derived reference table
  (scripts/derive_ercot_wtx_curtailment_share.py -> data/raw/reference/
  ercot_wtx_curtailment_share.csv), itself built ONLY from measured NP6-86 SCED
  congestion incidence (data/clean/ercot-wtx-congestion) geo-attributed via the
  ERCOT SP/bus mapping — never the reported curtailment volume or a price
  residual. A function of the model's OWN net-load, so it regenerates forward
  (more West VRE -> deeper net-load troughs -> higher congestion share) and
  reproduces the measured binding-frequency distribution leave-one-year-out
  (rule #23 / the anti-residual gate).
* ``depth`` — the **LEVEL**: a single per-tech coefficient converting congestion
  incidence into curtailed fraction, ``ScenarioConfig.ercot_wtx_curtail_depth_
  wind`` / ``_solar``. Empirically a stable structural constant of the West Texas
  network (~0.097 for wind across 2023-2025, LOYO-validated); centred on the
  measured curtailment MW quantity like the RTOLCAP-forward ``deliv`` coefficient
  (docs/handoffs/ercot-as-coopt-plan-2026-07.md). ``depth = 0`` is the
  zero-forcing ablation (driver inert).

Consumed by the orchestrator (gated on
``ScenarioConfig.ercot_wtx_curtailment_driver``) which computes the model's own
net-load and passes the per-(zone, hour) multipliers to the LP renewable bounds.
Returns neutral (1.0) multipliers for every zone that is not West/Panhandle and
whenever the reference table or clean congestion series is absent, so a missing
input degrades to the static behaviour rather than failing the solve.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Net-load percentile bins — matches the RTOLCAP-forward decile axis granularity
# (scarcity._ercot_rtolcap_fwd_decile) so the two derived drivers share a driver
# axis convention.
NET_LOAD_N_DECILE = 10

# The model zones behind the West Texas Export interface — the corridor whose
# wind/solar the nodal congestion curtails (zone_assignment._ercot_zone).
WEST_CORRIDOR_ZONES = ("West", "Panhandle")

# Reference-table datatype and columns (data/raw/reference).
SHARE_TABLE_NAME = "ercot_wtx_curtailment_share.csv"
_SHARE_KEY = ["net_load_decile", "hour_of_day", "season"]


def net_load_decile(net_load: np.ndarray) -> np.ndarray:
    """Within-year net-load percentile bin (0..NET_LOAD_N_DECILE-1) per hour.

    Ranks the year's net-load into equal-count bins. A forecast year ranks its
    OWN net-load, so the mapping regenerates and a changed VRE build shifts which
    hours fall in which bin (rule #10). Vectorized; no per-hour Python loop.
    """
    nl = np.asarray(net_load, dtype=float)
    n = len(nl)
    order = np.argsort(np.argsort(nl))  # ascending rank per hour
    return np.minimum(
        (order * NET_LOAD_N_DECILE) // max(n, 1), NET_LOAD_N_DECILE - 1
    ).astype("int64")


def hour_axes(n_hours: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(hour_of_day, season)`` arrays for the non-leap model clock.

    ``season`` is 0=DJF (winter), 1=MAM (spring), 2=JJA (summer), 3=SON (fall) —
    ``(month % 12) // 3`` on the fixed 2023 non-leap calendar template.
    """
    cal = pd.date_range("2023-01-01", periods=8760, freq="h")
    hod = cal.hour.to_numpy()[:n_hours]
    season = ((cal.month.to_numpy() % 12) // 3)[:n_hours]
    return hod.astype("int64"), season.astype("int64")


def load_share_table(reference_dir) -> pd.DataFrame | None:
    """Load the derived congestion-share table, or ``None`` when absent.

    ``reference_dir`` is ``paths.RAW_DIR / "reference"``. Returns a frame keyed by
    ``(net_load_decile, hour_of_day, season)`` carrying ``congestion_share`` in
    [0,1]; ``None`` (with a log line) when the derived CSV has not been generated.
    """
    from pathlib import Path

    path = Path(reference_dir) / SHARE_TABLE_NAME
    if not path.is_file():
        logger.info(
            "ercot-wtx-curtailment: no share table at %s "
            "(run scripts/derive_ercot_wtx_curtailment_share.py) — driver inert",
            path,
        )
        return None
    return pd.read_csv(path)


def _share_lookup(table: pd.DataFrame, net_load: np.ndarray) -> np.ndarray:
    """Map each hour to its congestion share via (decile, hour-of-day, season)."""
    n = len(net_load)
    dec = net_load_decile(net_load)
    hod, season = hour_axes(n)
    key = pd.DataFrame({"net_load_decile": dec, "hour_of_day": hod, "season": season})
    merged = key.merge(table, on=_SHARE_KEY, how="left")
    share = merged["congestion_share"].to_numpy(dtype=float)
    # An unseen (decile, hour, season) cell (sparse in a short derive) falls back
    # to 0 congestion — never a fabricated value.
    return np.nan_to_num(share, nan=0.0)


def wtx_curtail_multipliers(
    net_load: np.ndarray,
    zone_names: list[str],
    *,
    depth_wind: float,
    depth_solar: float,
    reference_dir,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Per-(zone, hour) curtailment ceiling multipliers for wind and solar.

    Parameters
    ----------
    net_load:
        The model's own system net-load ``(T,)`` (demand - wind_pot - solar_pot).
    zone_names:
        Ordered model zone names; the West/Panhandle rows get the ceiling, all
        others stay 1.0.
    depth_wind, depth_solar:
        The per-tech level coefficients (ScenarioConfig). ``0`` -> inert.
    reference_dir:
        ``paths.RAW_DIR / "reference"`` (where the derived share table lives).

    Returns
    -------
    (wind_mult, solar_mult) each ``(n_zones, T)`` in (0,1], or ``None`` when the
    share table is absent (caller keeps the static uncurtailed bound).
    """
    table = load_share_table(reference_dir)
    if table is None:
        return None
    nl = np.asarray(net_load, dtype=float)
    T = len(nl)
    n_zones = len(zone_names)
    share = _share_lookup(table, nl)  # (T,)

    wind_mult = np.ones((n_zones, T), dtype=float)
    solar_mult = np.ones((n_zones, T), dtype=float)
    corridor = [i for i, z in enumerate(zone_names) if z in WEST_CORRIDOR_ZONES]
    if not corridor:
        return wind_mult, solar_mult
    wind_row = np.clip(1.0 - float(depth_wind) * share, 0.0, 1.0)
    solar_row = np.clip(1.0 - float(depth_solar) * share, 0.0, 1.0)
    for i in corridor:
        wind_mult[i, :] = wind_row
        solar_mult[i, :] = solar_row
    return wind_mult, solar_mult
