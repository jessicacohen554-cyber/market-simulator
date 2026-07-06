"""Biomass injected as a measured EIA-923 must-run profile, not a dispatchable LP unit.

For every ISO the model now pins biomass to its measured EIA-923 annual+monthly
energy (vintage-carry reconciled) and injects it as a fixed must-run profile —
exactly like ERCOT — instead of leaving it as a raw LP unit the merit order runs
to max when gas rises. These tests pin the two invariants the fix must hold:

* the injected biomass equals the benchmark biomass it is scored against, and is
  a *fixed measured quantity* independent of gas price (so it cannot swing ~2x in
  a high-gas year — the NEISO 2025 over-dispatch this fixes); and
* biomass is not double-counted — the raw biomass LP units are dropped from the
  per-plant fleet when the injection is on (``fleet._drop_biomass_units``, the
  shared dispatch-fleet builder's ``drop_biomass_units`` seam since
  orchestrator-unification Stage 6), mirroring the ERCOT CAMPD path.
"""

import importlib.util
import unittest
from collections import namedtuple
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data import fleet as fleet_mod

REPO = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "rcf_bio", str(REPO / "scripts" / "run_calibration_full.py")
)
rcf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rcf)

_rc_spec = importlib.util.spec_from_file_location(
    "rc_bio", str(REPO / "scripts" / "run_calibration.py")
)
rc = importlib.util.module_from_spec(_rc_spec)
_rc_spec.loader.exec_module(rc)

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


def _gen_row(year, plant_id, prime_mover, fuel_code, annual):
    """One EIA-923 ``generation`` row (flat monthly shape)."""
    r = {
        "year": np.int16(year),
        "plant_id": plant_id,
        "prime_mover": prime_mover,
        "fuel_type": fuel_code,
        "chp": "N",
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


class TestReconciledBiomassMatchesBenchmark(unittest.TestCase):
    """Injected biomass == benchmark biomass, complete and incomplete vintages."""

    def setUp(self):
        self._orig = rcf._iso_plant_ids
        rcf._iso_plant_ids = lambda iso: frozenset({1, 2})

    def tearDown(self):
        rcf._iso_plant_ids = self._orig

    def _gen(self, year, iso_total, biomass):
        frames = []
        for y, tot, bio in (
            (year - 1, iso_total, biomass),
            (year, iso_total, biomass),
        ):
            frames.append(_gen_row(y, 1, "WT", "WND", tot - bio))
            frames.append(_gen_row(y, 2, "ST", "WDS", bio))
        return pd.DataFrame(frames)

    def test_complete_vintage_returns_raw(self):
        gen = self._gen(2024, 196.0e6, 4.0e6)  # 98% complete -> no carry
        e930 = _e930_long(2024, {"net_gen": 200.0e6})
        ann, mon = rcf._reconciled_biomass_class(2024, gen, "CAISO", e930)
        self.assertAlmostEqual(ann, 4.0e6, delta=1.0)
        self.assertAlmostEqual(float(mon.sum()), 4.0e6, delta=1.0)

    def test_incomplete_vintage_carries_prior(self):
        # Current year truncated to 70% of the grid; prior is complete.
        gen = self._gen(2025, 140.0e6, biomass=1.2e6)
        # Make the current-year biomass artificially low (truncated survey).
        gen.loc[(gen["year"] == 2025) & (gen["plant_id"] == 2), "netgen_annual_mwh"] = (
            0.5e6
        )
        for m in _MONTHS:
            gen.loc[
                (gen["year"] == 2025) & (gen["plant_id"] == 2), f"netgen_{m}_mwh"
            ] = 0.5e6 / 12.0
        e930 = _e930_long(2025, {"net_gen": 200.0e6})
        ann, _ = rcf._reconciled_biomass_class(2025, gen, "CAISO", e930)
        # Carry = prior 1.2e6 x vintage completeness (~0.70) ~ 0.84e6, which beats
        # the truncated 0.5e6 raw read, so the carried value is used.
        self.assertGreater(ann, 0.5e6)
        completeness = 139.3e6 / 200.0e6  # current-year total / EIA-930 net gen
        self.assertAlmostEqual(ann, 1.2e6 * completeness, delta=5e3)

    def test_injection_equals_benchmark_biomass(self):
        """The energy ``_must_run_profiles`` injects == the benchmark total."""
        gen = self._gen(2025, 140.0e6, biomass=1.2e6)
        e930 = _e930_long(2025, {"net_gen": 200.0e6})
        demand = np.full((1, 8760), 200.0e6 / 8760.0)
        mr = rcf._must_run_profiles(
            2025, gen, "CAISO", demand, skip_classes=frozenset(), e930=e930
        )
        self.assertIn("biomass", mr)
        injected = float(mr["biomass"].sum())
        bench, _ = rcf._reconciled_biomass_class(2025, gen, "CAISO", e930)
        self.assertAlmostEqual(injected, bench, delta=max(1.0, bench * 1e-6))

    def test_injection_is_gas_price_insensitive(self):
        """Injected biomass is a fixed measured quantity — no gas dependence.

        ``_must_run_profiles`` takes no price, so the same EIA-923 input yields the
        same biomass energy regardless of the gas year. This is what stops biomass
        swinging ~2x when gas rises (the NEISO 2025 5.28-vs-2.45 TWh over-dispatch).
        """
        gen = self._gen(2024, 196.0e6, biomass=3.0e6)
        e930 = _e930_long(2024, {"net_gen": 200.0e6})
        demand = np.full((1, 8760), 200.0e6 / 8760.0)
        a = rcf._must_run_profiles(
            2024, gen, "CAISO", demand, skip_classes=frozenset(), e930=e930
        )["biomass"].sum()
        b = rcf._must_run_profiles(
            2024, gen, "CAISO", demand, skip_classes=frozenset(), e930=e930
        )["biomass"].sum()
        self.assertEqual(float(a), float(b))
        self.assertAlmostEqual(float(a), 3.0e6, delta=1.0)


_Gen = namedtuple("_Gen", ["fuel_type", "plant_code"])


class TestDropBiomassUnits(unittest.TestCase):
    """No double-count: raw biomass LP units are removed when injection is on."""

    def test_drops_only_biomass_keeps_parallel_fracs(self):
        fleet = [
            _Gen("coal", 1),
            _Gen("biomass", 2),
            _Gen("gas_cc", 3),
            _Gen("biomass", 4),
            _Gen("nuclear", 5),
        ]
        fuel_fracs = [0.1, 0.2, 0.3, 0.4, 0.5]
        out_fleet, out_fracs = fleet_mod._drop_biomass_units(fleet, fuel_fracs)
        self.assertEqual(
            [g.fuel_type for g in out_fleet], ["coal", "gas_cc", "nuclear"]
        )
        # Fractions stay aligned to the surviving units (the 0.2 / 0.4 go too).
        self.assertEqual(out_fracs, [0.1, 0.3, 0.5])
        self.assertEqual(len(out_fleet), len(out_fracs))

    def test_noop_without_biomass(self):
        fleet = [_Gen("coal", 1), _Gen("gas_cc", 2)]
        fracs = [1.0, 2.0]
        out_fleet, out_fracs = fleet_mod._drop_biomass_units(fleet, fracs)
        self.assertEqual(len(out_fleet), 2)
        self.assertEqual(out_fracs, [1.0, 2.0])


if __name__ == "__main__":
    unittest.main()
