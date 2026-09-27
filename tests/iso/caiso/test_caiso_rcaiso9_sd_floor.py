"""R-CAISO-9: the SDGE per-year import cap floored at the static 1,436 MW.

``caiso_import_cap_floor_static`` (owner ruling 2026-09-27, "Floor at static
1,436") makes the per-year ``SP15_rest -> SDGE`` cap ``max(LCT cap, static)``;
LA Basin is untouched (owner card). Trivial cases first (mocked LCT rows), then
the landed LCT rows. Record: ``docs/handoffs/r-caiso-9/``.
"""

from __future__ import annotations

import unittest
from dataclasses import replace
from unittest import mock

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import ScenarioConfig
from market_sim.model.transmission import apply_caiso_local_import_limits

SD = ("SP15_rest", "SDGE")
LA = ("SP15_rest", "LA_BASIN")


def _links(ic):
    return {(ln.from_zone, ln.to_zone): ln.ttc_mw for ln in ic.links}


def _lcr(la: float, sd: float):
    return {
        "LA Basin": {"import_cap_mw": la},
        "San Diego/Imperial Valley": {"import_cap_mw": sd},
    }


class TestTrivialFloor(unittest.TestCase):
    """Mocked LCT rows: the floor is max(cap, baked static) on SDGE only."""

    def _apply(self, la, sd, floor):
        ic = get_iso_config("CAISO")
        with mock.patch(
            "market_sim.data.local_capacity.load_lcr_parameters",
            return_value=_lcr(la, sd),
        ):
            return ic, apply_caiso_local_import_limits(
                ic, "CAISO", 2019, sd_floor_static=floor
            )

    def test_baked_static_is_1436(self):
        self.assertEqual(_links(get_iso_config("CAISO"))[SD], 1436.0)

    def test_below_static_is_floored(self):
        _, out = self._apply(100.0, 100.0, True)
        self.assertEqual(_links(out)[SD], 1436.0)
        self.assertEqual(_links(out)[LA], 100.0)  # LA never floored

    def test_below_static_off_keeps_lct(self):
        _, out = self._apply(100.0, 100.0, False)
        self.assertEqual(_links(out)[SD], 100.0)

    def test_above_static_unchanged_by_floor(self):
        _, on = self._apply(15000.0, 2000.0, True)
        _, off = self._apply(15000.0, 2000.0, False)
        self.assertEqual(_links(on), _links(off))
        self.assertEqual(_links(on)[SD], 2000.0)

    def test_equal_static_is_identity_object(self):
        ic, out = self._apply(12008.0, 1.0, True)
        self.assertIs(out, ic)


class TestLandedLCTRows(unittest.TestCase):
    """The committed LCT rows: only 2019-21 move; 2022-25 byte-identical."""

    def test_per_year(self):
        ic = get_iso_config("CAISO")
        expect_sd = {
            2019: 1436.0,
            2020: 1436.0,
            2021: 1436.0,
            2023: 1436.0,
            2024: 2074.0,
            2025: 2071.0,
        }
        expect_la = {2019: 11150.0, 2020: 11897.0, 2021: 12803.0}
        for y, sd in expect_sd.items():
            on = _links(
                apply_caiso_local_import_limits(ic, "CAISO", y, sd_floor_static=True)
            )
            off = _links(apply_caiso_local_import_limits(ic, "CAISO", y))
            self.assertEqual(on[SD], sd, y)
            self.assertEqual(on[LA], off[LA], y)
            if y >= 2023:
                self.assertEqual(on, off, y)
            if y in expect_la:
                self.assertEqual(on[LA], expect_la[y], y)

    def test_2022_no_row_is_identity(self):
        ic = get_iso_config("CAISO")
        self.assertIs(
            apply_caiso_local_import_limits(ic, "CAISO", 2022, sd_floor_static=True), ic
        )


class TestCacheKey(unittest.TestCase):
    def test_default_off_key_unchanged(self):
        base = ScenarioConfig(iso="CAISO", mode="backcast")
        self.assertFalse(base.caiso_import_cap_floor_static)
        on = replace(base, caiso_import_cap_floor_static=True)
        self.assertNotEqual(base.cache_key(), on.cache_key())
        self.assertEqual(
            base.cache_key(),
            replace(base, caiso_import_cap_floor_static=False).cache_key(),
        )


if __name__ == "__main__":
    unittest.main()
