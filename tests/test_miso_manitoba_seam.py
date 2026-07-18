"""MISO Manitoba two-way seam (``miso_manitoba_seam``, miso-74).

The flag swaps the import-only annual-flat Manitoba (MHEB) firm block for a
fourth MEASURED two-way priced seam, reusing the PJM/SPP/South seam machinery
(reference-price bands + Q-Q ladder + measured deliverability envelope) with the
merit-cap composition unforked. These tests pin, trivial-case first:

* flag-OFF byte-identity (no Manitoba bands → the ladder/envelope Manitoba
  entries are inert, row-driven; the firm block is intact);
* flag-ON: 8 import + 8 export Manitoba bands built, firm block dropped;
* the Manitoba bands take their frozen ladder price (incl. the 2025 net-export
  the firm block cannot represent);
* the measured envelope auto-covers Manitoba (both directions) without touching
  the other seams;
* the merit-cap composition path is live for Manitoba (no fork).
"""

import unittest

import numpy as np

from market_sim.config.interchange_config import (
    MISO_MANITOBA_SEAM_SPEC,
    MISO_SEAM_LADDER_BY_YEAR,
    build_interchange_fleet,
    get_interchange_spec,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia_loader import measured_seam_import_envelope
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_miso_seam_flow_limit,
    inject_miso_seam_ladder_prices,
)

_FIRM_UID = "MISO-West_Manitoba_firmhydro"


def _cfg(manitoba: bool) -> ScenarioConfig:
    return ScenarioConfig(
        iso="MISO",
        mode="backcast",
        reference_price_interface=True,
        miso_firm_imports=True,
        miso_seam_measured_ladder=True,
        miso_manitoba_seam=manitoba,
    )


def _seam_band_uids(fleet) -> list[str]:
    return [
        g.unit_id
        for g in fleet
        if f"{_REF_IMPORT_MARK}Manitoba" in g.unit_id
        or f"{_REF_EXPORT_MARK}Manitoba" in g.unit_id
    ]


class TestSeamSwap(unittest.TestCase):
    """The flag atomically swaps the firm block for the two-way priced seam."""

    def test_flag_off_is_byte_identical(self):
        # Flag off must reproduce a flag-absent config exactly: no Manitoba
        # seam bands, firm block present, identical generator list.
        absent = ScenarioConfig(
            iso="MISO",
            mode="backcast",
            reference_price_interface=True,
            miso_firm_imports=True,
            miso_seam_measured_ladder=True,
        )
        off = build_interchange_fleet(get_interchange_spec(_cfg(False), "MISO", 2025))
        base = build_interchange_fleet(get_interchange_spec(absent, "MISO", 2025))
        self.assertEqual(
            [g.unit_id for g in off], [g.unit_id for g in base], "flag-off drift"
        )
        self.assertEqual(_seam_band_uids(off), [], "flag off built Manitoba bands")
        self.assertIn(_FIRM_UID, [g.unit_id for g in off], "flag off dropped firm")

    def test_flag_on_builds_two_way_bands_and_drops_firm(self):
        on = build_interchange_fleet(get_interchange_spec(_cfg(True), "MISO", 2025))
        imp = [u for u in _seam_band_uids(on) if _REF_IMPORT_MARK in u]
        exp = [u for u in _seam_band_uids(on) if _REF_EXPORT_MARK in u]
        self.assertEqual(len(imp), SEAM_FLOW_TRANCHES)
        self.assertEqual(len(exp), SEAM_FLOW_TRANCHES)
        self.assertNotIn(_FIRM_UID, [g.unit_id for g in on], "firm block not dropped")
        # Bands land in MISO-West's shared external node; each holds 1/8 of the
        # pinned interface limit.
        band = next(g for g in on if f"{_REF_IMPORT_MARK}Manitoba#1" in g.unit_id)
        self.assertAlmostEqual(
            band.pmax_mw,
            MISO_MANITOBA_SEAM_SPEC.interface_limit_mw / SEAM_FLOW_TRANCHES,
        )

    def test_spec_flag_resolves_and_drops_firm_import(self):
        self.assertEqual(
            len(get_interchange_spec(_cfg(True), "MISO", 2025).firm_imports), 0
        )
        self.assertEqual(
            len(get_interchange_spec(_cfg(False), "MISO", 2025).firm_imports), 1
        )


class TestLadderAndEnvelope(unittest.TestCase):
    """The Manitoba bands are priced by the frozen ladder and capped two-way."""

    def test_ladder_covers_manitoba_all_years_two_way(self):
        for year in (2023, 2024, 2025):
            man = MISO_SEAM_LADDER_BY_YEAR[year]["Manitoba"]
            self.assertEqual(len(man["import"]), SEAM_FLOW_TRANCHES)
            self.assertEqual(len(man["export"]), SEAM_FLOW_TRANCHES)
            # Rising import / falling export supply curve; no-wash (every export
            # band strictly below the cheapest import band).
            self.assertEqual(list(man["import"]), sorted(man["import"]))
            self.assertEqual(list(man["export"]), sorted(man["export"], reverse=True))
            self.assertLess(max(man["export"]), min(man["import"]))

    def test_bands_take_their_manitoba_ladder_price(self):
        node = build_reference_price_node(
            "MISO", extra_neighbors=[MISO_MANITOBA_SEAM_SPEC]
        )
        zone_names = sorted({g.zone for g in node})
        fleet = generators_to_fleet_arrays(node, zone_names, hours=24)
        mc = np.full((len(node), 24), -123.0)
        self.assertTrue(inject_miso_seam_ladder_prices(fleet, mc, "MISO", 2025))
        ladder = MISO_SEAM_LADDER_BY_YEAR[2025]["Manitoba"]
        for row, uid in enumerate(fleet.unit_ids):
            if f"{_REF_IMPORT_MARK}Manitoba#" in uid:
                k = int(uid.rsplit("#", 1)[1]) - 1
                np.testing.assert_allclose(mc[row, :], ladder["import"][k])
            elif f"{_REF_EXPORT_MARK}Manitoba#" in uid:
                k = int(uid.rsplit("#", 1)[1]) - 1
                np.testing.assert_allclose(mc[row, :], ladder["export"][k])

    def test_envelope_auto_covers_manitoba_without_touching_others(self):
        base_keys = {"PJM", "SPP", "South"}
        for direction in ("import", "export"):
            env = measured_seam_import_envelope("MISO", 2025, 8760, direction=direction)
            self.assertIn("Manitoba", env, direction)
            self.assertTrue(base_keys.issubset(env), direction)
            # Two-way capability: a positive measured envelope in both directions
            # (the firm block had no export path at all).
            self.assertGreater(float(np.max(env["Manitoba"])), 0.0, direction)


class TestMeritCapComposition(unittest.TestCase):
    """The merit-cap semantics reach the Manitoba seam through the shared path."""

    def _fleet(self):
        node = build_reference_price_node(
            "MISO", extra_neighbors=[MISO_MANITOBA_SEAM_SPEC]
        )
        zone_names = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, zone_names, hours=8760)

    def test_merit_cap_and_uniform_both_apply_to_manitoba(self):
        # Both semantics must bind the Manitoba import bands (no fork), and they
        # must differ: the waterfall keeps the cheap base band full-width while
        # the uniform derate shrinks every band, so the base band's mean
        # availability is strictly higher under the merit cap.
        _, fleet_u = self._fleet()
        _, fleet_w = self._fleet()
        applied_u = inject_miso_seam_flow_limit(fleet_u, "MISO", 2025, merit_cap=False)
        applied_w = inject_miso_seam_flow_limit(fleet_w, "MISO", 2025, merit_cap=True)
        self.assertTrue(applied_u)
        self.assertTrue(applied_w)
        base_row = next(
            r
            for r, u in enumerate(fleet_u.unit_ids)
            if u.endswith(f"{_REF_IMPORT_MARK}Manitoba#1")
        )
        self.assertGreater(
            float(fleet_w.availability[base_row].mean()),
            float(fleet_u.availability[base_row].mean()),
            "merit-cap waterfall did not preserve the Manitoba base band",
        )


if __name__ == "__main__":
    unittest.main()
