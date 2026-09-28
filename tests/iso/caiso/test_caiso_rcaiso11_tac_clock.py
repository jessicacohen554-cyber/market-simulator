"""R-CAISO-11: ``caiso_tac_shares_standard_time`` places TAC shares on fixed PST.

Guards the flag's contract: default off and cache-key neutral when off; when
on, a DST-month share row equals the default parse shifted one hour earlier
(the prevailing-time parse lands it one hour late), a standard-time month is
unchanged, and every column still sums to 1.
"""

from __future__ import annotations

import unittest
from dataclasses import replace

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.paths import RAW_DATA_DIR

ZONES = ["NP15", "ZP26", "SP15_rest", "LA_BASIN", "SDGE"]
YEAR = 2024
RAW = RAW_DATA_DIR / "zone-specific-demand" / "CAISO" / f"CAISO_tac_load_hourly_{YEAR}.csv"


class TestFlagRegistration(unittest.TestCase):
    """The field is default off and dropped from the cache key when off."""

    def test_default_off_and_key_neutral(self) -> None:
        """Off is the default; an explicit False keeps the key; True moves it."""
        base = ScenarioConfig()
        self.assertFalse(base.caiso_tac_shares_standard_time)
        self.assertEqual(
            base.cache_key(),
            replace(base, caiso_tac_shares_standard_time=False).cache_key(),
        )
        self.assertNotEqual(
            base.cache_key(),
            replace(base, caiso_tac_shares_standard_time=True).cache_key(),
        )


@unittest.skipUnless(RAW.exists(), "CAISO TAC raw file not hydrated")
class TestStandardTimeParse(unittest.TestCase):
    """The PST parse is the prevailing parse moved one hour earlier in DST."""

    @classmethod
    def setUpClass(cls) -> None:
        """Parse the year both ways once."""
        from scripts.data.curate_zonal_shares import parse_caiso_shares

        cls.dst = parse_caiso_shares(YEAR, ZONES)
        cls.pst = parse_caiso_shares(YEAR, ZONES, standard_time=True)

    def test_columns_sum_to_one(self) -> None:
        """Both parses are proper share matrices."""
        np.testing.assert_allclose(self.pst.sum(axis=0), 1.0, atol=1e-9)

    def test_july_is_shifted_one_hour(self) -> None:
        """Mid-July: PST share at hour t equals the prevailing share at t+1."""
        t = np.arange(4700, 4900)  # mid-July, well inside DST
        np.testing.assert_allclose(self.pst[:, t], self.dst[:, t + 1], atol=1e-12)

    def test_january_is_unchanged(self) -> None:
        """Standard-time months are identical under both parses."""
        t = np.arange(200, 400)
        np.testing.assert_allclose(self.pst[:, t], self.dst[:, t], atol=1e-12)

    def test_load_demand_off_is_byte_identical(self) -> None:
        """Arming changes only the zonal split, never the system total."""
        from market_sim.data.eia930.demand import load_demand

        cfg = get_iso_config("CAISO")
        off = load_demand("CAISO", YEAR, cfg)
        on = load_demand("CAISO", YEAR, cfg, caiso_tac_shares_standard_time=True)
        np.testing.assert_allclose(off.sum(axis=0), on.sum(axis=0), rtol=1e-12)
        self.assertGreater(float(np.abs(off - on).max()), 100.0)


if __name__ == "__main__":
    unittest.main()
