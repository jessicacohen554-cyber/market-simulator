"""Tests for scripts/data/curate_outages.py on a tiny synthetic raw fixture.

Builds a minimal set of raw outage-window CSVs (one CAMPD unit window, one ERCOT
curated unit window) plus a two-plant nameplate registry, runs ``curate``, and
asserts the written Parquet is schema-valid and
the reconciliation (hourly expansion, outage_mw / available_mw, UTC offset,
overlap de-duplication) is correct. NOT a full-data run: CLEAN_DIR is redirected
to a tmp dir (as in tests/test_clean_io.py) so it never touches the real tree.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_outages
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _write_registry(ref_dir: Path) -> None:
    # plant 999 -> 100 MW nameplate, plant 888 -> 50 MW nameplate.
    pd.DataFrame(
        {"plantid": [999, 888], "nameplate_capacity_mw": [100.0, 50.0]}
    ).to_csv(ref_dir / "master-plant-registry.csv", index=False)


def _write_campd_unit_outages(raw_dir: Path) -> None:
    # One 1-day (24h) window: plant 999, unit U1, 40 MW offline.
    pd.DataFrame(
        [
            {
                "facility_name": "Test Plant",
                "facility_id": 999,
                "unit_id": "U1",
                "unit_capacity_mw": 40.0,
                "plant_capacity_mw": 100.0,
                "unit_pct_of_plant": 40.0,
                "plant_group": "COAL",
                "capacity_source": "eia_exact",
                "outage_start": "2023-06-01",
                "outage_end": "2023-06-01",
                "duration_days": 1.0,
                "peer_units_online": 1,
                "total_units_at_plant": 2,
            }
        ]
    ).to_csv(raw_dir / "campd-unit-outages.csv", index=False)


def _write_tx_outages(ref_dir: Path) -> None:
    # ERCOT curated list (no capacity_source column). One window overlaps the
    # CAMPD unit window above (plant 999 / U1 / 2023-06-01) but with a SMALLER
    # offline MW, plus a second blank-capacity row that must fall back to an
    # equal share of plant_capacity_mw.
    pd.DataFrame(
        [
            {
                "facility_name": "Test Plant",
                "facility_id": 999,
                "unit_id": "U1",
                "unit_capacity_mw": 25.0,  # smaller -> CAMPD's 40 MW should win
                "plant_capacity_mw": 100.0,
                "unit_pct_of_plant": 25.0,
                "plant_group": "COAL",
                "outage_start": "2023-06-01",
                "outage_end": "2023-06-01",
                "duration_days": 1.0,
                "peer_units_online": 1,
                "total_units_at_plant": 2,
            },
            {
                "facility_name": "Test Plant",
                "facility_id": 999,
                "unit_id": "U2",
                "unit_capacity_mw": None,  # blank -> fallback 100/2 = 50 MW
                "plant_capacity_mw": 100.0,
                "unit_pct_of_plant": None,
                "plant_group": "COAL",
                "outage_start": "2023-07-01",
                "outage_end": "2023-07-01",
                "duration_days": 1.0,
                "peer_units_online": 1,
                "total_units_at_plant": 2,
            },
        ]
    ).to_csv(ref_dir / "tx-jan-aug23-unit-outages.csv", index=False)


class TestCurateOutages(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_dir = root / "raw"
        self.ref_dir = self.raw_dir / "reference"
        self.ref_dir.mkdir(parents=True)

        _write_registry(self.ref_dir)
        _write_campd_unit_outages(self.raw_dir)
        _write_tx_outages(self.ref_dir)

        # Redirect CLEAN_DIR so writes never touch the repo (see test_clean_io).
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate(self) -> pd.DataFrame:
        written = curate_outages.curate(
            raw_dir=self.raw_dir, reference_dir=self.ref_dir
        )
        self.assertTrue(written, "curate wrote nothing")
        for path in written:
            self.assertTrue(path.exists())
            schema = validate_clean(path)  # round-trip schema check
            self.assertEqual(schema.datatype, "outages")
        return pd.concat([pd.read_parquet(p) for p in written], ignore_index=True)

    def test_schema_valid_and_partitioned_by_year(self):
        written = curate_outages.curate(
            raw_dir=self.raw_dir, reference_dir=self.ref_dir
        )
        # All windows are in 2023 local time; +6h keeps them in UTC-year 2023.
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0].name, "outages_2023.parquet")
        validate_clean(written[0])

    def test_unit_window_reconciliation(self):
        df = self._curate()
        u1 = df[(df["plant_id"] == 999) & (df["unit_id"] == "U1")]
        # One 24-hour window.
        self.assertEqual(len(u1), 24)
        # CAMPD's 40 MW beats the ERCOT list's 25 MW on the overlapping hours.
        self.assertTrue((u1["outage_mw"] == 40.0).all())
        # available = nameplate(100) - outage(40).
        self.assertTrue((u1["available_mw"] == 60.0).all())
        self.assertTrue((u1["iso"] == "ERCOT").all())
        self.assertTrue(u1["outage_type"].isna().all())

    def test_utc_offset_and_local(self):
        df = self._curate()
        u1 = df[(df["plant_id"] == 999) & (df["unit_id"] == "U1")].sort_values(
            "interval_start_utc"
        )
        first = u1.iloc[0]
        # Local 2023-06-01 00:00 (Central Standard) -> 2023-06-01 06:00 UTC.
        self.assertEqual(
            pd.Timestamp(first["interval_start_local"]),
            pd.Timestamp("2023-06-01 00:00"),
        )
        self.assertEqual(
            pd.Timestamp(first["interval_start_utc"]),
            pd.Timestamp("2023-06-01 06:00", tz="UTC"),
        )

    def test_blank_capacity_falls_back_to_equal_share(self):
        df = self._curate()
        u2 = df[(df["plant_id"] == 999) & (df["unit_id"] == "U2")]
        self.assertEqual(len(u2), 24)
        # plant_capacity 100 / total_units 2 = 50 MW.
        self.assertTrue((u2["outage_mw"] == 50.0).all())
        self.assertTrue((u2["available_mw"] == 50.0).all())

    def test_keys_unique(self):
        df = self._curate()
        keys = df[["plant_id", "unit_id", "interval_start_utc"]]
        self.assertFalse(keys.duplicated().any())

    def test_idempotent_rerun(self):
        first = self._curate()
        second = self._curate()
        pd.testing.assert_frame_equal(
            first.sort_values(
                ["plant_id", "unit_id", "interval_start_utc"]
            ).reset_index(drop=True),
            second.sort_values(
                ["plant_id", "unit_id", "interval_start_utc"]
            ).reset_index(drop=True),
        )


if __name__ == "__main__":
    unittest.main()
