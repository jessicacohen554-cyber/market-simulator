"""Tests for the forecast invariant suite (W2-P5).

Two tiers, matching plan §2.4:

* **Fast, per-PR (this module's bulk):** the invariant *logic* is exercised
  against hand-built ``Run`` objects — fabricated evolution ledgers plus small
  real ``DispatchResult`` arrays. Each invariant is shown to PASS on a coherent
  trajectory and to FAIL/WARN on an engineered violation. No LP solves, so this
  runs in well under a second.
* **Real-LP integration (``test_real_forecast_invariants_pass``, marked slow):**
  a genuine multi-year ERCOT forecast is solved end-to-end on HiGHS — the first
  real-LP coverage of the capacity-evolution loop (closes TC-3) — then the
  checker is run over its cache and every invariant must be non-FAIL, and the
  engineered ledger fields (solve counts, fleet-by-fuel, reserve margin) must be
  present. Opt in with ``RUN_SLOW_FORECAST=1`` (or ``-m slow``); skipped by
  default so the fast suite stays fast.

The fast tier deliberately fabricates ledgers rather than mocking the solver:
the thing under test is the *checker*, and a fabricated ledger is the checker's
real input contract.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
import pytest

from scripts import check_forecast_invariants as C


# --------------------------------------------------------------------------- #
# Fabrication helpers
# --------------------------------------------------------------------------- #
def _mk_result(n_gen=3, n_zones=2, T=24, *, storage=True, emissions=True):
    """A tiny feasible-looking DispatchResult with a matching demand array."""
    from market_sim.model.dispatch import DispatchResult

    rng = np.random.default_rng(0)
    dispatch = np.abs(rng.normal(50, 5, (n_gen, T)))
    wind = np.abs(rng.normal(10, 2, (n_zones, T)))
    solar = np.abs(rng.normal(5, 1, (n_zones, T)))
    slack = np.zeros((n_zones, T))
    dump = np.zeros((n_zones, T))
    prices = np.abs(rng.normal(30, 3, (n_zones, T)))
    chg = np.zeros((1, T))
    dis = np.zeros((1, T))
    soc = np.abs(rng.normal(20, 1, (1, T)))
    # Demand exactly closes the system balance so I1 passes by construction.
    supply = (
        dispatch.sum(axis=0)
        + wind.sum(axis=0)
        + solar.sum(axis=0)
        + dis.sum(axis=0)
        - chg.sum(axis=0)
    )
    demand = np.zeros((n_zones, T))
    demand[0] = supply  # put all load on zone 0; Σ_zone demand == Σ supply
    r = DispatchResult(
        dispatch=dispatch,
        wind_dispatched=wind,
        solar_dispatched=solar,
        slack=slack,
        dump=dump,
        prices=prices,
        storage_charge=chg if storage else None,
        storage_discharge=dis if storage else None,
        storage_soc=soc if storage else None,
        flows=None,
        objective_value=1234.0,
        status="optimal",
        build_time=0.0,
        solve_time=0.0,
        emissions=(np.abs(rng.normal(1, 0.1, (n_gen, T))) if emissions else None),
    )
    return r, demand


class _Ctx:
    """Minimal FleetContext stand-in for the checks that read one."""

    def __init__(self, fuels, zones):
        self.fuel_types = fuels
        self.zones = zones
        self.wind_potential_mwh = 1e6
        self.solar_potential_mwh = 1e6


def _mk_yeardata(year, fuels=("gas_cc", "coal", "wind")):
    r, demand = _mk_result(n_gen=len(fuels))
    ctx = _Ctx(list(fuels), ["North", "South"])
    return C.YearData(year=year, result=r, demand=demand, context=ctx)


def _ledger(
    year,
    before,
    after,
    *,
    retirements=None,
    thermal_additions=None,
    ccs=None,
    renewable_additions=None,
    storage_additions=None,
    peak=None,
    reserve_margin=0.15,
    rps=0.0,
    solve=(1, 1, 0),
    bridge=False,
):
    return {
        "iso": "ERCOT",
        "year": year,
        "mode": "forecast",
        "hindcast": False,
        "bridge": bridge,
        "fleet_by_fuel_before": before,
        "fleet_by_fuel_after": after,
        "retirements": retirements or [],
        "floor_retained": [],
        "thermal_additions": thermal_additions or [],
        "ccs_retrofits": ccs or [],
        "renewable_additions": renewable_additions or [],
        "storage_additions": storage_additions or [],
        "peak_demand_mw": peak,
        "firm_clean_mw": 0.0,
        "reserve_margin": reserve_margin,
        "rps_dual": rps,
        "solve_counts": {"P0": solve[0], "P1": solve[1], "P2": solve[2]},
    }


def _mk_run(ledgers, years=None, config=None, iso="ERCOT"):
    from market_sim.config.scenarios import ScenarioConfig

    run = C.Run(
        run_dir=Path("."),
        config=config or ScenarioConfig(iso=iso),
        iso=iso,
    )
    run.ledgers = {led["year"]: led for led in ledgers}
    run.years = years or {}
    return run


# --------------------------------------------------------------------------- #
# I1 energy balance
# --------------------------------------------------------------------------- #
def test_i1_passes_on_balanced_year():
    run = _mk_run([], years={2026: _mk_yeardata(2026)})
    assert C.check_i1_energy_balance(run).status == C.PASS


def test_i1_fails_on_imbalance():
    yd = _mk_yeardata(2026)
    yd.demand = yd.demand + 100.0  # inject a 100 MW/zone imbalance
    run = _mk_run([], years={2026: yd})
    assert C.check_i1_energy_balance(run).status == C.FAIL


def test_i1_skips_without_demand():
    yd = _mk_yeardata(2026)
    yd.demand = None
    run = _mk_run([], years={2026: yd})
    assert C.check_i1_energy_balance(run).status == C.SKIP


# --------------------------------------------------------------------------- #
# I3 unserved / dump — and its R-4 reporting grain
# --------------------------------------------------------------------------- #
def test_i3_passes_with_no_slack():
    run = _mk_run([], years={2026: _mk_yeardata(2026)})
    assert C.check_i3_unserved_dump(run).status == C.PASS


def test_i3_grain_reports_hours_gwh_and_peak():
    """Trivial fixture (1 zone-pair, 24 h): the grain is arithmetic, not a fit.

    Two breach hours of 1,000 and 3,000 MW on a 24 h year → 4.0 GWh, peak
    3,000 MW, and a slack fraction well over the 1e-4 gate, so I3 FAILs and the
    detail carries all four numbers (R-4).
    """
    yd = _mk_yeardata(2026)
    yd.result.slack[0, 5] = 1000.0
    yd.result.slack[1, 9] = 3000.0
    run = _mk_run([], years={2026: yd})
    res = C.check_i3_unserved_dump(run)
    assert res.status == C.FAIL
    assert "2 h" in res.detail
    assert "4.0 GWh" in res.detail
    assert "peak 3,000 MW" in res.detail
    assert "of load" in res.detail  # the pre-R-4 fraction is still there


def test_i3_grain_counts_a_split_hour_once():
    """Slack in two zones in the SAME hour is one system breach hour."""
    yd = _mk_yeardata(2026)
    yd.result.slack[0, 3] = 2000.0
    yd.result.slack[1, 3] = 2000.0
    run = _mk_run([], years={2026: yd})
    res = C.check_i3_unserved_dump(run)
    assert res.status == C.FAIL
    assert "1 h" in res.detail
    assert "peak 4,000 MW" in res.detail


def test_i3_reporting_floor_does_not_move_the_gate():
    """Sub-MW dust is excluded from the hour tally but not from the fraction.

    Guards the one hazard in R-4: the reporting floor must never become a
    second gate. Here a large breach hour coexists with 24 hours of 0.1 MW
    dust — the tally counts 1, the FAIL/GWh arithmetic counts everything.
    """
    yd = _mk_yeardata(2026)
    yd.result.slack[0, :] = 0.1
    yd.result.slack[0, 7] = 5000.0
    run = _mk_run([], years={2026: yd})
    res = C.check_i3_unserved_dump(run)
    assert res.status == C.FAIL
    assert "1 h" in res.detail
    # 5000 + 0.1*23 (hour 7 overwritten) = 5002.3 MWh → 5.0 GWh
    assert "5.0 GWh" in res.detail


# --------------------------------------------------------------------------- #
# I2 no NaN/inf
# --------------------------------------------------------------------------- #
def test_i2_passes_clean():
    run = _mk_run([], years={2026: _mk_yeardata(2026)})
    assert C.check_i2_no_nan_inf(run).status == C.PASS


def test_i2_fails_on_nan_array():
    yd = _mk_yeardata(2026)
    yd.result.prices[0, 0] = np.nan
    run = _mk_run([], years={2026: yd})
    assert C.check_i2_no_nan_inf(run).status == C.FAIL


def test_i2_fails_on_inf_ledger_field():
    run = _mk_run(
        [_ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, reserve_margin=float("inf"))]
    )
    assert C.check_i2_no_nan_inf(run).status == C.FAIL


# --------------------------------------------------------------------------- #
# I4 capacity accounting
# --------------------------------------------------------------------------- #
def test_i4_closes_with_retire_and_build():
    led = _ledger(
        2027,
        before={"gas_cc": 1000, "coal": 500},
        after={"gas_cc": 1200, "coal": 400},
        retirements=[
            {"unit_id": "c1", "fuel": "coal", "mw": 100, "reason": "economic"}
        ],
        thermal_additions=[
            {
                "unit_id": "n1",
                "fuel": "gas_cc",
                "mw": 200,
                "zone": "N",
                "source": "economic",
                "eia860_id": None,
            }
        ],
    )
    assert C.check_i4_capacity_accounting(_mk_run([led])).status == C.PASS


def test_i4_fails_on_unexplained_delta():
    led = _ledger(
        2027, before={"gas_cc": 1000}, after={"gas_cc": 1500}
    )  # +500 unexplained
    assert C.check_i4_capacity_accounting(_mk_run([led])).status == C.FAIL


def test_i4_closes_with_confirmed_derates():
    # FFR-1A / FR-1: a plant-binned confirmed exit shrinks a SURVIVING unit_id,
    # recorded as a confirmed_derates row (no retirement row exists). I4 must
    # subtract derate_mw per fuel or the balance cannot close.
    led = _ledger(
        2027,
        before={"gas_st": 1333.0, "coal": 500.0},
        after={"coal": 500.0},
    )
    led["confirmed_derates"] = [
        {
            "unit_id": "b1",
            "fuel": "gas_st",
            "mw_before": 1333.0,
            "mw_after": 0.0,
            "derate_mw": 1333.0,
        }
    ]
    assert C.check_i4_capacity_accounting(_mk_run([led])).status == C.PASS


def test_i4_fails_on_unledgered_derate():
    # The pre-FFR-1A leak itself: derated MW with no confirmed_derates row
    # (legacy ledger, key absent) is an unexplained delta -> FAIL.
    led = _ledger(2027, before={"gas_st": 1333.0}, after={"gas_st": 0.0})
    assert C.check_i4_capacity_accounting(_mk_run([led])).status == C.FAIL


def test_i4_ccs_retrofit_shifts_fuel():
    led = _ledger(
        2027,
        before={"gas_cc": 1000},
        after={"gas_cc": 700, "gas_cc_ccs": 300},
        ccs=[
            {"unit_id": "g1", "mw": 300, "from_fuel": "gas_cc", "to_fuel": "gas_cc_ccs"}
        ],
    )
    assert C.check_i4_capacity_accounting(_mk_run([led])).status == C.PASS


def test_i4_continuity_across_years():
    a = _ledger(2026, {"gas_cc": 1000}, {"gas_cc": 1000})
    b = _ledger(2027, {"gas_cc": 900}, {"gas_cc": 900})  # before(2027) != after(2026)
    assert C.check_i4_capacity_accounting(_mk_run([a, b])).status == C.FAIL


# --------------------------------------------------------------------------- #
# I5 no retire-and-reenter
# --------------------------------------------------------------------------- #
def test_i5_flags_reentry():
    a = _ledger(
        2026,
        {"coal": 500},
        {"coal": 400},
        retirements=[
            {"unit_id": "c1", "fuel": "coal", "mw": 100, "reason": "economic"}
        ],
    )
    b = _ledger(
        2027,
        {"coal": 400},
        {"coal": 500},
        thermal_additions=[
            {
                "unit_id": "c1",
                "fuel": "coal",
                "mw": 100,
                "zone": "N",
                "source": "economic",
                "eia860_id": None,
            }
        ],
    )
    assert C.check_i5_no_retire_reenter(_mk_run([a, b])).status == C.FAIL


def test_i5_passes_distinct_ids():
    a = _ledger(
        2026,
        {"coal": 500},
        {"coal": 400},
        retirements=[
            {"unit_id": "c1", "fuel": "coal", "mw": 100, "reason": "economic"}
        ],
    )
    assert C.check_i5_no_retire_reenter(_mk_run([a])).status == C.PASS


# --------------------------------------------------------------------------- #
# I6 economic-retirement sanity
# --------------------------------------------------------------------------- #
def test_i6_flags_mass_single_year_retire():
    led = _ledger(
        2027,
        before={"coal": 1000},
        after={"coal": 600},
        retirements=[
            {"unit_id": "c1", "fuel": "coal", "mw": 400, "reason": "economic"}
        ],
    )
    assert C.check_i6_econ_retire_sanity(_mk_run([led])).status == C.FAIL


def test_i6_passes_modest_retire():
    led = _ledger(
        2027,
        before={"coal": 1000, "gas_cc": 1000},
        after={"coal": 900, "gas_cc": 1000},
        retirements=[
            {"unit_id": "c1", "fuel": "coal", "mw": 100, "reason": "economic"}
        ],
    )
    assert C.check_i6_econ_retire_sanity(_mk_run([led])).status == C.PASS


# --------------------------------------------------------------------------- #
# I7 reliability floor (G-41: market-design-dependent)
# --------------------------------------------------------------------------- #
# Energy-only ISOs (ERCOT): retirement-bounded nameplate floor.
def test_i7_energy_only_passes_above_floor():
    led = _ledger(2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000)
    assert C.check_i7_reliability_floor(_mk_run([led])).status == C.PASS


def test_i7_energy_only_tolerates_starting_below_floor():
    # Fleet started below the floor (3000 < 5750) but did not over-retire —
    # retirement-bounded floor tolerates it (no absolute floor in energy-only).
    led = _ledger(2026, {"gas_cc": 3000}, {"gas_cc": 3000}, peak=5000)
    assert C.check_i7_reliability_floor(_mk_run([led])).status == C.PASS


def test_i7_energy_only_fails_on_over_retirement():
    # Started above the floor (10000 > 5750), evolution retired down to 3000
    # (below the floor): over-retirement, FAIL.
    led = _ledger(2026, {"gas_cc": 10000}, {"gas_cc": 3000}, peak=5000)
    assert C.check_i7_reliability_floor(_mk_run([led])).status == C.FAIL


# Capacity-market ISOs (PJM): absolute floor on the model's accreditation
# convention (accredited firm = peak*(1+reserve_margin) vs the model's own
# resolve_adequacy_requirement_mw).
def test_i7_capacity_market_passes_when_accredited_meets_requirement():
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=0.15
    )
    run = _mk_run([led], iso="PJM")
    assert C.check_i7_reliability_floor(run).status == C.PASS


def test_i7_capacity_market_fails_when_accredited_below_requirement():
    # reserve_margin=-0.30 -> accredited firm 3500 MW, below PJM's UCAP-basis
    # requirement (~4355 MW at peak 5000 after the W2-D DR netting): absolute
    # floor FAIL.
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=-0.30
    )
    run = _mk_run([led], iso="PJM")
    assert C.check_i7_reliability_floor(run).status == C.FAIL


def test_i7_capacity_market_skips_year_without_reserve_margin():
    # No persisted firm-capacity accounting (reserve_margin None) -> skip, PASS.
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=None
    )
    run = _mk_run([led], iso="PJM")
    assert C.check_i7_reliability_floor(run).status == C.PASS


# D-1 checker repair (owner card C-A, 2026-08-25): the ledger year is threaded
# to resolve_adequacy_requirement_mw, so the checker grades the SAME bar the
# model builds to — the published FPR of the matching delivery year (2026-2028)
# or the held-last FPR beyond the table (2029+), never the lower year-less
# fallback composite. Bars at peak 5000, PJM (DR-netted firm peak x factor):
#   year-less fallback composite  0.871017 x peak = 4355.1 MW  (the old bar)
#   2026/27 published FPR 0.9170  0.880629 x peak = 4403.1 MW
#   2028/29 FPR 0.9401 held-last  0.902813 x peak = 4514.1 MW  (2029+)
def test_i7_capacity_market_grades_published_fpr_bar_not_fallback():
    # rm -12.2% -> accredited firm 4390 MW: above the stale fallback bar the
    # year-less checker graded (the D-1 defect would PASS this), below the
    # published 2026/27 FPR bar the model actually builds to -> FAIL.
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=-0.122
    )
    run = _mk_run([led], iso="PJM")
    res = C.check_i7_reliability_floor(run)
    assert res.status == C.FAIL, res.detail


def test_i7_capacity_market_holds_last_fpr_beyond_table():
    # HOLD-LAST-FPR (card C-A): 2030 -> delivery 2030/2031, beyond the last
    # published table entry -> bar holds the 2028/29 FPR (4514 MW at peak
    # 5000), never dropping back to the stale composite (4355 MW). rm -11%
    # (firm 4450 MW) sits between the two: the pre-C-A checker PASSed it; the
    # held-last bar FAILs it.
    led = _ledger(
        2030, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=-0.11
    )
    run = _mk_run([led], iso="PJM")
    res = C.check_i7_reliability_floor(run)
    assert res.status == C.FAIL, res.detail


# --------------------------------------------------------------------------- #
# I8 planned-additions mode gating
# --------------------------------------------------------------------------- #
def test_i8_backcast_forbids_planned():
    from market_sim.config.scenarios import ScenarioConfig

    led = _ledger(
        2024,
        {"gas_cc": 100},
        {"gas_cc": 200},
        thermal_additions=[
            {
                "unit_id": "p1",
                "fuel": "gas_cc",
                "mw": 100,
                "zone": "N",
                "source": "planned",
                "eia860_id": "55555",
            }
        ],
    )
    run = _mk_run([led], config=ScenarioConfig(iso="ERCOT", mode="backcast"))
    assert C.check_i8_planned_mode_gating(run).status == C.FAIL


def test_i8_forecast_planned_needs_eia_id():
    led = _ledger(
        2027,
        {"gas_cc": 100},
        {"gas_cc": 200},
        thermal_additions=[
            {
                "unit_id": "p1",
                "fuel": "gas_cc",
                "mw": 100,
                "zone": "N",
                "source": "planned",
                "eia860_id": None,
            }
        ],
    )
    assert C.check_i8_planned_mode_gating(_mk_run([led])).status == C.FAIL


def test_i8_forecast_traceable_planned_ok():
    led = _ledger(
        2027,
        {"gas_cc": 100},
        {"gas_cc": 200},
        thermal_additions=[
            {
                "unit_id": "p1",
                "fuel": "gas_cc",
                "mw": 100,
                "zone": "N",
                "source": "planned",
                "eia860_id": "55555",
            }
        ],
    )
    assert C.check_i8_planned_mode_gating(_mk_run([led])).status == C.PASS


# --------------------------------------------------------------------------- #
# I9 storage integrity
# --------------------------------------------------------------------------- #
def test_i9_passes_valid_storage():
    run = _mk_run([], years={2026: _mk_yeardata(2026)})
    assert C.check_i9_storage_integrity(run).status == C.PASS


def test_i9_fails_negative_soc():
    yd = _mk_yeardata(2026)
    yd.result.storage_soc[0, 5] = -50.0
    run = _mk_run([], years={2026: yd})
    assert C.check_i9_storage_integrity(run).status == C.FAIL


def test_i9_fails_simultaneous_charge_discharge():
    yd = _mk_yeardata(2026)
    yd.result.storage_charge[:] = 10.0
    yd.result.storage_discharge[:] = 10.0
    run = _mk_run([], years={2026: yd})
    assert C.check_i9_storage_integrity(run).status == C.FAIL


# --------------------------------------------------------------------------- #
# I10 RPS dual
# --------------------------------------------------------------------------- #
def test_i10_fails_negative_dual():
    led = _ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, rps=-1.0)
    assert C.check_i10_rps_dual(_mk_run([led])).status == C.FAIL


def test_i10_warns_on_oscillation():
    a = _ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, rps=10.0)
    b = _ledger(2027, {"gas_cc": 100}, {"gas_cc": 100}, rps=30.0)  # +200%
    assert C.check_i10_rps_dual(_mk_run([a, b])).status == C.WARN


def test_i10_passes_stable():
    a = _ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, rps=10.0)
    b = _ledger(2027, {"gas_cc": 100}, {"gas_cc": 100}, rps=11.0)
    assert C.check_i10_rps_dual(_mk_run([a, b])).status == C.PASS


# --------------------------------------------------------------------------- #
# I11 one-pass
# --------------------------------------------------------------------------- #
def test_i11_passes_single_pass():
    led = _ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, solve=(1, 1, 0))
    assert C.check_i11_one_pass(_mk_run([led])).status == C.PASS


def test_i11_fails_double_solve():
    led = _ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, solve=(2, 1, 0))
    assert C.check_i11_one_pass(_mk_run([led])).status == C.FAIL


def test_i11_bridge_year_must_not_solve():
    led = _ledger(2022, {"gas_cc": 100}, {"gas_cc": 100}, solve=(1, 1, 0), bridge=True)
    assert C.check_i11_one_pass(_mk_run([led])).status == C.FAIL


# --------------------------------------------------------------------------- #
# I12 reserve-margin band
# --------------------------------------------------------------------------- #
def test_i12_warns_single_excursion():
    led = _ledger(2026, {"gas_cc": 100}, {"gas_cc": 100}, reserve_margin=0.60)
    assert C.check_i12_reserve_margin(_mk_run([led])).status == C.WARN


# Capacity-market ISOs (PJM): the floor is the requirement-implied margin
# (resolve_adequacy_requirement_mw / peak - 1), the same basis as the ledger's
# accreditation-convention reserve_margin — I7's floor stated as a margin,
# plus the over-build band on top (W1-B F4 derivative fix, W2-D).
def test_i12_capacity_market_passes_above_requirement_implied_floor():
    # PJM requirement-implied floor at peak 5000 is ~-12.9% (UCAP basis, DR
    # netted); a UCAP-basis rm of -10% is above the floor and inside the band.
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=-0.10
    )
    run = _mk_run([led], iso="PJM")
    res = C.check_i12_reserve_margin(run)
    assert res.status == C.PASS, res.detail


def test_i12_capacity_market_warns_below_requirement_implied_floor():
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=-0.30
    )
    run = _mk_run([led], iso="PJM")
    assert C.check_i12_reserve_margin(run).status == C.WARN


def test_i12_capacity_market_warns_on_overbuild_above_band():
    # Over-procurement is I12's independent signal: a margin far above the
    # requirement-implied floor + band (BLK-10 class) is an excursion.
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=0.15
    )
    run = _mk_run([led], iso="PJM")
    assert C.check_i12_reserve_margin(run).status == C.WARN


def test_i12_capacity_market_skips_year_without_peak():
    # No persisted peak -> no requirement to imply a floor from -> skip.
    led = _ledger(
        2026, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=None, reserve_margin=-0.30
    )
    run = _mk_run([led], iso="PJM")
    assert C.check_i12_reserve_margin(run).status == C.PASS


def test_i12_capacity_market_floor_threads_year():
    # D-1 repair + hold-last (card C-A): the requirement-implied floor moves
    # with the delivery year's FPR. rm -12.5% is INSIDE the stale year-less
    # band (floor -12.90%) but below both the 2026 published-FPR floor
    # (-11.94%) and the 2029+ held-last floor (-9.72%) -> two excursions
    # (WARN; FAIL needs 3 consecutive), and the summary shows the per-year
    # band drift (first..last).
    leds = [
        _ledger(
            y, {"gas_cc": 10000}, {"gas_cc": 10000}, peak=5000, reserve_margin=-0.125
        )
        for y in (2026, 2030)
    ]
    run = _mk_run(leds, iso="PJM")
    res = C.check_i12_reserve_margin(run)
    assert res.status == C.WARN, res.detail
    assert "2026" in res.detail and "2030" in res.detail
    assert ".." in res.detail  # first-year band != last-year band, both shown


def test_i12_fails_sustained_excursion():
    leds = [
        _ledger(y, {"gas_cc": 100}, {"gas_cc": 100}, reserve_margin=0.60)
        for y in (2026, 2027, 2028)
    ]
    assert C.check_i12_reserve_margin(_mk_run(leds)).status == C.FAIL


# --------------------------------------------------------------------------- #
# I13 cobweb
# --------------------------------------------------------------------------- #
def test_i13_warns_on_alternating_builds():
    leds = []
    for i, y in enumerate(range(2026, 2033)):
        mw = 500.0 if i % 2 == 0 else 0.0
        leds.append(
            _ledger(
                y,
                {"gas_cc": 100},
                {"gas_cc": 100},
                renewable_additions=[{"zone": "N", "tech": "solar", "mw": mw}],
            )
        )
    assert C.check_i13_cobweb(_mk_run(leds)).status == C.WARN


# --------------------------------------------------------------------------- #
# Paired P1-P3
# --------------------------------------------------------------------------- #
def test_p1_co2_monotone_pass_and_fail():
    base = _mk_run([], years={2026: _mk_yeardata(2026)})
    # Scale down emissions in the "high carbon" run → lower cumulative CO2.
    high = _mk_run([], years={2026: _mk_yeardata(2026)})
    high.years[2026].result.emissions = high.years[2026].result.emissions * 0.5
    assert C.check_p1_co2_monotone(base, high).status == C.PASS
    # A high-carbon run with MORE CO2 fails.
    worse = _mk_run([], years={2026: _mk_yeardata(2026)})
    worse.years[2026].result.emissions = worse.years[2026].result.emissions * 2.0
    assert C.check_p1_co2_monotone(base, worse).status == C.FAIL


def test_p1_reconstructs_co2_from_context_rate_when_emissions_absent():
    # Forecast-path bundles carry no emissions array (a downstream/backcast
    # step); P1 must reconstruct dispatch x context emission_rate instead of
    # SKIPping "emissions absent" (the 2026-07-12 weekly's standing gap).
    def _run_with_rate(scale):
        run = _mk_run([], years={2026: _mk_yeardata(2026)})
        yd = run.years[2026]
        yd.result.emissions = None
        yd.context.emission_rate = np.full(yd.result.dispatch.shape[0], 0.4 * scale)
        return run

    base, high = _run_with_rate(1.0), _run_with_rate(0.5)
    assert C.check_p1_co2_monotone(base, high).status == C.PASS
    worse = _run_with_rate(2.0)
    assert C.check_p1_co2_monotone(base, worse).status == C.FAIL


def test_p1_still_skips_when_no_emissions_and_no_rate():
    base = _mk_run([], years={2026: _mk_yeardata(2026)})
    high = _mk_run([], years={2026: _mk_yeardata(2026)})
    for run in (base, high):
        run.years[2026].result.emissions = None  # and _Ctx has no emission_rate
    assert C.check_p1_co2_monotone(base, high).status == C.SKIP


def test_carbon_pair_premise_holds_on_additive_delta_arm():
    """The D26 repaired arm (base + carbon_price_delta) passes the premise
    with a strictly positive year-by-year delta table in the run record."""
    from market_sim.config.scenarios import ScenarioConfig

    years = {y: _mk_yeardata(y) for y in (2026, 2027)}
    base = _mk_run(
        [],
        years=dict(years),
        config=ScenarioConfig(iso="NEISO", start_year=2026, end_year=2027),
        iso="NEISO",
    )
    high = _mk_run(
        [],
        years=dict(years),
        config=ScenarioConfig(
            iso="NEISO", start_year=2026, end_year=2027, carbon_price_delta=25.0
        ),
        iso="NEISO",
    )
    res = C.carbon_pair_premise(base, high)
    assert res.status == C.PASS
    assert res.data is not None
    assert res.data["years"] == [2026, 2027]
    assert all(d == pytest.approx(25.0) for d in res.data["delta"])


def test_carbon_pair_premise_fails_on_replacement_override_inversion():
    """The D21/D23 broken construction: carbon_price=25 REPLACES a program
    ISO's escalating projected trajectory, so the 'high' arm is a CUT in
    every year — premise FAIL, and run_paired refuses to score P1."""
    from market_sim.config.scenarios import ScenarioConfig

    years = {y: _mk_yeardata(y) for y in (2026, 2027)}
    base = _mk_run(
        [],
        years=dict(years),
        config=ScenarioConfig(iso="NEISO", start_year=2026, end_year=2027),
        iso="NEISO",
    )
    high = _mk_run(
        [],
        years=dict(years),
        config=ScenarioConfig(
            iso="NEISO", start_year=2026, end_year=2027, carbon_price=25.0
        ),
        iso="NEISO",
    )
    res = C.carbon_pair_premise(base, high)
    assert res.status == C.FAIL
    assert "MIS-CONSTRUCTED" in res.detail
    # NEISO's projected RGGI base is $26.05 in 2026 — above the flat $25.
    assert res.data["delta"][0] < 0.0


def test_carbon_pair_premise_holds_on_no_program_iso_absolute_pair():
    """On a program-free ISO (ERCOT) the historical 0 → 25 absolute pair is a
    genuine increase — the guard does not fire on a clean construction."""
    from market_sim.config.scenarios import ScenarioConfig

    years = {y: _mk_yeardata(y) for y in (2026, 2027)}
    base = _mk_run(
        [],
        years=dict(years),
        config=ScenarioConfig(iso="ERCOT", start_year=2026, end_year=2027),
    )
    high = _mk_run(
        [],
        years=dict(years),
        config=ScenarioConfig(
            iso="ERCOT", start_year=2026, end_year=2027, carbon_price=25.0
        ),
    )
    assert C.carbon_pair_premise(base, high).status == C.PASS


# --------------------------------------------------------------------------- #
# capx-D73: the premise from COMMITTED run_config.json (zero LP) — one core,
# two routes, and the committed golden pairs pinned as the phase-0 table.
# --------------------------------------------------------------------------- #
def _write_run_config(path, scenario_config, solved_years=None):
    rc = {"scenario_config": scenario_config}
    if solved_years is not None:
        rc["solved_years"] = solved_years
    path.write_text(json.dumps(rc))
    return path


def test_scenario_config_from_run_config_rebuilds_and_drops_unknown_keys_loudly(
    tmp_path,
):
    """The committed record rebuilds to the same resolved config; a key the
    codebase has since deleted is dropped with a RuntimeWarning (the
    ScenarioConfig.from_yaml discipline, rule 26), never a TypeError; and
    solved_years falls back to start..end when the record carries none."""
    rc = _write_run_config(
        tmp_path / "run_config.json",
        {
            "iso": "NEISO",
            "start_year": 2026,
            "end_year": 2028,
            "carbon_price_delta": 25.0,
            "a_knob_deleted_since": 1.0,
        },
    )
    with pytest.warns(RuntimeWarning, match="a_knob_deleted_since"):
        cfg, years = C.scenario_config_from_run_config(rc)
    assert cfg.iso == "NEISO" and cfg.carbon_price_delta == 25.0
    assert years == [2026, 2027, 2028]
    rc2 = _write_run_config(
        tmp_path / "rc2.json", {"iso": "NEISO"}, solved_years=[2027, 2026]
    )
    assert C.scenario_config_from_run_config(rc2)[1] == [2026, 2027]
    with pytest.raises(SystemExit):
        C.scenario_config_from_run_config({"no": "block"})


def test_run_paired_run_configs_monotone_pair_premise_pass_p1_unscored(tmp_path):
    base = _write_run_config(
        tmp_path / "base.json",
        {"iso": "NEISO", "start_year": 2026, "end_year": 2027},
        solved_years=[2026, 2027],
    )
    high = _write_run_config(
        tmp_path / "high.json",
        {
            "iso": "NEISO",
            "start_year": 2026,
            "end_year": 2027,
            "carbon_price_delta": 25.0,
        },
        solved_years=[2026, 2027],
    )
    rows = C.run_paired_run_configs(base, high)
    by = {r.ident: r for r in rows}
    assert set(by) == {"P1", "P1.premise"}
    assert by["P1.premise"].status == C.PASS
    assert by["P1.premise"].data["years"] == [2026, 2027]
    assert all(d == pytest.approx(25.0) for d in by["P1.premise"].data["delta"])
    # P1 is never scored at this grain — emissions live in the caches.
    assert by["P1"].status == C.SKIP and "not scored at this grain" in by["P1"].detail


def test_run_paired_run_configs_inverted_pair_is_misconstructed_never_scored(tmp_path):
    """The archived D21 construction (carbon_price=25 REPLACING NEISO's
    projected RGGI base): the route emits a FAIL premise row and a SKIP P1 —
    never a PASS or FAIL P1 — so the scorer's FC-6.2 reclassification fires."""
    base = _write_run_config(
        tmp_path / "base.json",
        {"iso": "NEISO", "start_year": 2026, "end_year": 2027},
        solved_years=[2026, 2027],
    )
    high = _write_run_config(
        tmp_path / "high.json",
        {"iso": "NEISO", "start_year": 2026, "end_year": 2027, "carbon_price": 25.0},
        solved_years=[2026, 2027],
    )
    rows = C.run_paired_run_configs(base, high)
    by = {r.ident: r for r in rows}
    assert by["P1.premise"].status == C.FAIL
    assert "MIS-CONSTRUCTED" in by["P1.premise"].detail
    assert by["P1.premise"].data["delta"][0] < 0.0
    assert by["P1"].status == C.SKIP
    assert by["P1"].status not in (C.PASS, C.FAIL)
    assert "see P1.premise" in by["P1"].detail


def test_cache_route_and_run_config_route_share_one_premise_core():
    """Rule 19: the cache-directory front (carbon_pair_premise) and the
    committed-config core emit the identical row for the same pair."""
    from market_sim.config.scenarios import ScenarioConfig

    years = {y: _mk_yeardata(y) for y in (2026, 2027)}
    b_cfg = ScenarioConfig(iso="NEISO", start_year=2026, end_year=2027)
    h_cfg = ScenarioConfig(
        iso="NEISO", start_year=2026, end_year=2027, carbon_price=25.0
    )
    base = _mk_run([], years=dict(years), config=b_cfg, iso="NEISO")
    high = _mk_run([], years=dict(years), config=h_cfg, iso="NEISO")
    via_cache = C.carbon_pair_premise(base, high)
    via_configs = C.carbon_pair_premise_from_configs(b_cfg, h_cfg, [2026, 2027])
    assert via_cache == via_configs
    assert C.carbon_pair_premise_from_configs(b_cfg, h_cfg, []).status == C.SKIP


def test_paired_run_configs_cli_json_and_pair_kind_guard(tmp_path, capsys):
    base = _write_run_config(
        tmp_path / "base.json",
        {"iso": "ERCOT", "start_year": 2026, "end_year": 2026},
        solved_years=[2026],
    )
    high = _write_run_config(
        tmp_path / "high.json",
        {"iso": "ERCOT", "start_year": 2026, "end_year": 2026, "carbon_price": 25.0},
        solved_years=[2026],
    )
    rc = C.main(["--paired-run-configs", str(base), str(high), "--json"])
    rows = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert [(r["ident"], r["status"]) for r in rows] == [
        ("P1", C.SKIP),
        ("P1.premise", C.PASS),
    ]
    assert rows[1]["data"]["delta"] == [pytest.approx(25.0)]
    assert "data" not in rows[0]  # rows without evidence keep their exact shape
    # Table mode prints the year-by-year signal table.
    C.main(["--paired-run-configs", str(base), str(high)])
    out = capsys.readouterr().out
    assert "effective carbon signal" in out and "2026" in out
    with pytest.raises(SystemExit):
        C.main(["--paired-run-configs", str(base), str(high), "--pair-kind", "gas_up"])


_GOLDEN_FAMILIES = Path(__file__).resolve().parents[2] / "results/ff-t3-neiso-golden"
_LIVE_CARBON_PAIRS = [
    (fam, "carbon_plus25") for fam in ("bau", "bau-d46", "bau-prera-2026-08-31")
]
_ARCHIVED_CARBON_PAIR = ("bau-prera-2026-08-31", "carbon25")


def _arm_rc(family: str, arm: str) -> Path:
    return _GOLDEN_FAMILIES / family / "fc6" / "arms" / arm / "run_config.json"


@pytest.mark.parametrize("family,arm", _LIVE_CARBON_PAIRS)
def test_committed_live_carbon_pairs_are_monotone_plus25_every_year(family, arm):
    """capx-D73 phase 0(c): every committed carbon_plus25 pair resolves to
    +$25.00/t above its base in all 25 solved years — the guard's live effect
    is nil (FINDING-capx-d73-2026-09-06.md §2.3)."""
    base, high = _arm_rc(family, "base"), _arm_rc(family, arm)
    if not (base.exists() and high.exists()):
        pytest.skip(f"{family}/{arm} run_config.json not checked out")
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # deleted-knob drops
        rows = C.run_paired_run_configs(base, high)
    premise = next(r for r in rows if r.ident == "P1.premise")
    assert premise.status == C.PASS
    assert len(premise.data["years"]) == 25
    assert all(d == pytest.approx(25.0, abs=1e-6) for d in premise.data["delta"])


def test_committed_archived_carbon25_pair_is_inverted_in_every_year():
    """capx-D73 phase 0(c): the archived D21 `carbon25` arm (the ONLY
    inverted pair in the repository) is a cut of −$1.05 (2026) → −$107.16
    (2050) against its base, so the guard emits MIS-CONSTRUCTED for it and
    never a scored P1 — D23 §2.5 / D72 §6 to the cent."""
    family, arm = _ARCHIVED_CARBON_PAIR
    base, high = _arm_rc(family, "base"), _arm_rc(family, arm)
    if not (base.exists() and high.exists()):
        pytest.skip(f"{family}/{arm} run_config.json not checked out")
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        rows = C.run_paired_run_configs(base, high)
    by = {r.ident: r for r in rows}
    premise = by["P1.premise"]
    assert premise.status == C.FAIL and "25/25 years" in premise.detail
    assert premise.data["years"][0] == 2026 and premise.data["years"][-1] == 2050
    assert premise.data["delta"][0] == pytest.approx(-1.05, abs=0.005)
    assert premise.data["delta"][-1] == pytest.approx(-107.16, abs=0.005)
    assert premise.data["base"][0] == pytest.approx(26.05, abs=0.005)
    assert all(d < 0.0 for d in premise.data["delta"])
    assert by["P1"].status == C.SKIP


def test_p2_merit_sign():
    base = _mk_run([], years={2026: _mk_yeardata(2026, fuels=("gas_cc", "coal"))})
    gas_up = _mk_run([], years={2026: _mk_yeardata(2026, fuels=("gas_cc", "coal"))})
    # Engineer: gas up ⇒ less gas_cc, more coal, higher price + objective.
    gu = gas_up.years[2026].result
    b = base.years[2026].result
    gu.dispatch[0] = b.dispatch[0] * 0.5  # gas_cc (row 0) down
    gu.dispatch[1] = b.dispatch[1] * 1.5  # coal (row 1) up
    gu.prices[:] = b.prices + 5.0
    gu.objective_value = b.objective_value + 100.0
    assert C.check_p2_merit_sign(base, gas_up).status == C.PASS


# --------------------------------------------------------------------------- #
# P2 gas-leg scope (capx-D35, FINDING-capx-d35-p2-scope-2026-09-02)
# --------------------------------------------------------------------------- #
def test_p2_gas_scope_is_the_models_gas_partition():
    """The checker's literal mirrors data/fuel/_shared._GAS_FUEL_IDX exactly."""
    from market_sim.data.fleet import FUEL_TYPE_MAP
    from market_sim.data.fuel._shared import _GAS_FUEL_IDX

    name_of = {idx: name for name, idx in FUEL_TYPE_MAP.items()}
    assert C.GAS_FIRED_FUELS == frozenset(name_of[i] for i in _GAS_FUEL_IDX)
    assert C.GAS_FIRED_FUELS <= C.THERMAL_FUELS


def _ev(year, fuel_gen, lw_price, objective=None):
    return {year: {"fuel_gen": fuel_gen, "lw_price": lw_price, "objective": objective}}


def test_p2_migration_pair_scores_the_gas_total_not_the_class_label():
    """Base 100 % CCS-converted, arm holds unabated CC: the golden-2 shape.

    Per-class gas_cc rises 0 → 23 TWh (the legacy key reads a violation) while
    total gas-fired generation FALLS 36.5 → 35.4 TWh. The repaired leg PASSes
    on the all-gas sign and reports the legacy key as confounded.
    """
    base = _ev(
        2050,
        {"gas_cc_ccs": 35.08e6, "gas_ct": 1.22e6, "gas_st": 0.23e6, "import": 25.6e6},
        79.16,
    )
    up = _ev(
        2050,
        {
            "gas_cc": 23.19e6,
            "gas_cc_ccs": 10.83e6,
            "gas_ct": 1.0e6,
            "gas_st": 0.35e6,
            "import": 25.8e6,
        },
        93.95,
    )
    r = C.check_p2_merit_sign_evidence(base, up)
    assert r.status == C.PASS, r.detail
    assert r.data["legacy_gas_cc_key"]["would_fail"] is True
    assert r.data["legacy_gas_cc_key"]["disagrees_with_gas_fired_total"] is True
    assert r.data["scored"] == ["gas↓", "price↑"]
    assert r.data["not_scored"] == ["objective↑"]
    assert "objective↑" in r.detail  # named as unscored, never assumed
    assert r.data["gas_fired_mwh"]["base"] == pytest.approx(36.53e6)
    assert r.data["gas_fired_mwh"]["up"] == pytest.approx(35.37e6)


def test_p2_fails_when_total_gas_fired_generation_rises():
    """A dearer-gas world generating MORE from gas is a real sign violation."""
    base = _ev(2030, {"gas_cc": 30e6, "gas_ct": 2e6, "coal": 5e6}, 60.0, 1e9)
    up = _ev(2030, {"gas_cc": 29e6, "gas_ct": 4e6, "coal": 6e6}, 70.0, 1.1e9)
    r = C.check_p2_merit_sign_evidence(base, up)
    assert r.status == C.FAIL
    assert "wrong: gas↓" in r.detail
    # The per-class key would have PASSED here (gas_cc fell) — the two
    # constructions disagree in the other direction too, and the total wins.
    assert r.data["legacy_gas_cc_key"]["would_fail"] is False
    assert r.data["legacy_gas_cc_key"]["disagrees_with_gas_fired_total"] is True
    assert r.data["scored"] == ["coal↑", "gas↓", "price↑", "objective↑"]


def test_p2_same_fleet_pair_keeps_every_legacy_subcheck():
    """No migration: coal↑ / gas↓ / price↑ / objective↑ all score, all PASS."""
    base = _ev(2030, {"gas_cc": 30e6, "gas_ct": 2e6, "coal": 5e6}, 60.0, 1e9)
    up = _ev(2030, {"gas_cc": 25e6, "gas_ct": 1e6, "coal": 8e6}, 70.0, 1.1e9)
    r = C.check_p2_merit_sign_evidence(base, up)
    assert r.status == C.PASS
    assert r.data["scored"] == ["coal↑", "gas↓", "price↑", "objective↑"]
    assert r.data["not_scored"] == []
    assert r.data["legacy_gas_cc_key"]["disagrees_with_gas_fired_total"] is False


def test_p2_scores_the_last_common_year_and_carries_the_series():
    base = {**_ev(2026, {"gas_cc": 10e6}, 50.0), **_ev(2027, {"gas_cc": 11e6}, 51.0)}
    up = {**_ev(2026, {"gas_cc": 9e6}, 55.0), **_ev(2028, {"gas_cc": 9e6}, 56.0)}
    r = C.check_p2_merit_sign_evidence(base, up)
    assert r.data["year"] == 2026 and r.data["series"]["years"] == [2026]
    assert C.check_p2_merit_sign_evidence({}, up).status == C.SKIP


def test_p2_summary_evidence_matches_run_evidence():
    """A summary built from a run's own _fuel_gen_mwh scores identically (bar objective)."""
    base = _mk_run([], years={2026: _mk_yeardata(2026, fuels=("gas_cc", "coal"))})
    up = _mk_run([], years={2026: _mk_yeardata(2026, fuels=("gas_cc", "coal"))})
    u, b = up.years[2026].result, base.years[2026].result
    u.dispatch[0] = b.dispatch[0] * 0.5
    u.dispatch[1] = b.dispatch[1] * 1.5
    u.prices[:] = b.prices + 5.0

    def summary(run):
        return {
            "trajectory": [
                {
                    "year": y,
                    "lw_price": C._load_weighted_price(yd),
                    "generation_by_fuel_mwh": C._fuel_gen_mwh(yd),
                }
                for y, yd in run.years.items()
            ]
        }

    from_run = C.check_p2_merit_sign(base, up)
    from_summary = C.check_p2_merit_sign_evidence(
        C.p2_evidence_from_summary(summary(base)),
        C.p2_evidence_from_summary(summary(up)),
    )
    assert from_run.status == from_summary.status == C.PASS
    assert from_run.data["gas_fired_mwh"] == from_summary.data["gas_fired_mwh"]
    assert from_run.data["scored"] == ["coal↑", "gas↓", "price↑", "objective↑"]
    assert from_summary.data["scored"] == ["coal↑", "gas↓", "price↑"]
    assert from_summary.data["not_scored"] == ["objective↑"]
    # A pre-D29 summary (no energy block) yields no scoreable year.
    assert (
        C.p2_evidence_from_summary({"trajectory": [{"year": 2026, "lw_price": 1.0}]})
        == {}
    )


def test_p2_summaries_cli_scores_gas_up_only(tmp_path):
    base = tmp_path / "base.json"
    up = tmp_path / "up.json"
    base.write_text(
        json.dumps(
            {
                "trajectory": [
                    {
                        "year": 2030,
                        "lw_price": 60.0,
                        "generation_by_fuel_mwh": {"gas_cc": 10e6},
                    }
                ]
            }
        )
    )
    up.write_text(
        json.dumps(
            {
                "trajectory": [
                    {
                        "year": 2030,
                        "lw_price": 65.0,
                        "generation_by_fuel_mwh": {"gas_cc": 9e6},
                    }
                ]
            }
        )
    )
    rows = C.run_paired_summaries(base, up, "gas_up")
    assert [r.ident for r in rows] == ["P2"] and rows[0].status == C.PASS
    with pytest.raises(SystemExit):
        C.run_paired_summaries(base, up, "carbon")


_GOLDEN2_ARMS = (
    Path(__file__).resolve().parents[2] / "results/ff-t3-neiso-golden/bau/fc6/arms"
)


@pytest.mark.skipif(
    not (_GOLDEN2_ARMS / "gasup150/full_horizon_summary.json").exists(),
    reason="golden-2 FC-6 arm summaries not checked out",
)
def test_p2_legacy_key_on_committed_golden2_summaries_reproduces_the_committed_row():
    """Control: the retired per-class key, computed at summary grain, reproduces
    the committed golden-2 P2 detail ('year 2050: wrong: gas_cc↓') exactly —
    the summary grain IS the cache grain the committed row was scored on."""
    b = C.p2_evidence_from_summary(
        json.loads((_GOLDEN2_ARMS / "base/full_horizon_summary.json").read_text())
    )
    g = C.p2_evidence_from_summary(
        json.loads((_GOLDEN2_ARMS / "gasup150/full_horizon_summary.json").read_text())
    )
    year = max(set(b) & set(g))
    fb, fg = b[year]["fuel_gen"], g[year]["fuel_gen"]
    assert year == 2050 and fb.get("coal", 0) == 0
    legacy_failed = [
        n
        for n, ok in (
            ("gas_cc↓", fg.get("gas_cc", 0) <= fb.get("gas_cc", 0) + 1e-6),
            ("price↑", g[year]["lw_price"] >= b[year]["lw_price"] - 1e-6),
        )
        if not ok
    ]
    assert (
        f"year {year}: wrong: " + ",".join(legacy_failed) == "year 2050: wrong: gas_cc↓"
    )
    # And the repaired row's evidence block records exactly that confound.
    r = C.check_p2_merit_sign_evidence(b, g)
    assert r.data["legacy_gas_cc_key"]["would_fail"] is True
    assert r.data["legacy_gas_cc_key"]["base_mwh"] == 0.0


def test_p3_perturbation_stability():
    base = _mk_run(
        [
            _ledger(
                2026,
                {"gas_cc": 100},
                {"gas_cc": 100},
                thermal_additions=[
                    {
                        "unit_id": "n",
                        "fuel": "gas_cc",
                        "mw": 1000,
                        "zone": "N",
                        "source": "economic",
                        "eia860_id": None,
                    }
                ],
            )
        ]
    )
    small = _mk_run(
        [
            _ledger(
                2026,
                {"gas_cc": 100},
                {"gas_cc": 100},
                thermal_additions=[
                    {
                        "unit_id": "n",
                        "fuel": "gas_cc",
                        "mw": 1050,
                        "zone": "N",
                        "source": "economic",
                        "eia860_id": None,
                    }
                ],
            )
        ]
    )
    assert C.check_p3_perturbation(base, small).status == C.PASS
    big = _mk_run(
        [
            _ledger(
                2026,
                {"gas_cc": 100},
                {"gas_cc": 100},
                thermal_additions=[
                    {
                        "unit_id": "n",
                        "fuel": "gas_cc",
                        "mw": 2000,
                        "zone": "N",
                        "source": "economic",
                        "eia860_id": None,
                    }
                ],
            )
        ]
    )
    assert C.check_p3_perturbation(base, big).status == C.WARN


# --------------------------------------------------------------------------- #
# Real-LP integration (slow, opt-in) — closes TC-3
# --------------------------------------------------------------------------- #
@pytest.mark.slow
@pytest.mark.skipif(
    os.environ.get("RUN_SLOW_FORECAST") != "1",
    reason="set RUN_SLOW_FORECAST=1 to run the real multi-year ERCOT forecast",
)
def test_real_forecast_invariants_pass(tmp_path):
    """Solve a real multi-year ERCOT forecast and assert every invariant holds.

    This is the first real-LP exercise of the capacity-evolution loop + ledger
    (TC-3). Uses the legacy heat-rate-bin fleet (smaller LP) purely to bound
    runtime; it is a full-8760, two-pass HiGHS solve, not a mock.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.results import cache as cachemod
    from market_sim.runner import run_scenario_iso

    cachemod.CACHE_ROOT = tmp_path
    config = ScenarioConfig(
        iso="ERCOT", start_year=2026, end_year=2028, hours=8760, use_campd_bins=False
    )
    key = run_scenario_iso(config, "ERCOT")
    run_dir = tmp_path / "ERCOT" / key

    # Ledger present and populated for every solved year.
    run = C.load_run(run_dir)
    assert set(run.ledgers) == {2026, 2027, 2028}
    for led in run.ledgers.values():
        assert led["solve_counts"]["P0"] == 1 and led["solve_counts"]["P1"] == 1
        assert led["fleet_by_fuel_after"], "fleet-by-fuel must be recorded"
        assert led["peak_demand_mw"] and led["peak_demand_mw"] > 0
        assert led["reserve_margin"] is not None

    # The *machinery-correctness* invariants — those that validate the ledger,
    # persistence and one-pass solve rather than model calibration — must PASS
    # on a genuine forecast. Calibration invariants (I7 reliability floor, I12
    # reserve-margin band, I14 price band) may legitimately FAIL/WARN on a raw
    # forecast; those are findings for docs/forecast-invariant-findings.md, not
    # a defect in the checker, so they are not asserted here.
    results = {r.ident: r for r in C.run_single(run_dir)}
    for ident in ("I1", "I2", "I4", "I5", "I11"):
        assert results[ident].status == C.PASS, (
            f"{ident} must pass on a real forecast: {results[ident].detail}"
        )
    # I8: planned additions must be EIA-860-traceable (unit_id encodes plant).
    assert results["I8"].status != C.FAIL, results["I8"].detail
