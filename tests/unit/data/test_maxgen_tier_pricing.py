"""Tests for declared-window ELMP emergency-tier pricing (the F5 lane).

Covers the frozen design (``docs/handoffs/miso-f5-scarcity-depth-design-
2026-07.md`` §5.7): the level→tier-floor keying, the declared-region zone
scoping, the min(voll, floor) never-raise rule, the overlap minimum, the
no-Warning+-window ``None`` (byte-identical LP), the EST no-leap model-clock
placement, the ``build_cost_vector``/``DispatchModel`` ``slack_cost`` seam's
off-state byte identity, and — trivial case first (CLAUDE.md testing
pattern) — a 1-gen/1-zone/24-hour LP whose shortage hours price at the tier
floor inside a declared window and at VOLL outside it.
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from market_sim.config.reserve_config import (
    MISO_EMERGENCY_TIER1_OFFER_FLOOR,
    MISO_EMERGENCY_TIER2_OFFER_FLOOR,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.maxgen_events import (
    TIER_FLOOR_BY_LEVEL,
    tier_slack_cost_from_registry,
)
from market_sim.model.dispatch import (
    VariableLayout,
    build_cost_vector,
    solve_dispatch,
)

MISO_ZONES = [
    "MISO-West",
    "MISO-Plains",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-East",
    "MISO-South",
]
VOLL = 2000.0  # MISO ISOConfig.voll (FERC Order 831 bid cap)


def _registry(rows):
    """Build a synthetic model-clock registry frame (start/end naive EST)."""
    return pd.DataFrame(
        [
            {
                "level": level,
                "region": region,
                "start_model": pd.Timestamp(start),
                "end_model_excl": pd.Timestamp(end),
            }
            for level, region, start, end in rows
        ]
    )


class TierSlackCostCoreTest(unittest.TestCase):
    """The pure registry→array core (level/region/window/min semantics)."""

    def test_warning_prices_tier1_inside_window_only(self):
        ev = _registry(
            [("maxgen_warning", "footprint", "2024-08-26 13:00", "2024-08-26 20:00")]
        )
        cost = tier_slack_cost_from_registry(ev, "MISO", 2024, MISO_ZONES, VOLL, 8760)
        self.assertIsNotNone(cost)
        self.assertEqual(cost.shape, (6, 8760))
        # No-leap model clock: Aug-26 on the 365-day calendar is day-of-year
        # 238 -> hours 5701..5707 carry the window (13:00-20:00 half-open).
        lo = 237 * 24 + 13
        np.testing.assert_allclose(
            cost[:, lo : lo + 7], MISO_EMERGENCY_TIER1_OFFER_FLOOR
        )
        # Everything else stays at voll (off-window byte identity).
        mask = np.ones(8760, dtype=bool)
        mask[lo : lo + 7] = False
        self.assertTrue((cost[:, mask] == VOLL).all())

    def test_step1_is_tier1_and_step2_is_tier2(self):
        self.assertEqual(
            TIER_FLOOR_BY_LEVEL["maxgen_event_step1"], MISO_EMERGENCY_TIER1_OFFER_FLOOR
        )
        ev = _registry(
            [
                (
                    "maxgen_event_step2",
                    "footprint",
                    "2023-08-24 12:00",
                    "2023-08-25 00:00",
                )
            ]
        )
        cost = tier_slack_cost_from_registry(ev, "MISO", 2023, MISO_ZONES, VOLL, 8760)
        lo = 235 * 24 + 12  # Aug-24 = day-of-year 236, hours 12..23
        np.testing.assert_allclose(
            cost[:, lo : lo + 12], MISO_EMERGENCY_TIER2_OFFER_FLOOR
        )

    def test_advisory_and_alert_have_no_pricing_effect(self):
        ev = _registry(
            [
                (
                    "capacity_advisory",
                    "footprint",
                    "2025-07-24 00:00",
                    "2025-07-25 00:00",
                ),
                ("maxgen_alert", "footprint", "2025-07-28 14:00", "2025-07-28 22:00"),
            ]
        )
        self.assertIsNone(
            tier_slack_cost_from_registry(ev, "MISO", 2025, MISO_ZONES, VOLL, 8760)
        )

    def test_external_seam_buses_are_never_repriced(self):
        # The LP zone list carries the external seam buses; load slack there
        # is phantom import supply through the border links, so the tier
        # floor must never touch them (footprint or midwest alike) — else
        # the mechanism fabricates unmeasured emergency imports around the
        # measured seam ladders.
        zones = MISO_ZONES + ["MISO_external", "MISO_external_South"]
        ev = _registry(
            [
                ("maxgen_warning", "footprint", "2024-08-26 13:00", "2024-08-26 20:00"),
            ]
        )
        cost = tier_slack_cost_from_registry(ev, "MISO", 2024, zones, VOLL, 8760)
        self.assertTrue((cost[6:] == VOLL).all())  # externals untouched
        lo = 237 * 24 + 13
        np.testing.assert_allclose(
            cost[:6, lo : lo + 7], MISO_EMERGENCY_TIER1_OFFER_FLOOR
        )

    def test_midwest_region_excludes_south(self):
        ev = _registry(
            [("maxgen_warning", "midwest", "2025-06-24 00:00", "2025-06-25 00:00")]
        )
        cost = tier_slack_cost_from_registry(ev, "MISO", 2025, MISO_ZONES, VOLL, 8760)
        lo = 174 * 24  # Jun-24 = day-of-year 175
        south = MISO_ZONES.index("MISO-South")
        for z in range(len(MISO_ZONES)):
            expected = VOLL if z == south else MISO_EMERGENCY_TIER1_OFFER_FLOOR
            np.testing.assert_allclose(cost[z, lo : lo + 24], expected)

    def test_min_never_raises_a_low_voll(self):
        ev = _registry(
            [("maxgen_warning", "footprint", "2024-08-26 13:00", "2024-08-26 20:00")]
        )
        cost = tier_slack_cost_from_registry(ev, "MISO", 2024, MISO_ZONES, 300.0, 8760)
        self.assertTrue((cost == 300.0).all())  # floor 500 > voll 300 -> voll kept

    def test_overlapping_rows_take_the_minimum_floor(self):
        ev = _registry(
            [
                (
                    "maxgen_event_step2",
                    "footprint",
                    "2023-08-24 12:00",
                    "2023-08-25 00:00",
                ),
                ("maxgen_warning", "footprint", "2023-08-24 15:00", "2023-08-24 17:00"),
            ]
        )
        cost = tier_slack_cost_from_registry(ev, "MISO", 2023, MISO_ZONES, VOLL, 8760)
        lo = 235 * 24
        np.testing.assert_allclose(
            cost[:, lo + 15 : lo + 17], MISO_EMERGENCY_TIER1_OFFER_FLOOR
        )
        np.testing.assert_allclose(
            cost[:, lo + 12 : lo + 15], MISO_EMERGENCY_TIER2_OFFER_FLOOR
        )

    def test_no_window_overlapping_the_year_returns_none(self):
        ev = _registry(
            [("maxgen_warning", "footprint", "2024-08-26 13:00", "2024-08-26 20:00")]
        )
        self.assertIsNone(
            tier_slack_cost_from_registry(ev, "MISO", 2025, MISO_ZONES, VOLL, 8760)
        )

    def test_unknown_level_fails_loud(self):
        ev = _registry(
            [
                (
                    "maxgen_event_step9",
                    "footprint",
                    "2024-08-26 13:00",
                    "2024-08-26 20:00",
                )
            ]
        )
        with self.assertRaises(ValueError):
            tier_slack_cost_from_registry(ev, "MISO", 2024, MISO_ZONES, VOLL, 8760)


class SlackCostSeamTest(unittest.TestCase):
    """build_cost_vector / DispatchModel slack_cost pass-through."""

    def test_none_is_byte_identical(self):
        layout = VariableLayout(n_gen=1, n_zones=2, n_storage=0, n_links=0, T=4)
        mc = np.full((1, 4), 25.0)
        base = build_cost_vector(layout, mc, voll=VOLL)
        again = build_cost_vector(layout, mc, voll=VOLL, slack_cost=None)
        np.testing.assert_array_equal(base, again)

    def test_per_zone_hour_override_lands_in_the_slack_block(self):
        layout = VariableLayout(n_gen=1, n_zones=2, n_storage=0, n_links=0, T=4)
        mc = np.full((1, 4), 25.0)
        sc = np.full((2, 4), VOLL)
        sc[1, 2] = 500.0  # zone 1, hour 2
        cost = build_cost_vector(layout, mc, voll=VOLL, slack_cost=sc)
        for t in range(4):  # t: hour index
            for z in range(2):  # z: zone index
                expected = 500.0 if (z, t) == (1, 2) else VOLL
                self.assertEqual(cost[layout.slack_col(z, t)], expected)

    def test_shape_mismatch_fails_loud(self):
        fleet = generators_to_fleet_arrays(
            [
                Generator(
                    unit_id="G0",
                    name="G0",
                    zone="Z0",
                    fuel_type="gas_ct",
                    pmax_mw=50.0,
                    pmin_mw=0.0,
                    heat_rate=10.0,
                    eford=0.0,
                )
            ],
            ["Z0"],
            hours=24,
        )
        with self.assertRaises(ValueError):
            solve_dispatch(
                fleet,
                np.full((1, 24), 40.0),
                mc=np.full((1, 24), 50.0),
                wind_cf=np.zeros((1, 24)),
                wind_cap=np.zeros(1),
                solar_cf=np.zeros((1, 24)),
                solar_cap=np.zeros(1),
                slack_cost=np.full((24, 1), VOLL),  # transposed on purpose
                T=24,
            )


class TierPricedShortageLPTest(unittest.TestCase):
    """Trivial 1-gen / 1-zone / 24-h LP (CLAUDE.md testing pattern)."""

    def _solve(self, slack_cost=None):
        fleet = generators_to_fleet_arrays(
            [
                Generator(
                    unit_id="G0",
                    name="G0",
                    zone="Z0",
                    fuel_type="gas_ct",
                    pmax_mw=100.0,
                    pmin_mw=0.0,
                    heat_rate=10.0,
                    eford=0.0,
                )
            ],
            ["Z0"],
            hours=24,
        )
        demand = np.full((1, 24), 80.0)
        demand[0, 10:14] = 200.0  # shortage hours 10..13
        return solve_dispatch(
            fleet,
            demand,
            mc=np.full((1, 24), 50.0),
            voll=VOLL,
            slack_cost=slack_cost,
            wind_cf=np.zeros((1, 24)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, 24)),
            solar_cap=np.zeros(1),
            T=24,
        )

    def test_shortage_prices_tier_floor_inside_window_voll_outside(self):
        # Declared window = hours 10..11 only; hours 12..13 shortage outside.
        sc = np.full((1, 24), VOLL)
        sc[0, 10:12] = MISO_EMERGENCY_TIER1_OFFER_FLOOR
        result = self._solve(slack_cost=sc)
        np.testing.assert_allclose(
            result.prices[0, 10:12], MISO_EMERGENCY_TIER1_OFFER_FLOOR
        )
        np.testing.assert_allclose(result.prices[0, 12:14], VOLL)
        np.testing.assert_allclose(result.prices[0, :10], 50.0)

    def test_override_at_voll_everywhere_matches_flat_voll(self):
        flat = self._solve()
        arr = self._solve(slack_cost=np.full((1, 24), VOLL))
        np.testing.assert_allclose(arr.prices, flat.prices)
        np.testing.assert_allclose(arr.dispatch, flat.dispatch)

    def test_tier_floor_never_binds_without_shortage(self):
        # Window over non-shortage hours: $500 slack is dominated (price 50).
        sc = np.full((1, 24), VOLL)
        sc[0, 2:6] = MISO_EMERGENCY_TIER1_OFFER_FLOOR
        result = self._solve(slack_cost=sc)
        np.testing.assert_allclose(result.prices[0, 2:6], 50.0)


if __name__ == "__main__":
    unittest.main()
