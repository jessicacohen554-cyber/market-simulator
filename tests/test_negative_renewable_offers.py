"""Tests for the negative curtailable-renewable offer floor.

The ``negative_renewable_offers`` flag floors the curtailable wind/solar
dispatch offer at the negative keep-running (REC/PTC) value
(``renewable_keep_running_value``), so in oversupply the marginal — curtailed —
renewable clears the energy balance at a sub-$0 price, reproducing CAISO's
negative midday LMPs. These tests cover the offer-floor helper (off = identity,
on = the more-negative of the offer and the floor) and prove end-to-end in a
forced-long harness that the LMP goes negative for solar, which has no PTC and
floors at $0 today.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.policy.eac import apply_negative_renewable_offer_floor


def _make_fleet(zones_of_gens, zone_names, hours, pmax=100.0, pmin=0.0, eford=0.0):
    """Build ``FleetArrays`` with one gas_cc generator per zone entry."""
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=pmin,
            eford=eford,
        )
        for i, z in enumerate(zones_of_gens)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=hours)


class TestNegativeRenewableOfferFloor(unittest.TestCase):
    """Unit tests for ``apply_negative_renewable_offer_floor``."""

    def test_off_is_identity(self):
        """Flag off leaves wind/solar offers untouched (byte-identical)."""
        config = ScenarioConfig(negative_renewable_offers=False)
        wind_mc, solar_mc = apply_negative_renewable_offer_floor(
            -26.0, 0.0, config
        )
        self.assertEqual(wind_mc, -26.0)
        self.assertEqual(solar_mc, 0.0)

    def test_on_floors_solar_to_negative_rec_value(self):
        """Flag on drives the $0 solar offer to -keep_running_value."""
        config = ScenarioConfig(
            negative_renewable_offers=True, renewable_keep_running_value=20.0
        )
        _, solar_mc = apply_negative_renewable_offer_floor(-26.0, 0.0, config)
        self.assertEqual(solar_mc, -20.0)

    def test_on_does_not_double_count_wind_ptc(self):
        """Wind already below the floor (its PTC) is left more-negative."""
        config = ScenarioConfig(
            negative_renewable_offers=True, renewable_keep_running_value=20.0
        )
        # Wind PTC -26 is below the -20 floor -> stays -26 (no -46 stacking).
        wind_mc, _ = apply_negative_renewable_offer_floor(-26.0, 0.0, config)
        self.assertEqual(wind_mc, -26.0)

    def test_on_floors_wind_when_ptc_expired(self):
        """With the PTC expired (wind offer $0) the REC floor carries wind."""
        config = ScenarioConfig(
            negative_renewable_offers=True, renewable_keep_running_value=20.0
        )
        wind_mc, _ = apply_negative_renewable_offer_floor(0.0, 0.0, config)
        self.assertEqual(wind_mc, -20.0)

    def test_array_offers_floored_elementwise(self):
        """Per-zone/(n_zones, T) offers are floored element-wise."""
        config = ScenarioConfig(
            negative_renewable_offers=True, renewable_keep_running_value=20.0
        )
        solar_mc = np.array([0.0, -30.0, -5.0])
        _, floored = apply_negative_renewable_offer_floor(
            np.zeros(3), solar_mc, config
        )
        np.testing.assert_array_equal(floored, np.array([-20.0, -30.0, -20.0]))


class TestNegativeRenewablePriceFormation(unittest.TestCase):
    """Forced-long solves proving the floor drives the LMP negative."""

    T = 24

    def _solar_only_long_hour(self, solar_mc):
        """Solve a 1-zone hour with solar capacity far exceeding demand.

        One thermal unit at $50 and 200 MW of solar serve 80 MW of demand, so
        solar is on the margin (being curtailed). The marginal price is the
        solar offer ``solar_mc``. Returns the per-zone price array.
        """
        fleet = _make_fleet(["Z0"], ["Z0"], hours=self.T, pmax=200.0)
        mc = np.full((1, self.T), 50.0)
        demand = np.full((1, self.T), 80.0)
        result = solve_dispatch(
            fleet, demand, mc=mc, T=self.T,
            wind_cf=np.zeros((1, self.T)),
            wind_cap=np.zeros(1),
            solar_cf=np.full((1, self.T), 1.0),
            solar_cap=np.array([200.0]),  # 200 MW available, only 80 needed
            solar_mc=solar_mc,
        )
        return result

    def test_solar_floors_at_zero_without_flag(self):
        """Baseline: must-take solar at $0 floors the price at $0, not below."""
        result = self._solar_only_long_hour(solar_mc=0.0)
        np.testing.assert_allclose(result.prices, 0.0, atol=0.1)

    def test_negative_offer_drives_price_below_zero(self):
        """A -$20 curtailable solar offer clears the long hour at -$20."""
        config = ScenarioConfig(
            negative_renewable_offers=True, renewable_keep_running_value=20.0
        )
        _, solar_mc = apply_negative_renewable_offer_floor(0.0, 0.0, config)
        result = self._solar_only_long_hour(solar_mc=solar_mc)
        # Solar is marginal (curtailed) and bids -20, so LMP = -20.
        np.testing.assert_allclose(result.prices, -20.0, atol=0.1)
        # Thermal is off; solar serves the full 80 MW (the rest is curtailed,
        # i.e. left undispatched within its 200 MW availability).
        np.testing.assert_allclose(result.dispatch, 0.0, atol=0.1)
        np.testing.assert_allclose(result.solar_dispatched[0], 80.0, atol=0.1)

    def test_negative_price_only_below_the_zero_export_sink(self):
        """The $0 export sink still floors surplus at $0; this pushes below it.

        A $0 export sink (a negative-pmin pseudo-generator, exactly how
        ``transmission.build_export_sinks`` models curtailment/export) absorbs
        surplus at $0. While the sink has headroom it is marginal and the price
        is $0; once it saturates, the marginal resource is curtailed solar at
        -$20 and the price drops below the sink floor.
        """
        # One $0 export sink in zone Z0: pmax 0, can absorb down to -sink_cap.
        def _solve(sink_cap):
            sink = Generator(
                unit_id="SINK", name="SINK", zone="Z0", fuel_type="import",
                pmax_mw=0.0, pmin_mw=-sink_cap, eford=0.0,
            )
            fleet = generators_to_fleet_arrays([sink], ["Z0"], hours=self.T)
            mc = np.zeros((1, self.T))  # sink offers at $0
            demand = np.full((1, self.T), 80.0)
            return solve_dispatch(
                fleet, demand, mc=mc, T=self.T,
                wind_cf=np.zeros((1, self.T)), wind_cap=np.zeros(1),
                solar_cf=np.full((1, self.T), 1.0),
                solar_cap=np.array([200.0]),  # 120 MW surplus over the 80 load
                solar_mc=-20.0,
            )

        # Sink can absorb the full 120 MW surplus -> sink is marginal -> $0.
        deep = _solve(sink_cap=300.0)
        np.testing.assert_allclose(deep.prices, 0.0, atol=0.1)
        # Sink saturates below the surplus -> curtailed solar is marginal -> -$20.
        shallow = _solve(sink_cap=50.0)
        np.testing.assert_allclose(shallow.prices, -20.0, atol=0.1)

    def test_curtailment_not_dump_when_offer_negative(self):
        """Surplus is curtailed (solar left undispatched), not paid-to-dump.

        The dump cost in ``build_cost_vector`` exceeds the magnitude of the
        negative solar offer, so the LP backs solar down rather than generating
        it and dumping — no production credit is paid on undelivered energy.
        """
        result = self._solar_only_long_hour(solar_mc=-20.0)
        # Solar dispatched only to meet load; the surplus 120 MW is curtailed
        # (not generated-then-dumped).
        np.testing.assert_allclose(result.solar_dispatched[0], 80.0, atol=0.1)
        self.assertTrue(np.all(result.dump[0] < 1.0))


if __name__ == "__main__":
    unittest.main()
