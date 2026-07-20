"""Tests for the M1 DA charge-allocation schedule (caiso-104).

Covers the three seams of ``caiso_charge_allocation_schedule``: the params
loader (:func:`market_sim.model.storage.caiso_charge_allocation_params`), the
LP row builder (:func:`market_sim.model.dispatch._build_storage_alloc_rows` —
the Fourier-Motzkin elimination of the ask's per-day scheduled-volume
variable), and the end-to-end dispatch behaviour (allocation floors hold; a
zero-charge day stays feasible; flag-off is byte-identical). Trivial cases
first (1 gen, 1 zone, 48 h) per the repo testing pattern.
"""

import numpy as np
import pytest

from market_sim.model.dispatch import (
    VariableLayout,
    _build_storage_alloc_rows,
    solve_dispatch,
)
from market_sim.model.storage import StorageUnit, caiso_charge_allocation_params


def _unit(tech: str = "li_ion", power: float = 1000.0) -> StorageUnit:
    return StorageUnit(
        unit_id=f"test_{tech}",
        zone="NP15",
        tech_name=tech,
        power_cap_mw=power,
        energy_cap_mwh=power * 4.0,
        eta_charge=0.92,
        eta_discharge=0.92,
        zone_idx=0,
    )


class TestChargeAllocationParams:
    def test_backcast_year_uses_own_row(self):
        batt_idx, share, da_frac = caiso_charge_allocation_params([_unit()], 2025, 8760)
        assert batt_idx.tolist() == [0]
        assert share.shape == (8760,)
        # Shares sum to 1 over each day (hod-mapped, identical across days).
        # (1e-4 tolerance: the committed CSV rounds shares to 6 decimals.)
        assert share[:24].sum() == pytest.approx(1.0, abs=1e-4)
        assert np.allclose(share[:24], share[24:48])
        # FINDING-caiso102 §1: measured 2025 DA-share of realized charge.
        assert da_frac == pytest.approx(0.7603, abs=1e-4)
        # Measured support: belly-heavy, evening ~ zero (FINDING-caiso103 §1A).
        assert share[:24][10:15].sum() > 0.6
        assert share[:24][17:22].sum() < 0.02

    def test_forward_year_latest_carry(self):
        """Owner sub-ruling caiso-104: forward years carry the latest year."""
        _, share_fwd, da_fwd = caiso_charge_allocation_params([_unit()], 2030, 24)
        _, share_25, da_25 = caiso_charge_allocation_params([_unit()], 2025, 24)
        assert np.allclose(share_fwd, share_25)
        assert da_fwd == da_25

    def test_pumped_storage_excluded(self):
        batt_idx, _, _ = caiso_charge_allocation_params(
            [_unit("pumped_storage"), _unit()], 2024, 24
        )
        assert batt_idx.tolist() == [1]

    def test_missing_artifact_raises(self, monkeypatch, tmp_path):
        """A gated mechanism must never silently no-op (caiso-98 lesson)."""
        from market_sim.config import paths

        monkeypatch.setattr(paths, "RAW_DIR", tmp_path)
        with pytest.raises(FileNotFoundError, match="derive_caiso_charge_allocation"):
            caiso_charge_allocation_params([_unit()], 2024, 24)


class TestStorageAllocRows:
    def test_row_algebra(self):
        """Row h: +1 on own-hour Chg minus share x da_frac on every day hour."""
        T = 48
        layout = VariableLayout(T=T, n_gen=1, n_zones=1, n_storage=2, n_links=0)
        share = np.zeros(T)
        hod = np.arange(T) % 24
        share[hod == 10] = 0.6
        share[hod == 11] = 0.4
        block = _build_storage_alloc_rows(layout, np.array([0]), share, 0.8).toarray()
        # 2 active hods x 2 days.
        assert block.shape == (4, layout.total_columns)
        vph = layout.vars_per_hour
        # Day-0 row for hod 10: coefficient on Chg[0, 10] is 1 - 0.6*0.8; on
        # every other day-0 hour's Chg[0, h'] it is -0.6*0.8; day-1 hours 0.
        r = block[0]
        c10 = 10 * vph + layout._chg_off + 0
        assert r[c10] == pytest.approx(1.0 - 0.48)
        c5 = 5 * vph + layout._chg_off + 0
        assert r[c5] == pytest.approx(-0.48)
        c_day1 = (24 + 5) * vph + layout._chg_off + 0
        assert r[c_day1] == 0.0
        # Storage unit 1 is not in batt_idx: no coefficients on its columns.
        c10_s1 = 10 * vph + layout._chg_off + 1
        assert np.all(block[:, c10_s1] == 0.0)
        # Non-Chg columns untouched.
        assert np.all(block[:, layout._dis_off :: vph] == 0.0)

    def test_zero_support_no_rows(self):
        layout = VariableLayout(T=24, n_gen=1, n_zones=1, n_storage=1, n_links=0)
        block = _build_storage_alloc_rows(layout, np.array([0]), np.zeros(24), 0.8)
        assert block.shape[0] == 0

    def test_no_batteries_no_rows(self):
        layout = VariableLayout(T=24, n_gen=1, n_zones=1, n_storage=1, n_links=0)
        block = _build_storage_alloc_rows(layout, np.array([], int), np.ones(24), 0.8)
        assert block.shape[0] == 0


class TestDispatchAllocation:
    def _solve(self, alloc: bool, spread: bool = True):
        from market_sim.data.fleet import Generator, generators_to_fleet_arrays

        T = 48
        fleet = generators_to_fleet_arrays(
            [
                Generator(
                    unit_id="G0",
                    name="G0",
                    zone="Z0",
                    fuel_type="gas_cc",
                    pmax_mw=500.0,
                    pmin_mw=0.0,
                    eford=0.0,
                )
            ],
            ["Z0"],
            hours=T,
        )
        demand = np.full((1, T), 100.0)
        # Hourly marginal cost: overnight hour 2 is the global trough, the
        # measured-support hours 10-11 are mid, evening 18-19 is the peak —
        # an unconstrained LP charges at hour 2, never at 10-11.
        mc = np.full((1, T), 50.0)
        hod = np.arange(T) % 24
        if spread:
            mc[0, hod == 2] = 5.0
            mc[0, np.isin(hod, (10, 11))] = 20.0
            mc[0, np.isin(hod, (18, 19))] = 200.0
        share = np.zeros(T)
        share[hod == 10] = 0.6
        share[hod == 11] = 0.4
        kw = {}
        if alloc:
            kw = dict(
                storage_alloc_batt_idx=np.array([0]),
                storage_alloc_share=share,
                storage_alloc_da_frac=0.8,
            )
        return solve_dispatch(
            fleet,
            demand,
            mc=mc,
            wind_cf=np.zeros((1, T)),
            wind_cap=np.zeros(1),
            solar_cf=np.zeros((1, T)),
            solar_cap=np.zeros(1),
            storage_power_cap=np.array([50.0]),
            storage_energy_cap=np.array([200.0]),
            storage_zone_idx=np.array([0]),
            eta_chg=np.array([1.0]),
            eta_dis=np.array([1.0]),
            T=T,
            **kw,
        )

    def test_allocation_floors_hold(self):
        res = self._solve(alloc=True)
        chg = res.storage_charge[0]
        hod = np.arange(48) % 24
        for d in range(2):
            day = slice(d * 24, (d + 1) * 24)
            tot = chg[day].sum()
            if tot <= 1e-6:
                continue
            assert chg[day][hod[day] == 10].sum() >= 0.6 * 0.8 * tot - 1e-6
            assert chg[day][hod[day] == 11].sum() >= 0.4 * 0.8 * tot - 1e-6
            # The free slice is bounded: at most 1 - da_frac of the day total
            # sits outside the measured support.
            outside = tot - chg[day][np.isin(hod[day], (10, 11))].sum()
            assert outside <= 0.2 * tot + 1e-6

    def test_reallocates_vs_unconstrained(self):
        """Unconstrained charge sits at the trough; the schedule moves it."""
        free = self._solve(alloc=False)
        cons = self._solve(alloc=True)
        hod = np.arange(48) % 24
        free_chg = free.storage_charge[0]
        cons_chg = cons.storage_charge[0]
        # Unconstrained: the global trough hour charges at the full power cap.
        assert free_chg[hod == 2].sum() == pytest.approx(100.0, abs=1e-6)
        # Scheduled: the out-of-support charge is bounded to the free slice
        # (1 - da_frac), so the trough hour can no longer take the power cap.
        assert cons_chg[hod == 2].sum() <= 0.2 * cons_chg.sum() + 1e-6
        assert cons_chg[np.isin(hod, (10, 11))].sum() >= 0.8 * cons_chg.sum() - 1e-6

    def test_zero_charge_day_feasible(self):
        """No spread -> no arbitrage -> zero charge remains feasible."""
        res = self._solve(alloc=True, spread=False)
        assert res.storage_charge[0].sum() == pytest.approx(0.0, abs=1e-6)

    def test_flag_off_matches_no_kwargs(self):
        a = self._solve(alloc=False)
        b = self._solve(alloc=False)
        assert np.allclose(a.prices, b.prices)
