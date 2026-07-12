"""COMBINED-fossil EIA-923 reconcile + CAISO geo/biomass fold-in.

``render_calibration_html.reconcile_vintage_classes`` reconciles the COMBINED
fossil (gas+coal) EIA-923 total to the complete EIA-930 grid series in BOTH
directions — scaling a preliminary vintage UP, and an EIA-923 total that
over-states grid delivery DOWN — with every fossil class scaled by the SAME
factor so the CEMS-validated 923 gas/coal SPLIT is preserved. The reconcile
corrects the fossil LEVEL, never the SPLIT: EIA-930's per-fuel coal/gas
attribution mis-splits by 7-21 TWh/yr vs CAMPD, so the earlier per-family
reconcile (gas and coal each scaled to their own 930 cell) manufactured
per-class errors even when the total fossil was in tolerance (PJM 2024:
CC_REGULAR read +21 TWh over vs a ~+3 CEMS miss). For balancing authorities
whose EIA-930 "Natural Gas" aggregate silently folds in geothermal + biomass
(CISO is the documented live case), the combined target must be DEFLATED by
that fold-in first, else the fossil classes scale to gas+geo+biomass. The tests
pin: the fold-in deflation, the deadband, the combined split-preservation, and
the offsetting-in-band case the combined reconcile now correctly leaves alone.
"""

import importlib.util
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch_foldin", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)


class TestVintageReconcileFoldIn(unittest.TestCase):
    def _gas_sum(self, cf):
        return round(sum(cf[g] for g in rch._GAS_GROUPS if g in cf), 4)

    def test_caiso_gas_deflated_by_geo_biomass_foldin(self):
        """CAISO scales gas to (930 gas - OTHER - biomass), not the inflated cell.

        Mirrors the real 2024 bundle: raw EIA-923 gas (67.68) is a preliminary
        vintage below the 930 cell, but the 930 cell (85.37) folds in CA
        geothermal (OTHER, 8.08) + biomass (4.41). The reconcile must scale gas
        to the deflated true-gas target 72.88, NOT to 85.37.
        """
        cf = {
            "CC_REGULAR": 60.00,
            "CT_PEAKER": 5.00,
            "ST_GAS": 2.68,
            "OTHER": 8.08,
            "biomass": 4.41,
        }
        e930 = {"gas": 85.37, "coal": 0.0}
        rch.reconcile_vintage_classes(cf, e930, "CAISO")
        deflated = 85.37 - 8.08 - 4.41  # 72.88
        self.assertAlmostEqual(self._gas_sum(cf), round(deflated, 4), places=2)
        # The bug was scaling to the full inflated cell — guard against regress.
        self.assertLess(self._gas_sum(cf), e930["gas"] - 10.0)
        # The non-gas rows that were folded in are themselves untouched.
        self.assertEqual(cf["OTHER"], 8.08)
        self.assertEqual(cf["biomass"], 4.41)

    def test_clean_iso_scales_to_full_930_gas(self):
        """A clean ISO (no fold-in) scales a preliminary gas vintage to full 930.

        Subtracting its real OTHER+biomass would wrongly under-scale gas; the
        guard must not fire for an ISO outside EIA930_GAS_FOLDS_GEO_BIOMASS.
        """
        cf = {
            "CC_REGULAR": 80.0,
            "CT_PEAKER": 10.0,
            "OTHER": 2.0,
            "biomass": 0.4,
        }
        e930 = {"gas": 100.0, "coal": 0.0}
        rch.reconcile_vintage_classes(cf, e930, "ERCOT")
        self.assertAlmostEqual(self._gas_sum(cf), 100.0, places=2)
        # NOT the deflated 97.6 a fold-in subtraction would have produced.
        self.assertGreater(self._gas_sum(cf), 99.0)

    def test_within_deadband_untouched(self):
        """A family within +/-(1-frac) of the grid series is left byte-identical."""
        # gas sum 96 + 5 = 101 vs target 100 -> +1% (inside the ~3% deadband).
        cf = {"CC_REGULAR": 96.0, "CT_PEAKER": 5.0, "OTHER": 1.0, "biomass": 0.5}
        before = dict(cf)
        rch.reconcile_vintage_classes(cf, {"gas": 100.0}, "ERCOT")
        self.assertEqual(cf, before)

    def test_over_count_scaled_down_to_grid(self):
        """An EIA-923 family ABOVE the EIA-930 grid (residual CHP BTM / 923<->930
        assignment) is scaled DOWN to the grid total — the bidirectional reconcile
        that puts the actual on the model's grid-delivered basis. gas sum 104 + 6
        = 110 vs grid 100 (+10%, outside the deadband) -> reconciled to 100."""
        cf = {"CC_REGULAR": 104.0, "CT_PEAKER": 6.0, "OTHER": 1.0, "biomass": 0.5}
        rch.reconcile_vintage_classes(cf, {"gas": 100.0}, "ERCOT")
        self.assertAlmostEqual(self._gas_sum(cf), 100.0, places=2)
        # Inter-class split preserved (each scaled by the same factor).
        self.assertAlmostEqual(
            cf["CC_REGULAR"] / cf["CT_PEAKER"], 104.0 / 6.0, places=2
        )

    def test_caiso_complete_vintage_not_deflated_below_actual(self):
        """When CAISO raw gas already exceeds the deflated target, leave it alone.

        2023-style: raw gas 76.04 already exceeds 930 gas (88.02) - OTHER (9.26)
        - biomass (4.48) = 74.28, so the reconcile must NOT fire (no spurious
        scale-down of an already-complete gas vintage).
        """
        cf = {
            "CC_REGULAR": 68.0,
            "CT_PEAKER": 5.0,
            "ST_GAS": 3.04,
            "OTHER": 9.26,
            "biomass": 4.48,
        }
        before = dict(cf)
        rch.reconcile_vintage_classes(cf, {"gas": 88.02}, "CAISO")
        self.assertEqual(cf, before)

    def _coal_sum(self, cf):
        return round(sum(cf[g] for g in rch._COAL_GROUPS if g in cf), 4)

    def test_gas_foldin_deflates_the_combined_target(self):
        """The CAISO geo/biomass fold-in deflates the COMBINED gas+coal target.

        Combined reconcile (fossil scaled as one family): coal no longer scales
        to its own 930 coal cell — it scales by the same factor as gas — but the
        gas fold-in must still be subtracted from the combined target so the
        fossil classes don't scale to gas+geo+biomass. Here total fossil (69) is
        below the deflated target so it scales UP, preserving the coal/gas split.
        """
        cf = {"CC_REGULAR": 60.0, "OTHER": 8.0, "biomass": 4.0, "COAL_BIT": 9.0}
        rch.reconcile_vintage_classes(cf, {"gas": 85.0, "coal": 10.0}, "CAISO")
        # combined target = (85 + 10) - foldin(8+4) = 83; cur = 60+9 = 69 -> x1.203
        target = 85.0 + 10.0 - (8.0 + 4.0)
        self.assertAlmostEqual(self._gas_sum(cf) + self._coal_sum(cf), target, 1)
        # split preserved: coal scaled by the same factor as gas, NOT to 930 coal.
        self.assertAlmostEqual(cf["COAL_BIT"] / cf["CC_REGULAR"], 9.0 / 60.0, 3)

    def test_offsetting_split_within_total_deadband_untouched(self):
        """The core fix: gas over / coal under that OFFSET to an in-band total.

        PJM-2024 signature — gas +4.2% and coal -5.9% each breach the ±3% band
        (the old per-family reconcile fired on both, dumping a spurious -15 TWh
        gas cut ~85% onto CC_REGULAR), but the COMBINED fossil total is only
        +1.4% and must now be left byte-identical, preserving the CEMS-validated
        split. Guards the exact regression this change fixes.
        """
        cf = {
            "CC_REGULAR": 336.0,
            "CT_PEAKER": 24.0,
            "ST_GAS": 24.0,  # gas sum 384 vs 930 gas 368 -> +4.3% (would fire alone)
            "COAL_BIT": 115.0,  # coal vs 930 coal 124 -> -7.3% (would fire alone)
            "OTHER": 2.0,
            "biomass": 5.0,
        }
        before = dict(cf)
        # 930 'other' ≈ model OTHER+biomass so the fold-in self-zeros (clean BA).
        e930 = {"gas": 368.0, "coal": 124.0, "other": 7.0}
        rch.reconcile_vintage_classes(cf, e930, "PJM")
        self.assertEqual(cf, before)  # total 499 vs 492 = +1.4%, inside deadband

    def test_combined_vintage_scale_preserves_coal_gas_split(self):
        """A preliminary vintage (total below grid) scales UP preserving the split.

        Both families under-report; the combined reconcile scales every fossil
        class by ONE factor to the combined 930 total, so the coal/gas ratio is
        the CEMS-measured 923 ratio, NOT forced onto 930's per-fuel split.
        """
        cf = {"CC_REGULAR": 300.0, "COAL_BIT": 100.0, "OTHER": 1.0, "biomass": 1.0}
        e930 = {"gas": 340.0, "coal": 120.0, "other": 2.0}  # total 460 vs 400
        rch.reconcile_vintage_classes(cf, e930, "PJM")
        self.assertAlmostEqual(self._gas_sum(cf) + self._coal_sum(cf), 460.0, places=1)
        self.assertAlmostEqual(cf["COAL_BIT"] / cf["CC_REGULAR"], 100.0 / 300.0, 3)
        # coal NOT independently pinned to 930 coal (120) — that was the old bug.
        self.assertLess(cf["COAL_BIT"], 120.0)

    # --- general partial-fold path: bundle carries the EIA-930 "other" series ---

    def test_miso_partial_foldin_subtracts_only_leaked_portion(self):
        """MISO folds only PART of its geo/biomass into NG; 930 'other' carries rest.

        Real 2024 signature: 930 NG=252.9, 930 Other=2.74, model OTHER+biomass=15.5.
        With the 930 'other' series present, the deflation must be only the leaked
        12.76 (= 15.5 - 2.74), NOT the full 15.5 the legacy CAISO formula would use
        (which would under-scale MISO gas by ~2.7 TWh).
        """
        cf = {
            "CC_REGULAR": 150.0,
            "CT_PEAKER": 3.0,
            "ST_GAS": 11.0,  # gas sum 164 < frac*target -> reconcile fires
            "OTHER": 8.3,
            "biomass": 7.2,  # OTHER+biomass = 15.5
        }
        e930 = {"gas": 252.9, "coal": 0.0, "other": 2.74}
        rch.reconcile_vintage_classes(cf, e930, "MISO")
        target = 252.9 - max(0.0, 15.5 - 2.74)  # 240.14
        self.assertAlmostEqual(self._gas_sum(cf), round(target, 4), places=1)
        # NOT the over-deflated full-subtraction target (237.4) the allowlist gave.
        self.assertGreater(self._gas_sum(cf), 252.9 - 15.5 + 1.0)

    def test_clean_iso_with_other_series_no_subtraction(self):
        """A clean BA carrying 930 'other' ≈ model other+biomass deflates by ~0.

        PJM-style: 930 reports geo+biomass in its own Other series, so folded≈0 and
        gas scales to the FULL 930 gas cell — the general path self-zeroes without
        needing the allowlist.
        """
        cf = {"CC_REGULAR": 80.0, "CT_PEAKER": 10.0, "OTHER": 1.6, "biomass": 0.4}
        e930 = {"gas": 100.0, "coal": 0.0, "other": 2.0}  # 930 other ≈ model 2.0
        rch.reconcile_vintage_classes(cf, e930, "PJM")
        self.assertAlmostEqual(self._gas_sum(cf), 100.0, places=2)

    def test_clean_iso_other_series_overreports_clamps_at_zero(self):
        """930 'other' > model other+biomass (survey noise) clamps the deflation at 0.

        max(0, …) guards against a NEGATIVE deflation that would inflate the gas
        target above the raw 930 cell.
        """
        cf = {"CC_REGULAR": 80.0, "CT_PEAKER": 10.0, "OTHER": 1.5, "biomass": 0.3}
        e930 = {"gas": 100.0, "coal": 0.0, "other": 3.0}  # 930 other > model 1.8
        rch.reconcile_vintage_classes(cf, e930, "PJM")
        self.assertAlmostEqual(self._gas_sum(cf), 100.0, places=2)

    def test_caiso_total_foldin_via_other_series(self):
        """CAISO with 930 'other'≈0 deflates by the full model OTHER+biomass.

        The general path reproduces the legacy allowlist result for the total-fold
        case (930 reports ~0 Other, everything is in NG).
        """
        cf = {
            "CC_REGULAR": 60.0,
            "CT_PEAKER": 5.0,
            "ST_GAS": 2.68,
            "OTHER": 8.08,
            "biomass": 4.41,
        }
        e930 = {"gas": 85.37, "coal": 0.0, "other": 0.0}
        rch.reconcile_vintage_classes(cf, e930, "CAISO")
        self.assertAlmostEqual(self._gas_sum(cf), round(85.37 - 8.08 - 4.41, 4), 2)


class TestCemsAnchorCap(unittest.TestCase):
    """CEMS-anchor cap on the combined reconcile (owner-signed 2026-07-12).

    For an :data:`EIA930_NG_CELL_CORRUPT` ISO whose bench part carries
    ``fossil_cems_grid``, the reconcile target may never exceed the measured
    fossil total — the CISO 930 NG cell carries a fabricated solar-shaped block
    from ~2024-05 (FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md §3), so
    scaling classFull up to it inflated the actual ×1.10-×1.44.
    """

    def test_cap_binds_below_corrupt_930_cell(self):
        # 2025-shaped: booked 47.65 vs 930 target 68.53 (×1.44) — the cap holds
        # the scale at the measured 51.67 (×1.084) instead.
        cf = {"CC_REGULAR": 37.43, "CC_CHP": 6.5, "CT_PEAKER": 2.2, "ST_GAS": 1.52}
        e930 = {"gas": 68.53, "coal": 0.0, "other": 0.0, "fossil_cems_grid": 51.67}
        rch.reconcile_vintage_classes(cf, e930, "CAISO")
        total = round(sum(cf.values()), 2)
        self.assertAlmostEqual(total, 51.67, places=1)
        self.assertLess(total, 60.0)  # never the corrupted 930 level

    def test_cap_inert_within_deadband(self):
        # 2023/24-shaped: booked total within ±3% of the anchor — classFull is
        # left byte-identical (no scale fires at all).
        cf = {"CC_REGULAR": 51.86, "CC_CHP": 8.0, "CT_PEAKER": 4.6, "ST_GAS": 2.8}
        e930 = {"gas": 74.24, "coal": 0.0, "other": 0.0, "fossil_cems_grid": 68.76}
        before = dict(cf)
        rch.reconcile_vintage_classes(cf, e930, "CAISO")
        self.assertEqual(cf, before)

    def test_930_below_anchor_still_governs(self):
        # One-directional cap: a 930 total BELOW the anchor is not raised to it.
        cf = {"CC_REGULAR": 50.0}
        e930 = {"gas": 45.0, "coal": 0.0, "other": 0.0, "fossil_cems_grid": 60.0}
        rch.reconcile_vintage_classes(cf, e930, "CAISO")
        self.assertAlmostEqual(cf["CC_REGULAR"], 45.0, places=1)

    def test_non_member_iso_ignores_anchor_field(self):
        # A non-corrupt ISO with a (hypothetical) anchor field keeps the plain
        # 930 reconcile — membership is CEMS-evidence-gated per ISO.
        cf = {"CC_REGULAR": 90.0}
        e930 = {"gas": 100.0, "coal": 0.0, "other": 0.0, "fossil_cems_grid": 95.0}
        rch.reconcile_vintage_classes(cf, e930, "ERCOT")
        self.assertAlmostEqual(cf["CC_REGULAR"], 100.0, places=1)


if __name__ == "__main__":
    unittest.main()
