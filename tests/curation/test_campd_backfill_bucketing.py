"""Unit-prime-mover class bucketing for the CAMPD benchmark backfill.

``run_calibration_full._backfill_eia923_with_campd`` books a plant's measured
CAMPD net into the per-class EIA-923 benchmark. Before this fix it keyed the
whole plant net to a single last-generator-wins ``group_by_code`` class, so a
genuinely mixed-fuel plant (WA-Parish coal+gas, Doswell/Linden CC+CT) had large
energy blocks mislabelled — and, when the mapped class was the plant's *minority*
fuel, its measured CAMPD net was booked ON TOP of the already-correct majority
row, double-counting the plant. The fix splits the net across the plant's classes
by its measured EIA-923 prime-mover class shares (``class_shares``), keeps any
class EIA-923 already reports adequately, and preserves the plant total.

These are trivial synthetic fixtures (no on-disk data) exercising the backfill
directly: the real-data before/after (PJM/ERCOT) validates ``_plant_class_shares``
end-to-end. Every non-ERCOT / share-driven case is checked against the invariants;
the ERCOT / single-class / no-share paths are pinned byte-for-byte to the old
single-class behavior.
"""

import importlib.util
import unittest

import numpy as np
import pandas as pd
from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
_spec = importlib.util.spec_from_file_location(
    "rcf_bucketing", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_MCOLS = [f"m{i:02d}" for i in range(1, 13)]
_MIN = rcf._CAMPD_BACKFILL_MIN_MWH  # 50 GWh backfill threshold


def _e923_row(plant_id, klass, annual, year=2025):
    return {
        "year": np.int16(year),
        "plant_id": int(plant_id),
        "klass": klass,
        "annual_mwh": float(annual),
        **{c: float(annual) / 12.0 for c in _MCOLS},
    }


def _e923(rows):
    if not rows:
        return pd.DataFrame(
            columns=["year", "plant_id", "klass", "annual_mwh", *_MCOLS]
        )
    return pd.DataFrame(rows)


def _campd_year(nets, hours=24):
    """CAMPD net frame ``{plant_id: net_total_mwh}`` spread flat over ``hours``
    (all in January, so the assertions turn on the annual re-attribution)."""
    frames = [
        pd.DataFrame(
            {
                "plant_id": np.int32(int(pid)),
                "hour": np.arange(hours, dtype=np.int32),
                "net_mw": np.full(hours, float(total) / hours),
            }
        )
        for pid, total in nets.items()
    ]
    return pd.concat(frames, ignore_index=True)


def _annual(e923, pid, klass):
    mask = (e923["plant_id"] == int(pid)) & (e923["klass"] == klass)
    return float(e923.loc[mask, "annual_mwh"].sum())


def _plant_total(e923, pid):
    return float(e923.loc[e923["plant_id"] == int(pid), "annual_mwh"].sum())


class TestSingleClassAndFallback(unittest.TestCase):
    """Single-class / no-share plants keep the exact pre-split behavior."""

    def test_trivial_whole_net_to_mapped_class(self):
        # trivial case first: one plant, one class, no share map -> whole net
        # into the mapped class (the old single-class behavior).
        net = 10.0 * _MIN
        out = rcf._backfill_eia923_with_campd(
            _e923([]),
            _campd_year({700: net}),
            {700: "CC_REGULAR"},
            2025,
            class_shares=None,
        )
        self.assertAlmostEqual(_annual(out, 700, "CC_REGULAR"), net, places=3)
        self.assertAlmostEqual(_plant_total(out, 700), net, places=3)

    def test_default_arg_equals_explicit_none(self):
        # class_shares defaulting (old call signature) == passing None.
        net = 12.0 * _MIN
        e923 = _e923([_e923_row(710, "CC_REGULAR", 0.01 * _MIN)])
        cy = _campd_year({710: net})
        a = rcf._backfill_eia923_with_campd(e923.copy(), cy, {710: "CC_REGULAR"}, 2025)
        b = rcf._backfill_eia923_with_campd(
            e923.copy(), cy, {710: "CC_REGULAR"}, 2025, class_shares=None
        )
        self.assertAlmostEqual(_annual(a, 710, "CC_REGULAR"), net, places=3)
        self.assertAlmostEqual(_annual(b, 710, "CC_REGULAR"), net, places=3)

    def test_coal_fallback_uses_supply_class(self):
        # A coal plant's group IS its supply subclass since COAL-SUB
        # (2026-09-25), resolved at load by the same chain; with no shares the
        # fallback books the whole plant to it (rule/constraint 4 preserved).
        net = 10.0 * _MIN
        pid = 999901
        klass = "COAL_BIT"
        out = rcf._backfill_eia923_with_campd(
            _e923([]), _campd_year({pid: net}), {pid: klass}, 2025, class_shares=None
        )
        self.assertAlmostEqual(_annual(out, pid, klass), net, places=3)
        self.assertAlmostEqual(_plant_total(out, pid), net, places=3)

    def test_non_backfill_group_skipped(self):
        # a CHP / OTHER group is not eligible -> untouched.
        net = 10.0 * _MIN
        out = rcf._backfill_eia923_with_campd(
            _e923([]),
            _campd_year({720: net}),
            {720: "CC_CHP"},
            2025,
            class_shares={720: {"CC_REGULAR": 1.0}},
        )
        self.assertEqual(_plant_total(out, 720), 0.0)


class TestErcotPathUnchanged(unittest.TestCase):
    """``class_shares=None`` (the ERCOT path) reproduces single-class behavior."""

    def test_none_shares_books_whole_net_to_mapped_no_split(self):
        pid = 840
        net = 20.0 * _MIN
        e923 = _e923([_e923_row(pid, "CT_PEAKER", 0.01 * _MIN)])
        out = rcf._backfill_eia923_with_campd(
            e923, _campd_year({pid: net}), {pid: "CT_PEAKER"}, 2025, class_shares=None
        )
        # whole net into the single mapped class; no CC_REGULAR split row created
        self.assertAlmostEqual(_annual(out, pid, "CT_PEAKER"), net, places=3)
        self.assertEqual(_annual(out, pid, "CC_REGULAR"), 0.0)
        self.assertAlmostEqual(_plant_total(out, pid), net, places=3)


class TestMixedPlantSplit(unittest.TestCase):
    """Genuinely mixed plants split across their classes by measured shares."""

    def test_cc_ct_truncated_splits_by_shares_mass_preserved(self):
        # Doswell/Linden pattern: whole plant truncated in the current vintage,
        # split by (prior-year) shares. group maps to the minority class.
        net = 20.0 * _MIN
        pid = 810
        e923 = _e923(
            [
                _e923_row(pid, "CC_REGULAR", 0.001 * _MIN),  # under-reported
                _e923_row(pid, "CT_PEAKER", 0.001 * _MIN),  # under-reported
            ]
        )
        shares = {pid: {"CC_REGULAR": 0.8, "CT_PEAKER": 0.2}}
        out = rcf._backfill_eia923_with_campd(
            e923, _campd_year({pid: net}), {pid: "CT_PEAKER"}, 2025, class_shares=shares
        )
        cc = _annual(out, pid, "CC_REGULAR")
        ct = _annual(out, pid, "CT_PEAKER")
        # (i) net is SPLIT across the classes, not booked wholly to one
        self.assertAlmostEqual(cc, 0.8 * net, places=3)
        self.assertAlmostEqual(ct, 0.2 * net, places=3)
        self.assertGreater(cc, _MIN)
        self.assertGreater(ct, 0.0)
        # (ii) the split sums to the plant's CAMPD net
        self.assertAlmostEqual(cc + ct, net, places=3)
        self.assertAlmostEqual(_plant_total(out, pid), net, places=3)

    def test_coal_gas_split_by_shares_mass_preserved(self):
        # WA-Parish pattern: coal share -> its coal supply subclass, gas share ->
        # ST_GAS. group maps the whole plant to its coal subclass (COAL-SUB).
        net = 20.0 * _MIN
        pid = 820
        shares = {pid: {"COAL_BIT": 0.7, "ST_GAS": 0.3}}
        out = rcf._backfill_eia923_with_campd(
            _e923([]),
            _campd_year({pid: net}),
            {pid: "COAL_BIT"},
            2025,
            class_shares=shares,
        )
        coal = _annual(out, pid, "COAL_BIT")
        gas = _annual(out, pid, "ST_GAS")
        self.assertAlmostEqual(coal, 0.7 * net, places=3)
        self.assertAlmostEqual(gas, 0.3 * net, places=3)
        self.assertAlmostEqual(coal + gas, net, places=3)
        self.assertAlmostEqual(_plant_total(out, pid), net, places=3)

    def test_multi_under_class_split_is_share_weighted(self):
        # both eligible classes under-reported -> the whole net splits by shares
        # (the residual == net); shares need not be 50/50.
        net = 4.0 * _MIN
        pid = 860
        e923 = _e923(
            [
                _e923_row(pid, "CC_REGULAR", 0.4 * _MIN),
                _e923_row(pid, "CT_PEAKER", 0.2 * _MIN),
            ]
        )
        shares = {pid: {"CC_REGULAR": 0.65, "CT_PEAKER": 0.35}}
        out = rcf._backfill_eia923_with_campd(
            e923, _campd_year({pid: net}), {pid: "CT_PEAKER"}, 2025, class_shares=shares
        )
        self.assertAlmostEqual(_annual(out, pid, "CC_REGULAR"), 0.65 * net, places=3)
        self.assertAlmostEqual(_annual(out, pid, "CT_PEAKER"), 0.35 * net, places=3)
        self.assertAlmostEqual(_plant_total(out, pid), net, places=3)


class TestPartialReportedKept(unittest.TestCase):
    """A class EIA-923 already reports is measured and kept; no double count."""

    def test_reported_majority_kept_residual_to_minority(self):
        # Linden pattern: majority class adequately reported, minority (mapped)
        # class under-reported. OLD code booked the WHOLE net into the minority
        # class on top of the reported majority -> ~2x the plant. The fix keeps
        # the measured majority and books only the residual into the minority.
        pid = 830
        reported = 8.0 * _MIN
        net = reported + 0.2 * _MIN
        e923 = _e923(
            [
                _e923_row(pid, "CC_REGULAR", reported),  # >= MIN, measured
                _e923_row(pid, "CT_PEAKER", 0.02 * _MIN),  # < MIN, under-reported
            ]
        )
        shares = {pid: {"CC_REGULAR": 0.98, "CT_PEAKER": 0.02}}
        out = rcf._backfill_eia923_with_campd(
            e923, _campd_year({pid: net}), {pid: "CT_PEAKER"}, 2025, class_shares=shares
        )
        # measured majority untouched
        self.assertAlmostEqual(_annual(out, pid, "CC_REGULAR"), reported, places=3)
        # minority gets only the residual (net - reported), NOT the whole net
        self.assertAlmostEqual(_annual(out, pid, "CT_PEAKER"), net - reported, places=3)
        # plant total == CAMPD net (no double count)
        self.assertAlmostEqual(_plant_total(out, pid), net, places=3)


class TestAdequatelyReportedNotFired(unittest.TestCase):
    """The firing test is still the mapped class -> old touched-plant set."""

    def test_reported_mapped_class_untouched(self):
        pid = 850
        net = 10.0 * _MIN
        e923 = _e923([_e923_row(pid, "CC_REGULAR", 4.0 * _MIN)])  # >= MIN
        out = rcf._backfill_eia923_with_campd(
            e923,
            _campd_year({pid: net}),
            {pid: "CC_REGULAR"},
            2025,
            class_shares={pid: {"CC_REGULAR": 1.0}},
        )
        self.assertAlmostEqual(_annual(out, pid, "CC_REGULAR"), 4.0 * _MIN, places=3)

    def test_reported_mapped_leaves_secondary_under_class_untouched(self):
        # mapped class reported -> the whole plant is skipped (byte-identity
        # invariant vs the old code), even with a secondary under-reported class.
        pid = 851
        net = 10.0 * _MIN
        e923 = _e923(
            [
                _e923_row(pid, "CC_REGULAR", 4.0 * _MIN),  # mapped, reported
                _e923_row(pid, "CT_PEAKER", 0.01 * _MIN),  # secondary, under
            ]
        )
        out = rcf._backfill_eia923_with_campd(
            e923,
            _campd_year({pid: net}),
            {pid: "CC_REGULAR"},
            2025,
            class_shares={pid: {"CC_REGULAR": 0.9, "CT_PEAKER": 0.1}},
        )
        self.assertAlmostEqual(_annual(out, pid, "CC_REGULAR"), 4.0 * _MIN, places=3)
        self.assertAlmostEqual(_annual(out, pid, "CT_PEAKER"), 0.01 * _MIN, places=3)


if __name__ == "__main__":
    unittest.main()
