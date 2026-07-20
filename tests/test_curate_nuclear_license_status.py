"""Tests for the nuclear-license-status intake on a tiny synthetic fixture.

Writes a minimal registry CSV plus a fixture EIA-860 spine parquet into a tmp raw
tree, runs ``curate``, and asserts the written Parquet is schema-valid and the
tidy reconciliation (dtypes, controlled vocabularies, SLR/stage consistency) is
correct, then round-trips it back through the read-only loader stub. NOT a
full-data run: CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_confirmed_retirements.py) so it never touches the real tree.
Also covers the EIA-860 spine cross-check (unknown plant / MW off > 5 % fail),
the four closed vocabularies, and the skip-empty path.
"""

import unittest

import pandas as pd

from scripts.data import curate_nuclear_license_status as curate_nls
from scripts.lib import nuclear_license_status as nls
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import CleanDirTestCase

# Three units for MISO: a renewed_60, an SLR-granted (must carry slr_granted_80),
# and a restart-pathway unit with an announced uprate. All identities match the
# fixture spine below.
_MISO_CSV = """iso,plant_name,unit,eia_plant_id,capacity_mw,nrc_docket,license_issued_date,current_license_expiry,license_stage,license_instrument,slr_status,slr_docket,slr_instrument,slr_instrument_date,announced_uprate_mw,uprate_status,uprate_instrument,restart_status,restart_target_year,restart_instrument,retirement_announcement,confirmed_retirement_ref,source_url,source_doc,accessed,notes
MISO,Alpha,1,111,900.0,50-001,1980-01-01,2040-01-01,renewed_60,NRC renewed license,none,,,,,,,,,,,,https://nrc.example/alpha1,info-finder,2026-07-20,seed
MISO,Beta,1,222,700.0,50-002,1975-02-02,2055-02-02,slr_granted_80,NRC SLR,granted,,NRC SLR issued 2024-12-30,2024-12-30,,none,,,,,,,https://nrc.example/beta1,info-finder,2026-07-20,SLR granted
MISO,Gamma,1,333,800.0,50-003,1985-03-03,2035-03-03,renewed_60,NRC renewed license,announced_intent,,Holtec SLR intent,2024-04-18,,announced_intent,NRC Expected Uprate list,in_progress,2026,NRC reauthorization 2025,,,https://nrc.example/gamma1,info-finder,2026-07-20,restart
"""

# Spine: the three units exist with the stated nameplates.
_SPINE = pd.DataFrame(
    {
        "plant_id": [111, 222, 333],
        "generator_id": ["1", "1", "1"],
        "nameplate_capacity_mw": [900.0, 700.0, 800.0],
    }
)


class TestCurateNuclearLicenseStatus(CleanDirTestCase):
    def setUp(self) -> None:
        super().setUp()  # redirects paths.CLEAN_DIR to self.tmp_path / "clean"
        self.raw_root = self.tmp_path / "raw"
        (self.raw_root / nls.DATATYPE).mkdir(parents=True)
        self.spine_path = self.tmp_path / "spine.parquet"
        _SPINE.to_parquet(self.spine_path, index=False)

    def _write(self, text: str, iso: str = "miso") -> None:
        (self.raw_root / nls.DATATYPE / f"{iso}.csv").write_text(text)

    def _curate(self) -> pd.DataFrame:
        self._write(_MISO_CSV)
        written = curate_nls.curate(
            raw_root=self.raw_root, isos=["MISO"], spine_path=self.spine_path
        )
        self.assertEqual(len(written), 1)
        schema = validate_clean(written[0])
        self.assertEqual(schema.datatype, "nuclear-license-status")
        return pd.read_parquet(written[0])

    def test_schema_valid_and_columns(self) -> None:
        df = self._curate()
        self.assertEqual(list(df.columns), list(nls.CANONICAL_COLUMNS))
        self.assertEqual(set(df["iso"]), {"MISO"})
        self.assertEqual(len(df), 3)

    def test_vocabularies_and_slr_stage_consistency(self) -> None:
        df = self._curate()
        self.assertLessEqual(set(df["license_stage"]), nls.LICENSE_STAGE_VOCAB)
        self.assertLessEqual(
            set(df["slr_status"].dropna()) - {""}, nls.SLR_STATUS_VOCAB
        )
        granted = df[df["slr_status"] == "granted"]
        self.assertTrue((granted["license_stage"] == "slr_granted_80").all())

    def test_restart_and_uprate_fields(self) -> None:
        df = self._curate()
        gamma = df[df["eia_plant_id"] == 333].iloc[0]
        self.assertEqual(gamma["restart_status"], "in_progress")
        self.assertEqual(int(gamma["restart_target_year"]), 2026)
        self.assertEqual(gamma["uprate_status"], "announced_intent")

    def test_bad_license_stage_fails(self) -> None:
        bad = _MISO_CSV.replace(",renewed_60,NRC renewed license", ",vaporware,x")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_nls.curate(
                raw_root=self.raw_root, isos=["MISO"], spine_path=self.spine_path
            )
        self.assertIn("license_stage", str(ctx.exception))

    def test_granted_without_stage_fails(self) -> None:
        # slr_status=granted but license_stage left renewed_60 -> inconsistency.
        bad = _MISO_CSV.replace("2055-02-02,slr_granted_80", "2055-02-02,renewed_60")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_nls.curate(
                raw_root=self.raw_root, isos=["MISO"], spine_path=self.spine_path
            )
        self.assertIn("slr_status=granted", str(ctx.exception))

    def test_spine_unknown_plant_fails(self) -> None:
        bad = _MISO_CSV.replace("MISO,Alpha,1,111", "MISO,Alpha,1,999")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_nls.curate(
                raw_root=self.raw_root, isos=["MISO"], spine_path=self.spine_path
            )
        self.assertIn("not in EIA-860 spine", str(ctx.exception))

    def test_spine_mw_mismatch_fails(self) -> None:
        # 900 -> 1200 is 33 % off the 900 MW nameplate (> 5 %).
        bad = _MISO_CSV.replace("Alpha,1,111,900.0", "Alpha,1,111,1200.0")
        self._write(bad)
        with self.assertRaises(ValueError) as ctx:
            curate_nls.curate(
                raw_root=self.raw_root, isos=["MISO"], spine_path=self.spine_path
            )
        self.assertIn("off", str(ctx.exception))

    def test_missing_csv_skips(self) -> None:
        written = curate_nls.curate(
            raw_root=self.raw_root, isos=["PJM"], spine_path=self.spine_path
        )
        self.assertEqual(written, [])

    def test_loader_round_trip(self) -> None:
        self._curate()
        from market_sim.data.nuclear_license import load_nuclear_license_status

        units = load_nuclear_license_status("MISO")
        self.assertEqual(len(units), 3)
        by_id = {u.plant_id: u for u in units}
        self.assertEqual(by_id[222].license_stage, "slr_granted_80")
        self.assertEqual(by_id[222].slr_status, "granted")
        self.assertEqual(by_id[333].restart_status, "in_progress")
        self.assertEqual(by_id[333].restart_target_year, 2026)
        # Dates round-trip as datetime.date.
        self.assertEqual(str(by_id[111].current_license_expiry), "2040-01-01")

    def test_loader_absent_partition_returns_empty(self) -> None:
        from market_sim.data.nuclear_license import load_nuclear_license_status

        # Curated tree exists (setUp redirected CLEAN_DIR) but no NYISO partition.
        self.assertEqual(load_nuclear_license_status("NYISO"), [])


if __name__ == "__main__":
    unittest.main()
