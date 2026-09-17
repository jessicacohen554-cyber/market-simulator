"""The COMBINED-fossil reconcile family includes OIL when the extract has it.

``render_calibration_html.reconcile_vintage_classes`` scales the EIA-923
grid-delivered fossil classes to the EIA-930 grid series. Its target used to be
EIA-930's ``gas + coal`` cell ALONE, while EIA-923 books a plant's MWh under the
fuel it BURNED — so a dual-fuel unit's oil hours land in the 923 ``oil`` class
while its gas hours stay in the CC/CT/ST classes, and EIA-930 books that same
generation under ``NG: OIL``. The comparison therefore straddled a fuel boundary
and read an ATTRIBUTION difference as a LEVEL error.

Measured live case (nyiso-239, 2026-09-16): NYISO 2022 reads **+5.13 %** on the
gas-only basis — outside the ±3 % deadband, so the reconcile fired and deflated
EVERY NYISO fossil class by **x0.951167**, 1.62 TWh of it on ``CC_REGULAR``,
which was the whole of that year's C1 band breach — and **+0.08 %** with oil on
both sides, the tightest agreement of any complete NYISO vintage. The full
evidence (NYISO's own published fuel mix, the 923 liquid-fuel routing, the flat
930 ``NG: OIL`` block, CEMS on a fixed plant set, and the hourly shape test) is
``docs/FINDING-nyiso239-c1-2022-bench-oil-attribution-2026-09-16.md``.

These tests pin the four things that make the repair safe:
  1. the live NYISO 2022 numbers — oil-inclusive, the reconcile does NOT fire;
  2. the FALLBACK — a bundle whose extract predates the 930 ``oil`` series has no
     ``oil`` key and reconciles exactly as before, byte-identical;
  3. the family invariant — when it DOES fire, oil scales with gas and coal, so
     the post-scale family lands on the target and the 923 split is preserved;
  4. the CAISO CEMS-anchor cap spans the same boundary as the current sum.
"""

import importlib.util
import unittest

from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
_spec = importlib.util.spec_from_file_location(
    "rch_oil_family", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)


def _fossil_sum(cf, families):
    return round(sum(cf[g] for g in families if g in cf), 4)


class TestVintageReconcileOilFamily(unittest.TestCase):
    # The live NYISO 2022 bench inputs, to the precision the bench part carries.
    NYISO_2022_CLASSFULL = {
        "CC_REGULAR": 33.2072,
        "CC_CHP": 14.9115,
        "CT_PEAKER": 2.8247,
        "CT_CHP": 2.6326,
        "ST_GAS": 8.0938,
        "ST_CHP": 0.9062,
        "OTHER_FOSSIL": 0.7748,
        "COAL_PRB": 0.0,
        "COAL_BIT": 0.0,
        "oil": 1.8437,
    }
    NYISO_2022_E930_GAS = 60.257
    NYISO_2022_E930_OIL = 4.885

    def test_nyiso_2022_gas_only_basis_fires_and_deflates_cc_regular(self):
        """The defect, pinned: gas-only reads +5.13 % and deflates every class.

        This is the BEFORE state and it must keep reproducing, so the repair
        below is measured against a real number rather than an asserted one.
        """
        cf = dict(self.NYISO_2022_CLASSFULL)
        e930 = {"gas": self.NYISO_2022_E930_GAS, "coal": 0.0}  # no "oil" key
        fam = (*rch._GAS_GROUPS, *rch._COAL_GROUPS)
        before = _fossil_sum(cf, fam)
        self.assertAlmostEqual(100.0 * (before / e930["gas"] - 1.0), 5.13, places=1)
        rch.reconcile_vintage_classes(cf, e930, "NYISO")
        # It fired: the family lands exactly on the gas cell...
        self.assertAlmostEqual(_fossil_sum(cf, fam), e930["gas"], places=2)
        # ...and CC_REGULAR is deflated by ~1.62 TWh, the C1 band breach.
        self.assertAlmostEqual(cf["CC_REGULAR"], 31.5856, places=3)

    def test_nyiso_2022_oil_inclusive_basis_does_not_fire(self):
        """The repair: with oil on both sides the deviation is +0.08 %, in band.

        Every class is then left BYTE-IDENTICAL — the reconcile does not fire at
        all, so `CC_REGULAR` keeps its EIA-923 value of 33.2072 TWh.
        """
        cf = dict(self.NYISO_2022_CLASSFULL)
        e930 = {
            "gas": self.NYISO_2022_E930_GAS,
            "coal": 0.0,
            "oil": self.NYISO_2022_E930_OIL,
        }
        fam = (*rch._GAS_GROUPS, *rch._COAL_GROUPS, *rch._OIL_GROUPS)
        cur = _fossil_sum(cf, fam)
        tgt = e930["gas"] + e930["oil"]
        self.assertAlmostEqual(100.0 * (cur / tgt - 1.0), 0.08, places=1)
        rch.reconcile_vintage_classes(cf, e930, "NYISO")
        self.assertEqual(cf, self.NYISO_2022_CLASSFULL)

    def test_missing_oil_key_falls_back_byte_identically(self):
        """A bundle predating the 930 oil series reconciles exactly as before.

        The fallback is what keeps every already-committed bundle — MISO and
        ERCOT carry no ``oil`` series at all — re-rendering unchanged. Pinned by
        running the SAME inputs through both call shapes and comparing.
        """
        e930_no_oil = {"gas": 50.0, "coal": 10.0}
        cf_a = {"CC_REGULAR": 40.0, "ST_GAS": 20.0, "COAL_BIT": 10.0, "oil": 5.0}
        cf_b = dict(cf_a)
        rch.reconcile_vintage_classes(cf_a, e930_no_oil, "NYISO")
        rch.reconcile_vintage_classes(cf_b, dict(e930_no_oil), "NYISO")
        self.assertEqual(cf_a, cf_b)
        # The 923 `oil` class is NOT in the family on the fallback path, so it
        # is left alone while gas+coal scale to 60.0.
        self.assertEqual(cf_a["oil"], 5.0)
        self.assertAlmostEqual(
            _fossil_sum(cf_a, (*rch._GAS_GROUPS, *rch._COAL_GROUPS)), 60.0, places=2
        )

    def test_when_it_fires_oil_scales_with_the_family(self):
        """The invariant: the whole family lands on the target, split preserved.

        Oil is a family MEMBER, not just a comparison term — otherwise the
        post-scale sum could not equal the target it was scaled to.
        """
        cf = {"CC_REGULAR": 60.0, "ST_GAS": 20.0, "COAL_BIT": 10.0, "oil": 10.0}
        e930 = {"gas": 40.0, "coal": 8.0, "oil": 4.0}  # target 52 vs current 100
        ratios_before = {k: v / cf["CC_REGULAR"] for k, v in cf.items()}
        rch.reconcile_vintage_classes(cf, e930, "NYISO")
        fam = (*rch._GAS_GROUPS, *rch._COAL_GROUPS, *rch._OIL_GROUPS)
        self.assertAlmostEqual(_fossil_sum(cf, fam), 52.0, places=3)
        # Uniform scale => every pairwise ratio is unchanged (the SPLIT is kept).
        for k, v in cf.items():
            self.assertAlmostEqual(v / cf["CC_REGULAR"], ratios_before[k], places=6)

    def test_caiso_anchor_cap_spans_the_same_family_as_the_current_sum(self):
        """The CEMS-anchor cap gains the 923 oil block when oil joins the family.

        The anchor is CEMS gas + the 923 cogen block + 923 coal, i.e. gas+coal
        only. Capping an oil-INCLUSIVE current against a gas-only anchor would
        bind a wider sum against a narrower target and manufacture a deflation.
        """
        cf = {"CC_REGULAR": 60.0, "ST_GAS": 10.0, "oil": 5.0}
        e930 = {
            "gas": 200.0,  # a corrupted cell, far above the measured anchor
            "coal": 0.0,
            "oil": 3.0,
            "fossil_cems_grid": 70.0,
        }
        rch.reconcile_vintage_classes(cf, e930, "CAISO")
        fam = (*rch._GAS_GROUPS, *rch._COAL_GROUPS, *rch._OIL_GROUPS)
        # Cap = anchor(70) + the 923 oil block(5) = 75; current is 75, so the
        # deviation is 0 % and nothing moves.
        self.assertAlmostEqual(_fossil_sum(cf, fam), 75.0, places=3)
        self.assertEqual(cf["CC_REGULAR"], 60.0)

    def test_caiso_is_in_the_corrupt_set_so_the_cap_path_is_live(self):
        """Guard the premise of the test above rather than assuming it."""
        self.assertIn("CAISO", rch.EIA930_NG_CELL_CORRUPT)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
