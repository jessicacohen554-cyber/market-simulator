"""ercot-219 Option-B mechanism unit pins (B-1; PRECOMMIT-ercot219 §1).

Three pure-logic surfaces of the three-stage artificial-shortage mechanism:

* the hourly ``(n_storage, T)`` widening of ``build_cost_vector``'s storage
  discharge cost (stage 3's LP seam) — static callers must be byte-identical,
  and an hourly array must land per (unit, hour) in the discharge block;
* ``within_day_forward_max`` — the stage-2 remainder-of-operating-day window
  convention (reverse cumulative maximum per fixed-clock day block);
* the ScenarioConfig registration: pinned default cache key unmoved with the
  three fields at default (the nyiso-119 discipline), armed key distinct, and
  the stage-1 forecast-mode guard (``_BACKCAST_ONLY_OVERLAY_FIELDS``) firing.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.lp.costs import build_cost_vector
from market_sim.model.lp.layout import VariableLayout
from market_sim.results.scarcity import within_day_forward_max

_PINNED_DEFAULT_KEY = "cedadc285f8603b9"


class TestStorageDischargeCostHourly(unittest.TestCase):
    def _layout(self, T: int = 6) -> VariableLayout:
        return VariableLayout(n_gen=2, n_zones=1, n_storage=3, n_links=0, T=T)

    def test_static_vector_byte_identical_to_constant_hourly(self):
        layout = self._layout()
        mc = np.ones((2, layout.T))
        vom = np.array([1.0, 2.5, 10.0])
        static = build_cost_vector(layout, mc, 5000.0, storage_discharge_cost=vom)
        hourly = build_cost_vector(
            layout,
            mc,
            5000.0,
            storage_discharge_cost=np.repeat(vom[:, None], layout.T, axis=1),
        )
        np.testing.assert_array_equal(static, hourly)

    def test_hourly_cost_lands_per_unit_per_hour(self):
        layout = self._layout(T=4)
        mc = np.zeros((2, layout.T))
        cost = np.zeros((3, layout.T))
        cost[1, 2] = 777.0  # unit 1, hour 2 only
        vec = build_cost_vector(layout, mc, 5000.0, storage_discharge_cost=cost)
        block = vec.reshape(layout.T, layout.vars_per_hour)
        dis = block[:, layout._dis_off : layout._soc_off]
        # every discharge slot carries epsilon; only (h2, unit1) adds 777.
        base = dis[0, 0]
        self.assertAlmostEqual(dis[2, 1] - base, 777.0)
        off = dis - base
        off[2, 1] = 0.0
        self.assertAlmostEqual(float(np.abs(off).max()), 0.0)


class TestWithinDayForwardMax(unittest.TestCase):
    def test_two_day_forward_max(self):
        x = np.zeros(48)
        x[5] = 0.4
        x[20] = 0.9  # day-1 evening peak
        x[30] = 0.2  # day 2
        out = within_day_forward_max(x)
        # day 1: every hour <= 20 sees the 0.9 peak; hours after it fall back.
        self.assertAlmostEqual(out[0], 0.9)
        self.assertAlmostEqual(out[5], 0.9)
        self.assertAlmostEqual(out[20], 0.9)
        self.assertAlmostEqual(out[21], 0.0)
        # day 2 never sees day 1 (the window is within-day only).
        self.assertAlmostEqual(out[24], 0.2)
        self.assertAlmostEqual(out[31], 0.0)

    def test_non_multiple_tail_carried(self):
        x = np.arange(26, dtype=float)
        out = within_day_forward_max(x)
        self.assertAlmostEqual(out[0], 23.0)  # day-1 max
        self.assertAlmostEqual(out[24], 24.0)  # tail carried element-wise
        self.assertAlmostEqual(out[25], 25.0)


class TestErcot219Registration(unittest.TestCase):
    def test_default_key_unmoved_and_armed_distinct(self):
        cfg = ScenarioConfig()
        self.assertEqual(cfg.cache_key(), _PINNED_DEFAULT_KEY)
        base = cfg.with_overrides(mode="backcast")
        armed = base.with_overrides(
            ercot_capability_reconciliation=True,
            ercot_exhaustion_expectation=True,
            ercot_storage_reservation_offer=True,
        )
        self.assertNotEqual(armed.cache_key(), base.cache_key())

    def test_stage1_is_backcast_only(self):
        with self.assertRaises(ValueError):
            ScenarioConfig().with_overrides(ercot_capability_reconciliation=True)
        # stages 2-3 are not measured overlays; mode guard does not fire.
        ScenarioConfig().with_overrides(ercot_exhaustion_expectation=True)


if __name__ == "__main__":
    unittest.main()
