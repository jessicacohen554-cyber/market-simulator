"""Tests for ``results.evolution_ledger`` write/load and versioning.

Covers the durable capacity-evolution ledger: the write/load round-trip, the
new ``ledger_version`` stamp (additive), backward tolerance for legacy files
written before versioning, the path derivation beside a cached parquet, and the
multi-year ``load_ledgers_for_run`` collector.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from market_sim.results import evolution_ledger as EL
from tests.helpers.builders import make_gen


class TestWriteLoadRoundTrip(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def _sample(self) -> dict:
        led = EL.new_events()
        led.update({"iso": "ERCOT", "year": 2027, "mode": "forecast"})
        led["retirements"].append(
            {"unit_id": "U1", "fuel": "coal", "mw": 500.0, "reason": "economic"}
        )
        return led

    def test_round_trip_preserves_content(self):
        path = self.dir / "evolution_2027.json"
        EL.write_ledger(path, self._sample())
        loaded = EL.load_ledger(path)
        self.assertEqual(loaded["iso"], "ERCOT")
        self.assertEqual(loaded["year"], 2027)
        self.assertEqual(loaded["retirements"][0]["unit_id"], "U1")

    def test_write_stamps_ledger_version(self):
        path = self.dir / "evolution_2027.json"
        EL.write_ledger(path, self._sample())
        loaded = EL.load_ledger(path)
        self.assertEqual(loaded["ledger_version"], EL.LEDGER_VERSION)

    def test_write_does_not_mutate_input(self):
        led = self._sample()
        EL.write_ledger(self.dir / "evolution_2027.json", led)
        self.assertNotIn("ledger_version", led)

    def test_caller_ledger_version_preserved(self):
        led = self._sample()
        led["ledger_version"] = 99
        EL.write_ledger(self.dir / "evolution_2027.json", led)
        loaded = EL.load_ledger(self.dir / "evolution_2027.json")
        self.assertEqual(loaded["ledger_version"], 99)

    def test_legacy_file_without_version_loads(self):
        # A pre-versioning ledger (no ledger_version key) must still load; the
        # module contract treats an absent key as legacy (version 1).
        path = self.dir / "evolution_2020.json"
        path.write_text(json.dumps({"iso": "PJM", "year": 2020, "retirements": []}))
        loaded = EL.load_ledger(path)
        self.assertNotIn("ledger_version", loaded)
        self.assertEqual(loaded["iso"], "PJM")


class TestLedgerPathAndTotals(unittest.TestCase):
    def test_ledger_path_beside_parquet(self):
        p = Path("results/ERCOT/key/year_2027.parquet")
        self.assertEqual(EL.ledger_path(p).name, "evolution_2027.json")
        self.assertEqual(EL.ledger_path(p).parent, p.parent)

    def test_fleet_totals_by_fuel(self):
        fleet = [
            make_gen("A", fuel_type="coal", pmax_mw=500.0),
            make_gen("B", fuel_type="coal", pmax_mw=250.0),
            make_gen("C", fuel_type="gas_cc", pmax_mw=400.0),
        ]
        totals = EL.fleet_totals_by_fuel(fleet)
        self.assertAlmostEqual(totals["coal"], 750.0)
        self.assertAlmostEqual(totals["gas_cc"], 400.0)

    def test_new_events_has_expected_lists(self):
        ev = EL.new_events()
        for key in ("retirements", "thermal_additions", "ccs_retrofits"):
            self.assertEqual(ev[key], [])


class TestLoadLedgersForRun(unittest.TestCase):
    def test_collects_and_sorts_by_year(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d)
            for year in (2028, 2026, 2027):
                EL.write_ledger(cache / f"evolution_{year}.json", {"year": year})
            # A non-ledger file must be ignored.
            (cache / "year_2026.parquet").write_bytes(b"x")
            out = EL.load_ledgers_for_run(cache)
            self.assertEqual(list(out), [2026, 2027, 2028])
            self.assertEqual(out[2027]["year"], 2027)


if __name__ == "__main__":
    unittest.main()
