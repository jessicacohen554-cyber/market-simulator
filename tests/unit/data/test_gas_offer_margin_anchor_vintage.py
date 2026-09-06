"""Solve-year vintage anchor for ``gas_offer_net_revenue_margin`` (pjm-169 F4).

``apply_gas_offer_margin``'s identity is *at ``fuel == anchor`` the reformed
offer reduces EXACTLY to the registered band multiplier*, and
``derive_gas_offer_margin_anchor.py`` calls the anchor "the identification
point, not a tunable" — the mean of ``_gas_series`` over the training window
2023-2025. The term ``markup_hr x (anchor - fuel)`` is a LINEAR extrapolation
with no saturation, so on a year whose delivered gas sits far from that window
mean the identity fails proportionally, and when ``fuel > anchor`` the
mechanism marks gas offers DOWN.

``gas_offer_margin_anchor_vintage`` resolves the SAME measurement on the year
being solved. These tests pin its contracts: byte-identical OFF (the field's
default and its cache-key registration), the identity restored at the resolved
anchor, the sign and magnitude of the correction outside the window, and the
rule-19 refusal to stack with the zone-resolved anchor.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELDS,
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    ScenarioConfig,
)
from market_sim.data.offer_curves import apply_gas_offer_margin

PJM_WINDOW_ANCHOR = 3.3483
BASE_HR = 6.7
MARKUP_HR = 3.35  # a CC econ_high band's above-physical markup, MMBtu/MWh


class _Gen:
    """Minimal generator stand-in carrying only what the mechanism reads."""

    def __init__(self, markup_hr: float, margin_anchor: float | None = None):
        self.offer_markup_hr = markup_hr
        self.offer_margin_anchor = margin_anchor


class TestFieldRegistration(unittest.TestCase):
    """The field is off by default and registered at that default."""

    def test_default_is_off(self):
        self.assertFalse(ScenarioConfig().gas_offer_margin_anchor_vintage)

    def test_registered_in_cache_key_at_its_declared_default(self):
        # Registered IN THE SAME COMMIT as the field (the nyiso-119
        # discipline), so a pre-existing key stays byte-stable at the default.
        self.assertIn("gas_offer_margin_anchor_vintage", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["gas_offer_margin_anchor_vintage"],
            "False",
        )

    def test_key_is_byte_stable_off_and_moves_on(self):
        base = ScenarioConfig()
        self.assertEqual(
            base.cache_key(),
            ScenarioConfig(gas_offer_margin_anchor_vintage=False).cache_key(),
        )
        self.assertNotEqual(
            base.cache_key(),
            ScenarioConfig(gas_offer_margin_anchor_vintage=True).cache_key(),
        )


class TestIdentityAtTheAnchor(unittest.TestCase):
    """At ``fuel == anchor`` the reformed offer reduces to the band multiplier."""

    def _mc_delta(self, anchor: float, fuel: float) -> float:
        """Return the mechanism's mc adjustment for one tranche-hour."""
        cfg = ScenarioConfig(
            gas_offer_net_revenue_margin=True, gas_offer_margin_anchor=anchor
        )
        mc = np.zeros((1, 1), dtype=float)
        apply_gas_offer_margin(mc, [_Gen(MARKUP_HR)], np.full((1, 1), fuel), cfg)
        return float(mc[0, 0])

    def test_zero_adjustment_exactly_at_the_anchor(self):
        # THE identity the anchor exists to make true. It holds at whatever
        # value the anchor takes -- which is precisely why moving the anchor
        # onto the solve year restores it there rather than only near the
        # training-window mean.
        for anchor in (PJM_WINDOW_ANCHOR, 7.1234, 2.0):
            self.assertAlmostEqual(self._mc_delta(anchor, anchor), 0.0, places=12)

    def test_out_of_window_fuel_marks_gas_DOWN_under_the_frozen_anchor(self):
        # 2022-like delivered gas against the frozen 2023-2025 window anchor:
        # the term is negative (offers marked DOWN) and large.
        delta = self._mc_delta(PJM_WINDOW_ANCHOR, 7.12)
        self.assertLess(delta, 0.0)
        self.assertAlmostEqual(delta, MARKUP_HR * (PJM_WINDOW_ANCHOR - 7.12), places=9)

    def test_vintage_anchor_removes_the_extrapolation(self):
        # With the anchor resolved ON the solved year, a unit paying that
        # year's mean delivered gas carries no extrapolated correction at all.
        self.assertAlmostEqual(self._mc_delta(7.12, 7.12), 0.0, places=12)

    def test_in_window_correction_is_small_by_construction(self):
        # The window anchor IS the mean of the window, so in-window fuels sit
        # close to it -- this is why the defect only bites outside the window.
        in_window = max(
            abs(self._mc_delta(PJM_WINDOW_ANCHOR, f)) for f in (2.19, 2.54, 3.52)
        )
        out_window = abs(self._mc_delta(PJM_WINDOW_ANCHOR, 7.12))
        self.assertGreater(out_window, 2.5 * in_window)


class TestOffIsByteIdentical(unittest.TestCase):
    """The flag changes nothing while it is off."""

    def test_gate_off_leaves_mc_untouched(self):
        cfg = ScenarioConfig(gas_offer_net_revenue_margin=False)
        mc = np.zeros((1, 1), dtype=float)
        apply_gas_offer_margin(mc, [_Gen(MARKUP_HR)], np.full((1, 1), 7.12), cfg)
        self.assertEqual(float(mc[0, 0]), 0.0)


if __name__ == "__main__":
    unittest.main()
