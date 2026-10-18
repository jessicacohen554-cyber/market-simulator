"""Tests for the exact-repeat (stale-snapshot) run detector."""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.data.stale_runs import stale_run_mask


def _series_with_run(length: int, total: int = 12, start: int = 4) -> np.ndarray:
    """A strictly moving series with one exact-repeat block of ``length`` hours."""
    values = np.arange(total, dtype=float) * 10.0
    values[start : start + length] = values[start]
    return values


def test_trivial_constant_series_is_one_run():
    assert stale_run_mask(np.full(5, 3.0), 4).all()


def test_moving_series_has_no_run():
    assert not stale_run_mask(np.arange(24, dtype=float), 4).any()


@pytest.mark.parametrize("length, flagged", [(3, False), (4, True), (5, True)])
def test_run_length_boundary(length, flagged):
    mask = stale_run_mask(_series_with_run(length), 4)
    assert mask[4 : 4 + length].all() == flagged
    assert int(mask.sum()) == (length if flagged else 0)
    # Hours either side of the block are never flagged.
    assert not mask[3] and not mask[4 + length]


def test_first_hour_of_a_run_counts():
    mask = stale_run_mask(np.array([1.0, 5.0, 5.0, 5.0, 5.0, 9.0]), 4)
    assert mask.tolist() == [False, True, True, True, True, False]


def test_nan_breaks_a_run():
    values = np.array([5.0, 5.0, np.nan, 5.0, 5.0, 5.0])
    assert not stale_run_mask(values, 4).any()


def test_vector_requires_every_column_to_repeat():
    t = np.arange(10, dtype=float)
    frozen = np.full(10, 7.0)
    full = np.column_stack([frozen, frozen])
    partial = np.column_stack([frozen, t])  # one column frozen, one moving
    assert stale_run_mask(full, 4).all()
    assert not stale_run_mask(partial, 4).any()


def test_vector_partial_freeze_then_full_freeze():
    a = np.array([1, 2, 3, 3, 3, 3, 3, 3, 9, 10], dtype=float)
    b = np.array([1, 2, 3, 4, 5, 5, 5, 5, 9, 10], dtype=float)
    mask = stale_run_mask(np.column_stack([a, b]), 4)
    # Both columns frozen together only over hours 4-7 (b freezes at hour 4).
    assert np.flatnonzero(mask).tolist() == [4, 5, 6, 7]


def test_zero_runs_are_detected_by_the_generic_detector():
    # The detector is value-agnostic; the zero carve-out lives in the fuel mask.
    assert stale_run_mask(np.zeros(6), 4).all()


def test_rejects_degenerate_min_run():
    with pytest.raises(ValueError):
        stale_run_mask(np.ones(5), 1)


def test_rejects_3d_input():
    with pytest.raises(ValueError):
        stale_run_mask(np.ones((2, 2, 2)), 4)
