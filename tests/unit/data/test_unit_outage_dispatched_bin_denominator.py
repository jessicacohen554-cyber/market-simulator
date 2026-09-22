"""Unit tests for the DISPATCHED-bin derate denominator (miso-266).

``ScenarioConfig.unit_outage_dispatched_bin_denominator`` takes the unit-outage
derate denominator from the capacity the derate multiplier is APPLIED to — the
LP fleet's own per-bin ``pmax`` sum — instead of from
``outages._iso_plant_capacity``'s independently reconstructed map.

The arithmetic it repairs is an identity, not a judgement call: the accumulator
removes ``share = sum_u ucap_u / denom`` and the LP applies ``1 - share`` to the
bin's ``pmax``, so the MW actually removed is ``share x cap_LP`` and equals the
MW that went out iff ``denom == cap_LP``. ``_iso_plant_capacity``'s own docstring
already states that invariant; it simply cannot honour it by reconstruction,
because it is blind to the exit-cohort bins ``fleet/assembly.py`` synthesizes
with an ``_r{yyyy}{mm}`` tag under the SAME ``(plant_code, plant_group)`` key
(miso-191).

Every property below is asserted on a SYNTHETIC fleet and extract rather than on
MISO's committed data, so a change to the extract can never quietly turn a test
green (the miso-201 / miso-202 discipline). The properties under test are the
ones the mechanism's correctness rests on:

* the repair itself — a unit that is 27 % of the DISPATCHED bin removes 27 %,
  not the 60 % a half-sized reconstructed denominator charges it;
* the FULL-OUTAGE identity — a bin whose every dispatched MW is flagged lands on
  EXACTLY 0.0 availability, which is what makes the flag a basis repair rather
  than a level haircut;
* the exit-cohort case that motivates it — a plant whose LP capacity is the sum
  of a surviving bin and a retirement-cohort bin;
* MEMBERSHIP — a bin the LP dispatches but the reconstructed map lacks is
  derated rather than silently skipped (the SPP-48 Oklaunion pathology);
* and a bin the reconstructed map has but the LP does not dispatch is dropped;
* the identity property — where the two maps agree, the flag changes nothing;
* rule 19 ``[R-ONE-MECH]``: the loaders REFUSE to stack it on either other
  construction of the same denominator;
* the roster builder's own contract — hashable, sorted, ``pmax``-sourced,
  skipping rows with no plant code or group;
* scope and registration, so the field cannot repeat the caiso-184 / nyiso-128
  failure of landing unregistered and moving the pinned default cache key.
"""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd
import pytest

from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data import outages
from market_sim.data.outages import (
    _unit_outage_factors_from_events,
    lp_bin_capacity_index,
)

YEAR = 2024
#: The model clock is a FIXED non-leap 8760-hour year (``outages._hour_of_year``
#: uses a 28-day February), so hour-of-year arithmetic counts Feb as 28 days
#: even in 2024.
HOURS = 8760


class _Gen:
    """The two attributes :func:`lp_bin_capacity_index` reads off a generator."""

    def __init__(self, plant_code, plant_group, pmax_mw=0.0):
        self.plant_code = plant_code
        self.plant_group = plant_group
        self.pmax_mw = pmax_mw


def _events(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal unit-outage event frame from explicit row dicts."""
    return pd.DataFrame(
        [
            {
                "facility_id": r["plant"],
                "unit_id": r["unit"],
                "plant_group": r.get("group", "COAL"),
                "unit_capacity_mw": r["cap"],
                "outage_start": r["start"],
                "outage_end": r["end"],
                "duration_days": r.get("days", 19.0),
            }
            for r in rows
        ]
    )


def _patch(monkeypatch, cap: dict) -> None:
    """Install a synthetic reconstructed denominator and no status filter."""
    monkeypatch.setattr(
        outages,
        "_iso_plant_capacity",
        lambda iso, cc_steam_part_reclass=False, cc_nameplate_basis=False: cap,
    )
    monkeypatch.setattr(outages, "_fleet_status_index", lambda iso: None)


def _run(df: pd.DataFrame, roster) -> dict:
    """Run the accumulator, armed when ``roster`` is not ``None``."""
    return _unit_outage_factors_from_events(
        df, YEAR, HOURS, "", "MISO", per_unit_clip=True, lp_bin_capacity=roster
    )


#: One 432 MW unit out at a plant the LP dispatches at 1,625 MW while the
#: reconstructed map holds 722 MW — the R M Schahfer arithmetic, rounded to the
#: committed figures (FINDING-miso265 §3, PRECOMMIT-miso266 §2).
_SCHAHFER_WINDOW = {
    "plant": 6085,
    "unit": "14",
    "cap": 432.0,
    "start": "2024-03-01",
    "end": "2024-03-20",
}


class TestTheRepair:
    def test_share_is_taken_against_the_dispatched_capacity(self, monkeypatch):
        """One unit removes its share of what the LP dispatches, not of a stale map."""
        _patch(monkeypatch, {(6085, "COAL"): 722.0})
        df = _events([_SCHAHFER_WINDOW])
        roster = lp_bin_capacity_index(
            [_Gen(6085, "COAL"), _Gen(6085, "COAL")],
            np.array([722.0, 903.0]),
        )
        off = _run(df, None)[(6085, "COAL")]
        on = _run(df, roster)[(6085, "COAL")]
        # 2024-03-10 is inside the window on both legs.
        h = outages.outage_hour_mask("2024-03-05", "2024-03-15", YEAR, HOURS)
        assert off[h].max() == pytest.approx(1.0 - 432.0 / 722.0, abs=1e-9)
        assert on[h].max() == pytest.approx(1.0 - 432.0 / 1625.0, abs=1e-9)
        # The repair can only ever remove LESS here, because the denominator grew.
        assert float(on.min()) > float(off.min())

    def test_three_concurrent_units_no_longer_zero_a_running_plant(self, monkeypatch):
        """The defect in its sharpest form: a partly-out plant driven to zero."""
        _patch(monkeypatch, {(6085, "COAL"): 722.0})
        df = _events(
            [
                dict(_SCHAHFER_WINDOW, unit="14", cap=432.0),
                dict(_SCHAHFER_WINDOW, unit="15", cap=472.0),
                dict(_SCHAHFER_WINDOW, unit="17", cap=423.5),
            ]
        )
        roster = lp_bin_capacity_index([_Gen(6085, "COAL")], np.array([1625.0]))
        off = _run(df, None)[(6085, "COAL")]
        on = _run(df, roster)[(6085, "COAL")]
        assert float(off.min()) == 0.0  # 1,327.5 / 722.0 = 1.84 -> clipped to zero
        assert float(on.min()) == pytest.approx(1.0 - 1327.5 / 1625.0, abs=1e-9)
        assert float(on.min()) > 0.0  # the plant can still run, as its meter says

    def test_every_dispatched_mw_flagged_lands_on_exactly_zero(self, monkeypatch):
        """A basis repair, not a level haircut: a truly dark bin still reads 0.0."""
        _patch(monkeypatch, {(6085, "COAL"): 722.0})
        df = _events(
            [
                dict(_SCHAHFER_WINDOW, unit="14", cap=800.0),
                dict(_SCHAHFER_WINDOW, unit="15", cap=825.0),
            ]
        )
        roster = lp_bin_capacity_index([_Gen(6085, "COAL")], np.array([1625.0]))
        on = _run(df, roster)[(6085, "COAL")]
        assert float(on.min()) == 0.0

    def test_exit_cohort_bins_are_summed_into_the_denominator(self, monkeypatch):
        """The miso-191 ``_r{yyyy}{mm}`` cohort carries real dispatched MW.

        The cohort's tranches keep the plant's ``(plant_code, plant_group)`` key,
        which is the key the overlay is looked up by, so the roster must sum them
        with the surviving bin's — and the reconstructed map, built from a fleet
        load that never sees the cohort, cannot.
        """
        roster = dict(
            lp_bin_capacity_index(
                [
                    _Gen(6085, "COAL", 400.0),  # surviving bin, two tranches
                    _Gen(6085, "COAL", 322.0),
                    _Gen(6085, "COAL", 903.0),  # the r202110 exit cohort
                ]
            )
        )
        assert roster[(6085, "COAL")] == pytest.approx(1625.0)


class TestMembership:
    def test_a_bin_the_lp_dispatches_is_no_longer_skipped(self, monkeypatch):
        """The SPP-48 Oklaunion pathology, generalized.

        A plant absent from the reconstructed map rides un-derated through its
        own measured outage, because the accumulator skips a row whose target is
        not in ``cap``. On the dispatched roster it is derated.
        """
        _patch(monkeypatch, {})  # reconstructed map does not carry the plant
        df = _events([{**_SCHAHFER_WINDOW, "plant": 127, "unit": "1", "cap": 650.0}])
        assert _run(df, None) == {}
        roster = lp_bin_capacity_index([_Gen(127, "COAL")], np.array([650.0]))
        on = _run(df, roster)[(127, "COAL")]
        assert float(on.min()) == 0.0

    def test_a_bin_the_lp_does_not_dispatch_is_dropped(self, monkeypatch):
        """Nothing to derate: the factor is never built for an undispatched bin."""
        _patch(monkeypatch, {(9999, "COAL"): 500.0})
        df = _events([{**_SCHAHFER_WINDOW, "plant": 9999, "unit": "1", "cap": 500.0}])
        assert (9999, "COAL") in _run(df, None)
        roster = lp_bin_capacity_index([_Gen(6085, "COAL")], np.array([1625.0]))
        assert _run(df, roster) == {}


class TestChpExclusion:
    """The CHP bins keep their incumbent nameplate denominator, on construction.

    At a CHP bin ``cap_LP`` is a DELIBERATE CARVE-OUT — the grid-facing residual
    after the behind-the-meter host steam is held out — not the plant's
    dispatchable capacity, so the flag's identity does not apply and the
    incumbent denominator is the correct one (if a unit's output splits
    host/grid like its plant's, the share of the GRID bin its outage removes is
    ``ucap x grid_frac / (nameplate x grid_frac) = ucap / nameplate``).
    """

    def test_a_chp_bin_is_the_identity(self, monkeypatch):
        """Armed or not, a CHP bin's factor is byte-identical."""
        _patch(monkeypatch, {(1073, "ST_CHP"): 111.7})
        df = _events(
            [
                {
                    **_SCHAHFER_WINDOW,
                    "plant": 1073,
                    "unit": "1",
                    "cap": 40.0,
                    "group": "ST_CHP",
                }
            ]
        )
        # The LP dispatches only the 72.6 MW grid share (ratio 1.538 = 1/0.65).
        roster = lp_bin_capacity_index([_Gen(1073, "ST_CHP")], np.array([72.6]))
        np.testing.assert_array_equal(
            _run(df, None)[(1073, "ST_CHP")], _run(df, roster)[(1073, "ST_CHP")]
        )

    def test_the_excluded_set_is_exactly_the_three_chp_groups(self):
        assert outages._DISPATCHED_DENOM_EXCLUDED_GROUPS == frozenset(
            {"CC_CHP", "CT_CHP", "ST_CHP"}
        )

    def test_a_chp_bin_absent_from_the_reconstructed_map_is_still_skipped(
        self, monkeypatch
    ):
        """The exclusion is total: membership at a CHP bin is unchanged too."""
        _patch(monkeypatch, {})
        df = _events(
            [
                {
                    **_SCHAHFER_WINDOW,
                    "plant": 1073,
                    "unit": "1",
                    "cap": 40.0,
                    "group": "CC_CHP",
                }
            ]
        )
        roster = lp_bin_capacity_index([_Gen(1073, "CC_CHP")], np.array([72.6]))
        assert _run(df, roster) == {}

    def test_a_non_chp_bin_at_the_same_plant_still_moves(self, monkeypatch):
        """The exclusion is per BIN, not per plant.

        MISO plant 1073 carries BOTH an under-denominated COAL bin (43.6 MW of
        LP against 29.3 MW of map) and an over-denominated ST_CHP bin. The flag
        must reach the first and leave the second.
        """
        _patch(monkeypatch, {(1073, "COAL"): 29.3, (1073, "ST_CHP"): 111.7})
        roster = lp_bin_capacity_index(
            [_Gen(1073, "COAL"), _Gen(1073, "ST_CHP")], np.array([43.6, 72.6])
        )
        coal = _events([{**_SCHAHFER_WINDOW, "plant": 1073, "unit": "1", "cap": 14.0}])
        off = _run(coal, None)[(1073, "COAL")]
        on = _run(coal, roster)[(1073, "COAL")]
        assert float(on.min()) > float(off.min())  # the COAL bin moved
        chp = _events(
            [
                {
                    **_SCHAHFER_WINDOW,
                    "plant": 1073,
                    "unit": "1",
                    "cap": 40.0,
                    "group": "ST_CHP",
                }
            ]
        )
        np.testing.assert_array_equal(
            _run(chp, None)[(1073, "ST_CHP")], _run(chp, roster)[(1073, "ST_CHP")]
        )


class TestIdentityAndScope:
    def test_agreeing_maps_leave_the_factor_untouched(self, monkeypatch):
        """Where the two constructions agree the flag is the identity."""
        _patch(monkeypatch, {(1091, "COAL"): 510.0})
        df = _events([{**_SCHAHFER_WINDOW, "plant": 1091, "unit": "1", "cap": 255.0}])
        roster = lp_bin_capacity_index([_Gen(1091, "COAL")], np.array([510.0]))
        np.testing.assert_array_equal(
            _run(df, None)[(1091, "COAL")], _run(df, roster)[(1091, "COAL")]
        )

    def test_ercot_keeps_its_own_bin_sheet(self, monkeypatch):
        """Non-ERCOT only, like every sibling basis flag.

        ERCOT's branch caps on its CAMPD bin sheet and routes split facilities by
        asset class, a basis the extract's ``facility_id`` does not address, so
        the roster must not reach it.
        """
        src = inspect.getsource(outages._unit_outage_factors_from_events)
        head, _, tail = src.partition('if iso == "ERCOT":')
        assert tail, "the ERCOT branch moved; re-check this scoping assertion"
        ercot_branch, _, generic_branch = tail.partition("    else:")
        assert "lp_bin_capacity" not in ercot_branch
        assert "_dispatched_denominator(cap, lp_bin_capacity)" in generic_branch

    @pytest.mark.parametrize(
        "loader",
        [
            "unit_outage_derate_factors",
            "unit_outage_short_derate_factors",
            "unit_partial_outage_derate_factors",
            "unit_layup_removed_fractions",
            "unit_outage_maxgen_derate_factors",
        ],
    )
    def test_every_layer_that_divides_by_cap_takes_the_roster(self, loader):
        """Rule 19 ``[R-ONE-MECH]``: one denominator, one mechanism, every layer.

        The lay-up loader's contract is that a lay-up share and an outage share
        for the same plant are ADDITIVE, so it moves with the overlay by
        necessity. MAXGEN is included — unlike ``per_unit_clip`` and
        ``st_capacity_basis``, which it excludes — because it divides by the same
        ``cap[bin]`` on the same key and so carries the identical defect.
        """
        sig = inspect.signature(getattr(outages, loader))
        assert "lp_bin_capacity" in sig.parameters
        assert sig.parameters["lp_bin_capacity"].default is None


class TestRuleNineteenRefusals:
    def test_refuses_to_stack_on_the_cc_nameplate_denominator(self, monkeypatch):
        """``unit_outage_lp_capacity_basis`` reconstructs a raise already in pmax."""
        _patch(monkeypatch, {(6085, "COAL"): 722.0})
        roster = lp_bin_capacity_index([_Gen(6085, "COAL")], np.array([1625.0]))
        with pytest.raises(ValueError, match="rule 19"):
            _unit_outage_factors_from_events(
                _events([_SCHAHFER_WINDOW]),
                YEAR,
                HOURS,
                "",
                "MISO",
                cc_nameplate_basis=True,
                lp_bin_capacity=roster,
            )

    def test_refuses_to_stack_on_the_extract_basis_share(self, monkeypatch):
        """Both set the denominator; two constructions of one never stack."""
        _patch(monkeypatch, {(6085, "COAL"): 722.0})
        roster = lp_bin_capacity_index([_Gen(6085, "COAL")], np.array([1625.0]))
        with pytest.raises(ValueError, match="rule 19"):
            _unit_outage_factors_from_events(
                _events([_SCHAHFER_WINDOW]),
                YEAR,
                HOURS,
                "",
                "MISO",
                extract_basis={(6085, "COAL"): (True, 2009.0)},
                lp_bin_capacity=roster,
            )


class TestRosterBuilder:
    def test_is_hashable_sorted_and_pmax_sourced(self):
        """It crosses an ``lru_cache`` boundary, so it must hash deterministically."""
        gens = [_Gen(20, "ST_GAS", 1.0), _Gen(10, "COAL", 2.0), _Gen(10, "COAL", 3.0)]
        roster = lp_bin_capacity_index(gens)
        assert roster == (((10, "COAL"), 5.0), ((20, "ST_GAS"), 1.0))
        hash(roster)  # raises if any element is unhashable
        # Row order must not change the roster.
        assert lp_bin_capacity_index(list(reversed(gens))) == roster

    def test_pmax_argument_overrides_the_generator_attribute(self):
        """The overlay is applied to the ``pmax`` ARRAY, so that is the basis."""
        gens = [_Gen(10, "COAL", 2.0)]
        assert lp_bin_capacity_index(gens, np.array([77.0])) == (((10, "COAL"), 77.0),)

    def test_skips_rows_with_no_plant_code_group_or_capacity(self):
        """Exactly the rows ``_iso_plant_capacity`` skips, for the same reasons."""
        gens = [
            _Gen(0, "COAL", 5.0),
            _Gen(10, "", 5.0),
            _Gen(11, "COAL", 0.0),
            _Gen(12, "COAL", 5.0),
        ]
        assert lp_bin_capacity_index(gens) == (((12, "COAL"), 5.0),)


class TestRegistration:
    def test_field_exists_and_defaults_off(self):
        assert (
            ScenarioConfig(iso="MISO").unit_outage_dispatched_bin_denominator is False
        )

    def test_registered_in_the_cache_key(self):
        """Landing unregistered is the caiso-184 / nyiso-128 failure."""
        assert "unit_outage_dispatched_bin_denominator" in _CACHE_KEY_OPTIONAL_FIELDS

    def test_default_key_is_unmoved_and_armed_key_differs(self):
        base = ScenarioConfig(iso="MISO")
        assert base.cache_key() == ScenarioConfig(iso="MISO").cache_key()
        armed = ScenarioConfig(iso="MISO", unit_outage_dispatched_bin_denominator=True)
        assert armed.cache_key() != base.cache_key()

    def test_not_declared_backcast_only(self):
        """It adds no year-keyed record: a forecast fleet has ``pmax`` too.

        Listing it in the rule-13 hard-error family would ASSERT a
        non-regenerability that is false (the miso-200 reasoning).
        """
        from market_sim.config.scenarios import _BACKCAST_ONLY_OVERLAY_FIELDS

        assert (
            "unit_outage_dispatched_bin_denominator"
            not in _BACKCAST_ONLY_OVERLAY_FIELDS
        )
