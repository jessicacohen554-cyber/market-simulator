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
    MARKET_DESIGN_VINTAGES,
    MISO_SEASONAL_RBDC,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    CapacityDemandCurvePoint,
    evaluate_demand_curve,
    resolve_capacity_curve_eligible,
    resolve_demand_curve_vintage,
    seasonal_rbdc_price_per_firm_mw_yr,
)
from market_sim.config.paths import RAW_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.capacity import (
    apply_economic_retirements,
    capacity_reserve_position,
    capacity_revenue_per_mw_yr,
    thermal_accreditation_fraction,
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
# MISO prices on the SEASONAL RBDC (RC-1C) — a four-season sum, NOT the single
# annual ``demand_curve`` — so the tests that assert the annual-curve identity
# (cap = demand_curve[0] × anchor; price == evaluate(demand_curve) × anchor) run
# on the annual-grain ISOs only; MISO's seasonal behavior has its own class
# (TestMISOSeasonalRBDC).
_ANNUAL_CURVE_ISOS = ("PJM", "NYISO", "NEISO")
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
            # The public thermal helper: the pre-CR-1 fixed price times the
            # unit's basis-resolved accreditation (R4) — (1-EFORd) for UCAP
            # ISOs, the ELCC class rating for PJM.
            eford = 0.05
            fuel = "gas_cc"
            frac = thermal_accreditation_fraction(fuel, eford, iso)
            self.assertEqual(
                capacity_revenue_per_mw_yr(iso, fuel, eford),
                expected * frac,
            )
            # Gate off: reserve_position is inert (None vs a number identical).
            self.assertEqual(
                capacity_revenue_per_mw_yr(iso, fuel, eford, _CFG_OFF, None),
                capacity_revenue_per_mw_yr(iso, fuel, eford, _CFG_OFF, 0.85),
            )

    def test_ercot_zero_both_modes(self):
        ercot = MARKET_DESIGN["ERCOT"]
        self.assertEqual(ercot.capacity_price_per_firm_mw_yr(), 0.0)
        self.assertEqual(ercot.capacity_price_per_firm_mw_yr(_CFG_ON, 0.80), 0.0)
        self.assertEqual(capacity_revenue_per_mw_yr("ERCOT", "gas_ct", 0.06), 0.0)
        self.assertEqual(
            capacity_revenue_per_mw_yr("ERCOT", "gas_ct", 0.06, _CFG_ON, 0.80), 0.0
        )

    def test_unknown_iso_zero_both_modes(self):
        # An ISO absent from the registry falls back to the energy-only default.
        self.assertEqual(capacity_revenue_per_mw_yr("MADEUP", "gas_cc", 0.05), 0.0)
        self.assertEqual(
            capacity_revenue_per_mw_yr("MADEUP", "gas_cc", 0.05, _CFG_ON, 0.9), 0.0
        )

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
        # net_cone_curve), never higher. (Annual-grain ISOs; MISO's seasonal
        # cap is asserted in TestMISOSeasonalRBDC.)
        for iso in _ANNUAL_CURVE_ISOS:
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
        # position, scaled by net-CONE — for every annual-grain ISO-curve and
        # position. (MISO is seasonal — TestMISOSeasonalRBDC covers it.)
        for iso in _ANNUAL_CURVE_ISOS:
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

    def test_thermal_revenue_is_price_times_accreditation(self):
        # The thermal payment applies the unit's basis-resolved accreditation
        # to the shared price (R4). For PJM that is the published ELCC class
        # rating (NOT (1-EFORd)), the SAME resolver the adequacy ledger uses,
        # so ledger and payment can never diverge.
        eford = 0.06
        price = MARKET_DESIGN["PJM"].capacity_price_per_firm_mw_yr(_CFG_ON, 1.015)
        for fuel, rating in (("gas_cc", 0.74), ("gas_ct", 0.60)):
            self.assertAlmostEqual(
                capacity_revenue_per_mw_yr("PJM", fuel, eford, _CFG_ON, 1.015),
                price * rating,
            )
        # A class PJM does not publish falls back to UCAP (biomass).
        self.assertAlmostEqual(
            capacity_revenue_per_mw_yr("PJM", "biomass", eford, _CFG_ON, 1.015),
            price * (1.0 - eford),
        )


class TestReservePosition(unittest.TestCase):
    """capacity_reserve_position — accredited firm / shared requirement."""

    def test_hand_computed_ratio(self):
        # NYISO: DR fraction 0, ICAP->UCAP ratio 1.0, UCAP thermal basis (R5a
        # left NYISO on the default pending owner sign-off), so the
        # requirement and accredited sums are hand-computable. (Was NEISO
        # until R5b moved it to the claimed-capability basis — see
        # TestClaimedCapabilityBasis in tests/test_capacity.py for that
        # basis's own dedicated coverage.)
        iso = "NYISO"
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
        # Net-CONE anchor: the published UCAP net-CONE ($/MW-day row × 365/1000),
        # the basis the VRR curve is drawn around and the auction clears in
        # (P-2B Option A anchor re-derivation, R1). NOT the 60,396 $/MW-yr
        # ICAP-annual row, which mis-scaled the UCAP curve by PJM's ~0.78 factor.
        net_cone_day = self._scalar(rows, "net_cone", y_unit="usd_per_mw_day")
        self.assertAlmostEqual(
            design.net_cone_curve_per_kw_yr, net_cone_day * 365.0 / 1000.0, 3
        )
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


class TestMarketDesignVintages(unittest.TestCase):
    """RC-1B item 2 — per-delivery-year vintage table + resolver.

    Trivial-first: resolution is checked against hand values; then every
    encoded anchor/cap fraction is reconciled against the same P-0B datatype
    (rule 13); then the pricing seam's byte-identity and vintage-override
    behavior are exercised.
    """

    ON = SimpleNamespace(capacity_market_clearing=True)
    OFF = SimpleNamespace(capacity_market_clearing=False)

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

    # ---- resolution vs hand values --------------------------------------
    def test_resolve_hold_first_exact_hold_last(self):
        # PJM spans 2021/2022 .. 2027/2028 (start years 2021..2027).
        self.assertEqual(
            resolve_demand_curve_vintage("PJM", 2019).delivery_year, "2021/2022"
        )  # hold-first (before the earliest)
        self.assertEqual(
            resolve_demand_curve_vintage("PJM", 2024).delivery_year, "2024/2025"
        )  # exact
        self.assertEqual(
            resolve_demand_curve_vintage("PJM", 2026).delivery_year, "2026/2027"
        )
        self.assertEqual(
            resolve_demand_curve_vintage("PJM", 2035).delivery_year, "2027/2028"
        )  # hold-last (after the latest)

    def test_resolve_miso_pre_rbdc_vertical_and_forward_hold_last(self):
        # MISO now carries the pre-RBDC (vertical-at-CONE) vintages 2021/22-2024/25
        # plus the seasonal PY2025-26 (RC-1C). A pre-RBDC year resolves to its own
        # vertical vintage (seasonal_rbdc is None, demand_curve is the vertical
        # step); the RBDC year and every later year hold-last to PY2025-26 (which
        # carries the seasonal RBDC).
        v2021 = resolve_demand_curve_vintage("MISO", 2021)
        self.assertEqual(v2021.delivery_year, "2021-2022")
        self.assertIsNone(v2021.seasonal_rbdc)
        self.assertNotEqual(v2021.demand_curve, ())  # vertical step, not ()
        v2024 = resolve_demand_curve_vintage("MISO", 2024)
        self.assertEqual(v2024.delivery_year, "2024-2025")
        self.assertIsNone(v2024.seasonal_rbdc)
        v2030 = resolve_demand_curve_vintage("MISO", 2030)
        self.assertEqual(v2030.delivery_year, "2025-2026")  # hold-last
        self.assertIsNotNone(v2030.seasonal_rbdc)  # seasonal grain
        # A year before the earliest MISO vintage holds-first to 2021-2022.
        self.assertEqual(
            resolve_demand_curve_vintage("MISO", 2018).delivery_year, "2021-2022"
        )

    def test_resolve_nyiso_flat_anchor_years_present(self):
        # 2021-2022/2022-2023 are present as ()-shape flat-anchor vintages, so a
        # 2021 model year resolves to 2021-2022 exactly (not held-first past it),
        # and a pre-span year holds-first to 2021-2022.
        self.assertEqual(
            resolve_demand_curve_vintage("NYISO", 2021).delivery_year, "2021-2022"
        )
        self.assertEqual(
            resolve_demand_curve_vintage("NYISO", 2019).delivery_year, "2021-2022"
        )
        self.assertEqual(
            resolve_demand_curve_vintage("NYISO", 2024).delivery_year, "2024-2025"
        )

    def test_resolve_none_cases(self):
        self.assertIsNone(resolve_demand_curve_vintage("PJM", None))
        self.assertIsNone(resolve_demand_curve_vintage(None, 2026))
        self.assertIsNone(resolve_demand_curve_vintage("CAISO", 2026))  # no table
        self.assertIsNone(resolve_demand_curve_vintage("ERCOT", 2026))

    def test_vintages_sorted_ascending(self):
        for iso, vints in MARKET_DESIGN_VINTAGES.items():
            starts = [int(v.delivery_year[:4]) for v in vints]
            self.assertEqual(starts, sorted(starts), f"{iso} not ascending")

    # ---- reconciliation vs the published datatype (rule 13) -------------
    def _expected_anchor(self, iso, dy):
        r = self._rows(iso, dy)
        if iso == "PJM":
            return self._scalar(r, "net_cone", y_unit="usd_per_mw_day") * 365.0 / 1000.0
        if iso == "NYISO":
            nc = r[(r.metric == "net_cone") & (r.area == "NYCA")]
            if not nc.empty:
                return float(nc.y_value.iloc[0])
            # 2021-22/22-23 published no Annual Reference Value — the flat anchor
            # is the NYCA monthly reference-point price × 12.
            nyca = r[r.area == "NYCA"]
            ref = float(
                nyca[nyca.metric == "curve_point"]
                .sort_values("point_index")
                .y_value.iloc[0]
            )
            return ref * 12.0
        if iso == "NEISO":
            return self._scalar(r, "net_cone") * 12.0
        if iso == "MISO":
            # PY2025-26 (RBDC): North/Central Net CONE ($/MW-yr -> $/kW-yr).
            nc = r[
                (r.metric == "net_cone")
                & (r.area == "North/Central")
                & (r.y_unit == "usd_per_mw_yr")
            ]
            if not nc.empty:
                return float(nc.y_value.iloc[0]) / 1000.0
            # Pre-RBDC (vertical-at-CONE): the North/Central gross-CONE anchor =
            # the LRZ 1-7 mean (the same aggregation the registry test uses),
            # converted to $/kW-yr from whichever unit that year publishes.
            g = r[
                (r.metric == "gross_cone")
                & (r.area.isin([f"LRZ {i}" for i in range(1, 8)]))
            ]
            mean = float(g.y_value.mean())
            unit = str(g.y_unit.iloc[0])
            return mean * 365.0 / 1000.0 if unit == "usd_per_mw_day" else mean / 1000.0
        raise AssertionError(iso)

    def test_all_vintage_anchors_reconcile_with_published(self):
        for iso, vints in MARKET_DESIGN_VINTAGES.items():
            for v in vints:
                self.assertAlmostEqual(
                    v.net_cone_curve_per_kw_yr,
                    self._expected_anchor(iso, v.delivery_year),
                    places=2,
                    msg=f"{iso} {v.delivery_year} anchor",
                )

    def _expected_cap_frac(self, iso, dy):
        r = self._rows(iso, dy)
        if iso == "PJM":
            nc = self._scalar(r, "net_cone", y_unit="usd_per_mw_day")
            if not r[r.metric == "price_cap"].empty:
                return self._scalar(r, "price_cap", y_unit="usd_per_mw_day") / nc
            # Vintages without a published price-cap row (pre-2026/27): the
            # curve maximum is point (a)'s own published UCAP price — from the
            # MW-basis curve_point rows (pre-CIFP) or the curve_point_ucap
            # rows (2025/26, whose curve_point rows are Manual-18 pct-basis
            # with formula-defined y left null).
            metric = (
                "curve_point_ucap"
                if not r[r.metric == "curve_point_ucap"].empty
                else "curve_point"
            )
            pts = r[r.metric == metric].sort_values("point_index")
            return float(pts.y_value.iloc[0]) / nc
        if iso == "NEISO":
            return self._scalar(r, "price_cap") / self._scalar(r, "net_cone")
        if iso == "NYISO":
            nyca = r[r.area == "NYCA"]
            if "summer" in set(nyca.season.dropna()):
                cap = self._scalar(r, "price_cap", area="NYCA", season="summer")
                ref = float(
                    nyca[(nyca.metric == "curve_point") & (nyca.season == "summer")]
                    .sort_values("point_index")
                    .y_value.iloc[0]
                )
            else:
                cap = self._scalar(r, "price_cap", area="NYCA")
                ref = float(
                    nyca[nyca.metric == "curve_point"]
                    .sort_values("point_index")
                    .y_value.iloc[0]
                )
            return cap / ref
        raise AssertionError(iso)

    def test_curve_cap_fractions_reconcile_with_published(self):
        # Every vintage that carries a shape reconciles its cap fraction to the
        # raw published values. MISO's RBDC shape is first-order (a band, not a
        # point — asserted by the registry test), so it is excluded here.
        for iso in ("PJM", "NYISO", "NEISO"):
            for v in MARKET_DESIGN_VINTAGES[iso]:
                if not v.demand_curve:
                    continue
                self.assertAlmostEqual(
                    v.demand_curve[0].price_frac_net_cone,
                    self._expected_cap_frac(iso, v.delivery_year),
                    places=3,
                    msg=f"{iso} {v.delivery_year} cap fraction",
                )

    def test_empty_curve_vintages_are_pre_reform_or_uncapped(self):
        # The ()-shape vintages are exactly NYISO's 2021-22/2022-23 (no Annual
        # Reference Value + no cap → flat anchor only). PJM's 2021/22-2025/26
        # gained published-derived normalized shapes in RC-1A (2026-07-16):
        # x = published UCAP point level ÷ (published Reliability Requirement
        # adjusted for FRR + published EE Addback), y = published point price ÷
        # published UCAP net-CONE. Assert exactly the remaining set, so a
        # future data update that adds a normalizable shape must update here.
        empties = {
            (iso, v.delivery_year)
            for iso, vints in MARKET_DESIGN_VINTAGES.items()
            for v in vints
            if not v.demand_curve
        }
        self.assertEqual(
            empties,
            {
                ("NYISO", "2021-2022"),
                ("NYISO", "2022-2023"),
            },
        )

    def test_pjm_vintage_shapes_reconcile_with_published(self):
        # RC-1A: every PJM 2021/22-2025/26 vintage shape point reconciles to
        # the datatype rows — x = level / (reliability_requirement_frr_adj +
        # ee_addback), y = price / net_cone — and the 2025/26 x-fractions land
        # on PJM's own committed Manual-18 pct_of_requirement curve_point rows
        # (the two published forms of the same curve).
        for dy in (
            "2021/2022",
            "2022/2023",
            "2023/2024",
            "2024/2025",
            "2025/2026",
        ):
            r = self._rows("PJM", dy)
            nc = self._scalar(r, "net_cone", y_unit="usd_per_mw_day")
            denom = self._scalar(r, "reliability_requirement_frr_adj") + self._scalar(
                r, "ee_addback"
            )
            metric = "curve_point_ucap" if dy == "2025/2026" else "curve_point"
            pts = r[r.metric == metric].sort_values("point_index")
            vintage = resolve_demand_curve_vintage("PJM", int(dy[:4]))
            self.assertEqual(vintage.delivery_year, dy)
            self.assertEqual(len(vintage.demand_curve), len(pts))
            for cp, (_, row) in zip(vintage.demand_curve, pts.iterrows()):
                self.assertAlmostEqual(
                    cp.reserve_ratio,
                    float(row.x_value) / denom,
                    places=6,
                    msg=f"PJM {dy} x point {row.point_index}",
                )
                self.assertAlmostEqual(
                    cp.price_frac_net_cone,
                    float(row.y_value) / nc,
                    places=6,
                    msg=f"PJM {dy} y point {row.point_index}",
                )
            if dy == "2025/2026":
                m18 = r[r.metric == "curve_point"].sort_values("point_index")
                for cp, (_, row) in zip(vintage.demand_curve, m18.iterrows()):
                    # <=0.1% agreement between the two published forms (the
                    # M18 pct rows are printed at 3 decimals).
                    self.assertAlmostEqual(
                        cp.reserve_ratio,
                        float(row.x_value),
                        delta=0.002,
                        msg=f"PJM 2025/26 M18 pct point {row.point_index}",
                    )

    # ---- pricing-seam behavior ------------------------------------------
    def test_reference_year_equals_registry_default(self):
        # At each ISO's registry reference delivery year, the vintage override
        # reproduces the no-year (registry) price exactly — byte-identity. (NYISO
        # is curve-INELIGIBLE — TestCurveEligibility covers it; MISO reproduces
        # its seasonal price both ways.)
        for iso, ref_year in (
            ("PJM", 2026),
            ("NEISO", 2027),
            ("MISO", 2025),
        ):
            design = MARKET_DESIGN[iso]
            for pos in (0.6, 0.9, 1.0, 1.05, 1.2):
                base = design.capacity_price_per_firm_mw_yr(self.ON, pos, iso=iso)
                with_year = design.capacity_price_per_firm_mw_yr(
                    self.ON, pos, iso=iso, year=ref_year
                )
                self.assertAlmostEqual(
                    base, with_year, places=6, msg=f"{iso} {ref_year} @ {pos}"
                )

    def test_empty_curve_vintage_prices_flat_anchor(self):
        # A ()-shape vintage (NYISO 2021-2022 — no published ARV/cap) prices
        # its flat anchor × 1000, independent of the reserve position (no
        # sloped curve). PJM's 2021/22-2025/26 vintages are no longer () —
        # RC-1A derived their published shapes — so NYISO carries this case.
        design = MARKET_DESIGN["NYISO"]
        flat = 7.81 * 12.0 * 1000.0
        for pos in (0.3, 0.85, 1.0, 1.4):
            self.assertAlmostEqual(
                design.capacity_price_per_firm_mw_yr(
                    self.ON, pos, iso="NYISO", year=2021
                ),
                flat,
                places=3,
            )

    def test_pjm_pre_cifp_vintage_prices_slope(self):
        # RC-1A: a threaded pre-CIFP PJM year prices on its own published
        # sloped shape — cap plateau below point (a), zero past its
        # zero-cross (1.0741 for 2021/2022), monotone in between.
        design = MARKET_DESIGN["PJM"]
        anchor = 321.57 * 365.0 / 1000.0
        cap = design.capacity_price_per_firm_mw_yr(self.ON, 0.90, iso="PJM", year=2021)
        self.assertAlmostEqual(cap, 1.5 * anchor * 1000.0, delta=anchor)
        mid = design.capacity_price_per_firm_mw_yr(self.ON, 1.05, iso="PJM", year=2021)
        self.assertGreater(cap, mid)
        self.assertGreater(mid, 0.0)
        self.assertEqual(
            design.capacity_price_per_firm_mw_yr(self.ON, 1.10, iso="PJM", year=2021),
            0.0,
        )

    def test_default_off_byte_identity_with_year(self):
        # Gate OFF: passing a year never changes the price (fixed path, no
        # vintage consultation) for any ISO.
        for iso, design in MARKET_DESIGN.items():
            expected = design.capacity_price_per_firm_mw_yr()
            self.assertEqual(
                design.capacity_price_per_firm_mw_yr(
                    self.OFF, 0.85, iso=iso, year=2022
                ),
                expected,
                msg=iso,
            )

    def test_year_changes_anchor_only_where_a_vintage_differs(self):
        # PJM: pricing 2022/2023 (flat 95.08) differs from 2026/2027 (curve
        # anchor 77.43) — the year is live. CAISO has no vintage table, so year
        # is inert (fixed proxy in both).
        pjm = MARKET_DESIGN["PJM"]
        self.assertNotAlmostEqual(
            pjm.capacity_price_per_firm_mw_yr(self.ON, 1.015, iso="PJM", year=2022),
            pjm.capacity_price_per_firm_mw_yr(self.ON, 1.015, iso="PJM", year=2026),
            places=1,
        )
        caiso = MARKET_DESIGN["CAISO"]
        self.assertEqual(
            caiso.capacity_price_per_firm_mw_yr(self.ON, 0.8, iso="CAISO", year=2021),
            caiso.capacity_price_per_firm_mw_yr(self.ON, 0.8, iso="CAISO", year=2035),
        )


class TestMISOSeasonalRBDC(unittest.TestCase):
    """RC-1C — MISO seasonal RBDC grain (prereq 4a), hand-computed.

    The seam sums four seasonal RBDC evaluations at ONE annual reserve position:
    Σ_season frac(position) × daily_net_cone × days. daily_net_cone =
    79,800/365 = 218.6301 $/MW-day; the four seasons weigh 92/91/90/92 = 365 days.
    """

    ON = SimpleNamespace(capacity_market_clearing=True)
    DAILY_NET = 79_800.0 / 365.0
    # PY2025-26 North/Central seasonal gross-CONE caps ($/MW-day) and day counts.
    SEASONS = (
        ("summer", 92, 1384.36),
        ("fall", 91, 1399.58),
        ("winter", 90, 1415.13),
        ("spring", 92, 1384.36),
    )

    def _price(self, pos):
        return MARKET_DESIGN["MISO"].capacity_price_per_firm_mw_yr(
            self.ON, pos, iso="MISO"
        )

    def test_structure(self):
        s = MISO_SEASONAL_RBDC
        self.assertEqual(len(s.seasons), 4)
        self.assertEqual(sum(x.days for x in s.seasons), 365)
        self.assertAlmostEqual(s.daily_net_cone_per_mw_day, self.DAILY_NET, places=4)
        # Summer's cap fraction ≈ gross 1384.36 / daily net 218.63 ≈ 6.33.
        self.assertAlmostEqual(
            s.seasons[0].demand_curve[0].price_frac_net_cone,
            1384.36 / self.DAILY_NET,
            places=4,
        )

    def test_at_requirement_reduces_to_annual_net_cone(self):
        # position 1.0: every season pays the flat daily net-CONE, so the sum is
        # EXACTLY the annual net-CONE (reduces to the annual curve).
        self.assertAlmostEqual(self._price(1.0), 79_800.0, places=3)
        # Byte-consistency with the shared seasonal function.
        self.assertAlmostEqual(
            self._price(1.0),
            seasonal_rbdc_price_per_firm_mw_yr(MISO_SEASONAL_RBDC, 1.0),
            places=6,
        )

    def test_long_pays_zero(self):
        # At/beyond the zero-cross (1.05) every season is 0.
        self.assertAlmostEqual(self._price(1.05), 0.0, places=6)
        self.assertAlmostEqual(self._price(1.2), 0.0, places=6)

    def test_deep_short_caps_at_seasonal_gross_sum(self):
        # Below the cap-plateau start (0.97) every season clamps to its own
        # gross-CONE cap, so the annual sum is Σ (gross_daily × days) — the
        # ceiling of the seasonal construction (~4× annual gross; the documented
        # one-position over-statement at a short position).
        expected = sum(gross * days for _, days, gross in self.SEASONS)
        self.assertAlmostEqual(self._price(0.3), expected, places=2)
        self.assertAlmostEqual(self._price(0.90), expected, places=2)

    def test_monotone_non_increasing(self):
        xs = np.linspace(0.5, 1.4, 91)
        ys = [self._price(x) for x in xs]
        self.assertTrue(all(ys[i] >= ys[i + 1] - 1e-6 for i in range(len(ys) - 1)))

    def test_short_exceeds_annual_curve(self):
        # A short position lifts the seasonal price above the annual-curve price
        # (each season reaches for its own, higher, seasonal cap).
        seasonal = self._price(0.985)
        annual = (
            evaluate_demand_curve(MARKET_DESIGN["MISO"].demand_curve, 0.985)
            * MARKET_DESIGN["MISO"].net_cone_curve_per_kw_yr
            * 1000.0
        )
        self.assertGreater(seasonal, annual)

    def test_pre_rbdc_year_is_vertical_at_cone(self):
        # A pre-RBDC MISO year (2023) resolves to the vertical-at-CONE vintage:
        # its gross-CONE anchor (103.04 $/kW-yr) when short, ~0 when long — no
        # seasonal sum, no invented slope.
        design = MARKET_DESIGN["MISO"]
        short = design.capacity_price_per_firm_mw_yr(
            self.ON, 0.95, iso="MISO", year=2023
        )
        self.assertAlmostEqual(short, 103.04 * 1000.0, places=1)
        long = design.capacity_price_per_firm_mw_yr(self.ON, 1.2, iso="MISO", year=2023)
        self.assertAlmostEqual(long, 0.0, places=3)


class TestCurveEligibility(unittest.TestCase):
    """RC-1C — curve-eligibility governance gate (NYISO ineligible)."""

    ON = SimpleNamespace(capacity_market_clearing=True)

    def test_resolver_defaults_and_nyiso_false(self):
        self.assertFalse(resolve_capacity_curve_eligible("NYISO"))
        for iso in ("PJM", "NEISO", "MISO"):
            self.assertTrue(resolve_capacity_curve_eligible(iso))
        # iso=None and an unknown ISO default ELIGIBLE (byte-identity / no
        # silent block of a new curve ISO).
        self.assertTrue(resolve_capacity_curve_eligible(None))
        self.assertTrue(resolve_capacity_curve_eligible("MADEUP"))

    def test_nyiso_prices_fixed_when_iso_supplied(self):
        # Gate ON + iso="NYISO": ineligible, so it prices the FIXED anchor
        # (110 $/kW-yr × 1000) at EVERY position and year — never the curve.
        nyiso = MARKET_DESIGN["NYISO"]
        fixed = nyiso.net_cone_per_kw_yr * 1000.0
        for pos in (0.3, 0.85, 1.0, 1.2):
            self.assertEqual(
                nyiso.capacity_price_per_firm_mw_yr(self.ON, pos, iso="NYISO"), fixed
            )
            self.assertEqual(
                nyiso.capacity_price_per_firm_mw_yr(
                    self.ON, pos, iso="NYISO", year=2024
                ),
                fixed,
            )

    def test_nyiso_iso_none_still_curves(self):
        # iso=None bypasses the eligibility gate (pre-RC-1C call sites), so the
        # curve still evaluates — this is what keeps default paths byte-identical.
        nyiso = MARKET_DESIGN["NYISO"]
        curved = nyiso.capacity_price_per_firm_mw_yr(self.ON, 0.8)
        self.assertNotEqual(curved, nyiso.net_cone_per_kw_yr * 1000.0)

    def test_eligible_iso_unaffected(self):
        # PJM is eligible → iso-supplied curve pricing matches iso=None.
        pjm = MARKET_DESIGN["PJM"]
        self.assertAlmostEqual(
            pjm.capacity_price_per_firm_mw_yr(self.ON, 0.9, iso="PJM"),
            pjm.capacity_price_per_firm_mw_yr(self.ON, 0.9),
            places=6,
        )

class TestScreenSeamThreading(unittest.TestCase):
    """RC-1A completion of RC-1B items 1/2: the screens' own call paths thread
    ``iso``/``year`` into the pricing seam, so the by-ISO gate and the
    per-delivery-year vintage anchor govern where the screens actually price
    (capacity_revenue_per_mw_yr, estimate_capacity_value) — not just at the
    MarketDesign method the earlier classes exercise directly.
    """

    BY_ISO_PJM = SimpleNamespace(
        capacity_market_clearing=False,
        capacity_market_clearing_by_iso={"PJM": True},
    )

    def test_by_iso_row_activates_thermal_payment_curve(self):
        # Scalar off + a PJM by-ISO row: the thermal payment prices on the
        # curve (position-dependent), not the fixed anchor — the probe arm's
        # exact configuration (run_capacity_hindcast --capacity-market-clearing).
        eford = 0.05
        fixed = capacity_revenue_per_mw_yr("PJM", "gas_cc", eford)
        long_pos = capacity_revenue_per_mw_yr(
            "PJM", "gas_cc", eford, self.BY_ISO_PJM, 1.15
        )
        short_pos = capacity_revenue_per_mw_yr(
            "PJM", "gas_cc", eford, self.BY_ISO_PJM, 0.99
        )
        self.assertEqual(long_pos, 0.0)  # past the VRR zero-cross (1.045)
        self.assertGreater(short_pos, 0.0)
        self.assertNotAlmostEqual(short_pos, fixed, places=1)

    def test_by_iso_row_does_not_leak_to_other_isos(self):
        # The PJM row must not arm MISO: with the scalar off, MISO stays on
        # its fixed anchor even when a reserve position is supplied.
        eford = 0.05
        self.assertEqual(
            capacity_revenue_per_mw_yr("MISO", "coal", eford, self.BY_ISO_PJM, 1.15),
            capacity_revenue_per_mw_yr("MISO", "coal", eford),
        )

    def test_year_threads_vintage_anchor_through_thermal_payment(self):
        # Gate on, PJM, position inside the priced region: the payment at
        # year=2021 prices on the 2021/2022 vintage, year=None on the registry
        # default — and the two must agree with the MarketDesign seam priced
        # the same way (the threading adds no arithmetic of its own).
        eford = 0.05
        frac = thermal_accreditation_fraction("gas_cc", eford, "PJM")
        design = MARKET_DESIGN["PJM"]
        for year in (None, 2021, 2025):
            self.assertAlmostEqual(
                capacity_revenue_per_mw_yr("PJM", "gas_cc", eford, _CFG_ON, 1.0, year),
                design.capacity_price_per_firm_mw_yr(_CFG_ON, 1.0, iso="PJM", year=year)
                * frac,
            )
        # And the vintage is live: 2021 (pre-reform flat anchor) differs from
        # the registry-default (2026/27 curve) price at the same position.
        self.assertNotAlmostEqual(
            capacity_revenue_per_mw_yr("PJM", "gas_cc", eford, _CFG_ON, 1.0, 2021),
            capacity_revenue_per_mw_yr("PJM", "gas_cc", eford, _CFG_ON, 1.0, None),
            places=1,
        )

    def test_year_none_and_gate_off_stay_byte_identical(self):
        # Default paths: gate off (any year) == pre-RC-1B fixed price.
        eford = 0.05
        base = capacity_revenue_per_mw_yr("PJM", "gas_cc", eford)
        for year in (None, 2021, 2026):
            self.assertEqual(
                capacity_revenue_per_mw_yr(
                    "PJM", "gas_cc", eford, _CFG_OFF, 0.99, year
                ),
                base,
            )

    def test_storage_seam_threads_iso_and_year(self):
        # estimate_capacity_value: by-ISO gate + vintage anchor reach storage.
        config_by_iso = ScenarioConfig(
            iso="PJM",
            storage_capacity_value=True,
            capacity_market_clearing_by_iso={"PJM": True},
        )
        long_v = estimate_capacity_value(
            "li_ion_4hr", 0.0, config_by_iso, "PJM", reserve_position=1.15
        )
        short_v = estimate_capacity_value(
            "li_ion_4hr", 0.0, config_by_iso, "PJM", reserve_position=0.99
        )
        self.assertEqual(long_v, 0.0)
        self.assertGreater(short_v, 0.0)
        # Vintage: 2021 (flat pre-reform anchor) vs registry default differ.
        v_2021 = estimate_capacity_value(
            "li_ion_4hr", 0.0, config_by_iso, "PJM", reserve_position=1.0, year=2021
        )
        v_default = estimate_capacity_value(
            "li_ion_4hr", 0.0, config_by_iso, "PJM", reserve_position=1.0
        )
        self.assertNotAlmostEqual(v_2021, v_default, places=1)


if __name__ == "__main__":
    unittest.main()
