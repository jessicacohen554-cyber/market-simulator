"""soco-81: per-plant TWO-SIDED incremental heat rate on coal tranches.

``ScenarioConfig.coal_econ_marginal_hr_two_sided`` prices the committed + econ
tranches of a coal tranche set that carries a measured must-run floor at the
plant's own measured incremental heat rate (average x ratio from
``coal_incremental_hr_ratio_<ISO>.csv``). Contracts pinned here:

* OFF is byte-identical;
* ON, a floored plant's ``committed`` / ``econlo`` take ``ratio_econ_low`` and
  ``econhi`` takes ``ratio_econ_high`` — lowering as well as raising;
* ``mustrun`` and ``peak`` never move, and a floorless cycler never moves;
* the ratio REPLACES the band multiplier (rule 19), it does not multiply it;
* the year rule is the average-HR artifact's (year row, else pooled);
* an ISO with no artifact is a no-op (rule 25).
"""

import unittest

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import bins_to_fleet
from market_sim.data.fleet.assembly import _incremental_econ_ratio
from market_sim.data.fleet.campd_bins import coal_incremental_hr_ratios

ISO = "SOCO"
ZONE_NAMES = get_iso_config(ISO).zone_names
BASE_HR = 10.0
BOWEN = 703  # must-run floored in the SOCO keeper
BANDS = {
    "committed": 1.0,
    "econ_low": 1.0,
    "econ_high": 1.0,
    "peak": 1.0,
    "econ_low_share": 0.55,
}


def _bin(plant: int, pct_mr: float) -> dict:
    """One synthetic COAL_BIT bin row."""
    return {
        "Plant_Group": "COAL_BIT",
        "ERCOT_Zone": ZONE_NAMES[0],
        "Bin_Number": 1,
        "Bin_Label": f"TEST{plant}",
        "Plant_Code": plant,
        "Plant_Name": f"Test {plant}",
        "capacity_mw": 1000.0,
        "hr_weighted": BASE_HR,
        "hr_mr": BASE_HR,
        "hr_mc": BASE_HR,
        "hr_econ": BASE_HR,
        "hr_peak": BASE_HR,
        "pct_mr": pct_mr,
        "pct_mc": 20.0,
        "pct_econ": 100.0 - 20.0 - 5.0 - pct_mr,
        "pct_peak": 5.0,
        "min_run": 0,
        "min_down": 0,
        "plant_count": 1,
        "plant_codes": [plant],
        "fuel": "coal",
    }


def _config(bands: dict | None = None, **kw) -> ScenarioConfig:
    return ScenarioConfig(
        iso=ISO,
        mode="backcast",
        offer_curve_by_group={"COAL_BIT": dict(bands or BANDS)},
        **kw,
    )


def _hrs(config: ScenarioConfig, pct_mr: float, year: int | None) -> dict[str, float]:
    fleet, _ = bins_to_fleet(
        pd.DataFrame([_bin(BOWEN, pct_mr)]), ZONE_NAMES, config, year=year
    )
    return {g.unit_id.rsplit("_", 1)[-1]: g.heat_rate for g in fleet}


class TestTwoSidedIncrementalHr(unittest.TestCase):
    def test_off_is_identical_to_unset(self):
        self.assertEqual(
            _hrs(_config(), 40.0, 2019),
            _hrs(_config(coal_econ_marginal_hr_two_sided=False), 40.0, 2019),
        )

    def test_on_prices_floored_tranches_at_incremental(self):
        lo, hi = coal_incremental_hr_ratios(ISO, 2019)[BOWEN]
        off = _hrs(_config(), 40.0, 2019)
        on = _hrs(_config(coal_econ_marginal_hr_two_sided=True), 40.0, 2019)
        self.assertEqual(set(off), set(on))
        self.assertIn("mustrun", on)
        self.assertAlmostEqual(on["committed"], BASE_HR * lo)
        self.assertAlmostEqual(on["econlo"], BASE_HR * lo)
        self.assertAlmostEqual(on["econhi"], BASE_HR * hi)
        self.assertEqual(on["mustrun"], off["mustrun"])
        self.assertEqual(on["peak"], off["peak"])
        # Bowen 2019: incremental below average on both points -> LOWERS.
        self.assertLess(on["econlo"], off["econlo"])

    def test_two_sided_raises_too(self):
        lo, hi = coal_incremental_hr_ratios(ISO, 2025)[BOWEN]
        self.assertGreater(hi, 1.0)  # Bowen 2025 econ_high: 1.0502
        on = _hrs(_config(coal_econ_marginal_hr_two_sided=True), 40.0, 2025)
        self.assertAlmostEqual(on["econhi"], BASE_HR * hi)
        self.assertGreater(on["econhi"], BASE_HR)

    def test_ratio_replaces_band_multiplier(self):
        bands = dict(BANDS, committed=1.2, econ_low=1.3, econ_high=1.3)
        lo, _ = coal_incremental_hr_ratios(ISO, 2019)[BOWEN]
        on = _hrs(_config(bands, coal_econ_marginal_hr_two_sided=True), 40.0, 2019)
        self.assertAlmostEqual(on["committed"], BASE_HR * lo)

    def test_floorless_cycler_untouched(self):
        self.assertEqual(
            _hrs(_config(), 0.0, 2019),
            _hrs(_config(coal_econ_marginal_hr_two_sided=True), 0.0, 2019),
        )

    def test_year_rule_year_row_else_pooled(self):
        pooled = coal_incremental_hr_ratios(ISO, None)[BOWEN]
        y19 = coal_incremental_hr_ratios(ISO, 2019)[BOWEN]
        fwd = coal_incremental_hr_ratios(ISO, 2031)[BOWEN]
        self.assertNotEqual(pooled, y19)
        self.assertEqual(fwd, pooled)

    def test_iso_without_artifact_is_noop(self):
        self.assertEqual(coal_incremental_hr_ratios("ERCOT", 2023), {})

    def test_econ_ratio_mapping(self):
        self.assertEqual(_incremental_econ_ratio("econlo", 0, 2, 0.9, 1.1), 0.9)
        self.assertEqual(_incremental_econ_ratio("econhi", 1, 2, 0.9, 1.1), 1.1)
        self.assertAlmostEqual(_incremental_econ_ratio("econ", 0, 1, 0.9, 1.1), 1.0)
        self.assertAlmostEqual(_incremental_econ_ratio("econ03", 3, 6, 0.9, 1.0), 0.96)


if __name__ == "__main__":
    unittest.main()
