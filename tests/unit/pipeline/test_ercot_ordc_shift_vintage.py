"""Tests for the R-ERCOT-22 ORDC LOLP curve-shift vintage.

PUCT Project 48551 moved ERCOT's LOLP curve right in two 0.25-sigma steps
(2019-03-01, 2020-03-01). ``ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR`` carries
the year-grain value and ``pipeline.backcast_config`` applies it at the one
seam that already vintages ``ordc_voll`` / ``ordc_mcl_mw``: only 2019 moves.
"""

from market_sim.config.constants import ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline.backcast_config import backcast_config


def test_table_shift_is_published_step():
    """2019 carries the first 0.25-sigma step; 2020-2025 the shipped 0.5."""
    shipped = ScenarioConfig().ordc_lolp_shift_sigma
    assert (
        ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[2019]["ordc_lolp_shift_sigma"] == 0.25
    )
    for year in range(2020, 2026):
        assert (
            ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]["ordc_lolp_shift_sigma"]
            == shipped
        )


def test_backcast_config_resolves_shift_for_ercot_only():
    """The seam applies the shift to ERCOT 2019 and nowhere else."""
    assert backcast_config(2019, "ERCOT", 24, 2.5).ordc_lolp_shift_sigma == 0.25
    assert backcast_config(2024, "ERCOT", 24, 2.5).ordc_lolp_shift_sigma == 0.5
    assert backcast_config(2019, "PJM", 24, 2.5).ordc_lolp_shift_sigma == 0.5


def test_post_2019_configs_byte_identical():
    """2020-2025 resolve to exactly the shipped shift, so their keys are unmoved by it."""
    for year in range(2020, 2026):
        cfg = backcast_config(year, "ERCOT", 24, 2.5)
        assert cfg.ordc_lolp_shift_sigma == ScenarioConfig().ordc_lolp_shift_sigma
