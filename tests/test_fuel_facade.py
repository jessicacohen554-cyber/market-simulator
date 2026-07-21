"""Facade re-export + registry parity tests for the ``data/fuel`` package split (W-D3).

Pins the compatibility contract of the ``market_sim.data.fuel`` package: the
package took over the EXACT import path of the pre-split ``data/fuel.py``
module (no ``sys.modules`` alias needed — that construction exists for renamed
paths like ``eia_loader`` -> ``eia930``), so the package ``__init__`` must keep
resolving the ENTIRE pre-split module surface (public functions,
script/test-imported privates, module-level caches, path constants, and the
config/data re-imports that lived in the old module namespace), and historical
``monkeypatch.setattr("market_sim.data.fuel.<name>", ...)`` /
``mock.patch.object(fuel, ...)`` / direct attribute-write targets must keep
intercepting the package internals (resolved at call time via
``_shared._pkg_ns``).

``_EXPECTED_SURFACE`` below is the frozen inventory of every top-level name the
pre-split ``fuel.py`` (4,758 lines, main @ e2ada84) defined or re-exported.
Removing a name from the facade is a breaking change for the 3 src / 17 script
/ 11 test importer files — extend this list, never prune it.

Also pins the ``ZONAL_BASIS_APPLIERS`` registry (basis/__init__.py): its
entries must BE the per-ISO appliers and must produce arrays identical to
calling the standalone functions on a fixture year, per ISO (rule 25 guard:
the registry can never silently re-point an ISO at another ISO's — or a
generic — basis implementation).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Every top-level name defined by the pre-split fuel.py ...
_DEFINED = (
    "logger",
    "_GAS_FUEL_IDX",
    "_GAS_PRICE_FLOOR",
    "_COAL_FUEL_IDX",
    "_OIL_FUEL_IDX",
    "_BIOMASS_FUEL_IDX",
    "_HYDROGEN_FUEL_IDX",
    "_NUCLEAR_FUEL_IDX",
    "_ZERO_FUEL_PRICE",
    "_DAYS_IN_MONTH",
    "_USE_CLEAN_ENV",
    "_USE_CLEAN_TRUTHY",
    "_use_clean_data",
    "_hold_flat_extrapolate",
    "resolve_annual_gas_price",
    "resolve_annual_coal_price",
    "resolve_annual_oil_price",
    "resolve_nuclear_fuel_price",
    "_seasonal_factors",
    "gas_seasonal_shape",
    "_COAL_SIGMOID_FIELD_STEM",
    "_COAL_SIGMOID_PARAMS",
    "coal_sigmoid_params",
    "coal_passthrough_series",
    "coal_passthrough_by_supply",
    "prb_follower_passthrough_series",
    "_gas_series",
    "_sigmoid_passthrough",
    "_F923_FUEL_GROUP_BY_FUEL",
    "_month_index",
    "_PLANT_MONTHLY_CACHE",
    "_load_monthly_cache",
    "_expand_monthly_to_hourly",
    "_iso_monthly_fuel_prices",
    "iso_monthly_gas_prices",
    "iso_monthly_oil_prices",
    "WINTER_GAS_BASIS_PATH",
    "NYISO_ZONAL_GAS_HUB_PATH",
    "NYISO_GAS_HUB_REFERENCE_ZONE",
    "ERCOT_ZONAL_GAS_HUB_PATH",
    "PJM_ZONAL_GAS_HUB_PATH",
    "MISO_ZONAL_GAS_HUB_PATH",
    "CAISO_ZONAL_GAS_HUB_PATH",
    "ERCOT_ELECTRIC_POWER_GAS_PATH",
    "ERCOT_GAS_TAKEORPAY_PATH",
    "ERCOT_BIN_ASSIGNMENTS_PATH",
    "_MCF_TO_MMBTU",
    "HENRY_HUB_MONTHLY_PATH",
    "HENRY_HUB_DAILY_PATH",
    "TRANSCO_Z6_NY_DAILY_PATH",
    "ALGONQUIN_DAILY_PATH",
    "IROQUOIS_Z2_DAILY_PATH",
    "CAISO_CITYGATE_DAILY_PATH",
    "MISO_CITYGATE_DAILY_PATH",
    "PGE_SOCAL_CITYGATE_WEEKLY_PATH",
    "TRANSCO_IROQUOIS_MONTHLY_PATH",
    "NYISO_DOWNSTATE_CT_GAS_BASIS_PATH",
    "_WINTER_BASIS_CACHE",
    "_HH_MONTHLY_CACHE",
    "_HH_DAILY_CACHE",
    "_HH_DAILY_DATED_CACHE",
    "_TRANSCO_DAILY_CACHE",
    "_TRANSCO_DAILY_DATED_CACHE",
    "_ALGONQUIN_DAILY_CACHE",
    "_IROQUOIS_DAILY_CACHE",
    "_CAISO_CITYGATE_DAILY_CACHE",
    "_MISO_CITYGATE_DAILY_CACHE",
    "_FUEL_PRICES_DATATYPE",
    "_FUEL_HUB_MONTHLY_DATATYPE",
    "_FUEL_BASIS_DATATYPE",
    "_FUEL_ZONAL_HUB_DATATYPE",
    "_FUEL_ERCOT_EP_GAS_DATATYPE",
    "_FUEL_TAKEORPAY_DATATYPE",
    "_HENRY_HUB_CLEAN_KEY",
    "_HH_DAILY_CLEAN_CACHE",
    "_HH_DAILY_DATED_CLEAN_CACHE",
    "_WINTER_BASIS_CLEAN_CACHE",
    "_HH_MONTHLY_CLEAN_CACHE",
    "_ALGONQUIN_DAILY_CLEAN_CACHE",
    "_CAISO_CITYGATE_DAILY_CLEAN_CACHE",
    "_NYISO_ZONAL_HUB_CLEAN_CACHE",
    "_ERCOT_ZONAL_HUB_CLEAN_CACHE",
    "_ERCOT_EP_GAS_CLEAN_CACHE",
    "_ERCOT_GAS_SPOT_PLANT_CLEAN_CACHE",
    "_ERCOT_GAS_SPOT_ZONE_CLEAN_CACHE",
    "_ZONAL_HUB_ISO_CLEAN_CACHE",
    "_clean_fuel_price_daily",
    "_clean_fuel_price_daily_dated",
    "_clean_hub_monthly",
    "_clean_algonquin_daily",
    "_clean_caiso_citygate_daily",
    "_clean_zonal_hub_frame",
    "_clean_ercot_ep_gas_frame",
    "_clean_takeorpay_plant_dict",
    "_load_winter_basis_frame",
    "load_winter_gas_basis",
    "_henry_hub_monthly",
    "_henry_hub_daily",
    "_henry_hub_daily_dated",
    "_transco_z6_daily",
    "_algonquin_daily",
    "_transco_z6_daily_dated",
    "_iroquois_z2_daily",
    "_caiso_citygate_daily_dated",
    "_miso_citygate_daily_dated",
    "socal_citygate_weekly_hourly",
    "gas_daily_shape_factors",
    "iso_hub_monthly_gas_prices",
    "_nyiso_hub_daily_gas_prices",
    "_flow_date_staircase",
    "_trade_date_staircase",
    "_caiso_hub_daily_gas_prices",
    "iso_hub_daily_gas_prices",
    "apply_hub_basis_overlay",
    "_NYISO_ZONAL_HUB_CACHE",
    "_load_nyiso_zonal_gas_hub",
    "nyiso_zonal_gas_offsets",
    "nyiso_reconciled_reference_monthly",
    "nyiso_zonal_gas_ratios_monthly",
    "apply_nyiso_zonal_gas_basis",
    "_NYISO_DOWNSTATE_CT_BASIS_CACHE",
    "NYISO_DOWNSTATE_CT_ZONES",
    "nyiso_downstate_ct_gas_premium",
    "apply_nyiso_downstate_ct_gas_basis",
    "_zone_delivered_hourly",
    "_downstate_delivered_gas_hourly_by_zone",
    "apply_nyiso_downstate_ct_gas_daily",
    "_ERCOT_ZONAL_HUB_CACHE",
    "_load_ercot_zonal_gas_hub",
    "ercot_zonal_gas_basis_by_zone",
    "ercot_waha_collapse_freq",
    "_ERCOT_EP_GAS_CACHE",
    "_load_ercot_electric_power_gas",
    "ercot_electric_power_gas_basis",
    "_ERCOT_GAS_SPOT_CACHE",
    "_ERCOT_GAS_SPOT_PLANT_CACHE",
    "ercot_gas_spot_share_by_plant",
    "ercot_gas_spot_share_by_zone",
    "apply_ercot_zonal_gas_basis",
    "_ZONAL_HUB_CACHE",
    "_load_zonal_gas_hub",
    "_zonal_gas_basis_by_zone",
    "pjm_zonal_gas_basis_by_zone",
    "miso_zonal_gas_basis_by_zone",
    "_apply_meanzero_zonal_gas_basis",
    "apply_pjm_zonal_gas_basis",
    "apply_miso_zonal_gas_basis",
    "_MISO_WINTER_MONTHS",
    "_miso_chicago_hub_zones",
    "miso_chicago_daily_shape_factors",
    "apply_miso_winter_citygate_daily",
    "caiso_zonal_gas_basis_by_zone",
    "apply_caiso_zonal_gas_basis",
    "_WEST_GAS_COLLAPSE_FREQ_DEFAULT",
    "_ERCOT_WAHA_ZONES",
    "ercot_west_oversupply_collapse_freq",
    "apply_ercot_west_netload_gas_shape",
    "_hub_overlay_series",
    "resolve_fuel_prices",
    "dual_fuel_oil_price_series",
    "apply_dual_fuel_pricing",
    "dual_fuel_switch_mask",
    "load_oil_burn_budget",
    "apply_plant_monthly_fuel_prices",
    "_NearbyFuelPrices",
    "_fuel_name",
    "_build_coal_price_trajectories",
    "COAL_PRICE_LIGNITE_BY_YEAR",
    "COAL_PRICE_PRB_BY_YEAR",
    "_prb_monthly_actuals",
    "apply_coal_supply_pricing",
    "resolve_nox_price",
)

# ... plus the config/data names its from-imports put in the module namespace
# (scripts/tests read several; ``dual_fuel_plant_groups`` is monkeypatched here).
_CONFIG_REEXPORTS = (
    "BIOMASS_PRICE_PER_MMBTU",
    "CAISO_CITYGATE_TRANSPORT_ADDER",
    "COAL_PRICE_BASE",
    "COAL_PRICE_ESCALATION",
    "COAL_PRICE_TRAJECTORIES",
    "END_YEAR",
    "GAS_BASIS_DIFFERENTIAL",
    "GAS_MONTHLY_SEASONALITY",
    "HENRY_HUB_TRAJECTORIES",
    "HOURS_PER_YEAR",
    "INFLATION_RATE",
    "LIGNITE_PRICE_2023_25",
    "NUCLEAR_FUEL_PRICE_HISTORICAL",
    "OIL_PRICE_PER_MMBTU",
    "OIL_PRICE_TRAJECTORIES",
    "PRB_COMMODITY_DECLINE",
    "PRB_COMMODITY_FLAT_THROUGH",
    "PRB_COMMODITY_SHARE",
    "PRB_PRICE_BY_YEAR",
    "PRB_RAIL_DIESEL_SHARE",
    "PRB_RAIL_NONDIESEL_SHARE",
    "START_YEAR",
    "GAS_PRICES_DIR",
    "RAW_DATA_DIR",
    "COAL_SIGMOID_DEFAULTS",
    "ScenarioConfig",
    "EIA923_MONTHLY_COSTS_PATH",
    "available_years",
    "load_monthly_fuel_costs",
    "plant_month_price_grid",
    "state_month_price_grid",
    "FUEL_TYPE_MAP",
    "FleetArrays",
    "dual_fuel_plant_groups",
    "compute_h2_fuel_cost",
)

_EXPECTED_SURFACE = (
    _DEFINED + _CONFIG_REEXPORTS + ("ZONAL_BASIS_APPLIERS", "ZONAL_BASIS_ORDER")
)

_REGISTRY_ISOS = ("NYISO", "ERCOT", "PJM", "MISO", "CAISO")


class TestFacadeIsThePackage(unittest.TestCase):
    """The historical import path resolves to the package (one namespace)."""

    def test_module_path_is_the_package(self):
        import market_sim.data.fuel as fuel

        self.assertTrue(hasattr(fuel, "__path__"), "fuel must be a package")
        self.assertEqual(fuel.__name__, "market_sim.data.fuel")

    def test_pkg_ns_returns_the_facade(self):
        import market_sim.data.fuel as fuel
        from market_sim.data.fuel import _shared

        self.assertIs(_shared._pkg_ns(), fuel)

    def test_submodules_importable(self):
        import market_sim.data.fuel.basis.ercot  # noqa: F401
        import market_sim.data.fuel.basis.nyiso  # noqa: F401
        import market_sim.data.fuel.coal  # noqa: F401
        import market_sim.data.fuel.dual_fuel  # noqa: F401
        import market_sim.data.fuel.hubs  # noqa: F401
        import market_sim.data.fuel.plant_prices  # noqa: F401
        import market_sim.data.fuel.resolve  # noqa: F401
        import market_sim.data.fuel.trajectories  # noqa: F401


class TestFacadeSurface(unittest.TestCase):
    """Every pre-split top-level name still resolves via the facade."""

    def test_entire_pre_split_surface_resolves(self):
        import market_sim.data.fuel as m

        missing = [n for n in _EXPECTED_SURFACE if not hasattr(m, n)]
        self.assertEqual(missing, [], f"facade lost {len(missing)} name(s)")

    def test_named_from_imports_resolve(self):
        # The import styles the src/scripts/tests importers actually use.
        from market_sim.data.fuel import (  # noqa: F401
            ALGONQUIN_DAILY_PATH,
            COAL_PRICE_LIGNITE_BY_YEAR,
            COAL_PRICE_PRB_BY_YEAR,
            HENRY_HUB_DAILY_PATH,
            _downstate_delivered_gas_hourly_by_zone,
            _expand_monthly_to_hourly,
            _henry_hub_monthly,
            _hold_flat_extrapolate,
            _load_winter_basis_frame,
            _month_index,
            _NearbyFuelPrices,
            _nyiso_hub_daily_gas_prices,
            _prb_monthly_actuals,
            _seasonal_factors,
            load_oil_burn_budget,
            resolve_fuel_prices,
            socal_citygate_weekly_hourly,
        )


class TestZonalBasisRegistry(unittest.TestCase):
    """ZONAL_BASIS_APPLIERS replaces the sequential per-ISO applier calls."""

    def test_keys_and_order(self):
        from market_sim.data.fuel import ZONAL_BASIS_APPLIERS, ZONAL_BASIS_ORDER

        self.assertEqual(set(ZONAL_BASIS_APPLIERS), set(_REGISTRY_ISOS))
        self.assertEqual(tuple(ZONAL_BASIS_ORDER), _REGISTRY_ISOS)

    def test_entries_are_the_standalone_appliers(self):
        # Rule 25 guard: each ISO's registry entry IS that ISO's own applier —
        # never another ISO's, never a generic default.
        import market_sim.data.fuel as fuel

        expected = {
            "NYISO": fuel.apply_nyiso_zonal_gas_basis,
            "ERCOT": fuel.apply_ercot_zonal_gas_basis,
            "PJM": fuel.apply_pjm_zonal_gas_basis,
            "MISO": fuel.apply_miso_zonal_gas_basis,
            "CAISO": fuel.apply_caiso_zonal_gas_basis,
        }
        for iso, fn in expected.items():
            self.assertIs(fuel.ZONAL_BASIS_APPLIERS[iso], fn, iso)


def _stub_fleet(iso: str, n_zones: int):
    """Minimal FleetArrays stand-in: one gas CC per zone + one coal unit."""
    from market_sim.data.fleet import FUEL_TYPE_MAP

    n_gas = n_zones
    fuel_type_idx = np.array(
        [FUEL_TYPE_MAP["gas_cc"]] * n_gas + [FUEL_TYPE_MAP["coal"]], dtype=int
    )
    zone_idx = np.array(list(range(n_zones)) + [0], dtype=int)
    pmax = np.array([100.0 + 10.0 * z for z in range(n_zones)] + [400.0])
    plant_code = np.array([1000 + z for z in range(n_zones)] + [2000], dtype=int)
    return SimpleNamespace(
        fuel_type_idx=fuel_type_idx,
        zone_idx=zone_idx,
        pmax=pmax,
        plant_code=plant_code,
        plant_group=None,
    )


_FLAG_BY_ISO = {
    "NYISO": "nyiso_zonal_gas_basis",
    "ERCOT": "ercot_zonal_gas_basis",
    "PJM": "pjm_zonal_gas_basis",
    "MISO": "miso_zonal_gas_basis",
    "CAISO": "caiso_zonal_gas_basis",
}


class TestZonalBasisParity(unittest.TestCase):
    """Registry entries produce arrays IDENTICAL to the standalone appliers.

    Synthetic per-ISO hub-table fixtures (written to tmp dirs, passed via each
    applier's ``path`` override) so no repo data is needed; a fixture year
    (2024) and a 48-hour horizon. Exact equality — the registry may never
    change a single byte of an ISO's basis application.
    """

    YEAR = 2024
    HOURS = 48

    def _fixture_csv(self, tmp, iso: str, zone_names: list[str]) -> Path:
        import pandas as pd

        rows = []
        if iso == "NYISO":
            # hub_usd_mmbtu levels; the reference zone must be present.
            for i, z in enumerate(zone_names):
                rows.append(
                    {"year": self.YEAR, "zone": z, "hub_usd_mmbtu": 2.0 + 0.4 * i}
                )
            df = pd.DataFrame(rows)
        else:
            for i, z in enumerate(zone_names):
                rows.append(
                    {
                        "year": self.YEAR,
                        "zone": z,
                        "basis_vs_hh_usd_mmbtu": -0.6 + 0.3 * i,
                    }
                )
            df = pd.DataFrame(rows)
        p = Path(tmp) / f"{iso.lower()}_zonal_gas_hub.csv"
        df.to_csv(p, index=False)
        return p

    def test_registry_vs_standalone_identical_arrays(self):
        import tempfile

        import market_sim.data.fuel as fuel
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.config.scenarios import ScenarioConfig

        for iso in _REGISTRY_ISOS:
            with self.subTest(iso=iso), tempfile.TemporaryDirectory() as tmp:
                zone_names = list(get_iso_config(iso).zone_names)
                fixture = self._fixture_csv(tmp, iso, zone_names)
                fleet = _stub_fleet(iso, len(zone_names))
                config = ScenarioConfig(
                    iso=iso, **{_FLAG_BY_ISO[iso]: True}
                )
                rng = np.random.default_rng(20240721)
                base = 3.0 + rng.random((fleet.fuel_type_idx.size, self.HOURS))

                a = base.copy()
                b = base.copy()
                standalone = getattr(fuel, f"apply_{iso.lower()}_zonal_gas_basis")
                standalone(a, fleet, config, self.YEAR, path=fixture)
                fuel.ZONAL_BASIS_APPLIERS[iso](b, fleet, config, self.YEAR, path=fixture)

                self.assertTrue(
                    np.array_equal(a, b),
                    f"{iso}: registry applier diverged from standalone",
                )
                # The fixture basis must actually have moved the gas rows —
                # otherwise this parity test silently degenerates to 0 == 0.
                self.assertFalse(
                    np.array_equal(a, base),
                    f"{iso}: fixture applied no basis (inert test)",
                )

    def test_other_iso_appliers_are_noops(self):
        # Each applier self-gates on config.iso: running every OTHER ISO's
        # applier against this config must leave the array untouched.
        import tempfile

        import market_sim.data.fuel as fuel
        from market_sim.config.iso_configs import get_iso_config
        from market_sim.config.scenarios import ScenarioConfig

        iso = "PJM"
        zone_names = list(get_iso_config(iso).zone_names)
        fleet = _stub_fleet(iso, len(zone_names))
        config = ScenarioConfig(iso=iso, **{_FLAG_BY_ISO[iso]: True})
        base = np.full((fleet.fuel_type_idx.size, self.HOURS), 3.0)
        with tempfile.TemporaryDirectory() as tmp:
            for other in _REGISTRY_ISOS:
                if other == iso:
                    continue
                fixture = self._fixture_csv(tmp, other, zone_names)
                arr = base.copy()
                fuel.ZONAL_BASIS_APPLIERS[other](arr, fleet, config, self.YEAR, path=fixture)
                self.assertTrue(
                    np.array_equal(arr, base), f"{other} applier fired for {iso} config"
                )


class TestPatchSemantics(unittest.TestCase):
    """Historical facade patch targets keep reaching package internals."""

    def test_patch_henry_hub_monthly_reaches_internals(self):
        from market_sim.data.fuel import _shared

        with mock.patch(
            "market_sim.data.fuel._henry_hub_monthly", return_value={}
        ) as patched:
            self.assertIs(_shared._pkg_ns()._henry_hub_monthly, patched)

    def test_patch_load_monthly_cache_reaches_internals(self):
        import market_sim.data.fuel as fuel
        from market_sim.data.fuel import _shared

        with mock.patch.object(fuel, "_load_monthly_cache", return_value=None) as p:
            self.assertIs(_shared._pkg_ns()._load_monthly_cache, p)

    def test_attribute_write_reaches_internals(self):
        # tests/test_fuel.py writes fuel.ercot_gas_spot_share_by_plant directly.
        import market_sim.data.fuel as fuel
        from market_sim.data.fuel import _shared

        orig = fuel.ercot_gas_spot_share_by_plant
        try:
            fuel.ercot_gas_spot_share_by_plant = lambda *a, **k: {1: 0.5}
            self.assertEqual(
                _shared._pkg_ns().ercot_gas_spot_share_by_plant(), {1: 0.5}
            )
        finally:
            fuel.ercot_gas_spot_share_by_plant = orig

    def test_patched_daily_dated_reaches_gas_daily_shape(self):
        # Behavioral: gas_daily_shape_factors resolves _henry_hub_daily_dated
        # and _trade_date_staircase through the shared namespace at call time
        # (both are monkeypatched by tests/test_fuel.py).
        from market_sim.data.fuel import gas_daily_shape_factors

        jan = {1: 2.0, 2: 4.0}
        with mock.patch(
            "market_sim.data.fuel._henry_hub_daily_dated",
            lambda path: {2024: {1: jan}},
        ):
            factors = gas_daily_shape_factors(2024, 48)
        self.assertFalse(np.allclose(factors, 1.0))

    def test_patch_dual_fuel_plant_groups_reaches_dual_fuel(self):
        from market_sim.data.fuel import _shared

        with mock.patch(
            "market_sim.data.fuel.dual_fuel_plant_groups",
            return_value={(1, "CC_REGULAR")},
        ) as patched:
            self.assertIs(_shared._pkg_ns().dual_fuel_plant_groups, patched)

    def test_patch_registry_dict_reaches_resolve(self):
        import market_sim.data.fuel as fuel
        from market_sim.data.fuel import _shared

        sentinel = dict(fuel.ZONAL_BASIS_APPLIERS)
        with mock.patch.object(fuel, "ZONAL_BASIS_APPLIERS", sentinel):
            self.assertIs(_shared._pkg_ns().ZONAL_BASIS_APPLIERS, sentinel)


if __name__ == "__main__":
    unittest.main()
