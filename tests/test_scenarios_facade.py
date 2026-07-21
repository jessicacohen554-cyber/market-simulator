"""Facade re-export test for the ``config/scenarios.py`` extraction (plan §5 item 9).

Pins the compatibility contract of the scenarios facade: the PB-1 resolvers
(now defined in ``config/scenario_resolvers.py``) and ``SweepDefinition`` (now
defined in ``config/sweeps.py``) must keep resolving via their historical
``market_sim.config.scenarios`` import path, as the SAME objects — every
src/scripts/tests importer uses the historical spelling. The private helpers
are part of the surface too (``data/datacenter.py`` imports
``_effective_percentile`` / ``_interpolate_low_mid_high`` from scenarios).

``ScenarioConfig`` itself is pickle-borne and its ``__module__`` is frozen at
``market_sim.config.scenarios`` — that is asserted by
``tests/test_persisted_identity.py``; here we only assert the extraction left
it DEFINED (not re-exported) at the frozen path.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

# Every name the extraction moved out of scenarios.py, keyed by its new
# defining module. Removing a re-export is a breaking change for the
# importers — extend this list, never prune it.
_MOVED_SURFACE = {
    "market_sim.config.scenario_resolvers": (
        "_PERCENTILE_BY_PATH_LABEL",
        "_NEUTRAL_PERCENTILE",
        "_interpolate_low_mid_high",
        "_effective_percentile",
        "resolve_new_entry_costs",
        "resolve_demand_growth_rate",
        "_IRA_LAST_YEAR_FIELDS",
        "_POLICY_BUNDLES",
        "resolve_policy_bundle",
    ),
    "market_sim.config.sweeps": ("SweepDefinition",),
}


class TestScenariosFacadeSurface(unittest.TestCase):
    """Every moved name resolves via scenarios AND is the one new-home object."""

    def test_moved_names_resolve_via_facade_as_same_objects(self):
        import importlib

        import market_sim.config.scenarios as scenarios

        for new_module, names in _MOVED_SURFACE.items():
            home = importlib.import_module(new_module)
            for name in names:
                self.assertTrue(
                    hasattr(scenarios, name),
                    f"scenarios facade lost {name!r} — historical importers break",
                )
                self.assertIs(
                    getattr(scenarios, name),
                    getattr(home, name),
                    f"{name!r} via scenarios is not the {new_module} object",
                )

    def test_moved_callables_defined_in_their_new_modules(self):
        # A name silently migrating back (or on) is a refactor regression even
        # while the facade still resolves it.
        from market_sim.config.scenario_resolvers import (
            _effective_percentile,
            _interpolate_low_mid_high,
            resolve_demand_growth_rate,
            resolve_new_entry_costs,
            resolve_policy_bundle,
        )
        from market_sim.config.sweeps import SweepDefinition

        for obj in (
            _interpolate_low_mid_high,
            _effective_percentile,
            resolve_new_entry_costs,
            resolve_demand_growth_rate,
            resolve_policy_bundle,
        ):
            self.assertEqual(obj.__module__, "market_sim.config.scenario_resolvers")
        self.assertEqual(SweepDefinition.__module__, "market_sim.config.sweeps")

    def test_historical_import_styles_resolve(self):
        # The import spellings the live importers actually use (runner.py,
        # matrix.py, data/datacenter.py, scripts/ff_readiness_battery.py,
        # scripts/pb5_*.py, and the test suite).
        from market_sim.config.scenarios import (  # noqa: F401
            ScenarioConfig,
            SweepDefinition,
            _effective_percentile,
            _interpolate_low_mid_high,
            resolve_demand_growth_rate,
            resolve_new_entry_costs,
            resolve_policy_bundle,
            resolve_real_discount_rate,
        )

    def test_stayed_names_still_defined_in_scenarios(self):
        # The extraction moved ONLY the PB-1 resolvers + SweepDefinition;
        # everything else scenarios.py defined stays defined there.
        import market_sim.config.scenarios as scenarios

        self.assertEqual(
            scenarios.ScenarioConfig.__module__, "market_sim.config.scenarios"
        )
        for name in (
            "resolve_real_discount_rate",
            "COAL_SIGMOID_DEFAULTS",
            "TIER_TAGS",
            "_CACHE_KEY_OPTIONAL_FIELDS",
        ):
            self.assertTrue(hasattr(scenarios, name), name)
        self.assertEqual(
            scenarios.resolve_real_discount_rate.__module__,
            "market_sim.config.scenarios",
        )


class TestSweepDefinitionLazyBase(unittest.TestCase):
    """The lazy ScenarioConfig import inside sweeps.py expands correctly."""

    def test_generate_default_base_is_scenarios_config(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.config.sweeps import SweepDefinition

        configs = SweepDefinition(sweep={"carbon_price": [0.0, 50.0]}).generate()
        self.assertEqual(len(configs), 2)
        self.assertIsInstance(configs[0], ScenarioConfig)

    def test_case_configs_default_base_is_scenarios_config(self):
        from market_sim.config.scenarios import ScenarioConfig
        from market_sim.config.sweeps import SweepDefinition

        cases = SweepDefinition(cases={"REF": {}}).case_configs()
        self.assertIsInstance(cases["REF"], ScenarioConfig)


if __name__ == "__main__":
    unittest.main()
