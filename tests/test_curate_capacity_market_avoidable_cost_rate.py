"""Tests for the capacity-market-avoidable-cost-rate intake on a tiny fixture.

Writes a minimal unified PJM CSV into a tmp raw tree, runs ``curate``, and
asserts the written Parquet is schema-valid and the tidy reconciliation
(dtype coercion, valueless-row drop, vocab guards) is correct. CLEAN_DIR is
redirected to a tmp dir (as in
tests/test_curate_capacity_market_demand_curve.py) so it never touches the
real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_capacity_market_avoidable_cost_rate as curate_acr
from scripts.lib import capacity_market_avoidable_cost_rate as acr
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

# Two source types for the same technology class (PJM's own default vs. the
# IMM's independent benchmark), plus a trailing valueless row (an unpublished
# cell) that must be dropped rather than written or raised on.
_PJM_CSV = """iso,source_type,technology_class,capacity_bin,cost_component,value,unit,vintage,source_doc,source_page
PJM,pjm_manual18_default,Combustion Turbine,,gross_acr,7.87,usd_per_kw_month,"PJM Manual 18, Revision 62, effective 2025-12-17",m18.pdf,Schedule 2
PJM,pjm_manual18_default,Combined Cycle,,gross_acr,5.12,usd_per_kw_month,"PJM Manual 18, Revision 62, effective 2025-12-17",m18.pdf,Schedule 2
PJM,monitoring_analytics_som,Combustion Turbine,,gross_acr,68.40,usd_per_kw_yr,"2025 State of the Market Report for PJM, Volume 2",som-2025.pdf,Section 9
PJM,monitoring_analytics_som,Combustion Turbine,,gross_acr,,usd_per_kw_yr,"2026 State of the Market Report for PJM, Volume 2 (not yet published)",,
"""


def _write_pjm_fixture(raw_root: Path) -> None:
    d = acr.raw_dir_for("PJM", raw_root)
    d.mkdir(parents=True, exist_ok=True)
    (d / "pjm.csv").write_text(_PJM_CSV)


class TestCurateCapacityMarketAvoidableCostRate(unittest.TestCase):
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
        written = curate_acr.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1, "expected one PJM partition")
        path = written[0]
        self.assertTrue(path.exists())
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "capacity-market-avoidable-cost-rate")
        return pd.read_parquet(path)

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(set(df["iso"]), {"PJM"})
        self.assertEqual(list(df.columns), list(acr.CANONICAL_COLUMNS))

    def test_row_count_and_valueless_row_dropped(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(len(df), 3)

    def test_both_source_types_present(self) -> None:
        df = self._curate_pjm()
        self.assertEqual(
            set(df["source_type"]), {"pjm_manual18_default", "monitoring_analytics_som"}
        )

    def test_values_parsed(self) -> None:
        df = self._curate_pjm()
        row = df[
            (df["source_type"] == "pjm_manual18_default")
            & (df["technology_class"] == "Combustion Turbine")
        ].iloc[0]
        self.assertAlmostEqual(row["value"], 7.87)
        self.assertEqual(row["unit"], "usd_per_kw_month")

    def test_empty_iso_is_skipped(self) -> None:
        written = curate_acr.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(written, [])

    def test_unregistered_iso_raises(self) -> None:
        with self.assertRaises(ValueError):
            curate_acr.curate(raw_root=self.raw_root, isos=["NOTANISO"])

    def test_vocab_guard_rejects_bad_source_type(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "source_type": ["not_a_source"],
                "technology_class": ["Combined Cycle"],
                "capacity_bin": [pd.NA],
                "cost_component": ["gross_acr"],
                "value": [10.0],
                "unit": ["usd_per_kw_month"],
                "vintage": ["x"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            acr.validate_tidy(acr.finalize(bad))

    def test_vocab_guard_rejects_bad_cost_component(self) -> None:
        bad = pd.DataFrame(
            {
                "iso": ["PJM"],
                "source_type": ["pjm_manual18_default"],
                "technology_class": ["Combined Cycle"],
                "capacity_bin": [pd.NA],
                "cost_component": ["not_a_component"],
                "value": [10.0],
                "unit": ["usd_per_kw_month"],
                "vintage": ["x"],
                "source_doc": ["x"],
                "source_page": ["y"],
            }
        )
        with self.assertRaises(ValueError):
            acr.validate_tidy(acr.finalize(bad))

    def test_pjm_registered(self) -> None:
        registry = acr.load_registry()
        self.assertIn("PJM", registry)


if __name__ == "__main__":
    unittest.main()
