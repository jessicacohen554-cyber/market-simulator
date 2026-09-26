"""Tests for ``ScenarioConfig.coal_committed_nested_on_mustrun`` (NWPP-NEXT-4).

The CAMPD thermal-tranche artifact defines a coal plant's ``committed_pct`` and
``mustrun_pct`` as LEVELS from 0 MW; ``bins_to_fleet`` stacks ``_committed`` on
top of ``_mustrun``. Armed, a coal plant with a measured row sizes its
committed band as the increment above must-run. Off, the bins frame is
byte-identical.
"""

from __future__ import annotations

import unittest

import pandas as pd

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.plant_taxonomy import COAL_CLASSES
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.fleet import fleet_to_bins, load_fleet_from_csv
from market_sim.data.fleet.campd_bins import thermal_tranche_overrides

FIELD = "coal_committed_nested_on_mustrun"


class TestCoalCommittedNested(unittest.TestCase):
    """The nested committed band on NWPP's own fleet and artifact."""

    @classmethod
    def setUpClass(cls):
        ic = get_iso_config("NWPP")
        cls.fleet = load_fleet_from_csv("NWPP", ic)
        base = dict(iso="NWPP", mode="backcast", weather_year=2024)
        cls.off = fleet_to_bins(cls.fleet, "NWPP", ScenarioConfig(**base))
        cls.on = fleet_to_bins(
            cls.fleet, "NWPP", ScenarioConfig(**base, **{FIELD: True})
        )
        cls.ov = thermal_tranche_overrides("NWPP")

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

    def test_measured_coal_rows_nest(self):
        on = self.on.set_index(["Plant_Code", "Plant_Group"])
        off = self.off.set_index(["Plant_Code", "Plant_Group"])
        n = 0
        for (code, group), row in on.iterrows():
            if group not in COAL_CLASSES or (int(code), "COAL") not in self.ov:
                continue
            committed, mustrun = self.ov[(int(code), "COAL")]
            # Both paths keep fleet_to_bins' feasibility clip (committed +
            # peaking <= 100 - must-run), so compare against the clipped value.
            room = 100.0 - row["pct_mr"] - row["pct_peak"]
            self.assertAlmostEqual(
                off.loc[(code, group), "pct_mc"], min(committed, room), 6
            )
            self.assertAlmostEqual(
                row["pct_mc"], min(max(0.0, committed - mustrun), room), 6
            )
            self.assertAlmostEqual(row["pct_mr"], off.loc[(code, group), "pct_mr"], 9)
            # The removed share falls to the econ band; capacity is conserved.
            moved = off.loc[(code, group), "pct_mc"] - row["pct_mc"]
            self.assertAlmostEqual(
                row["pct_econ"] - off.loc[(code, group), "pct_econ"], moved, 6
            )
            n += 1
        self.assertGreaterEqual(n, 10)

    def test_everything_else_byte_identical(self):
        key = ["Plant_Code", "Plant_Group"]
        on = self.on.set_index(key)
        off = self.off.set_index(key)
        measured = [
            (c, g)
            for c, g in on.index
            if g in COAL_CLASSES and (int(c), "COAL") in self.ov
        ]
        pd.testing.assert_frame_equal(on.drop(index=measured), off.drop(index=measured))
        # Jim Bridger (8066) has no measured COAL row: default shares kept.
        bridger = [(c, g) for c, g in on.index if int(c) == 8066 and g in COAL_CLASSES]
        self.assertTrue(bridger)
        pd.testing.assert_frame_equal(on.loc[bridger], off.loc[bridger])


if __name__ == "__main__":
    unittest.main()
