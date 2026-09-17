"""The storage sidecar carries the LP's solved SOC and each unit's energy cap.

``DispatchResult.storage_soc`` has always been solved — the SOC recursion is a
core LP constraint — but until 2026-09-16 it was the one storage decision
variable no artifact persisted, so a committed bundle exposed throughput with no
reservoir state.

Why that mattered concretely (session caiso-284): the CAISO RA-bridge decommit
screen (``model/commitment._write_economic_bridges``) excludes storage-charge
headroom from its absorption term on an explicit ENERGY-capacity premise — *"the
fleet already fills by the belly in P1"* — and phase 0 could neither confirm nor
refute that premise from committed artifacts. Reconstructing SOC by integrating
the tech-aggregated charge/discharge series FAILS, because each unit carries its
own cyclic SOC constraint and the aggregation destroys it; the attempt returned a
span of 420-4,121 % of implied capacity. Persisting the solved variable removes
the reconstruction entirely.

These tests pin the two properties a reader depends on:

1. the per-unit frame carries ``soc_mwh`` + ``energy_cap_mwh``, and NaN (never a
   silent 0.0) when the solve carried no SOC block; and
2. the tech-aggregate sidecar SUMS both, so ``Σ cap − Σ soc`` is the tech's real
   absorption headroom — the quantity the screen's premise is about.

``docs/FINDING-caiso284-belly-commitment-phase0-2026-09-16.md`` §3.
"""

import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "rcf_storage_soc", str(REPO_ROOT / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

T = 4


def _units():
    return [
        SimpleNamespace(
            unit_id="NP15_batt", tech_name="li_ion", zone="NP15", energy_cap_mwh=400.0
        ),
        SimpleNamespace(
            unit_id="SP15_batt", tech_name="li_ion", zone="SP15", energy_cap_mwh=600.0
        ),
        SimpleNamespace(
            unit_id="HELMS",
            tech_name="pumped_storage",
            zone="NP15",
            energy_cap_mwh=10_000.0,
        ),
    ]


def _result(with_soc=True):
    chg = np.array([[10.0, 0, 0, 0], [20.0, 0, 0, 0], [30.0, 0, 0, 0]])
    dis = np.array([[0, 0, 0, 5.0], [0, 0, 0, 6.0], [0, 0, 0, 7.0]])
    soc = (
        np.array([[100.0, 110, 120, 130], [200.0, 210, 220, 230], [1.0, 2, 3, 4]])
        if with_soc
        else None
    )
    return SimpleNamespace(storage_charge=chg, storage_discharge=dis, storage_soc=soc)


class StorageFrameSocTests(unittest.TestCase):
    def test_per_unit_frame_carries_soc_and_cap(self):
        df = rcf._storage_frame(2024, "P1", _result(), _units())
        self.assertIn("soc_mwh", df.columns)
        self.assertIn("energy_cap_mwh", df.columns)
        self.assertEqual(len(df), 3 * T)
        helms = df[df.unit_id == "HELMS"].sort_values("hour")
        np.testing.assert_allclose(helms["soc_mwh"].to_numpy(), [1, 2, 3, 4])
        # The cap is a per-unit constant broadcast over that unit's hours.
        np.testing.assert_allclose(helms["energy_cap_mwh"].to_numpy(), 10_000.0)
        np.testing.assert_allclose(
            df[df.unit_id == "NP15_batt"]["energy_cap_mwh"].to_numpy(), 400.0
        )

    def test_soc_is_nan_not_zero_when_the_solve_carried_none(self):
        """A solve with no SOC block must be distinguishable from an empty one.

        Emitting 0.0 here would read as "the reservoir is empty in every hour",
        which is a real and very wrong claim about absorption headroom.
        """
        df = rcf._storage_frame(2024, "P1", _result(with_soc=False), _units())
        self.assertIn("soc_mwh", df.columns)
        self.assertTrue(df["soc_mwh"].isna().all())
        # The cap is a fleet fact, not a solve output, so it is still populated.
        self.assertFalse(df["energy_cap_mwh"].isna().any())

    def test_empty_fleet_still_returns_none(self):
        self.assertIsNone(rcf._storage_frame(2024, "P1", _result(), []))


class StorageSidecarAggregationTests(unittest.TestCase):
    def _write(self, frames):
        d = Path(tempfile.mkdtemp())
        out = rcf._write_storage_hourly_sidecar(d, 2024, frames)
        return pd.read_parquet(out)

    def test_sidecar_sums_soc_and_cap_over_a_techs_units(self):
        got = self._write([rcf._storage_frame(2024, "P1", _result(), _units())])
        li = got[got.tech == "li_ion"].sort_values("hour")
        # Two li_ion units: SOC and cap are EXTENSIVE, so they sum.
        np.testing.assert_allclose(li["soc_mwh"].to_numpy(), [300, 320, 340, 360])
        np.testing.assert_allclose(li["energy_cap_mwh"].to_numpy(), 1000.0)
        # Which is the whole point: headroom is computable at this grain.
        headroom = li["energy_cap_mwh"].to_numpy() - li["soc_mwh"].to_numpy()
        np.testing.assert_allclose(headroom, [700, 680, 660, 640])
        ps = got[got.tech == "pumped_storage"].sort_values("hour")
        np.testing.assert_allclose(ps["energy_cap_mwh"].to_numpy(), 10_000.0)

    def test_all_nan_soc_stays_nan_through_the_sum(self):
        """``min_count=1``: an unrecorded tech-hour must not collapse to 0.0."""
        got = self._write(
            [rcf._storage_frame(2024, "P1", _result(with_soc=False), _units())]
        )
        self.assertTrue(got["soc_mwh"].isna().all())
        self.assertFalse(got["energy_cap_mwh"].isna().any())

    def test_a_frame_predating_the_columns_still_writes(self):
        """A resumed year written before the pair existed must not raise."""
        legacy = rcf._storage_frame(2024, "P1", _result(), _units()).drop(
            columns=["soc_mwh", "energy_cap_mwh"]
        )
        got = self._write([legacy])
        self.assertIn("soc_mwh", got.columns)
        self.assertTrue(got["soc_mwh"].isna().all())

    def test_throughput_columns_are_unchanged(self):
        """The pair is ADDITIVE: charge/discharge aggregation must not move."""
        got = self._write([rcf._storage_frame(2024, "P1", _result(), _units())])
        li = got[got.tech == "li_ion"].sort_values("hour")
        np.testing.assert_allclose(li["charge_mw"].to_numpy(), [30, 0, 0, 0])
        np.testing.assert_allclose(li["discharge_mw"].to_numpy(), [0, 0, 0, 11])


if __name__ == "__main__":
    unittest.main()
