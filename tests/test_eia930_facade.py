"""Facade re-export test for the ``data/eia930`` package split (W-D2).

Pins the compatibility contract of the ``data/eia_loader.py`` facade: the
historical import path must keep resolving the ENTIRE pre-split module
surface (public loaders, script/test-imported privates, and the config
re-imports that lived in the old module namespace), and historical
``mock.patch("market_sim.data.eia_loader.<name>")`` targets must keep
intercepting the package internals. The facade achieves this by aliasing
itself to :mod:`market_sim.data.eia930` via ``sys.modules``, so both module
paths are ONE namespace object.

``_EXPECTED_SURFACE`` below is the frozen inventory of every top-level name
the pre-split ``eia_loader.py`` (3,239 lines, main @ 8dc39e9) defined or
re-exported. Removing a name from the facade is a breaking change for the
~45 script importers and the test suite — extend this list, never prune it.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Every top-level name defined by the pre-split eia_loader.py ...
_DEFINED = (
    "logger",
    "DATA_DIR",
    "_ZONAL_LOAD_DIR",
    "_PJM_ZONAL_LOAD_DIR",
    "_ERCOT_LOAD_ZONE_GROUPS",
    "_CAISO_TAC_ZONE_WEIGHTS",
    "_NYISO_LOAD_ZONE_GROUPS",
    "_NYISO_ZONAL_LOAD_DIR",
    "_NEISO_LOAD_ZONE_GROUPS",
    "_CAISO_TAC_MIN_HOURS",
    "_PJM_INTERCHANGE_DIR",
    "_PJM_LOAD_ZONE_GROUPS",
    "_MONTH_START_HOUR",
    "_DEMAND_PROFILES_FILE",
    "_DEMAND_META_FILE",
    "_GENERATION_PROFILES_FILE",
    "_ISO_TO_HOURLY_BA",
    "_ERCO_HOURLY_FILE",
    "_META_FIELDS",
    "_CLEAN_FLAG_TRUE",
    "_ISO_LOCAL_TZ",
    "_CLEAN_DEMAND_ISOS",
    "_CLEAN_GEN_FUEL_TO_BENCHMARK",
    "_use_clean",
    "_read_clean_seam",
    "_clean_local_year_rows",
    "_read_clean_iso_year",
    "_clean_system_demand",
    "_REGEN_DEMAND_PROFILE_CMD",
    "DemandProfileNotRepairedError",
    "_demand_profile_raw_pairs",
    "_demand_profile_clean",
    "_clean_generation_by_fuel",
    "_eia_hourly_path",
    "_eia_hourly_frame",
    "_HOURLY_FRAME_MAX_GAP",
    "_eia_hourly_frame_filled",
    "measured_monthly_hydro",
    "climatological_monthly_hydro",
    "_hydro_wat_month_hod",
    "measured_hydro_hourly_envelope",
    "measured_interchange_envelope",
    "measured_gas_floor_profile",
    "_LW_RAW",
    "_DOWNSTATE_RAW",
    "_load_weather_from_raw",
    "load_weather",
    "_broadcast_daily_to_hourly",
    "iso_zone_tmax",
    "neiso_load_weighted_temp",
    "_CAISO_IMPORT_TRANCHE_HUB",
    "measured_import_hub_prices",
    "measured_intertie_hub_price_raw",
    "measured_miso_pjm_border_prices",
    "_CAISO_INTERCHANGE_LAG_STD_H",
    "_CAISO_INTERCHANGE_LAG_DST_H",
    "_CAISO_DEMAND_CLOCK_LAG_H",
    "_CAISO_DEMAND_CLOCK_REALIGN_END",
    "_caiso_interchange_model_clock",
    "measured_corridor_flow_envelope",
    "measured_firm_import_shape",
    "caiso_solar_fraction",
    "measured_seam_import_envelope",
    "_EIA930_LONG_REGION_COLUMNS",
    "_fill_hourly_frame_from_long",
    "_ercot_hourly_frame",
    "_load_ercot_hourly",
    "_load_caiso_supply_consistent_demand",
    "_load_caiso_hourly_demand",
    "_load_nyiso_hourly_demand",
    "_load_neiso_hourly_demand",
    "_load_miso_hourly_demand",
    "_load_pjm_hourly_demand",
    "load_ercot_renewable_gen",
    "_EIA930_BENCHMARK_COLUMNS",
    "_STORAGE_BENCHMARK_SERIES",
    "_STORAGE_MIN_COVERAGE_FRAC",
    "_pad_to_year",
    "load_eia_hourly_benchmark",
    "load_eia_hourly_renewable_gen",
    "load_ercot_fossil_gen",
    "load_ercot_nuclear_gen",
    "load_ercot_other_gen",
    "load_ercot_battery_gen",
    "_filter_iso_year",
    "_hours_of_year",
    "_hourly_shares_from_groups",
    "_validate_zonal_shares",
    "_zonal_shares_from_raw",
    "load_zonal_shares",
    "_MISO_SUBBA_ZONE_GROUPS",
    "_miso_utc_to_local_hoy",
    "pjm_net_interchange",
    "_PJM_TIE_ZONE",
    "_PJM_TIE_ZONE_DEFAULT",
    "pjm_zonal_interchange",
    "pjm_zonal_interchange_envelope",
    "_eia930_net_interchange",
    "nyiso_net_interchange",
    "nyiso_forward_net_import_monthly",
    "neiso_net_interchange",
    "_SCALAR_INTERCHANGE_ISOS",
    "load_demand",
    "load_demand_meta",
    "load_generation_profiles",
)

# ... plus the config names its from-imports put in the module namespace
# (tests patch CALIBRATION_DIR / EIA_HOURLY_DIR here; scripts read others).
_CONFIG_REEXPORTS = (
    "CAISO_TAC_ZONE_WEIGHTS",
    "HOURS_PER_YEAR",
    "CAISO_IMPORT_TRANCHE_HUB",
    "ISOConfig",
    "get_iso_config",
    "CALIBRATION_DIR",
    "EIA_930_DIR",
    "EIA_HOURLY_DIR",
    "ISO_TRANSMISSION_DIR",
    "RAW_DIR",
    "ZONE_DEMAND_DIR",
)

_EXPECTED_SURFACE = _DEFINED + _CONFIG_REEXPORTS + ("DEMAND_LOADERS",)


class TestFacadeAlias(unittest.TestCase):
    """The facade and the package are one module object (one namespace)."""

    def test_facade_is_the_package(self):
        import market_sim.data.eia930 as pkg
        import market_sim.data.eia_loader as facade

        self.assertIs(facade, pkg)

    def test_from_import_resolves_to_the_package(self):
        import market_sim.data.eia930 as pkg
        from market_sim.data import eia_loader

        self.assertIs(eia_loader, pkg)


class TestFacadeSurface(unittest.TestCase):
    """Every pre-split top-level name still resolves via the facade."""

    def test_entire_pre_split_surface_resolves(self):
        import market_sim.data.eia_loader as m

        missing = [n for n in _EXPECTED_SURFACE if not hasattr(m, n)]
        self.assertEqual(missing, [], f"facade lost {len(missing)} name(s)")

    def test_named_from_imports_resolve(self):
        # The two import styles the ~45 script importers actually use.
        from market_sim.data.eia_loader import (  # noqa: F401
            DemandProfileNotRepairedError,
            _eia_hourly_frame_filled,
            load_demand,
            load_zonal_shares,
        )


class TestDemandLoaderRegistry(unittest.TestCase):
    """DEMAND_LOADERS replaces the if/elif ladder, keyed on SUPPORTED_ISOS names."""

    def test_keys_are_supported_isos(self):
        from market_sim.config.iso_configs import SUPPORTED_ISOS
        from market_sim.data.eia_loader import DEMAND_LOADERS

        self.assertTrue(set(DEMAND_LOADERS) <= set(SUPPORTED_ISOS))
        # The six ISOs with a dedicated per-BA demand source today.
        self.assertEqual(
            set(DEMAND_LOADERS),
            {"ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"},
        )

    def test_entries_are_callable(self):
        from market_sim.data.eia_loader import DEMAND_LOADERS

        for iso, fn in DEMAND_LOADERS.items():
            self.assertTrue(callable(fn), iso)


class TestPatchSemantics(unittest.TestCase):
    """Historical facade patch targets keep reaching package internals."""

    def test_patch_load_zonal_shares_reaches_demand_path(self):
        import market_sim.data.eia930.demand as demand_mod

        with mock.patch(
            "market_sim.data.eia_loader.load_zonal_shares", return_value=None
        ) as patched:
            self.assertIs(demand_mod._pkg_ns().load_zonal_shares, patched)

    def test_patch_pjm_loader_reaches_registry_adapter(self):
        import market_sim.data.eia930.demand as demand_mod

        with mock.patch(
            "market_sim.data.eia_loader._load_pjm_hourly_demand", return_value=None
        ) as patched:
            self.assertIs(demand_mod._pkg_ns()._load_pjm_hourly_demand, patched)
            self.assertEqual(demand_mod._pjm_demand_source(2024, {}), (None, None))

    def test_patch_calibration_dir_reaches_envelopes(self):
        import market_sim.data.eia_loader as facade
        import market_sim.data.eia930.envelopes as envelopes

        probe = facade.CALIBRATION_DIR / "does-not-exist"
        with mock.patch.object(facade, "CALIBRATION_DIR", probe):
            self.assertEqual(envelopes._calibration_dir(), probe)


if __name__ == "__main__":
    unittest.main()
