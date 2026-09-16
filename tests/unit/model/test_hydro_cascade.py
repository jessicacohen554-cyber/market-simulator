"""Tests for the hydraulic-cascade coupling rows (NWPP-36, owner ruling N3).

Two tiers, per the Testing Pattern (trivial case first, then scale):

* :class:`TestTrivialLink` — 1 zone, 1 link, 24 h: the OFF-identity guard
  (G-A6), the rule-19 invariant that the coupling never moves a monthly total
  (G-A1), the water-balance identity (G-A2) and the lag signature (G-A5).
* :class:`TestColumbiaChainReduced` — the REAL measured chain from the
  committed NWPP-36 artifact on a one-zone reduced system for January 2023
  (low flow, the rows bind) and May 2023 (the freshet, the spill object must
  appear), each solved OFF and ON, against the PRECOMMIT §7 gates G-A1..G-A5.
  Needs ``data/raw/nwpp-hydro`` and the EIA-930 BPAT extract (``fulldata``).

Every gate here is STRUCTURAL: it asks whether the mechanism does what its
own arithmetic says, never whether a residual moved (rule 29 ``[R-SCREEN]``).
"""

from __future__ import annotations

import unittest

import numpy as np
import pytest

from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import (
    HydroCascadeSpec,
    VariableLayout,
    build_constraints,
    build_cost_vector,
    build_variable_bounds,
    solve_dispatch,
)
from tests.helpers import REPO_ROOT

HYDRO_DIR = REPO_ROOT / "data" / "raw" / "nwpp-hydro"
BPAT_930 = REPO_ROOT / "data" / "raw" / "eia-930-hourly" / "BPAT hourly.parquet"


def _gen(uid, fuel, pmax, plant_code=0):
    return Generator(
        unit_id=uid,
        name=uid,
        zone="Z",
        fuel_type=fuel,
        pmax_mw=pmax,
        pmin_mw=0.0,
        eford=0.0,
        plant_code=plant_code,
    )


def _one_link_spec(T, tau=2, pond=50.0, eta=1.0):
    """Head H (gen 0) -> coupled D (gen 1); eta flat; no side inflow, no head spill."""
    return HydroCascadeSpec(
        coupled_gen_idx=np.array([1]),
        eta_dn=np.full((1, T), eta),
        pond_cap=np.array([pond]),
        side_inflow=np.zeros((1, T)),
        link_dn_local=np.array([0]),
        link_up_gen_idx=np.array([0]),
        link_up_local=np.array([-1]),
        link_tau=np.array([tau]),
        link_eta_up=np.full((1, T), eta),
        link_head_flow=np.zeros((1, T)),
        plant_codes=np.array([2]),
    )


def _lagged_corr(x, y, tau):
    """Pearson r of ``y(t)`` against ``x(t - tau)`` (cyclic)."""
    xs = np.roll(x, tau)
    if np.std(xs) == 0 or np.std(y) == 0:
        return 0.0
    return float(np.corrcoef(xs, y)[0, 1])


class TestTrivialLink(unittest.TestCase):
    """1 zone, 1 link, 24 h — the trivial case."""

    def setUp(self):
        self.T = 24
        gens = [
            _gen("H", "hydro", 100.0, 1),
            _gen("D", "hydro", 100.0, 2),
            _gen("C", "gas_cc", 400.0),
            _gen("E", "gas_ct", 400.0),
        ]
        self.fleet = generators_to_fleet_arrays(gens, ["Z"], hours=self.T)
        demand = np.full(self.T, 150.0)
        demand[16:20] = 420.0  # evening peak: peaker sets the price
        self.demand = demand[None, :]
        self.mc = np.vstack(
            [
                np.zeros(self.T),
                np.zeros(self.T),
                np.full(self.T, 20.0),
                np.full(self.T, 100.0),
            ]
        )
        self.month_idx = np.zeros(self.T, dtype=int)
        self.budget = np.array([[800.0], [600.0]])  # H, D: single-month caps
        self.zero_cf = np.zeros((1, self.T))
        self.zero_cap = np.zeros(1)

    def _solve(self, spec=None):
        kw = dict(hydro_cascade=spec) if spec is not None else {}
        return solve_dispatch(
            self.fleet,
            self.demand,
            self.zero_cf,
            self.zero_cap,
            self.zero_cf,
            self.zero_cap,
            mc=self.mc,
            voll=5000.0,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_gen_idx=np.array([0, 1]),
            **kw,
        )

    def test_off_identity_g_a6(self):
        """spec=None and no kwarg assemble byte-identical A, bounds and cost."""
        layout = VariableLayout(n_gen=4, n_zones=1, n_storage=0, n_links=0, T=self.T)
        a0, lo0, hi0, *_ = build_constraints(
            layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_gen_idx=np.array([0, 1]),
        )
        a1, lo1, hi1, *_ = build_constraints(
            layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_gen_idx=np.array([0, 1]),
            hydro_cascade=None,
        )
        self.assertEqual(a0.shape, a1.shape)
        np.testing.assert_array_equal(a0.indptr, a1.indptr)
        np.testing.assert_array_equal(a0.indices, a1.indices)
        np.testing.assert_array_equal(a0.data, a1.data)
        np.testing.assert_array_equal(lo0, lo1)
        np.testing.assert_array_equal(hi0, hi1)
        b0 = build_variable_bounds(
            layout, self.fleet, self.zero_cf, self.zero_cap, self.zero_cf, self.zero_cap
        )
        b1 = build_variable_bounds(
            layout,
            self.fleet,
            self.zero_cf,
            self.zero_cap,
            self.zero_cf,
            self.zero_cap,
            hydro_cascade_pond_cap=None,
        )
        np.testing.assert_array_equal(b0[0], b1[0])
        np.testing.assert_array_equal(b0[1], b1[1])
        c0 = build_cost_vector(layout, self.mc, 5000.0)
        self.assertEqual(layout.n_cascade, 0)
        self.assertEqual(c0.size, layout.total_columns)

    def test_armed_adds_two_columns_and_one_row_per_coupled_plant_hour(self):
        spec = _one_link_spec(self.T)
        layout = VariableLayout(
            n_gen=4, n_zones=1, n_storage=0, n_links=0, T=self.T, n_cascade=2
        )
        base = VariableLayout(n_gen=4, n_zones=1, n_storage=0, n_links=0, T=self.T)
        self.assertEqual(layout.vars_per_hour, base.vars_per_hour + 2)
        a_on, lo, hi, *_ = build_constraints(
            layout,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_gen_idx=np.array([0, 1]),
            hydro_cascade=spec,
        )
        a_off, *_ = build_constraints(
            base,
            self.fleet,
            self.demand,
            hydro_monthly_energy=self.budget,
            hydro_month_index=self.month_idx,
            hydro_gen_idx=np.array([0, 1]),
        )
        self.assertEqual(a_on.shape[0], a_off.shape[0] + self.T)
        # The cascade rows are equalities with RHS = side inflow (+ head flow) = 0 here.
        np.testing.assert_array_equal(lo[-self.T :], hi[-self.T :])
        np.testing.assert_array_equal(lo[-self.T :], np.zeros(self.T))

    def test_monthly_energy_unchanged_g_a1(self):
        """Rule 19: the coupling never changes HOW MUCH per month."""
        off = self._solve()
        on = self._solve(_one_link_spec(self.T))
        for g in (0, 1):
            self.assertAlmostEqual(off.dispatch[g].sum(), self.budget[g, 0], places=4)
            self.assertAlmostEqual(on.dispatch[g].sum(), self.budget[g, 0], places=4)
        self.assertEqual(on.status, "Optimal")

    def test_water_balance_identity_g_a2(self):
        spec = _one_link_spec(self.T, tau=2, pond=50.0)
        on = self._solve(spec)
        h = on.dispatch[0]
        d = on.dispatch[1]
        s = on.hydro_cascade_spill[0]
        v = on.hydro_cascade_storage[0]
        arrivals = np.roll(h, 2)  # H(t-2), cyclic
        v_prev = np.roll(v, 1)
        resid = d + s + v - v_prev - arrivals
        np.testing.assert_allclose(resid, 0.0, atol=1e-6)
        self.assertTrue(np.all(d <= arrivals + v_prev + 1e-6))
        self.assertTrue(np.all(v <= 50.0 + 1e-6))
        self.assertTrue(np.all(s >= -1e-9))
        self.assertEqual(on.hydro_cascade_water_value.shape, (1, self.T))
        np.testing.assert_array_equal(on.hydro_cascade_plant_codes, [2])

    def test_lag_signature_g_a5(self):
        """ON, D follows H two hours later; OFF it is free to peak on its own."""
        off = self._solve()
        on = self._solve(_one_link_spec(self.T, tau=2, pond=5.0))
        r_on = _lagged_corr(on.dispatch[0], on.dispatch[1], 2)
        r_off = _lagged_corr(off.dispatch[0], off.dispatch[1], 2)
        # The PRECOMMIT §7 G-A5 form: higher ON than OFF (and clearly positive —
        # a 5 kcfs·h pond lets D deviate from H's lagged shape only marginally).
        self.assertGreater(r_on, r_off)
        self.assertGreater(r_on, 0.5)

    def test_zero_downstream_budget_stays_feasible(self):
        """Spill is unbounded above, so the rows can never make the LP infeasible."""
        self.budget = np.array([[800.0], [0.0]])
        on = self._solve(_one_link_spec(self.T))
        self.assertEqual(on.status, "Optimal")
        self.assertAlmostEqual(on.dispatch[1].sum(), 0.0, places=6)
        self.assertAlmostEqual(on.hydro_cascade_spill[0].sum(), 800.0, places=4)


# --------------------------------------------------------------------------- #
# The real chain, reduced system
# --------------------------------------------------------------------------- #
CHAIN_CODES = [
    6163,
    3921,
    3886,
    3883,
    6200,
    3888,
    3887,
    3084,
    3082,
    3895,
    3075,
    840,
    6175,
    3926,
    3927,
    3925,
]
STATION_OF = {
    6163: "GCL",
    3921: "CHJ",
    3886: "WEL",
    3883: "RRH",
    6200: "RIS",
    3888: "WAN",
    3887: "PRD",
    3084: "MCN",
    3082: "JDA",
    3895: "TDA",
    3075: "BON",
    840: "DWR",
    6175: "LWG",
    3926: "LGS",
    3927: "LMN",
    3925: "IHR",
}
# Run-of-river members of the coupled set (PRECOMMIT §7 G-A3's plant list,
# restricted to the plants the measurement actually coupled).
ROR = {3921, 6200, 3084, 3082, 3895, 3075, 6175, 3926, 3927, 3925}
MONTH_HOURS = {1: (0, 744), 5: (2880, 3624)}
HYDRO_SHARE = 0.55  # the chain's measured share of NWPP-NW energy (NWPP-32 §5(a))


def _slice_spec(spec, h0, h1):
    """Restrict a full-year spec to hours [h0, h1) (lags wrap inside the window)."""
    from dataclasses import replace

    return replace(
        spec,
        eta_dn=spec.eta_dn[:, h0:h1],
        side_inflow=spec.side_inflow[:, h0:h1],
        link_eta_up=spec.link_eta_up[:, h0:h1],
        link_head_flow=spec.link_head_flow[:, h0:h1],
    )


@pytest.mark.fulldata
@pytest.mark.skipif(
    not (HYDRO_DIR / "nwpp_hydro_cascade_links.csv").exists() or not BPAT_930.exists(),
    reason="needs the NWPP-36 cascade artifact and the EIA-930 BPAT extract",
)
class TestColumbiaChainReduced(unittest.TestCase):
    """PRECOMMIT §7: the real chain on a one-zone reduced system, OFF vs ON."""

    @classmethod
    def setUpClass(cls):
        import pandas as pd

        from market_sim.data.hydro import load_hydro_cascade

        cls.pd = pd
        b = pd.read_parquet(HYDRO_DIR / "nwpp_hydro_budget.parquet")
        b = b[(b["year"] == 2023) & b["plant_id"].isin(CHAIN_CODES)].set_index(
            "plant_id"
        )
        cls.budget_2023 = b
        cls.nameplate = {int(p): float(b.loc[p, "max_mw"]) for p in CHAIN_CODES}
        cls.spec_full = load_hydro_cascade("NWPP", 2023, CHAIN_CODES)
        cls.monthly = pd.read_csv(HYDRO_DIR / "nwpp_hydro_cascade_monthly.csv")
        cls.links = pd.read_csv(HYDRO_DIR / "nwpp_hydro_cascade_links.csv")
        d = pd.read_parquet(BPAT_930)
        lt = pd.to_datetime(d["Local time"])
        d = d[lt.dt.year == 2023].sort_values("Local time")
        cls.bpat_demand_2023 = d["Demand"].to_numpy(dtype=float)
        cls.results = {}
        for m in (1, 5):
            cls.results[m] = cls._solve_month(m)

    @classmethod
    def _solve_month(cls, month):
        h0, h1 = MONTH_HOURS[month]
        T = h1 - h0
        gens = [_gen(f"{c}_hydro", "hydro", cls.nameplate[c], c) for c in CHAIN_CODES]
        gens += [
            _gen("CC", "gas_cc", 30000.0),
            _gen("CT", "gas_ct", 30000.0),
            _gen("PK", "gas_ct", 30000.0),
        ]
        fleet = generators_to_fleet_arrays(gens, ["Z"], hours=T)
        n_h = len(CHAIN_CODES)
        budget = np.array(
            [[float(cls.budget_2023.loc[c, f"m{month:02d}"])] for c in CHAIN_CODES]
        )
        shape = cls.bpat_demand_2023[h0:h1]
        shape = np.where(np.isfinite(shape), shape, np.nanmean(shape))
        demand = (shape / shape.mean()) * (budget.sum() / HYDRO_SHARE / T)
        mc = np.vstack(
            [
                np.zeros((n_h, T)),
                np.full((1, T), 30.0),
                np.full((1, T), 80.0),
                np.full((1, T), 200.0),
            ]
        )
        spec = _slice_spec(cls.spec_full, h0, h1)
        common = dict(
            mc=mc,
            voll=5000.0,
            hydro_monthly_energy=budget,
            hydro_month_index=np.zeros(T, dtype=int),
            hydro_gen_idx=np.arange(n_h),
        )
        zc, zk = np.zeros((1, T)), np.zeros(1)
        off = solve_dispatch(fleet, demand[None, :], zc, zk, zc, zk, **common)
        on = solve_dispatch(
            fleet, demand[None, :], zc, zk, zc, zk, hydro_cascade=spec, **common
        )
        return dict(off=off, on=on, spec=spec, budget=budget, T=T, demand=demand)

    def _arrivals(self, res):
        """Recompute each coupled plant's hourly arrivals from the solved columns."""
        spec, on, T = res["spec"], res["on"], res["T"]
        t = np.arange(T)
        arr = spec.side_inflow.copy()
        for ln in range(spec.n_links):
            d = int(spec.link_dn_local[ln])
            tl = (t - int(spec.link_tau[ln])) % T
            u = int(spec.link_up_gen_idx[ln])
            if u >= 0:
                arr[d] += on.dispatch[u][tl] / spec.link_eta_up[ln][tl]
            ul = int(spec.link_up_local[ln])
            if ul >= 0:
                arr[d] += on.hydro_cascade_spill[ul][tl]
            arr[d] += spec.link_head_flow[ln][tl]
        return arr

    def _amplitude(self, x):
        d = x.reshape(-1, 24)
        mean = d.mean(axis=1)
        ok = mean > 1e-6
        return (
            float(np.mean((d.max(axis=1) - d.min(axis=1))[ok] / mean[ok]))
            if ok.any()
            else 0.0
        )

    def test_g_a1_monthly_energy_unchanged(self):
        for m, res in self.results.items():
            spec = res["spec"]
            for c, g in enumerate(spec.coupled_gen_idx):
                e_off = res["off"].dispatch[g].sum()
                e_on = res["on"].dispatch[g].sum()
                self.assertLessEqual(
                    abs(e_on - e_off),
                    0.005 * max(e_off, 1.0),
                    f"month {m} plant {spec.plant_codes[c]}: {e_off:.0f} -> {e_on:.0f}",
                )

    def test_g_a2_identity_holds(self):
        for m, res in self.results.items():
            spec, on, T = res["spec"], res["on"], res["T"]
            arr = self._arrivals(res)
            for c, g in enumerate(spec.coupled_gen_idx):
                turb = on.dispatch[g] / spec.eta_dn[c]
                v = on.hydro_cascade_storage[c]
                v_prev = np.roll(v, 1)
                resid = turb + on.hydro_cascade_spill[c] + v - v_prev - arr[c]
                np.testing.assert_allclose(
                    resid,
                    0.0,
                    atol=1e-5,
                    err_msg=f"month {m} plant {spec.plant_codes[c]}",
                )
                self.assertTrue(np.all(turb <= arr[c] + v_prev + 1e-6))

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "PRECOMMIT-nwpp-36 §7 G-A3 FAILS AS PRE-REGISTERED and is reported at full "
            "magnitude (FINDING-nwpp-36 §5): a coupled plant inherits its UPSTREAM's "
            "hourly shape (Chief Joseph locks to Grand Coulee at tau = 0, r > 0.99), so "
            "its within-day amplitude falls only 1-10 %, not >= 30 %, and its peak follows "
            "the upstream's peak rather than the flat-arrivals bound eta*(mean arrivals + "
            "B). The gate's premise (flat arrivals) was wrong, not the identity (G-A2 holds "
            "to 1e-5). strict: if this ever passes, the measured chain changed — re-read."
        ),
    )
    def test_g_a3_low_flow_amplitude_and_peak_bound(self):
        res = self.results[1]
        spec = res["spec"]
        arr = self._arrivals(res)
        reductions = []
        for c, g in enumerate(spec.coupled_gen_idx):
            if int(spec.plant_codes[c]) not in ROR:
                continue
            a_off = self._amplitude(res["off"].dispatch[g])
            a_on = self._amplitude(res["on"].dispatch[g])
            reductions.append((a_off - a_on) / a_off if a_off > 0 else 0.0)
            # One-hour draw bound: eta * (mean arrivals + B_d / 1 h).
            bound = spec.eta_dn[c].max() * (arr[c].mean() + spec.pond_cap[c])
            self.assertLessEqual(res["on"].dispatch[g].max(), bound + 1e-6)
        self.assertGreaterEqual(float(np.median(reductions)), 0.30, reductions)

    def test_g_a4_spill_season_signature(self):
        res5 = self.results[5]
        spec = res5["spec"]
        codes = list(spec.plant_codes)
        bon = codes.index(3075)
        self.assertGreater(res5["on"].hydro_cascade_spill[bon].sum(), 0.0)
        for pid in (
            3075,
            3925,
        ):  # the coupled members of the PRECOMMIT's spill-season list
            c = codes.index(pid)
            row = self.monthly[
                (self.monthly["plant_id"] == pid)
                & (self.monthly["year"] == 2023)
                & (self.monthly["month"] == 5)
            ].iloc[0]
            measured = float(row["spill_mean_kcfs"]) * res5["T"]
            lp = float(res5["on"].hydro_cascade_spill[c].sum())
            self.assertLessEqual(
                abs(lp - measured),
                0.10 * measured,
                f"{pid}: LP {lp:.0f} vs measured {measured:.0f}",
            )
        res1 = self.results[1]
        arr1 = self._arrivals(res1)
        for c, pid in enumerate(codes):
            row = self.monthly[
                (self.monthly["plant_id"] == pid)
                & (self.monthly["year"] == 2023)
                & (self.monthly["month"] == 1)
            ].iloc[0]
            measured = float(row["spill_mean_kcfs"]) * res1["T"]
            self.assertLessEqual(
                res1["on"].hydro_cascade_spill[c].sum(), measured + 0.05 * arr1[c].sum()
            )

    def test_g_a5_lag_signature_on_short_pond_links(self):
        res = self.results[1]
        spec = res["spec"]
        for ln in range(spec.n_links):
            d = int(spec.link_dn_local[ln])
            u = int(spec.link_up_gen_idx[ln])
            if u < 0:
                continue
            pond_hours = spec.pond_cap[d] / max(self._arrivals(res)[d].mean(), 1e-6)
            if pond_hours > 6.0:
                continue
            g = int(spec.coupled_gen_idx[d])
            tau = int(spec.link_tau[ln])
            r_on = _lagged_corr(res["on"].dispatch[u], res["on"].dispatch[g], tau)
            r_off = _lagged_corr(res["off"].dispatch[u], res["off"].dispatch[g], tau)
            self.assertGreater(
                r_on, r_off, f"link {ln}: r_on {r_on:.3f} <= r_off {r_off:.3f}"
            )

    def test_report(self):
        """Print the PRECOMMIT §7 table (pytest -s); asserts nothing beyond solve status."""
        for m, res in self.results.items():
            spec = res["spec"]
            arr = self._arrivals(res)
            print(
                f"\n== month {m}: OFF {res['off'].status} ON {res['on'].status} T={res['T']}"
            )
            for c, g in enumerate(spec.coupled_gen_idx):
                pid = int(spec.plant_codes[c])
                print(
                    f"  {STATION_OF[pid]:>3} {pid}: E_off {res['off'].dispatch[g].sum():10.0f} E_on {res['on'].dispatch[g].sum():10.0f}"
                    f" | amp off {self._amplitude(res['off'].dispatch[g]):.3f} on {self._amplitude(res['on'].dispatch[g]):.3f}"
                    f" | peak off {res['off'].dispatch[g].max():7.1f} on {res['on'].dispatch[g].max():7.1f}"
                    f" | spill {res['on'].hydro_cascade_spill[c].sum():9.1f} kcfs·h | pond max {res['on'].hydro_cascade_storage[c].max():7.1f}/{spec.pond_cap[c]:.1f}"
                    f" | arr mean {arr[c].mean():7.2f} kcfs | water value mean {res['on'].hydro_cascade_water_value[c].mean():8.2f}"
                )
            gcl = 0
            print(
                f"  GCL head: amp off {self._amplitude(res['off'].dispatch[gcl]):.3f} on {self._amplitude(res['on'].dispatch[gcl]):.3f}"
            )
            self.assertEqual(res["on"].status, "Optimal")
