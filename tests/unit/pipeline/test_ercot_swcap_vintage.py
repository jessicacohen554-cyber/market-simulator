"""Tests for ``ScenarioConfig.ercot_swcap_vintage`` (R-ERCOT-14).

The flag puts ERCOT's offer cap, ORDC VOLL and LP shed penalty on one
published cap: armed, ``voll`` follows ``ordc_voll`` and
``pipeline.spec.shed_penalty_voll`` returns it. Off, or for any other ISO,
nothing moves.
"""

from types import SimpleNamespace

from market_sim.config.constants import ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.pipeline import shed_penalty_voll
from market_sim.pipeline.solve import _swcap_clip_level

_ISO_ERCOT = SimpleNamespace(voll=5000.0)


def _ercot(year: int, **kw) -> ScenarioConfig:
    order = ERCOT_ORDC_PUBLISHED_ORDER_PARAMS_BY_YEAR[year]
    return ScenarioConfig(
        iso="ERCOT", mode="backcast", weather_year=year
    ).with_overrides(**order, **kw)


def test_off_is_byte_identical():
    """Off: voll, shed penalty and cache key are the pre-flag values."""
    cfg = _ercot(2019)
    assert cfg.voll == 5000.0
    assert shed_penalty_voll(cfg, _ISO_ERCOT) == 5000.0
    assert cfg.cache_key() == _ercot(2019, ercot_swcap_vintage=False).cache_key()


def test_armed_pre2022_moves_all_three_together():
    """Armed in 2019-2021: voll, shed penalty and offer clip read $9,000."""
    for year in (2019, 2020, 2021):
        cfg = _ercot(year, ercot_swcap_vintage=True, ercot_offer_swcap_clip=True)
        assert cfg.voll == 9000.0
        assert shed_penalty_voll(cfg, _ISO_ERCOT) == 9000.0
        assert _swcap_clip_level(cfg) == 9000.0 - 0.01
        assert cfg.cache_key() != _ercot(year, ercot_offer_swcap_clip=True).cache_key()


def test_armed_post2022_is_inert():
    """Armed where the published cap is $5,000: every value is unchanged."""
    for year in (2022, 2023, 2024, 2025):
        cfg = _ercot(year, ercot_swcap_vintage=True)
        assert cfg.voll == 5000.0
        assert shed_penalty_voll(cfg, _ISO_ERCOT) == 5000.0


def test_other_iso_keeps_its_own_cap():
    """Non-ERCOT: the flag never touches voll or the ISOConfig shed penalty."""
    cfg = ScenarioConfig(iso="PJM", ercot_swcap_vintage=True, ordc_voll=9000.0)
    assert cfg.voll == 5000.0
    assert shed_penalty_voll(cfg, SimpleNamespace(voll=2000.0)) == 2000.0
