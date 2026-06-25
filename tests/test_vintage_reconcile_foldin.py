"""EIA-923 preliminary-vintage gas/coal reconcile + CAISO geo/biomass fold-in.

``render_calibration_html.reconcile_vintage_classes`` scales a preliminary
EIA-923 vintage's fossil classes up to the complete EIA-930 grid series the model
is calibrated to. For balancing authorities whose EIA-930 "Natural Gas" aggregate
silently folds in geothermal + biomass (CISO is the documented live case), the
gas target must be DEFLATED by that fold-in first, otherwise the gas classes are
scaled to gas+geo+biomass and the per-class actual is inflated by ~10 TWh — the
benchmark bug these tests pin. The guard must leave clean ISOs (whose 930 NG is
already gas-only) scaling to the full 930 gas cell.
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

    def test_complete_vintage_untouched(self):
        """A complete vintage (>= frac * target) is left byte-identical."""
        cf = {"CC_REGULAR": 99.0, "CT_PEAKER": 5.0, "OTHER": 1.0, "biomass": 0.5}
        before = dict(cf)
        rch.reconcile_vintage_classes(cf, {"gas": 100.0}, "ERCOT")
        self.assertEqual(cf, before)

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

    def test_coal_unaffected_by_gas_foldin(self):
        """Coal classes reconcile to 930 coal regardless of the gas fold-in."""
        cf = {
            "CC_REGULAR": 60.0,
            "OTHER": 8.0,
            "biomass": 4.0,
            "COAL_BIT": 9.0,
        }
        rch.reconcile_vintage_classes(cf, {"gas": 85.0, "coal": 10.0}, "CAISO")
        self.assertAlmostEqual(cf["COAL_BIT"], 10.0, places=2)

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


if __name__ == "__main__":
    unittest.main()
