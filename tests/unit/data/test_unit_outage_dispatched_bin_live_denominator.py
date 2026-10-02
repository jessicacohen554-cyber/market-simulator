"""Unit tests for the LIVE-capacity dispatched-bin denominator (NWPP-NEXT-15).

``ScenarioConfig.unit_outage_dispatched_bin_live_denominator`` is a sub-gate of
miso-266's ``unit_outage_dispatched_bin_denominator``. The parent reads the
derate denominator off the dispatched fleet's own per-bin ``pmax``; on NWPP that
bin still carries DATED EXIT COHORTS (``fleet/assembly.py``'s
``_p{plant}_r{yyyy}{mm}`` bins) that retired before the solve year and sit at
zero availability all year, so the divide is diluted (Centralia 3845: 1,340 MW
against the live 670; Colstrip 6076: 2,094 against 1,480 —
FINDING-nwppnext13 §1.3). Armed, the roster drops those rows.

Its second limb re-orders the existing WEFOR residual relief so that, with the
miso-273 screened-coal relief armed, coal is relieved on its screened share
only and ``wefor_residual_groups`` scopes the full cap for non-coal classes.

Every fixture is synthetic (trivial cases first, per docs/testing.md):

(a) default-off leaves the roster — and so every denominator — identical;
(b) armed drops a dead cohort and keeps the live unit, and a cohort retiring IN
    the solve year stays (it is live through its retirement month);
(c) armed without the parent raises at the point of use;
(d) the coal-only scoping leaves CC / ST gas availability untouched, and is
    inert while the sub-gate is off;
plus registration, so the pinned default cache key never moves.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data import outages
from market_sim.data.fleet import Generator
from market_sim.data.fleet import arrays as fleet_arrays_mod
from market_sim.data.outages import (
    _unit_outage_factors_from_events,
    dispatched_bin_live_year,
    exit_cohort_tag,
    lp_bin_capacity_index,
)

HOURS = 8760
YEAR = 2021


class _Gen:
    """The attributes :func:`lp_bin_capacity_index` reads off a generator."""

    def __init__(self, plant_code, plant_group, pmax_mw, unit_id=""):
        self.plant_code = plant_code
        self.plant_group = plant_group
        self.pmax_mw = pmax_mw
        self.unit_id = unit_id


def _centralia() -> list[_Gen]:
    """Centralia 3845 in 2021: live BW22 (670 MW) + the dead 2020-12 BW21 cohort."""
    return [
        _Gen(3845, "COAL_BIT", 670.0, "COAL_WA_p3845_committed"),
        _Gen(3845, "COAL_BIT", 670.0, "COAL_WA_p3845_r202012_committed"),
    ]


class TestDefaultOff:
    """(a) the sub-gate off is the miso-266 roster, byte-identical."""

    def test_field_defaults_off(self):
        assert (
            ScenarioConfig(iso="NWPP").unit_outage_dispatched_bin_live_denominator
            is False
        )

    def test_live_year_is_none_while_off(self):
        cfg = ScenarioConfig(iso="NWPP", unit_outage_dispatched_bin_denominator=True)
        assert dispatched_bin_live_year(cfg, YEAR) is None
        assert dispatched_bin_live_year(None, YEAR) is None

    def test_roster_identical_with_live_year_none(self):
        gens = _centralia()
        assert lp_bin_capacity_index(gens) == lp_bin_capacity_index(
            gens, live_year=None
        )
        assert dict(lp_bin_capacity_index(gens))[(3845, "COAL")] == 1340.0


class TestArmed:
    """(b) the dead cohort leaves the divide; live capacity stays."""

    def test_dead_cohort_excluded_live_unit_kept(self):
        roster = dict(lp_bin_capacity_index(_centralia(), live_year=YEAR))
        assert roster[(3845, "COAL")] == pytest.approx(670.0)

    def test_colstrip_two_dead_units(self):
        gens = [
            _Gen(6076, "COAL_WC", 1480.0, "COAL_MT_p6076_committed"),
            _Gen(6076, "COAL_WC", 307.0, "COAL_MT_p6076_r202001_committed"),
            _Gen(6076, "COAL_WC", 307.0, "COAL_MT_p6076_r202001_econ"),
        ]
        assert dict(lp_bin_capacity_index(gens))[(6076, "COAL")] == pytest.approx(
            2094.0
        )
        assert dict(lp_bin_capacity_index(gens, live_year=YEAR))[
            (6076, "COAL")
        ] == pytest.approx(1480.0)

    def test_cohort_retiring_in_the_solve_year_is_live(self):
        """``retirement_year == run_year`` is online through its month: kept."""
        roster = dict(lp_bin_capacity_index(_centralia(), live_year=2020))
        assert roster[(3845, "COAL")] == pytest.approx(1340.0)

    def test_pmax_argument_still_sources_the_mw(self):
        roster = dict(
            lp_bin_capacity_index(_centralia(), np.array([600.0, 700.0]), YEAR)
        )
        assert roster[(3845, "COAL")] == pytest.approx(600.0)

    def test_a_fully_dead_plant_leaves_the_roster(self):
        gens = [_Gen(99, "COAL_BIT", 500.0, "COAL_X_p99_r201905_committed")]
        assert lp_bin_capacity_index(gens, live_year=YEAR) == ()

    def test_exit_cohort_tag_parsing(self):
        assert exit_cohort_tag(_centralia()[1]) == (2020, 12)
        assert exit_cohort_tag(_centralia()[0]) is None
        # a tag on another plant's code is not this row's cohort
        assert exit_cohort_tag(_Gen(1, "COAL_BIT", 1.0, "COAL_X_p3845_r202012")) is None
        assert exit_cohort_tag(_Gen(3845, "COAL_BIT", 1.0, "COAL_X_p3845_rABC")) is None

    def test_full_outage_of_the_live_unit_zeroes_the_bin(self, monkeypatch):
        """The measured case: BW22 fully out leaves 0 MW, not 250-280 MW."""
        monkeypatch.setattr(
            outages,
            "_iso_plant_capacity",
            lambda iso, cc_steam_part_reclass=False, cc_nameplate_basis=False: {
                (3845, "COAL"): 670.0
            },
        )
        monkeypatch.setattr(outages, "_fleet_status_index", lambda iso: None)
        df = pd.DataFrame(
            [
                {
                    "facility_id": 3845,
                    "unit_id": "BW22",
                    "plant_group": "COAL",
                    "unit_capacity_mw": 670.0,
                    "outage_start": "2021-04-03",
                    "outage_end": "2021-06-26",
                    "duration_days": 85.0,
                }
            ]
        )

        def run(roster):
            return _unit_outage_factors_from_events(
                df, YEAR, HOURS, "", "NWPP", per_unit_clip=True, lp_bin_capacity=roster
            )[(3845, "COAL")]

        h = outages.outage_hour_mask("2021-05-01", "2021-06-01", YEAR, HOURS)
        diluted = run(lp_bin_capacity_index(_centralia()))
        live = run(lp_bin_capacity_index(_centralia(), live_year=YEAR))
        assert diluted[h].max() == pytest.approx(0.5, abs=1e-9)
        assert live[h].max() == pytest.approx(0.0, abs=1e-9)


class TestRequiresParent:
    """(c) armed alone fails closed at the point of use."""

    def test_raises_without_parent(self):
        cfg = ScenarioConfig(
            iso="NWPP", unit_outage_dispatched_bin_live_denominator=True
        )
        with pytest.raises(ValueError, match="requires"):
            dispatched_bin_live_year(cfg, YEAR)

    def test_raises_without_year(self):
        cfg = ScenarioConfig(
            iso="NWPP",
            unit_outage_dispatched_bin_denominator=True,
            unit_outage_dispatched_bin_live_denominator=True,
        )
        with pytest.raises(ValueError):
            dispatched_bin_live_year(cfg, None)

    def test_armed_with_parent_returns_year(self):
        cfg = ScenarioConfig(
            iso="NWPP",
            mode="backcast",
            unit_outage_dispatched_bin_denominator=True,
            unit_outage_dispatched_bin_live_denominator=True,
        )
        assert dispatched_bin_live_year(cfg, YEAR) == YEAR


_COAL_CLASSES = frozenset({"COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC"})
_SCREENED = dict(
    wefor_residual=0.0,
    unit_outage_short_windows=True,
    unit_outage_dispatched_bin_denominator=True,
    wefor_residual_short_screened_coal=True,
)


def _availability(monkeypatch, **kw) -> np.ndarray:
    """Annual-mean availability of one coal and one CC row, trivial 1-zone fleet."""
    monkeypatch.setattr(
        fleet_arrays_mod,
        "short_screened_coal_shares",
        lambda year, iso, roster: {(10, "COAL"): 0.5},
    )
    gens = [
        Generator(
            unit_id="COAL_Z_p10_committed",
            name="coal",
            zone="Z",
            fuel_type="coal",
            pmax_mw=500.0,
            plant_group="COAL_BIT",
            plant_code=10,
            online_year=1980,
            is_campd_bin=True,
        ),
        Generator(
            unit_id="CC_REGULAR_Z_p20_committed",
            name="cc",
            zone="Z",
            fuel_type="gas",
            pmax_mw=500.0,
            plant_group="CC_REGULAR",
            plant_code=20,
            online_year=2000,
            is_campd_bin=True,
        ),
        Generator(
            unit_id="ST_GAS_Z_p30_committed",
            name="st",
            zone="Z",
            fuel_type="gas",
            pmax_mw=300.0,
            plant_group="ST_GAS",
            plant_code=30,
            online_year=1970,
            is_campd_bin=True,
        ),
    ]
    cfg = ScenarioConfig(
        iso="NWPP", mode="backcast", weather_year=YEAR, outage_source="historic", **kw
    )
    av = np.ones((len(gens), HOURS))
    fleet_arrays_mod._availability_matrix(gens, av, HOURS, cfg, "NWPP", YEAR, set())
    return av.mean(axis=1)


class TestCoalOnlyScoping:
    """(d) the screened-coal relief scoped to coal leaves gas untouched."""

    def test_gas_availability_unchanged(self, monkeypatch):
        stat = _availability(monkeypatch)
        armed = _availability(
            monkeypatch,
            **_SCREENED,
            unit_outage_dispatched_bin_live_denominator=True,
            wefor_residual_groups=_COAL_CLASSES,
        )
        np.testing.assert_array_equal(armed[1:], stat[1:])  # CC + ST gas
        # coal is relieved, on its 0.5 screened share only
        full = _availability(
            monkeypatch, **_SCREENED, wefor_residual_groups=_COAL_CLASSES
        )
        assert stat[0] < armed[0] < full[0]
        assert armed[0] - stat[0] == pytest.approx(0.5 * (full[0] - stat[0]))

    def test_inert_while_off(self, monkeypatch):
        """Off: covered-first order unchanged (coal in groups takes the full cap)."""
        a = _availability(monkeypatch, **_SCREENED, wefor_residual_groups=_COAL_CLASSES)
        b = _availability(monkeypatch, **_SCREENED)
        # MISO's keeper form: coal not in groups -> the screened blend either way
        miso_groups = frozenset({"CC_REGULAR", "ST_GAS", "ST_CHP"})
        c_off = _availability(
            monkeypatch, **_SCREENED, wefor_residual_groups=miso_groups
        )
        c_on = _availability(
            monkeypatch,
            **_SCREENED,
            wefor_residual_groups=miso_groups,
            unit_outage_dispatched_bin_live_denominator=True,
        )
        np.testing.assert_array_equal(c_off, c_on)
        assert a[0] == b[0]  # coal gets the full cap under both off forms

    def test_none_groups_still_relieve_gas_by_default(self, monkeypatch):
        """The limb touches coal only; None groups keep their gas full cap."""
        off = _availability(monkeypatch, **_SCREENED)
        on = _availability(
            monkeypatch, **_SCREENED, unit_outage_dispatched_bin_live_denominator=True
        )
        np.testing.assert_array_equal(off[1:], on[1:])
        assert on[0] < off[0]


class TestRegistration:
    def test_registered_in_the_cache_key(self):
        assert "unit_outage_dispatched_bin_live_denominator" in (
            _CACHE_KEY_OPTIONAL_FIELDS
        )
        assert (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[
                "unit_outage_dispatched_bin_live_denominator"
            ]
            == "False"
        )

    def test_default_key_is_unmoved_and_armed_key_differs(self):
        parent = ScenarioConfig(iso="NWPP", unit_outage_dispatched_bin_denominator=True)
        armed = ScenarioConfig(
            iso="NWPP",
            unit_outage_dispatched_bin_denominator=True,
            unit_outage_dispatched_bin_live_denominator=True,
        )
        assert (
            ScenarioConfig(
                iso="NWPP", unit_outage_dispatched_bin_live_denominator=False
            ).cache_key()
            == ScenarioConfig(iso="NWPP").cache_key()
        )
        assert armed.cache_key() != parent.cache_key()
