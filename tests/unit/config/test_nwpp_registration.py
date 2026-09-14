"""NWPP registration pins (lane NWPP-20, 2026-09-14).

NWPP is the first POOL region — seventeen balancing authorities under one key
(owner ruling N1). These tests pin the three things that make it different
from every prior registration and that fail SILENTLY when wrong (NWPP-10 §3):

* the ISO -> BA direction is a codes tuple, never a scalar inverse of the
  many-to-one ``BA_CODE_TO_ISO`` (``len(ba_codes("NWPP")) == 17``, and the
  1:1 regions' scalar entries are unchanged — gate G8's byte-identity claim);
* the footprint admission predicate (``BA ∈ NWPP_BAS AND NERC == WECC``) and
  the curated fleet it produces: **939 plants / 1,930 generators / 98,238.1 MW**
  (docs/multi-iso/nwpp-data-audit.md §2.8(a));
* the deliberate absences: no import node (G7), no capacity market (N7), no
  CAMPD binning (N8), no tail threshold (G6), no offer-band delta (G5).
"""

from __future__ import annotations

import unittest

import pandas as pd

from market_sim.config.capacity_market import (
    CAMPD_BINNING_ISOS,
    MARKET_DESIGN,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    QUEUE_CAP_PER_TECH_GW,
)
from market_sim.config.interchange_config import IMPORT_TRANCHES, IMPORT_ZONE
from market_sim.config.iso_configs import SUPPORTED_ISOS, get_iso_config
from market_sim.config.paths import EIA_860_DIR
from market_sim.config.solve_surface import SURFACE_ISOS
from market_sim.data.eia930.demand import DEMAND_LOADERS
from market_sim.data.eia930.envelopes import _SCALAR_INTERCHANGE_ISOS
from market_sim.data.eia930.frames import _ISO_TO_HOURLY_BA, _POOL_HOURLY_MEMBERS
from market_sim.data.fleet.models import (
    BA_CODE_TO_ISO,
    EIA_860_PARQUET_NAME,
    ISO_NERC_REGION_ADMISSION,
    ISO_TO_BA_CODE,
    ISO_TO_BA_CODES,
    NWPP_BAS,
    ba_codes,
    footprint_plant_mask,
)
from market_sim.data.zone_assignment import _NWPP_BA_ZONES
from market_sim.model.interchange.spec import INTERFACE_NEIGHBORS

EXPECTED_BAS = (
    "BPAT",
    "PACE",
    "PACW",
    "PGE",
    "PSEI",
    "AVA",
    "IPCO",
    "NWMT",
    "CHPD",
    "DOPD",
    "GCPD",
    "SCL",
    "TPWR",
    "AVRN",
    "GRID",
    "WAUW",
    "NEVP",
)


class TestPinFlipAtomicity(unittest.TestCase):
    """Plan §2.3 / gate G1: builders, demand loaders and the surface tuple move together."""

    def test_nwpp_is_the_eighth_registered_region(self):
        self.assertEqual(SUPPORTED_ISOS[-1], "NWPP")
        self.assertEqual(len(SUPPORTED_ISOS), 8)
        self.assertNotIn("SOCO", SUPPORTED_ISOS)  # chartered, not registered

    def test_surface_isos_and_demand_loaders_carry_nwpp(self):
        self.assertIn("NWPP", SURFACE_ISOS)
        self.assertEqual(set(SURFACE_ISOS), set(SUPPORTED_ISOS))
        self.assertIn("NWPP", DEMAND_LOADERS)
        self.assertIn("NWPP", _SCALAR_INTERCHANGE_ISOS)
        self.assertEqual(_ISO_TO_HOURLY_BA["NWPP"], "NWPP")
        self.assertEqual(_POOL_HOURLY_MEMBERS["NWPP"], NWPP_BAS)


class TestIsoToBaCodes(unittest.TestCase):
    """The R-e blocker: a pool is a codes tuple, never one arbitrary member."""

    def test_nwpp_has_all_seventeen_members_in_order(self):
        self.assertEqual(ba_codes("NWPP"), EXPECTED_BAS)
        self.assertEqual(len(ba_codes("NWPP")), 17)
        self.assertEqual(ba_codes("nwpp"), EXPECTED_BAS)  # case-insensitive
        self.assertEqual(NWPP_BAS, EXPECTED_BAS)
        for ba in EXPECTED_BAS:
            self.assertEqual(BA_CODE_TO_ISO[ba], "NWPP")

    def test_scalar_inverse_has_no_pool_entry(self):
        """``ISO_TO_BA_CODE.get("NWPP")`` reads None, never one seventeenth."""
        self.assertNotIn("NWPP", ISO_TO_BA_CODE)
        self.assertIsNone(ISO_TO_BA_CODE.get("NWPP"))

    def test_one_to_one_regions_are_byte_identical(self):
        """Gate G8: every 1:1 region's scalar entry and tuple agree exactly."""
        expected = {
            "ERCOT": "ERCO",
            "CAISO": "CISO",
            "PJM": "PJM",
            "MISO": "MISO",
            "NYISO": "NYIS",
            "NEISO": "ISNE",
            "SPP": "SWPP",
        }
        self.assertEqual(ISO_TO_BA_CODE, expected)
        for iso, code in expected.items():
            self.assertEqual(ba_codes(iso), (code,))
            self.assertEqual(ISO_TO_BA_CODES[iso], (code,))

    def test_unregistered_region_selects_nothing(self):
        self.assertEqual(ba_codes("TVA"), ())

    def test_zone_map_membership_equals_the_pool(self):
        """Gate G18: every member is in exactly one whole-BA zone; no BA splits."""
        self.assertEqual(set(_NWPP_BA_ZONES), set(NWPP_BAS))
        self.assertEqual(
            set(_NWPP_BA_ZONES.values()),
            {"NWPP-NW", "NWPP-OR", "NWPP-INLAND", "NWPP-EAST", "NWPP-SNV"},
        )
        self.assertEqual(_NWPP_BA_ZONES["AVRN"], "NWPP-NW")  # supply-side member
        self.assertEqual(_NWPP_BA_ZONES["GRID"], "NWPP-OR")  # supply-side member
        self.assertEqual(_NWPP_BA_ZONES["NEVP"], "NWPP-SNV")
        self.assertEqual(_NWPP_BA_ZONES["PACE"], "NWPP-EAST")


class TestFootprintAdmission(unittest.TestCase):
    """Audit §2.8(a): BA ∈ NWPP_BAS AND NERC == WECC, as a registry predicate."""

    def test_predicate_is_registered_for_nwpp_only(self):
        self.assertEqual(ISO_NERC_REGION_ADMISSION, {"NWPP": "WECC"})

    def test_mask_rejects_the_tre_row_and_keeps_wecc_rows(self):
        ba = pd.Series(["DOPD", "DOPD", "WAUW", "PACE", "ERCO"])
        nerc = pd.Series(["WECC", "TRE", "MRO", "WECC", "TRE"])
        mask = footprint_plant_mask("NWPP", ba, nerc)
        # Wells (DOPD, WECC) in; Pine Forest (DOPD, TRE) out; Sand Creek
        # (WAUW, MRO) out; PACE in; an ERCOT plant never in.
        self.assertEqual(mask.tolist(), [True, False, False, True, False])

    def test_mask_is_ba_only_for_one_to_one_regions(self):
        ba = pd.Series(["ERCO", "ERCO", "CISO"])
        nerc = pd.Series(["TRE", "WECC", "WECC"])
        self.assertEqual(
            footprint_plant_mask("ERCOT", ba, nerc).tolist(), [True, True, False]
        )

    def test_curated_fleet_reproduces_the_post_adjudication_census(self):
        """939 plants / 1,930 generators / 98,238.1 MW; Pine Forest absent."""
        path = EIA_860_DIR / EIA_860_PARQUET_NAME
        if not path.exists():
            self.skipTest("eia860_generators.parquet not hydrated")
        df = pd.read_parquet(
            path,
            columns=["plant_id", "balancing_authority_code", "nameplate_capacity_mw"],
        )
        fleet = df[df["balancing_authority_code"].isin(NWPP_BAS)]
        self.assertEqual(fleet["plant_id"].nunique(), 939)
        self.assertEqual(len(fleet), 1930)
        self.assertAlmostEqual(
            float(fleet["nameplate_capacity_mw"].sum()), 98_238.1, places=1
        )
        self.assertFalse((df["plant_id"] == 68906).any())  # Pine Forest Solar I, TX/TRE
        self.assertFalse((df["plant_id"] == 69290).any())  # Desert Bloom, proposed only


class TestDeliberateAbsences(unittest.TestCase):
    """Each absence is a ruling, not an oversight (cards N7 / N8, gates G5-G7)."""

    def test_no_import_node(self):
        self.assertNotIn("NWPP", IMPORT_TRANCHES)
        self.assertNotIn("NWPP", IMPORT_ZONE)

    def test_no_capacity_market_and_no_campd_binning(self):
        self.assertNotIn("NWPP", MARKET_DESIGN)
        self.assertNotIn("NWPP", CAMPD_BINNING_ISOS)
        self.assertEqual(PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"], 0.144)

    def test_no_tail_threshold(self):
        """Gate G6: NWPP-13 read NO, so no C3c threshold exists in the scorer."""
        from scripts.calibration_verdict import TAIL_THRESHOLD

        self.assertNotIn("NWPP", TAIL_THRESHOLD)

    def test_queue_caps_cover_the_classic_candidates(self):
        for tech in ("wind", "solar", "gas_cc", "gas_ct", "nuclear"):
            self.assertIn(tech, QUEUE_CAP_PER_TECH_GW["NWPP"])

    def test_neighbour_blocks_are_the_three_ruled_seams(self):
        names = [n.name for n in INTERFACE_NEIGHBORS["NWPP"]]
        self.assertEqual(names, ["CAISO", "WECC_SW", "WECC_CAN"])
        zones = set(get_iso_config("NWPP").zone_names)
        for neighbor in INTERFACE_NEIGHBORS["NWPP"]:
            self.assertTrue(set(neighbor.border_zones) <= zones, neighbor.name)

    def test_offer_bands_are_the_generic_identity(self):
        """Gate G5: no NWPP-specific band; the backcast config carries the
        generic base curve for NWPP exactly as it does for SPP."""
        from market_sim.pipeline.backcast_config import backcast_config

        spp = backcast_config(2024, "SPP", 24, 3.0).offer_curve_by_group
        nwpp = backcast_config(2024, "NWPP", 24, 3.0).offer_curve_by_group
        gas_groups = [g for g in nwpp if g.startswith(("CC", "CT", "ST"))]
        self.assertTrue(gas_groups)
        for group in gas_groups:
            self.assertEqual(nwpp[group], spp[group], group)


if __name__ == "__main__":
    unittest.main()
