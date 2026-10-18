"""Exact-repeat ("stale snapshot") run detection for hourly measured series.

EIA-930 sometimes republishes one stale snapshot of a balancing authority's
record for many consecutive hours: demand, generation by fuel and the
sub-BA demands all freeze at one value while the real system moves
(``docs/records/spp/FINDING-spp-south-demand-flatruns-2026-10-18.md``). The
detector here is the definition the owner ruled (R22 / R23): an hour is stale
when it belongs to a block of consecutive hours whose values are EXACTLY
identical, of length at least ``min_run``.

For a vector series (``(T, k)``) the whole row must repeat: a block is stale
only when every column holds its value. A partial freeze (some columns
constant, others moving) is not a stale snapshot under this definition.
A NaN never equals anything, so a missing hour ends a run.
"""

from __future__ import annotations

import numpy as np


def stale_run_mask(values: np.ndarray, min_run: int) -> np.ndarray:
    """Return a ``(T,)`` bool mask of hours inside exact-repeat runs >= ``min_run``.

    Args:
        values: ``(T,)`` scalar series or ``(T, k)`` vector series.
        min_run: Minimum run length in hours (the first hour of a run counts:
            ``[5, 5, 5, 5]`` is a run of 4).

    Returns:
        Boolean mask, ``True`` at every hour of a qualifying run.

    Raises:
        ValueError: if ``min_run < 2`` or ``values`` is not 1-D / 2-D.
    """
    if min_run < 2:
        raise ValueError(f"min_run must be >= 2, got {min_run}")
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 1:
        arr = arr[:, None]
    if arr.ndim != 2:
        raise ValueError(f"values must be 1-D or 2-D, got shape {arr.shape}")
    n = arr.shape[0]
    if n == 0:
        return np.zeros(0, dtype=bool)
    # same[t] — hour t repeats hour t-1 in every column (NaN != NaN ends a run).
    same = np.zeros(n, dtype=bool)
    same[1:] = np.all(arr[1:] == arr[:-1], axis=1)
    # Run ids: a new run starts wherever ``same`` is False.
    run_id = np.cumsum(~same)
    lengths = np.bincount(run_id)
    return lengths[run_id] >= min_run
