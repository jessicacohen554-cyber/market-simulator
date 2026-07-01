"""Tests for load intake, aggregation, and growth."""

import numpy as np
import pandas as pd

from lce_portfolio.config import HOURS_PER_YEAR, PortfolioConfig
from lce_portfolio.intake import (
    aggregate_by_hour_iso,
    apply_load_growth,
    prepare_load,
)


def _long_df() -> pd.DataFrame:
    """Two facilities in one ISO plus a second ISO, a few hours each."""
    rows = []
    for h in range(HOURS_PER_YEAR):
        rows.append({"hour": h, "iso": "A", "facility": "f1", "load_mwh": 10.0})
        rows.append({"hour": h, "iso": "A", "facility": "f2", "load_mwh": 5.0})
        rows.append({"hour": h, "iso": "B", "facility": "g1", "load_mwh": 7.0})
    return pd.DataFrame(rows)


def test_aggregate_sums_facilities_per_iso() -> None:
    """Facilities within an (iso, hour) are summed; ISOs kept separate."""
    agg = aggregate_by_hour_iso(_long_df())
    assert set(agg) == {"A", "B"}
    assert agg["A"].shape == (HOURS_PER_YEAR,)
    assert np.allclose(agg["A"], 15.0)  # 10 + 5
    assert np.allclose(agg["B"], 7.0)


def test_growth_compounds() -> None:
    """Growth applies a compound multiplier, shape-preserving."""
    load = np.ones(HOURS_PER_YEAR)
    grown = apply_load_growth(load, 0.02, 5)
    assert np.allclose(grown, 1.02**5)


def test_prepare_load_end_to_end(tmp_path) -> None:
    """prepare_load reads, aggregates, and grows for one ISO."""
    path = tmp_path / "load.csv"
    _long_df().to_csv(path, index=False)
    cfg = PortfolioConfig(iso="A", load_growth_rate=0.1, load_growth_years=1)
    load = prepare_load(path, "A", cfg)
    assert load.shape == (HOURS_PER_YEAR,)
    assert np.allclose(load, 15.0 * 1.1)
