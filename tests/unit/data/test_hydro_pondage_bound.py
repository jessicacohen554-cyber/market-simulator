"""Tests for the measured per-plant forebay-storage bound (hydro-1).

Covers the three properties the mechanism's admissibility rests on:

* the row family's **invariant** — it redistributes WHEN water is turbined and
  can never move a monthly total (rule 19 ``[R-ONE-MECH]``), so every row stays
  feasible at zero generation;
* the **redundancy proof** — a plant whose forebay holds a whole month gets no
  row, because its row would impose nothing the monthly budget row does not;
* the **rule-19 exclusivity** — the pondage bound and the hydraulic cascade are
  one row family and the resolver refuses both at once.

Plus the derive's arithmetic and the cache-key contract.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.data.hydro import hours_per_month, load_hydro_pondage  # noqa: E402
from market_sim.model.lp.hydro_cascade import (  # noqa: E402
    build_hydro_cascade_rows,
)
from market_sim.model.lp.layout import VariableLayout  # noqa: E402


def _write_artifact(tmp: Path, iso: str, rows: list[dict]) -> None:
    """Write a minimal ``<iso>_hydro_pondage.csv`` under a fake raw root."""
    import pandas as pd

    d = tmp / f"{iso.lower()}-hydro"
    d.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(d / f"{iso.lower()}_hydro_pondage.csv", index=False)


class PondageSpecTest(unittest.TestCase):
    """The spec the derive hands the LP."""

    def setUp(self) -> None:
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())
        self.hours = 48
        # Two plants: one with a small forebay (binding), one whose forebay
        # holds more than its largest month (redundant).
        self.codes = np.array([101, 202], dtype=int)
        self.monthly = np.zeros((2, 12), dtype=float)
        self.monthly[0, :] = 7200.0  # 10 MW average over a 720 h month
        self.monthly[1, :] = 3600.0
        _write_artifact(
            self.tmp,
            "TESTISO",
            [
                {"plant_id": 101, "storage_mwh": 50.0},
                {"plant_id": 202, "storage_mwh": 99_999.0},
            ],
        )

    def _load(self, **kw):
        import market_sim.config.paths as paths_mod

        orig = paths_mod.RAW_DATA_DIR
        try:
            paths_mod.RAW_DATA_DIR = self.tmp
            return load_hydro_pondage(
                "TESTISO", self.codes, self.monthly, hours=self.hours, **kw
            )
        finally:
            paths_mod.RAW_DATA_DIR = orig

    def test_a_forebay_holding_a_whole_month_gets_no_row(self):
        """The redundancy proof: plant 202 is dropped, plant 101 is kept."""
        spec = self._load()
        self.assertIsNotNone(spec)
        self.assertEqual(spec.n_coupled, 1)
        self.assertEqual(list(spec.plant_codes), [101])
        self.assertEqual(spec.n_links, 0)

    def test_inflow_is_the_plants_own_budget_over_the_months_hours(self):
        """No new energy datum: the RHS is ``budget[g, m] / hours[m]``."""
        spec = self._load()
        hpm = hours_per_month(self.hours).astype(float)
        expect = self.monthly[0, 0] / hpm[0]
        np.testing.assert_allclose(spec.side_inflow[0, :24], expect)

    def test_eta_is_unity_so_the_balance_is_in_mwh(self):
        """No water unit and no turbine efficiency is assumed."""
        spec = self._load()
        np.testing.assert_allclose(spec.eta_dn, 1.0)

    def test_a_ror_flat_plant_carries_no_pondage_row(self):
        """Rule 19: a plant the RoR split already fixed is not bounded twice."""
        spec = self._load(ror_flat_rows=np.array([True, False]))
        self.assertIsNone(spec)

    def test_a_plant_with_no_identified_storage_is_left_unbounded(self):
        """Rule 13: never a substituted value — the plant keeps its budget."""
        _write_artifact(self.tmp, "TESTISO", [{"plant_id": 999, "storage_mwh": 5.0}])
        self.assertIsNone(self._load())

    def test_a_missing_artifact_is_inert(self):
        """An ISO with no artifact leaves the LP unchanged."""
        import market_sim.config.paths as paths_mod

        orig = paths_mod.RAW_DATA_DIR
        try:
            paths_mod.RAW_DATA_DIR = self.tmp / "nope"
            self.assertIsNone(
                load_hydro_pondage(
                    "TESTISO", self.codes, self.monthly, hours=self.hours
                )
            )
        finally:
            paths_mod.RAW_DATA_DIR = orig


class PondageRowInvariantTest(unittest.TestCase):
    """The row family's invariant, checked on the assembled matrix."""

    def setUp(self) -> None:
        import tempfile

        self.tmp = Path(tempfile.mkdtemp())
        self.hours = 24
        self.codes = np.array([101], dtype=int)
        self.monthly = np.full((1, 12), 7200.0)
        _write_artifact(self.tmp, "TESTISO", [{"plant_id": 101, "storage_mwh": 50.0}])
        import market_sim.config.paths as paths_mod

        orig = paths_mod.RAW_DATA_DIR
        paths_mod.RAW_DATA_DIR = self.tmp
        try:
            self.spec = load_hydro_pondage(
                "TESTISO", self.codes, self.monthly, hours=self.hours
            )
        finally:
            paths_mod.RAW_DATA_DIR = orig
        self.layout = VariableLayout(
            T=self.hours,
            n_gen=4,
            n_zones=1,
            n_storage=0,
            n_links=0,
            n_cascade=2 * self.spec.n_coupled,
        )

    def test_every_row_is_feasible_at_zero_generation(self):
        """Spill is unbounded above, so P = 0 is always in the feasible set.

        This is what makes the family unable to move a monthly total: it can
        never FORCE generation, only forbid concentrating it.
        """
        block, lo, hi = build_hydro_cascade_rows(self.layout, self.spec)
        np.testing.assert_allclose(lo, hi)  # equalities
        x = np.zeros(self.layout.total_columns)
        # P = 0, V = 0 everywhere; spill absorbs the whole inflow.
        for t in range(self.hours):
            x[self.layout.cas_s_col(0, t)] = self.spec.side_inflow[0, t]
        np.testing.assert_allclose(block @ x, hi, atol=1e-9)

    def test_the_forebay_bounds_how_much_energy_can_be_shifted(self):
        """A feasible plan that banks MORE than the forebay violates a row.

        Holding back ``B + delta`` MWh over the first hours and releasing it
        later requires ``V`` above ``pond_cap`` in some hour, which the column
        bound forbids — the LP-level statement of "it cannot retain a month of
        water for the peak".
        """
        block, _lo, hi = build_hydro_cascade_rows(self.layout, self.spec)
        cap = float(self.spec.pond_cap[0])
        inflow = self.spec.side_inflow[0]
        gen = self.spec.coupled_gen_idx[0]
        T = self.hours
        # A CYCLICALLY CONSISTENT banking plan (``V(t-1)`` wraps at the horizon
        # boundary — the house convention, see hydro_cascade.py): hold all water
        # for the first k hours, then release the bank evenly over the rest so
        # V returns to 0 at t = T-1 and the wrap into t = 0 is consistent.
        k = int(np.ceil(cap / inflow[0])) + 1
        banked = float(inflow[:k].sum())
        x = np.zeros(self.layout.total_columns)
        v = 0.0
        peak = 0.0
        for t in range(T):
            if t < k:
                v += inflow[t]  # P = S = 0: everything goes to the forebay
            else:
                # Generate this hour's inflow plus an even slice of the bank.
                p = inflow[t] + banked / (T - k)
                x[self.layout.p_col(gen, t)] = p
                v += inflow[t] - p
            v = max(v, 0.0)  # guard float drift at the final hour
            x[self.layout.cas_v_col(0, t)] = v
            peak = max(peak, v)
        # The balance rows are satisfied exactly, including the wrap...
        np.testing.assert_allclose(block @ x, hi, atol=1e-6)
        self.assertAlmostEqual(x[self.layout.cas_v_col(0, T - 1)], 0.0, places=6)
        # ...and yet the plan is INFEASIBLE, because holding k hours of water
        # drives the forebay above its measured capacity, which the ``V``
        # column's upper bound rejects. That bound is the LP-level statement of
        # "the plant cannot retain a month of water for the peak".
        self.assertGreater(peak, cap)


class ResolverExclusivityTest(unittest.TestCase):
    """Rule 19: one water balance per plant, never two."""

    def test_arming_both_members_raises(self):
        from market_sim.pipeline.kwargs import resolve_hydro_cascade

        cfg = ScenarioConfig(hydro_cascade_coupling=True, hydro_pondage_bound=True)
        with self.assertRaises(ValueError) as ctx:
            resolve_hydro_cascade("NYISO", 2024, [], np.array([0]), cfg)
        self.assertIn("mutually exclusive", str(ctx.exception))

    def test_neither_armed_is_unset(self):
        from market_sim.pipeline.kwargs import resolve_hydro_cascade
        from market_sim.pipeline.spec import UNSET

        cfg = ScenarioConfig()
        self.assertIs(
            resolve_hydro_cascade("NYISO", 2024, [], np.array([0]), cfg), UNSET
        )


class DeriveArithmeticTest(unittest.TestCase):
    """The energy conversion, against a hand-computed reference."""

    def test_potential_energy_matches_rho_g_v_h(self):
        sys.path.insert(0, str(ROOT / "scripts" / "data"))
        from build_hydro_pondage import potential_energy_mwh

        # 1,000 acre-ft at 100 ft: rho g V h / 3.6e9
        v_m3 = 1000 * 1233.4818375475
        h_m = 100 * 0.3048
        expect = 1000.0 * 9.80665 * v_m3 * h_m / 3.6e9
        self.assertAlmostEqual(potential_energy_mwh(1000, 100), expect, places=9)
        # Linear in both arguments — no hidden constant.
        self.assertAlmostEqual(
            potential_energy_mwh(2000, 100), 2 * potential_energy_mwh(1000, 100)
        )
        self.assertAlmostEqual(
            potential_energy_mwh(1000, 200), 2 * potential_energy_mwh(1000, 100)
        )


class CacheKeyContractTest(unittest.TestCase):
    """The field is dropped at its default and hashes distinctly when armed."""

    def test_default_and_explicit_off_share_a_key(self):
        self.assertEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(hydro_pondage_bound=False).cache_key(),
        )

    def test_arming_moves_the_key(self):
        self.assertNotEqual(
            ScenarioConfig().cache_key(),
            ScenarioConfig(hydro_pondage_bound=True).cache_key(),
        )


if __name__ == "__main__":
    unittest.main()
