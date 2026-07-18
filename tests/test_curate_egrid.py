"""Round-trip tests for eGRID curation (scripts/data/curate_egrid.py).

Builds a tiny synthetic eGRID-shaped workbook (the real workbook's first row
of long descriptive headers, then the short-code header row, then data rows)
and asserts the written Parquet is schema-valid and the column rename /
filtering matches what ``market_sim.data.zone_assignment`` and
``market_sim.data.egrid`` each expect from the union table.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_egrid
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_SHORT_COLS = [
    "ORISPL",
    "LAT",
    "LON",
    "FIPSST",
    "FIPSCNTY",
    "BACODE",
    "PLFUELCT",
    "PLNGENAN",
    "PLCO2AN",
]


def _write_egrid_xlsx(path: Path, sheet: str, rows: list[dict]) -> None:
    """Write a synthetic eGRID-shaped workbook: junk header row + short-code data."""
    data = pd.DataFrame(rows, columns=_SHORT_COLS)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame([["LONG DESCRIPTIVE HEADER"] * len(_SHORT_COLS)]).to_excel(
            writer, sheet_name=sheet, header=False, index=False, startrow=0
        )
        data.to_excel(writer, sheet_name=sheet, index=False, startrow=1)


class TestCurateEgrid(unittest.TestCase):
    def setUp(self):
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.fleet_dir = root / "fleet-egrid"
        self.fleet_dir.mkdir(parents=True)

        _write_egrid_xlsx(
            self.fleet_dir / curate_egrid.EGRID_FILES[2023],
            "PLNT23",
            [
                {
                    "ORISPL": 999,
                    "LAT": 30.1,
                    "LON": -97.5,
                    "FIPSST": 48,
                    "FIPSCNTY": 453,
                    "BACODE": "ERCO",
                    "PLFUELCT": "COAL",
                    "PLNGENAN": 1000.0,
                    "PLCO2AN": 900.0,
                },
                {
                    "ORISPL": 888,
                    "LAT": 32.0,
                    "LON": -96.0,
                    "FIPSST": 48,
                    "FIPSCNTY": 113,
                    "BACODE": "ERCO",
                    "PLFUELCT": "WIND",
                    "PLNGENAN": 500.0,
                    "PLCO2AN": None,  # non-fossil: no CO2 mass reported
                },
                {
                    "ORISPL": None,  # no ORIS code -> dropped (no usable key)
                    "LAT": 33.0,
                    "LON": -95.0,
                    "FIPSST": 48,
                    "FIPSCNTY": 1,
                    "BACODE": "ERCO",
                    "PLFUELCT": "GAS",
                    "PLNGENAN": 10.0,
                    "PLCO2AN": 5.0,
                },
            ],
        )

        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self):
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_schema_valid_year_partition(self):
        written = curate_egrid.curate(vintages=[2023], fleet_dir=self.fleet_dir)
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0].name, "egrid_2023.parquet")
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "egrid")

    def test_columns_renamed_and_unfiltered(self):
        written = curate_egrid.curate(vintages=[2023], fleet_dir=self.fleet_dir)
        df = pd.read_parquet(written[0])

        # Short eGRID codes renamed to snake_case schema columns.
        self.assertEqual(
            set(df.columns),
            {
                "plant_id",
                "lat",
                "lon",
                "fips_state",
                "fips_county",
                "ba_code",
                "fuel_cat",
                "net_mwh",
                "co2_tons",
            },
        )

        # The row with no ORIS code is dropped; the non-fossil WIND plant is
        # KEPT (this table is unfiltered — egrid.py applies its own fossil
        # filter downstream).
        self.assertEqual(set(df["plant_id"]), {999, 888})
        wind = df.loc[df["plant_id"] == 888].iloc[0]
        self.assertEqual(wind["fuel_cat"], "WIND")
        self.assertTrue(pd.isna(wind["co2_tons"]))

        coal = df.loc[df["plant_id"] == 999].iloc[0]
        self.assertEqual(coal["ba_code"], "ERCO")
        self.assertEqual(coal["fips_state"], 48)
        self.assertAlmostEqual(coal["net_mwh"], 1000.0)
        self.assertAlmostEqual(coal["co2_tons"], 900.0)

    def test_default_vintages_only_present_workbooks(self):
        # Only the 2023 workbook exists on disk; 2024 must be skipped, not error.
        written = curate_egrid.curate(fleet_dir=self.fleet_dir)
        self.assertEqual(len(written), 1)
        self.assertEqual(written[0].name, "egrid_2023.parquet")

    def test_idempotent_rerun(self):
        first = curate_egrid.curate(vintages=[2023], fleet_dir=self.fleet_dir)
        second = curate_egrid.curate(vintages=[2023], fleet_dir=self.fleet_dir)
        pd.testing.assert_frame_equal(
            pd.read_parquet(first[0]).sort_values("plant_id").reset_index(drop=True),
            pd.read_parquet(second[0]).sort_values("plant_id").reset_index(drop=True),
        )


if __name__ == "__main__":
    unittest.main()
