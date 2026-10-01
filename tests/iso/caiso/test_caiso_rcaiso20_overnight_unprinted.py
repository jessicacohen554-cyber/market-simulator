"""R-CAISO-20: the overnight clean rung armed in the unprinted-year hours (owner ruling).

``caiso_dsw_overnight_clean_unprinted_arm`` extends the caiso-93 overnight
evidence gate to the hod 0-5 hours the R-CAISO-18 unprinted-year branch prices
(all of 2019-2020, the unprinted Jan-Apr 2021). Default off and byte-identical
off; inert in 2022-2025 on (the 2023 Jan-Feb gap is a <=25 % gap and never
arms). Trivial cases first. Record:
``docs/records/caiso/r-caiso-20/PRECOMMIT-r-caiso-20-2026-09-30.md``.
"""

from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

import market_sim.data.eia930.envelopes as envelopes
from market_sim.config.interchange_config import (
    CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR,
    CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC,
    CAISO_DSW_OVERNIGHT_CLEAN_NAME,
    CAISO_OVERNIGHT_CLEAN_HOD_MAX,
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
    inject_caiso_dsw_overnight_clean,
    inject_caiso_firm_import_shape,
)

HOURS = 8760
ZONE = CAISO_PER_HUB_IMPORT_ZONES["PALOVRDE"]
UID = f"{ZONE}_{CAISO_DSW_OVERNIGHT_CLEAN_NAME}"
OVERNIGHT = np.arange(HOURS) % 24 <= CAISO_OVERNIGHT_CLEAN_HOD_MAX


def _fleet():
    gens = build_caiso_per_hub_intertie(overnight_clean=True)
    zones = sorted({g.zone for g in gens})
    fleet = generators_to_fleet_arrays(gens, zones, hours=HOURS)
    inject_caiso_firm_import_shape(fleet, "CAISO", 2024)
    return fleet


def _cap(fleet):
    row = list(fleet.unit_ids).index(UID)
    return fleet.pmax[row] * fleet.availability[row, :]


class TestMaskTrivial(unittest.TestCase):
    """The mask is the unprinted-year branch's hours, never the <=25 % gap."""

    def _run(self, raw_prices, formula):
        import pandas as pd

        frame = pd.DataFrame(
            {
                "year": 2019,
                "hour": np.arange(len(raw_prices)),
                "hub": "PALOVRDE",
                "price": raw_prices,
            }
        )
        with (
            mock.patch.object(pd, "read_parquet", return_value=frame),
            mock.patch.object(envelopes.Path, "exists", return_value=True),
            mock.patch.object(
                envelopes,
                "_fill_unprinted_measured_gas",
                side_effect=lambda p, g, *a: np.where(g, formula, p),
            ),
        ):
            return envelopes.measured_intertie_hub_unprinted_year_mask(
                "CAISO", 2019, len(raw_prices), "PALOVRDE"
            )

    def test_small_gap_never_masks(self):
        # 24 h, a 5-hour gap (21 %) -> the <=25 % path owns it: no arm.
        raw = np.full(24, 30.0)
        raw[3:8] = np.nan
        self.assertFalse(self._run(raw, np.full(24, 28.0)).any())

    def test_large_gap_masks_only_formula_priced_hours(self):
        raw = np.full(24, 30.0)
        raw[:12] = np.nan  # 50 % gap
        formula = np.full(24, 28.0)
        formula[0] = np.nan  # the formula cannot price hour 0
        mask = self._run(raw, formula)
        expected = np.zeros(24, bool)
        expected[1:12] = True
        np.testing.assert_array_equal(mask, expected)

    def test_other_iso_is_none(self):
        self.assertIsNone(
            envelopes.measured_intertie_hub_unprinted_year_mask(
                "ERCOT", 2019, 24, "PALOVRDE"
            )
        )


class TestCommittedMask(unittest.TestCase):
    """On the committed extract: 2019/20 whole year, 2021 Jan-Apr, 2023 gap never."""

    def test_per_year_counts(self):
        expected = {2019: 8760, 2020: 8760, 2021: 2784, 2022: 0, 2023: 0, 2024: 0}
        for year, n in expected.items():
            m = envelopes.measured_intertie_hub_unprinted_year_mask(
                "CAISO", year, HOURS, "PALOVRDE", gap_fill_measured_dam=True
            )
            self.assertEqual(int(m.sum()), n, year)

    def test_2023_gap_hours_exist_but_never_mask(self):
        raw = envelopes.measured_intertie_hub_price_raw(
            "CAISO", 2023, HOURS, "PALOVRDE", gap_fill_measured_dam=True
        )
        self.assertGreater(int((~np.isfinite(raw)).sum()), 0)
        m = envelopes.measured_intertie_hub_unprinted_year_mask(
            "CAISO", 2023, HOURS, "PALOVRDE", gap_fill_measured_dam=True
        )
        self.assertFalse(m.any())


class TestInjector(unittest.TestCase):
    def test_off_2019_is_inert(self):
        fleet = _fleet()
        before = fleet.availability.copy()
        self.assertFalse(inject_caiso_dsw_overnight_clean(fleet, "CAISO", 2019))
        np.testing.assert_array_equal(fleet.availability, before)

    def test_on_2019_arms_every_overnight_hour_at_measured_depth(self):
        fleet = _fleet()
        self.assertTrue(
            inject_caiso_dsw_overnight_clean(
                fleet,
                "CAISO",
                2019,
                gap_fill_measured_dam=True,
                unprinted_year_arm=True,
            )
        )
        row = list(fleet.unit_ids).index(UID)
        self.assertEqual(float(fleet.pmax[row]), 6566.0)
        cap = _cap(fleet)
        self.assertTrue(np.all(cap[~OVERNIGHT] == 0.0))
        self.assertGreater(float(cap[OVERNIGHT].min()), 0.0)

    def test_depths_are_the_preregistered_p95(self):
        self.assertEqual(CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR[2019], 6566.0)
        self.assertEqual(CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR[2020], 7166.0)
        self.assertNotIn(2021, CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_BY_YEAR)
        self.assertEqual(CAISO_DSW_OVERNIGHT_CLEAN_DEPTH_STATIC, 6187.0)

    def test_2021_on_adds_only_janapr_overnight(self):
        off, on = _fleet(), _fleet()
        inject_caiso_dsw_overnight_clean(off, "CAISO", 2021, gap_fill_measured_dam=True)
        inject_caiso_dsw_overnight_clean(
            on, "CAISO", 2021, gap_fill_measured_dam=True, unprinted_year_arm=True
        )
        c_off, c_on = _cap(off), _cap(on)
        moved = ~np.isclose(c_off, c_on)
        unprinted = envelopes.measured_intertie_hub_unprinted_year_mask(
            "CAISO", 2021, HOURS, "PALOVRDE", gap_fill_measured_dam=True
        )
        self.assertTrue(moved.any())
        self.assertFalse((moved & ~(unprinted & OVERNIGHT)).any())

    def test_2022_to_2025_byte_identical_on(self):
        for year in (2022, 2023, 2024, 2025):
            off, on = _fleet(), _fleet()
            inject_caiso_dsw_overnight_clean(
                off, "CAISO", year, gap_fill_measured_dam=True
            )
            inject_caiso_dsw_overnight_clean(
                on, "CAISO", year, gap_fill_measured_dam=True, unprinted_year_arm=True
            )
            np.testing.assert_array_equal(off.availability, on.availability)
            np.testing.assert_array_equal(off.pmax, on.pmax)


class TestConfigSeam(unittest.TestCase):
    def test_default_off_and_cache_registered(self):
        self.assertFalse(
            ScenarioConfig(iso="CAISO").caiso_dsw_overnight_clean_unprinted_arm
        )
        self.assertIn(
            "caiso_dsw_overnight_clean_unprinted_arm", _CACHE_KEY_OPTIONAL_FIELDS
        )
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS[
                "caiso_dsw_overnight_clean_unprinted_arm"
            ],
            "False",
        )


if __name__ == "__main__":
    unittest.main()
