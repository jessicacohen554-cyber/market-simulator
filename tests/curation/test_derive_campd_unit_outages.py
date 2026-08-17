"""Tests for the unit-outage deriver's WHEN-OPERABLE baseload guard and the
unit-grain partial-plateau mode.

The short/partial baseload guard (:data:`SHORT_BASELOAD_CF` = 0.55) is measured
on the hours a unit is OPERABLE — outside its own >= 5-day standard outage
windows — not on raw annual hours. A unit with a documented multi-month outage
plus a short event-coincident stop is baseload by its running capability and
must pass the guard; the same unit cycling economically (low CF throughout, no
documented outage) must fail. This is the identification correction of
docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md §7, cited to that measurement, not
to any price residual. Trivial synthetic cases only (no on-disk CEMS read).
"""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd


from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    EIA923_FALLBACK_OUTAGE_RATIO,
    SHORT_BASELOAD_CF,
    _eia923_month_windows,
    _is_liquid_only_fuel,
    _operable_mask,
    _partial_plateau_windows,
    _resolve_unit_group,
    _when_operable_cf,
)

HOURS = 8760
YEAR = 2025
CAP = 100.0  # detect nameplate MW


def _base_gross(run_cf: float) -> np.ndarray:
    """A unit running flat at ``run_cf`` x CAP for the whole year."""
    return np.full(HOURS, run_cf * CAP, dtype=float)


class WhenOperableGuardTest(unittest.TestCase):
    """The when-operable baseload guard (the LEG A identification correction)."""

    # A 180-day documented outage the standard >= 5-day extract carries: the
    # unit is 0 MW here. Feb-Jul (day 40 .. 220).
    LONG_START = pd.Timestamp("2025-02-10")
    LONG_END = pd.Timestamp("2025-08-08")  # inclusive last day, ~180 days

    def _standard_windows(self) -> dict:
        return {
            (99, "1", YEAR): [(self.LONG_START, self.LONG_END)],
        }

    def _baseload_with_outage_and_short_stop(self) -> np.ndarray:
        """Runs at 0.65 CF, zeroed across the 180-day outage AND a 2-day stop."""
        g = _base_gross(0.65)
        base = pd.Timestamp(f"{YEAR}-01-01")
        lo = int((self.LONG_START - base).total_seconds() // 3600)
        hi = int((self.LONG_END + pd.Timedelta(days=1) - base).total_seconds() // 3600)
        g[lo:hi] = 0.0
        # A 2-day event-coincident full stop OUTSIDE the documented window
        # (late August), the short-window phenomenon itself.
        s2 = int((pd.Timestamp("2025-08-20") - base).total_seconds() // 3600)
        g[s2 : s2 + 48] = 0.0
        return g

    def test_operable_mask_removes_only_the_standard_window(self):
        mask = _operable_mask(self._standard_windows(), 99, "1", YEAR, HOURS)
        base = pd.Timestamp(f"{YEAR}-01-01")
        lo = int((self.LONG_START - base).total_seconds() // 3600)
        hi = int((self.LONG_END + pd.Timedelta(days=1) - base).total_seconds() // 3600)
        self.assertFalse(mask[lo:hi].any())  # window hours are not operable
        self.assertTrue(mask[:lo].all())  # everything else operable
        self.assertTrue(mask[hi:].all())

    def test_baseload_unit_with_long_outage_passes_when_operable(self):
        g = self._baseload_with_outage_and_short_stop()
        # Raw-annual basis (no standard windows) is dragged below 0.55 by the
        # 180-day outage and SPURIOUSLY fails the guard...
        raw_cf = _when_operable_cf(g, CAP, {}, 99, "1", YEAR)
        self.assertLess(raw_cf, SHORT_BASELOAD_CF)
        # ...but the when-operable basis (excluding the documented window) sees
        # the unit's true running capability and PASSES.
        oper_cf = _when_operable_cf(g, CAP, self._standard_windows(), 99, "1", YEAR)
        self.assertGreaterEqual(oper_cf, SHORT_BASELOAD_CF)

    def test_economically_cycling_unit_fails_the_guard(self):
        # Same unit, no documented outage, just cycling at 0.40 CF all year:
        # when-operable CF == raw-annual CF == 0.40, below the baseload guard,
        # so an economic cycler is never admitted (either basis).
        g = _base_gross(0.40)
        self.assertLess(_when_operable_cf(g, CAP, {}, 99, "1", YEAR), SHORT_BASELOAD_CF)
        self.assertLess(
            _when_operable_cf(g, CAP, self._standard_windows(), 99, "1", YEAR),
            SHORT_BASELOAD_CF,
        )

    def test_no_windows_reduces_to_raw_annual(self):
        g = _base_gross(0.70)
        self.assertAlmostEqual(
            _when_operable_cf(g, CAP, {}, 99, "1", YEAR), 0.70, places=6
        )


class PartialPlateauModeTest(unittest.TestCase):
    """The unit-grain partial-plateau detector wrapper (LEG B)."""

    def test_sustained_half_capacity_plateau_is_detected(self):
        # Unit runs near ceiling (0.9 CF) except for a 20-day plateau at ~0.45
        # CF (half its units out) — a partial derate the >= 5-day plateau rule
        # must catch, with a derate_factor around 0.5.
        g = _base_gross(0.9)
        base = pd.Timestamp(f"{YEAR}-01-01")
        lo = int((pd.Timestamp("2025-07-10") - base).total_seconds() // 3600)
        g[lo : lo + 20 * 24] = 0.45 * CAP
        windows, factors = _partial_plateau_windows(g, CAP)
        self.assertTrue(windows, "expected at least one plateau window")
        # A window overlapping the depressed span with a derate_factor < 1.
        hit = [w for w in windows if w[0] <= lo < w[1]]
        self.assertTrue(hit)
        self.assertLess(factors[hit[0]], 1.0)
        self.assertGreater(factors[hit[0]], 0.0)

    def test_flat_baseload_unit_has_no_plateau(self):
        # A unit that never drops its ceiling yields no partial window.
        windows, factors = _partial_plateau_windows(_base_gross(0.9), CAP)
        self.assertEqual(windows, [])
        self.assertEqual(factors, {})


class TestEia923MonthWindows(unittest.TestCase):
    """The EIA-923 non-CAMPD fallback's month-run merger (pure, no I/O).

    A month at or below ``ratio`` x the plant's own normal monthly output is a
    full-stop window; contiguous out-months merge; NaN/absent months are never a
    signal (only FILED months appear in the input dict).
    """

    RATIO = EIA923_FALLBACK_OUTAGE_RATIO  # 0.10
    REF = 1000.0  # normal monthly output MWh

    def test_contiguous_out_months_merge_into_one_window(self):
        # Feb+Mar near-zero, everything else normal -> one Feb 1 .. Mar 31 window.
        monthly = {m: self.REF for m in range(1, 13)}
        monthly[2] = 10.0
        monthly[3] = 0.0
        wins = _eia923_month_windows(monthly, self.REF, 2021, self.RATIO)
        self.assertEqual(len(wins), 1)
        start, end, dur = wins[0]
        self.assertEqual(start.strftime("%Y-%m-%d"), "2021-02-01")
        self.assertEqual(end.strftime("%Y-%m-%d"), "2021-03-31")
        self.assertEqual(dur, 28.0 + 31.0)  # Feb(28)+Mar(31), 2021 non-leap

    def test_separated_out_months_are_distinct_windows(self):
        monthly = {m: self.REF for m in range(1, 13)}
        monthly[1] = 0.0
        monthly[8] = 0.0
        wins = _eia923_month_windows(monthly, self.REF, 2022, self.RATIO)
        self.assertEqual(len(wins), 2)
        self.assertEqual(wins[0][0].strftime("%m"), "01")
        self.assertEqual(wins[1][0].strftime("%m"), "08")

    def test_at_ratio_boundary_is_out_above_is_available(self):
        # exactly ratio*ref -> out; just above -> available.
        monthly = {1: self.RATIO * self.REF, 2: self.RATIO * self.REF + 1.0}
        wins = _eia923_month_windows(monthly, self.REF, 2020, self.RATIO)
        self.assertEqual([w[0].strftime("%m") for w in wins], ["01"])

    def test_absent_months_are_not_flagged(self):
        # Only Jan+Feb filed (partial year like 2026 Q1); both normal -> no window.
        monthly = {1: self.REF, 2: self.REF}
        self.assertEqual(_eia923_month_windows(monthly, self.REF, 2026, self.RATIO), [])


class TestLiquidFuelCombustionTurbineRouting(unittest.TestCase):
    """The liquid-fuel CT guard keeps an oil peaker out of its siblings' gas bin.

    ``_resolve_unit_group``'s ``fac_group`` short-circuit was a pjm-75
    conservatism ("single-group gas facilities are byte-identical"), not a
    physical claim, and at a facility that mixes an oil peaker with a gas block
    it handed the peaker's outage window to the block: NEISO plant 6081 Stony
    Brook's two Diesel Oil combustion turbines (83 MW each) derated a 305.1 MW
    combined cycle they are not in, for ~50 % of the 2024 and 2025 capacity-years
    in which the CC units themselves had no windows at all (neiso-99, rule 14
    ``[R-ACCURATE]``).

    The discriminator must be the unit's OWN ``primaryFuelInfo``, not
    ``unitType`` alone: 27 of the 35 CAMPD units filed "Combustion turbine" in a
    non-CT bin are gas-fired members of a genuine block and MUST keep inheriting
    it.
    """

    def test_liquid_ct_does_not_inherit_a_sibling_cc_bin(self):
        self.assertEqual(
            _resolve_unit_group(
                False, "Combustion turbine", {"CC_REGULAR"}, "CC_REGULAR", "Diesel Oil"
            ),
            "CT_PEAKER",
        )

    def test_liquid_ct_does_not_inherit_a_sibling_steam_bin(self):
        self.assertEqual(
            _resolve_unit_group(
                False, "Combustion turbine", {"ST_GAS"}, "ST_GAS", "Other Oil"
            ),
            "CT_PEAKER",
        )

    def test_gas_ct_still_inherits_its_block(self):
        # The 27-unit majority: a genuine CC block's CT filed "Combustion
        # turbine". Byte-identical to the pre-guard routing.
        self.assertEqual(
            _resolve_unit_group(
                False,
                "Combustion turbine",
                {"CC_REGULAR", "CT_PEAKER"},
                "CC_REGULAR",
                "Pipeline Natural Gas",
            ),
            "CC_REGULAR",
        )

    def test_dual_fuel_ct_is_not_liquid_only(self):
        # A dual-fuel machine carries its gas token in the SAME string.
        self.assertEqual(
            _resolve_unit_group(
                False,
                "Combustion turbine",
                {"ST_GAS"},
                "ST_GAS",
                "Natural Gas, Residual Oil",
            ),
            "ST_GAS",
        )

    def test_oil_fired_boiler_is_untouched(self):
        # The guard is conjunctive: a residual-oil BOILER is not a CT.
        self.assertEqual(
            _resolve_unit_group(
                False,
                "Dry bottom wall-fired boiler",
                {"ST_GAS"},
                "ST_GAS",
                "Residual Oil",
            ),
            "ST_GAS",
        )

    def test_coal_still_wins_over_the_guard(self):
        self.assertEqual(
            _resolve_unit_group(
                True, "Combustion turbine", {"COAL"}, "COAL", "Diesel Oil"
            ),
            "COAL",
        )

    def test_blank_fuel_is_fail_safe(self):
        # Unknown fuel must not evict a unit from its bin.
        self.assertEqual(
            _resolve_unit_group(
                False, "Combustion turbine", {"CC_REGULAR"}, "CC_REGULAR", ""
            ),
            "CC_REGULAR",
        )

    def test_liquid_predicate_vocabulary(self):
        for f in ("Diesel Oil", "Other Oil", "Residual Oil", "diesel oil"):
            self.assertTrue(_is_liquid_only_fuel(f), f)
        for f in (
            "Pipeline Natural Gas",
            "Natural Gas",
            "Coal",
            "Wood",
            "",
            "Natural Gas, Residual Oil",
        ):
            self.assertFalse(_is_liquid_only_fuel(f), f)


if __name__ == "__main__":
    unittest.main()
