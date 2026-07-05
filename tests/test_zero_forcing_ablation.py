"""Tests for the D-3 zero-forcing ablation twin (CLAUDE.md rule 21, audit §7).

Exercises the mechanism-registry-derived merchant off-list
(``market_sim.data.floor_mechanisms``) and the config transform
(``ScenarioConfig.as_zero_forcing_ablation``) on trivial synthetic configs — no
LP solve. The invariant under test: every MERCHANT floor/bridge is turned off
while the structural protected set (nuclear must-run, CHP steam, coal
take-or-pay) is untouched, and the off-list is derived from the registry so a
new floor is ablated by default.
"""

import unittest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import floor_mechanisms as fm


class MerchantRegistryTest(unittest.TestCase):
    """The merchant off-list derives from the D-2 mechanism registry."""

    def test_protected_set_never_merchant(self):
        merchant = fm.merchant_mechanism_ids()
        for keep in (fm.MECH_NUCLEAR, fm.MECH_CHP_STEAM, fm.MECH_COAL_MUSTRUN):
            self.assertNotIn(keep, merchant)
        # Firm interchange imports are a market-design boundary, not merchant.
        self.assertNotIn(fm.MECH_FIRM_IMPORT, merchant)
        self.assertNotIn(fm.MECH_NONE, merchant)

    def test_nyiso_selfsupply_is_merchant(self):
        # Outcome-anchored floor on a pseudo-unit — ablated (audit L2 / §2 DwC).
        self.assertIn(fm.MECH_NYISO_SELFSUPPLY, fm.merchant_mechanism_ids())

    def test_new_floor_is_merchant_by_default(self):
        # A hypothetical new mechanism id (not in the keep set) is merchant.
        new_id = max(fm.MECH_NAMES) + 1
        names = dict(fm.MECH_NAMES)
        names[new_id] = "hypothetical_new_floor"
        original = fm.MECH_NAMES
        try:
            fm.MECH_NAMES = names
            self.assertIn(new_id, fm.merchant_mechanism_ids())
        finally:
            fm.MECH_NAMES = original

    def test_ablation_fields_are_all_disabled(self):
        fields = fm.merchant_ablation_fields()
        # Every merchant field resolves to a boolean-off value.
        self.assertTrue(all(v is False for v in fields.values()))
        # Name-mismatched / multi-knob mechanisms are reconciled.
        self.assertIn("gas_st_netload_drag", fields)  # MECH name is st_netload_drag
        for k in (
            "caiso_ra_mustoffer",
            "caiso_ra_startup_bridge",
            "caiso_ra_bridge_decommit",
        ):
            self.assertIn(k, fields)


class ConfigAblationTest(unittest.TestCase):
    """ScenarioConfig.as_zero_forcing_ablation turns merchant floors off."""

    def _armed(self):
        return ScenarioConfig(
            reliability_floor=True,
            ct_netload_drag=True,
            gas_st_netload_drag=True,
            caiso_ra_mustoffer=True,
            caiso_ra_startup_bridge=True,
            caiso_ra_bridge_decommit=True,
            nyiso_local_selfsupply=True,
            ct_mustrun_per_plant=True,
            caiso_gas_commitment_floor=True,
            wefor_multiplier=0.7,
            wefor_residual=0.06,
        )

    def test_all_merchant_floors_off(self):
        a = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        for f in (
            "reliability_floor",
            "ct_netload_drag",
            "gas_st_netload_drag",
            "caiso_ra_mustoffer",
            "caiso_ra_startup_bridge",
            "caiso_ra_bridge_decommit",
            "nyiso_local_selfsupply",
            "ct_mustrun_per_plant",
            "ct_deployment_overlay",
            "reliability_deployment_overlay",
            "caiso_gas_commitment_floor",
        ):
            self.assertFalse(getattr(a, f), f)

    def test_wefor_haircuts_neutral(self):
        a = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        self.assertEqual(a.wefor_multiplier, 1.0)
        self.assertIsNone(a.wefor_residual)

    def test_protected_and_unrelated_fields_untouched(self):
        base = self._armed().with_overrides(
            chp_steam_following=True, mode="backcast", hydro_year="wet"
        )
        a = ScenarioConfig.as_zero_forcing_ablation(base)
        self.assertTrue(a.chp_steam_following)  # CHP steam kept
        self.assertEqual(a.mode, "backcast")
        self.assertEqual(a.hydro_year, "wet")

    def test_returns_copy_not_mutation(self):
        base = self._armed()
        _ = ScenarioConfig.as_zero_forcing_ablation(base)
        # The source config is unchanged (dataclasses.replace makes a copy).
        self.assertTrue(base.reliability_floor)
        self.assertEqual(base.wefor_multiplier, 0.7)

    def test_idempotent(self):
        a = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        b = ScenarioConfig.as_zero_forcing_ablation(a)
        self.assertEqual(a, b)

    def test_valid_config(self):
        # __post_init__ must not reject an all-floors-off config.
        a = ScenarioConfig.as_zero_forcing_ablation(self._armed())
        self.assertIsInstance(a, ScenarioConfig)


if __name__ == "__main__":
    unittest.main()
