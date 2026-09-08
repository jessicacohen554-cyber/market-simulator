"""Unit tests for the instrument-derived hydro budget period (nyiso-220).

The mechanism shortens the LP's hydro energy-budget period, per plant, to the
period that project's own governing instrument (or its measured pondage) permits
energy to be reallocated over. These tests pin the three properties the mechanism
has to have, all of which are load-bearing for the surrounding governance:

1. **Byte-identical when off, and when on for an ISO with no registry entry.**
   The mechanism is a strict opt-in refinement, so an unarmed run must not see a
   changed LP or a changed cache key.
2. **Monthly energy is conserved exactly.** The measured monthly total is the
   calibration anchor (the keeper matches it at month-energy r ~ 1.000); this
   mechanism constrains *when within a month* energy is used, never *how much*.
   Periods are month-aligned precisely so this holds.
3. **The registry is grounded, not tuned.** Every entry is a published
   instrument's own period, so the test asserts the two NYISO values rather than
   letting a future edit drift them silently.
"""

from __future__ import annotations

import numpy as np
import pytest

from market_sim.config.constants import HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import _hour_to_month_index
from market_sim.data.hydro import allocate_period_energy, hydro_budget_period_hours


def _config(**overrides) -> ScenarioConfig:
    """Return a minimal NYISO backcast config with ``overrides`` applied."""
    return ScenarioConfig(
        iso="NYISO", mode="backcast", start_year=2024, end_year=2024, **overrides
    )


class TestRegistryGrounding:
    """The registry carries published instrument periods, not tuned values."""

    def test_nyiso_entries_are_the_published_periods(self):
        """Niagara is daily (pondage-derived); St. Lawrence weekly (IJC directive)."""
        reg = HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NYISO"]
        # 2693 Robert Moses Niagara: instruments state NO conservation period and
        # measured pondage is 0.244 h -> use it or lose it -> one day.
        assert reg[2693] == 24
        # 2694 Robert Moses St. Lawrence: the IJC peaking-and-ponding directive
        # states ponding holds "the total weekly flow the same" -> one week.
        assert reg[2694] == 168

    def test_only_instrument_backed_plants_are_registered(self):
        """The 161 domestic-river plants are deliberately absent (rule 14)."""
        assert set(HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NYISO"]) == {2693, 2694}


class TestGating:
    """The mechanism is a strict opt-in refinement."""

    def test_returns_none_when_flag_off(self):
        """Flag off yields None, so the caller builds the unchanged monthly rows."""
        assert hydro_budget_period_hours("NYISO", [2693, 2694], _config()) is None

    def test_returns_none_for_iso_without_registry_entry(self):
        """An ISO with no entry is a no-op even with the flag on."""
        cfg = _config(hydro_budget_period_by_instrument=True)
        assert hydro_budget_period_hours("CAISO", [2693, 2694], cfg) is None

    def test_returns_none_when_no_fleet_plant_matches(self):
        """A NYISO fleet with none of the registered plants is still a no-op."""
        cfg = _config(hydro_budget_period_by_instrument=True)
        assert hydro_budget_period_hours("NYISO", [2612, 54580], cfg) is None

    def test_unregistered_plants_keep_the_month_sentinel(self):
        """Registered plants get their period; others get 0 = calendar month."""
        cfg = _config(hydro_budget_period_by_instrument=True)
        got = hydro_budget_period_hours("NYISO", [2693, 2694, 2612, 54580], cfg)
        assert got is not None
        np.testing.assert_array_equal(got, [24, 168, 0, 0])

    def test_cache_key_unchanged_when_off_and_distinct_when_on(self):
        """Off must not re-key any existing bundle; on must earn its own key."""
        off, on = _config(), _config(hydro_budget_period_by_instrument=True)
        baseline = ScenarioConfig(
            iso="NYISO", mode="backcast", start_year=2024, end_year=2024
        )
        assert off.cache_key() == baseline.cache_key()
        assert on.cache_key() != off.cache_key()


class TestPeriodAllocation:
    """Energy is re-partitioned in time without changing any month's total."""

    @pytest.mark.parametrize("period_hours", [24, 168])
    def test_monthly_energy_conserved_exactly(self, period_hours):
        """Flat-within-period allocation reproduces every month's measured total.

        This is the property month-alignment exists to guarantee: with periods
        allowed to straddle month boundaries it failed by up to ~8.3e4 MWh.
        """
        rng = np.random.default_rng(0)
        monthly = rng.uniform(1e4, 1e6, size=(5, 12))
        energy, index = allocate_period_energy(monthly, period_hours)

        hours_per_period = np.bincount(index)
        level = energy[:, index] / hours_per_period[index]  # flat MW within period
        month_of_hour = _hour_to_month_index(8760)
        recon = np.stack(
            [level[:, month_of_hour == m].sum(axis=1) for m in range(12)], axis=1
        )
        np.testing.assert_allclose(recon, monthly, rtol=0, atol=1e-6)

    @pytest.mark.parametrize("period_hours", [24, 168])
    def test_no_period_straddles_a_month_boundary(self, period_hours):
        """Month-aligned periods never span two months."""
        _, index = allocate_period_energy(np.ones((1, 12)), period_hours)
        month_of_hour = _hour_to_month_index(8760)
        for p in np.unique(index):
            assert len(np.unique(month_of_hour[index == p])) == 1

    def test_annual_energy_conserved(self):
        """The annual total is preserved as well as each month's."""
        rng = np.random.default_rng(1)
        monthly = rng.uniform(1e4, 1e6, size=(3, 12))
        energy, _ = allocate_period_energy(monthly, 24)
        np.testing.assert_allclose(energy.sum(axis=1), monthly.sum(axis=1))

    def test_daily_period_yields_365_periods(self):
        """A 24 h period partitions a standard 8760-hour year into 365 days."""
        _, index = allocate_period_energy(np.ones((1, 12)), 24)
        assert int(index.max()) + 1 == 365

    def test_weekly_period_is_month_aligned_so_exceeds_52(self):
        """Month alignment gives 59 weekly periods, not 52 calendar weeks.

        Each month contributes ceil(hours/168) periods, so its final period is
        short. That is the deliberate cost of conserving monthly totals exactly.
        """
        _, index = allocate_period_energy(np.ones((1, 12)), 168)
        assert int(index.max()) + 1 == 59

    def test_rejects_non_positive_period(self):
        """A non-positive period is a programming error, not a silent month."""
        with pytest.raises(ValueError, match="must be positive"):
            allocate_period_energy(np.ones((1, 12)), 0)
