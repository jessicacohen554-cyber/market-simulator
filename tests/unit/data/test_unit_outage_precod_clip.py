"""``unit_outage_precod_clip``: a new unit's pre-commercial window hours (soco-67).

The CAMPD deriver fills a unit's hours absent from the record as dark, so a unit
that enters the record before its first output carries a window from the start
of its record year, while the COD ramp already holds the same not-yet-commercial
capacity offline (rule 19 ``[R-ONE-MECH]``). The gate is the REGISTERED channel
(rule 24 ``[R-REGISTRY]``). Evidence: ``docs/handoffs/r-soco/FINDING-soco-67-2026-09-25.md``.
"""

import pandas as pd
import pytest

import market_sim.data.outages as om
from market_sim.config.scenarios import ScenarioConfig, cache_key_drop_defaults


class TestRegistration:
    """Registered, default-off, key-stable at its default."""

    def test_defaults_off(self):
        assert ScenarioConfig().unit_outage_precod_clip is False

    def test_is_dropped_from_the_cache_key_at_its_frozen_default(self):
        assert cache_key_drop_defaults()["unit_outage_precod_clip"] is False

    def test_arming_it_changes_the_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_precod_clip=True)
        assert base.cache_key() != armed.cache_key()


def _events(*rows):
    cols = [
        "facility_id",
        "unit_id",
        "unit_capacity_mw",
        "plant_group",
        "outage_start",
        "outage_end",
        "duration_days",
    ]
    return pd.DataFrame([dict(zip(cols, r)) for r in rows])


@pytest.fixture
def world(monkeypatch):
    """Plant 3 (AL) has a CC bin whose new constituent reaches COD 2023-11.

    Unit ``8`` is absent from the 2022 record (new); unit ``6A`` is present.
    """
    monkeypatch.setattr(
        "market_sim.data.cod_ramp.load_unit_cod_map",
        lambda: {(3, "gas_cc"): ((1000.0, 2000, 5), (774.0, 2023, 11))},
    )
    monkeypatch.setattr(om, "_eia860_plant_states", lambda d: {3: "AL"})
    record = {("AL", 2022): frozenset({(3, "6A")})}
    monkeypatch.setattr(om, "_campd_record_units", lambda s, y: record.get((s, y)))

    class _Dir:
        @staticmethod
        def glob(pattern):
            from pathlib import Path

            return [Path("AL_2022.parquet"), Path("AL_2023.parquet")]

    monkeypatch.setattr(om, "CAMPD_UNIT_LEVEL_DIR", _Dir)
    return om


class TestClip:
    """Each admission condition is categorical and each one is necessary."""

    def test_clips_a_new_units_window_to_the_bins_cod_month(self, world):
        out = world.clip_precod_unit_windows(
            _events((3, "8", 747.0, "CC_REGULAR", "2023-01-01", "2023-12-12", 345.6))
        )
        assert out.outage_start.tolist() == ["2023-11-01"]
        assert out.outage_end.tolist() == ["2023-12-12"]
        assert out.duration_days.tolist() == [41.0]

    def test_drops_a_window_wholly_before_the_cod_month(self, world):
        out = world.clip_precod_unit_windows(
            _events((3, "8", 747.0, "CC_REGULAR", "2023-01-01", "2023-08-07", 218.3))
        )
        assert out.empty

    def test_an_existing_unit_is_never_clipped(self, world):
        ev = _events((3, "6A", 308.0, "CC_REGULAR", "2023-02-28", "2023-05-31", 91.5))
        out = world.clip_precod_unit_windows(ev)
        pd.testing.assert_frame_equal(out.reset_index(drop=True), ev)

    def test_no_later_cod_leaves_the_window(self, world):
        ev = _events((3, "8", 747.0, "CC_REGULAR", "2024-01-26", "2024-02-06", 10.6))
        out = world.clip_precod_unit_windows(ev)
        pd.testing.assert_frame_equal(out.reset_index(drop=True), ev)

    def test_another_bins_cod_does_not_reach(self, world):
        ev = _events((3, "8", 747.0, "COAL_BIT", "2023-01-01", "2023-12-12", 345.6))
        out = world.clip_precod_unit_windows(ev)
        pd.testing.assert_frame_equal(out.reset_index(drop=True), ev)

    def test_no_earlier_record_year_establishes_nothing(self, world):
        ev = _events((3, "8", 747.0, "CC_REGULAR", "2022-01-01", "2022-12-31", 365.0))
        out = world.clip_precod_unit_windows(ev)
        pd.testing.assert_frame_equal(out.reset_index(drop=True), ev)
