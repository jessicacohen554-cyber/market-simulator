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
        # 2022 armed by miso-252, 2020 + 2021 by miso-260 — the whole
        # backcast span the ISO scores, so an unarmed year cannot reappear
        # silently and drop its seams back onto the flat gas-elastic
        # reference price (miso-252 §2.4's bang-bang).
        for year in (2020, 2021, 2022, 2023, 2024, 2025):
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

    def test_incumbent_registry_reproduces_the_frozen_derivation(self):
        """Rule 23 ``[R-FROZEN-DERIVE]``: the committed per-year ladder IS the
        output of its own derive, except at three pinned, known entries.

        THE GAP THIS CLOSES (miso-244).  Until 2026-09-08 this table was the
        only MISO seam ladder with no test that re-ran ``derive()`` and
        compared — the registry carried shape, monotonicity, no-wash ordering
        and one spot value, while the reproduce-the-derivation pin beside it
        covers the SPP HOURLY offsets alone.  A divergence between the
        committed table and its own estimator could therefore sit unseen, and
        one did: miso-243 reported it as per-seam maxima and could not fix it
        (a different object, outside that session's queue item).

        WHAT IS PINNED.  All 384 entries reproduce at ``atol=0.005`` — a half
        cent, the SPP-hourly pin's own bar — with NO exceptions.  (192 when
        this test was written over 2023-2025; 256 once miso-252 armed 2022;
        384 since miso-260 armed 2020 + 2021 on the same frozen estimator,
        which reproduced every previously-committed entry at max |diff|
        0.0000 — the evidence that the back-fill changed no armed year.)

        THE TABLE WAS RECONCILED BY miso-245 (2026-09-08).  miso-244 found
        three entries adrift from their own ``derive()`` by exactly one cent
        (2023 PJM import 5, 2023 South export 4, 2024 South export 5), pinned
        them at both values and REFUSED the re-derive: the gap is not a
        rounding tie (``t_max`` 0.0049998 against a 1e-4 bar) and not a
        no-wash clamp (none fires in any year), and its cause was
        unattributed, so rule 23 ``[R-FROZEN-DERIVE]`` had nothing to cite.
        miso-245 attributed it — each committed value is reached from the
        HEAD sample by perturbing that entry's own integer duration count by
        exactly ONE hour of 8,760, with the sign quantile monotonicity
        requires — and reconciled the three entries to the frozen
        estimator's output on the current source data (rule 14
        ``[R-ACCURATE]``, zero free parameters).  The exception list is
        DELETED rather than zeroed (rule 26 ``[R-DELETE]``).

        **Never widen ``atol`` to absorb a future drift, and never re-add an
        exception list** — that rebuilds exactly the blindness this test
        exists to remove.  A new divergence is a source-data change to be
        diagnosed and cited, not a tolerance.
        """
        import importlib.util

        repo = Path(__file__).resolve().parents[3]
        script = repo / "scripts/data/derive_miso_seam_ladders.py"
        if not script.exists():
            self.skipTest("derive script unavailable")
        spec = importlib.util.spec_from_file_location("_derive_miso_seam", script)
        dm = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(dm)
            joined = dm.load_joined()
        except Exception:  # pragma: no cover - source data not hydrated
            self.skipTest("measured seam/LMP series not available")
        for year, ladder in MISO_SEAM_LADDER_BY_YEAR.items():
            derived, _notes = dm.derive(joined.loc[[year]])
            self.assertEqual(set(derived), set(ladder), msg=f"{year} seam set")
            for seam, sides in ladder.items():
                for side in ("import", "export"):
                    for k, committed in enumerate(sides[side]):
                        got = float(derived[seam][side][k])
                        self.assertAlmostEqual(
                            got,
                            float(committed),
                            delta=0.005,
                            msg=(
                                f"{year} {seam} {side} band {k + 1} drifted from "
                                "its own derivation (rule 23 [R-FROZEN-DERIVE])"
                            ),
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
            np.testing.assert_allclose(mc[row, :], border + overlay[side][int(k) - 1])
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


class TestHourlySppOverlay(unittest.TestCase):
    """miso-233: the hourly neighbour anchor extended to the SECOND seam, SPP.

    A SUB-GATE of :class:`TestHourlyNeighbourOverlay`'s mechanism, never one
    beside it (rule 19 ``[R-ONE-MECH]``): the SPP entry rides the same per-seam
    ``hourly_anchor`` mapping and is refused without its parent. Its object is
    the miso-233 phase-0 attribution — under the miso-232 keeper the repaired
    PJM seam is already STEEPER than the measured PJM seam, and what cancels it
    is SPP and South still clearing a FIXED ladder against the model's own
    price. SOUTH stays uncovered: SOCO/TVA publish no hub price.
    """

    def _fleet_and_mc(self):
        node = build_reference_price_node("MISO")
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=T)
        return fleet, np.full((len(node), T), -123.0)

    def test_registry_holds_rising_offsets_for_spp_only(self):
        from market_sim.model.interchange.spec import (
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
        )

        for year in (2023, 2024, 2025):
            overlay = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[year]
            self.assertEqual(set(overlay), {"SPP"})
            imp = overlay["SPP"]["import"]
            exp = overlay["SPP"]["export"]
            self.assertEqual(len(imp), SEAM_FLOW_TRANCHES)
            self.assertEqual(len(exp), SEAM_FLOW_TRANCHES)
            self.assertEqual(list(imp), sorted(imp), msg=f"{year} import not rising")
            self.assertEqual(
                list(exp), sorted(exp, reverse=True), msg=f"{year} export not falling"
            )
            self.assertLess(max(exp), min(imp), msg=f"{year} wash ordering violated")

    def test_registry_reproduces_the_frozen_derivation(self):
        """Rule 23 ``[R-FROZEN-DERIVE]``: the table IS the derive's output.

        Recomputes the ladder with ``derive_spp_neighbour_hourly`` on the same
        committed measured series and pins it byte-for-byte to the registry, so
        a hand-edited offset (or a silently re-tuned one) fails here rather
        than reaching a solve.

        **This test is also a CORRECTNESS pin as of miso-243, and it was not
        before.** It previously passed ``joined.loc[year]``, whose index is
        ``hour`` alone, into a derive that joins a ``(year, hour)``-MultiIndexed
        hub series -- so pandas partial-joined on the shared level, the sample
        was replicated across all three hub years, and the test compared the
        committed table against that same mispaired output and agreed with it.
        It pinned CONSISTENCY, which is what rule 23 asks, but could not see a
        defect in the join itself. It now passes ``joined.loc[[year]]`` (the
        MultiIndex survives, so the join pairs within the year) and
        additionally asserts the JOIN'S ROW COUNT, which is the assertion that
        would have caught the defect. The same invariant is enforced inside
        ``derive_spp_neighbour_hourly`` itself, so no caller can reintroduce it.
        """
        import importlib.util
        from pathlib import Path

        from market_sim.model.interchange.spec import (
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
        )

        repo = Path(__file__).resolve().parents[3]
        script = repo / "scripts/data/derive_miso_seam_ladders.py"
        if not script.exists():
            self.skipTest("derive script unavailable")
        spec = importlib.util.spec_from_file_location("_derive_miso_seam", script)
        dm = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(dm)
            joined = dm.load_joined()
        except Exception:  # pragma: no cover - source data not hydrated
            self.skipTest("measured seam/LMP series not available")
        for year, entry in MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR.items():
            sample = joined.loc[[year]]
            # THE ROW-COUNT PIN (miso-243): the hub join is a left join, so it
            # can never legitimately add rows. A partial join on a single-level
            # `hour` index silently triples the sample and re-draws every
            # quantile from a three-year mixture of the spread.
            self.assertEqual(
                len(sample.join(dm.load_spp_hub_da(), how="left")),
                len(sample),
                msg=(
                    f"{year}: the SPP hub join changed the row count -- the "
                    "frame passed in has lost its 'year' index level and pandas "
                    "partial-joined across hub years"
                ),
            )
            derived, _notes = dm.derive_spp_neighbour_hourly(sample)
            for side in ("import", "export"):
                np.testing.assert_allclose(
                    np.asarray(entry["SPP"][side], dtype=float),
                    np.asarray(derived[side], dtype=float),
                    atol=0.005,
                    err_msg=f"{year} {side} offsets drifted from the derivation",
                )

    def test_spp_bands_become_hourly_and_equal_hub_plus_offset(self):
        from market_sim.data.eia_loader import measured_miso_spp_hub_prices
        from market_sim.model.interchange.spec import (
            MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR,
        )

        hub = measured_miso_spp_hub_prices("MISO", 2024, T)
        if hub is None:
            self.skipTest("no measured SPP hub series under data/raw")
        overlay = MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[2024]["SPP"]

        fleet, mc = self._fleet_and_mc()
        self.assertTrue(
            inject_miso_seam_ladder_prices(
                fleet,
                mc,
                "MISO",
                2024,
                neighbour_anchored=True,
                neighbour_hourly=True,
                neighbour_hourly_spp=True,
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
            if name != "SPP":
                continue
            np.testing.assert_allclose(mc[row, :], hub + overlay[side][int(k) - 1])
            self.assertGreater(float(mc[row, :].std()), 1.0)
            moved += 1
        self.assertEqual(moved, 2 * SEAM_FLOW_TRANCHES)

    def test_south_and_pjm_are_untouched_by_the_spp_extension(self):
        """Confinement: only the SPP rows move against the miso-232 keeper arm."""
        fleet, base = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(
            fleet,
            base,
            "MISO",
            2024,
            neighbour_anchored=True,
            neighbour_hourly=True,
        )
        _f, arm = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(
            fleet,
            arm,
            "MISO",
            2024,
            neighbour_anchored=True,
            neighbour_hourly=True,
            neighbour_hourly_spp=True,
        )
        moved = set()
        for row, uid in enumerate(fleet.unit_ids):
            if _REF_IMPORT_MARK in uid:
                tag = uid.rsplit(_REF_IMPORT_MARK, 1)[1]
            elif _REF_EXPORT_MARK in uid:
                tag = uid.rsplit(_REF_EXPORT_MARK, 1)[1]
            else:
                np.testing.assert_array_equal(arm[row, :], base[row, :])
                continue
            seam = tag.partition("#")[0]
            if np.array_equal(arm[row, :], base[row, :]):
                continue
            moved.add(seam)
        self.assertEqual(moved, {"SPP"})

    def test_off_is_byte_identical_to_the_keeper_arm(self):
        fleet, a = self._fleet_and_mc()
        _f2, b = self._fleet_and_mc()
        inject_miso_seam_ladder_prices(
            fleet, a, "MISO", 2024, neighbour_anchored=True, neighbour_hourly=True
        )
        inject_miso_seam_ladder_prices(
            fleet,
            b,
            "MISO",
            2024,
            neighbour_anchored=True,
            neighbour_hourly=True,
            neighbour_hourly_spp=False,
        )
        np.testing.assert_array_equal(a, b)

    def test_spp_extension_is_inert_without_its_parent(self):
        """Rule 19: the sub-gate never arms a seam on its own."""
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
            neighbour_hourly_spp=True,
        )
        np.testing.assert_array_equal(a, b)

    def test_the_solve_path_refuses_the_sub_gate_without_its_parent(self):
        from pathlib import Path

        source = (
            Path(__file__).resolve().parents[3] / "scripts/run_calibration.py"
        ).read_text()
        self.assertIn('"miso_seam_neighbour_hourly_spp requires "', source)
        self.assertIn(
            '"miso_seam_neighbour_hourly_ladder: the SPP hourly entry', source
        )

    def test_field_is_registered_and_off_by_default(self):
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig(iso="MISO", mode="backcast")
        self.assertFalse(base.miso_seam_neighbour_hourly_spp)
        armed = base.with_overrides(miso_seam_neighbour_hourly_spp=True)
        self.assertNotEqual(base.cache_key(), armed.cache_key())
