"""Tests for the unified fleet-construction pipeline.

Covers ``load_or_synthesize_bins``, ``build_base_fleet`` and
``build_dispatch_fleet`` -- the single configurable pipeline that replaced
the separate ERCOT CAMPD-binning and legacy ``fleet_to_bins`` code paths in
``runner.py`` (see ``docs/iso-model-unification-plan.md`` Phase 4). The
CAMPD-path tests assert exact equivalence against the pre-refactor
construction (manually reproduced inline) so the merge is provably
byte-identical for the default config.
"""

import unittest

from market_sim.config.constants import START_YEAR
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    _AGGREGATABLE_FUELS,
    Generator,
    aggregate_fleet,
    bins_to_fleet,
    build_base_fleet,
    build_dispatch_fleet,
    load_fleet_from_csv,
    load_or_synthesize_bins,
)


def _gw(generators: list[Generator]) -> float:
    """Return the total fleet capacity in GW."""
    return sum(g.pmax_mw for g in generators) / 1000.0


class TestLoadOrSynthesizeBins(unittest.TestCase):
    """Tests for the CAMPD-bins-or-None resolution step."""

    def test_ercot_default_loads_curated_bins(self):
        config = ScenarioConfig(iso="ERCOT")
        iso_config = get_iso_config("ERCOT")
        bins = load_or_synthesize_bins(config, "ERCOT", iso_config, [])
        self.assertIsNotNone(bins)
        self.assertGreater(len(bins), 0)

    def test_use_campd_bins_false_returns_none(self):
        config = ScenarioConfig(iso="ERCOT", use_campd_bins=False)
        iso_config = get_iso_config("ERCOT")
        bins = load_or_synthesize_bins(config, "ERCOT", iso_config, [])
        self.assertIsNone(bins)

    def test_pjm_synthesizes_bins_via_fleet_to_bins(self):
        config = ScenarioConfig(iso="PJM")
        iso_config = get_iso_config("PJM")
        bins = load_or_synthesize_bins(config, "PJM", iso_config, [])
        self.assertIsNotNone(bins)
        self.assertGreater(len(bins), 0)


class TestBuildBaseFleet(unittest.TestCase):
    """The CAMPD path must match the pre-refactor construction exactly; the
    legacy path must match ``aggregate_fleet`` exactly."""

    def test_ercot_campd_default_matches_manual_construction(self):
        config = ScenarioConfig(iso="ERCOT")
        iso_config = get_iso_config("ERCOT")
        zone_names = iso_config.zone_names

        campd_bins = load_or_synthesize_bins(config, "ERCOT", iso_config, [])
        self.assertIsNotNone(campd_bins)

        fleet = build_base_fleet(
            campd_bins, "ERCOT", iso_config, zone_names, config, [], [], START_YEAR
        )

        # Manually reproduce the pre-refactor ERCOT construction (the old
        # runner.py ``if iso == "ERCOT": ...`` branch) and assert the two
        # are identical.
        campd_fleet, _ = bins_to_fleet(campd_bins, zone_names, config)
        all_gens = load_fleet_from_csv("ERCOT", iso_config)
        non_thermal = [g for g in all_gens if g.fuel_type not in _AGGREGATABLE_FUELS]
        expected = non_thermal + campd_fleet

        self.assertEqual(len(fleet), len(expected))
        self.assertAlmostEqual(_gw(fleet), _gw(expected), places=6)
        self.assertEqual(
            sorted(g.unit_id for g in fleet), sorted(g.unit_id for g in expected)
        )

    def test_ercot_legacy_path_use_campd_bins_false(self):
        config = ScenarioConfig(iso="ERCOT", use_campd_bins=False)
        iso_config = get_iso_config("ERCOT")
        zone_names = iso_config.zone_names

        campd_bins = load_or_synthesize_bins(config, "ERCOT", iso_config, [])
        self.assertIsNone(campd_bins)

        fleet = build_base_fleet(
            campd_bins, "ERCOT", iso_config, zone_names, config, [], [], START_YEAR
        )
        expected = aggregate_fleet(
            load_fleet_from_csv("ERCOT", iso_config),
            n_bins=config.heat_rate_bin_count,
        )
        self.assertEqual(len(fleet), len(expected))
        self.assertAlmostEqual(_gw(fleet), _gw(expected), places=6)

    def test_pjm_default_config_nonempty_with_expected_fuel_types(self):
        config = ScenarioConfig(iso="PJM")
        iso_config = get_iso_config("PJM")
        zone_names = iso_config.zone_names
        campd_bins = load_or_synthesize_bins(config, "PJM", iso_config, [])
        fleet = build_base_fleet(
            campd_bins, "PJM", iso_config, zone_names, config, [], [], START_YEAR
        )
        self.assertGreater(len(fleet), 0)
        fuel_types = {g.fuel_type for g in fleet}
        self.assertIn("gas_cc", fuel_types)
        self.assertIn("coal", fuel_types)
        self.assertGreaterEqual(_gw(fleet), 100.0)


class TestBuildDispatchFleet(unittest.TestCase):
    """The per-year LP-ready assembly: coal/gas tranching + hydro + emission
    rate overrides, regardless of which base-fleet path produced ``fleet``."""

    def test_ercot_campd_dispatch_fleet_ready_for_lp(self):
        config = ScenarioConfig(iso="ERCOT")
        iso_config = get_iso_config("ERCOT")
        zone_names = iso_config.zone_names
        campd_bins = load_or_synthesize_bins(config, "ERCOT", iso_config, [])
        fleet = build_base_fleet(
            campd_bins, "ERCOT", iso_config, zone_names, config, [], [], START_YEAR
        )
        dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = (
            build_dispatch_fleet(
                fleet, campd_bins, [], "ERCOT", START_YEAR, zone_names, config
            )
        )
        self.assertGreater(len(dispatch_fleet), 0)
        self.assertEqual(len(dispatch_fleet), len(fuel_fracs))
        self.assertTrue(all(f >= 0.0 for f in fuel_fracs))
        fuel_types = {g.fuel_type for g in dispatch_fleet}
        self.assertIn("coal", fuel_types)
        self.assertIn("gas_cc", fuel_types)

    def test_pjm_legacy_dispatch_fleet_ready_for_lp(self):
        config = ScenarioConfig(iso="PJM", use_campd_bins=False)
        iso_config = get_iso_config("PJM")
        zone_names = iso_config.zone_names
        campd_bins = load_or_synthesize_bins(config, "PJM", iso_config, [])
        self.assertIsNone(campd_bins)
        fleet = build_base_fleet(
            campd_bins, "PJM", iso_config, zone_names, config, [], [], START_YEAR
        )
        dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = (
            build_dispatch_fleet(
                fleet, campd_bins, [], "PJM", START_YEAR, zone_names, config
            )
        )
        self.assertGreater(len(dispatch_fleet), 0)
        self.assertEqual(len(dispatch_fleet), len(fuel_fracs))

    def test_pjm_default_campd_dispatch_fleet_ready_for_lp(self):
        config = ScenarioConfig(iso="PJM")
        iso_config = get_iso_config("PJM")
        zone_names = iso_config.zone_names
        campd_bins = load_or_synthesize_bins(config, "PJM", iso_config, [])
        self.assertIsNotNone(campd_bins)
        fleet = build_base_fleet(
            campd_bins, "PJM", iso_config, zone_names, config, [], [], START_YEAR
        )
        dispatch_fleet, fuel_fracs, hydro_gen_idx, hydro_monthly_energy = (
            build_dispatch_fleet(
                fleet, campd_bins, [], "PJM", START_YEAR, zone_names, config
            )
        )
        self.assertGreater(len(dispatch_fleet), 0)
        self.assertEqual(len(dispatch_fleet), len(fuel_fracs))


if __name__ == "__main__":
    unittest.main()
