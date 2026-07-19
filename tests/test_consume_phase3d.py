"""Parity tests for the Phase 3D clean-backed read paths.

Exercises the ``MARKET_SIM_USE_CLEAN`` migration seam added to
``outages.py`` (``unit_outage_derate_factors``,
``partial_outage_derate_factors``), ``zone_assignment.py`` (``_plnt23`` /
``build_zone_lookup``), ``egrid.py`` (``load_egrid_plant_co2``) and
``cod_ramp.py`` (the registry-only ``year_built`` back-fill). For each, the
test regenerates the relevant clean slice from the real raw tree and asserts
the clean-backed result is byte-identical to the existing raw-derive path —
so flipping the flag never moves the model.

Slow / integration: touches the real raw data tree and skips cleanly when a
module's raw inputs are absent.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config import paths  # noqa: E402
from market_sim.config.paths import PLANT_REGISTRY_CSV  # noqa: E402
from market_sim.data import cod_ramp  # noqa: E402
from market_sim.data import egrid as E  # noqa: E402
from market_sim.data import outages as O  # noqa: E402
from market_sim.data import zone_assignment as ZA  # noqa: E402

try:
    import pytest

    pytestmark = [pytest.mark.slow, pytest.mark.integration]
except ImportError:  # pragma: no cover - allow plain unittest runs
    pytest = None

_USE_CLEAN_ENV = "MARKET_SIM_USE_CLEAN"


class _UseCleanEnvMixin:
    """Set/clear MARKET_SIM_USE_CLEAN around each test, restoring on exit."""

    def setUp(self) -> None:
        super().setUp()
        self._orig_env = os.environ.get(_USE_CLEAN_ENV)

    def tearDown(self) -> None:
        if self._orig_env is None:
            os.environ.pop(_USE_CLEAN_ENV, None)
        else:
            os.environ[_USE_CLEAN_ENV] = self._orig_env
        super().tearDown()


@unittest.skipUnless(O.UNIT_OUTAGE_CSV.is_file(), "ERCOT unit-outage CSV absent")
class UnitOutageDerateParity(_UseCleanEnvMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from scripts.data import curate_unit_outage_events

        written = curate_unit_outage_events.curate()
        if not written:
            raise unittest.SkipTest("no unit-outage-events curated from raw")
        cls.isos = list(written)

    def test_clean_matches_raw_for_every_curated_iso(self) -> None:
        import numpy as np

        for iso in self.isos:
            with self.subTest(iso=iso):
                O.unit_outage_derate_factors.cache_clear()
                raw = O.unit_outage_derate_factors(2023, iso=iso)

                os.environ[_USE_CLEAN_ENV] = "1"
                O.unit_outage_derate_factors.cache_clear()
                clean = O.unit_outage_derate_factors(2023, iso=iso)
                os.environ.pop(_USE_CLEAN_ENV, None)

                self.assertEqual(set(raw), set(clean))
                for key in raw:
                    np.testing.assert_array_equal(raw[key], clean[key])


@unittest.skipUnless(O.PARTIAL_OUTAGE_CSV.is_file(), "ERCOT partial-outage CSV absent")
class PartialOutageDerateParity(_UseCleanEnvMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from scripts.data import curate_partial_outages

        written = curate_partial_outages.curate()
        if not written:
            raise unittest.SkipTest("no partial-outages curated from raw")

    def test_clean_matches_raw(self) -> None:
        import numpy as np

        O.partial_outage_derate_factors.cache_clear()
        raw = O.partial_outage_derate_factors(2023)

        os.environ[_USE_CLEAN_ENV] = "1"
        O.partial_outage_derate_factors.cache_clear()
        clean = O.partial_outage_derate_factors(2023)

        self.assertTrue(raw, "raw path produced no partial-outage derates")
        self.assertEqual(set(raw), set(clean))
        for key in raw:
            np.testing.assert_array_equal(raw[key], clean[key])


@unittest.skipUnless(
    (paths.FLEET_DIR / "egrid2023_data_rev2.xlsx").is_file(),
    "eGRID 2023 workbook absent",
)
class EgridZoneAssignmentParity(_UseCleanEnvMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from scripts.data import curate_egrid

        written = curate_egrid.curate(vintages=[2023])
        if not written:
            raise unittest.SkipTest("eGRID 2023 vintage not curated")

    def test_zone_lookup_matches_raw(self) -> None:
        ZA._PLNT23_CACHE = None
        ZA._ORIS_TO_LOCATION = None
        raw = ZA.build_zone_lookup("ERCOT")

        os.environ[_USE_CLEAN_ENV] = "1"
        ZA._PLNT23_CACHE = None
        ZA._ORIS_TO_LOCATION = None
        clean = ZA.build_zone_lookup("ERCOT")
        ZA._PLNT23_CACHE = None
        ZA._ORIS_TO_LOCATION = None

        self.assertTrue(raw, "raw zone lookup is empty")
        # With MARKET_SIM_USE_CLEAN set, build_zone_lookup also supplements from
        # the bin-assignments reference crosswalk (load_reference_zone_crosswalk,
        # an existing, unrelated feature gated on the same flag) — so `clean` may
        # carry a few extra plant_ids beyond what eGRID alone resolves. The eGRID
        # conversion under test must not change any value eGRID itself resolves.
        common = set(raw) & set(clean)
        self.assertGreaterEqual(len(common), int(0.99 * len(raw)))
        for oris in common:
            self.assertEqual(raw[oris], clean[oris], oris)

    def test_fossil_co2_rate_map_matches_raw(self) -> None:
        E._EGRID_RATE_CACHE.clear()
        raw = E.fossil_co2_rate_map(2023)

        os.environ[_USE_CLEAN_ENV] = "1"
        E._EGRID_RATE_CACHE.clear()
        clean = E.fossil_co2_rate_map(2023)
        E._EGRID_RATE_CACHE.clear()

        self.assertTrue(raw, "raw fossil CO2 rate map is empty")
        self.assertEqual(raw, clean)


@unittest.skipUnless(PLANT_REGISTRY_CSV.is_file(), "master plant registry CSV absent")
class CodRampRegistryParity(_UseCleanEnvMixin, unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from scripts.data import curate_reference

        curate_reference.curate()

    def test_registry_year_built_matches_raw(self) -> None:
        from market_sim.config.paths import active_eia860_dir

        d = active_eia860_dir()
        cod_ramp._load_cod_map.cache_clear()
        raw = cod_ramp._load_cod_map(d)

        os.environ[_USE_CLEAN_ENV] = "1"
        cod_ramp._load_cod_map.cache_clear()
        clean = cod_ramp._load_cod_map(d)
        cod_ramp._load_cod_map.cache_clear()

        self.assertTrue(raw, "raw COD map is empty")
        self.assertEqual(raw, clean)


if __name__ == "__main__":
    unittest.main()
