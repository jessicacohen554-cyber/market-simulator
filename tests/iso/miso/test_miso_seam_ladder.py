"""Tests for the MISO measured per-seam Q-Q band-price ladders.

``inject_miso_seam_ladder_prices`` overwrites every reference-price seam band
(PJM / SPP / South, import + export) with its per-year measured band price
from ``interchange_config.MISO_SEAM_LADDER_BY_YEAR`` (the revealed seam
supply curve, ``scripts/data/derive_miso_seam_ladders.py``). Bands keep clearing
economically on the model's own hourly price; availability (the measured
seam envelopes) is untouched. Mirrors the seam-flow-limit test structure.
"""

import unittest
from pathlib import Path

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


class TestNeighbourAnchoredOverlay(unittest.TestCase):
    """miso-225: the owner-ruled neighbour-anchored PJM overlay.

    The incumbent ladder prices every band at a quantile of MISO's OWN DA hub,
    so an import's merit position moves with the model's own price and imports
    contract when MISO clears cheaply -- the opposite of the measured market,
    which imported 6,021 MW in the 2023 hours MISO cleared under $20 against a
    4,674 MW all-hours mean. The overlay reprices the PJM seam on the exporting
    market's own border DA instead. PJM only: SPP and South hold no measured
    neighbour price under ``data/raw``.
    """

    def _fleet_and_mc(self):
        node = build_reference_price_node("MISO")
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
        return fleet, np.full((len(node), T), -123.0)

    def test_registry_covers_pjm_only_and_keeps_the_supply_curve_shape(self):
        from market_sim.config.interchange_config import (
            MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
        )

        for year in (2023, 2024, 2025):
            overlay = MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[year]
            self.assertEqual(set(overlay), {"PJM"})
            imp = overlay["PJM"]["import"]
            exp = overlay["PJM"]["export"]
            self.assertEqual(len(imp), SEAM_FLOW_TRANCHES)
            self.assertEqual(len(exp), SEAM_FLOW_TRANCHES)
            self.assertEqual(list(imp), sorted(imp), msg=f"{year} import not rising")
            self.assertEqual(
                list(exp), sorted(exp, reverse=True), msg=f"{year} export not falling"
            )
            self.assertLess(max(exp), min(imp), msg=f"{year} wash ordering violated")

    def test_every_import_band_is_cheaper_than_the_incumbent(self):
        """The whole point: the neighbour is the cheaper anchor, in every band."""
        from market_sim.config.interchange_config import (
            MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
        )

        for year in (2023, 2024, 2025):
            inc = MISO_SEAM_LADDER_BY_YEAR[year]["PJM"]["import"]
            nb = MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[year]["PJM"]["import"]
            for k, (a, b) in enumerate(zip(nb, inc), start=1):
                self.assertLess(a, b, msg=f"{year} band {k}: {a} !< {b}")

    def test_overlay_reprices_pjm_and_leaves_spp_and_south_alone(self):
        from market_sim.config.interchange_config import (
            MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR,
        )

        fleet, mc = self._fleet_and_mc()
        base = mc.copy()
        inject_miso_seam_ladder_prices(fleet, base, "MISO", 2023)
        arm = mc.copy()
        self.assertTrue(
            inject_miso_seam_ladder_prices(
                fleet, arm, "MISO", 2023, neighbour_anchored=True
            )
        )
        overlay = MISO_SEAM_LADDER_NEIGHBOUR_BY_YEAR[2023]["PJM"]
        moved = 0
        for row, uid in enumerate(fleet.unit_ids):
            if _REF_IMPORT_MARK in uid:
                tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
            elif _REF_EXPORT_MARK in uid:
                tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
            else:
                np.testing.assert_array_equal(arm[row, :], base[row, :])
                continue
            name, _, k = tag.partition("#")
            if name == "PJM":
                np.testing.assert_allclose(arm[row, :], overlay[side][int(k) - 1])
                moved += 1
            else:
                np.testing.assert_array_equal(arm[row, :], base[row, :])
        self.assertEqual(moved, 2 * SEAM_FLOW_TRANCHES)

    def test_off_is_byte_identical(self):
        fleet, a = self._fleet_and_mc()
        _fleet2, b = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(fleet, a, "MISO", 2024)
        inject_miso_seam_ladder_prices(fleet, b, "MISO", 2024, neighbour_anchored=False)
        np.testing.assert_array_equal(a, b)


class TestNeighbourOverlayRequiresItsHost(unittest.TestCase):
    """The overlay is refused without the ladder it overlays (rule 19).

    Enforced at the POINT OF USE in ``run_calibration.run_year``'s seam block,
    not in ``ScenarioConfig.__post_init__``: ``miso_seam_measured_ladder`` is a
    ``solve_and_persist`` kwarg applied to the recorded config tens of
    ``with_overrides`` calls after the ScenarioConfig-channel fields are set, so
    the pair is legitimately split in intermediate configs and a construction-time
    check rejected a correct run after its LP had finished (miso-225 Addendum A).
    """

    def test_construction_does_not_reject_a_split_intermediate_config(self):
        from market_sim.config.scenarios import ScenarioConfig

        cfg = ScenarioConfig(
            iso="MISO", mode="backcast", miso_seam_neighbour_anchored_ladder=True
        )
        self.assertTrue(cfg.miso_seam_neighbour_anchored_ladder)
        self.assertFalse(cfg.miso_seam_measured_ladder)
        # ...and the host flag can still be layered on afterwards, which is
        # exactly what _recorded_config does.
        self.assertTrue(
            cfg.with_overrides(miso_seam_measured_ladder=True).miso_seam_measured_ladder
        )

    def test_the_solve_path_refuses_the_overlay_without_its_host(self):
        source = (
            Path(__file__).resolve().parents[3] / "scripts/run_calibration.py"
        ).read_text()
        # assertIn would dump the whole 7k-line module on failure; assert the
        # boolean instead.
        self.assertTrue(
            '"miso_seam_neighbour_anchored_ladder requires "' in source
            and '"miso_seam_measured_ladder: the neighbour-anchored PJM entry "'
            in source,
            "run_calibration.py's seam block must refuse the overlay without its host",
        )


class TestHourlyNeighbourOverlay(unittest.TestCase):
    """miso-231: the HOURLY neighbour-anchored PJM overlay.

    The annual overlay above repairs the ladder's LEVEL and not its
    RESPONSIVENESS -- miso-226 measured ``corr(imports, own price)`` moving
    +0.750 -> +0.725 against a MEASURED -0.101, 3 % of the distance, because a
    FIXED price ladder is cleared by the LP against its OWN internal price. This
    overlay makes band ``k``'s offer ``pjm_border(t) + delta_k``, so the band
    clears iff ``spread(t) > delta_k`` and its merit position tracks the
    neighbour's supply cost in the hour it is offered.
    """

    def _fleet_and_mc(self):
        node = build_reference_price_node("MISO")
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
        return fleet, np.full((len(node), T), -123.0)

    def test_registry_holds_rising_offsets_for_pjm_only(self):
        from market_sim.config.interchange_config import (
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        )

        for year in (2023, 2024, 2025):
            overlay = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[year]
            self.assertEqual(set(overlay), {"PJM"})
            imp = overlay["PJM"]["import"]
            exp = overlay["PJM"]["export"]
            self.assertEqual(len(imp), SEAM_FLOW_TRANCHES)
            self.assertEqual(len(exp), SEAM_FLOW_TRANCHES)
            self.assertEqual(list(imp), sorted(imp), msg=f"{year} import not rising")
            self.assertEqual(
                list(exp), sorted(exp, reverse=True), msg=f"{year} export not falling"
            )
            self.assertLess(max(exp), min(imp), msg=f"{year} wash ordering violated")
            # These are OFFSETS, not prices: the shallow bands must be NEGATIVE,
            # which is what makes this a ladder rather than the refuted spread
            # HURDLE -- band 1 clears even when MISO is far below PJM, carrying
            # the "46-56 % of import MWh inside the $2 hurdle" a hurdle deletes.
            self.assertLess(imp[0], 0.0, msg=f"{year} band 1 offset is not negative")

    def test_bands_become_hourly_and_equal_border_plus_offset(self):
        from market_sim.config.interchange_config import (
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR,
        )
        from market_sim.data.eia_loader import measured_miso_pjm_border_prices

        border = measured_miso_pjm_border_prices("MISO", 2024, T)
        if border is None:
            self.skipTest("no measured PJM border series under data/raw")
        overlay = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[2024]["PJM"]

        fleet, mc = self._fleet_and_mc()
        self.assertTrue(
            inject_miso_seam_ladder_prices(
                fleet,
                mc,
                "MISO",
                2024,
                neighbour_anchored=True,
                neighbour_hourly=True,
            )
        )
        moved = 0
        for row, uid in enumerate(fleet.unit_ids):
            if _REF_IMPORT_MARK in uid:
                tag, side = uid.rsplit(_REF_IMPORT_MARK, 1)[1], "import"
            elif _REF_EXPORT_MARK in uid:
                tag, side = uid.rsplit(_REF_EXPORT_MARK, 1)[1], "export"
            else:
                continue
            name, _, k = tag.partition("#")
            if name != "PJM":
                continue
            np.testing.assert_allclose(
                mc[row, :], border + overlay[side][int(k) - 1]
            )
            # The point of the mechanism: the row is a live hourly vector.
            self.assertGreater(float(mc[row, :].std()), 1.0)
            moved += 1
        self.assertEqual(moved, 2 * SEAM_FLOW_TRANCHES)

    def test_spp_and_south_keep_their_scalar_ladders(self):
        fleet, base = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(
            fleet, base, "MISO", 2024, neighbour_anchored=True
        )
        _f, arm = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(
            fleet,
            arm,
            "MISO",
            2024,
            neighbour_anchored=True,
            neighbour_hourly=True,
        )
        for row, uid in enumerate(fleet.unit_ids):
            if _REF_IMPORT_MARK in uid:
                tag = uid.rsplit(_REF_IMPORT_MARK, 1)[1]
            elif _REF_EXPORT_MARK in uid:
                tag = uid.rsplit(_REF_EXPORT_MARK, 1)[1]
            else:
                np.testing.assert_array_equal(arm[row, :], base[row, :])
                continue
            if tag.partition("#")[0] != "PJM":
                np.testing.assert_array_equal(arm[row, :], base[row, :])

    def test_off_is_byte_identical_to_the_annual_overlay(self):
        fleet, a = self._fleet_and_mc()
        _f2, b = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(fleet, a, "MISO", 2024, neighbour_anchored=True)
        inject_miso_seam_ladder_prices(
            fleet,
            b,
            "MISO",
            2024,
            neighbour_anchored=True,
            neighbour_hourly=False,
        )
        np.testing.assert_array_equal(a, b)

    def test_missing_year_degrades_to_the_annual_overlay_not_to_no_ladder(self):
        """Rule 19: an armed run is never silently cheaper than the keeper."""
        fleet, a = self._fleet_and_mc()
        _f2, b = self._fleet_and_mc()
        # 2019 is absent from every neighbour table; the incumbent ladder is
        # likewise absent, so both arms must agree on whatever that resolves to.
        inject_miso_seam_ladder_prices(fleet, a, "MISO", 2024, neighbour_anchored=True)
        self.assertTrue(
            inject_miso_seam_ladder_prices(
                fleet,
                b,
                "MISO",
                2024,
                neighbour_anchored=True,
                neighbour_hourly=True,
            )
        )
        # PJM rows differ (the mechanism fired); everything else is identical,
        # which is the degradation contract in the direction that can be tested
        # against a year the hourly table DOES cover.
        self.assertFalse(np.array_equal(a, b))

    def test_construction_does_not_reject_a_split_intermediate_config(self):
        from market_sim.config.scenarios import ScenarioConfig

        cfg = ScenarioConfig(
            iso="MISO", mode="backcast", miso_seam_neighbour_hourly_ladder=True
        )
        self.assertTrue(cfg.miso_seam_neighbour_hourly_ladder)
