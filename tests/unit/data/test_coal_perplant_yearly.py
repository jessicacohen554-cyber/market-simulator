"""Tests for the per-year windowed per-plant coal offer curves (ercot-168).

``ScenarioConfig.coal_perplant_offer_yearly`` — matrix §5.1 item 12's rule-23
re-derivation of the armed ERCOT-144 identification from the delivery-2023
corpus. What must hold (the precommit's construction contract,
``docs/PRECOMMIT-ercot168-coal-perplant-year-curves-2026-08-05.md``):

- a solve year PRESENT in the year table prices committed/econ tranches per
  (months × hours) window on the window's own curve, on the model's fixed-CST
  non-leap calendar;
- a solve year ABSENT from the table is BYTE-IDENTICAL to the static ERCOT-144
  path (the G-BIT kill's unit-level face);
- a one-window year table whose curve equals the static registry reproduces
  the static path's mc exactly (the "SAME window mapping" claim, executable);
- `_mustrun`/`_peak` rows are untouched; arming without the ERCOT-144 gate,
  or without a solve year, is a hard error (rule 24/25).

Trivial fixtures per the repo testing pattern: one plant, three tranches
(mustrun/committed/econhi), 8760 hours where the calendar matters and 24
where it does not.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.data.fleet.legacy_bins import (
    _hour_month_hod,
    apply_coal_tranches,
    assemble_mc,
)

COAL_HR = 10.0
COAL_VOM = 4.5
COAL_FUEL = 1.45
PLANT = 6180

#: Static (ERCOT-144-style) plant curve: 300 MW @ $9, 300 @ $12 (top 600).
STATIC_CURVE = ((300.0, 9.0), (600.0, 12.0))
ALL_MONTHS = tuple(range(1, 13))
ALL_HOURS = tuple(range(24))
#: Overnight window (CST h23–h8) at a $60.26 top — the measured Aug shape.
NIGHT_HOURS = (23, 0, 1, 2, 3, 4, 5, 6, 7, 8)
DAY_HOURS = tuple(h for h in range(24) if h not in NIGHT_HOURS)
HI_CURVE = ((600.0, 60.26),)


def _gen(unit_id: str, pmax: float) -> Generator:
    """One trivial CAMPD coal tranche generator."""
    return Generator(
        unit_id=unit_id,
        name="t",
        zone="N",
        fuel_type="coal",
        efficiency_bin="subcritical",
        pmax_mw=pmax,
        pmin_mw=0.0,
        heat_rate=COAL_HR,
        vom=COAL_VOM,
        emission_rate_co2=0.0,
        nox_rate=0.0,
        eford=0.05,
        online_year=1980,
        is_campd_bin=True,
        plant_group="COAL_BIT",
        bin_label="X",
        plant_code=PLANT,
    )


def _fleet():
    """Three tranches in rank order: mustrun 300 MW, committed 150, econhi 150."""
    gens = [
        _gen(f"COAL_N_{PLANT}_mustrun", 300.0),
        _gen(f"COAL_N_{PLANT}_committed", 150.0),
        _gen(f"COAL_N_{PLANT}_econhi", 150.0),
    ]
    return gens


def _mc(config: ScenarioConfig, hours: int, year: int | None):
    gens = _fleet()
    fa = generators_to_fleet_arrays(gens, ["N"], config=config, hours=hours)
    fuel = np.full((len(gens), hours), COAL_FUEL)
    mc = assemble_mc(fa, fuel, 0.0, 0.0)
    apply_coal_tranches(mc, gens, fa, [1.0, 1.0, 1.0], fuel, config, year=year)
    return mc


def _static_cfg(hours: int) -> ScenarioConfig:
    return ScenarioConfig(
        hours=hours,
        coal_perplant_offer_level=True,
        coal_perplant_offer_curves={PLANT: STATIC_CURVE},
    )


def _yearly_cfg(hours: int, table) -> ScenarioConfig:
    return ScenarioConfig(
        hours=hours,
        coal_perplant_offer_level=True,
        coal_perplant_offer_curves={PLANT: STATIC_CURVE},
        coal_perplant_offer_yearly=True,
        coal_perplant_offer_curves_yearly=table,
    )


class HourMonthCalendar(unittest.TestCase):
    def test_nonleap_calendar_boundaries(self) -> None:
        month, hod = _hour_month_hod(8760)
        self.assertEqual(month[0], 1)
        self.assertEqual(month[31 * 24 - 1], 1)
        self.assertEqual(month[31 * 24], 2)
        self.assertEqual(month[8759], 12)
        self.assertEqual(hod[0], 0)
        self.assertEqual(hod[8759], 23)
        # August spans doy 212..242 (0-indexed 212*24 .. 243*24-1)
        aug0 = (31 + 28 + 31 + 30 + 31 + 30 + 31) * 24
        self.assertEqual(month[aug0], 8)
        self.assertEqual(month[aug0 - 1], 7)


class YearlyWindowPricing(unittest.TestCase):
    def test_window_levels_land_on_window_hours(self) -> None:
        """Aug nights price at the HI curve; Aug days and Jan at the static."""
        table = {
            2023: {
                PLANT: (
                    (ALL_MONTHS[:7] + (11, 12), ALL_HOURS, (STATIC_CURVE)),
                    ((8, 9, 10), NIGHT_HOURS, HI_CURVE),
                    ((8, 9, 10), DAY_HOURS, STATIC_CURVE),
                )
            }
        }
        mc = _mc(_yearly_cfg(8760, table), 8760, 2023)
        month, hod = _hour_month_hod(8760)
        aug_night = (month == 8) & np.isin(hod, NIGHT_HOURS)
        aug_day = (month == 8) & np.isin(hod, DAY_HOURS)
        jan = month == 1
        # committed tranche (row 1) covers 300–450 MW of the 600 MW curve:
        # static window mean = $12 (the 300–600 block); HI curve = $60.26.
        self.assertTrue(np.allclose(mc[1, aug_night], 60.26))
        self.assertTrue(np.allclose(mc[1, aug_day], 12.0))
        self.assertTrue(np.allclose(mc[1, jan], 12.0))
        # econhi tranche (row 2) covers 450–600 MW: same windows apply.
        self.assertTrue(np.allclose(mc[2, aug_night], 60.26))
        self.assertTrue(np.allclose(mc[2, aug_day], 12.0))
        # mustrun row keeps the assembled cost (no perplant repricing).
        base = COAL_HR * COAL_FUEL + COAL_VOM
        self.assertTrue(np.allclose(mc[0, :], base))

    def test_single_window_table_equals_static_path(self) -> None:
        """One all-months/all-hours window at the static curve == static mc."""
        table = {2023: {PLANT: ((ALL_MONTHS, ALL_HOURS, STATIC_CURVE),)}}
        mc_static = _mc(_static_cfg(8760), 8760, 2023)
        mc_yearly = _mc(_yearly_cfg(8760, table), 8760, 2023)
        np.testing.assert_array_equal(mc_static, mc_yearly)

    def test_absent_year_falls_through_bit_identical(self) -> None:
        """Solve year not in the table -> byte-identical to the static path."""
        table = {2023: {PLANT: ((ALL_MONTHS, ALL_HOURS, HI_CURVE),)}}
        mc_static = _mc(_static_cfg(8760), 8760, 2024)
        mc_yearly = _mc(_yearly_cfg(8760, table), 8760, 2024)
        np.testing.assert_array_equal(mc_static, mc_yearly)

    def test_string_keys_normalize(self) -> None:
        """A JSON-round-tripped table (string year/plant keys) still resolves."""
        table = {"2023": {str(PLANT): ((ALL_MONTHS, ALL_HOURS, HI_CURVE),)}}
        mc = _mc(_yearly_cfg(8760, table), 8760, 2023)
        self.assertTrue(np.allclose(mc[1, :], 60.26))


class YearlyValidation(unittest.TestCase):
    def test_yearly_without_level_gate_raises(self) -> None:
        cfg = ScenarioConfig(
            hours=24,
            coal_perplant_offer_yearly=True,
            coal_perplant_offer_curves_yearly={
                2023: {PLANT: ((ALL_MONTHS, ALL_HOURS, HI_CURVE),)}
            },
        )
        with self.assertRaisesRegex(ValueError, "coal_perplant_offer_level"):
            _mc(cfg, 24, 2023)

    def test_yearly_without_table_raises(self) -> None:
        cfg = ScenarioConfig(
            hours=24,
            coal_perplant_offer_level=True,
            coal_perplant_offer_curves={PLANT: STATIC_CURVE},
            coal_perplant_offer_yearly=True,
        )
        with self.assertRaisesRegex(ValueError, "coal_perplant_offer_curves_yearly"):
            _mc(cfg, 24, 2023)

    def test_yearly_without_solve_year_raises(self) -> None:
        table = {2023: {PLANT: ((ALL_MONTHS, ALL_HOURS, HI_CURVE),)}}
        with self.assertRaisesRegex(ValueError, "solve year"):
            _mc(_yearly_cfg(24, table), 24, None)

    def test_uncovered_hours_raise(self) -> None:
        """A gap in the (month x hour) coverage is a hard error, not a NaN."""
        table = {2023: {PLANT: (((1,), (0, 1), STATIC_CURVE),)}}
        with self.assertRaisesRegex(ValueError, "uncovered"):
            _mc(_yearly_cfg(8760, table), 8760, 2023)


if __name__ == "__main__":
    unittest.main()
