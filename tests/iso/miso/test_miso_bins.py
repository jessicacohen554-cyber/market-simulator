"""Tests for the MISO per-plant CAMPD offer-curve tranches and bin synthesis.

MISO was the second-to-last ISO (with SPP) still on the legacy equal-width
``aggregate_fleet`` heat-rate path: it had zones, wind and zonal demand but the
per-plant tranche artifact step had simply never been run, so coal had no
per-plant take-or-pay floor and freely cycled to zero overnight. This pack adds
``data/raw/_processed-legacy/thermal_tranches_MISO.csv`` (44 coal plants with a
measured online Pmin ~20-30% of nameplate, CC committed bands) and flips MISO
into :data:`CAMPD_BINNING_ISOS`, so the runner synthesizes one LP unit per plant
with a rising offer curve via :func:`fleet_to_bins` exactly as the other
non-ERCOT ISOs do.

Unlike NEISO (whose lone coal unit is a winter peaker with a zero must-run
share), MISO carries a genuine coal baseload take-or-pay layer: the large PRB /
lignite supercriticals (Monroe, Labadie, Rush Island, ...) hold a measured
synchronization floor that the dispatch must respect instead of cycling them off.
"""

from market_sim.config.plant_taxonomy import COAL_CLASSES
import unittest

import pandas as pd

from market_sim.config.constants import CAMPD_BINNING_ISOS
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import PROCESSED_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    fleet_to_bins,
    load_fleet_from_csv,
    thermal_tranche_overrides,
    thermal_tranche_peaking,
)
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
TRANCHES = PROCESSED_DIR / "thermal_tranches_MISO.csv"


class TestMisoBinningEnabled(unittest.TestCase):
    """MISO is gated onto the per-plant CAMPD binning path."""

    def test_miso_in_campd_binning_isos(self):
        self.assertIn("MISO", CAMPD_BINNING_ISOS)


class TestMisoTrancheArtifact(unittest.TestCase):
    """The CAMPD-derived thermal-tranche artifact for MISO."""

    @classmethod
    def setUpClass(cls):
        cls.df = pd.read_csv(TRANCHES)

    def test_artifact_present_and_covers_thermal_fleet(self):
        self.assertGreater(len(self.df), 100)
        ok = self.df[self.df["status"] == "ok"]
        self.assertGreater(len(ok), 100)

    def test_coal_has_real_mustrun_layer(self):
        """MISO coal carries a genuine take-or-pay floor: most coal plants
        derive a non-zero must-run share, unlike NEISO's winter-peaker coal."""
        overrides = thermal_tranche_overrides("MISO")
        coal = {
            (c, g): mr for (c, g), (_committed, mr) in overrides.items() if g == "COAL"
        }
        self.assertGreater(len(coal), 30)
        non_zero = [mr for mr in coal.values() if mr > 0.0]
        # A clear majority of coal plants hold a sunk baseload floor.
        self.assertGreater(len(non_zero), len(coal) / 2)
        # And those floors are a sane fraction of nameplate, not noise.
        for mr in non_zero:
            self.assertTrue(0.0 < mr <= 60.0, f"coal mustrun {mr}")

    def test_committed_shares_bounded(self):
        overrides = thermal_tranche_overrides("MISO")
        for (code, group), (committed, _mustrun) in overrides.items():
            self.assertTrue(
                0.0 < committed <= 70.0, f"{code} {group} committed {committed}"
            )

    def test_peaking_shares_bounded_and_cc_only(self):
        peaking = thermal_tranche_peaking("MISO")
        self.assertGreater(len(peaking), 10)
        for (code, group), pct in peaking.items():
            self.assertIn(group, ("CC_REGULAR", "CC_CHP"))
            self.assertTrue(0.0 <= pct <= 25.0, f"{code} peaking {pct}")


class TestMisoFleetToBins(unittest.TestCase):
    """The runner's per-plant synthesis path for MISO."""

    @classmethod
    def setUpClass(cls):
        cls.config = ScenarioConfig(iso="MISO", mode="backcast")
        cls.gens = load_fleet_from_csv("MISO", get_iso_config("MISO"))
        cls.bins = fleet_to_bins(cls.gens, "MISO", cls.config)

    def test_returns_non_empty_frame(self):
        self.assertFalse(self.bins.empty)
        self.assertGreater(len(self.bins), 100)
        # one row per (plant, group)
        keys = list(zip(self.bins["Plant_Code"], self.bins["Plant_Group"]))
        self.assertEqual(len(keys), len(set(keys)))

    def test_coal_mustrun_positive(self):
        """Synthesized coal bins carry a positive must-run floor (pct_mr > 0),
        so coal holds its overnight/morning floor instead of cycling to zero."""
        coal = self.bins[self.bins["Plant_Group"].isin(COAL_CLASSES)]
        self.assertGreater(len(coal), 20)
        self.assertTrue((coal["pct_mr"] > 0.0).any())
        # The capacity-weighted coal must-run is a meaningful baseload floor.
        cw = float(
            (coal["pct_mr"] * coal["capacity_mw"]).sum() / coal["capacity_mw"].sum()
        )
        self.assertGreater(cw, 10.0)

    def test_cc_committed_band(self):
        """Combined-cycle plants get a per-plant committed band (not the coarse
        legacy 30% class default)."""
        cc = self.bins[self.bins["Plant_Group"] == "CC_REGULAR"]
        self.assertGreater(len(cc), 10)
        self.assertTrue((cc["pct_mc"] > 0.0).all())


if __name__ == "__main__":
    unittest.main()
