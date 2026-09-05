"""capx D53 (2026-09-05): the retirement-screen sector gate is ARMED FOR MISO ONLY.

Owner instruction on the measured A/B (``FINDING-capx-d53-2026-09-05.md`` §6.1):
``retirement_sector_gate`` stays ``False`` on the dataclass and is armed through
MISO's ``default_scenario_overrides`` (rule 25 ``[R-ISO-SCOPE]``). These tests
pin the four things that arming must and must not move: the MISO forecast
config resolves the gate ON; every other ISO resolves it OFF; the pinned
``ScenarioConfig()`` and bare-backcast keys are unmoved; and a plain backcast
of MISO still coerces the gate to its default (a backcast runs no capacity
evolution), so no backcast keeper key can move.
"""

from __future__ import annotations

import unittest

from market_sim.config.iso_configs import (
    SUPPORTED_ISOS,
    apply_iso_scenario_defaults,
    get_iso_config,
)
from market_sim.config.scenarios import ScenarioConfig


class TestSectorGateMisoArming(unittest.TestCase):
    def test_default_stays_off_and_pinned_keys_are_unmoved(self):
        self.assertFalse(ScenarioConfig().retirement_sector_gate)
        self.assertEqual(ScenarioConfig().cache_key(), "e5ecd4105ada3e58")
        self.assertEqual(
            ScenarioConfig(mode="backcast").cache_key(), "6a2845e50951394e"
        )

    def test_miso_forecast_resolves_the_gate_on(self):
        cfg = apply_iso_scenario_defaults(
            ScenarioConfig(iso="MISO", mode="forecast", hindcast=True), "MISO"
        )
        self.assertTrue(cfg.retirement_sector_gate)
        # The armed MISO config keys distinctly from the unarmed one (the
        # field enters the hash the moment it leaves its declared default).
        unarmed = apply_iso_scenario_defaults(
            ScenarioConfig(iso="MISO", mode="forecast", hindcast=True), "MISO"
        )
        unarmed.retirement_sector_gate = False
        self.assertNotEqual(cfg.cache_key(), unarmed.cache_key())

    def test_every_other_iso_resolves_the_gate_off(self):
        for iso in SUPPORTED_ISOS:
            if iso == "MISO":
                continue
            cfg = apply_iso_scenario_defaults(
                ScenarioConfig(iso=iso, mode="forecast"), iso
            )
            self.assertFalse(cfg.retirement_sector_gate, iso)
            self.assertNotIn(
                "retirement_sector_gate",
                get_iso_config(iso).default_scenario_overrides,
                iso,
            )

    def test_miso_backcast_still_coerces_the_gate_to_default(self):
        cfg = apply_iso_scenario_defaults(
            ScenarioConfig(iso="MISO", mode="backcast"), "MISO"
        )
        self.assertFalse(cfg.retirement_sector_gate)
