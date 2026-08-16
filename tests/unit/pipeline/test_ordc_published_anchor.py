"""The published-anchor repair of the cap-additive RTORPA (ercot-213).

``_system_frame``'s cap-dual branch writes the post-solve additive ORDC price
adder from the reserve-supply-cap rows' duals. Those duals come out of a
**VOLL-anchored** in-LP demand curve (``scarcity.ercot_ordc_demand_steps`` —
an LP objective coefficient must be constant, so lambda cannot appear in it),
while the published additive formula the channel is emulating is

    RTORPA = 0.5 (VOLL - lambda) (LOLP_full + LOLP_half),   lambda + adder <= VOLL

(:func:`market_sim.results.scarcity.ordc_adder`). Writing the VOLL-anchored
dual verbatim, summed over BOTH headroom tiers, can therefore emit up to
2 x VOLL — a price the market design cannot produce, which is what killed the
ercot-212 arm (docs/FINDING-ercot212-reserve-basis-phase0-2026-08-16.md §5).

``ercot_ordc_adder_published_anchor`` repairs both halves: a SINGLE counterpart
(the all-tier / total-reserve cap row) rescaled onto the ``(VOLL - lambda)``
anchor and capped at ``VOLL - lambda``. These tests pin (1) default-off
byte-identity with the pre-repair branch, (2) the exact published identity
against ``ordc_adder`` itself, (3) the protocol cap, and (4) the
single-counterpart property.
"""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
for _p in (str(REPO), str(REPO / "src"), str(REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from market_sim.results.scarcity import lolp  # noqa: E402
from run_calibration_full import _system_frame  # noqa: E402

VOLL = 5000.0
T = 6
ZONES = ["A", "B"]


@dataclass
class _Result:
    """Minimal DispatchResult stand-in carrying only what _system_frame reads."""

    prices: np.ndarray
    slack: np.ndarray
    reserve_price: np.ndarray
    reserve_supply_cap_dual: np.ndarray
    reserve_price_by_family: np.ndarray
    dump: np.ndarray | None = None


def _frame(cap_dual, prices, demand, *, anchor: bool, voll=VOLL):
    """Build the ERCOT system frame for one hour-block under the cap-dual branch."""
    res = _Result(
        prices=prices,
        slack=np.zeros_like(prices),
        reserve_price=np.zeros(T),
        reserve_supply_cap_dual=cap_dual,
        reserve_price_by_family=np.zeros((T, 1)),
    )
    return _system_frame(
        2024,
        "P1",
        res,
        demand,
        ZONES,
        iso="ERCOT",
        ercot_reserve_supply_cap=True,
        ercot_ordc_total_reserve=True,
        ercot_ordc_cap_dual_adder=True,
        ercot_ordc_adder_published_anchor=anchor,
        ordc_voll=voll,
    )


def _adder(df) -> np.ndarray:
    """The written (T,) ordc_adder series (broadcast identically to every zone)."""
    return df[df["zone"] == ZONES[0]].sort_values("hour")["ordc_adder"].to_numpy()


class PublishedAnchorTest(unittest.TestCase):
    def setUp(self) -> None:
        # Two headroom tiers (fast, all) x T hours, hand-set to exercise the
        # sum-vs-single-counterpart difference and the 2 x VOLL ceiling.
        self.cap_dual = np.array(
            [
                [0.0, 100.0, 5000.0, 250.0, 0.0, 40.0],  # fast tier
                [0.0, 300.0, 5000.0, 0.0, 900.0, 40.0],  # all tier
            ]
        )
        self.prices = np.vstack(
            [
                np.array([20.0, 45.0, 3000.0, 60.0, 120.0, 30.0]),
                np.array([25.0, 55.0, 3200.0, 80.0, 140.0, 30.0]),
            ]
        )
        self.demand = np.vstack([np.full(T, 30_000.0), np.full(T, 10_000.0)])

    def _lambda(self) -> np.ndarray:
        return (self.prices * self.demand).sum(axis=0) / self.demand.sum(axis=0)

    def test_default_off_is_the_pre_repair_two_tier_sum(self) -> None:
        """Flag off reproduces the armed branch exactly — keeper-reproducing."""
        got = _adder(_frame(self.cap_dual, self.prices, self.demand, anchor=False))
        np.testing.assert_allclose(got, self.cap_dual.sum(axis=0))
        # ... and that pre-repair series really does exceed VOLL (2 x VOLL in
        # h2), which is the defect the repair exists for.
        self.assertGreater(got.max(), VOLL)
        self.assertAlmostEqual(got[2], 2.0 * VOLL)

    def test_armed_is_single_counterpart_on_the_published_anchor(self) -> None:
        """adder = gamma_all * (VOLL - lambda) / VOLL, capped at VOLL - lambda."""
        lam = self._lambda()
        headroom = np.maximum(VOLL - lam, 0.0)
        want = np.minimum(self.cap_dual[-1] * headroom / VOLL, headroom)
        got = _adder(_frame(self.cap_dual, self.prices, self.demand, anchor=True))
        np.testing.assert_allclose(got, want)
        # The fast-tier-only hour (h3: fast 250, all 0) writes NOTHING: the
        # total-reserve family is not the constrained one there.
        self.assertEqual(got[3], 0.0)
        # The h4 hour (fast 0, all 900) is carried on the all tier alone.
        self.assertGreater(got[4], 0.0)

    def test_protocol_cap_lambda_plus_adder_never_exceeds_voll(self) -> None:
        """The published system-wide offer cap holds hour by hour."""
        lam = self._lambda()
        got = _adder(_frame(self.cap_dual, self.prices, self.demand, anchor=True))
        self.assertTrue(np.all(lam + got <= VOLL + 1e-9))
        # h2 is the pre-repair 2 x VOLL hour; it now lands exactly on the cap
        # (its all-tier dual is VOLL, so the rescale returns VOLL - lambda).
        self.assertAlmostEqual(got[2], VOLL - lam[2])

    def test_reproduces_the_published_ordc_adder_at_the_same_level(self) -> None:
        """The rescale IS the published formula — an anchor change, not a curve change.

        Take a reserve level R, price it with the in-LP VOLL-anchored curve to
        get the cap dual the LP would carry, run it through the repair, and
        compare against ``0.5 (VOLL - lambda)(LOLP_full + LOLP_half)`` evaluated
        at that same R — the published RTORPA.
        """
        mu, sigma, mcl, shift = 924.0, 1348.0, 3000.0, 0.5
        r = np.array([4000.0, 5500.0, 6800.0, 8000.0, 9500.0, 10500.0])
        lolp_f = lolp(r, mu, sigma, mcl, shift)
        lolp_h = lolp(r, mu / 2.0, sigma / np.sqrt(2.0), mcl, shift)
        gamma = 0.5 * VOLL * (lolp_f + lolp_h)  # the VOLL-anchored LP step price
        cap_dual = np.vstack([np.zeros(T), gamma])

        got = _adder(_frame(cap_dual, self.prices, self.demand, anchor=True))
        lam = self._lambda()
        published = np.minimum(
            0.5 * np.maximum(VOLL - lam, 0.0) * (lolp_f + lolp_h),
            np.maximum(VOLL - lam, 0.0),
        )
        np.testing.assert_allclose(got, published, rtol=1e-12, atol=1e-12)

    def test_single_row_cap_is_its_own_total_reserve_row(self) -> None:
        """The lumped single-product design has one cap row; it is the all tier."""
        one = self.cap_dual[[1]]
        got = _adder(_frame(one, self.prices, self.demand, anchor=True))
        two = _adder(_frame(self.cap_dual, self.prices, self.demand, anchor=True))
        np.testing.assert_allclose(got, two)

    def test_missing_voll_is_a_loud_error_not_a_silent_default(self) -> None:
        """Rule 5: no magic VOLL — the registered value must be threaded in."""
        with self.assertRaises(ValueError):
            _frame(self.cap_dual, self.prices, self.demand, anchor=True, voll=None)

    def test_flag_is_inert_without_the_cap_dual_branch(self) -> None:
        """Armed alone (cap-dual adder off) the flag changes nothing."""
        res = _Result(
            prices=self.prices,
            slack=np.zeros_like(self.prices),
            reserve_price=np.zeros(T),
            reserve_supply_cap_dual=self.cap_dual,
            reserve_price_by_family=np.arange(T, dtype=float).reshape(T, 1),
        )
        kw = dict(
            iso="ERCOT",
            ercot_reserve_supply_cap=True,
            ercot_ordc_total_reserve=True,
            ercot_ordc_cap_dual_adder=False,
            ordc_voll=VOLL,
        )
        off = _system_frame(
            2024,
            "P1",
            res,
            self.demand,
            ZONES,
            **kw,
            ercot_ordc_adder_published_anchor=False,
        )
        on = _system_frame(
            2024,
            "P1",
            res,
            self.demand,
            ZONES,
            **kw,
            ercot_ordc_adder_published_anchor=True,
        )
        np.testing.assert_allclose(_adder(off), _adder(on))
        # ... and it is the total-family balance-dual branch that ran.
        np.testing.assert_allclose(_adder(on), np.arange(T, dtype=float))


if __name__ == "__main__":
    unittest.main()
