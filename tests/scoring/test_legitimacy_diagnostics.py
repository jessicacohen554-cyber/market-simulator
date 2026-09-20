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
    MECH_FIRM_IMPORT,
    MECH_NUCLEAR,
    MECH_RELIABILITY_FLOOR,
    ensure_mechanism,
)
from market_sim.model.transmission import _distribute_group_floor
from scripts.legitimacy_diagnostics import (
    aggregate_floors_by_plant,
    build_plant_matrices,
    at_floor_mask,
    d1_shape_metrics,
    run_d1,
    run_d2,
    run_d4,
    run_d5,
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
        """Owner directive 2026-07-06 (rubric v2.1): a class dispatching below
        ``PROTECTIVE_MIN_LOAD_FRAC`` (2 %) of total load is not force-gated,
        however high its forced SHARE — a near-idle merchant class is not 'the
        dispatch model'. Reported, flagged immaterial, verdict pass."""
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.full((1, HOURS), 100.0)  # 100 % forced
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        # class energy = 100 * 24 = 2400 MWh; 1.2 % of a 200 000 MWh load < 2 %.
        res = run_d2(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),
            year=2023,
            total_load_mwh=200_000.0,
        )
        assert res.passed
        row = res.summary[0]
        assert row["immaterial"] is True
        assert row["verdict"] == "pass"
        assert row["forced_share"] == pytest.approx(1.0)

    def test_material_class_still_gated(self):
        """A class above the ``PROTECTIVE_MIN_LOAD_FRAC`` (2 %) materiality
        floor is gated as before."""
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

    def test_2pt2pct_class_gated_identically_by_quarantine_and_rubric(self):
        """One materiality line (CLAUDE.md rules 17/20/23): a merchant class at
        2.2 % of ISO load — between the OLD duplicate 2.5 % quarantine constant
        and the rubric's 2.0 % — must be MATERIAL (gated) on BOTH the D-2
        quarantine side (``run_d2``) and the C7/C8 rubric side
        (``calibration_verdict._class_load_share`` vs
        ``PROTECTIVE_MIN_LOAD_FRAC``). Before the unify this class was skipped
        by the quarantine gate yet scored by the rubric — the 0.5 pp divergence
        this fix closes."""
        import scripts.legitimacy_diagnostics as ld
        from scripts import calibration_verdict as cv

        # Both sides read the SAME constant, not two copies.
        assert ld.PROTECTIVE_MIN_LOAD_FRAC == cv.PROTECTIVE_MIN_LOAD_FRAC == 0.02

        # --- Quarantine side: 2.2 % of load, 100 % force-floored ---
        dispatch = np.full((1, HOURS), 100.0)
        min_gen = np.full((1, HOURS), 100.0)
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        class_mwh = 100.0 * HOURS
        total_load = class_mwh / 0.022  # → load_share = 2.2 %
        res = run_d2(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),
            year=2023,
            total_load_mwh=total_load,
        )
        gate_row = res.summary[0]
        assert gate_row["load_share"] == pytest.approx(0.022, abs=1e-4)
        gate_immaterial = gate_row["immaterial"]
        assert gate_immaterial is False  # >= 2 % → gated, verdict FAIL
        assert gate_row["verdict"] == "FAIL"

        # --- Rubric side: same 2.2 % share via the C7/C8 materiality helper ---
        ypay = {"gmModel": {"CT_PEAKER": 2.2}, "lmp": {"z": {"d": 100.0}}}
        ybench = {"classFull": {"CT_PEAKER": 2.2, "_rest": 97.8}}
        rubric_share = cv._class_load_share("CT_PEAKER", ypay, ybench)
        assert rubric_share == pytest.approx(0.022, abs=1e-4)
        rubric_immaterial = rubric_share < cv.PROTECTIVE_MIN_LOAD_FRAC
        assert rubric_immaterial is False  # rubric also gates

        # Identical material/immaterial verdict on both sides — the whole point.
        assert gate_immaterial == rubric_immaterial

    def test_materiality_denominator_is_max_model_actual(self):
        """Rule-20 amendment: the D-2 materiality denominator is
        ``max(model, actual)`` class energy (mirroring ``score_shape`` /
        ``_class_load_share``), so a class the model nearly zeroes but whose
        CAMPD actual is material stays gated — the actual side keeps it scored."""
        # Model dispatches 50 MW flat (1200 MWh, 1.2 % of load) → below the
        # line on the model side alone; but the CAMPD actual is 3 % of load.
        dispatch = np.full((1, HOURS), 50.0)
        min_gen = np.full((1, HOURS), 50.0)  # 100 % forced on the model side
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        total_load = 100_000.0
        actual = {"CT_PEAKER": 0.03 * total_load}  # 3 % of load → material
        res = run_d2(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),
            year=2023,
            total_load_mwh=total_load,
            actual_by_class=actual,
        )
        row = res.summary[0]
        # load_share uses max(model=1200, actual=3000) / 100000 = 3 %.
        assert row["load_share"] == pytest.approx(0.03, abs=1e-4)
        assert row["immaterial"] is False
        assert row["verdict"] == "FAIL"

        # Without the actual side, the same near-zeroed model class is immaterial
        # — proving the actual side (not the model side) is doing the gating.
        res_model_only = run_d2(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),
            year=2023,
            total_load_mwh=total_load,
        )
        assert res_model_only.summary[0]["immaterial"] is True

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
        """A 24 h CT floor with an evening-justified driver → ~67 % off-window.

        The reliability_floor × CT_PEAKER justified window is [14, 22) (the
        driver-derived HB14-21 ramp; G-05), so 8 of 24 h are in-window and
        16/24 fall outside — a 24h floor still fails heavily.
        """
        dispatch = np.full((1, HOURS), 40.0)
        min_gen = np.full((1, HOURS), 40.0)
        mech = np.full((1, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        res = run_d4(dispatch, min_gen, mech, np.array(["CT_PEAKER"]), year=2023)
        assert not res.passed
        assert res.rows[0]["offwindow_share"] == pytest.approx(16 / 24, abs=1e-3)

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


class TestD4PerUnitConductRider:
    """The rider adopted with K6' at nyiso-140 §5 (owner, 2026-08-16).

    D-4's off-window test is tautological for an h0-23 floor, so K6' leg (a)
    and rule 20's grounded-above-budget escalation both rested on a check that
    could not fire. The rider restores rule 17's substance at per-unit grain:
    a floored plant whose own measured median output over the declared window
    is exactly zero fails provenance.
    """

    # ST_GAS × reliability_floor is the D4_WINDOWS h0-23 row the NYISO keeper
    # actually carries (nyiso-139b §3); MECH_RELIABILITY_FLOOR × CT_PEAKER is
    # the [14, 22) row, used here for the sub-daily scope check.
    KLASS = np.array(["ST_GAS"])

    def _floored(self, n=1):
        dispatch = np.full((n, HOURS), 40.0)
        min_gen = np.full((n, HOURS), 40.0)
        mech = np.full((n, HOURS), MECH_RELIABILITY_FLOOR, dtype=np.int8)
        return dispatch, min_gen, mech

    def test_laid_up_plant_fails_provenance(self):
        """The Port Jefferson signature: floored all year, meter flat zero."""
        dispatch, min_gen, mech = self._floored()
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["2517"],
            bench_pl={"2517": {"npl": 100.0, "mw": np.zeros(HOURS)}},
        )
        assert not res.passed
        conduct = [r for r in res.rows if r["check"] == "unit-conduct"]
        assert len(conduct) == 1
        assert conduct[0]["plant"] == "2517"
        assert conduct[0]["verdict"] == "FAIL"
        assert conduct[0]["measured_zero_share"] == 1.0
        # The window row itself still passes — which is exactly the blindness
        # the rider exists to cover.
        window = [r for r in res.rows if r["check"] == "window"]
        assert window[0]["verdict"] == "pass"
        assert window[0]["offwindow_share"] == 0.0

    def test_running_plant_passes(self):
        dispatch, min_gen, mech = self._floored()
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["8906"],
            bench_pl={"8906": {"npl": 100.0, "mw": np.full(HOURS, 55.0)}},
        )
        assert res.passed
        conduct = [r for r in res.rows if r["check"] == "unit-conduct"]
        assert len(conduct) == 1 and conduct[0]["verdict"] == "pass"

    def test_majority_zero_still_fails_on_the_median(self):
        """Offline in > half the window hours ⇒ median 0 ⇒ FAIL.

        The statistic is threshold-free on purpose (rule 5 [R-NO-MAGIC]):
        "the meter says it is offline in at least half the hours the floor
        asserts it must be online".
        """
        dispatch, min_gen, mech = self._floored()
        meas = np.zeros(HOURS)
        meas[: HOURS // 3] = 60.0  # online a third of the year
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["1"],
            bench_pl={"1": {"npl": 100.0, "mw": meas}},
        )
        assert not res.passed

    def test_minority_zero_passes(self):
        dispatch, min_gen, mech = self._floored()
        meas = np.full(HOURS, 60.0)
        meas[: HOURS // 3] = 0.0  # offline a third of the year
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["1"],
            bench_pl={"1": {"npl": 100.0, "mw": meas}},
        )
        assert res.passed

    def test_unmetered_plant_never_fails_and_is_disclosed(self):
        dispatch, min_gen, mech = self._floored()
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["nohydrometer"],
            bench_pl={},
        )
        assert res.passed
        assert not [r for r in res.rows if r["check"] == "unit-conduct"]
        assert any("no measured series" in n for n in res.notes)

    def test_rider_scoped_to_all_hours_windows_only(self):
        """A sub-daily window can already fail off-window; no rider row."""
        dispatch, min_gen, mech = self._floored()
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            np.array(["CT_PEAKER"]),  # the [14, 22) row
            year=2023,
            pids=["1"],
            bench_pl={"1": {"npl": 100.0, "mw": np.zeros(HOURS)}},
        )
        assert not [r for r in res.rows if r["check"] == "unit-conduct"]

    def test_skipped_without_bench_and_says_so(self):
        dispatch, min_gen, mech = self._floored()
        res = run_d4(dispatch, min_gen, mech, self.KLASS, year=2023)
        assert res.passed
        assert any("NOT RUN" in n for n in res.notes)

    def test_substituted_row_is_excluded_and_disclosed(self):
        """A row whose dispatch IS its floor cannot carry a conduct verdict.

        pjm-149 / caiso-155 substitute ``dispatch := min_gen`` for plants the
        active source carries no series for, which makes the at-floor set the
        whole floor-positive set by construction — "indeterminate on a fail".
        """
        dispatch, min_gen, mech = self._floored()
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["2517"],
            bench_pl={"2517": {"npl": 100.0, "mw": np.zeros(HOURS)}},
            substituted=np.array([True]),
        )
        assert res.passed
        assert not [r for r in res.rows if r["check"] == "unit-conduct"]
        assert any("SUBSTITUTED" in n for n in res.notes)

    def test_ct_only_cems_plant_is_not_convicted(self):
        """The benchmark's own CT-only flag means its hourly meter is partial.

        ``ct_only`` marks EIA-923 net > 1.1x CAMPD gross, i.e. a plant the
        BENCHMARK scores on EIA-923 monthly because the CAMPD hourly series is
        incomplete. A zero median there is a metering artifact, not conduct
        (rule 14 ``[R-ACCURATE]``).
        """
        dispatch, min_gen, mech = self._floored()
        b = {"npl": 65.0, "mw": np.zeros(HOURS), "ct_only": True}
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["50744"],
            bench_pl={"50744": b},
        )
        assert res.passed
        assert not [r for r in res.rows if r["check"] == "unit-conduct"]
        assert any("CT-only CEMS flag" in n for n in res.notes)

    def test_driver_gated_limb_scored_on_its_binding_hours(self):
        """A limb inside an h0-23 window but gated by its own driver.

        NYISO's ``Capital_Hudson × ST_GAS`` tmax limb (threshold 31.1 °C, no
        start/end hour) binds only on design-cooling hours. A unit that runs
        exactly then has an ANNUAL median of 0 — a window-wide test would fail
        it — but its conduct in the hours the floor actually forces it is
        precisely what the driver predicts, so it must PASS.
        """
        dispatch = np.zeros((1, HOURS))
        min_gen = np.zeros((1, HOURS))
        mech = np.zeros((1, HOURS), dtype=np.int8)
        hot = np.zeros(HOURS, dtype=bool)
        hot[13:19] = True  # the limb's own driver window (design-cooling hours)
        dispatch[0, hot] = 40.0
        min_gen[0, hot] = 40.0
        mech[0, hot] = MECH_RELIABILITY_FLOOR
        meas = np.zeros(HOURS)
        meas[hot] = 70.0  # the meter agrees: it runs exactly then
        res = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["2625"],
            bench_pl={"2625": {"npl": 621.0, "mw": meas}},
        )
        assert res.passed
        conduct = [r for r in res.rows if r["check"] == "unit-conduct"]
        assert len(conduct) == 1
        assert conduct[0]["binding_hours"] == 6
        assert conduct[0]["measured_median_mw"] == 70.0
        # And the same unit DOES fail when it is idle in those very hours.
        res2 = run_d4(
            dispatch,
            min_gen,
            mech,
            self.KLASS,
            year=2023,
            pids=["2625"],
            bench_pl={"2625": {"npl": 621.0, "mw": np.zeros(HOURS)}},
        )
        assert not res2.passed


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
# D-5 — NYISO downstate parity, measured on the REAL entry-point sources
#
# nyiso-102. The NYISO downstate mechanisms were wired only in the backcast
# orchestrator, so D-5 read nyiso_local_selfsupply as an UNDECLARED
# backcast-only difference and FAILed on every NYISO keeper through nyiso-100.
# Declaring it would have been wrong: the LMIC / local-reliability rule is
# NYISO market design that scales with load and republishes every capability
# year, so it is forward-reproducible (rule 13 [R-MEASURED]) and its registry
# row is mode="both", declared=False. The fix was to close the wiring gap in
# src/market_sim/runner.py. These tests read the REAL sources so the drift
# cannot silently return.
# ---------------------------------------------------------------------------


class TestD5NyisoDownstateParity:
    """The NYISO downstate family must be reachable from BOTH orchestrators."""

    # Keeper-shaped config (2026-07-30-nyiso-100-silretire): all three
    # downstate flags on, no declared-overlay toggles that would mask a gap.
    CFG = {
        "outage_source": "estimated",
        "nyiso_local_selfsupply": True,
        "nyiso_li_lcr_tsl": True,
        "nyiso_nyc_lcr_tsl": True,
        "reliability_floor": False,
        "ct_netload_drag": False,
        "gas_st_netload_drag": False,
    }

    @staticmethod
    def _entry_sources():
        from scripts.legitimacy_diagnostics import REPO_ROOT

        return (
            (REPO_ROOT / "scripts/run_calibration.py").read_text(),
            (REPO_ROOT / "src/market_sim/runner.py").read_text(),
        )

    def test_keeper_config_has_no_undeclared_parity_gap(self):
        """The real sources clear D-5 for a NYISO keeper-shaped config."""
        backcast_src, forecast_src = self._entry_sources()
        res = run_d5(self.CFG, "NYISO", backcast_src, forecast_src)
        assert res.passed, res.failures
        # Every emitted row must be a sanctioned overlay, never a bare FAIL.
        assert all(r["verdict"] == "declared" for r in res.rows)
        assert not any(r["mechanism"] == "nyiso_local_selfsupply" for r in res.rows)

    def test_selfsupply_floor_wired_in_both_orchestrators(self):
        backcast_src, forecast_src = self._entry_sources()
        for src in (backcast_src, forecast_src):
            assert "inject_nyiso_local_selfsupply" in src

    def test_lcr_tsl_caps_travel_with_the_floor(self):
        """Anti-gaming guard (rule 1 [R-STRUCT]).

        ``nyiso_li_lcr_tsl`` is exactly what excludes Long_Island — the only
        pocket in ``NYISO_LOCAL_SELFSUPPLY_FRAC`` — from the self-supply floor
        (rule 19 [R-ONE-MECH]). Wiring the floor into an orchestrator WITHOUT
        the published-limit caps would leave a run carrying the keeper's config
        with NEITHER mechanism on the downstate pocket: D-5 green, real gap
        still open. The caps must therefore appear wherever the floor does.
        """
        for src in self._entry_sources():
            assert "inject_nyiso_local_selfsupply" in src
            assert "apply_nyiso_li_tsl_import_cap" in src
            assert "apply_nyiso_nyc_tsl_import_cap" in src

    def test_backcast_chain_never_loads_the_forecast_orchestrator(self):
        """Why the fix cannot perturb a backcast solve.

        The forecast orchestrator (``market_sim.runner``) is not on the
        calibration import graph at all, so editing it is byte-identical for
        every backcast run by construction — the empirical zero-delta control
        (nyiso-102) confirms the same thing on a full 3-year solve.

        Probed in a CLEAN subprocess (2026-07-30): the claim is about what
        ``scripts.run_calibration`` pulls in BY ITSELF, which is only
        observable in an interpreter that has imported nothing else. The
        former in-process form read the whole worker's accumulated
        ``sys.modules``, so under ``pytest -n`` it failed whenever an
        unrelated test happened to import ``market_sim.runner`` into the same
        worker first — a test-ORDER artifact, not an import-graph regression.
        Exit code 3 (not 1) signals the leak so an import crash stays
        distinguishable from a positive detection.
        """
        import subprocess
        import sys

        from market_sim.config.paths import REPO_ROOT

        probe = (
            "import sys; import scripts.run_calibration; "
            "sys.exit(3 if 'market_sim.runner' in sys.modules else 0)"
        )
        proc = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        assert proc.returncode != 3, (
            "importing scripts.run_calibration pulled market_sim.runner onto "
            "the calibration import graph: a backcast solve now loads the "
            "forecast orchestrator, so editing it is no longer byte-identical "
            "for backcast runs."
        )
        assert proc.returncode == 0, (
            f"import probe crashed (rc={proc.returncode}), so the import graph "
            f"was never checked:\n{proc.stderr}"
        )


# ---------------------------------------------------------------------------
# D-5 — NYISO Central-East measured TTC, the DECLARED-OVERLAY half
#
# nyiso-104. The measured Central-East DAM TTC tables have been live in every
# NYISO backcast since they landed but carried no D-5 row at all, so parity was
# blind to them. Classification (rule 13 [R-MEASURED]) resolved OPPOSITE to
# nyiso_local_selfsupply above: this one is a genuine backcast overlay, so the
# fix is a declared registry row, NOT a forecast wiring. These tests pin both
# halves of that verdict — the declaration, and the evidence it rests on.
# ---------------------------------------------------------------------------


class TestD5NyisoCentralEastTtc:
    """The measured Central-East envelope is declared, scoped, and not wired forward."""

    ROW = "nyiso_central_east_measured_ttc"
    # Keeper-shaped (2026-07-30-nyiso-100-silretire) minus every toggle that
    # would emit an unrelated declared row and blur what is being asserted.
    CFG = {
        "outage_source": "estimated",
        "reliability_floor": False,
        "ct_netload_drag": False,
        "gas_st_netload_drag": False,
    }

    @staticmethod
    def _entry_sources():
        from scripts.legitimacy_diagnostics import REPO_ROOT

        return (
            (REPO_ROOT / "scripts/run_calibration.py").read_text(),
            (REPO_ROOT / "src/market_sim/runner.py").read_text(),
        )

    def _spec(self):
        from scripts.legitimacy_diagnostics import D5_REGISTRY

        return next(s for s in D5_REGISTRY if s.name == self.ROW)

    def test_registered_as_a_declared_backcast_overlay(self):
        spec = self._spec()
        assert spec.declared is True
        assert spec.mode == "backcast_only"
        assert spec.iso == "NYISO"
        # No ScenarioConfig flag gates it — it is unconditional for any NYISO
        # backcast year with a table, which is exactly why it needs iso scoping.
        assert spec.toggle is None

    def test_emitted_as_declared_on_the_real_sources(self):
        backcast_src, forecast_src = self._entry_sources()
        res = run_d5(self.CFG, "NYISO", backcast_src, forecast_src)
        assert res.passed, res.failures
        rows = [r for r in res.rows if r["mechanism"] == self.ROW]
        assert rows, "the Central-East overlay is invisible to D-5 again"
        assert rows[0]["difference"] == "backcast-only"
        assert rows[0]["verdict"] == "declared"

    def test_scoped_to_nyiso_only(self):
        """An always-on ISO-exclusive overlay must not report itself elsewhere."""
        backcast_src, forecast_src = self._entry_sources()
        for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NEISO"):
            res = run_d5(self.CFG, iso, backcast_src, forecast_src)
            assert not any(r["mechanism"] == self.ROW for r in res.rows), (
                f"the NYISO Central-East overlay claims to be active in {iso}"
            )

    def test_not_wired_into_the_forecast_orchestrator(self):
        """The declaration is only honest while the helpers stay backcast-only.

        If a future session wires these tables into ``runner.py``, the overlay
        stops being a declared backcast difference and this test must fail
        LOUDLY rather than let a forecast year inherit one historical year's
        transmission-outage schedule (see the classification test below).
        """
        backcast_src, forecast_src = self._entry_sources()
        for sym in ("apply_iso_year_ttc", "apply_iso_monthly_ttc"):
            assert sym in backcast_src
            assert sym not in forecast_src, (
                f"{sym} is now called from the forecast orchestrator; the "
                "nyiso-104 classification (rule 13) must be re-adjudicated "
                "before this is allowed to stand"
            )

    def test_within_year_shape_is_not_a_reproducible_seasonal_rating(self):
        """The measured evidence the OVERLAY verdict rests on (nyiso-104).

        A published seasonal rating is recomputed the same way every year, so
        on an unchanged network its level-normalized monthly shape must repeat
        (r ~ 0.9+). 2024 and 2025 share the post-AC-Transmission topology and
        correlate at only r = +0.21 — the signature of that year's own approved
        transmission outages, which have no forward analogue.

        Guards the classification against a silent data refresh: if updated
        postings ever DID show a reproducible seasonal shape, the overlay would
        have to be re-adjudicated as a forward mechanism, and this fails first.
        """
        import statistics as st

        from market_sim.config.constants import NYISO_INTERFACE_TTC_BY_MONTH

        link = ("Upstate_West", "Capital_Hudson")
        shapes = {}
        for year in (2024, 2025):  # the two fully post-upgrade years
            vals = NYISO_INTERFACE_TTC_BY_MONTH[year][link]
            mu = st.mean(vals)
            shapes[year] = [v / mu for v in vals]
        a, b = shapes[2024], shapes[2025]
        ma, mb = st.mean(a), st.mean(b)
        num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
        den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
        r = num / den
        assert r < 0.5, (
            f"same-topology monthly shape now correlates at r={r:+.3f}; the "
            "series may be a reproducible seasonal rating after all, which "
            "would make it a forward MECHANISM rather than the declared "
            "backcast overlay nyiso-104 classified it as"
        )


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
        pids, floor_sum, mech_plant, groups, _fk = aggregate_floors_by_plant(arrays)
        assert pids.tolist() == ["7"]  # string keys since caiso-155
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
        _, _, _, groups, _ = aggregate_floors_by_plant(arrays)
        assert groups.tolist() == ["ST_GAS"]

    def test_plant_class_vote_is_capacity_weighted_not_row_count(self):
        """nyiso-233: the class carrying the most CAPACITY names the plant.

        The measured NYISO keeper case, at its real magnitudes: Ravenswood
        (plant 2500) carries 1724.8 MW of ``ST_GAS`` in 4 LP rows against
        268.5 MW of ``CC_REGULAR`` in 7 — 6.4:1 on capacity, 4-7 against on
        rows. The superseded ROW-COUNT vote labelled an 87 %-steam site
        ``CC_REGULAR``, moving its whole dispatch into the wrong class
        denominator and flipping C8
        (``docs/FINDING-d2-plant-class-is-a-tranche-count-vote-2026-09-13.md``).
        """
        h = HOURS
        pmax = [431.2] * 4 + [38.36] * 7
        groups_in = ["ST_GAS"] * 4 + ["CC_REGULAR"] * 7
        arrays = {
            "min_gen": np.zeros((11, h)),
            "mechanism": np.zeros((11, h), dtype=np.int8),
            "unit_ids": np.array([f"u{i}" for i in range(11)]),
            "plant_code": np.full(11, 2500),
            "plant_group": np.array(groups_in),
            "pmax": np.array(pmax),
        }
        assert sum(pmax[:4]) > sum(pmax[4:])  # capacity says ST_GAS
        assert len(pmax[:4]) < len(pmax[4:])  # rows say CC_REGULAR
        _, _, _, groups, _ = aggregate_floors_by_plant(arrays)
        assert groups.tolist() == ["ST_GAS"]

    def test_plant_class_vote_is_invariant_to_tranche_count(self):
        """The defining property of the repair: splitting a class into more
        bands cannot move the label, because bands partition that class's
        capacity however many of them there are. This is the exact failure the
        row-count vote had — NYISO's ``ST_GAS`` econ ladder collapsing 8 bands
        to 4 moved ~2.5 GW between denominators with no physical change.
        """
        h = HOURS

        def label(n_st: int, n_cc: int) -> str:
            arrays = {
                "min_gen": np.zeros((n_st + n_cc, h)),
                "mechanism": np.zeros((n_st + n_cc, h), dtype=np.int8),
                "unit_ids": np.array([f"u{i}" for i in range(n_st + n_cc)]),
                "plant_code": np.full(n_st + n_cc, 2500),
                "plant_group": np.array(["ST_GAS"] * n_st + ["CC_REGULAR"] * n_cc),
                # Same TOTAL capacity per class, re-sliced into more/fewer bands.
                "pmax": np.array([1724.8 / n_st] * n_st + [268.5 / n_cc] * n_cc),
            }
            _, _, _, groups, _ = aggregate_floors_by_plant(arrays)
            return groups[0]

        assert label(8, 7) == "ST_GAS"
        assert label(4, 7) == "ST_GAS"  # the ladder collapse — row count flipped here
        assert label(1, 20) == "ST_GAS"  # and it survives any re-slicing

    def test_plant_class_vote_falls_back_to_row_count_without_pmax(self):
        """Arrays with no ``pmax`` (a pre-nyiso-233 ``floors/*.npz`` whose
        backfill was unavailable) score on the superseded row-count basis. The
        caller records ``plant_class_vote_basis="row_count_fallback"`` so the
        degradation is never silent; the fallback itself must still work.
        """
        h = HOURS
        arrays = {
            "min_gen": np.zeros((11, h)),
            "mechanism": np.zeros((11, h), dtype=np.int8),
            "unit_ids": np.array([f"u{i}" for i in range(11)]),
            "plant_code": np.full(11, 2500),
            "plant_group": np.array(["ST_GAS"] * 4 + ["CC_REGULAR"] * 7),
        }
        _, _, _, groups, _ = aggregate_floors_by_plant(arrays)
        assert groups.tolist() == ["CC_REGULAR"]

    def test_plant_class_vote_zero_capacity_falls_back_to_row_count(self):
        """A fully-derated site whose classified rows all carry zero ``pmax``
        cannot be voted on by capacity, so that ONE plant reverts to the row
        count — never to the alphabetically-first label a zero-weight
        ``argmax`` would otherwise pick (``CC_REGULAR`` sorts before
        ``ST_GAS``).
        """
        h = HOURS
        arrays = {
            "min_gen": np.zeros((5, h)),
            "mechanism": np.zeros((5, h), dtype=np.int8),
            "unit_ids": np.array([f"u{i}" for i in range(5)]),
            "plant_code": np.full(5, 999),
            "plant_group": np.array(["ST_GAS"] * 3 + ["CC_REGULAR"] * 2),
            "pmax": np.zeros(5),
        }
        _, _, _, groups, _ = aggregate_floors_by_plant(arrays)
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
        _, _, _, groups, _ = aggregate_floors_by_plant(arrays)
        assert groups.tolist() == [""]

    def test_floored_pseudo_unit_rides_as_own_row(self):
        """caiso-151 §F / caiso-155: a plant_code-0 tranche carrying a firm
        floor was DROPPED from the plant matrix; it now rides as its own
        ``u:<unit_id>`` row with its floor, mechanism and (empty) class, while
        the plant_code > 0 aggregation is byte-identical to before."""
        h = HOURS
        arrays = {
            "min_gen": np.array([[30.0] * h, [900.0] * h]),
            "mechanism": np.array(
                [[MECH_RELIABILITY_FLOOR] * h, [MECH_FIRM_IMPORT] * h],
                dtype=np.int8,
            ),
            "unit_ids": np.array(["p7_committed", "NYISO_external_HQ_hydro"]),
            "plant_code": np.array([7, 0]),
            "plant_group": np.array(["CT_PEAKER", ""]),
        }
        pids, floor_sum, mech_plant, groups, _fk = aggregate_floors_by_plant(arrays)
        assert pids.tolist() == ["7", "u:NYISO_external_HQ_hydro"]
        assert (floor_sum[0] == 30.0).all()
        assert (floor_sum[1] == 900.0).all()
        assert (mech_plant[1] == MECH_FIRM_IMPORT).all()
        assert groups.tolist() == ["CT_PEAKER", ""]

    def test_unfloored_pseudo_units_stay_excluded(self):
        """plant_code <= 0 rows with NO floor (economic import bands, export
        sinks) stay out of the matrix — they must not perturb any denominator
        (PREREG-caiso155 §2 P3)."""
        h = HOURS
        arrays = {
            "min_gen": np.array([[5.0] * h, [0.0] * h, [0.5] * h]),
            "mechanism": np.array(
                [[MECH_RELIABILITY_FLOOR] * h, [0] * h, [0] * h], dtype=np.int8
            ),
            "unit_ids": np.array(["p9_econ", "WECC_import_spot", "WECC_export"]),
            "plant_code": np.array([9, 0, 0]),
            "plant_group": np.array(["ST_GAS", "", ""]),
        }
        pids, floor_sum, _, _, _ = aggregate_floors_by_plant(arrays)
        assert pids.tolist() == ["9"]
        assert floor_sum.shape[0] == 1

    def test_pseudo_unit_rows_report_but_never_gate_d2(self):
        """The pseudo-unit floor appears in D-2 DETAIL rows (visibility) under
        its non-thermal mechanism and the ``''`` class, and produces NO gated
        summary row — C8 arithmetic is invariant (PREREG-caiso155 §3.4)."""
        h = HOURS
        disp = np.array([[50.0] * h, [900.0] * h])
        floors = np.array([[0.0] * h, [900.0] * h])
        mechs = np.array([[0] * h, [MECH_FIRM_IMPORT] * h], dtype=np.int8)
        klass = np.array(["CT_PEAKER", ""], dtype=object)
        res = run_d2(disp, floors, mechs, klass, year=2024)
        firm_rows = [r for r in res.rows if r["mechanism"] == "firm_import"]
        assert len(firm_rows) == 1
        assert firm_rows[0]["class"] == ""
        assert firm_rows[0]["forced_twh"] == pytest.approx(900.0 * h / 1e6)
        assert all(row["class"] != "" for row in res.summary)
        assert res.passed

    def test_pseudo_unit_rows_visible_to_d4_all_hours_window(self):
        """The firm_import floor is D-4-visible under its all-hours window
        (caiso-151 added the D4_WINDOWS row; caiso-155 makes the rows reach
        it) and cannot fail off-window by construction."""
        h = HOURS
        disp = np.array([[900.0] * h])
        floors = np.array([[900.0] * h])
        mechs = np.array([[MECH_FIRM_IMPORT] * h], dtype=np.int8)
        klass = np.array([""], dtype=object)
        res = run_d4(disp, floors, mechs, klass, year=2024)
        row = next(r for r in res.rows if r["floor"] == "firm_import")
        assert row["offwindow_share"] == 0.0
        assert row["verdict"] == "pass"
        assert row["floored_twh"] == pytest.approx(900.0 * h / 1e6)

    def test_g06_bridge_family_covers_every_p0_pattern_bridge(self):
        """caiso-155: the G-06 recompute must subtract EVERY P0-run-pattern
        bridge from the committed side, not just the CAISO RA leg — nyiso109's
        armed nyiso_gas_commitment_bridge carries 3-5 pp of CC_REGULAR's gated
        share and no fleet_only rebuild can reproduce it."""
        from market_sim.data.floor_mechanisms import (
            MECH_GAS_COMMITMENT_BRIDGE,
            MECH_MISO_COAL_NIGHT_FLOOR,
            MECH_NYISO_GAS_COMMITMENT_BRIDGE,
            MECH_RA_MUSTOFFER,
            MECH_SPP_GAS_COMMITMENT_BRIDGE,
        )
        from scripts.legitimacy_diagnostics import BRIDGE_MECHS

        # SPP-44 added the SPP leg (same detector, same P0-pattern anchor, so
        # the same "no fleet_only rebuild can reproduce it" property).
        assert set(BRIDGE_MECHS) == {
            MECH_RA_MUSTOFFER,
            MECH_GAS_COMMITMENT_BRIDGE,
            MECH_NYISO_GAS_COMMITMENT_BRIDGE,
            MECH_MISO_COAL_NIGHT_FLOOR,
            MECH_SPP_GAS_COMMITMENT_BRIDGE,
        }

    def test_rebuild_rename_map_threads_generic_override_channels(self):
        """caiso-155 addendum Part 0: the floors rebuild must map the generic
        override channels to run_year kwargs exactly as replay_keeper does —
        dropping them rebuilt floors without any channel-armed mechanism
        (CAISO's firm-import trio rides ONLY there, caiso-150 §E2)."""
        from inspect import signature

        from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES
        from scripts.run_calibration import run_year

        params = signature(run_year).parameters
        for meta_key, kwarg in REBUILD_META_RENAMES.items():
            assert kwarg in params, f"{meta_key} -> {kwarg} not a run_year kwarg"
        for channel in (
            "coal_prb_sigmoid_overrides",
            "coal_bit_sigmoid_overrides",
            "coal_bit_passthrough_sigmoid",
        ):
            assert channel in REBUILD_META_RENAMES
        from scripts.replay_keeper import _REMAP

        for meta_key, kwarg in _REMAP.items():
            if meta_key in REBUILD_META_RENAMES and kwarg in params:
                assert REBUILD_META_RENAMES[meta_key] == kwarg

    def test_rebuild_splats_derived_run_year_inputs(self, tmp_path, monkeypatch):
        """caiso-292: the floors rebuild must carry the inputs the bundle NEVER
        records — replay_keeper.DERIVED_RUN_YEAR_INPUTS, recovered from the
        bundle's own class_hourly sidecar.

        ``meta.json`` records ``solve_and_persist``'s kwargs; it cannot record
        what ``solve_and_persist`` DERIVES from its own locals, so no mapping
        of meta keys ever reaches ``inject_biomass_mustrun``. Omitting it made
        the rebuild carry phantom biomass LP rows the scored solve had dropped
        (caiso-248) — measured on the CAISO keeper as 1,905 rebuilt rows
        against the solve's 1,705, a strict superset of exactly 200 biomass
        rows, so the rebuilt fleet was not row-aligned with the bundle's own
        per-unit artifacts and rule 19 [R-FORCED-BUDGET]'s "keepers re-score in
        place" did not hold for CAISO.
        """
        import scripts.legitimacy_diagnostics as ld
        import scripts.replay_keeper as rk
        import scripts.run_calibration as rc

        captured = {}

        def fake_run_year(
            year,
            iso,
            hours,
            gas_price,
            ttc_overrides,
            coal_drop_pof=False,
            inject_biomass_mustrun=False,
            fleet_only=False,
            **_,
        ):
            captured.update(
                coal_drop_pof=coal_drop_pof,
                inject_biomass_mustrun=inject_biomass_mustrun,
            )
            return {"fleet_arrays": "sentinel"}

        monkeypatch.setattr(rc, "run_year", fake_run_year)
        monkeypatch.setattr(
            rk,
            "derived_run_year_inputs",
            lambda bundle, year: {"inject_biomass_mustrun": True},
        )

        bundle = tmp_path / "bundle"
        bundle.mkdir()
        # A recorded meta key the rebuild DOES reach, plus the same derived key
        # recorded WRONG — the solve-side value must win either way.
        (bundle / "meta.json").write_text(
            json.dumps(
                {
                    "hours": 8760,
                    "gas_prices": {"2024": 2.19},
                    "coal_drop_pof": True,
                    "inject_biomass_mustrun": False,
                }
            )
        )

        assert ld._rebuild_fleet_arrays(bundle, "CAISO", 2024) == "sentinel"
        assert captured["coal_drop_pof"] is True, "recorded meta key must survive"
        assert captured["inject_biomass_mustrun"] is True, (
            "the derived solve-side input must reach run_year and must win "
            "over any same-named recorded key"
        )

    def test_derived_run_year_inputs_are_all_run_year_kwargs(self):
        """Every name in DERIVED_RUN_YEAR_INPUTS must be a run_year parameter.

        The splat is unconditional, so a name added to that tuple that run_year
        does not accept is a TypeError at rebuild time rather than a silent
        drop — this asserts it at import time instead.
        """
        from inspect import signature

        from scripts.replay_keeper import DERIVED_RUN_YEAR_INPUTS
        from scripts.run_calibration import run_year

        params = signature(run_year).parameters
        for name in DERIVED_RUN_YEAR_INPUTS:
            assert name in params, f"{name} is not a run_year kwarg"


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


def _fake_keeper_repo(
    tmp_path, run_id, iso, years, committed_summary, committed_rows=None
):
    """Build a minimal repo root: keepers.json + sidecar + committed bundle.

    ``committed_rows`` (the per-mechanism D-2 rows) is optional; it carries the
    ``ra_mustoffer_bridge`` attribution the recompute cannot rebuild, which the
    staleness check subtracts from the committed side before comparing.
    """
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
    d2 = {"summary": committed_summary}
    if committed_rows is not None:
        d2["rows"] = committed_rows
    (bundle / "legitimacy_diagnostics.json").write_text(
        json.dumps({"diagnostics": {"D2": d2}})
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

    def test_immaterial_class_drift_is_skipped(self, tmp_path, monkeypatch):
        """An immaterial class (< 2.5 % of load, never gates) whose forced_share
        differs between the committed artifact and a fresh floor rebuild is
        SKIPPED, not failed. Its near-zero-denominator share is numerically
        unstable across machines (float-summation order in the rebuild), so a
        strict compare would false-positive; the staleness check only needs the
        MATERIAL, gate-relevant shares to reproduce."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {
                "year": 2023,
                "class": "ST_GAS",
                "forced_share": 0.5549,
                "immaterial": True,
            },
        ]
        root = _fake_keeper_repo(tmp_path, "keeper1", "NEISO", [2023], committed)
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {
                            "year": 2023,
                            "class": "ST_GAS",
                            "forced_share": 0.5671,  # drifted, but immaterial
                            "immaterial": True,
                        }
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert res.passed
        assert res.rows[0]["verdict"] == "skip (immaterial)"

    def test_material_class_drift_still_fails(self, tmp_path, monkeypatch):
        """The immaterial skip must NOT weaken the staleness check for a
        material (gate-relevant) class — a real drift there still fails."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {
                "year": 2023,
                "class": "ST_GAS",
                "forced_share": 0.40,
                "immaterial": False,
            },
        ]
        root = _fake_keeper_repo(tmp_path, "keeper1", "NYISO", [2023], committed)
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {
                            "year": 2023,
                            "class": "ST_GAS",
                            "forced_share": 0.55,
                            "immaterial": False,
                        }
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert not res.passed
        assert any("ST_GAS" in f for f in res.failures)

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

    def test_p2_ra_mustoffer_bridge_excluded_from_committed(
        self, tmp_path, monkeypatch
    ):
        """The recompute's floor rebuild (run_year(fleet_only=True)) runs no P2
        solve, so it cannot reproduce the P2 ``ra_mustoffer_bridge``. A keeper
        whose committed forced energy for a class is ENTIRELY that bridge (e.g.
        caiso-58 CC_REGULAR 0.0527 = 3.24 TWh RA must-offer) must PASS against a
        recompute that shows ~0 there — the bridge share is subtracted from the
        committed side, not demanded of the rebuild. Regenerating the artifact to
        the recompute would erase the real, disclosed forced energy instead."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {
                "year": 2023,
                "class": "CC_REGULAR",
                "forced_share": 0.0527,
                "class_total_twh": 61.4225,
                "immaterial": False,
            },
        ]
        rows = [
            {
                "year": 2023,
                "class": "CC_REGULAR",
                "mechanism": "ra_mustoffer_bridge",
                "forced_twh": 3.2381,
                "class_total_twh": 61.4225,
                "share_of_class": 0.0527,
            },
        ]
        root = _fake_keeper_repo(
            tmp_path, "caiso58", "CAISO", [2023], committed, committed_rows=rows
        )
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {
                            "year": 2023,
                            "class": "CC_REGULAR",
                            "forced_share": 0.0003,  # rebuild has no P2 bridge
                            "class_total_twh": 61.5033,
                            "immaterial": False,
                        }
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert res.passed
        assert res.rows[0]["verdict"] == "pass"
        assert res.rows[0]["committed_rebuildable"] == 0.0

    def test_denominator_jitter_within_tolerance_passes(self, tmp_path, monkeypatch):
        """A material class whose committed vs recomputed share differs only by
        class-denominator attribution jitter (a boundary plant binning into a
        different class shifts the class total ~0.08 TWh) passes — this is the
        CAISO CT_PEAKER 0.5933 (rebuildable) vs 0.6099 case, ~1.7 pp < the 2.5 pp
        tolerance. The small ra_mustoffer_bridge component is excluded first."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {
                "year": 2023,
                "class": "CT_PEAKER",
                "forced_share": 0.5972,
                "class_total_twh": 2.0980,
                "immaterial": False,
            },
        ]
        rows = [
            {
                "year": 2023,
                "class": "CT_PEAKER",
                "mechanism": "ct_netload_drag",
                "forced_twh": 1.2449,
                "class_total_twh": 2.0980,
                "share_of_class": 0.5934,
            },
            {
                "year": 2023,
                "class": "CT_PEAKER",
                "mechanism": "ra_mustoffer_bridge",
                "forced_twh": 0.0081,
                "class_total_twh": 2.0980,
                "share_of_class": 0.0039,
            },
        ]
        root = _fake_keeper_repo(
            tmp_path, "caiso58", "CAISO", [2023], committed, committed_rows=rows
        )
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {
                            "year": 2023,
                            "class": "CT_PEAKER",
                            "forced_share": 0.6099,
                            "class_total_twh": 2.0181,
                            "immaterial": False,
                        }
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert res.passed

    def test_staleness_beyond_tolerance_still_fails_after_bridge_exclusion(
        self, tmp_path, monkeypatch
    ):
        """Excluding the P2 bridge must NOT blind the gate: a rebuildable-floor
        share that drifts past the tolerance still fails. Here the committed
        rebuildable share (0.20, after removing a 0.05 bridge share) vs a
        recompute of 0.10 is a 10 pp drift — a genuinely stale artifact."""
        import scripts.legitimacy_diagnostics as ld

        committed = [
            {
                "year": 2023,
                "class": "CT_PEAKER",
                "forced_share": 0.25,
                "class_total_twh": 100.0,
                "immaterial": False,
            },
        ]
        rows = [
            {
                "year": 2023,
                "class": "CT_PEAKER",
                "mechanism": "ct_netload_drag",
                "forced_twh": 20.0,
                "class_total_twh": 100.0,
                "share_of_class": 0.20,
            },
            {
                "year": 2023,
                "class": "CT_PEAKER",
                "mechanism": "ra_mustoffer_bridge",
                "forced_twh": 5.0,
                "class_total_twh": 100.0,
                "share_of_class": 0.05,
            },
        ]
        root = _fake_keeper_repo(
            tmp_path, "keeperx", "CAISO", [2023], committed, committed_rows=rows
        )
        monkeypatch.setattr(
            ld,
            "diagnose_bundle",
            lambda *a, **k: [
                ld.GateResult(
                    "D-2 forced-energy attribution",
                    summary=[
                        {
                            "year": 2023,
                            "class": "CT_PEAKER",
                            "forced_share": 0.10,
                            "class_total_twh": 100.0,
                            "immaterial": False,
                        }
                    ],
                )
            ],
        )
        res = ld.run_d2_keepers_verify(root)
        assert not res.passed
        assert any("CT_PEAKER" in f for f in res.failures)


# ---------------------------------------------------------------------------
# pjm-149 — the D-2/D-4 DISPATCH-PATH attribution drop
# ---------------------------------------------------------------------------


class TestDispatchPathIndependence:
    """``build_plant_matrices`` must not lose a floored plant because the
    active dispatch source happens not to cover it (PREREG-pjm149 §3.1/§3.2).

    Before pjm-149 the row set was a comprehension over the dispatch map alone,
    so on the CAMPD-bench-keyed run payload every floored plant with no CEMS
    meter — PJM's 14 CC_CHP plants, the nuclear must-run block at all six ISOs,
    CAISO/NYISO's hydro min-flow fleet — silently lost all D-2/D-4 attribution.
    """

    @staticmethod
    def _floors(codes, level, mech, groups, hours=HOURS):
        """One floored unit per plant code; returns aggregate_floors_by_plant."""
        n = len(codes)
        return aggregate_floors_by_plant(
            {
                "min_gen": np.array([[level] * hours] * n, dtype=float),
                "mechanism": np.array([[mech] * hours] * n, dtype=np.int8),
                "unit_ids": np.array([f"u{c}" for c in codes]),
                "plant_code": np.array(codes),
                "plant_group": np.array(groups, dtype=object),
            }
        )

    def _matrices(self, dispatch_map, codes, level, mech, groups, hours=HOURS):
        pids, floor_sum, mech_plant, grp, _fk = self._floors(
            codes, level, mech, groups, hours
        )
        return build_plant_matrices(
            dispatch_map,
            [str(p) for p in pids],
            floor_sum,
            mech_plant,
            grp,
            {},
            t=hours,
        )

    def test_floored_plant_absent_from_dispatch_map_keeps_its_rows(self):
        """A4/A5: the payload path drops plant 20; its rows must survive.

        Plant 10 is payload-present and dispatches above its floor; plant 20 is
        payload-ABSENT. On HEAD before pjm-149 the D-2 output carried plant 10
        only and 20's forced energy vanished with no failure and no note.
        """
        h = HOURS
        payload_only = {"10": np.full(h, 80.0)}  # plant 20 missing by construction
        mats = self._matrices(
            payload_only, [10, 20], 30.0, MECH_CT_NETLOAD_DRAG, ["CT_PEAKER"] * 2
        )
        assert mats.pids == ["10", "20"]
        assert mats.substituted_plants == ["20"]
        assert not mats.substituted[0] and mats.substituted[1]
        # §3.2: the absent plant enters with dispatch := its own floor.
        assert (mats.disp[1] == 30.0).all()
        assert (mats.disp[0] == 80.0).all()

        res = run_d2(
            mats.disp,
            mats.floors,
            mats.mechs,
            mats.klass,
            year=2024,
            dispatch_substituted=mats.substituted,
        )
        drag = [r for r in res.rows if r["mechanism"] == "ct_netload_drag"]
        assert len(drag) == 1
        # Plant 20's floor energy is attributed; plant 10 runs above its floor
        # so it contributes nothing to the numerator but does to the class total.
        # the artifact rounds TWh to 4 dp — compare on the reported grain
        assert drag[0]["forced_twh"] == round(30.0 * h / 1e6, 4)
        assert drag[0]["class_total_twh"] == round((80.0 + 30.0) * h / 1e6, 4)

    def test_absent_floored_plant_stamps_upper_bound_on_its_class(self):
        """The bound travels with the number: any class holding a substituted
        row is stamped ``upper_bound`` so a breach reads as indeterminate."""
        h = HOURS
        mats = self._matrices(
            {"10": np.full(h, 80.0)},
            [10, 20],
            30.0,
            MECH_CT_NETLOAD_DRAG,
            ["CT_PEAKER", "ST_GAS"],
        )
        res = run_d2(
            mats.disp,
            mats.floors,
            mats.mechs,
            mats.klass,
            year=2024,
            dispatch_substituted=mats.substituted,
        )
        by_class = {r["class"]: r for r in res.summary}
        assert by_class["ST_GAS"]["upper_bound"] is True
        assert by_class["CT_PEAKER"]["upper_bound"] is False

    def test_upper_bound_defaults_false_without_substitution(self):
        """Every direct caller (and the parquet path) omits the argument, and
        must keep a plain, un-flagged summary row."""
        h = HOURS
        res = run_d2(
            np.array([[30.0] * h]),
            np.array([[30.0] * h]),
            np.array([[MECH_CT_NETLOAD_DRAG] * h], dtype=np.int8),
            np.array(["CT_PEAKER"], dtype=object),
            year=2024,
        )
        assert all(row["upper_bound"] is False for row in res.summary)

    def test_no_op_when_the_dispatch_source_covers_the_floored_fleet(self):
        """A4: the parquet path carries every model plant, so the fix must be a
        NO-OP there — same rows, same values, nothing substituted."""
        h = HOURS
        full_map = {"10": np.full(h, 80.0), "20": np.full(h, 45.0)}
        mats = self._matrices(
            full_map, [10, 20], 30.0, MECH_CT_NETLOAD_DRAG, ["CT_PEAKER"] * 2
        )
        assert mats.substituted_plants == []
        assert not mats.substituted.any()
        assert (mats.disp[0] == 80.0).all() and (mats.disp[1] == 45.0).all()
        res = run_d2(
            mats.disp,
            mats.floors,
            mats.mechs,
            mats.klass,
            year=2024,
            dispatch_substituted=mats.substituted,
        )
        assert all(row["upper_bound"] is False for row in res.summary)

    def test_unfloored_absent_plants_stay_excluded(self):
        """C5 control: a plant absent from the dispatch map with NO floor must
        NOT be dragged in — it would perturb its class denominator with a
        fabricated zero (PREREG-caiso155 §2 P3, carried forward)."""
        h = HOURS
        pids, floor_sum, mech_plant, grp, _fk = self._floors(
            [10, 20], 0.0, 0, ["CT_PEAKER"] * 2
        )
        mats = build_plant_matrices(
            {"10": np.full(h, 80.0)},
            [str(p) for p in pids],
            floor_sum,
            mech_plant,
            grp,
            {},
            t=h,
        )
        assert mats.pids == ["10"]
        assert mats.substituted_plants == []

    def test_pseudo_units_still_ride_under_the_same_convention(self):
        """caiso-155's ``u:`` family is SUBSUMED by the generalized rule, not
        handled by a second parallel mechanism (rule 19 [R-ONE-MECH])."""
        h = HOURS
        arrays = {
            "min_gen": np.array([[30.0] * h, [900.0] * h]),
            "mechanism": np.array(
                [[MECH_CT_NETLOAD_DRAG] * h, [MECH_FIRM_IMPORT] * h], dtype=np.int8
            ),
            "unit_ids": np.array(["p7_committed", "NYISO_external_HQ_hydro"]),
            "plant_code": np.array([7, 0]),
            "plant_group": np.array(["CT_PEAKER", ""], dtype=object),
        }
        pids, floor_sum, mech_plant, grp, _fk = aggregate_floors_by_plant(arrays)
        mats = build_plant_matrices(
            {"7": np.full(h, 80.0)},
            [str(p) for p in pids],
            floor_sum,
            mech_plant,
            grp,
            {},
            t=h,
        )
        assert mats.substituted_pseudo == ["u:NYISO_external_HQ_hydro"]
        assert mats.substituted_plants == []
        assert (mats.disp[mats.pids.index("u:NYISO_external_HQ_hydro")] == 900.0).all()

    def test_absent_floored_plant_reaches_d4(self):
        """D-4 window testing must see the row too — a floor invisible to D-4
        is a rule-17 [R-FLOOR-WINDOW] declaration that is never checked."""
        h = HOURS
        mats = self._matrices(
            {"10": np.full(h, 80.0)},
            [10, 20],
            30.0,
            MECH_CT_NETLOAD_DRAG,
            ["CT_PEAKER"] * 2,
        )
        res = run_d4(mats.disp, mats.floors, mats.mechs, mats.klass, year=2024)
        row = next(r for r in res.rows if r["floor"] == "ct_netload_drag")
        assert row["floored_twh"] == round(30.0 * h / 1e6, 4)

    def test_prefix_comprehension_is_the_defect_regression_guard(self):
        """Pins WHAT WAS WRONG so it cannot be reintroduced.

        The pre-pjm-149 row set was literally
        ``[p for p in model_plants_plant if p in klass_by_pid or p in pid_strs]``
        — a comprehension over the DISPATCH map. Reproduced here against the
        same fixture, it drops the floored payload-absent plant; the shipped
        builder keeps it. If a future edit re-derives the row set from the
        dispatch map, the second assertion fails.
        """
        h = HOURS
        dispatch_map = {"10": np.full(h, 80.0)}
        pids, floor_sum, mech_plant, grp, _fk = self._floors(
            [10, 20], 30.0, MECH_CT_NETLOAD_DRAG, ["CT_PEAKER"] * 2
        )
        pid_strs = [str(p) for p in pids]
        klass_by_pid = dict(zip(pid_strs, grp))
        prefix_rows = [p for p in dispatch_map if p in klass_by_pid or p in pid_strs]
        assert prefix_rows == ["10"]  # the defect: plant 20 is gone
        mats = build_plant_matrices(
            dispatch_map, pid_strs, floor_sum, mech_plant, grp, {}, t=h
        )
        assert mats.pids == ["10", "20"]  # the fix: it is not


class TestFloorClassAttribution:
    """The miso-171 unit-grain repair of the D-4/D-2 plant-grain class
    attribution defect (miso-170 K-1 forensic): a mixed-class plant's
    minority-class floor must be charged to the class CARRYING it, never to
    the plant's majority label. Live case pinned here: plant 1104's CT_PEAKER
    netload floor was tested — and convicted — under ST_GAS's D-4 conduct row
    and charged to ST_GAS's D-2 mechanism list in every pre-repair artifact.
    """

    HOURS = HOURS

    @staticmethod
    def _mixed_plant_arrays(h=HOURS):
        """Plant 9: two ST_GAS units (no floor) + one CT_PEAKER unit floored
        by the CT netload limb — the 1104 topology."""
        return {
            "min_gen": np.array([[0.0] * h, [0.0] * h, [20.0] * h], dtype=float),
            "mechanism": np.array(
                [[0] * h, [0] * h, [MECH_CT_NETLOAD_DRAG] * h], dtype=np.int8
            ),
            "unit_ids": np.array(["p9_st_a", "p9_st_b", "p9_ct"]),
            "plant_code": np.array([9, 9, 9]),
            "plant_group": np.array(["ST_GAS", "ST_GAS", "CT_PEAKER"], dtype=object),
        }

    def test_floor_class_is_the_carrying_units_class(self):
        pids, floor_sum, mech_plant, grp, fk = aggregate_floors_by_plant(
            self._mixed_plant_arrays()
        )
        assert grp.tolist() == ["ST_GAS"]  # the plant LABEL stays majority
        assert (floor_sum[0] == 20.0).all()
        assert (mech_plant[0] == MECH_CT_NETLOAD_DRAG).all()
        # The floor class is the CT unit's, in every floored hour.
        assert fk.eq("CT_PEAKER")[0].all()
        assert not fk.eq("ST_GAS")[0].any()

    def test_single_class_plant_attribution_unchanged(self):
        """A pure-class plant's floor class equals its label — the repair is
        a no-op outside mixed-class sites (incl. the #1488 empty-group
        imputation, which resolves BEFORE the max-composition pick)."""
        h = HOURS
        arrays = {
            "min_gen": np.array([[5.0] * h, [7.0] * h], dtype=float),
            "mechanism": np.array(
                [[MECH_RELIABILITY_FLOOR] * h, [MECH_RELIABILITY_FLOOR] * h],
                dtype=np.int8,
            ),
            "unit_ids": np.array(["p546_x", "p546_a"]),
            "plant_code": np.array([546, 546]),
            "plant_group": np.array(["", "ST_GAS"], dtype=object),
        }
        _, _, _, grp, fk = aggregate_floors_by_plant(arrays)
        assert grp.tolist() == ["ST_GAS"]
        assert fk.eq("ST_GAS")[0].all()

    def _mixed_mats(self, h=HOURS):
        pids, floor_sum, mech_plant, grp, fk = aggregate_floors_by_plant(
            self._mixed_plant_arrays(h)
        )
        # Plant dispatch sits AT the CT floor (the ST units are offline).
        return build_plant_matrices(
            {"9": np.full(h, 20.0)},
            [str(p) for p in pids],
            floor_sum,
            mech_plant,
            grp,
            {},
            t=h,
            floor_klass=fk,
        )

    def test_run_d2_charges_the_carrying_class(self):
        mats = self._mixed_mats()
        res = run_d2(
            mats.disp,
            mats.floors,
            mats.mechs,
            mats.klass,
            year=2024,
            floor_klass=mats.floor_klass,
        )
        by_class = {(r["class"], r["mechanism"]): r for r in res.rows}
        assert ("CT_PEAKER", "ct_netload_drag") in by_class
        assert ("ST_GAS", "ct_netload_drag") not in by_class

    def test_run_d2_without_floor_klass_reproduces_the_defect(self):
        """The pre-repair rule is preserved behind ``floor_klass=None`` so
        legacy artifacts re-score exactly as before — and this pins what the
        defect WAS."""
        mats = self._mixed_mats()
        res = run_d2(mats.disp, mats.floors, mats.mechs, mats.klass, year=2024)
        by_class = {(r["class"], r["mechanism"]): r for r in res.rows}
        assert ("ST_GAS", "ct_netload_drag") in by_class

    def test_run_d4_conduct_conviction_lands_on_the_carrying_class(self):
        h = HOURS
        mats = self._mixed_mats()
        windows = {
            (MECH_CT_NETLOAD_DRAG, "ST_GAS"): (0, 24),
            (MECH_CT_NETLOAD_DRAG, "CT_PEAKER"): (0, 24),
        }
        bench_pl = {"9": {"mw": np.zeros(h), "npl": 100.0, "group": "ST_GAS"}}
        res = run_d4(
            mats.disp,
            mats.floors,
            mats.mechs,
            mats.klass,
            year=2024,
            windows=windows,
            pids=mats.pids,
            bench_pl=bench_pl,
            floor_klass=mats.floor_klass,
        )
        conduct = [r for r in res.rows if r["check"] == "unit-conduct"]
        assert conduct, "conduct rider must fire on the dark meter"
        assert {r["floor"] for r in conduct} == {"ct_netload_drag × CT_PEAKER"}
        assert all(r["verdict"] == "FAIL" for r in conduct)
        # No window/conduct row exists under the majority label.
        assert not any("ST_GAS" in r["floor"] for r in res.rows)


class TestMaterialityDenominator:
    """nyiso-242: the D-2 materiality denominator, and the two defects it had.

    Rule 20 ``[R-FORCED-BUDGET]`` gates a class only when its annual energy is
    >= 2 % of total ISO load. The denominator that decides that was wrong twice
    over, and both halves are pinned here because each one silently over-gates
    (a class rule 20 says is "reported ... but never gated" was being failed).
    """

    def test_payload_total_load_uses_zone_demand_not_fuelrows(self, tmp_path):
        """The denominator is served load, not a partial generation sum.

        ``fuelRows`` carries gas/coal/nuclear/wind/solar/interchange only: it
        OMITS hydro (26.2 of NYISO's 152.7 TWh in 2022) and SUBTRACTS the
        signed net-interchange row when a net importer's imports are part of
        the load it serves. The fixture reproduces exactly that shape, so the
        old construction would return 67.92 TWh against a true 152.68.
        """
        import scripts.legitimacy_diagnostics as L

        run = {
            "years": {
                "2022": {
                    "fuelRows": [
                        {"k": "gas", "m": 63.5},
                        {"k": "coal", "m": 0.67},
                        {"k": "nuclear", "m": 26.75},
                        {"k": "wind", "m": 4.7},
                        {"k": "solar", "m": 0.11},
                        {"k": "interchange", "m": -27.81},
                    ],
                    # hydro is absent from fuelRows by construction
                    "lmp": {
                        "Upstate_West": {"d": 60.0},
                        "NYC": {"d": 52.68},
                        "Long_Island": {"d": 40.0},
                    },
                }
            }
        }
        import base64
        import gzip as _gzip

        sidecar = {"file": "runs/fixture.js"}
        (tmp_path / "runs").mkdir()
        blob = base64.b64encode(_gzip.compress(json.dumps(run).encode())).decode()
        (tmp_path / "runs" / "fixture.js").write_text(
            f'window.BC.runGz["fixture"]="{blob}";'
        )

        got = L.load_payload_total_load_mwh(tmp_path, sidecar, 2022)
        assert got == pytest.approx(152.68e6, rel=1e-9)
        # The superseded construction, kept explicit so the regression is named.
        fuelrows_sum = sum(r["m"] for r in run["years"]["2022"]["fuelRows"])
        assert fuelrows_sum == pytest.approx(67.92, rel=1e-6)
        assert got > fuelrows_sum * 1e6 * 2.0  # ~2.25x on this ISO-year

    def test_bundle_total_load_falls_back_to_committed_system_sidecar(self, tmp_path):
        """Solve time has no registry sidecar, so the bundle must supply it.

        The artifact is written BEFORE the run is registered, which left
        ``load_share`` null in 285 of 315 committed D-2 rows (90 %) and
        disabled the rule-20 guard in every one of them.
        """
        pd = pytest.importorskip("pandas")
        import scripts.legitimacy_diagnostics as L

        hourly = tmp_path / "hourly"
        hourly.mkdir()
        pd.DataFrame(
            {
                "pass": ["P1"] * 4 + ["P0"] * 2,
                "zone": ["A", "B", "A", "NYISO_external", "A", "B"],
                "demand": [10.0, 20.0, 30.0, 999.0, 7.0, 7.0],
            }
        ).to_parquet(hourly / "system_2022.parquet")

        # Final pass only (P1 over P0), external proxy nodes excluded.
        assert L.load_bundle_total_load_mwh(tmp_path, 2022) == pytest.approx(60.0)
        # Absent sidecar -> None, never a silent substitution.
        assert L.load_bundle_total_load_mwh(tmp_path, 2099) is None

    def test_dispatch_source_is_recorded_so_substitution_is_never_silent(self):
        """The artifact must name which dispatch source produced its rows.

        ``dispatch/<year>_<pass>.parquet`` is gitignored, so a re-run from a
        clean checkout silently takes the CEMS-only payload path: measured on
        the NYISO keeper, that moves 148 gating numerics. The stamp is what
        makes the two artifacts distinguishable rather than reading as drift.
        """
        import scripts.legitimacy_diagnostics as L

        saved = dict(L._dispatch_source_basis)
        try:
            L._dispatch_source_basis.clear()
            L._dispatch_source_basis[2022] = "dispatch/2022_P1.parquet"
            L._dispatch_source_basis[2023] = "run payload runs/x.js"
            art = L.build_json_report(
                [], bundle="/tmp/b", iso="NYISO", years=[2022, 2023, 2024]
            )
        finally:
            L._dispatch_source_basis.clear()
            L._dispatch_source_basis.update(saved)

        assert art["dispatch_source"] == {
            "2022": "dispatch/2022_P1.parquet",
            "2023": "run payload runs/x.js",
        }, "both sources must be distinguishable in the committed artifact"
        # A year that built no per-plant matrices is absent, not mislabelled.
        assert "2024" not in art["dispatch_source"]


class TestScorerDoesNotTrustArtifactMateriality:
    """nyiso-242: the redundancy that kept a wrong artifact from being a wrong verdict.

    ``calibration_verdict`` computes C8 materiality itself (``_class_load_share``
    over its own ``_total_load``) and must NEVER fall back to the artifact's
    ``load_share`` / ``immaterial`` / D-2 ``passed``. That independence is the
    only reason 285 of 315 committed D-2 rows carrying ``load_share: null`` —
    and NEISO's five D-2 failures on classes at 0.08-0.80 % of ISO load — did
    not become wrong determinations.

    It was undocumented and untested. A future refactor that "simplified" the
    scorer to trust the artifact would convert a latent defect into silently
    wrong verdicts, so it is pinned here as a property of the scorer.
    """

    def test_verdict_source_never_reads_the_artifact_materiality_fields(self):
        import ast
        import pathlib

        src = pathlib.Path("scripts/calibration_verdict.py").read_text()
        tree = ast.parse(src)

        banned = {"load_share", "immaterial"}
        # Only a real READ counts — a subscript or a ``.get(...)``. The scorer
        # legitimately mentions both words in its own message text (e.g.
        # "<class> immaterial (0.2% of ISO load ...)"), and that is not a read.
        reads: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript):
                s = node.slice
                if isinstance(s, ast.Constant) and s.value in banned:
                    reads.append(f"subscript line {node.lineno}")
            elif isinstance(node, ast.Call):
                fn = node.func
                if (
                    isinstance(fn, ast.Attribute)
                    and fn.attr == "get"
                    and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and node.args[0].value in banned
                ):
                    reads.append(f".get() line {node.lineno}")
        assert reads == [], (
            "calibration_verdict must compute C8 materiality itself, never read "
            f"it from the legitimacy artifact; found: {reads}"
        )

    def test_verdict_computes_its_own_total_load_from_zone_demand(self):
        """The scorer's denominator is served load, and it is the correct one."""
        import scripts.calibration_verdict as V

        ypay = {"lmp": {"A": {"d": 100.0}, "B": {"d": 52.68}}}
        assert V._total_load(ypay, a_gen=999.0) == pytest.approx(152.68)
        # No zone block -> falls back to actual generation, never to 0.
        assert V._total_load({}, a_gen=123.0) == pytest.approx(123.0)
