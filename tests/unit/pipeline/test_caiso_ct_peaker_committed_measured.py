"""CT_PEAKER's ``committed`` band grounded on its own measured basis (caiso-241).

``_CAISO_OFFER_CURVE["CT_PEAKER"]["committed"] = 1.35`` is a fitted scalar whose
own band dict already carries the measured counterpart ``phys_committed = 0.991``
(``caiso_campd_marginal_hr_summary.csv`` ``avg_committed_p50``, n = 75).
``ScenarioConfig.caiso_ct_peaker_committed_measured`` substitutes the one for the
other — zero new numbers, zero free parameters.

Unlike its caiso-239 / caiso-240 siblings, whose plants are BYPASSED out of
``offer_curve_by_group`` entirely, ``CT_PEAKER`` resolves a class curve, so the
substitution is made on the resolved band dict in ``pipeline.backcast_config``
and these tests pin it there.

Six contracts:
  * byte-identical OFF;
  * the band takes its own ``phys_committed`` ON;
  * EXACTLY ONE band on EXACTLY ONE group moves;
  * band-disjoint from ``caiso_offer_surface_measured*`` (rule 19
    ``[R-ONE-MECH]``), which arm ``econ_low`` / ``econ_high`` / ``peak`` only;
  * a non-CAISO ISO is a HARD ERROR (rule 25 ``[R-ISO-SCOPE]``) — NYISO (0.843)
    and NEISO (0.985) carry the same uncited 1.35 and the same defect, but each
    lane grounds its own band on its own measurement;
  * a CAISO ``CT_PEAKER`` band with no ``phys_committed`` is a HARD ERROR, never
    a silent fallback to the fitted value.
"""

import unittest
from unittest import mock

import sys

import market_sim.pipeline.backcast_config  # noqa: F401  (module, not the re-exported fn)

#: ``market_sim.pipeline`` re-exports the FUNCTION under this name, so the module
#: object has to be taken from ``sys.modules`` for ``mock.patch.object`` to reach
#: ``_CAISO_OFFER_CURVE``.
bc = sys.modules["market_sim.pipeline.backcast_config"]

BASE = dict(iso="CAISO", year=2024, hours=8760, gas_price=2.19)
MEASURED = dict(
    caiso_offer_surface_measured=True,
    caiso_offer_surface_measured_ungrounded=True,
)
#: The fitted value the arm retires, and the measurement it retires to.
FITTED = 1.35
PHYS = 0.991


def _curve(**kw):
    return bc.backcast_config(**BASE, **kw).offer_curve_by_group


def _moved(a: dict, b: dict) -> dict:
    """Return ``{group: {band: (off, on)}}`` for every band that differs."""
    out: dict = {}
    for g in set(a) | set(b):
        ba, bb = a.get(g) or {}, b.get(g) or {}
        d = {
            k: (ba.get(k), bb.get(k))
            for k in set(ba) | set(bb)
            if ba.get(k) != bb.get(k)
        }
        if d:
            out[g] = d
    return out


class TestCaisoCtPeakerCommittedMeasured(unittest.TestCase):
    def test_off_is_byte_identical_and_keeps_the_fitted_value(self):
        off = _curve(**MEASURED)
        self.assertEqual(off["CT_PEAKER"]["committed"], FITTED)
        self.assertEqual(off["CT_PEAKER"]["phys_committed"], PHYS)
        self.assertFalse(
            bc.backcast_config(**BASE, **MEASURED).caiso_ct_peaker_committed_measured
        )

    def test_on_takes_the_band_s_own_measured_counterpart(self):
        on = _curve(**MEASURED, caiso_ct_peaker_committed_measured=True)
        self.assertEqual(on["CT_PEAKER"]["committed"], PHYS)
        self.assertEqual(
            on["CT_PEAKER"]["committed"], on["CT_PEAKER"]["phys_committed"]
        )
        self.assertTrue(
            bc.backcast_config(
                **BASE, **MEASURED, caiso_ct_peaker_committed_measured=True
            ).caiso_ct_peaker_committed_measured
        )

    def test_exactly_one_band_on_exactly_one_group_moves(self):
        moved = _moved(
            _curve(**MEASURED),
            _curve(**MEASURED, caiso_ct_peaker_committed_measured=True),
        )
        self.assertEqual(list(moved), ["CT_PEAKER"])
        self.assertEqual(moved["CT_PEAKER"], {"committed": (FITTED, PHYS)})

    def test_band_disjoint_from_the_measured_offer_surface(self):
        """Rule 19 [R-ONE-MECH]: the surface arms econ/peak, this arms committed."""
        plain = _curve()
        surface_moved = _moved(plain, _curve(**MEASURED))
        both_moved = _moved(
            plain, _curve(**MEASURED, caiso_ct_peaker_committed_measured=True)
        )
        surface_bands = set(surface_moved.get("CT_PEAKER", {}))
        both_bands = set(both_moved.get("CT_PEAKER", {}))
        self.assertNotIn("committed", surface_bands)
        self.assertEqual(both_bands - surface_bands, {"committed"})
        # every band the surface moves keeps the value the surface gave it
        for band, (_, on_val) in surface_moved["CT_PEAKER"].items():
            self.assertEqual(both_moved["CT_PEAKER"][band][1], on_val)

    def test_non_caiso_iso_is_a_hard_error(self):
        for iso in ("NYISO", "NEISO", "ERCOT", "PJM", "MISO"):
            with self.subTest(iso=iso), self.assertRaises(ValueError) as cm:
                bc.backcast_config(
                    iso=iso,
                    year=2024,
                    hours=8760,
                    gas_price=2.19,
                    caiso_ct_peaker_committed_measured=True,
                )
            self.assertIn("CAISO-scoped", str(cm.exception))

    def test_missing_phys_committed_is_a_hard_error_not_a_fallback(self):
        patched = {
            k: (
                {kk: vv for kk, vv in v.items() if kk != "phys_committed"}
                if k == "CT_PEAKER"
                else dict(v)
            )
            for k, v in bc._CAISO_OFFER_CURVE.items()
        }
        with mock.patch.object(bc, "_CAISO_OFFER_CURVE", patched):
            base_curve = _curve()
            # the generic fallback must not supply one either, or this test is vacuous
            self.assertNotIn("phys_committed", base_curve.get("CT_PEAKER", {}))
            with self.assertRaises(ValueError) as cm:
                _curve(caiso_ct_peaker_committed_measured=True)
        self.assertIn("phys_committed", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
