"""``build_calibration_reference`` consumes the SCREENED EIA-930 loader (SPP-41).

Rule 19 ``[R-ONE-MECH]`` / rule 26 ``[R-DELETE]``: the builder-local
``_screen_fuel_spikes`` that SPP-31 landed is DELETED, not kept as a thin
call — the one mechanism lives at the loader seam
(``eia930.actuals._screen_fuel_spike_columns``) and the builder simply sums
what ``load_eia_hourly_benchmark`` returns. A second copy here would be a
second place the same artifact class could be screened differently.
"""

from __future__ import annotations

import importlib.util
import unittest

import numpy as np
from tests.helpers import REPO_ROOT

_spec = importlib.util.spec_from_file_location(
    "bcr_spp41", str(REPO_ROOT / "scripts" / "data" / "build_calibration_reference.py")
)
bcr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bcr)


class TestBuilderHasNoScreenOfItsOwn(unittest.TestCase):
    def test_builder_local_screen_is_deleted(self):
        for name in (
            "_screen_fuel_spikes",
            "_FUEL_SPIKE_RATIO",
            "_FUEL_SPIKE_SCALE_PCT",
            "_NON_FUEL_BENCHMARK_SERIES",
        ):
            self.assertFalse(hasattr(bcr, name), name)

    def test_annual_by_fuel_sums_exactly_what_the_loader_returns(self):
        """No re-screen in the builder: an hour the loader leaves in place is
        summed as-is, so the loader seam is the ONLY place the repair happens."""
        arrays = {
            "wind": np.full(8760, 1_000.0),
            "solar": np.r_[np.full(8759, 500.0), 5e6],
            "net_gen": np.full(8760, 2_000.0),
        }
        orig = bcr.load_eia_hourly_benchmark
        bcr.load_eia_hourly_benchmark = lambda iso, year: arrays
        try:
            out = bcr._eia930_annual_by_fuel("SPP", 2023)
        finally:
            bcr.load_eia_hourly_benchmark = orig
        self.assertEqual(out["wind"], round(8760 * 1_000.0 / 1e6, 4))
        self.assertEqual(out["solar"], round((8759 * 500.0 + 5e6) / 1e6, 4))
        self.assertEqual(out["net_gen"], round(8760 * 2_000.0 / 1e6, 4))

    def test_empty_when_no_extract(self):
        orig = bcr.load_eia_hourly_benchmark
        bcr.load_eia_hourly_benchmark = lambda iso, year: None
        try:
            self.assertEqual(bcr._eia930_annual_by_fuel("SPP", 2023), {})
        finally:
            bcr.load_eia_hourly_benchmark = orig
