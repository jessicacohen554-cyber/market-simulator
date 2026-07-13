"""Validation of the ERCOT-65 wind PTC vintage-scoped dispatch offer.

Covers :func:`market_sim.data.renewables.wind_ptc_eligible_monthly_share`
(the measured EIA-860 per-zone-month share of online wind capacity inside its
10-year federal §45 window) and
:func:`market_sim.policy.ira.wind_ptc_vintage_dispatch_offer` (the scoped
``(n_zones, hours)`` replacement for the flat ``-ira_ptc_wind`` offer, gated
by ``ScenarioConfig.wind_ptc_vintage_offers``). Contract:

* flag off is byte-identical (the orchestrators never call the builder);
* the share is capacity-weighted, month-precise (a unit ages out of the
  window mid-year in the month its 120 credit months end), and a unit with
  an unknown vintage counts in the denominator but never as eligible;
* missing source data ⇒ ``None`` (callers keep the flat unscoped offer);
* the statutory per-year level (constants.WIND_PTC_STATUTORY_USD_PER_MWH)
  prices table years, ``ira_ptc_wind`` prices non-table years, and the
  ``ira_wind_solar_last_year`` cliff returns ``None`` (flat path already
  zeroes the credit);
* end-to-end in a forced-long harness, a wind-marginal zone clears at the
  zone's scoped blend — deeper where the fleet is younger — and dump stays
  zero (the dump-cost guard follows the array min).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.renewables import wind_ptc_eligible_monthly_share
from market_sim.model.dispatch import solve_dispatch
from market_sim.policy.ira import wind_ptc_vintage_dispatch_offer

CAL_YEAR = 2023
ZONES = ["ZA", "ZB"]


def _write_wind_parquet(
    data_dir: Path,
    rows: list[dict],
) -> None:
    """Write a minimal EIA-860 wind operable parquet into ``data_dir``."""
    defaults = {
        "Status": "OP",
        "Plant Code": 1,
        "Nameplate Capacity (MW)": 100.0,
        "Operating Year": 2015,
        "Operating Month": 1,
    }
    df = pd.DataFrame([{**defaults, **r} for r in rows])
    df.to_parquet(data_dir / "eia860_wind_operable.parquet")


def _share(rows, zone_lookup, cal_year=CAL_YEAR, zones=None):
    """Run the share builder against a synthetic parquet + zone lookup."""
    with TemporaryDirectory() as td:
        data_dir = Path(td)
        _write_wind_parquet(data_dir, rows)
        with mock.patch(
            "market_sim.data.zone_assignment.build_zone_lookup",
            return_value=zone_lookup,
        ):
            return wind_ptc_eligible_monthly_share(
                "ERCOT", zones or ZONES, cal_year, data_dir=data_dir
            )


class TestEligibleMonthlyShare(unittest.TestCase):
    def test_in_window_and_expired_split_evenly(self):
        """Equal-capacity in-window + expired plants -> share 0.5 all year."""
        share = _share(
            [
                {"Plant Code": 1, "Operating Year": CAL_YEAR - 5},  # in window
                {"Plant Code": 2, "Operating Year": CAL_YEAR - 15},  # expired
            ],
            {1: "ZA", 2: "ZA"},
        )
        np.testing.assert_allclose(share[0], 0.5)
        np.testing.assert_allclose(share[1], 0.0)  # ZB holds no capacity

    def test_capacity_weighting(self):
        """The share is nameplate-weighted, not plant-counted."""
        share = _share(
            [
                {
                    "Plant Code": 1,
                    "Operating Year": CAL_YEAR - 3,
                    "Nameplate Capacity (MW)": 300.0,
                },
                {
                    "Plant Code": 2,
                    "Operating Year": CAL_YEAR - 20,
                    "Nameplate Capacity (MW)": 100.0,
                },
            ],
            {1: "ZA", 2: "ZA"},
        )
        np.testing.assert_allclose(share[0], 0.75)

    def test_month_precise_expiry(self):
        """A COD-June unit 10 years ago is eligible Jan-May, expired June on.

        months_since_cod at month m of ``CAL_YEAR`` is ``120 + (m - 6)`` for a
        June ``CAL_YEAR - 10`` COD, so the 120-month window (26 U.S.C.
        §45(a)(2)(A)(ii)) still covers Jan-May and closes at June.
        """
        share = _share(
            [{"Plant Code": 1, "Operating Year": CAL_YEAR - 10, "Operating Month": 6}],
            {1: "ZA"},
        )
        np.testing.assert_allclose(share[0, :5], 1.0)  # Jan-May
        np.testing.assert_allclose(share[0, 5:], 0.0)  # Jun-Dec

    def test_new_cod_enters_window_at_its_month(self):
        """A CAL_YEAR COD is offline before its month, eligible from it."""
        share = _share(
            [
                {"Plant Code": 1, "Operating Year": CAL_YEAR, "Operating Month": 7},
                {"Plant Code": 2, "Operating Year": CAL_YEAR - 20},
            ],
            {1: "ZA", 2: "ZA"},
        )
        np.testing.assert_allclose(share[0, :6], 0.0)  # only the expired unit
        np.testing.assert_allclose(share[0, 6:], 0.5)

    def test_unknown_vintage_counts_only_in_denominator(self):
        """Unknown COD stays online (mask convention) but never eligible."""
        share = _share(
            [
                {"Plant Code": 1, "Operating Year": np.nan},
                {"Plant Code": 2, "Operating Year": CAL_YEAR - 1},
            ],
            {1: "ZA", 2: "ZA"},
        )
        np.testing.assert_allclose(share[0], 0.5)

    def test_zone_assignment_routes_capacity(self):
        """Plants land in their looked-up zones; per-zone shares differ."""
        share = _share(
            [
                {"Plant Code": 1, "Operating Year": CAL_YEAR - 2},
                {"Plant Code": 2, "Operating Year": CAL_YEAR - 18},
            ],
            {1: "ZA", 2: "ZB"},
        )
        np.testing.assert_allclose(share[0], 1.0)
        np.testing.assert_allclose(share[1], 0.0)

    def test_missing_parquet_returns_none(self):
        with TemporaryDirectory() as td:
            self.assertIsNone(
                wind_ptc_eligible_monthly_share(
                    "ERCOT", ZONES, CAL_YEAR, data_dir=Path(td)
                )
            )


class TestVintageDispatchOffer(unittest.TestCase):
    def _offer(self, year, share, config=None, hours=8760):
        cfg = config or ScenarioConfig(wind_ptc_vintage_offers=True)
        with mock.patch(
            "market_sim.data.renewables.wind_ptc_eligible_monthly_share",
            return_value=share,
        ):
            return wind_ptc_vintage_dispatch_offer("ERCOT", year, ZONES, cfg, hours)

    def test_statutory_level_on_table_year(self):
        """2023 prices at the IRS statutory $28, scaled by the share."""
        share = np.full((2, 12), 0.5)
        share[1] = 1.0
        offer = self._offer(2023, share)
        self.assertEqual(offer.shape, (2, 8760))
        np.testing.assert_allclose(offer[0], -14.0)  # -28 x 0.5
        np.testing.assert_allclose(offer[1], -28.0)

    def test_flat_fallback_level_off_table(self):
        """A non-table (forward) year falls back to ira_ptc_wind."""
        cfg = ScenarioConfig(wind_ptc_vintage_offers=True)
        offer = self._offer(2026, np.full((2, 12), 1.0), config=cfg)
        np.testing.assert_allclose(offer, -cfg.ira_ptc_wind)

    def test_monthly_expansion_follows_calendar(self):
        """The (n_zones, 12) share expands on the calendar month of hour."""
        share = np.zeros((2, 12))
        share[0, 0] = 1.0  # January only
        offer = self._offer(2023, share)
        np.testing.assert_allclose(offer[0, : 31 * 24], -28.0)
        np.testing.assert_allclose(offer[0, 31 * 24 :], 0.0)

    def test_cliff_returns_none(self):
        """Past ira_wind_solar_last_year the flat path already zeroes."""
        self.assertIsNone(self._offer(2028, np.full((2, 12), 1.0)))

    def test_missing_share_returns_none(self):
        self.assertIsNone(self._offer(2023, None))


def _wind_fleet(zone_names, hours, pmax=200.0):
    """One $50 gas_cc per zone, for the forced-long price-formation solves."""
    generators = [
        Generator(
            unit_id=f"G{i}",
            name=f"G{i}",
            zone=z,
            fuel_type="gas_cc",
            pmax_mw=pmax,
            pmin_mw=0.0,
            eford=0.0,
        )
        for i, z in enumerate(zone_names)
    ]
    return generators_to_fleet_arrays(generators, zone_names, hours=hours)


class TestVintagePriceFormation(unittest.TestCase):
    """Forced-long solves: a wind-marginal zone clears at its scoped blend."""

    T = 24

    def test_zonal_lmp_equals_the_zonal_blend(self):
        """Two islanded long zones price at their own vintage blends.

        Both zones have 200 MW of wind against 80 MW of demand (wind is
        marginal / curtailed); ZA's fleet blend is -28, ZB's -14. No links,
        so each zone's LMP is its own wind offer, and dump never binds (the
        guard follows the array min).
        """
        zone_names = ["ZA", "ZB"]
        fleet = _wind_fleet(zone_names, self.T)
        wind_mc = np.tile(np.array([[-28.0], [-14.0]]), (1, self.T))
        result = solve_dispatch(
            fleet,
            np.full((2, self.T), 80.0),
            mc=np.full((2, self.T), 50.0),
            T=self.T,
            wind_cf=np.full((2, self.T), 1.0),
            wind_cap=np.array([200.0, 200.0]),
            solar_cf=np.zeros((2, self.T)),
            solar_cap=np.zeros(2),
            wind_mc=wind_mc,
        )
        np.testing.assert_allclose(result.prices[0], -28.0, atol=0.1)
        np.testing.assert_allclose(result.prices[1], -14.0, atol=0.1)
        # Wind serves the full load in both zones; thermal off; nothing dumped.
        np.testing.assert_allclose(result.wind_dispatched, 80.0, atol=0.1)
        np.testing.assert_allclose(result.dispatch, 0.0, atol=0.1)
        self.assertLessEqual(float(np.abs(result.dump).max()), 1e-6)


if __name__ == "__main__":
    unittest.main()
