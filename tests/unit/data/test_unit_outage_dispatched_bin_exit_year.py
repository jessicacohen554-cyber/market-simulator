"""Unit tests for the TIME-WEIGHTED dispatched-bin denominator (closeout-W0, D-1).

``ScenarioConfig.unit_outage_dispatched_bin_denominator`` divides each measured
unit outage by the LP bin's own ``pmax`` sum. When that bin holds an exit cohort
that ``partial_plant_exit_carry`` / ``mid_vintage_exit_carry`` carries for only
PART of the solve year, a full-year sum over-states the bin in every month after
the cohort's retirement (the COD ramp has it offline) and dilutes the survivors'
measured derate — Scherer 6257 in 2022: unit 4 carried January only, the
denominator 3,440 MW all year against 2,580 MW live Feb-Dec.

The repair (no new field, rule 19) time-weights the roster: a bin an in-year
exit touches carries a monthly entry, and the accumulators divide hour by hour.

Every fixture is synthetic, trivial case first (docs/testing.md): one plant, two
cohorts — survivors A (600 MW) and an exit cohort B (400 MW) retiring after
January — and one 300 MW unit of A out all year.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import outages
from market_sim.data.fleet.models import _hour_to_month_index
from market_sim.data.outages import (
    ROSTER_MONTHLY_TAG,
    _dispatched_denominator_hourly,
    _unit_outage_factors_from_events,
    dispatched_bin_exit_year,
    lp_bin_capacity_index,
)

HOURS = 8760
YEAR = 2022
JAN = _hour_to_month_index(HOURS) == 0


class _Gen:
    """The attributes :func:`lp_bin_capacity_index` reads off a generator."""

    def __init__(self, plant_code, plant_group, pmax_mw, unit_id=""):
        self.plant_code = plant_code
        self.plant_group = plant_group
        self.pmax_mw = pmax_mw
        self.unit_id = unit_id


def _survivors() -> list[_Gen]:
    return [_Gen(100, "COAL_PRB", 600.0, "COAL_GA_p100_committed")]


def _cohort(tag: str = "r202201", mw: float = 400.0) -> list[_Gen]:
    return [_Gen(100, "COAL_PRB", mw, f"COAL_GA_p100_{tag}_committed")]


def _events() -> pd.DataFrame:
    """One 300 MW unit of the surviving cohort out for the whole year."""
    return pd.DataFrame(
        [
            {
                "facility_id": 100,
                "unit_id": "1",
                "plant_group": "COAL",
                "unit_capacity_mw": 300.0,
                "outage_start": f"{YEAR - 1}-12-01",
                "outage_end": f"{YEAR + 1}-01-15",
                "duration_days": 400.0,
            }
        ]
    )


@pytest.fixture(autouse=True)
def _no_reconstruction(monkeypatch):
    """The dispatched roster replaces the reconstructed map; keep the latter empty."""
    monkeypatch.setattr(
        outages,
        "_iso_plant_capacity",
        lambda iso, cc_steam_part_reclass=False, cc_nameplate_basis=False: {},
    )
    monkeypatch.setattr(outages, "_fleet_status_index", lambda iso: None)


def _factor(roster, per_unit_clip: bool = False) -> np.ndarray:
    out = _unit_outage_factors_from_events(
        _events(),
        YEAR,
        HOURS,
        "",
        "SOCO",
        per_unit_clip=per_unit_clip,
        lp_bin_capacity=roster,
    )
    return out[(100, "COAL")]


class TestTrivialToy:
    """The charter's case: cohort B exits after January."""

    @pytest.mark.parametrize("per_unit_clip", [False, True])
    def test_feb_dec_derate_equals_the_no_cohort_case(self, per_unit_clip):
        no_b = _factor(
            lp_bin_capacity_index(_survivors(), exit_year=YEAR), per_unit_clip
        )
        with_b = _factor(
            lp_bin_capacity_index(_survivors() + _cohort(), exit_year=YEAR),
            per_unit_clip,
        )
        np.testing.assert_array_equal(with_b[~JAN], no_b[~JAN])
        assert no_b[~JAN] == pytest.approx(0.5)

    @pytest.mark.parametrize("per_unit_clip", [False, True])
    def test_january_includes_the_cohort(self, per_unit_clip):
        with_b = _factor(
            lp_bin_capacity_index(_survivors() + _cohort(), exit_year=YEAR),
            per_unit_clip,
        )
        # 300 MW out of the 1,000 MW the LP carries in January.
        assert with_b[JAN] == pytest.approx(0.7)

    def test_without_exit_year_the_incumbent_dilution_stands(self):
        """``exit_year=None`` is the pre-fix roster: 1,000 MW all year."""
        with_b = _factor(lp_bin_capacity_index(_survivors() + _cohort()))
        assert with_b == pytest.approx(0.7)

    def test_mw_removed_matches_mw_out_every_hour(self):
        """The identity the denominator exists for: share x cap_LP == 300 MW."""
        roster = lp_bin_capacity_index(_survivors() + _cohort(), exit_year=YEAR)
        f = _factor(roster)
        cap_lp = np.where(JAN, 1000.0, 600.0)
        np.testing.assert_allclose((1.0 - f) * cap_lp, 300.0)


class TestRoster:
    def test_monthly_entry_holds_the_online_capacity(self):
        roster = dict(
            lp_bin_capacity_index(_survivors() + _cohort("r202203"), exit_year=YEAR)
        )
        assert roster[(100, "COAL")] == 1000.0
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)] == (
            (1000.0,) * 3 + (600.0,) * 9
        )

    def test_january_value_is_the_full_year_value_exactly(self):
        gens = [
            _Gen(100, "COAL_PRB", 0.1, "a"),
            _Gen(100, "COAL_PRB", 0.2, "COAL_GA_p100_r202201_x"),
            _Gen(100, "COAL_PRB", 0.3, "b"),
        ]
        roster = dict(lp_bin_capacity_index(gens, exit_year=YEAR))
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)][0] == roster[(100, "COAL")]

    @pytest.mark.parametrize(
        "tag",
        [
            "r202212",  # retires in December: online all year
            "r202112",  # retired before the solve year: the live sub-gate's job
            "r202306",  # retires after the solve year
        ],
    )
    def test_no_monthly_entry_without_an_in_year_partial_exit(self, tag):
        gens = _survivors() + _cohort(tag)
        assert lp_bin_capacity_index(gens, exit_year=YEAR) == lp_bin_capacity_index(
            gens
        )

    def test_byte_identical_without_exit_cohorts(self):
        gens = _survivors() + [_Gen(200, "CC_REGULAR", 500.0, "CC_GA_p200_econ")]
        assert lp_bin_capacity_index(gens, exit_year=YEAR) == lp_bin_capacity_index(
            gens
        )

    def test_scalar_consumers_see_only_two_tuples(self):
        roster = lp_bin_capacity_index(_survivors() + _cohort(), exit_year=YEAR)
        merged = outages._dispatched_denominator({}, roster)
        assert merged == {(100, "COAL"): 1000.0}


class TestHourly:
    def test_whole_bin_cohort_keeps_the_full_value_once_retired(self):
        """A plant that is ALL exit cohort (Wansley 6052) never divides by 0."""
        roster = lp_bin_capacity_index(_cohort("r202209", 1744.0), exit_year=YEAR)
        prof = _dispatched_denominator_hourly(roster, HOURS)[(100, "COAL")]
        assert np.all(prof == 1744.0)

    def test_chp_groups_are_excluded(self):
        gens = [
            _Gen(300, "ST_CHP", 100.0, "a"),
            _Gen(300, "ST_CHP", 50.0, "ST_GA_p300_r202201_x"),
        ]
        roster = lp_bin_capacity_index(gens, exit_year=YEAR)
        assert _dispatched_denominator_hourly(roster, HOURS) == {}

    def test_empty_without_monthly_entries(self):
        assert _dispatched_denominator_hourly(None, HOURS) == {}
        roster = lp_bin_capacity_index(_survivors(), exit_year=YEAR)
        assert _dispatched_denominator_hourly(roster, HOURS) == {}


class TestExitYearAccessor:
    def test_backcast_with_the_companion_returns_the_year(self):
        cfg = ScenarioConfig(
            iso="SOCO", mode="backcast", unit_outage_dispatched_bin_denominator=True
        )
        assert dispatched_bin_exit_year(cfg, YEAR) == YEAR

    def test_none_while_the_companion_is_off(self):
        cfg = ScenarioConfig(
            iso="SOCO", mode="backcast", unit_outage_dispatched_bin_denominator=False
        )
        assert dispatched_bin_exit_year(cfg, YEAR) is None

    def test_none_without_the_cod_ramp(self):
        """The LP carries the cohort all year, so its full-year MW is right."""
        cfg = ScenarioConfig(
            iso="SOCO",
            mode="backcast",
            unit_outage_dispatched_bin_denominator=True,
            cod_ramp_enabled=False,
        )
        assert dispatched_bin_exit_year(cfg, YEAR) is None

    def test_none_without_a_year_or_config(self):
        assert dispatched_bin_exit_year(None, YEAR) is None
        cfg = ScenarioConfig(
            iso="SOCO", mode="backcast", unit_outage_dispatched_bin_denominator=True
        )
        assert dispatched_bin_exit_year(cfg, None) is None
