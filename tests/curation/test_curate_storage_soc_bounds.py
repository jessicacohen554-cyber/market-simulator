"""Tests for the storage-soc-bounds intake on tiny synthetic fixtures.

Two seams: ``extract_caiso_rtm_eoh_soc.extract_day`` on a hand-built
PUB_RTM_GRP-shaped zip (EOH rows collapse to one per resource-hour, the S1
storage universe, a non-unique bound is refused), and ``curate`` on a tiny
committed-extract fixture (schema-valid, Pacific clock incl. the DST fall-back
repeat hour). CLEAN_DIR is redirected to a tmp dir.
"""

import datetime as dt
import zipfile

import pandas as pd

from scripts.data import curate_storage_soc_bounds as curate_ssb
from scripts.data import extract_caiso_rtm_eoh_soc as ext
from scripts.lib import storage_soc_bounds as ssb
from scripts.lib.clean_io import read_clean, validate_clean
from tests.helpers.base import CleanDirTestCase

_HDR = [
    "RESOURCE_TYPE",
    "SCHEDULINGCOORDINATOR_SEQ",
    "RESOURCEBID_SEQ",
    "MARKETPRODUCTTYPE",
    "TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTART_GMT",
    "SCH_BID_TIMEINTERVALSTOP_GMT",
    "SCH_BID_XAXISDATA",
    "MINEOHSTATEOFCHARGE",
    "MAXEOHSTATEOFCHARGE",
]


def _row(rid, product, x, lo=None, hi=None, h=13, rtype="GENERATOR"):
    s = f"2024-07-10T{h:02d}:00:00-00:00"
    e = f"2024-07-10T{h + 1:02d}:00:00-00:00"
    return [rtype, "9", str(rid), product, None, s, e, x, lo, hi]


def _write_zip(path, rows):
    df = pd.DataFrame(rows, columns=_HDR)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("20240710_20240710_PUB_BID_RTM_v3.csv", df.to_csv(index=False))


class TestExtractDay(CleanDirTestCase):
    def test_trivial_storage_resource(self) -> None:
        rows = [
            # storage resource 1: EN curve -10..+10, bound on 3 product rows
            _row(1, "EN", "-10", "2", "38"),
            _row(1, "EN", "10", "2", "38"),
            _row(1, "RU", None, "2", "38"),
            # generator 2: injection only, no bound -> outside the universe
            _row(2, "EN", "50"),
            # storage resource 3: no bound -> in the universe, submits_eoh False
            _row(3, "EN", "-5"),
            _row(3, "EN", "5"),
            # an intertie row with a bound is ignored (GENERATOR only)
            _row(4, "EN", "5", "1", "2", rtype="ITIE"),
        ]
        z = self.tmp_path / "d.zip"
        _write_zip(z, rows)
        eoh, uni, man = ext.extract_day(z, dt.date(2024, 7, 10))
        self.assertEqual(len(eoh), 1)
        self.assertEqual(eoh.loc[0, "min_eoh_soc_mwh"], 2.0)
        self.assertEqual(eoh.loc[0, "max_eoh_soc_mwh"], 38.0)
        self.assertEqual(sorted(uni["resourcebid_seq"]), [1, 3])
        r1 = uni.set_index("resourcebid_seq").loc[1]
        self.assertTrue(r1["submits_eoh"] and r1["is_storage_s1"])
        self.assertEqual((r1["en_min_mw"], r1["en_max_mw"]), (-10.0, 10.0))
        self.assertEqual(man["eoh_resources"], 1)

    def test_non_unique_bound_refused(self) -> None:
        z = self.tmp_path / "d.zip"
        _write_zip(z, [_row(1, "EN", "-1", "2", "38"), _row(1, "EN", "1", "3", "38")])
        with self.assertRaises(ValueError):
            ext.extract_day(z, dt.date(2024, 7, 10))


class TestCurateStorageSocBounds(CleanDirTestCase):
    def _fixture(self) -> None:
        d = self.tmp_path / "caiso-rtm-eoh-soc"
        d.mkdir()
        td = pd.Timestamp("2024-11-03")
        # DST fall-back: 08Z and 09Z are both 01:00 local, distinct UTC keys.
        eoh = pd.DataFrame(
            {
                "trade_date": [td, td],
                "interval_start_utc": pd.to_datetime(
                    ["2024-11-03T08:00Z", "2024-11-03T09:00Z"], utc=True
                ),
                "resourcebid_seq": [7, 7],
                "sc_seq": [9, 9],
                "min_eoh_soc_mwh": [1.0, 2.0],
                "max_eoh_soc_mwh": [40.0, 40.0],
            }
        )
        uni = pd.DataFrame(
            {
                "trade_date": [td],
                "resourcebid_seq": [7],
                "sc_seq": [9],
                "en_min_mw": [-10.0],
                "en_max_mw": [10.0],
                "n_en_hours": [25],
                "is_storage_s1": [True],
                "submits_eoh": [True],
            }
        )
        eoh.to_parquet(d / "caiso_rtm_eoh_soc_2024.parquet")
        uni.to_parquet(d / "caiso_rtm_storage_universe_2024.parquet")

    def test_curate_writes_valid_partition(self) -> None:
        self._fixture()
        paths = curate_ssb.curate(raw_root=self.tmp_path, isos=["CAISO"])
        self.assertEqual(len(paths), 1)
        schema = validate_clean(paths[0])
        self.assertEqual(schema.datatype, ssb.DATATYPE)
        df = read_clean(ssb.DATATYPE, iso="CAISO", year=2024)
        self.assertEqual(len(df), 2)
        local = pd.to_datetime(df["interval_start_local"])
        self.assertTrue((local == pd.Timestamp("2024-11-03 01:00")).all())
        self.assertEqual(set(df["resource_id"]), {"7"})
        self.assertTrue(df["is_storage_s1"].all())

    def test_missing_raw_is_skipped(self) -> None:
        self.assertEqual(curate_ssb.curate(raw_root=self.tmp_path, isos=["CAISO"]), [])
