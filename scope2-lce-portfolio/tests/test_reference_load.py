"""Tests for the stylized ADR-ratification reference load generator.

Data-free and RNG-free: scripts/make_reference_load.py is a pure function of
its module constants, so determinism is checked by re-running and comparing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from make_reference_load import (  # noqa: E402
    AVG_LOAD_MW,
    DIURNAL_SWING_FRACTION,
    HOURS_PER_YEAR,
    ISOS,
    build_reference_load,
    make_shape,
)

from lce_portfolio.intake import aggregate_by_hour_iso, load_intake  # noqa: E402


def test_shape_is_deterministic() -> None:
    """Two independent calls produce byte-identical arrays (no RNG/wall-clock)."""
    a = make_shape()
    b = make_shape()
    assert np.array_equal(a, b)


def test_shape_mean_and_bounds() -> None:
    """Annual mean is exactly AVG_LOAD_MW; swing stays within +/-10%."""
    shape = make_shape()
    assert shape.shape == (HOURS_PER_YEAR,)
    assert abs(shape.mean() - AVG_LOAD_MW) < 1e-9
    lo = AVG_LOAD_MW * (1.0 - DIURNAL_SWING_FRACTION)
    hi = AVG_LOAD_MW * (1.0 + DIURNAL_SWING_FRACTION)
    assert shape.min() >= lo - 1e-9
    assert shape.max() <= hi + 1e-9


def test_build_reference_load_replicates_shape_across_all_six_isos() -> None:
    """Long-form frame: every ISO carries the identical 8760 shape."""
    df = build_reference_load()
    assert set(df["iso"].unique()) == set(ISOS)
    assert len(ISOS) == 6
    assert len(df) == HOURS_PER_YEAR * len(ISOS)
    assert set(df.columns) >= {"hour", "iso", "load_mwh", "facility"}

    shape = make_shape()
    for iso in ISOS:
        sub = df[df["iso"] == iso].sort_values("hour")
        assert np.allclose(sub["load_mwh"].to_numpy(), shape)


def test_build_reference_load_is_deterministic_across_calls() -> None:
    """Re-running the builder reproduces the identical frame (same dtype/values)."""
    a = build_reference_load()
    b = build_reference_load()
    assert a.equals(b)


def test_reference_load_passes_intake_validation(tmp_path) -> None:
    """The generated CSV satisfies lce_portfolio.intake's load-intake contract:
    required columns present, hour in [0, 8759], full calendar per ISO."""
    df = build_reference_load()
    path = tmp_path / "reference_load_100mw.csv"
    df.to_csv(path, index=False, float_format="%.3f")

    intake_df = load_intake(path)  # raises on missing columns / bad hour range
    by_iso = aggregate_by_hour_iso(intake_df)  # raises on dup rows / missing hours
    assert set(by_iso) == set(ISOS)
    for iso in ISOS:
        assert by_iso[iso].shape == (HOURS_PER_YEAR,)
        assert abs(by_iso[iso].mean() - AVG_LOAD_MW) < 1e-6
