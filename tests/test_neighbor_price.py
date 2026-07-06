"""Tests for the forecast-grade neighbor reference-price interface.

Covers the pure price construction (gas x heat-rate x load-shape), the
per-neighbor resolution with proxy fallback, the capacity-weighted aggregate,
and the spread-driven seam flow direction. The pure-arithmetic cases use a
synthetic load frame (monkeypatched loader) so they run with no data files;
an integration case validates the PJM registry against the real EIA-930
neighbor extracts when they are present.
"""

import os
import unittest

import numpy as np

import market_sim.data.neighbor_price as np_mod
from market_sim.config.constants import HENRY_HUB_TRAJECTORIES
from market_sim.config.interchange_config import INTERFACE_NEIGHBORS, NeighborInterface
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import _eia_hourly_frame_filled
from market_sim.data.neighbor_price import (
    InterfacePrices,
    interface_reference_prices,
    neighbor_gas_price,
    neighbor_heat_rate,
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

        self._frames = {ba: pd.DataFrame({"Demand": arr}) for ba, arr in loads.items()}

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


class TestNeighborHeatRate(unittest.TestCase):
    """Resolution order: measured backcast -> elastic forward -> flat fallback."""

    def test_backcast_year_uses_measured_anchor(self):
        # A tabulated backcast year resolves to its measured hr_by_year, never
        # the elastic forward path (which must leave the backcast untouched).
        # name="PJM" gives this spec the MISO PJM elastic fit (11.06, 3.21).
        spec = _spec(
            name="PJM",
            marginal_heat_rate=12.3,
            hr_by_year={2024: 13.49},
        )
        self.assertEqual(neighbor_heat_rate(spec, 2024), 13.49)

    def test_forecast_year_is_gas_elastic(self):
        # An untabulated (forecast) year uses hr_phys + hr_adder/gas from the
        # _HR_GAS_ELASTIC map (keyed by name), NOT the flat marginal_heat_rate.
        spec = _spec(name="PJM", marginal_heat_rate=12.3, hr_by_year={2024: 13.49})
        hr_phys, hr_adder = np_mod._HR_GAS_ELASTIC["PJM"]
        gas = neighbor_gas_price(spec, 2030, "mid")
        self.assertAlmostEqual(
            neighbor_heat_rate(spec, 2030, "mid"), hr_phys + hr_adder / gas
        )

    def test_elastic_hr_falls_as_gas_rises(self):
        # The defining forward behaviour: a dearer gas year carries a LOWER
        # implied HR (the fixed non-gas adder is diluted) — so a wind-set
        # neighbor (SPP) does not get spuriously lifted when gas spikes.
        spec = _spec(name="SPP", hr_by_year=None)
        cheap = neighbor_heat_rate(_at_gas(spec, 2.0), 2030, "mid")
        dear = neighbor_heat_rate(_at_gas(spec, 4.0), 2030, "mid")
        self.assertLess(dear, cheap)

    def test_flat_fallback_without_elasticity(self):
        # A neighbor with no elasticity fit (name not in _HR_GAS_ELASTIC, e.g. a
        # non-organized-market neighbor) keeps the flat marginal_heat_rate for
        # forecast years — byte-identical.
        spec = _spec(name="South", marginal_heat_rate=12.0, hr_by_year=None)
        self.assertEqual(neighbor_heat_rate(spec, 2030, "mid"), 12.0)


class TestForwardSkillNotAnEnvVar(unittest.TestCase):
    """The removed FORWARD_SKILL_ENV channel must stay dead (CLAUDE.md rule 23).

    ``forward_skill`` is a plain parameter threaded from
    ``ScenarioConfig.neighbor_hr_forward_skill``; the old
    ``MARKET_SIM_NEIGHBOR_HR_FORWARD_SKILL`` environment variable must have no
    effect at all, however it is set.
    """

    def test_env_var_does_not_affect_heat_rate(self):
        spec = _spec(name="PJM", marginal_heat_rate=12.3, hr_by_year={2024: 13.49})
        os.environ["MARKET_SIM_NEIGHBOR_HR_FORWARD_SKILL"] = "elastic"
        try:
            # Still the measured backcast anchor, not the elastic forward path
            # the (dead) env var would have selected.
            self.assertEqual(neighbor_heat_rate(spec, 2024), 13.49)
            hr_phys, hr_adder = np_mod._HR_GAS_ELASTIC["PJM"]
            gas = neighbor_gas_price(spec, 2030, "mid")
            # Forecast year: still the gas-elastic path (the parameter default),
            # not forced flat by the env var.
            self.assertAlmostEqual(
                neighbor_heat_rate(spec, 2030, "mid"), hr_phys + hr_adder / gas
            )
        finally:
            del os.environ["MARKET_SIM_NEIGHBOR_HR_FORWARD_SKILL"]

    def test_scenario_config_field_is_the_only_channel(self):
        # The explicit keyword argument (sourced from ScenarioConfig in the
        # dispatch path) is what actually changes behavior.
        spec = _spec(name="PJM", marginal_heat_rate=12.3, hr_by_year={2024: 13.49})
        self.assertEqual(neighbor_heat_rate(spec, 2024, forward_skill="flat"), 12.3)
        cfg = ScenarioConfig(neighbor_hr_forward_skill="flat")
        self.assertEqual(cfg.neighbor_hr_forward_skill, "flat")

    def test_scenario_config_rejects_invalid_value(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(neighbor_hr_forward_skill="bogus")


def _at_gas(spec: NeighborInterface, gas: float) -> NeighborInterface:
    """Return a copy of ``spec`` whose delivered gas equals ``gas`` via the basis."""
    import dataclasses

    basis = gas - HENRY_HUB_TRAJECTORIES["mid"][2030]
    return dataclasses.replace(spec, gas_basis=basis)


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
            shape, _ = neighbor_load_shape(_spec(load_shape_exponent=2.0), 2023, _HOURS)
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
        # PJM MISO limit 7300, NYISO 3900 -> weighted toward MISO's 20.
        w = (7300 * 20 + 3900 * 40) / (7300 + 3900)
        np.testing.assert_allclose(agg, w)

    def test_aggregate_none_when_empty(self):
        self.assertIsNone(InterfacePrices(iso="PJM", year=2023, hours=2).aggregate())

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


class TestReferencePriceNode(unittest.TestCase):
    """The LP seam builder + the hourly mc injector."""

    def test_node_has_import_and_export_tranches_per_neighbor(self):
        from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
        from market_sim.model.transmission import build_reference_price_node

        gens = build_reference_price_node("PJM")
        n_neighbors = len(INTERFACE_NEIGHBORS["PJM"])
        # n tranches x 2 directions per neighbor.
        self.assertEqual(len(gens), 2 * SEAM_FLOW_TRANCHES * n_neighbors)
        imports = [g for g in gens if g.pmax_mw > 0]
        exports = [g for g in gens if g.pmax_mw == 0 and g.pmin_mw < 0]
        self.assertEqual(len(imports), SEAM_FLOW_TRANCHES * n_neighbors)
        self.assertEqual(len(exports), SEAM_FLOW_TRANCHES * n_neighbors)
        # The MISO import tranches each carry limit/n and sum to the limit.
        miso = next(n for n in INTERFACE_NEIGHBORS["PJM"] if n.name == "MISO")
        miso_imp = [g for g in imports if "_refimp_MISO#" in g.unit_id]
        self.assertEqual(len(miso_imp), SEAM_FLOW_TRANCHES)
        for g in miso_imp:
            self.assertAlmostEqual(
                g.pmax_mw, miso.interface_limit_mw / SEAM_FLOW_TRANCHES
            )
        self.assertAlmostEqual(
            sum(g.pmax_mw for g in miso_imp), miso.interface_limit_mw
        )

    def test_unregistered_iso_node_is_empty(self):
        from market_sim.model.transmission import build_reference_price_node

        self.assertEqual(build_reference_price_node("ERCOT"), [])

    def test_inject_sets_flow_responsive_tranche_prices(self):
        from types import SimpleNamespace

        from market_sim.data.neighbor_price import seam_tranche_prices
        from market_sim.model.transmission import (
            build_reference_price_node,
            inject_reference_price_mc,
        )

        gens = build_reference_price_node("PJM")
        # A fleet with one ordinary unit ahead of the seam pseudo-gens.
        unit_ids = ["gas_cc_PJM_x"] + [g.unit_id for g in gens]
        fa = SimpleNamespace(unit_ids=unit_ids)
        mc = np.full((len(unit_ids), 8760), 99.0)  # sentinel
        applied = inject_reference_price_mc(fa, mc, "PJM", 2023)
        if not applied:
            self.skipTest("EIA-930 neighbor extracts not present")
        # The ordinary unit's row is untouched.
        np.testing.assert_array_equal(mc[0], 99.0)
        cache: dict[str, object] = {}
        for r, uid in enumerate(unit_ids):
            for mark, is_export in (("_refimp_", False), ("_refexp_", True)):
                if mark not in uid:
                    continue
                tag = uid.rsplit(mark, 1)[1]
                name, _, k_str = tag.partition("#")
                k = int(k_str) - 1
                spec = next(n for n in INTERFACE_NEIGHBORS["PJM"] if n.name == name)
                if name not in cache:
                    cache[name] = seam_tranche_prices(spec, 2023, 8760)
                export_p, import_p, _ = cache[name]
                band = export_p[k] if is_export else import_p[k]
                expect = band - spec.hurdle if is_export else band + spec.hurdle
                np.testing.assert_allclose(mc[r], expect)
        # Export tranches must be monotone non-increasing in flow (the seam
        # slopes down: deeper export bands pay less), and the deepest export
        # band is strictly below the first — the self-limiting slope.
        miso_exp = sorted(
            (int(uid.rsplit("#", 1)[1]), r)
            for r, uid in enumerate(unit_ids)
            if "_refexp_MISO#" in uid
        )
        first = mc[miso_exp[0][1]]
        last = mc[miso_exp[-1][1]]
        self.assertTrue(np.all(last <= first + 1e-9))
        self.assertLess(float(last.mean()), float(first.mean()))

    def test_inject_noop_without_node(self):
        from types import SimpleNamespace

        from market_sim.model.transmission import inject_reference_price_mc

        fa = SimpleNamespace(unit_ids=["gas_cc_PJM_x", "coal_PJM_y"])
        mc = np.full((2, 8760), 50.0)
        self.assertFalse(inject_reference_price_mc(fa, mc, "PJM", 2023))
        np.testing.assert_array_equal(mc, 50.0)  # byte-identical

    def test_miso_node_prices_its_three_seams(self):
        """MISO's import node prices PJM, SPP and SERC/South individually.

        Each neighbor resolves an EIA-930 load shape (PJM/SWPP/SOCO extracts),
        and the constructed reference prices land near each neighbor's anchored
        gas x heat-rate level (forecast-native, not tuned to MISO's flow).
        """
        from market_sim.data.neighbor_price import (
            SEAM_FLOW_TRANCHES,
            interface_reference_prices,
        )
        from market_sim.model.transmission import build_reference_price_node

        gens = build_reference_price_node("MISO")
        n_neighbors = len(INTERFACE_NEIGHBORS["MISO"])
        self.assertEqual(len(gens), 2 * SEAM_FLOW_TRANCHES * n_neighbors)
        self.assertEqual({g.zone for g in gens}, {"MISO_external"})

        prices = interface_reference_prices("MISO", 2023, 8760)
        if not prices.per_neighbor:
            self.skipTest("EIA-930 neighbor extracts not present")
        # All three seams price individually (no fold into the aggregate).
        self.assertEqual(set(prices.per_neighbor), {"PJM", "SPP", "South"})
        self.assertEqual(prices.missing, [])
        # 2023 Henry Hub $2.54/MMBtu x each neighbor's RESOLVED heat rate gives
        # the annual-mean level (mean-preserving exponent 1.0). 2023 is a
        # backcast year, so PJM/SPP resolve to their measured hr_by_year anchor
        # (11.2 / 9.24), not the flat marginal_heat_rate; South keeps the flat
        # estimate (no organized-market LMP).
        hh_2023 = 2.54
        for spec in INTERFACE_NEIGHBORS["MISO"]:
            expect = hh_2023 * neighbor_heat_rate(spec, 2023)
            got = float(prices.per_neighbor[spec.name].mean())
            self.assertAlmostEqual(got, expect, delta=0.5 * expect * 0.05 + 0.5)
        # Merit order on the measured 2023 anchors: SPP (wind-rich, HR 9.24) is
        # the cheapest seam, PJM (HR 11.2) above it, and SERC/South (flat HR
        # 12.0) the dearest — the order MISO clears the seam against.
        self.assertLess(
            prices.per_neighbor["SPP"].mean(),
            prices.per_neighbor["PJM"].mean(),
        )
        self.assertLess(
            prices.per_neighbor["PJM"].mean(),
            prices.per_neighbor["South"].mean(),
        )


if __name__ == "__main__":
    unittest.main()
