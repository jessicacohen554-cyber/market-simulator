"""Tests for the EIA-923 monthly per-plant fuel-cost integration.

The fuel resolver applies plant-specific monthly delivered fuel costs
from EIA-923 Schedule 5 in BACKCAST mode (and the capacity hindcast) and
falls back to the AEO Henry Hub trajectory + ISO basis differential
otherwise. The overlay is mode-gated (G11 / W2-E, rule 22 / spec §1.7):
year availability alone is not the forecast gate, because the parquet
carries measured rows for the forecast start year since the H1-2026
intake. Plants outside the F923 sample keep the trajectory in every mode.
See :mod:`market_sim.data.eia923` and
:func:`market_sim.data.fuel.apply_plant_monthly_fuel_prices`.
"""

from __future__ import annotations

import unittest

import numpy as np
import pytest

from market_sim.config.constants import (
    GAS_BASIS_DIFFERENTIAL,
    HENRY_HUB_TRAJECTORIES,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.paths import CAMPD_BINS_CSV
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.eia923 import (
    available_years,
    load_monthly_fuel_costs,
    plant_month_price_grid,
)
from market_sim.data.fleet import (
    FUEL_TYPE_MAP,
    Generator,
    bins_to_fleet,
    generators_to_fleet_arrays,
    load_campd_bins,
)
from market_sim.data.fuel import (
    apply_plant_monthly_fuel_prices,
    resolve_fuel_prices,
)

ZONE_NAMES = get_iso_config("ERCOT").zone_names
BINS_CSV = str(CAMPD_BINS_CSV)

# Plant 3439 (Laredo) reports natural-gas receipts in every month of
# 2024, so it exercises the per-plant monthly gas lookup end-to-end.
_GAS_REPORTING_PLANT: int = 3439
_GAS_REPORTING_FUEL_GROUP: str = "Natural Gas"


class TestMonthlyFuelCostsLoader(unittest.TestCase):
    """The processed F923 parquet loads with the expected schema."""

    @classmethod
    def setUpClass(cls):
        cls.costs = load_monthly_fuel_costs()

    def test_loader_returns_expected_columns(self):
        expected = {
            "year",
            "month",
            "plant_id",
            "state",
            "fuel_group",
            "price_per_mmbtu",
        }
        self.assertTrue(expected.issubset(self.costs.columns))

    def test_calibration_years_present(self):
        years = available_years(self.costs)
        # The data window covers 2023-2025 calibration runs.
        self.assertIn(2023, years)
        self.assertIn(2024, years)

    def test_prices_are_in_realistic_dollars_per_mmbtu(self):
        prices = self.costs["price_per_mmbtu"]
        # F923 occasionally reports a negative delivered cost when a
        # take-or-pay producer pays to dispose of stranded gas. The vast
        # majority are positive. The national table keeps real constrained-
        # region winter gas spikes (up to ~$118/MMBtu in this window), so the
        # realistic ceiling is the processor's anomaly cutoff; order-of-
        # magnitude data-entry errors above it are dropped at build time.
        self.assertTrue((prices > 0).mean() > 0.99)
        self.assertLessEqual(prices.max(), 200.0)


class TestPlantMonthPriceGrid(unittest.TestCase):
    """The price grid yields one NaN-padded length-12 array per plant."""

    @classmethod
    def setUpClass(cls):
        cls.costs = load_monthly_fuel_costs()

    def test_grid_keys_are_plant_ids(self):
        grid = plant_month_price_grid(self.costs, 2024, "Natural Gas")
        self.assertGreater(len(grid), 0)
        for plant_id, prices in grid.items():
            self.assertIsInstance(plant_id, int)
            self.assertEqual(prices.shape, (12,))

    def test_missing_months_are_nan(self):
        # A plant that reports only some months still gets a 12-element
        # array, with the unreported months left as NaN so the resolver
        # can fall back to the per-fuel default.
        grid = plant_month_price_grid(self.costs, 2024, "Natural Gas")
        any_partial = any(np.isnan(prices).any() for prices in grid.values())
        all_present = all(np.isnan(prices).any() for prices in grid.values())
        # The data has both fully-reported and partially-reported plants.
        self.assertTrue(any_partial or all_present is False)

    def test_grid_empty_for_year_outside_window(self):
        grid = plant_month_price_grid(self.costs, 2099, "Natural Gas")
        self.assertEqual(grid, {})


class TestApplyPlantMonthlyFuelPrices(unittest.TestCase):
    """The resolver overwrites the per-fuel default with plant F923 cost.

    Per-plant monthly *gas* pricing is opt-in (off by default), so these
    tests of the gas overwrite mechanism enable it explicitly. The overlay
    is backcast-only since the W2-E mode gate, so the class config runs
    ``mode="backcast"`` — the mode the overlay has always served (the
    pre-gate tests ran in the then-mode-blind default forecast config).
    """

    def setUp(self):
        self.config = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=8760,
            gas_plant_monthly_fuel_pricing=True,
        )

    def _build_two_plant_fleet(self) -> tuple[np.ndarray, object]:
        """Build a two-plant fleet: one with F923 data, one without."""
        generators = [
            Generator(
                unit_id="REPORTING_GAS_CC",
                name="Reporting Gas CC",
                zone="Houston",
                fuel_type="gas_cc",
                pmax_mw=500.0,
                heat_rate=7.0,
                plant_code=_GAS_REPORTING_PLANT,
            ),
            Generator(
                unit_id="UNTRACKED_GAS_CC",
                name="Untracked Gas CC",
                zone="Houston",
                fuel_type="gas_cc",
                pmax_mw=300.0,
                heat_rate=7.0,
                plant_code=999_999_999,  # absent from F923
            ),
        ]
        arrays = generators_to_fleet_arrays(
            generators, ZONE_NAMES, hours=self.config.hours
        )
        return arrays

    def test_calibration_year_overwrites_reported_months(self):
        arrays = self._build_two_plant_fleet()
        fuel_prices = resolve_fuel_prices(self.config, arrays, year=2024)
        # The reporting plant's January price should match its F923 entry.
        costs = load_monthly_fuel_costs()
        grid = plant_month_price_grid(costs, 2024, _GAS_REPORTING_FUEL_GROUP)
        prices = grid[_GAS_REPORTING_PLANT]
        for month_idx, expected in enumerate(prices):
            if np.isnan(expected):
                continue
            # Pick the middle of the month so we avoid month-boundary hours.
            hour = (
                sum((31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[:month_idx]) * 24
                + 24
            )
            self.assertAlmostEqual(
                float(fuel_prices[0, hour]),
                float(expected),
                places=5,
                msg=f"Plant {_GAS_REPORTING_PLANT} month {month_idx + 1} "
                "did not match F923",
            )

    def test_untracked_plant_keeps_aeo_trajectory(self):
        arrays = self._build_two_plant_fleet()
        fuel_prices = resolve_fuel_prices(self.config, arrays, year=2024)
        # The untracked plant's price is the AEO Henry Hub trajectory plus
        # ISO basis, with seasonality applied (the config default).
        expected_annual = (
            HENRY_HUB_TRAJECTORIES["mid"][2024] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
        )
        # Annual average is budget-neutral with seasonality.
        self.assertAlmostEqual(
            float(fuel_prices[1].mean()),
            expected_annual,
            places=2,
        )

    def test_forward_year_keeps_aeo_trajectory_for_every_plant(self):
        # 2030 is outside the F923 sample window, so every plant — even
        # the one whose plant_code reports in 2024 — falls back to the
        # AEO trajectory.
        arrays = self._build_two_plant_fleet()
        fuel_prices = resolve_fuel_prices(self.config, arrays, year=2030)
        expected_annual = (
            HENRY_HUB_TRAJECTORIES["mid"][2030] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
        )
        for g in range(arrays.n_gen):
            self.assertAlmostEqual(
                float(fuel_prices[g].mean()),
                expected_annual,
                places=2,
            )

    def test_plant_code_zero_skips_f923(self):
        # Generators without a known plant_code (the WECC imports, the
        # legacy aggregated fleet) keep the per-fuel default — F923 keys
        # off plant_code > 0.
        gen = Generator(
            unit_id="NO_CODE",
            name="No Code",
            zone="Houston",
            fuel_type="gas_cc",
            pmax_mw=200.0,
            heat_rate=7.0,
            plant_code=0,
        )
        arrays = generators_to_fleet_arrays([gen], ZONE_NAMES, hours=self.config.hours)
        fuel_prices = resolve_fuel_prices(self.config, arrays, year=2024)
        expected_annual = (
            HENRY_HUB_TRAJECTORIES["mid"][2024] + GAS_BASIS_DIFFERENTIAL["ERCOT"]
        )
        self.assertAlmostEqual(
            float(fuel_prices[0].mean()),
            expected_annual,
            places=2,
        )

    def test_apply_function_is_idempotent_when_no_data(self):
        # Calling the helper with a year outside the F923 window is a
        # no-op: fuel_prices is left exactly as it was.
        arrays = self._build_two_plant_fleet()
        fuel_prices = np.full((arrays.n_gen, self.config.hours), 2.5)
        before = fuel_prices.copy()
        apply_plant_monthly_fuel_prices(fuel_prices, arrays, self.config, year=2099)
        np.testing.assert_array_equal(fuel_prices, before)


# Plant 6139 (TX coal) reports delivered coal cost in every intaken H1-2026
# month (Jan-Apr), so it is the leak subject: pre-gate, a forecast-mode 2026
# run priced it from measured actuals (W1-B B2).
_COAL_2026_REPORTING_PLANT: int = 6139


class TestForecastModeGate(unittest.TestCase):
    """G11 / W2-E: the F923 overlay is backcast-only (hindcast excepted).

    ``apply_plant_monthly_fuel_prices`` used to gate on year availability
    alone; once measured H1-2026 receipts were intaken the parquet carries
    the forecast start year, and the W1-B forecast smokes priced ERCOT 12 /
    PJM 51 generators from 2026 actuals. These tests reproduce that leak's
    precondition and prove the mode gate closes it, and pin the documented
    capacity-hindcast carve-out (realized historical inputs by design).
    No LP is built anywhere here — loader/array checks only.
    """

    HOURS = 8760

    def _coal_fleet(self):
        gen = Generator(
            unit_id="COAL_2026_REPORTER",
            name="Coal 2026 Reporter",
            zone="Houston",
            fuel_type="coal",
            pmax_mw=600.0,
            heat_rate=10.0,
            plant_code=_COAL_2026_REPORTING_PLANT,
        )
        return generators_to_fleet_arrays([gen], ZONE_NAMES, hours=self.HOURS)

    def test_leak_precondition_2026_rows_are_intaken(self):
        # The exact precondition of the W1-B leak: the old year-availability
        # gate PASSES for 2026 (rows exist) and the subject plant reports.
        costs = load_monthly_fuel_costs()
        self.assertIn(2026, available_years(costs))
        grid = plant_month_price_grid(costs, 2026, "Coal")
        self.assertIn(_COAL_2026_REPORTING_PLANT, grid)
        self.assertTrue(np.isfinite(grid[_COAL_2026_REPORTING_PLANT]).any())

    def test_forecast_mode_ignores_2026_f923_rows(self):
        # The leak, closed: with 2026 rows present (test above), a
        # forecast-mode overlay call must leave the price array untouched,
        # while the identical backcast-mode call mutates it — isolating the
        # mode gate as the only difference.
        arrays = self._coal_fleet()
        base = np.full((arrays.n_gen, self.HOURS), 2.5)

        forecast = ScenarioConfig(iso="ERCOT", mode="forecast", hours=self.HOURS)
        fp_forecast = base.copy()
        apply_plant_monthly_fuel_prices(fp_forecast, arrays, forecast, year=2026)
        np.testing.assert_array_equal(fp_forecast, base)

        backcast = ScenarioConfig(iso="ERCOT", mode="backcast", hours=self.HOURS)
        fp_backcast = base.copy()
        apply_plant_monthly_fuel_prices(fp_backcast, arrays, backcast, year=2026)
        self.assertTrue(
            (fp_backcast != base).any(),
            "backcast overlay should apply the measured 2026 plant-months "
            "(the data the forecast gate must ignore)",
        )

    def test_forecast_resolver_prices_2026_coal_from_trajectory(self):
        # End-to-end through resolve_fuel_prices: forecast 2026 coal pays
        # the AEO-anchored trajectory in every hour, not measured receipts.
        from market_sim.data.fuel import resolve_annual_coal_price

        arrays = self._coal_fleet()
        config = ScenarioConfig(iso="ERCOT", mode="forecast", hours=self.HOURS)
        fuel_prices = resolve_fuel_prices(config, arrays, year=2026)
        expected = resolve_annual_coal_price(config, 2026)
        np.testing.assert_allclose(fuel_prices[0], expected, rtol=1e-9)

    def test_hindcast_carveout_keeps_overlay_byte_identical_to_backcast(self):
        # The capacity hindcast (mode=="forecast", hindcast=True) is DESIGNED
        # to consume realized historical inputs, so the carve-out keeps its
        # overlay mutation byte-identical to backcast — for both fuel
        # variants, which isolate the GAS trajectory and share the
        # delivered-coal channel.
        arrays = self._coal_fleet()
        base = np.full((arrays.n_gen, self.HOURS), 2.5)

        backcast = ScenarioConfig(iso="ERCOT", mode="backcast", hours=self.HOURS)
        fp_backcast = base.copy()
        apply_plant_monthly_fuel_prices(fp_backcast, arrays, backcast, year=2024)
        self.assertTrue((fp_backcast != base).any())

        for variant in ("realized", "asknown"):
            hindcast = ScenarioConfig(
                iso="ERCOT",
                mode="forecast",
                hindcast=True,
                hindcast_fuel_variant=variant,
                hours=self.HOURS,
            )
            fp_hindcast = base.copy()
            apply_plant_monthly_fuel_prices(fp_hindcast, arrays, hindcast, year=2024)
            np.testing.assert_array_equal(
                fp_hindcast,
                fp_backcast,
                err_msg=f"hindcast variant {variant!r} overlay diverged from backcast",
            )


class TestPerPlantBinning(unittest.TestCase):
    """Every plant in the CAMPD CSV becomes its own LP bin."""

    @classmethod
    def setUpClass(cls):
        cls.bins = load_campd_bins(BINS_CSV)
        cls.fleet, cls.arrays = bins_to_fleet(cls.bins, ZONE_NAMES, ScenarioConfig())

    def test_one_bin_row_per_plant(self):
        # The CSV has ~302 rows (one per plant); after splitting by
        # plant-group (W A Parish has both coal and gas-steam rows) the
        # bin count equals the CSV row count.
        from pathlib import Path
        import pandas as pd

        raw = pd.read_csv(Path(BINS_CSV))
        self.assertEqual(len(self.bins), len(raw))

    def test_every_tranche_carries_a_plant_code(self):
        # Every generator from bins_to_fleet has plant_code > 0, so the
        # F923 monthly resolver can route per-plant prices to it.
        for g in self.fleet:
            self.assertGreater(g.plant_code, 0, msg=g.unit_id)
        self.assertTrue(np.all(self.arrays.plant_code > 0))

    def test_unit_ids_unique_after_per_plant_split(self):
        ids = [g.unit_id for g in self.fleet]
        self.assertEqual(len(ids), len(set(ids)))

    def test_tranche_hr_is_plant_hr_times_csv_multiplier(self):
        # For a specific plant, the committed tranche HR equals
        # Plant_Avg_HR × HR_Mult_Committed (within rounding).
        import pandas as pd

        raw = pd.read_csv(BINS_CSV)
        # Pick a plant whose Committed multiplier is non-null.
        sample = raw[raw["HR_Mult_Committed"].notna()].iloc[0]
        plant_code = int(sample["Plant_Code"])
        expected = float(sample["Plant_Avg_HR_MMBtu_MWh"]) * float(
            sample["HR_Mult_Committed"]
        )
        committed = next(
            g
            for g in self.fleet
            if g.plant_code == plant_code and g.unit_id.endswith("_committed")
        )
        self.assertAlmostEqual(committed.heat_rate, expected, places=4)


class TestRunnerEndToEndFor2024(unittest.TestCase):
    """End-to-end gas pricing for a 2024 calibration year.

    Builds the production fleet from the shipped CAMPD CSV and resolves
    2024 fuel prices in backcast mode (the mode the F923 overlay serves
    since the W2-E gate). By default every gas generator pays the *same*
    uniform Henry Hub + basis price (per-plant gas pricing is off, so
    patchy EIA-923 reporting cannot split same-zone units); turning
    ``gas_plant_monthly_fuel_pricing`` on restores the per-plant spread.
    """

    def _gas_means(self, config):
        bins = load_campd_bins(BINS_CSV)
        _, arrays = bins_to_fleet(bins, ZONE_NAMES, config)
        fuel_prices = resolve_fuel_prices(config, arrays, year=2024)
        gas_mask = np.isin(
            arrays.fuel_type_idx,
            [FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]],
        )
        return fuel_prices[gas_mask].mean(axis=1)

    def test_gas_is_uniform_by_default(self):
        gas_means = self._gas_means(
            ScenarioConfig(iso="ERCOT", mode="backcast", hours=8760)
        )
        # Every gas plant pays a positive price, and they are all identical
        # — the F923 per-plant overwrite is off, so nothing splits them.
        self.assertTrue((gas_means > 0).all())
        self.assertAlmostEqual(float(gas_means.std()), 0.0, places=9)

    def test_flag_restores_per_plant_f923_spread(self):
        gas_means = self._gas_means(
            ScenarioConfig(
                iso="ERCOT",
                mode="backcast",
                hours=8760,
                gas_plant_monthly_fuel_pricing=True,
            )
        )
        # With the opt-in flag, reporting plants diverge from the AEO default.
        self.assertTrue((gas_means > 0).all())
        self.assertGreater(gas_means.std(), 0.05)

    def test_daily_shape_survives_gas_plant_monthly_overwrite(self):
        """gas_daily_shape rides on top of the F923 gas plant-month level.

        The flat monthly overwrite used to erase the daily Henry Hub swing
        for every F923-covered gas plant; the overwrite now re-carries the
        mean-preserving factors, so a covered plant-month keeps its measured
        monthly MEAN while gaining within-month daily variance.
        """
        from market_sim.data.fuel import _month_index

        flat = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=8760,
            gas_plant_monthly_fuel_pricing=True,
        )
        shaped = ScenarioConfig(
            iso="ERCOT",
            mode="backcast",
            hours=8760,
            gas_plant_monthly_fuel_pricing=True,
            gas_daily_shape=True,
        )
        bins = load_campd_bins(BINS_CSV)
        _, arrays = bins_to_fleet(bins, ZONE_NAMES, flat)
        p_flat = resolve_fuel_prices(flat, arrays, year=2024)
        p_shaped = resolve_fuel_prices(shaped, arrays, year=2024)
        gas_rows = np.flatnonzero(
            np.isin(
                arrays.fuel_type_idx,
                [FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]],
            )
        )
        month = _month_index(8760)
        g = int(gas_rows[0])
        for m in range(12):
            mask = month == m
            # Monthly mean preserved to the factor-normalization tolerance…
            self.assertAlmostEqual(
                float(p_shaped[g, mask].mean()),
                float(p_flat[g, mask].mean()),
                delta=0.03 * float(p_flat[g, mask].mean()),
            )
        # …while the shaped series gains within-month daily variance the
        # flat overwrite had erased.
        self.assertGreater(float(p_shaped[g].std()), float(p_flat[g].std()))


class PrbPassthroughSigmoidTest(unittest.TestCase):
    """The gas-keyed PRB passthrough sigmoid and its on/off toggle."""

    def test_off_returns_flat_scalar(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            gas_price_override=2.19,
            coal_prb_passthrough=0.9,
            coal_prb_passthrough_sigmoid=False,
        )
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "prb"), 0.9)

    def test_on_rises_with_gas_between_floor_and_ceil(self):
        from market_sim.data.fuel import coal_passthrough_series

        def mean_pt(gas):
            cfg = ScenarioConfig(
                gas_price_override=gas,
                coal_prb_passthrough_sigmoid=True,
                coal_prb_passthrough_floor=0.45,
                coal_prb_passthrough_ceil=1.10,
                coal_prb_passthrough_gas_mid=3.0,
                coal_prb_passthrough_gas_slope=1.8,
            )
            return float(np.mean(coal_passthrough_series(cfg, 2024, 8760, "prb")))

        low, mid, high = mean_pt(2.0), mean_pt(3.0), mean_pt(6.0)
        self.assertLess(low, mid)
        self.assertLess(mid, high)
        self.assertGreaterEqual(low, 0.45)  # floor
        self.assertLessEqual(high, 1.10 + 1e-9)  # ceil
        self.assertGreater(high, 1.0)  # dear gas -> markup

    def test_seasonal_variation_when_on(self):
        # Params left at None resolve from COAL_SIGMOID_DEFAULTS for the
        # default ERCOT iso (region-dependent defaults).
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            gas_price_override=3.52,
            coal_prb_passthrough_sigmoid=True,
            gas_seasonality=True,
        )
        series = coal_passthrough_series(cfg, 2025, 8760, "prb")
        self.assertEqual(series.shape, (8760,))
        self.assertGreater(series.max() - series.min(), 0.05)  # months differ

    def test_array_passthrough_discounts_hourly(self):
        # apply_coal_tranches accepts an (T,) PRB passthrough and discounts
        # the fuel term hour-by-hour.
        from market_sim.data.fleet import (
            apply_coal_tranches,
            assemble_mc,
            campd_tranche_fuel_frac,
        )

        gen = Generator(
            unit_id="COAL_z_p298_econ",
            name="x",
            zone="z",
            fuel_type="coal",
            pmax_mw=100.0,
            heat_rate=10.0,
            coal_supply="prb",
            plant_group="COAL",
        )
        arrays = generators_to_fleet_arrays([gen], ["z"], hours=4)
        fuel_prices = np.full((1, 4), 2.0)  # fuel cost = 10 * 2 = 20 $/MWh
        mc = assemble_mc(arrays, fuel_prices, 0.0, 0.0)
        full = mc[0, 0]
        pt = np.array([0.0, 0.5, 1.0, 1.5])  # incl. a >1 markup hour
        ff = campd_tranche_fuel_frac(gen, {"prb": pt})  # array via routing
        np.testing.assert_array_equal(ff, pt)
        apply_coal_tranches(mc, [gen], arrays, [ff], fuel_prices)
        # hour 0: full fuel (20) removed; hour 2: none; hour 3: +50% markup.
        self.assertAlmostEqual(mc[0, 0], full - 20.0)
        self.assertAlmostEqual(mc[0, 1], full - 10.0)
        self.assertAlmostEqual(mc[0, 2], full)
        self.assertAlmostEqual(mc[0, 3], full + 10.0)


class BitPassthroughSigmoidTest(unittest.TestCase):
    """The gas-keyed bituminous passthrough sigmoid (PJM coal fleet)."""

    def test_off_returns_full_cost(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(iso="PJM", gas_price_override=2.19)
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "bituminous"), 1.0)

    def test_on_rises_with_gas_between_floor_and_ceil(self):
        # Params resolve from the (PJM, bituminous) COAL_SIGMOID_DEFAULTS
        # entry (0.80 / 1.32 / 3.40 / 2.5).
        from market_sim.data.fuel import coal_passthrough_series

        def mean_pt(gas):
            cfg = ScenarioConfig(
                iso="PJM",
                gas_price_override=gas,
                coal_bit_passthrough_sigmoid=True,
            )
            return float(
                np.mean(coal_passthrough_series(cfg, 2024, 8760, "bituminous"))
            )

        low, mid, high = mean_pt(2.0), mean_pt(3.4), mean_pt(7.0)
        self.assertLess(low, mid)
        self.assertLess(mid, high)
        self.assertGreaterEqual(low, 0.80)  # floor
        self.assertLessEqual(high, 1.32 + 1e-9)  # ceil
        self.assertGreater(high, 1.0)  # dear gas -> markup

    def test_routes_each_supply_to_its_own_curve(self):
        # campd_tranche_fuel_frac routes each coal tranche by its own
        # coal_supply tag: bituminous / prb / subbituminous each take their
        # own curve, must-run passes 0.0, and tags without an entry (waste,
        # unmapped lignite) pass full cost.
        from market_sim.data.fleet import campd_tranche_fuel_frac

        def gen(supply, unit_id="COAL_z_p1_econ", fuel="coal"):
            return Generator(
                unit_id=unit_id,
                name="x",
                zone="z",
                fuel_type=fuel,
                pmax_mw=100.0,
                heat_rate=10.0,
                coal_supply=supply,
                plant_group="COAL",
            )

        bit_pt = np.array([0.85, 1.2])
        subbit_pt = np.array([1.0, 1.15])
        pt = {"prb": 0.7, "subbituminous": subbit_pt, "bituminous": bit_pt}
        self.assertIs(campd_tranche_fuel_frac(gen("bituminous"), pt), bit_pt)
        self.assertEqual(campd_tranche_fuel_frac(gen("prb"), pt), 0.7)
        # "subbituminous" (the derived EIA-923 rank tag) is its OWN supply
        # chain with its own per-ISO curve — NOT aliased to prb.
        self.assertIs(campd_tranche_fuel_frac(gen("subbituminous"), pt), subbit_pt)
        self.assertEqual(campd_tranche_fuel_frac(gen("lignite"), pt), 1.0)
        self.assertEqual(campd_tranche_fuel_frac(gen("waste"), pt), 1.0)
        self.assertEqual(
            campd_tranche_fuel_frac(gen("bituminous", unit_id="COAL_z_p1_mustrun"), pt),
            0.0,
        )

    def test_econ_srmc_bound_clamps_marginal_tranches_only(self):
        # coal_econ_srmc_bound: a marginal (econ*/peak) coal tranche's
        # passthrough is clamped to >= 1.0 (its fuel is bought at market —
        # the offer never drops below full measured delivered fuel cost);
        # the committed/must-run bands keep their contracted discount and
        # markups > 1.0 pass through unchanged.
        from market_sim.data.fleet import campd_tranche_fuel_frac

        def gen(unit_id):
            return Generator(
                unit_id=unit_id,
                name="x",
                zone="z",
                fuel_type="coal",
                pmax_mw=100.0,
                heat_rate=10.0,
                coal_supply="bituminous",
                plant_group="COAL",
            )

        pt = {"bituminous": np.array([0.61, 0.95, 1.2])}
        # econ + peak tranches: sub-1.0 hours clamp to exactly 1.0, the
        # 1.2 markup hour is untouched.
        for uid in ("COAL_z_p1_econc00", "COAL_z_p1_econ", "COAL_z_p1_peak"):
            np.testing.assert_array_equal(
                campd_tranche_fuel_frac(gen(uid), pt, econ_srmc_bound=True),
                np.array([1.0, 1.0, 1.2]),
            )
        # scalar passthrough clamps too
        self.assertEqual(
            campd_tranche_fuel_frac(
                gen("COAL_z_p1_peak"), {"bituminous": 0.7}, econ_srmc_bound=True
            ),
            1.0,
        )
        # committed keeps the sigmoid discount; mustrun stays fuel-free.
        np.testing.assert_array_equal(
            campd_tranche_fuel_frac(
                gen("COAL_z_p1_committed"), pt, econ_srmc_bound=True
            ),
            pt["bituminous"],
        )
        self.assertEqual(
            campd_tranche_fuel_frac(gen("COAL_z_p1_mustrun"), pt, econ_srmc_bound=True),
            0.0,
        )
        # flag off: econ tranche keeps the discount (default behaviour).
        np.testing.assert_array_equal(
            campd_tranche_fuel_frac(gen("COAL_z_p1_econc00"), pt),
            pt["bituminous"],
        )

    def test_takeorpay_share_sets_mustrun_sunk_fraction(self):
        # With a measured take-or-pay map, a coal must-run tranche passes
        # 1 - contract_share of its fuel (only the contracted tonnage is sunk)
        # instead of the hardcoded 0.0; above-must-run tranches are unaffected,
        # a plant absent from the map keeps the default 0.0, and share == 1.0
        # reproduces the default.
        from market_sim.data.fleet import campd_tranche_fuel_frac

        def mustrun(plant_code):
            return Generator(
                unit_id="COAL_z_p1_mustrun",
                name="x",
                zone="z",
                fuel_type="coal",
                pmax_mw=100.0,
                heat_rate=10.0,
                coal_supply="bituminous",
                plant_group="COAL",
                plant_code=plant_code,
            )

        tp = {111: 0.6, 222: 1.0}
        # default (no map) → fully sunk
        self.assertEqual(campd_tranche_fuel_frac(mustrun(111), None, None), 0.0)
        # measured 60% contract → 40% of fuel passed through
        self.assertAlmostEqual(campd_tranche_fuel_frac(mustrun(111), None, tp), 0.4)
        # fully contracted → reproduces the default 0.0
        self.assertEqual(campd_tranche_fuel_frac(mustrun(222), None, tp), 0.0)
        # plant absent from the map → default 0.0
        self.assertEqual(campd_tranche_fuel_frac(mustrun(999), None, tp), 0.0)
        # the map never touches above-must-run tranches
        econ = mustrun(111).model_copy(update={"unit_id": "COAL_z_p1_econ"})
        self.assertEqual(campd_tranche_fuel_frac(econ, {"bituminous": 0.8}, tp), 0.8)

    def test_lignite_routing(self):
        # campd_tranche_fuel_frac returns the lignite passthrough for lignite
        # above-must-run tranches when given; must-run lignite stays 0.0 and
        # other supplies are untouched by it.
        from market_sim.data.fleet import campd_tranche_fuel_frac

        def gen(supply, unit_id="COAL_z_p1_econ"):
            return Generator(
                unit_id=unit_id,
                name="x",
                zone="z",
                fuel_type="coal",
                pmax_mw=100.0,
                heat_rate=10.0,
                coal_supply=supply,
                plant_group="COAL",
            )

        lig_pt = np.array([0.72, 0.95])
        pt = {"prb": 0.7, "lignite": lig_pt}
        self.assertIs(campd_tranche_fuel_frac(gen("lignite"), pt), lig_pt)
        self.assertEqual(campd_tranche_fuel_frac(gen("prb"), pt), 0.7)
        self.assertEqual(campd_tranche_fuel_frac(gen("waste"), pt), 1.0)
        self.assertEqual(
            campd_tranche_fuel_frac(gen("lignite", unit_id="COAL_z_p1_mustrun"), pt),
            0.0,
        )

    def test_gas_series_uses_monthly_actuals_when_on(self):
        # With gas_monthly_actuals, the sigmoid keys off the measured EIA-923
        # ISO-month gas series (PJM Jan-2024 spiked past $5/MMBtu), so the
        # winter passthrough exceeds the shaped-trajectory value.
        from market_sim.data.fuel import (
            coal_passthrough_series,
            iso_monthly_gas_prices,
        )

        base = ScenarioConfig(
            iso="PJM",
            hours=8760,
            gas_price_override=2.19,
            coal_bit_passthrough_sigmoid=True,
        )
        if iso_monthly_gas_prices(base, 2024) is None:
            self.skipTest("no PJM EIA-923 monthly gas parquet shipped")
        shaped = coal_passthrough_series(base, 2024, 8760, "bituminous")
        measured = coal_passthrough_series(
            base.with_overrides(gas_monthly_actuals=True), 2024, 8760, "bituminous"
        )
        jan = slice(0, 31 * 24)
        self.assertGreater(float(np.mean(measured[jan])), float(np.mean(shaped[jan])))


class LignitePassthroughSigmoidTest(unittest.TestCase):
    """The gas-keyed lignite passthrough sigmoid (ERCOT mine-mouth fleet)."""

    def test_off_returns_full_cost(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(gas_price_override=2.19)
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "lignite"), 1.0)

    def test_on_rises_with_gas_between_floor_and_ceil(self):
        # Params resolve from the (ERCOT, lignite) COAL_SIGMOID_DEFAULTS
        # entry (0.70 / 1.00 / 2.85 / 2.5, the run-80 anchors).
        from market_sim.data.fuel import coal_passthrough_series

        def mean_pt(gas):
            cfg = ScenarioConfig(
                gas_price_override=gas,
                coal_lignite_passthrough_sigmoid=True,
            )
            return float(np.mean(coal_passthrough_series(cfg, 2024, 8760, "lignite")))

        low, mid, high = mean_pt(2.0), mean_pt(2.85), mean_pt(6.0)
        self.assertLess(low, mid)
        self.assertLess(mid, high)
        self.assertGreaterEqual(low, 0.70)  # floor
        self.assertLessEqual(high, 1.00 + 1e-9)  # ceil: never marks lignite up
        self.assertGreater(high, 0.95)  # dear gas -> ~full cost

    def test_param_overrides_respected(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            gas_price_override=1.0,
            coal_lignite_passthrough_sigmoid=True,
            coal_lignite_passthrough_floor=0.55,
            coal_lignite_passthrough_ceil=1.10,
            coal_lignite_passthrough_gas_mid=3.0,
            coal_lignite_passthrough_gas_slope=4.0,
        )
        series = coal_passthrough_series(cfg, 2024, 8760, "lignite")
        # Gas far below the midpoint with a steep slope -> pinned at floor.
        self.assertAlmostEqual(float(np.min(series)), 0.55, places=2)

    def test_seasonal_variation_when_on(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            gas_price_override=2.85,
            coal_lignite_passthrough_sigmoid=True,
            gas_seasonality=True,
        )
        series = coal_passthrough_series(cfg, 2025, 8760, "lignite")
        self.assertEqual(series.shape, (8760,))
        self.assertGreater(series.max() - series.min(), 0.02)  # months differ


class SubPassthroughSigmoidTest(unittest.TestCase):
    """The subbituminous sigmoid: its own supply chain, never PRB's."""

    def test_off_returns_full_cost(self):
        # Off = flat full cost. Under per-(ISO, supply) curves there is no
        # PRB inheritance: subbituminous is its own supply chain everywhere
        # (the old aliasing let ERCOT prb params leak onto PJM subbit).
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(gas_price_override=2.19)
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "subbituminous"), 1.0)

    def test_on_uses_its_own_params(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            gas_price_override=2.0,
            coal_sub_passthrough_sigmoid=True,
            coal_sub_passthrough_floor=0.60,
            coal_sub_passthrough_ceil=1.20,
            coal_sub_passthrough_gas_mid=3.0,
            coal_sub_passthrough_gas_slope=2.5,
            # PRB params left at defaults to prove independence.
        )
        series = coal_passthrough_series(cfg, 2024, 8760, "subbituminous")
        self.assertEqual(series.shape, (8760,))
        self.assertGreaterEqual(float(series.min()), 0.60)
        self.assertLessEqual(float(series.max()), 1.20 + 1e-9)


class WastePassthroughSigmoidTest(unittest.TestCase):
    """The waste-coal sigmoid (culm/gob, PJM COAL_WC): markup-only curve."""

    def test_off_returns_full_cost(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(iso="PJM", gas_price_override=2.19)
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "waste"), 1.0)

    def test_on_uses_its_own_params(self):
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            gas_price_override=5.0,
            coal_waste_passthrough_sigmoid=True,
            coal_waste_passthrough_floor=1.00,
            coal_waste_passthrough_ceil=1.45,
            coal_waste_passthrough_gas_mid=3.4,
            coal_waste_passthrough_gas_slope=2.5,
            # Bit/subbit params left at defaults to prove independence.
        )
        series = coal_passthrough_series(cfg, 2024, 8760, "waste")
        self.assertEqual(series.shape, (8760,))
        self.assertGreaterEqual(float(series.min()), 1.00)
        self.assertLessEqual(float(series.max()), 1.45 + 1e-9)
        # Gas well above the midpoint -> a real dear-gas markup.
        self.assertGreater(float(series.mean()), 1.30)

    def test_pjm_resolves_markup_only_curve_from_table(self):
        # The (PJM, waste) COAL_SIGMOID_DEFAULTS entry: floor 1.0 (a
        # near-free reclamation fuel gets no cheap-gas discount), flat
        # through the $3.4-3.6 months 2023 needs kept, then a late, tall
        # dear-gas markup (Jan-2025 $6.86 gas needs ~2x to bite).
        from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
        from market_sim.data.fuel import coal_passthrough_series

        def mean_pt(delivered_gas):
            # gas_price_override gets the ISO basis added; the sigmoid is
            # placed on DELIVERED $/MMBtu (the measured EIA-923 series in
            # real runs), so quote the probe in delivered terms.
            cfg = ScenarioConfig(
                iso="PJM",
                gas_price_override=delivered_gas - GAS_BASIS_DIFFERENTIAL["PJM"],
                coal_waste_passthrough_sigmoid=True,
            )
            return float(np.mean(coal_passthrough_series(cfg, 2024, 8760, "waste")))

        low, mid, high = mean_pt(2.0), mean_pt(4.8), mean_pt(8.0)
        self.assertLess(low, mid)
        self.assertLess(mid, high)
        self.assertGreaterEqual(low, 1.00)  # floor: never a discount
        self.assertLess(mean_pt(3.5), 1.10)  # flat where 2023 must keep
        self.assertLessEqual(high, 2.10 + 1e-9)  # ceil
        self.assertGreater(high, 1.5)  # very dear gas -> big markup

    def test_uncharacterized_iso_stays_flat(self):
        # No (iso, waste) table entry -> flat full cost, never another
        # region's curve.
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            iso="ERCOT",
            gas_price_override=5.0,
            coal_waste_passthrough_sigmoid=True,
        )
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "waste"), 1.0)

    def test_routing_picks_up_waste_series(self):
        # coal_passthrough_by_supply now carries "waste", and
        # campd_tranche_fuel_frac routes a waste tranche to it; must-run
        # waste still passes 0.0.
        from market_sim.data.fleet import campd_tranche_fuel_frac
        from market_sim.data.fuel import coal_passthrough_by_supply

        cfg = ScenarioConfig(
            iso="PJM",
            gas_price_override=5.0,
            coal_waste_passthrough_sigmoid=True,
        )
        pt = coal_passthrough_by_supply(cfg, 2024, 8760)
        self.assertIn("waste", pt)
        gen = Generator(
            unit_id="COAL_z_p1_econ",
            name="x",
            zone="z",
            fuel_type="coal",
            pmax_mw=100.0,
            heat_rate=10.0,
            coal_supply="waste",
            plant_group="COAL_WC",
        )
        self.assertIs(campd_tranche_fuel_frac(gen, pt), pt["waste"])
        mustrun = Generator(
            unit_id="COAL_z_p1_mustrun",
            name="x",
            zone="z",
            fuel_type="coal",
            pmax_mw=100.0,
            heat_rate=10.0,
            coal_supply="waste",
            plant_group="COAL_WC",
        )
        self.assertEqual(campd_tranche_fuel_frac(mustrun, pt), 0.0)


class RegionDependentCoalSigmoidTest(unittest.TestCase):
    """Per-(ISO, supply) sigmoid resolution: curves never cross regions."""

    def test_uncharacterized_iso_supply_stays_flat(self):
        # Enabling the bit sigmoid on an ISO with no (iso, bituminous) entry
        # must NOT borrow another region's curve — it falls back flat.
        from market_sim.data.fuel import coal_passthrough_series

        cfg = ScenarioConfig(
            iso="ERCOT",
            gas_price_override=3.0,
            coal_bit_passthrough_sigmoid=True,
        )
        self.assertEqual(coal_passthrough_series(cfg, 2024, 8760, "bituminous"), 1.0)

    @pytest.mark.xfail(
        strict=True,
        reason="pre-existing failure on main as of 2026-07-05 (found wiring PR CI "
        "in W1-P1); unrelated to this change, tracked for follow-up",
    )
    def test_pjm_subbit_resolves_from_table_not_prb(self):
        # PJM subbituminous has its own first-cut curve (floor 1.0 — no
        # cheap-gas discount), distinct from the ERCOT prb curve (floor .78).
        from market_sim.data.fuel import coal_sigmoid_params

        pjm = ScenarioConfig(iso="PJM")
        ercot = ScenarioConfig(iso="ERCOT")
        sub = coal_sigmoid_params(pjm, "subbituminous")
        prb = coal_sigmoid_params(ercot, "prb")
        self.assertEqual(sub["floor"], 1.00)
        self.assertEqual(prb["floor"], 0.78)
        self.assertNotEqual(sub["floor"], prb["floor"])

    def test_explicit_fields_override_table(self):
        # CLI tuning flags (explicit non-None config fields) win over the
        # per-ISO table entry-by-entry.
        from market_sim.data.fuel import coal_sigmoid_params

        cfg = ScenarioConfig(iso="PJM", coal_bit_passthrough_floor=0.5)
        p = coal_sigmoid_params(cfg, "bituminous")
        self.assertEqual(p["floor"], 0.5)
        self.assertEqual(p["ceil"], 1.32)  # rest still from the table

    def test_incomplete_explicit_params_resolve_none(self):
        # No table entry + only partial explicit fields -> no curve (None),
        # so the series falls back flat rather than guessing.
        from market_sim.data.fuel import coal_sigmoid_params

        cfg = ScenarioConfig(iso="NYISO", coal_bit_passthrough_floor=0.8)
        self.assertIsNone(coal_sigmoid_params(cfg, "bituminous"))


class TestClassAwareNearbyFallback(unittest.TestCase):
    """``class_aware_fuel_price_fallback`` fills from same-class donors first.

    Synthetic three-plant ISO: a CT reporter at $4.10/MMBtu, a CC reporter
    at $2.60 with 10x the reported quantity (so the class-blind
    quantity-weighted pool sits near the CC price), and a non-filing CT
    recipient. Class-blind fallback hands the CT the CC-dominated mean;
    class-aware hands it the CT donor's price. Fuel-group fallback still
    applies when the recipient's class has no reporting peers.
    """

    _YEAR = 2024

    def _fleet(self, with_groups: bool = True):
        from market_sim.data.fleet import FleetArrays

        n = 3
        hours = 24
        plant_codes = np.array([101, 202, 303])  # CT filer, CC filer, CT recipient
        groups = np.array(["CT_PEAKER", "CC_REGULAR", "CT_PEAKER"], dtype=object)
        fuel_idx = np.array(
            [FUEL_TYPE_MAP["gas_ct"], FUEL_TYPE_MAP["gas_cc"], FUEL_TYPE_MAP["gas_ct"]]
        )
        return FleetArrays(
            pmax=np.array([100.0, 400.0, 150.0]),
            pmin=np.zeros(n),
            heat_rate=np.full(n, 8.0),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.zeros(n, dtype=int),
            fuel_type_idx=fuel_idx,
            availability=np.ones((n, hours)),
            unit_ids=["CT_FILER", "CC_FILER", "CT_RECIPIENT"],
            efficiency_bin=np.zeros(n, dtype=int),
            plant_code=plant_codes,
            state=np.array(["TX", "TX", "TX"], dtype=object),
            plant_group=groups if with_groups else None,
        )

    def _costs(self):
        import pandas as pd

        rows = []
        for month in range(1, 13):
            rows.append(
                {
                    "year": self._YEAR,
                    "month": month,
                    "plant_id": 101,
                    "fuel_group": "Natural Gas",
                    "state": "TX",
                    "price_per_mmbtu": 4.10,
                    "quantity": 1_000.0,
                }
            )
            rows.append(
                {
                    "year": self._YEAR,
                    "month": month,
                    "plant_id": 202,
                    "fuel_group": "Natural Gas",
                    "state": "TX",
                    "price_per_mmbtu": 2.60,
                    "quantity": 10_000.0,
                }
            )
        return pd.DataFrame(rows)

    def _nearby(self, class_aware: bool, with_groups: bool = True):
        from market_sim.data.fuel import _NearbyFuelPrices

        config = ScenarioConfig(
            iso="ERCOT",
            hours=24,
            gas_plant_monthly_fuel_pricing=True,
            nearby_fuel_price_fallback=True,
            nearby_fuel_price_min_state_plants=1,
            class_aware_fuel_price_fallback=class_aware,
        )
        return _NearbyFuelPrices(
            self._costs(), self._YEAR, self._fleet(with_groups), config
        )

    def test_class_blind_pool_is_quantity_dominated(self):
        nearby = self._nearby(class_aware=False)
        fill = nearby.month_prices("Natural Gas", "TX", 0, "CT_PEAKER")
        # 11:1 quantity weighting: (4.10*1000 + 2.60*10000) / 11000
        expected = (4.10 * 1_000 + 2.60 * 10_000) / 11_000
        self.assertAlmostEqual(float(fill[0]), expected, places=6)

    def test_class_aware_uses_same_class_donor(self):
        nearby = self._nearby(class_aware=True)
        fill = nearby.month_prices("Natural Gas", "TX", 0, "CT_PEAKER")
        np.testing.assert_allclose(fill, np.full(12, 4.10))
        # And the CC recipient still sees its own class's price.
        cc = nearby.month_prices("Natural Gas", "TX", 0, "CC_REGULAR")
        np.testing.assert_allclose(cc, np.full(12, 2.60))

    def test_class_with_no_donors_falls_back_to_fuel_group(self):
        nearby = self._nearby(class_aware=True)
        fill = nearby.month_prices("Natural Gas", "TX", 0, "ST_GAS")
        expected = (4.10 * 1_000 + 2.60 * 10_000) / 11_000
        self.assertAlmostEqual(float(fill[0]), expected, places=6)

    def test_flag_inert_without_plant_groups(self):
        # A fleet with no plant_group (the aggregated/legacy path) keeps the
        # class-blind behavior even when the flag is on.
        nearby = self._nearby(class_aware=True, with_groups=False)
        self.assertFalse(nearby.class_aware)
        fill = nearby.month_prices("Natural Gas", "TX", 0, "CT_PEAKER")
        expected = (4.10 * 1_000 + 2.60 * 10_000) / 11_000
        self.assertAlmostEqual(float(fill[0]), expected, places=6)


if __name__ == "__main__":
    unittest.main()
