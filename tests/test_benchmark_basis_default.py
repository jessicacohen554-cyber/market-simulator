"""Integration guard: the G-21/G-21b benchmark basis is the go-forward default.

This test is the CI backstop for the owner directive of **2026-07-12**
(session_01SfBzT4EggvRfh35MYgoYXH): the "new PJM scoring mechanism" for class and
fuel-family totals is the repo default for **every ISO**, unconditional, with no
flag or env knob able to re-arm the old basis. Three mechanisms make up that
basis; the unit-level tests pin each one in isolation
(``tests/test_vintage_reconcile_foldin.py`` and
``tests/test_campd_backfill_bucketing.py`` cover fixes 1 and 2, and the
``test_g21b_*`` cases in ``tests/test_calibration_verdict.py`` cover fix 3). This
file instead pins the *system-level invariant* the directive settled — **no raw
EIA-930 per-fuel cell gates a scored class or family number** — so that a future
edit which reintroduces any of the three deprecated behaviors fails CI here with a
pointer back to the log entries and the directive:

  1. **G-21 combined reconcile** (``render_calibration_html.reconcile_vintage_classes``)
     — the fossil family reconciles to EIA-930 as ONE combined gas+coal family
     (level corrected, CEMS-validated 923 split preserved). The retired
     per-family reconcile scaled gas and coal each to their own unreliable
     EIA-930 fuel cell, manufacturing PJM's phantom "+21 TWh CC_REGULAR over-run".
     Log: ``docs/calibration-log.md`` 2026-07-11 "SCORER FIX (all ISOs)" +
     2026-07-12 PJM pjm-98 promotion; ``docs/handoffs/
     pjm-cc-overrun-benchmark-basis-g21-2026-07.md``.
  2. **#2049 backfill bucketing** (``run_calibration_full._backfill_eia923_with_campd``
     × ``_plant_class_shares``) — a mixed non-ERCOT plant's CAMPD net splits by
     measured EIA-923 prime-mover class shares. The retired last-generator-wins
     path double-counted minority-class plants (PJM Linden p2406 ≈9.5 → ≈4.8 TWh).
  3. **G-21b C2 preliminary-vintage fallback** (``calibration_verdict.score_sysvol``
     + ``_fallback_coal_anchor``) — an incomplete family gates on the EIA-930
     COMBINED-fossil LEVEL with a CEMS-anchored coal/gas split, never the raw 930
     per-fuel cell.

All three are UNCONDITIONAL in code (verified 2026-07-12): no flags, no env vars,
no ``getattr`` fallback literals (CLAUDE.md rule 24). These guards assert that
property behaviorally and structurally, not merely that the mechanisms exist.
"""

import ast
import importlib.util
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]


def _load(mod_name: str, filename: str):
    spec = importlib.util.spec_from_file_location(
        mod_name, str(_REPO / "scripts" / filename)
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rch = _load("rch_basis", "render_calibration_html.py")
rcf = _load("rcf_basis", "run_calibration_full.py")
cv = _load("cv_basis", "calibration_verdict.py")

# The directive/log citation surfaced in every failure message so a future editor
# who trips a guard is pointed straight at why the behavior is load-bearing.
_CITE = (
    "owner default directive 2026-07-12 (benchmark basis is the go-forward "
    "default for ALL ISOs); docs/calibration-log.md 2026-07-11 'SCORER FIX "
    "(all ISOs)' + 2026-07-12 pjm-98; docs/handoffs/"
    "pjm-cc-overrun-benchmark-basis-g21-2026-07.md"
)


# ---------------------------------------------------------------------------
# Completeness-map injection (mirrors tests/test_calibration_verdict.py so the
# family-fallback path is exercised hermetically, no committed parts read).
# ---------------------------------------------------------------------------
def _incomplete(iso: str):
    cv._COMPLETENESS_CACHE = {
        2025: {
            "isos": {iso: {}},
            "families": {iso: {"gas": False, "coal": False}},
        }
    }


def _reset_completeness():
    cv._COMPLETENESS_CACHE = None


class TestCombinedReconcileIsTheDefault(unittest.TestCase):
    """Fix 1 — the fossil reconcile is COMBINED, never per-family.

    The litmus is the PJM-2024 signature: gas over / coal under that each breach
    the ±(1−frac) band but OFFSET to an in-band combined total. A per-family
    reconcile fires on both and forces the CEMS-validated split onto EIA-930's
    unreliable fuel attribution; the combined reconcile leaves it byte-identical.
    """

    def _gas(self, cf):
        return sum(cf[g] for g in rch._GAS_GROUPS if g in cf)

    def _coal(self, cf):
        return sum(cf[g] for g in rch._COAL_GROUPS if g in cf)

    def test_offsetting_split_left_byte_identical(self):
        # gas 384 vs 930 gas 368 = +4.3% (fires alone); coal 115 vs 930 coal 124
        # = −7.3% (fires alone); combined 499 vs 492 = +1.4% (in band).
        cf = {
            "CC_REGULAR": 336.0,
            "CT_PEAKER": 24.0,
            "ST_GAS": 24.0,
            "COAL_BIT": 115.0,
            "OTHER": 2.0,
            "biomass": 5.0,
        }
        before = dict(cf)
        e930 = {"gas": 368.0, "coal": 124.0, "other": 7.0}
        rch.reconcile_vintage_classes(cf, e930, "PJM")
        self.assertEqual(
            cf,
            before,
            "A per-family EIA-930 reconcile was reintroduced: the offsetting "
            "gas-over/coal-under split scaled instead of being left untouched. "
            "The fossil family must reconcile as ONE combined total (level only, "
            f"CEMS split preserved). {_CITE}",
        )

    def test_out_of_band_total_preserves_cems_split_not_per_fuel_cells(self):
        # Both families under-report; combined scales UP by ONE factor, so the
        # coal/gas ratio stays the 923 CEMS-measured ratio and coal is NOT pinned
        # to the raw 930 coal cell (the old per-family behaviour).
        cf = {"CC_REGULAR": 300.0, "COAL_BIT": 100.0, "OTHER": 1.0, "biomass": 1.0}
        e930 = {"gas": 340.0, "coal": 120.0, "other": 2.0}  # combined 460 vs 400
        rch.reconcile_vintage_classes(cf, e930, "PJM")
        self.assertAlmostEqual(self._gas(cf) + self._coal(cf), 460.0, places=1)
        self.assertAlmostEqual(cf["COAL_BIT"] / cf["CC_REGULAR"], 100.0 / 300.0, 3)
        self.assertLess(
            cf["COAL_BIT"],
            120.0,
            "Coal was pinned to the raw EIA-930 coal cell (120) — the retired "
            f"per-family reconcile. Combined reconcile scales the split. {_CITE}",
        )


class TestNoRawPerFuelCellGates(unittest.TestCase):
    """Fix 3 — C2's preliminary-vintage fallback gates on the CEMS-anchored split.

    Whenever the bench carries ``coal_cems`` and a complete-vintage k is
    derivable, the coal family gates on the CEMS anchor and the gas family on the
    930 COMBINED total minus that anchor — never the raw 930 per-fuel cell. The
    raw cell is used ONLY on the explicitly-labelled legacy path (no anchor).
    """

    # MISO-shaped: 930 coal 192.1 runs −20.9 TWh below CEMS 213.0, the documented
    # attribution swap the anchor corrects; k from the complete 2023/24 vintages.
    _BENCH_ALL = {
        2023: {
            "classFull": {"COAL_PRB": 121.7, "COAL_BIT": 57.1, "COAL_LIGNITE": 7.0},
            "e930": {"coal": 174.9, "coal_cems": 191.8},
        },
        2024: {
            "classFull": {"COAL_PRB": 116.5, "COAL_BIT": 53.3, "COAL_LIGNITE": 6.5},
            "e930": {"coal": 167.1, "coal_cems": 185.1},
        },
        2025: {
            "classFull": {},
            "e930": {"gas": 233.2, "coal": 192.1, "coal_cems": 213.0},
        },
    }

    def setUp(self):
        _incomplete("MISO")

    def tearDown(self):
        _reset_completeness()

    def _row(self, gm, key):
        rows = cv.score_sysvol(
            2025,
            {"gmModel": gm},
            self._BENCH_ALL[2025],
            "MISO",
            bench_all=self._BENCH_ALL,
        )
        return [r for r in rows if r["key"] == key][0]

    def test_coal_family_actual_is_the_cems_anchor_not_raw_cell(self):
        coal = self._row({"COAL_PRB": 205.0}, "coal")
        raw = self._BENCH_ALL[2025]["e930"]["coal"]  # 192.1
        self.assertNotAlmostEqual(
            coal["actual"],
            raw,
            places=1,
            msg="C2 coal family gated on the raw EIA-930 coal cell (192.1). It "
            "must gate on the CEMS anchor (CAMPD coal × complete-vintage grid "
            f"ratio) whenever coal_cems is present. {_CITE}",
        )
        self.assertIn("CEMS", coal["source"], _CITE)

    def test_gas_family_actual_is_combined_minus_anchor_not_raw_cell(self):
        gas = self._row({"CC_REGULAR": 205.0}, "gas")
        raw = self._BENCH_ALL[2025]["e930"]["gas"]  # 233.2
        self.assertNotAlmostEqual(
            gas["actual"],
            raw,
            places=1,
            msg="C2 gas family gated on the raw EIA-930 gas cell (233.2). It must "
            "gate on the 930 COMBINED fossil total minus the coal anchor "
            f"whenever a coal anchor is derivable. {_CITE}",
        )
        self.assertIn("combined fossil minus coal anchor", gas["source"], _CITE)

    def test_anchor_is_preferred_whenever_coal_cems_present(self):
        # The load-bearing invariant: coal_cems present + a complete-vintage k
        # derivable => the anchor helper returns non-None and the coal family
        # never falls back to the raw-930-cell "preliminary-923 vintage" source.
        anchor = cv._fallback_coal_anchor(
            "MISO", self._BENCH_ALL[2025], self._BENCH_ALL
        )
        self.assertIsNotNone(
            anchor,
            "_fallback_coal_anchor returned None though coal_cems is present and "
            "complete-vintage coal years exist — the anchor path was disabled. "
            f"{_CITE}",
        )
        coal = self._row({"COAL_PRB": 205.0}, "coal")
        self.assertNotIn(
            "preliminary-923 vintage",
            coal["source"],
            "Coal family fell back to the raw-930-cell legacy source though the "
            f"CEMS anchor was available. {_CITE}",
        )


class TestNonErcotBackfillAlwaysPassesShares(unittest.TestCase):
    """Fix 2 — the non-ERCOT plant-level CAMPD backfill always passes class shares.

    Structural: the sole production call site (``_benchmark_eia923_frame``) wires
    ``_plant_class_shares`` into every non-ERCOT backfill. Behavioral: a
    minority-mapped mixed plant double-counts under the shares-less path, so
    dropping shares changes a SCORED number — the guard proves the shares path is
    the mass-preserving one the directive settled.
    """

    _MIN = rcf._CAMPD_BACKFILL_MIN_MWH
    _MCOLS = [f"m{i:02d}" for i in range(1, 13)]

    def _campd(self, pid, total, hours=24):
        return pd.DataFrame(
            {
                "plant_id": np.int32(int(pid)),
                "hour": np.arange(hours, dtype=np.int32),
                "net_mw": np.full(hours, float(total) / hours),
            }
        )

    def _e923(self, rows):
        cols = ["year", "plant_id", "klass", "annual_mwh", *self._MCOLS]
        return pd.DataFrame(rows or [], columns=cols if not rows else None)

    def _row(self, pid, klass, annual):
        return {
            "year": np.int16(2025),
            "plant_id": int(pid),
            "klass": klass,
            "annual_mwh": float(annual),
            **{c: float(annual) / 12.0 for c in self._MCOLS},
        }

    def _plant_total(self, e923, pid):
        return float(e923.loc[e923["plant_id"] == int(pid), "annual_mwh"].sum())

    def test_shares_path_prevents_the_minority_mapped_double_count(self):
        # Linden pattern: majority CC_REGULAR adequately reported, minority
        # (mapped) CT_PEAKER under-reported. Shares-less books the WHOLE net into
        # the minority ON TOP of the reported majority (≈2× the plant). Shares
        # books only the residual, so the plant total == CAMPD net (mass held).
        pid = 2406  # PJM Linden — the documented ≈9.5→≈4.8 TWh regression
        reported = 8.0 * self._MIN
        net = reported + 0.2 * self._MIN
        rows = [
            self._row(pid, "CC_REGULAR", reported),
            self._row(pid, "CT_PEAKER", 0.02 * self._MIN),
        ]
        shares = {pid: {"CC_REGULAR": 0.98, "CT_PEAKER": 0.02}}
        gmap = {pid: "CT_PEAKER"}

        with_shares = rcf._backfill_eia923_with_campd(
            self._e923(rows), self._campd(pid, net), gmap, 2025, class_shares=shares
        )
        no_shares = rcf._backfill_eia923_with_campd(
            self._e923(rows), self._campd(pid, net), gmap, 2025, class_shares=None
        )
        t_shares = self._plant_total(with_shares, pid)
        t_none = self._plant_total(no_shares, pid)

        self.assertAlmostEqual(
            t_shares,
            net,
            places=3,
            msg="Shares-driven backfill must preserve the plant's CAMPD net "
            f"(no double count). {_CITE}",
        )
        self.assertGreater(
            t_none,
            t_shares + self._MIN,
            "Shares-less and shares-driven backfill produced the SAME plant total "
            "— the minority-mapped double count is gone from both, so the "
            "regression this guard protects is no longer observable; re-anchor "
            f"the fixture. {_CITE}",
        )

    def test_sole_backfill_call_site_wires_plant_class_shares(self):
        # Structural guard (rule 24): parse run_calibration_full.py and assert the
        # ONLY call to _backfill_eia923_with_campd supplies a class_shares kwarg,
        # and _benchmark_eia923_frame derives it from _plant_class_shares gated
        # solely on iso == "ERCOT". A regression hardwiring class_shares=None (or
        # dropping the kwarg) for the non-ERCOT path fails here.
        src = (_REPO / "scripts" / "run_calibration_full.py").read_text()
        tree = ast.parse(src)

        backfill_calls = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "_backfill_eia923_with_campd"
        ]
        self.assertEqual(
            len(backfill_calls),
            1,
            f"Expected exactly one _backfill_eia923_with_campd call site. {_CITE}",
        )
        kwnames = {kw.arg for kw in backfill_calls[0].keywords}
        self.assertIn(
            "class_shares",
            kwnames,
            "The backfill call site dropped the class_shares keyword — non-ERCOT "
            f"plants would revert to last-generator-wins bucketing. {_CITE}",
        )

        frame_fn = next(
            n
            for n in ast.walk(tree)
            if isinstance(n, ast.FunctionDef) and n.name == "_benchmark_eia923_frame"
        )
        frame_src = ast.get_source_segment(src, frame_fn) or ""
        self.assertIn("_plant_class_shares", frame_src, _CITE)
        # The gate is ISO == ERCOT only: non-ERCOT ALWAYS computes shares — so
        # the shares value is a ternary keyed on that test, never a bare literal.
        gate = next(
            n
            for n in ast.walk(frame_fn)
            if isinstance(n, ast.IfExp)
            and isinstance(n.test, ast.Compare)
            and any(
                isinstance(c, ast.Constant) and c.value == "ERCOT"
                for c in (n.test.left, *n.test.comparators)
            )
        )
        # The non-ERCOT (orelse) branch must call _plant_class_shares, not None.
        self.assertTrue(
            isinstance(gate.orelse, ast.Call)
            and isinstance(gate.orelse.func, ast.Name)
            and gate.orelse.func.id == "_plant_class_shares",
            "The non-ERCOT branch of the class_shares gate no longer computes "
            f"_plant_class_shares — shares-less backfill was re-armed. {_CITE}",
        )


if __name__ == "__main__":
    unittest.main()
