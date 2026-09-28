"""Tests for the gated SPP West/East re-partition (SPP-93).

The default (``north_south``) topology, plant zoning and load shares are the
keeper's, byte-identical. Armed (``west_east``), the partition of
``PRECOMMIT-spp-93-west-east-2026-09-27.md`` §1-§2 appears consistently in the
topology, the plant zone lookup and the hourly zonal load shares, and the N<->S
link is REPLACED rather than stacked (rule 19).
"""

import unittest

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.topology_variant import (
    set_spp_zone_partition,
    spp_west_east_active,
)


class SppVariantCase(unittest.TestCase):
    """Base class: always leave the process-wide variant at its default."""

    def tearDown(self) -> None:  # noqa: D102 - trivial reset
        set_spp_zone_partition("north_south")


class TestTopology(SppVariantCase):
    """The partition transform in config.iso_configs._spp_config."""

    def test_default_is_keeper_topology(self):
        self.assertFalse(spp_west_east_active())
        self.assertEqual(ScenarioConfig().spp_zone_partition, "north_south")
        cfg = get_iso_config("SPP")
        self.assertEqual(cfg.zone_names, ["SPP-North", "SPP-South"])
        self.assertEqual(
            [(ln.from_zone, ln.to_zone, ln.ttc_mw) for ln in cfg.links],
            [("SPP-North", "SPP-South", 3400.0)],
        )

    def test_armed_replaces_zones_and_link(self):
        set_spp_zone_partition("west_east")
        cfg = get_iso_config("SPP")
        self.assertEqual(cfg.zone_names, ["SPP-West", "SPP-East"])
        self.assertAlmostEqual(sum(z.load_share for z in cfg.zones), 1.0, places=9)
        # One link, the W<->E one; the N<->S link is gone (rule 19).
        self.assertEqual(
            [(ln.from_zone, ln.to_zone, ln.ttc_mw) for ln in cfg.links],
            [("SPP-West", "SPP-East", 4000.0)],
        )

    def test_unknown_value_raises(self):
        with self.assertRaises(ValueError):
            set_spp_zone_partition("west-east")

    def test_other_isos_untouched(self):
        base = get_iso_config("MISO").zone_names
        set_spp_zone_partition("west_east")
        self.assertEqual(get_iso_config("MISO").zone_names, base)


class TestPlantZoning(SppVariantCase):
    """The measured plant table and its 1-NN fallback."""

    def test_named_plants(self):
        from market_sim.data.zone_assignment import assign_zone, build_zone_lookup

        base = build_zone_lookup("SPP")
        set_spp_zone_partition("west_east")
        we = build_zone_lookup("SPP")
        self.assertEqual(set(base), set(we))  # re-zones, never widens
        self.assertEqual(set(we.values()), {"SPP-West", "SPP-East"})
        # Node-labelled by SPP's own registry (PRECOMMIT §1.3).
        expect = {
            6194: "SPP-West",  # Tolk (SPS, RZ 3)
            108: "SPP-West",  # Holcomb (SECI, RZ 2)
            8036: "SPP-West",  # Cooper (NPPD, RZ 1)
            6065: "SPP-West",  # Iatan (KCPL node in RZ 1)
            6068: "SPP-East",  # Jeffrey (WR, RZ 4)
            6095: "SPP-East",  # Sooner (OKGE, RZ 4)
            2952: "SPP-East",
        }  # Muskogee (OKGE, RZ 4)
        for oris, zone in expect.items():
            self.assertEqual(assign_zone(oris, "SPP"), zone, oris)
            if oris in we:
                self.assertEqual(we[oris], zone, oris)

    def test_nearest_neighbour_has_no_parameter(self):
        from market_sim.data.zone_assignment import _spp_we_nearest

        set_spp_zone_partition("west_east")
        self.assertEqual(_spp_we_nearest(35.2, -101.8), "SPP-West")  # Amarillo
        self.assertEqual(_spp_we_nearest(35.5, -97.5), "SPP-East")  # Oklahoma City
        self.assertEqual(_spp_we_nearest(None, None), "SPP-East")


class TestZonalShares(SppVariantCase):
    """The sub-BA grouping under each partition."""

    def test_groupings_cover_the_same_17_subbas(self):
        from scripts.data.curate_zonal_shares import (
            _SPP_SUBBA_ZONE_GROUPS,
            _SPP_SUBBA_ZONE_GROUPS_WEST_EAST,
        )

        self.assertEqual(
            set(_SPP_SUBBA_ZONE_GROUPS), set(_SPP_SUBBA_ZONE_GROUPS_WEST_EAST)
        )
        west = {
            k for k, v in _SPP_SUBBA_ZONE_GROUPS_WEST_EAST.items() if v == "SPP-West"
        }
        self.assertEqual(west, {"LES", "NPPD", "OPPD", "SECI", "SPS", "WAUE"})

    def test_armed_shares_sum_to_one(self):
        from market_sim.data.eia930.zonal_shares import load_zonal_shares

        sh = load_zonal_shares("SPP", 2024, ["SPP-West", "SPP-East"])
        self.assertIsNotNone(sh)
        self.assertEqual(sh.shape, (2, 8760))
        np.testing.assert_allclose(sh.sum(axis=0), 1.0, atol=1e-9)
        # The measured West share (EIA-930 sub-BA energy) sits near 0.40.
        self.assertTrue(0.35 < sh[0].mean() < 0.45)


if __name__ == "__main__":
    unittest.main()
