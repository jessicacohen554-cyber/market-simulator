"""Tests for the committed/economic two-tranche heat-rate split.

A CAMPD bin's base capacity is split into a Committed tranche (the
part-load range, heat rate above the bin average) and an Economic
tranche (the upper load range, heat rate below the bin average). No
tranche carries a Pmin floor. See
:func:`market_sim.data.fleet.bins_to_fleet`.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    assemble_mc,
    bins_to_fleet,
    generators_to_fleet_arrays,
    get_emission_rate,
)
from market_sim.model.commitment import apply_commitment_with_coal_pin
from market_sim.model.dispatch import solve_dispatch

ZONE_NAMES = get_iso_config("ERCOT").zone_names


def _bin_row(**overrides) -> dict:
    """Return one per-plant bin row, with no peaking tranche by default.

    The per-tranche heat rates default to the legacy CC config multipliers
    applied to ``hr_weighted`` so the tranche-merit assertions below have
    distinct values for committed vs econ. Override ``hr_mc`` / ``hr_econ``
    / ``hr_peak`` directly for non-CC bins.
    """
    hr = float(overrides.get("hr_weighted", 7.0))
    row = {
        "Plant_Group": "CC_REGULAR",
        "ERCOT_Zone": "Houston",
        "Bin_Number": 1,
        "Bin_Label": "T1",
        "Plant_Code": 1,
        "Plant_Name": "Test Plant",
        "capacity_mw": 1000.0,
        "hr_weighted": hr,
        "hr_mr": hr,
        "hr_mc": hr * 1.23,
        "hr_econ": hr * 0.96,
        "hr_peak": hr * 1.15,
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
            committed.pmax_mw * committed.heat_rate + econ.pmax_mw * econ.heat_rate
        ) / (committed.pmax_mw + econ.pmax_mw)
        # (400 x 8.61 + 600 x 6.72) / 1000 = 7.476 -- intentionally above
        # the 7.0 nameplate: nameplate is a full-load rating, and real
        # dispatch is never 100% full-load every hour.
        self.assertAlmostEqual(weighted, 7.476, places=3)
        self.assertGreater(weighted, 7.0)


class TestTrancheMeritOrder(unittest.TestCase):
    """The LP fills tranches strictly by heat-rate merit order."""

    def test_cheap_econ_dispatched_before_expensive_committed(self):
        # Bin A is a low-HR bin, bin B a high-HR bin. With no Pmin floor
        # every tranche is freely dispatchable, so the LP fills strictly
        # by merit order: bin A's cheap econ tranche before bin B's pricey
        # committed tranche.
        config = ScenarioConfig()
        bins = _bins(
            _bin_row(
                Bin_Number=1,
                Bin_Label="A",
                Plant_Code=1001,
                hr_weighted=6.0,
            ),
            _bin_row(
                Bin_Number=2,
                Bin_Label="B",
                Plant_Code=1002,
                hr_weighted=10.0,
            ),
        )
        fleet, _ = bins_to_fleet(bins, ZONE_NAMES, config)

        T = 24
        arrays = generators_to_fleet_arrays(fleet, ZONE_NAMES, hours=T)
        fuel_prices = np.full((1, T), 3.5)
        mc = assemble_mc(arrays, fuel_prices, carbon_price=0.0)

        # Bin A's econ tranche is the globally cheapest (lowest HR); bin
        # B's committed tranche is the globally priciest (highest HR).
        a_econ = int(np.argmin(arrays.heat_rate))
        b_committed = int(np.argmax(arrays.heat_rate))
        self.assertTrue(arrays.unit_ids[a_econ].endswith("_econ"))
        self.assertTrue(arrays.unit_ids[b_committed].endswith("_committed"))

        # Demand small enough that the pricey committed tranche is not
        # needed -- only cheaper tranches clear it.
        zone = ZONE_NAMES.index("Houston")
        demand = np.zeros((len(ZONE_NAMES), T))
        demand[zone, :] = 800.0

        result = solve_dispatch(
            arrays,
            demand,
            mc=mc,
            T=T,
            wind_cf=np.zeros((len(ZONE_NAMES), T)),
            wind_cap=np.zeros(len(ZONE_NAMES)),
            solar_cf=np.zeros((len(ZONE_NAMES), T)),
            solar_cap=np.zeros(len(ZONE_NAMES)),
        )

        # The cheap econ tranche serves load; the pricey committed tranche
        # stays idle -- A_econ is dispatched before B_committed.
        self.assertTrue(np.all(result.dispatch[a_econ] > 1.0))
        self.assertTrue(np.allclose(result.dispatch[b_committed], 0.0, atol=1e-6))


class TestCommitmentCoupling(unittest.TestCase):
    """Decommitting a bin shuts down both its committed and econ tranches."""

    def test_econ_tranche_follows_committed_decommit(self):
        config = ScenarioConfig()
        fleet, arrays = bins_to_fleet(_bins(_bin_row()), ZONE_NAMES, config)
        n_gen = len(fleet)
        T = 12
        arrays = generators_to_fleet_arrays(fleet, ZONE_NAMES, hours=T)

        committed_i = next(
            i for i, g in enumerate(fleet) if g.unit_id.endswith("_committed")
        )
        econ_i = next(i for i, g in enumerate(fleet) if g.unit_id.endswith("_econ"))

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

    def test_emission_rate_is_invariant_across_tranches(self):
        """Every tranche of a plant books CO2 at its PHYSICAL heat rate.

        Re-adjudicated 2026-07-26 (fast-tier §6.3). This test previously
        asserted the OPPOSITE — that the committed tranche's CO2/MWh exceeds
        the bin average by ``cc_committed_hr_mult`` and the econ tranche's
        falls below it by ``cc_econ_hr_mult`` — and was xfailed as an uncited
        "pre-existing failure" when the assertion started failing. The
        assertion was the defect: R2/EM-4 corrected ``bins_to_fleet`` to book
        ``emission_rate_co2`` at ``base_hr`` (the plant's physical heat rate),
        never at the bid-tranche heat rate ``tr_hr``, because ``tr_hr`` carries
        the OFFER-CURVE pricing multipliers (peak x2.0-2.5, committed x0.92 —
        docs/binning-methodology.md) that shape the bid stack. A plant's CO2
        per MWh does not change because a block is offered at a scarcity price.
        Keeping the old xfail preserved a physics error as the expected
        behaviour; this inverts it into the guard the correction deserves.
        (CEMS-covered plants are overwritten later with their measured rate by
        ``apply_plant_emission_rates``; this base_hr value is the physical
        default for uncovered plants and entrants.)
        """
        config = ScenarioConfig()
        fleet, _ = bins_to_fleet(_bins(_bin_row()), ZONE_NAMES, config)
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))

        base_rate = get_emission_rate("gas_cc", 7.0)
        # The BID heat rates still diverge (that is the offer curve's job) ...
        self.assertAlmostEqual(
            committed.heat_rate / 7.0, config.cc_committed_hr_mult, places=6
        )
        self.assertAlmostEqual(econ.heat_rate / 7.0, config.cc_econ_hr_mult, places=6)
        # ... while CO2/MWh stays pinned to the plant's physical heat rate.
        self.assertAlmostEqual(committed.emission_rate_co2, base_rate, places=9)
        self.assertAlmostEqual(econ.emission_rate_co2, base_rate, places=9)


class TestCoalPaths(unittest.TestCase):
    """Coal through CAMPD binning is split; legacy take-or-pay is not."""

    def test_campd_coal_gets_committed_econ_split(self):
        config = ScenarioConfig()
        # CSV-driven HRs: COAL HR_Mult_Committed=1.15, HR_Mult_Economic=1.0
        # for the latest bin file.
        fleet, _ = bins_to_fleet(
            _bins(
                _bin_row(
                    Plant_Group="COAL_PRB",
                    hr_weighted=9.5,
                    hr_mc=9.5 * 1.15,
                    hr_econ=9.5,
                    hr_peak=9.5 * 1.05,
                )
            ),
            ZONE_NAMES,
            config,
        )
        committed = next(g for g in fleet if g.unit_id.endswith("_committed"))
        econ = next(g for g in fleet if g.unit_id.endswith("_econ"))
        self.assertAlmostEqual(committed.heat_rate, 9.5 * 1.15, places=6)
        self.assertAlmostEqual(econ.heat_rate, 9.5, places=6)
        self.assertEqual(committed.pmin_mw, 0.0)
        self.assertEqual(econ.pmin_mw, 0.0)

    # test_legacy_coal_tranches_unchanged deleted 2026-08-12 with
    # split_coal_tranches itself (rule 26 [R-DELETE], ercot-188 G#3 owner
    # ruling): the legacy non-CAMPD coal split no longer exists — the
    # non-CAMPD fallback passes coal through unsplit.


if __name__ == "__main__":
    unittest.main()
