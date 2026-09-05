"""FFR-9C R-b: the ``smr_available_year`` SMR entry availability gate.

``nuclear_smr`` sits in the always-eligible ``_NEW_ENTRY_TECHS`` tuple with no
availability-year gate, while ATB itself costs SMR from 2030 only
(``NEW_ENTRY_COSTS["nuclear_smr"]``) — so an ungated hindcast "builds" a
2022-decided ERCOT SMR (FFR-9B §3: 4.0 GW of phantom SMR crowding wind out of
the shared ISO budget). The gate is GATED default-off (``None`` = the shipped
always-eligible posture, byte-identical) and armed by invocation with the
ATB-cited 2030 in FFR-9C measurement arms; these tests pin both halves plus
the cache-key registration discipline (rule 24 / the nyiso-119 same-commit
rule).
"""

import unittest
from dataclasses import fields

from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.model.capacity_evolution import _new_entry_candidates

# The pinned default-config cache key (the cache-key flip guard's anchor).
_PINNED_DEFAULT_KEY = "e5ecd4105ada3e58"


class TestSmrAvailableYearRegistration(unittest.TestCase):
    """The field is registered, default-off, and cache-key-inert when off."""

    def test_field_is_registered_and_defaults_off(self):
        # Rule 24 [R-REGISTRY]: the gate is a ScenarioConfig field, so it
        # appears in run_config.json rather than being an off-registry knob.
        names = {f.name for f in fields(ScenarioConfig)}
        self.assertIn("smr_available_year", names)
        self.assertIsNone(ScenarioConfig().smr_available_year)

    def test_default_cache_key_is_unmoved(self):
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS in the SAME COMMIT as the
        # field, so it drops out of the hash at its default and every
        # pre-existing cached bundle keeps its key.
        self.assertIn("smr_available_year", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertIn("smr_available_year", _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS)
        self.assertEqual(ScenarioConfig().cache_key(), _PINNED_DEFAULT_KEY)

    def test_armed_run_gets_a_distinct_cache_key(self):
        # An armed run is a different scenario, not a cache collision — which
        # is what keeps the FFR-9C stage-B arm independent on disk.
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(smr_available_year=2030).cache_key(),
        )


class TestSmrAvailableYearGate(unittest.TestCase):
    """The candidate-pool behaviour at both settings."""

    def test_default_none_keeps_smr_always_eligible(self):
        # The shipped posture is byte-identical: nuclear_smr is a candidate
        # in every year, exactly the pre-field _NEW_ENTRY_TECHS behaviour.
        config = ScenarioConfig(iso="ERCOT")
        for year in (2022, 2025, 2029, 2030, 2040):
            self.assertIn("nuclear_smr", _new_entry_candidates(year, config, "ERCOT"))

    def test_armed_gate_excludes_smr_before_the_year(self):
        config = ScenarioConfig(iso="ERCOT", smr_available_year=2030)
        for year in (2022, 2023, 2024, 2025, 2029):
            self.assertNotIn(
                "nuclear_smr", _new_entry_candidates(year, config, "ERCOT")
            )

    def test_armed_gate_admits_smr_at_and_after_the_year(self):
        config = ScenarioConfig(iso="ERCOT", smr_available_year=2030)
        for year in (2030, 2031, 2045):
            self.assertIn("nuclear_smr", _new_entry_candidates(year, config, "ERCOT"))

    def test_gate_touches_only_nuclear_smr(self):
        # The classic four and the emerging-tech gates are untouched at any
        # setting — one mechanism, one tech (rule 19).
        base = ScenarioConfig(iso="ERCOT")
        armed = ScenarioConfig(iso="ERCOT", smr_available_year=2030)
        for year in (2022, 2029, 2030, 2036):
            without_smr = [
                t
                for t in _new_entry_candidates(year, base, "ERCOT")
                if t != "nuclear_smr"
            ]
            armed_without_smr = [
                t
                for t in _new_entry_candidates(year, armed, "ERCOT")
                if t != "nuclear_smr"
            ]
            self.assertEqual(without_smr, armed_without_smr)


if __name__ == "__main__":
    unittest.main()
