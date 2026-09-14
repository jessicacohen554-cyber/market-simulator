"""Tests for the voluntary clean-energy demand row (SCN-WS3b).

Readiness plan 2026-09 §3 WS-3 item 2 / §7 "WS-3b"; the design memo
``docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md`` §2.1, §3,
§5. One annual volumetric clean-attribute row per ISO-year on the clean-tier
family (its second consumer after SCN-WS2a's federal CES target row), with an
all-zone mask, a DC-linked volume read from the run's own demand, and an
escape priced at the buyer's willingness-to-pay ceiling. Trivial-first
(1 zone, 24 h: binding → dual = the clean-minus-dirty cost gap; ceiling →
dual = WTP, escape = shortfall; slack → 0; curtailment recovered before
thermal displacement), then the config guards, the derivation gates on the
published anchors, the composition postures and the byte-identity proofs.
"""

import unittest
from dataclasses import asdict

import numpy as np

from market_sim.config.constants import (
    VOLUNTARY_BASELINE_ISO_WEIGHT,
    VOLUNTARY_BASELINE_SHARE,
    VOLUNTARY_COMMITTED_DC_FRACTION,
    VOLUNTARY_ELIGIBLE_FUELS_DEFAULT,
    VOLUNTARY_NATIONAL_SHARE_OF_RETAIL_SALES,
    VOLUNTARY_WTP_CEILING_USD_PER_MWH,
)
from market_sim.config.iso_configs import get_iso_config
from market_sim.config.scenarios import _CACHE_KEY_OPTIONAL_FIELDS, ScenarioConfig
from market_sim.data.datacenter import (
    datacenter_block_energy_mwh,
    datacenter_block_mw_by_zone,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.lp import VariableLayout, build_constraints, solve_dispatch
from market_sim.policy.clean_tiers import (
    append_clean_region,
    build_clean_region_arrays,
    clean_credit_by_fuel,
)
from market_sim.policy.federal_ces import FEDERAL_CES_REGION_LABEL
from market_sim.policy.voluntary_demand import (
    VOLUNTARY_REGION_LABEL,
    VoluntaryVolume,
    _interp_edge_held,
    append_voluntary_region,
    baseline_share,
    build_voluntary_region,
    committed_dc_fraction,
    eligible_fuels,
    iso_baseline_weight,
    resolve_voluntary_volume,
    validate_voluntary_config,
    voluntary_obligation_frac,
    voluntary_region_spec,
    voluntary_row_active,
    wtp_ceiling,
)

T = 24
_NEW_FIELDS = (
    "voluntary_clean_demand_path",
    "voluntary_wtp_ceiling_usd_per_mwh",
    "voluntary_eligible_fuels",
)
_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "NWPP")


def _vol_config(path="mid", **overrides) -> ScenarioConfig:
    kwargs = dict(voluntary_clean_demand_path=path)
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
    return dict(
        clean_region_zone_mask=arrays.eligible_zone_mask,
        clean_region_obligation_frac=arrays.obligation_frac,
        clean_region_fuels=arrays.qualifying_fuels,
    )


def _clean_kwargs(arrays):
    return dict(clean_region_acp_price=arrays.acp_price, **_build_kwargs(arrays))


def _explicit_region(
    volume_mwh, demand, ceiling, fuels=VOLUNTARY_ELIGIBLE_FUELS_DEFAULT
):
    """A standalone voluntary region with an EXPLICIT volume (the LP tests)."""
    return append_clean_region(
        None, **voluntary_region_spec(volume_mwh, demand, ceiling, tuple(fuels))
    )


# ---------------------------------------------------------------------------
# 1. Config guards and coercion (rule 13 / rule 24).
# ---------------------------------------------------------------------------
class TestVoluntaryConfigGuards(unittest.TestCase):
    def test_defaults_carry_no_row(self):
        cfg = ScenarioConfig()
        self.assertEqual(cfg.voluntary_clean_demand_path, "off")
        self.assertIsNone(cfg.voluntary_wtp_ceiling_usd_per_mwh)
        self.assertIsNone(cfg.voluntary_eligible_fuels)
        self.assertFalse(voluntary_row_active(cfg))

    def test_path_labels(self):
        for path in ("low", "mid", "high"):
            self.assertTrue(voluntary_row_active(_vol_config(path)))
        with self.assertRaisesRegex(ValueError, "voluntary_clean_demand_path"):
            _vol_config("max")

    def test_backcast_coerces_the_whole_block_to_defaults(self):
        cfg = ScenarioConfig(
            mode="backcast",
            voluntary_clean_demand_path="high",
            voluntary_wtp_ceiling_usd_per_mwh=9.0,
            voluntary_eligible_fuels=["wind", "solar", "nuclear"],
        )
        self.assertEqual(cfg.voluntary_clean_demand_path, "off")
        self.assertIsNone(cfg.voluntary_wtp_ceiling_usd_per_mwh)
        self.assertIsNone(cfg.voluntary_eligible_fuels)
        self.assertFalse(voluntary_row_active(cfg))
        validate_voluntary_config(cfg)  # no raise

    def test_hindcast_coerces_to_defaults(self):
        cfg = ScenarioConfig(
            mode="forecast", hindcast=True, voluntary_clean_demand_path="mid"
        )
        self.assertEqual(cfg.voluntary_clean_demand_path, "off")
        self.assertFalse(voluntary_row_active(cfg))

    def test_coercion_lands_on_the_dataclass_default(self):
        fields = ScenarioConfig.__dataclass_fields__
        cfg = ScenarioConfig(mode="backcast", voluntary_clean_demand_path="low")
        for name in _NEW_FIELDS:
            self.assertEqual(getattr(cfg, name), fields[name].default)

    def test_validate_refuses_a_mutated_backcast(self):
        cfg = _vol_config("mid")
        object.__setattr__(cfg, "mode", "backcast")
        with self.assertRaisesRegex(ValueError, "forecast-only"):
            validate_voluntary_config(cfg)
        cfg = _vol_config("mid")
        object.__setattr__(cfg, "hindcast", True)
        with self.assertRaisesRegex(ValueError, "forecast-only"):
            validate_voluntary_config(cfg)

    def test_ceiling_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "must be > 0"):
            _vol_config("mid", voluntary_wtp_ceiling_usd_per_mwh=0.0)
        with self.assertRaisesRegex(ValueError, "must be > 0"):
            _vol_config("mid", voluntary_wtp_ceiling_usd_per_mwh=-1.0)
        cfg = _vol_config("mid", voluntary_wtp_ceiling_usd_per_mwh=12.0)
        self.assertEqual(wtp_ceiling(cfg), 12.0)

    def test_companions_refused_with_the_path_off(self):
        with self.assertRaisesRegex(ValueError, "no row to price"):
            ScenarioConfig(voluntary_wtp_ceiling_usd_per_mwh=5.0)
        with self.assertRaisesRegex(ValueError, "no row to credit"):
            ScenarioConfig(voluntary_eligible_fuels=["wind", "solar"])

    def test_eligible_list_hygiene(self):
        with self.assertRaisesRegex(ValueError, "non-empty list"):
            _vol_config("mid", voluntary_eligible_fuels=[])
        with self.assertRaisesRegex(ValueError, "must include 'solar'"):
            _vol_config("mid", voluntary_eligible_fuels=["wind", "nuclear"])
        with self.assertRaisesRegex(ValueError, "must include 'wind'"):
            _vol_config("mid", voluntary_eligible_fuels=["solar", "nuclear"])
        cfg = _vol_config("mid", voluntary_eligible_fuels=["wind", "solar", "nuclear"])
        self.assertEqual(eligible_fuels(cfg), ("wind", "solar", "nuclear"))

    def test_unknown_fuel_is_refused_at_resolution(self):
        cfg = _vol_config("mid", voluntary_eligible_fuels=["wind", "solar", "fusion"])
        with self.assertRaisesRegex(ValueError, "fleet fuel types"):
            eligible_fuels(cfg)

    def test_default_eligible_set_is_the_memo_recommendation(self):
        self.assertEqual(
            eligible_fuels(_vol_config()), VOLUNTARY_ELIGIBLE_FUELS_DEFAULT
        )


# ---------------------------------------------------------------------------
# 2. Cache key: all three fields registered at their inert defaults.
# ---------------------------------------------------------------------------
class TestVoluntaryCacheKey(unittest.TestCase):
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

    def test_off_is_the_default_key_and_armed_keys_distinctly(self):
        base = ScenarioConfig().cache_key()
        self.assertEqual(
            ScenarioConfig(voluntary_clean_demand_path="off").cache_key(), base
        )
        mid = _vol_config("mid").cache_key()
        self.assertNotEqual(mid, base)
        self.assertNotEqual(_vol_config("high").cache_key(), mid)
        self.assertNotEqual(
            _vol_config("mid", voluntary_wtp_ceiling_usd_per_mwh=6.0).cache_key(), mid
        )
        self.assertNotEqual(
            _vol_config(
                "mid", voluntary_eligible_fuels=["wind", "solar", "nuclear"]
            ).cache_key(),
            mid,
        )

    def test_backcast_key_is_byte_identical_whatever_the_block_carries(self):
        bare = ScenarioConfig(mode="backcast").cache_key()
        armed = ScenarioConfig(
            mode="backcast",
            voluntary_clean_demand_path="high",
            voluntary_wtp_ceiling_usd_per_mwh=9.0,
            voluntary_eligible_fuels=["wind", "solar", "nuclear"],
        ).cache_key()
        self.assertEqual(armed, bare)


# ---------------------------------------------------------------------------
# 3. Levels: every value gates a PUBLISHED fact or carries its label.
# ---------------------------------------------------------------------------
class TestVoluntaryLevels(unittest.TestCase):
    def test_baseline_share_paths_read_from_the_nrel_series(self):
        series = VOLUNTARY_NATIONAL_SHARE_OF_RETAIL_SALES
        latest = series[max(series)]
        self.assertAlmostEqual(
            VOLUNTARY_BASELINE_SHARE["mid"][2023], latest
        )  # 2023: ~8 %
        self.assertAlmostEqual(
            VOLUNTARY_BASELINE_SHARE["low"][2023], min(series.values())
        )
        self.assertAlmostEqual(
            VOLUNTARY_BASELINE_SHARE["high"][2023], max(series.values())
        )
        # Stated, not smoothed: the series' ceiling IS its latest value.
        self.assertEqual(
            VOLUNTARY_BASELINE_SHARE["high"], VOLUNTARY_BASELINE_SHARE["mid"]
        )
        self.assertAlmostEqual(latest, 0.08)

    def test_committed_fraction_box5_floor_and_ceiling(self):
        self.assertEqual(committed_dc_fraction(_vol_config("low"), 2030), 0.0)
        self.assertEqual(committed_dc_fraction(_vol_config("high"), 2030), 1.0)
        mid = committed_dc_fraction(_vol_config("mid"), 2030)
        self.assertTrue(0.0 < mid < 1.0)  # ILLUSTRATIVE, owner-set (D-2)
        self.assertEqual(VOLUNTARY_COMMITTED_DC_FRACTION["mid"][2026], mid)

    def test_wtp_ceiling_endpoints_are_the_cited_rec_range(self):
        # docs/handoffs/ces-ci-crediting-audit-2026-07.md §5.2: national
        # voluntary RECs $2-7/MWh.
        self.assertEqual(VOLUNTARY_WTP_CEILING_USD_PER_MWH["low"], 2.0)
        self.assertEqual(VOLUNTARY_WTP_CEILING_USD_PER_MWH["high"], 7.0)
        mid = VOLUNTARY_WTP_CEILING_USD_PER_MWH["mid"]
        self.assertTrue(2.0 < mid < 7.0)  # ILLUSTRATIVE, owner-set (D-2)
        for path in ("low", "mid", "high"):
            self.assertEqual(
                wtp_ceiling(_vol_config(path)), VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]
            )

    def test_default_eligible_set_is_renewable_only(self):
        for fuel in ("wind", "solar", "offshore_wind", "geothermal"):
            self.assertIn(fuel, VOLUNTARY_ELIGIBLE_FUELS_DEFAULT)
        for fuel in ("hydro", "biomass", "nuclear", "gas_cc_ccs", "gas_cc"):
            self.assertNotIn(fuel, VOLUNTARY_ELIGIBLE_FUELS_DEFAULT)

    def test_iso_weight_is_needs_intake_everywhere(self):
        for iso in _ISOS:
            self.assertIsNone(VOLUNTARY_BASELINE_ISO_WEIGHT[iso])
            self.assertEqual(iso_baseline_weight(iso), 1.0)
        self.assertEqual(iso_baseline_weight("unknown"), 1.0)

    def test_edge_held_interpolation(self):
        knots = {2026: 0.0, 2030: 1.0}
        self.assertEqual(_interp_edge_held(knots, 2020), 0.0)
        self.assertEqual(_interp_edge_held(knots, 2040), 1.0)
        self.assertAlmostEqual(_interp_edge_held(knots, 2028), 0.5)
        self.assertAlmostEqual(_interp_edge_held({"2023": 0.08}, 2050), 0.08)
        self.assertEqual(baseline_share(_vol_config("mid"), 2050), 0.08)
        with self.assertRaisesRegex(ValueError, "empty"):
            _interp_edge_held({}, 2030)


# ---------------------------------------------------------------------------
# 4. The volume construction (memo §3.1) on the run's own demand.
# ---------------------------------------------------------------------------
class TestVolumeResolver(unittest.TestCase):
    def setUp(self):
        self.zones = get_iso_config("ERCOT").zone_names
        rng = np.random.default_rng(3)
        self.demand = rng.random((len(self.zones), T)) * 5e4 + 2e4

    def test_dc_energy_helper_is_the_block_times_hours(self):
        cfg = ScenarioConfig(iso="ERCOT", datacenter_load_path="mid")
        block = datacenter_block_mw_by_zone(cfg, "ERCOT", 2030, self.zones)
        self.assertAlmostEqual(
            datacenter_block_energy_mwh(cfg, "ERCOT", 2030, self.zones, T),
            float(block.sum()) * T,
        )
        off = ScenarioConfig(iso="ERCOT", datacenter_load_path="off")
        self.assertEqual(
            datacenter_block_energy_mwh(off, "ERCOT", 2030, self.zones, T), 0.0
        )

    def test_closed_form_at_every_path(self):
        e_total = float(self.demand.sum())
        for path in ("low", "mid", "high"):
            cfg = _vol_config(path, iso="ERCOT", datacenter_load_path="mid")
            e_dc = datacenter_block_energy_mwh(cfg, "ERCOT", 2030, self.zones, T)
            self.assertGreater(e_dc, 0.0)
            v = resolve_voluntary_volume(cfg, "ERCOT", 2030, self.zones, self.demand)
            self.assertIsInstance(v, VoluntaryVolume)
            s = VOLUNTARY_BASELINE_SHARE[path][2023]
            f = VOLUNTARY_COMMITTED_DC_FRACTION[path][2026]
            self.assertAlmostEqual(v.energy_total_mwh, e_total)
            self.assertAlmostEqual(v.energy_dc_mwh, e_dc)
            self.assertAlmostEqual(v.energy_non_dc_mwh, e_total - e_dc)
            self.assertAlmostEqual(
                v.volume_mwh, s * (e_total - e_dc) + f * e_dc, places=6
            )

    def test_dc_block_off_sizes_on_the_baseline_alone(self):
        cfg = _vol_config("mid", iso="ERCOT", datacenter_load_path="off")
        v = resolve_voluntary_volume(cfg, "ERCOT", 2030, self.zones, self.demand)
        self.assertEqual(v.energy_dc_mwh, 0.0)
        self.assertAlmostEqual(v.volume_mwh, 0.08 * float(self.demand.sum()), places=6)

    def test_high_dc_raises_the_volume_without_a_second_knob(self):
        mid = resolve_voluntary_volume(
            _vol_config("mid", iso="ERCOT", datacenter_load_path="mid"),
            "ERCOT",
            2030,
            self.zones,
            self.demand,
        )
        high_dc = resolve_voluntary_volume(
            _vol_config("mid", iso="ERCOT", datacenter_load_path="high"),
            "ERCOT",
            2030,
            self.zones,
            self.demand,
        )
        self.assertGreater(high_dc.energy_dc_mwh, mid.energy_dc_mwh)
        # Same demand array here, so the DC half moves and the baseline
        # shrinks by the same energy: ΔV = (f_commit − s_base) × ΔE_DC.
        self.assertAlmostEqual(
            high_dc.volume_mwh - mid.volume_mwh,
            (0.5 - 0.08) * (high_dc.energy_dc_mwh - mid.energy_dc_mwh),
            places=6,
        )

    def test_obligation_fraction_expresses_the_volume_exactly(self):
        demand = self.demand.copy()
        demand[0, :] = 0.0  # a zero-load zone (ERCOT Panhandle carries load_share 0)
        frac = voluntary_obligation_frac(1234.5, demand)
        self.assertEqual(frac.shape, (len(self.zones),))
        self.assertAlmostEqual(float(frac @ demand.sum(axis=1)), 1234.5, places=9)
        self.assertEqual(float(frac[0] * demand[0].sum()), 0.0)
        np.testing.assert_array_equal(
            voluntary_obligation_frac(10.0, np.zeros((2, T))), np.zeros(2)
        )

    def test_misaligned_demand_is_refused(self):
        cfg = _vol_config("mid", iso="ERCOT")
        with self.assertRaisesRegex(ValueError, "aligned with zone_names"):
            resolve_voluntary_volume(cfg, "ERCOT", 2030, self.zones, self.demand[:2])


# ---------------------------------------------------------------------------
# 5. The region on the family: shape, order, off-path identity.
# ---------------------------------------------------------------------------
class TestVoluntaryRegionBuilder(unittest.TestCase):
    def setUp(self):
        self.zones = ["A", "B", "C"]
        self.demand = np.vstack([np.full(T, 100.0), np.full(T, 50.0), np.zeros(T)])
        self.cfg = _vol_config("mid", iso="TEST")  # no DC block for an unsourced ISO

    def test_standalone_region(self):
        arrays = build_voluntary_region(self.cfg, "TEST", 2030, self.zones, self.demand)
        self.assertEqual(arrays.labels, (VOLUNTARY_REGION_LABEL,))
        np.testing.assert_array_equal(arrays.eligible_zone_mask, [[True] * 3])
        v = resolve_voluntary_volume(self.cfg, "TEST", 2030, self.zones, self.demand)
        self.assertAlmostEqual(v.volume_mwh, 0.08 * 150.0 * T)
        np.testing.assert_allclose(arrays.obligation_frac, [[0.08] * 3])
        np.testing.assert_allclose(arrays.acp_price, [4.5])
        self.assertEqual(arrays.qualifying_fuels, (VOLUNTARY_ELIGIBLE_FUELS_DEFAULT,))
        self.assertEqual(arrays.fuel_credit, (None,))

    def test_off_returns_the_family_unchanged(self):
        cfg = ScenarioConfig(iso="TEST")
        self.assertIsNone(
            build_voluntary_region(cfg, "TEST", 2030, self.zones, self.demand)
        )
        state = append_clean_region(
            None,
            label="STATE",
            eligible_zone_mask=np.array([True, False, False]),
            obligation_frac=np.array([0.3, 0.0, 0.0]),
            acp_price=30.0,
            qualifying=("nuclear", "wind", "solar"),
        )
        self.assertIs(
            append_voluntary_region(cfg, "TEST", 2030, self.zones, state, self.demand),
            state,
        )
        # And a demand-less call is the pre-SCN-WS3b shape when off.
        self.assertIs(
            append_voluntary_region(cfg, "TEST", 2030, self.zones, state, None), state
        )

    def test_active_without_demand_is_refused(self):
        with self.assertRaisesRegex(ValueError, "no zone_demand"):
            append_voluntary_region(self.cfg, "TEST", 2030, self.zones, None, None)

    def test_appends_last_after_a_prior_family(self):
        prior = append_clean_region(
            None,
            label=FEDERAL_CES_REGION_LABEL,
            eligible_zone_mask=np.ones(3, dtype=bool),
            obligation_frac=np.full(3, 0.5),
            acp_price=50.0,
            qualifying=np.array([1.0, 0.0]),
            fuel_credit={"nuclear": 1.0},
        )
        both = append_voluntary_region(
            self.cfg, "TEST", 2030, self.zones, prior, self.demand
        )
        self.assertEqual(
            both.labels, (FEDERAL_CES_REGION_LABEL, VOLUNTARY_REGION_LABEL)
        )
        np.testing.assert_allclose(both.acp_price, [50.0, 4.5])
        np.testing.assert_array_equal(both.obligation_frac[0], prior.obligation_frac[0])
        self.assertEqual(both.fuel_credit, ({"nuclear": 1.0}, None))

    def test_override_set_flows_into_the_qualifying_spec(self):
        cfg = _vol_config(
            "mid",
            iso="TEST",
            voluntary_eligible_fuels=["wind", "solar", "nuclear", "gas_cc_ccs"],
            voluntary_wtp_ceiling_usd_per_mwh=25.0,
        )
        arrays = build_voluntary_region(cfg, "TEST", 2030, self.zones, self.demand)
        self.assertEqual(
            arrays.qualifying_fuels, (("wind", "solar", "nuclear", "gas_cc_ccs"),)
        )
        np.testing.assert_allclose(arrays.acp_price, [25.0])

    def test_consumer_map_credits_every_eligible_fuel_at_the_dual(self):
        arrays = build_voluntary_region(self.cfg, "TEST", 2030, self.zones, self.demand)
        by_fuel = clean_credit_by_fuel(arrays, np.array([3.25]))
        for fuel in VOLUNTARY_ELIGIBLE_FUELS_DEFAULT:
            np.testing.assert_allclose(by_fuel[fuel], [3.25] * 3)
        self.assertNotIn("gas_cc", by_fuel)
        self.assertNotIn("nuclear", by_fuel)


# ---------------------------------------------------------------------------
# 6. Trivial-first LP: 1 zone, 24 h — the row's dual and escape semantics.
# ---------------------------------------------------------------------------
class TestVoluntaryRowLP(unittest.TestCase):
    DEMAND = 80.0

    def _geo_gas(self, geo_pmax=100.0):
        return _fleet(
            [_gen("GEO", "Z", "geothermal", pmax=geo_pmax), _gen("G", "Z", "gas_cc")],
            ["Z"],
        )

    def _solve(self, fleet, arrays=None, mc_clean=60.0, mc_dirty=50.0, **extra):
        demand = np.full((1, T), self.DEMAND)
        kwargs = dict(_no_renewables(1))
        if arrays is not None:
            kwargs.update(_clean_kwargs(arrays))
        kwargs.update(extra)
        result = solve_dispatch(
            fleet,
            demand,
            mc=np.vstack([np.full(T, mc_clean), np.full(T, mc_dirty)]),
            T=T,
            **kwargs,
        )
        self.assertEqual(result.status, "Optimal")
        return result

    def test_binding_row_dual_is_the_clean_dirty_cost_gap(self):
        # V = half the energy, WTP $30 above the $10 gap: geothermal (mc 60)
        # displaces gas (mc 50) for exactly V, dual = 60 − 50 = 10.
        demand = np.full((1, T), self.DEMAND)
        volume = 0.5 * self.DEMAND * T
        arrays = _explicit_region(volume, demand, 30.0)
        result = self._solve(self._geo_gas(), arrays)
        np.testing.assert_allclose(result.clean_region_duals, [10.0], atol=1e-3)
        self.assertAlmostEqual(float(result.dispatch[0].sum()), volume, places=4)

    def test_ceiling_dual_equals_wtp_and_escape_is_the_shortfall(self):
        # WTP $5 below the $10 gap: the buyer stops buying — the escape fires
        # for the whole volume, dual = w, and the objective rises by exactly
        # w × escape (the row's own arithmetic, memo §2.1).
        demand = np.full((1, T), self.DEMAND)
        volume = 0.5 * self.DEMAND * T
        arrays = _explicit_region(volume, demand, 5.0)
        fleet = self._geo_gas()
        base = self._solve(fleet)
        result = self._solve(fleet, arrays)
        np.testing.assert_allclose(result.clean_region_duals, [5.0], atol=1e-3)
        delivered = float(result.dispatch[0].sum())
        self.assertAlmostEqual(delivered, 0.0, places=4)
        escape = volume - delivered
        self.assertAlmostEqual(
            result.objective_value - base.objective_value, 5.0 * escape, places=2
        )

    def test_partial_escape_is_the_physical_shortfall_at_the_ceiling(self):
        # Eligible capacity 20 MW < V/T: geothermal runs flat out (480 MWh),
        # the escape covers the rest (480 MWh) at the $20 ceiling, dual = w.
        demand = np.full((1, T), self.DEMAND)
        volume = 0.5 * self.DEMAND * T  # 960
        arrays = _explicit_region(volume, demand, 20.0)
        fleet = self._geo_gas(geo_pmax=20.0)
        base = self._solve(fleet)
        result = self._solve(fleet, arrays)
        np.testing.assert_allclose(result.clean_region_duals, [20.0], atol=1e-3)
        delivered = float(result.dispatch[0].sum())
        self.assertAlmostEqual(delivered, 20.0 * T, places=4)
        escape = volume - delivered
        self.assertAlmostEqual(escape, 480.0, places=4)
        # Objective: the 480 MWh of geothermal at +$10 plus 480 MWh escaped at $20.
        self.assertAlmostEqual(
            result.objective_value - base.objective_value,
            10.0 * delivered + 20.0 * escape,
            places=2,
        )

    def test_slack_row_has_zero_dual(self):
        demand = np.full((1, T), self.DEMAND)
        arrays = _explicit_region(0.5 * self.DEMAND * T, demand, 30.0)
        result = self._solve(self._geo_gas(), arrays, mc_clean=10.0, mc_dirty=50.0)
        np.testing.assert_allclose(result.clean_region_duals, [0.0], atol=1e-3)

    def test_curtailed_wind_is_recovered_before_thermal_is_displaced(self):
        # Memo A.3 regime (ii): wind potential 100 MW against 50 MW of demand
        # — the surplus is dumped in REF. A voluntary volume of 70 MW·h is met
        # by UN-curtailing (W rises to 70, the dump absorbs it) at the dump
        # tiebreaker's cost, never by touching the thermal column: the
        # cheapest attribute is a dumped MWh's certificate.
        fleet = _fleet([_gen("G", "Z", "gas_cc")], ["Z"])
        demand = np.full((1, T), 50.0)
        renew = dict(
            wind_cf=np.ones((1, T)),
            wind_cap=np.array([100.0]),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
        )
        base = solve_dispatch(fleet, demand, mc=np.full((1, T), 50.0), T=T, **renew)
        self.assertEqual(base.status, "Optimal")
        self.assertAlmostEqual(float(base.wind_dispatched.sum()), 50.0 * T, places=3)
        arrays = _explicit_region(70.0 * T, demand, 4.5)
        result = solve_dispatch(
            fleet,
            demand,
            mc=np.full((1, T), 50.0),
            T=T,
            **renew,
            **_clean_kwargs(arrays),
        )
        self.assertEqual(result.status, "Optimal")
        self.assertAlmostEqual(float(result.wind_dispatched.sum()), 70.0 * T, places=3)
        self.assertAlmostEqual(float(result.dump.sum()), 20.0 * T, places=3)
        self.assertAlmostEqual(float(result.dispatch.sum()), 0.0, places=4)
        dual = float(result.clean_region_duals[0])
        self.assertGreater(dual, 0.0)
        self.assertLess(dual, 0.05)  # the dump tiebreaker, not a merit-order gap

    def test_footprint_is_the_eligible_columns_only(self):
        fleet = _fleet(
            [
                _gen("GEO", "Z", "geothermal"),
                _gen("G", "Z", "gas_cc"),
                _gen("N", "Z", "nuclear"),
            ],
            ["Z"],
        )
        demand = np.full((1, T), self.DEMAND)
        arrays = _explicit_region(960.0, demand, 4.5)
        layout = VariableLayout(
            n_gen=3, n_zones=1, n_storage=0, n_links=0, T=T, n_rec_acp=1
        )
        A, lower, upper = build_constraints(
            layout, fleet, demand, **_build_kwargs(arrays)
        )[:3]
        row = A.shape[0] - 1
        self.assertEqual(A[row, layout.p_col(0, 0)], 1.0)  # geothermal
        self.assertEqual(A[row, layout.p_col(1, 0)], 0.0)  # gas
        self.assertEqual(
            A[row, layout.p_col(2, 0)], 0.0
        )  # nuclear (renewable-only default)
        self.assertEqual(A[row, layout.w_col(0, 0)], 1.0)
        self.assertEqual(A[row, layout.s_col(0, 0)], 1.0)
        self.assertEqual(A[row, layout.acp_col(0, 0)], 1.0)
        nz = set(A[row].indices.tolist())
        expected = set()
        for t in range(T):
            expected |= {
                layout.p_col(0, t),
                layout.w_col(0, t),
                layout.s_col(0, t),
                layout.acp_col(t, 0),
            }
        self.assertEqual(nz, expected)
        self.assertAlmostEqual(lower[row], 960.0)
        self.assertEqual(upper[row], np.inf)

    def test_carbon_free_override_credits_nuclear(self):
        fleet = _fleet([_gen("N", "Z", "nuclear"), _gen("G", "Z", "gas_cc")], ["Z"])
        demand = np.full((1, T), self.DEMAND)
        arrays = _explicit_region(
            960.0, demand, 30.0, fuels=("wind", "solar", "nuclear")
        )
        result = self._solve(fleet, arrays)
        np.testing.assert_allclose(result.clean_region_duals, [10.0], atol=1e-3)
        self.assertAlmostEqual(float(result.dispatch[0].sum()), 960.0, places=4)

    def test_beside_legacy_rps_row_with_its_own_escape(self):
        # Slot 0 the RPS escape, slot 1 the voluntary escape; both duals read
        # back. Geothermal is not RPS-row eligible here (wind/solar only), so
        # the 20 % renewable row escapes at its $30 ACP with no VRE, while the
        # voluntary row binds at the cost gap.
        demand = np.full((1, T), self.DEMAND)
        arrays = _explicit_region(960.0, demand, 30.0)
        result = self._solve(
            self._geo_gas(), arrays, rps_target=0.2, rps_acp_price=30.0
        )
        np.testing.assert_allclose(result.rps_shadow_price, 30.0, atol=1e-3)
        np.testing.assert_allclose(result.clean_region_duals, [10.0], atol=1e-3)


# ---------------------------------------------------------------------------
# 7. The runner resolver: region order and the off-path identity.
# ---------------------------------------------------------------------------
class TestRunnerPostures(unittest.TestCase):
    def _iso(self, iso, **overrides):
        zones = get_iso_config(iso).zone_names
        fleet = _fleet([_gen("N", zones[0], "nuclear")], zones)
        demand = np.full((len(zones), T), 100.0)
        return zones, fleet, demand, ScenarioConfig(iso=iso, **overrides)

    def test_ercot_voluntary_row_stands_alone(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, demand, cfg = self._iso(
            "ERCOT", voluntary_clean_demand_path="mid"
        )
        arrays = _clean_region_arrays_for_year(
            cfg, "ERCOT", 2026, zones, fleet, zone_demand=demand
        )
        self.assertEqual(arrays.labels, (VOLUNTARY_REGION_LABEL,))
        self.assertEqual(arrays.eligible_zone_mask.shape, (1, len(zones)))
        v = resolve_voluntary_volume(cfg, "ERCOT", 2026, zones, demand)
        self.assertAlmostEqual(
            float(arrays.obligation_frac[0] @ demand.sum(axis=1)), v.volume_mwh
        )

    def test_off_is_none_with_or_without_demand(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, demand, cfg = self._iso("ERCOT")
        self.assertIsNone(
            _clean_region_arrays_for_year(cfg, "ERCOT", 2026, zones, fleet)
        )
        self.assertIsNone(
            _clean_region_arrays_for_year(
                cfg, "ERCOT", 2026, zones, fleet, zone_demand=demand
            )
        )

    def test_active_without_demand_is_refused_at_the_resolver(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, _, cfg = self._iso("ERCOT", voluntary_clean_demand_path="mid")
        with self.assertRaisesRegex(ValueError, "no zone_demand"):
            _clean_region_arrays_for_year(cfg, "ERCOT", 2026, zones, fleet)

    def test_federal_then_voluntary(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, demand, cfg = self._iso(
            "NEISO",
            federal_ces_enabled=True,
            federal_ces_target_by_year={2026: 0.5},
            federal_ces_acp_usd_per_mwh=50.0,
            voluntary_clean_demand_path="high",
        )
        arrays = _clean_region_arrays_for_year(
            cfg, "NEISO", 2026, zones, fleet, zone_demand=demand
        )
        self.assertEqual(
            arrays.labels, (FEDERAL_CES_REGION_LABEL, VOLUNTARY_REGION_LABEL)
        )
        np.testing.assert_allclose(arrays.acp_price, [50.0, 7.0])

    def test_miso_state_rows_then_voluntary_and_state_family_untouched_when_off(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, demand, cfg = self._iso(
            "MISO",
            miso_rps_compliance_regions=True,
            miso_clean_tier_rows=True,
            voluntary_clean_demand_path="mid",
        )
        arrays = _clean_region_arrays_for_year(
            cfg, "MISO", 2035, zones, fleet, zone_demand=demand
        )
        state = build_clean_region_arrays("MISO", 2035, zones)
        self.assertEqual(arrays.labels, state.labels + (VOLUNTARY_REGION_LABEL,))
        np.testing.assert_array_equal(
            arrays.obligation_frac[:-1], state.obligation_frac
        )
        zones, fleet, demand, off = self._iso(
            "MISO", miso_rps_compliance_regions=True, miso_clean_tier_rows=True
        )
        off_arrays = _clean_region_arrays_for_year(
            off, "MISO", 2035, zones, fleet, zone_demand=demand
        )
        self.assertEqual(off_arrays.labels, state.labels)
        self.assertIsNone(off_arrays.fuel_credit)

    def test_not_suppressed_by_federal_replaces_state_rps(self):
        from market_sim.runner import _clean_region_arrays_for_year

        zones, fleet, demand, cfg = self._iso(
            "MISO",
            miso_rps_compliance_regions=True,
            miso_clean_tier_rows=True,
            federal_ces_enabled=True,
            federal_ces_target_by_year={2026: 0.5},
            federal_ces_acp_usd_per_mwh=50.0,
            federal_ces_replaces_state_rps=True,
            voluntary_clean_demand_path="mid",
        )
        arrays = _clean_region_arrays_for_year(
            cfg, "MISO", 2035, zones, fleet, zone_demand=demand
        )
        self.assertEqual(
            arrays.labels, (FEDERAL_CES_REGION_LABEL, VOLUNTARY_REGION_LABEL)
        )


if __name__ == "__main__":
    unittest.main()
