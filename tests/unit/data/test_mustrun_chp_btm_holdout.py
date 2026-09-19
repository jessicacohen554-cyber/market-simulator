"""Host-steam / behind-the-meter partition of the INJECTED must-run classes.

``ScenarioConfig.mustrun_chp_btm_holdout`` (miso-253) drops rows carrying the
published EIA-923 CHP flag from the two injected residual classes (``biomass``
and ``OTHER``) at the single ``_eia923_frame`` seam. These tests pin the four
properties the mechanism's admissibility rests on:

* **byte-identical off** — the default path is untouched, so every keeper
  replays unchanged (rule 24 ``[R-REGISTRY]``);
* **scoped to the injected classes** — a gas / coal cogen row is NOT dropped,
  because those classes already carry their own host-steam partition
  (``classify_plant``'s ``*_CHP`` split plus ``data.chp.chp_btm_pct``), and
  stacking a second one would breach rule 19 ``[R-ONE-MECH]``;
* **row grain, not plant grain** — a mill reporting a ``chp=Y`` recovery boiler
  and a ``chp=N`` grid unit under one plant code keeps the grid unit; and
* **bench and injection move in lockstep** — both read the same seam, so the
  partition can never manufacture a benchmark miss (which is also why biomass
  stays self-scored; see the module docstring of
  ``docs/FINDING-miso252-biomass-selfscored-and-the-lp-memory-ceiling-2026-09-10.md``
  §2, a gap this flag deliberately does not close).
"""

import importlib.util
import unittest

import numpy as np
import pandas as pd

from tests.helpers import REPO_ROOT

REPO = REPO_ROOT
_spec = importlib.util.spec_from_file_location(
    "rcf_btm", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_MONTHS = [
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
]


def _gen_row(year, plant_id, prime_mover, fuel_code, annual, chp="N"):
    """One EIA-923 ``generation`` row (flat monthly shape)."""
    r = {
        "year": np.int16(year),
        "plant_id": plant_id,
        "prime_mover": prime_mover,
        "fuel_type": fuel_code,
        "chp": chp,
        "netgen_annual_mwh": float(annual),
    }
    r.update({f"netgen_{m}_mwh": annual / 12.0 for m in _MONTHS})
    return r


def _e930_long(year, series_totals):
    rows = []
    for series, annual in series_totals.items():
        per_hour = annual / 8760.0
        for h in range(8760):
            rows.append((year, series, h, per_hour))
    return pd.DataFrame(rows, columns=["year", "series", "hour", "mw"])


# Plant ids used by the fixtures below:
#   1  wind, the ISO's bulk energy so the vintage reads complete
#   2  WDS biomass, chp=N   -> grid biomass, always kept
#   3  BLQ biomass, chp=Y   -> paper-mill recovery boiler, dropped when armed
#   4  BFG OTHER,   chp=Y   -> steel-mill blast-furnace gas, dropped when armed
#   5  LFG biomass, chp=N + WDS biomass chp=Y at ONE plant (the row-grain case)
#   6  NG CC,       chp=Y   -> CC_CHP, NEVER dropped (already partitioned)
_ALL_PLANTS = frozenset({1, 2, 3, 4, 5, 6})


class _IsoPlantPatch(unittest.TestCase):
    def setUp(self):
        self._orig = rcf._iso_plant_ids
        # spp-49 widened the seam to (iso, year, vintage_union); the
        # patch absorbs the extra arguments so this fixture keeps
        # pinning the partition and nothing else.
        rcf._iso_plant_ids = lambda iso, *_a, **_kw: _ALL_PLANTS

    def tearDown(self):
        rcf._iso_plant_ids = self._orig


def _fixture(year, *, bulk=196.0e6):
    """Two vintages of the fleet above, so the prior-year carry has a source."""
    frames = []
    for y in (year - 1, year):
        frames += [
            _gen_row(y, 1, "WT", "WND", bulk),
            _gen_row(y, 2, "ST", "WDS", 2.0e6, chp="N"),
            _gen_row(y, 3, "ST", "BLQ", 3.0e6, chp="Y"),
            _gen_row(y, 4, "ST", "BFG", 4.0e6, chp="Y"),
            _gen_row(y, 5, "IC", "LFG", 0.5e6, chp="N"),
            _gen_row(y, 5, "ST", "WDS", 1.5e6, chp="Y"),
            _gen_row(y, 6, "CA", "NG", 9.0e6, chp="Y"),
        ]
    return pd.DataFrame(frames)


class TestFrameFilter(_IsoPlantPatch):
    """The seam itself: which rows the partition removes, and which it keeps."""

    def test_off_is_byte_identical(self):
        gen = _fixture(2024)
        a = rcf._eia923_frame(2024, gen, "MISO")
        b = rcf._eia923_frame(2024, gen, "MISO", False)
        pd.testing.assert_frame_equal(a, b)

    def test_armed_drops_only_chp_rows_of_injected_classes(self):
        gen = _fixture(2024)
        off = rcf._eia923_frame(2024, gen, "MISO")
        on = rcf._eia923_frame(2024, gen, "MISO", True)

        def _tot(frame, klass):
            return float(frame.loc[frame["klass"] == klass, "annual_mwh"].sum())

        # biomass: 2.0 (chp=N) + 3.0 (chp=Y) + 0.5 (chp=N) + 1.5 (chp=Y) = 7.0
        self.assertAlmostEqual(_tot(off, "biomass"), 7.0e6, delta=1.0)
        # armed keeps only the two chp=N rows
        self.assertAlmostEqual(_tot(on, "biomass"), 2.5e6, delta=1.0)
        # OTHER: the whole 4.0 TWh BFG block is chp=Y
        self.assertAlmostEqual(_tot(off, "OTHER"), 4.0e6, delta=1.0)
        self.assertAlmostEqual(_tot(on, "OTHER"), 0.0, delta=1.0)

    def test_gas_chp_is_never_touched(self):
        """Rule 19 [R-ONE-MECH]: CC_CHP already carries a host-steam partition."""
        gen = _fixture(2024)
        off = rcf._eia923_frame(2024, gen, "MISO")
        on = rcf._eia923_frame(2024, gen, "MISO", True)
        for frame in (off, on):
            self.assertAlmostEqual(
                float(frame.loc[frame["klass"] == "CC_CHP", "annual_mwh"].sum()),
                9.0e6,
                delta=1.0,
            )

    def test_partition_is_row_grain_not_plant_grain(self):
        """Plant 5 reports both a chp=N genset and a chp=Y boiler."""
        gen = _fixture(2024)
        on = rcf._eia923_frame(2024, gen, "MISO", True)
        kept = on[(on["plant_id"] == 5) & (on["klass"] == "biomass")]
        self.assertEqual(len(kept), 1)
        # only the 0.5 TWh chp=N landfill-gas row survives at that plant
        self.assertAlmostEqual(float(kept["annual_mwh"].sum()), 0.5e6, delta=1.0)

    def test_monthly_shape_is_partitioned_with_the_annual(self):
        gen = _fixture(2024)
        on = rcf._eia923_frame(2024, gen, "MISO", True)
        bio = on[on["klass"] == "biomass"]
        mcols = [f"m{i:02d}" for i in range(1, 13)]
        self.assertAlmostEqual(
            float(bio[mcols].to_numpy().sum()),
            float(bio["annual_mwh"].sum()),
            delta=1.0,
        )


class TestInjectionAndBenchMoveTogether(_IsoPlantPatch):
    """One seam feeds both, so the partition cannot manufacture a miss."""

    def _injected(self, gen, year, armed):
        demand = np.full((1, 8760), 200.0e6 / 8760.0)
        e930 = _e930_long(year, {"net_gen": 200.0e6})
        return rcf._must_run_profiles(
            year,
            gen,
            "MISO",
            demand,
            skip_classes=frozenset(),
            e930=e930,
            mustrun_chp_btm_holdout=armed,
        )

    def test_injection_equals_reconciled_class_both_ways(self):
        gen = _fixture(2024)
        e930 = _e930_long(2024, {"net_gen": 200.0e6})
        for armed, expected in ((False, 7.0e6), (True, 2.5e6)):
            mr = self._injected(gen, 2024, armed)
            injected = float(mr["biomass"].sum())
            bench, _ = rcf._reconciled_mustrun_class(
                "biomass", 2024, gen, "MISO", e930, armed
            )
            self.assertAlmostEqual(injected, bench, delta=max(1.0, bench * 1e-6))
            self.assertAlmostEqual(injected, expected, delta=1.0)

    def test_injection_is_strictly_reduced_by_the_partition(self):
        gen = _fixture(2024)
        off = self._injected(gen, 2024, False)
        on = self._injected(gen, 2024, True)
        for klass in ("biomass", "OTHER"):
            off_e = float(off.get(klass, np.zeros(1)).sum())
            on_e = float(on.get(klass, np.zeros(1)).sum())
            self.assertLessEqual(on_e, off_e)
        # OTHER is entirely chp=Y here, so the class drops out of the injection
        self.assertNotIn("OTHER", on)

    def test_benchmark_frame_carries_the_same_partition(self):
        gen = _fixture(2024)
        e930 = _e930_long(2024, {"net_gen": 200.0e6})
        off = rcf._benchmark_eia923_frame(2024, gen, "MISO", None, {}, e930)
        on = rcf._benchmark_eia923_frame(
            2024, gen, "MISO", None, {}, e930, mustrun_chp_btm_holdout=True
        )

        def _tot(frame, klass):
            return float(frame.loc[frame["klass"] == klass, "annual_mwh"].sum())

        self.assertAlmostEqual(_tot(off, "biomass"), 7.0e6, delta=1.0)
        self.assertAlmostEqual(_tot(on, "biomass"), 2.5e6, delta=1.0)


class TestVintageCarryUsesThePartitionedBasis(_IsoPlantPatch):
    """An incomplete vintage carries the PARTITIONED prior year, not the raw one."""

    def test_carry_is_partitioned(self):
        # Current year truncated: the ISO reads ~70% complete, so the carry fires.
        gen = _fixture(2025, bulk=136.0e6)
        for pid in (2, 3, 4, 5):
            mask = (gen["year"] == 2025) & (gen["plant_id"] == pid)
            gen.loc[mask, "netgen_annual_mwh"] = 0.0
            for m in _MONTHS:
                gen.loc[mask, f"netgen_{m}_mwh"] = 0.0
        e930 = _e930_long(2025, {"net_gen": 200.0e6})
        ann_off, _ = rcf._reconciled_mustrun_class(
            "biomass", 2025, gen, "MISO", e930, False
        )
        ann_on, _ = rcf._reconciled_mustrun_class(
            "biomass", 2025, gen, "MISO", e930, True
        )
        # Both carry; the armed carry is scaled off the 2.5 TWh partitioned prior
        # rather than the 7.0 TWh raw one, so it is strictly smaller and their
        # ratio is the partition's own ratio.
        self.assertGreater(ann_off, 0.0)
        self.assertGreater(ann_on, 0.0)
        self.assertLess(ann_on, ann_off)
        self.assertAlmostEqual(ann_on / ann_off, 2.5 / 7.0, places=6)


class TestConfigRegistration(unittest.TestCase):
    """Rule 24 [R-REGISTRY] + the cache-key declaration (the nyiso-119 discipline)."""

    def test_field_exists_and_defaults_off(self):
        from market_sim.config.scenarios import ScenarioConfig

        self.assertFalse(ScenarioConfig().mustrun_chp_btm_holdout)

    def test_declared_in_the_optional_cache_key_fields(self):
        from market_sim.config import scenarios as sc

        self.assertIn("mustrun_chp_btm_holdout", sc._CACHE_KEY_OPTIONAL_FIELDS)
        self.assertEqual(
            sc._CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["mustrun_chp_btm_holdout"],
            "False",
        )

    def test_default_cache_key_is_unmoved_by_the_new_field(self):
        """Dropped at its False default, so every pre-existing key stays valid."""
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig()
        self.assertEqual(
            base.cache_key(),
            base.with_overrides(mustrun_chp_btm_holdout=False).cache_key(),
        )

    def test_armed_config_hashes_distinctly(self):
        from market_sim.config.scenarios import ScenarioConfig

        base = ScenarioConfig()
        self.assertNotEqual(
            base.cache_key(),
            base.with_overrides(mustrun_chp_btm_holdout=True).cache_key(),
        )


if __name__ == "__main__":
    unittest.main()
