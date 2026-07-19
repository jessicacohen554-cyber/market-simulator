"""Tests for the transmission-expansion curation pipeline.

Covers the tidy value rules (``scripts.lib.transmission_expansion.validate_tidy``
— closed vocabularies, per-kind column requirements, the intra_zonal zero-delta
rule, mapping-note requirement, supersession citation), the live-topology
resolvability check in ``scripts.data.curate_transmission_expansion``, and a
full curate round-trip against a tmp CLEAN_DIR fixture (written partition
validates against the schema).
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts.data import curate_transmission_expansion as curate_tx
from scripts.lib import clean_io
from scripts.lib import transmission_expansion as tx

_HEADER = (
    "iso,row_id,project_id,project_name,sponsor,status_tier,instrument,"
    "instrument_id,instrument_date,in_service_year,in_service_month,"
    "target_kind,from_zone,to_zone,interface_name,delta_mw,delta_mw_reverse,"
    "capacity_basis,mapping_confidence,mapping_note,superseded,"
    "superseding_instrument,superseding_instrument_date,source_url,"
    "source_doc,accessed,notes"
)

# A valid NEISO fixture: an applicable link row + interface row, a
# recorded-not-applied import_tranche + intra_zonal pair, and a superseded row.
_NEISO_ROWS = [
    "NEISO,necec--hq_north,necec,NECEC,Avangrid,under_construction,"
    '"MA 83D PPAs; DPU 18-64",ma-83d,2018-06-13,2026,,link,HQ_import,North,,'
    "1200.0,,converter_rating,exact,"
    '"1200 MW HVDC lands in North; additive to the RSP-2023 static 900 MW",'
    "false,,,https://example.test/necec,doc,2026-07-19,",
    "NEISO,necec--simultaneous,necec,NECEC,Avangrid,under_construction,"
    '"MA 83D PPAs; DPU 18-64",ma-83d,2018-06-13,2026,,interface,,,'
    "HQ_import_simultaneous,1200.0,1200.0,converter_rating,reconciled,"
    '"new HQ export path raises the simultaneous tie cap; additive to 3850",'
    "false,,,https://example.test/necec,doc,2026-07-19,",
    "NEISO,fake-hvdc--tranche,fake-hvdc,Fake HVDC,X,approved_funded,"
    '"State contract",sc-1,2025-01-01,2029,,import_tranche,,Boston,,'
    "500.0,,converter_rating,reconciled,"
    '"supply-side line; import fleet has no per-year seam (V1 exclusion)",'
    "false,,,https://example.test/fake,doc,2026-07-19,",
    "NEISO,boston-rebuild--intra,boston-rebuild,Boston 345 kV rebuild,X,"
    'approved_funded,"PAC TCA approval",pac-1,2024-05-01,2027,,intra_zonal,'
    "Boston,,,0.0,,thermal_rating,exact,"
    '"entirely inside the Boston zone; no modeled limit changes",'
    "false,,,https://example.test/boston,doc,2026-07-19,",
    "NEISO,dead-line--hq_north,dead-line,Cancelled HVDC,X,approved_funded,"
    '"State contract",sc-2,2020-01-01,2026,,link,HQ_import,North,,'
    '600.0,,converter_rating,exact,"cancelled project kept for audit",'
    'true,"Termination agreement 2023-01-01",2023-01-01,'
    "https://example.test/dead,doc,2026-07-19,",
]


def _write_fixture(raw_root: Path, rows: list[str]) -> None:
    d = raw_root / tx.DATATYPE
    d.mkdir(parents=True, exist_ok=True)
    (d / "neiso.csv").write_text("\n".join([_HEADER, *rows]) + "\n")


def _frame(rows: list[str]) -> pd.DataFrame:
    import io

    raw = pd.read_csv(io.StringIO("\n".join([_HEADER, *rows])), dtype=str)
    raw["iso"] = "NEISO"
    return tx.finalize(raw)


class TestValidateTidy(unittest.TestCase):
    def test_valid_fixture_passes(self) -> None:
        tx.validate_tidy(_frame(_NEISO_ROWS))

    def _assert_fails(self, row: str, fragment: str) -> None:
        with self.assertRaises(ValueError) as ctx:
            tx.validate_tidy(_frame([row]))
        self.assertIn(fragment, str(ctx.exception))

    def test_bad_status_tier(self) -> None:
        bad = _NEISO_ROWS[0].replace("under_construction", "roadmap")
        self._assert_fails(bad, "status_tier")

    def test_intra_zonal_nonzero_delta(self) -> None:
        bad = _NEISO_ROWS[3].replace(",0.0,,thermal_rating", ",50.0,,thermal_rating")
        self._assert_fails(bad, "intra_zonal")

    def test_link_missing_zone(self) -> None:
        bad = _NEISO_ROWS[0].replace(",link,HQ_import,North,", ",link,HQ_import,,")
        self._assert_fails(bad, "link row(s) missing")

    def test_interface_missing_name(self) -> None:
        bad = _NEISO_ROWS[1].replace("HQ_import_simultaneous,", ",")
        self._assert_fails(bad, "interface row(s) missing")

    def test_missing_mapping_note(self) -> None:
        bad = _NEISO_ROWS[0].replace(
            '"1200 MW HVDC lands in North; additive to the RSP-2023 static 900 MW"',
            "",
        )
        self._assert_fails(bad, "mapping_note")

    def test_superseded_without_citation(self) -> None:
        bad = _NEISO_ROWS[4].replace('"Termination agreement 2023-01-01"', "")
        self._assert_fails(bad, "superseding_instrument")

    def test_duplicate_row_id(self) -> None:
        with self.assertRaises(ValueError) as ctx:
            tx.validate_tidy(_frame([_NEISO_ROWS[0], _NEISO_ROWS[0]]))
        self.assertIn("duplicate", str(ctx.exception))


class TestCurateRoundTrip(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        _write_fixture(self.raw_root, _NEISO_ROWS)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_curate_writes_valid_partition(self) -> None:
        written = curate_tx.curate(raw_root=self.raw_root, isos=["NEISO"])
        self.assertEqual(len(written), 1)
        df = pd.read_parquet(written[0])
        self.assertEqual(len(df), len(_NEISO_ROWS))
        self.assertEqual(int(df["superseded"].sum()), 1)

    def test_absent_iso_skipped(self) -> None:
        self.assertEqual(curate_tx.curate(raw_root=self.raw_root, isos=["MISO"]), [])

    def test_unknown_zone_fails_topology_validation(self) -> None:
        bad = _NEISO_ROWS[0].replace(
            ",link,HQ_import,North,", ",link,HQ_import,Nortth,"
        )
        _write_fixture(self.raw_root, [bad])
        with self.assertRaises(ValueError) as ctx:
            curate_tx.curate(raw_root=self.raw_root, isos=["NEISO"])
        self.assertIn("not a NEISO model zone", str(ctx.exception))

    def test_unlinked_zone_pair_fails(self) -> None:
        # North and Connecticut are both real zones but share no TransferLink.
        bad = _NEISO_ROWS[0].replace(
            ",link,HQ_import,North,", ",link,North,Connecticut,"
        )
        _write_fixture(self.raw_root, [bad])
        with self.assertRaises(ValueError) as ctx:
            curate_tx.curate(raw_root=self.raw_root, isos=["NEISO"])
        self.assertIn("no declared TransferLink", str(ctx.exception))

    def test_unknown_interface_fails(self) -> None:
        bad = _NEISO_ROWS[1].replace(
            "HQ_import_simultaneous,", "HQ_import_simultaneos,"
        )
        _write_fixture(self.raw_root, [bad])
        with self.assertRaises(ValueError) as ctx:
            curate_tx.curate(raw_root=self.raw_root, isos=["NEISO"])
        self.assertIn("InterfaceLimit", str(ctx.exception))

    def test_pre_floor_year_fails(self) -> None:
        bad = _NEISO_ROWS[0].replace(",2026,,link,", ",2021,,link,")
        _write_fixture(self.raw_root, [bad])
        with self.assertRaises(ValueError) as ctx:
            curate_tx.curate(raw_root=self.raw_root, isos=["NEISO"])
        self.assertIn("floor", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
