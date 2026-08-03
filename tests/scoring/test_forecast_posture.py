"""Tests for the ONE shipped-capacity-posture reader (owner decision C.4(a) B1).

Trivial-first, LP-free. The contract is that **every** runner answers "what
capacity-price posture does production ship?" from the same place — the
``ScenarioConfig`` field — so a T1-F leg, a T1-H leg and the readiness battery
cannot disagree about it. The divergence this replaces was real and silent:
``ff_readiness_battery.GOLDEN_CMC_BY_ISO`` carried ``NYISO: True`` while the
shipped field omits NYISO, so every ``--golden-posture`` NYISO leg solved
curve-ON against a production path that runs curve-OFF (audit FR-14, one lane
over from the hindcast case FFR-2E fixed).

Four seams, no solve:

* the reader returns the live dataclass default, never a copy of it (rule 24);
* it hands back a fresh mapping, so one caller's mutation cannot leak;
* the per-ISO resolver agrees with a real solve's resolver, ISO by ISO —
  including NYISO and ERCOT resolving OFF by the model's own fallthrough;
* the three runner surfaces (hindcast harness, full-horizon runner, readiness
  battery) all land on that one answer.
"""

from __future__ import annotations

import unittest

from market_sim.config.capacity_market import (
    MARKET_DESIGN,
    resolve_capacity_market_clearing,
)
from market_sim.config.scenarios import ScenarioConfig
from scripts.lib.forecast_posture import (
    shipped_capacity_clearing,
    shipped_capacity_clearing_by_iso,
)


class ShippedMappingTest(unittest.TestCase):
    """The reader reads; it never mirrors."""

    def test_returns_the_live_scenarioconfig_default(self):
        self.assertEqual(
            shipped_capacity_clearing_by_iso(),
            ScenarioConfig().capacity_market_clearing_by_iso,
        )

    def test_returns_a_fresh_mapping(self):
        first = shipped_capacity_clearing_by_iso()
        assert first is not None
        first["PJM"] = False
        self.assertNotEqual(first, shipped_capacity_clearing_by_iso())
        self.assertEqual(
            shipped_capacity_clearing_by_iso(),
            ScenarioConfig().capacity_market_clearing_by_iso,
        )


class PerIsoResolutionTest(unittest.TestCase):
    """The per-ISO answer equals what a solve would resolve."""

    def test_agrees_with_the_model_resolver_for_every_iso(self):
        for iso in MARKET_DESIGN:
            cfg = ScenarioConfig(iso=iso, mode="forecast")
            self.assertEqual(
                shipped_capacity_clearing(iso),
                bool(resolve_capacity_market_clearing(cfg, iso)),
                msg=iso,
            )

    def test_nyiso_and_ercot_resolve_off(self):
        # The signature names both by hand: "NYISO must resolve curve-OFF,
        # matching production." NYISO is absent from the shipped mapping
        # (excluded pending re-calibration) and ERCOT is energy-only; both fall
        # through to the scalar default, which is OFF.
        self.assertFalse(shipped_capacity_clearing("NYISO"))
        self.assertFalse(shipped_capacity_clearing("ERCOT"))

    def test_case_insensitive(self):
        self.assertEqual(
            shipped_capacity_clearing("pjm"), shipped_capacity_clearing("PJM")
        )


class OneAnswerAcrossRunnersTest(unittest.TestCase):
    """All three runner surfaces resolve the same posture (the whole point)."""

    def test_hindcast_harness_and_full_horizon_and_battery_agree(self):
        from scripts import ff_readiness_battery as B
        from scripts import run_capacity_hindcast as H
        from scripts import run_full_horizon as F

        shipped = shipped_capacity_clearing_by_iso()

        # T1-H harness: the default ("shipped") posture.
        for iso in MARKET_DESIGN:
            by_iso, label = H.resolve_capacity_clearing_posture(iso, False, False)
            self.assertEqual(label, "shipped")
            self.assertEqual(by_iso, shipped, msg=iso)

        # T1-F runner under --golden-posture, and the readiness battery.
        for iso in MARKET_DESIGN:
            self.assertEqual(
                F.reference_config(
                    iso, 2026, 2026, cmc=False, golden_posture=True
                ).capacity_market_clearing_by_iso,
                shipped,
                msg=iso,
            )
            self.assertEqual(
                B.golden_posture_config(
                    iso, 2026, 2026
                ).capacity_market_clearing_by_iso,
                shipped,
                msg=iso,
            )

    def test_the_parallel_constant_is_gone(self):
        # Rule 26 [R-DELETE]: removed, not zeroed.
        from scripts import ff_readiness_battery as B

        self.assertFalse(hasattr(B, "GOLDEN_CMC_BY_ISO"))


if __name__ == "__main__":
    unittest.main()
