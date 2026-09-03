"""Unit tests for the per-unit unit-outage removal clip (miso-202).

``ScenarioConfig.unit_outage_per_unit_clip`` enforces, in the shared unit-outage
accumulator, the invariant that ONE UNIT CANNOT BE MORE THAN 100 % OUT OF
SERVICE.

The defect it repairs: ``outages.unit_outage_event_window`` reconstructs a
day-granular extract row as the half-open window
``[outage_start, outage_end + 1 day)``, so two windows of the SAME unit that
share a boundary date both cover that day, and
``_unit_outage_factors_from_events`` SUMS row shares rather than unioning them —
subtracting the unit's capacity TWICE for 24 h.

Every property below is asserted on a SYNTHETIC fleet and extract rather than on
MISO's committed data, so a change to the extract can never quietly turn a test
green (the miso-201 discipline). The properties under test are the ones the
mechanism's correctness rests on:

* the repair itself — a boundary-day overlap on a HALF-of-the-bin unit reads 0.5
  availability, not 0.0;
* **MONOTONICITY**, the mechanism's own soundness line: the clip can only ever
  remove LESS, never more, on every bin and every hour (the A/B's S-3 gate);
* the identity property — with no same-unit overlap the flag changes nothing, so
  the off path and the on path agree bit for bit;
* that it clips PER UNIT and not per bin: two DIFFERENT units out concurrently
  still sum to a full bin derate, which is correct and must not be clipped away;
* partial-derate rows (a ``derate_factor`` column), where two legitimate
  non-overlapping plateaus must survive and only the impossible sum is capped;
* the ceiling is the LARGEST capacity a unit's own rows claim, so a re-rating
  mid-extract cannot clip a legitimate single window;
* scope: the flag is byte-inert while off, and the maxgen layer never receives it;
* registration, so the field cannot repeat the caiso-184 / nyiso-128 failure of
  landing unregistered and moving the pinned default cache key.
"""

from __future__ import annotations

import inspect

import numpy as np
import pandas as pd

from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data import outages
from market_sim.data.outages import _unit_outage_factors_from_events

YEAR = 2024
# The model clock is a FIXED non-leap 8760-hour year (outages._hour_of_year uses
# a 28-day February), so hour-of-year arithmetic below counts Feb as 28 days
# even in 2024. Getting this wrong is a silent 24-hour offset.
HOURS = 8760


def _events(rows: list[dict]) -> pd.DataFrame:
    """Build a minimal unit-outage event frame from explicit row dicts."""
    return pd.DataFrame(
        [
            {
                "facility_id": r["plant"],
                "unit_id": r["unit"],
                "plant_group": r.get("group", "ST_GAS"),
                "unit_capacity_mw": r["cap"],
                "outage_start": r["start"],
                "outage_end": r["end"],
                "duration_days": r.get("days", 19.0),
                **({"derate_factor": r["derate"]} if "derate" in r else {}),
            }
            for r in rows
        ]
    )


def _run(df: pd.DataFrame, cap: dict, clip: bool) -> dict:
    """Run the accumulator with the synthetic bin-capacity map."""
    return _unit_outage_factors_from_events(
        df, YEAR, HOURS, "", "MISO", per_unit_clip=clip
    )


def _patch(monkeypatch, cap: dict) -> None:
    """Install a synthetic bin-capacity denominator and no status filter."""
    monkeypatch.setattr(
        outages,
        "_iso_plant_capacity",
        lambda iso, cc_steam_part_reclass=False, cc_nameplate_basis=False: cap,
    )
    monkeypatch.setattr(outages, "_fleet_status_index", lambda iso: None)


class TestTheRepair:
    def test_boundary_day_overlap_no_longer_double_counts(self, monkeypatch):
        """The defect, and its repair, on one unit that is HALF of its bin.

        Two windows of unit ``1`` abut on 2024-03-20. Under the day-granular
        reconstruction the first covers ``[03-01, 03-21)`` and the second
        ``[03-20, 04-11)``, so 03-20 is covered twice. The unit is 500 of the
        bin's 1000 MW, so the production accumulator removes 1.0 of the bin on
        that day and the clip removes the correct 0.5.
        """
        cap = {(1, "ST_GAS"): 1000.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-20",
                    "end": "2024-04-10",
                },
            ]
        )
        off = _run(df, cap, False)[(1, "ST_GAS")]
        on = _run(df, cap, True)[(1, "ST_GAS")]

        # The boundary day: hour-of-year of 2024-03-20 00:00 on the model clock.
        h0 = (31 + 28 + 19) * 24
        boundary = slice(h0, h0 + 24)
        assert np.allclose(off[boundary], 0.0)  # the double-count, clipped to 0
        assert np.allclose(on[boundary], 0.5)  # the physically correct value

        # Every OTHER hour of the two windows is a single window and unchanged.
        assert np.allclose(off[h0 - 24 : h0], 0.5)
        assert np.allclose(on[h0 - 24 : h0], 0.5)
        assert np.allclose(off[h0 + 24 : h0 + 48], 0.5)
        assert np.allclose(on[h0 + 24 : h0 + 48], 0.5)

    def test_the_overlap_is_exactly_twentyfour_hours(self, monkeypatch):
        """The `+ 1 day` artifact's signature: 24 h, no more and no less."""
        cap = {(1, "ST_GAS"): 1000.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-20",
                    "end": "2024-04-10",
                },
            ]
        )
        off = _run(df, cap, False)[(1, "ST_GAS")]
        on = _run(df, cap, True)[(1, "ST_GAS")]
        assert int(np.sum(~np.isclose(off, on))) == 24


class TestMonotonicity:
    """The mechanism's own soundness line — it can only ever remove LESS."""

    def test_availability_never_falls_anywhere(self, monkeypatch):
        cap = {(1, "ST_GAS"): 1000.0, (2, "ST_GAS"): 400.0, (3, "COAL"): 900.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                # a same-unit boundary-day overlap
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-20",
                    "end": "2024-04-10",
                },
                # two DIFFERENT units of the same bin, concurrent
                {
                    "plant": 1,
                    "unit": "2",
                    "cap": 500.0,
                    "start": "2024-03-05",
                    "end": "2024-03-25",
                },
                # a whole-bin single unit
                {
                    "plant": 2,
                    "unit": "A",
                    "cap": 400.0,
                    "start": "2024-06-01",
                    "end": "2024-06-30",
                },
                # a disjoint pair (no overlap at all)
                {
                    "plant": 3,
                    "unit": "B",
                    "cap": 300.0,
                    "start": "2024-01-05",
                    "end": "2024-01-20",
                },
                {
                    "plant": 3,
                    "unit": "B",
                    "cap": 300.0,
                    "start": "2024-02-05",
                    "end": "2024-02-20",
                },
            ]
        )
        off = _run(df, cap, False)
        on = _run(df, cap, True)
        assert set(off) == set(on)
        for key in off:
            assert np.all(on[key] >= off[key] - 1e-12), key


class TestIdentityWhereThereIsNoOverlap:
    def test_disjoint_windows_of_one_unit_are_unchanged(self, monkeypatch):
        cap = {(3, "COAL"): 900.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 3,
                    "unit": "B",
                    "group": "COAL",
                    "cap": 300.0,
                    "start": "2024-01-05",
                    "end": "2024-01-20",
                },
                {
                    "plant": 3,
                    "unit": "B",
                    "group": "COAL",
                    "cap": 300.0,
                    "start": "2024-02-05",
                    "end": "2024-02-20",
                },
            ]
        )
        assert np.array_equal(
            _run(df, cap, False)[(3, "COAL")], _run(df, cap, True)[(3, "COAL")]
        )

    def test_a_single_window_is_unchanged(self, monkeypatch):
        cap = {(2, "ST_GAS"): 400.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 2,
                    "unit": "A",
                    "cap": 400.0,
                    "start": "2024-06-01",
                    "end": "2024-06-30",
                }
            ]
        )
        assert np.array_equal(
            _run(df, cap, False)[(2, "ST_GAS")], _run(df, cap, True)[(2, "ST_GAS")]
        )


class TestItClipsPerUnitNotPerBin:
    def test_two_different_units_out_concurrently_still_zero_the_bin(self, monkeypatch):
        """Two units, each half the bin, concurrently out IS a full outage.

        The clip must not touch this: it is a per-UNIT ceiling, and a bin all of
        whose units are out is correctly 100 % derated. Clipping per bin would
        be a different (and wrong) mechanism.
        """
        cap = {(1, "ST_GAS"): 1000.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                },
                {
                    "plant": 1,
                    "unit": "2",
                    "cap": 500.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                },
            ]
        )
        on = _run(df, cap, True)[(1, "ST_GAS")]
        h0 = (31 + 28) * 24  # 2024-03-01 on the model clock
        assert np.allclose(on[h0 : h0 + 24], 0.0)


class TestPartialDerateRows:
    def test_two_overlapping_plateaus_of_one_unit_cap_at_the_unit(self, monkeypatch):
        """Two 60 %-removal plateaus of ONE unit cannot remove 120 % of it."""
        cap = {(1, "ST_GAS"): 1000.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 1000.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                    "derate": 0.4,
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 1000.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                    "derate": 0.4,
                },
            ]
        )
        off = _run(df, cap, False)[(1, "ST_GAS")]
        on = _run(df, cap, True)[(1, "ST_GAS")]
        h0 = (31 + 28) * 24
        assert np.allclose(off[h0 : h0 + 24], 0.0)  # 1.2 removed, clipped
        assert np.allclose(on[h0 : h0 + 24], 0.0)  # 1.0 removed — still fully out

    def test_two_partial_plateaus_summing_below_the_unit_are_untouched(
        self, monkeypatch
    ):
        """0.3 + 0.4 of one unit is possible, so the clip must not fire."""
        cap = {(1, "ST_GAS"): 1000.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 1000.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                    "derate": 0.7,
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 1000.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                    "derate": 0.6,
                },
            ]
        )
        off = _run(df, cap, False)[(1, "ST_GAS")]
        on = _run(df, cap, True)[(1, "ST_GAS")]
        # allclose, not array_equal: the two paths reach the same value by a
        # different order of float operations (sum-then-divide vs
        # min-then-divide). What matters is that the clip did not FIRE.
        assert np.allclose(off, on, rtol=0.0, atol=1e-12)
        h0 = (31 + 28) * 24
        assert np.allclose(on[h0 : h0 + 24], 1.0 - 0.7)


class TestTheCeilingIsTheLargestCapacityTheUnitClaims:
    def test_a_rerating_does_not_clip_a_legitimate_single_window(self, monkeypatch):
        """A unit re-rated mid-extract keeps its larger window intact.

        If the ceiling were the SMALLEST capacity the unit's rows claim, the
        later 500 MW window would be clipped to 400 MW — a legitimate single
        window silently reduced. The ceiling is the largest, so it is not.
        """
        cap = {(1, "ST_GAS"): 1000.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 400.0,
                    "start": "2024-01-05",
                    "end": "2024-01-20",
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-06-05",
                    "end": "2024-06-20",
                },
            ]
        )
        off = _run(df, cap, False)[(1, "ST_GAS")]
        on = _run(df, cap, True)[(1, "ST_GAS")]
        assert np.array_equal(off, on)


class TestScope:
    def test_off_is_byte_inert(self, monkeypatch):
        cap = {(1, "ST_GAS"): 1000.0, (3, "COAL"): 900.0}
        _patch(monkeypatch, cap)
        df = _events(
            [
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-01",
                    "end": "2024-03-20",
                },
                {
                    "plant": 1,
                    "unit": "1",
                    "cap": 500.0,
                    "start": "2024-03-20",
                    "end": "2024-04-10",
                },
                {
                    "plant": 3,
                    "unit": "B",
                    "group": "COAL",
                    "cap": 300.0,
                    "start": "2024-01-05",
                    "end": "2024-01-20",
                },
            ]
        )
        baseline = _unit_outage_factors_from_events(df, YEAR, HOURS, "", "MISO")
        explicit_off = _run(df, cap, False)
        assert set(baseline) == set(explicit_off)
        for k in baseline:
            assert np.array_equal(baseline[k], explicit_off[k])

    def test_the_maxgen_layer_never_receives_the_flag(self):
        """The maxgen layer is out of scope BY MEASUREMENT (phase-0 N-5).

        Its windows are already hour-granular, so it cannot carry a boundary-DAY
        artifact. It does not share the accumulator, and it must not grow the
        parameter either — a signature check, so a future edit that wires it in
        fails here rather than silently widening the blast radius.
        """
        sig = inspect.signature(outages.unit_outage_maxgen_derate_factors)
        assert "per_unit_clip" not in sig.parameters

    def test_every_layer_that_shares_the_accumulator_carries_the_flag(self):
        for fn in (
            outages.unit_outage_derate_factors,
            outages.unit_outage_short_derate_factors,
            outages.unit_partial_outage_derate_factors,
            outages.unit_layup_removed_fractions,
        ):
            assert "per_unit_clip" in inspect.signature(fn).parameters, fn.__name__


class TestRegistration:
    def test_default_is_off(self):
        assert ScenarioConfig().unit_outage_per_unit_clip is False

    def test_registered_in_the_cache_key_optional_fields(self):
        assert "unit_outage_per_unit_clip" in _CACHE_KEY_OPTIONAL_FIELDS
