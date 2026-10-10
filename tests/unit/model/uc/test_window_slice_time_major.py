"""The window slicer takes a time-major ``(T, n_links)`` transfer limit with it.

ERCOT's measured GTC overlay hands ``ttc`` / ``ttc_import`` to the LP as
``(T, n_links)`` (``lp/bounds.py`` accepts both the static ``(n_links,)`` and
the per-hour form). The UC window slices every hourly input to ``[t0, t1)``;
a time-major array left at ``T`` rows cannot broadcast into the window's flow
bounds (the UC-2-ERCOT L1 gate stop, 2026-10-10).
"""

from __future__ import annotations

import numpy as np

from market_sim.model.uc.window import _slice_obj, slice_window_inputs

from .conftest import toy_inputs


def test_slice_obj_time_major_2d_and_static_1d() -> None:
    T, t0, t1 = 48, 10, 22
    ttc_hourly = np.arange(T * 3, dtype=float).reshape(T, 3)
    ttc_static = np.array([1.0, 2.0, 3.0])
    hour_minor = np.arange(2 * T, dtype=float).reshape(2, T)
    out = _slice_obj(
        {"ttc": ttc_hourly, "static": ttc_static, "minor": hour_minor}, t0, t1, T
    )
    assert out["ttc"].shape == (t1 - t0, 3)
    np.testing.assert_array_equal(out["ttc"], ttc_hourly[t0:t1, :])
    assert out["static"] is ttc_static  # no T axis: passes through untouched
    np.testing.assert_array_equal(out["minor"], hour_minor[:, t0:t1])


def test_window_inputs_carry_hourly_ttc_at_window_length() -> None:
    T, t0, t1 = 48, 0, 12
    _gens, fa, demand, _mc, dk = toy_inputs(T)
    dk = {**dk, "ttc": np.full((T, 1), 50.0), "ttc_import": np.full((T, 1), 40.0)}
    inputs = slice_window_inputs(fa, demand, dk, t0, t1)
    assert inputs.kwargs["ttc"].shape == (t1 - t0, 1)
    assert inputs.kwargs["ttc_import"].shape == (t1 - t0, 1)
