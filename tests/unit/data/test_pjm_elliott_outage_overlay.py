"""PJM Winter Storm Elliott measured forced-outage overlay (closeout-PJM-elliott, R-64).

Trivial cases first: the loader's clock and window, then the applier on a two-unit
fleet (one gas, one coal) where every number can be checked by hand, then the
byte-identity guarantees (off, other years, other ISOs, hours outside the window)
and the rule-19 refusal.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.config.scenarios import ScenarioConfig
from market_sim.data import pjm_elliott_outages as peo
from market_sim.data.fleet.arrays import _apply_outage_overlays

HOURS = 8760
T0 = 356 * 24  # 23 Dec 2022 00:00 EPT, hour-beginning


def _gen(fuel: str, group: str) -> SimpleNamespace:
    """A minimal Generator stand-in carrying only what the applier reads."""
    return SimpleNamespace(fuel_type=fuel, plant_group=group, plant_code=1, name=group)


def _run(config, iso="PJM", year=2022, avail=None):
    """Apply the overlays to a 2-unit fleet (gas 40 GW, coal 20 GW) and return availability."""
    gens = [_gen("gas_cc", "CC_REGULAR"), _gen("coal", "COAL_BIT")]
    pmax = np.array([40_000.0, 20_000.0])
    a = np.ones((2, HOURS)) if avail is None else avail.copy()
    _apply_outage_overlays(
        gens, a, pmax, np.array([7.0, 10.0]), HOURS, config, iso, year
    )
    return a, pmax


def _cfg(**kw) -> ScenarioConfig:
    return ScenarioConfig(mode="backcast", **kw)


class TestLoader:
    def test_window_and_clock(self):
        d = peo.elliott_forced_outage_mw(2022)
        assert set(d) == {"gas", "coal", "oil", "nuclear"}
        for arr in d.values():
            fin = np.flatnonzero(np.isfinite(arr))
            assert fin[0] == T0 and fin[-1] == T0 + 71 and fin.size == 72

    def test_other_years_return_none(self):
        assert peo.elliott_forced_outage_mw(2021) is None
        assert peo.elliott_forced_outage_mw(2023) is None

    def test_odd_hours_interpolate_and_last_hour_holds(self):
        g = peo.elliott_forced_outage_mw(2022)["gas"]
        assert g[T0 + 1] == pytest.approx(0.5 * (g[T0] + g[T0 + 2]))
        assert g[T0 + 71] == g[T0 + 70]

    def test_peak_matches_the_figure_label(self):
        f = peo.build_hourly_frame()
        peak = f[f.hour_of_year == T0 + 24 + 7].forced_outage_mw.sum()
        # labelled 46,124 MW; digitisation tolerance +-1 px per segment (README)
        assert abs(peak - 46_124.0) < 500.0


class TestApplier:
    def test_off_is_byte_identical(self):
        a, _ = _run(_cfg())
        assert (a == 1.0).all()

    def test_other_year_and_other_iso_untouched(self):
        on = _cfg(pjm_elliott_measured_outage_overlay=True)
        assert (_run(on, year=2023)[0] == 1.0).all()
        assert (_run(on, iso="MISO")[0] == 1.0).all()

    def test_forecast_mode_refuses_it(self):
        with pytest.raises(ValueError, match="backcast-only measured overlays"):
            ScenarioConfig(mode="forecast", pjm_elliott_measured_outage_overlay=True)

    def test_withdraws_the_measured_rise_outside_nothing(self):
        a, pmax = _run(_cfg(pjm_elliott_measured_outage_overlay=True))
        win = np.zeros(HOURS, bool)
        win[T0 : T0 + 72] = True
        assert (a[:, ~win] == 1.0).all()
        m = peo.elliott_forced_outage_mw(2022)
        for i, fuel in ((0, "gas"), (1, "coal")):
            mf = m[fuel][T0 : T0 + 72]
            # model's own outage is flat zero here, so inc = rise over the 5-bar base
            want = np.clip(mf - mf[: peo.BASELINE_HOURS].mean(), 0.0, pmax[i])
            got = pmax[i] * (1.0 - a[i, T0 : T0 + 72])
            np.testing.assert_allclose(got, want, atol=1e-6)
        assert a[0, T0 + 31] < 0.5  # 24 Dec 07:00: ~28 GW of 40 GW gas withdrawn

    def test_nets_against_the_models_own_rise(self):
        # If the model already carries the whole rise in a fuel, nothing is added.
        m = peo.elliott_forced_outage_mw(2022)["coal"][T0 : T0 + 72]
        # model outage = the measured profile + a constant: the same rise, any level
        own = m - m[: peo.BASELINE_HOURS].mean() + 5_000.0
        avail = np.ones((2, HOURS))
        avail[1, T0 : T0 + 72] = 1.0 - own / 20_000.0
        a, _ = _run(_cfg(pjm_elliott_measured_outage_overlay=True), avail=avail)
        np.testing.assert_allclose(a[1], avail[1])

    def test_zero_stays_zero(self):
        avail = np.ones((2, HOURS))
        avail[0, T0 + 30] = 0.0
        a, _ = _run(_cfg(pjm_elliott_measured_outage_overlay=True), avail=avail)
        assert a[0, T0 + 30] == 0.0
        assert (a >= 0.0).all() and (a <= 1.0).all()


class TestConfig:
    def test_refused_with_the_event_cap(self):
        with pytest.raises(ValueError, match="arm exactly one"):
            ScenarioConfig(
                mode="backcast",
                pjm_elliott_measured_outage_overlay=True,
                pjm_measured_outage_event_cap=True,
            )

    def test_default_key_unchanged_and_armed_key_distinct(self):
        base = ScenarioConfig(mode="backcast")
        off = ScenarioConfig(mode="backcast", pjm_elliott_measured_outage_overlay=False)
        on = ScenarioConfig(mode="backcast", pjm_elliott_measured_outage_overlay=True)
        assert base.cache_key() == off.cache_key()
        assert on.cache_key() != base.cache_key()
