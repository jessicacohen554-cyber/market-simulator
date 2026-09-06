"""Tests for the endogenous federal CES TARGET row (SCN-WS2a).

Readiness plan 2026-09 §3 WS-2 items 1–2 (G-S1 / G-S3): one annual federal
CES row per ISO on the clean-tier row family, credited by
``federal_ces.unit_credit_fractions``, escaping at the ACP, its dual the
endogenous federal EAC price; the ``rows.py`` "requires the RPS region
family" coupling relaxed; two config fields with a rule-19 mutual-exclusion
guard; the three state/federal postures. Trivial-first (1 zone, 24 h),
then the composition and byte-identity proofs.
"""

import unittest
from dataclasses import asdict

import numpy as np

from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.lp import VariableLayout, build_constraints, solve_dispatch
from market_sim.policy.clean_tiers import (
    append_clean_region,
    build_clean_region_arrays,
    clean_credit_by_fuel,
)
from market_sim.policy.federal_ces import (
    FEDERAL_CES_REGION_LABEL,
    append_federal_ces_region,
    build_federal_ces_region,
    federal_ces_row_fuel_credit,
    federal_ces_target_row_active,
    target_for_year,
    unit_credit_fractions,
)

T = 24
_NEW_FIELDS = ("federal_ces_target_by_year", "federal_ces_acp_usd_per_mwh")


def _target_config(**overrides) -> ScenarioConfig:
    """A forecast config carrying the target row (illustrative knots)."""
    kwargs = dict(
        federal_ces_enabled=True,
        federal_ces_target_by_year={2026: 0.5},
        federal_ces_acp_usd_per_mwh=50.0,
    )
    kwargs.update(overrides)
    return ScenarioConfig(**kwargs)


def _gen(uid, zone, fuel, pmax=100.0):
    return Generator(
        unit_id=uid,
        name=uid,
        zone=zone,
        fuel_type=fuel,
        pmax_mw=pmax,
        pmin_mw=0.0,
        eford=0.0,
    )


def _fleet(units, zone_names):
    return generators_to_fleet_arrays(list(units), zone_names, hours=T)


def _no_renewables(n_zones):
    return dict(
        wind_cf=np.zeros((n_zones, T)),
        wind_cap=np.zeros(n_zones),
        solar_cf=np.zeros((n_zones, T)),
        solar_cap=np.zeros(n_zones),
    )


def _build_kwargs(arrays):
    """The build_constraints kwargs (no ACP price — that is a cost, not a row)."""
    return dict(
        clean_region_zone_mask=arrays.eligible_zone_mask,
        clean_region_obligation_frac=arrays.obligation_frac,
        clean_region_fuels=arrays.qualifying_fuels,
    )


def _clean_kwargs(arrays):
    """The solve_dispatch kwargs the runner derives from a CleanRegionArrays."""
    return dict(clean_region_acp_price=arrays.acp_price, **_build_kwargs(arrays))


class TestTargetRowConfigGuards(unittest.TestCase):
    """The __post_init__ preconditions of the target row (rule 19 / rule 13)."""

    def test_valid_target_config_constructs(self):
        cfg = _target_config()
        self.assertTrue(federal_ces_target_row_active(cfg))

    def test_defaults_carry_no_row(self):
        cfg = ScenarioConfig()
        self.assertIsNone(cfg.federal_ces_target_by_year)
        self.assertIsNone(cfg.federal_ces_acp_usd_per_mwh)
        self.assertFalse(federal_ces_target_row_active(cfg))
        self.assertIsNone(target_for_year(cfg, 2030))

    def test_target_requires_master_gate(self):
        with self.assertRaisesRegex(ValueError, "requires federal_ces_enabled"):
            _target_config(federal_ces_enabled=False)

    def test_target_refused_in_backcast(self):
        with self.assertRaisesRegex(ValueError, "forecast-only"):
            ScenarioConfig(
                mode="backcast",
                federal_ces_target_by_year={2024: 0.5},
                federal_ces_acp_usd_per_mwh=50.0,
            )

    def test_target_and_exogenous_premium_are_mutually_exclusive(self):
        # rule 19 [R-ONE-MECH]: the row's dual IS the federal EAC price.
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            _target_config(federal_ces_premium_usd_per_mwh=20.0)
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            _target_config(federal_ces_premium_by_year={2026: 10.0, 2030: 20.0})
        # An all-zero knot path is not a premium: allowed.
        cfg = _target_config(federal_ces_premium_by_year={2026: 0.0})
        self.assertTrue(federal_ces_target_row_active(cfg))

    def test_target_requires_positive_acp(self):
        with self.assertRaisesRegex(ValueError, "positive federal_ces_acp"):
            _target_config(federal_ces_acp_usd_per_mwh=None)
        with self.assertRaisesRegex(ValueError, "positive federal_ces_acp"):
            _target_config(federal_ces_acp_usd_per_mwh=0.0)

    def test_acp_without_target_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no row to price"):
            ScenarioConfig(federal_ces_enabled=True, federal_ces_acp_usd_per_mwh=50.0)

    def test_storage_crediting_refused_with_target(self):
        with self.assertRaisesRegex(ValueError, "storage_eligible"):
            _target_config(federal_ces_storage_eligible=True)

    def test_wind_and_solar_must_stay_eligible(self):
        with self.assertRaisesRegex(ValueError, "'solar' in federal_ces_eligible"):
            _target_config(federal_ces_eligible_fuels=["nuclear", "wind"])

    def test_knot_values_are_shares(self):
        with self.assertRaisesRegex(ValueError, "not a credited share"):
            _target_config(federal_ces_target_by_year={2026: 1.5})
        with self.assertRaisesRegex(ValueError, "not a year"):
            _target_config(federal_ces_target_by_year={"soon": 0.5})

    def test_empty_mapping_refused(self):
        with self.assertRaisesRegex(ValueError, "empty mapping"):
            _target_config(federal_ces_target_by_year={})


class TestTargetRowCacheKey(unittest.TestCase):
    """Both fields registered at None: every existing key is byte-stable."""

    def test_fields_are_cache_key_optional(self):
        for name in _NEW_FIELDS:
            self.assertIn(name, _CACHE_KEY_OPTIONAL_FIELDS)

    def test_fields_drop_out_of_default_payload(self):
        defaults = ScenarioConfig()
        payload = asdict(defaults)
        for name in _CACHE_KEY_OPTIONAL_FIELDS:
            if payload.get(name) == getattr(defaults, name):
                payload.pop(name, None)
        self.assertEqual([k for k in payload if k in _NEW_FIELDS], [])

    def test_configured_row_keys_distinctly(self):
        base = ScenarioConfig(federal_ces_enabled=True).cache_key()
        self.assertNotEqual(_target_config().cache_key(), base)
        self.assertNotEqual(
            _target_config(federal_ces_acp_usd_per_mwh=60.0).cache_key(),
            _target_config().cache_key(),
        )


class TestTargetPath(unittest.TestCase):
    """Sparse knots, linear between, edge-held — the premium's convention."""

    def test_interpolation_and_edge_hold(self):
        cfg = _target_config(
            federal_ces_target_by_year={2026: 0.55, 2035: 0.80, 2050: 1.0}
        )
        self.assertAlmostEqual(target_for_year(cfg, 2026), 0.55)
        self.assertAlmostEqual(target_for_year(cfg, 2035), 0.80)
        self.assertAlmostEqual(target_for_year(cfg, 2050), 1.0)
        self.assertAlmostEqual(target_for_year(cfg, 2030), 0.55 + 4 / 9 * 0.25)
        self.assertAlmostEqual(target_for_year(cfg, 2020), 0.55)
        self.assertAlmostEqual(target_for_year(cfg, 2060), 1.0)

    def test_string_keys_coerced(self):
        cfg = _target_config(federal_ces_target_by_year={"2026": 0.4, "2036": 0.6})
        self.assertAlmostEqual(target_for_year(cfg, 2031), 0.5)


class TestFederalRegionBuilder(unittest.TestCase):
    """The federal region: every zone, target on every zone, credit vector."""

    def setUp(self):
        self.zones = ["A", "B", "C"]
        self.fleet = _fleet(
            [
                _gen("N", "A", "nuclear"),
                _gen("G", "B", "gas_cc"),
                _gen("X", "C", "gas_cc_ccs"),
            ],
            self.zones,
        )

    def test_standalone_region(self):
        cfg = _target_config(federal_ces_target_by_year={2026: 0.6})
        arrays = build_federal_ces_region(cfg, 2026, self.zones, self.fleet)
        self.assertEqual(arrays.labels, (FEDERAL_CES_REGION_LABEL,))
        np.testing.assert_array_equal(arrays.eligible_zone_mask, [[True] * 3])
        np.testing.assert_allclose(arrays.obligation_frac, [[0.6] * 3])
        np.testing.assert_allclose(arrays.acp_price, [50.0])
        spec = arrays.qualifying_fuels[0]
        self.assertIsInstance(spec, np.ndarray)
        np.testing.assert_allclose(spec, unit_credit_fractions(cfg, self.fleet))
        np.testing.assert_allclose(spec, [1.0, 0.0, 0.95])
        self.assertEqual(arrays.fuel_credit[0], federal_ces_row_fuel_credit(cfg))
        self.assertAlmostEqual(arrays.fuel_credit[0]["gas_cc_ccs"], 0.95)
        self.assertAlmostEqual(arrays.fuel_credit[0]["nuclear"], 1.0)
        self.assertNotIn("gas_cc", arrays.fuel_credit[0])

    def test_cesa_ci_mode_credits_through_the_same_vector(self):
        cfg = _target_config(federal_ces_crediting="cesa_ci")
        arrays = build_federal_ces_region(cfg, 2026, self.zones, self.fleet)
        np.testing.assert_allclose(
            arrays.qualifying_fuels[0], unit_credit_fractions(cfg, self.fleet)
        )

    def test_off_returns_state_family_unchanged(self):
        cfg = ScenarioConfig(federal_ces_enabled=True)
        self.assertIsNone(build_federal_ces_region(cfg, 2026, self.zones, self.fleet))
        state = append_clean_region(
            None,
            label="STATE",
            eligible_zone_mask=np.array([True, False, False]),
            obligation_frac=np.array([0.3, 0.0, 0.0]),
            acp_price=30.0,
            qualifying=("nuclear", "wind", "solar"),
        )
        self.assertIs(
            append_federal_ces_region(cfg, 2026, self.zones, self.fleet, state), state
        )

    def test_appends_after_state_family(self):
        cfg = _target_config()
        state = append_clean_region(
            None,
            label="STATE",
            eligible_zone_mask=np.array([True, False, False]),
            obligation_frac=np.array([0.3, 0.0, 0.0]),
            acp_price=30.0,
            qualifying=("nuclear", "wind", "solar"),
        )
        both = append_federal_ces_region(cfg, 2026, self.zones, self.fleet, state)
        self.assertEqual(both.labels, ("STATE", FEDERAL_CES_REGION_LABEL))
        np.testing.assert_array_equal(
            both.eligible_zone_mask[0], state.eligible_zone_mask[0]
        )
        np.testing.assert_array_equal(both.obligation_frac[0], state.obligation_frac[0])
        self.assertEqual(both.qualifying_fuels[0], state.qualifying_fuels[0])
        self.assertEqual(both.fuel_credit, (None, federal_ces_row_fuel_credit(cfg)))
        np.testing.assert_allclose(both.acp_price, [30.0, 50.0])

    def test_miso_state_family_is_untouched_when_off(self):
        # K-row / clean-tier byte-identity for MISO: with no target row the
        # composition returns the state family object itself.
        zones = [z.name for z in get_iso_config("MISO").zones]
        fleet = _fleet([_gen("N", zones[0], "nuclear")], zones)
        state = build_clean_region_arrays("MISO", 2035, zones)
        cfg = ScenarioConfig(federal_ces_enabled=True)
        self.assertIs(append_federal_ces_region(cfg, 2035, zones, fleet, state), state)
        self.assertIsNone(state.fuel_credit)

    def test_consumer_map_is_dual_times_fraction(self):
        cfg = _target_config()
        arrays = build_federal_ces_region(cfg, 2026, self.zones, self.fleet)
        by_fuel = clean_credit_by_fuel(arrays, np.array([20.0]))
        np.testing.assert_allclose(by_fuel["nuclear"], [20.0] * 3)
        np.testing.assert_allclose(by_fuel["gas_cc_ccs"], [19.0] * 3)
        np.testing.assert_allclose(by_fuel["wind"], [20.0] * 3)
        self.assertNotIn("gas_cc", by_fuel)


class TestTargetRowLP(unittest.TestCase):
    """Trivial-first: 1 zone, 24 h, the row's dual and escape semantics."""

    def _nuclear_gas(self):
        return _fleet([_gen("N", "Z", "nuclear"), _gen("G", "Z", "gas_cc")], ["Z"])

    def _solve(self, cfg, mc_clean=60.0, mc_dirty=50.0, **extra):
        fleet = self._nuclear_gas()
        arrays = build_federal_ces_region(cfg, 2026, ["Z"], fleet)
        result = solve_dispatch(
            fleet,
            np.full((1, T), 80.0),
            mc=np.vstack([np.full(T, mc_clean), np.full(T, mc_dirty)]),
            T=T,
            **_clean_kwargs(arrays),
            **_no_renewables(1),
            **extra,
        )
        self.assertEqual(result.status, "Optimal")
        return result

    def test_binding_row_dual_is_the_clean_dirty_cost_gap(self):
        # Target 50% with a $50 ACP: the row binds, nuclear (mc 60) displaces
        # gas (mc 50) for exactly half the energy, dual = 60 - 50 = 10.
        result = self._solve(_target_config())
        np.testing.assert_allclose(result.clean_region_duals, [10.0], atol=1e-3)
        credited = result.dispatch[0].sum() / (80.0 * T)
        self.assertGreaterEqual(credited, 0.5 - 1e-6)
        self.assertAlmostEqual(credited, 0.5, places=6)

    def test_escape_case_dual_equals_acp(self):
        # ACP $5 below the $10 gap: the row escapes — pays the ACP instead of
        # dispatching nuclear — and its dual is pinned at the ACP.
        result = self._solve(_target_config(federal_ces_acp_usd_per_mwh=5.0))
        np.testing.assert_allclose(result.clean_region_duals, [5.0], atol=1e-3)
        self.assertLess(result.dispatch[0].sum() / (80.0 * T), 0.5)

    def test_slack_row_has_zero_dual(self):
        # Nuclear cheaper than gas: the target is met in-merit, dual 0.
        result = self._solve(_target_config(), mc_clean=10.0, mc_dirty=50.0)
        np.testing.assert_allclose(result.clean_region_duals, [0.0], atol=1e-3)

    def test_footprint_is_the_eligible_columns_at_their_fractions(self):
        fleet = _fleet(
            [
                _gen("N", "Z", "nuclear"),
                _gen("G", "Z", "gas_cc"),
                _gen("X", "Z", "gas_cc_ccs"),
            ],
            ["Z"],
        )
        cfg = _target_config()
        arrays = build_federal_ces_region(cfg, 2026, ["Z"], fleet)
        layout = VariableLayout(
            n_gen=3, n_zones=1, n_storage=0, n_links=0, T=T, n_rec_acp=1
        )
        A, lower, upper = build_constraints(
            layout, fleet, np.full((1, T), 80.0), **_build_kwargs(arrays)
        )[:3]
        row = A.shape[0] - 1
        self.assertEqual(A[row, layout.p_col(0, 0)], 1.0)  # nuclear
        self.assertEqual(A[row, layout.p_col(1, 0)], 0.0)  # unabated gas
        self.assertEqual(A[row, layout.p_col(2, 0)], 0.95)  # CCS at 0.95
        self.assertEqual(A[row, layout.w_col(0, 0)], 1.0)
        self.assertEqual(A[row, layout.s_col(0, 0)], 1.0)
        self.assertEqual(A[row, layout.acp_col(0, 0)], 1.0)
        # Only these column families touch the row: P (credited), W, S, ACP.
        nz = set(A[row].indices.tolist())
        expected = set()
        for t in range(T):
            expected |= {
                layout.p_col(0, t),
                layout.p_col(2, t),
                layout.w_col(0, t),
                layout.s_col(0, t),
                layout.acp_col(t, 0),
            }
        self.assertEqual(nz, expected)
        self.assertAlmostEqual(lower[row], 0.5 * 80.0 * T)
        self.assertEqual(upper[row], np.inf)

    def test_beside_legacy_rps_row_with_its_own_escape(self):
        # Posture: a single ISO-wide RPS row (with ACP) + the federal row. The
        # RPS escape takes slot 0, the federal escape slot 1; both duals are
        # read back. Nuclear is not RPS-eligible, so the 20% renewable row
        # escapes at its $30 ACP (no VRE capacity here) while the federal
        # row binds at the cost gap.
        result = self._solve(_target_config(), rps_target=0.2, rps_acp_price=30.0)
        np.testing.assert_allclose(result.rps_shadow_price, 30.0, atol=1e-3)
        np.testing.assert_allclose(result.clean_region_duals, [10.0], atol=1e-3)

    def test_beside_state_family_appends_only(self):
        # Posture: MISO-style region RPS (zero RHS) + a state clean row + the
        # federal row: every shared row/bound is byte-identical to the build
        # without the federal row, which is purely appended last.
        fleet = _fleet(
            [_gen("N", "E", "nuclear"), _gen("G", "S", "gas_cc")], ["E", "S"]
        )
        demand = np.full((2, T), 80.0)
        state = append_clean_region(
            None,
            label="MI",
            eligible_zone_mask=np.array([True, False]),
            obligation_frac=np.array([0.8, 0.0]),
            acp_price=30.0,
            qualifying=("nuclear", "wind", "solar"),
        )
        both = append_federal_ces_region(
            _target_config(), 2026, ["E", "S"], fleet, state
        )
        rps_kwargs = dict(
            rps_region_zone_mask=np.ones((1, 2), dtype=bool),
            rps_region_obligation_frac=np.zeros((1, 2)),
        )
        lay_off = VariableLayout(
            n_gen=2, n_zones=2, n_storage=0, n_links=0, T=T, n_rec_acp=2
        )
        lay_on = VariableLayout(
            n_gen=2, n_zones=2, n_storage=0, n_links=0, T=T, n_rec_acp=3
        )
        A_off, lo_off, up_off = build_constraints(
            lay_off, fleet, demand, **rps_kwargs, **_build_kwargs(state)
        )[:3]
        A_on, lo_on, up_on = build_constraints(
            lay_on, fleet, demand, **rps_kwargs, **_build_kwargs(both)
        )[:3]
        self.assertEqual(A_on.shape[0], A_off.shape[0] + 1)
        # Column layouts differ by one ACP column per hour, so compare the
        # shared rows on the columns that exist in both (drop the new slot).
        keep = np.array(
            [
                c
                for c in range(lay_on.total_columns)
                if (c % lay_on.vars_per_hour) != lay_on._rec_acp_off + 2
            ]
        )
        self.assertEqual((A_on[: A_off.shape[0]][:, keep] != A_off).nnz, 0)
        np.testing.assert_array_equal(lo_on[: lo_off.size], lo_off)
        np.testing.assert_array_equal(up_on[: up_off.size], up_off)
        # And the federal row's escape is slot 2 (after RPS K1=1 and MI K2=1).
        self.assertEqual(A_on[A_on.shape[0] - 1, lay_on.acp_col(0, 2)], 1.0)
        self.assertEqual(A_on[A_on.shape[0] - 1, lay_on.acp_col(0, 1)], 0.0)

    def test_misaligned_credit_vector_is_refused(self):
        fleet = self._nuclear_gas()
        arrays = append_clean_region(
            None,
            label=FEDERAL_CES_REGION_LABEL,
            eligible_zone_mask=np.array([True]),
            obligation_frac=np.array([0.5]),
            acp_price=50.0,
            qualifying=np.array([1.0, 0.0, 0.5]),  # three entries, two units
            fuel_credit={"nuclear": 1.0},
        )
        layout = VariableLayout(
            n_gen=2, n_zones=1, n_storage=0, n_links=0, T=T, n_rec_acp=1
        )
        with self.assertRaisesRegex(ValueError, "crediting vector has 3 entries"):
            build_constraints(
                layout, fleet, np.full((1, T), 80.0), **_build_kwargs(arrays)
            )


class TestRunnerPostures(unittest.TestCase):
    """The three documented state/federal postures at the runner resolver."""

    def _miso(self, **overrides):
        zones = [z.name for z in get_iso_config("MISO").zones]
        fleet = _fleet([_gen("N", zones[0], "nuclear")], zones)
        kwargs = dict(
            miso_rps_compliance_regions=True,
            miso_clean_tier_rows=True,
        )
        kwargs.update(overrides)
        return zones, fleet, ScenarioConfig(**kwargs)

    def test_state_rows_plus_federal_row_default(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, cfg = self._miso(
            federal_ces_enabled=True,
            federal_ces_target_by_year={2026: 0.5},
            federal_ces_acp_usd_per_mwh=50.0,
        )
        arrays = _clean_region_arrays_for_year(cfg, "MISO", 2035, zones, fleet)
        state = build_clean_region_arrays("MISO", 2035, zones)
        self.assertEqual(arrays.labels, state.labels + (FEDERAL_CES_REGION_LABEL,))
        np.testing.assert_array_equal(
            arrays.eligible_zone_mask[:-1], state.eligible_zone_mask
        )
        np.testing.assert_array_equal(
            arrays.obligation_frac[:-1], state.obligation_frac
        )

    def test_federal_replaces_state_rows(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, cfg = self._miso(
            federal_ces_enabled=True,
            federal_ces_target_by_year={2026: 0.5},
            federal_ces_acp_usd_per_mwh=50.0,
            federal_ces_replaces_state_rps=True,
        )
        arrays = _clean_region_arrays_for_year(cfg, "MISO", 2035, zones, fleet)
        self.assertEqual(arrays.labels, (FEDERAL_CES_REGION_LABEL,))

    def test_state_rows_only_is_the_pre_scn_ws2a_family(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, cfg = self._miso()
        arrays = _clean_region_arrays_for_year(cfg, "MISO", 2035, zones, fleet)
        state = build_clean_region_arrays("MISO", 2035, zones)
        self.assertEqual(arrays.labels, state.labels)
        self.assertEqual(arrays.qualifying_fuels, state.qualifying_fuels)
        self.assertIsNone(arrays.fuel_credit)

    def test_non_miso_iso_has_federal_row_only_or_nothing(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones = [z.name for z in get_iso_config("NEISO").zones]
        fleet = _fleet([_gen("N", zones[0], "nuclear")], zones)
        cfg = _target_config()
        arrays = _clean_region_arrays_for_year(cfg, "NEISO", 2026, zones, fleet)
        self.assertEqual(arrays.labels, (FEDERAL_CES_REGION_LABEL,))
        self.assertEqual(arrays.eligible_zone_mask.shape, (1, len(zones)))
        self.assertIsNone(
            _clean_region_arrays_for_year(ScenarioConfig(), "NEISO", 2026, zones, fleet)
        )


if __name__ == "__main__":
    unittest.main()
