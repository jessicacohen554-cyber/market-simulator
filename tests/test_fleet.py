"""Tests for the generation fleet inventory and vectorization."""

import tempfile
import unittest
import unittest.mock
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.constants import HEAT_RATE_BINS
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import CAMPD_BINS_CSV, PROCESSED_DIR
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
from market_sim.data.floor_mechanisms import MECH_ST_GAS_MUSTRUN_PER_PLANT
from market_sim.data.offer_curves import split_coal_tranches


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

    ALL_ISOS = ["ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO"]

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
        mystic = [g for g in retirees if int(g.plant_code) == 1588]
        self.assertTrue(mystic, "Mystic (plant 1588) should be a NEISO exit")
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
    """Tests for the coal take-or-pay supply-curve tranche split."""

    def _coal_and_cc(self) -> list[Generator]:
        return [
            Generator(
                unit_id="COAL",
                name="COAL",
                zone="z",
                fuel_type="coal",
                pmax_mw=1000.0,
                pmin_mw=400.0,
                heat_rate=10.0,
                vom=4.5,
                emission_rate_co2=1.0,
                eford=0.08,
            ),
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

    def test_split_produces_three_tranches_per_coal_bin(self):
        fleet, fuel_fracs = split_coal_tranches(self._coal_and_cc(), ScenarioConfig())
        # 3 coal tranches + 1 unchanged CC.
        self.assertEqual(len(fleet), 4)
        self.assertEqual(len(fuel_fracs), 4)

        coal = [g for g in fleet if g.fuel_type == "coal"]
        self.assertEqual([g.unit_id for g in coal], ["COAL_t1", "COAL_t2", "COAL_t3"])
        # Capacity fractions 0.30 / 0.25 / 0.45 of the 1000 MW bin.
        np.testing.assert_allclose([g.pmax_mw for g in coal], [300.0, 250.0, 450.0])
        # Tranches carry no Pmin floor.
        self.assertTrue(all(g.pmin_mw == 0.0 for g in coal))
        # Fuel passthrough: T1 none, T2 partial, T3 full; CC always full.
        np.testing.assert_allclose(fuel_fracs, [0.0, 0.35, 1.0, 1.0])

    def test_non_coal_passes_through_unchanged(self):
        fleet, fuel_fracs = split_coal_tranches(self._coal_and_cc(), ScenarioConfig())
        cc = fleet[-1]
        self.assertEqual(cc.unit_id, "CC")
        self.assertEqual(cc.fuel_type, "gas_cc")
        self.assertEqual(fuel_fracs[-1], 1.0)

    def test_tranche_capacity_sums_to_original_bin(self):
        fleet, _ = split_coal_tranches(self._coal_and_cc(), ScenarioConfig())
        coal_total = sum(g.pmax_mw for g in fleet if g.fuel_type == "coal")
        self.assertAlmostEqual(coal_total, 1000.0)

    def test_apply_coal_tranches_discounts_only_fuel(self):
        # T1 bids at VOM only; T2 keeps 35% of its fuel cost; T3 unchanged.
        # Fuel cost = heat_rate (10) x fuel_price (2) = 20 $/MWh.
        # Coal MC before tranching = fuel 20 + VOM 4.5 + carbon 30 = 54.5.
        fleet, fuel_fracs = split_coal_tranches(self._coal_and_cc(), ScenarioConfig())
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

    def test_tranche_fractions_follow_config(self):
        config = ScenarioConfig(
            coal_tranche_1_frac=0.50,
            coal_tranche_2_frac=0.20,
            coal_tranche_3_frac=0.30,
        )
        fleet, _ = split_coal_tranches(self._coal_and_cc(), config)
        coal = [g for g in fleet if g.fuel_type == "coal"]
        np.testing.assert_allclose([g.pmax_mw for g in coal], [500.0, 200.0, 300.0])


class HistoricOutageOverlayTest(unittest.TestCase):
    """The backcast-only historic-outage availability overlay."""

    # Repo root (tests/ lives at the repo root); the overlay reads the
    # committed bin assignments and outage extract.
    _REPO = Path(__file__).parents[1]
    _BINS = str(CAMPD_BINS_CSV)

    def _fleet(self):
        # Coleto Creek (6178) is a coal plant with a real >2-day 2023
        # outage. Here it appears once as a COAL bin and once (synthetically)
        # as a CT_PEAKER bin to verify the per-bin group filter: CT_PEAKER is
        # not a qualifying overlay group, so its bin must be spared even though
        # the plant code is outaged. Plant 99999 is a coal plant with no outage.
        return [
            Generator(
                unit_id="coleto_coal",
                name="Coleto coal",
                zone="z",
                fuel_type="coal",
                pmax_mw=600.0,
                online_year=1980,
                plant_group="COAL",
                plant_code=6178,
            ),
            Generator(
                unit_id="coleto_ctpeaker",
                name="Coleto peaker",
                zone="z",
                fuel_type="gas_ct",
                pmax_mw=100.0,
                online_year=1980,
                plant_group="CT_PEAKER",
                plant_code=6178,
            ),
            Generator(
                unit_id="other_coal",
                name="Other coal",
                zone="z",
                fuel_type="coal",
                pmax_mw=500.0,
                online_year=1990,
                plant_group="COAL",
                plant_code=99999,
            ),
        ]

    def _outage_hour(self):
        from market_sim.data.outages import outage_masks_for_year

        masks = outage_masks_for_year(2023, 8760, bins_path=self._BINS)
        return int(np.argmax(masks[6178]))  # first outaged hour for Coleto

    def _config(self, source):
        return ScenarioConfig(
            weather_year=2023,
            outage_source=source,
            campd_bins_path=self._BINS,
        )

    def _august_hour(self):
        from market_sim.data.outages import _hour_of_year

        return _hour_of_year(8, 1, 0)  # summer peak, outside every window

    def test_historic_zeros_outaged_coal_bin(self):
        arrays = generators_to_fleet_arrays(
            self._fleet(),
            ["z"],
            hours=8760,
            iso="ERCOT",
            config=self._config("historic"),
        )
        out_h = self._outage_hour()
        # Coleto's COAL bin is fully zeroed during the outage hour...
        self.assertEqual(arrays.availability[0, out_h], 0.0)
        # ...but available outside the window (a summer-peak hour).
        self.assertGreater(arrays.availability[0, self._august_hour()], 0.0)

    def test_group_filter_spares_non_coal_cc_bin(self):
        arrays = generators_to_fleet_arrays(
            self._fleet(),
            ["z"],
            hours=8760,
            iso="ERCOT",
            config=self._config("historic"),
        )
        out_h = self._outage_hour()
        # Same plant_code (6178) but a CT_PEAKER bin (non-qualifying) -> spared.
        self.assertGreater(arrays.availability[1, out_h], 0.0)
        # A coal plant with no historic outage is untouched.
        self.assertGreater(arrays.availability[2, out_h], 0.0)

    def test_statistical_source_does_not_apply_outages(self):
        arrays = generators_to_fleet_arrays(
            self._fleet(),
            ["z"],
            hours=8760,
            iso="ERCOT",
            config=self._config("statistical"),
        )
        out_h = self._outage_hour()
        # The default statistical model leaves WEFOR/POF availability (>0).
        self.assertGreater(arrays.availability[0, out_h], 0.0)


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


if __name__ == "__main__":
    unittest.main()
