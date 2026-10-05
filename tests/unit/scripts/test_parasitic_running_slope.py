"""Tests for the running-slope parasitic factor and the measured-HR net rebase (closeout-SOCO-w3)."""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.data.derive_parasitic_load import running_parasitic_factors  # noqa: E402
from scripts.data.rebase_measured_hr_parasitic import rebase  # noqa: E402


def _months(
    pid: int, slope: float, intercept: float, gross: np.ndarray
) -> pd.DataFrame:
    """Monthly rows whose net is exactly ``intercept + slope * gross``."""
    return pd.DataFrame(
        {
            "plant_id": pid,
            "year": 2021,
            "month": np.arange(1, len(gross) + 1),
            "gross_mwh": gross,
            "net_mwh": intercept + slope * gross,
        }
    )


def test_slope_recovers_running_factor_and_ignores_offline_draw() -> None:
    """A plant with a fixed offline draw gets its running factor, not the annual ratio."""
    gross = np.linspace(50_000, 400_000, 12)
    m = _months(1, 0.93, -12_000.0, gross)
    out = running_parasitic_factors(m, {1: {"COAL"}})
    assert len(out) == 1
    assert abs(out.parasitic_factor.iloc[0] - 0.93) < 1e-6
    assert out.source.iloc[0] == "measured_running"
    annual = m.net_mwh.sum() / m.gross_mwh.sum()
    assert annual < 0.93  # the annual ratio carries the offline draw


def test_ct_mixed_positive_intercept_and_out_of_band_are_not_written() -> None:
    """CT, mixed-family, positive-intercept and out-of-band plants keep their class default."""
    gross = np.linspace(50_000, 400_000, 12)
    m = pd.concat(
        [
            _months(2, 0.95, -1_000.0, gross),  # CT
            _months(3, 0.95, -1_000.0, gross),  # mixed COAL + CC
            _months(4, 0.95, 5_000.0, gross),  # positive intercept
            _months(5, 0.70, -1_000.0, gross),  # below band
        ]
    )
    fams = {2: {"CT"}, 3: {"COAL", "CC"}, 4: {"CC"}, 5: {"ST"}}
    assert running_parasitic_factors(m, fams).empty


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
    assert out.flag.iloc[0] == "above_physical_band"
    assert out.heat_rate.iloc[1] == 10.0 and out.heat_rate.iloc[2] == 7.0
