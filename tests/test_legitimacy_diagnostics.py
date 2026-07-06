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

    def test_immaterial_class_not_gated(self):
        """Owner directive 2026-07-06: a class dispatching < 2.5 % of total
        load is not force-gated, however high its forced SHARE — a near-idle
        merchant class is not 'the dispatch model'. Reported, flagged
        immaterial, verdict pass."""
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.full((1, HOURS), 100.0)  # 100 % forced
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        # class energy = 100 * 24 = 2400 MWh; 2 % of a 120 000 MWh load.
        res = run_d2(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),
            year=2023,
            total_load_mwh=120_000.0,
        )
        assert res.passed
        row = res.summary[0]
        assert row["immaterial"] is True
        assert row["verdict"] == "pass"
        assert row["forced_share"] == pytest.approx(1.0)

    def test_material_class_still_gated(self):
        """A class above the 2.5 % materiality floor is gated as before."""
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.full((1, HOURS), 100.0)  # 100 % forced
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        # class energy 2400 MWh = 4.8 % of a 50 000 MWh load → material.
        res = run_d2(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),
            year=2023,
            total_load_mwh=50_000.0,
        )
        assert not res.passed
        assert res.summary[0]["immaterial"] is False
        assert res.summary[0]["verdict"] == "FAIL"

    def test_materiality_guard_off_by_default(self):
        """No total_load_mwh → guard disabled, every breach gates (the
        pre-directive behaviour; no denominator must never hide a breach)."""
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.full((1, HOURS), 100.0)
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        res = run_d2(dispatch, min_gen, mech, np.array(["CT_PEAKER"]), year=2023)
        assert not res.passed
        assert res.summary[0]["immaterial"] is False
        assert res.summary[0]["load_share"] is None


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
# D-10 — free-class-only rescore (renewable-bound provenance)
# ---------------------------------------------------------------------------


class TestD10:
    def test_pinned_rows_fail_nothing_but_are_flagged(self, monkeypatch):
        """A delivered-pinned ISO (e.g. MISO) never gates — but every row
        is flagged PINNED so it can't be quoted as skill (audit §4 L1)."""
        import scripts.legitimacy_diagnostics as ld

        monkeypatch.setattr(
            "market_sim.data.renewables.renewable_bound_provenance",
            lambda iso, year, fuel: "delivered_pinned",
        )
        res = ld.run_d10("MISO", [2023, 2024], fuels=("wind", "solar"))
        assert res.passed  # report-only: never fails the gate
        assert len(res.rows) == 4
        assert all(r["pinned"] for r in res.rows)
        assert "4/4" in res.notes[0]

    def test_measured_potential_rows_are_not_pinned(self, monkeypatch):
        """A real HSL-covered ISO-year (e.g. CAISO 2023-2025) reports free."""
        import scripts.legitimacy_diagnostics as ld

        monkeypatch.setattr(
            "market_sim.data.renewables.renewable_bound_provenance",
            lambda iso, year, fuel: "measured_potential",
        )
        res = ld.run_d10("CAISO", [2023], fuels=("wind", "solar"))
        assert res.passed
        assert not any(r["pinned"] for r in res.rows)
        assert "0/2" in res.notes[0]

    def test_forecast_uncurtailed_is_not_pinned_but_distinct(self, monkeypatch):
        """ERCOT 2024/25's grossed-up fallback is real headroom, not the raw
        delivered bound — flagged distinctly, still excluded from PINNED."""
        import scripts.legitimacy_diagnostics as ld

        monkeypatch.setattr(
            "market_sim.data.renewables.renewable_bound_provenance",
            lambda iso, year, fuel: "forecast_uncurtailed",
        )
        res = ld.run_d10("ERCOT", [2024], fuels=("wind", "solar"))
        assert res.passed
        assert all(not r["pinned"] for r in res.rows)
        assert all(r["provenance"] == "forecast_uncurtailed" for r in res.rows)


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

    def test_dominant_nonempty_group_wins_over_first_unit(self):
        """A plant mixing classified units with an unbinned/unclassified one
        takes its MAJORITY real class, never the (possibly first) empty label.

        Root cause of #1488: NEISO plant 546 carried 8 ``ST_GAS`` units + 1
        empty-group unit; the old first-unit pick captured the whole plant into
        the ``''`` bucket, so its dispatch and its binding netload floor were
        attributed to a nuclear-inclusive '' denominator instead of ST_GAS
        (true 2023 share ≈ 3.7 %, reported 0.01 %; rule 20 / #1498 finding 3).
        """
        h = HOURS
        arrays = {
            # The empty-group unit sorts FIRST inside the plant block.
            "min_gen": np.array([[5.0] * h, [5.0] * h, [5.0] * h]),
            "mechanism": np.full((3, h), MECH_RELIABILITY_FLOOR, dtype=np.int8),
            "unit_ids": np.array(["p546_x", "p546_a", "p546_b"]),
            "plant_code": np.array([546, 546, 546]),
            "plant_group": np.array(["", "ST_GAS", "ST_GAS"]),
        }
        _, _, _, groups = aggregate_floors_by_plant(arrays)
        assert groups.tolist() == ["ST_GAS"]

    def test_all_unbinned_plant_stays_unclassified(self):
        """A plant whose units ALL carry no CAMPD group (nuclear / hydro /
        renewables) stays ``''`` — those non-thermal must-run rows are excluded
        from the merchant forced-share summary, not folded into a class."""
        h = HOURS
        arrays = {
            "min_gen": np.array([[9.0] * h, [9.0] * h]),
            "mechanism": np.full((2, h), MECH_NUCLEAR, dtype=np.int8),
            "unit_ids": np.array(["nuke_a", "nuke_b"]),
            "plant_code": np.array([12, 12]),
            "plant_group": np.array(["", ""]),
        }
        _, _, _, groups = aggregate_floors_by_plant(arrays)
        assert groups.tolist() == [""]


class TestD2ClassTotalInvariant:
    """G-06 / #1488: the gated per-class D-2 summary must be identical whether
    the dispatch frame is the FULL fleet (dispatch/*.parquet, carries per-plant
    nuclear/hydro rows) or the run-payload subset (non-fossil represented only
    as scalar aggregates, so those rows are simply absent). The empty ('')
    unclassified bucket is the only place the two frames legitimately differ —
    excluding it from the summary makes every merchant row path-independent.
    """

    @staticmethod
    def _thermal_arrays():
        """A minimal thermal fleet: 2 ST_GAS plants (one part-floored) + 1
        free CT_PEAKER plant. Returns (dispatch, min_gen, mech, klass, npl)."""
        h = HOURS
        dispatch = np.array([[50.0] * h, [100.0] * h, [30.0] * h])
        min_gen = np.array([[50.0] * h, [0.0] * h, [0.0] * h])  # ST_GAS #1 forced
        mech = np.zeros((3, h), dtype=np.int8)
        mech[0] = MECH_RELIABILITY_FLOOR
        klass = np.array(["ST_GAS", "ST_GAS", "CT_PEAKER"], dtype=object)
        npl = np.array([60.0, 120.0, 40.0])
        return dispatch, min_gen, mech, klass, npl

    def test_summary_invariant_to_absent_nonthermal_rows(self):
        payload = self._thermal_arrays()
        res_payload = run_d2(*payload[:4], year=2023, npl=payload[4])

        # The FULL frame appends two per-plant nuclear ('' class) rows that the
        # payload frame never carries — big dispatch, all at a nuclear floor.
        h = HOURS
        d, mg, me, kl, npl = payload
        full = (
            np.vstack([d, [[500.0] * h], [[480.0] * h]]),
            np.vstack([mg, [[500.0] * h], [[480.0] * h]]),
            np.vstack([me, np.full((2, h), MECH_NUCLEAR, dtype=np.int8)]),
            np.concatenate([kl, np.array(["", ""], dtype=object)]),
            np.concatenate([npl, [600.0, 520.0]]),
        )
        res_full = run_d2(*full[:4], year=2023, npl=full[4])

        def _summary_map(res):
            return {
                r["class"]: (r["class_total_twh"], r["forced_share"])
                for r in res.summary
            }

        # No '' bucket ever reaches the gated summary...
        assert "" not in _summary_map(res_payload)
        assert "" not in _summary_map(res_full)
        # ...and every merchant class total + share is byte-identical across
        # the two dispatch frames (the invariant G-06 recompute relies on).
        assert _summary_map(res_payload) == _summary_map(res_full)
        # Sanity: the ST_GAS denominator is the class's own energy (150 units),
        # NOT diluted by the 980 units of nuclear in the full frame.
        assert _summary_map(res_full)["ST_GAS"][1] == pytest.approx(1.0 / 3.0, abs=1e-3)

    def test_empty_class_excluded_but_still_detailed(self):
        """The '' bucket is dropped from the gated summary yet still visible in
        the detail rows (transparency: nuclear/hydro must-run is reported, just
        never gated as a merchant forced share)."""
        h = HOURS
        dispatch = np.array([[500.0] * h, [40.0] * h])
        min_gen = np.array([[500.0] * h, [0.0] * h])
        mech = np.zeros((2, h), dtype=np.int8)
        mech[0] = MECH_NUCLEAR
        klass = np.array(["", "CT_PEAKER"], dtype=object)
        res = run_d2(
            dispatch, min_gen, mech, klass, year=2023, npl=np.array([600.0, 50.0])
        )
        assert not any(r["class"] == "" for r in res.summary)
        assert any(r["class"] == "" for r in res.rows)


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


# ---------------------------------------------------------------------------
# D-2 recompute-vs-committed (gap G-06)
# ---------------------------------------------------------------------------


def _fake_keeper_repo(tmp_path, run_id, iso, years, committed_summary):
    """Build a minimal repo root: keepers.json + sidecar + committed bundle."""
    reg = tmp_path / "frontend" / "data" / "backcast" / "registry"
    reg.mkdir(parents=True)
    (tmp_path / "frontend" / "data" / "backcast" / "keepers.json").write_text(
        json.dumps({"keepers": [run_id]})
    )
    bundle_rel = f"results/calibration/{run_id}"
    (reg / f"{run_id}.json").write_text(
        json.dumps({"iso": iso, "years": years, "bundle": bundle_rel})
    )
    bundle = tmp_path / bundle_rel
    bundle.mkdir(parents=True)
    (bundle / "legitimacy_diagnostics.json").write_text(
        json.dumps({"diagnostics": {"D2": {"summary": committed_summary}}})
    )
    return tmp_path


class TestD2KeepersVerify:
    def test_matching_recompute_passes(self, tmp_path, monkeypatch):
        """A recompute that reproduces the committed share is a pass, even
        when that committed share already FAILs its own D-2 threshold —
        this gate checks staleness, not the threshold itself."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.111},
        ]
        root = _fake_keeper_repo(tmp_path, "keeper1", "ERCOT", [2023], committed)
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.111}
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert res.passed
        assert res.rows[0]["verdict"] == "pass"

    def test_discrepancy_fails(self, tmp_path, monkeypatch):
        """A recomputed share that disagrees with the committed one fails —
        the committed artifact has drifted from the bundle it describes."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.111},
        ]
        root = _fake_keeper_repo(tmp_path, "keeper1", "ERCOT", [2023], committed)
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.60}
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert not res.passed
        assert "keeper1" in res.failures[0]
        assert "0.111" in res.failures[0] and "0.6" in res.failures[0]

    def test_missing_committed_artifact_notes_not_fails(self, tmp_path, monkeypatch):
        """A keeper with no committed legitimacy_diagnostics.json yet (e.g.
        G-01/G-02's MISO gap) is noted, not failed — that absence is a
        separate, already-tracked gap."""
        import scripts.legitimacy_diagnostics as ld

        reg = tmp_path / "frontend" / "data" / "backcast" / "registry"
        reg.mkdir(parents=True)
        (tmp_path / "frontend" / "data" / "backcast" / "keepers.json").write_text(
            json.dumps({"keepers": ["keeper2"]})
        )
        (reg / "keeper2.json").write_text(
            json.dumps(
                {
                    "iso": "MISO",
                    "years": [2023],
                    "bundle": "results/calibration/keeper2",
                }
            )
        )
        (tmp_path / "results" / "calibration" / "keeper2").mkdir(parents=True)
        res = ld.run_d2_keepers_verify(tmp_path)
        assert res.passed
        assert not res.rows
        assert "keeper2" in res.notes[0]

    def test_no_keepers_file_passes_trivially(self, tmp_path):
        """No keepers.json (e.g. a from-scratch repo checkout) is a no-op."""
        import scripts.legitimacy_diagnostics as ld

        res = ld.run_d2_keepers_verify(tmp_path)
        assert res.passed

    def test_class_dropped_by_zero_total_filter_is_not_a_discrepancy(
        self, tmp_path, monkeypatch
    ):
        """A class present with forced_share 0.0 in one summary and absent
        from the other (run_d2's own total_by_class <= 0 filter drops rows
        with zero dispatch) is the same substantive fact, not drift — e.g.
        a non-thermal 'hydro' row committed at 0.0 that the recompute's
        floor-rebuild fallback doesn't emit at all."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.10},
            {"year": 2023, "class": "hydro", "forced_share": 0.0},
        ]
        root = _fake_keeper_repo(tmp_path, "keeper1", "PJM", [2023], committed)
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.10}
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert res.passed

    def test_a_real_nonzero_class_missing_on_one_side_still_fails(
        self, tmp_path, monkeypatch
    ):
        """Missing-as-zero must not mask a genuine nonzero-vs-absent drift."""
        import scripts.legitimacy_diagnostics as ld

        committed = [{"year": 2023, "class": "CT_PEAKER", "forced_share": 0.10}]
        root = _fake_keeper_repo(tmp_path, "keeper1", "PJM", [2023], committed)
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {"year": 2023, "class": "CT_PEAKER", "forced_share": 0.10},
                        {"year": 2023, "class": "ST_GAS", "forced_share": 0.35},
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert not res.passed
        assert any("ST_GAS" in f for f in res.failures)
