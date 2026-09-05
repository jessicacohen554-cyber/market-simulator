"""Emissions grain in the annual summary (SCN-WS0 deliverable 1).

Trivial-first per CLAUDE.md "Testing Pattern": the partition identities are
proved on a 1-generator / 1-zone / 24-hour fixture where the arithmetic is
exact, then re-checked on a small multi-fuel, multi-zone fleet.

What is under test (scenario-readiness plan §2.5 G-E1/G-E3):

* ``emissions_by_fuel_mt`` and ``emissions_by_zone_mt`` each PARTITION
  ``emissions_mt`` — they are the same ``dispatch x emission_rate`` product
  grouped two ways, so neither may add or lose carbon.
* ``import_co2_mt_reported`` is a reported-only side line that stays OUTSIDE
  ``emissions_mt``, with its disclosure string carried in the summary.
* ``unserved_mwh`` is the slack column's annual energy.
* ``DispatchResult.emissions`` comes back populated from a round-tripped
  Parquet even though no solve wrote the column.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np

from market_sim.model.dispatch import DispatchResult
from market_sim.results import outputs  # noqa: F401  (installs to/from_parquet)
from market_sim.results.emissions import (
    IMPORT_CO2_DISCLOSURE,
    import_co2_tons,
    import_tranche_ef,
)
from market_sim.results.export import _summarize_year
from market_sim.results.outputs import FleetContext

HOURS = 24
# tCO2/MWh — the repo's gas-CC and coal best-bin rates' order of magnitude;
# the identities under test hold for any rate, so exact values are irrelevant.
GAS_RATE = 0.37
COAL_RATE = 0.95


def _result(dispatch: np.ndarray, n_zones: int = 1, slack_mw: float = 0.0):
    """A minimal solved-looking result over ``HOURS`` hours."""
    return DispatchResult(
        dispatch=np.asarray(dispatch, dtype=float),
        wind_dispatched=np.zeros((n_zones, HOURS)),
        solar_dispatched=np.zeros((n_zones, HOURS)),
        slack=np.full((n_zones, HOURS), slack_mw),
        dump=np.zeros((n_zones, HOURS)),
        prices=np.full((n_zones, HOURS), 40.0),
        storage_charge=None,
        storage_discharge=None,
        storage_soc=None,
        flows=None,
        objective_value=0.0,
        status="Optimal",
        build_time=0.0,
        solve_time=0.0,
    )


def _context(fuel_types, rates, zones, unit_ids=None) -> FleetContext:
    n = len(fuel_types)
    return FleetContext(
        fuel_types=list(fuel_types),
        pmax_mw=[100.0] * n,
        emission_rate=[float(r) for r in rates],
        efficiency_bins=["default"] * n,
        heat_rates=[8.0] * n,
        zones=list(zones),
        unit_ids=list(unit_ids or [f"U{i}" for i in range(n)]),
        wind_cap_mw=0.0,
        solar_cap_mw=0.0,
        wind_potential_mwh=0.0,
        solar_potential_mwh=0.0,
        storage_energy_cap_mwh=0.0,
    )


class TestTrivialPartition(unittest.TestCase):
    """1 gen / 1 zone / 24 h — the partition identities are exact here."""

    def setUp(self):
        # 50 MW every hour on one gas-CC unit in one zone.
        self.dispatch = np.full((1, HOURS), 50.0)
        self.result = _result(self.dispatch)
        self.context = _context(["gas_cc"], [GAS_RATE], ["Z"])
        self.summary = _summarize_year(self.result, self.context)

    def test_scalar_is_the_hand_arithmetic(self):
        expected_mt = 50.0 * HOURS * GAS_RATE / 1e6
        self.assertAlmostEqual(self.summary["emissions_mt"], round(expected_mt, 4))

    def test_by_fuel_sums_to_the_scalar_exactly(self):
        # Exact partition: the dicts round at 6 dp and the scalar at 4, so the
        # identity is stated at the scalar's own grain.
        self.assertEqual(
            round(sum(self.summary["emissions_by_fuel_mt"].values()), 4),
            self.summary["emissions_mt"],
        )

    def test_by_zone_sums_to_the_scalar_exactly(self):
        self.assertEqual(
            round(sum(self.summary["emissions_by_zone_mt"].values()), 4),
            self.summary["emissions_mt"],
        )

    def test_the_two_grains_are_the_same_carbon(self):
        # One generator, so both dicts hold the single unit's whole product —
        # equal to the last bit, before any rounding grain enters.
        self.assertEqual(
            sum(self.summary["emissions_by_fuel_mt"].values()),
            sum(self.summary["emissions_by_zone_mt"].values()),
        )

    def test_by_fuel_keys_match_generation_keys(self):
        # The two dicts must join key-for-key for every delta table.
        self.assertEqual(
            set(self.summary["emissions_by_fuel_mt"]),
            set(self.summary["generation_twh"]),
        )

    def test_unserved_is_the_slack_energy(self):
        served = _summarize_year(_result(self.dispatch, slack_mw=3.0), self.context)
        self.assertAlmostEqual(served["unserved_mwh"], 3.0 * HOURS)
        self.assertEqual(self.summary["unserved_mwh"], 0.0)


class TestMultiFuelMultiZone(unittest.TestCase):
    """The partition survives several fuels and zones, and DR is excluded."""

    def setUp(self):
        # gas_cc (Z1), coal (Z2), nuclear (Z2), demand_response (Z1).
        self.dispatch = np.vstack(
            [
                np.full(HOURS, 50.0),
                np.full(HOURS, 80.0),
                np.full(HOURS, 100.0),
                np.full(HOURS, 10.0),
            ]
        )
        self.context = _context(
            ["gas_cc", "coal", "nuclear", "demand_response"],
            [GAS_RATE, COAL_RATE, 0.0, 0.0],
            ["Z1", "Z2", "Z2", "Z1"],
        )
        self.summary = _summarize_year(_result(self.dispatch, n_zones=2), self.context)

    def test_partitions_agree_with_each_other_and_the_scalar(self):
        by_fuel = sum(self.summary["emissions_by_fuel_mt"].values())
        by_zone = sum(self.summary["emissions_by_zone_mt"].values())
        # Both dicts round at 6 dp; the scalar at 4. Agreement to the coarser
        # of the two is the identity, and the two dicts agree to their own.
        self.assertAlmostEqual(by_fuel, by_zone, places=6)
        self.assertAlmostEqual(by_fuel, self.summary["emissions_mt"], places=4)

    def test_zero_carbon_fuels_carry_zero_not_absence(self):
        self.assertEqual(self.summary["emissions_by_fuel_mt"]["nuclear"], 0.0)
        self.assertEqual(self.summary["emissions_by_fuel_mt"]["wind"], 0.0)

    def test_demand_response_is_excluded_like_generation(self):
        self.assertNotIn("demand_response", self.summary["emissions_by_fuel_mt"])
        self.assertNotIn("demand_response", self.summary["generation_twh"])

    def test_zone_grain_attributes_to_the_right_zones(self):
        z = self.summary["emissions_by_zone_mt"]
        self.assertAlmostEqual(z["Z1"], 50.0 * HOURS * GAS_RATE / 1e6, places=6)
        self.assertAlmostEqual(z["Z2"], 80.0 * HOURS * COAL_RATE / 1e6, places=6)


class TestImportLineStaysOutsideTheTotal(unittest.TestCase):
    """G-E3: import-attributed CO2 is disclosed beside the total, never in it."""

    def setUp(self):
        # One gas-CC unit plus two NEISO import tranches on the HQ_import node:
        # HQ_PhaseII (contracted firm hydro, EF 0) and import_scarcity (no
        # derived seam EF -> the CARB unspecified disclosure default).
        self.dispatch = np.vstack(
            [
                np.full(HOURS, 50.0),
                np.full(HOURS, 200.0),
                np.full(HOURS, 100.0),
            ]
        )
        self.context = _context(
            ["gas_cc", "import", "import"],
            [GAS_RATE, 0.0, 0.0],
            ["Z", "HQ_import", "HQ_import"],
            unit_ids=["CC1", "HQ_import_HQ_PhaseII", "HQ_import_import_scarcity"],
        )
        self.summary = _summarize_year(_result(self.dispatch), self.context)

    def test_imports_contribute_nothing_to_the_scored_total(self):
        # The LP holds import emission rates at zero by design, so the scored
        # total is the gas unit alone.
        self.assertAlmostEqual(
            self.summary["emissions_mt"], round(50.0 * HOURS * GAS_RATE / 1e6, 4)
        )
        self.assertEqual(self.summary["emissions_by_fuel_mt"]["import"], 0.0)

    def test_reported_line_prices_each_tranche_by_its_own_factor(self):
        # HQ Phase II is firm hydro (0); the scarcity rung takes the CARB
        # unspecified default. 100 MW x 24 h x 0.428 t/MWh.
        expected_mt = 100.0 * HOURS * 0.428 / 1e6
        self.assertAlmostEqual(
            self.summary["import_co2_mt_reported"], round(expected_mt, 6), places=6
        )

    def test_reported_line_is_never_added_into_the_total(self):
        self.assertGreater(self.summary["import_co2_mt_reported"], 0.0)
        self.assertAlmostEqual(
            sum(self.summary["emissions_by_fuel_mt"].values()),
            self.summary["emissions_mt"],
            places=4,
        )

    def test_disclosure_string_rides_in_the_summary(self):
        self.assertEqual(self.summary["import_co2_basis"], IMPORT_CO2_DISCLOSURE)
        self.assertIn("NEVER", self.summary["import_co2_basis"])

    def test_firm_hydro_seams_are_explicit_zeros(self):
        for name in ("HQ_PhaseII", "Highgate"):
            self.assertEqual(import_tranche_ef(f"HQ_import_{name}", "HQ_import"), 0.0)
        self.assertEqual(
            import_tranche_ef("NYISO_external_HQ_hydro", "NYISO_external"), 0.0
        )

    def test_caiso_reads_the_published_ladder(self):
        # The CAISO tranches carry the LP's own CARB ladder, read live.
        self.assertEqual(
            import_tranche_ef("WECC_import_PNW_hydro_base", "WECC_import"), 0.0
        )
        self.assertAlmostEqual(
            import_tranche_ef("WECC_import_DSW_CCGT", "WECC_import"), 0.37
        )

    def test_export_sinks_are_outside_the_line_not_netted_against_it(self):
        # An export sink is the SAME "import" fuel type with pmax 0 / pmin
        # -capacity, so it dispatches negative. Netting it would credit this
        # ISO for the neighbour's generation at the neighbour's unspecified
        # rate — an unearned offset, not a disclosure.
        ctx = _context(
            ["import", "import"],
            [0.0, 0.0],
            ["HQ_import", "HQ_import"],
            unit_ids=["HQ_import_import_scarcity", "HQ_import_export_NYISO"],
        )
        gen = np.array([100.0 * HOURS, -500.0 * HOURS])
        tons = import_co2_tons(ctx.fuel_types, ctx.unit_ids, ctx.zones, gen)
        self.assertAlmostEqual(tons, 100.0 * HOURS * 0.428, places=6)
        self.assertGreater(tons, 0.0)

    def test_iso_without_an_import_node_reports_zero(self):
        ctx = _context(["gas_cc"], [GAS_RATE], ["Houston"], unit_ids=["CC1"])
        self.assertEqual(
            import_co2_tons(
                ctx.fuel_types, ctx.unit_ids, ctx.zones, np.array([1200.0])
            ),
            0.0,
        )


class TestDispatchResultEmissionsRoundTrip(unittest.TestCase):
    """The declared ``emissions`` field stops being a null on a loaded run."""

    def test_derived_from_the_files_own_context(self):
        dispatch = np.vstack([np.full(HOURS, 50.0), np.full(HOURS, 80.0)])
        result = _result(dispatch)
        context = _context(["gas_cc", "coal"], [GAS_RATE, COAL_RATE], ["Z", "Z"])
        self.assertIsNone(result.emissions)
        with tempfile.TemporaryDirectory() as tmp:
            path = result.to_parquet(Path(tmp) / "year_2026.parquet", context=context)
            loaded = DispatchResult.from_parquet(path)
        self.assertIsNotNone(loaded.emissions)
        np.testing.assert_allclose(
            loaded.emissions, dispatch * np.array([[GAS_RATE], [COAL_RATE]])
        )
        # And it agrees with the summary scalar the export path reports.
        summary = _summarize_year(result, context)
        self.assertAlmostEqual(
            float(np.asarray(loaded.emissions).sum()) / 1e6,
            summary["emissions_mt"],
            places=4,
        )

    def test_absent_context_leaves_the_field_null(self):
        result = _result(np.full((1, HOURS), 50.0))
        with tempfile.TemporaryDirectory() as tmp:
            path = result.to_parquet(Path(tmp) / "year_2026.parquet")
            loaded = DispatchResult.from_parquet(path)
        self.assertIsNone(loaded.emissions)


if __name__ == "__main__":
    unittest.main()
