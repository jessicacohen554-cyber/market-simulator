"""Tests for the D-3 zero-forcing ablation registry (audit §7 D-3 / rule 20).

Covers the off-list registry in ``market_sim.data.floor_mechanisms`` and the
``ScenarioConfig.as_zero_forcing_ablation`` classmethod that consumes it. The
ablation twin is a reference solve with every MERCHANT floor/bridge OFF, keeping
only the structural must-run set (nuclear / CHP-steam / coal take-or-pay). The
off-list is DERIVED from the D-2 mechanism registry, so a new floor mechanism is
ablated by default or the coverage guard fails — these tests pin both.
"""

import unittest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import floor_mechanisms as fm


class TestAblationRegistry(unittest.TestCase):
    """The mechanism-id → ScenarioConfig-field ablation registry."""

    def test_every_mechanism_is_classified(self):
        """Coverage guard: no mechanism id is left unclassified."""
        fm.assert_ablation_coverage()  # raises AssertionError on a gap

    def test_kept_and_ablated_are_disjoint_and_total(self):
        """Every id is EITHER kept OR ablated, never both, never neither."""
        kept = set(fm.MECH_ABLATION_KEPT)
        ablated = set(fm.MECH_ABLATION_FIELDS)
        self.assertEqual(kept & ablated, set())
        self.assertEqual(kept | ablated, set(fm.MECH_NAMES))

    def test_structural_mustrun_kept(self):
        """Nuclear / CHP-steam / coal take-or-pay carry no ablation entry."""
        for mech in (fm.MECH_NUCLEAR, fm.MECH_CHP_STEAM, fm.MECH_COAL_MUSTRUN):
            self.assertIn(mech, fm.MECH_ABLATION_KEPT)
            self.assertNotIn(mech, fm.MECH_ABLATION_FIELDS)

    def test_merchant_floors_ablated(self):
        """The named merchant floors/bridges are in the off-list."""
        for mech in (
            fm.MECH_RELIABILITY_FLOOR,
            fm.MECH_CT_NETLOAD_DRAG,
            fm.MECH_ST_NETLOAD_DRAG,
            fm.MECH_RA_MUSTOFFER,
            fm.MECH_NYISO_SELFSUPPLY,
        ):
            self.assertIn(mech, fm.MECH_ABLATION_FIELDS)

    def test_import_boundary_kept(self):
        """Firm-import bands are a network boundary, not merchant forcing."""
        self.assertIn(fm.MECH_FIRM_IMPORT, fm.MECH_ABLATION_KEPT)

    def test_overrides_include_ra_companions_and_wefor(self):
        """RA bridge + decommit and the WEFOR haircuts are neutralized."""
        ov = fm.zero_forcing_field_overrides()
        self.assertIs(ov["caiso_ra_mustoffer"], False)
        self.assertIs(ov["caiso_ra_startup_bridge"], False)
        self.assertIs(ov["caiso_ra_bridge_decommit"], False)
        self.assertIsNone(ov["wefor_residual"])
        self.assertEqual(ov["wefor_multiplier"], 1.0)

    def test_coverage_guard_fails_on_unclassified_mechanism(self):
        """A new mechanism id with no ablation decision trips the guard."""
        original = dict(fm.MECH_NAMES)
        try:
            fm.MECH_NAMES[99] = "hypothetical_new_floor"
            with self.assertRaises(AssertionError):
                fm.assert_ablation_coverage()
        finally:
            fm.MECH_NAMES.clear()
            fm.MECH_NAMES.update(original)


class TestAsZeroForcingAblation(unittest.TestCase):
    """ScenarioConfig.as_zero_forcing_ablation on a trivial config."""

    def _armed(self):
        """A minimal backcast config with every merchant floor armed."""
        return ScenarioConfig(
            mode="backcast",
            reliability_floor=True,
            ct_netload_drag=True,
            gas_st_netload_drag=True,
            caiso_ra_mustoffer=True,
            caiso_ra_startup_bridge=True,
            caiso_ra_bridge_decommit=True,
            nyiso_local_selfsupply=True,
            caiso_gas_commitment_floor=True,
            wefor_residual=0.06,
            wefor_multiplier=0.7,
        )

    def test_merchant_floors_off(self):
        twin = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        self.assertFalse(twin.reliability_floor)
        self.assertFalse(twin.ct_netload_drag)
        self.assertFalse(twin.gas_st_netload_drag)
        self.assertFalse(twin.caiso_ra_mustoffer)
        self.assertFalse(twin.caiso_ra_startup_bridge)
        self.assertFalse(twin.caiso_ra_bridge_decommit)
        self.assertFalse(twin.nyiso_local_selfsupply)
        self.assertFalse(twin.caiso_gas_commitment_floor)

    def test_wefor_neutralized(self):
        twin = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        self.assertIsNone(twin.wefor_residual)
        self.assertEqual(twin.wefor_multiplier, 1.0)

    def test_non_floor_knobs_untouched(self):
        """Offer curves / fuel / fleet knobs carry through unchanged."""
        cfg = self._armed().with_overrides(
            td_loss_factor=0.05, battery_dispatch_adder=1.25
        )
        twin = ScenarioConfig.as_zero_forcing_ablation(cfg)
        self.assertEqual(twin.td_loss_factor, 0.05)
        self.assertEqual(twin.battery_dispatch_adder, 1.25)
        self.assertEqual(twin.mode, "backcast")

    def test_structural_mustrun_untouched(self):
        """The ablation does not disturb structural must-run flags."""
        cfg = self._armed().with_overrides(chp_export_floor_measured=True)
        twin = ScenarioConfig.as_zero_forcing_ablation(cfg)
        # chp_export_floor_measured (steam-host physics) is NOT in the off-list.
        self.assertTrue(twin.chp_export_floor_measured)

    def test_idempotent(self):
        """Applying the transform twice equals applying it once."""
        once = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        twice = ScenarioConfig.as_zero_forcing_ablation(once)
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()
