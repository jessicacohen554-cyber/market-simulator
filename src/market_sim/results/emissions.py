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
    bins: pd.DataFrame, year: int, must_run_cf: float = 0.85
) -> pd.DataFrame:
    """Reconstruct CHP must-run generation and emissions for asset reporting.

    The Must-Run tranche of each CHP bin (the always-on capacity serving a
    steam contract) is removed from the dispatch LP, so its grid generation
    never appears in the dispatch result. This adds it back: for every
    non-coal bin with ``pct_mr > 0`` the must-run MW runs ``8760 ×
    must_run_cf`` hours and its CO2 is the must-run generation times the
    bin's emission rate. This covers CC_CHP, CT_CHP and ST_CHP and is
    used for fleet-specific emissions trajectories on an asset basis.

    Coal bins are excluded: their must-run share stays in the LP as a
    ``_mustrun`` tranche, so its generation already appears in the
    dispatch result.

    Args:
        bins: The aggregated bin frame from
            :func:`market_sim.data.fleet.load_campd_bins`, carrying
            ``pct_mr``, ``capacity_mw``, ``hr_weighted`` and ``fuel``.
        year: Simulation year, recorded on each output row.
        must_run_cf: Assumed capacity factor for must-run generation.

    Returns:
        One row per non-coal must-run bin with ``mr_mw``, ``mr_gen_mwh``
        and ``mr_co2_tons``; empty when no such bin exists.
    """
    from market_sim.data.fleet import get_emission_rate

    mr = bins[(bins["pct_mr"] > 0) & (bins["fuel"] != "coal")].copy()
    if mr.empty:
        return mr.assign(mr_mw=[], mr_gen_mwh=[], mr_co2_tons=[], year=[])

    mr["year"] = year
    mr["mr_mw"] = mr["capacity_mw"] * mr["pct_mr"] / 100.0
    mr["mr_gen_mwh"] = mr["mr_mw"] * 8760.0 * must_run_cf
    mr["mr_co2_tons"] = mr.apply(
        lambda r: r["mr_gen_mwh"]
        * get_emission_rate(r["fuel"], r["hr_weighted"]),
        axis=1,
    )
    return mr
