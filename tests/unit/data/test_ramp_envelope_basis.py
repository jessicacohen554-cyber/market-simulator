"""Tests for the ``ramp_limits`` mechanism's reachability and its net basis.

Two defects repaired by ERCOT-132 leg A, one test each:

* **Reachability.** ``ramp_limits`` had a CLI flag, a TIER_TAGS entry, LP row
  builders, a loader, a frozen derive and a committed CAISO artifact — but its
  ``ScenarioConfig`` declaration was never written (``git log -S`` finds no
  history for it), so arming the flag raised ``TypeError`` while every consumer
  read it through ``getattr(config, "ramp_limits", False)`` and silently saw
  ``False``. The mechanism could not be turned on at all.
* **Basis.** ``scripts/data/derive_campd_ramp_envelopes.py`` measures CAMPD
  ``grossLoad`` deltas; the LP's ``P`` columns are NET. The loader fed the
  published MW straight through, so every ISO's ramp rows were ~2-7 % looser
  than the measured capability (the station-service fraction).

Design: docs/ramp-locational-design-2026-07.md §1. Trivial fixtures first, per
the repo testing pattern.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.campd import DEFAULT_PARASITIC_LOAD_PCT
from market_sim.data.fleet import build_ramp_groups
from market_sim.data.fleet.models import FleetArrays


# The default ScenarioConfig cache key, pinned repo-wide. Declaring a new field
# must NOT move it — ``ramp_limits`` is registered in
# ``_CACHE_KEY_OPTIONAL_FIELDS`` so its default value is dropped from the hash.
PINNED_DEFAULT_CACHE_KEY = "e5ecd4105ada3e58"


def _fleet(plant_codes, plant_groups, pmax):
    """Minimal FleetArrays carrying only what ``build_ramp_groups`` reads."""
    n = len(plant_codes)
    z = np.zeros(n)
    return FleetArrays(
        pmax=np.asarray(pmax, dtype=float),
        pmin=z.copy(),
        heat_rate=np.full(n, 10.0),
        vom=z.copy(),
        emission_rate=z.copy(),
        nox_rate=z.copy(),
        so2_rate=z.copy(),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.zeros(n, dtype=int),
        availability=np.ones((n, 1)),
        unit_ids=[f"u{i}" for i in range(n)],
        efficiency_bin=np.zeros(n, dtype=int),
        plant_code=np.asarray(plant_codes, dtype=int),
        plant_group=np.asarray(plant_groups, dtype=object),
    )


class TestRampLimitsReachable(unittest.TestCase):
    """The flag must exist, default off, arm cleanly and keep the pinned key."""

    def test_field_is_declared_and_defaults_off(self):
        cfg = ScenarioConfig()
        self.assertTrue(
            hasattr(cfg, "ramp_limits"),
            "ramp_limits must be a declared ScenarioConfig field — the CLI "
            "flag, TIER_TAGS entry and both orchestrators already assume it",
        )
        self.assertFalse(cfg.ramp_limits, "ramp_limits is GATED, default off")

    def test_flag_arms(self):
        # The defect: this raised TypeError, so --ramp-limits crashed at
        # run_calibration_full.py:4046 and the mechanism was unreachable.
        armed = ScenarioConfig().with_overrides(ramp_limits=True)
        self.assertTrue(armed.ramp_limits)

    def test_default_cache_key_is_byte_stable(self):
        self.assertEqual(ScenarioConfig().cache_key(), PINNED_DEFAULT_CACHE_KEY)

    def test_armed_cache_key_is_distinct(self):
        armed = ScenarioConfig().with_overrides(ramp_limits=True)
        self.assertNotEqual(armed.cache_key(), PINNED_DEFAULT_CACHE_KEY)


class TestRampEnvelopeNetBasis(unittest.TestCase):
    """``basis == "plant"`` MW rebase to net; ``class_fraction`` rows do not."""

    ENV = pd.DataFrame(
        [
            # A measured plant row, published on CAMPD's GROSS basis.
            {
                "plant_code": 7,
                "bucket": "CC",
                "pmax_obs_mw": 300.0,
                "n_online_hours": 9000,
                "ramp_up_mw": 100.0,
                "ramp_dn_mw": 80.0,
                "basis": "plant",
            },
            # The class-median FRACTION fallback (plant_code 0).
            {
                "plant_code": 0,
                "bucket": "CC",
                "pmax_obs_mw": np.nan,
                "n_online_hours": 9000,
                "ramp_up_mw": 0.40,
                "ramp_dn_mw": 0.30,
                "basis": "class_fraction",
            },
        ]
    )

    def _groups(self, monkeypatched_factors, plant_codes=(7,), pmax=(300.0,)):
        """Run build_ramp_groups against the fixture with a stubbed factor map."""
        import market_sim.data.fleet.campd_bins as cb

        real_env = cb.load_campd_ramp_envelopes
        real_par = cb._ramp_parasitic_factor_map
        cb.load_campd_ramp_envelopes = lambda iso: self.ENV
        cb._ramp_parasitic_factor_map = lambda: monkeypatched_factors
        try:
            fleet = _fleet(
                list(plant_codes), ["CC_REGULAR"] * len(plant_codes), list(pmax)
            )
            return build_ramp_groups(fleet, "TEST")
        finally:
            cb.load_campd_ramp_envelopes = real_env
            cb._ramp_parasitic_factor_map = real_par

    def test_measured_plant_row_is_rebased_by_the_measured_factor(self):
        out = self._groups({7: 0.94})
        self.assertIsNotNone(out)
        _, _, ru, rd = out
        # 100 gross x 0.94 = 94 net; 80 gross x 0.94 = 75.2 net.
        np.testing.assert_allclose(ru, [94.0])
        np.testing.assert_allclose(rd, [75.2])

    def test_missing_factor_falls_back_to_the_cited_class_default(self):
        out = self._groups({})  # no measured reconciliation for plant 7
        self.assertIsNotNone(out)
        _, _, ru, rd = out
        factor = 1.0 - DEFAULT_PARASITIC_LOAD_PCT["CC_REGULAR"]
        np.testing.assert_allclose(ru, [100.0 * factor])
        np.testing.assert_allclose(rd, [80.0 * factor])

    def test_rebasis_tightens_never_loosens(self):
        _, _, ru_net, rd_net = self._groups({7: 0.94})
        self.assertLess(float(ru_net[0]), 100.0)
        self.assertLess(float(rd_net[0]), 80.0)

    def test_class_fraction_rows_are_not_rebased(self):
        # Plant 9 has no measured row, so it takes the CC class FRACTION.
        # That fraction is already basis-neutral (the derive forms it as
        # gross_delta / gross_pmax_obs and it is applied to NET pmax), so
        # applying a parasitic factor to it would DOUBLE-COUNT.
        out = self._groups({9: 0.90}, plant_codes=(9,), pmax=(500.0,))
        self.assertIsNotNone(out)
        _, _, ru, rd = out
        np.testing.assert_allclose(ru, [0.40 * 500.0])
        np.testing.assert_allclose(rd, [0.30 * 500.0])


if __name__ == "__main__":
    unittest.main()
