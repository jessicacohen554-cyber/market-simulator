"""Curate test for the ``pjm-elliott-forced-outages`` clean datatype (closeout-PJM-elliott)."""

from __future__ import annotations

from scripts.data import curate_pjm_elliott_forced_outages as cur
from scripts.lib import clean_io
from market_sim.data import pjm_elliott_outages as peo
from tests.helpers.base import CleanDirTestCase
from tests.helpers.pjm_elliott_fixture import write_fixture_csv


class TestCuratePjmElliottForcedOutages(CleanDirTestCase):
    def setUp(self):
        super().setUp()
        raw = self.tmp_path / "pjm-elliott-forced-outages"
        raw.mkdir(parents=True)
        self.csv = write_fixture_csv(raw / peo.RAW_CSV.name)

    def test_writes_a_valid_partition_matching_the_runtime_builder(self):
        paths = cur.curate(raw_root=self.tmp_path)
        self.assertEqual(len(paths), 1)
        clean_io.validate_clean(paths[0])
        df = clean_io.read_clean("pjm-elliott-forced-outages", iso="PJM", year=2022)
        self.assertEqual(len(df), 72 * 6)
        want = peo.build_hourly_frame(self.csv)
        self.assertEqual(df.forced_outage_mw.sum(), want.forced_outage_mw.sum())

    def test_skips_when_pjm_not_requested(self):
        self.assertEqual(cur.curate(raw_root=self.tmp_path, isos=["MISO"]), [])
