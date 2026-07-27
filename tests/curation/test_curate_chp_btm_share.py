"""Tests for the chp-btm-share intake on tiny synthetic fixtures.

Writes minimal ``plant_emission_rates_v2`` (CAMPD) and
``eia923_monthly_generation`` (EIA-923) fixture parquets into a tmp raw tree,
runs ``curate``, and asserts the written Parquet is schema-valid and the
measured share reconciles by hand. CLEAN_DIR is redirected to a tmp dir so the
suite never touches the real tree. Trivial case first (one covered plant, one
year), then a second plant/year to exercise pooling and an uncovered plant.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_chp_btm_share as curate_mod
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean


def _v2_row(**kw):
    base = {
        "iso": "ERCOT",
        "plant_id": 1001,
        "unit_id": "U1",
        "year": 2023,
        "primary_fuel": "Natural Gas",
        "unit_type": "Combined cycle",
        "gross_mwh": 0.0,
        "net_mwh": 0.0,
        "parasitic_factor": 1.0,
        "heat_mmbtu": 0.0,
        "co2_kg": 0.0,
        "co2_kg_per_mwh_net": 0.0,
        "co2_source": "measured",
        "starts": 0,
        "op_hours": 0,
        "steam_load_klbh_sum": 0.0,
    }
    base.update(kw)
    return base


def _gen_row(**kw):
    base = {
        "plant_id": 1001,
        "plant_name": "Test Plant",
        "prime_mover": "CA",
        "fuel_type": "NG",
        "chp": "Y",
        "netgen_annual_mwh": 0.0,
        "ba_code": "ERCO",
        "year": 2023,
    }
    for m in (
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ):
        base[f"netgen_{m}_mwh"] = 0.0
    base.update(kw)
    return base


def _write_fixture(raw_root: Path, v2_rows: list[dict], gen_rows: list[dict]) -> None:
    v2_path = raw_root / curate_mod._V2_RELPATH
    gen_path = raw_root / curate_mod._GEN_RELPATH
    v2_path.parent.mkdir(parents=True, exist_ok=True)
    gen_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(v2_rows).to_parquet(v2_path, index=False)
    pd.DataFrame(gen_rows).to_parquet(gen_path, index=False)


class TestCurateChpBtmShare(unittest.TestCase):
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

    def test_trivial_one_plant_one_year(self) -> None:
        # CAMPD reports 700 MWh grid-net for the plant's one steam-reporting
        # CC unit; EIA-923 reports 1000 MWh net for the same plant/class/year
        # -> btm_share == (1000-700)/1000 == 0.3.
        v2 = [_v2_row(net_mwh=700.0, steam_load_klbh_sum=50.0)]
        gen = [_gen_row(netgen_annual_mwh=1000.0)]
        _write_fixture(self.raw_root, v2, gen)

        written = curate_mod.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 1)
        path = written[0]
        schema = validate_clean(path)
        self.assertEqual(schema.datatype, "chp-btm-share")

        df = pd.read_parquet(path)
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        self.assertEqual(row["iso"], "ERCOT")
        self.assertEqual(int(row["plant_id"]), 1001)
        self.assertEqual(row["plant_group"], "CC_CHP")
        self.assertAlmostEqual(row["eia923_net_mwh"], 1000.0)
        self.assertAlmostEqual(row["campd_net_mwh"], 700.0)
        self.assertAlmostEqual(row["btm_share"], 0.3, places=6)
        self.assertEqual(int(row["n_years"]), 1)
        self.assertEqual(int(row["first_year"]), 2023)
        self.assertEqual(int(row["last_year"]), 2023)

    def test_pools_across_years_and_clips_share(self) -> None:
        # Two years for the same plant/class: pooled ratio-of-sums, not a
        # per-year average, and the share clips to [0, 1] even if a single
        # year's CAMPD total exceeds that year's EIA-923 total.
        v2 = [
            _v2_row(year=2023, net_mwh=700.0, steam_load_klbh_sum=50.0),
            _v2_row(year=2024, net_mwh=1200.0, steam_load_klbh_sum=55.0),
        ]
        gen = [
            _gen_row(year=2023, netgen_annual_mwh=1000.0),
            _gen_row(year=2024, netgen_annual_mwh=1000.0),
        ]
        _write_fixture(self.raw_root, v2, gen)

        written = curate_mod.curate(raw_root=self.raw_root)
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), 1)
        row = df.iloc[0]
        # sums: eia923 = 2000, campd = 1900 -> ratio 0.05, clipped stays 0.05
        self.assertAlmostEqual(row["eia923_net_mwh"], 2000.0)
        self.assertAlmostEqual(row["campd_net_mwh"], 1900.0)
        self.assertAlmostEqual(row["btm_share"], 0.05, places=6)
        self.assertEqual(int(row["n_years"]), 2)
        self.assertEqual(int(row["first_year"]), 2023)
        self.assertEqual(int(row["last_year"]), 2024)

    def test_non_steam_reporting_unit_excluded(self) -> None:
        # A CEMS unit with no steam load is not part of the CHP signature, so
        # it contributes nothing to campd_net_mwh -- the plant has no
        # covered row at all (no steam-reporting unit for its class).
        v2 = [_v2_row(net_mwh=700.0, steam_load_klbh_sum=0.0)]
        gen = [_gen_row(netgen_annual_mwh=1000.0)]
        _write_fixture(self.raw_root, v2, gen)

        written = curate_mod.curate(raw_root=self.raw_root)
        self.assertEqual(written, [])

    def test_quarantined_year_dropped(self) -> None:
        v2 = [_v2_row(year=2022, net_mwh=700.0, steam_load_klbh_sum=50.0)]
        gen = [_gen_row(year=2022, netgen_annual_mwh=1000.0)]
        _write_fixture(self.raw_root, v2, gen)

        written = curate_mod.curate(raw_root=self.raw_root)
        self.assertEqual(written, [])

    def test_skips_when_no_raw_sources(self) -> None:
        self.assertEqual(curate_mod.curate(raw_root=self.raw_root), [])

    def test_isos_filter(self) -> None:
        v2 = [
            _v2_row(
                iso="ERCOT", plant_id=1001, net_mwh=700.0, steam_load_klbh_sum=50.0
            ),
            _v2_row(
                iso="CAISO", plant_id=2002, net_mwh=300.0, steam_load_klbh_sum=20.0
            ),
        ]
        gen = [
            _gen_row(plant_id=1001, netgen_annual_mwh=1000.0),
            _gen_row(plant_id=2002, netgen_annual_mwh=500.0),
        ]
        _write_fixture(self.raw_root, v2, gen)

        written = curate_mod.curate(raw_root=self.raw_root, isos=["ERCOT"])
        self.assertEqual(len(written), 1)
        df = pd.read_parquet(written[0])
        self.assertEqual(set(df["iso"]), {"ERCOT"})


if __name__ == "__main__":
    unittest.main()
