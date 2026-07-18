"""Tests for the MISO measured per-seam Q-Q band-price ladders.

``inject_miso_seam_ladder_prices`` overwrites every reference-price seam band
(PJM / SPP / South, import + export) with its per-year measured band price
from ``interchange_config.MISO_SEAM_LADDER_BY_YEAR`` (the revealed seam
supply curve, ``scripts/data/derive_miso_seam_ladders.py``). Bands keep clearing
economically on the model's own hourly price; availability (the measured
seam envelopes) is untouched. Mirrors the seam-flow-limit test structure.
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    INTERFACE_NEIGHBORS,
    MISO_MANITOBA_SEAM_SPEC,
    MISO_SEAM_LADDER_BY_YEAR,
)
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_miso_seam_ladder_prices,
)

T = 48  # trivial clock first — the injector is hour-constant per band


class TestLadderRegistry(unittest.TestCase):
    """The measured ladder registry is complete, ordered, and wash-free."""

    def test_every_backcast_year_covers_every_seam_and_band(self):
        # The three registry seams plus the Manitoba two-way seam (miso-74),
        # whose spec lives outside INTERFACE_NEIGHBORS (built only under
        # ScenarioConfig.miso_manitoba_seam) but whose ladder is always present.
        seams = {n.name for n in INTERFACE_NEIGHBORS["MISO"]} | {
            MISO_MANITOBA_SEAM_SPEC.name
        }
        for year in (2023, 2024, 2025):
            self.assertIn(year, MISO_SEAM_LADDER_BY_YEAR)
            ladder = MISO_SEAM_LADDER_BY_YEAR[year]
            self.assertEqual(set(ladder), seams)
            for seam, sides in ladder.items():
                self.assertEqual(
                    len(sides["import"]), SEAM_FLOW_TRANCHES, msg=f"{year} {seam}"
                )
                self.assertEqual(
                    len(sides["export"]), SEAM_FLOW_TRANCHES, msg=f"{year} {seam}"
                )

    def test_import_ladders_rise_and_export_ladders_fall(self):
        # A supply curve: deeper import bands cost weakly more; deeper export
        # bands pay weakly less (both are duration-coupled quantiles).
        for year, ladder in MISO_SEAM_LADDER_BY_YEAR.items():
            for seam, sides in ladder.items():
                imp, exp = sides["import"], sides["export"]
                self.assertEqual(
                    list(imp), sorted(imp), msg=f"{year} {seam} import not rising"
                )
                self.assertEqual(
                    list(exp),
                    sorted(exp, reverse=True),
                    msg=f"{year} {seam} export not falling",
                )

    def test_same_seam_no_wash_ordering(self):
        # Every export band strictly below the seam's cheapest import band —
        # a seam cannot deeply import and export at once (rule-14 note in the
        # registry comment; holds naturally in the measured record).
        for year, ladder in MISO_SEAM_LADDER_BY_YEAR.items():
            for seam, sides in ladder.items():
                self.assertLess(
                    max(sides["export"]),
                    min(sides["import"]),
                    msg=f"{year} {seam} wash ordering violated",
                )


class TestLadderInjection(unittest.TestCase):
    """``inject_miso_seam_ladder_prices`` reprices bands, touches nothing else."""

    def _fleet_and_mc(self):
        node = build_reference_price_node("MISO")
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
        mc = np.full((len(node), T), -123.0)  # sentinel: formula-priced rows
        return fleet, mc

    def test_bands_take_their_ladder_price(self):
        fleet, mc = self._fleet_and_mc()
        self.assertTrue(inject_miso_seam_ladder_prices(fleet, mc, "MISO", 2025))
        ladder = MISO_SEAM_LADDER_BY_YEAR[2025]
        for row, uid in enumerate(fleet.unit_ids):
            if _REF_IMPORT_MARK in uid:
                tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
            elif _REF_EXPORT_MARK in uid:
                tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
            else:
                continue
            name, _, k = tag.partition("#")
            expected = ladder[name][side][int(k) - 1]
            np.testing.assert_allclose(mc[row, :], expected)

    def test_pjm_2025_base_band_is_the_derived_value(self):
        # Spot-check the headline number: the 2025 PJM base import band is the
        # $21.82 revealed threshold (flows ~always vs the $43.73 DA mean).
        fleet, mc = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(fleet, mc, "MISO", 2025)
        row = next(
            r
            for r, uid in enumerate(fleet.unit_ids)
            if uid.endswith(f"{_REF_IMPORT_MARK}PJM#1")
        )
        np.testing.assert_allclose(mc[row, :], 21.82)

    def test_availability_untouched(self):
        fleet, mc = self._fleet_and_mc()
        before = fleet.availability.copy()
        inject_miso_seam_ladder_prices(fleet, mc, "MISO", 2025)
        np.testing.assert_array_equal(fleet.availability, before)

    def test_noop_off_scope(self):
        # Non-MISO ISO and a year outside the registry (forecast) both no-op.
        fleet, mc = self._fleet_and_mc()
        before = mc.copy()
        self.assertFalse(inject_miso_seam_ladder_prices(fleet, mc, "PJM", 2025))
        self.assertFalse(inject_miso_seam_ladder_prices(fleet, mc, "MISO", 2030))
        np.testing.assert_array_equal(mc, before)

    def test_non_seam_rows_untouched(self):
        fleet, mc = self._fleet_and_mc()
        # Graft a non-seam sentinel row id in place, keeping shapes aligned.
        fleet.unit_ids[0] = "MISO-West_Manitoba_firmhydro"
        inject_miso_seam_ladder_prices(fleet, mc, "MISO", 2025)
        np.testing.assert_array_equal(mc[0, :], -123.0)


if __name__ == "__main__":
    unittest.main()
