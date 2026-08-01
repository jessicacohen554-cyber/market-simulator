"""Validation of the regulated-PRB committed-run night-level floor (miso-113).

Covers :func:`market_sim.model.commitment.coal_selfcommit_night_min_gen` and
:func:`market_sim.pipeline.commitment.build_coal_night_floor_p1_prep` — the
P1-native FLOOR successor to the two R-adjudicated offer-side forms of
regulated-PRB self-commitment (``coal_prb_committed_dispatchable``, miso-111;
``coal_prb_committed_split``, miso-112). Contract:

* flag off ⇒ ``None`` (byte-identical P1 — rule 26), and an armed mechanism on
  a fleet carrying no measured floor share is likewise ``None`` rather than an
  all-zero fleet swap;
* the WINDOW is the plant's OWN P0-detected committed run and nothing else —
  a plant the base-cost solve has offline is never floored, which is the whole
  rule-17 [R-FLOOR-WINDOW] claim and the reason off-window binding is
  structurally impossible rather than merely unobserved;
* the floor is applied PER TRANCHE at the fill-order share assembly computed,
  so a plant floor larger than ``_committed`` reaches ``_econ`` instead of
  being silently collapsed by the clip to the tranche's own capacity;
* the floor is availability-scaled, so ``min_gen <= pmax x availability`` holds
  by construction and an outage hour carries no floor;
* rule 19 [R-ONE-MECH]: the flag is mutually exclusive with BOTH offer-side
  forms, enforced at ``ScenarioConfig.__post_init__``;
* D-2 attribution: floored gen-hours tagged ``MECH_COAL_SELFCOMMIT_NIGHT``,
  separate from the coal must-run and min-config ids.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.floor_mechanisms import (
    MECH_COAL_SELFCOMMIT_NIGHT,
    MECH_NAMES,
    assert_ablation_coverage,
)
from market_sim.model.commitment import coal_selfcommit_night_min_gen
from market_sim.pipeline.commitment import build_coal_night_floor_p1_prep

_HOURS = 48


def _tranche(suffix, cap, night_floor=0.0, plant="1733"):
    """One CAMPD tranche row of plant ``plant``."""
    return Generator(
        unit_id=f"{plant}_{suffix}",
        name=f"{plant} {suffix}",
        zone="z",
        fuel_type="coal",
        pmax_mw=cap,
        pmin_mw=0.0,
        heat_rate=10.0,
        eford=0.0,
        plant_group="COAL",
        is_campd_bin=True,
        coal_supply="prb",
        plant_code=int(plant),
        coal_night_floor_pmin_mw=night_floor,
    )


class _R0:
    """The minimal ``r0`` shape the P1 fleet prep reads."""

    def __init__(self, dispatch):
        self.dispatch = dispatch


def _plant_fleet():
    """A 1,000 MW PRB plant: 300 mustrun / 300 committed / 400 econ.

    Its measured night level is 0.55 of nameplate, so the incremental floor
    above the 0.30 contracted band is 250 MW — which does NOT fit in the
    300 MW committed tranche alone once the fill also has to cover... it does,
    so ``_econ`` stays unfloored here and the spill case gets its own test.
    """
    return [
        _tranche("mustrun", 300.0),
        _tranche("committed", 300.0, night_floor=250.0),
        _tranche("econ00", 400.0),
    ]


class TestWindow(unittest.TestCase):
    """The floor binds inside the plant's own P0 run and nowhere else."""

    def test_offline_hours_are_never_floored(self):
        fleet = _plant_fleet()
        fa = generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)
        # The plant runs h0-23 and is completely off h24-47.
        p0 = np.zeros((len(fleet), _HOURS))
        p0[0, :24] = 300.0
        p0[1, :24] = 200.0
        floor = coal_selfcommit_night_min_gen(p0, fa, fleet)
        self.assertTrue(np.all(floor[:, 24:] == 0.0), "floored an offline hour")
        np.testing.assert_allclose(floor[1, :24], 250.0)
        # The unfloored tranches carry no share, armed or not.
        self.assertEqual(floor[0].max(), 0.0)
        self.assertEqual(floor[2].max(), 0.0)

    def test_plant_offline_all_year_is_a_no_op(self):
        fleet = _plant_fleet()
        fa = generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)
        floor = coal_selfcommit_night_min_gen(np.zeros((len(fleet), _HOURS)), fa, fleet)
        self.assertEqual(floor.max(), 0.0, "the floor manufactured a start")

    def test_window_is_the_plant_total_not_the_floored_tranche(self):
        """A plant online only on its mustrun band is still committed."""
        fleet = _plant_fleet()
        fa = generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)
        p0 = np.zeros((len(fleet), _HOURS))
        p0[0, :] = 300.0  # only the mustrun tranche dispatches in P0
        floor = coal_selfcommit_night_min_gen(p0, fa, fleet)
        self.assertTrue(np.all(floor[1] == 250.0))


class TestFillOrderSpill(unittest.TestCase):
    """A floor larger than ``_committed`` reaches ``_econ`` (not collapsed)."""

    def test_spill_share_is_floored_on_econ(self):
        fleet = [
            _tranche("mustrun", 0.0 + 1e-9),
            _tranche("committed", 200.0, night_floor=200.0),
            _tranche("econ00", 400.0, night_floor=150.0),
        ]
        fa = generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)
        p0 = np.full((len(fleet), _HOURS), 100.0)
        floor = coal_selfcommit_night_min_gen(p0, fa, fleet)
        np.testing.assert_allclose(floor[1], 200.0)
        np.testing.assert_allclose(floor[2], 150.0)
        # Total plant floor == the measured night level, not one slice of it.
        self.assertAlmostEqual(float(floor[:, 0].sum()), 350.0)


class TestFeasibility(unittest.TestCase):
    """Availability scaling keeps ``min_gen <= pmax x availability``."""

    def test_floor_scales_with_availability(self):
        fleet = _plant_fleet()
        fa = generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)
        avail = np.asarray(fa.availability, dtype=float).copy()
        avail[1, :12] = 0.5
        avail[1, 12:16] = 0.0
        fa = fa.__class__(**{**fa.__dict__, "availability": avail})
        p0 = np.full((len(fleet), _HOURS), 100.0)
        floor = coal_selfcommit_night_min_gen(p0, fa, fleet)
        np.testing.assert_allclose(floor[1, :12], 125.0)
        self.assertEqual(floor[1, 12:16].max(), 0.0, "floored an outage hour")
        self.assertTrue(
            np.all(floor <= np.asarray(fa.pmax)[:, None] * avail + 1e-9),
            "floor exceeds pmax x availability (infeasible P1 bound)",
        )


class TestHookGating(unittest.TestCase):
    """Flag/scope gating and the D-2 attribution the hook writes."""

    def _fa_and_fleet(self):
        fleet = _plant_fleet()
        return fleet, generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)

    def test_flag_off_is_none(self):
        fleet, fa = self._fa_and_fleet()
        self.assertIsNone(
            build_coal_night_floor_p1_prep(ScenarioConfig(iso="MISO"), fleet, fa)
        )

    def test_armed_but_unmeasured_fleet_is_none(self):
        """Self-scoping (rule 25): no measured share ⇒ no fleet swap."""
        fleet = [_tranche("mustrun", 300.0), _tranche("committed", 300.0)]
        fa = generators_to_fleet_arrays(fleet, ["z"], hours=_HOURS)
        prep = build_coal_night_floor_p1_prep(
            ScenarioConfig(iso="MISO").with_overrides(coal_prb_night_floor=True),
            fleet,
            fa,
        )
        self.assertIsNotNone(prep)
        self.assertIsNone(prep(_R0(np.full((len(fleet), _HOURS), 100.0))))

    def test_floored_hours_carry_the_mechanism_id(self):
        fleet, fa = self._fa_and_fleet()
        prep = build_coal_night_floor_p1_prep(
            ScenarioConfig(iso="MISO").with_overrides(coal_prb_night_floor=True),
            fleet,
            fa,
        )
        p0 = np.zeros((len(fleet), _HOURS))
        p0[0, :24] = 300.0
        fa_floored = prep(_R0(p0))
        self.assertIsNotNone(fa_floored)
        np.testing.assert_allclose(fa_floored.min_gen[1, :24], 250.0)
        self.assertTrue(np.all(fa_floored.min_gen[1, 24:] == 0.0))
        mech = np.asarray(fa_floored.min_gen_mechanism)
        self.assertTrue(np.all(mech[1, :24] == MECH_COAL_SELFCOMMIT_NIGHT))
        self.assertTrue(np.all(mech[1, 24:] != MECH_COAL_SELFCOMMIT_NIGHT))


class TestRegistrations(unittest.TestCase):
    """Rule 19/20 registrations that must land with the mechanism itself."""

    def test_mutually_exclusive_with_both_offer_side_forms(self):
        for field in ("coal_prb_committed_split", "coal_prb_committed_dispatchable"):
            with self.subTest(field=field), self.assertRaises(ValueError):
                ScenarioConfig(iso="MISO").with_overrides(
                    coal_prb_night_floor=True, **{field: True}
                )

    def test_mechanism_is_named_and_ablatable(self):
        self.assertEqual(
            MECH_NAMES[MECH_COAL_SELFCOMMIT_NIGHT], "coal_selfcommit_night"
        )
        # Rule 20: a merchant floor must be ablatable, not silently exempt.
        assert_ablation_coverage()


if __name__ == "__main__":
    unittest.main()
