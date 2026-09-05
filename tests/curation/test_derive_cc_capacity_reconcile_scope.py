"""Tests for the ``--classes`` scope argument of the CC capacity reconcile derive.

The derive's screened population became a PARAMETER at nyiso-191 (previously the
literal ``"CC_REGULAR"``). These tests pin the two properties that make that a
population argument rather than a tuning channel:

* **rule 25 ``[R-ISO-SCOPE]`` / reproducibility** — the default is
  ``("CC_REGULAR",)``, so re-deriving any ISO at the default screens exactly the
  plants it always did and every committed ``cc_capacity_reconcile_<ISO>.csv``
  reproduces. The raise-mode filter (the ERCOT curated-bin path, whose input is a
  solved bundle that is not in the repo) is pinned by selecting on the real
  bin CSV and asserting the widened-vs-default membership relation directly.
* **rules 23 / 24 — the thresholds are frozen.** Widening the class set must not
  move ``_CAP_MARGIN``, ``_MIN_DELTA``, ``_PURE_PLAY_CC_SHARE``,
  ``_CT_ONLY_RATIO``, ``_CAP_FEASIBLE_CF`` or ``_CC_NET_OF_GROSS``; the values
  are asserted against their literals so a future edit to any of them has to
  break a test that says so out loud.

Neither test builds a fleet or reads CAMPD — they are pure unit tests over the
derive's own constants and its class-selection predicate.
"""

import unittest

import pandas as pd

from scripts.data import derive_cc_capacity_reconcile as d


class TestDefaultScopeIsUnchanged(unittest.TestCase):
    """The default screened set is exactly what every committed table used."""

    def test_default_classes_is_cc_regular_only(self):
        self.assertEqual(d.DEFAULT_CLASSES, ("CC_REGULAR",))

    def test_isin_default_equals_the_old_equality_filter(self):
        """``Plant_Group.isin(DEFAULT_CLASSES)`` == the pre-change ``== "CC_REGULAR"``.

        Pins the raise-mode path (ERCOT), whose own input artifact is a solved
        bundle absent from the repo, so it cannot be re-derived in a test.
        """
        csv = pd.read_csv(d.CAMPD_BINS_CSV)
        old = csv[csv["Plant_Group"] == "CC_REGULAR"]
        new = csv[csv["Plant_Group"].isin(d.DEFAULT_CLASSES)]
        self.assertTrue(old.equals(new))
        self.assertGreater(len(old), 0, "fixture would be vacuous")

    def test_widening_is_purely_additive_on_membership(self):
        """A widened set selects a SUPERSET — it can never drop a screened plant."""
        csv = pd.read_csv(d.CAMPD_BINS_CSV)
        base = set(csv[csv["Plant_Group"].isin(d.DEFAULT_CLASSES)].index)
        wide = set(csv[csv["Plant_Group"].isin(("CC_REGULAR", "CC_CHP"))].index)
        self.assertTrue(base.issubset(wide))


class TestThresholdsAreFrozen(unittest.TestCase):
    """Widening the population must not move any screen threshold (rules 23/24)."""

    def test_frozen_constants(self):
        self.assertEqual(d._CAP_MARGIN, 1.10)
        self.assertEqual(d._MIN_DELTA, 0.01)
        self.assertEqual(d._PURE_PLAY_CC_SHARE, 0.90)
        self.assertEqual(d._CT_ONLY_RATIO, 1.1)
        self.assertEqual(d._CAP_FEASIBLE_CF, 0.90)
        self.assertEqual(d._CC_NET_OF_GROSS, 0.975)

    def test_cc_chp_shares_cc_regular_parasitic_load(self):
        """``_CC_NET_OF_GROSS`` is already right for the widened class.

        The derive converts CAMPD gross to net with one factor. Widening to
        ``CC_CHP`` would need a NEW constant if that class's registered
        parasitic load differed — it does not, so the widening adds no
        parameter.
        """
        from market_sim.data.campd import DEFAULT_PARASITIC_LOAD_PCT

        self.assertEqual(
            DEFAULT_PARASITIC_LOAD_PCT["CC_CHP"],
            DEFAULT_PARASITIC_LOAD_PCT["CC_REGULAR"],
        )
        self.assertAlmostEqual(
            d._CC_NET_OF_GROSS, 1.0 - DEFAULT_PARASITIC_LOAD_PCT["CC_CHP"]
        )


class TestNoCommittedTableIsWidened(unittest.TestCase):
    """The widening was TESTED AND REJECTED (nyiso-191) — no ISO ships it.

    ``docs/FINDING-nyiso191-ccchp-capacity-scope-2026-09-05.md``: widening NYISO
    to ``CC_CHP`` is inert and mildly counterproductive because
    ``chp_layup_duty_curve`` (matrix row ``offer_curve_by_group``, NYISO cell
    ``K``) already withholds those plants' capacity to a MEASURED
    price-conditional duty that binds tighter than the demonstrated peak in
    every cohort member — a rule 19 ``[R-ONE-MECH]`` collision. The ``--classes``
    argument stays because it made that adjudication reproducible and is a
    default-preserving no-op; what must not drift is any ISO silently acquiring
    the widened scope.
    """

    ISOS = ("NYISO", "CAISO", "MISO", "NEISO", "PJM", "ERCOT")

    def test_every_committed_table_is_cc_regular_only(self):
        from market_sim.config.paths import cc_capacity_reconcile_path

        for iso in self.ISOS:
            with self.subTest(iso=iso):
                t = pd.read_csv(cc_capacity_reconcile_path(iso))
                if "plant_group" in t.columns:
                    self.assertEqual(
                        set(t["plant_group"]),
                        {"CC_REGULAR"},
                        f"{iso} table carries a non-CC_REGULAR row — the nyiso-191 "
                        "widening was rejected and must not reappear without a new "
                        "adjudication",
                    )


if __name__ == "__main__":
    unittest.main()
