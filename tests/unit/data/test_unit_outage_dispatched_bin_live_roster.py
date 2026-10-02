"""Unit tests for the LIVE dispatched-bin denominator (closeout-W0, desk ruling D-1).

``ScenarioConfig.unit_outage_dispatched_bin_denominator`` divides each measured
unit outage by the capacity the LP carries ONLINE in the hour,
``D_k(t) = sum_i pmax_i * online_i(month t)``, read off the COD ramp's own
resolver (``cod_ramp.generator_online_mask``). A dated exit cohort is online
through its EIA-860 retirement month only (the COD ramp masks it after), so:

* a cohort retired BEFORE the solve year ("dead") leaves the divide all year —
  the NWPP-NEXT-15 live sub-gate, folded in, its field deleted (rule 26);
* a cohort retiring IN the solve year divides through its retirement month
  (PR #7047) — Scherer 6257 in 2022: unit 4 carried January only;
* a month whose live roster is zero (the whole key is an exit cohort) keeps the
  full-year value, so no key is over-derated or divided by zero;
* a mid-year new build likewise divides only from its COD month.

Every fixture is synthetic, trivial case first (docs/testing.md): one plant, two
cohorts — survivors A (600 MW) and an exit cohort B (400 MW) — and one 300 MW
unit of A out all year.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import outages
from market_sim.data.fleet import Generator
from market_sim.data.fleet import arrays as fleet_arrays_mod
from market_sim.data.fleet.models import _hour_to_month_index
from market_sim.data.outages import (
    ROSTER_MONTHLY_TAG,
    _dispatched_denominator_hourly,
    _unit_outage_factors_from_events,
    dispatched_bin_live_year,
    lp_bin_capacity_index,
)

HOURS = 8760
YEAR = 2022
JAN = _hour_to_month_index(HOURS) == 0


class _Gen:
    """The attributes :func:`lp_bin_capacity_index` and the COD ramp read."""

    def __init__(
        self,
        plant_code,
        plant_group,
        pmax_mw,
        unit_id="",
        retire=None,
        online=(1980, 1),
    ):
        self.plant_code = plant_code
        self.plant_group = plant_group
        self.pmax_mw = pmax_mw
        self.unit_id = unit_id
        self.online_year, self.online_month = online
        self.retirement_year, self.retirement_month = retire or (None, None)
        self.is_campd_bin = False


def _survivors() -> list[_Gen]:
    return [_Gen(100, "COAL_PRB", 600.0, "COAL_GA_p100_committed")]


def _cohort(tag: str = "r202201", mw: float = 400.0) -> list[_Gen]:
    """An exit cohort carrying the retirement its ``_r{yyyy}{mm}`` tag names."""
    ret = (int(tag[1:5]), int(tag[5:7]))
    return [_Gen(100, "COAL_PRB", mw, f"COAL_GA_p100_{tag}_committed", retire=ret)]


@pytest.fixture(autouse=True)
def _no_cod_maps(monkeypatch):
    """No EIA-860 map entry: every row's own dates drive its COD-ramp mask."""
    from market_sim.data import cod_ramp

    monkeypatch.setattr(cod_ramp, "load_cod_map", lambda: {})
    monkeypatch.setattr(cod_ramp, "load_unit_cod_map", lambda: {})


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
            lp_bin_capacity_index(_survivors(), live_year=YEAR), per_unit_clip
        )
        with_b = _factor(
            lp_bin_capacity_index(_survivors() + _cohort(), live_year=YEAR),
            per_unit_clip,
        )
        np.testing.assert_array_equal(with_b[~JAN], no_b[~JAN])
        assert no_b[~JAN] == pytest.approx(0.5)

    @pytest.mark.parametrize("per_unit_clip", [False, True])
    def test_january_includes_the_cohort(self, per_unit_clip):
        with_b = _factor(
            lp_bin_capacity_index(_survivors() + _cohort(), live_year=YEAR),
            per_unit_clip,
        )
        # 300 MW out of the 1,000 MW the LP carries in January.
        assert with_b[JAN] == pytest.approx(0.7)

    def test_without_live_year_the_cohort_divides_all_year(self):
        """``live_year=None`` (outside a COD-ramped backcast): 1,000 MW all year."""
        with_b = _factor(lp_bin_capacity_index(_survivors() + _cohort()))
        assert with_b == pytest.approx(0.7)

    def test_mw_removed_matches_mw_out_every_hour(self):
        """The identity the denominator exists for: share x cap_LP == 300 MW."""
        roster = lp_bin_capacity_index(_survivors() + _cohort(), live_year=YEAR)
        f = _factor(roster)
        cap_lp = np.where(JAN, 1000.0, 600.0)
        np.testing.assert_allclose((1.0 - f) * cap_lp, 300.0)


class TestRoster:
    def test_monthly_entry_holds_the_online_capacity(self):
        roster = dict(
            lp_bin_capacity_index(_survivors() + _cohort("r202203"), live_year=YEAR)
        )
        assert roster[(100, "COAL")] == 1000.0
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)] == (
            (1000.0,) * 3 + (600.0,) * 9
        )

    def test_january_value_is_the_full_year_value_exactly(self):
        gens = [
            _Gen(100, "COAL_PRB", 0.1, "a"),
            _Gen(100, "COAL_PRB", 0.2, "COAL_GA_p100_r202201_x", retire=(2022, 1)),
            _Gen(100, "COAL_PRB", 0.3, "b"),
        ]
        roster = dict(lp_bin_capacity_index(gens, live_year=YEAR))
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)][0] == roster[(100, "COAL")]

    @pytest.mark.parametrize(
        "tag",
        [
            "r202212",  # retires in December: online all year
            "r202306",  # retires after the solve year
        ],
    )
    def test_no_monthly_entry_without_an_in_year_partial_exit(self, tag):
        gens = _survivors() + _cohort(tag)
        assert lp_bin_capacity_index(gens, live_year=YEAR) == lp_bin_capacity_index(
            gens
        )

    def test_byte_identical_without_exit_cohorts(self):
        gens = _survivors() + [_Gen(200, "CC_REGULAR", 500.0, "CC_GA_p200_econ")]
        assert lp_bin_capacity_index(gens, live_year=YEAR) == lp_bin_capacity_index(
            gens
        )

    def test_scalar_consumers_see_only_two_tuples(self):
        roster = lp_bin_capacity_index(_survivors() + _cohort(), live_year=YEAR)
        merged = outages._dispatched_denominator({}, roster)
        assert merged == {(100, "COAL"): 1000.0}


class TestHourly:
    def test_whole_bin_cohort_keeps_the_full_value_once_retired(self):
        """A plant that is ALL exit cohort (Wansley 6052) never divides by 0."""
        roster = lp_bin_capacity_index(_cohort("r202209", 1744.0), live_year=YEAR)
        prof = _dispatched_denominator_hourly(roster, HOURS)[(100, "COAL")]
        assert np.all(prof == 1744.0)

    def test_chp_groups_are_excluded(self):
        gens = [
            _Gen(300, "ST_CHP", 100.0, "a"),
            _Gen(300, "ST_CHP", 50.0, "ST_GA_p300_r202201_x", retire=(2022, 1)),
        ]
        roster = lp_bin_capacity_index(gens, live_year=YEAR)
        assert _dispatched_denominator_hourly(roster, HOURS) == {}

    def test_empty_without_monthly_entries(self):
        assert _dispatched_denominator_hourly(None, HOURS) == {}
        roster = lp_bin_capacity_index(_survivors(), live_year=YEAR)
        assert _dispatched_denominator_hourly(roster, HOURS) == {}


class TestLiveYearAccessor:
    def test_backcast_with_the_companion_returns_the_year(self):
        cfg = ScenarioConfig(
            iso="SOCO", mode="backcast", unit_outage_dispatched_bin_denominator=True
        )
        assert dispatched_bin_live_year(cfg, YEAR) == YEAR

    def test_none_while_the_companion_is_off(self):
        cfg = ScenarioConfig(
            iso="SOCO", mode="backcast", unit_outage_dispatched_bin_denominator=False
        )
        assert dispatched_bin_live_year(cfg, YEAR) is None

    def test_none_without_the_cod_ramp(self):
        """The LP carries the cohort all year, so its full-year MW is right."""
        cfg = ScenarioConfig(
            iso="SOCO",
            mode="backcast",
            unit_outage_dispatched_bin_denominator=True,
            cod_ramp_enabled=False,
        )
        assert dispatched_bin_live_year(cfg, YEAR) is None

    def test_none_without_a_year_or_config(self):
        assert dispatched_bin_live_year(None, YEAR) is None
        cfg = ScenarioConfig(
            iso="SOCO", mode="backcast", unit_outage_dispatched_bin_denominator=True
        )
        assert dispatched_bin_live_year(cfg, None) is None

    def test_none_outside_a_backcast(self):
        cfg = ScenarioConfig(iso="SOCO", unit_outage_dispatched_bin_denominator=True)
        assert dispatched_bin_live_year(cfg, YEAR) is None

    def test_the_live_sub_gate_field_is_deleted(self):
        """Rule 26: the folded sub-gate cannot be set, so it cannot be re-armed."""
        with pytest.raises(TypeError):
            ScenarioConfig(iso="NWPP", unit_outage_dispatched_bin_live_denominator=True)


class TestDeadCohort:
    """A cohort retired before the solve year is offline every hour: excluded."""

    @pytest.mark.parametrize("per_unit_clip", [False, True])
    def test_dead_cohort_excluded_all_year(self, per_unit_clip):
        no_b = _factor(
            lp_bin_capacity_index(_survivors(), live_year=YEAR), per_unit_clip
        )
        with_dead_b = _factor(
            lp_bin_capacity_index(_survivors() + _cohort("r202112"), live_year=YEAR),
            per_unit_clip,
        )
        np.testing.assert_array_equal(with_dead_b, no_b)
        assert with_dead_b == pytest.approx(0.5)  # 300 of the live 600 MW, every hour

    def test_without_live_year_the_dead_cohort_dilutes(self):
        assert _factor(
            lp_bin_capacity_index(_survivors() + _cohort("r202112"))
        ) == pytest.approx(0.7)

    def test_dead_cohort_gets_no_monthly_entry(self):
        roster = lp_bin_capacity_index(
            _survivors() + _cohort("r202112"), live_year=YEAR
        )
        assert roster == (((100, "COAL"), 600.0),)

    def test_dead_and_in_year_cohorts_together(self):
        gens = _survivors() + _cohort("r202112", 200.0) + _cohort("r202201")
        roster = dict(lp_bin_capacity_index(gens, live_year=YEAR))
        assert roster[(100, "COAL")] == 1000.0
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)] == (1000.0,) + (600.0,) * 11
        f = _factor(tuple(sorted(roster.items())))
        np.testing.assert_allclose((1.0 - f) * np.where(JAN, 1000.0, 600.0), 300.0)

    def test_centralia_measured_case(self):
        """NWPP 2021: live BW22 670 MW, the dead 2020-12 BW21 cohort leaves."""
        gens = [
            _Gen(3845, "COAL_BIT", 670.0, "COAL_WA_p3845_committed"),
            _Gen(
                3845,
                "COAL_BIT",
                670.0,
                "COAL_WA_p3845_r202012_committed",
                retire=(2020, 12),
            ),
        ]
        assert dict(lp_bin_capacity_index(gens))[(3845, "COAL")] == 1340.0
        assert dict(lp_bin_capacity_index(gens, live_year=2021))[
            (3845, "COAL")
        ] == pytest.approx(670.0)
        # In its own retirement year (December) it is online all year: kept.
        assert dict(lp_bin_capacity_index(gens, live_year=2020))[
            (3845, "COAL")
        ] == pytest.approx(1340.0)

    def test_pmax_argument_sources_the_mw(self):
        roster = dict(
            lp_bin_capacity_index(
                _survivors() + _cohort("r202112"), np.array([550.0, 700.0]), YEAR
            )
        )
        assert roster[(100, "COAL")] == pytest.approx(550.0)

    def test_a_fully_dead_plant_leaves_the_roster(self):
        assert lp_bin_capacity_index(_cohort("r201905", 500.0), live_year=YEAR) == ()

    def test_a_row_with_no_retirement_is_always_live(self):
        roster = lp_bin_capacity_index(_survivors(), live_year=YEAR)
        assert roster == (((100, "COAL"), 600.0),)


class TestCodRamp:
    """The roster reads the COD ramp's own mask, not a unit-id convention."""

    def test_mid_year_new_build_divides_from_its_cod_month(self):
        new = _Gen(100, "COAL_PRB", 400.0, "COAL_GA_p100_new", online=(YEAR, 7))
        roster = dict(lp_bin_capacity_index(_survivors() + [new], live_year=YEAR))
        assert roster[(100, "COAL")] == 1000.0
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)] == (600.0,) * 6 + (1000.0,) * 6

    def test_future_build_leaves_the_roster(self):
        new = _Gen(100, "COAL_PRB", 400.0, "COAL_GA_p100_new", online=(YEAR + 1, 3))
        assert lp_bin_capacity_index(
            _survivors() + [new], live_year=YEAR
        ) == lp_bin_capacity_index(_survivors(), live_year=YEAR)

    def test_fractional_plant_level_bin(self, monkeypatch):
        """A plant-level bin partly in service divides by its online fraction."""
        monkeypatch.setattr(
            outages,
            "_roster_online_masks",
            lambda gens, year: np.full((len(gens), 12), 0.5),
        )
        roster = dict(lp_bin_capacity_index(_survivors(), live_year=YEAR))
        assert roster[(100, "COAL")] == 600.0
        assert roster[(100, "COAL", ROSTER_MONTHLY_TAG)] == (300.0,) * 12
        f = _factor(tuple(sorted(roster.items())))
        assert f == pytest.approx(0.0)  # 300 MW out of the 300 MW online

    def test_one_ulp_over_one_is_fully_online(self, monkeypatch):
        """A weighted-mean mask a rounding step above 1 adds no monthly entry."""
        from market_sim.data import cod_ramp

        monkeypatch.setattr(
            cod_ramp,
            "generator_online_mask",
            lambda *a: (np.full(12, np.nextafter(1.0, 2.0)), 1980),
        )
        assert lp_bin_capacity_index(
            _survivors(), live_year=YEAR
        ) == lp_bin_capacity_index(_survivors())

    def test_the_mask_is_the_cod_ramps_own(self):
        """Same resolver, same inputs as fleet.arrays' COD ramp."""
        from market_sim.data.cod_ramp import generator_online_mask

        g = _cohort("r202205")[0]
        expect = generator_online_mask(
            100, "COAL_PRB", 1980, 1, 2022, 5, False, {}, {}, YEAR
        )[0]
        np.testing.assert_array_equal(
            outages._roster_online_masks([g], YEAR)[0], expect
        )
        assert expect.tolist() == [1.0] * 5 + [0.0] * 7


class TestAllExitKey:
    """A key that is entirely an in-year exit cohort is never over-derated."""

    @pytest.mark.parametrize("per_unit_clip", [False, True])
    def test_no_over_derate_after_the_whole_key_retires(self, per_unit_clip):
        # 300 MW of a 400 MW all-cohort key out all year; the key exits after
        # January. Every hour divides by 400 MW: 0.25, never 300 / 0.
        roster = lp_bin_capacity_index(_cohort("r202201"), live_year=YEAR)
        f = _factor(roster, per_unit_clip)
        assert np.all(np.isfinite(f))
        assert f == pytest.approx(0.25)
        assert f.min() >= 0.0


_COAL_CLASSES = frozenset({"COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC"})
_SCREENED = dict(
    wefor_residual=0.0,
    unit_outage_short_windows=True,
    unit_outage_dispatched_bin_denominator=True,
    wefor_residual_short_screened_coal=True,
)


def _availability(monkeypatch, **kw) -> np.ndarray:
    """Annual-mean availability of one coal, one CC and one ST-gas row."""
    monkeypatch.setattr(
        fleet_arrays_mod,
        "short_screened_coal_shares",
        lambda year, iso, roster: {(10, "COAL"): 0.5},
    )
    rows = [
        ("COAL_Z_p10_committed", "coal", "COAL_BIT", 10, 1980, 500.0),
        ("CC_REGULAR_Z_p20_committed", "gas", "CC_REGULAR", 20, 2000, 500.0),
        ("ST_GAS_Z_p30_committed", "gas", "ST_GAS", 30, 1970, 300.0),
    ]
    gens = [
        Generator(
            unit_id=u,
            name=u,
            zone="Z",
            fuel_type=f,
            pmax_mw=mw,
            plant_group=g,
            plant_code=c,
            online_year=oy,
            is_campd_bin=True,
        )
        for u, f, g, c, oy, mw in rows
    ]
    cfg = ScenarioConfig(
        iso="NWPP", mode="backcast", weather_year=2021, outage_source="historic", **kw
    )
    av = np.ones((len(gens), HOURS))
    fleet_arrays_mod._availability_matrix(gens, av, HOURS, cfg, "NWPP", 2021, set())
    return av.mean(axis=1)


class TestScreenedCoalFirst:
    """NWPP-NEXT-15's second limb, now part of the screened-coal relief."""

    def test_coal_relieved_on_its_screened_share_only(self, monkeypatch):
        stat = _availability(monkeypatch)
        armed = _availability(
            monkeypatch, **_SCREENED, wefor_residual_groups=_COAL_CLASSES
        )
        np.testing.assert_array_equal(armed[1:], stat[1:])  # CC + ST gas untouched
        assert stat[0] < armed[0]

    def test_coal_blend_independent_of_the_groups(self, monkeypatch):
        """Coal named or not in the groups: the same screened-share blend."""
        named = _availability(
            monkeypatch, **_SCREENED, wefor_residual_groups=_COAL_CLASSES
        )
        miso = _availability(
            monkeypatch,
            **_SCREENED,
            wefor_residual_groups=frozenset({"CC_REGULAR", "ST_GAS", "ST_CHP"}),
        )
        none = _availability(monkeypatch, **_SCREENED)
        assert named[0] == miso[0] == none[0]
        # None groups keep the full cap on the gas classes.
        assert none[1] > named[1]
