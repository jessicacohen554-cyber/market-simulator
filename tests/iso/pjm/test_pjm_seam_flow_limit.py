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

    A zone-summed construction preceded it: a per-model-ZONE envelope summed
    over each neighbour's ``border_zones``. A zone bucket holds every tie that
    lands in it, so the caps absorbed other counterparties' ties. The seam
    envelope is now built from that seam's OWN ties, unconditionally — the
    ``pjm_seam_envelope_by_neighbor`` gate and the zone-summed branch were
    deleted at pjm-152 under rule 26 ``[R-DELETE]`` once the repair became the
    keeper's armed path. The zone-summed cap is reconstructed inline below so
    the regression evidence survives the flag's deletion.
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

    def test_export_cap_is_the_seam_s_own_envelope_not_a_zone_sum(self):
        """The injected export cap IS the neighbour's own row, with no summation.

        Pins the repaired construction directly rather than against a flag: for
        every seam the applied cap must equal that seam's own envelope row
        (clipped to the band's total capacity), never a sum over
        ``border_zones``.
        """
        names = [n.name for n in PJM_NEIGHBORS]
        env = pjm_neighbor_interchange_envelope(2024, names, T)
        self.assertIsNotNone(env)
        _, export_cap = env
        _, fleet = self._fleet()
        self.assertTrue(
            inject_pjm_seam_flow_limit(
                fleet, "PJM", 2024, PJM_ZONE_NAMES, T, direction="export"
            )
        )
        for i, name in enumerate(names):
            rows = [
                r
                for r, uid in enumerate(fleet.unit_ids)
                if _REF_EXPORT_MARK in uid
                and uid.rsplit(_REF_EXPORT_MARK, 1)[1].partition("#")[0] == name
            ]
            if not rows:
                continue
            total = -float(fleet.pmin[rows].sum())
            expected = np.minimum(np.clip(export_cap[i], 0.0, None), total)
            applied = -fleet.min_gen[rows, :].sum(axis=0)
            np.testing.assert_allclose(applied, expected, rtol=0, atol=1e-6)

    def test_the_zone_summed_cap_was_looser_on_tva_and_lgee(self):
        """The defect the repair closed, reconstructed without the deleted flag.

        TVA and LGEE are the two seams the zone path mis-attributes worst (the
        whole tie lands in one border zone while the interface names two, so
        their caps absorbed every other tie in those buckets). The zone-summed
        export cap is rebuilt here from the still-public
        :func:`pjm_zonal_interchange_envelope` and must sit strictly above the
        per-neighbour one the injector now applies.
        """
        names = [n.name for n in PJM_NEIGHBORS]
        by_nb = pjm_neighbor_interchange_envelope(2024, names, T)
        by_zone = pjm_zonal_interchange_envelope(2024, PJM_ZONE_NAMES, T)
        self.assertIsNotNone(by_nb)
        self.assertIsNotNone(by_zone)
        _, nb_export = by_nb
        _, zone_export = by_zone
        z_idx = {z: i for i, z in enumerate(PJM_ZONE_NAMES)}
        for neighbor in PJM_NEIGHBORS:
            if neighbor.name not in ("TVA", "LGEE"):
                continue
            legacy = np.clip(
                zone_export[
                    [z_idx[z] for z in neighbor.border_zones if z in z_idx]
                ].sum(axis=0),
                0.0,
                None,
            )
            direct = np.clip(nb_export[names.index(neighbor.name)], 0.0, None)
            self.assertGreater(
                float(legacy.mean()),
                float(direct.mean()),
                f"{neighbor.name}: the zone-summed export cap should be looser",
            )


if __name__ == "__main__":
    unittest.main()
