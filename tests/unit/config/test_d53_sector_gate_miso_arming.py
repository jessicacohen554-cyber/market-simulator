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
        # The GLOBAL default forecast key. ADVANCED e5ecd4105ada3e58 ->
        # 547053bdfccd4264 on 2026-09-06 by capx D65-B (owner ruling Q47): the
        # COUPLED arming of ccs_retrofit_fixed_cost_co2_scaling (Act A, a declared
        # (b'-1) default flip) with ccs_retrofit_vom_adder 8.0 -> 2.95 $/MWh 2026$
        # (Act B, re-identified off the widened ATB extract). Act B is NOT a
        # _CACHE_KEY_OPTIONAL_FIELDS member, so it has no drop value and re-keys
        # unconditionally. Pre-declared BEFORE the solve in
        # docs/handoffs/PRECOMMIT-capx-d65b-2026-09-06.md §3; cache-epoch ledger
        # entry 2026-09-06c in src/market_sim/results/cache.py. Nothing about THIS
        # field moved — the pin advances because the global default did.
        self.assertEqual(ScenarioConfig().cache_key(), "547053bdfccd4264")
        self.assertEqual(
            ScenarioConfig(mode="backcast").cache_key(), "f61891696e671969"
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
        # Rule 25: the gate arms PER ISO, on that ISO's own ISOConfig and its
        # own evidence. MISO (capx D53, 2026-09-05) and PJM (owner ruling Q56,
        # capx D78-ARM, 2026-09-06, on the D78-R2 / D78-R3 full window) each
        # carry their own arm; every other ISO still resolves the gate OFF
        # and carries no override until it measures its own sector census.
        for iso in SUPPORTED_ISOS:
            if iso in ("MISO", "PJM"):
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
