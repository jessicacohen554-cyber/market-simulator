"""The merit-order panel prices a common-generator stack pair as ONE unit (nyiso-192).

``outage_detect.build_merit_order_panel`` read the CAMPD parquets with a bare
``pd.read_parquet`` and never applied the stack-duplicate helpers that
``campd._normalize_campd`` applies, so Astoria 8906's ``31RH``/``32SH`` and
``51RH``/``52SH`` pairs entered the panel as two units each carrying the SAME
generator MW with half the heat — a heat rate of ~5.5 against a merged ~11.0
(nyiso-184 §4.1), i.e. an SRMC at half its physical value inside the guard
that decides whether a dead span is a mechanical outage or an economic lay-up.
These tests pin the repair on the fixture the ``_normalize_campd`` tests use.
"""

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.lib import outage_detect as od
from tests.curation.test_campd import _stack_pair_extract


def _fixture_frame(hours: int) -> pd.DataFrame:
    """The Astoria stack-pair fixture stretched over *hours* hours."""
    base = _stack_pair_extract(2023)
    days = int(np.ceil(hours / 24))
    frames = []
    for d in range(days):
        f = base.copy()
        f["date"] = pd.Timestamp("2023-01-01") + pd.Timedelta(days=d)
        frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    df["primaryFuelInfo"] = "Pipeline Natural Gas"
    return df


class TestMeritPanelStackPair(unittest.TestCase):
    def _panel(self):
        hours = 24 * 3  # comfortably above MIN_REAL_RUN_HOURS
        with tempfile.TemporaryDirectory() as tmp:
            _fixture_frame(hours).to_parquet(Path(tmp) / "NY_2023.parquet")
            saved = od._MERIT_UNIT_LEVEL_DIR
            od._MERIT_UNIT_LEVEL_DIR = Path(tmp)
            try:
                return od.build_merit_order_panel("NYISO", 2023, hours, ("NY",))
            finally:
                od._MERIT_UNIT_LEVEL_DIR = saved

    def test_duplicate_stack_is_merged_onto_its_primary(self):
        panel = self._panel()
        self.assertIsNotNone(panel)
        keys = set(panel.srmc)
        self.assertIn((8906, "31RH"), keys)
        self.assertNotIn((8906, "32SH"), keys, "the duplicate path must not be a unit")
        self.assertIn((8906, "20"), keys, "ordinary units are untouched")

    def test_merged_heat_rate_is_the_generator_heat_rate(self):
        panel = self._panel()
        gas = od.delivered_gas_price_hourly("NYISO", 2023, 24 * 3)
        self.assertIsNotNone(gas)
        # (1600 + 1500) MMBtu over 300 MW every hour -> 10.333 MMBtu/MWh;
        # the pre-repair panel read 1600 / 300 = 5.333 on the primary alone.
        hr_pair = panel.srmc[(8906, "31RH")] / gas
        np.testing.assert_allclose(hr_pair, 3100.0 / 300.0, rtol=1e-9)
        hr_plain = panel.srmc[(8906, "20")] / gas
        np.testing.assert_allclose(hr_plain, 600.0 / 50.0, rtol=1e-9)


if __name__ == "__main__":
    unittest.main()
