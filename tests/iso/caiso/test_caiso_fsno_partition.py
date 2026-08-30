"""Tests for the gated CAISO FSNO sub-zonal partition (caiso-224).

Covers the topology-variant gate end to end at unit grain: the default
(flag-off) topology, zone carve, and load shapes are byte-identical to the
pre-caiso-224 base; armed, the P-A' partition of
``PRECOMMIT-caiso224-fsno-arm-2026-08-30.md`` §1 appears consistently in the
topology, the plant zone lookup, and the hourly zonal load shares.
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    CAISO_TAC_ZONE_WEIGHTS,
    CAISO_TAC_ZONE_WEIGHTS_FSNO,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.topology_variant import (
    caiso_fsno_partition_active,
    set_caiso_fsno_partition,
)

BASE_ZONES = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest", "WECC_import"]
FSNO_ZONES = ["NP15", "FSNO", "ZP26", "LA_BASIN", "SDGE", "SP15_rest", "WECC_import"]


class FsnoVariantCase(unittest.TestCase):
    """Base class: always leave the process-wide variant disarmed."""

    def tearDown(self) -> None:  # noqa: D102 - trivial reset
        set_caiso_fsno_partition(False)


class TestFsnoTopology(FsnoVariantCase):
    """The partition transform in config.iso_configs._caiso_config."""

    def test_default_off_base_topology(self):
        self.assertFalse(caiso_fsno_partition_active())
        cfg = get_iso_config("CAISO")
        self.assertEqual(cfg.zone_names, BASE_ZONES)
        pairs = {(ln.from_zone, ln.to_zone) for ln in cfg.links}
        self.assertIn(("NP15", "ZP26"), pairs)
        self.assertNotIn(("NP15", "FSNO"), pairs)

    def test_armed_partition(self):
        set_caiso_fsno_partition(True)
        cfg = get_iso_config("CAISO")
        self.assertEqual(cfg.zone_names, FSNO_ZONES)
        shares = {z.name: z.load_share for z in cfg.zones}
        # The measured 3-way PG&E split (caiso-223 §C), summing exactly to
        # the 2-way pair's 0.4615 so the seven zones keep summing to 1.0.
        self.assertAlmostEqual(shares["NP15"], 0.347332)
        self.assertAlmostEqual(shares["FSNO"], 0.061191)
        self.assertAlmostEqual(shares["ZP26"], 0.052977)
        self.assertAlmostEqual(sum(shares.values()), 1.0, places=6)
        ttc = {(ln.from_zone, ln.to_zone): ln.ttc_mw for ln in cfg.links}
        # DMM 2023 element caps: 1,600 + 340 and 2,500 (precommit §2).
        self.assertEqual(ttc[("NP15", "FSNO")], 1940.0)
        self.assertEqual(ttc[("FSNO", "ZP26")], 2500.0)
        self.assertNotIn(("NP15", "ZP26"), ttc)
        # Existing boundaries untouched.
        self.assertEqual(ttc[("ZP26", "SP15_rest")], 4000.0)
        self.assertEqual(ttc[("WECC_import", "NP15")], 4800.0)
        cfg.validate_topology()

    def test_other_isos_untouched_when_armed(self):
        set_caiso_fsno_partition(True)
        for iso in ("ERCOT", "PJM", "MISO", "NYISO", "NEISO"):
            self.assertNotIn("FSNO", get_iso_config(iso).zone_names)


class TestFsnoZoneCarve(FsnoVariantCase):
    """The zone_assignment carve (caiso-223 §B membership + county tier)."""

    def test_carve_matches_caiso223_membership(self):
        from market_sim.data.zone_assignment import (
            build_zone_lookup,
            load_caiso_fsno_subzone_membership,
        )

        off = build_zone_lookup("CAISO")
        self.assertNotIn("FSNO", set(off.values()))

        set_caiso_fsno_partition(True)
        on = build_zone_lookup("CAISO")
        subzones = load_caiso_fsno_subzone_membership()
        self.assertTrue(subzones, "membership CSV missing")
        # Every measured recut row present in the lookup is honored verbatim
        # — including honest non-moves (Henrietta-D 57706 stays ZP26).
        for oris, subzone in subzones.items():
            if oris in on:
                self.assertEqual(on[oris], subzone, f"plant {oris}")
        # The county tier moves unjoined Fresno/Kings/Madera/Merced plants
        # (caiso-223 §B: 116 plants incl. Helms) and only re-cuts plants the
        # geography had in NP15/ZP26.
        moved = {k for k, v in on.items() if v == "FSNO"}
        county_tier = moved - set(subzones)
        self.assertGreater(len(county_tier), 0)
        for oris in moved:
            self.assertIn(off[oris], ("NP15", "ZP26"))
        # Off-path again: byte-identical to the first off lookup.
        set_caiso_fsno_partition(False)
        self.assertEqual(build_zone_lookup("CAISO"), off)


class TestFsnoZonalShares(FsnoVariantCase):
    """The exact scalar re-split in data.eia930.zonal_shares."""

    def test_weights_are_exact_resplit_of_pge_pair(self):
        w2 = CAISO_TAC_ZONE_WEIGHTS["PGE-TAC"]
        self.assertAlmostEqual(
            sum(CAISO_TAC_ZONE_WEIGHTS_FSNO.values()), sum(w2.values()), places=9
        )

    def test_fsno_rescale_preserves_columns(self):
        from market_sim.data.eia930.zonal_shares import load_zonal_shares

        base = load_zonal_shares("CAISO", 2023, BASE_ZONES)
        if base is None:
            self.skipTest("no measured CAISO TAC load on disk")
        shares = load_zonal_shares("CAISO", 2023, FSNO_ZONES)
        self.assertEqual(shares.shape, (7, base.shape[1]))
        np.testing.assert_allclose(shares.sum(axis=0), 1.0, atol=1e-9)
        # Non-PG&E rows byte-identical; the three PG&E rows sum to the old
        # NP15+ZP26 pair in every hour (same PGE-TAC hourly mass).
        for zone in ("LA_BASIN", "SDGE", "SP15_rest", "WECC_import"):
            np.testing.assert_array_equal(
                shares[FSNO_ZONES.index(zone)], base[BASE_ZONES.index(zone)]
            )
        pge_new = (
            shares[FSNO_ZONES.index("NP15")]
            + shares[FSNO_ZONES.index("FSNO")]
            + shares[FSNO_ZONES.index("ZP26")]
        )
        pge_old = base[BASE_ZONES.index("NP15")] + base[BASE_ZONES.index("ZP26")]
        np.testing.assert_allclose(pge_new, pge_old, atol=1e-12)


class TestFsnoInheritanceAliases(FsnoVariantCase):
    """The precommit §3 parent-inheritance rules (NP15 -> FSNO)."""

    def test_loss_surface_parent_row(self):
        from market_sim.model.interchange.caiso import _caiso_loss_surface_row

        surface = {"NP15": [0.01] * 12, "ZP26": [0.02] * 12}
        np.testing.assert_array_equal(
            _caiso_loss_surface_row(surface, "FSNO"),
            _caiso_loss_surface_row(surface, "NP15"),
        )
        with self.assertRaises(KeyError):
            _caiso_loss_surface_row(surface, "NO_SUCH_ZONE")

    def test_as_np26_region_includes_fsno(self):
        from market_sim.data.caiso_as_requirements import REGION_ZONES

        self.assertIn("FSNO", REGION_ZONES["AS_NP26"])


if __name__ == "__main__":
    unittest.main()
