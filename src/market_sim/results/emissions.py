"""Emissions accounting from dispatch results.

Converts a thermal dispatch schedule into hourly system-wide pollutant
totals. Both functions follow the same vectorized pattern: weight each
generator's hourly output by its per-MWh emission rate and sum across the
fleet.
"""

import numpy as np


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
