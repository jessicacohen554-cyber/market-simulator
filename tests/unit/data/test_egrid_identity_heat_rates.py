"""Tests for the eGRID identity-reconciled heat-rate input (nyiso-151).

Covers the three seams:

1. the artifact reader (committed NYISO artifact resolves; an ISO with no
   artifact is an empty no-op),
2. the fleet apply — the swap reaches every unit of a covered plant and no
   other generator, and is a strict no-op while
   ``ScenarioConfig.egrid_identity_heat_rates`` is off,
3. the derive's discovery rule on the committed data — exactly the proven
   Allegany identity (EIA 7784 <-> eGRID 10619) with the pooled rate and its
   LOYO range inside the per-vintage envelope
   (``FINDING-nyiso150-allegany-hr-identity-2026-08-22.md``).
"""

import unittest
from types import SimpleNamespace

from market_sim.data.fleet.eia860 import (
    apply_egrid_identity_heat_rates,
    egrid_identity_heat_rates_for,
)


def _gen(plant_code: int, heat_rate: float) -> SimpleNamespace:
    return SimpleNamespace(plant_code=plant_code, heat_rate=heat_rate)


class TestReader(unittest.TestCase):
    def test_nyiso_artifact_resolves_allegany(self):
        rates = egrid_identity_heat_rates_for("NYISO")
        self.assertIn(7784, rates)
        self.assertAlmostEqual(rates[7784], 8.4209, places=4)

    def test_iso_without_artifact_is_empty(self):
        self.assertEqual(egrid_identity_heat_rates_for("NEISO"), {})


class TestApply(unittest.TestCase):
    def test_swap_reaches_only_covered_plant(self):
        gens = [_gen(7784, 7.5), _gen(7784, 7.5), _gen(50744, 8.56)]
        touched = apply_egrid_identity_heat_rates(gens, "NYISO")
        self.assertEqual(len(touched), 2)
        self.assertAlmostEqual(gens[0].heat_rate, 8.4209, places=4)
        self.assertAlmostEqual(gens[1].heat_rate, 8.4209, places=4)
        self.assertEqual(gens[2].heat_rate, 8.56)

    def test_no_artifact_iso_is_noop(self):
        gens = [_gen(7784, 7.5)]
        touched = apply_egrid_identity_heat_rates(gens, "NEISO")
        self.assertEqual(touched, frozenset())
        self.assertEqual(gens[0].heat_rate, 7.5)


class TestCommittedArtifact(unittest.TestCase):
    """The committed artifact is exactly the proven identity set."""

    def test_single_row_and_loyo_envelope(self):
        import pandas as pd

        from market_sim.config.paths import PROCESSED_DIR

        df = pd.read_csv(PROCESSED_DIR / "egrid_identity_heat_rates_NYISO.csv")
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(int(row.plant_id), 7784)
        self.assertEqual(int(row.egrid_orispl), 10619)
        self.assertGreaterEqual(int(row.n_vintages), 7)
        # The pooled rate sits inside its own leave-one-vintage-out range.
        self.assertLessEqual(float(row.loyo_min), float(row.heat_rate_mmbtu_mwh))
        self.assertLessEqual(float(row.heat_rate_mmbtu_mwh), float(row.loyo_max))


if __name__ == "__main__":
    unittest.main()
