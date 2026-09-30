"""Tests for the gated NYISO F/G re-partition (NYISO-NEXT-17, ``nyiso_fg_split``).

Default off: the five-zone topology, plant zoning, load shares, PAR landings,
border links and floor limbs are the keeper's, byte-identical. Armed, NYISO
load zone G (Hudson Valley) moves from ``Capital_Hudson`` to ``Lower_Hudson``
everywhere at once, the upstate cutset gets its second link, and the TOTAL
EAST cutset envelope is REPLACED by its two measured legs (rule 19).
"""

import unittest

import numpy as np

from market_sim.config.constants import (
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_TE_NONCE_ENVELOPE_BY_MONTH,
)
from market_sim.config.iso_configs import (
    RELIABILITY_FLOOR_REGISTRY,
    get_iso_config,
    remap_nyiso_fg_split_floor_specs,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.topology_variant import (
    nyiso_fg_split_active,
    set_nyiso_fg_split,
)
from market_sim.data.eia930.zonal_shares import nyiso_load_zone_groups
from market_sim.data.nyiso_demand_response import nyiso_zone_to_model
from market_sim.data.nyiso_par_attribution import interface_zone
from market_sim.data.zone_assignment import (
    NYISO_CAPITAL_HUDSON_COUNTIES,
    NYISO_HUDSON_VALLEY_COUNTIES,
    _nyiso_zone,
    _nyiso_zone_from_latlon,
)
from market_sim.model.interchange.spec import IMPORT_NODE_LINKS, import_node_links
from market_sim.pipeline.ttc import apply_iso_monthly_ttc

NY = 36  # New York state FIPS


class FgVariantCase(unittest.TestCase):
    """Base class: always leave the process-wide variant at its default."""

    def tearDown(self) -> None:  # noqa: D102 - trivial reset
        set_nyiso_fg_split(False)


class TestConfigField(FgVariantCase):
    """The ScenarioConfig field and its required companion."""

    def test_default_off(self):
        self.assertFalse(ScenarioConfig().nyiso_fg_split)
        self.assertFalse(nyiso_fg_split_active())

    def test_requires_cutset(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(nyiso_fg_split=True)
        cfg = ScenarioConfig(nyiso_fg_split=True, nyiso_total_east_cutset_ttc=True)
        self.assertTrue(cfg.nyiso_fg_split)

    def test_cache_key_drops_default(self):
        base = ScenarioConfig(nyiso_total_east_cutset_ttc=True)
        armed = ScenarioConfig(nyiso_total_east_cutset_ttc=True, nyiso_fg_split=True)
        self.assertNotEqual(base.cache_key(), armed.cache_key())


class TestTopology(FgVariantCase):
    """The partition transform in config.iso_configs._nyiso_config."""

    def test_default_is_keeper_topology(self):
        cfg = get_iso_config("NYISO")
        self.assertEqual(
            [(ln.from_zone, ln.to_zone) for ln in cfg.links],
            [
                ("Upstate_West", "Capital_Hudson"),
                ("Capital_Hudson", "Lower_Hudson"),
                ("Lower_Hudson", "NYC"),
                ("NYC", "Long_Island"),
            ],
        )

    def test_armed_adds_second_upstate_link(self):
        base = get_iso_config("NYISO")
        set_nyiso_fg_split(True)
        cfg = get_iso_config("NYISO")
        self.assertEqual(cfg.zone_names, base.zone_names)
        self.assertAlmostEqual(sum(z.load_share for z in cfg.zones), 1.0, places=9)
        # The four base links keep their order; the new link is appended.
        self.assertEqual(
            [(ln.from_zone, ln.to_zone) for ln in cfg.links[:4]],
            [(ln.from_zone, ln.to_zone) for ln in base.links],
        )
        self.assertEqual(
            (cfg.links[4].from_zone, cfg.links[4].to_zone),
            ("Upstate_West", "Lower_Hudson"),
        )

    def test_other_isos_untouched(self):
        base = get_iso_config("NEISO").zone_names
        set_nyiso_fg_split(True)
        self.assertEqual(get_iso_config("NEISO").zone_names, base)


class TestMembership(FgVariantCase):
    """County, load-zone, DR and PAR maps move zone G together."""

    def test_county_zone(self):
        g = sorted(NYISO_HUDSON_VALLEY_COUNTIES)
        f = sorted(NYISO_CAPITAL_HUDSON_COUNTIES - NYISO_HUDSON_VALLEY_COUNTIES)
        self.assertTrue(NYISO_HUDSON_VALLEY_COUNTIES < NYISO_CAPITAL_HUDSON_COUNTIES)
        for c in g + f:
            self.assertEqual(_nyiso_zone(None, None, NY, c), "Capital_Hudson")
        set_nyiso_fg_split(True)
        for c in g:
            self.assertEqual(_nyiso_zone(None, None, NY, c), "Lower_Hudson")
        for c in f:
            self.assertEqual(_nyiso_zone(None, None, NY, c), "Capital_Hudson")

    def test_latlon_fallback(self):
        # Newburgh (zone G), ~41.5 N 74.0 W.
        self.assertEqual(_nyiso_zone_from_latlon(41.5, -74.0), "Capital_Hudson")
        set_nyiso_fg_split(True)
        self.assertEqual(_nyiso_zone_from_latlon(41.5, -74.0), "Lower_Hudson")
        # Albany (zone F).
        self.assertEqual(_nyiso_zone_from_latlon(42.65, -73.75), "Capital_Hudson")

    def test_load_zone_groups(self):
        self.assertEqual(nyiso_load_zone_groups()["HUD VL"], "Capital_Hudson")
        set_nyiso_fg_split(True)
        groups = nyiso_load_zone_groups()
        self.assertEqual(groups["HUD VL"], "Lower_Hudson")
        self.assertEqual(groups["G"], "Lower_Hudson")
        self.assertEqual(groups["CAPITL"], "Capital_Hudson")

    def test_demand_response_map(self):
        self.assertEqual(nyiso_zone_to_model()["G"], "Capital_Hudson")
        set_nyiso_fg_split(True)
        self.assertEqual(nyiso_zone_to_model()["G"], "Lower_Hudson")
        self.assertEqual(nyiso_zone_to_model()["F"], "Capital_Hudson")

    def test_par_landings(self):
        self.assertEqual(interface_zone()["ramapo"], "Capital_Hudson")
        set_nyiso_fg_split(True)
        land = interface_zone()
        self.assertEqual(land["ramapo"], "Lower_Hudson")
        self.assertEqual(land["jk"], "Lower_Hudson")
        self.assertEqual(land["abc"], "NYC")

    def test_border_links_conserve_capability(self):
        base = dict(import_node_links("NYISO"))
        self.assertEqual(base, dict(IMPORT_NODE_LINKS["NYISO"]))
        set_nyiso_fg_split(True)
        split = dict(import_node_links("NYISO"))
        self.assertEqual(sum(split.values()), sum(base.values()))
        self.assertEqual(
            split["Capital_Hudson"] + split["Lower_Hudson"], base["Capital_Hudson"]
        )


class TestFloorRemap(FgVariantCase):
    """G-only Capital_Hudson ST_GAS limbs follow their plants."""

    def test_remap(self):
        specs = RELIABILITY_FLOOR_REGISTRY.get("NYISO", [])
        self.assertIs(remap_nyiso_fg_split_floor_specs(specs, "NYISO"), specs)
        set_nyiso_fg_split(True)
        out = remap_nyiso_fg_split_floor_specs(specs, "NYISO")
        self.assertEqual(len(out), len(specs))
        for a, b in zip(specs, out, strict=True):
            if a.zone == "Capital_Hudson" and a.plant_class == "ST_GAS":
                self.assertEqual(b.zone, "Lower_Hudson")
                self.assertEqual(a.threshold, b.threshold)
            else:
                self.assertIs(a, b)
        self.assertIs(remap_nyiso_fg_split_floor_specs(specs, "NEISO"), specs)


class TestUpstateTtc(FgVariantCase):
    """The cutset envelope is replaced by its two measured legs (rule 19)."""

    def _ttc(self, cfg_iso, config):
        ttc = np.array([ln.ttc_mw for ln in cfg_iso.links], dtype=float)
        return apply_iso_monthly_ttc(ttc, cfg_iso, "NYISO", 2021, 8760, config)

    def test_legs(self):
        set_nyiso_fg_split(True)
        cfg_iso = get_iso_config("NYISO")
        config = ScenarioConfig(nyiso_total_east_cutset_ttc=True, nyiso_fg_split=True)
        out = self._ttc(cfg_iso, config)
        self.assertEqual(out.shape, (8760, 5))
        ce = NYISO_INTERFACE_TTC_BY_MONTH[2021][("Upstate_West", "Capital_Hudson")]
        nonce = NYISO_TE_NONCE_ENVELOPE_BY_MONTH[2021][("Upstate_West", "Lower_Hudson")]
        self.assertEqual(out[0, 0], ce[0])
        self.assertEqual(out[-1, 0], ce[11])
        self.assertEqual(out[0, 4], nonce[0])
        self.assertEqual(out[-1, 4], nonce[11])
        # Links that carry no monthly table keep their static values.
        self.assertEqual(out[0, 1], cfg_iso.links[1].ttc_mw)


if __name__ == "__main__":
    unittest.main()
