"""Emissions accounting from dispatch results.

Converts a thermal dispatch schedule into hourly system-wide pollutant
totals. The hourly functions follow the same vectorized pattern: weight
each generator's hourly output by its per-MWh emission rate and sum across
the fleet.

:func:`compute_must_run_emissions` is a separate, post-processing step: the
CHP must-run (steam) tranche is removed from the LP capacity, so its
generation and emissions are reconstructed here for asset-level reporting.
"""

import numpy as np
import pandas as pd


def compute_emissions(
    dispatch: np.ndarray, emission_rates: np.ndarray
) -> np.ndarray:
    """Return hourly system CO2 emissions from a dispatch schedule.

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        emission_rates: Per-generator CO2 rate of shape ``(n_gen,)`` in
            tCO2/MWh.

    Returns:
        Hourly system CO2 emissions of shape ``(T,)`` in tCO2.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    emission_rates = np.asarray(emission_rates, dtype=float)
    return (dispatch * emission_rates[:, None]).sum(axis=0)


def compute_nox(dispatch: np.ndarray, nox_rates: np.ndarray) -> np.ndarray:
    """Return hourly system NOx emissions from a dispatch schedule.

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        nox_rates: Per-generator NOx rate of shape ``(n_gen,)`` in
            tons NOx/MWh.

    Returns:
        Hourly system NOx emissions of shape ``(T,)`` in tons NOx.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    nox_rates = np.asarray(nox_rates, dtype=float)
    return (dispatch * nox_rates[:, None]).sum(axis=0)


def compute_must_run_emissions(
    bins: pd.DataFrame,
    year: int,
    must_run_cf: float = 0.85,
    total_gen_by_plant: dict[int, float] | None = None,
    grid_gen_by_plant: dict[int, float] | None = None,
) -> pd.DataFrame:
    """Reconstruct CHP must-run (behind-the-meter) generation and emissions.

    The Must-Run tranche of each CHP plant (capacity serving a steam
    contract) is removed from the dispatch LP, so its behind-the-meter
    grid-invisible generation never appears in the dispatch result. This
    adds it back for asset-level emissions and total-generation reporting.
    Covers CC_CHP, CT_CHP and ST_CHP; coal is excluded (its must-run share
    stays in the LP as a ``_mustrun`` tranche).

    Two sizing modes:

    * **Data-driven (preferred for backcasts).** When ``total_gen_by_plant``
      is given — the plant's measured total net generation, e.g. EIA-923
      Page 1 — the behind-the-meter generation is that total minus the
      grid-delivered portion the LP already dispatched
      (``grid_gen_by_plant``, summed by plant code). This reconciles
      reported total CHP generation to the measured figure: EIA-923 is
      gross-minus-station-service and so *includes* the host's on-site
      electricity, while the LP only dispatches the grid-delivered slice
      (which EIA-930 sees). The difference is the behind-the-meter must-run.
    * **Flat-CF fallback (forecasts).** Without measured totals, the
      legacy estimate ``nameplate × pct_mr × 8760 × must_run_cf`` is used.

    Args:
        bins: The per-plant bin frame from
            :func:`market_sim.data.fleet.load_campd_bins`, carrying
            ``Plant_Code``, ``pct_mr``, ``capacity_mw``, ``hr_weighted``
            and ``fuel``.
        year: Simulation year, recorded on each output row.
        must_run_cf: Capacity factor for the flat-CF fallback.
        total_gen_by_plant: Optional ``{plant_code: annual MWh}`` of measured
            total net generation (e.g. EIA-923). Triggers the data-driven mode.
        grid_gen_by_plant: Optional ``{plant_code: annual MWh}`` of the LP's
            grid-delivered dispatch per plant, subtracted from the total to
            isolate the behind-the-meter portion. Treated as zero for any
            plant absent from the mapping.

    Returns:
        One row per non-coal must-run plant with ``mr_mw``, ``mr_gen_mwh``
        and ``mr_co2_tons``; empty when no such plant exists.
    """
    from market_sim.data.fleet import get_emission_rate

    mr = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")].copy()
    if mr.empty:
        return mr.assign(mr_mw=[], mr_gen_mwh=[], mr_co2_tons=[], year=[])

    mr["year"] = year
    if total_gen_by_plant is not None:
        grid = grid_gen_by_plant or {}
        total = mr["Plant_Code"].map(total_gen_by_plant).fillna(0.0)
        grid_gen = mr["Plant_Code"].map(grid).fillna(0.0)
        mr["mr_gen_mwh"] = (total - grid_gen).clip(lower=0.0)
        mr["mr_mw"] = mr["mr_gen_mwh"] / 8760.0
    else:
        mr["mr_mw"] = mr["capacity_mw"] * mr["pct_mr"] / 100.0
        mr["mr_gen_mwh"] = mr["mr_mw"] * 8760.0 * must_run_cf
    mr["mr_co2_tons"] = mr.apply(
        lambda r: r["mr_gen_mwh"]
        * get_emission_rate(r["fuel"], r["hr_weighted"]),
        axis=1,
    )
    return mr
