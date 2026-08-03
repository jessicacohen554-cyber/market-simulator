"""Tests for the PJM reference-price seam deliverability cap.

Each of PJM's 5 priced seams (MISO / NYISO / Carolinas / TVA / LGEE) has its
import-band availability scaled to the measured per-neighbor deliverability
envelope from the PJM tie-line file (border zones summed to neighbor level, per
(month x hod) p90). The cap is applied per-direction: import caps scale
availability; export caps raise min_gen. Mirrors the MISO seam flow limit tests.
"""

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
from market_sim.data.eia_loader import (
    pjm_neighbor_interchange,
    pjm_neighbor_interchange_envelope,
    pjm_zonal_interchange_envelope,
)
from market_sim.model.interchange.spec import PJM_TIE_NEIGHBOR
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    _REF_EXPORT_MARK,
    _REF_IMPORT_MARK,
    build_reference_price_node,
    inject_pjm_seam_flow_limit,
)

REPO = Path(__file__).resolve().parents[3]
T = 8760
PJM_NEIGHBORS = INTERFACE_NEIGHBORS.get("PJM", [])
PJM_ZONE_NAMES = [
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_ComEd",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_MAAC",
    "PJM_West_APS",
    "PJM_external",
]


class TestPjmEnvelopeLoader(unittest.TestCase):
    """The PJM per-zone interchange envelope loads and is non-negative."""

    def test_envelope_present_for_backcast_year(self):
        env = pjm_zonal_interchange_envelope(2024, PJM_ZONE_NAMES, T)
        self.assertIsNotNone(env)
        import_cap, export_cap = env
        self.assertEqual(import_cap.shape, (len(PJM_ZONE_NAMES), T))
        self.assertEqual(export_cap.shape, (len(PJM_ZONE_NAMES), T))
        self.assertTrue(np.all(import_cap >= 0.0))
        self.assertTrue(np.all(export_cap >= 0.0))

    def test_envelope_none_for_future_year(self):
        self.assertIsNone(pjm_zonal_interchange_envelope(2030, PJM_ZONE_NAMES, T))


class TestPjmSeamInjection(unittest.TestCase):
    """``inject_pjm_seam_flow_limit`` caps import bands per neighbor."""

    def _fleet(self):
        node = build_reference_price_node("PJM")
        fleet_zones = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, fleet_zones, hours=T)

    def test_import_bands_capped(self):
        node, fleet = self._fleet()
        self.assertTrue(
            inject_pjm_seam_flow_limit(fleet, "PJM", 2024, PJM_ZONE_NAMES, T)
        )
        for neighbor in PJM_NEIGHBORS:
            imp_rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_IMPORT_MARK in uid
                and uid.rsplit(_REF_IMPORT_MARK, 1)[1].partition("#")[0]
                == neighbor.name
            ]
            self.assertTrue(imp_rows, f"no import rows for {neighbor.name}")
            avail_mw = (
                fleet.availability[imp_rows, :] * fleet.pmax[imp_rows, None]
            ).sum(axis=0)
            limit = float(fleet.pmax[imp_rows].sum())
            self.assertTrue(np.all(avail_mw <= limit + 1.0))

    def test_export_bands_untouched_by_import_cap(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        inject_pjm_seam_flow_limit(fleet, "PJM", 2024, PJM_ZONE_NAMES, T)
        exp_rows = [
            r for r, uid in enumerate(fleet.unit_ids) if _REF_EXPORT_MARK in uid
        ]
        self.assertTrue(exp_rows)
        np.testing.assert_array_equal(
            fleet.availability[exp_rows, :], before[exp_rows, :]
        )

    def test_noop_for_non_pjm(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        self.assertFalse(
            inject_pjm_seam_flow_limit(fleet, "MISO", 2024, PJM_ZONE_NAMES, T)
        )
        np.testing.assert_array_equal(fleet.availability, before)

    def test_noop_for_future_year(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        self.assertFalse(
            inject_pjm_seam_flow_limit(fleet, "PJM", 2030, PJM_ZONE_NAMES, T)
        )
        np.testing.assert_array_equal(fleet.availability, before)


class TestPjmSeamExportInjection(unittest.TestCase):
    """``inject_pjm_seam_flow_limit(direction="export")`` caps export bands."""

    def _fleet(self):
        node = build_reference_price_node("PJM")
        fleet_zones = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, fleet_zones, hours=T)

    def test_export_bands_capped(self):
        node, fleet = self._fleet()
        self.assertTrue(
            inject_pjm_seam_flow_limit(
                fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="export"
            )
        )
        self.assertIsNotNone(fleet.min_gen)
        for neighbor in PJM_NEIGHBORS:
            exp_rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_EXPORT_MARK in uid
                and uid.rsplit(_REF_EXPORT_MARK, 1)[1].partition("#")[0]
                == neighbor.name
            ]
            self.assertTrue(exp_rows, f"no export rows for {neighbor.name}")
            max_export = -fleet.min_gen[exp_rows, :].sum(axis=0)
            limit = -float(fleet.pmin[exp_rows].sum())
            self.assertTrue(np.all(max_export <= limit + 1.0))

    def test_import_bands_untouched_by_export_cap(self):
        node, fleet = self._fleet()
        before = fleet.availability.copy()
        inject_pjm_seam_flow_limit(
            fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="export"
        )
        imp_rows = [
            r for r, uid in enumerate(fleet.unit_ids) if _REF_IMPORT_MARK in uid
        ]
        self.assertTrue(imp_rows)
        np.testing.assert_array_equal(
            fleet.availability[imp_rows, :], before[imp_rows, :]
        )

    def test_invalid_direction_raises(self):
        node, fleet = self._fleet()
        with self.assertRaises(ValueError):
            inject_pjm_seam_flow_limit(
                fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="sideways"
            )


class TestPjmSeamEnvelopeByNeighbor(unittest.TestCase):
    """The pjm-151 per-neighbour envelope construction (rule 14 repair).

    The legacy path sums a per-model-ZONE envelope over each neighbour's
    ``border_zones``; a zone bucket holds every tie that lands in it, so the
    caps absorb other counterparties' ties. ``by_neighbor=True`` builds each
    seam's envelope from that seam's own ties instead.
    """

    def _fleet(self):
        node = build_reference_price_node("PJM")
        fleet_zones = sorted({g.zone for g in node})
        return node, generators_to_fleet_arrays(node, fleet_zones, hours=T)

    def test_tie_neighbor_map_covers_every_named_interface(self):
        """Every PJM interface name owns at least one tie, and no stray names."""
        named = {n.name for n in PJM_NEIGHBORS}
        mapped = set(PJM_TIE_NEIGHBOR.values())
        self.assertEqual(mapped, named)

    def test_tie_neighbor_map_covers_the_measured_file(self):
        """Every tie in a backcast year's file has a named interface."""
        path = (
            REPO
            / "data/raw/iso-specific-transmission"
            / "PJM_2024_import_export_act_sch_interchange.csv"
        )
        if not path.exists():  # pragma: no cover - raw file not provisioned
            self.skipTest("PJM tie-line file not present")
        ties = set(pd.read_csv(path, usecols=["tie_line"])["tie_line"].unique())
        self.assertEqual(ties - set(PJM_TIE_NEIGHBOR), set())

    def test_neighbor_envelope_shape_and_sign(self):
        names = [n.name for n in PJM_NEIGHBORS]
        env = pjm_neighbor_interchange_envelope(2024, names, T)
        self.assertIsNotNone(env)
        import_cap, export_cap = env
        self.assertEqual(import_cap.shape, (len(names), T))
        self.assertEqual(export_cap.shape, (len(names), T))
        self.assertTrue(np.all(import_cap >= 0.0))
        self.assertTrue(np.all(export_cap >= 0.0))

    def test_neighbor_envelope_none_for_future_year(self):
        names = [n.name for n in PJM_NEIGHBORS]
        self.assertIsNone(pjm_neighbor_interchange_envelope(2030, names, T))

    def test_ties_are_netted_before_the_directional_clip(self):
        """A seam that nets to export in an hour must not report an import.

        The construction error this repair had to avoid: clipping each tie
        before summing reports the import-side ties of a net-exporting seam as
        an import cap. Netting first is what ``pjm_zonal_interchange`` does.
        """
        series = pjm_neighbor_interchange(2024, ["MISO"])
        self.assertIsNotNone(series)
        # MISO is a near-always export seam on PJM's measured record; its
        # netted import side must be far below the sum of its import-side ties.
        netted_import = np.clip(-series[0], 0.0, None)
        self.assertLess(float(netted_import.mean()), 500.0)

    def test_by_neighbor_changes_the_tva_and_lgee_export_caps(self):
        """Liveness: the two single-tie seams the zone path mis-attributes."""
        caps = {}
        for by_nb in (False, True):
            _, fleet = self._fleet()
            self.assertTrue(
                inject_pjm_seam_flow_limit(
                    fleet,
                    "PJM",
                    2024,
                    PJM_ZONE_NAMES,
                    T,
                    direction="export",
                    by_neighbor=by_nb,
                )
            )
            for name in ("TVA", "LGEE"):
                rows = [
                    r
                    for r, uid in enumerate(fleet.unit_ids)
                    if _REF_EXPORT_MARK in uid
                    and uid.rsplit(_REF_EXPORT_MARK, 1)[1].partition("#")[0] == name
                ]
                caps[(by_nb, name)] = float(
                    (-fleet.min_gen[rows, :].sum(axis=0)).mean()
                )
        for name in ("TVA", "LGEE"):
            self.assertLess(
                caps[(True, name)],
                caps[(False, name)],
                f"{name} export cap should tighten under the direct construction",
            )

    def test_legacy_path_is_unchanged(self):
        """``by_neighbor=False`` reproduces the pre-repair caps exactly."""
        _, a = self._fleet()
        inject_pjm_seam_flow_limit(a, "PJM", 2024, PJM_ZONE_NAMES, T)
        _, b = self._fleet()
        inject_pjm_seam_flow_limit(b, "PJM", 2024, PJM_ZONE_NAMES, T, by_neighbor=False)
        np.testing.assert_array_equal(a.availability, b.availability)


if __name__ == "__main__":
    unittest.main()
