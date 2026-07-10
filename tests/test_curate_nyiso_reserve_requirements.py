"""Tests for the nyiso-reserve-requirements / nyiso-operating-events intake.

Writes a minimal raw fixture (a two-row requirement transcription plus one
day of each MIS message feed) into a tmp raw tree, runs ``curate``, and
asserts both written Parquet partitions are schema-valid and round-trip the
fixture values — including the TSA start/end extraction, the OOM and
emergency-transaction parses, and the Eastern->UTC stamp conversion.
CLEAN_DIR is redirected to a tmp dir so the real tree is never touched.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from scripts import curate_nyiso_reserve_requirements as curate_rr
from scripts.lib import clean_io
from scripts.lib.clean_io import validate_clean

_REQ_CSV = """version,region,zones,product,period_label,hb_start,hb_end,requirement_mw,tsa_reduced_to_zero,evidence_start,evidence_end,source_doc,notes
v2021,SENY,G-K,total_30,hb_range,7,21,1800,True,2021-12-04,2026-02-14,lrr_wayback_20211204.pdf,hourly-step regime
v2021,NYC,J,total_10,all,0,23,500,True,2021-12-04,2026-02-14,lrr_wayback_20211204.pdf,
"""

_RTE_CSV = """source_file,timestamp_local,message
20240705RealTimeEvents.csv,07/05/2024 00:00:00,Start of day system state is NORMAL
20240705RealTimeEvents.csv,07/05/2024 19:00:00,**System now operating in thunderstorm alert.**
20240705RealTimeEvents.csv,07/05/2024 22:35:00,**System no longer operating in thunderstorm alert.**
20240705RealTimeEvents.csv,07/05/2024 23:00:00,Some unrelated narrative message
"""

_OM_CSV = """source_file,timestamp_local,message
20240705OperMessages.csv,05-Jul-2024 14:43,"Prices in the July 04, 2024 Real-Time Market are correct."
20240705OperMessages.csv,05-Jul-2024 15:00,ISO REQUESTS GILBOA___2 OUT OF MERIT. COMMITED FOR ISO RELIABILITY AT START TIME 07/05/2024 15:00 FOR For TSA..
20240705OperMessages.csv,05-Jul-2024 16:00,NPX Emergency transaction added 251 MWs.  07/05/2024 16:00 EDT
"""


def _write_fixture(raw_root: Path) -> None:
    req_dir = raw_root / "NYISO-AS" / "requirements"
    (req_dir / "realtime-events").mkdir(parents=True)
    (req_dir / "oper-messages").mkdir(parents=True)
    (req_dir / "nyiso_locational_reserve_requirements.csv").write_text(_REQ_CSV)
    (req_dir / "realtime-events" / "NYISO_realtime_events_2024.csv").write_text(
        _RTE_CSV
    )
    (req_dir / "oper-messages" / "NYISO_oper_messages_2024.csv").write_text(_OM_CSV)


class TestCurateNyisoReserveRequirements(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        _write_fixture(self.raw_root)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def test_requirements_frame(self) -> None:
        """The transcription round-trips with hour bounds and TSA flags."""
        df = curate_rr.build_requirements_frame(self.raw_root)
        self.assertEqual(len(df), 2)
        seny = df[df["region"] == "SENY"].iloc[0]
        self.assertEqual(seny["requirement_mw"], 1800.0)
        self.assertEqual(seny["hb_start"], 7)
        self.assertEqual(seny["hb_end"], 21)
        self.assertTrue(bool(seny["tsa_reduced_to_zero"]))

    def test_events_extraction(self) -> None:
        """TSA window, OOM commit and emergency transaction are extracted."""
        ev = curate_rr.build_events_frame(self.raw_root)
        # 3 RTE events (narrative line dropped) + 2 OM events (price notice dropped)
        self.assertEqual(len(ev), 5)
        tsa = ev[ev["event_type"] == "thunderstorm_alert"].sort_values("seq")
        self.assertListEqual(list(tsa["action"]), ["start", "end"])
        # 19:00 EDT on 2024-07-05 == 23:00 UTC
        self.assertEqual(
            tsa.iloc[0]["timestamp_utc"],
            pd.Timestamp("2024-07-05 23:00:00", tz="UTC"),
        )
        oom = ev[ev["event_type"] == "oom_commitment"].iloc[0]
        self.assertEqual(oom["action"], "requested")
        self.assertEqual(oom["detail"], "GILBOA___2")
        emerg = ev[ev["event_type"] == "emergency_transaction"].iloc[0]
        self.assertEqual(emerg["mw"], 251.0)
        self.assertEqual(emerg["detail"], "NPX")
        sod = ev[ev["start_of_day"]]
        self.assertEqual(len(sod), 1)
        self.assertEqual(sod.iloc[0]["event_type"], "system_state")

    def test_curate_writes_valid_partitions(self) -> None:
        """Both partitions write through the seam and re-validate."""
        written = curate_rr.curate(raw_root=self.raw_root)
        self.assertEqual(len(written), 2)
        for path in written:
            schema = validate_clean(path)
            self.assertIn(
                schema.datatype,
                ("nyiso-reserve-requirements", "nyiso-operating-events"),
            )


if __name__ == "__main__":
    unittest.main()
