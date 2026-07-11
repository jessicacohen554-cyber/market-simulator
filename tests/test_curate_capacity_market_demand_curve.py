"""Tests for the capacity-market-demand-curve intake on a tiny synthetic fixture.

Writes a minimal unified PJM CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and the tidy reconciliation
(native ``vrr_point`` alias -> ``curve_point``, dtype coercion, valueless-row
drop) is correct. CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_capacity_deliverability.py) so it never touches the real
tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_capacity_market_demand_curve as curate_dc
from scripts.lib import capacity_market_demand_curve as dc
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# One delivery year: a scalar net_cone + irm row, three curve points (native
# vrr_point alias, to exercise the alias-mapping path), and a trailing
# valueless row (an unpublished cell) that must be dropped rather than
# written or raised on.
_PJM_CSV = """iso,delivery_year,area,season,metric,point_index,x_value,x_unit,y_value,y_unit,vintage,source_doc,source_page
PJM,2026/2027,,,net_cone,,,,270.5,usd_per_mw_day,2026/2027 BRA Planning Parameters,params-2026-2027.pdf,Table 3
PJM,2026/2027,,,irm,,,,15.9,pct,2026/2027 BRA Planning Parameters,params-2026-2027.pdf,Table 3
PJM,2026/2027,,,vrr_point,0,0.95,pct_of_requirement,473.4,usd_per_mw_day,2026/2027 BRA Planning Parameters,params-2026-2027.pdf,Table 4
PJM,2026/2027,,,vrr_point,1,1.0,pct_of_requirement,270.5,usd_per_mw_day,2026/2027 BRA Planning Parameters,params-2026-2027.pdf,Table 4
PJM,2026/2027,,,vrr_point,2,1.14,pct_of_requirement,0.0,usd_per_mw_day,2026/2027 BRA Planning Parameters,params-2026-2027.pdf,Table 4
PJM,2027/2028,,,net_cone,,,,,usd_per_mw_day,2027/2028 BRA Planning Parameters,params-2027-2028.pdf,Table 3
"""


def _write_pjm_fixture(raw_root: Path) -> None:
    d = dc.raw_dir_for("PJM", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "pjm.csv").write_text(_PJM_CSV)


class TestCurateCapacityMarketDemandCurve(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_pjm(self) -> pd.DataFrame:
        _write_pjm_fixture(self.raw_root)
        written = curate_dc.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1, "expected one PJM partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-market-demand-curve")
        return pd.read_parquet(path)

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(set(df["iso"]), {"PJM"})
        self.assertEqual(list(df.columns), list(dc.CANONICAL_COLUMNS))

    def test_native_metric_alias_mapped(self) -> None:
        df = self._curate_pjm()
        self.assertIn("curve_point", set(df["metric"]))
        self.assertNotIn("vrr_point", set(df["metric"]))

    def test_scalar_metrics_have_no_point_index(self) -> None:
        df = self._curate_pjm()
        scalars = df[df["metric"].isin(["net_cone", "irm"])]
        self.assertTrue(scalars["point_index"].isna().all())
        self.assertEqual(
            dict(zip(scalars["metric"], scalars["y_value"])),
            {"net_cone": 270.5, "irm": 15.9},
        )

    def test_curve_points_ordered_with_index(self) -> None:
        df = self._curate_pjm()
        curve = df[df["metric"] == "curve_point"].sort_values("point_index")
        self.assertEqual(list(curve["point_index"]), [0.0, 1.0, 2.0])
        self.assertEqual(list(curve["y_value"]), [473.4, 270.5, 0.0])

    def test_valueless_row_dropped(self) -> None:
        df = self._curate_pjm()
        self.assertTrue(df[df["delivery_year"] == "2027/2028"].empty)

    def test_empty_iso_is_skipped(self) -> None:
        written = curate_dc.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(written, [])

    def test_unregistered_iso_raises(self) -> None:
        with self.assertRaises(ValueError):
            curate_dc.curate(raw_root=self.raw_root, isos=["NOTANISO"])

    def test_vocab_guard_rejects_bad_metric(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "delivery_year": ["2026/2027"],
                "area": [pd.NA],
                "season": [pd.NA],
                "metric": ["not_a_metric"],
                "point_index": [pd.NA],
                "x_value": [pd.NA],
                "x_unit": [pd.NA],
                "y_value": [100.0],
                "y_unit": ["usd_per_mw_day"],
                "vintage": ["x"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            dc.validate_tidy(dc.finalize(bad))

    def test_curve_point_missing_point_index_rejected(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "delivery_year": ["2026/2027"],
                "area": [pd.NA],
                "season": [pd.NA],
                "metric": ["curve_point"],
                "point_index": [pd.NA],
                "x_value": [1.0],
                "x_unit": ["pct_of_requirement"],
                "y_value": [100.0],
                "y_unit": ["usd_per_mw_day"],
                "vintage": ["x"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            dc.validate_tidy(dc.finalize(bad))

    def test_curve_point_with_only_x_value_accepted(self) -> None:
        # PJM's Manual 18 publishes the VRR curve as a formula whose price at
        # a point is not itself a standalone published number -- only the
        # point's x-position (reserve requirement fraction) is. Such a row
        # must survive validate_tidy with y_value null.
        formula_point = pd.DataFrame(
            {
                "iso": ["PJM"],
                "delivery_year": ["2026/2027"],
                "area": [pd.NA],
                "season": [pd.NA],
                "metric": ["curve_point"],
                "point_index": [0],
                "x_value": [0.99],
                "x_unit": ["pct_of_requirement"],
                "y_value": [pd.NA],
                "y_unit": ["usd_per_mw_day"],
                "vintage": ["x"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        out = dc.validate_tidy(dc.finalize(formula_point))
        self.assertTrue(out["y_value"].isna().all())

    def test_scalar_metric_still_requires_y_value(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "delivery_year": ["2026/2027"],
                "area": [pd.NA],
                "season": [pd.NA],
                "metric": ["net_cone"],
                "point_index": [pd.NA],
                "x_value": [pd.NA],
                "x_unit": [pd.NA],
                "y_value": [pd.NA],
                "y_unit": ["usd_per_mw_day"],
                "vintage": ["x"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            dc.validate_tidy(dc.finalize(bad))

    def test_pjm_registered(self) -> None:
        registry = dc.load_registry()
        self.assertIn("PJM", registry)


if __name__ == "__main__":
    unittest.main()
