"""The mass-cap budget SCHEDULE field (SCN-CAP, owner ruling S12 2026-09-06).

``ScenarioConfig.mass_cap_tons_by_year`` — ``{ISO: {year: metric tonnes}}`` —
is read FIRST by ``policy/cap_and_trade.py::_power_sector_cap``, ahead of the
scalar ``mass_cap_tons`` and the published RGGI/CARB budget, so a DECLINING
power-sector cap (the ``CAP-STATE-TIGHT`` case, ``FINDING-scn-ws1a-2026-09-05.md``
§4.2) is expressible. Trivial-first (rule "Testing Pattern"): 1 generator /
1 zone / 24 hours through the SAME seam the runner and the calibration
harness use (``policy.constraints.build_mass_cap_dispatch_kwargs`` →
``solve_dispatch``), then the reader, the fallback order, and the backcast /
hindcast coercion that keeps every keeper byte-identical.
"""

from __future__ import annotations

import json
from unittest import mock

import numpy as np
import pytest

from market_sim.config.constants import CAP_AND_TRADE_PROGRAMS
from market_sim.config.scenarios import (
    _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS,
    _CACHE_KEY_OPTIONAL_FIELDS,
    ScenarioConfig,
)
from market_sim.data.fleet import Generator, generators_to_fleet_arrays
from market_sim.model.dispatch import solve_dispatch
from market_sim.policy import cap_and_trade
from market_sim.policy.cap_and_trade import (
    resolve_carbon_program,
    scheduled_power_sector_budget,
)
from market_sim.policy.constraints import build_mass_cap_dispatch_kwargs

# The committed CAP-STATE-TIGHT schedule (WS-1a §4.2, ruled S12): metric
# tonnes, a linear decline to 20 % of the 2025 published per-state budget by
# 2050 (CAISO anchored to the model's own REF-2026 CO2 — CARB publishes no
# power-sector budget). Repeated here as the test's fixture, not sourced from
# the YAML, so the reader is tested on its own arithmetic.
SCHEDULE = {
    "NYISO": {2026: 23.16e6, 2030: 20.2e6, 2040: 12.8e6, 2050: 4.6e6},
    "NEISO": {2026: 20.67e6, 2030: 18.0e6, 2040: 11.4e6, 2050: 4.1e6},
    "CAISO": {2026: 30.5e6, 2030: 26.5e6, 2040: 16.5e6, 2050: 6.1e6},
}

T = 24
VOLL = 5000.0


def _forecast(iso: str, **kw) -> ScenarioConfig:
    return ScenarioConfig(iso=iso, mode="forecast", **kw)


def _armed(iso: str, schedule=SCHEDULE, **kw) -> ScenarioConfig:
    return _forecast(
        iso,
        mass_cap_enabled=True,
        mass_cap_program="co2",
        mass_cap_tons_by_year=schedule,
        **kw,
    )


class TestScheduleReader:
    """``scheduled_power_sector_budget``: knots, interpolation, edge hold."""

    def test_knot_year_is_exact(self):
        cfg = _armed("NYISO")
        assert scheduled_power_sector_budget(cfg, 2026) == pytest.approx(23.16e6)
        assert scheduled_power_sector_budget(cfg, 2030) == pytest.approx(20.2e6)
        assert scheduled_power_sector_budget(cfg, 2050) == pytest.approx(4.6e6)

    def test_interpolates_linearly_at_a_non_knot_year(self):
        # 2028 sits halfway between the 2026 and 2030 knots:
        # 23.16 + 0.5 * (20.2 - 23.16) = 21.68 Mt.
        cfg = _armed("NYISO")
        assert scheduled_power_sector_budget(cfg, 2028) == pytest.approx(21.68e6)
        # 2035 halfway between 2030 (20.2) and 2040 (12.8): 16.5 Mt.
        assert scheduled_power_sector_budget(cfg, 2035) == pytest.approx(16.5e6)

    def test_holds_the_last_knot_flat_after_2050_and_the_first_before_2026(self):
        cfg = _armed("NEISO")
        assert scheduled_power_sector_budget(cfg, 2055) == pytest.approx(4.1e6)
        assert scheduled_power_sector_budget(cfg, 2100) == pytest.approx(4.1e6)
        assert scheduled_power_sector_budget(cfg, 2025) == pytest.approx(20.67e6)

    def test_per_iso_lookup_reads_the_config_iso(self):
        assert scheduled_power_sector_budget(_armed("CAISO"), 2030) == pytest.approx(
            26.5e6
        )
        assert scheduled_power_sector_budget(_armed("NEISO"), 2030) == pytest.approx(
            18.0e6
        )

    def test_iso_absent_from_the_schedule_returns_none(self):
        for iso in ("ERCOT", "PJM", "MISO"):
            assert scheduled_power_sector_budget(_armed(iso), 2028) is None

    def test_none_schedule_returns_none(self):
        cfg = _forecast("NYISO", mass_cap_enabled=True)
        assert scheduled_power_sector_budget(cfg, 2028) is None

    def test_json_round_trip_string_keys_resolve_identically(self):
        # run_config.json stringifies the int year keys; the reader coerces
        # them back so on-disk and in-memory configs resolve the same budget
        # and hash to the same cache key.
        as_json = json.loads(json.dumps(SCHEDULE))
        assert list(as_json["NYISO"]) == ["2026", "2030", "2040", "2050"]
        a = _armed("NYISO")
        b = _armed("NYISO", schedule=as_json)
        assert scheduled_power_sector_budget(b, 2028) == pytest.approx(21.68e6)
        assert a.cache_key() == b.cache_key()


class TestFallbackOrder:
    """schedule → scalar → published → inert, and nothing stacks."""

    def test_schedule_wins_over_scalar_and_published(self):
        # NYISO 2025 has BOTH a published per-state budget and, here, an
        # explicit scalar; the schedule still wins (edge-held 2026 knot).
        cfg = _armed("NYISO", mass_cap_tons=1.0e6)
        res = resolve_carbon_program(cfg, 2025)
        assert res.cap_spec is not None
        assert res.cap_spec.cap_tons == pytest.approx(23.16e6)
        assert res.cap_spec.label == "co2"
        assert res.price_adder is None

    def test_none_schedule_keeps_the_scalar_first(self):
        cfg = _forecast("CAISO", mass_cap_enabled=True, mass_cap_tons=5.0e6)
        res = resolve_carbon_program(cfg, 2028)
        assert res.cap_spec.cap_tons == pytest.approx(5.0e6)

    def test_none_schedule_keeps_the_published_budget_second(self):
        from market_sim.config.constants import CARB_ALLOWANCE_BUDGET

        cfg = _forecast("CAISO", mass_cap_enabled=True)
        res = resolve_carbon_program(cfg, 2028)
        assert res.cap_spec.cap_tons == pytest.approx(CARB_ALLOWANCE_BUDGET[2028] * 1e6)

    def test_none_schedule_keeps_inert_third(self):
        # No published 2026 budget row is landed: the row stays inert and the
        # adder path carries the projected program price — unchanged.
        cfg = _forecast("NYISO", mass_cap_enabled=True)
        res = resolve_carbon_program(cfg, 2026)
        assert res.cap_spec is None
        assert res.price_adder is not None and res.price_adder > 0.0

    def test_schedule_makes_the_inert_2026_year_a_row(self):
        # The whole point of the field: 2026 had no published budget, so the
        # published-only path was inert there (WS-1a §4.1); the schedule
        # gives it a row.
        res = resolve_carbon_program(_armed("NYISO"), 2026)
        assert res.cap_spec is not None
        assert res.cap_spec.cap_tons == pytest.approx(23.16e6)

    def test_requires_mass_cap_enabled(self):
        # The schedule is a budget SOURCE, not a gate: without the row gate
        # the adder path is untouched.
        cfg = _forecast("NYISO", mass_cap_tons_by_year=SCHEDULE)
        res = resolve_carbon_program(cfg, 2028)
        assert res.cap_spec is None
        assert res.price_adder is not None

    def test_no_program_isos_resolve_to_nothing_under_the_case(self):
        # ERCOT / MISO carry no cap-and-trade program: the case is
        # byte-identical to REF there — no resolution, no row, no adder.
        for iso in ("ERCOT", "MISO"):
            assert iso not in CAP_AND_TRADE_PROGRAMS
            for year in (2026, 2028, 2030):
                assert resolve_carbon_program(_armed(iso), year) is None

    def test_pjm_absent_from_the_schedule_falls_through_to_the_published_fallback(
        self,
    ):
        # ROUTED FINDING (FINDING-scn-cap-2026-09-06.md §5): PJM IS in
        # CAP_AND_TRADE_PROGRAMS (its partial RGGI footprint), so under
        # mass_cap_enabled the ISO falls through — exactly as the charter's
        # fallback order requires — to the published REGIONAL RGGI budget in
        # 2027-2030 (RGGI_MEMBER_STATES_BY_YEAR stops at 2025), i.e. a slack
        # row rather than a byte-identical LP. 2026 and 2031+ stay inert.
        # Pinned so the desk's ruling on it cannot be pre-empted silently.
        from market_sim.config.constants import (
            RGGI_STATE_CO2_BUDGET,
            SHORT_TON_TO_METRIC_TONNE,
        )

        cfg = _armed("PJM")
        assert resolve_carbon_program(cfg, 2026).cap_spec is None
        res = resolve_carbon_program(cfg, 2028)
        assert res.cap_spec is not None
        assert res.cap_spec.cap_tons == pytest.approx(
            RGGI_STATE_CO2_BUDGET["RGGI"][2028] * SHORT_TON_TO_METRIC_TONNE
        )
        assert resolve_carbon_program(cfg, 2031).cap_spec is None


class TestBackcastInertness:
    """Rule 13: a scenario slope never enters a scored backcast or a hindcast."""

    def test_backcast_coerces_the_schedule_to_none(self):
        cfg = ScenarioConfig(
            iso="NYISO",
            mode="backcast",
            mass_cap_enabled=True,
            mass_cap_tons_by_year=SCHEDULE,
        )
        assert cfg.mass_cap_tons_by_year is None

    def test_hindcast_coerces_the_schedule_to_none(self):
        cfg = ScenarioConfig(
            iso="NYISO",
            mode="forecast",
            hindcast=True,
            mass_cap_enabled=True,
            mass_cap_tons_by_year=SCHEDULE,
        )
        assert cfg.mass_cap_tons_by_year is None

    def test_backcast_keeps_the_pre_existing_scalar_and_published_paths(self):
        # The coercion touches the schedule ONLY: mass_cap_enabled and the
        # scalar are live in backcast exactly as before this field.
        cfg = ScenarioConfig(
            iso="CAISO",
            mode="backcast",
            mass_cap_enabled=True,
            mass_cap_tons=5.0e6,
            mass_cap_tons_by_year=SCHEDULE,
        )
        assert cfg.mass_cap_tons == 5.0e6
        assert resolve_carbon_program(cfg, 2024).cap_spec.cap_tons == pytest.approx(
            5.0e6
        )

    def test_backcast_cache_key_is_unmoved_by_the_field(self):
        with_field = ScenarioConfig(
            iso="NEISO", mode="backcast", mass_cap_tons_by_year=SCHEDULE
        )
        without = ScenarioConfig(iso="NEISO", mode="backcast")
        assert with_field.cache_key() == without.cache_key()

    def test_field_is_cache_optional_at_none_and_an_armed_run_keys_distinctly(self):
        assert "mass_cap_tons_by_year" in _CACHE_KEY_OPTIONAL_FIELDS
        assert _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["mass_cap_tons_by_year"] == "None"
        base = _forecast("NYISO", mass_cap_enabled=True, mass_cap_program="co2")
        assert (
            base.cache_key()
            == ScenarioConfig(
                iso="NYISO",
                mode="forecast",
                mass_cap_enabled=True,
                mass_cap_program="co2",
                mass_cap_tons_by_year=None,
            ).cache_key()
        )
        assert _armed("NYISO").cache_key() != base.cache_key()

    @pytest.mark.parametrize(
        "bad",
        [
            {},
            {"NYISO": {}},
            {"NYISO": {"not-a-year": 1.0e6}},
            {"NYISO": {2026: 0.0}},
            {"NYISO": {2026: -1.0}},
        ],
    )
    def test_malformed_schedules_are_refused(self, bad):
        with pytest.raises(ValueError, match="mass_cap_tons_by_year"):
            _forecast("NYISO", mass_cap_tons_by_year=bad)


class TestTrivialFirstLp:
    """1 generator / 1 zone / 24 h through the runner's own kwargs seam."""

    ZONES = ["Z0"]
    RATE = 0.5  # t/MWh
    MC = 50.0
    DEMAND = 80.0

    def _fleet(self):
        gens = [
            Generator(
                unit_id="G0",
                name="G0",
                zone="Z0",
                fuel_type="gas_cc",
                pmax_mw=200.0,
                pmin_mw=0.0,
                eford=0.0,
                emission_rate_co2=self.RATE,
            )
        ]
        return generators_to_fleet_arrays(gens, self.ZONES, hours=T)

    def _solve(self, fleet, **cap_kwargs):
        n = len(self.ZONES)
        return solve_dispatch(
            fleet,
            np.full((n, T), self.DEMAND),
            mc=np.full((1, T), self.MC),
            T=T,
            voll=VOLL,
            wind_cf=np.zeros((n, T)),
            wind_cap=np.zeros(n),
            solar_cf=np.zeros((n, T)),
            solar_cap=np.zeros(n),
            **cap_kwargs,
        )

    def _kwargs(self, cfg, year, fleet):
        # Synthetic plant_code 0 keeps the zone-level membership (1.0 on a
        # non-external zone); the EIA-860 lookup is pinned empty so the test
        # is hermetic.
        with mock.patch.dict(cap_and_trade._PLANT_STATE_CACHE, {"NEISO": {}}):
            return build_mass_cap_dispatch_kwargs(cfg, year, self.ZONES, fleet)

    def test_binding_schedule_dual_is_the_allowance_price_and_emissions_hit_the_cap(
        self,
    ):
        # Uncapped: 80 MW x 24 h x 0.5 t/MWh = 960 t. The schedule reads
        # {2026: 1000, 2030: 200} -> 600 t at 2028 (interpolated), so the row
        # binds and the only way to meet it is to shed load at VOLL: the
        # analytic dual is (VOLL - mc) / rate.
        fleet = self._fleet()
        cfg = _armed("NEISO", schedule={"NEISO": {2026: 1000.0, 2030: 200.0}})
        kw = self._kwargs(cfg, 2028, fleet)
        np.testing.assert_allclose(kw["mass_cap_rhs"], [600.0])
        np.testing.assert_allclose(kw["mass_cap_coeffs"], [[self.RATE]])
        assert kw["mass_cap_labels"] == ["co2"]

        res = self._solve(fleet, **kw)
        assert res.status == "Optimal"
        emissions = float((kw["mass_cap_coeffs"][0][:, None] * res.dispatch).sum())
        assert emissions == pytest.approx(600.0, rel=1e-6)
        assert res.co2_cap_price is not None
        expected = (VOLL - self.MC) / self.RATE  # 9,900 $/t
        assert res.co2_cap_price[0] == pytest.approx(expected, rel=1e-6)
        assert res.co2_cap_price[0] > 0.0

    def test_slack_schedule_dual_is_zero_and_dispatch_is_unconstrained(self):
        fleet = self._fleet()
        cfg = _armed("NEISO", schedule={"NEISO": {2026: 1.0e6, 2030: 1.0e6}})
        kw = self._kwargs(cfg, 2028, fleet)
        res = self._solve(fleet, **kw)
        assert res.status == "Optimal"
        assert res.co2_cap_price[0] == pytest.approx(0.0, abs=1e-9)
        np.testing.assert_allclose(res.dispatch[0], self.DEMAND, atol=1e-6)

    def test_none_schedule_in_an_unpublished_year_builds_no_row(self):
        # 2026 has no published NEISO budget, so with the field None the seam
        # returns {} and the LP is the unconstrained one — the pre-field
        # behaviour, byte for byte.
        fleet = self._fleet()
        cfg = _forecast("NEISO", mass_cap_enabled=True)
        assert self._kwargs(cfg, 2026, fleet) == {}
        res = self._solve(fleet)
        assert res.co2_cap_price is None
        np.testing.assert_allclose(res.dispatch[0], self.DEMAND, atol=1e-6)

    def test_no_program_iso_builds_no_row_under_the_schedule(self):
        fleet = self._fleet()
        cfg = _armed("ERCOT", schedule=SCHEDULE)
        with mock.patch.dict(cap_and_trade._PLANT_STATE_CACHE, {"ERCOT": {}}):
            assert build_mass_cap_dispatch_kwargs(cfg, 2028, self.ZONES, fleet) == {}
