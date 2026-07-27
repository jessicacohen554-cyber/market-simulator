"""Tests for the CAISO measured WECC corridor deliverability limit.

Each per-hub import corridor (COI/Path-66 → NP15, Path-46/WOR → SP15) has its
import-direction link flow capped at the per-(month × hour-of-day) p95 measured
net import (an ATC proxy that tightens midday). Implemented as a one-sided
per-hour interface-limit row, so the LP clears its merit order below the ceiling
and the export direction keeps the physical TTC.
"""

import unittest

import numpy as np

from market_sim.config.iso_configs import TransferLink
from market_sim.data.eia_loader import measured_corridor_flow_envelope
from market_sim.data.fleet import (
    Generator,
    generators_to_fleet_arrays,
)
from market_sim.model.dispatch import (
    VariableLayout,
    _build_interface_rows,
    solve_dispatch,
)
from market_sim.model.transmission import (
    build_caiso_corridor_flow_groups,
    build_incidence_matrix,
)

T = 24


class TestInterfaceRowsHourlyCap(unittest.TestCase):
    """``_build_interface_rows`` accepts a scalar OR a per-hour ``(T,)`` cap."""

    def _layout(self, n_links=1):
        # One zone, n_links flow columns, no gen/storage — enough for the row
        # builder, which only reads the flow offset and the column count.
        return VariableLayout(T=T, n_gen=0, n_zones=1, n_storage=0, n_links=n_links)

    def test_scalar_cap_broadcasts_byte_identical(self):
        layout = self._layout()
        _, lower, upper = _build_interface_rows(layout, [(np.array([0]), 500.0, True)])
        self.assertEqual(upper.shape, (T,))
        self.assertTrue(np.all(upper == 500.0))
        self.assertTrue(np.all(lower == -500.0))  # bidirectional floor

    def test_array_cap_is_per_hour(self):
        layout = self._layout()
        cap = np.arange(T, dtype=float) * 100.0  # distinct per hour
        _, lower, upper = _build_interface_rows(layout, [(np.array([0]), cap, False)])
        # Hour-major ordering: row t carries hour t's cap.
        np.testing.assert_allclose(upper, cap)
        # One-sided (bidirectional=False) leaves the lower bound open.
        self.assertTrue(np.all(np.isneginf(lower)))

    def test_two_groups_interleaved_hour_major(self):
        layout = self._layout(n_links=2)
        capA = np.full(T, 200.0)
        capB = np.arange(T, dtype=float)
        _, _, upper = _build_interface_rows(
            layout, [(np.array([0]), capA, False), (np.array([1]), capB, False)]
        )
        # Rows are hour-major, group-minor: [h0:gA,gB, h1:gA,gB, ...].
        self.assertEqual(upper.shape, (2 * T,))
        np.testing.assert_allclose(upper[0::2], capA)
        np.testing.assert_allclose(upper[1::2], capB)


class TestBuildCorridorFlowGroups(unittest.TestCase):
    """The builder maps each corridor to its import link as a one-sided group."""

    def _links(self):
        return [
            TransferLink(from_zone="WECC_PNW", to_zone="NP15", ttc_mw=4800.0),
            TransferLink(from_zone="WECC_DSW", to_zone="SP15_rest", ttc_mw=10623.0),
            TransferLink(from_zone="NP15", to_zone="SP15_rest", ttc_mw=4000.0),
        ]

    def test_groups_target_corridor_links_one_sided(self):
        env = {
            "WECC_PNW": np.full(T, 1000.0),
            "WECC_DSW": np.full(T, 3000.0),
        }
        groups = build_caiso_corridor_flow_groups(self._links(), env)
        self.assertEqual(len(groups), 2)
        by_link = {int(idx[0]): (cap, bidir) for idx, cap, bidir in groups}
        # WECC_PNW link is index 0, WECC_DSW index 1; both one-sided.
        self.assertIn(0, by_link)
        self.assertIn(1, by_link)
        self.assertFalse(by_link[0][1])
        self.assertFalse(by_link[1][1])
        np.testing.assert_allclose(by_link[1][0], 3000.0)

    def test_empty_when_no_corridor_link(self):
        links = [TransferLink(from_zone="NP15", to_zone="SP15_rest", ttc_mw=4000.0)]
        self.assertEqual(
            build_caiso_corridor_flow_groups(links, {"WECC_DSW": np.ones(T)}), []
        )


class TestCorridorCapLimitsImport(unittest.TestCase):
    """End-to-end: a tight midday cap forces in-state gen over cheap imports."""

    def _solve(self, corridor_cap):
        # One trading zone (LOAD) fed by an expensive in-state gen and a cheap
        # import gen in an external corridor zone, linked LOAD<-CORR.
        # SP15_rest (load) fed by an expensive in-state gen and a cheap import
        # gen in the WECC_DSW corridor zone, over the real WECC_DSW→SP15_rest
        # corridor link (the SP15 split's south gateway).
        zone_names = ["SP15_rest", "WECC_DSW"]
        links = [TransferLink(from_zone="WECC_DSW", to_zone="SP15_rest", ttc_mw=5000.0)]
        gens = [
            Generator(
                unit_id="instate",
                name="instate",
                zone="SP15_rest",
                fuel_type="gas_cc",
                pmax_mw=5000.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=50.0,
            ),
            Generator(
                unit_id="WECC_DSW_imp",
                name="imp",
                zone="WECC_DSW",
                fuel_type="import",
                pmax_mw=5000.0,
                pmin_mw=0.0,
                heat_rate=0.0,
                vom=10.0,
            ),  # cheap
        ]
        fleet = generators_to_fleet_arrays(gens, zone_names, hours=T)
        # heat_rate=0 for both, so mc is just each gen's vom (no fuel/carbon).
        mc = np.array([[50.0] * T, [10.0] * T])  # in-state $50, import $10
        demand = np.zeros((2, T))
        demand[0, :] = 2000.0  # all load in SP15_rest
        incidence = build_incidence_matrix(links, zone_names)
        groups = build_caiso_corridor_flow_groups(links, {"WECC_DSW": corridor_cap})
        res = solve_dispatch(
            fleet=fleet,
            demand=demand,
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
            mc=mc,
            incidence=incidence,
            ttc=np.array([5000.0]),
            interface_groups=groups or None,
        )
        return res

    def test_tight_cap_binds_only_in_capped_hours(self):
        # Cap import at 500 MW in hour 0, 5000 MW elsewhere.
        cap = np.full(T, 5000.0)
        cap[0] = 500.0
        res = self._solve(cap)
        gen = res.dispatch  # (n_gen, T); row order = gens above
        imp = gen[1]
        # Hour 0: import capped at 500 → in-state supplies the rest (1500).
        self.assertAlmostEqual(imp[0], 500.0, delta=1.0)
        self.assertAlmostEqual(gen[0, 0], 1500.0, delta=1.0)
        # Hour 1: cap loose → cheap import serves all 2000, in-state idle.
        self.assertAlmostEqual(imp[1], 2000.0, delta=1.0)
        self.assertAlmostEqual(gen[0, 1], 0.0, delta=1.0)


class TestEnvelopeLoader(unittest.TestCase):
    """The measured envelope is present, diurnal, and CAISO-only."""

    def test_diurnal_shape_and_scope(self):
        self.assertIsNone(measured_corridor_flow_envelope("PJM", 2024, T))
        env = measured_corridor_flow_envelope("CAISO", 2024, 8760)
        self.assertIsNotNone(env)
        self.assertIn("WECC_DSW", env)
        self.assertIn("WECC_PNW", env)
        for cap in env.values():
            self.assertEqual(cap.shape, (8760,))
            self.assertTrue(np.all(cap >= 0.0))  # import ceiling, never forces export
        # DSW deliverability is lower midday (h12) than overnight (h00).
        hod = np.arange(8760) % 24
        dsw = env["WECC_DSW"]
        self.assertLess(dsw[hod == 12].mean(), dsw[hod == 0].mean())


class TestInterchangeModelClock(unittest.TestCase):
    """Per-DIBA stamps map onto the model clock: −1 h standard, −2 h daylight.

    The measured lag of the CISO per-DIBA ``local_time`` stamps against the
    model's hourly frame (see the ``_CAISO_INTERCHANGE_LAG_*`` constant block
    in ``eia_loader`` and FINDING-caiso-seam-tz-correction-2026-07-07).
    """

    def test_standard_time_shifts_one_hour(self):
        import pandas as pd

        from market_sim.data.eia_loader import _caiso_interchange_model_clock

        stamps = pd.DatetimeIndex(["2024-01-15 08:00", "2024-12-01 23:00"])
        out = _caiso_interchange_model_clock(stamps)
        self.assertEqual(list(out), list(stamps - pd.Timedelta(hours=1)))

    def test_daylight_time_shifts_two_hours(self):
        import pandas as pd

        from market_sim.data.eia_loader import _caiso_interchange_model_clock

        stamps = pd.DatetimeIndex(["2024-07-15 14:00", "2024-04-08 11:00"])
        out = _caiso_interchange_model_clock(stamps)
        self.assertEqual(list(out), list(stamps - pd.Timedelta(hours=2)))

    def test_fall_back_repeated_hour_is_deterministic(self):
        import pandas as pd

        from market_sim.data.eia_loader import _caiso_interchange_model_clock

        # 2024-11-03 01:00 occurs twice on the wall clock; ambiguous=False
        # resolves it as standard time (−1 h), deterministically.
        stamps = pd.DatetimeIndex(["2024-11-03 01:00"])
        out = _caiso_interchange_model_clock(stamps)
        self.assertEqual(out[0], pd.Timestamp("2024-11-03 00:00"))


if __name__ == "__main__":
    unittest.main()
