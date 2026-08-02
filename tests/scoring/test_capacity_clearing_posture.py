"""Tests for the FFR-2E capacity-price posture of the hindcast harness (FR-14).

Trivial-first, LP-free: the *contract* is that the capacity hindcast exercises
the capacity-price formation the FORECAST ships, so an FC-3 verdict scores the
configuration production runs (peer review §3.1, "validate the configuration you
ship"). Four seams are asserted without a solve —

* :func:`production_capacity_clearing_default` reads the live
  ``ScenarioConfig`` default rather than a hardcoded copy (rule 24), so an owner
  flip is followed by the harness with no edit;
* :func:`resolve_capacity_clearing_posture` maps the three postures
  (shipped / ``--fixed-net-cone`` / ``--capacity-market-clearing``) onto the
  ``capacity_market_clearing_by_iso`` values the config already supports, and
  refuses the contradictory pair;
* ``build_config`` carries each posture into a real ``ScenarioConfig`` whose
  ``__post_init__`` does NOT coerce the field away on a hindcast leg, so the
  resolved per-ISO gate reaches the capacity screens;
* the ``--fixed-net-cone`` arm reproduces the PRE-FFR-2E harness default
  byte-identically (``None``), so every committed leg's scored FC-3 verdict
  still describes the run that produced it.
"""

from __future__ import annotations

import unittest

from market_sim.config.capacity_market import (
    MARKET_DESIGN,
    resolve_capacity_market_clearing,
)
from market_sim.config.scenarios import ScenarioConfig
from scripts import run_capacity_hindcast as H


class ProductionDefaultTest(unittest.TestCase):
    """The harness reads the shipped default; it never mirrors it."""

    def test_reads_the_live_scenarioconfig_default(self):
        self.assertEqual(
            H.production_capacity_clearing_default(),
            ScenarioConfig().capacity_market_clearing_by_iso,
        )

    def test_returned_mapping_is_a_copy(self):
        # A shared mutable default would let one leg's mutation leak into the
        # next config built in the same process.
        first = H.production_capacity_clearing_default()
        assert first is not None
        first["PJM"] = False
        self.assertNotEqual(first, H.production_capacity_clearing_default())


class PostureResolutionTest(unittest.TestCase):
    """The three postures and their mutual exclusion."""

    def test_shipped_is_the_default_posture(self):
        for iso in MARKET_DESIGN:
            by_iso, label = H.resolve_capacity_clearing_posture(iso, False, False)
            self.assertEqual(label, "shipped")
            self.assertEqual(by_iso, ScenarioConfig().capacity_market_clearing_by_iso)

    def test_fixed_net_cone_reproduces_the_pre_ffr2e_default(self):
        for iso in MARKET_DESIGN:
            by_iso, label = H.resolve_capacity_clearing_posture(iso, False, True)
            self.assertIsNone(by_iso)
            self.assertEqual(label, "fixed_net_cone")

    def test_force_on_arms_this_iso_only(self):
        by_iso, label = H.resolve_capacity_clearing_posture("NYISO", True, False)
        self.assertEqual(by_iso, {"NYISO": True})
        self.assertEqual(label, "forced_curve")

    def test_contradictory_flags_refuse(self):
        with self.assertRaises(SystemExit):
            H.resolve_capacity_clearing_posture("PJM", True, True)


class ResolvedGateTest(unittest.TestCase):
    """What the capacity screens actually see, per ISO, per posture."""

    # The ISOs the production default ships curve-ON. Derived from the live
    # default so the assertion follows an owner flip instead of pinning today's
    # set as a fit target.
    @property
    def shipped_on(self) -> set[str]:
        default = ScenarioConfig().capacity_market_clearing_by_iso or {}
        return {iso for iso, on in default.items() if on}

    def test_shipped_posture_gate_matches_production(self):
        for iso in MARKET_DESIGN:
            config = H.build_config(iso, 2021, 2025, "realized", vintage=2020)
            self.assertEqual(
                resolve_capacity_market_clearing(config, iso),
                iso in self.shipped_on,
                msg=f"{iso} shipped-posture gate",
            )

    def test_fixed_arm_gate_is_off_everywhere(self):
        for iso in MARKET_DESIGN:
            config = H.build_config(
                iso, 2021, 2025, "realized", vintage=2020, fixed_net_cone=True
            )
            self.assertIsNone(config.capacity_market_clearing_by_iso)
            self.assertFalse(resolve_capacity_market_clearing(config, iso))

    def test_force_on_arm_gate_is_on_for_an_iso_production_leaves_off(self):
        # NYISO is curve-eligible but production ships it OFF, so the RC-1B
        # probe flag is the only way to exercise its curve.
        self.assertNotIn("NYISO", self.shipped_on)
        config = H.build_config(
            "NYISO", 2021, 2025, "realized", vintage=2020, capacity_market_clearing=True
        )
        self.assertTrue(resolve_capacity_market_clearing(config, "NYISO"))

    def test_post_init_does_not_coerce_the_hindcast_leg(self):
        # The field is coerced to None in a plain backcast (keeper byte-
        # identity) but must survive on a hindcast leg, or the shipped posture
        # would silently never reach the screens.
        config = H.build_config("PJM", 2021, 2025, "realized", vintage=2020)
        self.assertEqual(config.mode, "forecast")
        self.assertTrue(config.hindcast)
        self.assertIsNotNone(config.capacity_market_clearing_by_iso)


class PostureDivergenceTest(unittest.TestCase):
    """Where the two arms feed different $/firm-MW-yr into the screens.

    The seam is shared by all three capacity screens (rule 19), so a price
    identity here IS a screen identity — this is what makes CAISO's curve-ON
    posture provably inert without an LP.
    """

    def _price(self, iso: str, config, position: float, year: int) -> float:
        return MARKET_DESIGN[iso].capacity_price_per_firm_mw_yr(
            config, position, iso=iso, year=year
        )

    def test_caiso_arms_are_identical_no_published_curve(self):
        # CAISO's RA construction is not an auction, so the registry carries no
        # demand curve; the seam falls through to the fixed anchor in BOTH
        # postures (FF-2C §1.3 pricing no-op, re-confirmed at HEAD).
        self.assertFalse(bool(MARKET_DESIGN["CAISO"].demand_curve))
        self.assertIsNone(MARKET_DESIGN["CAISO"].seasonal_rbdc)
        shipped = H.build_config("CAISO", 2021, 2025, "realized", vintage=2020)
        fixed = H.build_config(
            "CAISO", 2021, 2025, "realized", vintage=2020, fixed_net_cone=True
        )
        self.assertTrue(resolve_capacity_market_clearing(shipped, "CAISO"))
        for year in (2021, 2023, 2025, 2028):
            for pos in (0.95, 1.0, 1.05, 1.15):
                self.assertEqual(
                    self._price("CAISO", shipped, pos, year),
                    self._price("CAISO", fixed, pos, year),
                    msg=f"CAISO {year} @ {pos}",
                )

    def test_ercot_is_energy_only_in_both_arms(self):
        shipped = H.build_config("ERCOT", 2021, 2025, "realized", vintage=2020)
        fixed = H.build_config(
            "ERCOT", 2021, 2025, "realized", vintage=2020, fixed_net_cone=True
        )
        for cfg in (shipped, fixed):
            self.assertEqual(self._price("ERCOT", cfg, 1.0, 2025), 0.0)

    def test_curve_isos_diverge_from_the_fixed_arm(self):
        # PJM / MISO / NEISO all carry a published curve (or seasonal RBDC), so
        # the shipped posture must price differently from the flat stub at a
        # SHORT position — otherwise the flip is not reaching the seam.
        for iso in ("PJM", "MISO", "NEISO"):
            shipped = H.build_config(iso, 2021, 2025, "realized", vintage=2020)
            fixed = H.build_config(
                iso, 2021, 2025, "realized", vintage=2020, fixed_net_cone=True
            )
            self.assertGreater(
                self._price(iso, shipped, 0.95, 2025),
                self._price(iso, fixed, 0.95, 2025),
                msg=f"{iso} short-position price",
            )

    def test_pjm_2028_vintage_pays_a_floor_past_the_zero_cross(self):
        # FFR-2C re-anchored PJM's net-CONE from the 2028/29 Planning-Parameters
        # workbook, whose curve ends at a PUBLISHED PRICE FLOOR rather than a
        # zero-cross. evaluate_demand_curve flat-extrapolates the rightmost
        # point, so a long fleet is paid the floor forever — the mechanism that
        # supersedes FF-2C's "quantitatively inert" verdict from 2028 onward.
        shipped = H.build_config("PJM", 2026, 2028, "realized", vintage=2023)
        long_position = 1.15
        self.assertEqual(self._price("PJM", shipped, long_position, 2027), 0.0)
        self.assertGreater(self._price("PJM", shipped, long_position, 2028), 0.0)


if __name__ == "__main__":
    unittest.main()
