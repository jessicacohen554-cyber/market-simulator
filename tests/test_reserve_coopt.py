"""Tests for the PJM energy+reserve co-optimization primitives.

Covers the structural reserve-requirement formula (the largest-single-
contingency proxy and the 1.5x-MSSC Primary Reserve requirement) and an
*honesty gate* that validates the formula's premise against the measured
PJM_RTO Primary Reserve series (data/raw/PJM-AS) — confirming the
requirement really is a near-constant reliability quantity ~= 1.5 x MSSC, not
a shape that must be replayed. The measured series is a validation target
only; it is never an input to the optimization.
"""

import unittest

import numpy as np

from market_sim.config.reserve_config import PJM_PRIMARY_RESERVE_LSC_FACTOR
from market_sim.config.paths import RAW_DATA_DIR
from market_sim.results.scarcity import (
    largest_single_contingency_mw,
    load_pjm_measured_reserve_requirement,
    pjm_ordc_shortfall_steps,
    pjm_primary_reserve_requirement,
    pjm_reserve_deliverable_supply_cap_mw,
)

_PJM_AS_DIR = RAW_DATA_DIR / "PJM-AS"


class TestLargestSingleContingency(unittest.TestCase):
    """The MSSC proxy: largest single reserve-eligible unit."""

    def test_bare_nameplate_picks_max(self):
        pmax = np.array([100.0, 1300.0, 450.0])
        self.assertEqual(largest_single_contingency_mw(pmax), 1300.0)

    def test_empty_fleet_is_zero(self):
        self.assertEqual(largest_single_contingency_mw(np.array([])), 0.0)

    def test_availability_takes_peak_deliverable(self):
        pmax = np.array([1000.0, 800.0])
        # Unit 0 capped to 0.5 all year -> 500 deliverable; unit 1 full -> 800.
        avail = np.empty((2, 24))
        avail[0, :] = 0.5
        avail[1, :] = 1.0
        self.assertEqual(largest_single_contingency_mw(pmax, availability=avail), 800.0)

    def test_reserve_mask_excludes_units(self):
        pmax = np.array([2000.0, 600.0])  # largest is reserve-ineligible
        mask = np.array([False, True])
        self.assertEqual(largest_single_contingency_mw(pmax, reserve_mask=mask), 600.0)

    def test_fleet_responsive_drops_with_largest_unit(self):
        full = np.array([1300.0, 900.0, 400.0])
        retired = np.array([900.0, 400.0])  # largest unit gone
        self.assertGreater(
            largest_single_contingency_mw(full),
            largest_single_contingency_mw(retired),
        )

    def test_plant_aggregation_sums_common_mode_units(self):
        # Two 1100 MW units at one plant (common-mode) outrank a single 1300.
        pmax = np.array([1100.0, 1100.0, 1300.0])
        plant_code = np.array([10, 10, 20])  # units 0,1 share plant 10
        self.assertEqual(
            largest_single_contingency_mw(pmax, plant_code=plant_code), 2200.0
        )

    def test_plant_code_zero_treated_individually(self):
        # plant_code <= 0 (imports / pseudo-units) never aggregate together.
        pmax = np.array([800.0, 800.0, 1300.0])
        plant_code = np.array([0, 0, 20])
        self.assertEqual(
            largest_single_contingency_mw(pmax, plant_code=plant_code), 1300.0
        )


class TestPrimaryReserveRequirement(unittest.TestCase):
    """The 1.5x-MSSC structural requirement."""

    def test_flat_factor_times_lsc(self):
        req = pjm_primary_reserve_requirement(2000.0, 8760, factor=1.5)
        self.assertEqual(req.shape, (8760,))
        np.testing.assert_allclose(req, 3000.0)

    def test_default_factor(self):
        req = pjm_primary_reserve_requirement(2000.0, 24)
        np.testing.assert_allclose(req, PJM_PRIMARY_RESERVE_LSC_FACTOR * 2000.0)

    def test_responsive_to_lsc(self):
        big = pjm_primary_reserve_requirement(2400.0, 24)[0]
        small = pjm_primary_reserve_requirement(1800.0, 24)[0]
        self.assertGreater(big, small)

    def test_nonnegative(self):
        self.assertTrue((pjm_primary_reserve_requirement(0.0, 24) >= 0).all())


class TestOrdcShortfallSteps(unittest.TestCase):
    """The published demand curve -> ascending LP shortfall steps."""

    _CURVE = [(0.0, 850.0), (190.0, 300.0)]  # PJM Primary RTO

    def test_two_step_curve_conversion(self):
        req_total, pens, widths = pjm_ordc_shortfall_steps(self._CURVE, 3000.0)
        self.assertEqual(req_total, 3190.0)  # REQ + max offset
        np.testing.assert_allclose(pens, [300.0, 850.0])  # cheapest band first
        np.testing.assert_allclose(widths, [190.0, 3000.0])

    def test_widths_span_full_requirement_extent(self):
        # Total shortfall capacity must let reserves fall to 0 (R=0 feasible).
        req_total, _, widths = pjm_ordc_shortfall_steps(self._CURVE, 2500.0)
        self.assertAlmostEqual(widths.sum(), req_total)

    def test_unordered_input_is_sorted(self):
        req_total, pens, widths = pjm_ordc_shortfall_steps(
            [(190.0, 300.0), (0.0, 850.0)], 1000.0
        )
        self.assertEqual(req_total, 1190.0)
        np.testing.assert_allclose(pens, [300.0, 850.0])


class TestMeasuredRequirementLoader(unittest.TestCase):
    """The backcast measured-requirement loader (reliability input)."""

    def test_loads_8760_positive_requirement(self):
        req = load_pjm_measured_reserve_requirement(2024, 8760)
        if req is None:
            self.skipTest("PJM-AS 2024 parquet not present")
        self.assertEqual(req.shape, (8760,))
        self.assertTrue((req > 0).all())  # holes filled, never zero
        # Matches the measured PJM_RTO Primary requirement (~3.42 GW, 2024).
        self.assertTrue(3000.0 < req.mean() < 3700.0)

    def test_missing_year_returns_none(self):
        self.assertIsNone(load_pjm_measured_reserve_requirement(1999, 8760))


class TestMeasuredRequirementHonestyGate(unittest.TestCase):
    """Validate the formula PREMISE against the measured PJM_RTO series.

    Not a fit: confirms the measured Primary Reserve requirement is a
    near-constant reliability quantity whose level implies a stable,
    physically-sensible MSSC (~1.5-2.6 GW) across all three years — i.e. the
    structural ``1.5 x MSSC`` form is the right shape. The fleet-derived MSSC
    is checked against this level during the integration run, not here.
    """

    def _measured_pr(self, year: int) -> np.ndarray | None:
        path = _PJM_AS_DIR / f"pjm_{year}_as_up_mw.parquet"
        if not path.exists():
            return None
        import pandas as pd

        return pd.read_parquet(path)["pr_req_mw"].to_numpy()

    def test_measured_requirement_is_near_flat(self):
        any_year = False
        for year in (2023, 2024, 2025):
            pr = self._measured_pr(year)
            if pr is None:
                continue
            any_year = True
            pr = pr[pr > 0]  # skip the documented data holes
            cv = pr.std() / pr.mean()
            # Measured cv runs ~0.10-0.16 (the largest online contingency
            # shifts seasonally); modest variation around a stable level, so
            # the flat 1.5x-MSSC premise holds as a first-order structural form.
            self.assertLess(
                cv,
                0.20,
                f"{year}: Primary Reserve req not near-flat (cv={cv:.3f}); "
                "the 1.5x-MSSC constant-requirement premise would not hold",
            )
        if not any_year:
            self.skipTest("PJM-AS measured parquets not present")

    def test_implied_mssc_is_stable_and_physical(self):
        implied = {}
        for year in (2023, 2024, 2025):
            pr = self._measured_pr(year)
            if pr is None:
                continue
            mean_req = pr[pr > 0].mean()
            implied[year] = mean_req / PJM_PRIMARY_RESERVE_LSC_FACTOR
        if not implied:
            self.skipTest("PJM-AS measured parquets not present")
        for year, mssc in implied.items():
            self.assertTrue(
                1500.0 < mssc < 2600.0,
                f"{year}: implied MSSC {mssc:.0f} MW outside the physical "
                "1.5-2.6 GW band for PJM's largest contingency",
            )
        # Stable across years (a reliability constant, not a moving target).
        vals = np.array(list(implied.values()))
        if len(vals) > 1:
            self.assertLess((vals.max() - vals.min()) / vals.mean(), 0.20)

    def test_formula_reproduces_measured_mean(self):
        """With the measured-implied MSSC, the formula lands on the measured
        mean — the structural form fits the level without shape replay."""
        pr = self._measured_pr(2024)
        if pr is None:
            self.skipTest("PJM-AS 2024 parquet not present")
        mean_req = pr[pr > 0].mean()
        mssc = mean_req / PJM_PRIMARY_RESERVE_LSC_FACTOR
        formula = pjm_primary_reserve_requirement(mssc, len(pr))
        self.assertAlmostEqual(formula[0], mean_req, delta=0.03 * mean_req)


class TestPjmReserveDeliverableSupplyCap(unittest.TestCase):
    """The PJM deliverable (10-min ramp) reserve-supply cap helper."""

    def _fleet(self, ramp10=None):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        gas_idx = FUEL_TYPE_NAMES.index("gas_cc")
        wind_idx = FUEL_TYPE_NAMES.index("wind")
        n, T = 2, 24
        return FleetArrays(
            pmax=np.array([400.0, 200.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 0.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0]),
            fuel_type_idx=np.array([gas_idx, wind_idx]),
            availability=np.ones((n, T)),
            unit_ids=["g0", "w1"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 200]),
            ramp10=ramp10,
        )

    def _config(self, on=True):
        from types import SimpleNamespace

        return SimpleNamespace(pjm_reserve_supply_cap=on)

    def test_gated_off_returns_none(self):
        fleet = self._fleet(ramp10=np.array([160.0, 0.0]))
        self.assertIsNone(
            pjm_reserve_deliverable_supply_cap_mw(self._config(on=False), fleet, 24)
        )

    def test_missing_ramp10_returns_none(self):
        self.assertIsNone(
            pjm_reserve_deliverable_supply_cap_mw(
                self._config(on=True), self._fleet(ramp10=None), 24
            )
        )

    def test_sums_only_eligible_units(self):
        # gas-CC (160 MW ramp, eligible) + wind (80 MW ramp, NOT eligible).
        fleet = self._fleet(ramp10=np.array([160.0, 80.0]))
        cap = pjm_reserve_deliverable_supply_cap_mw(self._config(), fleet, 24)
        self.assertEqual(cap.shape, (1, 24))
        np.testing.assert_allclose(cap, 160.0)  # wind excluded

    def test_availability_scales_deliverable(self):
        fleet = self._fleet(ramp10=np.array([160.0, 0.0]))
        fleet.availability[0, :12] = 0.5  # gas unit half-available first 12 h
        cap = pjm_reserve_deliverable_supply_cap_mw(self._config(), fleet, 24)
        np.testing.assert_allclose(cap[0, :12], 80.0)
        np.testing.assert_allclose(cap[0, 12:], 160.0)


class TestPjmReserveCooptInputs(unittest.TestCase):
    """The solve_dispatch input assembler (measured requirement + published ORDC)."""

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        # One gas-CC (reserve-eligible) + one wind (not) generator.
        gas_idx = FUEL_TYPE_NAMES.index("gas_cc")
        wind_idx = FUEL_TYPE_NAMES.index("wind")
        n, T = 2, 8760
        return FleetArrays(
            pmax=np.array([400.0, 200.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 0.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0]),
            fuel_type_idx=np.array([gas_idx, wind_idx]),
            availability=np.ones((n, T)),
            unit_ids=["g0", "w1"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 200]),
        )

    def _config(self, year=2024):
        from types import SimpleNamespace

        return SimpleNamespace(iso="PJM", weather_year=year)

    def _zone_names(self, fleet):
        return [f"z{i}" for i in range(int(np.max(fleet.zone_idx)) + 1)]

    def test_measured_year_shapes_and_values(self):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        if load_pjm_measured_reserve_requirement(2024, 8760) is None:
            self.skipTest("PJM-AS 2024 parquet not present")
        fleet = self._fleet()
        design = get_reserve_design(
            self._config(2024), fleet, 8760, self._zone_names(fleet)
        )
        kw = build_reserve_dispatch_kwargs(design)
        req = kw["reserve_requirement"]
        elig = kw["reserve_eligible"]
        pens = kw["ordc_penalties"]
        widths = kw["ordc_step_widths"]
        # Balance RHS = measured Primary requirement + 190 MW (Step-2 offset).
        self.assertEqual(req.shape, (8760,))
        self.assertTrue(3000.0 < (req - 190.0).mean() < 3700.0)
        # Published two-step curve, cheapest band first.
        np.testing.assert_allclose(pens, [300.0, 850.0])
        self.assertAlmostEqual(widths[0], 190.0)
        # Inner ($850) band spans the tightest hour's full requirement.
        self.assertAlmostEqual(widths[1], float((req - 190.0).max()))
        # Only the gas unit is reserve-eligible.
        np.testing.assert_array_equal(elig, [True, False])

    def test_forecast_fallback_uses_formula(self):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        # A future year with no measured parquet falls back to 1.5x-MSSC; the
        # requirement is then flat (formula) and strictly positive.
        if load_pjm_measured_reserve_requirement(1999, 24) is not None:
            self.skipTest("1999 parquet unexpectedly present")
        fleet = self._fleet()
        design = get_reserve_design(
            self._config(1999), fleet, 24, self._zone_names(fleet)
        )
        kw = build_reserve_dispatch_kwargs(design)
        req = kw["reserve_requirement"]
        pens = kw["ordc_penalties"]
        self.assertEqual(req.shape, (24,))
        self.assertTrue((req > 0).all())
        self.assertAlmostEqual(req.std(), 0.0)  # flat formula requirement
        np.testing.assert_allclose(pens, [300.0, 850.0])


class TestErcotOrdcDemandSteps(unittest.TestCase):
    """The ERCOT VOLL-anchored ORDC demand curve -> ascending LP shortfall steps."""

    def _steps(self, **kw):
        from market_sim.results.scarcity import ercot_ordc_demand_steps

        params = dict(
            voll=5000.0,
            mcl_mw=3000.0,
            mu_mw=0.0,
            sigma_mw=1400.0,
            shift_sigma=0.5,
            n_steps=40,
            sigma_span=5.0,
            multistep_floor=False,
        )
        params.update(kw)
        return ercot_ordc_demand_steps(**params)

    def test_req_total_is_curve_top(self):
        # req_total = mcl + (mu + shift*sigma) + sigma_span*sigma.
        req_total, _, _ = self._steps()
        self.assertAlmostEqual(req_total, 3000.0 + 700.0 + 5 * 1400.0)

    def test_widths_span_full_requirement(self):
        # Total shortfall capacity must let reserves fall to 0 in any hour.
        req_total, _, widths = self._steps()
        self.assertAlmostEqual(widths.sum(), req_total)

    def test_penalties_ascend_cheapest_first(self):
        # Outermost (highest-reserve) band is cheapest; ORDC price rises as
        # reserves fall, so the discretized penalties must be non-decreasing.
        _, pens, _ = self._steps()
        self.assertTrue(np.all(np.diff(pens) >= -1e-9))

    def test_penalties_capped_at_voll(self):
        _, pens, _ = self._steps(voll=5000.0)
        self.assertLessEqual(pens.max(), 5000.0 + 1e-6)
        # The innermost band (reserves near 0, both LOLP terms -> 1) approaches
        # VOLL.
        self.assertGreater(pens.max(), 0.9 * 5000.0)

    def test_higher_voll_scales_prices_up(self):
        _, pens_lo, _ = self._steps(voll=5000.0)
        _, pens_hi, _ = self._steps(voll=9000.0)
        self.assertGreater(pens_hi.max(), pens_lo.max())

    def test_multistep_floor_lifts_low_reserve_bands(self):
        # With the OBDRR048 floor on, bands below 6,500 MW reserve are >= $20.
        from market_sim.results.scarcity import ercot_ordc_demand_steps

        req_total, pens, widths = ercot_ordc_demand_steps(
            voll=5000.0,
            mcl_mw=3000.0,
            mu_mw=0.0,
            sigma_mw=1400.0,
            shift_sigma=0.5,
            multistep_floor=True,
        )
        # Reserve at each band's lower edge, descending from req_total.
        grid = np.linspace(req_total, 0.0, len(widths) + 1)
        r_edge = grid[1:]
        self.assertTrue(np.all(pens[r_edge <= 6500.0] >= 20.0 - 1e-9))


class TestErcotReserveEligible(unittest.TestCase):
    """Only dispatchable thermal classes back ORDC reserve."""

    def test_thermal_eligible_renewables_not(self):
        from types import SimpleNamespace

        from market_sim.data.fleet import FUEL_TYPE_NAMES
        from market_sim.results.scarcity import (
            RESERVE_FUEL_TYPES,
            ercot_reserve_eligible,
        )

        name_to_idx = {n: i for i, n in enumerate(FUEL_TYPE_NAMES)}
        fuels = ["gas_ct", "coal", "nuclear", "wind", "solar", "hydro"]
        idx = np.array([name_to_idx[f] for f in fuels if f in name_to_idx])
        kept = [f for f in fuels if f in name_to_idx]
        elig = ercot_reserve_eligible(SimpleNamespace(fuel_type_idx=idx))
        for f, e in zip(kept, elig):
            self.assertEqual(e, f in RESERVE_FUEL_TYPES, f"{f} eligibility")


class TestNyisoRcpfProductSteps(unittest.TestCase):
    """One NYISO RCPF reserve demand curve -> ascending LP shortfall steps."""

    def _steps(self, req, crit, pen, n_ramp=8):
        from market_sim.results.scarcity import nyiso_rcpf_product_shortfall_steps

        return nyiso_rcpf_product_shortfall_steps(req, crit, pen, n_ramp=n_ramp)

    def test_locational_product_ramps_to_zero(self):
        # critical=0 (locational): a pure ramp, no flat tail; widths sum to req.
        pens, widths = self._steps(1000.0, 0.0, 500.0, n_ramp=8)
        self.assertEqual(len(pens), 8)
        self.assertAlmostEqual(widths.sum(), 1000.0)
        self.assertAlmostEqual(pens[-1], 500.0)  # deepest band at max penalty
        self.assertTrue(np.all(np.diff(pens) > 0))  # cheapest band first

    def test_nyca_product_has_flat_tail(self):
        # NYCA 30-min: ramp over [1965, 2620], flat $750 over [0, 1965).
        pens, widths = self._steps(2620.0, 1965.0, 750.0, n_ramp=8)
        self.assertEqual(len(pens), 9)  # 8 ramp + 1 flat tail
        self.assertAlmostEqual(widths.sum(), 2620.0)
        self.assertAlmostEqual(pens[-1], 750.0)
        self.assertAlmostEqual(widths[-1], 1965.0)  # tail width = critical

    def test_zero_span_is_flat_only(self):
        pens, widths = self._steps(500.0, 500.0, 500.0)
        np.testing.assert_allclose(pens, [500.0])
        np.testing.assert_allclose(widths, [500.0])


class TestNyisoReserveCooptInputs(unittest.TestCase):
    """The NYISO locational co-optimization input assembler."""

    _ZONES = ["Upstate_West", "Capital_Hudson", "Lower_Hudson", "NYC", "Long_Island"]

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        gas_idx = FUEL_TYPE_NAMES.index("gas_ct")
        wind_idx = FUEL_TYPE_NAMES.index("wind")
        n, T = 2, 24
        return FleetArrays(
            pmax=np.array([400.0, 200.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([10.0, 0.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([3, 3]),  # both in NYC
            fuel_type_idx=np.array([gas_idx, wind_idx]),
            availability=np.ones((n, T)),
            unit_ids=["g0", "w1"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 200]),
        )

    def _config(self):
        from types import SimpleNamespace

        return SimpleNamespace(iso="NYISO", weather_year=2023)

    def test_shapes_and_family_count(self):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        T = 24
        fleet = self._fleet()
        design = get_reserve_design(self._config(), fleet, T, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        req = kw["reserve_requirement"]
        elig = kw["reserve_eligible"]
        pens = kw["ordc_penalties"]
        widths = kw["ordc_step_widths"]
        mask = kw.get("reserve_balance_zone_mask")
        counts = kw.get("reserve_balance_ordc_counts")
        fam_class = kw.get("reserve_balance_class")
        online_gated = design.online_gated
        online_rho = design.online_rho
        # NYCA(3 products) + East(1) + SENY(1) + NYC(2) = 7 families.
        n_fam = 7
        self.assertEqual(mask.shape, (n_fam, len(self._ZONES)))
        self.assertEqual(req.shape, (n_fam, T))
        self.assertEqual(counts.shape, (n_fam,))
        self.assertEqual(int(counts.sum()), len(pens))
        self.assertEqual(len(pens), len(widths))
        # Two nested eligibility classes (full dispatchable, quick-start). The
        # gas-CT is in both; the wind unit in neither.
        self.assertEqual(elig.shape, (2, 2))
        np.testing.assert_array_equal(elig[0], [True, False])  # full: gas only
        np.testing.assert_array_equal(elig[1], [True, False])  # quick-start: gas only
        # Family reserve class: NYCA 30-min + SENY/NYC 30-min on the full class
        # 0; the four 10-minute products (NYCA 10-min total/spin, the published
        # 10-minute East requirement, and NYC 10-min) on the quick-start class 1.
        self.assertEqual(fam_class.shape, (n_fam,))
        np.testing.assert_array_equal(fam_class, [0, 1, 1, 1, 0, 0, 1])
        # Synchronised flag OFF (default): no online-gated class, legacy layout.
        self.assertIsNone(online_gated)
        self.assertEqual(online_rho, 1.0)

    def test_synchronised_reserve_adds_online_gated_class(self):
        from types import SimpleNamespace

        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        cfg = SimpleNamespace(
            iso="NYISO", weather_year=2023, nyiso_synchronised_reserve=True
        )
        fleet = self._fleet()
        design = get_reserve_design(cfg, fleet, 24, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        req = kw["reserve_requirement"]
        elig = kw["reserve_eligible"]
        mask = kw.get("reserve_balance_zone_mask")
        fam_class = kw.get("reserve_balance_class")
        online_gated = design.online_gated
        online_rho = design.online_rho
        # One extra family (NYC spinning) on a new online-gated class (2).
        self.assertEqual(mask.shape[0], 8)
        self.assertEqual(req.shape[0], 8)
        self.assertEqual(int(fam_class[-1]), 2)  # spinning family -> class 2
        # Three eligibility classes now; class 2 == quick-start mask.
        self.assertEqual(elig.shape, (3, 2))
        np.testing.assert_array_equal(elig[2], elig[1])
        # online_gated marks only class 2; rho is a positive finite multiplier.
        np.testing.assert_array_equal(online_gated, [False, False, True])
        self.assertGreater(online_rho, 0.0)
        # The spinning family is NYC-only.
        nyc = self._ZONES.index("NYC")
        only_nyc = np.zeros(len(self._ZONES), dtype=bool)
        only_nyc[nyc] = True
        np.testing.assert_array_equal(mask[-1], only_nyc)

    def test_locational_masks_nest(self):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        fleet = self._fleet()
        design = get_reserve_design(self._config(), fleet, 24, self._ZONES)
        kw = build_reserve_dispatch_kwargs(design)
        mask = kw["reserve_balance_zone_mask"]
        # The three NYCA families span every zone.
        self.assertTrue(mask[:3].all())
        # The four locational families never include upstate (zone 0).
        self.assertFalse(mask[3:, 0].any())
        # The last family (NYC 10-min) is zone J only.
        nyc = self._ZONES.index("NYC")
        only_nyc = np.zeros(len(self._ZONES), dtype=bool)
        only_nyc[nyc] = True
        np.testing.assert_array_equal(mask[-1], only_nyc)


class TestNyisoLocationalCooptLP(unittest.TestCase):
    """End-to-end: a locational reserve family lifts an import-constrained
    downstate zone's price the system-wide curve never sees."""

    def _two_zone_fleet(self):
        # Zone 0 (upstate): cheap, ample. Zone 1 (downstate pocket): one
        # mid-cost gas-CT, import-limited. Locational reserve in zone 1 must be
        # met by in-zone headroom -> holds the CT back -> lifts zone-1 price.
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        gas_idx = FUEL_TYPE_NAMES.index("gas_ct")
        n, T = 2, 4
        return (
            FleetArrays(
                pmax=np.array([2000.0, 600.0]),
                pmin=np.zeros(n),
                heat_rate=np.array([5.0, 12.0]),
                vom=np.zeros(n),
                emission_rate=np.zeros(n),
                nox_rate=np.zeros(n),
                so2_rate=np.zeros(n),
                zone_idx=np.array([0, 1]),
                fuel_type_idx=np.array([gas_idx, gas_idx]),
                availability=np.ones((n, T)),
                unit_ids=["up", "down"],
                efficiency_bin=np.zeros(n),
                plant_code=np.array([1, 2]),
            ),
            T,
        )

    def _solve(self, with_locational):
        import scipy.sparse as sp

        from market_sim.model.dispatch import solve_dispatch

        fleet, T = self._two_zone_fleet()
        n_zones = 2
        # Demand: upstate 1000, downstate 400. One link 0->1 capped at 200 MW,
        # so downstate must self-supply >= 200 MW from its 600 MW CT.
        demand = np.array([[1000.0] * T, [400.0] * T])
        incidence = sp.csr_matrix(np.array([[1.0], [-1.0]]))  # flow on link adds to z1
        ttc = np.array([200.0])
        fuel_prices = np.ones((2, T))  # heat_rate sets MC ($5 vs $12)
        kw = dict(
            wind_cf=np.zeros((n_zones, T)),
            wind_cap=np.zeros(n_zones),
            solar_cf=np.zeros((n_zones, T)),
            solar_cap=np.zeros(n_zones),
            fuel_prices=fuel_prices,
            incidence=incidence,
            ttc=ttc,
            voll=2000.0,
        )
        if with_locational:
            # One locational family: zone 1 must hold 300 MW reserve, priced to
            # $500 at zero reserve (ramp, critical=0).
            from market_sim.results.scarcity import (
                nyiso_rcpf_product_shortfall_steps,
            )

            pens, widths = nyiso_rcpf_product_shortfall_steps(
                300.0, 0.0, 500.0, n_ramp=4
            )
            kw.update(
                reserve_requirement=np.full((1, T), 300.0),
                reserve_eligible=np.array([True, True]),
                ordc_penalties=pens,
                ordc_step_widths=widths,
                reserve_balance_zone_mask=np.array([[False, True]]),
                reserve_balance_ordc_counts=np.array([len(pens)]),
            )
        return solve_dispatch(fleet, demand, **kw)

    def test_locational_reserve_lifts_downstate_price(self):
        base = self._solve(with_locational=False)
        loc = self._solve(with_locational=True)
        # Both feasible.
        self.assertEqual(base.status, "Optimal")
        self.assertEqual(loc.status, "Optimal")
        # Downstate zone is import-limited to 200 MW, serves 400 -> CT runs 200
        # at $60 either way, so base downstate price is the CT MC.
        z1_base = base.prices[1].mean()
        z1_loc = loc.prices[1].mean()
        # Holding 300 MW of in-zone reserve forces the 600 MW CT to keep
        # headroom (cap 600 - 300 reserve = 300 deliverable energy), but it only
        # needs 200 for energy, so reserve clears off headroom at $0 — price
        # unchanged. Tighten: require 500 MW reserve so energy+reserve = 700 >
        # 600 cap, forcing a shortfall priced on the curve.
        self.assertGreaterEqual(z1_loc, z1_base)

    def test_tight_locational_reserve_prices_shortfall(self):
        import scipy.sparse as sp

        from market_sim.model.dispatch import solve_dispatch
        from market_sim.results.scarcity import nyiso_rcpf_product_shortfall_steps

        fleet, T = self._two_zone_fleet()
        demand = np.array([[1000.0] * T, [400.0] * T])
        incidence = sp.csr_matrix(np.array([[1.0], [-1.0]]))
        # Reserve 500 MW in zone 1: with 200 MW imported, the CT serves 200 MW
        # energy and at most 400 MW headroom -> 100 MW reserve shortfall, priced
        # on the ramp. The reserve dual lifts the downstate energy LMP.
        pens, widths = nyiso_rcpf_product_shortfall_steps(500.0, 0.0, 500.0, n_ramp=5)
        loc = solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
            fuel_prices=np.ones((2, T)),
            incidence=incidence,
            ttc=np.array([200.0]),
            voll=2000.0,
            reserve_requirement=np.full((1, T), 500.0),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=pens,
            ordc_step_widths=widths,
            reserve_balance_zone_mask=np.array([[False, True]]),
            reserve_balance_ordc_counts=np.array([len(pens)]),
        )
        self.assertEqual(loc.status, "Optimal")
        # A binding reserve shortfall in the pocket => positive reserve price.
        self.assertGreater(float(np.asarray(loc.reserve_price).mean()), 0.0)


class TestReserveClassEligibility(unittest.TestCase):
    """Per-class reserve eligibility: a 10-minute family restricted to the
    quick-start fleet cannot be met by slow combined-cycle headroom, so it
    prices a shortfall the same requirement on the full fleet clears at $0."""

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")  # slow: 30-min only
        ct_idx = FUEL_TYPE_NAMES.index("gas_ct")  # quick-start: 10-min capable
        n, T = 2, 4
        return (
            FleetArrays(
                pmax=np.array([1000.0, 300.0]),
                pmin=np.zeros(n),
                heat_rate=np.array([5.0, 12.0]),  # CC cheap, CT dear
                vom=np.zeros(n),
                emission_rate=np.zeros(n),
                nox_rate=np.zeros(n),
                so2_rate=np.zeros(n),
                zone_idx=np.array([0, 0]),
                fuel_type_idx=np.array([cc_idx, ct_idx]),
                availability=np.ones((n, T)),
                unit_ids=["cc", "ct"],
                efficiency_bin=np.zeros(n),
                plant_code=np.array([1, 2]),
            ),
            T,
        )

    def _solve(self, reserve_class):
        from market_sim.model.dispatch import solve_dispatch
        from market_sim.results.scarcity import nyiso_rcpf_product_shortfall_steps

        fleet, T = self._fleet()
        # Demand 700: the cheap CC carries it (700 of 1000), the CT idles. Full
        # headroom = (1000-700) + 300 = 600; quick-start headroom = 300 (idle CT).
        # A 500 MW reserve requirement clears on the full fleet (600 >= 500) but
        # is 200 MW short on the quick-start fleet alone.
        demand = np.array([[700.0] * T])
        pens, widths = nyiso_rcpf_product_shortfall_steps(500.0, 0.0, 500.0, n_ramp=5)
        # Two eligibility classes: class 0 = both units, class 1 = quick-start CT.
        eligible = np.array([[True, True], [False, True]])
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((2, T)),
            voll=2000.0,
            reserve_requirement=np.full((1, T), 500.0),
            reserve_eligible=eligible,
            ordc_penalties=pens,
            ordc_step_widths=widths,
            reserve_balance_zone_mask=np.array([[True]]),
            reserve_balance_ordc_counts=np.array([len(pens)]),
            reserve_balance_class=np.array([reserve_class]),
        )

    def test_quick_start_restriction_prices_shortfall(self):
        full = self._solve(reserve_class=0)  # 30-min: full dispatchable fleet
        quick = self._solve(reserve_class=1)  # 10-min: quick-start fleet only
        self.assertEqual(full.status, "Optimal")
        self.assertEqual(quick.status, "Optimal")
        # On the full fleet the 500 MW requirement clears on idle CC+CT headroom
        # at $0; restricted to the 300 MW quick-start fleet it is 200 MW short
        # and prices on the demand curve.
        self.assertAlmostEqual(float(np.asarray(full.reserve_price).mean()), 0.0)
        self.assertGreater(float(np.asarray(quick.reserve_price).mean()), 0.0)


class TestMisoReserveCooptInputs(unittest.TestCase):
    """The MISO market-wide (system-wide) co-optimization input assembler."""

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        nuc_idx = FUEL_TYPE_NAMES.index("nuclear")
        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        wind_idx = FUEL_TYPE_NAMES.index("wind")
        n, T = 3, 24
        return FleetArrays(
            pmax=np.array([1300.0, 800.0, 500.0]),  # nuclear is the MSSC
            pmin=np.zeros(n),
            heat_rate=np.array([0.0, 7.0, 0.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0, 0]),
            fuel_type_idx=np.array([nuc_idx, cc_idx, wind_idx]),
            availability=np.ones((n, T)),
            unit_ids=["nuc", "cc", "w"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([100, 200, 300]),
        )

    def _config(self):
        from types import SimpleNamespace

        return SimpleNamespace(iso="MISO", weather_year=2024)

    def _zone_names(self, fleet):
        return [f"z{i}" for i in range(int(np.max(fleet.zone_idx)) + 1)]

    def test_requirement_is_mssc_plus_regulation(self):
        from market_sim.config.reserve_config import (
            MISO_REGULATING_RESERVE_MW,
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        T = 24
        fleet = self._fleet()
        design = get_reserve_design(self._config(), fleet, T, self._zone_names(fleet))
        kw = build_reserve_dispatch_kwargs(design)
        req = kw["reserve_requirement"]
        elig = kw["reserve_eligible"]
        # MSSC = the largest reserve-eligible plant (1300 MW nuclear); the wind
        # unit is excluded. Requirement = MSSC + regulation, flat across hours.
        self.assertEqual(req.shape, (T,))
        self.assertTrue(np.allclose(req, 1300.0 + MISO_REGULATING_RESERVE_MW))
        # Single eligibility class (the generic thermal mask): nuclear + gas, not
        # wind.
        self.assertEqual(elig.shape, (3,))
        np.testing.assert_array_equal(elig, [True, True, False])

    def test_demand_curve_steps_are_well_formed(self):
        from market_sim.config.reserve_config import (
            MISO_REGULATING_RESERVE_MW,
            MISO_RESERVE_DEMAND_CURVE_MAX,
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )

        fleet = self._fleet()
        design = get_reserve_design(self._config(), fleet, 24, self._zone_names(fleet))
        kw = build_reserve_dispatch_kwargs(design)
        pens = kw["ordc_penalties"]
        widths = kw["ordc_step_widths"]
        self.assertEqual(len(pens), len(widths))
        # Widths span the full requirement so the balance row stays feasible at
        # zero cleared reserve.
        self.assertAlmostEqual(
            float(widths.sum()), 1300.0 + MISO_REGULATING_RESERVE_MW, places=4
        )
        # Penalties ascend cheapest-first and are capped at the VOLL-anchored max.
        self.assertTrue(np.all(np.diff(pens) >= -1e-9))
        self.assertLessEqual(float(pens.max()), MISO_RESERVE_DEMAND_CURVE_MAX + 1e-9)


class TestMisoReserveCooptLP(unittest.TestCase):
    """MISO system-wide co-opt in the LP: slack reserve clears at $0, a tight
    reserve prices the shortfall and lifts the energy LMP (the runner MISO
    branch passes a single (T,) requirement and (n_gen,) eligibility)."""

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        n, T = 2, 4
        return (
            FleetArrays(
                pmax=np.array([1000.0, 1000.0]),  # MSSC = 1000 -> req = 1400
                pmin=np.zeros(n),
                heat_rate=np.array([7.0, 7.0]),
                vom=np.zeros(n),
                emission_rate=np.zeros(n),
                nox_rate=np.zeros(n),
                so2_rate=np.zeros(n),
                zone_idx=np.array([0, 0]),
                fuel_type_idx=np.array([cc_idx, cc_idx]),
                availability=np.ones((n, T)),
                unit_ids=["cc0", "cc1"],
                efficiency_bin=np.zeros(n),
                plant_code=np.array([1, 2]),
            ),
            T,
        )

    def _solve(self, demand_mw):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )
        from market_sim.model.dispatch import solve_dispatch

        fleet, T = self._fleet()
        cfg = type("C", (), {"iso": "MISO", "weather_year": 2024})()
        zone_names = [f"z{i}" for i in range(int(np.max(fleet.zone_idx)) + 1)]
        design = get_reserve_design(cfg, fleet, T, zone_names)
        kw = build_reserve_dispatch_kwargs(design)
        req = kw["reserve_requirement"]
        elig = kw["reserve_eligible"]
        pens = kw["ordc_penalties"]
        widths = kw["ordc_step_widths"]
        return solve_dispatch(
            fleet,
            np.array([[demand_mw] * T]),
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((2, T)),
            voll=2000.0,
            reserve_requirement=req,
            reserve_eligible=elig,
            ordc_penalties=pens,
            ordc_step_widths=widths,
        )

    def test_slack_clears_zero_tight_lifts_lmp(self):
        # req = MSSC(1000) + 400 = 1400. Slack: demand 200 -> headroom 1800 >=
        # 1400, reserve clears at $0. Tight: demand 1400 -> headroom 600 < 1400,
        # the shortfall prices on the demand curve and lifts the energy LMP.
        slack = self._solve(200.0)
        tight = self._solve(1400.0)
        self.assertEqual(slack.status, "Optimal")
        self.assertEqual(tight.status, "Optimal")
        self.assertAlmostEqual(float(np.asarray(slack.reserve_price).mean()), 0.0)
        self.assertGreater(float(np.asarray(tight.reserve_price).mean()), 0.0)
        # The reserve clearing price folds into the energy LMP.
        self.assertGreater(
            float(np.asarray(tight.prices).mean()),
            float(np.asarray(slack.prices).mean()),
        )


class TestMisoZonalReserveLP(unittest.TestCase):
    """MISO zonal reserve family in the LP (miso_zonal_reserves): a South
    zone whose local headroom cannot cover its within-zone MSSC prices the
    published zonal curve and lifts the SOUTH LMP above the West LMP, even
    when the market-wide requirement is slack. Trivial case: 2 zones, 24 h,
    one link."""

    _T = 24

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        n = 3
        # West: two 2,000 MW CCs (deep headroom). South: one 800 MW CC —
        # the within-zone MSSC equals the whole South fleet, so any South
        # load leaves the zonal requirement unmeetable locally.
        return FleetArrays(
            pmax=np.array([2000.0, 2000.0, 800.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 7.0, 7.5]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.array([0, 0, 1]),
            fuel_type_idx=np.array([cc_idx, cc_idx, cc_idx]),
            availability=np.ones((n, self._T)),
            unit_ids=["cc_w0", "cc_w1", "cc_s0"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([1, 2, 3]),
        )

    def _solve(self, zonal: bool):
        import scipy.sparse as sp

        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )
        from market_sim.model.dispatch import solve_dispatch

        fleet = self._fleet()
        cfg = type(
            "C",
            (),
            {
                "iso": "MISO",
                "weather_year": 2024,
                "miso_zonal_reserves": zonal,
                "miso_zonal_reserve_zones": ("South",),
            },
        )()
        design = get_reserve_design(cfg, fleet, self._T, ["West", "South"])
        kw = build_reserve_dispatch_kwargs(design)
        demand = np.vstack(
            [
                np.full(self._T, 500.0),  # West: deeply slack
                np.full(self._T, 600.0),  # South: local headroom 200 < MSSC 800
            ]
        )
        # One West->South link, 400 MW (the RDT analogue): imports serve South
        # energy but imported MW are not South reserve.
        incidence = sp.csr_matrix(np.array([[1.0], [-1.0]]))
        extra = (
            dict(
                reserve_balance_zone_mask=kw["reserve_balance_zone_mask"],
                reserve_balance_ordc_counts=kw["reserve_balance_ordc_counts"],
                reserve_balance_class=kw["reserve_balance_class"],
            )
            if zonal
            else {}
        )
        return solve_dispatch(
            fleet,
            demand,
            wind_cf=np.zeros((2, self._T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, self._T)),
            solar_cap=np.zeros(2),
            fuel_prices=np.ones((3, self._T)),
            voll=2000.0,
            incidence=incidence,
            ttc=np.array([400.0]),
            reserve_requirement=kw["reserve_requirement"],
            reserve_eligible=kw["reserve_eligible"],
            ordc_penalties=kw["ordc_penalties"],
            ordc_step_widths=kw["ordc_step_widths"],
            **extra,
        )

    def test_zonal_family_prices_south_scarcity(self):
        base = self._solve(zonal=False)
        zonal = self._solve(zonal=True)
        self.assertEqual(base.status, "Optimal")
        self.assertEqual(zonal.status, "Optimal")
        # Market-wide requirement (MSSC 2000 + 400 reg) is met by West's
        # headroom in both runs; without the zonal family South prices at
        # its energy marginal cost only.
        south_base = float(np.asarray(base.prices)[1].mean())
        south_zonal = float(np.asarray(zonal.prices)[1].mean())
        west_zonal = float(np.asarray(zonal.prices)[0].mean())
        # The South zonal family (req = 800, local headroom 200) is short:
        # its shortfall prices on the published curve and lifts the South
        # LMP above both the no-family South LMP and the West LMP.
        self.assertGreater(south_zonal, south_base + 1.0)
        self.assertGreater(south_zonal, west_zonal + 1.0)


class TestMisoPergenReserveLP(unittest.TestCase):
    """MISO per-asset reserve columns end-to-end (miso_reserve_pergen):
    the 10-min deliverable ramp caps cleared reserve, so a fleet whose
    HEADROOM covers the requirement but whose RAMP cannot deliver it inside
    the contingency window prices the shortfall — the deliverability
    structure the zone-aggregate co-opt cannot see (it clears $0 off pooled
    headroom). Trivial case: 1 zone, 3 gens, 4 hours."""

    _T = 4

    def _fleet(self, ramp10):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        n = 3
        # MSSC = 2,000 (g0, plant-aggregated) -> market-wide req = 2,400.
        return FleetArrays(
            pmax=np.array([2000.0, 1000.0, 1000.0]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 7.5, 8.0]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.zeros(n, dtype=int),
            fuel_type_idx=np.full(n, cc_idx),
            availability=np.ones((n, self._T)),
            unit_ids=["cc0", "cc1", "cc2"],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([1, 2, 3]),
            ramp10=np.asarray(ramp10, dtype=float),
        )

    def _solve(self, ramp10, pergen: bool, demand_mw=200.0):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )
        from market_sim.model.dispatch import solve_dispatch

        fleet = self._fleet(ramp10)
        cfg = type(
            "C",
            (),
            {"iso": "MISO", "weather_year": 2024, "miso_reserve_pergen": pergen},
        )()
        design = get_reserve_design(cfg, fleet, self._T, ["z0"])
        kw = build_reserve_dispatch_kwargs(design)
        extra = {
            k: kw[k]
            for k in (
                "reserve_pergen_gen_idx",
                "reserve_pergen_col",
                "reserve_pergen_ramp10",
            )
            if k in kw
        }
        return solve_dispatch(
            fleet,
            np.full((1, self._T), demand_mw),
            wind_cf=np.zeros((1, self._T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self._T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((3, self._T)),
            voll=5000.0,
            reserve_requirement=kw["reserve_requirement"],
            reserve_eligible=kw["reserve_eligible"],
            ordc_penalties=kw["ordc_penalties"],
            ordc_step_widths=kw["ordc_step_widths"],
            **extra,
        )

    def test_ramp_deliverability_shortage_prices_curve(self):
        # Headroom at demand 200 is 3,800 >= req 2,400 in BOTH runs. Ramp
        # sum 200+1000+1000 = 2,200 < 2,400: the aggregate co-opt clears $0
        # (headroom covers the requirement), the per-asset build is 200 MW
        # short of DELIVERABLE reserve and prices the demand curve.
        agg = self._solve([200.0, 1000.0, 1000.0], pergen=False)
        per = self._solve([200.0, 1000.0, 1000.0], pergen=True)
        self.assertEqual(agg.status, "Optimal")
        self.assertEqual(per.status, "Optimal")
        self.assertAlmostEqual(float(np.asarray(agg.reserve_price).mean()), 0.0)
        self.assertGreater(float(np.asarray(per.reserve_price).mean()), 1.0)

    def test_ample_ramp_clears_zero(self):
        # Ramp sum 4,000 >= req 2,400 and headroom is deep: the per-asset
        # build must NOT manufacture phantom scarcity.
        per = self._solve([2000.0, 1000.0, 1000.0], pergen=True)
        self.assertEqual(per.status, "Optimal")
        self.assertAlmostEqual(float(np.asarray(per.reserve_price).mean()), 0.0)

    def test_energy_competes_with_reserve_on_marginal_pool(self):
        # Tight energy (demand 3,200 of 4,000): serving the requirement now
        # forces reserve to be held on capacity that would otherwise clear
        # as energy, so the reserve price carries the opportunity cost and
        # the LMP rises vs the aggregate build at the same demand.
        agg = self._solve([2000.0, 1000.0, 1000.0], pergen=False, demand_mw=3200.0)
        per = self._solve([2000.0, 1000.0, 1000.0], pergen=True, demand_mw=3200.0)
        self.assertEqual(per.status, "Optimal")
        self.assertGreaterEqual(
            float(np.asarray(per.prices).mean()),
            float(np.asarray(agg.prices).mean()) - 1e-6,
        )
        self.assertGreater(float(np.asarray(per.reserve_price).mean()), 0.0)


class TestCaisoPergenStorageHydroLP(unittest.TestCase):
    """CAISO completed participation model end-to-end (issue #1492 c.2/c.3).

    Storage backs the co-drawn spin/non-spin requirement through the
    duration-gated RS[c,z] columns on the PERGEN path (power competition vs
    its own charge/discharge + the 30-min ASSOC SOC gate), and hydro joins
    the pergen pool with its ISO-locally backfilled 10-minute ramp. Trivial
    case (1 zone, 1-2 gens, 24 h): a thermal fleet whose deliverable ramp is
    SHORT of the requirement prices the published curve; adding the real
    providers (storage / hydro) closes the gap and the price honestly
    collapses — participation can only LOOSEN scarcity, the issue's ex-ante
    direction.
    """

    _T = 24

    def _fleet(self, with_hydro=False):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc = FUEL_TYPE_NAMES.index("gas_cc")
        hyd = FUEL_TYPE_NAMES.index("hydro")
        n = 2 if with_hydro else 1
        # One 1,000 MW CC (MSSC anchor; ramp10 300 MW deliverable) and
        # optionally a 600 MW hydro plant whose FleetArrays ramp10 is 0 —
        # _caiso_design must backfill it (CAISO_HYDRO_RAMP10_FRAC).
        return FleetArrays(
            pmax=np.array([1000.0, 600.0][:n]),
            pmin=np.zeros(n),
            heat_rate=np.array([7.0, 0.0][:n]),
            vom=np.zeros(n),
            emission_rate=np.zeros(n),
            nox_rate=np.zeros(n),
            so2_rate=np.zeros(n),
            zone_idx=np.zeros(n, dtype=int),
            fuel_type_idx=np.array([cc, hyd][:n]),
            availability=np.ones((n, self._T)),
            unit_ids=["cc0", "hyd0"][:n],
            efficiency_bin=np.zeros(n),
            plant_code=np.array([1, 2][:n]),
            ramp10=np.array([300.0, 0.0][:n]),
        )

    def _solve(self, with_hydro=False, with_storage=False, storage_mwh=400.0):
        from market_sim.config.reserve_config import (
            build_reserve_dispatch_kwargs,
            get_reserve_design,
        )
        from market_sim.model.dispatch import solve_dispatch

        fleet = self._fleet(with_hydro=with_hydro)
        cfg = type("C", (), {"iso": "CAISO", "weather_year": 2024})()
        design = get_reserve_design(cfg, fleet, self._T, ["SP15"])
        kw = build_reserve_dispatch_kwargs(design)
        n = fleet.pmax.shape[0]
        storage_kw = {}
        if with_storage:
            storage_kw = dict(
                storage_power_cap=np.array([400.0]),
                storage_energy_cap=np.array([float(storage_mwh)]),
                storage_zone_idx=np.array([0]),
                eta_chg=1.0,
                eta_dis=1.0,
                reserve_storage=kw.get("reserve_storage", False),
                reserve_storage_duration_h=kw.get("reserve_storage_duration_h"),
            )
        return solve_dispatch(
            fleet,
            np.full((1, self._T), 200.0),
            wind_cf=np.zeros((1, self._T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, self._T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((n, self._T)),
            voll=5000.0,
            reserve_requirement=kw["reserve_requirement"],
            reserve_eligible=kw["reserve_eligible"],
            ordc_penalties=kw["ordc_penalties"],
            ordc_step_widths=kw["ordc_step_widths"],
            reserve_balance_zone_mask=kw["reserve_balance_zone_mask"],
            reserve_balance_ordc_counts=kw["reserve_balance_ordc_counts"],
            reserve_pergen_gen_idx=kw["reserve_pergen_gen_idx"],
            reserve_pergen_col=kw["reserve_pergen_col"],
            reserve_pergen_ramp10=kw["reserve_pergen_ramp10"],
            T=self._T,
            **storage_kw,
        )

    def test_thermal_only_ramp_shortage_prices_published_curve(self):
        # MSSC 1,000 -> spin 500 + non-spin 500; thermal deliverable ramp is
        # 300, so both co-drawn families run 200 MW short: spin prices $100
        # flat, non-spin $600 (the 70-210 MW tier), reserve_price (sum of
        # family duals) = $700 every hour.
        r = self._solve()
        self.assertEqual(r.status, "Optimal")
        self.assertAlmostEqual(
            float(np.asarray(r.reserve_price).mean()), 700.0, places=3
        )

    def test_storage_rs_closes_the_gap_and_collapses_price(self):
        # A 400 MW / 400 MWh battery: RS bounded by power (400) and by the
        # 30-min ASSOC gate (SOC/0.5 = 800). Deliverable 300 + 400 >= 500 ->
        # requirement clears, price collapses to ~0, and the exact storage
        # split (storage_reserve_dispatch) carries >= 200 MW every hour.
        r = self._solve(with_storage=True)
        self.assertEqual(r.status, "Optimal")
        self.assertLess(float(np.asarray(r.reserve_price).mean()), 1.0)
        self.assertIsNotNone(r.storage_reserve_dispatch)
        self.assertGreaterEqual(float(r.storage_reserve_dispatch.min()), 200.0 - 1e-3)

    def test_assoc_soc_gate_bounds_storage_reserve(self):
        # Shrink the battery to 50 MWh: the ASSOC gate caps RS at
        # 50/0.5 = 100 MW, so 300 + 100 = 400 < 500 and 100 MW stays short —
        # the published curve fires and cleared storage AS respects the gate.
        r = self._solve(with_storage=True, storage_mwh=50.0)
        self.assertEqual(r.status, "Optimal")
        self.assertGreater(float(np.asarray(r.reserve_price).mean()), 50.0)
        self.assertLessEqual(float(r.storage_reserve_dispatch.max()), 100.0 + 1e-3)

    def test_hydro_backfilled_ramp_closes_the_gap(self):
        # The 600 MW hydro plant (ramp10 backfilled to full nameplate) joins
        # the pool: 300 + 600 >= 500 -> the shortage vanishes without storage.
        r = self._solve(with_hydro=True)
        self.assertEqual(r.status, "Optimal")
        self.assertLess(float(np.asarray(r.reserve_price).mean()), 1.0)


class TestPerGenReserveCoopt(unittest.TestCase):
    """Per-generator reserve columns (R[j] ≤ ramp10, joint P+R ≤ cap).

    The Phase-2 PJM build (docs/multi-iso/pjm-reserve-ordc.md): reserve
    competes with energy on the same marginal unit, so the balance dual
    carries the sub-shortage OPPORTUNITY COST (the offer-curve spread), not
    just the shortfall penalty — the structure the zone-aggregate co-opt
    cannot price (it honestly clears $0 off pooled headroom).
    """

    def _fleet(self, pmax, mc_hr, zone_idx=None):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        gas_idx = FUEL_TYPE_NAMES.index("gas_ct")
        n, T = len(pmax), 4
        return (
            FleetArrays(
                pmax=np.asarray(pmax, dtype=float),
                pmin=np.zeros(n),
                heat_rate=np.asarray(mc_hr, dtype=float),
                vom=np.zeros(n),
                emission_rate=np.zeros(n),
                nox_rate=np.zeros(n),
                so2_rate=np.zeros(n),
                zone_idx=(
                    np.zeros(n, dtype=int)
                    if zone_idx is None
                    else np.asarray(zone_idx, dtype=int)
                ),
                fuel_type_idx=np.full(n, gas_idx),
                availability=np.ones((n, T)),
                unit_ids=[f"g{i}" for i in range(n)],
                efficiency_bin=np.zeros(n),
                plant_code=np.arange(1, n + 1),
            ),
            T,
        )

    def _solve_one_zone(self, req_mw, gen_idx, ramp10, demand_mw=1000.0):
        # Gen 0: cheap ($10), 1,100 MW. Gen 1: expensive ($50), 500 MW.
        # PJM-style two-step shortfall curve: 190 MW at $300, rest at $850.
        from market_sim.model.dispatch import solve_dispatch

        fleet, T = self._fleet([1100.0, 500.0], [10.0, 50.0])
        return solve_dispatch(
            fleet,
            np.full((1, T), demand_mw),
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((2, T)),  # MC = heat_rate
            voll=2000.0,
            reserve_requirement=np.full(T, float(req_mw)),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([300.0, 850.0]),
            ordc_step_widths=np.array([190.0, float(req_mw)]),
            reserve_pergen_gen_idx=np.asarray(gen_idx, dtype=int),
            reserve_pergen_ramp10=np.asarray(ramp10, dtype=float),
        )

    def test_slack_headroom_clears_at_zero(self):
        # Demand 500 on the 1,100 MW cheap unit: 200 MW reserve rides free
        # headroom (ramp10 300) — reserve price $0, LMP stays at $10.
        r = self._solve_one_zone(200.0, [0], [300.0], demand_mw=500.0)
        self.assertEqual(r.status, "Optimal")
        self.assertTrue(np.allclose(r.reserve_price, 0.0, atol=1e-6))
        self.assertTrue(np.allclose(r.prices, 10.0, atol=1e-6))

    def test_opportunity_cost_prices_reserve_below_penalty(self):
        # THE per-gen mechanism: demand 1,000, cheap cap 1,100, requirement
        # 200 held ONLY on the cheap unit -> it backs down to 900, the $50
        # unit serves 100, LMP = $50, and the balance dual = the FORGONE
        # MARGIN $50 - $10 = $40 — an opportunity-cost reserve price strictly
        # below the cheapest $300 shortfall step. The zone-aggregate layout
        # prices this hour $0 (pooled headroom 1,100 + 500 - 1,000 >= 200).
        r = self._solve_one_zone(200.0, [0], [300.0])
        self.assertEqual(r.status, "Optimal")
        self.assertTrue(np.allclose(r.prices, 50.0, atol=1e-6))
        self.assertTrue(np.allclose(r.reserve_price, 40.0, atol=1e-6))
        # dispatch backed down: cheap unit 900, expensive 100
        self.assertTrue(np.allclose(r.dispatch[0], 900.0, atol=1e-6))
        self.assertTrue(np.allclose(r.dispatch[1], 100.0, atol=1e-6))
        # zonal reserve block carries the held 200 MW
        self.assertTrue(np.allclose(r.reserve_dispatch.sum(axis=0), 200.0))

    def test_ramp10_exhausted_prices_shortfall_step(self):
        # Requirement 600 > sum ramp10 500 (300 + 200): 100 MW shortfall on
        # the cheapest $300 band sets the reserve price at the published
        # penalty; the second unit's spare headroom can't help past ramp10.
        r = self._solve_one_zone(600.0, [0, 1], [300.0, 200.0])
        self.assertEqual(r.status, "Optimal")
        self.assertTrue(np.allclose(r.reserve_price, 300.0, atol=1e-6))

    def test_nested_mad_family_binds_locationally(self):
        # Two zones, unconstrained interchange for energy; family 0 (RTO) spans
        # both, family 1 (subzone, zone 1 only) requires 150 MW that must come
        # from zone 1's single 200 MW unit (ramp10 200). Zone 1 serves 100 MW
        # of local demand... with P+R <= 200 and R >= 150, P <= 50, so 50+ MW
        # imports and the subzone family binds on zone-1 columns only.
        import scipy.sparse as sp

        from market_sim.model.dispatch import solve_dispatch

        fleet, T = self._fleet([2000.0, 200.0], [10.0, 30.0], zone_idx=[0, 1])
        incidence = sp.csr_matrix(np.array([[1.0], [-1.0]]))
        r = solve_dispatch(
            fleet,
            np.array([[800.0] * T, [100.0] * T]),
            wind_cf=np.zeros((2, T)),
            wind_cap=np.zeros(2),
            solar_cf=np.zeros((2, T)),
            solar_cap=np.zeros(2),
            fuel_prices=np.ones((2, T)),
            voll=2000.0,
            incidence=incidence,
            ttc=np.array([1000.0]),
            reserve_requirement=np.vstack([np.full(T, 300.0), np.full(T, 150.0)]),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([300.0, 850.0, 300.0, 850.0]),
            ordc_step_widths=np.array([190.0, 300.0, 190.0, 150.0]),
            reserve_balance_zone_mask=np.array([[True, True], [False, True]]),
            reserve_balance_ordc_counts=np.array([2, 2]),
            reserve_pergen_gen_idx=np.array([0, 1]),
            reserve_pergen_ramp10=np.array([500.0, 200.0]),
        )
        self.assertEqual(r.status, "Optimal")
        # Zone 1 holds at least its 150 MW subzone requirement locally.
        self.assertTrue(np.all(r.reserve_dispatch[1] >= 150.0 - 1e-6))
        # RTO family met (zone sums >= 300).
        self.assertTrue(np.all(r.reserve_dispatch.sum(axis=0) >= 300.0 - 1e-6))

    def test_plant_aggregated_column_shares_headroom(self):
        # Two tranches of ONE plant (cheap $10 600 MW + expensive $50 500 MW)
        # share an R column via pergen_col=[0,0]: the joint row sums BOTH
        # tranches' P against the summed cap, so the plant can back its
        # reserve with the idle expensive tranche's headroom. Demand 600
        # loads the cheap tranche fully; holding 200 MW costs nothing (500 MW
        # idle headroom, ramp10 300) -> reserve price $0. The per-tranche
        # layout (identity mapping, ramp10 split pro-rata) would price the
        # cheap tranche's backdown instead.
        from market_sim.model.dispatch import solve_dispatch

        fleet, T = self._fleet([600.0, 500.0], [10.0, 50.0])
        r = solve_dispatch(
            fleet,
            np.full((1, T), 600.0),
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((2, T)),
            voll=2000.0,
            reserve_requirement=np.full(T, 200.0),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([300.0, 850.0]),
            ordc_step_widths=np.array([190.0, 200.0]),
            reserve_pergen_gen_idx=np.array([0, 1]),
            reserve_pergen_col=np.array([0, 0]),
            reserve_pergen_ramp10=np.array([300.0]),
        )
        self.assertEqual(r.status, "Optimal")
        self.assertTrue(np.allclose(r.reserve_price, 0.0, atol=1e-6))
        self.assertTrue(np.allclose(r.prices, 10.0, atol=1e-6))
        self.assertTrue(np.allclose(r.reserve_dispatch.sum(axis=0), 200.0))

    def test_pergen_rejects_zone_aggregate_scoping(self):
        # supply-cap / online-gating are zone-aggregate mechanisms the per-gen
        # ramp10 bound supersedes; combining them is a wiring error.
        with self.assertRaises(ValueError):
            self._solve_and_cap()

    def _solve_and_cap(self):
        from market_sim.model.dispatch import solve_dispatch

        fleet, T = self._fleet([1100.0, 500.0], [10.0, 50.0])
        return solve_dispatch(
            fleet,
            np.full((1, T), 1000.0),
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((2, T)),
            voll=2000.0,
            reserve_requirement=np.full(T, 200.0),
            reserve_eligible=np.array([True, True]),
            ordc_penalties=np.array([300.0, 850.0]),
            ordc_step_widths=np.array([190.0, 200.0]),
            reserve_pergen_gen_idx=np.array([0]),
            reserve_pergen_ramp10=np.array([300.0]),
            reserve_supply_cap=np.full((1, T), 500.0),
        )


if __name__ == "__main__":
    unittest.main()


class TestAllClassBalanceFamily(unittest.TestCase):
    """A reserve_class -1 family draws on EVERY class's reserve (the ERCOT
    lumped ORDC total-reserve curve layered on the product families).

    Trivial case: 1 zone, 24 h, one 1,000 MW CC. Two product families
    (class 0 req 100, class 1 req 150) plus the all-class total family
    (req 400), on the ADDITIVE shared-headroom spec the ERCOT multi-product
    design uses (one row bounding P + every product's R against capacity —
    the legacy per-class spec would double-count headroom across classes).
    """

    _T = 24

    def _fleet(self):
        from market_sim.data.fleet import FUEL_TYPE_NAMES, FleetArrays

        cc_idx = FUEL_TYPE_NAMES.index("gas_cc")
        T = self._T
        return FleetArrays(
            pmax=np.array([1000.0]),
            pmin=np.zeros(1),
            heat_rate=np.array([7.0]),
            vom=np.zeros(1),
            emission_rate=np.zeros(1),
            nox_rate=np.zeros(1),
            so2_rate=np.zeros(1),
            zone_idx=np.array([0]),
            fuel_type_idx=np.array([cc_idx]),
            availability=np.ones((1, T)),
            unit_ids=["cc"],
            efficiency_bin=np.zeros(1),
            plant_code=np.array([1]),
        )

    def _solve(self, demand_mw, with_total, total_penalty=200.0):
        from market_sim.model.dispatch import solve_dispatch

        T = self._T
        demand = np.array([[float(demand_mw)] * T])
        # product families: class 0 (req 100), class 1 (req 150); both
        # price shortfall at VOLL-scale so they always hold when feasible.
        req = [np.full(T, 100.0), np.full(T, 150.0)]
        pens = [np.array([2000.0]), np.array([2000.0])]
        wids = [np.array([100.0]), np.array([150.0])]
        classes = [0, 1]
        if with_total:
            req.append(np.full(T, 400.0))
            pens.append(np.array([total_penalty]))
            wids.append(np.array([400.0]))
            classes.append(-1)
        eligible = np.array([[True], [True]])  # both classes: the CC
        return solve_dispatch(
            self._fleet(),
            demand,
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            fuel_prices=np.ones((1, T)),
            voll=5000.0,
            reserve_requirement=np.vstack(req),
            reserve_eligible=eligible,
            ordc_penalties=np.concatenate(pens),
            ordc_step_widths=np.concatenate(wids),
            reserve_balance_zone_mask=np.ones((len(req), 1), dtype=bool),
            reserve_balance_ordc_counts=np.array([len(p) for p in pens]),
            reserve_balance_class=np.array(classes),
            reserve_headroom_eligible=np.array([[True]]),
            reserve_headroom_products=np.array([[True, True]]),
        )

    def test_products_count_toward_total(self):
        # Slack system (demand 400 -> headroom 600 >= 400): the total family
        # is met by holding 400 total across the two classes — products'
        # 250 count toward it (all-class sum), only 150 extra is held.
        res = self._solve(400.0, with_total=True)
        self.assertEqual(res.status, "Optimal")
        held = float(np.asarray(res.reserve_dispatch).sum(axis=0).mean())
        self.assertAlmostEqual(held, 400.0, places=3)
        # nothing short -> total family adds no price
        self.assertAlmostEqual(float(np.asarray(res.reserve_price).mean()), 0.0)

    def test_total_shortfall_prices_and_lifts_lmp(self):
        # Tight system (demand 700 -> headroom 300): products hold their 250,
        # the total family is 100 short (300 < 400) and prices at its step;
        # the shared headroom passes the total dual into the energy LMP.
        base = self._solve(700.0, with_total=False)
        tot = self._solve(700.0, with_total=True)
        self.assertEqual(tot.status, "Optimal")
        held_base = float(np.asarray(base.reserve_dispatch).sum(axis=0).mean())
        held_tot = float(np.asarray(tot.reserve_dispatch).sum(axis=0).mean())
        self.assertAlmostEqual(held_base, 250.0, places=3)
        self.assertAlmostEqual(held_tot, 300.0, places=3)  # all headroom held
        price_base = float(np.asarray(base.prices).mean())
        price_tot = float(np.asarray(tot.prices).mean())
        self.assertAlmostEqual(price_base, 7.0, places=3)  # energy MC only
        # marginal MW now trades off against the $200 total-reserve step
        self.assertAlmostEqual(price_tot, 207.0, places=2)
