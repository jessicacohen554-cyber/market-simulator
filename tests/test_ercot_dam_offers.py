"""Reshape correctness for the ERCOT DAM offer parser.

Covers :func:`scripts.data.parse_ercot_dam_offers._parse_one_file`: the wide→tidy
melt of the 10-point energy curve, NaN-padding removal, the resource-type→model
class map, the thermal-class filter, the ``committed`` status tag, and graceful
handling of a missing optional column (ECRS, absent in pre-mid-2023 files).
"""

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.data import parse_ercot_dam_offers as parser  # noqa: E402


def _wide_row(**over):
    """One wide disclosure row with all-NaN curve, overridden by ``over``."""
    row = {
        "Delivery Date": "08/15/2023",
        "Hour Ending": 16,
        "QSE": "QABC",
        "DME": "D",
        "Resource Name": "FAKE_CT_1",
        "Resource Type": "SCGT90",
        "Resource Status": "ON",
        "Settlement Point Name": "FAKE",
        "HSL": 185.0,
        "LSL": 95.0,
        "Awarded Quantity": 0.0,
        "Min Gen Cost": 34.58,
        "Start Up Hot": 5902.0,
        "Start Up Inter": 5902.0,
        "Start Up Cold": 5902.0,
        "Energy Settlement Point Price": 20.0,
        "RegUp Awarded": np.nan,
        "RegDown Awarded": np.nan,
        "RRSPFR Awarded": np.nan,
        "RRSFFR Awarded": np.nan,
        "RRSUFR Awarded": np.nan,
        "ECRSSD Awarded": np.nan,
        "NonSpin Awarded": np.nan,
    }
    for k in range(1, 11):
        row[f"QSE submitted Curve-MW{k}"] = np.nan
        row[f"QSE submitted Curve-Price{k}"] = np.nan
    row.update(over)
    return row


class TestParseOneFile(unittest.TestCase):
    def _write(self, rows, drop_cols=()):
        df = pd.DataFrame(rows)
        for c in drop_cols:
            df = df.drop(columns=c)
        path = Path(self._tmp.name) / "wide.parquet"
        df.to_parquet(path, index=False)
        return str(path)

    def setUp(self):
        import tempfile

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_three_point_curve_melts_and_drops_padding(self):
        row = _wide_row(
            **{
                "QSE submitted Curve-MW1": 95.0,
                "QSE submitted Curve-Price1": 23.0,
                "QSE submitted Curve-MW2": 140.0,
                "QSE submitted Curve-Price2": 25.0,
                "QSE submitted Curve-MW3": 185.0,
                "QSE submitted Curve-Price3": 28.0,
            }
        )
        path = self._write([row])
        tidy = parser._parse_one_file(path, parser.THERMAL_CLASSES)
        # 3 real points, 7 NaN-padded points dropped.
        self.assertEqual(len(tidy), 3)
        self.assertEqual(sorted(tidy["point"]), [1, 2, 3])
        self.assertEqual(list(tidy["curve_mw"]), [95.0, 140.0, 185.0])
        self.assertEqual(list(tidy["curve_price"]), [23.0, 25.0, 28.0])
        # Three-part fields carried onto every point row.
        self.assertTrue((tidy["min_gen_cost"] == 34.58).all())
        self.assertTrue((tidy["startup_cold"] == 5902.0).all())
        self.assertEqual(tidy["model_class"].iloc[0], "CT_PEAKER")
        self.assertTrue(tidy["committed"].all())  # status ON

    def test_class_map_and_thermal_filter(self):
        ct = _wide_row(
            **{
                "Resource Name": "C1",
                "Resource Type": "SCGT90",
                "QSE submitted Curve-MW1": 1.0,
                "QSE submitted Curve-Price1": 5.0,
            }
        )
        cc = _wide_row(
            **{
                "Resource Name": "G1",
                "Resource Type": "CCGT90",
                "QSE submitted Curve-MW1": 1.0,
                "QSE submitted Curve-Price1": 5.0,
            }
        )
        wind = _wide_row(
            **{
                "Resource Name": "W1",
                "Resource Type": "WIND",
                "QSE submitted Curve-MW1": 1.0,
                "QSE submitted Curve-Price1": 5.0,
            }
        )
        path = self._write([ct, cc, wind])
        tidy = parser._parse_one_file(path, parser.THERMAL_CLASSES)
        # WIND dropped (non-thermal); CT/CC kept and mapped.
        classes = dict(zip(tidy["resource_name"], tidy["model_class"]))
        self.assertEqual(classes, {"C1": "CT_PEAKER", "G1": "CC"})

    def test_committed_flag_from_status(self):
        on = _wide_row(
            **{
                "Resource Name": "A",
                "Resource Status": "ON",
                "QSE submitted Curve-MW1": 1.0,
                "QSE submitted Curve-Price1": 5.0,
            }
        )
        off = _wide_row(
            **{
                "Resource Name": "B",
                "Resource Status": "OFF",
                "QSE submitted Curve-MW1": 1.0,
                "QSE submitted Curve-Price1": 5.0,
            }
        )
        path = self._write([on, off])
        tidy = parser._parse_one_file(path, parser.THERMAL_CLASSES)
        flag = dict(zip(tidy["resource_name"], tidy["committed"]))
        self.assertTrue(flag["A"])
        self.assertFalse(flag["B"])

    def test_missing_optional_column_is_tolerated(self):
        # Pre-mid-2023 files have no ECRS column; the parser must fill NaN.
        row = _wide_row(
            **{"QSE submitted Curve-MW1": 95.0, "QSE submitted Curve-Price1": 23.0}
        )
        path = self._write([row], drop_cols=["ECRSSD Awarded"])
        tidy = parser._parse_one_file(path, parser.THERMAL_CLASSES)
        self.assertEqual(len(tidy), 1)
        self.assertIn("ecrs_awarded", tidy.columns)
        self.assertTrue(tidy["ecrs_awarded"].isna().all())


if __name__ == "__main__":
    unittest.main()
