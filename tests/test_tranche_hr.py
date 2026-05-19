"""Tests for the committed/economic two-tranche heat-rate split.

A CAMPD bin's base capacity is split into a Committed tranche (the
part-load must-run block, heat rate above the bin average) and an
Economic tranche (the incremental dispatch range, heat rate below the
bin average). See :func:`market_sim.data.fleet.bins_to_fleet`.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    assemble_mc,
    bins_to_fleet,
    generators_to_fleet_arrays,
    get_emission_rate,
    split_coal_tranches,
)
from market_sim.model.commitment import apply_commitment_with_coal_pin
from market_sim.model.dispatch import solve_dispatch

ZONE_NAMES = get_iso_config("ERCOT").zone_names


def _bin_row(**overrides) -> dict:
    """Return one aggregated-bin row, with no peaking tranche by default."""
    row = {
        "Plant_Group": "CC_REGULAR",
        "ERCOT_Zone": "Houston",
        "Bin_Number": 1,
        "Bin_Label": "T1",
        "capacity_mw": 1000.0,
        "hr_weighted": 7.0,
        "pct_mr": 0,
        "pct_mc": 40,
        "pct_econ": 60,
        "pct_peak": 0,
        "min_run": 8,
        "min_down": 4,
        "plant_codes": [1],
    }
    row.update(overrides)
    return row


def _bins(*rows: dict) -> pd.DataFrame:
    return pd.DataFrame(list(rows))


class TestWeightedAverageHeatRate(unittest.TestCase):
    """The capacity-weighted tranche HR sits above the nameplate HR."""

    def test_weighted_hr_exceeds_nameplate(self):
        # committed_cap = 400, econ_cap = 600, nameplate HR = 7.0.
        config = ScenarioConfig()
        fleet, _ = bins_to_fleet(_bins(_bin_row()), ZONE_NAMES, config)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))

        self.assertAlmostEqual(committed.pmax_mw, 400.0, places=6)
        self.assertAlmostEqual(econ.pmax_mw, 600.0, places=6)
        # committed HR = 7.0 x 1.23 = 8.61; econ HR = 7.0 x 0.96 = 6.72.
        self.assertAlmostEqual(committed.heat_rate, 8.61, places=6)
        self.assertAlmostEqual(econ.heat_rate, 6.72, places=6)

        weighted = (
            committed.pmax_mw * committed.heat_rate
            + econ.pmax_mw * econ.heat_rate
        ) / (committed.pmax_mw + econ.pmax_mw)
        # (400 x 8.61 + 600 x 6.72) / 1000 = 7.476 -- intentionally above
        # the 7.0 nameplate: nameplate is a full-load rating, and real
        # dispatch is never 100% full-load every hour.
        self.assertAlmostEqual(weighted, 7.476, places=3)
        self.assertGreater(weighted, 7.0)


class TestTrancheMeritOrder(unittest.TestCase):
    """Cheaper econ capacity is dispatched ahead of pricier econ capacity."""

    def test_cheap_econ_dispatched_before_expensive_econ(self):
        # Bin A is a low-HR bin, bin B a high-HR bin. Both bins' committed
        # tranches are must-run (pmin = pmax) so they run regardless of
        # merit order; the dispatchable comparison is between the econ
        # tranches, and bin A's cheaper econ tranche must fill first.
        config = ScenarioConfig()
        bins = _bins(
            _bin_row(Bin_Number=1, Bin_Label="A", hr_weighted=6.0),
            _bin_row(Bin_Number=2, Bin_Label="B", hr_weighted=10.0),
        )
        fleet, _ = bins_to_fleet(bins, ZONE_NAMES, config)

        T = 24
        arrays = generators_to_fleet_arrays(fleet, ZONE_NAMES, hours=T)
        fuel_prices = np.full((1, T), 3.5)
        mc = assemble_mc(arrays, fuel_prices, carbon_price=0.0)

        committed_idx = [
            i for i, u in enumerate(arrays.unit_ids)
            if u.endswith("_committed")
        ]
        econ_idx = [
            i for i, u in enumerate(arrays.unit_ids) if u.endswith("_econ")
        ]
        # The cheaper econ tranche (bin A) has the lower heat rate.
        a_econ, b_econ = sorted(econ_idx, key=lambda i: arrays.heat_rate[i])

        # Demand: every committed tranche at its availability ceiling, plus
        # a slice that only the cheapest econ tranche need serve.
        forced = sum(
            arrays.pmax[i] * arrays.availability[i, 0]
            for i in committed_idx
        )
        zone = ZONE_NAMES.index("Houston")
        demand = np.zeros((len(ZONE_NAMES), T))
        demand[zone, :] = forced + 150.0

        result = solve_dispatch(
            arrays, demand, mc=mc, T=T,
            wind_cf=np.zeros((len(ZONE_NAMES), T)),
            wind_cap=np.zeros(len(ZONE_NAMES)),
            solar_cf=np.zeros((len(ZONE_NAMES), T)),
            solar_cap=np.zeros(len(ZONE_NAMES)),
        )

        # Committed tranches are must-run: dispatched in every hour.
        for i in committed_idx:
            self.assertTrue(np.all(result.dispatch[i] > 0.0))
        # Merit order: bin A's cheap econ tranche serves the incremental
        # load; bin B's pricier econ tranche stays idle.
        self.assertTrue(np.all(result.dispatch[a_econ] > 1.0))
        self.assertTrue(np.allclose(result.dispatch[b_econ], 0.0, atol=1e-6))


class TestCommitmentCoupling(unittest.TestCase):
    """Decommitting a bin shuts down both its committed and econ tranches."""

    def test_econ_tranche_follows_committed_decommit(self):
        config = ScenarioConfig()
        fleet, arrays = bins_to_fleet(
            _bins(_bin_row()), ZONE_NAMES, config
        )
        n_gen = len(fleet)
        T = 12
        arrays = generators_to_fleet_arrays(fleet, ZONE_NAMES, hours=T)

        committed_i = next(
            i for i, g in enumerate(fleet)
            if g.unit_id.endswith("_committed")
        )
        econ_i = next(
            i for i, g in enumerate(fleet) if g.unit_id.endswith("_econ")
        )

        # Commitment screen runs on the committed tranche only; the econ
        # tranche's own mask is all-committed (it is never screened).
        committed = np.ones((n_gen, T), dtype=bool)
        committed[committed_i, 4:8] = False  # a 4-hour decommit window

        out = apply_commitment_with_coal_pin(
            arrays, committed, np.zeros((n_gen, T)), fleet
        )

        # Both tranches are off in the decommitted window...
        self.assertTrue(np.all(out.availability[committed_i, 4:8] == 0.0))
        self.assertTrue(np.all(out.availability[econ_i, 4:8] == 0.0))
        # ...and both are available outside it.
        self.assertTrue(np.all(out.availability[committed_i, :4] > 0.0))
        self.assertTrue(np.all(out.availability[econ_i, :4] > 0.0))
        self.assertTrue(np.all(out.availability[committed_i, 8:] > 0.0))
        self.assertTrue(np.all(out.availability[econ_i, 8:] > 0.0))


class TestEmissionScaling(unittest.TestCase):
    """CO2 emission rate scales with each tranche's heat rate."""

    def test_emission_rate_ordering(self):
        config = ScenarioConfig()
        fleet, _ = bins_to_fleet(_bins(_bin_row()), ZONE_NAMES, config)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))

        base_rate = get_emission_rate("gas_cc", 7.0)
        # committed (HR x 1.23) emits more per MWh than the bin average,
        # econ (HR x 0.96) less -- CO2/MWh is proportional to fuel burned.
        self.assertGreater(committed.emission_rate_co2, base_rate)
        self.assertGreater(base_rate, econ.emission_rate_co2)
        self.assertAlmostEqual(
            committed.emission_rate_co2 / base_rate,
            config.cc_committed_hr_mult,
            places=6,
        )
        self.assertAlmostEqual(
            econ.emission_rate_co2 / base_rate,
            config.cc_econ_hr_mult,
            places=6,
        )


class TestCoalPaths(unittest.TestCase):
    """Coal through CAMPD binning is split; legacy take-or-pay is not."""

    def test_campd_coal_gets_committed_econ_split(self):
        config = ScenarioConfig()
        fleet, _ = bins_to_fleet(
            _bins(_bin_row(Plant_Group="COAL", hr_weighted=9.5)),
            ZONE_NAMES, config,
        )
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))
        self.assertAlmostEqual(
            committed.heat_rate, 9.5 * config.coal_committed_hr_mult, places=6
        )
        self.assertAlmostEqual(
            econ.heat_rate, 9.5 * config.coal_econ_hr_mult, places=6
        )
        self.assertEqual(committed.pmin_mw, committed.pmax_mw)
        self.assertEqual(econ.pmin_mw, 0.0)

    def test_legacy_coal_tranches_unchanged(self):
        config = ScenarioConfig()
        coal = Generator(
            unit_id="legacy_coal", name="legacy coal", zone="Houston",
            fuel_type="coal", pmax_mw=1000.0, pmin_mw=0.0, heat_rate=10.0,
        )
        expanded, _ = split_coal_tranches([coal], config)
        # Three take-or-pay tranches, every one at the unmodified heat rate
        # and with no Pmin floor -- the committed/econ split does not apply.
        self.assertEqual(len(expanded), 3)
        for ti, g in enumerate(expanded):
            self.assertTrue(g.unit_id.endswith(f"_t{ti + 1}"))
            self.assertEqual(g.heat_rate, 10.0)
            self.assertEqual(g.pmin_mw, 0.0)


if __name__ == "__main__":
    unittest.main()
