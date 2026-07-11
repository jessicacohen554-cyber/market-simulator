"""Tests for the CR-1 reserve-margin-indexed capacity demand curve.

Trivial-first (CLAUDE.md testing pattern): the curve math is exercised on
hand-computed synthetic curves and 1-unit fleets before any ISO curve is
touched. Covers the plan's acceptance list
(docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md §3, test
line 4): price-at-requirement = net-CONE, zero-cross, cap, monotonicity, ERCOT
zero in both modes, default-off byte-identity, the T2.1 arithmetic-identity, and
the reconciliation of every encoded curve against the P-0B
``capacity-market-demand-curve`` datatype (rule 13 — published input, never a
fit target).
"""

import unittest
from types import SimpleNamespace

import numpy as np

from market_sim.config.constants import (
    MARKET_DESIGN,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    CapacityDemandCurvePoint,
    evaluate_demand_curve,
)
from market_sim.config.paths import RAW_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    apply_economic_retirements,
    capacity_reserve_position,
    capacity_revenue_per_mw_yr,
)
from market_sim.model.storage import estimate_capacity_value

# A hand-computed synthetic curve anchored at the requirement: cap 1.5 x
# net-CONE at 90% of requirement, net-CONE (1.0) at the requirement, zero-cross
# at 110%. Every value below is derivable by hand from these three points.
_SYNTH = (
    CapacityDemandCurvePoint(0.9, 1.5),
    CapacityDemandCurvePoint(1.0, 1.0),
    CapacityDemandCurvePoint(1.1, 0.0),
)

_CURVE_ISOS = ("PJM", "NYISO", "NEISO", "MISO")
_CFG_ON = SimpleNamespace(capacity_market_clearing=True)
_CFG_OFF = SimpleNamespace(capacity_market_clearing=False)


class TestDemandCurveEval(unittest.TestCase):
    """The normalized piecewise-linear curve evaluator (pure math)."""

    def test_price_at_requirement_equals_net_cone(self):
        # The defining property: at the requirement (reserve_ratio 1.0) the
        # curve pays exactly net-CONE (fraction 1.0).
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 1.0), 1.0)

    def test_zero_cross(self):
        # At and beyond the zero-cross the price is 0 (flat-extrapolated right).
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 1.1), 0.0)
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 1.5), 0.0)

    def test_cap(self):
        # At and below the leftmost point the price clamps to the cap (flat
        # left) — the shortage price ceiling, never exceeded.
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 0.9), 1.5)
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 0.5), 1.5)

    def test_linear_interpolation(self):
        # Halfway up each segment is the arithmetic midpoint of its endpoints.
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 0.95), 1.25)
        self.assertAlmostEqual(evaluate_demand_curve(_SYNTH, 1.05), 0.5)

    def test_monotone_non_increasing(self):
        xs = np.linspace(0.7, 1.3, 61)
        ys = [evaluate_demand_curve(_SYNTH, x) for x in xs]
        self.assertTrue(all(ys[i] >= ys[i + 1] - 1e-12 for i in range(len(ys) - 1)))

    def test_empty_curve_is_zero(self):
        self.assertEqual(evaluate_demand_curve((), 1.0), 0.0)


class TestCapacityPriceSeam(unittest.TestCase):
    """MarketDesign.capacity_price_per_firm_mw_yr + capacity_revenue_per_mw_yr."""

    def test_default_off_byte_identity(self):
        # With no config (the pre-CR-1 call) OR the gate explicitly off, every
        # ISO returns the FIXED net-CONE price — byte-identical to the stub —
        # regardless of any reserve position.
        for iso, design in MARKET_DESIGN.items():
            expected = (
                design.net_cone_per_kw_yr * 1000.0 if design.capacity_market else 0.0
            )
            self.assertEqual(design.capacity_price_per_firm_mw_yr(), expected)
            self.assertEqual(
                design.capacity_price_per_firm_mw_yr(_CFG_OFF, 0.85), expected
            )
            # The public thermal helper: 2-arg call == pre-CR-1 formula.
            eford = 0.05
            self.assertEqual(
                capacity_revenue_per_mw_yr(iso, eford),
                expected * (1.0 - eford),
            )
            # Gate off: reserve_position is inert (None vs a number identical).
            self.assertEqual(
                capacity_revenue_per_mw_yr(iso, eford, _CFG_OFF, None),
                capacity_revenue_per_mw_yr(iso, eford, _CFG_OFF, 0.85),
            )

    def test_ercot_zero_both_modes(self):
        ercot = MARKET_DESIGN["ERCOT"]
        self.assertEqual(ercot.capacity_price_per_firm_mw_yr(), 0.0)
        self.assertEqual(ercot.capacity_price_per_firm_mw_yr(_CFG_ON, 0.80), 0.0)
        self.assertEqual(capacity_revenue_per_mw_yr("ERCOT", 0.06), 0.0)
        self.assertEqual(capacity_revenue_per_mw_yr("ERCOT", 0.06, _CFG_ON, 0.80), 0.0)

    def test_unknown_iso_zero_both_modes(self):
        # An ISO absent from the registry falls back to the energy-only default.
        self.assertEqual(capacity_revenue_per_mw_yr("MADEUP", 0.05), 0.0)
        self.assertEqual(capacity_revenue_per_mw_yr("MADEUP", 0.05, _CFG_ON, 0.9), 0.0)

    def test_caiso_keeps_fixed_proxy_even_with_curve_on(self):
        # CAISO has no published auction curve, so the gate being on must not
        # change its price — it keeps the fixed proxy (documented low-fidelity).
        caiso = MARKET_DESIGN["CAISO"]
        self.assertEqual(caiso.demand_curve, ())
        self.assertEqual(
            caiso.capacity_price_per_firm_mw_yr(_CFG_ON, 0.80),
            caiso.net_cone_per_kw_yr * 1000.0,
        )

    def test_curve_price_at_requirement_is_net_cone(self):
        # Curve mode ON: every ISO whose published curve places net-CONE at the
        # requirement pays exactly net_cone_curve there. (PJM's real curve puts
        # its net-CONE point at 1.015, so it is tested at that x.)
        anchor_x = {"PJM": 1.015, "NYISO": 1.0, "NEISO": 1.0, "MISO": 1.0}
        for iso in _CURVE_ISOS:
            design = MARKET_DESIGN[iso]
            price = design.capacity_price_per_firm_mw_yr(_CFG_ON, anchor_x[iso])
            self.assertAlmostEqual(
                price, design.net_cone_curve_per_kw_yr * 1000.0, places=4
            )

    def test_curve_zero_when_long(self):
        # Far above the zero-cross the curve pays nothing (fleet is long).
        for iso in _CURVE_ISOS:
            self.assertEqual(
                MARKET_DESIGN[iso].capacity_price_per_firm_mw_yr(_CFG_ON, 1.5), 0.0
            )

    def test_curve_cap_when_short(self):
        # Deep shortage clamps to the published price cap (cap fraction x
        # net_cone_curve), never higher.
        for iso in _CURVE_ISOS:
            design = MARKET_DESIGN[iso]
            cap_frac = design.demand_curve[0].price_frac_net_cone
            price = design.capacity_price_per_firm_mw_yr(_CFG_ON, 0.3)
            self.assertAlmostEqual(
                price, cap_frac * design.net_cone_curve_per_kw_yr * 1000.0, places=3
            )

    def test_curve_monotone_non_increasing(self):
        for iso in _CURVE_ISOS:
            design = MARKET_DESIGN[iso]
            xs = np.linspace(0.5, 1.4, 91)
            ys = [design.capacity_price_per_firm_mw_yr(_CFG_ON, x) for x in xs]
            self.assertTrue(
                all(ys[i] >= ys[i + 1] - 1e-9 for i in range(len(ys) - 1)),
                f"{iso} curve not monotone",
            )

    def test_t2_1_arithmetic_identity(self):
        # T2.1: the clearing price IS the VRR curve evaluated at the reserve
        # position, scaled by net-CONE — for every ISO-curve and position.
        for iso in _CURVE_ISOS:
            design = MARKET_DESIGN[iso]
            for pos in (0.6, 0.85, 0.97, 1.0, 1.02, 1.08, 1.2):
                identity = (
                    evaluate_demand_curve(design.demand_curve, pos)
                    * design.net_cone_curve_per_kw_yr
                    * 1000.0
                )
                self.assertAlmostEqual(
                    design.capacity_price_per_firm_mw_yr(_CFG_ON, pos),
                    identity,
                    places=6,
                )

    def test_thermal_revenue_is_price_times_ucap(self):
        # The thermal payment applies the unit's UCAP to the shared price.
        eford = 0.06
        price = MARKET_DESIGN["PJM"].capacity_price_per_firm_mw_yr(_CFG_ON, 1.015)
        self.assertAlmostEqual(
            capacity_revenue_per_mw_yr("PJM", eford, _CFG_ON, 1.015),
            price * (1.0 - eford),
        )


class TestReservePosition(unittest.TestCase):
    """capacity_reserve_position — accredited firm / shared requirement."""

    def test_hand_computed_ratio(self):
        # NEISO: DR fraction 0, ICAP->UCAP ratio 1.0, UCAP thermal basis, so the
        # requirement and accredited sums are hand-computable.
        iso = "NEISO"
        gen = Generator(
            unit_id="G0",
            name="G0",
            zone="Z0",
            fuel_type="gas_cc",
            pmax_mw=1000.0,
            heat_rate=7.0,
            eford=0.05,
        )
        peak = 1000.0
        config = ScenarioConfig(iso=iso)
        firm = 1000.0 * (1.0 - 0.05)  # UCAP
        requirement = peak * (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO[iso])
        pos = capacity_reserve_position([gen], 0.0, 0.0, 0.0, config, iso, peak)
        self.assertAlmostEqual(pos, firm / requirement)

    def test_none_when_peak_nonpositive(self):
        config = ScenarioConfig(iso="PJM")
        self.assertIsNone(
            capacity_reserve_position([], 0.0, 0.0, 0.0, config, "PJM", 0.0)
        )

    def test_pools_and_storage_lift_position(self):
        # Adding accredited wind/solar/storage raises the reserve position.
        iso = "NEISO"
        config = ScenarioConfig(iso=iso)
        gen = Generator(
            unit_id="G0",
            name="G0",
            zone="Z0",
            fuel_type="gas_cc",
            pmax_mw=1000.0,
            heat_rate=7.0,
            eford=0.05,
        )
        bare = capacity_reserve_position([gen], 0.0, 0.0, 0.0, config, iso, 1000.0)
        with_pools = capacity_reserve_position(
            [gen], 500.0, 500.0, 200.0, config, iso, 1000.0
        )
        self.assertGreater(with_pools, bare)


class TestScreenByteIdentity(unittest.TestCase):
    """Default-off byte-identity — and gate-on liveness — through the screen."""

    T = 24

    def _run(self, config, reserve_position):
        # Three coal units, deeply unprofitable on energy (price 10 < mc), so
        # the retire/keep decision turns entirely on the capacity payment. Floor
        # disabled (peak_demand=0) so only the economic screen decides.
        fleet = [
            Generator(
                unit_id=f"C{i}",
                name=f"C{i}",
                zone="Z0",
                fuel_type="coal",
                pmax_mw=1000.0,
                heat_rate=11.0 - i,
            )
            for i in range(3)
        ]
        arrays = generators_to_fleet_arrays(fleet, ["Z0"], hours=self.T)
        prices = np.full((1, self.T), 10.0)
        dispatch = SimpleNamespace(dispatch=np.full((len(fleet), self.T), 10.0))
        survivors, _, _ = apply_economic_retirements(
            fleet,
            arrays,
            dispatch,
            prices,
            config,
            {},
            peak_demand=0.0,
            reserve_position=reserve_position,
        )
        return sorted(g.unit_id for g in survivors)

    def test_gate_off_ignores_reserve_position(self):
        # With capacity_market_clearing off (default), passing a reserve
        # position must not change which units retire — the gate, not the
        # position, controls curve mode (proves default-off byte-identity).
        config = ScenarioConfig(iso="PJM")  # gate defaults off
        self.assertFalse(config.capacity_market_clearing)
        base = self._run(config, None)
        self.assertEqual(base, self._run(config, 0.80))
        self.assertEqual(base, self._run(config, 1.20))

    def test_gate_on_curve_drives_retirement(self):
        # Gate on: a short position (cap price) keeps strictly more coal online
        # than a long position (capacity price collapses to 0) — the mechanism
        # is live and the reserve position drives it (not a vacuous no-op).
        config = ScenarioConfig(iso="PJM", capacity_market_clearing=True)
        short = self._run(config, 0.80)
        long = self._run(config, 1.20)
        self.assertGreater(len(short), len(long))


class TestStorageCurve(unittest.TestCase):
    """estimate_capacity_value routes through the shared curve seam."""

    def test_fixed_mode_byte_identity(self):
        # Default (gate off / no reserve position) == net_cone x ELCC x derate,
        # byte-identical to the pre-CR-1 storage capacity value.
        config = ScenarioConfig(iso="PJM", storage_capacity_value=True)
        v_none = estimate_capacity_value("li_ion_4hr", 0.0, config, "PJM")
        v_gate_off = estimate_capacity_value(
            "li_ion_4hr", 0.0, config, "PJM", reserve_position=0.8
        )
        self.assertEqual(v_none, v_gate_off)
        self.assertGreater(v_none, 0.0)

    def test_curve_mode_scales_by_curve_price(self):
        # Gate on: a long position (low curve price) yields less capacity value
        # than a short position (cap price) for the same tech.
        config = ScenarioConfig(
            iso="PJM", storage_capacity_value=True, capacity_market_clearing=True
        )
        short = estimate_capacity_value(
            "li_ion_4hr", 0.0, config, "PJM", reserve_position=0.85
        )
        long = estimate_capacity_value(
            "li_ion_4hr", 0.0, config, "PJM", reserve_position=1.15
        )
        self.assertGreater(short, long)
        self.assertEqual(long, 0.0)  # past the zero-cross

    def test_ercot_storage_zero_both_modes(self):
        config = ScenarioConfig(
            iso="ERCOT", storage_capacity_value=True, capacity_market_clearing=True
        )
        self.assertEqual(
            estimate_capacity_value("li_ion_4hr", 0.0, config, "ERCOT", 0.8), 0.0
        )


class TestP0BReconciliation(unittest.TestCase):
    """Every encoded curve traces to the P-0B demand-curve datatype (rule 13)."""

    @classmethod
    def setUpClass(cls):
        from scripts.lib import capacity_market_demand_curve as dc

        cls.dc = dc

    def _rows(self, iso, delivery_year):
        df = self.dc.parse_iso(iso, RAW_DIR)
        return df[df.delivery_year == delivery_year]

    @staticmethod
    def _scalar(rows, metric, **filt):
        sub = rows[rows.metric == metric]
        for col, val in filt.items():
            sub = sub[sub[col] == val]
        return float(sub.y_value.iloc[0])

    def test_pjm_curve_matches_published(self):
        rows = self._rows("PJM", "2026/2027")
        design = MARKET_DESIGN["PJM"]
        # Net-CONE anchor ($/MW-yr row -> $/kW-yr).
        net_cone = self._scalar(rows, "net_cone", y_unit="usd_per_mw_yr")
        self.assertAlmostEqual(design.net_cone_curve_per_kw_yr, net_cone / 1000.0, 3)
        # Curve x-positions.
        cps = rows[rows.metric == "curve_point"].sort_values("point_index")
        self.assertEqual(
            [round(p.reserve_ratio, 4) for p in design.demand_curve],
            [round(x, 4) for x in cps.x_value],
        )
        # Cap fraction = price_cap / net_cone (both $/MW-day).
        cap = self._scalar(rows, "price_cap", y_unit="usd_per_mw_day")
        ncd = self._scalar(rows, "net_cone", y_unit="usd_per_mw_day")
        self.assertAlmostEqual(
            design.demand_curve[0].price_frac_net_cone, cap / ncd, places=3
        )

    def test_nyiso_curve_matches_published(self):
        rows = self._rows("NYISO", "2025-2026")
        design = MARKET_DESIGN["NYISO"]
        net_cone = self._scalar(rows, "net_cone", area="NYCA")
        self.assertAlmostEqual(design.net_cone_curve_per_kw_yr, net_cone, 2)
        # Published zero-cross (summer curve length) == encoded right-hand point.
        summer = rows[(rows.area == "NYCA") & (rows.season == "summer")]
        zero_x = float(
            summer[summer.metric == "curve_point"]
            .sort_values("point_index")
            .x_value.iloc[-1]
        )
        self.assertAlmostEqual(design.demand_curve[-1].reserve_ratio, zero_x, 3)
        # Cap fraction = summer max clearing / summer reference point.
        cap = float(summer[summer.metric == "price_cap"].y_value.iloc[0])
        ref = float(
            summer[summer.metric == "curve_point"]
            .sort_values("point_index")
            .y_value.iloc[0]
        )
        self.assertAlmostEqual(
            design.demand_curve[0].price_frac_net_cone, cap / ref, places=2
        )

    def test_neiso_curve_matches_published(self):
        rows = self._rows("NEISO", "2027-2028")
        design = MARKET_DESIGN["NEISO"]
        net_cone_month = self._scalar(rows, "net_cone")
        self.assertAlmostEqual(
            design.net_cone_curve_per_kw_yr, net_cone_month * 12.0, 1
        )
        cap_month = self._scalar(rows, "price_cap")
        self.assertAlmostEqual(
            design.demand_curve[0].price_frac_net_cone,
            cap_month / net_cone_month,
            places=2,
        )

    def test_miso_curve_matches_published(self):
        rows = self._rows("MISO", "2025-2026")
        design = MARKET_DESIGN["MISO"]
        # Net-CONE anchor: North/Central annual Net CONE ($/MW-yr -> $/kW-yr).
        # (Filter by the annual $/MW-yr unit; the seasonal rows are $/MW-day.)
        net_cone = self._scalar(
            rows, "net_cone", area="North/Central", y_unit="usd_per_mw_yr"
        )
        self.assertAlmostEqual(design.net_cone_curve_per_kw_yr, net_cone / 1000.0, 2)
        # Cap fraction ~ North/Central average gross CONE / Net CONE. The RBDC
        # shape is first-order (documented), so this is a band, not equality.
        nc_lrz = rows[(rows.metric == "gross_cone") & (rows.area.str.startswith("LRZ"))]
        # LRZ 1-7 make up the North/Central region.
        nc = nc_lrz[nc_lrz.area.isin([f"LRZ {i}" for i in range(1, 8)])]
        gross_avg = float(nc.y_value.mean())
        cap_frac_data = gross_avg / net_cone
        self.assertAlmostEqual(
            design.demand_curve[0].price_frac_net_cone, cap_frac_data, places=1
        )

    def test_caiso_proxy_recited_to_cpm_soft_offer_cap(self):
        # CAISO carries no curve; its fixed anchor is re-cited to the CPM
        # soft-offer cap. Assert the anchor is within 5% of the published cap.
        rows = self.dc.parse_iso("CAISO", RAW_DIR)
        soft_cap_month = float(
            rows[
                (rows.metric == "soft_offer_cap") & (rows.delivery_year == "2024")
            ].y_value.iloc[0]
        )
        soft_cap_yr = soft_cap_month * 12.0
        design = MARKET_DESIGN["CAISO"]
        self.assertEqual(design.demand_curve, ())
        self.assertLess(
            abs(design.net_cone_per_kw_yr - soft_cap_yr) / soft_cap_yr, 0.05
        )


if __name__ == "__main__":
    unittest.main()
