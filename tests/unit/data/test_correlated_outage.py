"""Tests for the correlated cold-event forced-outage derate (FF-1B).

Trivial cases first (synthetic TMIN, one generator, 48 hours), then the
gating/era semantics, the ORDC sigma guard, and finally the Uri
self-consistency validation (charter D.5: the forward statistical model must
regenerate the measured Uri-scale derate depth from weather + physics alone).
"""

import numpy as np
import pytest

import market_sim.data.outages as outages
from market_sim.config.constants import CORRELATED_OUTAGE_CURVE
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.fleet import FUEL_TYPE_MAP, FleetArrays
from market_sim.data.outages import (
    apply_correlated_outage_derate,
    correlated_outage_excess_by_class,
    correlated_outage_system_tmin,
)
from market_sim.results.scarcity import resolve_lolp_params

PRE = CORRELATED_OUTAGE_CURVE["ERCOT"]["pre"]
POST = CORRELATED_OUTAGE_CURVE["ERCOT"]["post"]


def _fleet(groups: list[str], t: int) -> FleetArrays:
    n = len(groups)
    return FleetArrays(
        pmax=np.full(n, 100.0),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 7.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.full(n, FUEL_TYPE_MAP["gas_cc"], dtype=int),
        availability=np.full((n, t), 0.9),
        unit_ids=[f"g{i}" for i in range(n)],
        efficiency_bin=np.zeros(n),
        plant_code=np.arange(1, n + 1, dtype=int),
        plant_group=np.array(groups),
    )


def _patch_tmin(monkeypatch, tmin_by_day: list[float]):
    """Patch the system TMIN series to a synthetic per-day (24 h blocks) array."""

    def fake(iso, year, hours=8760):
        out = np.full(hours, np.nan)
        for d, t in enumerate(tmin_by_day):
            lo = d * 24
            if lo >= hours:
                break
            if np.isfinite(t):
                out[lo : min(lo + 24, hours)] = t
        return out

    monkeypatch.setattr(outages, "correlated_outage_system_tmin", fake)


class TestExcessCurve:
    def test_hinge_zero_above_onset_and_capped_below(self, monkeypatch):
        _patch_tmin(monkeypatch, [0.0, -7.0, -8.0, -30.0, np.nan])
        built = correlated_outage_excess_by_class(
            "ERCOT", 2024, 5 * 24, t0_c=-7.0, winterized_year=2022
        )
        assert built is not None
        excess, shares = built
        ct = excess["CT_PEAKER"]
        assert ct[0] == 0.0  # mild day: no excess
        assert ct[24] == 0.0  # exactly at onset: hinge is zero
        assert ct[48] == pytest.approx(POST["CT_PEAKER"]["slope_per_c"] * 1.0)
        assert ct[72] == POST["CT_PEAKER"]["cap"]  # deep cold clips at cap
        assert ct[96] == 0.0  # uncovered (NaN) day carries no excess
        assert shares["CT_PEAKER"] == POST["CT_PEAKER"]["winter_event_share"]

    def test_era_selection_by_weather_year(self, monkeypatch):
        _patch_tmin(monkeypatch, [-30.0])
        pre_built = correlated_outage_excess_by_class(
            "ERCOT", 2021, 24, t0_c=-7.0, winterized_year=2022
        )
        post_built = correlated_outage_excess_by_class(
            "ERCOT", 2024, 24, t0_c=-7.0, winterized_year=2022
        )
        assert pre_built[0]["CC_REGULAR"][0] == PRE["CC_REGULAR"]["cap"]
        assert post_built[0]["CC_REGULAR"][0] == POST["CC_REGULAR"]["cap"]
        # Winterization halves the demonstrated saturation depth.
        assert POST["CC_REGULAR"]["cap"] < PRE["CC_REGULAR"]["cap"]

    def test_iso_without_curve_returns_none(self, monkeypatch):
        _patch_tmin(monkeypatch, [-30.0])
        assert (
            correlated_outage_excess_by_class(
                "CAISO", 2024, 24, t0_c=-7.0, winterized_year=2022
            )
            is None
        )


class TestApplyDerate:
    def test_one_gen_deep_cold_day(self, monkeypatch):
        # 2 days in January (winter): day 1 mild, day 2 deep cold.
        _patch_tmin(monkeypatch, [0.0, -30.0])
        fa = _fleet(["CC_REGULAR"], 48)
        cfg = ScenarioConfig(mode="forecast", correlated_forced_outage=True)
        assert apply_correlated_outage_derate(fa, cfg, "ERCOT", 2024)
        share = POST["CC_REGULAR"]["winter_event_share"]
        cap = POST["CC_REGULAR"]["cap"]
        # Mild winter day: only the event-share add-back (WEFOR relocation).
        assert fa.availability[0, 0] == pytest.approx(0.9 + share)
        # Deep-cold day: add-back minus the saturated excess.
        assert fa.availability[0, 24] == pytest.approx(0.9 + share - cap)

    def test_uncovered_class_untouched(self, monkeypatch):
        _patch_tmin(monkeypatch, [-30.0])
        fa = _fleet(["CC_REGULAR", "NUCLEAR"], 24)
        cfg = ScenarioConfig(mode="forecast", correlated_forced_outage=True)
        assert apply_correlated_outage_derate(fa, cfg, "ERCOT", 2024)
        assert np.all(fa.availability[1] == 0.9)  # no curve for NUCLEAR

    def test_clip_never_negative(self, monkeypatch):
        _patch_tmin(monkeypatch, [-30.0])
        fa = _fleet(["CT_PEAKER"], 24)
        fa.availability[:] = 0.1  # already deeply derated
        cfg = ScenarioConfig(mode="forecast", correlated_forced_outage=True)
        apply_correlated_outage_derate(fa, cfg, "ERCOT", 2021)
        assert np.all(fa.availability >= 0.0)

    def test_flag_off_is_noop(self, monkeypatch):
        # Explicit flag-off is a byte-identical no-op even on a deep-cold day.
        _patch_tmin(monkeypatch, [-30.0])
        fa = _fleet(["CC_REGULAR"], 24)
        cfg = ScenarioConfig(mode="forecast", correlated_forced_outage=False)
        assert not apply_correlated_outage_derate(fa, cfg, "ERCOT", 2024)
        assert np.all(fa.availability == 0.9)

    def test_default_on_forecast_forms_derate(self, monkeypatch):
        # FF-1F (owner, 2026-07-18): the flag defaults ON, so a bare forecast
        # config derates a covered class on a deep-cold day (ERCOT has a
        # CORRELATED_OUTAGE_CURVE entry). This is the whole point of the flip —
        # default-off it was dead code in the forecast runs it exists to fix.
        _patch_tmin(monkeypatch, [-30.0])
        fa = _fleet(["CC_REGULAR"], 24)
        cfg = ScenarioConfig(mode="forecast")
        assert cfg.correlated_forced_outage is True
        assert apply_correlated_outage_derate(fa, cfg, "ERCOT", 2024)
        share = POST["CC_REGULAR"]["winter_event_share"]
        cap = POST["CC_REGULAR"]["cap"]
        assert np.all(fa.availability == pytest.approx(0.9 + share - cap))

    def test_backcast_is_noop(self, monkeypatch):
        # Backcast carries the measured CAMPD overlays (charter D.5): the
        # statistical event model must never stack the same event on top.
        _patch_tmin(monkeypatch, [-30.0])
        fa = _fleet(["CC_REGULAR"], 24)
        cfg = ScenarioConfig(mode="backcast", correlated_forced_outage=True)
        assert not apply_correlated_outage_derate(fa, cfg, "ERCOT", 2024)
        assert np.all(fa.availability == 0.9)

    def test_iso_without_curve_is_noop(self, monkeypatch):
        _patch_tmin(monkeypatch, [-30.0])
        fa = _fleet(["CC_REGULAR"], 24)
        cfg = ScenarioConfig(mode="forecast", correlated_forced_outage=True)
        assert not apply_correlated_outage_derate(fa, cfg, "CAISO", 2024)
        assert np.all(fa.availability == 0.9)


class TestSigmaGuard:
    def test_scale_rejected_without_derate(self):
        # The sigma re-scale is gated on the derate being armed. Since FF-1F the
        # derate defaults ON, so the OFF state must be set explicitly to exercise
        # the guard (a bare config would now accept the scale).
        with pytest.raises(ValueError, match="gated with"):
            ScenarioConfig(
                correlated_forced_outage=False, correlated_outage_sigma_scale=0.8
            )

    def test_scale_accepted_with_derate_and_applied(self):
        cfg = ScenarioConfig(
            correlated_forced_outage=True, correlated_outage_sigma_scale=0.8
        )
        _, sigma = resolve_lolp_params(cfg, hours=8760)
        assert sigma == pytest.approx(0.8 * cfg.ordc_lolp_sigma_mw)

    def test_default_scale_is_identity(self):
        cfg = ScenarioConfig()
        _, sigma = resolve_lolp_params(cfg, hours=8760)
        assert sigma == cfg.ordc_lolp_sigma_mw


class TestUriSelfConsistency:
    """Charter D.5 Stage 4(i): forecast-mode model on 2021 weather must
    regenerate the measured Uri-scale derate depth from weather + physics."""

    def test_uri_depth_reproduced_from_weather(self):
        tmin = correlated_outage_system_tmin("ERCOT", 2021, 8760)
        if tmin is None:
            pytest.skip("ERCOT 2021 weather not available in this checkout")
        built = correlated_outage_excess_by_class(
            "ERCOT", 2021, 8760, t0_c=-7.0, winterized_year=2022
        )
        assert built is not None
        excess, _ = built
        # Feb 16 2021 (Uri peak): hour index on the fixed non-leap clock.
        feb16 = outages._hour_of_year(2, 16, 12)
        jul15 = outages._hour_of_year(7, 15, 12)
        # The hinge on the realized TMIN reproduces the measured saturation
        # depth for every covered class (the pre-era caps ARE the measured
        # Feb-16 excess — this asserts the temperature series alone recovers
        # them through the curve, i.e. the event regenerates from weather).
        for group, c in PRE.items():
            assert excess[group][feb16] == pytest.approx(c["cap"], abs=1e-9)
            assert excess[group][jul15] == 0.0  # no summer leakage
