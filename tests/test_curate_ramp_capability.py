"""Tests for the ramp-capability intake on a tiny synthetic fixture.

Writes minimal EIA-860 + CAMPD parquet fixtures into a tmp raw tree, runs
``curate``, and asserts the written Parquet is schema-valid and the
reconciliation is correct: the EIA-860 "10M" fast-start aggregation, the
CEMS 1-hour up-ramp envelope with gap exclusion and offline-null handling,
the outer join, and the model-side ``measured_ramp10_frac`` formula. NOT a
full-data run: CLEAN_DIR is redirected to a tmp dir (as in
tests/test_curate_outages.py) so it never touches the real tree. Trivial
case first (one plant, 24 hours), then the multi-source join.
"""

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pandas as pd

from market_sim.data.ramp_capability import (
    MIN_OBSERVED_HOURS,
    PlantRampCapability,
    measured_ramp10_frac,
)
from scripts import curate_ramp_capability as curate_rc
from scripts.lib import clean_io
from scripts.lib import ramp_capability as rc
from scripts.lib.clean_io import validate_clean


def _write_eia860_fixture(raw_root: Path) -> None:
    """Two PJM plants: one with a 10M GT + a 1H ST, one pure-ST; one MISO row."""
    d = raw_root / "eia-860"
    d.mkdir(parents=True, exist_ok=True)
    operable = pd.DataFrame(
        {
            "Plant Code": [100, 100, 200, 300],
            "Generator ID": ["GT1", "ST1", "ST1", "GT1"],
            "Prime Mover": ["GT", "ST", "ST", "GT"],
            "Energy Source 1": ["NG", "NG", "NG", "NG"],
            "Nameplate Capacity (MW)": [50.0, 150.0, 400.0, 80.0],
            "Time from Cold Shutdown to Full Load": ["10M", "1H", "12H", "10M"],
        }
    )
    operable.to_parquet(d / "eia860_generator_operable.parquet")
    ba = pd.DataFrame(
        {
            "plant_id": [100, 100, 200, 300],
            "generator_id": ["GT1", "ST1", "ST1", "GT1"],
            "balancing_authority_code": ["PJM", "PJM", "PJM", "MISO"],
        }
    )
    ba.to_parquet(d / "eia860_generators.parquet")


def _write_campd_fixture(raw_root: Path) -> None:
    """Plant 100 (PA): 24 hours, two units, one gap; plant 999 CEMS-only."""
    d = raw_root / "campd-unit-level"
    d.mkdir(parents=True, exist_ok=True)
    hours = list(range(24))
    # Unit A ramps 0 -> 120 at hour 12 (offline before: null grossLoad).
    load_a = [np.nan] * 12 + [120.0] * 12
    # Unit B steady 30 MW, with hour 5 missing entirely (a row gap): the
    # 4->6 diff spans 2 hours and must be EXCLUDED from the envelope.
    rows = []
    for h, ld in zip(hours, load_a):
        rows.append((100, "A", "2023-01-01", h, ld))
    for h in hours:
        if h == 5:
            continue
        rows.append((100, "B", "2023-01-01", h, 30.0 if h != 6 else 200.0))
    # CEMS-only plant 999, single unit: 0 MW (h0-5), 60 MW (h6-8), hour 9
    # MISSING (a plant-level row gap), 200 MW (h10), 60 MW (h11-23). The
    # h8->h10 +140 move spans the gap and must be EXCLUDED; the largest
    # consecutive up-move is the +60 step at h5->h6.
    for h in hours:
        if h == 9:
            continue
        if h < 6:
            ld = 0.0
        elif h == 10:
            ld = 200.0
        else:
            ld = 60.0
        rows.append((999, "C", "2023-01-01", h, ld))
    df = pd.DataFrame(
        rows, columns=["facilityId", "unitId", "date", "hour", "grossLoad"]
    )
    df["date"] = pd.to_datetime(df["date"])
    df.to_parquet(d / "PA_2023.parquet")


class TestCurateRampCapability(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        root = Path(self._tmp.name)
        self.raw_root = root / "raw"
        self.raw_root.mkdir(parents=True)
        self._orig_clean = clean_io.paths.CLEAN_DIR
        clean_io.paths.CLEAN_DIR = root / "clean"

    def tearDown(self) -> None:
        clean_io.paths.CLEAN_DIR = self._orig_clean
        self._tmp.cleanup()

    def _curate_pjm(self) -> pd.DataFrame:
        _write_eia860_fixture(self.raw_root)
        _write_campd_fixture(self.raw_root)
        written = curate_rc.curate(raw_root=self.raw_root, isos=["PJM"])
        self.assertEqual(len(written), 1, "expected one PJM partition")
        path = written[0]
        validate_clean(path)
        return pd.read_parquet(path)

    def test_pjm_reconciliation(self) -> None:
        df = self._curate_pjm().set_index("plant_code")
        # EIA-860 aggregation: plant 100 fast = the 10M GT only.
        self.assertAlmostEqual(df.loc[100, "fast_start_mw"], 50.0)
        self.assertAlmostEqual(df.loc[100, "thermal_nameplate_mw"], 200.0)
        # Plant 200: no 10M rows.
        self.assertAlmostEqual(df.loc[200, "fast_start_mw"], 0.0)
        self.assertAlmostEqual(df.loc[200, "thermal_nameplate_mw"], 400.0)
        # MISO plant 300 must NOT appear in the PJM partition.
        self.assertNotIn(300, df.index)
        # CEMS envelope, plant 100. Plant-hour sums (offline nulls -> 0;
        # unit A carries every hour so the plant series has no gap even
        # though unit B's hour-5 row is absent): h0-4 = 30, h5 = 0 (A
        # offline-zero, B row absent), h6 = 200 (B spike), h7-11 = 30,
        # h12-23 = 150 (A's 0->120 start + B's 30). Largest consecutive
        # up-move = h5->h6 = +200; observed pmax = 200.
        self.assertAlmostEqual(df.loc[100, "ramp_up_1h_mw"], 200.0)
        self.assertAlmostEqual(df.loc[100, "observed_pmax_mw"], 200.0)
        self.assertEqual(int(df.loc[100, "hours_observed"]), 24)
        # CEMS-only plant 999 gets a row with null EIA-860 columns, and its
        # +140 move across the missing hour 9 is excluded: envelope = the
        # +60 consecutive step, while observed pmax still sees the 200.
        self.assertAlmostEqual(df.loc[999, "ramp_up_1h_mw"], 60.0)
        self.assertAlmostEqual(df.loc[999, "observed_pmax_mw"], 200.0)
        self.assertTrue(np.isnan(df.loc[999, "thermal_nameplate_mw"]))
        self.assertEqual(int(df.loc[999, "hours_observed"]), 23)
        self.assertEqual(df.loc[999, "vintage_span"], "2023-2025")

    def test_skip_iso_without_raw(self) -> None:
        # No fixtures at all -> MISO curation writes nothing and doesn't raise.
        written = curate_rc.curate(raw_root=self.raw_root, isos=["MISO"])
        self.assertEqual(written, [])

    def test_registry_covers_pjm_and_miso(self) -> None:
        registry = rc.load_registry()
        self.assertIn("PJM", registry)
        self.assertIn("MISO", registry)
        self.assertEqual(registry["PJM"].ba_code, "PJM")

    def test_measured_ramp10_frac_formula(self) -> None:
        # Fast-start floor: a plant reported all-10M gets frac 1.0 whatever
        # the class rate says.
        cap = PlantRampCapability(
            fast_start_mw=100.0,
            thermal_nameplate_mw=100.0,
            ramp_up_1h_mw=10.0,
            observed_pmax_mw=100.0,
            hours_observed=MIN_OBSERVED_HOURS,
        )
        self.assertAlmostEqual(measured_ramp10_frac(0.2, cap), 1.0)
        # Envelope ceiling: class 0.40 CC whose largest hourly move is 20% of
        # capacity is capped at 0.20.
        cap = PlantRampCapability(
            fast_start_mw=0.0,
            thermal_nameplate_mw=500.0,
            ramp_up_1h_mw=100.0,
            observed_pmax_mw=480.0,
            hours_observed=MIN_OBSERVED_HOURS,
        )
        self.assertAlmostEqual(measured_ramp10_frac(0.40, cap), 0.20)
        # Below the coverage threshold the envelope is NOT trusted: class rate
        # survives (fast floor still applies).
        cap = PlantRampCapability(
            fast_start_mw=0.0,
            thermal_nameplate_mw=500.0,
            ramp_up_1h_mw=100.0,
            observed_pmax_mw=480.0,
            hours_observed=MIN_OBSERVED_HOURS - 1,
        )
        self.assertAlmostEqual(measured_ramp10_frac(0.40, cap), 0.40)
        # No usable basis -> class rate unchanged.
        cap = PlantRampCapability(
            fast_start_mw=float("nan"),
            thermal_nameplate_mw=float("nan"),
            ramp_up_1h_mw=float("nan"),
            observed_pmax_mw=float("nan"),
            hours_observed=0,
        )
        self.assertAlmostEqual(measured_ramp10_frac(0.15, cap), 0.15)


if __name__ == "__main__":
    unittest.main()
