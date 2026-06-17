"""Tests for the forecast-grade neighbor reference-price interface.

Covers the pure price construction (gas x heat-rate x load-shape), the
per-neighbor resolution with proxy fallback, the capacity-weighted aggregate,
and the spread-driven seam flow direction. The pure-arithmetic cases use a
synthetic load frame (monkeypatched loader) so they run with no data files;
an integration case validates the PJM registry against the real EIA-930
neighbor extracts when they are present.
"""
import unittest

import numpy as np

import market_sim.data.neighbor_price as np_mod
from market_sim.config.constants import HENRY_HUB_TRAJECTORIES, NeighborInterface
from market_sim.data.eia_loader import _eia_hourly_frame_filled
from market_sim.data.neighbor_price import (
    InterfacePrices,
    interface_reference_prices,
    neighbor_gas_price,
    neighbor_load_shape,
    neighbor_reference_price,
    seam_flow_direction,
)

_HOURS = 24


def _spec(**kw) -> NeighborInterface:
    """A minimal neighbor spec with sane defaults for unit tests."""
    base = dict(
        name="TEST",
        ba_code="TEST_BA",
        gas_basis=0.0,
        marginal_heat_rate=7.5,
        hurdle=3.0,
        interface_limit_mw=1000.0,
        border_zones=("Z",),
    )
    base.update(kw)
    return NeighborInterface(**base)


class _FakeFrames:
    """Monkeypatch for ``_eia_hourly_frame_filled`` returning canned loads.

    Maps a BA code to a flat load array; an unknown BA returns ``None`` so the
    proxy/aggregate fallbacks can be exercised without data files.
    """

    def __init__(self, loads: dict[str, np.ndarray]):
        import pandas as pd

        self._frames = {
            ba: pd.DataFrame({"Demand": arr}) for ba, arr in loads.items()
        }

    def __call__(self, ba_code: str, year: int):
        return self._frames.get(ba_code)


class TestNeighborGasPrice(unittest.TestCase):
    """gas = Henry Hub + basis."""

    def test_basis_adds_to_henry_hub(self):
        spec = _spec(gas_basis=0.55)
        expected = HENRY_HUB_TRAJECTORIES["mid"][2023] + 0.55
        self.assertAlmostEqual(neighbor_gas_price(spec, 2023, "mid"), expected)

    def test_zero_basis_is_henry_hub(self):
        spec = _spec(gas_basis=0.0)
        self.assertAlmostEqual(
            neighbor_gas_price(spec, 2024, "mid"),
            HENRY_HUB_TRAJECTORIES["mid"][2024],
        )

    def test_backcast_year_scenario_invariant(self):
        spec = _spec()
        self.assertEqual(
            neighbor_gas_price(spec, 2023, "low"),
            neighbor_gas_price(spec, 2023, "high"),
        )


class TestLoadShape(unittest.TestCase):
    """Normalized load shape and the proxy fallback."""

    def test_linear_shape_is_mean_preserving(self):
        load = np.array([50.0, 100.0, 150.0] * 8, dtype=float)  # mean 100
        self.assertEqual(len(load), _HOURS)
        np_mod._eia_hourly_frame_filled = _FakeFrames({"TEST_BA": load})
        try:
            shape, ba = neighbor_load_shape(_spec(), 2023, _HOURS)
        finally:
            np_mod._eia_hourly_frame_filled = _eia_hourly_frame_filled
        self.assertEqual(ba, "TEST_BA")
        self.assertAlmostEqual(float(shape.mean()), 1.0)
        # Proportional to load: the 150 hour is 1.5x the mean.
        self.assertAlmostEqual(shape[2], 1.5)

    def test_falls_back_to_proxy(self):
        load = np.full(_HOURS, 80.0)
        np_mod._eia_hourly_frame_filled = _FakeFrames({"PROXY_BA": load})
        try:
            shape, ba = neighbor_load_shape(
                _spec(ba_code="MISSING", proxy_ba="PROXY_BA"), 2023, _HOURS
            )
        finally:
            np_mod._eia_hourly_frame_filled = _eia_hourly_frame_filled
        self.assertEqual(ba, "PROXY_BA")
        np.testing.assert_allclose(shape, 1.0)  # flat load -> flat shape

    def test_none_when_no_extract(self):
        np_mod._eia_hourly_frame_filled = _FakeFrames({})
        try:
            self.assertIsNone(neighbor_load_shape(_spec(), 2023, _HOURS))
        finally:
            np_mod._eia_hourly_frame_filled = _eia_hourly_frame_filled

    def test_exponent_adds_peak_premium(self):
        load = np.array([50.0, 100.0, 150.0] * 8, dtype=float)
        np_mod._eia_hourly_frame_filled = _FakeFrames({"TEST_BA": load})
        try:
            shape, _ = neighbor_load_shape(
                _spec(load_shape_exponent=2.0), 2023, _HOURS
            )
        finally:
            np_mod._eia_hourly_frame_filled = _eia_hourly_frame_filled
        # Convex shape lifts the mean above 1 and the peak above linear.
        self.assertGreater(float(shape.mean()), 1.0)
        self.assertAlmostEqual(shape[2], 1.5**2)


class TestReferencePrice(unittest.TestCase):
    """price = gas x heat-rate x shape."""

    def test_flat_load_gives_baseload_price(self):
        load = np.full(_HOURS, 100.0)
        np_mod._eia_hourly_frame_filled = _FakeFrames({"TEST_BA": load})
        try:
            price, ba = neighbor_reference_price(
                _spec(gas_basis=0.0, marginal_heat_rate=7.5), 2023, _HOURS
            )
        finally:
            np_mod._eia_hourly_frame_filled = _eia_hourly_frame_filled
        expected = HENRY_HUB_TRAJECTORIES["mid"][2023] * 7.5
        np.testing.assert_allclose(price, expected)
        self.assertEqual(ba, "TEST_BA")

    def test_none_without_load(self):
        np_mod._eia_hourly_frame_filled = _FakeFrames({})
        try:
            self.assertIsNone(neighbor_reference_price(_spec(), 2023, _HOURS))
        finally:
            np_mod._eia_hourly_frame_filled = _eia_hourly_frame_filled


class TestInterfacePricesAndAggregate(unittest.TestCase):
    """Per-neighbor resolution, missing tracking, and the weighted blend."""

    def test_aggregate_is_capacity_weighted(self):
        prices = InterfacePrices(iso="PJM", year=2023, hours=2)
        # Stub two neighbors that exist in the PJM registry.
        prices.per_neighbor = {
            "MISO": np.array([20.0, 20.0]),
            "NYISO": np.array([40.0, 40.0]),
        }
        agg = prices.aggregate()
        # PJM MISO limit 10000, NYISO 3000 -> weighted toward MISO's 20.
        w = (10000 * 20 + 3000 * 40) / 13000
        np.testing.assert_allclose(agg, w)

    def test_aggregate_none_when_empty(self):
        self.assertIsNone(
            InterfacePrices(iso="PJM", year=2023, hours=2).aggregate()
        )

    def test_unregistered_iso_is_empty(self):
        res = interface_reference_prices("NONEXISTENT", 2023, _HOURS)
        self.assertEqual(res.per_neighbor, {})
        self.assertEqual(res.missing, [])


class TestSeamFlowDirection(unittest.TestCase):
    """Hurdle dead-band: import high, export low, hold inside the band."""

    def test_import_export_hold(self):
        iso = np.array([100.0, 10.0, 50.0])
        neigh = np.array([50.0, 60.0, 50.0])
        direction = seam_flow_direction(iso, neigh, hurdle=3.0)
        # ISO dearer -> import (+1); ISO cheaper -> export (-1); equal -> hold.
        np.testing.assert_array_equal(direction, [1.0, -1.0, 0.0])

    def test_dead_band_holds(self):
        iso = np.array([52.0, 48.0])
        neigh = np.array([50.0, 50.0])
        # Both within +/-3 of neighbor -> hold.
        np.testing.assert_array_equal(
            seam_flow_direction(iso, neigh, hurdle=3.0), [0.0, 0.0]
        )


class TestPJMIntegration(unittest.TestCase):
    """Validate the real PJM registry against EIA-930 extracts when present."""

    def test_pjm_2023_resolves_neighbors(self):
        res = interface_reference_prices("PJM", 2023, 8760)
        if not res.per_neighbor and res.missing == ["MISO", "NYISO", "Carolinas"]:
            self.skipTest("EIA-930 neighbor extracts not present")
        # MISO and NYISO have direct extracts; Carolinas uses the SOCO proxy.
        self.assertIn("MISO", res.per_neighbor)
        self.assertIn("NYISO", res.per_neighbor)
        if "Carolinas" in res.per_neighbor:
            self.assertEqual(res.ba_used["Carolinas"], "SOCO")
        for price in res.per_neighbor.values():
            self.assertEqual(price.shape, (8760,))
            self.assertTrue(np.all(price > 0.0))


if __name__ == "__main__":
    unittest.main()
