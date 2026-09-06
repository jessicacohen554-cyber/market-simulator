"""Synthetic-curve tests for ``scripts/ces_national_clearing.py`` (SCN-WS2b).

Zero-solve by construction: every curve here is a fabricated
``<iso>_clean_share_vs_premium.csv`` on the real column contract
``scripts/report_ces_campaign.py`` writes, with closed-form answers worked out
by hand in each test's docstring. The point of a synthetic curve is that the
right answer is known independently of the code under test.
"""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts import ces_national_clearing as C

HEADER = [
    "case",
    "year",
    "premium_usd_per_mwh",
    "clean_share",
    "negative_price_hours",
    "avg_price_usd_per_mwh",
    "generation_twh",
]


def _write_headline(
    root: Path, iso: str, rows: list[tuple[str, int, float, float, float]]
) -> Path:
    """Write one ISO's headline CSV; rows are (case, year, premium, share, twh)."""
    path = root / f"{iso.lower()}_clean_share_vs_premium.csv"
    with path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(HEADER)
        for case, year, premium, share, twh in rows:
            w.writerow([case, year, premium, share, 0, 40.0, twh])
    return path


def _curve(rows: list[tuple[str, int, float, float, float]]) -> dict:
    """Build the ``{year: [Rung]}`` mapping the solver consumes, via the reader."""
    with tempfile.TemporaryDirectory() as td:
        path = _write_headline(Path(td), "TEST", rows)
        _, per_year = C.read_headline(path)
    return per_year


class TestInterpolation(unittest.TestCase):
    """The energy interpolation, and its refusal to extrapolate."""

    def test_linear_midpoint(self):
        """A 0.30→0.50 share on a constant 100 TWh reads 0.40 at the midpoint.

        Credited energy is 30 TWh at $0 and 50 TWh at $40, so at $20 it is
        40 TWh on 100 TWh served — exactly 0.40.
        """
        rungs = _curve(
            [("BAU", 2030, 0.0, 0.30, 100.0), ("CES-40", 2030, 40.0, 0.50, 100.0)]
        )[2030]
        credited, served = C.interpolate(rungs, 20.0)
        self.assertAlmostEqual(credited / 1e6, 40.0, places=6)
        self.assertAlmostEqual(served / 1e6, 100.0, places=6)

    def test_served_energy_moves_with_the_premium(self):
        """Served energy is interpolated too, not pinned at the BAU volume.

        100 TWh at $0 and 120 TWh at $40 must read 110 TWh at $20; the share is
        then credited/served on the INTERPOLATED denominator, not the BAU one.
        """
        rungs = _curve(
            [("BAU", 2030, 0.0, 0.30, 100.0), ("CES-40", 2030, 40.0, 0.50, 120.0)]
        )[2030]
        credited, served = C.interpolate(rungs, 20.0)
        self.assertAlmostEqual(served / 1e6, 110.0, places=6)
        # credited: 30 TWh → 60 TWh, midpoint 45 TWh ⇒ share 45/110.
        self.assertAlmostEqual(credited / 1e6, 45.0, places=6)
        self.assertAlmostEqual(credited / served, 45.0 / 110.0, places=9)

    def test_refuses_to_extrapolate(self):
        """A premium outside the solved ladder raises rather than guessing."""
        rungs = _curve(
            [("BAU", 2030, 0.0, 0.30, 100.0), ("CES-40", 2030, 40.0, 0.50, 100.0)]
        )[2030]
        with self.assertRaises(ValueError):
            C.interpolate(rungs, 60.0)
        with self.assertRaises(ValueError):
            C.interpolate(rungs, -1.0)


class TestSingleIsoClearing(unittest.TestCase):
    """One ISO — the clearing premium is readable straight off the curve."""

    def test_monotone_curve_clears_at_the_exact_root(self):
        """0.30 at $0 → 0.50 at $40 on constant volume; a 0.40 target clears at $20.

        Residual f(p) = credited(p) − 0.40 × served = (30 + p/2) − 40 TWh, whose
        root is p = 20 exactly.
        """
        curves = {
            "TEST": _curve(
                [("BAU", 2030, 0.0, 0.30, 100.0), ("CES-40", 2030, 40.0, 0.50, 100.0)]
            )
        }
        [r] = C.clear_campaign(curves, {2030: 0.40})
        self.assertEqual(r.status, C.STATUS_CLEARED)
        self.assertAlmostEqual(r.premium, 20.0, places=6)
        self.assertAlmostEqual(r.system_share, 0.40, places=9)
        self.assertAlmostEqual(r.share_spread_pp, 0.0, places=9)

    def test_saturating_curve_picks_the_correct_segment(self):
        """A curve that rises fast then flattens clears inside the FIRST segment.

        Rungs (share on constant 100 TWh): $0→0.30, $20→0.55, $40→0.57. A 0.40
        target sits inside [0,20]: f(p) = 30 + 1.25p − 40 ⇒ p = 8.
        """
        curves = {
            "TEST": _curve(
                [
                    ("BAU", 2030, 0.0, 0.30, 100.0),
                    ("CES-20", 2030, 20.0, 0.55, 100.0),
                    ("CES-40", 2030, 40.0, 0.57, 100.0),
                ]
            )
        }
        [r] = C.clear_campaign(curves, {2030: 0.40})
        self.assertEqual(r.status, C.STATUS_CLEARED)
        self.assertAlmostEqual(r.premium, 8.0, places=6)

    def test_flat_curve_that_never_reaches_reports_not_reached(self):
        """An inert premium reports NOT_REACHED and no premium at all.

        A flat 0.30 share at every rung cannot reach 0.40; the result must
        carry the attainable share and refuse to name a price.
        """
        curves = {
            "TEST": _curve(
                [
                    ("BAU", 2030, 0.0, 0.30, 100.0),
                    ("CES-40", 2030, 40.0, 0.30, 100.0),
                ]
            )
        }
        [r] = C.clear_campaign(curves, {2030: 0.40})
        self.assertEqual(r.status, C.STATUS_NOT_REACHED)
        self.assertIsNone(r.premium)
        self.assertAlmostEqual(r.system_share, 0.30, places=9)
        self.assertTrue(any("Not met" in n for n in r.notes))

    def test_target_already_met_at_the_floor_is_an_upper_bound(self):
        """A target below the BAU share reports MET_AT_FLOOR, not $0 'cleared'.

        The distinction matters: the true clearing premium is BELOW the solved
        ladder (possibly negative), and the script must say so rather than
        report the floor as an estimate.
        """
        curves = {
            "TEST": _curve(
                [
                    ("BAU", 2030, 0.0, 0.45, 100.0),
                    ("CES-40", 2030, 40.0, 0.60, 100.0),
                ]
            )
        }
        [r] = C.clear_campaign(curves, {2030: 0.40})
        self.assertEqual(r.status, C.STATUS_MET_AT_FLOOR)
        self.assertAlmostEqual(r.premium, 0.0, places=9)
        self.assertTrue(any("UPPER BOUND" in n for n in r.notes))


class TestMultiIsoClearing(unittest.TestCase):
    """Two ISOs — the aggregate constraint, and the spread that is the result."""

    def _two_iso_curves(self) -> dict:
        """A cheap-abatement ISO and an expensive one, on equal volumes.

        A: 0.20 → 0.80 over $0–$40 on 100 TWh (steep).
        B: 0.40 → 0.44 over $0–$40 on 100 TWh (nearly inert).
        Aggregate credited(p) = (20 + 1.5p) + (40 + 0.1p) = 60 + 1.6p TWh on
        200 TWh served, so a 0.40 target (80 TWh) clears at p = 12.5.
        At $12.5: A = 0.20 + 0.015×12.5 = 0.3875; B = 0.40 + 0.001×12.5 = 0.4125.
        """
        return {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.20, 100.0),
                    ("CES-40", 2030, 40.0, 0.80, 100.0),
                ]
            ),
            "B": _curve(
                [
                    ("BAU", 2030, 0.0, 0.40, 100.0),
                    ("CES-40", 2030, 40.0, 0.44, 100.0),
                ]
            ),
        }

    def test_uniform_premium_clears_the_aggregate_not_each_iso(self):
        """The cleared point meets the SYSTEM target while each ISO misses it.

        That asymmetry is the whole content of the uniform-price representation:
        cheap abatement in A is doing B's compliance, which is only legitimate
        if credits trade across the seam.
        """
        [r] = C.clear_campaign(self._two_iso_curves(), {2030: 0.40})
        self.assertEqual(r.status, C.STATUS_CLEARED)
        self.assertAlmostEqual(r.premium, 12.5, places=6)
        self.assertAlmostEqual(r.system_share, 0.40, places=9)
        self.assertAlmostEqual(r.iso_shares["A"], 0.3875, places=9)
        self.assertAlmostEqual(r.iso_shares["B"], 0.4125, places=9)
        # Neither ISO individually carries the national share.
        self.assertLess(r.iso_shares["A"], 0.40)
        self.assertGreater(r.iso_shares["B"], 0.40)
        self.assertAlmostEqual(r.share_spread_pp, 2.5, places=6)

    def test_volume_weighting_is_by_energy_not_by_iso_count(self):
        """A ten-times-larger ISO dominates the aggregate, as energy weighting must.

        A: 0.20 flat on 1,000 TWh. B: 0.90 flat on 100 TWh. The system share is
        (200 + 90) / 1100 = 0.2636…, NOT the unweighted mean 0.55.
        """
        curves = {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.20, 1000.0),
                    ("CES-40", 2030, 40.0, 0.20, 1000.0),
                ]
            ),
            "B": _curve(
                [
                    ("BAU", 2030, 0.0, 0.90, 100.0),
                    ("CES-40", 2030, 40.0, 0.90, 100.0),
                ]
            ),
        }
        [r] = C.clear_campaign(curves, {2030: 0.25})
        self.assertAlmostEqual(r.system_share, 290.0 / 1100.0, places=9)
        self.assertEqual(r.status, C.STATUS_MET_AT_FLOOR)

    def test_mismatched_ladders_search_only_the_common_support(self):
        """When one ISO stops at $20, nothing is evaluated above $20.

        A spans $0–$40, B only $0–$20. The searchable range is [0, 20] and the
        result says so, rather than extrapolating B to $40.
        """
        curves = {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.20, 100.0),
                    ("CES-40", 2030, 40.0, 0.80, 100.0),
                ]
            ),
            "B": _curve(
                [
                    ("BAU", 2030, 0.0, 0.20, 100.0),
                    ("CES-20", 2030, 20.0, 0.30, 100.0),
                ]
            ),
        }
        [r] = C.clear_campaign(curves, {2030: 0.90})
        self.assertEqual(r.status, C.STATUS_NOT_REACHED)
        self.assertTrue(any("intersection" in n for n in r.notes))

    def test_missing_iso_year_is_excluded_and_named_never_zeroed(self):
        """An ISO with no rungs in a year is dropped from that year, with a note.

        Treating it as zero credited energy would fabricate a national shortfall
        out of a missing file.
        """
        curves = {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.50, 100.0),
                    ("CES-40", 2030, 40.0, 0.60, 100.0),
                ]
            ),
            "B": _curve(
                [
                    ("BAU", 2029, 0.0, 0.10, 100.0),
                    ("CES-40", 2029, 40.0, 0.10, 100.0),
                ]
            ),
        }
        results = {
            r.year: r for r in C.clear_campaign(curves, {2029: 0.40, 2030: 0.40})
        }
        self.assertEqual(results[2030].isos, ["A"])
        self.assertAlmostEqual(results[2030].system_share, 0.50, places=9)
        self.assertTrue(any("EXCLUDED" in n for n in results[2030].notes))
        self.assertEqual(results[2029].isos, ["B"])


class TestTargets(unittest.TestCase):
    """Target parsing: flat, and the sparse-knot convention."""

    def test_flat_target_applies_to_every_year(self):
        self.assertEqual(C.parse_targets("0.8", [2026, 2030]), {2026: 0.8, 2030: 0.8})

    def test_sparse_knots_interpolate_and_hold_flat_outside(self):
        """`2030:0.6,2050:1.0` reads 0.6 before 2030, 0.8 at 2040, 1.0 after 2050."""
        got = C.parse_targets("2030:0.6,2050:1.0", [2026, 2030, 2040, 2050, 2055])
        self.assertAlmostEqual(got[2026], 0.6, places=9)
        self.assertAlmostEqual(got[2030], 0.6, places=9)
        self.assertAlmostEqual(got[2040], 0.8, places=9)
        self.assertAlmostEqual(got[2050], 1.0, places=9)
        self.assertAlmostEqual(got[2055], 1.0, places=9)

    def test_out_of_range_target_is_refused(self):
        with self.assertRaises(SystemExit):
            C.parse_targets("1.4", [2030])


class TestReaderContract(unittest.TestCase):
    """The input contract, and the two refusals that keep it honest."""

    def test_missing_column_is_refused_with_a_named_source(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "test_clean_share_vs_premium.csv"
            path.write_text("case,year,clean_share\nBAU,2030,0.3\n")
            with self.assertRaises(SystemExit):
                C.read_headline(path)

    def test_ambiguous_ladder_is_refused_not_averaged(self):
        """Two cases at the same premium with different credited energy is an error."""
        with tempfile.TemporaryDirectory() as td:
            path = _write_headline(
                Path(td),
                "TEST",
                [
                    ("BAU", 2030, 0.0, 0.30, 100.0),
                    ("ALT", 2030, 0.0, 0.50, 100.0),
                ],
            )
            with self.assertRaises(SystemExit):
                C.read_headline(path)

    def test_iso_is_taken_from_the_filename_prefix(self):
        with tempfile.TemporaryDirectory() as td:
            path = _write_headline(Path(td), "ercot", [("BAU", 2030, 0.0, 0.3, 100.0)])
            iso, per_year = C.read_headline(path)
            self.assertEqual(iso, "ERCOT")
            self.assertEqual(sorted(per_year), [2030])


class TestReportOutputs(unittest.TestCase):
    """The bracket's empty half stays empty."""

    def test_markdown_says_the_bracket_is_open_when_ws2a_is_absent(self):
        curves = {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.30, 100.0),
                    ("CES-40", 2030, 40.0, 0.50, 100.0),
                ]
            )
        }
        results = C.clear_campaign(curves, {2030: 0.40})
        with tempfile.TemporaryDirectory() as td:
            md = Path(td) / "out.md"
            C.write_markdown(results, {}, md)
            text = md.read_text()
        self.assertIn("deliberately empty", text)
        self.assertIn("not estimated, inferred or filled with a placeholder", text)
        self.assertNotIn(
            "national total", text.lower().replace("not a national total", "")
        )

    def test_csv_leaves_the_target_row_columns_blank_without_ws2a(self):
        curves = {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.30, 100.0),
                    ("CES-40", 2030, 40.0, 0.50, 100.0),
                ]
            )
        }
        results = C.clear_campaign(curves, {2030: 0.40})
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.csv"
            C.write_csv(results, {}, out)
            rows = list(csv.DictReader(out.open()))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["target_row_share"], "")
        self.assertEqual(rows[0]["share_gap_pp"], "")
        self.assertEqual(rows[0]["iso_served_twh"], "100.0000")

    def test_target_row_results_close_the_bracket(self):
        """With WS-2a supplied, the gap column is the two representations' spread."""
        curves = {
            "A": _curve(
                [
                    ("BAU", 2030, 0.0, 0.30, 100.0),
                    ("CES-40", 2030, 40.0, 0.50, 100.0),
                ]
            )
        }
        results = C.clear_campaign(curves, {2030: 0.40})
        target_row = {("A", 2030): {"clean_share": 0.42, "premium_usd_per_mwh": 31.0}}
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "out.csv"
            C.write_csv(results, target_row, out)
            rows = list(csv.DictReader(out.open()))
        self.assertEqual(rows[0]["target_row_share"], "0.420000")
        # uniform-price 0.40 vs target-row 0.42 ⇒ −2.00 pp.
        self.assertAlmostEqual(float(rows[0]["share_gap_pp"]), -2.0, places=4)


if __name__ == "__main__":
    unittest.main()
