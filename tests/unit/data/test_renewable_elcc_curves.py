"""Tests for the CR-3.1 penetration-indexed renewable ELCC curves.

Trivial-first (CLAUDE.md testing pattern): the curve evaluator is exercised on
a hand-computed synthetic curve, then on the published per-ISO points, then
through the resolution ladder and the adequacy-ledger consumers. Covers the
P-2C charter's acceptance list (docs/handoffs/
forecast-driver-capacity-revenue-audit-plan-2026-07.md §3.4.1): interpolation
vs hand values, credit falls as penetration rises, the frozen-penetration
byte-compat mode, the storage no-double-derate guarantee (rule 19), and the
reconciliation of every encoded point against the P-0B
``capacity-market-elcc`` datatype (rule 13 — published input, never a fit
target). Ends with the #2063 regression lock (ira_phaseout_fraction fields).
"""

import unittest

from market_sim.config.capacity_market import PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE
from market_sim.config.constants import (
    RENEWABLE_CAPACITY_CREDIT,
    RENEWABLE_CAPACITY_CREDIT_BY_ISO,
    RENEWABLE_ELCC_CURVES_BY_ISO,
    RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO,
    RenewableElccCurve,
    evaluate_renewable_elcc_curve,
)
from market_sim.config.paths import RAW_DIR
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import Generator
from market_sim.model.capacity import (
    accredited_firm_capacity_mw,
    capacity_reserve_position,
    renewable_credits_applied,
    resolve_renewable_capacity_credit,
    vre_accreditation_vintage_armed,
)
from tests.helpers.builders import no_hydro_accreditation

# A hand-computable synthetic declining curve on the installed-MW axis:
# 50% at 1 GW, 30% at 2 GW, 10% at 4 GW.
_SYNTH = RenewableElccCurve(
    penetration_basis="installed_mw",
    points=((1000.0, 0.50), (2000.0, 0.30), (4000.0, 0.10)),
    source="synthetic (test)",
)


def _gas_unit(mw: float = 1000.0, eford: float = 0.05) -> Generator:
    return Generator(
        unit_id="G0",
        name="G0",
        zone="Z0",
        fuel_type="gas_cc",
        pmax_mw=mw,
        heat_rate=7.0,
        eford=eford,
    )


class TestCurveEvaluator(unittest.TestCase):
    """evaluate_renewable_elcc_curve — pure math on a synthetic curve."""

    def test_interpolation_hand_values(self):
        # Midpoint of the first segment: (0.50 + 0.30) / 2 at 1.5 GW.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(_SYNTH, 1500.0, None), 0.40
        )
        # Quarter point of the second segment: 0.30 + 0.25 x (0.10 - 0.30).
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(_SYNTH, 2500.0, None), 0.25
        )
        # Exactly on a published point.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(_SYNTH, 2000.0, None), 0.30
        )

    def test_flat_clamp_both_ends(self):
        # Below the first point the credit clamps to the first value; beyond
        # the last it holds the endpoint — no extrapolated slope is invented.
        self.assertAlmostEqual(evaluate_renewable_elcc_curve(_SYNTH, 0.0, None), 0.50)
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(_SYNTH, 99000.0, None), 0.10
        )

    def test_credit_falls_as_penetration_rises(self):
        # The charter's directional property on a declining published curve.
        credits = [
            evaluate_renewable_elcc_curve(_SYNTH, mw, None)
            for mw in (1000.0, 1500.0, 2000.0, 3000.0, 4000.0)
        ]
        for lo, hi in zip(credits[1:], credits):
            self.assertLess(lo, hi)

    def test_pct_of_peak_basis_needs_peak(self):
        curve = RenewableElccCurve(
            penetration_basis="pct_of_peak_load",
            points=((10.0, 0.20), (20.0, 0.10)),
            source="synthetic (test)",
        )
        # 15% of peak: midpoint.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 15_000.0, 100_000.0), 0.15
        )
        # Peak unavailable -> None so the caller falls back (never misprice).
        self.assertIsNone(evaluate_renewable_elcc_curve(curve, 15_000.0, None))
        self.assertIsNone(evaluate_renewable_elcc_curve(curve, 15_000.0, 0.0))

    def test_installed_mw_basis_needs_installed(self):
        self.assertIsNone(evaluate_renewable_elcc_curve(_SYNTH, None, 100_000.0))

    def test_single_point_curve_is_constant(self):
        point = RenewableElccCurve(
            penetration_basis=None,
            points=((0.0, 0.1684),),
            source="synthetic (test)",
        )
        for mw in (None, 0.0, 1e6):
            self.assertAlmostEqual(
                evaluate_renewable_elcc_curve(point, mw, None), 0.1684
            )

    def test_unknown_basis_returns_none(self):
        bad = RenewableElccCurve(
            penetration_basis="pct_of_installed_capacity",  # no conversion wired
            points=((1.0, 0.5),),
            source="synthetic (test)",
        )
        self.assertIsNone(evaluate_renewable_elcc_curve(bad, 1.0, 1.0))


class TestPublishedCurveHandValues(unittest.TestCase):
    """The encoded per-ISO points, evaluated at hand-computed positions."""

    def test_pjm_solar_declines_and_clamps(self):
        curve = RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]["solar"]
        # At the two published fleet sizes: the MW-weighted blends.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 9902.0, None), 0.1064
        )
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 13106.0, None), 0.0789
        )
        # Midpoint of the segment by hand.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, (9902.0 + 13106.0) / 2.0, None),
            (0.1064 + 0.0789) / 2.0,
        )
        # Beyond the published domain: clamp, and still monotone non-rising.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 40_000.0, None), 0.0789
        )

    def test_pjm_wind_flat_at_published_rating(self):
        curve = RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]["wind"]
        for mw in (1000.0, 3549.0, 3956.0, 12_000.0):
            self.assertAlmostEqual(evaluate_renewable_elcc_curve(curve, mw, None), 0.41)

    def test_miso_wind_pct_of_peak_hand_values(self):
        curve = RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]["wind"]
        peak = 100_000.0
        # On published points: 7.6% -> 0.080, 16.7% -> 0.166.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 7_600.0, peak), 0.080
        )
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 16_700.0, peak), 0.166
        )
        # Hand midpoint of the first segment: 8.65% -> (0.080 + 0.129) / 2.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 8_650.0, peak),
            (0.080 + 0.129) / 2.0,
        )
        # MISO's published curve RISES with penetration (geographic
        # dispersion era) and clamps at its endpoint beyond 16.7% of peak —
        # the model follows the published shape, never an assumed decline.
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(curve, 28_335.0, 127_000.0), 0.166
        )

    def test_miso_solar_constant_at_season_weighted_credit(self):
        # FFR-4B: a flat published default -> a constant curve at every
        # penetration, and it must NOT need the peak (unlike MISO wind).
        curve = RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]["solar"]
        for mw, peak in ((None, None), (0.0, 100_000.0), (60_000.0, 127_000.0)):
            self.assertAlmostEqual(
                evaluate_renewable_elcc_curve(curve, mw, peak), 0.3875
            )
        # And it displaces the generic 0.18 fallback through the ladder.
        self.assertAlmostEqual(
            resolve_renewable_capacity_credit(
                "solar", "MISO", installed_mw=None, curves_enabled=True
            ),
            0.3875,
        )
        self.assertAlmostEqual(
            resolve_renewable_capacity_credit(
                "solar", "MISO", installed_mw=None, curves_enabled=False
            ),
            RENEWABLE_CAPACITY_CREDIT["solar"],
        )

    def test_nyiso_single_points(self):
        ny = RENEWABLE_ELCC_CURVES_BY_ISO["NYISO"]
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(ny["wind"], 5_000.0, 32_000.0), 0.1684
        )
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(ny["solar"], None, None), 0.1224
        )
        self.assertAlmostEqual(
            evaluate_renewable_elcc_curve(ny["offshore_wind"], None, None), 0.3579
        )


class TestResolutionLadder(unittest.TestCase):
    """resolve_renewable_capacity_credit — curve > point override > generic."""

    def test_frozen_mode_reproduces_legacy_everywhere(self):
        # curves_enabled=False is the frozen-penetration byte-compat mode:
        # every (ISO, fuel) resolves exactly as pre-CR-3.1.
        for iso in ("PJM", "MISO", "NYISO", "NEISO", "CAISO", "ERCOT", None):
            for fuel in ("wind", "solar", "offshore_wind", "hydro"):
                legacy = (RENEWABLE_CAPACITY_CREDIT_BY_ISO.get(iso or "", {})).get(
                    fuel, RENEWABLE_CAPACITY_CREDIT.get(fuel)
                )
                self.assertEqual(
                    resolve_renewable_capacity_credit(
                        fuel,
                        iso,
                        installed_mw=12_345.0,
                        peak_demand_mw=98_765.0,
                        curves_enabled=False,
                    ),
                    legacy,
                    msg=f"{iso}/{fuel}",
                )

    def test_curve_wins_when_enabled(self):
        self.assertAlmostEqual(
            resolve_renewable_capacity_credit(
                "wind", "PJM", installed_mw=12_000.0, curves_enabled=True
            ),
            0.41,
        )

    def test_axis_unavailable_falls_back_to_point_basis(self):
        # MISO wind's curve needs the peak; without it the generic constant
        # answers — a curve can never silently misprice.
        self.assertEqual(
            resolve_renewable_capacity_credit(
                "wind",
                "MISO",
                installed_mw=28_335.0,
                peak_demand_mw=None,
                curves_enabled=True,
            ),
            RENEWABLE_CAPACITY_CREDIT["wind"],
        )

    def test_ercot_stays_on_cdr_point_override(self):
        # ERCOT has no curve (CDR basis stays, plan §3.4.1): curves on/off
        # both resolve the published BY_ISO override.
        for enabled in (True, False):
            self.assertEqual(
                resolve_renewable_capacity_credit(
                    "wind",
                    "ERCOT",
                    installed_mw=40_000.0,
                    peak_demand_mw=85_000.0,
                    curves_enabled=enabled,
                ),
                0.20,
            )

    def test_no_study_isos_keep_generic_fallback(self):
        # NEISO (third-party-only studies) and CAISO (incremental-basis-only
        # study) are deliberately absent from the curve registry — the
        # documented neutral fallback (rule 25 spirit).
        self.assertNotIn("NEISO", RENEWABLE_ELCC_CURVES_BY_ISO)
        self.assertNotIn("CAISO", RENEWABLE_ELCC_CURVES_BY_ISO)
        for iso in ("NEISO", "CAISO"):
            self.assertEqual(
                resolve_renewable_capacity_credit(
                    "solar",
                    iso,
                    installed_mw=5_000.0,
                    peak_demand_mw=25_000.0,
                    curves_enabled=True,
                ),
                RENEWABLE_CAPACITY_CREDIT["solar"],
            )

    def test_thermal_resolves_none(self):
        self.assertIsNone(
            resolve_renewable_capacity_credit("gas_cc", "PJM", curves_enabled=True)
        )


class TestAccreditedLedger(unittest.TestCase):
    """accredited_firm_capacity_mw with the curves on/off (hand-computed)."""

    def setUp(self):
        # Hand-computed VRE/thermal ledger arithmetic: zero the FFR-1C hydro
        # pool so PJM's real EIA hydro census stays out of these sums (the
        # hydro term has its own tests in test_hydro_accreditation.py).
        patcher = no_hydro_accreditation()
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_hand_computed_pjm_ledger_curves_on(self):
        # 1 x 1000 MW gas-CC accredited at PJM's published ELCC class rating
        # 0.74 (740 MW — R3 elcc_class_rating basis, NOT the (1-EFORd)=950 UCAP)
        # + 1000 MW wind pool at the published 0.41 clamp + 1000 MW solar pool
        # at the published 0.1064 clamp (both pools below the first curve point)
        # + PJM's 1,281.7 MW cleared BRA import UCAP (W2-D external-tie term).
        firm = accredited_firm_capacity_mw(
            [_gas_unit()],
            wind_pool_mw=1000.0,
            solar_pool_mw=1000.0,
            storage_firm_mw=0.0,
            iso="PJM",
            peak_demand_mw=100_000.0,
            elcc_curves_enabled=True,
        )
        self.assertAlmostEqual(firm, 740.0 + 410.0 + 106.4 + 1_281.7)

    def test_hand_computed_pjm_ledger_frozen_mode(self):
        # Same fleet, frozen-penetration VRE mode: the pre-CR-3.1 flat VRE
        # credits. Thermal is still on PJM's ELCC class rating (740, R3) — the
        # elcc_curves gate is a VRE-only switch and never re-derates thermal.
        # The W2-D external-tie term (1,281.7 MW) is VRE-mode-independent.
        firm = accredited_firm_capacity_mw(
            [_gas_unit()],
            wind_pool_mw=1000.0,
            solar_pool_mw=1000.0,
            storage_firm_mw=0.0,
            iso="PJM",
            peak_demand_mw=100_000.0,
            elcc_curves_enabled=False,
        )
        self.assertAlmostEqual(firm, 740.0 + 160.0 + 180.0 + 1_281.7)

    def test_default_args_reproduce_legacy_signature(self):
        # Callers that never pass the new kwargs get the pre-CR-3.1 result.
        legacy = accredited_firm_capacity_mw(
            [_gas_unit()], 1000.0, 1000.0, 0.0, iso="PJM"
        )
        frozen = accredited_firm_capacity_mw(
            [_gas_unit()],
            1000.0,
            1000.0,
            0.0,
            iso="PJM",
            peak_demand_mw=100_000.0,
            elcc_curves_enabled=False,
        )
        self.assertAlmostEqual(legacy, frozen)

    def test_per_mw_solar_credit_falls_as_pjm_solar_grows(self):
        # The saturation feedback: the ledger's solar $/MW accreditation
        # falls as the model's own solar pool grows through the published
        # declining curve.
        def solar_credit(pool_mw: float) -> float:
            base = accredited_firm_capacity_mw(
                [],
                0.0,
                0.0,
                0.0,
                iso="PJM",
                peak_demand_mw=100_000.0,
                elcc_curves_enabled=True,
            )
            with_solar = accredited_firm_capacity_mw(
                [],
                0.0,
                pool_mw,
                0.0,
                iso="PJM",
                peak_demand_mw=100_000.0,
                elcc_curves_enabled=True,
            )
            return (with_solar - base) / pool_mw

        credits = [solar_credit(mw) for mw in (9_902.0, 11_504.0, 13_106.0)]
        self.assertGreater(credits[0], credits[1])
        self.assertGreater(credits[1], credits[2])

    def test_storage_passthrough_untouched_rule19(self):
        # Rule 19 (no double-derate): the pre-accredited storage_firm_mw
        # passes through the ledger EXACTLY in both modes — the wind/solar
        # curve mechanism never re-derates storage (its duration-ELCC /
        # saturation / dilution stack lives in storage.py + the evolve seam).
        for enabled in (True, False):
            without = accredited_firm_capacity_mw(
                [_gas_unit()],
                500.0,
                500.0,
                0.0,
                iso="PJM",
                peak_demand_mw=100_000.0,
                elcc_curves_enabled=enabled,
            )
            with_storage = accredited_firm_capacity_mw(
                [_gas_unit()],
                500.0,
                500.0,
                1234.5,
                iso="PJM",
                peak_demand_mw=100_000.0,
                elcc_curves_enabled=enabled,
            )
            self.assertAlmostEqual(with_storage - without, 1234.5)

    def test_fleet_units_count_toward_penetration(self):
        # A wind Generator in the fleet adds to the class nameplate, so the
        # pool + fleet split cannot change the resolved class credit.
        wind_gen = Generator(
            unit_id="W0",
            name="W0",
            zone="Z0",
            fuel_type="wind",
            pmax_mw=6_000.0,
            heat_rate=0.0,
            eford=0.0,
        )
        split = renewable_credits_applied(
            [wind_gen],
            6_000.0,
            0.0,
            "MISO",
            peak_demand_mw=100_000.0,
            elcc_curves_enabled=True,
        )
        pooled = renewable_credits_applied(
            [],
            12_000.0,
            0.0,
            "MISO",
            peak_demand_mw=100_000.0,
            elcc_curves_enabled=True,
        )
        self.assertAlmostEqual(split["wind"], pooled["wind"])
        # And the hand value: 12% of peak on the MISO curve -> between the
        # published 11.8% (0.141) and 12.2% (0.147) points.
        self.assertAlmostEqual(
            split["wind"], 0.141 + (12.0 - 11.8) / (12.2 - 11.8) * (0.147 - 0.141)
        )

    def test_reserve_position_moves_with_the_gate(self):
        # The CR-1 curve position consumes the same ledger: PJM position
        # shifts when the curves flip on (wind up 0.16 -> 0.41 dominates).
        gen = _gas_unit()
        pos_on = capacity_reserve_position(
            [gen],
            5_000.0,
            5_000.0,
            0.0,
            ScenarioConfig(iso="PJM", renewable_elcc_curves=True),
            "PJM",
            20_000.0,
        )
        pos_off = capacity_reserve_position(
            [gen],
            5_000.0,
            5_000.0,
            0.0,
            ScenarioConfig(iso="PJM", renewable_elcc_curves=False),
            "PJM",
            20_000.0,
        )
        self.assertGreater(pos_on, pos_off)


class TestP0BElccReconciliation(unittest.TestCase):
    """Every encoded constant point matches the committed P-0B datatype rows.

    Rule 13/23 discipline (the P-1B demand-curve precedent): the constants
    are digitized FROM data/raw/capacity-market/elcc/ and this test fails if
    they ever drift from the committed source rows.
    """

    @classmethod
    def setUpClass(cls):
        from scripts.lib import capacity_market_elcc as elcc

        cls.elcc = elcc

    def _rows(self, iso: str):
        return self.elcc.parse_iso(iso, RAW_DIR)

    def test_pjm_wind_points_match_published(self):
        df = self._rows("PJM")
        wind = df[
            (df["resource_class"] == "wind")
            & (df["study_vintage"].str.contains("official/final"))
        ]
        published = {
            (float(r.penetration_pct), float(r.elcc_pct) / 100.0)
            for r in wind.itertuples()
        }
        encoded = set(RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]["wind"].points)
        self.assertEqual(encoded, published)

    def test_pjm_solar_blend_rederives_from_published_rows(self):
        df = self._rows("PJM")
        solar = df[
            (df["resource_class"] == "solar")
            & (df["study_vintage"].str.contains("official/final"))
        ]
        # Re-derive the MW-weighted blend per vintage from the raw rows.
        rederived = set()
        for vintage, grp in solar.groupby("study_vintage"):
            mw = grp["penetration_pct"].astype(float)
            rating = grp["elcc_pct"].astype(float) / 100.0
            rederived.add(
                (
                    round(float(mw.sum()), 1),
                    round(float((mw * rating).sum() / mw.sum()), 4),
                )
            )
        encoded = {
            (round(x, 1), round(c, 4))
            for x, c in RENEWABLE_ELCC_CURVES_BY_ISO["PJM"]["solar"].points
        }
        self.assertEqual(encoded, rederived)

    def test_miso_wind_points_match_published(self):
        df = self._rows("MISO")
        rows = df[
            (df["resource_class"] == "wind")
            & (df["study_vintage"] == "2019 Wind & Solar Capacity Credit Report")
            & (df["elcc_type"] == "class_average")
        ]
        published = {
            (float(r.penetration_pct), round(float(r.elcc_pct) / 100.0, 4))
            for r in rows.itertuples()
        }
        encoded = {
            (x, round(c, 4))
            for x, c in RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]["wind"].points
        }
        # The constants dedupe the identical PY2012/PY2015 point; the sets
        # are equal because a set collapses that duplicate the same way.
        self.assertEqual(encoded, published)
        # And the axis is what the study published.
        self.assertEqual(
            RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]["wind"].penetration_basis,
            "pct_of_peak_load",
        )

    def test_miso_solar_season_weighted_rederives_from_published_rows(self):
        """0.3875 re-derives from the committed rows by the settled rule.

        FFR-4B / owner D-12: MISO's published solar credit is SEASONAL (50 %
        Summer/Fall/Spring, 5 % Winter) and this registry is ANNUAL. The
        settled selection rule is the duration-weighted mean over MISO's four
        equal-length PRA seasons, i.e. the plain mean with weights 3 and 1 —
        re-derived here from the CSV so the constant can never drift from the
        source rows (the same discipline as the PJM MW-weighted blend).
        """
        df = self._rows("MISO")
        rows = df[
            (df["resource_class"] == "solar")
            & (df["study_vintage"] == "2025-2026 PY report")
            & (df["elcc_type"] == "class_average")
        ]
        self.assertEqual(len(rows), 2, "expected the two published seasonal rows")
        winter = rows[rows["source_page"].str.contains("Winter", regex=False)]
        non_winter = rows[~rows["source_page"].str.contains("Winter", regex=False)]
        self.assertEqual(len(winter), 1)
        self.assertEqual(len(non_winter), 1)
        # Three equal-length non-winter seasons (Summer/Fall/Spring) + Winter.
        rederived = (
            (
                3.0 * float(non_winter["elcc_pct"].iloc[0])
                + float(winter["elcc_pct"].iloc[0])
            )
            / 4.0
            / 100.0
        )
        curve = RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]["solar"]
        self.assertAlmostEqual(curve.points[0][1], rederived)
        self.assertAlmostEqual(curve.points[0][1], 0.3875)
        # MISO published a FLAT default, not a penetration curve: the encoded
        # entry must never fabricate an axis (P-0B intake discipline).
        self.assertIsNone(curve.penetration_basis)
        self.assertEqual(len(curve.points), 1)

    def test_nyiso_points_match_published_ros_li(self):
        df = self._rows("NYISO")
        caf = df[df["study_vintage"] == "2025-2026"]

        def _published(resource_class: str, region: str) -> float:
            rows = caf[
                (caf["resource_class"] == resource_class)
                & (caf["source_page"].str.contains(f"[REGION: {region}]", regex=False))
            ]
            self.assertEqual(len(rows), 1)
            return float(rows["elcc_pct"].iloc[0]) / 100.0

        ny = RENEWABLE_ELCC_CURVES_BY_ISO["NYISO"]
        self.assertAlmostEqual(ny["wind"].points[0][1], _published("wind", "ROS"))
        self.assertAlmostEqual(ny["solar"].points[0][1], _published("solar", "ROS"))
        self.assertAlmostEqual(
            ny["offshore_wind"].points[0][1], _published("wind_offshore", "LI")
        )

    def test_registry_curves_are_sorted_and_in_unit_range(self):
        for iso, curves in RENEWABLE_ELCC_CURVES_BY_ISO.items():
            for fuel, curve in curves.items():
                xs = [x for x, _ in curve.points]
                self.assertEqual(xs, sorted(xs), msg=f"{iso}/{fuel} axis order")
                for _, credit in curve.points:
                    self.assertGreaterEqual(credit, 0.0, msg=f"{iso}/{fuel}")
                    self.assertLessEqual(credit, 1.0, msg=f"{iso}/{fuel}")
                self.assertTrue(curve.source, msg=f"{iso}/{fuel} needs a citation")


class TestIraPhaseoutRegression2063(unittest.TestCase):
    """#2063 lock: the OBBBA step-schedule fields resolve on a default config.

    The T1.6/T1.9 driver-battery rungs crashed with AttributeError because
    ira_phaseout_fraction referenced ScenarioConfig fields that had not
    landed. P-1C added them; this locks the step schedule end-to-end so the
    crash class cannot silently return.
    """

    def test_step_schedule_on_default_config(self):
        from market_sim.policy.ira import ira_phaseout_fraction

        config = ScenarioConfig()
        expected = {2030: 1.0, 2033: 1.0, 2034: 0.75, 2035: 0.50, 2036: 0.0, 2050: 0.0}
        for year, frac in expected.items():
            self.assertEqual(ira_phaseout_fraction(year, config), frac)


class TestPjmVreAccreditationVintage(unittest.TestCase):
    """capx D75-R — the delivery-year VINTAGE axis on PJM VRE accreditation.

    Three duties, in the order the rules impose them: the encoded ratings are
    PJM's own published numbers and nothing else (rules 13/23 — reconciled
    byte-for-byte to the committed source rows); the gate is default-OFF and
    inert everywhere it is not armed (rules 5/24/25 — every other ISO and every
    unarmed run byte-identical); and the axis cannot be devintaged apart from
    the D48 thermal half (rule 19).
    """

    _PJM_DY_PUBLISHED = {
        # delivery year -> (raw study_vintage label, wind %, fixed %, tracking %)
        "2023/2024": (
            "2023/2024 BRA (final for DY 2023/2024; posted 2021-12-16)",
            15.0,
            38.0,
            54.0,
        ),
        "2024/2025": (
            "2024/2025 (Dec 2023 ELCC Report -- FINAL for DY 2024/2025)",
            21.0,
            33.0,
            50.0,
        ),
        "2025/2026": (
            "2025/2026 3IA (final for DY 2025/2026; posted 2025-03-12)",
            38.0,
            10.0,
            14.0,
        ),
    }

    @staticmethod
    def _raw_pjm_rows():
        import csv

        path = RAW_DIR / "capacity-market" / "elcc" / "pjm" / "pjm.csv"
        with path.open(newline="") as fh:
            return list(csv.DictReader(fh))

    @staticmethod
    def _armed(**kw) -> ScenarioConfig:
        return ScenarioConfig(
            mode="forecast",
            iso="PJM",
            hindcast=True,
            pjm_accreditation_design_vintage=True,
            pjm_vre_accreditation_vintage=True,
            **kw,
        )

    # --- provenance: every encoded rating is a published PJM class rating --- #

    def test_every_vintage_rating_rederives_from_the_committed_rows(self):
        """Wind verbatim; solar the declared mix of PJM's two solar classes.

        This is the whole DOF story of the mechanism (rule 21): the only thing
        that is not a transcribed number is the fixed/tracking blend weight,
        and that weight is itself PJM's own published 2026/27 installed-MW
        pairing, re-derived here from the same committed rows rather than
        typed. Nothing is fitted, and there is nothing else to fit.
        """
        rows = self._raw_pjm_rows()

        def _rating(vintage: str, cls: str) -> float:
            hits = [
                float(r["elcc_pct"])
                for r in rows
                if r["study_vintage"] == vintage and r["resource_class"] == cls
            ]
            self.assertEqual(len(hits), 1, f"{vintage} / {cls}")
            return hits[0]

        def _official_mw(cls: str) -> float:
            hits = [
                float(r["penetration_pct"])
                for r in rows
                if r["study_vintage"] == "2026/2027 BRA (official/final)"
                and r["resource_class"] == cls
            ]
            self.assertEqual(len(hits), 1, cls)
            return hits[0]

        # The declared cross-vintage reconciliation, re-derived from the ONLY
        # installed-MW pairing PJM publishes (ELCC/RRS Table 5, 2026/27).
        fixed_mw = _official_mw("Fixed-Tilt Solar")
        tracking_mw = _official_mw("Tracking Solar")
        fixed_share = fixed_mw / (fixed_mw + tracking_mw)
        self.assertAlmostEqual(fixed_share, PJM_SOLAR_CLASS_MIX_FIXED_TILT_SHARE, 12)

        table = RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]
        self.assertEqual(set(table), set(self._PJM_DY_PUBLISHED))
        for dy, (vintage, wind, fixed, tracking) in self._PJM_DY_PUBLISHED.items():
            # Whichever naming that vintage's posting used for its two solar
            # classes — PJM renamed them at the reform.
            fixed_label = (
                "Solar Fixed Panel"
                if any(
                    r["study_vintage"] == vintage
                    and r["resource_class"] == "Solar Fixed Panel"
                    for r in rows
                )
                else "Fixed-Tilt Solar"
            )
            tracking_label = (
                "Solar Tracking Panel"
                if fixed_label == "Solar Fixed Panel"
                else "Tracking Solar"
            )
            self.assertEqual(_rating(vintage, "Onshore Wind"), wind, dy)
            self.assertEqual(_rating(vintage, fixed_label), fixed, dy)
            self.assertEqual(_rating(vintage, tracking_label), tracking, dy)
            self.assertAlmostEqual(table[dy]["wind"], wind / 100.0, 12, dy)
            self.assertAlmostEqual(
                table[dy]["solar"],
                fixed_share * fixed / 100.0 + (1.0 - fixed_share) * tracking / 100.0,
                12,
                dy,
            )

    def test_the_2024_25_row_is_the_final_study_not_the_superseded_one(self):
        # The repository also carries PJM's December 2021 preliminary 2024/25
        # set (wind 16 %, solar 36/54 %). Wiring THAT would be a stale
        # published number on the accreditation path — rule 14 forbids it as
        # squarely as an estimate (FINDING-capx-d75 §1.1).
        superseded = {
            r["resource_class"]: float(r["elcc_pct"])
            for r in self._raw_pjm_rows()
            if "Dec 2021 ELCC Report" in r["study_vintage"]
        }
        self.assertEqual(superseded["Onshore Wind"], 16.0)
        encoded = RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]["2024/2025"]
        self.assertAlmostEqual(encoded["wind"], 0.21, 12)
        self.assertNotAlmostEqual(encoded["wind"], 0.16, 3)

    # --- the gate: default-off, PJM-only, never apart from the D48 half ----- #

    def test_default_config_is_unarmed_and_the_ladder_is_unchanged(self):
        config = ScenarioConfig(mode="forecast", iso="PJM", hindcast=True)
        self.assertFalse(config.pjm_vre_accreditation_vintage)
        self.assertFalse(vre_accreditation_vintage_armed(config, "PJM"))
        for year in (2023, 2024, 2025):
            for fuel, expected in (("wind", 0.41), ("solar", 0.1064)):
                self.assertAlmostEqual(
                    resolve_renewable_capacity_credit(
                        fuel,
                        "PJM",
                        installed_mw=(10153.9 if fuel == "wind" else 4549.8),
                        peak_demand_mw=150000.0,
                        curves_enabled=True,
                        config=config,
                        year=year,
                    ),
                    expected,
                    9,
                )

    def test_armed_credits_are_the_delivery_years_own_published_ratings(self):
        config = self._armed()
        table = RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"]
        for year, dy in ((2023, "2023/2024"), (2024, "2024/2025"), (2025, "2025/2026")):
            for fuel in ("wind", "solar"):
                self.assertAlmostEqual(
                    resolve_renewable_capacity_credit(
                        fuel,
                        "PJM",
                        installed_mw=5000.0,
                        peak_demand_mw=150000.0,
                        curves_enabled=True,
                        config=config,
                        year=year,
                    ),
                    table[dy][fuel],
                    12,
                    f"{year} {fuel}",
                )

    def test_no_hold_last_at_either_edge(self):
        # Pre-ELCC years (PJM's construct began with the 2023/2024 BRA) and
        # every year from 2026/27 on fall THROUGH to the incumbent curve.
        # Carrying a pre-reform class rating forward past the reform would
        # rebuild the mixed-vintage error the axis exists to remove.
        config = self._armed()
        for year in (2021, 2022, 2026, 2030):
            self.assertAlmostEqual(
                resolve_renewable_capacity_credit(
                    "wind",
                    "PJM",
                    installed_mw=10153.9,
                    peak_demand_mw=150000.0,
                    curves_enabled=True,
                    config=config,
                    year=year,
                ),
                0.41,
                9,
                str(year),
            )

    def test_the_vre_half_cannot_be_armed_without_the_d48_thermal_half(self):
        # rule 19 [R-ONE-MECH]: a basis vintaged on one half and not the other
        # is the exact failure D45 §2.2 measured and D48 exists to remove.
        lone = ScenarioConfig(
            mode="forecast",
            iso="PJM",
            hindcast=True,
            pjm_accreditation_design_vintage=False,
            pjm_vre_accreditation_vintage=True,
        )
        self.assertFalse(vre_accreditation_vintage_armed(lone, "PJM"))
        self.assertAlmostEqual(
            resolve_renewable_capacity_credit(
                "wind",
                "PJM",
                installed_mw=10153.9,
                peak_demand_mw=150000.0,
                curves_enabled=True,
                config=lone,
                year=2024,
            ),
            0.41,
            9,
        )

    def test_inert_on_every_other_iso(self):
        # rule 25 [R-ISO-SCOPE]: the registry holds one ISO and the predicate
        # requires an entry, so the flag armed on another ISO's run cannot
        # move a single MW — nothing transfers, and no ISO inherits PJM's
        # verdict.
        config = self._armed()
        for iso in ("MISO", "NYISO", "NEISO", "CAISO", "ERCOT"):
            self.assertFalse(vre_accreditation_vintage_armed(config, iso))
            for fuel in ("wind", "solar"):
                self.assertEqual(
                    resolve_renewable_capacity_credit(
                        fuel,
                        iso,
                        installed_mw=5000.0,
                        peak_demand_mw=100000.0,
                        curves_enabled=True,
                        config=config,
                        year=2024,
                    ),
                    resolve_renewable_capacity_credit(
                        fuel,
                        iso,
                        installed_mw=5000.0,
                        peak_demand_mw=100000.0,
                        curves_enabled=True,
                    ),
                    f"{iso} {fuel}",
                )

    def test_year_none_is_byte_identical_to_the_pre_d75r_resolver(self):
        config = self._armed()
        for fuel in ("wind", "solar"):
            self.assertEqual(
                resolve_renewable_capacity_credit(
                    fuel,
                    "PJM",
                    installed_mw=5000.0,
                    peak_demand_mw=150000.0,
                    curves_enabled=True,
                    config=config,
                    year=None,
                ),
                resolve_renewable_capacity_credit(
                    fuel,
                    "PJM",
                    installed_mw=5000.0,
                    peak_demand_mw=150000.0,
                    curves_enabled=True,
                ),
                fuel,
            )

    def test_a_plain_backcast_coerces_the_gate_off(self):
        # A forecast-lane mechanism: capacity evolution never runs in a plain
        # backcast, so an armed flag there would be an unregistered posture.
        backcast = ScenarioConfig(
            mode="backcast", iso="PJM", pjm_vre_accreditation_vintage=True
        )
        self.assertFalse(backcast.pjm_vre_accreditation_vintage)

    # --- the ledger: one accreditation, applied and reported alike ---------- #

    def test_ledger_and_its_diagnostic_move_together(self):
        # The ledger's credit and the ledger's RECORD of that credit resolve
        # through the same rung, or the evolution trail would misreport what
        # the screen priced (rule 19).
        config = self._armed()
        wind_pool, solar_pool = 10153.9, 4549.8
        for year, dy in ((2023, "2023/2024"), (2024, "2024/2025"), (2025, "2025/2026")):
            applied = renewable_credits_applied(
                [],
                wind_pool,
                solar_pool,
                "PJM",
                peak_demand_mw=150000.0,
                elcc_curves_enabled=True,
                config=config,
                accreditation_year=year,
            )
            table = RENEWABLE_ELCC_VINTAGE_RATINGS_BY_ISO["PJM"][dy]
            for fuel in ("wind", "solar"):
                self.assertAlmostEqual(applied[fuel], table[fuel], 12, f"{year} {fuel}")
            with no_hydro_accreditation():
                firm = accredited_firm_capacity_mw(
                    [],
                    wind_pool,
                    solar_pool,
                    0.0,
                    iso="PJM",
                    peak_demand_mw=150000.0,
                    elcc_curves_enabled=True,
                    config=config,
                    accreditation_year=year,
                )
            expected_vre = wind_pool * table["wind"] + solar_pool * table["solar"]
            self.assertAlmostEqual(
                firm - _pjm_non_vre_firm_mw(config, year), expected_vre, 6, str(year)
            )

    def test_accredited_vre_falls_in_every_in_scope_delivery_year(self):
        """The pre-declared SIGN (PRECOMMIT-capx-d75 §6), locked as a test.

        DOWN in all three in-scope delivery years. This is a property of PJM's
        own published ratings against the clamped 2026/27 curve, not a target:
        it is asserted here so a later edit to either side cannot silently
        invert the mechanism's direction without a test saying so.
        """
        armed, control = (
            self._armed(),
            ScenarioConfig(mode="forecast", iso="PJM", hindcast=True),
        )
        wind_pool, solar_pool = 10153.9, 4549.8
        for year in (2023, 2024, 2025):
            deltas = []
            for config in (control, armed):
                credits = renewable_credits_applied(
                    [],
                    wind_pool,
                    solar_pool,
                    "PJM",
                    peak_demand_mw=150000.0,
                    elcc_curves_enabled=True,
                    config=config,
                    accreditation_year=year,
                )
                deltas.append(
                    wind_pool * credits["wind"] + solar_pool * credits["solar"]
                )
            self.assertLess(deltas[1], deltas[0], f"DY {year}/{year + 1}")


def _pjm_non_vre_firm_mw(config: ScenarioConfig, year: int) -> float:
    """The firm MW an empty PJM fleet contributes outside the VRE pools.

    Isolates the VRE term of :func:`accredited_firm_capacity_mw` without
    re-implementing the ledger: the same call with both pools zeroed.
    """
    with no_hydro_accreditation():
        return accredited_firm_capacity_mw(
            [],
            0.0,
            0.0,
            0.0,
            iso="PJM",
            peak_demand_mw=150000.0,
            elcc_curves_enabled=True,
            config=config,
            accreditation_year=year,
        )


if __name__ == "__main__":
    unittest.main()
