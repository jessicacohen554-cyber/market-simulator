"""Parse-validation for the committed base forecast scenario (G-46).

Confirms configs/scenarios/ercot_base.yaml — the example
docs/codebase/07-runner-and-cli.md and README.md point at for
`market-sim run --config` — actually loads into a valid ScenarioConfig.
Does not run the forecast; parse-verification only.
"""

import unittest
from pathlib import Path

from market_sim.config.scenarios import ScenarioConfig

_ERCOT_BASE_YAML = (
    Path(__file__).resolve().parents[1] / "configs" / "scenarios" / "ercot_base.yaml"
)


class TestErcotBaseScenarioYaml(unittest.TestCase):
    """The committed base scenario YAML must parse into a valid ScenarioConfig."""

    def test_file_exists(self):
        self.assertTrue(_ERCOT_BASE_YAML.is_file())

    def test_parses_into_scenario_config(self):
        config = ScenarioConfig.from_yaml(_ERCOT_BASE_YAML)
        self.assertIsInstance(config, ScenarioConfig)

    def test_declares_forecast_mode_and_ercot(self):
        config = ScenarioConfig.from_yaml(_ERCOT_BASE_YAML)
        self.assertEqual(config.mode, "forecast")
        self.assertEqual(config.iso, "ERCOT")

    def test_declares_full_forecast_horizon(self):
        config = ScenarioConfig.from_yaml(_ERCOT_BASE_YAML)
        self.assertEqual(config.start_year, 2026)
        self.assertEqual(config.end_year, 2050)


if __name__ == "__main__":
    unittest.main()
