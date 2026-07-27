"""Tests for the nyiso_renewable_curtailment reader (model consumption seam).

Exercises the raw-fallback path directly against the real committed CSVs
under data/raw/nyiso-renewable-curtailment/ (no clean-tree dependency), then
checks the resource_type/geographic_scope filters.
"""

import unittest

from market_sim.data import nyiso_renewable_curtailment as nrc


class TestNyisoRenewableCurtailment(unittest.TestCase):
    def test_annual_unfiltered_has_wind_and_solar(self) -> None:
        frame = nrc.load_annual_curtailment()
        self.assertFalse(frame.empty)
        self.assertIn("wind", set(frame["resource_type"]))
        self.assertIn("ftm_solar", set(frame["resource_type"]))
        self.assertIn("NYCA", set(frame["geographic_scope"]))

    def test_annual_filters_by_resource_and_scope(self) -> None:
        nyca_wind = nrc.load_annual_curtailment(
            resource_type="wind", geographic_scope="NYCA"
        )
        self.assertTrue((nyca_wind["resource_type"] == "wind").all())
        self.assertTrue((nyca_wind["geographic_scope"] == "NYCA").all())
        # 2017-2025 NYCA-wide wind rows, one per year.
        self.assertGreaterEqual(len(nyca_wind), 9)

        west_wind = nrc.load_annual_curtailment(
            resource_type="wind", geographic_scope="WEST"
        )
        self.assertTrue((west_wind["curtailed_pct"].isna()).all())

    def test_monthly_nyca_rows_carry_pct_not_gwh(self) -> None:
        nyca_monthly = nrc.load_monthly_curtailment(
            resource_type="wind", geographic_scope="NYCA"
        )
        self.assertEqual(len(nyca_monthly), 12 * 9)  # 2017-2025
        self.assertTrue(nyca_monthly["curtailed_energy_gwh"].isna().all())
        self.assertFalse(nyca_monthly["curtailed_pct"].isna().any())

    def test_monthly_zonal_rows_carry_gwh_not_pct(self) -> None:
        zonal_monthly = nrc.load_monthly_curtailment(
            resource_type="wind", geographic_scope="CENTRAL"
        )
        self.assertFalse(zonal_monthly.empty)
        self.assertTrue(zonal_monthly["curtailed_pct"].isna().all())
        self.assertFalse(zonal_monthly["curtailed_energy_gwh"].isna().any())


if __name__ == "__main__":
    unittest.main()
