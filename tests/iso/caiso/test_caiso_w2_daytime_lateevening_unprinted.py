"""closeout-CAISO-w2: the daytime / late-evening clean rungs in the unprinted-year hours.

``caiso_dsw_daytime_lateevening_unprinted_arm`` extends the caiso-94 daytime
(hod 6-21) and caiso-269 late-evening (hod 22-23) evidence gates to the hours
the R-CAISO-18 unprinted-year branch prices (all of 2019-2020, the unprinted
Jan-Apr 2021) — an owner-gated transfer of the R-CAISO-20 overnight pattern.
Default off and byte-identical off; inert in 2022-2025 on. Trivial cases
first. Record:
``docs/records/caiso/closeout-caiso-w2/PRECOMMIT-closeout-caiso-w2-unprinted-rungs-2026-10-03.md``.
"""

from __future__ import annotations

import unittest

import numpy as np

import market_sim.data.eia930.envelopes as envelopes
from market_sim.config.interchange_config import (
    CAISO_DAYTIME_CLEAN_HOD_MAX,
    CAISO_DAYTIME_CLEAN_HOD_MIN,
    CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC,
    CAISO_DSW_DAYTIME_CLEAN_NAME,
    CAISO_DSW_DAYTIME_CLEAN_UNPRINTED_DEPTH_BY_YEAR,
    CAISO_DSW_LATEEVENING_CLEAN_DEPTH_STATIC,
    CAISO_DSW_LATEEVENING_CLEAN_NAME,
    CAISO_DSW_LATEEVENING_CLEAN_UNPRINTED_DEPTH_BY_YEAR,
    CAISO_LATEEVENING_CLEAN_HOD_MIN,
    CAISO_PER_HUB_IMPORT_ZONES,
)
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.fleet import generators_to_fleet_arrays
from market_sim.model.transmission import (
    build_caiso_per_hub_intertie,
    inject_caiso_dsw_daytime_clean,
    inject_caiso_dsw_lateevening_clean,
    inject_caiso_firm_import_shape,
)

HOURS = 8760
ZONE = CAISO_PER_HUB_IMPORT_ZONES["PALOVRDE"]
DAY_UID = f"{ZONE}_{CAISO_DSW_DAYTIME_CLEAN_NAME}"
EVE_UID = f"{ZONE}_{CAISO_DSW_LATEEVENING_CLEAN_NAME}"
HOD = np.arange(HOURS) % 24
DAYTIME = (HOD >= CAISO_DAYTIME_CLEAN_HOD_MIN) & (HOD <= CAISO_DAYTIME_CLEAN_HOD_MAX)
LATE = HOD >= CAISO_LATEEVENING_CLEAN_HOD_MIN


def _fleet():
    gens = build_caiso_per_hub_intertie(
        overnight_clean=True, daytime_clean=True, lateevening_clean=True
    )
    zones = sorted({g.zone for g in gens})
    fleet = generators_to_fleet_arrays(gens, zones, hours=HOURS)
    inject_caiso_firm_import_shape(fleet, "CAISO", 2024)
    return fleet


def _cap(fleet, uid):
    row = list(fleet.unit_ids).index(uid)
    return fleet.pmax[row] * fleet.availability[row, :]


def _both(fleet, year, arm):
    day = inject_caiso_dsw_daytime_clean(
        fleet, "CAISO", year, gap_fill_measured_dam=True, unprinted_year_arm=arm
    )
    eve = inject_caiso_dsw_lateevening_clean(
        fleet, "CAISO", year, gap_fill_measured_dam=True, unprinted_year_arm=arm
    )
    return day, eve


class TestDepthTables(unittest.TestCase):
    def test_preregistered_p95_and_no_2021_entry(self):
        self.assertEqual(
            CAISO_DSW_DAYTIME_CLEAN_UNPRINTED_DEPTH_BY_YEAR,
            {2019: 7348.0, 2020: 7122.0},
        )
        self.assertEqual(
            CAISO_DSW_LATEEVENING_CLEAN_UNPRINTED_DEPTH_BY_YEAR,
            {2019: 6922.0, 2020: 7281.0},
        )


class TestInjectors(unittest.TestCase):
    def test_off_2019_is_inert(self):
        fleet = _fleet()
        before = fleet.availability.copy()
        self.assertEqual(_both(fleet, 2019, False), (False, False))
        np.testing.assert_array_equal(fleet.availability, before)

    def test_on_2019_arms_window_hours_only_at_unprinted_depth(self):
        fleet = _fleet()
        self.assertEqual(_both(fleet, 2019, True), (True, True))
        day, eve = _cap(fleet, DAY_UID), _cap(fleet, EVE_UID)
        rows = list(fleet.unit_ids)
        self.assertEqual(float(fleet.pmax[rows.index(DAY_UID)]), 7348.0)
        self.assertEqual(float(fleet.pmax[rows.index(EVE_UID)]), 6922.0)
        self.assertTrue(np.all(day[~DAYTIME] == 0.0))
        self.assertTrue(np.all(eve[~LATE] == 0.0))
        self.assertGreater(float(day[DAYTIME].max()), 0.0)
        self.assertGreater(float(eve[LATE].min()), 0.0)

    def test_2021_on_moves_only_unprinted_window_hours(self):
        off, on = _fleet(), _fleet()
        _both(off, 2021, False)
        _both(on, 2021, True)
        unprinted = envelopes.measured_intertie_hub_unprinted_year_mask(
            "CAISO", 2021, HOURS, "PALOVRDE", gap_fill_measured_dam=True
        )
        for uid, win in ((DAY_UID, DAYTIME), (EVE_UID, LATE)):
            moved = ~np.isclose(_cap(off, uid), _cap(on, uid))
            self.assertTrue(moved.any(), uid)
            self.assertFalse((moved & ~(unprinted & win)).any(), uid)
        rows = list(on.unit_ids)
        self.assertEqual(
            float(on.pmax[rows.index(DAY_UID)]), CAISO_DSW_DAYTIME_CLEAN_DEPTH_STATIC
        )
        self.assertEqual(
            float(on.pmax[rows.index(EVE_UID)]),
            CAISO_DSW_LATEEVENING_CLEAN_DEPTH_STATIC,
        )

    def test_2022_to_2025_byte_identical_on(self):
        for year in (2022, 2023, 2024, 2025):
            off, on = _fleet(), _fleet()
            _both(off, year, False)
            _both(on, year, True)
            np.testing.assert_array_equal(off.availability, on.availability)
            np.testing.assert_array_equal(off.pmax, on.pmax)


class TestConfigSeam(unittest.TestCase):
    def test_default_off_and_cache_registered(self):
        self.assertFalse(
            ScenarioConfig(iso="CAISO").caiso_dsw_daytime_lateevening_unprinted_arm
        )
        self.assertIn(
            "caiso_dsw_daytime_lateevening_unprinted_arm", _CACHE_KEY_OPTIONAL_FIELDS
        )
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[
                "caiso_dsw_daytime_lateevening_unprinted_arm"
            ],
            "False",
        )


if __name__ == "__main__":
    unittest.main()
