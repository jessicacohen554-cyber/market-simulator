"""Tests for the PJM measured per-seam Q-Q band-price ladders.

``inject_pjm_seam_ladder_prices`` overwrites every reference-price seam band
(MISO / NYISO / Carolinas / TVA / LGEE, import + export) with its per-year
measured band price from ``interchange_config.PJM_SEAM_LADDER_BY_YEAR`` (the
revealed seam supply curve, ``scripts/data/derive_pjm_seam_ladders.py``). Bands
keep clearing economically on the model's own hourly price; availability (the
measured seam envelopes) is untouched, and the firm scheduled-export floor is
displaced on ladder years (rule 19 — alternatives, never stacked). Mirrors
``test_miso_seam_ladder.py``.
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    INTERFACE_NEIGHBORS,
    PJM_SEAM_LADDER_BY_YEAR,
    PJM_SEAM_TIE,
)
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_pjm_seam_ladder_prices,
)

T = 48  # trivial clock first — the injector is hour-constant per band


class TestLadderRegistry(unittest.TestCase):
    """The measured ladder registry is complete, ordered, and wash-free."""

    def test_every_backcast_year_covers_every_seam_and_band(self):
        seams = {n.name for n in INTERFACE_NEIGHBORS["PJM"]}
        for year in (2023, 2024, 2025):
            self.assertIn(year, PJM_SEAM_LADDER_BY_YEAR)
            ladder = PJM_SEAM_LADDER_BY_YEAR[year]
            self.assertEqual(set(ladder), seams)
            for seam, sides in ladder.items():
                self.assertEqual(
                    len(sides["import"]), SEAM_FLOW_TRANCHES, msg=f"{year} {seam}"
                )
                self.assertEqual(
                    len(sides["export"]), SEAM_FLOW_TRANCHES, msg=f"{year} {seam}"
                )

    def test_seam_tie_map_covers_every_priced_seam(self):
        # The tie→seam pooling registry names exactly the priced seams (the
        # derive script hard-fails on a tie absent from it, so drift between
        # the map and the neighbor registry would break the derivation).
        self.assertEqual(
            set(PJM_SEAM_TIE), {n.name for n in INTERFACE_NEIGHBORS["PJM"]}
        )
        all_ties = [t for ties in PJM_SEAM_TIE.values() for t in ties]
        self.assertEqual(len(all_ties), len(set(all_ties)), "tie mapped twice")

    def test_import_ladders_rise_and_export_ladders_fall(self):
        # A supply curve: deeper import bands cost weakly more; deeper export
        # bands pay weakly less (both are duration-coupled quantiles).
        for year, ladder in PJM_SEAM_LADDER_BY_YEAR.items():
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
        for year, ladder in PJM_SEAM_LADDER_BY_YEAR.items():
            for seam, sides in ladder.items():
                self.assertLess(
                    max(sides["export"]),
                    min(sides["import"]),
                    msg=f"{year} {seam} wash ordering violated",
                )


class TestLadderInjection(unittest.TestCase):
    """``inject_pjm_seam_ladder_prices`` reprices bands, touches nothing else."""

    def _fleet_and_mc(self):
        node = build_reference_price_node("PJM")
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
        mc = np.full((len(node), T), -123.0)  # sentinel: formula-priced rows
        return fleet, mc

    def test_bands_take_their_ladder_price(self):
        fleet, mc = self._fleet_and_mc()
        self.assertTrue(inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2023))
        ladder = PJM_SEAM_LADDER_BY_YEAR[2023]
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

    def test_2023_miso_base_export_band_is_the_derived_value(self):
        # Spot-check the headline number: the 2023 MISO base export band is
        # the $72.78 revealed threshold — the seam exports its first 912 MW
        # whenever PJM's own price is below it (99.6% of hours), encoding the
        # measured near-always-export record economically.
        fleet, mc = self._fleet_and_mc()
        inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2023)
        row = next(
            r
            for r, uid in enumerate(fleet.unit_ids)
            if uid.endswith(f"{_REF_EXPORT_MARK}MISO#1")
        )
        np.testing.assert_allclose(mc[row, :], 72.78)

    def test_availability_untouched(self):
        fleet, mc = self._fleet_and_mc()
        before = fleet.availability.copy()
        inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2023)
        np.testing.assert_array_equal(fleet.availability, before)

    def test_noop_off_scope(self):
        # Non-PJM ISO and a year outside the registry (forecast) both no-op.
        fleet, mc = self._fleet_and_mc()
        before = mc.copy()
        self.assertFalse(inject_pjm_seam_ladder_prices(fleet, mc, "MISO", 2023))
        self.assertFalse(inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2030))
        np.testing.assert_array_equal(mc, before)

    def test_non_seam_rows_untouched(self):
        fleet, mc = self._fleet_and_mc()
        # Graft a non-seam sentinel row id in place, keeping shapes aligned.
        fleet.unit_ids[0] = "PJM_external_import_scarcity_1"
        inject_pjm_seam_ladder_prices(fleet, mc, "PJM", 2023)
        np.testing.assert_array_equal(mc[0, :], -123.0)


class TestFirmExportFloorDisplacement(unittest.TestCase):
    """The ladder displaces the firm scheduled-export floor on ladder years."""

    def _config(self, ladder_on: bool):
        from market_sim.config.scenarios import ScenarioConfig

        return ScenarioConfig(
            iso="PJM",
            mode="backcast",
            reference_price_interface=True,
            pjm_seam_measured_ladder=ladder_on,
        )

    def _apply(self, ladder_on: bool):
        from market_sim.model.transmission import apply_interchange_injections

        node = build_reference_price_node("PJM")
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
        mc = np.zeros((len(node), T))
        apply_interchange_injections(fleet, mc, self._config(ladder_on), "PJM", 2023)
        return fleet

    def test_floor_pins_export_bands_without_ladder(self):
        # 2023 carries firm floors (MISO 1250 MW, NYISO 900 MW): without the
        # ladder the cheapest export bands are forced (pmax < 0).
        fleet = self._apply(ladder_on=False)
        pinned = [
            uid
            for r, uid in enumerate(fleet.unit_ids)
            if _REF_EXPORT_MARK in uid and fleet.pmax[r] < 0.0
        ]
        self.assertTrue(pinned, "expected the 2023 firm export floor to pin bands")

    def test_ladder_displaces_the_floor(self):
        # With the measured ladder on, no export band is forced — the firm
        # base clears economically through the ladder prices (rule 19).
        fleet = self._apply(ladder_on=True)
        pinned = [
            uid
            for r, uid in enumerate(fleet.unit_ids)
            if _REF_EXPORT_MARK in uid and fleet.pmax[r] < 0.0
        ]
        self.assertEqual(pinned, [], "ladder must displace the firm export floor")


if __name__ == "__main__":
    unittest.main()
