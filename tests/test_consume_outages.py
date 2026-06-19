"""Parity test for the clean-backed outage read path.

Exercises the ``MARKET_SIM_USE_CLEAN`` migration seam added to
``src/market_sim/data/outages.py``: the model can source its facility-outage
overlay from the curated clean tree (``data/clean/outages``, written by
``scripts/curate_outages.py`` through the frozen ``scripts/lib/clean_io.py``
seam) instead of re-deriving it from raw. The test asserts that, for one small
slice, the clean-backed ``outage_mw`` / ``available_mw`` match the existing
raw-derive path within tolerance — so flipping the flag does not move the model.

This is a slow / integration test: it reconciles the real raw CAMPD + ERCOT
outage extracts. It regenerates the clean slice from raw itself (the clean tree
is gitignored), and skips cleanly when the raw inputs are absent.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.config.paths import CAMPD_BINS_CSV  # noqa: E402
from market_sim.data import outages as O  # noqa: E402

# pytest markers: keep this out of the fast unit suite (touches real raw data).
try:
    import pytest

    pytestmark = [pytest.mark.slow, pytest.mark.integration]
except ImportError:  # pragma: no cover - allow plain unittest runs
    pytest = None

HOURS = 8760

# Raw inputs the clean curation reconciles. Absent in a minimal checkout -> skip.
_RAW_FACILITY = paths.RAW_DATA_DIR / "campd-outages.csv"
_RAW_REGISTRY = paths.RAW_DATA_DIR / "reference" / "master-plant-registry.csv"


def _raw_inputs_present() -> bool:
    return (
        _RAW_FACILITY.is_file() and _RAW_REGISTRY.is_file() and CAMPD_BINS_CSV.is_file()
    )


def _registry_nameplate() -> dict[int, float]:
    """``plant_id -> nameplate_capacity_mw`` from the raw plant registry."""
    reg = pd.read_csv(_RAW_REGISTRY, usecols=["plantid", "nameplate_capacity_mw"])
    return {
        int(r.plantid): float(r.nameplate_capacity_mw)
        for r in reg.itertuples(index=False)
        if pd.notna(r.plantid)
        and pd.notna(r.nameplate_capacity_mw)
        and float(r.nameplate_capacity_mw) > 0.0
    }


@unittest.skipUnless(_raw_inputs_present(), "raw outage inputs absent")
class CleanBackedOutageParity(unittest.TestCase):
    """Clean-backed facility outages match the raw derive within tolerance."""

    @classmethod
    def setUpClass(cls) -> None:
        # Regenerate the clean slice from raw (gitignored / disposable), then
        # pick a year present in both the clean tree and the raw derive.
        from scripts import curate_outages

        written = curate_outages.curate()
        if not written:
            raise unittest.SkipTest("no outage rows curated from raw")

        clean_io = O._clean_io()
        cls.year = None
        for path in written:
            year = int(
                pd.read_parquet(path, columns=["interval_start_utc"])[
                    "interval_start_utc"
                ].dt.year.iloc[0]
            )
            if clean_io.clean_exists("outages", year=year) and O.outage_masks_for_year(
                year, HOURS, bins_path=str(CAMPD_BINS_CSV)
            ):
                cls.year = year
                break
        if cls.year is None:
            raise unittest.SkipTest("no curated year overlaps the raw derive")

    def setUp(self) -> None:
        # The clean-backed builder is cached on its args; clear so flag flips
        # within the test take effect deterministically.
        O._clean_outage_masks_for_year.cache_clear()

    def test_facility_mask_parity(self) -> None:
        """Clean-backed masks match the raw-derive masks within tolerance.

        The raw derive carries a few facility windows whose plant has no
        registry nameplate (no availability denominator), which the clean
        curation drops — so the clean plant set is a subset of the raw set.
        Where both cover a plant, the offline-hour sets agree up to a couple of
        UTC/local year-boundary hours.
        """
        bins = str(CAMPD_BINS_CSV)
        raw = O.outage_masks_for_year(self.year, HOURS, bins_path=bins)
        clean = O._clean_outage_masks_for_year(self.year, HOURS, bins)

        self.assertTrue(raw, "raw derive produced no facility masks")
        self.assertTrue(clean, "clean path produced no facility masks")

        common = set(raw) & set(clean)
        # Overlap must be high: clean drops only nameplate-less plants.
        self.assertGreaterEqual(len(common), int(0.9 * len(raw)))
        self.assertFalse(
            set(clean) - set(raw),
            f"clean masks for plants absent from raw: {set(clean) - set(raw)}",
        )

        diff_hours = sum(int((raw[c] ^ clean[c]).sum()) for c in common)
        # Only UTC/local year-boundary spillover should differ (<= 6h/plant).
        self.assertLessEqual(diff_hours, 6 * len(common))

    def test_outage_and_available_mw_parity(self) -> None:
        """Per-plant clean outage_mw / available_mw match the derive path.

        For a facility-grain (``"ALL"``) plant, the clean ``outage_mw`` is the
        plant nameplate at every offline hour and ``available_mw`` is zero. The
        derive path marks the same hours offline; reconstructing its MW with the
        same registry nameplate must reproduce the clean columns hour-for-hour.
        """
        bins = str(CAMPD_BINS_CSV)
        raw = O.outage_masks_for_year(self.year, HOURS, bins_path=bins)
        nameplate = _registry_nameplate()

        clean = O.read_clean_outages(self.year)
        all_rows = clean[clean["unit_id"] == "ALL"]
        local = pd.to_datetime(all_rows["interval_start_local"])
        all_rows = all_rows[local.dt.year == self.year]
        local = local[local.dt.year == self.year]

        # A plant covered by both layers that has a registry nameplate.
        candidates = [
            c
            for c in raw
            if c in set(all_rows["plant_id"].astype("int64")) and c in nameplate
        ]
        self.assertTrue(candidates, "no shared facility plant with a nameplate")
        plant = candidates[0]
        cap = nameplate[plant]

        sub = all_rows[all_rows["plant_id"].astype("int64") == plant]
        sub_local = local.loc[sub.index]

        # Clean MW indexed on the model 8760-hour clock.
        clean_outage = np.zeros(HOURS)
        clean_avail = np.full(HOURS, np.nan)
        for ts, o_mw, a_mw in zip(
            sub_local,
            sub["outage_mw"].to_numpy(float),
            sub["available_mw"].to_numpy(float),
        ):
            h = O._hour_of_year(ts.month, ts.day, ts.hour)
            if 0 <= h < HOURS:
                clean_outage[h] = o_mw
                clean_avail[h] = a_mw

        # Derive MW: nameplate offline where the raw mask is set, available 0.
        mask = raw[plant]
        derive_outage = np.where(mask, cap, 0.0)
        derive_avail = np.where(mask, 0.0, np.nan)

        # Compare only the offline hours common to both (boundary hours aside).
        both_off = (clean_outage > 0) & mask
        self.assertGreater(both_off.sum(), 0, "no overlapping offline hours")
        np.testing.assert_allclose(
            clean_outage[both_off], derive_outage[both_off], rtol=0, atol=1e-6
        )
        np.testing.assert_allclose(
            clean_avail[both_off], derive_avail[both_off], rtol=0, atol=1e-6
        )
        # Clean's facility availability is zero (whole plant offline).
        self.assertTrue(np.all(clean_avail[both_off] == 0.0))


if __name__ == "__main__":
    unittest.main()
