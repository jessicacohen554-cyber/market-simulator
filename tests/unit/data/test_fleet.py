"""Tests for the generation fleet inventory and vectorization."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HEAT_RATE_BINS
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import PROCESSED_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    _CC_SHOULDER_MONTHS,
    _SUMMER_CLASS_DERATE,
    _SUMMER_MONTHS,
    _SUMMER_WEFOR_SHARE,
    _AGGREGATABLE_FUELS,
    _hour_to_month_index,
    _map_fuel_type,
    EIA860_OPERABLE_VINTAGE,
    FUEL_TYPE_MAP,
    FUEL_TYPE_NAMES,
    Generator,
    aggregate_fleet,
    apply_coal_tranches,
    apply_ct_netload_drag_floor,
    apply_gas_st_netload_drag_floor,
    assemble_mc,
    coal_summer_derate_ratio,
    generators_to_fleet_arrays,
    load_fleet_from_csv,
    load_planned_additions,
    load_retired_within_window,
)
from market_sim.data.floor_mechanisms import (
    MECH_ST_GAS_MUSTRUN_PER_PLANT,
    MECH_ST_NETLOAD_DRAG,
)
from market_sim.config.constants import ST_GAS_COMMITMENT_PARAMS
from market_sim.data.fleet.floors import (
    _circular_centred_mean,
    _min_run_hours,
)


def _sample_generators() -> list[Generator]:
    """Return three generators spanning two zones and three fuel types."""
    return [
        Generator(
            unit_id="G1",
            name="Combined Cycle 1",
            zone="north",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            pmin_mw=120.0,
            heat_rate=6.8,
            eford=0.04,
        ),
        Generator(
            unit_id="G2",
            name="Combustion Turbine 1",
            zone="south",
            fuel_type="gas_ct",
            pmax_mw=100.0,
            heat_rate=10.5,
            eford=0.06,
        ),
        Generator(
            unit_id="G3",
            name="Coal 1",
            zone="north",
            fuel_type="coal",
            pmax_mw=600.0,
            pmin_mw=250.0,
            heat_rate=9.9,
            eford=0.08,
        ),
    ]


class TestFleetArrays(unittest.TestCase):
    """Tests for ``generators_to_fleet_arrays`` conversion."""

    def setUp(self):
        self.hours = 24
        self.zone_names = ["north", "south"]
        self.generators = _sample_generators()
        self.fleet = generators_to_fleet_arrays(
            self.generators, self.zone_names, hours=self.hours
        )

    def test_scalar_array_shape(self):
        self.assertEqual(self.fleet.pmax.shape, (3,))
        self.assertEqual(self.fleet.n_gen, 3)

    def test_availability_shape(self):
        self.assertEqual(self.fleet.availability.shape, (3, self.hours))

    def test_zone_idx_maps_zone_names(self):
        np.testing.assert_array_equal(self.fleet.zone_idx, [0, 1, 0])

    def test_fuel_type_idx_matches_map(self):
        expected = [
            FUEL_TYPE_MAP["gas_cc"],
            FUEL_TYPE_MAP["gas_ct"],
            FUEL_TYPE_MAP["coal"],
        ]
        np.testing.assert_array_equal(self.fleet.fuel_type_idx, expected)

    def test_availability_equals_one_minus_eford(self):
        for i, gen in enumerate(self.generators):
            expected = np.full(self.hours, 1.0 - gen.eford)
            np.testing.assert_allclose(self.fleet.availability[i], expected)

    def test_unit_ids_match(self):
        self.assertEqual(self.fleet.unit_ids, ["G1", "G2", "G3"])


class TestNuclearAvailability(unittest.TestCase):
    """Tests for nuclear seasonal availability shaping."""

    def _nuclear_gen(self) -> Generator:
        return Generator(
            unit_id="nuc1",
            name="Test Nuclear",
            zone="North",
            fuel_type="nuclear",
            pmax_mw=1000.0,
            pmin_mw=900.0,
            heat_rate=0.0,
            vom=2.5,
            emission_rate_co2=0.0,
            nox_rate=0.0,
            eford=0.03,
        )

    def test_nuclear_availability_seasonal(self):
        """Nuclear availability reflects monthly CF factors, not flat EFORD."""
        fa = generators_to_fleet_arrays([self._nuclear_gen()], ["North"], iso="ERCOT")

        # Availability should NOT be flat 0.97.
        self.assertGreater(
            fa.availability[0].std(),
            0.001,
            "Nuclear availability should vary by month",
        )

        # Annual average reflects the ERCOT monthly CF series (deep Apr/Oct
        # refueling troughs) scaled by 1 - EFORD: ~0.87.
        annual_avg = fa.availability[0].mean()
        self.assertTrue(
            0.85 < annual_avg < 0.89,
            f"Nuclear avg availability {annual_avg:.3f} outside 0.85-0.89",
        )

        # Spring months should have lower availability than summer.
        mar_hours = fa.availability[0, 1416:2160]
        jul_hours = fa.availability[0, 4344:5088]
        self.assertLess(
            mar_hours.mean(),
            jul_hours.mean(),
            "Spring should have lower availability than summer",
        )

    def test_caiso_nuclear_by_year_refueling(self):
        """CAISO backcast years use the Diablo Canyon EIA-923 monthly CF.

        The per-year vector embeds the actual staggered refueling cadence:
        unit 2 down Oct-Dec 2023, unit 1 down Apr-May 2024. The 923-derived
        CF is realized availability, applied directly (no EFORD stacking).
        """
        starts = np.cumsum(
            [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)]
        )
        cfg23 = ScenarioConfig(mode="backcast", weather_year=2023, iso="CAISO")
        fa23 = generators_to_fleet_arrays(
            [self._nuclear_gen()], ["North"], iso="CAISO", config=cfg23
        )
        oct23 = fa23.availability[0, starts[9] : starts[10]].mean()
        self.assertAlmostEqual(oct23, 0.47, places=2)

        cfg24 = ScenarioConfig(mode="backcast", weather_year=2024, iso="CAISO")
        fa24 = generators_to_fleet_arrays(
            [self._nuclear_gen()], ["North"], iso="CAISO", config=cfg24
        )
        apr24 = fa24.availability[0, starts[3] : starts[4]].mean()
        self.assertAlmostEqual(apr24, 0.60, places=2)
        # Full-output months run at the measured ~1.0, not 1 - EFORD.
        jan24 = fa24.availability[0, starts[0] : starts[1]].mean()
        self.assertAlmostEqual(jan24, 1.00, places=2)

    def test_no_iso_keeps_flat_availability(self):
        """Without an ISO, nuclear availability stays flat 1 - eford."""
        gen = self._nuclear_gen()
        fa = generators_to_fleet_arrays([gen], ["North"])
        np.testing.assert_allclose(fa.availability[0], 1.0 - gen.eford)

    def test_non_nuclear_unaffected_by_iso(self):
        """Non-nuclear units keep flat availability even with an ISO."""
        coal = Generator(
            unit_id="c1",
            name="Coal",
            zone="North",
            fuel_type="coal",
            pmax_mw=500.0,
            heat_rate=10.0,
            eford=0.08,
        )
        fa = generators_to_fleet_arrays([coal], ["North"], iso="ERCOT")
        np.testing.assert_allclose(fa.availability[0], 1.0 - coal.eford)


class TestCaisoChpOverrides(unittest.TestCase):
    """Tests for the derived CAISO CHP steam-following artifact."""

    def test_caiso_chp_artifact_loads(self):
        """thermal_tranches_CAISO.csv supplies per-plant floors + sectors."""
        from market_sim.data.chp import (
            chp_btm_pct,
            chp_overrides,
            chp_pmin_cf,
        )

        overrides = chp_overrides("CAISO")
        self.assertGreater(
            len(overrides),
            50,
            "CAISO CHP artifact should cover the cogen fleet",
        )
        for code, (pmin, sector, btm_override) in overrides.items():
            if pmin is not None:
                self.assertTrue(
                    0.0 <= pmin <= 75.0,
                    f"plant {code} floor {pmin} outside [0, 75]",
                )
            if sector is not None:
                self.assertIn(sector, ("merchant", "industrial", "commercial"))
            if btm_override is not None:
                self.assertTrue(
                    0.0 <= btm_override <= 100.0,
                    f"plant {code} btm_override {btm_override} outside [0, 100]",
                )
        # Watson Cogeneration (Torrance refinery host): EIA-923 floor re-derived
        # with factor=0.40 (Step 5 Lever C); BTM raised to 65% (per-plant override).
        self.assertAlmostEqual(chp_pmin_cf(50216, iso="CAISO"), 14.7, places=0)
        self.assertEqual(chp_btm_pct(50216, "CC_CHP", iso="CAISO"), 65.0)
        # The CAISO artifact must not leak into the ERCOT lookup (Baytown
        # keeps its hardcoded CAMPD value).
        self.assertEqual(chp_pmin_cf(55015, iso="ERCOT"), 49.7)


class TestThermalAvailability(unittest.TestCase):
    """Age-based thermal availability (POF / WEFOR / derate by category)."""

    # Hour offsets: April (shoulder) and July (summer peak).
    _APRIL_H = 31 * 24 + 28 * 24 + 31 * 24 + 100  # mid-April
    _JULY_H = sum([31, 28, 31, 30, 31, 30]) * 24 + 100  # mid-July

    def _arrays(self, plant_group, online_year, fuel_type, weather_year=2024):
        gen = Generator(
            unit_id="g1",
            name="G",
            zone="North",
            fuel_type=fuel_type,
            pmax_mw=400.0,
            heat_rate=8.0,
            online_year=online_year,
            plant_group=plant_group,
        )
        # These tests validate the legacy WEFOR/POF age mechanics and the
        # summer->shoulder redistribution, so they pin the flat-block model
        # (maintenance_monthly_shape=False). The forecast monthly-maintenance
        # shape is covered separately in TestMaintenanceMonthlyShape.
        return generators_to_fleet_arrays(
            [gen],
            ["North"],
            config=ScenarioConfig(
                weather_year=weather_year, maintenance_monthly_shape=False
            ),
        )

    @staticmethod
    def _old_annual_avail(pof, wefor, derate, hours=8760):
        # Annual-average availability of the prior flat-WEFOR + shoulder-POF
        # model, which the summer-shifting model conserves.
        month = _hour_to_month_index(hours) + 1
        shoulder = np.isin(month, list(_CC_SHOULDER_MONTHS))
        return (1.0 - wefor - derate) - pof * (int(shoulder.sum()) / hours)

    def test_old_coal_unit_summer_drops_pof_and_cuts_wefor(self):
        # Coal, age 47 (online 1977, run 2024): POF 7%, WEFOR 12 + 7*0.5 =
        # 15.5%, derate 3 + 12*0.2 = 5.4%. In the summer peak POF is removed
        # and only 30% of WEFOR applies; the annual average is conserved.
        fa = self._arrays("COAL", 1977, "coal")
        self.assertAlmostEqual(
            fa.availability[0, self._JULY_H],
            1.0 - _SUMMER_WEFOR_SHARE * 0.155 - 0.054,
        )
        self.assertGreater(
            fa.availability[0, self._JULY_H],
            fa.availability[0, self._APRIL_H],
        )
        self.assertAlmostEqual(
            fa.availability[0].mean(),
            self._old_annual_avail(0.07, 0.155, 0.054),
            places=4,
        )

    def test_modern_cc_no_escalation(self):
        # CC regular, age 14 (online 2010): below both onsets, so WEFOR 5%
        # and derate 2% stay at base; POF 5%. Summer applies only 30% of WEFOR
        # and no POF, then a CC summer ambient-temperature derate (heat cuts
        # gas-turbine output). The WEFOR redistribution conserves the annual
        # average; the summer ambient derate is an additional real loss.
        sd = _SUMMER_CLASS_DERATE["CC_REGULAR"]
        summer_pre = 1.0 - _SUMMER_WEFOR_SHARE * 0.05 - 0.02
        fa = self._arrays("CC_REGULAR", 2010, "gas_cc")
        self.assertAlmostEqual(
            fa.availability[0, self._JULY_H], summer_pre * (1.0 - sd)
        )
        summer = np.isin(_hour_to_month_index(8760) + 1, list(_SUMMER_MONTHS))
        summer_frac = int(summer.sum()) / 8760
        self.assertAlmostEqual(
            fa.availability[0].mean(),
            self._old_annual_avail(0.05, 0.05, 0.02) - sd * summer_pre * summer_frac,
            places=4,
        )

    def test_wefor_escalates_with_age(self):
        # CC regular, age 26 (online 1998): WEFOR escalates past onset 20 ->
        # 5 + 6*0.2 = 6.2%; derate past onset 25 -> 2 + 1*0.1 = 2.1%. Summer
        # also carries the CC ambient-temperature derate.
        sd = _SUMMER_CLASS_DERATE["CC_REGULAR"]
        fa = self._arrays("CC_REGULAR", 1998, "gas_cc")
        self.assertAlmostEqual(
            fa.availability[0, self._JULY_H],
            (1.0 - _SUMMER_WEFOR_SHARE * 0.062 - 0.021) * (1.0 - sd),
        )

    def test_non_thermal_keeps_eford(self):
        # A generator with no plant-group category keeps the 1 - EFORD derate.
        nuc = Generator(
            unit_id="n1",
            name="Nuke",
            zone="North",
            fuel_type="nuclear",
            pmax_mw=1000.0,
            heat_rate=10.0,
            eford=0.03,
        )
        fa = generators_to_fleet_arrays(
            [nuc], ["North"], config=ScenarioConfig(weather_year=2024)
        )
        np.testing.assert_allclose(fa.availability[0], 1.0 - 0.03)


class TestMaintenanceMonthlyShape(unittest.TestCase):
    """Forecast-mode historically-derived monthly maintenance shape (spec 1.7)."""

    _APRIL_H = 31 * 24 + 28 * 24 + 31 * 24 + 100  # mid-April (shoulder peak)
    _JULY_H = sum([31, 28, 31, 30, 31, 30]) * 24 + 100  # mid-July (summer peak)
    _JAN_H = 100  # mid-January (winter)

    @staticmethod
    def _gen(plant_group, online_year, fuel_type):
        return Generator(
            unit_id="g1",
            name="G",
            zone="North",
            fuel_type=fuel_type,
            pmax_mw=400.0,
            heat_rate=8.0,
            online_year=online_year,
            plant_group=plant_group,
        )

    def _fa(self, plant_group, online_year, fuel_type, shape=True, mode="forecast"):
        cfg = ScenarioConfig(
            mode=mode, weather_year=2024, maintenance_monthly_shape=shape
        )
        return generators_to_fleet_arrays(
            [self._gen(plant_group, online_year, fuel_type)], ["North"], config=cfg
        )

    def test_annual_budget_conserved_vs_flat_block(self):
        # The shape has a month-length-weighted mean of 1, so the annual-average
        # availability of a coal unit is identical to the legacy flat-block model
        # (only the seasonal distribution moves). Coal has no summer ambient
        # derate, so the conservation is exact.
        on = self._fa("COAL", 1977, "coal", shape=True)
        off = self._fa("COAL", 1977, "coal", shape=False)
        # places=5: the baked shape weights are rounded to 3 decimals, so the
        # mean-1 normalization (and thus budget conservation) holds to ~1e-6.
        self.assertAlmostEqual(
            on.availability[0].mean(), off.availability[0].mean(), places=5
        )

    def test_summer_peak_protected(self):
        # July weight is ~0 for the thermal groups, so the firm summer-peak
        # capacity is unchanged from the flat-block model (which also has no
        # summer POF).
        on = self._fa("COAL", 1977, "coal", shape=True)
        off = self._fa("COAL", 1977, "coal", shape=False)
        self.assertAlmostEqual(
            on.availability[0, self._JULY_H], off.availability[0, self._JULY_H]
        )

    def test_seasonal_reshape_spring_and_autumn(self):
        # The shape concentrates maintenance in spring/autumn: April availability
        # is below July (deeper maintenance), and below the flat-block April
        # (the curve peaks higher than the smeared block in its peak month).
        on = self._fa("CC_REGULAR", 2010, "gas_cc", shape=True)
        self.assertLess(
            on.availability[0, self._APRIL_H], on.availability[0, self._JULY_H]
        )

    def test_winter_carries_some_maintenance(self):
        # Unlike the flat block (zero POF in winter), the historical shape places
        # a modest amount of maintenance in winter — so January availability is
        # slightly below the flat-block January for a group with a nonzero winter
        # weight (coal Jan weight 0.239 > 0).
        on = self._fa("COAL", 1977, "coal", shape=True)
        off = self._fa("COAL", 1977, "coal", shape=False)
        self.assertLess(
            on.availability[0, self._JAN_H], off.availability[0, self._JAN_H]
        )

    def test_backcast_unaffected_by_flag(self):
        # In backcast mode the maintenance shape never engages (POF there comes
        # from the historic overlay path), so the flag is a no-op.
        on = self._fa("COAL", 1977, "coal", shape=True, mode="backcast")
        off = self._fa("COAL", 1977, "coal", shape=False, mode="backcast")
        np.testing.assert_allclose(on.availability[0], off.availability[0])


class TestCcDerateFromTop(unittest.TestCase):
    """Top-of-stack outage allocation for CC_REGULAR tranche stacks."""

    @staticmethod
    def _cc_tranches(eford=0.25):
        """A 2-tranche CC_REGULAR plant: 400 MW committed + 600 MW econ."""
        shared = dict(
            name="CC",
            zone="North",
            fuel_type="gas_cc",
            online_year=2020,
            plant_group="CC_REGULAR",
            plant_code=999,
            eford=eford,
        )
        return [
            Generator(unit_id="p999_committed", pmax_mw=400.0, heat_rate=6.0, **shared),
            Generator(unit_id="p999_econc00", pmax_mw=600.0, heat_rate=7.5, **shared),
        ]

    def test_derate_comes_off_the_top_tranche(self):
        """With the flag on, the committed floor keeps its full level."""
        fa = generators_to_fleet_arrays(
            self._cc_tranches(),
            ["North"],
            hours=24,
            config=ScenarioConfig(cc_outage_derate_from_top=True),
        )
        # 1000 MW * availability; committed (400 MW) fills first, the econ
        # tranche absorbs the entire shortfall.
        avail_mw = 400.0 * fa.availability[0] + 600.0 * fa.availability[1]
        self.assertTrue(np.all(fa.availability[0] == 1.0))
        self.assertTrue(np.all(fa.availability[1] < 1.0))
        # Plant-total available MW must be unchanged by the reallocation.
        fa_off = generators_to_fleet_arrays(
            self._cc_tranches(),
            ["North"],
            hours=24,
            config=ScenarioConfig(cc_outage_derate_from_top=False),
        )
        np.testing.assert_allclose(
            avail_mw,
            400.0 * fa_off.availability[0] + 600.0 * fa_off.availability[1],
        )

    def test_deep_outage_reaches_the_committed_tranche(self):
        """When available MW falls below the committed cap, it derates too."""
        fa = generators_to_fleet_arrays(
            self._cc_tranches(eford=0.70),
            ["North"],
            hours=24,
            config=ScenarioConfig(cc_outage_derate_from_top=True),
        )
        # 1000 * ~0.3 = ~300 MW available < 400 MW committed: econ zeroed,
        # committed holds the whole remainder.
        self.assertTrue(np.all(fa.availability[1] == 0.0))
        self.assertTrue(np.all(fa.availability[0] < 1.0))
        self.assertTrue(np.all(fa.availability[0] > 0.0))

    def test_flag_off_keeps_pro_rata(self):
        """Default behavior is unchanged: equal factors on every tranche."""
        fa = generators_to_fleet_arrays(
            self._cc_tranches(),
            ["North"],
            hours=24,
            config=ScenarioConfig(),
        )
        np.testing.assert_allclose(fa.availability[0], fa.availability[1])


class TestCtNetloadDragFloor(unittest.TestCase):
    """Evening-ramp net-load reliability-drag floor for CT_PEAKER."""

    @staticmethod
    def _ct_tranches():
        """A CT_PEAKER plant: 100 MW committed + 100 MW econ + 100 MW peak."""
        shared = dict(
            name="CT",
            zone="North",
            fuel_type="gas_ct",
            online_year=2018,
            plant_group="CT_PEAKER",
            plant_code=777,
        )
        return [
            Generator(
                unit_id="p777_committed", pmax_mw=100.0, heat_rate=10.0, **shared
            ),
            Generator(unit_id="p777_econc00", pmax_mw=100.0, heat_rate=11.0, **shared),
            Generator(unit_id="p777_peak", pmax_mw=100.0, heat_rate=13.0, **shared),
        ]

    def _net_load(self, hours):
        # Constant 40 GW net-load so the floor fraction is the same every hour
        # and only the ramp-window gate varies it.
        return np.full(hours, 40_000.0)

    def test_flag_off_is_noop(self):
        gens = self._ct_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        applied = apply_ct_netload_drag_floor(
            fa, gens, self._net_load(48), ScenarioConfig(ct_netload_drag=False)
        )
        self.assertFalse(applied)

    def test_floor_only_in_ramp_window_and_not_on_peak(self):
        gens = self._ct_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        cfg = ScenarioConfig(
            ct_netload_drag=True,
            ct_drag_slope_per_gw=0.00703,
            ct_drag_intercept=-0.1427,
            ct_drag_cap=0.47,
            ct_drag_ramp_start=15,
            ct_drag_ramp_end=22,
        )
        self.assertTrue(apply_ct_netload_drag_floor(fa, gens, self._net_load(48), cfg))
        # Expected fraction at 40 GW: 0.00703*40 - 0.1427 = 0.1385.
        frac = 0.00703 * 40.0 - 0.1427
        hod = np.arange(48) % 24
        in_win = (hod >= 15) & (hod < 22)
        # committed + econ tranches carry the floor in-window, zero out of window.
        for g in (0, 1):
            np.testing.assert_allclose(fa.min_gen[g, in_win], frac * 100.0, rtol=1e-6)
            np.testing.assert_allclose(fa.min_gen[g, ~in_win], 0.0)
        # the _peak scarcity tranche is never floored.
        np.testing.assert_allclose(fa.min_gen[2], 0.0)

    def test_floor_never_exceeds_available_capacity(self):
        gens = self._ct_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        fa.availability[0, :] = 0.05  # committed tranche nearly fully out
        cfg = ScenarioConfig(ct_netload_drag=True)
        apply_ct_netload_drag_floor(fa, gens, self._net_load(48), cfg)
        self.assertTrue(np.all(fa.min_gen[0] <= fa.availability[0] * 100.0 + 1e-9))


class TestGasStNetloadDragFloor(unittest.TestCase):
    """All-hours net-load reliability-drag floor for ST_GAS (via the shared engine)."""

    @staticmethod
    def _st_tranches():
        """An ST_GAS plant: 200 MW committed + 200 MW econ + 100 MW peak."""
        shared = dict(
            name="ST",
            zone="North",
            fuel_type="gas_st",
            online_year=1975,
            plant_group="ST_GAS",
            plant_code=555,
        )
        return [
            Generator(
                unit_id="p555_committed", pmax_mw=200.0, heat_rate=11.0, **shared
            ),
            Generator(unit_id="p555_econc00", pmax_mw=200.0, heat_rate=12.0, **shared),
            Generator(unit_id="p555_peak", pmax_mw=100.0, heat_rate=14.0, **shared),
        ]

    def test_flag_off_is_noop(self):
        gens = self._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        applied = apply_gas_st_netload_drag_floor(
            fa, gens, np.full(48, 40_000.0), ScenarioConfig(gas_st_netload_drag=False)
        )
        self.assertFalse(applied)

    def test_all_hours_floor_on_non_peak_tranches(self):
        gens = self._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        cfg = ScenarioConfig(
            gas_st_netload_drag=True,
            gas_st_drag_slope_per_gw=0.00906,
            gas_st_drag_intercept=-0.1376,
            gas_st_drag_cap=0.34,
        )
        self.assertTrue(
            apply_gas_st_netload_drag_floor(fa, gens, np.full(48, 40_000.0), cfg)
        )
        # Expected fraction at 40 GW: 0.00906*40 - 0.1376 = 0.2264, every hour
        # (no ramp window for the all-hours boiler).
        frac = 0.00906 * 40.0 - 0.1376
        np.testing.assert_allclose(fa.min_gen[0], frac * 200.0, rtol=1e-6)
        np.testing.assert_allclose(fa.min_gen[1], frac * 200.0, rtol=1e-6)
        # the _peak scarcity tranche is never floored.
        np.testing.assert_allclose(fa.min_gen[2], 0.0)


class TestNetloadDragMinRunPersistence(unittest.TestCase):
    """pjm-177: the drag's hour-eligibility persisted across each unit's min-run.

    The mechanism replaces WHICH HOURS the same mandate lands in and nothing
    else (rule 19 [R-ONE-MECH]) — same rows, same coefficients, same mechanism
    id — so these tests pin the three properties the screen rests on: the flag
    is byte-identical off, the transform is mean-preserving on the fraction,
    and a WINDOWED floor (the CT evening-ramp limb) is never persisted.
    """

    @staticmethod
    def _st_tranches():
        """An ST_GAS plant: 200 MW committed + 200 MW econ + 100 MW peak."""
        shared = dict(
            name="ST",
            zone="North",
            fuel_type="gas_st",
            online_year=1975,
            plant_group="ST_GAS",
            plant_code=555,
        )
        return [
            Generator(
                unit_id="p555_committed", pmax_mw=200.0, heat_rate=11.0, **shared
            ),
            Generator(unit_id="p555_econc00", pmax_mw=200.0, heat_rate=12.0, **shared),
            Generator(unit_id="p555_peak", pmax_mw=100.0, heat_rate=14.0, **shared),
        ]

    @staticmethod
    def _diurnal_netload(hours: int = 8760) -> np.ndarray:
        """A net-load with a strong diurnal wave straddling the zero-crossing."""
        t = np.arange(hours)
        return 70_000.0 + 25_000.0 * np.sin(2.0 * np.pi * (t % 24) / 24.0)

    def _cfg(self, **kw) -> ScenarioConfig:
        return ScenarioConfig(
            gas_st_netload_drag=True,
            gas_st_drag_slope_per_gw=0.01029,
            gas_st_drag_intercept=-0.7263,
            gas_st_drag_cap=0.39,
            **kw,
        )

    def test_flag_off_is_byte_identical(self):
        """The default path must not move a single float (every keeper replays)."""
        nl = self._diurnal_netload()
        gens_a, gens_b = self._st_tranches(), self._st_tranches()
        fa_a = generators_to_fleet_arrays(gens_a, ["North"], hours=8760)
        fa_b = generators_to_fleet_arrays(gens_b, ["North"], hours=8760)
        apply_gas_st_netload_drag_floor(fa_a, gens_a, nl, self._cfg())
        apply_gas_st_netload_drag_floor(
            fa_b, gens_b, nl, self._cfg(netload_drag_min_run_persistence=False)
        )
        self.assertTrue(np.array_equal(fa_a.min_gen, fa_b.min_gen))

    def test_persistence_is_mean_preserving_and_flattens_the_day(self):
        """Same annual mandate, no diurnal cycle — the whole claim, in one test."""
        nl = self._diurnal_netload()
        gens_c, gens_p = self._st_tranches(), self._st_tranches()
        fa_c = generators_to_fleet_arrays(gens_c, ["North"], hours=8760)
        fa_p = generators_to_fleet_arrays(gens_p, ["North"], hours=8760)
        apply_gas_st_netload_drag_floor(fa_c, gens_c, nl, self._cfg())
        apply_gas_st_netload_drag_floor(
            fa_p, gens_p, nl, self._cfg(netload_drag_min_run_persistence=True)
        )
        # availability is 1.0 in this fixture, so the clip never binds and the
        # mandate is preserved exactly rather than approximately.
        ctrl = fa_c.min_gen[:2].sum(axis=0)
        pers = fa_p.min_gen[:2].sum(axis=0)
        self.assertAlmostEqual(float(ctrl.sum()), float(pers.sum()), places=3)
        hod = np.arange(8760) % 24
        prof_c = np.array([ctrl[hod == h].mean() for h in range(24)])
        prof_p = np.array([pers[hod == h].mean() for h in range(24)])
        self.assertGreater(prof_c.max() / max(prof_c.min(), 1e-9), 3.0)
        self.assertAlmostEqual(prof_p.max() / prof_p.min(), 1.0, places=6)
        # the _peak scarcity tranche is still never floored.
        np.testing.assert_allclose(fa_p.min_gen[2], 0.0)

    def test_window_comes_from_the_frozen_table_not_the_bin(self):
        """Zero DOF: the window is the heat-rate-keyed commitment table (rule 21).

        A CAMPD-binned fleet carries ``min_run_hours = 0`` on every tranche, so
        reading the generator would silently disable the mechanism.
        """
        gens = self._st_tranches()
        self.assertTrue(all(g.min_run_hours == 0 for g in gens))
        self.assertEqual(_min_run_hours(gens[0], ST_GAS_COMMITMENT_PARAMS), 48)
        efficient = Generator(
            unit_id="p556_committed",
            name="ST",
            zone="North",
            fuel_type="gas_st",
            online_year=1975,
            plant_group="ST_GAS",
            plant_code=556,
            pmax_mw=100.0,
            heat_rate=9.0,
        )
        self.assertEqual(_min_run_hours(efficient, ST_GAS_COMMITMENT_PARAMS), 24)

    def test_ct_ramp_window_limb_is_never_persisted(self):
        """A WINDOWED floor keeps its window (rule 17 / rule 18: CTs cycle)."""
        shared = dict(
            name="CT",
            zone="North",
            fuel_type="gas_ct",
            online_year=2000,
            plant_group="CT_PEAKER",
            plant_code=777,
        )
        gens_c = [
            Generator(unit_id="p777_committed", pmax_mw=100.0, heat_rate=10.5, **shared)
        ]
        gens_p = [
            Generator(unit_id="p777_committed", pmax_mw=100.0, heat_rate=10.5, **shared)
        ]
        nl = self._diurnal_netload()
        cfg = dict(
            ct_netload_drag=True,
            ct_drag_slope_per_gw=0.01108,
            ct_drag_intercept=-0.9987,
            ct_drag_cap=0.46,
            ct_drag_ramp_start=15,
            ct_drag_ramp_end=22,
        )
        fa_c = generators_to_fleet_arrays(gens_c, ["North"], hours=8760)
        fa_p = generators_to_fleet_arrays(gens_p, ["North"], hours=8760)
        apply_ct_netload_drag_floor(fa_c, gens_c, nl, ScenarioConfig(**cfg))
        apply_ct_netload_drag_floor(
            fa_p,
            gens_p,
            nl,
            ScenarioConfig(netload_drag_min_run_persistence=True, **cfg),
        )
        self.assertTrue(np.array_equal(fa_c.min_gen, fa_p.min_gen))
        hod = np.arange(8760) % 24
        self.assertTrue(np.all(fa_p.min_gen[0][(hod < 15) | (hod >= 22)] == 0.0))

    def test_circular_centred_mean_is_exact_and_wraps(self):
        """The kernel is circular and mean-preserving (the LP's 8760 is cyclic)."""
        rng = np.random.default_rng(177)
        x = rng.random(240)
        for w in (24, 48):
            y = _circular_centred_mean(x, w)
            self.assertEqual(y.size, x.size)
            self.assertAlmostEqual(float(y.mean()), float(x.mean()), places=12)
        # a constant series is a fixed point; a pure 24 h wave is annihilated.
        np.testing.assert_allclose(
            _circular_centred_mean(np.full(240, 0.3), 24), 0.3, atol=1e-12
        )
        wave = np.sin(2.0 * np.pi * (np.arange(240) % 24) / 24.0)
        np.testing.assert_allclose(_circular_centred_mean(wave, 24), 0.0, atol=1e-12)


class TestNetloadDragLayupWindowMask(unittest.TestCase):
    """ercot-256 measured lay-up window mask on the net-load drag floors.

    The mask subtracts the merit-order guard's measured ECONOMIC-LAY-UP share
    from the floor's eligible-capacity clip basis, so the drag cannot force a
    plant on inside a window the model's own outage pipeline classified as
    not-operating (rule 17 [R-FLOOR-WINDOW]). Availability itself is untouched.
    """

    @staticmethod
    def _st_tranches():
        """One ST_GAS plant: 200 MW committed + 200 MW econ + 100 MW peak."""
        shared = dict(
            name="ST",
            zone="North",
            fuel_type="gas_st",
            online_year=1975,
            plant_group="ST_GAS",
            plant_code=555,
        )
        return [
            Generator(
                unit_id="p555_committed", pmax_mw=200.0, heat_rate=11.0, **shared
            ),
            Generator(unit_id="p555_econc00", pmax_mw=200.0, heat_rate=12.0, **shared),
            Generator(unit_id="p555_peak", pmax_mw=100.0, heat_rate=14.0, **shared),
        ]

    @staticmethod
    def _cfg(**kw):
        return ScenarioConfig(
            gas_st_netload_drag=True,
            gas_st_drag_slope_per_gw=0.00906,
            gas_st_drag_intercept=-0.1376,
            gas_st_drag_cap=0.34,
            **kw,
        )

    def test_none_is_byte_identical_to_the_unmasked_clip(self):
        gens = self._st_tranches()
        fa_a = generators_to_fleet_arrays(gens, ["North"], hours=48)
        fa_b = generators_to_fleet_arrays(gens, ["North"], hours=48)
        net = np.full(48, 40_000.0)
        apply_gas_st_netload_drag_floor(fa_a, gens, net, self._cfg())
        apply_gas_st_netload_drag_floor(fa_b, gens, net, self._cfg(), None)
        np.testing.assert_array_equal(fa_a.min_gen, fa_b.min_gen)

    def test_a_plant_with_no_series_is_unmasked(self):
        gens = self._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        # A series for a DIFFERENT plant must not reach plant 555.
        other = {(999, "ST_GAS"): np.ones(48)}
        apply_gas_st_netload_drag_floor(
            fa, gens, np.full(48, 40_000.0), self._cfg(), other
        )
        frac = 0.00906 * 40.0 - 0.1376
        np.testing.assert_allclose(fa.min_gen[0], frac * 200.0, rtol=1e-6)

    def test_full_layup_hours_lose_the_floor_entirely(self):
        gens = self._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        lu = np.zeros(48)
        lu[:24] = 1.0  # day 1 fully laid up, day 2 operating
        apply_gas_st_netload_drag_floor(
            fa, gens, np.full(48, 40_000.0), self._cfg(), {(555, "ST_GAS"): lu}
        )
        frac = 0.00906 * 40.0 - 0.1376
        np.testing.assert_allclose(fa.min_gen[0, :24], 0.0)
        np.testing.assert_allclose(fa.min_gen[0, 24:], frac * 200.0, rtol=1e-6)

    def test_partial_layup_caps_the_floor_at_the_non_laidup_share(self):
        gens = self._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        # Eligible = availability - 0.90, well below the 0.2264 curve fraction,
        # so the masked clip binds and sets the floor.
        avail = float(fa.availability[0, 0])
        apply_gas_st_netload_drag_floor(
            fa,
            gens,
            np.full(48, 40_000.0),
            self._cfg(),
            {(555, "ST_GAS"): np.full(48, 0.90)},
        )
        np.testing.assert_allclose(
            fa.min_gen[0], max(0.0, avail - 0.90) * 200.0, rtol=1e-6
        )

    def test_the_mask_can_only_remove_forcing_never_add_it(self):
        gens = self._st_tranches()
        fa_ctrl = generators_to_fleet_arrays(gens, ["North"], hours=48)
        fa_arm = generators_to_fleet_arrays(gens, ["North"], hours=48)
        net = np.linspace(20_000.0, 55_000.0, 48)
        rng = np.random.default_rng(0)
        lu = rng.random(48)
        apply_gas_st_netload_drag_floor(fa_ctrl, gens, net, self._cfg())
        apply_gas_st_netload_drag_floor(
            fa_arm, gens, net, self._cfg(), {(555, "ST_GAS"): lu}
        )
        self.assertTrue(np.all(fa_arm.min_gen <= fa_ctrl.min_gen + 1e-9))

    def test_resolver_is_inert_off_and_in_forecast_mode(self):
        from market_sim.data.fleet.floors import _resolve_drag_layup_shares

        off = ScenarioConfig(iso="ERCOT", mode="backcast")
        self.assertEqual(_resolve_drag_layup_shares(off, "ERCOT", 2021, 8760), {})
        # The field is registered in _BACKCAST_ONLY_OVERLAY_FIELDS, so arming it
        # in forecast mode is refused at construction (rule 13) — the engine
        # gate below is the second layer.
        with self.assertRaises(ValueError):
            ScenarioConfig(
                iso="ERCOT", mode="forecast", netload_drag_layup_window_mask=True
            )

    def test_ct_drag_forwards_the_mask_too(self):
        shared = dict(
            name="CT",
            zone="North",
            fuel_type="gas_ct",
            online_year=2000,
            plant_group="CT_PEAKER",
            plant_code=777,
        )
        gens = [
            Generator(unit_id="p777_committed", pmax_mw=100.0, heat_rate=10.0, **shared)
        ]
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        apply_ct_netload_drag_floor(
            fa,
            gens,
            np.full(48, 40_000.0),
            ScenarioConfig(ct_netload_drag=True),
            {(777, "CT_PEAKER"): np.ones(48)},
        )
        np.testing.assert_allclose(fa.min_gen[0], 0.0)


class TestNetloadDragMeritAllocation(unittest.TestCase):
    """ercot-259 merit-order ALLOCATION of the net-load drag mandate.

    The driver curve yields a FLEET capacity factor; the pro-rata applier puts
    it on every plant's own pmax, asserting that every plant is committed at
    that fraction in every hour. This mode keeps the SAME hourly mandate over
    the SAME rows and only redistributes it: commitment blocks before economic
    tranches, cheapest first. Rule 19 [R-ONE-MECH] — only the level source
    changes; same mechanism id, still a per-row min_gen, so D-2/D-4 attribution
    and the C8 forced share stay measurable.
    """

    @staticmethod
    def _two_plants():
        """A cheap plant and an expensive one, each committed + econ + peak."""

        def _p(code, name, hr):
            shared = dict(
                name=name,
                zone="North",
                fuel_type="gas_st",
                online_year=1975,
                plant_group="ST_GAS",
                plant_code=code,
            )
            return [
                Generator(
                    unit_id=f"p{code}_committed",
                    pmax_mw=100.0,
                    heat_rate=hr,
                    **shared,
                ),
                Generator(
                    unit_id=f"p{code}_econc00",
                    pmax_mw=100.0,
                    heat_rate=hr + 1.0,
                    **shared,
                ),
                Generator(
                    unit_id=f"p{code}_peak", pmax_mw=50.0, heat_rate=hr + 3.0, **shared
                ),
            ]

        return _p(111, "CHEAP", 9.0) + _p(222, "PRICEY", 13.0)

    @staticmethod
    def _cfg(**kw):
        return ScenarioConfig(
            gas_st_netload_drag=True,
            gas_st_drag_slope_per_gw=0.00906,
            gas_st_drag_intercept=-0.1376,
            gas_st_drag_cap=0.34,
            **kw,
        )

    def _run(self, merit, net):
        gens = self._two_plants()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=len(net))
        apply_gas_st_netload_drag_floor(
            fa, gens, net, self._cfg(netload_drag_merit_allocation=merit)
        )
        return gens, fa

    def test_default_off_is_byte_identical(self):
        net = np.full(48, 40_000.0)
        _, fa_off = self._run(False, net)
        gens = self._two_plants()
        fa_plain = generators_to_fleet_arrays(gens, ["North"], hours=48)
        apply_gas_st_netload_drag_floor(fa_plain, gens, net, self._cfg())
        np.testing.assert_array_equal(fa_off.min_gen, fa_plain.min_gen)

    def test_aggregate_is_preserved_even_when_availability_clips(self):
        """The clip case: pro-rata drops the shortfall, so must the merit fill.

        Targeting the NOMINAL floor_frac x sum(pmax) instead of the delivered
        MW would silently raise the class's total forcing (measured +20-40 % on
        the real ERCOT fleet), folding a level change into an allocation swap.
        """
        net = np.full(24, 45_000.0)
        gens = self._two_plants()
        outs = []
        for merit in (False, True):
            fa = generators_to_fleet_arrays(gens, ["North"], hours=24)
            # Squeeze availability well below the curve fraction so the
            # pro-rata path's min() clip binds on every row.
            fa.availability[:] = 0.05
            apply_gas_st_netload_drag_floor(
                fa, gens, net, self._cfg(netload_drag_merit_allocation=merit)
            )
            outs.append(fa.min_gen.sum(axis=0))
        np.testing.assert_allclose(outs[1], outs[0], rtol=1e-9)
        self.assertGreater(float(outs[0][0]), 0.0)

    def test_the_hourly_aggregate_is_preserved(self):
        """Same mandated MW per hour — only its distribution changes."""
        net = np.linspace(20_000.0, 50_000.0, 48)
        _, fa_u = self._run(False, net)
        _, fa_m = self._run(True, net)
        # Sum over the class's rows, hour by hour. The peak tranche carries no
        # floor in either mode, so the totals are directly comparable.
        np.testing.assert_allclose(
            fa_m.min_gen.sum(axis=0), fa_u.min_gen.sum(axis=0), rtol=1e-9
        )

    def test_the_mandate_lands_on_the_cheap_plant_first(self):
        net = np.full(48, 40_000.0)
        gens, fa = self._run(True, net)
        idx = {g.unit_id: i for i, g in enumerate(gens)}
        frac = 0.00906 * 40.0 - 0.1376
        avail = float(fa.availability[idx["p111_committed"], 0])
        total = frac * (100.0 + 100.0 + 100.0 + 100.0)  # non-peak pmax
        # The cheap plant's commitment block absorbs the whole mandate ...
        np.testing.assert_allclose(
            fa.min_gen[idx["p111_committed"], 0], min(total, avail * 100.0), rtol=1e-6
        )
        # ... and the expensive plant is not forced at all.
        np.testing.assert_allclose(fa.min_gen[idx["p222_committed"]], 0.0)
        np.testing.assert_allclose(fa.min_gen[idx["p222_econc00"]], 0.0)

    def test_commitment_blocks_fill_before_any_economic_tranche(self):
        """Both plants commit at min load before either runs above it."""
        # A high net-load whose mandate exceeds one plant's committed block.
        net = np.full(24, 52_000.0)
        gens, fa = self._run(True, net)
        idx = {g.unit_id: i for i, g in enumerate(gens)}
        # The PRICEY plant's committed tranche is floored ...
        self.assertGreater(float(fa.min_gen[idx["p222_committed"], 0]), 0.0)
        # ... while the CHEAP plant's economic tranche is not yet reached.
        np.testing.assert_allclose(fa.min_gen[idx["p111_econc00"]], 0.0)

    def test_the_peak_tranche_is_never_floored(self):
        gens, fa = self._run(True, np.full(24, 52_000.0))
        idx = {g.unit_id: i for i, g in enumerate(gens)}
        for uid in ("p111_peak", "p222_peak"):
            np.testing.assert_allclose(fa.min_gen[idx[uid]], 0.0)

    def test_forcing_stays_attributed_so_c8_cannot_go_blind(self):
        """The anti-blindness property: every floored cell keeps its mech id."""
        gens, fa = self._run(True, np.full(24, 45_000.0))
        self.assertIsNotNone(fa.min_gen_mechanism)
        forced = fa.min_gen > 0.0
        self.assertTrue(forced.any(), "the arm must actually force something")
        self.assertTrue(
            np.all(fa.min_gen_mechanism[forced] == MECH_ST_NETLOAD_DRAG),
            "a forced cell with no mechanism id would make D-2/D-4 blind",
        )

    def test_the_layup_mask_still_bounds_the_fill(self):
        """A fully laid-up plant carries no floor and the fill moves on."""
        gens = self._two_plants()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=24)
        idx = {g.unit_id: i for i, g in enumerate(gens)}
        apply_gas_st_netload_drag_floor(
            fa,
            gens,
            np.full(24, 40_000.0),
            self._cfg(netload_drag_merit_allocation=True),
            {(111, "ST_GAS"): np.ones(24)},
        )
        np.testing.assert_allclose(fa.min_gen[idx["p111_committed"]], 0.0)
        # The mandate falls through to the next-cheapest commitment block.
        self.assertGreater(float(fa.min_gen[idx["p222_committed"], 0]), 0.0)

    def test_zero_netload_floor_forces_nothing(self):
        gens, fa = self._run(True, np.full(24, 10_000.0))  # below the ~15.2 GW crossing
        np.testing.assert_allclose(fa.min_gen, 0.0)


class TestGasStSeasonalDrag(unittest.TestCase):
    """ERCOT-91 season-grain fix of the ST_GAS drag curve (gas_st_drag_seasonal)."""

    _SEASONS = {
        "0": {"name": "DJF", "slope_per_gw": 0.014, "intercept": -0.43, "cap": 0.27},
        "1": {"name": "MAM", "slope_per_gw": 0.007, "intercept": -0.11, "cap": 0.24},
        "2": {"name": "JJA", "slope_per_gw": 0.011, "intercept": -0.28, "cap": 0.36},
        "3": {"name": "SON", "slope_per_gw": 0.006, "intercept": -0.08, "cap": 0.28},
    }

    def _artifact(self, tmp, iso="ERCOT", drop_season=None):
        import json as _json

        seasons = dict(self._SEASONS)
        if drop_season is not None:
            seasons.pop(drop_season)
        path = tmp / "seasonal.json"
        path.write_text(
            _json.dumps(
                {
                    "_provenance": {
                        "iso": iso,
                        "season_of_month": [0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0],
                    },
                    "seasons": seasons,
                }
            )
        )
        return str(path)

    def test_seasonal_swaps_coefficients_by_calendar_season(self):
        import pathlib
        import tempfile

        gens = TestGasStNetloadDragFloor._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=8760)
        with tempfile.TemporaryDirectory() as td:
            cfg = ScenarioConfig(
                gas_st_netload_drag=True,
                gas_st_drag_seasonal=True,
                gas_st_drag_seasonal_path=self._artifact(pathlib.Path(td)),
            )
            self.assertTrue(
                apply_gas_st_netload_drag_floor(fa, gens, np.full(8760, 40_000.0), cfg)
            )
        # Hour 0 is January (DJF): clip(0.014*40 - 0.43, 0, 0.27) = 0.13.
        np.testing.assert_allclose(fa.min_gen[0, 0], 0.13 * 200.0, rtol=1e-6)
        # July 1 (hoy = 181*24) is JJA: clip(0.011*40 - 0.28, 0, 0.36) = 0.16.
        jul = 181 * 24
        np.testing.assert_allclose(fa.min_gen[0, jul], 0.16 * 200.0, rtol=1e-6)
        # April 1 (hoy = 90*24) is MAM: clip(0.007*40 - 0.11, 0, 0.24) = 0.17.
        apr = 90 * 24
        np.testing.assert_allclose(fa.min_gen[0, apr], 0.17 * 200.0, rtol=1e-6)
        # the _peak scarcity tranche is never floored, seasonal or not.
        np.testing.assert_allclose(fa.min_gen[2], 0.0)

    def test_seasonal_off_keeps_pooled_scalars(self):
        gens = TestGasStNetloadDragFloor._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        cfg = ScenarioConfig(gas_st_netload_drag=True, gas_st_drag_seasonal=False)
        apply_gas_st_netload_drag_floor(fa, gens, np.full(48, 40_000.0), cfg)
        frac = 0.00906 * 40.0 - 0.1376
        np.testing.assert_allclose(fa.min_gen[0], frac * 200.0, rtol=1e-6)

    def test_iso_mismatch_is_hard_error(self):
        import pathlib
        import tempfile

        gens = TestGasStNetloadDragFloor._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        with tempfile.TemporaryDirectory() as td:
            cfg = ScenarioConfig(
                iso="PJM",
                gas_st_netload_drag=True,
                gas_st_drag_seasonal=True,
                gas_st_drag_seasonal_path=self._artifact(pathlib.Path(td)),
            )
            with self.assertRaisesRegex(ValueError, "rule 25"):
                apply_gas_st_netload_drag_floor(fa, gens, np.full(48, 40_000.0), cfg)

    def test_missing_season_is_hard_error(self):
        import pathlib
        import tempfile

        gens = TestGasStNetloadDragFloor._st_tranches()
        fa = generators_to_fleet_arrays(gens, ["North"], hours=48)
        with tempfile.TemporaryDirectory() as td:
            cfg = ScenarioConfig(
                gas_st_netload_drag=True,
                gas_st_drag_seasonal=True,
                gas_st_drag_seasonal_path=self._artifact(
                    pathlib.Path(td), drop_season="2"
                ),
            )
            with self.assertRaisesRegex(ValueError, "season 2"):
                apply_gas_st_netload_drag_floor(fa, gens, np.full(48, 40_000.0), cfg)


class TestAssembleMC(unittest.TestCase):
    """Tests for the vectorized marginal cost assembly."""

    def test_single_gen_constant_fuel_price(self):
        gen = Generator(
            unit_id="G1",
            name="CC 1",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            heat_rate=7.0,
            vom=3.0,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=4)
        fuel_prices = np.full((1, 4), 4.0)
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        self.assertEqual(mc.shape, (1, 4))
        np.testing.assert_allclose(mc, 7.0 * 4.0 + 3.0)

    def test_two_gens_different_heat_rates(self):
        gens = [
            Generator(
                unit_id="G1",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=400.0,
                heat_rate=7.0,
            ),
            Generator(
                unit_id="G2",
                name="CT",
                zone="z",
                fuel_type="gas_ct",
                pmax_mw=100.0,
                heat_rate=11.0,
            ),
        ]
        fleet = generators_to_fleet_arrays(gens, ["z"], hours=3)
        fuel_prices = np.full((2, 3), 5.0)
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        np.testing.assert_allclose(mc[0], 35.0)
        np.testing.assert_allclose(mc[1], 55.0)
        self.assertFalse(np.allclose(mc[0], mc[1]))

    def test_carbon_price_scales_with_emission_rate(self):
        gen = Generator(
            unit_id="G1",
            name="Coal",
            zone="z",
            fuel_type="coal",
            pmax_mw=600.0,
            heat_rate=10.0,
            emission_rate_co2=0.95,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=2)
        fuel_prices = np.full((1, 2), 2.0)
        base = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        with_carbon = assemble_mc(fleet, fuel_prices, carbon_price=50.0)
        np.testing.assert_allclose(with_carbon - base, 0.95 * 50.0)

    def test_custom_adder(self):
        gen = Generator(
            unit_id="G1",
            name="Coal",
            zone="z",
            fuel_type="coal",
            pmax_mw=600.0,
            heat_rate=10.0,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=3)
        fuel_prices = np.full((1, 3), 2.0)
        so2_rate = np.array([0.4])
        so2_price = np.array([10.0, 20.0, 30.0])
        mc = assemble_mc(
            fleet,
            fuel_prices,
            carbon_price=0.0,
            so2=(so2_rate, so2_price),
        )
        expected = 10.0 * 2.0 + 0.4 * so2_price
        np.testing.assert_allclose(mc[0], expected)

    def test_time_varying_fuel_price(self):
        gen = Generator(
            unit_id="G1",
            name="CC",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=400.0,
            heat_rate=7.0,
            vom=2.0,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=4)
        fuel_prices = np.array([[3.0, 4.0, 5.0, 6.0]])
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        np.testing.assert_allclose(mc[0], 7.0 * fuel_prices[0] + 2.0)
        self.assertFalse(np.allclose(mc[0], mc[0, 0]))


class TestFleetLoader(unittest.TestCase):
    """Tests for ``load_fleet_from_csv``."""

    ALL_ISOS = [
        "ERCOT",
        "CAISO",
        "PJM",
        "MISO",
        "NYISO",
        "NEISO",
        "SPP",
        "NWPP",
        "SOCO",
    ]

    def _gw(self, generators: list[Generator]) -> float:
        """Return the total fleet capacity in GW."""
        return sum(g.pmax_mw for g in generators) / 1000.0

    def test_ercot_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("ERCOT")
        self.assertGreaterEqual(self._gw(fleet), 70.0)
        self.assertLessEqual(self._gw(fleet), 120.0)

    def test_caiso_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("CAISO")
        self.assertGreaterEqual(self._gw(fleet), 25.0)
        self.assertLessEqual(self._gw(fleet), 50.0)

    def test_pjm_fleet_total_in_range(self):
        fleet = load_fleet_from_csv("PJM")
        self.assertGreaterEqual(self._gw(fleet), 150.0)
        self.assertLessEqual(self._gw(fleet), 200.0)

    def test_no_generators_in_wecc_import_zone(self):
        fleet = load_fleet_from_csv("CAISO")
        self.assertTrue(all(g.zone != "WECC_import" for g in fleet))

    def test_nuclear_units_are_must_run(self):
        fleet = load_fleet_from_csv("ERCOT")
        nuclear = [g for g in fleet if g.fuel_type == "nuclear"]
        self.assertTrue(nuclear)
        self.assertTrue(all(g.is_must_run for g in nuclear))

    def test_heat_rates_use_actual_egrid_values(self):
        # With eGRID PLHTRT joined into the parquet, gas_cc units span a
        # real heat-rate gradient instead of collapsing onto the three
        # HEAT_RATE_BINS vintage centers.
        fleet = load_fleet_from_csv("ERCOT")
        cc_hrs = {round(g.heat_rate, 3) for g in fleet if g.fuel_type == "gas_cc"}
        bin_centers = set(HEAT_RATE_BINS["gas_cc"].values())
        self.assertGreater(len(cc_hrs), len(bin_centers))
        self.assertTrue(
            cc_hrs - bin_centers, "no actual (non-bin-center) heat rates loaded"
        )

    def test_missing_heat_rate_falls_back_to_bin_centers(self):
        # Units with no eGRID match keep the vintage bin-center fallback,
        # so every loaded generator still has a positive heat rate.
        fleet = load_fleet_from_csv("ERCOT")
        self.assertTrue(
            all(g.heat_rate > 0.0 for g in fleet if g.fuel_type in HEAT_RATE_BINS)
        )

    def test_some_coal_units_have_retirement_year(self):
        fleet = load_fleet_from_csv("ERCOT")
        coal = [g for g in fleet if g.fuel_type == "coal"]
        self.assertTrue(any(g.retirement_year is not None for g in coal))

    def test_fleet_converts_to_fleet_arrays(self):
        config = get_iso_config("ERCOT")
        fleet = load_fleet_from_csv("ERCOT", config)
        arrays = generators_to_fleet_arrays(fleet, config.zone_names, hours=24)
        self.assertEqual(arrays.n_gen, len(fleet))
        self.assertEqual(arrays.pmax.shape, (len(fleet),))
        self.assertEqual(arrays.availability.shape, (len(fleet), 24))

    def test_all_seven_isos_load(self):
        for iso in self.ALL_ISOS:
            fleet = load_fleet_from_csv(iso)
            self.assertTrue(fleet, f"{iso} fleet is empty")
            zone_names = sorted({g.zone for g in fleet})
            arrays = generators_to_fleet_arrays(fleet, zone_names, hours=4)
            self.assertEqual(arrays.n_gen, len(fleet))

    def test_raises_when_no_eia860_data(self):
        with tempfile.TemporaryDirectory() as empty_dir:
            with self.assertRaises(FileNotFoundError):
                load_fleet_from_csv("ERCOT", data_dir=Path(empty_dir))


class TestAggregateFleet(unittest.TestCase):
    """Tests for collapsing individual units into representative units."""

    def _gas_cc_fleet(self) -> list[Generator]:
        """Ten gas_cc units across two zones and two efficiency bins.

        Five units per zone, alternating efficiency bins, so the fleet
        spans all four ``(fuel_type, efficiency_bin, zone)`` groups.
        """
        gens: list[Generator] = []
        for i in range(10):
            zone = "north" if i < 5 else "south"
            ebin = "h_class" if i % 2 == 0 else "f_class"
            gens.append(
                Generator(
                    unit_id=f"CC{i}",
                    name=f"CC{i}",
                    zone=zone,
                    fuel_type="gas_cc",
                    efficiency_bin=ebin,
                    pmax_mw=100.0 + 10.0 * i,
                    pmin_mw=20.0 + i,
                    heat_rate=6.5 + 0.1 * i,
                    vom=3.0,
                    emission_rate_co2=0.36,
                    nox_rate=0.02,
                    eford=0.05,
                )
            )
        return gens

    def test_groups_collapse_to_representative_units(self):
        # 2 zones x 2 efficiency bins -> 4 representative units.
        result = aggregate_fleet(self._gas_cc_fleet())
        self.assertEqual(len(result), 4)
        keys = {(g.fuel_type, g.efficiency_bin, g.zone) for g in result}
        self.assertEqual(
            keys,
            {
                ("gas_cc", "h_class", "north"),
                ("gas_cc", "f_class", "north"),
                ("gas_cc", "h_class", "south"),
                ("gas_cc", "f_class", "south"),
            },
        )

    def test_representative_unit_id_and_name(self):
        result = aggregate_fleet(self._gas_cc_fleet())
        for g in result:
            expected = f"{g.fuel_type}_{g.efficiency_bin}_{g.zone}"
            self.assertEqual(g.unit_id, expected)
            self.assertEqual(g.name, expected)

    def test_aggregated_pmax_is_group_sum(self):
        gens = self._gas_cc_fleet()
        result = aggregate_fleet(gens)
        for rep in result:
            group = [
                g
                for g in gens
                if g.fuel_type == rep.fuel_type
                and g.efficiency_bin == rep.efficiency_bin
                and g.zone == rep.zone
            ]
            self.assertAlmostEqual(rep.pmax_mw, sum(g.pmax_mw for g in group))
            self.assertAlmostEqual(rep.pmin_mw, sum(g.pmin_mw for g in group))

    def test_aggregated_heat_rate_is_capacity_weighted(self):
        gens = self._gas_cc_fleet()
        result = aggregate_fleet(gens)
        for rep in result:
            group = [
                g
                for g in gens
                if g.fuel_type == rep.fuel_type
                and g.efficiency_bin == rep.efficiency_bin
                and g.zone == rep.zone
            ]
            total_cap = sum(g.pmax_mw for g in group)
            expected = sum(g.heat_rate * g.pmax_mw for g in group) / total_cap
            self.assertAlmostEqual(rep.heat_rate, expected)

    def test_nuclear_units_pass_through_unchanged(self):
        nuclear = [
            Generator(
                unit_id="NUKE1",
                name="Nuke 1",
                zone="north",
                fuel_type="nuclear",
                pmax_mw=1200.0,
                pmin_mw=1080.0,
                heat_rate=10.4,
                is_must_run=True,
            ),
            Generator(
                unit_id="NUKE2",
                name="Nuke 2",
                zone="south",
                fuel_type="nuclear",
                pmax_mw=1350.0,
                pmin_mw=1215.0,
                heat_rate=10.4,
                is_must_run=True,
            ),
        ]
        result = aggregate_fleet(nuclear)
        self.assertEqual(result, nuclear)

    def test_scheduled_retirement_units_pass_through(self):
        # A thermal unit with a retirement_year keeps its identity so the
        # known-retirement mechanism can still apply its scheduled exit.
        gens = [
            Generator(
                unit_id="C_RET",
                name="C_RET",
                zone="north",
                fuel_type="coal",
                efficiency_bin="older",
                pmax_mw=300.0,
                retirement_year=2030,
            ),
            Generator(
                unit_id="C0",
                name="C0",
                zone="north",
                fuel_type="coal",
                efficiency_bin="older",
                pmax_mw=400.0,
            ),
        ]
        result = aggregate_fleet(gens)
        self.assertEqual(len(result), 2)
        ids = {g.unit_id for g in result}
        self.assertIn("C_RET", ids)
        self.assertIn("coal_older_north", ids)

    def test_campd_bins_pass_through_preserving_plant_code(self):
        # G-28: CAMPD per-plant tranches (is_campd_bin) must survive
        # re-aggregation with their plant_code intact so a confirmed exit
        # effective 2+ years into a forecast still matches by plant_code.
        # Two same-(fuel, bin, zone) tranches from DIFFERENT plants would be
        # merged into one vintage representative (losing plant_code) without
        # the passthrough; a plain thermal unit alongside still aggregates.
        gens = [
            Generator(
                unit_id="3470_coal_mustrun",
                name="3470_coal_mustrun",
                zone="north",
                fuel_type="coal",
                efficiency_bin="COAL",
                pmax_mw=300.0,
                heat_rate=9.5,
                is_campd_bin=True,
                plant_group="COAL",
                plant_code=3470,
            ),
            Generator(
                unit_id="6146_coal_econ",
                name="6146_coal_econ",
                zone="north",
                fuel_type="coal",
                efficiency_bin="COAL",
                pmax_mw=500.0,
                heat_rate=10.2,
                is_campd_bin=True,
                plant_group="COAL",
                plant_code=6146,
            ),
            Generator(
                unit_id="legacy_coal",
                name="legacy_coal",
                zone="north",
                fuel_type="coal",
                efficiency_bin="older",
                pmax_mw=400.0,
                heat_rate=11.0,
            ),
        ]
        result = aggregate_fleet(gens)
        ids = {g.unit_id for g in result}
        # Both CAMPD tranches pass through with their identity intact.
        self.assertIn("3470_coal_mustrun", ids)
        self.assertIn("6146_coal_econ", ids)
        by_id = {g.unit_id: g for g in result}
        self.assertEqual(by_id["3470_coal_mustrun"].plant_code, 3470)
        self.assertEqual(by_id["6146_coal_econ"].plant_code, 6146)
        self.assertEqual(by_id["6146_coal_econ"].pmax_mw, 500.0)  # not merged
        # The legacy (non-CAMPD) unit still collapses to a vintage rep.
        self.assertIn("coal_older_north", ids)

    def test_campd_bins_pass_through_under_n_bins(self):
        # The integer-n_bins path must also preserve plant_code identity.
        gens = [
            Generator(
                unit_id="3470_coal_mustrun",
                name="3470_coal_mustrun",
                zone="north",
                fuel_type="coal",
                efficiency_bin="COAL",
                pmax_mw=300.0,
                heat_rate=9.5,
                is_campd_bin=True,
                plant_code=3470,
            ),
            Generator(
                unit_id="6146_coal_econ",
                name="6146_coal_econ",
                zone="north",
                fuel_type="coal",
                efficiency_bin="COAL",
                pmax_mw=500.0,
                heat_rate=10.2,
                is_campd_bin=True,
                plant_code=6146,
            ),
        ]
        result = aggregate_fleet(gens, n_bins=3)
        by_id = {g.unit_id: g for g in result}
        self.assertEqual(by_id["3470_coal_mustrun"].plant_code, 3470)
        self.assertEqual(by_id["6146_coal_econ"].plant_code, 6146)

    def test_more_bins_produce_more_cc_groups(self):
        # With actual per-plant heat rates, n_bins=10 yields a finer merit
        # order -- more distinct gas_cc bins than n_bins=3.
        fleet = load_fleet_from_csv("ERCOT")
        cc_3 = [g for g in aggregate_fleet(fleet, n_bins=3) if g.fuel_type == "gas_cc"]
        cc_10 = [
            g for g in aggregate_fleet(fleet, n_bins=10) if g.fuel_type == "gas_cc"
        ]
        self.assertGreater(len(cc_10), len(cc_3))
        hrs_3 = {round(g.heat_rate, 2) for g in cc_3}
        hrs_10 = {round(g.heat_rate, 2) for g in cc_10}
        self.assertGreater(len(hrs_10), len(hrs_3))

    def test_n_bins_zero_disables_aggregation(self):
        gens = self._gas_cc_fleet()
        self.assertEqual(aggregate_fleet(gens, n_bins=0), gens)
        self.assertEqual(aggregate_fleet(gens, n_bins="unit"), gens)

    def test_round_trip_to_fleet_arrays(self):
        aggregated = aggregate_fleet(self._gas_cc_fleet())
        arrays = generators_to_fleet_arrays(aggregated, ["north", "south"], hours=24)
        self.assertEqual(arrays.n_gen, 4)
        self.assertEqual(arrays.pmax.shape, (4,))
        self.assertEqual(arrays.availability.shape, (4, 24))
        self.assertEqual(len(arrays.unit_ids), 4)


class TestAggregationPreservesVintage(unittest.TestCase):
    """Bin representatives carry a capacity-weighted ``online_year``.

    Dropping the vintage to the Generator default (2000) made every
    aggregated gas-CC bin look near end-of-life, permanently disqualifying
    it from the CCS-retrofit screen and breaking new-build learning
    attribution (peer review B3).
    """

    def _two_unit_fleet(self) -> list[Generator]:
        common = dict(
            zone="north",
            fuel_type="gas_cc",
            efficiency_bin="h_class",
            heat_rate=6.5,
            vom=3.0,
            emission_rate_co2=0.36,
            nox_rate=0.02,
            eford=0.05,
        )
        return [
            Generator(
                unit_id="CC_old",
                name="CC_old",
                pmax_mw=100.0,
                pmin_mw=0.0,
                online_year=2010,
                **common,
            ),
            Generator(
                unit_id="CC_new",
                name="CC_new",
                pmax_mw=300.0,
                pmin_mw=0.0,
                online_year=2020,
                **common,
            ),
        ]

    def test_vintage_bin_path(self):
        (rep,) = aggregate_fleet(self._two_unit_fleet())
        # (2010*100 + 2020*300) / 400 = 2017.5 -> 2018.
        self.assertEqual(rep.online_year, 2018)

    def test_equal_width_bin_path(self):
        (rep,) = aggregate_fleet(self._two_unit_fleet(), n_bins=1)
        self.assertEqual(rep.online_year, 2018)


class TestLoadPlannedAdditions(unittest.TestCase):
    """EIA-860 planned/under-construction thermal units (spec §5.4)."""

    def test_ercot_planned_units(self):
        gens = load_planned_additions("ERCOT")
        self.assertTrue(
            gens, "expected planned units in the committed EIA-860 proposed parquet"
        )
        for g in gens:
            # Construction-committed, post-snapshot, thermal-only.
            self.assertGreater(g.online_year, EIA860_OPERABLE_VINTAGE)
            self.assertIn(
                g.fuel_type,
                {"gas_cc", "gas_ct", "coal", "nuclear", "oil", "biomass"},
            )
            self.assertTrue(g.unit_id.startswith("planned_"))
            self.assertGreater(g.pmax_mw, 0.0)
        # Sorted by online year so the runner's year filter sees them in
        # chronological order.
        years = [g.online_year for g in gens]
        self.assertEqual(years, sorted(years))

    def test_unknown_data_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_planned_additions("ERCOT", data_dir=tmp), [])


class TestLoadRetiredWithinWindow(unittest.TestCase):
    """Within-window plant exits — the backcast mirror of planned additions."""

    def test_neiso_includes_mystic_cc(self):
        retirees = load_retired_within_window("NEISO")
        self.assertTrue(retirees, "expected NEISO within-window retirees")
        # 7934e92c (2026-09-09) widened the retiree window 2023 -> 2019, which
        # correctly adds Mystic's 2021 exits (unit 7 steam + GT1, oil) to plant
        # 1588. The CC assertions below are about the 2024 CC exit, so they
        # scope to the in-2023+ rows; the 2021 rows are pinned separately.
        plant = [g for g in retirees if int(g.plant_code) == 1588]
        mystic = [g for g in plant if g.retirement_year >= 2023]
        self.assertTrue(mystic, "Mystic (plant 1588) should be a NEISO exit")
        early = [g for g in plant if g.retirement_year < 2023]
        self.assertTrue(all(g.retirement_year >= 2019 for g in early))
        for g in mystic:
            self.assertEqual(g.fuel_type, "gas_cc")
            self.assertEqual(g.plant_group, "CC_REGULAR")
            self.assertEqual(g.zone, "Boston")  # NEMA, not a fallback zone
            self.assertEqual(g.retirement_year, 2024)
            self.assertIn(g.retirement_month, (4, 5, 6))
            self.assertLess(g.online_year, 2023)
            self.assertGreater(g.pmax_mw, 0.0)
        self.assertGreater(
            sum(g.pmax_mw for g in mystic),
            1_000.0,
            "Mystic CC is ~1.4 GW",
        )

    def test_retiree_absent_from_operable_snapshot(self):
        # The whole point: Mystic is gone from the single recent operable
        # vintage, so it is sourced only from the retiree parquet.
        operable = load_fleet_from_csv("NEISO")
        self.assertFalse(any(int(g.plant_code) == 1588 for g in operable))

    def test_unknown_data_dir_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_retired_within_window("NEISO", data_dir=tmp), [])


class TestCoalTranches(unittest.TestCase):
    """Fuel-fraction discounting of coal take-or-pay tranche marginal cost.

    The legacy non-CAMPD tranche SPLIT (``split_coal_tranches`` and the six
    ``coal_tranche_*`` scalars) was deleted 2026-08-12 (rule 26 [R-DELETE],
    ercot-188 G#3 owner ruling) — the split tests went with it. What remains
    under test is :func:`apply_coal_tranches`'s partial-passthrough arithmetic
    on an explicit per-generator ``fuel_fracs`` vector, the CAMPD-path
    contract (:func:`campd_tranche_fuel_frac` produces the fractions).
    """

    def _tranche_fleet(self) -> list[Generator]:
        coal_kwargs = dict(
            name="COAL",
            zone="z",
            fuel_type="coal",
            pmin_mw=0.0,
            heat_rate=10.0,
            vom=4.5,
            emission_rate_co2=1.0,
            eford=0.08,
        )
        return [
            Generator(unit_id="COAL_t1", pmax_mw=300.0, **coal_kwargs),
            Generator(unit_id="COAL_t2", pmax_mw=250.0, **coal_kwargs),
            Generator(unit_id="COAL_t3", pmax_mw=450.0, **coal_kwargs),
            Generator(
                unit_id="CC",
                name="CC",
                zone="z",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                heat_rate=7.0,
                vom=2.0,
                eford=0.05,
            ),
        ]

    def test_apply_coal_tranches_discounts_only_fuel(self):
        # T1 bids at VOM only; T2 keeps 35% of its fuel cost; T3 unchanged.
        # Fuel cost = heat_rate (10) x fuel_price (2) = 20 $/MWh.
        # Coal MC before tranching = fuel 20 + VOM 4.5 + carbon 30 = 54.5.
        fleet = self._tranche_fleet()
        fuel_fracs = [0.0, 0.35, 1.0, 1.0]
        arrays = generators_to_fleet_arrays(fleet, ["z"], hours=4)
        fuel_prices = np.array([np.full(4, 2.0)] * len(fleet))
        mc = np.array(
            [
                np.full(4, 54.5),  # COAL_t1
                np.full(4, 54.5),  # COAL_t2
                np.full(4, 54.5),  # COAL_t3
                np.full(4, 25.0),  # CC
            ]
        )

        apply_coal_tranches(mc, fleet, arrays, fuel_fracs, fuel_prices)

        # T1: full 20 fuel removed -> 34.5 (VOM + carbon survive).
        np.testing.assert_allclose(mc[0], 34.5)
        # T2: 65% of the 20 fuel removed (13) -> 41.5.
        np.testing.assert_allclose(mc[1], 41.5)
        # T3: unchanged. CC: unchanged.
        np.testing.assert_allclose(mc[2], 54.5)
        np.testing.assert_allclose(mc[3], 25.0)


class TestOilBiomassFuelTypes(unittest.TestCase):
    """Registration, classification, MC and emissions for oil and biomass."""

    def test_fuel_codes_and_names(self):
        # Oil takes the previously-reserved code 11; biomass the next free
        # integer after gas_st (14). FUEL_TYPE_NAMES is sized to the max code
        # and round-trips both names.
        self.assertEqual(FUEL_TYPE_MAP["oil"], 11)
        self.assertEqual(FUEL_TYPE_MAP["biomass"], 15)
        self.assertEqual(len(FUEL_TYPE_NAMES), max(FUEL_TYPE_MAP.values()) + 1)
        self.assertEqual(FUEL_TYPE_NAMES[11], "oil")
        self.assertEqual(FUEL_TYPE_NAMES[15], "biomass")

    def test_eia_classifier_maps_oil_sources(self):
        # Distillate, residual and petroleum coke classify as oil.
        for src in ("DFO", "RFO", "PC"):
            self.assertEqual(
                _map_fuel_type("Petroleum Liquids", src, "GT"),
                "oil",
                f"{src} should classify as oil",
            )

    def test_eia_classifier_maps_biomass_sources(self):
        # Wood solids, ag byproducts, municipal solid waste and landfill gas
        # all classify as biomass.
        for src in ("WDS", "AB", "MSW", "LFG"):
            self.assertEqual(
                _map_fuel_type("Wood/Wood Waste Biomass", src, "ST"),
                "biomass",
                f"{src} should classify as biomass",
            )

    def test_oil_and_biomass_are_aggregatable(self):
        # Both are thermal blocks that aggregate; this also makes ERCOT's
        # CAMPD path exclude them from the EIA non-aggregatable carve-out.
        self.assertIn("oil", _AGGREGATABLE_FUELS)
        self.assertIn("biomass", _AGGREGATABLE_FUELS)

    def test_oil_marginal_cost_and_emissions(self):
        # Oil burns at a high heat rate and emits CO2, so a carbon price lifts
        # its MC. MC = heat_rate*fuel + vom + emission_rate*carbon.
        gen = Generator(
            unit_id="OIL",
            name="Oil",
            zone="z",
            fuel_type="oil",
            pmax_mw=100.0,
            heat_rate=13.5,
            vom=4.5,
            emission_rate_co2=1.0,
            nox_rate=0.0004,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=2)
        fuel_prices = np.full((1, 2), 18.0)
        mc = assemble_mc(fleet, fuel_prices, carbon_price=50.0)
        np.testing.assert_allclose(mc[0], 13.5 * 18.0 + 4.5 + 1.0 * 50.0)
        # Carbon price moves oil MC (it emits).
        base = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        np.testing.assert_allclose(mc[0] - base[0], 50.0)

    def test_biomass_marginal_cost_and_carbon_neutral(self):
        # Biomass burns cheap fuel; its biogenic CO2 is carbon-neutral, so a
        # carbon price leaves its MC unchanged.
        gen = Generator(
            unit_id="BIO",
            name="Biomass",
            zone="z",
            fuel_type="biomass",
            pmax_mw=100.0,
            heat_rate=13.5,
            vom=5.0,
            emission_rate_co2=0.0,
            nox_rate=0.001,
        )
        fleet = generators_to_fleet_arrays([gen], ["z"], hours=2)
        fuel_prices = np.full((1, 2), 2.5)
        no_carbon = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        with_carbon = assemble_mc(fleet, fuel_prices, carbon_price=100.0)
        np.testing.assert_allclose(no_carbon[0], 13.5 * 2.5 + 5.0)
        np.testing.assert_allclose(with_carbon[0], no_carbon[0])

    def test_oil_is_more_expensive_than_gas_cc(self):
        # An oil unit's MC sits well above a gas CC's, putting it at the
        # peaking end of the merit order.
        oil = Generator(
            unit_id="OIL",
            name="Oil",
            zone="z",
            fuel_type="oil",
            pmax_mw=100.0,
            heat_rate=13.5,
            vom=4.5,
            emission_rate_co2=1.0,
        )
        cc = Generator(
            unit_id="CC",
            name="CC",
            zone="z",
            fuel_type="gas_cc",
            pmax_mw=100.0,
            heat_rate=7.0,
            vom=2.0,
        )
        fleet = generators_to_fleet_arrays([oil, cc], ["z"], hours=1)
        fuel_prices = np.array([[18.0], [3.0]])
        mc = assemble_mc(fleet, fuel_prices, carbon_price=0.0)
        self.assertGreater(mc[0, 0], mc[1, 0])


if __name__ == "__main__":
    unittest.main()


class TestDualFuelPlantGroups(unittest.TestCase):
    """EIA-860 multifuel dual-fuel capability lookup (doc 03 Pack G)."""

    def test_real_multifuel_extract(self):
        """The committed EIA-860 multifuel parquet yields gas-class keys."""
        from market_sim.config.paths import EIA_860_DIR
        from market_sim.data.fleet import (
            _EIA860_GAS_GROUPS,
            EIA_860_MULTIFUEL_PARQUET_NAME,
            dual_fuel_plant_groups,
        )

        if not (EIA_860_DIR / EIA_860_MULTIFUEL_PARQUET_NAME).exists():
            self.skipTest("EIA-860 multifuel parquet not present")
        pairs = dual_fuel_plant_groups()
        self.assertGreater(len(pairs), 0)
        for plant_code, group in pairs:
            self.assertIsInstance(plant_code, int)
            self.assertGreater(plant_code, 0)
            # Gas-primary switchers only — they class into the gas groups.
            self.assertIn(group, _EIA860_GAS_GROUPS)

    def test_missing_parquet_returns_empty(self):
        """A directory without the multifuel extract flags nothing."""
        from market_sim.data.fleet import dual_fuel_plant_groups

        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(dual_fuel_plant_groups(Path(tmp)), frozenset())


class TestLoadPlannedAdditionsNonThermal(unittest.TestCase):
    """An ISO whose proposed pipeline is all non-thermal returns empty.

    CAISO's proposed schedule is dominated by solar/batteries, which the
    fuel mapper deliberately skips -- the loader must return [] rather
    than crash on the empty post-mapping list.
    """

    def test_caiso_all_nonthermal_pipeline(self):
        gens = load_planned_additions("CAISO")
        self.assertIsInstance(gens, list)
        for g in gens:
            self.assertNotIn(g.fuel_type, {"wind", "solar"})


class TestCcCapacityReconcile(unittest.TestCase):
    """``cc_capacity_reconcile`` raises listed CC capacities, raise-only.

    The reconciliation table lifts an understated CC's LP capacity to its
    demonstrated CAMPD peak; it must never lower a plant, and a missing
    table must be a no-op so an enabled flag with no artifact is safe.
    """

    _BINS = ScenarioConfig().campd_bins_path
    _RECON = str(PROCESSED_DIR / "cc_capacity_reconcile_ERCOT.csv")

    def test_raises_listed_plants_only(self):
        from market_sim.data.fleet import load_campd_bins

        off = load_campd_bins(self._BINS).set_index("Plant_Code")["capacity_mw"]
        on = load_campd_bins(self._BINS, capacity_reconcile_path=self._RECON).set_index(
            "Plant_Code"
        )["capacity_mw"]
        table = pd.read_csv(self._RECON)
        listed = set(table["plant_code"].astype(int))
        # Every plant absent from the table is byte-identical.
        for code in off.index:
            if int(code) not in listed:
                self.assertAlmostEqual(off[code], on[code], places=3)
        # Freestone (55226) is raised to its reconciled value; never lowered.
        self.assertGreater(on[55226], off[55226])
        self.assertTrue((on >= off - 1e-6).all())

    def test_missing_table_is_noop(self):
        from market_sim.data.fleet import load_campd_bins

        off = load_campd_bins(self._BINS)["capacity_mw"].to_numpy()
        on = load_campd_bins(
            self._BINS, capacity_reconcile_path="/nonexistent/recon.csv"
        )["capacity_mw"].to_numpy()
        self.assertTrue(np.allclose(off, on))


class TestCcCapacityReconcilePathIsoScope(unittest.TestCase):
    """``cc_capacity_reconcile_path`` resolves per-ISO — rule 25 ``[R-ISO-SCOPE]``.

    The field defaults to ``None`` and is resolved in
    ``ScenarioConfig.__post_init__`` to ``cc_capacity_reconcile_<ISO>.csv``. That
    default is load-bearing: a shared or ERCOT-shaped default would feed one
    ISO's demonstrated peaks to any other ISO that flipped the boolean without
    overriding the path, which is exactly the cross-ISO leak rule 25 closes.

    Asserted rather than merely observed (caiso-185 P0-4 / BE-2; the caiso-184
    ``G-CONSIST`` discipline — a scope property that only a probe checks is a
    property nothing defends).
    """

    _ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP", "SOCO")

    def test_each_iso_resolves_to_its_own_table(self):
        from market_sim.config.paths import cc_capacity_reconcile_path

        for iso in self._ISOS:
            with self.subTest(iso=iso):
                resolved = Path(ScenarioConfig(iso=iso).cc_capacity_reconcile_path)
                self.assertEqual(resolved, cc_capacity_reconcile_path(iso))
                self.assertIn(iso, resolved.name)

    def test_paths_are_pairwise_distinct(self):
        paths = {
            ScenarioConfig(iso=iso).cc_capacity_reconcile_path for iso in self._ISOS
        }
        self.assertEqual(len(paths), len(self._ISOS))

    def test_arming_one_iso_does_not_move_another(self):
        armed = ScenarioConfig(iso="CAISO", cc_capacity_reconcile=True)
        self.assertIn("CAISO", Path(armed.cc_capacity_reconcile_path).name)
        for iso in self._ISOS:
            if iso == "CAISO":
                continue
            with self.subTest(iso=iso):
                self.assertIn(
                    iso, Path(ScenarioConfig(iso=iso).cc_capacity_reconcile_path).name
                )

    def test_explicit_path_still_wins(self):
        cfg = ScenarioConfig(iso="CAISO", cc_capacity_reconcile_path="/tmp/custom.csv")
        self.assertEqual(cfg.cc_capacity_reconcile_path, "/tmp/custom.csv")


class TestCcSummerCapacityGuard(unittest.TestCase):
    """``_reconcile_cc_pmax_to_nameplate`` clamps double-filed CC summer rows.

    EIA-860 sometimes files a CC block's total summer capability on one
    generator row (with the component rows left blank, so the loader
    nameplate-fills them) or on both the component and total rows. Either way
    the fleet-loaded merchant-CC pmax sum ends up above the plant's nameplate
    sum — physically impossible per the EIA-860 schema. The guard reconciles
    the plant to its trusted bound ``max(nameplate_sum, demonstrated_peak)`` —
    nameplate for a plant with no CAMPD peak in its reconcile table, but the
    demonstrated CAMPD peak where that peak sits *above* nameplate (a real
    cold-weather over-rating the guard must never discard — rule 13).
    """

    def _cc_row(self, gid, prime_mover, net_summer, nameplate):
        """One normalized EIA-860 CC generator row (dict) for the loader."""
        return {
            "plant_id": 999001,
            "generator_id": gid,
            "plant_name": "Synthetic CC",
            "technology": "Natural Gas Fired Combined Cycle",
            "energy_source": "NG",
            "prime_mover": prime_mover,
            "chp": "N",
            "status": "OP",
            "state": "PA",
            "net_summer_capacity_mw": net_summer,
            "nameplate_capacity_mw": nameplate,
            "operating_year": 2015,
            "operating_month": 1,
            "planned_retirement_year": None,
            "planned_retirement_month": None,
            "heat_rate": 7.0,
        }

    def _fleet(self, rows):
        from market_sim.data.fleet import _rows_to_generators

        return _rows_to_generators(pd.DataFrame(rows), "PJM", get_iso_config("PJM"))

    def test_total_on_one_row_clamped_to_nameplate(self):
        # 2x1 block: the two CTs carry no summer figure (loader nameplate-fills
        # 150 each), the steam row carries the whole 450 MW block total. Fleet
        # pmax sum = 150 + 150 + 450 = 750; nameplate sum = 400. The guard must
        # clamp the plant's CC pmax sum to 400 (scaling each row by 400/750).
        gens = self._fleet(
            [
                self._cc_row("CT1", "CT", float("nan"), 150.0),
                self._cc_row("CT2", "CT", float("nan"), 150.0),
                self._cc_row("STG", "CA", 450.0, 100.0),
            ]
        )
        cc = [g for g in gens if g.plant_group == "CC_REGULAR"]
        self.assertEqual(len(cc), 3)
        self.assertAlmostEqual(sum(g.pmax_mw for g in cc), 400.0, places=3)
        # Reconciliation is proportional (offer-curve shape preserved).
        by_gid = {g.unit_id.split("_")[1]: g.pmax_mw for g in cc}
        self.assertAlmostEqual(by_gid["STG"], 450.0 * 400.0 / 750.0, places=3)
        self.assertAlmostEqual(by_gid["CT1"], 150.0 * 400.0 / 750.0, places=3)

    def test_double_filed_component_and_total_clamped(self):
        # Both the CT and its paired CA carry the block total (the New Covert
        # 55297 pattern): pmax sum 360 + 360 = 720, nameplate sum 245 + 147.
        gens = self._fleet(
            [
                self._cc_row("1", "CT", 360.0, 245.0),
                self._cc_row("1A", "CA", 360.0, 147.0),
            ]
        )
        cc = [g for g in gens if g.plant_group == "CC_REGULAR"]
        self.assertAlmostEqual(sum(g.pmax_mw for g in cc), 392.0, places=3)

    def test_clean_plant_untouched(self):
        # A well-behaved block (each row's summer <= its nameplate) is a no-op.
        gens = self._fleet(
            [
                self._cc_row("CT1", "CT", 180.0, 200.0),
                self._cc_row("STG", "CA", 90.0, 100.0),
            ]
        )
        cc = [g for g in gens if g.plant_group == "CC_REGULAR"]
        self.assertAlmostEqual(sum(g.pmax_mw for g in cc), 270.0, places=3)

    def test_within_tolerance_untouched(self):
        # A 0.05% overage (rounding noise) stays below the 0.1% guard band.
        gens = self._fleet(
            [
                self._cc_row("CT1", "CT", 200.1, 200.0),
                self._cc_row("STG", "CA", 100.0, 100.0),
            ]
        )
        cc = [g for g in gens if g.plant_group == "CC_REGULAR"]
        self.assertAlmostEqual(sum(g.pmax_mw for g in cc), 300.1, places=3)

    def test_demonstrated_peak_above_nameplate_wins(self):
        # A double-filed block whose measured CAMPD peak sits ABOVE nameplate:
        # pmax sum 360 + 360 = 720, nameplate sum 245 + 147 = 392, demonstrated
        # peak 410. The guard must clamp to max(nameplate, peak) = 410 — never
        # to nameplate 392, which would discard 18 MW of measured capability
        # (the New Covert 55297 rule-13 inversion). Peak from the reconcile
        # table, so it is mocked here.
        import unittest.mock as _m

        from market_sim.data import fleet as _F

        _F._cc_demonstrated_peaks.cache_clear()
        with _m.patch.object(
            _F, "_cc_demonstrated_peaks", return_value={999001: 410.0}
        ):
            gens = self._fleet(
                [
                    self._cc_row("1", "CT", 360.0, 245.0),
                    self._cc_row("1A", "CA", 360.0, 147.0),
                ]
            )
        cc = [g for g in gens if g.plant_group == "CC_REGULAR"]
        self.assertAlmostEqual(sum(g.pmax_mw for g in cc), 410.0, places=3)

    def test_demonstrated_peak_below_nameplate_ignored(self):
        # When the demonstrated peak sits BELOW nameplate (the plant never ran
        # to its rating, or is CT-only with an understated peak), the bound is
        # nameplate — the peak does not lower the guard target (a cap row, not
        # the guard, handles capping). pmax 720, nameplate 392, peak 300 ->
        # clamp to 392.
        import unittest.mock as _m

        from market_sim.data import fleet as _F

        _F._cc_demonstrated_peaks.cache_clear()
        with _m.patch.object(
            _F, "_cc_demonstrated_peaks", return_value={999001: 300.0}
        ):
            gens = self._fleet(
                [
                    self._cc_row("1", "CT", 360.0, 245.0),
                    self._cc_row("1A", "CA", 360.0, 147.0),
                ]
            )
        cc = [g for g in gens if g.plant_group == "CC_REGULAR"]
        self.assertAlmostEqual(sum(g.pmax_mw for g in cc), 392.0, places=3)


class TestNewCovertDemonstratedPeakPin(unittest.TestCase):
    """New Covert (55297) pins to its demonstrated CAMPD peak under the keeper.

    The rule-13 inversion the peak-aware guard fixes: New Covert's fleet-loaded
    pmax double-files to ~1586 MW, its EIA-860 nameplate sums to 1176 MW, and
    its measured CAMPD demonstrated peak is 1192.4 MW (recorded in the committed
    PJM reconcile table). The old nameplate-only guard clipped it to 1176,
    discarding 16 MW of measured capability; the peak-aware guard keeps it at
    1192.4. Integration test on the real PJM fleet — skipped if EIA-860 is
    absent.
    """

    def test_new_covert_pinned_to_demonstrated_peak(self):
        from market_sim.config.paths import (
            EIA_860_DIR,
            cc_capacity_reconcile_path,
        )
        from market_sim.data import fleet as _F

        if not (EIA_860_DIR / "eia860_generator_operable.parquet").exists():
            self.skipTest("EIA-860 fleet parquet not present")
        if not cc_capacity_reconcile_path("PJM").exists():
            self.skipTest("PJM reconcile table not present")

        _F._cc_demonstrated_peaks.cache_clear()
        gens = _F.load_fleet_from_csv("PJM", get_iso_config("PJM"), year=2025)

        cfg = ScenarioConfig(
            iso="PJM",
            mode="backcast",
            cc_nameplate_summer_derate=True,
            cc_capacity_reconcile=True,
        )
        bins = _F.fleet_to_bins(gens, "PJM", cfg)
        cap = dict(
            zip(
                bins["Plant_Code"].astype(int),
                bins["capacity_mw"].astype(float),
            )
        )
        self.assertAlmostEqual(cap[55297], 1192.4, places=1)
        # A CT-only plant (Allegheny 3-4-5, 55710) stays at its nameplate
        # (excluded from the reconcile — its CAMPD peak is understated).
        self.assertAlmostEqual(cap[55710], 556.0, places=1)


class TestOtherFossilScoring(unittest.TestCase):
    """The OTHER_FOSSIL scoring bucket for genuinely-mixed gas-thermal plants."""

    def _frame(self):
        return pd.DataFrame(
            {
                "plant_code": [6243, 6243, 298, 4195, 6243],
                "klass": ["CT_PEAKER", "ST_GAS", "COAL_PRB", "ST_GAS", "nuclear"],
                "mw": [1.0, 1.0, 1.0, 1.0, 1.0],
            }
        )

    def test_mixed_plants_rebucketed_both_classes(self):
        from unittest import mock

        from market_sim.data.fleet import apply_other_fossil_scoring

        with mock.patch(
            "market_sim.data.fleet.mixed_fossil_plants",
            return_value=frozenset({6243, 4195}),
        ):
            out = apply_other_fossil_scoring(self._frame(), 2023)
        klass = list(out["klass"])
        # Both of mixed plant 6243's gas-thermal rows -> OTHER_FOSSIL ...
        self.assertEqual(klass[0], "OTHER_FOSSIL")
        self.assertEqual(klass[1], "OTHER_FOSSIL")
        # ... 4195 too ...
        self.assertEqual(klass[3], "OTHER_FOSSIL")
        # ... but coal and the non-gas-thermal nuclear row are untouched.
        self.assertEqual(klass[2], "COAL_PRB")
        self.assertEqual(klass[4], "nuclear")

    def test_no_mixed_plants_is_noop(self):
        from unittest import mock

        from market_sim.data.fleet import apply_other_fossil_scoring

        df = self._frame()
        with mock.patch(
            "market_sim.data.fleet.mixed_fossil_plants",
            return_value=frozenset(),
        ):
            out = apply_other_fossil_scoring(df, 2023)
        self.assertEqual(list(out["klass"]), list(df["klass"]))

    def test_categorical_class_column_supported(self):
        from unittest import mock

        from market_sim.data.fleet import apply_other_fossil_scoring

        df = self._frame()
        df["klass"] = df["klass"].astype("category")
        with mock.patch(
            "market_sim.data.fleet.mixed_fossil_plants",
            return_value=frozenset({6243}),
        ):
            out = apply_other_fossil_scoring(df, 2023)
        self.assertEqual(out["klass"].iloc[0], "OTHER_FOSSIL")

    def test_real_eia923_flags_known_mixed_plant(self):
        # Integration: Dansby (6243) is a ~50/50 steam+GT plant in 2023.
        from market_sim.data.fleet import mixed_fossil_plants

        self.assertIn(6243, mixed_fossil_plants(2023))


class TestCaisoChpSteamCreditHr(unittest.TestCase):
    """CAISO CHP steam-credit heat-rate correction (CT_CHP + CC_CHP)."""

    def _gen(self, plant_code, group, hr):
        from market_sim.data.fleet import Generator

        return Generator(
            unit_id=f"u{plant_code}",
            name=f"p{plant_code}",
            zone="SP15",
            fuel_type="gas_ct",
            pmax_mw=200.0,
            pmin_mw=0.0,
            heat_rate=hr,
            plant_group=group,
            plant_code=plant_code,
        )

    def test_eor_plants_lifted_to_power_only_hr(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr
        from market_sim.data.fleet import CAISO_EOR_TOPPING_FACTOR

        gens = [
            self._gen(10496, "CT_CHP", 5.795),  # Kern River
            self._gen(50134, "CT_CHP", 5.987),  # Sycamore
            self._gen(52169, "CT_CHP", 5.090),  # Midway Sunset
        ]
        _correct_chp_steam_credit_hr(gens, "CAISO")
        self.assertAlmostEqual(gens[0].heat_rate, 5.795 * CAISO_EOR_TOPPING_FACTOR, 3)
        self.assertAlmostEqual(gens[1].heat_rate, 5.987 * CAISO_EOR_TOPPING_FACTOR, 3)
        self.assertAlmostEqual(gens[2].heat_rate, 5.090 * CAISO_EOR_TOPPING_FACTOR, 3)
        self.assertTrue(all(9.0 <= g.heat_rate <= 11.0 for g in gens))

    def test_all_ct_chp_below_threshold_corrected(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr
        from market_sim.data.fleet import CAISO_EOR_TOPPING_FACTOR

        g = self._gen(50170, "CT_CHP", 5.53)  # Berry Cogen (non-EOR)
        _correct_chp_steam_credit_hr([g], "CAISO")
        self.assertAlmostEqual(g.heat_rate, 5.53 * CAISO_EOR_TOPPING_FACTOR, 3)

    def test_ct_chp_above_threshold_untouched(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr

        g = self._gen(50495, "CT_CHP", 9.09)  # High Sierra — already realistic
        _correct_chp_steam_credit_hr([g], "CAISO")
        self.assertEqual(g.heat_rate, 9.09)

    def test_cc_chp_below_threshold_corrected(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr
        from market_sim.data.fleet import (
            CAISO_CHP_CC_STEAM_CREDIT_FACTOR,
            CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR,
        )

        g = self._gen(50216, "CC_CHP", 5.61)  # Watson
        _correct_chp_steam_credit_hr([g], "CAISO")
        expected = max(
            5.61 * CAISO_CHP_CC_STEAM_CREDIT_FACTOR, CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR
        )
        self.assertAlmostEqual(g.heat_rate, expected, 3)

    def test_cc_chp_above_threshold_untouched(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr

        g = self._gen(55217, "CC_CHP", 6.65)  # Los Medanos
        _correct_chp_steam_credit_hr([g], "CAISO")
        self.assertEqual(g.heat_rate, 6.65)

    def test_uncorrected_iso_is_noop(self):
        # ISOs outside CHP_STEAM_CREDIT_HR_CORRECTION_ISOS are untouched.
        from market_sim.data.chp import _correct_chp_steam_credit_hr

        g = self._gen(10496, "CT_CHP", 5.795)
        _correct_chp_steam_credit_hr([g], "ERCOT")
        self.assertEqual(g.heat_rate, 5.795)

    def test_pjm_chp_corrected(self):
        # PJM joined the correction set (2026-07-07); its steam-credited CHP
        # gets the same universal turbine-physics correction as CAISO.
        from market_sim.data.chp import _correct_chp_steam_credit_hr
        from market_sim.data.fleet import (
            CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR,
            CAISO_EOR_TOPPING_FACTOR,
        )

        ct = self._gen(999001, "CT_CHP", 6.04)  # PJM median CT_CHP HR
        cc = self._gen(999002, "CC_CHP", 4.50)  # PJM median CC_CHP HR
        _correct_chp_steam_credit_hr([ct, cc], "PJM")
        self.assertAlmostEqual(ct.heat_rate, 6.04 * CAISO_EOR_TOPPING_FACTOR, 3)
        self.assertTrue(9.0 <= ct.heat_rate <= 11.0)
        self.assertGreaterEqual(cc.heat_rate, CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR)

    def test_non_chp_group_untouched(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr

        g = self._gen(10496, "CC_REGULAR", 5.5)
        _correct_chp_steam_credit_hr([g], "CAISO")
        self.assertEqual(g.heat_rate, 5.5)

    def test_cc_chp_floor_prevents_undercorrection(self):
        from market_sim.data.chp import _correct_chp_steam_credit_hr
        from market_sim.data.fleet import CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR

        g = self._gen(52109, "CC_CHP", 5.14)  # Richmond — very low HR
        _correct_chp_steam_credit_hr([g], "CAISO")
        self.assertGreaterEqual(g.heat_rate, CAISO_CHP_CC_STEAM_CREDIT_HR_FLOOR)


class TestTemperatureDependentDerate(unittest.TestCase):
    """Tests for config.temp_dependent_derate (fleet.generators_to_fleet_arrays).

    The switch replaces the flat net-summer/_SUMMER_CLASS_DERATE treatment with a
    per-class temperature curve driven by measured hourly zone dry-bulb TMAX. We
    monkeypatch the weather loader so the test is deterministic and offline.
    """

    ZONE = "North"
    # July window used to isolate the temperature effect from the seasonal
    # WEFOR/POF split: same calendar month -> identical statistical availability,
    # so any difference between these two hours is purely the temperature curve.
    _JUL_SPIKE = 4400  # forced to 42 C
    _JUL_NORMAL = 4500  # left at the 30 C July baseline

    def _tmax_series(self, hours: int = 8760) -> np.ndarray:
        """Monthly dry-bulb baseline (deg C) with a mid-July heat spike."""
        monthly = np.array([2, 5, 11, 16, 24, 29, 30, 30, 25, 16, 8, 3], dtype=float)
        tmax = monthly[_hour_to_month_index(hours)]
        tmax[self._JUL_SPIKE : self._JUL_SPIKE + 24] = 42.0
        return tmax

    def _gen(self, unit_id: str, group: str, fuel: str) -> Generator:
        return Generator(
            unit_id=unit_id,
            name=unit_id,
            zone=self.ZONE,
            fuel_type=fuel,
            pmax_mw=400.0,
            heat_rate=8.0,
            eford=0.05,
            online_year=2015,
            plant_group=group,
            plant_code=90000 + hash(unit_id) % 1000,
        )

    def _run(self, temp_on: bool):
        gens = [
            self._gen("cc1", "CC_REGULAR", "gas_cc"),
            self._gen("ct1", "CT_PEAKER", "gas_ct"),
            self._gen("coal1", "COAL", "coal"),
        ]
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2023,
            iso="ERCOT",
            temp_dependent_derate=temp_on,
        )
        tmax = self._tmax_series()
        fake = lambda iso, year, hours, zone=None: (tmax, tmax)  # noqa: E731
        with unittest.mock.patch(
            "market_sim.data.eia_loader.iso_zone_tmax", side_effect=fake
        ):
            fa = generators_to_fleet_arrays(
                gens, [self.ZONE], iso="ERCOT", config=cfg, year=2023
            )
        return {g.unit_id: fa.availability[i] for i, g in enumerate(gens)}

    def test_off_has_no_temperature_signal(self):
        """Switch off: same-month hours are identical (no temperature curve)."""
        off = self._run(temp_on=False)
        for uid in ("cc1", "ct1", "coal1"):
            self.assertAlmostEqual(
                off[uid][self._JUL_SPIKE],
                off[uid][self._JUL_NORMAL],
                places=6,
                msg=f"{uid} should have no within-July temperature spread when off",
            )

    def test_gas_turbines_derated_on_heat_spike(self):
        """CC/CT lose capacity on the 42 C spike vs a 30 C July hour, CT steeper."""
        on = self._run(temp_on=True)
        for uid, lo, hi in (("cc1", 0.88, 0.95), ("ct1", 0.78, 0.90)):
            ratio = on[uid][self._JUL_SPIKE] / on[uid][self._JUL_NORMAL]
            self.assertTrue(
                lo < ratio < hi,
                f"{uid} spike/normal ratio {ratio:.3f} outside ({lo}, {hi})",
            )
        # Simple-cycle CT must derate more steeply than the CC (steam bottoming
        # cycle partly compensates the CC).
        self.assertLess(
            on["ct1"][self._JUL_SPIKE] / on["ct1"][self._JUL_NORMAL],
            on["cc1"][self._JUL_SPIKE] / on["cc1"][self._JUL_NORMAL],
        )

    def test_coal_gets_additive_hot_hour_derate(self):
        """Coal (no existing summer derate) picks up a hot-hour condenser derate."""
        off = self._run(temp_on=False)
        on = self._run(temp_on=True)
        # Off: flat within July. On: the spike hour is derated below the 30 C hour.
        self.assertLess(on["coal1"][self._JUL_SPIKE], on["coal1"][self._JUL_NORMAL])
        self.assertGreater(
            on["coal1"][self._JUL_SPIKE] / on["coal1"][self._JUL_NORMAL], 0.90
        )
        # The additive derate is a net reduction relative to off at the spike.
        self.assertLess(on["coal1"][self._JUL_SPIKE], off["coal1"][self._JUL_SPIKE])

    def test_cc_ct_capacity_neutral_on_summer_mean(self):
        """CC/CT summer mean is reshaped, not lowered wholesale (rules 1, 9)."""
        off = self._run(temp_on=False)
        on = self._run(temp_on=True)
        summer = np.isin(_hour_to_month_index(8760), [5, 6, 7, 8])
        for uid in ("cc1", "ct1"):
            ratio = on[uid][summer].mean() / off[uid][summer].mean()
            # Clipping at 1.0 makes the on-mean slightly below the off-mean, but
            # it must stay close (neutral reshape) and never rise above it.
            self.assertTrue(
                0.85 <= ratio <= 1.02,
                f"{uid} summer-mean on/off ratio {ratio:.3f} not capacity-neutral",
            )


class TestCoalNameplateSummerDerate(unittest.TestCase):
    """EIA-860 net-summer capacity derate for coal (coal_nameplate_summer_derate)."""

    ZONE = "ERCOT_S"

    def test_ratio_from_eia860(self):
        """net_summer/nameplate per plant, clamped to (0, 1]; None when absent."""
        # Oak Grove (6180) and Major Oak (7030) are derated; Martin Lake (6146)
        # is rated at/above nameplate -> clamps to 1.0. 99999 is not a coal plant.
        self.assertAlmostEqual(coal_summer_derate_ratio(6180), 0.952, places=2)
        self.assertAlmostEqual(coal_summer_derate_ratio(7030), 0.873, places=2)
        self.assertEqual(coal_summer_derate_ratio(6146), 1.0)
        self.assertIsNone(coal_summer_derate_ratio(99999))

    def _avail(self, plant_code: int, flag: bool) -> np.ndarray:
        gen = Generator(
            unit_id="coal1",
            name="coal1",
            zone=self.ZONE,
            fuel_type="coal",
            pmax_mw=1000.0,
            heat_rate=10.0,
            eford=0.05,
            online_year=2010,
            plant_group="COAL",
            plant_code=plant_code,
        )
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2023,
            iso="ERCOT",
            coal_nameplate_summer_derate=flag,
        )
        fa = generators_to_fleet_arrays(
            [gen], [self.ZONE], iso="ERCOT", config=cfg, year=2023
        )
        return fa.availability[0]

    def test_summer_derate_applies_only_in_summer(self):
        """Flag on: summer availability drops by net_summer/nameplate; winter unchanged."""
        summer = np.isin(_hour_to_month_index(8760), [5, 6, 7, 8])  # Jun-Sep
        off = self._avail(6180, flag=False)  # Oak Grove, ratio ~0.952
        on = self._avail(6180, flag=True)
        ratio = on[summer].mean() / off[summer].mean()
        self.assertTrue(
            0.94 <= ratio <= 0.97, f"summer on/off ratio {ratio:.3f} not net-summer"
        )
        np.testing.assert_allclose(on[~summer], off[~summer], rtol=1e-6)
        self.assertTrue(np.all(on <= off + 1e-9))

    def test_no_derate_for_at_or_above_nameplate_plant(self):
        """A plant rated at/above nameplate (ratio clamps to 1.0) is unchanged."""
        off = self._avail(6146, flag=False)  # Martin Lake, ratio 1.0
        on = self._avail(6146, flag=True)
        np.testing.assert_allclose(on, off, rtol=1e-6)


class TestCcNameplateRescaleHeatRate(unittest.TestCase):
    """The CC nameplate rescale must not deflate the plant heat rate.

    ``fleet_to_bins`` accumulates the capacity-weighted heat rate on the
    fleet's net-summer ratings; under ``cc_nameplate_summer_derate`` the
    plant's capacity is rescaled up to full nameplate. Heat rate is an
    intensive property — dividing the net-summer-weighted sum by the rescaled
    capacity deflated every CC plant's base heat rate (and every offer band
    built on it) by its own net-summer/nameplate ratio, scrambling the
    within-class merit order (FINDING-caiso78-cc-hr-basis-2026-07-12.md §3).
    """

    def _bins(self, flag: bool):
        from market_sim.data.fleet import fleet_to_bins

        gen = Generator(
            unit_id="999901_1",
            name="Test CC",
            zone="NP15",
            fuel_type="gas_cc",
            pmax_mw=80.0,  # net-summer rating (the fleet-carried pmax)
            heat_rate=8.0,
            plant_group="CC_REGULAR",
            plant_code=999901,
        )
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2023,
            iso="CAISO",
            cc_nameplate_summer_derate=flag,
        )
        with unittest.mock.patch(
            "market_sim.data.fleet.cc_summer_derate_ratio", return_value=0.8
        ):
            return fleet_to_bins([gen], "CAISO", cfg)

    def test_rescale_inflates_capacity_but_preserves_heat_rate(self):
        """Flag on: capacity 80 -> 100 (nameplate); base HR stays 8.0."""
        row = self._bins(flag=True).iloc[0]
        self.assertAlmostEqual(float(row["capacity_mw"]), 100.0, places=6)
        self.assertAlmostEqual(float(row["hr_weighted"]), 8.0, places=6)
        # every band multiplies the (undeflated) base heat rate
        self.assertAlmostEqual(
            float(row["hr_econ"]) / 8.0,
            float(row["hr_econ"]) / row["hr_weighted"],
            places=9,
        )

    def test_flag_off_unchanged(self):
        """Flag off: net-summer capacity and the same base heat rate."""
        row = self._bins(flag=False).iloc[0]
        self.assertAlmostEqual(float(row["capacity_mw"]), 80.0, places=6)
        self.assertAlmostEqual(float(row["hr_weighted"]), 8.0, places=6)


class TestStGasP25LevelFloor(unittest.TestCase):
    """ST_GAS p25-LEVEL commitment floor (``st_gas_mustrun_p25_level``, miso-67).

    Restores the phase-B unit coverage (the original tests were container-local
    and lost): gate-on-both-flags, cheapest-first tranche distribution, the
    pmax x availability clip (never pins), and the rule-19 level REPLACE of the
    committed-tranche floor. The measured artifact lookups are monkeypatched so
    the tests exercise the application block, not the CSV.
    """

    _HOURS = 48
    _PLANT = 9901

    def _gens(self, n_tranches=2, cc_pmin=0.0, cc_frac=0.0):
        # Two tranches of one ST_GAS plant, heat rates 7 (cheap) and 9.
        return [
            Generator(
                unit_id=f"stg_{i}",
                name=f"Steamer T{i}",
                zone="North",
                fuel_type="gas_st",
                pmax_mw=60.0,
                heat_rate=7.0 + 2.0 * i,
                plant_group="ST_GAS",
                plant_code=self._PLANT,
                cc_mustrun_pmin_mw=cc_pmin,
                cc_mustrun_online_frac=cc_frac,
            )
            for i in range(n_tranches)
        ]

    def _fa(self, gens, p25_on=True, per_plant_on=True, level=100.0, frac=0.5):
        cfg = ScenarioConfig(
            # Measured per-plant ST_GAS operating levels are a backcast-only
            # overlay (FFR-1D rule-13 guard, audit FR-11).
            mode="backcast",
            weather_year=2024,
            st_gas_mustrun_per_plant=per_plant_on,
            st_gas_mustrun_p25_level=p25_on,
        )
        # Ascending load: the top-``frac`` window is the LAST k hours.
        load = np.arange(self._HOURS, dtype=float) + 1.0
        with (
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_level",
                return_value={(self._PLANT, "ST_GAS"): level},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac",
                return_value={(self._PLANT, "ST_GAS"): frac},
            ),
        ):
            return generators_to_fleet_arrays(
                gens,
                ["North"],
                hours=self._HOURS,
                iso="MISO",
                config=cfg,
                load_shape=load,
            )

    def test_gate_requires_both_flags(self):
        # p25 armed WITHOUT st_gas_mustrun_per_plant: no floor is placed (the
        # level swap modifies the existing phenomenon, it never arms one).
        fa = self._fa(self._gens(), p25_on=True, per_plant_on=False)
        if fa.min_gen is not None:
            self.assertEqual(float(fa.min_gen.sum()), 0.0)

    def test_level_window_and_cheapest_first(self):
        # Level 100 in the top-24 (of 48) load hours: the cheap tranche (hr 7)
        # carries its full 60 MW, the expensive one (hr 9) the 40 MW remainder;
        # off-window hours carry no floor; raised cells stamp the SAME
        # mechanism id as the committed floor (rule 19 — no new mechanism).
        fa = self._fa(self._gens())
        window = np.arange(self._HOURS - 24, self._HOURS)  # top-load hours
        off = np.arange(0, self._HOURS - 24)
        cap0 = fa.pmax[0] * fa.availability[0, window]
        cap1 = fa.pmax[1] * fa.availability[1, window]
        # Cheap tranche carries its full available capacity, the expensive one
        # the remainder of the 100 MW level (both below cap1 here).
        np.testing.assert_allclose(fa.min_gen[0, window], cap0)
        np.testing.assert_allclose(fa.min_gen[1, window], 100.0 - cap0)
        self.assertTrue((100.0 - cap0 <= cap1 + 1e-9).all())
        np.testing.assert_allclose(fa.min_gen[:, off], 0.0)
        self.assertTrue(
            (fa.min_gen_mechanism[0, window] == MECH_ST_GAS_MUSTRUN_PER_PLANT).all()
        )

    def test_clip_to_pmax_availability_never_pins(self):
        # The per-tranche floor is capped at pmax x availability each hour, so
        # an outage hour relaxes it and the floor can never pin a tranche.
        fa = self._fa(self._gens())
        cap = fa.pmax[:, None] * fa.availability
        self.assertTrue((fa.min_gen <= cap + 1e-9).all())

    def test_level_replaces_committed_floor(self):
        # A gate-armed plant carrying the committed-tranche floor
        # (cc_mustrun_pmin_mw) is handed off to the p25 block when the level
        # swap is armed: the floor is the p25 distribution, NOT the committed
        # pmin (rule 19 — replaced, never stacked).
        gens = self._gens(cc_pmin=50.0, cc_frac=0.5)
        fa_p25 = self._fa(gens, p25_on=True)
        fa_lsl = self._fa(gens, p25_on=False)
        window = np.arange(self._HOURS - 24, self._HOURS)
        # p25 on: cheapest-first split of the 100 MW level (cheap tranche at
        # its available cap, expensive at the remainder) — NOT the 50 MW pmin.
        cap0 = fa_p25.pmax[0] * fa_p25.availability[0, window]
        np.testing.assert_allclose(fa_p25.min_gen[0, window], cap0)
        np.testing.assert_allclose(fa_p25.min_gen[1, window], 100.0 - cap0)
        # p25 off: the committed floor (50 MW per tranche) is unchanged.
        np.testing.assert_allclose(fa_lsl.min_gen[0, window], 50.0)
        np.testing.assert_allclose(fa_lsl.min_gen[1, window], 50.0)


class TestCoalSyncOnlineFracPerYear(unittest.TestCase):
    """Per-YEAR COAL synchronization window (``coal_sync_online_frac_per_year``).

    pjm-h15 — the coal sibling of :class:`TestMustrunOnlineFracPerYear`, on its
    own gate because coal is its own mechanism id (``MECH_COAL_MUSTRUN``) with
    its own D-4 conduct evidence (rule 19 ``[R-ONE-MECH]``). PJM's committed
    ``thermal_tranches_PJM.csv`` is derived on 2023-2025 and its pooled
    ``online_frac`` is applied as EVERY solve year's window: plant 50888 reads
    pooled 0.684 against an own-year 0.013 in 2020 — floored in 68 % of a year
    whose own meter says it synchronized in 1.3 % of it (rule 17
    ``[R-FLOOR-WINDOW]``).

    Same four properties as the gas sibling: default-off byte-inertness, the
    per-year window sizing the floor, the backcast-only mode gate (rule 13),
    and membership staying on the pooled artifact (an unmeasured plant-year
    keeps its pooled fraction, so the arm never removes a floor for want of a
    measurement).
    """

    _HOURS = 48
    _PLANT = 9903

    def _gens(self):
        g = Generator(
            unit_id="coal_0",
            name="Cycler",
            zone="North",
            fuel_type="coal",
            pmax_mw=300.0,
            heat_rate=10.0,
            plant_group="COAL",
            plant_code=self._PLANT,
        )
        g.coal_sync_pmin_mw = 100.0
        g.coal_sync_online_frac = 0.5
        return [g]

    def _fa(self, *, per_year=False, mode="backcast", by_year=None):
        cfg = ScenarioConfig(
            mode=mode,
            weather_year=2024,
            coal_sync_online_frac_per_year=per_year,
        )
        load = np.arange(self._HOURS, dtype=float) + 1.0  # top-frac == last k h
        with unittest.mock.patch(
            "market_sim.data.fleet.thermal_tranche_online_frac_by_year",
            return_value=(
                by_year if by_year is not None else {(self._PLANT, "COAL", 2024): 0.25}
            ),
        ):
            return generators_to_fleet_arrays(
                self._gens(),
                ["North"],
                hours=self._HOURS,
                iso="PJM",
                config=cfg,
                load_shape=load,
            )

    def test_default_off_is_byte_inert(self):
        """Flag off: the pooled window sizes the floor, unchanged."""
        fa = self._fa(per_year=False)
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 24)  # 0.5 x 48 h

    def test_per_year_window_sizes_the_floor(self):
        """Armed: the SOLVE YEAR's own fraction sizes the window."""
        fa = self._fa(per_year=True)
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 12)  # 0.25 x 48 h
        np.testing.assert_allclose(fa.min_gen[0, :36], 0.0)  # top-load hours

    def test_unmeasured_plant_year_keeps_the_pooled_fraction(self):
        """No own-year row: the floor is untouched (never removed for want of
        a measurement)."""
        fa = self._fa(per_year=True, by_year={})
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 24)

    def test_measured_dark_year_carries_no_floor(self):
        """An own-year fraction of ZERO means the meter says the plant never
        synchronized — the one deliberate membership consequence."""
        fa = self._fa(per_year=True, by_year={(self._PLANT, "COAL", 2024): 0.0})
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 0)

    def test_gas_rows_never_reach_the_coal_seam(self):
        """The gather filters on group: a same-coded ST_GAS row is ignored."""
        fa = self._fa(per_year=True, by_year={(self._PLANT, "ST_GAS", 2024): 0.25})
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 24)  # pooled kept

    def test_backcast_only_mode_gate(self):
        """Forecast mode keeps the pooled window (rule 13 — no same-year meter).

        The ScenarioConfig guard refuses the flag outright in forecast mode, so
        the engine gate is only reachable when a caller bypasses construction;
        assert both halves.
        """
        with self.assertRaises(ValueError):
            ScenarioConfig(
                mode="forecast", iso="PJM", coal_sync_online_frac_per_year=True
            )
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2024,
            coal_sync_online_frac_per_year=True,
        )
        cfg.mode = "forecast"  # post-construction: bypasses the config guard
        load = np.arange(self._HOURS, dtype=float) + 1.0
        with unittest.mock.patch(
            "market_sim.data.fleet.thermal_tranche_online_frac_by_year",
            return_value={(self._PLANT, "COAL", 2024): 0.25},
        ):
            fa = generators_to_fleet_arrays(
                self._gens(),
                ["North"],
                hours=self._HOURS,
                iso="PJM",
                config=cfg,
                load_shape=load,
            )
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 24)  # pooled window

    def test_cache_key_dropped_at_default_and_distinct_when_armed(self):
        """nyiso-119 discipline: the default key is unmoved, armed is distinct."""
        off = ScenarioConfig(iso="PJM", mode="backcast")
        on = ScenarioConfig(
            iso="PJM", mode="backcast", coal_sync_online_frac_per_year=True
        )
        self.assertNotEqual(off.cache_key(), on.cache_key())


class TestMustrunOnlineFracPerYear(unittest.TestCase):
    """Per-YEAR must-run commitment window (``mustrun_online_frac_per_year``).

    miso-172. The committed thermal-tranche artifact publishes ONE pooled
    ``online_frac`` per plant and the runtime applies it as a SINGLE solve
    year's commitment window, so a plant whose synchronization share moves
    across the derive window is over-committed in its light years (MISO 1402:
    pooled 0.508 vs per-year 0.251/0.615/0.658). These tests pin the four
    properties that make the correction safe: default-off byte-inertness,
    the per-year window actually sizing the floor, the backcast-only mode gate
    (rule 13), and membership staying on the pooled artifact.
    """

    _HOURS = 48
    _PLANT = 9902

    def _gens(self):
        return [
            Generator(
                unit_id="stg_0",
                name="Steamer",
                zone="North",
                fuel_type="gas_st",
                pmax_mw=200.0,
                heat_rate=7.0,
                plant_group="ST_GAS",
                plant_code=self._PLANT,
            )
        ]

    def _fa(self, *, per_year=False, mode="backcast", pooled=0.5, by_year=None):
        cfg = ScenarioConfig(
            mode=mode,
            weather_year=2024,
            st_gas_mustrun_per_plant=True,
            st_gas_mustrun_p25_level=True,
            mustrun_online_frac_per_year=per_year,
        )
        load = np.arange(self._HOURS, dtype=float) + 1.0  # top-frac == last k h
        with (
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_level",
                return_value={(self._PLANT, "ST_GAS"): 100.0},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac",
                return_value={(self._PLANT, "ST_GAS"): pooled},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac_by_year",
                return_value=(
                    by_year
                    if by_year is not None
                    else {(self._PLANT, "ST_GAS", 2024): 0.25}
                ),
            ),
        ):
            return generators_to_fleet_arrays(
                self._gens(),
                ["North"],
                hours=self._HOURS,
                iso="MISO",
                config=cfg,
                load_shape=load,
            )

    def test_default_off_is_byte_inert(self):
        """Flag off: the pooled window is used, unchanged."""
        fa = self._fa(per_year=False)
        floored = int((fa.min_gen[0] > 0).sum())
        self.assertEqual(floored, 24)  # pooled 0.5 x 48 h

    def test_per_year_window_sizes_the_floor(self):
        """Armed: the SOLVE YEAR's own fraction sizes the window, not the pool."""
        fa = self._fa(per_year=True)
        floored = int((fa.min_gen[0] > 0).sum())
        self.assertEqual(floored, 12)  # per-year 0.25 x 48 h
        # And it is the TOP-load hours that carry it.
        np.testing.assert_allclose(fa.min_gen[0, :36], 0.0)

    def test_backcast_only_mode_gate(self):
        """Forecast mode keeps the pooled window (rule 13 — no same-year meter).

        The ScenarioConfig guard refuses the flag outright in forecast mode, so
        the engine gate is only reachable when a caller bypasses construction;
        assert both halves.
        """
        with self.assertRaises(ValueError):
            ScenarioConfig(
                mode="forecast", iso="MISO", mustrun_online_frac_per_year=True
            )
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2024,
            st_gas_mustrun_per_plant=True,
            st_gas_mustrun_p25_level=True,
            mustrun_online_frac_per_year=True,
        )
        cfg.mode = "forecast"  # post-construction: bypasses the config guard
        load = np.arange(self._HOURS, dtype=float) + 1.0
        with (
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_level",
                return_value={(self._PLANT, "ST_GAS"): 100.0},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac",
                return_value={(self._PLANT, "ST_GAS"): 0.5},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac_by_year",
                return_value={(self._PLANT, "ST_GAS", 2024): 0.25},
            ),
        ):
            fa = generators_to_fleet_arrays(
                self._gens(),
                ["North"],
                hours=self._HOURS,
                iso="MISO",
                config=cfg,
                load_shape=load,
            )
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 24)  # pooled, not 12

    def test_membership_stays_on_the_pooled_artifact(self):
        """A plant absent from the pooled artifact acquires no floor.

        The per-year file must never ADD members — only re-size the window of
        plants the pooled artifact already qualifies (rule 19).
        """
        fa = self._fa(per_year=True, pooled=0.0)
        self.assertTrue(fa.min_gen is None or float(fa.min_gen.sum()) == 0.0)

    def test_zero_per_year_fraction_drops_the_floor_that_year(self):
        """A year the plant's own meter says it never synchronized carries none."""
        fa = self._fa(per_year=True, by_year={(self._PLANT, "ST_GAS", 2024): 0.0})
        self.assertTrue(fa.min_gen is None or float(fa.min_gen.sum()) == 0.0)


class TestMustrunLayupWindowMask(unittest.TestCase):
    """Measured lay-up window mask (``mustrun_layup_window_mask``).

    miso-173. The merit-order guard's economic-lay-up extract records the
    >= 5-day windows it removed from the availability envelope because the
    unit sat out of merit — the measured hours in which the plant's
    self-commitment driver is absent. The mask confines the per-plant
    must-run floor to hours OUTSIDE those windows (clip basis
    ``pmax x max(0, availability - layup_share)``) without touching
    availability itself. These tests pin default-off byte-inertness, the
    mask zeroing/clipping the floor inside windows, availability staying
    untouched, the backcast-only mode gate (rule 13), and the generic
    (non-p25) branch honouring the same mask.
    """

    _HOURS = 48
    _PLANT = 9904

    def _gens(self, **extra):
        return [
            Generator(
                unit_id="stg_0",
                name="Steamer",
                zone="North",
                fuel_type="gas_st",
                pmax_mw=200.0,
                heat_rate=7.0,
                plant_group="ST_GAS",
                plant_code=self._PLANT,
                **extra,
            )
        ]

    def _layup(self, share, lo, hi):
        arr = np.zeros(self._HOURS)
        arr[lo:hi] = share
        return {(self._PLANT, "ST_GAS"): arr}

    def _fa(self, *, masked=False, layup=None, mode="backcast", gens=None, p25=True):
        cfg = ScenarioConfig(
            mode=mode,
            weather_year=2024,
            st_gas_mustrun_per_plant=True,
            st_gas_mustrun_p25_level=p25,
            mustrun_layup_window_mask=masked,
        )
        load = np.arange(self._HOURS, dtype=float) + 1.0  # top-frac == last k h
        with (
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_level",
                return_value={(self._PLANT, "ST_GAS"): 100.0},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac",
                return_value={(self._PLANT, "ST_GAS"): 0.5},
            ),
            unittest.mock.patch(
                "market_sim.data.outages.unit_layup_removed_fractions",
                return_value=layup if layup is not None else {},
            ),
        ):
            return generators_to_fleet_arrays(
                gens if gens is not None else self._gens(),
                ["North"],
                hours=self._HOURS,
                iso="MISO",
                config=cfg,
                load_shape=load,
            )

    def test_default_off_is_byte_inert(self):
        """Flag off: the floor is unchanged even when windows exist on disk."""
        fa = self._fa(masked=False, layup=self._layup(1.0, 24, 48))
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 24)

    def test_masked_window_hours_lose_the_floor(self):
        """A full-share lay-up window zeroes the floor in exactly its hours."""
        # Window = top-half load hours = h24-47; lay-up covers h36-47.
        fa = self._fa(masked=True, layup=self._layup(1.0, 36, 48))
        np.testing.assert_allclose(fa.min_gen[0, 36:], 0.0)
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 12)  # h24-35 keep it

    def test_partial_share_clips_at_nonlaidup_capacity(self):
        """A partial lay-up clips the floor at pmax x (avail - share)."""
        # share 0.7 on a 200 MW plant: clip = pmax x (availability - 0.7),
        # computed against the run's own (statistical-base) availability.
        fa = self._fa(masked=True, layup=self._layup(0.7, 36, 48))
        expected = 200.0 * np.maximum(0.0, fa.availability[0, 36:] - 0.7)
        np.testing.assert_allclose(fa.min_gen[0, 36:], expected)
        self.assertTrue((fa.min_gen[0, 36:] < 100.0).all())
        np.testing.assert_allclose(fa.min_gen[0, 24:36], 100.0)

    def test_availability_is_not_touched(self):
        """The mask confines the FLOOR only; availability stays as loaded."""
        fa_off = self._fa(masked=False, layup=self._layup(1.0, 0, 48))
        fa_on = self._fa(masked=True, layup=self._layup(1.0, 0, 48))
        np.testing.assert_array_equal(fa_on.availability, fa_off.availability)
        self.assertTrue(float(fa_on.min_gen.sum()) == 0.0)

    def test_backcast_only_mode_gate(self):
        """Forecast mode refuses the flag at construction, and the engine
        gate independently no-ops when construction is bypassed."""
        with self.assertRaises(ValueError):
            ScenarioConfig(mode="forecast", iso="MISO", mustrun_layup_window_mask=True)
        fa = self._fa(masked=True, layup=self._layup(1.0, 36, 48), mode="backcast")
        fa2_cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2024,
            st_gas_mustrun_per_plant=True,
            st_gas_mustrun_p25_level=True,
            mustrun_layup_window_mask=True,
        )
        fa2_cfg.mode = "forecast"  # post-construction: bypasses the config guard
        load = np.arange(self._HOURS, dtype=float) + 1.0
        with (
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_level",
                return_value={(self._PLANT, "ST_GAS"): 100.0},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac",
                return_value={(self._PLANT, "ST_GAS"): 0.5},
            ),
            unittest.mock.patch(
                "market_sim.data.outages.unit_layup_removed_fractions",
                return_value=self._layup(1.0, 36, 48),
            ),
        ):
            fa2 = generators_to_fleet_arrays(
                self._gens(),
                ["North"],
                hours=self._HOURS,
                iso="MISO",
                config=fa2_cfg,
                load_shape=load,
            )
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 12)  # masked in backcast
        self.assertEqual(int((fa2.min_gen[0] > 0).sum()), 24)  # unmasked forecast

    def test_generic_branch_honours_the_mask(self):
        """The non-p25 (committed-tranche) floor branch masks identically."""
        gens = self._gens(cc_mustrun_pmin_mw=80.0, cc_mustrun_online_frac=0.5)
        fa = self._fa(masked=True, layup=self._layup(1.0, 36, 48), gens=gens, p25=False)
        np.testing.assert_allclose(fa.min_gen[0, 36:], 0.0)
        self.assertEqual(int((fa.min_gen[0] > 0).sum()), 12)


class TestStGasP25MeasuredLevelBasis(unittest.TestCase):
    """Measured-MW p25 level basis (``st_gas_mustrun_p25_measured_level``).

    miso-172. ``p25_cf`` is a percentile of ``net / (nameplate x avail_mult)``,
    so the incumbent ``p25_cf x nameplate`` reconstruction drops the derate the
    statistic was divided by and over-floors deep-derate plants by
    ``1 / avail_mult`` (MISO 1122 Ames: 73.3 MW reconstructed vs 33 MW
    measured). These tests pin default-off inertness and the level REPLACE.
    """

    _HOURS = 48
    _PLANT = 9903

    def _fa(self, *, measured=False):
        cfg = ScenarioConfig(
            mode="backcast",
            weather_year=2024,
            st_gas_mustrun_per_plant=True,
            st_gas_mustrun_p25_level=True,
            st_gas_mustrun_p25_measured_level=measured,
        )
        gens = [
            Generator(
                unit_id="stg_0",
                name="Steamer",
                zone="North",
                fuel_type="gas_st",
                pmax_mw=200.0,
                heat_rate=7.0,
                plant_group="ST_GAS",
                plant_code=self._PLANT,
            )
        ]
        load = np.arange(self._HOURS, dtype=float) + 1.0
        with (
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_level",
                return_value={(self._PLANT, "ST_GAS"): 120.0},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_online_frac",
                return_value={(self._PLANT, "ST_GAS"): 0.5},
            ),
            unittest.mock.patch(
                "market_sim.data.fleet.thermal_tranche_p25_measured_level",
                return_value={(self._PLANT, "ST_GAS"): 50.0},
            ),
        ):
            return generators_to_fleet_arrays(
                gens,
                ["North"],
                hours=self._HOURS,
                iso="MISO",
                config=cfg,
                load_shape=load,
            )

    def test_default_off_keeps_the_reconstructed_level(self):
        fa = self._fa(measured=False)
        window = np.arange(self._HOURS - 24, self._HOURS)
        np.testing.assert_allclose(fa.min_gen[0, window], 120.0)

    def test_armed_replaces_the_level_only(self):
        """The measured MW level replaces the CF reconstruction; window intact."""
        fa = self._fa(measured=True)
        window = np.arange(self._HOURS - 24, self._HOURS)
        np.testing.assert_allclose(fa.min_gen[0, window], 50.0)
        np.testing.assert_allclose(fa.min_gen[0, : self._HOURS - 24], 0.0)
        self.assertTrue(
            (fa.min_gen_mechanism[0, window] == MECH_ST_GAS_MUSTRUN_PER_PLANT).all()
        )

    def test_forecast_mode_refused(self):
        with self.assertRaises(ValueError):
            ScenarioConfig(
                mode="forecast", iso="MISO", st_gas_mustrun_p25_measured_level=True
            )


class TestCcWinterCapabilityBasis(unittest.TestCase):
    """``cc_winter_capability_basis`` — the published seasonal capability basis.

    caiso-186 (BE-4). The mechanism was **REFUSED at CAISO on measured evidence**
    (G-NOCONTRA, ``FINDING-caiso186-seasonal-capability-2026-08-09.md``) and is
    armed by no keeper; these tests pin the properties that make the refusal
    reproducible and keep the default path byte-inert for every ISO:

    * the field is **default-off** everywhere;
    * with the PARENT flag ``cc_nameplate_summer_derate`` off, arming it is a
      **no-op** by construction (the fleet carries net-summer capacity to which a
      winter rating cannot be applied without a basis change ``fleet_to_bins``
      did not make);
    * the published-pair arithmetic is exactly ``B = max(net_summer, winter)``
      with ratios ``net_summer / B`` and ``winter / B``, both in ``(0, 1]``, the
      net-summer double-file clamp preserved and the winter rating deliberately
      **unclamped** (8 of 67 California CC plants publish a winter capability
      above nameplate — deleting that half would delete the upward direction).
    """

    def test_defaults_off_for_every_iso(self) -> None:
        """No ISO gets the basis by default (rule 25 ``[R-ISO-SCOPE]``)."""
        from market_sim.config.scenarios import ScenarioConfig

        for iso in (
            "ERCOT",
            "CAISO",
            "PJM",
            "MISO",
            "NYISO",
            "NEISO",
            "SPP",
            "NWPP",
            "SOCO",
        ):
            with self.subTest(iso=iso):
                self.assertFalse(ScenarioConfig(iso=iso).cc_winter_capability_basis)

    def test_arming_hashes_distinctly(self) -> None:
        """An armed config is a different scenario and must not reuse a bundle."""
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig(iso="CAISO", cc_nameplate_summer_derate=True)
        armed = base.with_overrides(cc_winter_capability_basis=True)
        self.assertNotEqual(base.cache_key(), armed.cache_key())

    def test_registered_in_cache_key_optional_fields(self) -> None:
        """Registered WITH its declared default, in the field's own commit."""
        from market_sim.config.scenarios import (
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
            _CACHE_KEY_OPTIONAL_FIELDS,
        )

        self.assertIn("cc_winter_capability_basis", _CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["cc_winter_capability_basis"], "False"
        )

    def test_ratios_are_published_pair_over_their_own_max(self) -> None:
        """``B = max(ns, winter)``; both ratios published, in ``(0, 1]``."""
        from market_sim.data.fleet import campd_bins as cb

        pairs = {
            # (nameplate, net_summer) as cc_summer_capacity returns them, with
            # the double-file clamp already applied.
            10: (1398.0, 1020.0),  # winter == net summer -> B = ns, both ratios 1
            20: (1036.8, 1018.0),  # winter ABOVE nameplate -> B = winter
            30: (710.7, 592.72),  # winter between ns and nameplate -> B = winter
        }
        winters = {10: 1020.0, 20: 1110.0, 30: 602.53}
        with (
            unittest.mock.patch.object(cb, "cc_summer_capacity", return_value=pairs),
            unittest.mock.patch.object(cb, "cc_winter_capacity", return_value=winters),
        ):
            for code, (nameplate, ns) in pairs.items():
                with self.subTest(plant=code):
                    sr, wr = cb.cc_seasonal_capability_ratios(code)
                    basis = max(ns, winters[code])
                    self.assertAlmostEqual(sr, ns / basis)
                    self.assertAlmostEqual(wr, winters[code] / basis)
                    self.assertGreater(sr, 0.0)
                    self.assertLessEqual(sr, 1.0)
                    self.assertGreater(wr, 0.0)
                    self.assertLessEqual(wr, 1.0)
                    # The basis is a PUBLISHED rating, never nameplate, except
                    # where a published rating happens to equal it.
                    self.assertLessEqual(basis, max(nameplate, winters[code]))
            # Plant 20 is the upward direction: B exceeds nameplate, so the bin
            # RISES. Deleting the unclamped winter would silently lose this.
            self.assertGreater(max(pairs[20][1], winters[20]), pairs[20][0])

    def test_absent_plant_falls_back(self) -> None:
        """A plant missing from either EIA-860 map returns ``None``.

        The caller then keeps the incumbent ``cc_summer_derate_ratio`` treatment
        — the identical fallback ``fleet_to_bins`` takes — so the capacity basis
        and the availability legs can never disagree.
        """
        from market_sim.data.fleet import campd_bins as cb

        with (
            unittest.mock.patch.object(
                cb, "cc_summer_capacity", return_value={7: (100.0, 90.0)}
            ),
            unittest.mock.patch.object(cb, "cc_winter_capacity", return_value={}),
        ):
            self.assertIsNone(cb.cc_seasonal_capability_ratios(7))
        with (
            unittest.mock.patch.object(cb, "cc_summer_capacity", return_value={}),
            unittest.mock.patch.object(
                cb, "cc_winter_capacity", return_value={7: 95.0}
            ),
        ):
            self.assertIsNone(cb.cc_seasonal_capability_ratios(7))

    def test_parent_off_is_a_noop(self) -> None:
        """With ``cc_nameplate_summer_derate`` off the flag changes nothing."""
        gens = [
            Generator(
                unit_id="999902_1",
                name="Test CC",
                zone="Z",
                fuel_type="gas_cc",
                pmax_mw=400.0,
                heat_rate=7.0,
                plant_group="CC_REGULAR",
                plant_code=999902,
            )
        ]
        from market_sim.config.scenarios import ScenarioConfig

        avails = []
        for arm in (False, True):
            cfg = ScenarioConfig(
                iso="CAISO",
                mode="backcast",
                weather_year=2024,
                cc_nameplate_summer_derate=False,
                cc_winter_capability_basis=arm,
            )
            fa = generators_to_fleet_arrays(
                gens, ["Z"], hours=48, iso="CAISO", config=cfg, year=2024
            )
            avails.append(fa.availability.copy())
        np.testing.assert_array_equal(avails[0], avails[1])


if __name__ == "__main__":
    unittest.main()
