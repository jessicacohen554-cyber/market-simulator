"""Tests for ``ScenarioConfig.admit_standby_units`` (NWPP-NEXT-5).

EIA-860 ``SB`` ("Standby/Backup — available for service but not normally
used") generators are dropped by the fleet's ``Status == "OP"`` filter. Armed,
the admitted status set widens to ``{"OP", "SB"}`` at the single fleet status
seam; off, the fleet, the outage-cache keys and the re-carry scope are
byte-identical.
"""

from __future__ import annotations

import unittest

import pytest

from market_sim.config import paths
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data import outages
from market_sim.data.fleet import load_fleet_from_csv

FIELD = "admit_standby_units"


class TestAdmitStandbyConfig(unittest.TestCase):
    """Field, cache-key registration and the process-global setter."""

    def tearDown(self):
        paths.set_eia860_standby_admission(False)

    def test_default_off(self):
        self.assertFalse(getattr(ScenarioConfig(), FIELD))

    def test_cache_key_registered_at_default(self):
        self.assertIn(FIELD, _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[FIELD], "False")
        self.assertEqual(
            ScenarioConfig(iso="NWPP").cache_key(),
            ScenarioConfig(iso="NWPP", **{FIELD: False}).cache_key(),
        )
        self.assertNotEqual(
            ScenarioConfig(iso="NWPP").cache_key(),
            ScenarioConfig(iso="NWPP", **{FIELD: True}).cache_key(),
        )

    def test_setter_round_trip(self):
        self.assertEqual(paths.eia860_operable_statuses(), frozenset({"OP"}))
        self.assertFalse(paths.eia860_standby_admitted())
        paths.set_eia860_standby_admission(True)
        self.assertEqual(paths.eia860_operable_statuses(), frozenset({"OP", "SB"}))
        self.assertTrue(paths.eia860_standby_admitted())
        paths.set_eia860_standby_admission(False)
        self.assertEqual(paths.eia860_operable_statuses(), frozenset({"OP"}))

    def test_outage_cache_key_unchanged_off_suffixed_on(self):
        off = outages._fleet_cache_dir_key()
        self.assertEqual(off, str(paths.active_eia860_dir()))
        paths.set_eia860_standby_admission(True)
        self.assertEqual(outages._fleet_cache_dir_key(), f"{off}|SB")


@pytest.mark.fulldata
class TestAdmitStandbyNwppFleet(unittest.TestCase):
    """On NWPP's own 2023 vintage: exactly the SB generators enter."""

    @classmethod
    def setUpClass(cls):
        ic = get_iso_config("NWPP")
        paths.set_eia860_vintage(2023)
        try:
            paths.set_eia860_standby_admission(False)
            cls.off = load_fleet_from_csv("NWPP", ic)
            paths.set_eia860_standby_admission(True)
            cls.on = load_fleet_from_csv("NWPP", ic)
        finally:
            paths.set_eia860_standby_admission(False)
            paths.set_eia860_vintage(None)

    @staticmethod
    def _key(g):
        return (int(g.plant_code), g.unit_id)

    def test_off_is_subset_of_on(self):
        off = {self._key(g) for g in self.off}
        on = {self._key(g) for g in self.on}
        self.assertTrue(off <= on)

    def test_fredonia_and_sun_peak_admitted(self):
        off_plants = {int(g.plant_code) for g in self.off}
        added = [
            g for g in self.on if self._key(g) not in {self._key(h) for h in self.off}
        ]
        added_plants = {int(g.plant_code) for g in added}
        for code in (607, 54854):
            self.assertNotIn(code, off_plants)
            self.assertIn(code, added_plants)
        sun_peak = [g for g in added if int(g.plant_code) == 54854]
        self.assertEqual({g.zone for g in sun_peak}, {"NWPP-SNV"})
        fredonia = [g for g in added if int(g.plant_code) == 607]
        self.assertEqual({g.zone for g in fredonia}, {"NWPP-NW"})


if __name__ == "__main__":
    unittest.main()
