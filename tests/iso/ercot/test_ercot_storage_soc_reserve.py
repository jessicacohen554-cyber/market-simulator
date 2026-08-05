"""Tests for the ERCOT measured AS SOC reservation (ercot-167 mechanism).

Trivial cases first (CLAUDE.md testing pattern): the freeze arithmetic
(shares x published product durations x the committed total) and the
energy-cap clip are exercised on a tiny 2-unit fleet with patched parquet
reads; then the config validators. No clean-data dependency.
"""

import unittest
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.model import storage as storage_mod
from market_sim.model.storage import ercot_storage_as_soc_min

HOURS = 4


def _patched_read(total, products):
    """Return a pd.read_parquet stand-in serving the two award parquets."""

    def _read(path, *a, **k):
        p = str(path)
        if p.endswith("_as_by_restype_hourly.parquet"):
            return pd.DataFrame({"storage": total})
        if p.endswith("_storage_as_products_hourly.parquet"):
            return pd.DataFrame(products)
        raise AssertionError(f"unexpected read: {p}")

    return _read


class SocFloorTests(unittest.TestCase):
    def _run(self, total, products, ecap=(1200.0, 400.0)):
        with (
            mock.patch("pathlib.Path.exists", return_value=True),
            mock.patch.object(
                storage_mod.pd,
                "read_parquet",
                side_effect=_patched_read(total, products),
            ),
        ):
            return ercot_storage_as_soc_min(np.array(ecap), 2023, HOURS)

    def test_freeze_is_shares_times_duration_times_committed_total(self):
        # 100 MW RRS (1 h) + 100 MW ECRS (2 h) measured -> blended 1.5 h; the
        # committed total (200) is the normalization basis, so the fleet floor
        # is 1.5 x 200 = 300 MWh, split 3:1 by energy cap (1200 vs 400).
        total = np.full(HOURS, 200.0)
        products = {
            "regup": np.zeros(HOURS),
            "rrs": np.full(HOURS, 100.0),
            "ecrs": np.full(HOURS, 100.0),
            "nonspin": np.zeros(HOURS),
        }
        soc = self._run(total, products)
        np.testing.assert_allclose(soc.sum(axis=0), np.full(HOURS, 300.0))
        np.testing.assert_allclose(soc[0], np.full(HOURS, 225.0))
        np.testing.assert_allclose(soc[1], np.full(HOURS, 75.0))

    def test_committed_total_governs_when_vintages_differ(self):
        # 2025-style vintage split: measured products sum to 400 but the
        # committed total is 200 -> the floor uses shares x 200, never 400
        # (the armed power dock's basis governs; rule 19 one-award-basis).
        total = np.full(HOURS, 200.0)
        products = {
            "regup": np.zeros(HOURS),
            "rrs": np.full(HOURS, 400.0),
            "ecrs": np.zeros(HOURS),
            "nonspin": np.zeros(HOURS),
        }
        soc = self._run(total, products)
        np.testing.assert_allclose(soc.sum(axis=0), np.full(HOURS, 200.0))

    def test_nonspin_duration_dominates(self):
        # Pure Non-Spin (4 h): 100 MW award -> 400 MWh fleet floor.
        total = np.full(HOURS, 100.0)
        products = {
            "regup": np.zeros(HOURS),
            "rrs": np.zeros(HOURS),
            "ecrs": np.zeros(HOURS),
            "nonspin": np.full(HOURS, 100.0),
        }
        soc = self._run(total, products)
        np.testing.assert_allclose(soc.sum(axis=0), np.full(HOURS, 400.0))

    def test_floor_clipped_at_energy_cap(self):
        # A freeze larger than a unit's tank clips at its energy cap.
        total = np.full(HOURS, 2000.0)
        products = {
            "regup": np.zeros(HOURS),
            "rrs": np.zeros(HOURS),
            "ecrs": np.zeros(HOURS),
            "nonspin": np.full(HOURS, 2000.0),  # 8000 MWh >> fleet 1600
        }
        soc = self._run(total, products)
        self.assertTrue((soc[0] <= 1200.0 + 1e-9).all())
        self.assertTrue((soc[1] <= 400.0 + 1e-9).all())

    def test_missing_files_inert(self):
        with mock.patch("pathlib.Path.exists", return_value=False):
            soc = ercot_storage_as_soc_min(np.array([1200.0, 400.0]), 2023, HOURS)
        self.assertEqual(float(np.abs(soc).max()), 0.0)

    def test_empty_fleet_passthrough(self):
        soc = ercot_storage_as_soc_min(np.array([]), 2023, HOURS)
        self.assertEqual(soc.size, 0)


class ValidatorTests(unittest.TestCase):
    def _cfg(self, **kw):
        from market_sim.config.scenarios import ScenarioConfig

        return ScenarioConfig(**kw)

    def test_arming_without_commitment_is_allowed_but_inert(self):
        # The commitment dependency is a WIRING guard (the deployment-flag
        # pattern): storage_as_commitment threads in as a solve kwarg after
        # construction, so the config accepts the flag alone and the
        # run_calibration.py guard simply never builds the floor without it.
        cfg = self._cfg(ercot_storage_as_soc_reserve=True)
        self.assertTrue(cfg.ercot_storage_as_soc_reserve)
        self.assertFalse(cfg.storage_as_commitment)

    def test_exclusive_with_endogenous(self):
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            self._cfg(
                ercot_storage_as_soc_reserve=True,
                storage_as_commitment=True,
                ercot_storage_as_endogenous=True,
                energy_reserve_coopt=True,
            )

    def test_valid_arming(self):
        cfg = self._cfg(
            ercot_storage_as_soc_reserve=True,
            storage_as_commitment=True,
        )
        self.assertTrue(cfg.ercot_storage_as_soc_reserve)


if __name__ == "__main__":
    unittest.main()
