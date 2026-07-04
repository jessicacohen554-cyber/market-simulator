"""Tests for the legitimacy diagnostic suite (audit §7 D-1/D-2/D-4/D-5/D-9).

Trivial cases first per the repo testing pattern: 1 generator, 1 zone,
24 hours — each diagnostic's pass and fail paths on synthetic fixtures —
then the mechanism-id threading through the real floor injectors.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pytest

from market_sim.data.fleet import FleetArrays, apply_netload_reliability_floor
from market_sim.data.floor_mechanisms import (
    MECH_CT_NETLOAD_DRAG,
    MECH_NUCLEAR,
    MECH_RELIABILITY_FLOOR,
    ensure_mechanism,
)
from market_sim.model.transmission import _distribute_group_floor
from scripts.legitimacy_diagnostics import (
    D6_CALIBRATION_YEARS,
    D6_MARKER_FILE,
    aggregate_floors_by_plant,
    at_floor_mask,
    d1_shape_metrics,
    run_d1,
    run_d2,
    run_d4,
    run_d5,
    run_d6_quarantine,
    run_d9,
)

HOURS = 24


def _fleet(
    n: int = 1,
    hours: int = HOURS,
    pmax: float = 100.0,
    group: str = "CT_PEAKER",
) -> FleetArrays:
    """One-zone trivial fleet: ``n`` identical generators, ``hours`` hours."""
    return FleetArrays(
        pmax=np.full(n, pmax),
        pmin=np.zeros(n),
        heat_rate=np.full(n, 10.0),
        vom=np.zeros(n),
        emission_rate=np.zeros(n),
        nox_rate=np.zeros(n),
        so2_rate=np.zeros(n),
        zone_idx=np.zeros(n, dtype=int),
        fuel_type_idx=np.zeros(n, dtype=int),
        availability=np.ones((n, hours)),
        unit_ids=[f"g{i}_committed" for i in range(n)],
        efficiency_bin=np.array(["b"] * n, dtype=str),
        plant_code=np.arange(1, n + 1),
        plant_group=np.array([group] * n, dtype=object),
    )


def _gens(fleet: FleetArrays) -> list:
    """Duck-typed generator list aligned with a trivial fleet."""
    return [
        SimpleNamespace(
            plant_group=fleet.plant_group[i],
            unit_id=fleet.unit_ids[i],
            plant_code=int(fleet.plant_code[i]),
        )
        for i in range(fleet.n_gen)
    ]


# ---------------------------------------------------------------------------
# D-1 — diurnal shape
# ---------------------------------------------------------------------------


class TestD1:
    def test_flat_model_fails_cv_gate(self):
        """The caiso-42 signature: flat model vs shaped actual → CV ratio 0."""
        hod = np.arange(HOURS)
        actual = 50.0 + 40.0 * np.sin(hod / 24 * 2 * np.pi)
        model = np.full(HOURS, 60.0)
        res = run_d1({"CT_PEAKER": model}, {"CT_PEAKER": actual}, year=2023)
        assert not res.passed
        assert any("CV ratio" in f for f in res.failures)

    def test_matching_shape_passes(self):
        hod = np.arange(HOURS)
        actual = 50.0 + 40.0 * np.sin(hod / 24 * 2 * np.pi)
        res = run_d1({"CT_PEAKER": actual * 1.1}, {"CT_PEAKER": actual}, year=2023)
        assert res.passed

    def test_anticorrelated_profile_fails_r_gate(self):
        hod = np.arange(HOURS).astype(float)
        actual = 10.0 + hod  # rising through the day
        model = 10.0 + hod[::-1]  # falling — r = -1
        res = run_d1({"CT_PEAKER": model}, {"CT_PEAKER": actual}, year=2023)
        assert any("profile r" in f for f in res.failures)

    def test_ungated_class_reported_not_failed(self):
        """A flat CC_CHP profile is reported but never gates (CHP exempt)."""
        hod = np.arange(HOURS)
        actual = 50.0 + 40.0 * np.sin(hod / 24 * 2 * np.pi)
        model = np.full(HOURS, 60.0)
        res = run_d1({"CC_CHP": model}, {"CC_CHP": actual}, year=2023)
        assert res.passed
        assert res.rows and res.rows[0]["gated"] is False

    def test_metrics_flat_series(self):
        r, cv_m, cv_a = d1_shape_metrics(np.full(HOURS, 5.0), np.linspace(1, 48, HOURS))
        assert r == 0.0 and cv_m == 0.0 and cv_a > 0.0


# ---------------------------------------------------------------------------
# D-2 — forced-energy attribution
# ---------------------------------------------------------------------------


class TestD2:
    def test_peaker_forced_share_fails(self):
        """1 gen / 24 h: 20 floored hours out of 24 → share ≫ 10 %."""
        dispatch = np.full((1, HOURS), 50.0)
        dispatch[0, 16:20] = 100.0  # evening hours dispatch above the floor
        min_gen = np.full((1, HOURS), 50.0)
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        res = run_d2(dispatch, min_gen, mech, np.array(["CT_PEAKER"]), year=2023)
        assert not res.passed
        assert "CT_PEAKER" in res.failures[0]
        row = res.rows[0]
        assert row["mechanism"] == "reliability_floor"
        assert row["share_of_class"] == pytest.approx(1000.0 / 1400.0, abs=1e-3)

    def test_exempt_mechanism_never_gates(self):
        """Nuclear must-run floors 100 % of energy — exempt, no failure."""
        dispatch = np.full((1, HOURS), 90.0)
        min_gen = np.full((1, HOURS), 90.0)
        mech = np.full((1, HOURS), MECH_NUCLEAR, dtype=np.int8)
        res = run_d2(dispatch, min_gen, mech, np.array(["nuclear"]), year=2023)
        assert res.passed
        assert res.rows  # still reported

    def test_small_forced_share_passes(self):
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.zeros((1, HOURS))
        min_gen[0, :2] = 100.0  # 2 of 24 floored hours ≈ 8 % < 10 %
        mech = np.zeros((1, HOURS), dtype=np.int8)
        mech[0, :2] = MECH_RELIABILITY_FLOOR
        res = run_d2(dispatch, min_gen, mech, np.array(["CT_PEAKER"]), year=2023)
        assert res.passed

    def test_merchant_gate_is_30pct(self):
        """A CC class fails only above the 30 % merchant budget."""
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.zeros((1, HOURS))
        min_gen[0, :6] = 100.0  # 25 % forced — under the merchant gate
        mech = np.zeros((1, HOURS), dtype=np.int8)
        mech[0, :6] = MECH_RELIABILITY_FLOOR
        res = run_d2(dispatch, min_gen, mech, np.array(["CC_REGULAR"]), year=2023)
        assert res.passed
        min_gen[0, :10] = 100.0  # 42 % forced — over
        mech[0, :10] = MECH_RELIABILITY_FLOOR
        res = run_d2(dispatch, min_gen, mech, np.array(["CC_REGULAR"]), year=2023)
        assert not res.passed

    def test_at_floor_mask_tolerance(self):
        dispatch = np.array([[50.4, 53.0, 0.0, 50.0]])
        min_gen = np.array([[50.0, 50.0, 0.5, 50.0]])
        mask = at_floor_mask(dispatch, min_gen)
        # 50.4 ≈ at floor; 53.0 above tolerance; 0.5 MW floor is noise.
        assert mask.tolist() == [[True, False, False, True]]


# ---------------------------------------------------------------------------
# D-4 — off-window binding
# ---------------------------------------------------------------------------


class TestD4:
    def test_all_day_floor_fails_evening_window(self):
        """A 24 h CT floor with an evening-justified driver → ~71 % off-window."""
        dispatch = np.full((1, HOURS), 40.0)
        min_gen = np.full((1, HOURS), 40.0)
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        res = run_d4(dispatch, min_gen, mech, np.array(["CT_PEAKER"]), year=2023)
        assert not res.passed
        assert res.rows[0]["offwindow_share"] == pytest.approx(17 / 24, abs=1e-3)

    def test_windowed_floor_passes(self):
        dispatch = np.zeros((1, HOURS))
        min_gen = np.zeros((1, HOURS))
        dispatch[0, 15:22] = 40.0
        min_gen[0, 15:22] = 40.0
        mech = np.zeros((1, HOURS), dtype=np.int8)
        mech[0, 15:22] = MECH_RELIABILITY_FLOOR
        res = run_d4(dispatch, min_gen, mech, np.array(["CT_PEAKER"]), year=2023)
        assert res.passed
        assert res.rows[0]["offwindow_share"] == 0.0

    def test_unwindowed_mechanism_not_checked(self):
        """Mechanisms with no declared window (e.g. nuclear) are exempt."""
        dispatch = np.full((1, HOURS), 90.0)
        min_gen = np.full((1, HOURS), 90.0)
        mech = np.full((1, HOURS), MECH_NUCLEAR, dtype=np.int8)
        res = run_d4(dispatch, min_gen, mech, np.array(["nuclear"]), year=2023)
        assert res.passed and not res.rows


# ---------------------------------------------------------------------------
# D-5 — forecast/backcast parity
# ---------------------------------------------------------------------------


class TestD5:
    CFG = {
        "outage_source": "estimated",
        "caiso_ra_mustoffer": True,
        "reliability_floor": False,
        "ct_netload_drag": False,
        "gas_st_netload_drag": False,
    }

    def test_wiring_gap_fails(self):
        """RA must-offer built only in the calibration script → violation."""
        res = run_d5(
            self.CFG,
            "CAISO",
            backcast_entry_src="... caiso_ra_mustoffer_min_gen(...)",
            forecast_entry_src="... no such call ...",
        )
        assert not res.passed
        assert "caiso_ra_mustoffer" in res.failures[0]

    def test_wired_both_modes_passes(self):
        src = "... caiso_ra_mustoffer_min_gen(...)"
        res = run_d5(self.CFG, "CAISO", src, src)
        assert res.passed
        assert not any(r["mechanism"] == "caiso_ra_mustoffer" for r in res.rows)

    def test_declared_overlay_difference_allowed(self):
        """reliability_floor is a declared backcast overlay: reported, no fail."""
        cfg = {**self.CFG, "caiso_ra_mustoffer": False, "reliability_floor": True}
        res = run_d5(
            cfg,
            "CAISO",
            backcast_entry_src="inject_reliability_floor(",
            forecast_entry_src="",
        )
        assert res.passed
        rows = [r for r in res.rows if r["mechanism"] == "reliability_floor"]
        assert rows and rows[0]["verdict"] == "declared"

    def test_mode_gated_overlays_declared(self):
        """historic outages / measured renewables etc. diff but are declared."""
        cfg = {**self.CFG, "caiso_ra_mustoffer": False, "outage_source": "historic"}
        res = run_d5(cfg, "CAISO", "", "")
        assert res.passed
        assert any(r["mechanism"] == "historic_outage_overlay" for r in res.rows)


# ---------------------------------------------------------------------------
# D-9 — overlay quarantine
# ---------------------------------------------------------------------------


def _clean_rc(**scenario_overrides) -> dict:
    sc = {
        "ct_deployment_overlay": False,
        "reliability_deployment_overlay": False,
        "ct_mustrun_per_plant": False,
        "ordc_reliability_deployment_mw": 0.0,
        "caiso_gas_commitment_floor": False,
        "gas_offer_curve": False,
        "offer_curve_by_group": {},
    }
    sc.update(scenario_overrides)
    return {"scenario_config": sc, "calibration_flags": {}}


class TestD9:
    def test_clean_config_passes(self):
        assert run_d9(_clean_rc(), "CAISO").passed

    @pytest.mark.parametrize(
        "key,value",
        [
            ("ct_deployment_overlay", True),
            ("reliability_deployment_overlay", True),
            ("ct_mustrun_per_plant", True),
            ("ordc_reliability_deployment_mw", 2500.0),
            ("caiso_gas_commitment_floor", True),
        ],
    )
    def test_armed_overlay_fails(self, key, value):
        res = run_d9(_clean_rc(**{key: value}), "CAISO")
        assert not res.passed
        assert key in res.failures[0]

    def test_generic_share_fallback_fails_non_ercot(self):
        res = run_d9(_clean_rc(gas_offer_curve=True), "MISO")
        assert not res.passed
        assert "_GAS_TRANCHE_SHARES" in res.failures[0]

    def test_hr_literal_fallback_fails_non_ercot(self):
        res = run_d9(_clean_rc(cc_committed_hr_override=0.9), "NEISO")
        assert not res.passed
        assert any("1.2" in f for f in res.failures)

    def test_hr_literal_covered_by_per_iso_curve_passes(self):
        curves = {"CC_REGULAR": {"committed": 0.9}, "CC_CHP": {"committed": 0.9}}
        res = run_d9(
            _clean_rc(cc_committed_hr_override=0.9, offer_curve_by_group=curves),
            "NEISO",
        )
        assert res.passed

    def test_ercot_may_use_its_own_fitted_bands(self):
        res = run_d9(
            _clean_rc(gas_offer_curve=True, cc_committed_hr_override=0.9),
            "ERCOT",
        )
        assert res.passed


# ---------------------------------------------------------------------------
# Mechanism-id threading through the real injectors
# ---------------------------------------------------------------------------


class TestMechanismThreading:
    def test_netload_drag_tags_window_hours(self):
        """1 gen / 1 zone / 24 h: the CT drag floors + tags only its window."""
        fleet = _fleet()
        net_load = np.full(HOURS, 60_000.0)  # 60 GW → frac well above 0
        applied = apply_netload_reliability_floor(
            fleet,
            _gens(fleet),
            net_load,
            plant_group="CT_PEAKER",
            slope=0.009,
            intercept=-0.1124,
            cap=0.36,
            ramp_window=(15, 22),
            mech_id=MECH_CT_NETLOAD_DRAG,
        )
        assert applied
        hod = np.arange(HOURS) % 24
        in_win = (hod >= 15) & (hod < 22)
        assert (fleet.min_gen[0, in_win] > 0).all()
        assert (fleet.min_gen[0, ~in_win] == 0).all()
        assert (fleet.min_gen_mechanism[0, in_win] == MECH_CT_NETLOAD_DRAG).all()
        assert (fleet.min_gen_mechanism[0, ~in_win] == 0).all()

    def test_maximum_composition_keeps_binding_mechanism(self):
        """A pre-existing HIGHER floor keeps its mechanism id (max-compose)."""
        fleet = _fleet()
        fleet.min_gen = np.zeros((1, HOURS))
        fleet.min_gen[0, 18] = 99.0  # higher than any drag target below
        mech = ensure_mechanism(fleet)
        mech[0, 18] = MECH_NUCLEAR  # stand-in incumbent id
        apply_netload_reliability_floor(
            fleet,
            _gens(fleet),
            np.full(HOURS, 60_000.0),
            plant_group="CT_PEAKER",
            slope=0.009,
            intercept=-0.1124,
            cap=0.36,
            ramp_window=(15, 22),
            mech_id=MECH_CT_NETLOAD_DRAG,
        )
        assert fleet.min_gen[0, 18] == 99.0
        assert fleet.min_gen_mechanism[0, 18] == MECH_NUCLEAR
        assert fleet.min_gen_mechanism[0, 15] == MECH_CT_NETLOAD_DRAG

    def test_distribute_group_floor_tags_cheapest_first(self):
        """Two units: the cheaper carries the group floor and its mech id."""
        fleet = _fleet(n=2)
        fleet.heat_rate = np.array([8.0, 12.0])
        frac = np.full(HOURS, 0.25)  # 25 % of 200 MW group = 50 MW target
        _distribute_group_floor(
            fleet, np.array([0, 1]), frac, HOURS, mech_id=MECH_RELIABILITY_FLOOR
        )
        assert (fleet.min_gen[0] == 50.0).all()  # cheapest takes it all
        assert (fleet.min_gen[1] == 0.0).all()
        assert (fleet.min_gen_mechanism[0] == MECH_RELIABILITY_FLOOR).all()
        assert (fleet.min_gen_mechanism[1] == 0).all()

    def test_aggregate_floors_by_plant_binding_mech(self):
        """Two tranches of one plant: sum floors, binding tranche's mech wins."""
        arrays = {
            "min_gen": np.array([[30.0] * HOURS, [10.0] * HOURS]),
            "mechanism": np.array(
                [[MECH_RELIABILITY_FLOOR] * HOURS, [MECH_CT_NETLOAD_DRAG] * HOURS],
                dtype=np.int8,
            ),
            "unit_ids": np.array(["p1_committed", "p1_econ"]),
            "plant_code": np.array([7, 7]),
            "plant_group": np.array(["CT_PEAKER", "CT_PEAKER"]),
        }
        pids, floor_sum, mech_plant, groups = aggregate_floors_by_plant(arrays)
        assert pids.tolist() == [7]
        assert (floor_sum[0] == 40.0).all()
        assert (mech_plant[0] == MECH_RELIABILITY_FLOOR).all()
        assert groups[0] == "CT_PEAKER"


# ---------------------------------------------------------------------------
# D-6 — holdout quarantine (CLAUDE.md rule 22, amended 2026-07-04)
# ---------------------------------------------------------------------------


def _fake_registry(tmp_path, sidecars, complete=None):
    """Build a minimal repo root with registry sidecars + the marker file."""
    reg = tmp_path / "frontend" / "data" / "backcast" / "registry"
    reg.mkdir(parents=True)
    for name, side in sidecars.items():
        (reg / f"{name}.json").write_text(json.dumps(side))
    marker = tmp_path / "frontend" / "data" / "backcast" / "calibration-complete.json"
    marker.write_text(json.dumps({"complete": complete or {}}))
    return tmp_path


class TestD6Quarantine:
    def test_in_window_years_pass(self, tmp_path):
        """2023-2025 solve years never trip the quarantine."""
        root = _fake_registry(
            tmp_path, {"r1": {"iso": "CAISO", "years": [2023, 2024, 2025]}}
        )
        res = run_d6_quarantine(root)
        assert res.passed and not res.rows

    def test_holdout_year_without_marker_fails(self, tmp_path):
        """A 2022 (or 2026) solve year fails while the ISO is unmarked."""
        root = _fake_registry(tmp_path, {"r1": {"iso": "CAISO", "years": [2022, 2023]}})
        res = run_d6_quarantine(root)
        assert not res.passed
        assert "2022" in res.failures[0] and "CAISO" in res.failures[0]

    def test_marker_authorizes_one_shot(self, tmp_path):
        """A calibration-complete marker authorizes the holdout score."""
        root = _fake_registry(
            tmp_path,
            {"r1": {"iso": "CAISO", "years": [2022]}},
            complete={"CAISO": {"declared": "2026-08-01"}},
        )
        res = run_d6_quarantine(root)
        assert res.passed
        assert res.rows[0]["verdict"] == "authorized one-shot"

    def test_probes_are_swept_too(self, tmp_path):
        """The sweep covers every registered bundle, not just keepers."""
        root = _fake_registry(
            tmp_path,
            {
                "keeper": {"iso": "PJM", "years": [2023, 2024, 2025]},
                "probe-2026": {"iso": "PJM", "years": [2026]},
            },
        )
        res = run_d6_quarantine(root)
        assert not res.passed
        assert "probe-2026" in res.failures[0]

    def test_audit_keepers_parity(self):
        """audit_keepers' stdlib-inline H1 constants match this module's."""
        from scripts import audit_keepers as ak

        assert ak.CALIBRATION_YEARS == D6_CALIBRATION_YEARS
        assert str(ak.MARKER_FILE).endswith(D6_MARKER_FILE.split("/")[-1])
