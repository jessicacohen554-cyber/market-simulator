"""Facade re-export test for the ``model/capacity_evolution`` package split (W-D4).

Pins the compatibility contract of the ``model/capacity.py`` facade: the
historical import path must keep resolving the ENTIRE pre-split module
surface (public functions, script/test-imported privates, and the
config/data/policy re-imports that lived in the old module namespace), and
historical ``mock.patch("market_sim.model.capacity.<name>")`` /
probe-style ``capacity.<name> = wrapped`` targets must keep intercepting the
package internals. The facade achieves this by aliasing itself to
:mod:`market_sim.model.capacity_evolution` via ``sys.modules``, so both
module paths are ONE namespace object.

``_EXPECTED_SURFACE`` below is the frozen inventory of every top-level name
the pre-split ``capacity.py`` (4,269 lines, main @ e2ada84) defined or
re-exported. Removing a name from the facade is a breaking change for the
src/scripts importers and the test suite — extend this list, never prune it.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Every top-level name defined by the pre-split capacity.py ...
_DEFINED = (
    "logger",
    # retirements (steps 0/1/3 + shared capacity-market/adequacy helpers)
    "_THERMAL_FOM",
    "_CLEAN_FUELS",
    "_RPS_ELIGIBLE_FUELS",
    "_FIRM_CLEAN_FUELS",
    "_RETIREMENT_YEARS",
    "_RETIREMENT_EXECUTION_LAG",
    "_execution_lag_years",
    "_FOM_MULTIPLIER",
    "_THERMAL_PLANT_LIFE_YEARS",
    "_NEW_ENTRY_DEFAULT_ZONE",
    "_default_build_zone",
    "compute_attribute_revenue",
    "_FOSSIL_FUELS",
    "_confirmed_effective_year",
    "_unit_generator_id",
    "_CONFIRMED_EXIT_MW_EPS",
    "apply_confirmed_exits",
    "_is_confirmed_binned",
    "_derate_generator",
    "apply_announced_retirements",
    "compute_clean_share",
    "_dispatch_rows",
    "capacity_revenue_per_mw_yr",
    "_DELIVERABILITY_LONG_BAND",
    "deliverability_headroom_by_zone",
    "_zone_is_long",
    "resolve_planning_reserve_margin",
    "_storage_portfolio_elcc_dilution",
    "resolve_forecast_pool_requirement",
    "resolve_adequacy_requirement_mw",
    "thermal_accreditation_fraction",
    "_thermal_firm_mw",
    "_renewable_credit",
    "resolve_renewable_capacity_credit",
    "_floor_retention_merit",
    "_apply_reliability_floor",
    "_apply_pipeline_retirements",
    "apply_economic_retirements",
    # new_entry (step 5)
    "_NEW_ENTRY_TECHS",
    "_RENEWABLE_NEW_FUELS",
    "_EMERGING_AVAILABLE_YEAR",
    "_QUEUE_CAP_GROUP",
    "_EMERGING_SCREEN_CF",
    "_offshore_wind_params",
    "_emerging_screen_cf",
    "_new_entry_candidates",
    "_emerging_lcoe",
    "CumulativeDeployment",
    "_merge_renewable_additions",
    "wright_cost",
    "_capital_recovery_factor",
    "compute_lcoe",
    "estimate_expected_revenue",
    "_make_new_generator",
    "apply_economic_new_entry",
    # adequacy (ledger + step-6 backstop)
    "_renewable_nameplate_by_fuel",
    "renewable_credits_applied",
    "_firm_import_mw",
    "accredited_firm_capacity_mw",
    "capacity_reserve_position",
    "resolve_reserve_margin_build_enabled",
    "apply_reserve_margin_build",
    # ccs (step 2)
    "_adjust_retrofit_capex",
    "_ccs_45q_window_years",
    "_ccs_retrofit_payback_years",
    "_retrofit_price_row",
    "apply_ccs_retrofit",
    # evolve (the one-pass year step)
    "_prior_attr",
    "evolve_fleet",
)

# ... plus the config/data/policy names its from-imports put in the module
# namespace (patch.dict targets MARKET_DESIGN here; scripts read others).
_CONFIG_REEXPORTS = (
    "ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO",
    "ADEQUACY_EXTERNAL_TIE_FIRM_MW",
    "CCUS_PARAMS",
    "CO2_RATES",
    "DEFAULT_MARKET_DESIGN",
    "EFORD",
    "FORECAST_POOL_REQUIREMENT_BY_ISO",
    "GEOTHERMAL_PARAMS",
    "GLOBAL_ANNUAL_DEPLOYMENT_GW",
    "HEAT_RATE_BINS",
    "HOURS_PER_YEAR",
    "HYDROGEN_TURBINE_PARAMS",
    "MARKET_DESIGN",
    "NEW_ENTRY_COSTS",
    "NONFOSSIL_ANNOUNCED_HORIZON_YEARS",
    "NOX_RATES",
    "OFFSHORE_WIND_PARAMS",
    "PLANNING_RESERVE_MARGIN_BY_ISO",
    "PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO",
    "QUEUE_CAP_GW",
    "QUEUE_CAP_PER_TECH_GW",
    "RENEWABLE_CAPACITY_CREDIT",
    "RENEWABLE_CAPACITY_CREDIT_BY_ISO",
    "RENEWABLE_ELCC_CURVES_BY_ISO",
    "STORAGE_DEPLOYMENT_CEILING_MW",
    "STORAGE_ELCC_DILUTION_CEILING_RATIO_BY_ISO",
    "STORAGE_ELCC_DILUTION_REFERENCE_MW_BY_ISO",
    "THERMAL_ACCREDITATION_BASIS_BY_ISO",
    "THERMAL_ELCC_CLASS_RATING_BY_ISO",
    "VOM",
    "WRIGHT_REFERENCE_GW",
    "evaluate_renewable_elcc_curve",
    "aggregate_by_zone",
    "ENTRY_COD_LAG_DEFAULT_YEARS",
    "ENTRY_COD_LAG_YEARS",
    "get_iso_config",
    "QUICK_START_FUEL_TYPES",
    "RESERVE_FUEL_TYPES",
    "ScenarioConfig",
    "resolve_new_entry_costs",
    "resolve_real_discount_rate",
    "capdel",
    "as_revenue_per_mw_yr",
    "ConfirmedExit",
    "EIA860_OPERABLE_VINTAGE",
    "FleetArrays",
    "Generator",
    "aggregate_fleet",
    "compute_h2_fuel_cost",
    "get_renewable_zone",
    "DispatchResult",
    "effective_eac_price_for_tech",
    "effective_eac_price_for_unit",
    "apply_ira_credits_to_lcoe",
    "ccus_45q_credit_per_mwh",
    "h2_45v_credit_per_mmbtu",
    "section_45u_credit_per_mwh",
)

_EXPECTED_SURFACE = _DEFINED + _CONFIG_REEXPORTS


class TestFacadeAlias(unittest.TestCase):
    """The facade and the package are one module object (one namespace)."""

    def test_facade_is_the_package(self):
        import market_sim.model.capacity as facade
        import market_sim.model.capacity_evolution as pkg

        self.assertIs(facade, pkg)

    def test_from_import_resolves_to_the_package(self):
        import market_sim.model.capacity_evolution as pkg
        from market_sim.model import capacity

        self.assertIs(capacity, pkg)


class TestFacadeSurface(unittest.TestCase):
    """Every pre-split top-level name still resolves via the facade."""

    def test_entire_pre_split_surface_resolves(self):
        import market_sim.model.capacity as m

        missing = [n for n in _EXPECTED_SURFACE if not hasattr(m, n)]
        self.assertEqual(missing, [], f"facade lost {len(missing)} name(s)")

    def test_named_from_imports_resolve(self):
        # The import styles the src/script importers actually use.
        from market_sim.model.capacity import (  # noqa: F401
            CumulativeDeployment,
            _FIRM_CLEAN_FUELS,
            _storage_portfolio_elcc_dilution,
            accredited_firm_capacity_mw,
            apply_confirmed_exits,
            compute_lcoe,
            evolve_fleet,
            resolve_adequacy_requirement_mw,
        )

    def test_step_functions_defined_in_their_planned_modules(self):
        # The plan §5 item 4 module map — a name silently migrating between
        # submodules is a refactor regression even if the facade still works.
        from market_sim.model.capacity_evolution import (
            adequacy,
            ccs,
            evolve,
            new_entry,
            retirements,
        )

        for mod, names in (
            (
                retirements,
                (
                    "apply_confirmed_exits",
                    "apply_announced_retirements",
                    "resolve_adequacy_requirement_mw",
                    "apply_economic_retirements",
                    "_apply_reliability_floor",
                ),
            ),
            (new_entry, ("_new_entry_candidates", "apply_economic_new_entry")),
            (adequacy, ("apply_reserve_margin_build", "accredited_firm_capacity_mw")),
            (
                ccs,
                (
                    "_adjust_retrofit_capex",
                    "_ccs_45q_window_years",
                    "_ccs_retrofit_payback_years",
                    "_retrofit_price_row",
                    "apply_ccs_retrofit",
                ),
            ),
            (evolve, ("evolve_fleet",)),
        ):
            for name in names:
                fn = getattr(mod, name)
                self.assertEqual(fn.__module__, mod.__name__, name)


class TestPatchSemantics(unittest.TestCase):
    """Historical facade patch targets keep reaching package internals."""

    def test_patch_estimate_expected_revenue_reaches_new_entry_path(self):
        import market_sim.model.capacity_evolution.new_entry as new_entry_mod

        with mock.patch(
            "market_sim.model.capacity.estimate_expected_revenue", return_value=0.0
        ) as patched:
            self.assertIs(new_entry_mod._pkg_ns().estimate_expected_revenue, patched)

    def test_patch_step_functions_reach_evolve_path(self):
        # run_foresight_ab.py / the confirmed-retirement probe wrap the step
        # functions on the capacity namespace and rely on evolve_fleet calling
        # the wrappers.
        import market_sim.model.capacity_evolution.evolve as evolve_mod

        for step in (
            "apply_confirmed_exits",
            "apply_announced_retirements",
            "apply_ccs_retrofit",
            "apply_economic_retirements",
            "apply_economic_new_entry",
            "apply_reserve_margin_build",
        ):
            with mock.patch(
                f"market_sim.model.capacity.{step}", return_value=None
            ) as patched:
                self.assertIs(getattr(evolve_mod._pkg_ns(), step), patched, step)

    def test_probe_style_attribute_write_reaches_evolve_path(self):
        # Probe scripts assign wrappers directly (capacity.<name> = wrapped)
        # rather than using mock.patch; the namespace write must be seen too.
        import market_sim.model.capacity as facade
        import market_sim.model.capacity_evolution.evolve as evolve_mod

        original = facade.apply_economic_retirements
        sentinel = object()
        try:
            facade.apply_economic_retirements = sentinel
            self.assertIs(evolve_mod._pkg_ns().apply_economic_retirements, sentinel)
        finally:
            facade.apply_economic_retirements = original

    def test_market_design_is_the_shared_registry_object(self):
        # mock.patch.dict("market_sim.model.capacity.MARKET_DESIGN", ...)
        # mutates the dict object in place, so every submodule must reference
        # the ONE registry object for the patch to be visible everywhere.
        import market_sim.model.capacity as facade
        import market_sim.model.capacity_evolution.adequacy as adequacy_mod
        import market_sim.model.capacity_evolution.new_entry as new_entry_mod
        import market_sim.model.capacity_evolution.retirements as retirements_mod

        self.assertIs(facade.MARKET_DESIGN, retirements_mod.MARKET_DESIGN)
        self.assertIs(facade.MARKET_DESIGN, new_entry_mod.MARKET_DESIGN)
        self.assertIs(facade.MARKET_DESIGN, adequacy_mod.MARKET_DESIGN)

    def test_cumulative_deployment_is_one_class(self):
        from market_sim.model.capacity import CumulativeDeployment as via_facade
        from market_sim.model.capacity_evolution.new_entry import (
            CumulativeDeployment as via_package,
        )

        self.assertIs(via_facade, via_package)


if __name__ == "__main__":
    unittest.main()
