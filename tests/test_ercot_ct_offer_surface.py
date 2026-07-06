"""Validation of the ERCOT G-22 condition-responsive CT/peaker offer surface.

Covers :func:`market_sim.data.fleet.apply_ercot_ct_offer_surface` — the
measured self-withholding offer posted on the CT/peaker ``econ``/``peak``
tranches above a net-load-percentile hinge (design note
``docs/handoffs/ercot-g22-offer-surface-2026-07.md``). The contract:

* flag off / non-ERCOT ⇒ byte-identical (the mechanism must never fire by
  default — rules 14/26);
* only CT_PEAKER ``econ``/``peak`` rows move, never the ``committed``/
  ``mustrun``/``sync`` min-gen scaffolding nor any other class (the CT↔ST
  coupling this design avoids — FINDING §6);
* sub-hinge hours are byte-identical (condition-responsive, not a static wall);
* the post is ``max(mc, level)`` — it raises, never lowers, an offer.
"""

import unittest

import numpy as np

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import (
    Generator,
    _load_ct_offer_surface,
    apply_ercot_ct_offer_surface,
)


def _gen(uid: str, group: str) -> Generator:
    return Generator(
        name=uid,
        unit_id=uid,
        plant_group=group,
        zone="LZ_HOUSTON",
        fuel_type="gas",
        pmax_mw=100.0,
    )


class TestCtOfferSurface(unittest.TestCase):
    def setUp(self) -> None:
        # CT econ + peak (targeted), CT committed (scaffolding, untouched),
        # CC econ (other class, untouched).
        self.gens = [
            _gen("PLANT1_econc00", "CT_PEAKER"),
            _gen("PLANT1_peak", "CT_PEAKER"),
            _gen("PLANT1_committed", "CT_PEAKER"),
            _gen("PLANT2_econc00", "CC_REGULAR"),
        ]
        self.T = 10
        self.mc = np.tile(np.array([[50.0], [60.0], [20.0], [30.0]]), (1, self.T))
        # strictly rising net-load: the top decile (hour 9) is the only q>=0.9 hour
        self.net = np.arange(self.T, dtype=float) * 100.0
        self.cfg_on = ScenarioConfig(iso="ERCOT", ercot_ct_offer_surface=True)

    def test_flag_off_byte_identical(self) -> None:
        mc = self.mc.copy()
        cfg = ScenarioConfig(iso="ERCOT", ercot_ct_offer_surface=False)
        self.assertFalse(apply_ercot_ct_offer_surface(mc, self.gens, self.net, cfg))
        self.assertTrue(np.array_equal(mc, self.mc))

    def test_non_ercot_byte_identical(self) -> None:
        mc = self.mc.copy()
        cfg = ScenarioConfig(iso="CAISO", ercot_ct_offer_surface=True)
        self.assertFalse(apply_ercot_ct_offer_surface(mc, self.gens, self.net, cfg))
        self.assertTrue(np.array_equal(mc, self.mc))

    def test_only_ct_econ_peak_raised_in_top_hours(self) -> None:
        mc = self.mc.copy()
        self.assertTrue(
            apply_ercot_ct_offer_surface(mc, self.gens, self.net, self.cfg_on)
        )
        hi = self.net >= np.quantile(self.net, 0.9)
        level = _load_ct_offer_surface()[-1][2]  # high-regime measured level
        # CT econ (0) and CT peak (1) raised to the measured level in top hours
        self.assertTrue(np.all(mc[0, hi] == level))
        self.assertTrue(np.all(mc[1, hi] == level))
        # scaffolding + other class untouched everywhere
        self.assertTrue(np.array_equal(mc[2], self.mc[2]))
        self.assertTrue(np.array_equal(mc[3], self.mc[3]))

    def test_sub_hinge_hours_byte_identical(self) -> None:
        mc = self.mc.copy()
        apply_ercot_ct_offer_surface(mc, self.gens, self.net, self.cfg_on)
        lo = self.net < np.quantile(self.net, 0.9)
        self.assertTrue(np.array_equal(mc[0, lo], self.mc[0, lo]))
        self.assertTrue(np.array_equal(mc[1, lo], self.mc[1, lo]))

    def test_max_never_lowers(self) -> None:
        mc = self.mc.copy()
        mc[0, 9] = 9999.0  # already above the measured level
        apply_ercot_ct_offer_surface(mc, self.gens, self.net, self.cfg_on)
        self.assertEqual(mc[0, 9], 9999.0)

    def test_frozen_surface_is_condition_responsive(self) -> None:
        # The low regime must be inert (0) so slack hours stay byte-identical;
        # the high regime must post a positive cap-band level above a hinge < 1.
        regimes = _load_ct_offer_surface()
        self.assertEqual(regimes[0][2], 0.0)
        hinge = min(lo for lo, _hi, lv in regimes if lv > 0.0)
        self.assertGreater(hinge, 0.0)
        self.assertLess(hinge, 1.0)


if __name__ == "__main__":
    unittest.main()
