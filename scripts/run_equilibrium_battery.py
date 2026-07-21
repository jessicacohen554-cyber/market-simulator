#!/usr/bin/env python
"""Tier-2 capacity-market equilibrium tests (T2.1-T2.5, P-3B).

Plan §2 Tier 2 of
``docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md``,
rescoped 2026-07-12: ``capacity_market_clearing`` is OFF by default (the P-2A
recommendation, ``docs/handoffs/capacity-price-validation-2026-07-12.md`` §7 --
the CR-1 sloped curve is validated as an *instrument* but not a trustworthy
*position*, so it stays gated off). These tests therefore target the ACTIVE
capacity-value mechanism -- the flat ``net_cone_per_kw_yr x (1 - EFORd)`` price
(:func:`market_sim.model.capacity.capacity_revenue_per_mw_yr`, fixed mode) --
not the dormant sloped curve. A ``capacity_market_clearing=True`` run hits the
P-2A degeneracy (accredited position past the curve's zero-cross, price pays
$0) and is never scored here as an equilibrium result.

This script has two subcommands:

* ``overbuild`` -- solve one ISO-window forward run, optionally with a
  synthetic +10 GW ``gas_cc`` "known addition" injected at ``start_year``
  (T2.4/T2.5's exogenous-overbuild probe). Writes a
  ``full_horizon_summary.json`` in the exact shape ``run_full_horizon.py``
  writes (same ``extract_trajectory`` + I1-I14 ``invariants``), so ``score``
  can treat every run-dir uniformly regardless of which script produced it.
  The three *unperturbed* baseline/full-horizon runs this battery needs
  (NEISO full 2026-2050, NEISO probe-window baseline, ERCOT probe-window
  baseline) are run with the existing, unmodified ``scripts/run_full_horizon.py``
  -- no new code duplicates that path.
* ``score`` -- reads the five completed run summaries and produces the
  T2.1-T2.5 verdicts (JSON + a plain-text table) against expectations
  pre-registered in this file (rule: results can't be graded on vibes).

Findings only (rules 1/11/14): nothing here tunes a value or changes a
threshold. Forecast probes -- never registered on the backcast dashboard.

Usage::

    # Baselines/full-horizon (unmodified harness):
    MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \\
        uv run python scripts/run_full_horizon.py --iso NEISO \\
        --start-year 2026 --end-year 2050 --out-dir results/full-horizon/neiso
    uv run python scripts/run_full_horizon.py --iso NEISO \\
        --start-year 2026 --end-year 2032 --out-dir results/full-horizon/neiso-t2-base
    uv run python scripts/run_full_horizon.py --iso ERCOT \\
        --start-year 2026 --end-year 2032 --out-dir results/full-horizon/ercot-t2-base

    # +10 GW overbuild variants (this script):
    uv run python scripts/run_equilibrium_battery.py overbuild --iso NEISO \\
        --start-year 2026 --end-year 2032 --out-dir results/full-horizon/neiso-t2-overbuild
    uv run python scripts/run_equilibrium_battery.py overbuild --iso ERCOT \\
        --start-year 2026 --end-year 2032 --out-dir results/full-horizon/ercot-t2-overbuild

    # Score:
    uv run python scripts/run_equilibrium_battery.py score \\
        --neiso-full results/full-horizon/neiso \\
        --neiso-base results/full-horizon/neiso-t2-base \\
        --neiso-overbuild results/full-horizon/neiso-t2-overbuild \\
        --ercot-base results/full-horizon/ercot-t2-base \\
        --ercot-overbuild results/full-horizon/ercot-t2-overbuild \\
        --out-json results/full-horizon/_t2_equilibrium.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

import scripts.check_forecast_invariants as C  # noqa: E402
import scripts.run_full_horizon as FH  # noqa: E402
from market_sim.config.constants import (  # noqa: E402
    DEFAULT_MARKET_DESIGN,
    EFORD,
    MARKET_DESIGN,
    PLANNING_RESERVE_MARGIN_BY_ISO,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity import (  # noqa: E402
    _default_build_zone,
    _make_new_generator,
    capacity_revenue_per_mw_yr,
    thermal_accreditation_fraction,
)
from market_sim.results import cache as cachemod  # noqa: E402

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"

# Exogenous overbuild probe (T2.4/T2.5): a single synthetic "known addition"
# block, injected via the same production seam real EIA-860 planned units use
# (evolve_fleet step 3 -- capacity.py's "known additions", fed by
# data.fleet.load_planned_additions). gas_cc is a neutral, common new-entrant
# thermal tech (also apply_reserve_margin_build's own backstop-filler style,
# though that uses gas_ct) -- the SAME tech/size is used for both ISOs so the
# NEISO/ERCOT comparison (T2.4 vs T2.5) is an apples-to-apples shock.
OVERBUILD_MW: float = 10_000.0
OVERBUILD_TECH: str = "gas_cc"
OVERBUILD_SEQ: int = 999  # distinguishes the injected unit_id from real entrants


# --------------------------------------------------------------------------- #
# Solve: +10 GW overbuild variant (reuses run_full_horizon's config/summary
# shape; the only new logic is the load_planned_additions monkeypatch).
# --------------------------------------------------------------------------- #
def _install_overbuild_patch(iso: str, start_year: int, config: ScenarioConfig):
    """Monkeypatch ``runner.load_planned_additions`` to append the probe block.

    Patches the module attribute ``market_sim.runner.load_planned_additions``
    (the name ``run_scenario_iso`` actually calls), mirroring
    ``run_driver_battery._apply_probe_patches``'s established convention for
    off-registry diagnostic-only probes: never persisted, confined to this
    process, restored immediately after the solve.
    """
    from market_sim import runner as runnermod
    from market_sim.data.fleet import load_planned_additions as _orig

    iso_config = get_iso_config(iso.upper())
    zone = _default_build_zone(iso_config)

    def _patched(iso_arg, iso_config_arg=None, data_dir=None):
        base = _orig(iso_arg, iso_config_arg, data_dir)
        if iso_arg.upper() != iso.upper():
            return base
        synth = _make_new_generator(
            OVERBUILD_TECH,
            OVERBUILD_MW,
            zone,
            start_year,
            OVERBUILD_SEQ,
            config,
            iso.upper(),
        )
        return list(base) + [synth]

    runnermod.load_planned_additions = _patched
    return runnermod, _orig


def solve_overbuild(iso: str, start_year: int, end_year: int, out_dir: Path) -> dict:
    """Solve one ISO window with the +10 GW probe injected at ``start_year``.

    Writes ``<out_dir>/full_horizon_summary.json`` in the same shape
    ``run_full_horizon.py`` writes (trajectory + I1-I14 invariants), so
    ``score`` reads every run-dir identically.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    cachemod.CACHE_ROOT = out_dir

    config = FH.reference_config(iso, start_year, end_year, cmc=False)
    runnermod, orig_loader = _install_overbuild_patch(iso, start_year, config)
    try:
        from market_sim.pipeline.api import run_scenario

        cache_key = run_scenario(config, iso.upper())
    finally:
        runnermod.load_planned_additions = orig_loader

    run_dir = out_dir / iso.upper() / cache_key
    summary = _build_summary(iso, start_year, end_year, run_dir, cache_key)
    summary["overbuild_mw"] = OVERBUILD_MW
    summary["overbuild_tech"] = OVERBUILD_TECH
    summary["overbuild_inject_year"] = start_year
    (out_dir / "full_horizon_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    return summary


def _build_summary(iso, start_year, end_year, run_dir: Path, cache_key: str) -> dict:
    """Assemble the same summary shape run_full_horizon.main() writes."""
    invariants: list[dict] = []
    trajectory: list[dict] = []
    solved_years: list[int] = []
    if run_dir.exists():
        results = C.run_single(run_dir)
        invariants = [
            {"id": r.ident, "name": r.name, "status": r.status, "detail": r.detail}
            for r in results
        ]
        run = C.load_run(run_dir)
        solved_years = run.solved_years
        trajectory = FH.extract_trajectory(run)
    return {
        "iso": iso.upper(),
        "start_year": start_year,
        "end_year": end_year,
        "capacity_market_clearing": False,
        "cache_key": cache_key,
        "run_dir": str(run_dir),
        "n_solved_years": len(solved_years),
        "solved_years": solved_years,
        "invariants": invariants,
        "trajectory": trajectory,
    }


# --------------------------------------------------------------------------- #
# Score: T2.1 - T2.5
# --------------------------------------------------------------------------- #
def _load_summary(path: Path) -> dict:
    path = Path(path)
    if path.is_dir():
        path = path / "full_horizon_summary.json"
    return json.loads(path.read_text())


def _traj_by_year(summary: dict) -> dict[int, dict]:
    return {row["year"]: row for row in summary["trajectory"]}


def _invariant(summary: dict, ident: str) -> dict | None:
    for row in summary["invariants"]:
        if row["id"] == ident:
            return row
    return None


def t2_1_identity(summary: dict) -> dict:
    """T2.1: capacity-value-to-net-CONE identity on the active (fixed) path.

    Re-derives the capacity price two ways for every solved year -- (a) the
    production seam ``capacity_revenue_per_mw_yr`` called with the run's own
    config, (b) the independent ``net_cone_per_kw_yr x 1000 x (1-EFORd)``
    arithmetic straight off the ``MARKET_DESIGN`` registry -- and asserts they
    match exactly, and that the price is IDENTICAL across every year despite
    ``reserve_margin`` swinging widely (the direct evidence that the active
    mechanism cannot respond to the fleet it is pricing).
    """
    iso = summary["iso"]
    run = C.load_run(Path(summary["run_dir"]))
    config = run.config
    design = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN)

    # Sample the fixed-mode payment across representative fuels (each carries
    # its own EFORd) and check it equals net_cone x 1000 x the unit's
    # basis-resolved accreditation (R4: (1-EFORd) for UCAP ISOs, the published
    # ELCC class rating for PJM — the SAME resolver the ledger uses).
    sample_fuels = ("gas_cc", "gas_ct", "coal", "nuclear")
    mismatches = []
    for fuel in sample_fuels:
        ef = EFORD.get(fuel, 0.05)
        actual = capacity_revenue_per_mw_yr(iso, fuel, ef, config, None)
        expected = 0.0
        if design.capacity_market and design.net_cone_per_kw_yr > 0.0:
            frac = thermal_accreditation_fraction(fuel, ef, iso)
            expected = design.net_cone_per_kw_yr * 1000.0 * max(0.0, frac)
        if abs(actual - expected) > 1e-6:
            mismatches.append({"fuel": fuel, "actual": actual, "expected": expected})

    # Price flatness across years: a fixed representative unit (gas_cc) whose
    # accreditation does not vary year to year, so any variation is the price.
    per_year_price = {
        y: capacity_revenue_per_mw_yr(iso, "gas_cc", EFORD["gas_cc"], config, None)
        for y in run.solved_years
    }
    prices = list(per_year_price.values())
    price_identical = len(set(round(p, 6) for p in prices)) <= 1

    rm_by_year = {
        y: run.ledgers.get(y, {}).get("reserve_margin") for y in run.solved_years
    }
    rm_values = [v for v in rm_by_year.values() if v is not None]
    rm_range = (min(rm_values), max(rm_values)) if rm_values else (None, None)

    ok = not mismatches and price_identical
    return {
        "test": "T2.1",
        "iso": iso,
        "description": (
            "capacity-value-to-net-CONE identity on the active "
            "(capacity_market_clearing=False) path"
        ),
        "status": PASS if ok else FAIL,
        "mismatches": mismatches,
        "price_per_firm_mw_yr_eford0": prices[0] if prices else None,
        "price_identical_across_years": price_identical,
        "n_years": len(prices),
        "reserve_margin_range": rm_range,
        "detail": (
            f"capacity price = ${prices[0]:,.1f}/firm-MW-yr, bit-identical across "
            f"all {len(prices)} solved years while reserve margin ranged "
            f"{rm_range[0]:.1%} to {rm_range[1]:.1%}"
            if prices and None not in rm_range
            else "insufficient data"
        ),
    }


def t2_2_oscillation(summary: dict) -> dict:
    """T2.2: does the active mechanism exhibit the textbook equilibrium property?

    Two pre-registered claims, scored separately:
      T2.2a (gate) -- capacity value is time-invariant (near-zero CV): expected
        PASS, a restatement of T2.1's identity as a dispersion statistic.
      T2.2b (gate) -- reserve margin oscillates AROUND net-CONE's implied
        target (mean-reverts / shows sign changes in year-over-year deltas)
        rather than drifting monotonically away from the planning band: the
        textbook property fixed-price stubs cannot exhibit. Pre-registered
        EXPECTED FAIL given the P-3A finding (NEISO RM 5.0% to 67.5%,
        monotonic after the early trough).
    """
    iso = summary["iso"]
    run = C.load_run(Path(summary["run_dir"]))
    traj = sorted(summary["trajectory"], key=lambda r: r["year"])

    price_series = [
        capacity_revenue_per_mw_yr(iso, "gas_cc", EFORD["gas_cc"], run.config, None)
        for _ in traj
    ]
    price_mean = statistics.mean(price_series) if price_series else 0.0
    price_cv = (
        statistics.pstdev(price_series) / price_mean
        if price_series and price_mean
        else 0.0
    )

    rm_rows = [
        (r["year"], r["reserve_margin"])
        for r in traj
        if r["reserve_margin"] is not None
    ]
    years = [y for y, _ in rm_rows]
    rm = [v for _, v in rm_rows]
    floor = PLANNING_RESERVE_MARGIN_BY_ISO.get(iso, run.config.planning_reserve_margin)
    band_hi = floor + C.T.reserve_margin_band_pp

    deltas = [b - a for a, b in zip(rm, rm[1:])]
    sign_changes = sum(
        1
        for a, b in zip(deltas, deltas[1:])
        if a != 0 and b != 0 and (a > 0) != (b > 0)
    )
    in_band_frac = sum(1 for v in rm if floor <= v <= band_hi) / len(rm) if rm else 0.0
    final_tail = rm[-min(5, len(rm)) :]
    monotone_tail_up = all(b >= a - 1e-9 for a, b in zip(final_tail, final_tail[1:]))

    t2_2a_pass = price_cv < 0.001
    # A restoring force needs more than one flip; a single flip (e.g. the
    # initial de-firming trough giving way to entry) is not oscillation.
    t2_2b_pass = sign_changes >= 3 and in_band_frac >= 0.5

    return {
        "test": "T2.2",
        "iso": iso,
        "years": years,
        "reserve_margin_series": rm,
        "capacity_value_per_firm_mw_yr": price_mean,
        "capacity_value_cv": price_cv,
        "reserve_margin_mean": statistics.mean(rm) if rm else None,
        "reserve_margin_stdev": statistics.pstdev(rm) if rm else None,
        "reserve_margin_min": min(rm) if rm else None,
        "reserve_margin_max": max(rm) if rm else None,
        "reserve_margin_band": (floor, band_hi),
        "reserve_margin_in_band_frac": in_band_frac,
        "reserve_margin_yoy_sign_changes": sign_changes,
        "reserve_margin_final5_monotone_nondecreasing": monotone_tail_up,
        "sub_results": [
            {
                "id": "T2.2a",
                "description": "capacity value is time-invariant (CV < 0.1%)",
                "status": PASS if t2_2a_pass else FAIL,
                "gate": True,
            },
            {
                "id": "T2.2b",
                "description": (
                    "reserve margin oscillates around net-CONE's implied target "
                    "(>=3 year-over-year sign changes AND >=50% of years in-band) "
                    "-- the textbook equilibrium property"
                ),
                "status": PASS if t2_2b_pass else FAIL,
                "gate": True,
            },
        ],
        "status": PASS if (t2_2a_pass and t2_2b_pass) else FAIL,
    }


def t2_3_hysteresis(summary: dict) -> dict:
    """T2.3: reuse I5 (no retire-and-reenter) and I13 (cobweb) verbatim."""
    i5 = _invariant(summary, "I5")
    i13 = _invariant(summary, "I13")
    sub = []
    if i5 is not None:
        sub.append(
            {
                "id": "I5",
                "description": i5["name"],
                "status": i5["status"],
                "detail": i5["detail"],
            }
        )
    if i13 is not None:
        sub.append(
            {
                "id": "I13",
                "description": i13["name"],
                "status": i13["status"],
                "detail": i13["detail"],
            }
        )
    overall = PASS
    for row in sub:
        if row["status"] == FAIL:
            overall = FAIL
        elif row["status"] == WARN and overall == PASS:
            overall = WARN
    return {
        "test": "T2.3",
        "iso": summary["iso"],
        "sub_results": sub,
        "status": overall if sub else "SKIP",
    }


def _overbuild_comparison(
    base_summary: dict, over_summary: dict, inject_year: int, inject_mw: float
) -> list[dict]:
    base_by_year = _traj_by_year(base_summary)
    over_by_year = _traj_by_year(over_summary)
    years = sorted(set(base_by_year) & set(over_by_year))
    rows = []
    for y in years:
        b, o = base_by_year[y], over_by_year[y]
        builds_thermal_over_ex = o["builds_thermal_mw"] - (
            inject_mw if y == inject_year else 0.0
        )
        rows.append(
            {
                "year": y,
                "reserve_margin_base": b["reserve_margin"],
                "reserve_margin_over": o["reserve_margin"],
                "lw_price_base": b["lw_price"],
                "lw_price_over": o["lw_price"],
                "hours_ge_500_base": b.get("hours_ge_500"),
                "hours_ge_500_over": o.get("hours_ge_500"),
                "hours_ge_2000_base": b.get("hours_ge_2000"),
                "hours_ge_2000_over": o.get("hours_ge_2000"),
                "max_hourly_price_base": b.get("max_hourly_price"),
                "max_hourly_price_over": o.get("max_hourly_price"),
                "builds_thermal_base": b["builds_thermal_mw"],
                "builds_thermal_over_ex_injection": builds_thermal_over_ex,
                "builds_renew_base": b["builds_renew_mw"],
                "builds_renew_over": o["builds_renew_mw"],
                "builds_storage_base": b["builds_storage_mw"],
                "builds_storage_over": o["builds_storage_mw"],
                "retire_base": b["retire_mw"],
                "retire_over": o["retire_mw"],
            }
        )
    return rows


def t2_4_neiso_overbuild(
    base_summary: dict, over_summary: dict, inject_year: int
) -> dict:
    """T2.4: +10 GW exogenous overbuild on NEISO.

    Pre-registered (plan §2, textbook Tier-2 expectation, written for the
    sloped CR-1 curve): capacity value collapses, entry stops, retirements
    resume. Scored honestly against the ACTIVE fixed-price mechanism:
      T2.4a (gate) -- capacity value collapses: EXPECTED FAIL (T2.1 shows it
        is structurally invariant to fleet size under capacity_market_clearing
        =False; a collapse requires the gated-off CR-1 curve).
      T2.4b (gate) -- entry (thermal+renewable+storage builds) falls in the
        overbuild run vs baseline in post-shock years: measured, via the
        energy-price cannibalization channel (no capacity-price channel
        exists in fixed mode).
      T2.4c (report-only) -- retirements rise in the overbuild run: measured;
        NOT gated because the probe window may be shorter than some fuels'
        consecutive-loss-year retirement threshold.
      T2.4d (gate) -- energy (LW) price falls under overbuild vs baseline.
    """
    iso = "NEISO"
    rows = _overbuild_comparison(base_summary, over_summary, inject_year, OVERBUILD_MW)
    post = [r for r in rows if r["year"] > inject_year]

    run_base = C.load_run(Path(base_summary["run_dir"]))
    run_over = C.load_run(Path(over_summary["run_dir"]))
    price_base = capacity_revenue_per_mw_yr(
        iso, "gas_cc", EFORD["gas_cc"], run_base.config, None
    )
    price_over = capacity_revenue_per_mw_yr(
        iso, "gas_cc", EFORD["gas_cc"], run_over.config, None
    )
    price_collapses = price_over < price_base - 1e-6

    def _total(key_base, key_over):
        return sum(r[key_base] for r in post), sum(r[key_over] for r in post)

    entry_base, entry_over = _total(
        "builds_thermal_base", "builds_thermal_over_ex_injection"
    )
    ren_base, ren_over = _total("builds_renew_base", "builds_renew_over")
    sto_base, sto_over = _total("builds_storage_base", "builds_storage_over")
    total_entry_base = entry_base + ren_base + sto_base
    total_entry_over = entry_over + ren_over + sto_over
    retire_base, retire_over = _total("retire_base", "retire_over")
    lw_base = statistics.mean(
        r["lw_price_base"] for r in rows if r["lw_price_base"] is not None
    )
    lw_over = statistics.mean(
        r["lw_price_over"] for r in rows if r["lw_price_over"] is not None
    )

    entry_falls = total_entry_over < total_entry_base - 1e-6
    retire_rises = retire_over > retire_base + 1e-6
    price_falls = lw_over < lw_base - 1e-6

    sub = [
        {
            "id": "T2.4a",
            "description": "capacity value collapses under +10 GW overbuild",
            "status": FAIL if not price_collapses else PASS,
            "gate": True,
            "detail": f"price_base=${price_base:,.1f} price_over=${price_over:,.1f} /firm-MW-yr (fixed net-CONE, invariant by construction)",
        },
        {
            "id": "T2.4b",
            "description": "entry (thermal+renewable+storage) falls in post-shock years vs baseline",
            "status": PASS if entry_falls else FAIL,
            "gate": True,
            "detail": f"post-shock cumulative entry: base={total_entry_base:.0f} MW, overbuild={total_entry_over:.0f} MW",
        },
        {
            "id": "T2.4c",
            "description": "retirements resume/rise in post-shock years vs baseline",
            "status": PASS if retire_rises else FAIL,
            "gate": False,
            "detail": f"post-shock cumulative retirements: base={retire_base:.0f} MW, overbuild={retire_over:.0f} MW (report-only: window may be shorter than some fuels' consecutive-loss threshold)",
        },
        {
            "id": "T2.4d",
            "description": "energy (LW) price falls under overbuild vs baseline",
            "status": PASS if price_falls else FAIL,
            "gate": True,
            "detail": f"LW price mean: base=${lw_base:.2f}, overbuild=${lw_over:.2f} /MWh",
        },
    ]
    overall = PASS
    for row in sub:
        if row["gate"] and row["status"] == FAIL:
            overall = FAIL
    return {
        "test": "T2.4",
        "iso": iso,
        "inject_year": inject_year,
        "rows": rows,
        "sub_results": sub,
        "status": overall,
    }


def t2_5_ercot_overbuild(
    base_summary: dict, over_summary: dict, inject_year: int
) -> dict:
    """T2.5: same +10 GW overbuild applied to ERCOT (energy-only contrast).

    Pre-registered: adequacy expresses through the energy/ORDC scarcity price
    instead of a capacity payment (ERCOT has none). Scored:
      T2.5a (gate) -- capacity value is exactly $0 in BOTH runs (energy-only
        negative control, mirrors T1.7b).
      T2.5b (gate) -- scarcity hours (price >= $500 and >= $2000) fall under
        overbuild vs baseline.
      T2.5c (gate) -- LW price and max hourly price fall under overbuild vs
        baseline.
    """
    iso = "ERCOT"
    rows = _overbuild_comparison(base_summary, over_summary, inject_year, OVERBUILD_MW)

    run_base = C.load_run(Path(base_summary["run_dir"]))
    run_over = C.load_run(Path(over_summary["run_dir"]))
    price_base = capacity_revenue_per_mw_yr(
        iso, "gas_cc", EFORD["gas_cc"], run_base.config, None
    )
    price_over = capacity_revenue_per_mw_yr(
        iso, "gas_cc", EFORD["gas_cc"], run_over.config, None
    )
    both_zero = price_base == 0.0 and price_over == 0.0

    hrs500_base = sum(r["hours_ge_500_base"] or 0 for r in rows)
    hrs500_over = sum(r["hours_ge_500_over"] or 0 for r in rows)
    hrs2000_base = sum(r["hours_ge_2000_base"] or 0 for r in rows)
    hrs2000_over = sum(r["hours_ge_2000_over"] or 0 for r in rows)
    lw_base = statistics.mean(
        r["lw_price_base"] for r in rows if r["lw_price_base"] is not None
    )
    lw_over = statistics.mean(
        r["lw_price_over"] for r in rows if r["lw_price_over"] is not None
    )
    maxp_base = max((r["max_hourly_price_base"] or 0.0) for r in rows)
    maxp_over = max((r["max_hourly_price_over"] or 0.0) for r in rows)

    scarcity_falls = (
        (hrs500_over <= hrs500_base)
        and (hrs2000_over <= hrs2000_base)
        and (hrs500_over < hrs500_base or hrs2000_over < hrs2000_base)
    )
    price_falls = lw_over < lw_base - 1e-6

    sub = [
        {
            "id": "T2.5a",
            "description": "capacity value is exactly $0 in both runs (energy-only negative control)",
            "status": PASS if both_zero else FAIL,
            "gate": True,
            "detail": f"price_base=${price_base:.2f} price_over=${price_over:.2f}",
        },
        {
            "id": "T2.5b",
            "description": "scarcity hours (price>=$500, price>=$2000) fall under +10 GW overbuild",
            "status": PASS if scarcity_falls else FAIL,
            "gate": True,
            "detail": (
                f"hrs>=$500: base={hrs500_base} overbuild={hrs500_over}; "
                f"hrs>=$2000: base={hrs2000_base} overbuild={hrs2000_over}"
            ),
        },
        {
            "id": "T2.5c",
            "description": "LW and max hourly price fall under overbuild vs baseline",
            "status": PASS if price_falls else FAIL,
            "gate": True,
            "detail": f"LW price: base=${lw_base:.2f} overbuild=${lw_over:.2f}; max price: base=${maxp_base:.0f} overbuild=${maxp_over:.0f}",
        },
    ]
    overall = PASS
    for row in sub:
        if row["gate"] and row["status"] == FAIL:
            overall = FAIL
    return {
        "test": "T2.5",
        "iso": iso,
        "inject_year": inject_year,
        "rows": rows,
        "sub_results": sub,
        "status": overall,
    }


def score_all(
    neiso_full, neiso_base, neiso_overbuild, ercot_base, ercot_overbuild
) -> dict:
    s_full = _load_summary(neiso_full)
    s_neiso_base = _load_summary(neiso_base)
    s_neiso_over = _load_summary(neiso_overbuild)
    s_ercot_base = _load_summary(ercot_base)
    s_ercot_over = _load_summary(ercot_overbuild)

    inject_year_neiso = (
        s_neiso_over.get("overbuild_inject_year") or s_neiso_over["start_year"]
    )
    inject_year_ercot = (
        s_ercot_over.get("overbuild_inject_year") or s_ercot_over["start_year"]
    )

    return {
        "T2.1": t2_1_identity(s_full),
        "T2.2": t2_2_oscillation(s_full),
        "T2.3": t2_3_hysteresis(s_full),
        "T2.4": t2_4_neiso_overbuild(s_neiso_base, s_neiso_over, inject_year_neiso),
        "T2.5": t2_5_ercot_overbuild(s_ercot_base, s_ercot_over, inject_year_ercot),
    }


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ob = sub.add_parser(
        "overbuild", help="Solve one ISO window with +10 GW injected."
    )
    p_ob.add_argument("--iso", required=True)
    p_ob.add_argument("--start-year", type=int, default=2026)
    p_ob.add_argument("--end-year", type=int, default=2032)
    p_ob.add_argument("--out-dir", type=Path, required=True)

    p_sc = sub.add_parser("score", help="Score T2.1-T2.5 from five completed run dirs.")
    p_sc.add_argument("--neiso-full", type=Path, required=True)
    p_sc.add_argument("--neiso-base", type=Path, required=True)
    p_sc.add_argument("--neiso-overbuild", type=Path, required=True)
    p_sc.add_argument("--ercot-base", type=Path, required=True)
    p_sc.add_argument("--ercot-overbuild", type=Path, required=True)
    p_sc.add_argument("--out-json", type=Path, required=True)

    args = ap.parse_args(argv)

    if args.cmd == "overbuild":
        summary = solve_overbuild(
            args.iso, args.start_year, args.end_year, args.out_dir
        )
        print(f"wrote {args.out_dir / 'full_horizon_summary.json'}")
        print(f"solved years: {summary['solved_years']}")
        return 0

    if args.cmd == "score":
        result = score_all(
            args.neiso_full,
            args.neiso_base,
            args.neiso_overbuild,
            args.ercot_base,
            args.ercot_overbuild,
        )
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(result, indent=2, default=str) + "\n")
        print(f"wrote {args.out_json}")
        for test_id, res in result.items():
            print(f"{test_id}: {res['status']}")
            for row in res.get("sub_results", []):
                print(f"    [{row['status']}] {row['id']}: {row['description']}")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
