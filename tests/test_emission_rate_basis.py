"""R3/EM-8 gross-vs-net emission-rate basis regression guard.

The CAMPD-derived per-plant CO2 rate is per **net** MWh (gross scaled by the
parasitic factor), and the dispatch model's generation is net MWh. This asserts
the round-trip identity that guards the basis: applying a plant's measured
``co2_kg_per_mwh_net`` to its net generation reproduces the measured CAMPD CO2
mass within backfill tolerance. A future change that silently derived the rate
on a gross basis (station-service ~2-4% gas / 7-10% coal error) would break it.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.data import campd


def _fixture_plant(parasitic: float) -> pd.DataFrame:
    """One plant, 24 on-hours, CO2 reported for every (heat-covered) hour."""
    n = 24
    ts = pd.date_range("2023-06-01 00:00", periods=n, freq="h")
    gross = np.full(n, 200.0)
    heat = gross * 8.0  # 8 MMBtu/MWh gross
    co2_kg = heat * 53.0  # measured kg CO2, proportional to heat
    return pd.DataFrame(
        {
            "plant_id": 12345,
            "facility_name": "Fixture",
            "state": "TX",
            "year": 2023,
            "date": ts.normalize(),
            "hour": ts.hour,
            "gross_mw": gross,
            "steam_load": np.nan,
            "co2_kg": co2_kg,
            "nox_kg": gross * 0.1,
            "so2_kg": gross * 0.05,
            "heat_mmbtu": heat,
            "hour_of_year": np.arange(n),
        }
    )


class TestGrossNetBasis(unittest.TestCase):
    def test_rate_times_net_reproduces_measured_co2(self):
        parasitic = 0.94  # 6% station service
        df = _fixture_plant(parasitic)
        rates = campd.plant_emission_rates(df, {12345: parasitic})
        row = rates[(rates["plant_id"] == 12345) & (rates["year"] == 2023)].iloc[0]

        measured_co2 = float(df["co2_kg"].sum())
        net_mwh = float(df["gross_mw"].sum()) * parasitic

        # The rate is per NET MWh, so rate × net MWh == measured CO2.
        reconstructed = row["co2_kg_per_mwh_net"] * net_mwh
        self.assertEqual(row["co2_source"], "measured")
        self.assertAlmostEqual(reconstructed, measured_co2, delta=measured_co2 * 1e-3)

        # And the rate is explicitly on the NET (not gross) basis: applying it to
        # gross MWh would overstate CO2 by exactly 1/parasitic.
        gross_mwh = float(df["gross_mw"].sum())
        self.assertAlmostEqual(
            row["co2_kg_per_mwh_net"] * gross_mwh,
            measured_co2 / parasitic,
            delta=measured_co2 * 1e-3,
        )


if __name__ == "__main__":
    unittest.main()
