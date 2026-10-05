"""closeout-CAISO-w5 D1: the CT heat-rate crosswalk-remap companion.

``measured_ct_heat_rates_crosswalk_remap`` makes the CT loader read the
``-ctremap-`` companion: the incumbent CAISO artifact byte-for-byte plus the
rows of the plants CEMS files under a legacy facility (Carlsbad 302 -> 59002,
King City 10294 -> 55811). Off, the loader and the fleet selector are unchanged.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from market_sim.config.paths import PROCESSED_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import campd
from market_sim.data.fleet.campd_bins import (
    CT_REMAP_TAG,
    measured_ct_heat_rate_selector,
    measured_ct_heat_rates,
)

INCUMBENT = Path(PROCESSED_DIR) / "campd_ct_heat_rates_CAISO.csv"
COMPANION = Path(PROCESSED_DIR) / f"campd_ct_heat_rates-{CT_REMAP_TAG}-CAISO.csv"


def test_remap_rows_present_for_carlsbad_and_king_city():
    """The remap table re-keys Carlsbad's five CTs and King City's unit 2."""
    for unit in ("6", "7", "8", "9", "10"):
        assert campd.CAMPD_UNIT_PLANT_REMAP[(302, unit)] == 59002
    assert campd.CAMPD_UNIT_PLANT_REMAP[(10294, "2")] == 55811


@pytest.mark.skipif(not COMPANION.exists(), reason="companion not hydrated")
def test_companion_is_incumbent_plus_remapped_plants_only():
    """Plant-scoped splice: every incumbent line kept verbatim, only new plants added."""
    inc = INCUMBENT.read_text().splitlines()
    comp = COMPANION.read_text().splitlines()
    assert comp[: len(inc)] == inc
    added = comp[len(inc) :]
    assert added, "companion adds no rows"
    header = inc[0].split(",")
    pi = header.index("plant_code")
    assert {line.split(",")[pi] for line in added} == {"59002", "55811"}


@pytest.mark.skipif(not COMPANION.exists(), reason="companion not hydrated")
def test_loader_adds_only_the_remapped_plants():
    """Armed, the rate map gains Carlsbad / King City; every other plant is identical."""
    base = measured_ct_heat_rates("CAISO", 2020)
    remap = measured_ct_heat_rates("CAISO", 2020, crosswalk_remap=True)
    assert set(remap) - set(base) == {59002, 55811}
    assert all(remap[k] == base[k] for k in base)
    assert 8.0 < remap[59002] < 10.5  # an LMS100 loaded rate, net basis


def test_selector_plain_bool_unless_both_flags():
    """Off, the selector returns the plain bool; armed, the companion tag."""
    on = ScenarioConfig(mode="backcast", measured_ct_heat_rates=True)
    assert measured_ct_heat_rate_selector(on) is True
    off = ScenarioConfig(mode="backcast", measured_ct_heat_rates=False)
    assert measured_ct_heat_rate_selector(off) is False
    armed = ScenarioConfig(
        mode="backcast",
        measured_ct_heat_rates=True,
        measured_ct_heat_rates_crosswalk_remap=True,
    )
    assert measured_ct_heat_rate_selector(armed) == CT_REMAP_TAG
    # the remap gate alone never turns the measured swap on
    only_remap = ScenarioConfig(
        mode="backcast",
        measured_ct_heat_rates=False,
        measured_ct_heat_rates_crosswalk_remap=True,
    )
    assert measured_ct_heat_rate_selector(only_remap) is False


def test_armed_without_companion_raises(tmp_path, monkeypatch):
    """An absent companion raises instead of silently pricing on the incumbent."""
    import market_sim.data.fleet.campd_bins as cb

    monkeypatch.setattr(cb, "PROCESSED_DIR", tmp_path)
    cb.measured_ct_heat_rates.cache_clear()
    try:
        with pytest.raises(FileNotFoundError):
            cb.measured_ct_heat_rates("CAISO", 2020, crosswalk_remap=True)
    finally:
        cb.measured_ct_heat_rates.cache_clear()
