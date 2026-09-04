"""Unit tests for the ST-side unit-outage capacity BASIS alignment (miso-201).

``ScenarioConfig.unit_outage_st_capacity_basis`` puts a STEAM bin's unit-outage
removed MW on the LP's own per-unit ``pmax_mw`` basis, closing the side
``unit_outage_lp_capacity_basis`` structurally cannot reach
(``_CC_NAMEPLATE_BASIS_GROUPS`` is CC-only).

The properties under test are the ones the mechanism's correctness rests on, and
each is asserted on a SYNTHETIC fleet/extract rather than on MISO's data, so a
change to the committed extract can never quietly turn a test green:

* the all-or-nothing rule (a bin with any unresolved unit keeps the production
  basis ENTIRELY — partial alignment is the failure mode the design refuses);
* the three resolution routes, including the 1-1 residual pairing that is
  *forced* rather than chosen;
* the invariant that makes the repair correct: a bin all of whose units are out
  lands on EXACTLY 1.0, so availability is exactly 0.0 — never 1.13 (over-remove)
  and never 0.94 (phantom availability);
* scope: non-steam bins never move, ERCOT never moves, and the flag is byte-inert
  while off;
* registration, so the field cannot repeat the caiso-184 / nyiso-128 failure of
  landing unregistered and moving the pinned default cache key.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data import outages
from market_sim.data.outages import (
    _ST_CAPACITY_BASIS_GROUPS,
    _CC_NAMEPLATE_BASIS_GROUPS,
    _st_basis_pairmap,
)


def _events(rows: list[tuple[int, str, str, float]]) -> pd.DataFrame:
    """Build a minimal unit-outage event frame: (plant, unit, group, cap_mw)."""
    return pd.DataFrame(
        [
            {
                "facility_id": p,
                "unit_id": u,
                "plant_group": g,
                "unit_capacity_mw": c,
                "outage_start": "2024-03-01",
                "outage_end": "2024-03-20",
                "duration_days": 19.0,
            }
            for p, u, g, c in rows
        ]
    )


@pytest.fixture
def roster(monkeypatch):
    """Patch the per-unit fleet roster with a synthetic one and return it."""

    def _install(mapping):
        monkeypatch.setattr(
            outages,
            "_iso_plant_unit_capacity",
            lambda iso, cc_steam_part_reclass=False: mapping,
        )
        return mapping

    return _install


class TestTheGroupsAreExactlyTheOnesTheCCFlagCannotReach:
    def test_steam_groups_are_disjoint_from_the_cc_basis_groups(self):
        assert set(_ST_CAPACITY_BASIS_GROUPS).isdisjoint(_CC_NAMEPLATE_BASIS_GROUPS)

    def test_steam_groups_are_the_steam_bins(self):
        assert set(_ST_CAPACITY_BASIS_GROUPS) == {"ST_GAS", "ST_CHP"}


class TestResolutionRoutes:
    def test_exact_normalised_id_hit(self, roster):
        roster({(1, "ST_GAS"): {"5": 742.6, "6": 722.8}})
        df = _events([(1, "5", "ST_GAS", 895.1), (1, "6", "ST_GAS", 895.1)])
        pm = _st_basis_pairmap(df, {(1, "ST_GAS"): 1465.4}, "MISO", False)
        assert pm == {(1, "ST_GAS", "5"): 742.6, (1, "ST_GAS", "6"): 722.8}

    def test_unambiguous_trailing_digit_hit(self, roster):
        # CAMPD "WAP5" against EIA "5": digits match and only one fleet unit
        # carries them.
        roster({(1, "ST_GAS"): {"WAP5": 100.0, "GEN9": 50.0}})
        df = _events([(1, "5", "ST_GAS", 120.0), (1, "9", "ST_GAS", 60.0)])
        pm = _st_basis_pairmap(df, {(1, "ST_GAS"): 150.0}, "MISO", False)
        assert pm == {(1, "ST_GAS", "5"): 100.0, (1, "ST_GAS", "9"): 50.0}

    def test_ambiguous_digits_refuse_the_whole_bin(self, roster):
        # Two fleet units carry digits "1", so the join is not unambiguous.
        roster({(1, "ST_GAS"): {"A1": 100.0, "B1": 100.0}})
        df = _events([(1, "1", "ST_GAS", 120.0)])
        assert _st_basis_pairmap(df, {(1, "ST_GAS"): 200.0}, "MISO", False) == {}

    def test_unique_residual_pairing_is_forced_not_chosen(self, roster):
        # The Ninemile Point 1403 shape: CAMPD "4" cannot match EIA "6(4)" on
        # digits, but exactly one extract unit and exactly one fleet unit are
        # left over, so the pairing is forced.
        roster({(1403, "ST_GAS"): {"5": 742.6, "64": 722.8}})
        df = _events([(1403, "5", "ST_GAS", 895.1), (1403, "4", "ST_GAS", 786.0)])
        pm = _st_basis_pairmap(df, {(1403, "ST_GAS"): 1465.4}, "MISO", False)
        assert pm == {
            (1403, "ST_GAS", "5"): 742.6,
            (1403, "ST_GAS", "4"): 722.8,
        }

    def test_two_unresolved_units_are_not_paired(self, roster):
        # Ambiguity is refused rather than resolved by an arbitrary ordering.
        roster({(1, "ST_GAS"): {"AA": 10.0, "BB": 20.0, "CC": 30.0}})
        df = _events(
            [
                (1, "X", "ST_GAS", 11.0),
                (1, "Y", "ST_GAS", 22.0),
                (1, "CC", "ST_GAS", 33.0),
            ]
        )
        assert _st_basis_pairmap(df, {(1, "ST_GAS"): 60.0}, "MISO", False) == {}


class TestAllOrNothing:
    def test_one_unresolved_unit_leaves_the_WHOLE_bin_on_the_production_basis(
        self, roster
    ):
        # The design's core refusal: a half-aligned bin is less coherent than
        # either basis alone, so the resolvable units are NOT aligned either.
        roster({(1, "ST_GAS"): {"5": 100.0, "6": 100.0, "7": 100.0}})
        df = _events(
            [
                (1, "5", "ST_GAS", 120.0),
                (1, "6", "ST_GAS", 120.0),
                (1, "ZZ", "ST_GAS", 120.0),
                (1, "QQ", "ST_GAS", 120.0),
            ]
        )
        assert _st_basis_pairmap(df, {(1, "ST_GAS"): 300.0}, "MISO", False) == {}

    def test_a_collision_refuses_the_bin(self, roster):
        # Two extract units resolving onto the SAME fleet unit is not 1-1.
        roster({(1, "ST_GAS"): {"GEN5": 100.0, "OTHER": 50.0}})
        df = _events([(1, "5", "ST_GAS", 60.0), (1, "GEN5", "ST_GAS", 60.0)])
        assert _st_basis_pairmap(df, {(1, "ST_GAS"): 150.0}, "MISO", False) == {}

    def test_a_synthetic_whole_plant_row_refuses_the_bin(self, roster):
        # eia923_netzero rows carry the PLANT's total nameplate standing for a
        # whole-plant lay-up — a different object, never aligned here.
        roster({(1, "ST_CHP"): {"ST1": 8.0, "ST2": 8.0}})
        df = _events([(1, "NET0-923", "ST_CHP", 100.8)])
        assert _st_basis_pairmap(df, {(1, "ST_CHP"): 16.0}, "MISO", False) == {}

    def test_bins_are_refused_independently(self, roster):
        roster(
            {
                (1, "ST_GAS"): {"5": 100.0, "6": 100.0},
                (2, "ST_GAS"): {"A": 50.0},
            }
        )
        df = _events(
            [
                (1, "5", "ST_GAS", 120.0),
                (1, "6", "ST_GAS", 120.0),
                (2, "ZZ", "ST_GAS", 60.0),
                (2, "YY", "ST_GAS", 60.0),
            ]
        )
        cap = {(1, "ST_GAS"): 200.0, (2, "ST_GAS"): 50.0}
        pm = _st_basis_pairmap(df, cap, "MISO", False)
        assert set(k[0] for k in pm) == {1}


class TestScope:
    def test_non_steam_bins_are_never_aligned(self, roster):
        roster({(1, "CC_REGULAR"): {"1": 100.0, "2": 100.0}})
        df = _events([(1, "1", "CC_REGULAR", 120.0), (1, "2", "CC_REGULAR", 120.0)])
        assert _st_basis_pairmap(df, {(1, "CC_REGULAR"): 200.0}, "MISO", False) == {}

    def test_coal_bins_are_never_aligned(self, roster):
        roster({(1, "COAL"): {"1": 100.0}})
        df = _events([(1, "1", "COAL", 120.0)])
        assert _st_basis_pairmap(df, {(1, "COAL"): 100.0}, "MISO", False) == {}

    def test_a_bin_absent_from_the_cap_map_is_skipped(self, roster):
        roster({(1, "ST_GAS"): {"5": 100.0}})
        df = _events([(1, "5", "ST_GAS", 120.0)])
        assert _st_basis_pairmap(df, {}, "MISO", False) == {}


class TestTheInvariantThatMakesTheRepairCorrect:
    """A bin all of whose units are out must land on EXACTLY 1.0."""

    def test_full_concurrent_stop_removes_exactly_the_bin(self, roster):
        roster({(1403, "ST_GAS"): {"5": 742.6, "64": 722.8}})
        cap = {(1403, "ST_GAS"): 1465.4}
        df = _events([(1403, "5", "ST_GAS", 895.1), (1403, "4", "ST_GAS", 786.0)])
        pm = _st_basis_pairmap(df, cap, "MISO", False)
        aligned = sum(pm.values()) / cap[(1403, "ST_GAS")]
        assert aligned == pytest.approx(1.0, abs=1e-12)

        # ... where the production basis over-removes ...
        production = (895.1 + 786.0) / 1465.4
        assert production > 1.0

        # ... and a NAMEPLATE denominator (the CC flag's direction) would leave
        # phantom availability at a plant that is entirely out.
        nameplate_denominator = (895.1 + 786.0) / (895.1 + 895.1)
        assert nameplate_denominator < 1.0

    def test_one_unit_out_removes_exactly_that_unit(self, roster):
        roster({(1403, "ST_GAS"): {"5": 742.6, "64": 722.8}})
        cap = {(1403, "ST_GAS"): 1465.4}
        df = _events([(1403, "5", "ST_GAS", 895.1), (1403, "4", "ST_GAS", 786.0)])
        pm = _st_basis_pairmap(df, cap, "MISO", False)
        assert pm[(1403, "ST_GAS", "5")] / cap[(1403, "ST_GAS")] == pytest.approx(
            0.50676, abs=1e-5
        )
        # the production basis removes 0.611 of the bin for the same outage
        assert 895.1 / 1465.4 == pytest.approx(0.61082, abs=1e-5)


class TestAccumulatorWiring:
    """The accumulator substitutes the aligned numerator, and only there."""

    @staticmethod
    def _run(monkeypatch, df, cap, iso, flag):
        monkeypatch.setattr(outages, "_iso_plant_capacity", lambda *a, **k: cap)
        return outages._unit_outage_factors_from_events(
            df, 2024, 8760, "", iso, False, False, False, st_capacity_basis=flag
        )

    def test_off_keeps_the_production_basis_and_on_aligns_it(self, roster, monkeypatch):
        roster({(1, "ST_GAS"): {"5": 100.0, "6": 100.0}})
        df = _events([(1, "5", "ST_GAS", 150.0)])
        cap = {(1, "ST_GAS"): 200.0}
        off = self._run(monkeypatch, df, cap, "MISO", False)
        on = self._run(monkeypatch, df, cap, "MISO", True)
        in_window = off[(1, "ST_GAS")].argmin()
        # production: 150/200 removed -> availability 0.25
        assert off[(1, "ST_GAS")][in_window] == pytest.approx(0.25)
        # aligned: the unit's own 100 MW of a 200 MW bin -> availability 0.5
        assert on[(1, "ST_GAS")][in_window] == pytest.approx(0.5)
        # outside the window both are untouched
        assert off[(1, "ST_GAS")].max() == pytest.approx(1.0)
        assert on[(1, "ST_GAS")].max() == pytest.approx(1.0)

    def test_a_refused_bin_is_byte_identical_armed_and_unarmed(
        self, roster, monkeypatch
    ):
        roster({(1, "ST_GAS"): {"5": 100.0, "6": 100.0}})
        df = _events([(1, "ZZ", "ST_GAS", 150.0)])
        cap = {(1, "ST_GAS"): 200.0}
        off = self._run(monkeypatch, df, cap, "MISO", False)
        on = self._run(monkeypatch, df, cap, "MISO", True)
        assert np.array_equal(off[(1, "ST_GAS")], on[(1, "ST_GAS")])

    def test_a_non_steam_bin_is_byte_identical_armed_and_unarmed(
        self, roster, monkeypatch
    ):
        roster({(1, "CC_REGULAR"): {"1": 100.0, "2": 100.0}})
        df = _events([(1, "1", "CC_REGULAR", 150.0)])
        cap = {(1, "CC_REGULAR"): 200.0}
        off = self._run(monkeypatch, df, cap, "MISO", False)
        on = self._run(monkeypatch, df, cap, "MISO", True)
        assert np.array_equal(off[(1, "CC_REGULAR")], on[(1, "CC_REGULAR")])

    def test_full_concurrent_stop_gives_availability_exactly_zero(
        self, roster, monkeypatch
    ):
        roster({(1403, "ST_GAS"): {"5": 742.6, "64": 722.8}})
        df = _events([(1403, "5", "ST_GAS", 895.1), (1403, "4", "ST_GAS", 786.0)])
        cap = {(1403, "ST_GAS"): 1465.4}
        on = self._run(monkeypatch, df, cap, "MISO", True)
        assert on[(1403, "ST_GAS")].min() == pytest.approx(0.0, abs=1e-12)

    def test_the_miso_path_builds_a_pairmap_and_ercot_does_not(
        self, roster, monkeypatch
    ):
        """The ERCOT guard sits AHEAD of the pairmap build.

        ERCOT caps on its own CAMPD bin sheet — a different basis, with no
        per-unit fleet roster to align onto — so arming the flag there must never
        even construct a pairmap, let alone substitute a numerator.
        """
        calls: list[str] = []
        real = outages._st_basis_pairmap
        monkeypatch.setattr(
            outages,
            "_st_basis_pairmap",
            lambda df, cap, iso, r: calls.append(iso) or real(df, cap, iso, r),
        )
        roster({(1, "ST_GAS"): {"5": 100.0}})
        cap = {(1, "ST_GAS"): 100.0}
        monkeypatch.setattr(outages, "_iso_plant_capacity", lambda *a, **k: cap)
        df = _events([(1, "5", "ST_GAS", 120.0)])

        outages._unit_outage_factors_from_events(
            df, 2024, 8760, "", "MISO", False, False, False, st_capacity_basis=True
        )
        assert calls == ["MISO"]

        calls.clear()
        # The ERCOT branch imports load_campd_bins from the fleet package
        # inside the function, so the patch has to land there.
        import market_sim.data.fleet as fleet_pkg

        monkeypatch.setattr(
            fleet_pkg,
            "load_campd_bins",
            lambda *a, **k: pd.DataFrame(
                {"Plant_Code": [1], "Plant_Group": ["ST_GAS"], "capacity_mw": [100.0]}
            ),
        )
        outages._unit_outage_factors_from_events(
            df, 2024, 8760, "", "ERCOT", False, False, False, st_capacity_basis=True
        )
        assert calls == [], "ERCOT must never build an ST pairmap"


class TestRegistration:
    def test_field_exists_and_defaults_off(self):
        assert ScenarioConfig().unit_outage_st_capacity_basis is False

    def test_field_is_cache_key_registered(self):
        # caiso-184 and nyiso-128 both moved the pinned DEFAULT cache key by
        # landing a gated field unregistered. Registered in the same commit here.
        assert "unit_outage_st_capacity_basis" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_armed_config_keeps_a_distinct_cache_key(self):
        base = ScenarioConfig()
        armed = base.with_overrides(unit_outage_st_capacity_basis=True)
        assert base.cache_key() != armed.cache_key()
