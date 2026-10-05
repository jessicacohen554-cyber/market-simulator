"""Tests for the measured-HR net rebase onto measured parasitic factors (closeout-SOCO-w3p)."""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.rebase_measured_hr_parasitic import rebase  # noqa: E402


def test_rebase_moves_only_measured_plants_and_reflags_band() -> None:
    """Net HR moves by old/new factor for measured plants; others and identity rows stay."""
    t = pd.DataFrame(
        {
            "plant_code": [1, 2, 3],
            "parasitic_factor": [0.93, 0.93, 0.975],
            "heat_rate": [10.0, 10.0, 7.0],
            "model_heat_rate_egrid": [11.0, 11.0, 7.5],
            "model_over_measured": [1.1, 1.1, 1.0714],
            "flag": ["ok", "ok", "eia923_identity"],
        }
    )
    out, n = rebase(t, {1: 0.91, 3: 0.99}, lo=8.0, hi=10.1)
    assert n == 1
    assert abs(out.heat_rate.iloc[0] - round(10.0 * 0.93 / 0.91, 4)) < 1e-9
    assert out.parasitic_factor.iloc[0] == 0.91
    assert (
        abs(out.model_over_measured.iloc[0] - round(11.0 / out.heat_rate.iloc[0], 4))
        < 1e-9
    )
    assert out.flag.iloc[0] == "above_physical_band"
    assert out.heat_rate.iloc[1] == 10.0 and out.heat_rate.iloc[2] == 7.0


def test_rebase_is_a_no_op_without_measured_factors() -> None:
    """An empty factor map moves nothing."""
    t = pd.DataFrame(
        {
            "plant_code": [1],
            "parasitic_factor": [0.93],
            "heat_rate": [10.0],
            "model_heat_rate_egrid": [11.0],
            "model_over_measured": [1.1],
            "flag": ["ok"],
        }
    )
    out, n = rebase(t, {}, lo=8.0, hi=27.0)
    assert n == 0
    pd.testing.assert_frame_equal(out, t)
