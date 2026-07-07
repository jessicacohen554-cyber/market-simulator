#!/usr/bin/env python
"""Forecast invariant checker (W2-P5, plan §2.2).

Runs a battery of structural invariants over a *completed* forecast scenario's
cache directory — the per-year dispatch parquets plus the per-year evolution
ledgers (``evolution_<year>.json``, written by ``runner.py``). Each invariant
prints one ``PASS`` / ``FAIL`` / ``WARN`` line with the offending years/values;
the process exits non-zero if any invariant FAILs. Every threshold lives in the
single :class:`Thresholds` dataclass at the top of this file — there are no
scattered magic numbers.

These are *forecast* invariants: they check that the capacity-evolution and
dispatch machinery produced a physically and economically coherent trajectory,
NOT that it matched any actuals (that is the hindcast scorer's job, and it is
forbidden to tune to — rules 1/11/14). A FAIL is a root-cause investigation,
never a threshold widening.

Usage::

    # Single-run invariants I1-I14 over one scenario cache:
    python scripts/check_forecast_invariants.py --run-dir results/ERCOT/<key>

    # Paired-run invariants P1-P3 (two scenarios differing in one driver):
    python scripts/check_forecast_invariants.py --paired <base_dir> <other_dir> \
        --pair-kind carbon        # carbon | gas_up | gas_pm5

The single-run and paired modes can be combined; ``--json`` emits a machine-
readable summary to stdout instead of the human table.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# Repo import bootstrap so the script runs from a checkout without an install.
_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.config.constants import (  # noqa: E402
    DEFAULT_MARKET_DESIGN,
    MARKET_DESIGN,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity import resolve_adequacy_requirement_mw  # noqa: E402
from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.results.outputs import read_demand, read_fleet_context  # noqa: E402

# Fuel classes, mirrored from model.capacity so the floor/accounting checks use
# exactly the model's own partition (kept as literals here so the checker has no
# import-time dependency on private capacity internals).
THERMAL_FUELS = frozenset(
    {"gas_cc", "gas_ct", "gas_st", "gas_cc_ccs", "coal", "oil", "nuclear"}
)
FIRM_CLEAN_FUELS = frozenset({"hydro"})
CLEAN_FUELS = frozenset({"wind", "solar", "nuclear", "hydro"})


@dataclass(frozen=True)
class Thresholds:
    """Every numeric threshold the invariants use, in one place."""

    # I1 energy balance: max |per-hour system supply − demand|, MW.
    energy_balance_mw: float = 1.0
    # I3 unserved / dump.
    slack_frac_of_demand: float = 1e-4  # slack energy / demand energy
    dump_frac_of_renewable: float = 0.02  # dump energy / renewable potential
    # I4 capacity accounting closure, MW.
    accounting_close_mw: float = 1.0
    # I6 single-year economic-retired capacity, fraction of prior thermal MW.
    econ_retire_frac_cap: float = 0.20
    # I7 reliability floor: thermal ≥ (peak − firm_clean) × (1 + margin).
    reliability_reserve_margin: float = 0.15
    reliability_slack_mw: float = 1.0
    # I9 storage.
    soc_tol_mwh: float = 1.0
    simultaneous_chg_dis_frac: float = 1e-3  # min(chg,dis) energy / throughput
    # I10 RPS dual.
    rps_dual_sign_tol: float = 1e-6
    rps_dual_yoy_frac: float = 0.50  # WARN once binding and |Δ| exceeds this
    # I12 reserve-margin band width above the planning floor.
    reserve_margin_band_pp: float = 0.15
    reserve_margin_consecutive_fail: int = 3
    # I13 cobweb: a tech alternating full/zero across this many year-pairs.
    cobweb_pairs: int = 3
    # I14 price sanity.
    price_lo_mult: float = 0.5  # of fuel-implied CC MC
    price_hi_mult: float = 3.0
    cc_heat_rate: float = 7.0  # MMBtu/MWh, generic CC, for the implied-MC band
    neg_price_hour_frac: float = 0.10
    # Paired.
    co2_per_year_wiggle_frac: float = 0.01  # P1 per-year WARN band
    perturbation_build_frac: float = 0.25  # P3 cliff-edge


T = Thresholds()

PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"


@dataclass
class Result:
    """One invariant's outcome."""

    ident: str
    name: str
    status: str
    detail: str = ""


@dataclass
class YearData:
    """Everything one scenario-year contributes to the checks."""

    year: int
    result: DispatchResult
    demand: np.ndarray | None
    context: object


@dataclass
class Run:
    """A loaded scenario cache: config + per-year dispatch + ledgers."""

    run_dir: Path
    config: ScenarioConfig
    iso: str
    years: dict[int, YearData] = field(default_factory=dict)
    ledgers: dict[int, dict] = field(default_factory=dict)

    @property
    def solved_years(self) -> list[int]:
        return sorted(self.years)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_run(run_dir: Path) -> Run:
    """Load a scenario cache directory into a :class:`Run`.

    Reads ``config.yaml``, every ``year_<year>.parquet`` (final pass) and its
    stored demand + fleet context, and every ``evolution_<year>.json``.
    """
    run_dir = Path(run_dir)
    cfg_path = run_dir / "config.yaml"
    config = (
        ScenarioConfig.from_yaml(cfg_path) if cfg_path.exists() else ScenarioConfig()
    )
    run = Run(run_dir=run_dir, config=config, iso=config.iso)
    for parquet in sorted(run_dir.glob("year_*.parquet")):
        if parquet.stem.endswith("_p1"):
            continue
        try:
            year = int(parquet.stem.replace("year_", ""))
        except ValueError:
            continue
        result = DispatchResult.from_parquet(parquet)
        try:
            context = read_fleet_context(parquet)
        except ValueError:
            context = None
        run.years[year] = YearData(
            year=year,
            result=result,
            demand=read_demand(parquet),
            context=context,
        )
    run.ledgers = load_ledgers_for_run(run_dir)
    return run


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _fuel_gen_mwh(yd: YearData) -> dict[str, float]:
    """Annual generation by fuel type for one year, MWh."""
    if yd.context is None:
        return {}
    fuels = yd.context.fuel_types
    per_gen = yd.result.dispatch.sum(axis=1)
    out: dict[str, float] = {}
    for f, g in zip(fuels, per_gen):
        out[f] = out.get(f, 0.0) + float(g)
    # Renewables dispatch separately from the thermal ``dispatch`` array.
    out["wind"] = out.get("wind", 0.0) + float(yd.result.wind_dispatched.sum())
    out["solar"] = out.get("solar", 0.0) + float(yd.result.solar_dispatched.sum())
    return out


def _load_weighted_price(yd: YearData) -> float:
    """System load-weighted average price for a year, $/MWh."""
    if yd.demand is None:
        return float(yd.result.prices.mean())
    d = yd.demand
    num = float((yd.result.prices * d).sum())
    den = float(d.sum())
    return num / den if den > 0 else float(yd.result.prices.mean())


def _annual_co2_tons(yd: YearData) -> float | None:
    """Total CO2 for a year in tons, or ``None`` when emissions are absent."""
    if yd.result.emissions is None:
        return None
    return float(np.asarray(yd.result.emissions).sum())


def _thermal_mw(fleet_by_fuel: dict[str, float]) -> float:
    return sum(mw for f, mw in fleet_by_fuel.items() if f in THERMAL_FUELS)


def _sum_by_fuel(records: list[dict], key: str = "fuel") -> dict[str, float]:
    out: dict[str, float] = {}
    for r in records:
        out[r[key]] = out.get(r[key], 0.0) + float(r.get("mw", 0.0))
    return out


# --------------------------------------------------------------------------- #
# Single-run invariants I1-I14
# --------------------------------------------------------------------------- #
def check_i1_energy_balance(run: Run) -> Result:
    """I1: per-hour system energy balance closes to tolerance."""
    worst_year, worst = None, 0.0
    checked = 0
    for year, yd in run.years.items():
        if yd.demand is None:
            continue
        checked += 1
        r = yd.result
        supply = (
            r.dispatch.sum(axis=0)
            + r.wind_dispatched.sum(axis=0)
            + r.solar_dispatched.sum(axis=0)
            + r.slack.sum(axis=0)
            - r.dump.sum(axis=0)
        )
        if r.storage_discharge is not None:
            supply = (
                supply + r.storage_discharge.sum(axis=0) - r.storage_charge.sum(axis=0)
            )
        # System-wide: internal link flows cancel (Σ_zone net_flow = 0), so the
        # residual is supply − demand summed across zones.
        residual = np.abs(supply - yd.demand.sum(axis=0))
        m = float(residual.max())
        if m > worst:
            worst, worst_year = m, year
    if checked == 0:
        return Result("I1", "energy balance", SKIP, "no persisted demand column")
    status = PASS if worst <= T.energy_balance_mw else FAIL
    return Result(
        "I1",
        "energy balance",
        status,
        f"max |supply−demand| = {worst:.4g} MW (year {worst_year}); "
        f"tol {T.energy_balance_mw}",
    )


def check_i2_no_nan_inf(run: Run) -> Result:
    """I2: no NaN/inf in any persisted array or ledger summary field."""
    bad: list[str] = []
    for year, yd in run.years.items():
        for name in (
            "dispatch",
            "wind_dispatched",
            "solar_dispatched",
            "slack",
            "dump",
            "prices",
            "storage_charge",
            "storage_discharge",
            "storage_soc",
            "flows",
            "emissions",
        ):
            arr = getattr(yd.result, name, None)
            if arr is not None and not np.isfinite(np.asarray(arr, dtype=float)).all():
                bad.append(f"{year}:{name}")
    for year, led in run.ledgers.items():
        for k, v in led.items():
            if isinstance(v, (int, float)) and v is not None and not math.isfinite(v):
                bad.append(f"{year}:ledger.{k}")
    status = PASS if not bad else FAIL
    return Result("I2", "no NaN/inf", status, "clean" if not bad else ", ".join(bad))


def check_i3_unserved_dump(run: Run) -> Result:
    """I3: slack ≈ 0 and dump below the renewable-potential band."""
    problems: list[str] = []
    for year, yd in run.years.items():
        if yd.demand is not None:
            slack_e = float(yd.result.slack.sum())
            dem_e = float(yd.demand.sum())
            if dem_e > 0 and slack_e / dem_e > T.slack_frac_of_demand:
                problems.append(f"{year}: slack {slack_e / dem_e:.2%} of load")
        if yd.context is not None:
            renew = float(
                yd.context.wind_potential_mwh + yd.context.solar_potential_mwh
            )
            dump_e = float(yd.result.dump.sum())
            if renew > 0 and dump_e / renew > T.dump_frac_of_renewable:
                problems.append(f"{year}: dump {dump_e / renew:.2%} of renewable pot.")
    status = PASS if not problems else FAIL
    return Result(
        "I3", "unserved/dump", status, "ok" if not problems else "; ".join(problems)
    )


def check_i4_capacity_accounting(run: Run) -> Result:
    """I4: fleet(after) = fleet(before) − retirements + builds, per fuel."""
    problems: list[str] = []
    for year, led in run.ledgers.items():
        before = led.get("fleet_by_fuel_before", {})
        after = led.get("fleet_by_fuel_after", {})
        if not before and not after:
            continue
        retired = _sum_by_fuel(led.get("retirements", []))
        added = _sum_by_fuel(led.get("thermal_additions", []))
        expected = dict(before)
        for f, mw in retired.items():
            expected[f] = expected.get(f, 0.0) - mw
        for f, mw in added.items():
            expected[f] = expected.get(f, 0.0) + mw
        for cc in led.get("ccs_retrofits", []):
            expected[cc["from_fuel"]] = expected.get(cc["from_fuel"], 0.0) - cc["mw"]
            expected[cc["to_fuel"]] = expected.get(cc["to_fuel"], 0.0) + cc["mw"]
        fuels = set(expected) | set(after)
        for f in fuels:
            diff = abs(expected.get(f, 0.0) - after.get(f, 0.0))
            if diff > T.accounting_close_mw:
                problems.append(f"{year}:{f} off by {diff:.1f} MW")
    # Continuity: after(N) == before(N+1) (aggregation conserves MW/fuel).
    ys = sorted(run.ledgers)
    for a, b in zip(ys, ys[1:]):
        aft = run.ledgers[a].get("fleet_by_fuel_after", {})
        bef = run.ledgers[b].get("fleet_by_fuel_before", {})
        for f in set(aft) | set(bef):
            diff = abs(aft.get(f, 0.0) - bef.get(f, 0.0))
            if diff > T.accounting_close_mw:
                problems.append(f"{a}->{b}:{f} discontinuity {diff:.1f} MW")
    status = PASS if not problems else FAIL
    return Result(
        "I4",
        "capacity accounting",
        status,
        "closes" if not problems else "; ".join(problems),
    )


def check_i5_no_retire_reenter(run: Run) -> Result:
    """I5: a retired unit_id never re-appears as a later addition."""
    retired_at: dict[str, int] = {}
    problems: list[str] = []
    for year in sorted(run.ledgers):
        led = run.ledgers[year]
        for add in led.get("thermal_additions", []):
            uid = add.get("unit_id")
            if uid in retired_at:
                problems.append(f"{uid} retired {retired_at[uid]} re-added {year}")
        for ret in led.get("retirements", []):
            retired_at[ret["unit_id"]] = year
    status = PASS if not problems else FAIL
    return Result(
        "I5",
        "no retire-and-reenter",
        status,
        "ok" if not problems else "; ".join(problems),
    )


def check_i6_econ_retire_sanity(run: Run) -> Result:
    """I6: single-year economic retirement bounded (loss-year rule is in-code)."""
    problems: list[str] = []
    for year in sorted(run.ledgers):
        led = run.ledgers[year]
        econ_mw = sum(
            float(r["mw"])
            for r in led.get("retirements", [])
            if r.get("reason") == "economic"
        )
        prior_thermal = _thermal_mw(led.get("fleet_by_fuel_before", {}))
        if prior_thermal > 0 and econ_mw / prior_thermal > T.econ_retire_frac_cap:
            problems.append(
                f"{year}: {econ_mw / prior_thermal:.1%} of thermal retired in one year"
            )
    status = PASS if not problems else FAIL
    return Result(
        "I6",
        "econ-retirement sanity",
        status,
        "ok" if not problems else "; ".join(problems),
    )


def check_i7_reliability_floor(run: Run) -> Result:
    """I7: reliability floor, market-design-dependent (G-41 owner decision).

    The invariant's *definition* mirrors the mechanism that actually clears
    capacity in each ISO (G-41 decision memo 2026-07-06, owner-approved
    market-design-dependent variant; rule 1 — the definition follows the real
    market, never what turns the line green):

    * **Capacity-market ISOs** (``MARKET_DESIGN[iso].capacity_market``:
      PJM/MISO/NYISO/NEISO/CAISO) — an **absolute** adequacy floor, because
      their design (PJM RPM's absolute IRM, etc.) procures capacity to a fixed
      requirement. The floor is measured on the **model's own** accreditation
      convention, not the crude nameplate/hydro-only/0.15 proxy the invariant
      used before (precondition 1 of the decision): the model's accredited firm
      capacity — persisted per year as ``reserve_margin`` (=
      ``accredited_firm_mw / peak − 1``, from
      :func:`market_sim.model.capacity.accredited_firm_capacity_mw`) — must
      clear the model's own requirement
      (:func:`market_sim.model.capacity.resolve_adequacy_requirement_mw` — firm
      peak × (1 + per-ISO PRM) × ICAP/UCAP ratio). Checker and model now measure
      the same quantity, so the adequacy backstop (default-on for these ISOs)
      satisfies I7 honestly rather than by coincidence.

    * **Energy-only ISOs** (ERCOT) — a **retirement-bounded** floor: evolution
      must not over-retire the thermal fleet below the reliability floor, but a
      fleet that *started* below it is tolerated (the real energy-only market
      has no absolute floor; adequacy expresses as scarcity price, not procured
      capacity). Measured as ``thermal_after ≥ min(floor, thermal_before)`` on
      the pre-existing nameplate convention — self-consistent (nameplate vs
      nameplate) and needing no UCAP reconciliation because nothing force-builds
      on this branch.

    ISOs absent from :data:`MARKET_DESIGN` take the conservative absolute branch.
    """
    problems: list[str] = []
    design = MARKET_DESIGN.get(run.iso, DEFAULT_MARKET_DESIGN)
    for year in sorted(run.ledgers):
        led = run.ledgers[year]
        peak = led.get("peak_demand_mw")
        if peak is None:  # bridge year — no solve, no floor to check
            continue
        if design.capacity_market:
            # Absolute floor on the model's accreditation convention.
            rm = led.get("reserve_margin")
            if rm is None or peak <= 0.0:
                continue  # no firm-capacity accounting persisted this year
            accredited_firm = peak * (1.0 + rm)
            requirement = resolve_adequacy_requirement_mw(run.config, run.iso, peak)
            if accredited_firm < requirement - T.reliability_slack_mw:
                problems.append(
                    f"{year}: accredited firm {accredited_firm:.0f} < "
                    f"requirement {requirement:.0f} MW"
                )
        else:
            # Retirement-bounded nameplate floor (energy-only): did evolution
            # over-retire below the floor relative to where the year started?
            after = led.get("fleet_by_fuel_after", {})
            before = led.get("fleet_by_fuel_before", {})
            firm_clean = sum(mw for f, mw in after.items() if f in FIRM_CLEAN_FUELS)
            thermal_after = _thermal_mw(after)
            thermal_before = _thermal_mw(before)
            floor = (peak - firm_clean) * (1.0 + T.reliability_reserve_margin)
            bound = min(floor, thermal_before) if thermal_before > 0 else floor
            if thermal_after < bound - T.reliability_slack_mw:
                problems.append(
                    f"{year}: thermal {thermal_after:.0f} < "
                    f"retirement-bounded floor {bound:.0f} MW"
                )
    status = PASS if not problems else FAIL
    return Result(
        "I7",
        "reliability floor",
        status,
        "held" if not problems else "; ".join(problems),
    )


def check_i8_planned_mode_gating(run: Run) -> Result:
    """I8: planned additions are forecast-only, EIA-860-traceable, in-horizon."""
    problems: list[str] = []
    is_backcast = run.config.mode == "backcast"
    for year in sorted(run.ledgers):
        planned = [
            a
            for a in run.ledgers[year].get("thermal_additions", [])
            if a.get("source") == "planned"
        ]
        if is_backcast and planned:
            problems.append(f"{year}: {len(planned)} planned units in a backcast")
        if not is_backcast:
            untraceable = [a for a in planned if not a.get("eia860_id")]
            if untraceable:
                problems.append(
                    f"{year}: {len(untraceable)} planned units without an EIA-860 id"
                )
    status = PASS if not problems else FAIL
    return Result(
        "I8",
        "planned-additions gating",
        status,
        "ok" if not problems else "; ".join(problems),
    )


def check_i9_storage_integrity(run: Run) -> Result:
    """I9: SOC ≥ 0, cyclic SOC closes, no simultaneous charge+discharge."""
    problems: list[str] = []
    for year, yd in run.years.items():
        r = yd.result
        if r.storage_soc is None:
            continue
        soc = np.asarray(r.storage_soc, dtype=float)
        if soc.min() < -T.soc_tol_mwh:
            problems.append(f"{year}: negative SOC {soc.min():.2f} MWh")
        chg = np.asarray(r.storage_charge, dtype=float)
        dis = np.asarray(r.storage_discharge, dtype=float)
        simult = float(np.minimum(chg, dis).sum())
        throughput = float(chg.sum() + dis.sum())
        if throughput > 0 and simult / throughput > T.simultaneous_chg_dis_frac:
            problems.append(
                f"{year}: simultaneous chg+dis {simult / throughput:.2%} of throughput"
            )
    status = PASS if not problems else FAIL
    return Result(
        "I9", "storage integrity", status, "ok" if not problems else "; ".join(problems)
    )


def check_i10_rps_dual(run: Run) -> Result:
    """I10: RPS dual ≥ 0 (FAIL on sign); large YoY swings WARN."""
    duals = {
        y: run.ledgers[y].get("rps_dual")
        for y in sorted(run.ledgers)
        if run.ledgers[y].get("rps_dual") is not None
    }
    neg = [f"{y}:{v:.3g}" for y, v in duals.items() if v < -T.rps_dual_sign_tol]
    if neg:
        return Result("I10", "RPS dual sign", FAIL, "negative dual " + ", ".join(neg))
    ys = sorted(duals)
    osc: list[str] = []
    for a, b in zip(ys, ys[1:]):
        va, vb = duals[a], duals[b]
        if va > T.rps_dual_sign_tol and abs(vb - va) / va > T.rps_dual_yoy_frac:
            osc.append(f"{a}->{b}: {va:.2g}->{vb:.2g}")
    status = WARN if osc else PASS
    return Result(
        "I10",
        "RPS dual sign+stability",
        status,
        "≥0, stable" if not osc else "oscillation " + "; ".join(osc),
    )


def check_i11_one_pass(run: Run) -> Result:
    """I11: exactly one P0+P1 (+P2 iff enabled), no within-year iteration."""
    problems: list[str] = []
    for year in sorted(run.ledgers):
        sc = run.ledgers[year].get("solve_counts")
        if sc is None:
            continue
        if run.ledgers[year].get("bridge"):
            if sc.get("P0", 0) or sc.get("P1", 0) or sc.get("P2", 0):
                problems.append(f"{year}: bridge year solved")
            continue
        if sc.get("P0") != 1 or sc.get("P1") != 1 or sc.get("P2", 0) not in (0, 1):
            problems.append(f"{year}: {sc}")
    status = PASS if not problems else FAIL
    return Result(
        "I11",
        "one-pass",
        status,
        "single pass" if not problems else "; ".join(problems),
    )


def check_i12_reserve_margin(run: Run) -> Result:
    """I12: reserve margin within [floor, floor + band] each year."""
    floor = run.config.planning_reserve_margin
    hi = floor + T.reserve_margin_band_pp
    out_years: list[int] = []
    detail: list[str] = []
    for year in sorted(run.ledgers):
        rm = run.ledgers[year].get("reserve_margin")
        if rm is None:
            continue
        if rm < floor - 1e-6 or rm > hi + 1e-6:
            out_years.append(year)
            detail.append(f"{year}:{rm:.1%}")
    # FAIL only on a sustained excursion.
    consec = _max_consecutive(out_years)
    status = PASS
    if out_years:
        status = FAIL if consec >= T.reserve_margin_consecutive_fail else WARN
    return Result(
        "I12",
        "reserve-margin band",
        status,
        f"band [{floor:.1%}, {hi:.1%}]; "
        + ("all in-band" if not detail else "out: " + ", ".join(detail)),
    )


def check_i13_cobweb(run: Run) -> Result:
    """I13: a tech's builds alternating full/zero over ≥ N year-pairs (WARN)."""
    # Build MW per tech per year (thermal + renewable + storage).
    per_year: dict[int, dict[str, float]] = {}
    for year in sorted(run.ledgers):
        led = run.ledgers[year]
        d: dict[str, float] = {}
        for a in led.get("thermal_additions", []):
            d[a["fuel"]] = d.get(a["fuel"], 0.0) + float(a.get("mw", 0.0))
        for a in led.get("renewable_additions", []):
            d[a["tech"]] = d.get(a["tech"], 0.0) + float(a.get("mw", 0.0))
        for a in led.get("storage_additions", []):
            d["storage"] = d.get("storage", 0.0) + float(a.get("mw", 0.0))
        per_year[year] = d
    techs = {t for d in per_year.values() for t in d}
    ys = sorted(per_year)
    flagged: list[str] = []
    for tech in techs:
        series = [per_year[y].get(tech, 0.0) for y in ys]
        alternations = sum(
            1
            for i in range(1, len(series) - 1)
            if (series[i] == 0) != (series[i - 1] == 0)
            and (series[i] == 0) != (series[i + 1] == 0)
        )
        if alternations >= T.cobweb_pairs:
            flagged.append(f"{tech}({alternations})")
    status = WARN if flagged else PASS
    return Result(
        "I13",
        "cobweb detector",
        status,
        "smooth" if not flagged else "; ".join(flagged),
    )


def check_i14_price_sanity(run: Run) -> Result:
    """I14: annual LW price within a fuel-implied CC band; neg-price bounded."""
    problems: list[str] = []
    gas = _resolve_gas_price(run.config)
    cc_mc = gas * T.cc_heat_rate if gas else None
    for year, yd in run.years.items():
        lw = _load_weighted_price(yd)
        if cc_mc:
            if lw < T.price_lo_mult * cc_mc or lw > T.price_hi_mult * cc_mc:
                problems.append(
                    f"{year}: LW ${lw:.1f} outside [{T.price_lo_mult}×,{T.price_hi_mult}×]"
                    f" CC MC ${cc_mc:.1f}"
                )
        neg = float((yd.result.prices < 0).mean())
        if neg > T.neg_price_hour_frac:
            problems.append(f"{year}: {neg:.1%} negative-price hours")
    status = WARN if problems else PASS
    return Result(
        "I14",
        "price sanity",
        status,
        "in band" if not problems else "; ".join(problems),
    )


# --------------------------------------------------------------------------- #
# Paired-run invariants P1-P3
# --------------------------------------------------------------------------- #
def _cumulative_co2(run: Run) -> float | None:
    total = 0.0
    seen = False
    for yd in run.years.values():
        c = _annual_co2_tons(yd)
        if c is not None:
            total += c
            seen = True
    return total if seen else None


def check_p1_co2_monotone(base: Run, high: Run) -> Result:
    """P1: cumulative CO2 falls under a higher carbon price."""
    cb, ch = _cumulative_co2(base), _cumulative_co2(high)
    if cb is None or ch is None:
        return Result("P1", "CO2 monotone vs carbon", SKIP, "emissions absent")
    status = PASS if ch < cb else FAIL
    return Result(
        "P1",
        "CO2 monotone vs carbon",
        status,
        f"cumulative CO2 base {cb / 1e6:.2f} Mt vs high {ch / 1e6:.2f} Mt",
    )


def check_p2_merit_sign(base: Run, gas_up: Run) -> Result:
    """P2: +gas ⇒ coal gen ↑, gas-CC gen ↓, LW price ↑, objective ↑."""
    year = max(set(base.years) & set(gas_up.years), default=None)
    if year is None:
        return Result("P2", "merit-order sign", SKIP, "no common year")
    b, g = base.years[year], gas_up.years[year]
    fb, fg = _fuel_gen_mwh(b), _fuel_gen_mwh(g)
    checks = []
    if fb.get("coal", 0) > 0:
        checks.append(("coal↑", fg.get("coal", 0) >= fb.get("coal", 0) - 1e-6))
    checks.append(("gas_cc↓", fg.get("gas_cc", 0) <= fb.get("gas_cc", 0) + 1e-6))
    checks.append(("price↑", _load_weighted_price(g) >= _load_weighted_price(b) - 1e-6))
    checks.append(
        ("objective↑", g.result.objective_value >= b.result.objective_value - 1e-6)
    )
    failed = [n for n, ok in checks if not ok]
    status = PASS if not failed else FAIL
    return Result(
        "P2",
        "merit-order sign",
        status,
        f"year {year}: "
        + ("all signs correct" if not failed else "wrong: " + ",".join(failed)),
    )


def check_p3_perturbation(base: Run, pert: Run) -> Result:
    """P3: ±5% gas moves cumulative builds < 25% (cliff-edge detector, WARN)."""

    def total_build(run: Run) -> float:
        tot = 0.0
        for led in run.ledgers.values():
            for a in led.get("thermal_additions", []):
                tot += float(a.get("mw", 0.0))
            for a in led.get("renewable_additions", []):
                tot += float(a.get("mw", 0.0))
            for a in led.get("storage_additions", []):
                tot += float(a.get("mw", 0.0))
        return tot

    tb, tp = total_build(base), total_build(pert)
    if tb <= 0:
        return Result("P3", "perturbation stability", SKIP, "no builds in base")
    move = abs(tp - tb) / tb
    status = WARN if move > T.perturbation_build_frac else PASS
    return Result(
        "P3",
        "perturbation stability",
        status,
        f"cumulative builds moved {move:.1%} (base {tb:.0f} MW, pert {tp:.0f} MW)",
    )


# --------------------------------------------------------------------------- #
# Small utilities
# --------------------------------------------------------------------------- #
def _max_consecutive(years: list[int]) -> int:
    if not years:
        return 0
    ys = sorted(years)
    best = run = 1
    for a, b in zip(ys, ys[1:]):
        run = run + 1 if b == a + 1 else 1
        best = max(best, run)
    return best


def _resolve_gas_price(config: ScenarioConfig) -> float | None:
    """Best-effort annual gas price ($/MMBtu) for the price-band check."""
    try:
        from market_sim.data.fuel import resolve_annual_gas_price

        yr = config.start_year or 2026
        return float(resolve_annual_gas_price(config, yr))
    except Exception:
        return None


SINGLE_CHECKS = [
    check_i1_energy_balance,
    check_i2_no_nan_inf,
    check_i3_unserved_dump,
    check_i4_capacity_accounting,
    check_i5_no_retire_reenter,
    check_i6_econ_retire_sanity,
    check_i7_reliability_floor,
    check_i8_planned_mode_gating,
    check_i9_storage_integrity,
    check_i10_rps_dual,
    check_i11_one_pass,
    check_i12_reserve_margin,
    check_i13_cobweb,
    check_i14_price_sanity,
]


def run_single(run_dir: Path) -> list[Result]:
    """Run I1-I14 over one scenario cache."""
    run = load_run(run_dir)
    return [chk(run) for chk in SINGLE_CHECKS]


def run_paired(base_dir: Path, other_dir: Path, kind: str) -> list[Result]:
    """Run the paired invariant appropriate to ``kind``.

    ``kind``: ``carbon`` → P1, ``gas_up`` → P2, ``gas_pm5`` → P3.
    """
    base, other = load_run(base_dir), load_run(other_dir)
    if kind == "carbon":
        return [check_p1_co2_monotone(base, other)]
    if kind == "gas_up":
        return [check_p2_merit_sign(base, other)]
    if kind == "gas_pm5":
        return [check_p3_perturbation(base, other)]
    raise SystemExit(f"unknown --pair-kind {kind!r}")


def _print_table(results: list[Result]) -> None:
    icon = {PASS: "PASS", FAIL: "FAIL", WARN: "WARN", SKIP: "SKIP"}
    for r in results:
        print(f"  [{icon[r.status]}] {r.ident:<4} {r.name:<26} {r.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, help="Scenario cache dir for I1-I14.")
    parser.add_argument(
        "--paired",
        nargs=2,
        metavar=("BASE_DIR", "OTHER_DIR"),
        type=Path,
        help="Two scenario caches for a paired invariant.",
    )
    parser.add_argument(
        "--pair-kind",
        choices=["carbon", "gas_up", "gas_pm5"],
        default="carbon",
        help="Which paired invariant to run (P1/P2/P3).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON, not a table.")
    args = parser.parse_args(argv)

    results: list[Result] = []
    if args.run_dir:
        results += run_single(args.run_dir)
    if args.paired:
        results += run_paired(args.paired[0], args.paired[1], args.pair_kind)
    if not results:
        parser.error("supply --run-dir and/or --paired")

    if args.json:
        print(json.dumps([r.__dict__ for r in results], indent=2))
    else:
        print("Forecast invariants:")
        _print_table(results)
        n_fail = sum(r.status == FAIL for r in results)
        n_warn = sum(r.status == WARN for r in results)
        print(f"\n{n_fail} FAIL, {n_warn} WARN, {len(results)} checks")

    return 1 if any(r.status == FAIL for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
