"""EIA-930 zero-coded filing gaps in the per-fuel benchmark loader.

Covers :data:`market_sim.data.eia930.actuals._ZERO_CODED_GAP_SERIES` — the
registry of ``(BA, fuel column)`` pairs whose exact ``0.0`` values are filing
gaps rather than observations. The benchmark loader's gap machinery guards NaN
only, so without the mask those hours are averaged into the annual benchmark as
genuine zero-output hours and deflate it.

Motivating measurement (2026-07-24, NYISO lane): the NYIS extract reads exactly
0 MW of ``NG: NUC`` for 1,275 h of 2023 against a four-unit ~3.4 GW baseload
fleet that NYISO's own hourly fuel-mix posting never shows below 1,989 MW — a
3.46 TWh benchmark deflation that read as the model over-running nuclear. See
``docs/FINDING-nyiso-import-hour-assignment-and-nuclear-benchmark-2026-07-24.md``.
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from market_sim.data import eia_loader  # noqa: E402


def _frame(column: str) -> pd.DataFrame:
    """A 48-hour synthetic extract carrying a 12-hour zero-coded gap."""
    times = pd.date_range("2023-01-01", periods=48, freq="h")
    values = np.full(48, 3_000.0)
    values[12:24] = 0.0
    return pd.DataFrame(
        {
            "UTC time": times,
            "Local date": times,
            column: values,
            "Net generation": np.full(48, 5_000.0),
        }
    )


def _benchmark(ba_code: str, iso: str, frame: pd.DataFrame):
    """Run ``load_eia_hourly_benchmark`` against a synthetic per-BA extract."""
    with tempfile.TemporaryDirectory() as tmp:
        frame.to_parquet(Path(tmp) / f"{ba_code} hourly.parquet", index=False)
        with mock.patch.object(eia_loader, "EIA_HOURLY_DIR", Path(tmp)):
            return eia_loader.load_eia_hourly_benchmark(iso, 2023)


class TestZeroCodedFilingGaps(unittest.TestCase):
    """Registered zero-coded gaps are bridged; unregistered real zeros survive."""

    def test_nyis_nuclear_zero_gap_is_bridged(self):
        bench = _benchmark("NYIS", "NYISO", _frame("NG: NUC"))
        self.assertIsNotNone(bench)
        gap = bench["nuclear"][12:24]
        # Interpolated across from the neighbouring hours: no phantom zero
        # survives into the benchmark, so the annual total is not deflated.
        self.assertTrue(np.all(gap > 0.0))
        np.testing.assert_allclose(gap, 3_000.0)

    def test_unregistered_series_keeps_its_real_zeros(self):
        """ERCO ``NG: WAT`` genuinely reaches 0 — masking it would fabricate MWh.

        ERCOT's conventional hydro fleet is ~0.05-0.24 TWh/yr and legitimately
        sits at zero for thousands of hours a year, so it is deliberately absent
        from the registry (as is ISNE ``NG: COL``).
        """
        bench = _benchmark("ERCO", "ERCOT", _frame("NG: WAT"))
        self.assertIsNotNone(bench)
        np.testing.assert_allclose(bench["hydro"][12:24], 0.0)

    def test_registry_scope_is_the_measured_pathology_only(self):
        """The registry names only pairs proven to be filing gaps."""
        from market_sim.data.eia930.actuals import _ZERO_CODED_GAP_SERIES

        self.assertEqual(set(_ZERO_CODED_GAP_SERIES), {"NYIS"})
        self.assertEqual(set(_ZERO_CODED_GAP_SERIES["NYIS"]), {"NG: NUC"})


if __name__ == "__main__":
    unittest.main()
