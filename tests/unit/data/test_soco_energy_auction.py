"""Southern Company Energy Auction loader (lane soco-84; REPORTED-ONLY series)."""

import tempfile
import unittest
from pathlib import Path

from market_sim.data.soco_energy_auction import (
    load_soco_energy_auction_daily,
    load_soco_energy_auction_hourly,
)

_HOURLY = (
    '"UTC_FLOW_HOUR","CPT_FLOW_HOUR","CPT_HOUR_END","PRICE","TLU"\n'
    '"2023-07-15 05:00:00","2023-07-15 00:00:00","01","32","2023-07-15 03:52:52"\n'
    '"2023-07-15 14:00:00","2023-07-15 09:00:00","10","32.08","2023-07-15 12:52:11"\n'
)
_DAILY = (
    '"CLEARING_DATE","FLOW_DATE","PRODUCT","HEATRATE","PRICE","TLU"\n'
    '"2022-01-18","2022-01-19","Firm-LD","","51.17","2022-01-18 12:50:06"\n'
)


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "hourly").mkdir()
        (self.tmp / "daily").mkdir()
        (self.tmp / "hourly/2023-07-15_HOURLY_CLEARING_PRICES.CSV").write_text(_HOURLY)
        (self.tmp / "daily/2022-01-18_DAILY_CLEARING_PRICES.CSV").write_text(_DAILY)

    def test_hourly_is_utc_hour_beginning(self):
        s = load_soco_energy_auction_hourly(self.tmp)
        self.assertEqual(len(s), 2)
        self.assertEqual(str(s.index[0]), "2023-07-15 05:00:00")
        self.assertAlmostEqual(float(s.iloc[1]), 32.08)

    def test_duplicate_hour_is_refused(self):
        (self.tmp / "hourly/2023-07-16_HOURLY_CLEARING_PRICES.CSV").write_text(_HOURLY)
        with self.assertRaises(ValueError):
            load_soco_energy_auction_hourly(self.tmp)

    def test_foreign_layout_is_refused(self):
        (self.tmp / "hourly/2023-07-17_HOURLY_CLEARING_PRICES.CSV").write_text(
            "A,B\n1,2\n"
        )
        with self.assertRaises(ValueError):
            load_soco_energy_auction_hourly(self.tmp)

    def test_daily(self):
        d = load_soco_energy_auction_daily(self.tmp)
        self.assertEqual(d["PRODUCT"].tolist(), ["Firm-LD"])

    def test_committed_store_loads(self):
        s = load_soco_energy_auction_hourly()
        self.assertEqual(len(s), 5082)
        self.assertGreater(len(load_soco_energy_auction_daily()), 0)


if __name__ == "__main__":
    unittest.main()
