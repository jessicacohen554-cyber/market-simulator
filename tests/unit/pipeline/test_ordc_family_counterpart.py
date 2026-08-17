"""The counterpart decontamination of the published-anchor RTORPA (ercot-215).

``_system_frame``'s published-anchor branch (ercot-213) writes the additive
ORDC adder from a SINGLE counterpart — the all-tier reserve-supply-cap row's
dual — rescaled onto the published ``(VOLL - lambda)`` anchor. ercot-214
measured that this counterpart is CONTAMINATED: one capped reserve MW serves
an AS-product row and the ORDC total row simultaneously, so the cap dual
decomposes exactly (808/808 writing hours, 2023-25) as

    gamma_all = k x (VOLL / ercot_as_n_ramp) + gamma_ordc_family,   k integer

— the AS-product shortfall-ramp step plus the ORDC total family's own
balance-row dual. 2023-25 ERCOT has no real-time per-product scarcity pricing
(a product-vs-capability squeeze triggers RUC commitment, not a price —
``model/reserves/spec.py``, the ``ercot_ordc_only_scarcity`` citation block),
so the ramp term is a price-formation channel the real design cannot emit.

``ercot_ordc_adder_family_counterpart`` writes the ORDC component alone:
``gamma' = min(gamma_all, gamma_ordc_family)``. These tests pin (1) default-off
byte-identity with the published-anchor branch (keeper-reproducing), (2) the
exact decontaminated formula including the min's protocol-capped-hour
invariance, (3) inertness when armed WITHOUT the published-anchor branch or
without the cap-dual branch, (4) the family-column selection (LAST column =
the total family), and (5) the loud-error contract when the family duals are
absent (rule 5 — no silent fallback to the contaminated sum).

See docs/FINDING-ercot214-gspur-phase0-2026-08-17.md and
docs/PRECOMMIT-ercot215-counterpart-decontamination-2026-08-17.md.
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

from run_calibration_full import _system_frame  # noqa: E402

VOLL = 5000.0
RAMP_STEP = VOLL / 12.0  # the registered ercot_as_n_ramp=12 first step, $416.67
T = 6
ZONES = ["A", "B"]


@dataclass
class _Result:
    """Minimal DispatchResult stand-in carrying only what _system_frame reads."""

    prices: np.ndarray
    slack: np.ndarray
    reserve_price: np.ndarray
    reserve_supply_cap_dual: np.ndarray
    reserve_price_by_family: np.ndarray | None
    dump: np.ndarray | None = None


def _frame(
    cap_dual,
    prices,
    demand,
    rpf,
    *,
    anchor: bool = True,
    family_counterpart: bool,
    cap_dual_adder: bool = True,
    voll=VOLL,
):
    """Build the ERCOT system frame for one hour-block under the adder stack."""
    res = _Result(
        prices=prices,
        slack=np.zeros_like(prices),
        reserve_price=np.zeros(T),
        reserve_supply_cap_dual=cap_dual,
        reserve_price_by_family=rpf,
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
        ercot_ordc_cap_dual_adder=cap_dual_adder,
        ercot_ordc_adder_published_anchor=anchor,
        ercot_ordc_adder_family_counterpart=family_counterpart,
        ordc_voll=voll,
    )


def _adder(df) -> np.ndarray:
    """The written (T,) ordc_adder series (broadcast identically to every zone)."""
    return df[df["zone"] == ZONES[0]].sort_values("hour")["ordc_adder"].to_numpy()


class FamilyCounterpartTest(unittest.TestCase):
    def setUp(self) -> None:
        # The ORDC total family's own balance-row dual (T,): h0 quiet, h1-h3
        # the ercot-214 spill regime (family comfortable, cents-to-dollars),
        # h4 a real deep ORDC step, h5 ABOVE VOLL (the protocol-cap hour).
        self.fam = np.array([0.0, 0.31, 2.51, 25.7, 900.0, 6000.0])
        # Contamination k per hour: the AS-product shortfall-ramp step count
        # the ercot-214 decomposition isolates (k=0 hours are uncontaminated
        # and must be UNTOUCHED by the repair).
        self.k = np.array([0.0, 1.0, 1.0, 2.0, 0.0, 1.0])
        gamma_all = self.fam + self.k * RAMP_STEP
        # Two headroom tiers (fast, all): the fast tier is zero under the
        # published-anchor single-counterpart form; the all tier carries the
        # contaminated sum the LP would emit.
        self.cap_dual = np.vstack([np.zeros(T), gamma_all])
        # The total family is the LAST reserve family column (reserve_config
        # appends it last); two leading product columns prove [-1] selection.
        self.rpf = np.column_stack([np.full(T, 416.67), np.zeros(T), self.fam])
        self.prices = np.vstack(
            [
                np.array([20.0, 49.68, 58.27, 75.29, 120.0, 298.86]),
                np.array([25.0, 49.68, 58.27, 75.29, 140.0, 298.86]),
            ]
        )
        self.demand = np.vstack([np.full(T, 30_000.0), np.full(T, 10_000.0)])

    def _lambda(self) -> np.ndarray:
        return (self.prices * self.demand).sum(axis=0) / self.demand.sum(axis=0)

    def _head(self) -> np.ndarray:
        return np.maximum(VOLL - self._lambda(), 0.0)

    def test_default_off_is_the_published_anchor_branch(self) -> None:
        """Flag off reproduces the ercot-213 arm exactly — keeper-reproducing."""
        got = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                family_counterpart=False,
            )
        )
        head = self._head()
        want = np.minimum(self.cap_dual[-1] * head / VOLL, head)
        np.testing.assert_allclose(got, want)
        # ... and the contaminated hours really do carry the ramp leak the
        # repair exists for (h1: family $0.31, written adder ~$412).
        self.assertGreater(got[1], 400.0)

    def test_armed_writes_the_ordc_component_alone(self) -> None:
        """adder = min(min(gamma_all, gamma_fam) * (VOLL-lambda)/VOLL, VOLL-lambda)."""
        got = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                family_counterpart=True,
            )
        )
        head = self._head()
        gam = np.minimum(self.cap_dual[-1], self.fam)
        want = np.minimum(gam * head / VOLL, head)
        np.testing.assert_allclose(got, want)
        # Contaminated spill hours (k>=1, family at cents): the written adder
        # collapses to the family component's order of magnitude.
        self.assertLess(got[1], 1.0)
        self.assertLess(got[2], 3.0)
        # Uncontaminated hours (k=0) are byte-untouched vs the flag-off branch.
        off = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                family_counterpart=False,
            )
        )
        np.testing.assert_allclose(got[self.k == 0], off[self.k == 0])

    def test_protocol_capped_hour_is_invariant_under_the_min(self) -> None:
        """Where the adder saturates at VOLL - lambda the min changes nothing.

        h5: gamma_all = 6000 + 416.67 and gamma_fam = 6000, both >= VOLL, so
        the written adder is exactly VOLL - lambda either way — the 2023
        max-adder hour ($4,701.14 at lambda $298.86) the ercot-214
        counterfactual reports UNTOUCHED.
        """
        on = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                family_counterpart=True,
            )
        )
        off = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                family_counterpart=False,
            )
        )
        lam = self._lambda()
        self.assertAlmostEqual(on[5], VOLL - lam[5])
        self.assertAlmostEqual(on[5], off[5])
        self.assertAlmostEqual(on[5], 4701.14)

    def test_protocol_cap_lambda_plus_adder_never_exceeds_voll(self) -> None:
        """The published system-wide offer cap still holds hour by hour."""
        got = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                family_counterpart=True,
            )
        )
        self.assertTrue(np.all(self._lambda() + got <= VOLL + 1e-9))

    def test_flag_is_inert_without_the_published_anchor_branch(self) -> None:
        """Armed with the anchor OFF, the flag is never consulted: the branch
        writes the pre-repair two-tier sum either way."""
        on = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                anchor=False,
                family_counterpart=True,
            )
        )
        off = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                anchor=False,
                family_counterpart=False,
            )
        )
        np.testing.assert_allclose(on, off)
        np.testing.assert_allclose(on, self.cap_dual.sum(axis=0))

    def test_flag_is_inert_without_the_cap_dual_branch(self) -> None:
        """Armed with the cap-dual adder OFF, the total-family balance-dual
        branch runs and the flag changes nothing."""
        on = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                cap_dual_adder=False,
                family_counterpart=True,
            )
        )
        off = _adder(
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                self.rpf,
                cap_dual_adder=False,
                family_counterpart=False,
            )
        )
        np.testing.assert_allclose(on, off)
        np.testing.assert_allclose(on, self.fam)

    def test_missing_family_duals_is_a_loud_error(self) -> None:
        """Rule 5: no silent fallback to the contaminated sum when the family
        stack is absent."""
        with self.assertRaises(ValueError):
            _frame(
                self.cap_dual,
                self.prices,
                self.demand,
                None,
                family_counterpart=True,
            )


if __name__ == "__main__":
    unittest.main()
