"""Tests for the ERCOT measured storage-capability re-basis (ERCOT-66).

Covers ``model.storage.ercot_storage_capability_caps`` — the backcast battery
power re-basis onto the 60-Day DAM disclosure registered non-OUT storage HSL
(``scripts/derive_ercot_storage_capability.py``) — at the trivial scale first
(2 units / 24 hours), per the repo testing pattern.
"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from market_sim.model import storage as storage_mod
from market_sim.model.storage import StorageUnit, ercot_storage_capability_caps

HOURS = 24


def _units() -> list[StorageUnit]:
    """Two battery zone-aggregates (2:1 power, 2h/4h duration) + pumped storage."""
    return [
        StorageUnit(
            unit_id="HOUSTON_eia860_storage",
            zone="HOUSTON",
            tech_name="li_ion",
            power_cap_mw=200.0,
            energy_cap_mwh=400.0,
            zone_idx=0,
        ),
        StorageUnit(
            unit_id="WEST_eia860_storage",
            zone="WEST",
            tech_name="li_ion",
            power_cap_mw=100.0,
            energy_cap_mwh=400.0,
            zone_idx=1,
        ),
        StorageUnit(
            unit_id="PS",
            zone="HOUSTON",
            tech_name="pumped_storage",
            power_cap_mw=50.0,
            energy_cap_mwh=500.0,
            zone_idx=0,
        ),
    ]


def _write_csv(path: Path, capability: np.ndarray, year: int = 2023) -> None:
    pd.DataFrame(
        {
            "year": np.full(capability.size, year, dtype=int),
            "hour": np.arange(capability.size, dtype=int),
            "capability_mw": capability,
        }
    ).to_csv(path, index=False)


class TestErcotStorageCapabilityCaps(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self._orig = storage_mod._STORAGE_CAPABILITY_PATH
        storage_mod._STORAGE_CAPABILITY_PATH = (
            Path(self._tmp.name) / "ercot-storage-capability.csv"
        )

    def tearDown(self) -> None:
        storage_mod._STORAGE_CAPABILITY_PATH = self._orig
        self._tmp.cleanup()

    def test_covered_hours_rebase_power_and_energy(self) -> None:
        """Measured MW splits by EIA-860 zone shares; energy = MW x duration."""
        units = _units()
        cap = np.full(HOURS, 600.0)
        _write_csv(storage_mod._STORAGE_CAPABILITY_PATH, cap)
        p = np.array([200.0, 100.0, 50.0])
        e = np.array([400.0, 400.0, 500.0])
        new_p, new_e = ercot_storage_capability_caps(p, e, units, 2023, HOURS)
        # Batteries: 600 MW split 2:1 -> 400/200; durations 2h/4h -> 800/800.
        np.testing.assert_allclose(new_p[0], np.full(HOURS, 400.0))
        np.testing.assert_allclose(new_p[1], np.full(HOURS, 200.0))
        np.testing.assert_allclose(new_e[0], np.full(HOURS, 800.0))
        np.testing.assert_allclose(new_e[1], np.full(HOURS, 800.0))
        # Pumped storage untouched.
        np.testing.assert_allclose(new_p[2], np.full(HOURS, 50.0))
        np.testing.assert_allclose(new_e[2], np.full(HOURS, 500.0))

    def test_uncovered_hours_keep_eia860(self) -> None:
        """NaN hours (the Oct-2023 hole) fall back to the EIA-860 caps."""
        units = _units()
        cap = np.full(HOURS, 600.0)
        cap[6:12] = np.nan
        _write_csv(storage_mod._STORAGE_CAPABILITY_PATH, cap)
        p = np.array([200.0, 100.0, 50.0])
        e = np.array([400.0, 400.0, 500.0])
        new_p, new_e = ercot_storage_capability_caps(p, e, units, 2023, HOURS)
        np.testing.assert_allclose(new_p[0, 6:12], np.full(6, 200.0))
        np.testing.assert_allclose(new_p[0, :6], np.full(6, 400.0))
        np.testing.assert_allclose(new_e[1, 6:12], np.full(6, 400.0))

    def test_missing_file_or_year_passes_through(self) -> None:
        """No CSV / no rows for the year -> both caps returned unchanged."""
        units = _units()
        p = np.array([200.0, 100.0, 50.0])
        e = np.array([400.0, 400.0, 500.0])
        out_p, out_e = ercot_storage_capability_caps(p, e, units, 2023, HOURS)
        self.assertIs(out_p, p)
        self.assertIs(out_e, e)
        _write_csv(storage_mod._STORAGE_CAPABILITY_PATH, np.full(HOURS, 600.0), 2024)
        out_p, out_e = ercot_storage_capability_caps(p, e, units, 2023, HOURS)
        self.assertIs(out_p, p)

    def test_ramped_2d_caps_use_hourly_shares(self) -> None:
        """A COD-ramped (2-D) EIA-860 profile splits by the hour's own shares."""
        units = _units()
        cap = np.full(HOURS, 300.0)
        _write_csv(storage_mod._STORAGE_CAPABILITY_PATH, cap)
        p = np.tile(np.array([[200.0], [100.0], [50.0]]), (1, HOURS))
        p[1, :12] = 0.0  # WEST battery not yet energized in the first half
        e = np.tile(np.array([[400.0], [400.0], [500.0]]), (1, HOURS))
        e[1, :12] = 0.0
        new_p, _ = ercot_storage_capability_caps(p, e, units, 2023, HOURS)
        # First half: HOUSTON carries all 300 MW; second half splits 2:1.
        np.testing.assert_allclose(new_p[0, :12], np.full(12, 300.0))
        np.testing.assert_allclose(new_p[1, :12], np.zeros(12))
        np.testing.assert_allclose(new_p[0, 12:], np.full(12, 200.0))
        np.testing.assert_allclose(new_p[1, 12:], np.full(12, 100.0))


if __name__ == "__main__":
    unittest.main()
