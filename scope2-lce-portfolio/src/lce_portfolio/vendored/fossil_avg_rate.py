"""Vendored hourly fossil-only average CO2 rate logic (copied from market_sim).

=============================================================================
VENDORING HEADER (keep current — see ``vendored/README.md``)
-----------------------------------------------------------------------------
WHAT was copied:
  * ``compute_fossil_avg_rate`` — hourly fossil-only average CO2 emission
    rate (tCO2/MWh) from a ``(n_gen, T)`` dispatch schedule and a
    ``(n_gen,)`` per-generator emission-rate array: tCO2 emitted by fossil
    generation each hour divided by fossil MWh generated that hour, with
    zero-carbon generators excluded from both numerator and denominator.
    Zero-fossil-dispatch hours return 0.0 (nothing emitting to attribute),
    never nan/inf. This is the location-based average emission factor used
    for attributional Scope 2 accounting of unmatched grid purchases
    (ADR 0013).

FROM (upstream file):
  src/market_sim/results/emissions.py::compute_fossil_avg_rate

UPSTREAM COMMIT at copy time (``git rev-parse HEAD``):
  ea2fa86c78e9243876013501bd8d8a819d8670bd (the upstream function is
  introduced in the same change-set as this copy, on branch
  claude/scope2-marginal-emission-rates-nsr1zv; both bodies are identical
  at creation).

HOW to re-sync:
  1. Diff ``compute_fossil_avg_rate`` here against the current
     ``src/market_sim/results/emissions.py``.
  2. Re-copy the body verbatim if it changed; the only local adaptation is
     the docstring's upstream pointer (no ``market_sim`` import here, ever).
  3. Bump the UPSTREAM COMMIT line above to the new HEAD.
  4. Parity is enforced by ``tests/test_emissions.py::TestVendoredParityScope2``
     in the *market_sim* test tree (the parity test imports market_sim, so it
     cannot live in this package's suite).
=============================================================================

The function is pure (numpy in, numpy out), deterministic, and vectorized —
no per-hour Python loops, no filesystem or ``market_sim`` dependency — so
the tool stays 100% standalone.
"""

from __future__ import annotations

import numpy as np


def compute_fossil_avg_rate(
    dispatch: np.ndarray, emission_rates: np.ndarray
) -> np.ndarray:
    """Return the hourly fossil-only average CO2 emission rate (tCO2/MWh).

    For each hour ``t``::

        rate[t] = Σ_g dispatch[g, t] × emission_rates[g]   (over fossil g)
                  ------------------------------------------------------
                  Σ_g dispatch[g, t]                       (over fossil g)

    i.e. the tCO2 emitted by fossil generation that hour divided by the
    fossil MWh generated that hour — the average carbon intensity of the
    *emitting* fleet, not of the whole system (zero-carbon generation is
    excluded from both numerator and denominator). Fossil generators are
    identified as ``emission_rates > 0``: in the upstream market simulator
    only fossil fuels carry a nonzero CO2 factor (nuclear, wind, solar,
    hydro, geothermal, imports, hydrogen, and biogenic biomass are all zero).

    (Vendored verbatim from
    ``market_sim.results.emissions.compute_fossil_avg_rate``.)

    Args:
        dispatch: Thermal generation of shape ``(n_gen, T)`` in MWh/hour.
        emission_rates: Per-generator CO2 rate of shape ``(n_gen,)`` in
            tCO2/MWh.

    Returns:
        Hourly fossil-fleet average CO2 rate of shape ``(T,)`` in tCO2/MWh.
        Hours with zero fossil dispatch return ``0.0`` (no fossil generation
        that hour means there is nothing to attribute at the fossil rate),
        never ``nan``/``inf``.
    """
    dispatch = np.asarray(dispatch, dtype=float)
    emission_rates = np.asarray(emission_rates, dtype=float)
    fossil = emission_rates > 0.0  # emitting (fossil) generators only
    fossil_co2 = (dispatch[fossil] * emission_rates[fossil][:, None]).sum(axis=0)
    fossil_mwh = dispatch[fossil].sum(axis=0)
    # Zero-fossil hours: no emitting generation to average -> rate 0, not nan.
    return np.divide(
        fossil_co2,
        fossil_mwh,
        out=np.zeros_like(fossil_co2),
        where=fossil_mwh > 0.0,
    )
