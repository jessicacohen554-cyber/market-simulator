"""Round-trip tests for unit-outage-events curation
(scripts/data/curate_unit_outage_events.py).

Builds tiny synthetic ``campd-unit-outages*.csv`` fixtures for two ISOs
(ERCOT's canonical filename and PJM's per-ISO filename), runs ``curate``, and
asserts the written Parquet is schema-valid, ``iso`` is stamped correctly, and
the event-grain rows (not hourly-expanded) match the source CSV.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_unit_outage_events as cuoe
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _write_unit_outages(path: Path, facility_id: int) -> None:
    pd.DataFrame(
        [
            {
                "facility_name": "Test Plant",
                "facility_id": facility_id,
                "unit_id": "U1",
                "unit_capacity_mw": 40.0,
                "plant_capacity_mw": 100.0,
                "unit_pct_of_plant": 40.0,
                "plant_group": "COAL",
                "capacity_source": "eia_exact",
                "outage_start": "2023-06-01",
                "outage_end": "2023-06-05",
                "duration_days": 5.0,
                "peer_units_online": 1,
                "total_units_at_plant": 2,
            },
            {
                "facility_name": "Test Plant",
                "facility_id": facility_id,
                "unit_id": "U2",
                "unit_capacity_mw": None,
                "plant_capacity_mw": 100.0,
                "unit_pct_of_plant": None,
                "plant_group": "CC_REGULAR",
                "capacity_source": "plant_share",
                "outage_start": "2023-07-10",
                "outage_end": "2023-07-11",
                "duration_days": 2.0,
                "peer_units_online": 1,
                "total_units_at_plant": 2,
            },
        ]
    ).to_csv(path, index=False)


class TestCurateUnitOutageEvents(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_dir = root / "raw"
        self.raw_dir.mkdir(parents=True)

        _write_unit_outages(self.raw_dir / "campd-unit-outages.csv", 999)
        _write_unit_outages(self.raw_dir / "campd-unit-outages-PJM.csv", 777)

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid_per_iso(self):
        written = cuoe.curate(raw_dir=self.raw_dir)
        self.assertEqual(set(written), {"ERCOT", "PJM"})
        for iso, path in written.items():
            self.assertTrue(path.exists())
            schema = validate_clean(path)
            self.assertEqual(schema.datatype, "unit-outage-events")
            self.assertIn(iso, path.parts)

    def test_event_grain_preserved_and_iso_stamped(self):
        written = cuoe.curate(raw_dir=self.raw_dir)
        df = pd.read_parquet(written["ERCOT"])

        # 2 rows in -> 2 rows out (event grain, not hourly-expanded).
        self.assertEqual(len(df), 2)
        self.assertTrue((df["iso"] == "ERCOT").all())
        self.assertTrue((df["plant_id"] == 999).all())

        u1 = df[df["unit_id"] == "U1"].iloc[0]
        self.assertEqual(u1["unit_capacity_mw"], 40.0)
        self.assertEqual(u1["duration_days"], 5.0)
        self.assertEqual(pd.Timestamp(u1["outage_start"]), pd.Timestamp("2023-06-01"))
        self.assertEqual(pd.Timestamp(u1["outage_end"]), pd.Timestamp("2023-06-05"))

        u2 = df[df["unit_id"] == "U2"].iloc[0]
        self.assertTrue(pd.isna(u2["unit_capacity_mw"]))

    def test_only_requested_iso_csvs_read(self):
        written = cuoe.curate(raw_dir=self.raw_dir, isos=["ERCOT"])
        self.assertEqual(set(written), {"ERCOT"})

    def test_idempotent_rerun(self):
        first = cuoe.curate(raw_dir=self.raw_dir)
        second = cuoe.curate(raw_dir=self.raw_dir)
        for iso in first:
            pd.testing.assert_frame_equal(
                pd.read_parquet(first[iso]), pd.read_parquet(second[iso])
            )


if __name__ == "__main__":
    unittest.main()
