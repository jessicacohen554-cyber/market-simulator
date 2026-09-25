"""Tests for the coal MINIMUM ONLINE CONFIGURATION floor (ercot128-unit-grain).

``ScenarioConfig.ercot_coal_min_config_floor`` bounds a coal plant below by the
registered minimum load of its SMALLEST online configuration — ``min over units
u of MinLoad_u`` from EIA-860, derived by
``scripts/data/derive_eia860_coal_min_config.py`` into
``data/raw/_processed-legacy/coal_min_config_ERCOT.csv``.

The pins here are the ones the arm's own pre-registration promises:

* **byte-identical off** — the default-off fleet carries no floor at all, and
  the default ``ScenarioConfig`` cache key is unmoved (so no existing cached run
  is orphaned) while an armed run gets its own key;
* **ERCOT-scoped** (rule 25 ``[R-ISO-SCOPE]``) and coal-only, so a mixed plant's
  gas-steam rows never pick the floor up;
* **spread across tranches in fill order**, because ``min_gen`` is clipped to
  each TRANCHE's ``pmax x availability`` — pinning a plant-level MW on one slice
  would silently collapse it;
* **its own mechanism id** (``MECH_COAL_MIN_CONFIG``), so D-2/D-4 attribution
  stays per-mechanism and it cannot be confused with the step-3a synchronization
  floor ``MECH_COAL_MUSTRUN`` (rule 19 ``[R-ONE-MECH]``);
* **zero free parameters** (rule 21 ``[R-DOF]``) — every level in the artifact
  is an EIA-860 registration value, never a fitted one.

See ``docs/DIAGNOSIS-ercot128-coal-unit-grain-2026-07-28.md`` and the
``ScenarioConfig`` field docstring.
"""

import unittest

import numpy as np
import pandas as pd

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    bins_to_fleet,
    coal_min_config,
)
from market_sim.data.floor_mechanisms import MECH_COAL_MIN_CONFIG

ZONES = ["North"]

# Limestone: 2 units, min-config 300 MW (EIA-860 Minimum Load), gap-free.
_LIMESTONE = 298
# W A Parish: 4 coal units at 175 MW min-load each, plus gas steamers the
# ``fuel == "coal"`` gate must exclude.
_PARISH = 3470


def _bin_row(code: int, name: str, group: str = "COAL_PRB") -> dict:
    """One synthetic per-plant bin row in the schema ``bins_to_fleet`` consumes."""
    return {
        "Plant_Group": group,
        "ERCOT_Zone": "North",
        "Bin_Number": 1,
        "Bin_Label": name,
        "Plant_Code": code,
        "Plant_Name": name,
        "Turbine_Class": "",
        "capacity_mw": 1500.0,
        "hr_weighted": 10.0,
        "pct_mr": 0.0,
        "pct_mc": 20.0,
        "pct_econ": 75.0,
        "pct_peak": 5.0,
        "min_run": 0,
        "min_down": 0,
        "hr_mr": 10.0,
        "hr_mc": 9.5,
        "hr_econ": 10.0,
        "hr_peak": 12.0,
        "plant_count": 1,
        "plant_codes": [code],
        "fuel": "coal" if group.startswith("COAL") else "gas_st",
    }


def _build(flag_on: bool, rows=None, iso: str = "ERCOT"):
    bins = pd.DataFrame(rows or [_bin_row(_LIMESTONE, "Limestone")])
    cfg = ScenarioConfig(
        iso=iso,
        weather_year=2024,
        mode="backcast",
        hours=8760,
        ercot_coal_min_config_floor=flag_on,
    )
    return bins_to_fleet(bins, ZONES, cfg)


def _plant_floor(fleet: list[Generator], code: int) -> float:
    return sum(g.coal_min_config_pmin_mw for g in fleet if g.plant_code == code)


class TestArtifactAccessor(unittest.TestCase):
    """The derived artifact is present, well-formed and registration-valued."""

    def test_ercot_coal_rows_present(self):
        mc = coal_min_config("ERCOT")
        self.assertIn(_LIMESTONE, mc)
        self.assertIn(_PARISH, mc)
        # EIA-860 registered Minimum Load, not a fitted value (rule 21).
        self.assertAlmostEqual(mc[_LIMESTONE], 300.0, places=1)
        self.assertAlmostEqual(mc[_PARISH], 175.0, places=1)

    def test_every_level_is_positive_and_sub_capacity(self):
        for code, mw in coal_min_config("ERCOT").items():
            self.assertGreater(mw, 0.0, code)
            # A minimum online configuration is one unit's worth, so it must be
            # far below the plant's capacity; the loosest real value is San
            # Miguel's single-unit 0.639.
            self.assertLess(mw, 1000.0, code)

    def test_missing_iso_is_empty(self):
        self.assertEqual(coal_min_config("NOSUCHISO"), {})


class TestByteIdenticalOff(unittest.TestCase):
    """Default-off must change nothing at all."""

    def test_flag_defaults_off(self):
        self.assertFalse(ScenarioConfig().ercot_coal_min_config_floor)

    def test_off_fleet_carries_no_floor(self):
        fleet, fa = _build(flag_on=False)
        for g in fleet:
            self.assertEqual(g.coal_min_config_pmin_mw, 0.0)
        self.assertIsNone(fa.min_gen)

    def test_default_cache_key_unmoved_and_armed_key_distinct(self):
        base = ScenarioConfig()
        armed = ScenarioConfig(ercot_coal_min_config_floor=True)
        # Registered in _CACHE_KEY_OPTIONAL_FIELDS: the DEFAULT key must be
        # untouched by the field's existence, or every cached run is orphaned.
        self.assertEqual(base.cache_key(), ScenarioConfig().cache_key())
        self.assertNotEqual(base.cache_key(), armed.cache_key())


class TestArmedTagging(unittest.TestCase):
    """Armed, the plant-level MW lands on the plant's tranches in fill order."""

    def test_plant_total_equals_registered_min_config(self):
        fleet, _ = _build(flag_on=True)
        self.assertAlmostEqual(
            _plant_floor(fleet, _LIMESTONE),
            coal_min_config("ERCOT")[_LIMESTONE],
            places=1,
        )

    def test_floor_is_spread_in_fill_order_not_pinned_on_one_slice(self):
        """Each floored tranche's share never exceeds that tranche's capacity."""
        fleet, _ = _build(flag_on=True)
        floored = [
            g
            for g in fleet
            if g.plant_code == _LIMESTONE and g.coal_min_config_pmin_mw > 0.0
        ]
        self.assertTrue(floored)
        for g in floored:
            self.assertLessEqual(g.coal_min_config_pmin_mw, g.pmax_mw + 1e-6)
        # Fill order: everything but the last floored tranche is filled whole.
        for g in floored[:-1]:
            self.assertAlmostEqual(g.coal_min_config_pmin_mw, g.pmax_mw, places=3)

    def test_uncovered_plant_gets_no_floor(self):
        """Rule 18 self-targeting: no artifact row, no floor."""
        fleet, _ = _build(flag_on=True, rows=[_bin_row(999999, "Phantom")])
        self.assertEqual(_plant_floor(fleet, 999999), 0.0)

    def test_non_coal_fuel_excluded(self):
        """W A Parish's gas-steam rows must not pick up the coal plant's floor."""
        fleet, _ = _build(
            flag_on=True, rows=[_bin_row(_PARISH, "W A Parish gas", group="ST_GAS")]
        )
        self.assertEqual(_plant_floor(fleet, _PARISH), 0.0)

    def test_iso_scoped_to_ercot(self):
        """Rule 25: another ISO derives its own artifact in its own lane."""
        fleet, _ = _build(flag_on=True, iso="MISO")
        self.assertEqual(_plant_floor(fleet, _LIMESTONE), 0.0)


class TestMinGenAndAttribution(unittest.TestCase):
    """The floor reaches ``min_gen`` under its own mechanism id."""

    def test_min_gen_carries_the_floor_under_its_own_id(self):
        fleet, fa = _build(flag_on=True)
        self.assertIsNotNone(fa.min_gen)
        self.assertIsNotNone(fa.min_gen_mechanism)
        tagged = fa.min_gen_mechanism == MECH_COAL_MIN_CONFIG
        self.assertTrue(tagged.any(), "no unit-hour attributed to the mechanism")
        # Every tagged unit-hour carries a strictly positive floor.
        self.assertTrue((fa.min_gen[tagged] > 0.0).all())

    def test_floor_never_exceeds_available_capacity(self):
        """min_gen is clipped to pmax x availability, so an outage relaxes it."""
        _, fa = _build(flag_on=True)
        cap = fa.pmax[:, None] * fa.availability
        self.assertTrue(np.all(fa.min_gen <= cap + 1e-6))

    def test_hourly_floor_sums_to_the_registered_level_when_fully_available(self):
        fleet, fa = _build(flag_on=True)
        idx = [
            i
            for i, g in enumerate(fleet)
            if g.plant_code == _LIMESTONE and g.coal_min_config_pmin_mw > 0.0
        ]
        # Pick the most-available hour so the clip is not what is being measured.
        h = int(np.argmax(fa.availability[idx, :].min(axis=0)))
        self.assertAlmostEqual(
            float(fa.min_gen[idx, h].sum()),
            coal_min_config("ERCOT")[_LIMESTONE] * float(fa.availability[idx, h].min()),
            delta=1.0,
        )


class TestAvailabilityConditional(unittest.TestCase):
    """The ercot129 contract: CONDITIONAL on availability, never scaled by it.

    ERCOT-128 applied a per-tranche constant and let the generic clip to
    ``pmax x availability`` scale it, which under ERCOT's DAM availability
    water-fill put the applied floor BELOW the physical minimum in most hours
    and removed none of the impossible loadings. The corrected form asks whether
    the PLANT can reach its minimum configuration at all, and then delivers the
    WHOLE level or nothing.
    """

    def _plant_floor_hourly(self):
        fleet, fa = _build(flag_on=True)
        idx = [
            i
            for i, g in enumerate(fleet)
            if g.plant_code == _LIMESTONE and g.fuel_type == "coal"
        ]
        level = sum(fleet[i].coal_min_config_pmin_mw for i in idx)
        tagged = fa.min_gen_mechanism[idx, :] == MECH_COAL_MIN_CONFIG
        applied = np.where(tagged, fa.min_gen[idx, :], 0.0).sum(axis=0)
        avail_cap = (fa.availability[idx, :] * fa.pmax[idx, None]).sum(axis=0)
        return level, applied, avail_cap

    def test_full_level_delivered_whenever_the_plant_can_reach_it(self):
        """Feasible hours carry the WHOLE min-config, not a scaled fraction."""
        level, applied, avail_cap = self._plant_floor_hourly()
        feasible = avail_cap >= level
        self.assertTrue(feasible.any(), "no feasible hour in the fixture")
        np.testing.assert_allclose(applied[feasible], level, rtol=1e-6, atol=1e-3)

    def test_zero_where_the_plant_cannot_reach_min_config(self):
        """Infeasible hours carry NO floor — the plant is off, not part-loaded."""
        level, applied, avail_cap = self._plant_floor_hourly()
        infeasible = avail_cap < level
        if infeasible.any():
            np.testing.assert_allclose(applied[infeasible], 0.0, atol=1e-6)

    def test_floor_is_never_the_availability_scaled_value(self):
        """The ERCOT-128 regression guard: applied != level x availability.

        Where the plant is derated but still able to reach its minimum
        configuration, the scaled form would deliver ``level x avail`` and the
        conditional form delivers ``level``. Those differ, and this pins which
        one is live.
        """
        level, applied, avail_cap = self._plant_floor_hourly()
        plant_avail = avail_cap / max(float(avail_cap.max()), 1e-9)
        derated = (plant_avail < 0.995) & (avail_cap >= level)
        if derated.any():
            scaled = level * plant_avail[derated]
            self.assertTrue(
                np.all(applied[derated] > scaled + 1e-6),
                "floor is tracking the availability-SCALED value (ercot128 bug)",
            )

    def test_level_spills_into_higher_tranches_when_the_committed_band_derates(self):
        """A derated committed tranche must not shrink the plant's floor.

        The level is re-allocated in fill order over the plant's AVAILABLE
        tranche capacity, so what the committed band cannot carry is taken by
        the bands above it — the plant still holds its whole minimum
        configuration.
        """
        fleet, fa = _build(flag_on=True)
        idx = [
            i
            for i, g in enumerate(fleet)
            if g.plant_code == _LIMESTONE and g.fuel_type == "coal"
        ]
        level = sum(fleet[i].coal_min_config_pmin_mw for i in idx)
        tagged = fa.min_gen_mechanism[idx, :] == MECH_COAL_MIN_CONFIG
        applied = np.where(tagged, fa.min_gen[idx, :], 0.0)
        # Hours where the first floored tranche alone cannot carry the level.
        first = fa.availability[idx[0], :] * fa.pmax[idx[0]]
        avail_cap = (fa.availability[idx, :] * fa.pmax[idx, None]).sum(axis=0)
        spill = (first < level - 1e-6) & (avail_cap >= level)
        if spill.any():
            np.testing.assert_allclose(
                applied[:, spill].sum(axis=0), level, rtol=1e-6, atol=1e-3
            )
            self.assertTrue(
                (applied[1:, spill] > 0.0).any(),
                "level did not spill past the first tranche",
            )


if __name__ == "__main__":
    unittest.main()
