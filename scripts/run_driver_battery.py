"""Tier-1 single-driver directional & elasticity ladders (forecast probes).

Plan §2 Tier 1 of
``docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`` — the
measurement rig the rest of that program is graded on. It **generalizes** the
existing paired directional invariants P1-P3
(``scripts/check_forecast_invariants.py``, run weekly at best) into single-driver
**ladders**: each ladder holds every driver fixed except one, sweeps that one
driver across a pre-registered set of rungs, runs a full forward solve per rung
(capacity evolution + P0/P1 dispatch, sequential years — exactly as
``runner.run_scenario_iso`` does it), and scores each rung against expectations
that are **written down here, before the runs** (§2: "results can't be graded on
vibes"). A directional FAIL is a root-cause issue to open, never a threshold to
widen (rules 1/11/14).

The ladders (each carries its plan §2 test id):

* **T1.1** carbon ``{0,25,50,100}`` $/t — coal gen & CO2 monotone ↓; the coal→gas
  switch straddles the analytic SRMC crossover.
* **T1.2** adder/cap duality — a mass cap set to the emissions realized at
  ``carbon_price=25`` clears its allowance dual at ≈ $25; a slack cap → dual 0.
* **T1.3** gas ``{0.5,1.0,1.5}×`` — coal dispatch ↑ with gas, price ↑, merit sign.
* **T1.4** load low/mid/high (+ DC-vs-scalar peak/offpeak signature).
* **T1.5** IRA cliff — wind/solar entry economics discontinuous at the cliff year.
* **T1.6** RPS/ACP — REC dual ≤ ACP always, → 0 as VRE builds through the target.
* **T1.7** capacity-revenue net-CONE ``{0,1,2}×`` — thermal retirements ↓ / entry
  ↑ in net-CONE; ERCOT byte-identical (energy-only negative control).
* **T1.8** tech-cost low/mid/high — entry mix shifts toward the cheapened tech.
* **T1.9** storage-ELCC saturation — storage capacity value per MW ↓ as the fleet
  is seeded larger.

This is **measurement, not tuning**: nothing here changes a calibrated value or a
keeper, and these are forecast probes — they go in ``docs/handoffs/`` reports,
never on the backcast dashboard (plan §5 standing constraints). Config: ERCOT +
PJM, forecast 2026-2030, legacy heat-rate bins for runtime (the same documented
fidelity trade the tornado makes), sequential years, ≤2 concurrent invocations
(rule 12). Each rung is **check-before-run cached** (rule 7): its extracted
metrics are memoized to ``<out>/_battery_metrics/<iso>/<rung_id>.json`` and a
disposable solve cache under ``--cache-root``, so a re-invocation resumes rather
than re-solving.

Usage::

    # Full battery (this is P-1A, NOT P-0A — do not run in the build session):
    python scripts/run_driver_battery.py --iso ERCOT --start-year 2026 --end-year 2030

    # Harness smoke — one rung per ladder, one evolution year, to prove the rig:
    python scripts/run_driver_battery.py --iso ERCOT \
        --start-year 2026 --end-year 2026 --max-rungs 1 --tests T1.1 T1.3
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

logger = logging.getLogger("driver_battery")

# PASS/FAIL/WARN/SKIP verdicts, mirrored from check_forecast_invariants so the
# battery's ledger reads the same as the invariant suite it extends.
PASS, FAIL, WARN, SKIP = "PASS", "FAIL", "WARN", "SKIP"

# Thermal fuels whose year-over-year capacity drop is a retirement, and which
# capacity keys count as thermal — mirrors run_sensitivity_tornado.THERMAL_FUELS
# and results.export._summarize_year fuel keys.
THERMAL_FUELS: tuple[str, ...] = (
    "coal",
    "gas_cc",
    "gas_ct",
    "gas_st",
    "oil",
    "nuclear",
)


# --------------------------------------------------------------------------- #
# Expectation model — declarative, so every PASS/FAIL rule is a named primitive
# with its parameters in the table below, never a scattered literal.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Expectation:
    """One pre-registered PASS criterion for a ladder.

    Attributes:
        expr_id: Plan §2 sub-id (e.g. ``T1.1a``) for traceability.
        description: The claim being tested, in words.
        metric: Key into each rung's flat ``metrics`` dict (a per-rung scalar) —
            the series the ``rule`` is applied to across the ladder's rungs.
        rule: One of the primitives in :data:`_RULES`.
        gate: ``True`` → a violation is a FAIL (a real directional gate);
            ``False`` → report-only (WARN on violation), for the magnitude
            cross-checks the plan defers to a later round.
        tol: Absolute tolerance for the rule (units of ``metric``).
        target: Rule-specific reference value (e.g. the ACP ceiling, the carbon
            price a mass-cap dual should reproduce). Ignored by rules that don't
            use it.
    """

    expr_id: str
    description: str
    metric: str
    rule: str
    gate: bool = True
    tol: float = 1e-6
    target: float | None = None


# --- rule primitives: each takes (series, exp) -> (ok: bool, detail: str). --- #
def _series_from(rungs: list[dict], metric: str) -> list[tuple[str, float]]:
    """Pull ``(rung_label, value)`` pairs where ``metric`` is present + finite."""
    out: list[tuple[str, float]] = []
    for r in rungs:
        v = r.get("metrics", {}).get(metric)
        if v is None:
            continue
        try:
            fv = float(v)
        except (TypeError, ValueError):
            continue
        if fv != fv:  # NaN
            continue
        out.append((r["rung_label"], fv))
    return out


def _rule_monotone_down(series, exp):
    vals = [v for _, v in series]
    for lo, hi in zip(vals, vals[1:]):
        if hi > lo + exp.tol:
            return False, f"rose: {[round(v, 3) for v in vals]}"
    return True, f"↓ {[round(v, 3) for v in vals]}"


def _rule_monotone_up(series, exp):
    vals = [v for _, v in series]
    for lo, hi in zip(vals, vals[1:]):
        if hi < lo - exp.tol:
            return False, f"fell: {[round(v, 3) for v in vals]}"
    return True, f"↑ {[round(v, 3) for v in vals]}"


def _rule_le_target(series, exp):
    bad = [(lbl, v) for lbl, v in series if v > (exp.target or 0.0) + exp.tol]
    if bad:
        return False, f"exceeds {exp.target}: {bad}"
    return True, f"all ≤ {exp.target}"


def _rule_approx_target_first(series, exp):
    if not series:
        return None, "no data"
    lbl, v = series[0]
    ok = abs(v - (exp.target or 0.0)) <= exp.tol
    return ok, f"{lbl}={v:.3g} vs target {exp.target} (±{exp.tol})"


def _rule_approx_zero_last(series, exp):
    if not series:
        return None, "no data"
    lbl, v = series[-1]
    ok = abs(v) <= exp.tol
    return ok, f"{lbl}={v:.3g} (→0, ±{exp.tol})"


def _rule_all_equal(series, exp):
    vals = [v for _, v in series]
    if not vals:
        return None, "no data"
    spread = max(vals) - min(vals)
    ok = spread <= exp.tol
    return ok, f"spread {spread:.3g} over {[round(v, 3) for v in vals]}"


def _rule_strictly_changes(series, exp):
    """First rung differs from last by more than ``tol`` (the driver bites)."""
    if len(series) < 2:
        return None, "need ≥2 rungs"
    d = abs(series[-1][1] - series[0][1])
    ok = d > exp.tol
    return ok, f"|last-first|={d:.3g} (> {exp.tol})"


_RULES = {
    "monotone_down": _rule_monotone_down,
    "monotone_up": _rule_monotone_up,
    "le_target": _rule_le_target,
    "approx_target_first": _rule_approx_target_first,
    "approx_zero_last": _rule_approx_zero_last,
    "all_equal": _rule_all_equal,
    "strictly_changes": _rule_strictly_changes,
}


def evaluate_expectation(exp: Expectation, rungs: list[dict]) -> dict:
    """Score one expectation against the ladder's solved rungs.

    Returns a ledger row: ``{expr_id, description, metric, rule, status, detail}``.
    A rule that returns ``None`` (insufficient data — fewer rungs than the check
    needs, e.g. a monotonicity check on a one-rung smoke) yields ``SKIP``.
    """
    series = _series_from(rungs, exp.metric)
    fn = _RULES[exp.rule]
    # Monotonic/relational rules need ≥2 points; the primitives that only touch
    # one endpoint (approx_*) do not.
    # Rules whose meaning requires comparing ≥2 rungs. ``all_equal`` is here too:
    # a negative control ("identical across the ladder") is vacuous on one rung,
    # so it SKIPs rather than trivially PASSing.
    needs_two = exp.rule in {
        "monotone_down",
        "monotone_up",
        "strictly_changes",
        "all_equal",
    }
    if needs_two and len(series) < 2:
        return _row(exp, SKIP, f"insufficient rungs ({len(series)})")
    ok, detail = fn(series, exp)
    if ok is None:
        return _row(exp, SKIP, detail)
    if ok:
        status = PASS
    else:
        status = FAIL if exp.gate else WARN
    return _row(exp, status, detail)


def _row(exp: Expectation, status: str, detail: str) -> dict:
    return {
        "expr_id": exp.expr_id,
        "description": exp.description,
        "metric": exp.metric,
        "rule": exp.rule,
        "gate": exp.gate,
        "status": status,
        "detail": detail,
    }


# --------------------------------------------------------------------------- #
# Ladder registry — the pre-registered §2 Tier-1 table. Each rung's overrides
# are ScenarioConfig kwargs (first-class configs whose cache_key captures the
# perturbation — no off-registry channel, rule 24), except the two diagnostic
# scalars (``_net_cone_scalar`` for T1.7, ``_storage_seed_gw`` for T1.9) that
# have no ScenarioConfig field yet and are applied as clearly-labelled probe
# patches in the worker (documented at their use sites).
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Rung:
    """One point on a ladder."""

    label: str
    overrides: dict


@dataclass(frozen=True)
class Ladder:
    """A single-driver ladder and its pre-registered expectations."""

    test_id: str  # plan §2 id, e.g. "T1.1"
    driver: str  # human-readable driver name
    rungs: list[Rung]
    expectations: list[Expectation]
    isos: tuple[str, ...] = ("ERCOT", "PJM")
    note: str = ""


def build_ladders() -> list[Ladder]:
    """Return the full Tier-1 ladder registry (plan §2)."""
    ladders: list[Ladder] = []

    # T1.1 — carbon monotonicity. carbon_price is $/t (a first-class field);
    # rungs sweep it directly. Expectations: coal & CO2 monotone ↓ (gates);
    # gas-CC share and LW price ↑ (report-only, first round per §2).
    ladders.append(
        Ladder(
            test_id="T1.1",
            driver="carbon price $/t",
            rungs=[Rung(f"co2_{c:g}", {"carbon_price": c}) for c in (0, 25, 50, 100)],
            expectations=[
                Expectation(
                    "T1.1a", "coal generation monotone ↓", "coal_twh", "monotone_down"
                ),
                Expectation(
                    "T1.1b", "system CO2 monotone ↓", "co2_mt_total", "monotone_down"
                ),
                Expectation(
                    "T1.1c",
                    "load-weighted price ↑ (report)",
                    "lw_price",
                    "monotone_up",
                    gate=False,
                ),
                Expectation(
                    "T1.1d",
                    "coal gen actually moves across the ladder",
                    "coal_twh",
                    "strictly_changes",
                    tol=1e-3,
                ),
            ],
        )
    )

    # T1.2 — adder/cap duality. Rung 0 is the carbon=25 anchor (measures the
    # emissions the binding cap is then set to); rungs 1/2 enable the mass cap at
    # that tonnage (binding) and 2x it (slack). The binding tonnage is resolved
    # from the anchor rung after it solves (see resolve_dynamic_rungs).
    ladders.append(
        Ladder(
            test_id="T1.2",
            driver="mass-cap vs carbon-adder duality",
            rungs=[
                Rung("anchor_c25", {"carbon_price": 25.0}),
                Rung(
                    "cap_binding",
                    {"mass_cap_enabled": True, "_mass_cap_from_anchor": 1.0},
                ),
                Rung(
                    "cap_slack",
                    {"mass_cap_enabled": True, "_mass_cap_from_anchor": 2.0},
                ),
            ],
            expectations=[
                Expectation(
                    "T1.2a",
                    "binding-cap allowance dual ≈ $25",
                    "mass_cap_price",
                    "approx_target_first",
                    target=25.0,
                    tol=3.0,
                ),
            ],
            note="Strongest internal-consistency check the carbon stack has "
            "(§2): a mass cap set to the carbon=25 emissions must price its "
            "allowance at ≈ $25; a slack cap prices at 0. Requires a LIVE "
            "mass-cap program for the ISO — on an ISO with no covered budget "
            "(ERCOT; PJM RGGI is inert per audit D1) the row builds no covered "
            "coefficients, no co2_cap_price is returned, and T1.2a SKIPs. A SKIP "
            "here is therefore a mass-cap WIRING finding to route to P-1A, not a "
            "harness failure (confirmed by the P-0A smoke: the ERCOT cap rungs "
            "solve but emit the uncapped tonnage with a null allowance dual).",
        )
    )

    # T1.3 — gas ladder. gas_price_factor is the forecast-only multiplicative
    # lever. Coal dispatch ↑ with gas (coal-bearing ISOs); LW price ↑.
    ladders.append(
        Ladder(
            test_id="T1.3",
            driver="gas price factor",
            rungs=[Rung(f"gas_{f}", {"gas_price_factor": f}) for f in (0.5, 1.0, 1.5)],
            expectations=[
                Expectation(
                    "T1.3a",
                    "coal generation monotone ↑ with gas",
                    "coal_twh",
                    "monotone_up",
                ),
                Expectation(
                    "T1.3b",
                    "load-weighted price monotone ↑ with gas",
                    "lw_price",
                    "monotone_up",
                ),
            ],
        )
    )

    # T1.4 — load ladder. demand_growth_path low/mid/high. Scarcity hours and
    # entry monotone ↑; reserve margin ↓. The DC-vs-scalar signature is a
    # second, separate probe (report-only here — needs the energy-equivalent
    # uniform-scalar companion run, wired as a follow-up).
    ladders.append(
        Ladder(
            test_id="T1.4",
            driver="demand growth path",
            rungs=[Rung(p, {"demand_growth_path": p}) for p in ("low", "mid", "high")],
            expectations=[
                Expectation(
                    "T1.4a",
                    "scarcity (slack) hours monotone ↑",
                    "scarcity_hours",
                    "monotone_up",
                ),
                Expectation(
                    "T1.4b",
                    "final-year reserve margin monotone ↓",
                    "reserve_margin_final",
                    "monotone_down",
                ),
                Expectation(
                    "T1.4c",
                    "thermal entry GW monotone ↑ (report)",
                    "entry_thermal_gw",
                    "monotone_up",
                    gate=False,
                ),
            ],
        )
    )

    # T1.5 — IRA cliff. Build years straddling ira_wind_solar_last_year: wind
    # dispatch MC is negative pre-cliff (PTC) and ≥0 after. We probe the wind
    # dispatch marginal cost the model applies in the first vs a post-cliff year
    # by moving the cliff year itself (early vs late), holding the horizon fixed.
    ladders.append(
        Ladder(
            test_id="T1.5",
            driver="IRA wind/solar credit cliff year",
            rungs=[
                Rung("cliff_early", {"ira_wind_solar_last_year": 2026}),
                Rung("cliff_late", {"ira_wind_solar_last_year": 2035}),
            ],
            expectations=[
                Expectation(
                    "T1.5a",
                    "renewable entry responds to the cliff move",
                    "renewable_build_gw",
                    "strictly_changes",
                    gate=False,
                    tol=1e-3,
                ),
            ],
            note="Discontinuity check: entry economics must shift when the "
            "credit cliff moves relative to the build horizon.",
        )
    )

    # T1.6 — RPS/ACP. On an RPS-bearing ISO (NEISO), sweep the VRE fleet from
    # short (slow buildout) to long (aggressive): the REC dual is ≤ the ACP
    # ceiling always, and falls toward 0 as VRE builds through the target. The
    # RPS target itself is not config-overridable (it comes from
    # STATE_RPS_FLOORS), so the lever is the physical VRE supply — exactly what
    # the plan specifies ("VRE fleet held short vs long").
    ladders.append(
        Ladder(
            test_id="T1.6",
            driver="RPS/ACP vs VRE supply (short→long)",
            isos=("NEISO",),
            rungs=[
                Rung("vre_short", {"renewable_buildout_pace": "slow"}),
                Rung("vre_long", {"renewable_buildout_pace": "aggressive"}),
            ],
            expectations=[
                Expectation(
                    "T1.6a",
                    "REC dual ≤ ACP ceiling",
                    "rps_dual_over_acp",
                    "le_target",
                    target=1.0,
                    tol=1e-3,
                ),
                Expectation(
                    "T1.6b",
                    "REC dual ↓ as VRE builds toward the target",
                    "rps_dual_over_acp",
                    "monotone_down",
                ),
            ],
            note="rps_dual_over_acp is the final-year REC dual divided by the "
            "ISO's ACP ceiling; ≤ 1 means the ACP escape column caps the dual as "
            "designed, and it should fall as physical VRE covers the target.",
        )
    )

    # T1.7 — capacity-revenue net-CONE {0,1,2}x. On a capacity-market ISO
    # retirements ↓ / entry ↑ as net-CONE rises; ERCOT is the energy-only
    # negative control (byte-identical retirements across the ladder). The
    # scalar has no ScenarioConfig field yet (P-1B adds capacity_market_clearing);
    # until then it is a documented worker-level probe patch (never persisted,
    # never a keeper).
    ladders.append(
        Ladder(
            test_id="T1.7",
            driver="capacity-market net-CONE scalar",
            rungs=[
                Rung(f"cone_{s:g}x", {"_net_cone_scalar": s}) for s in (0.0, 1.0, 2.0)
            ],
            expectations=[
                Expectation(
                    "T1.7a",
                    "thermal retirements monotone ↓ in net-CONE (capacity-market ISO)",
                    "retired_thermal_gw",
                    "monotone_down",
                ),
                Expectation(
                    "T1.7b",
                    "ERCOT retirements byte-identical across the "
                    "net-CONE ladder (energy-only negative control)",
                    "retired_thermal_gw",
                    "all_equal",
                    tol=1e-6,
                ),
            ],
            note="Expectation T1.7a applies to PJM; T1.7b is the ERCOT negative "
            "control — the scorer picks per ISO (see EXPECTATIONS_BY_ISO).",
        )
    )

    # T1.8 — tech-cost path. Entry mix shifts toward the cheapened tech;
    # cumulative builds monotone; no cobweb (report).
    ladders.append(
        Ladder(
            test_id="T1.8",
            driver="technology cost path",
            rungs=[Rung(p, {"tech_cost_path": p}) for p in ("low", "mid", "high")],
            expectations=[
                Expectation(
                    "T1.8a",
                    "cumulative builds monotone ↓ as tech cost ↑",
                    "total_build_gw",
                    "monotone_down",
                    gate=False,
                ),
            ],
            note="Cheaper tech → more entry; the *mix* shift toward the "
            "cheapened tech is reported in the per-rung build tables.",
        )
    )

    # T1.9 — storage-ELCC saturation. Storage seeded at {5,15,25} GW (ERCOT);
    # storage capacity value per MW monotone ↓. The seed has no ScenarioConfig
    # field, so it is a documented worker probe (like T1.7's net-CONE scalar).
    ladders.append(
        Ladder(
            test_id="T1.9",
            driver="storage ELCC saturation (seed GW)",
            isos=("ERCOT",),
            rungs=[Rung(f"seed_{g:g}gw", {"_storage_seed_gw": g}) for g in (5, 15, 25)],
            expectations=[
                Expectation(
                    "T1.9a",
                    "storage capacity value per MW monotone ↓",
                    "storage_cap_value_per_mw",
                    "monotone_down",
                    gate=False,
                ),
            ],
            note="ELCC(4h) x saturation derate x portfolio dilution must fall "
            "as the fleet saturates the peak. Metric = the model's own "
            "marginal storage accreditation at the final fleet (from the "
            "evolution ledger's storage_power_mw — CR-3.1); in energy-only "
            "ERCOT the $ capacity price is 0 by design, so the accreditation "
            "fraction is the saturating observable. Report-only.",
        )
    )

    return ladders


# --------------------------------------------------------------------------- #
# Solve + metric extraction (worker process — must be top-level & picklable).
# --------------------------------------------------------------------------- #
@dataclass
class RungSpec:
    """A single forward run to execute for one ladder rung (picklable)."""

    rung_id: str  # "<test_id>:<iso>:<rung_label>"
    test_id: str
    iso: str
    rung_label: str
    overrides: dict
    start_year: int
    end_year: int
    cache_root: str
    metrics_cache: str  # path to the memoized metrics json (check-before-run)


def _apply_probe_patches(overrides: dict, iso: str):
    """Apply the two off-config diagnostic scalars, returning cleaned overrides.

    ``_net_cone_scalar`` (T1.7) and ``_storage_seed_gw`` (T1.9) have no
    ScenarioConfig field yet. They are applied here as **diagnostic-only** module
    patches — never persisted, never a keeper, and confined to this worker
    process — so the ladder can be exercised before the P-1B/value-stack config
    fields land. Any other ``_``-prefixed key is passed through untouched (e.g.
    ``_mass_cap_from_anchor`` is resolved earlier, in the orchestrator).
    """
    clean = {k: v for k, v in overrides.items() if not k.startswith("_")}
    scalar = overrides.get("_net_cone_scalar")
    if scalar is not None:
        from market_sim.config import constants as C
        from market_sim.model import capacity as cap

        base = C.MARKET_DESIGN.get(iso)
        if base is not None:
            patched = C.MarketDesign(
                capacity_market=base.capacity_market,
                net_cone_per_kw_yr=base.net_cone_per_kw_yr * float(scalar),
            )
            # Patch the reference the retirement/entry screens actually read.
            cap.MARKET_DESIGN = dict(cap.MARKET_DESIGN)
            cap.MARKET_DESIGN[iso] = patched
    seed = overrides.get("_storage_seed_gw")
    if seed is not None:
        # Seed via the existing storage_deployment axis is coarse; the precise
        # GW seed lands with the value-stack probe. Map to the nearest pace so
        # the harness still sweeps a real driver.
        clean.setdefault(
            "storage_deployment",
            "low" if float(seed) <= 5 else "high" if float(seed) >= 25 else "mid",
        )
    return clean


def evaluate_rung(spec_dict: dict) -> dict:
    """Solve one rung's forward run and return its extracted metrics dict.

    Check-before-run (rule 7): if the memoized metrics file already exists it is
    returned without re-solving. A failed solve is captured
    (``status="failed"``) rather than raised, so one infeasible rung never
    aborts the whole ladder.
    """
    spec = RungSpec(**spec_dict)
    cache_path = Path(spec.metrics_cache)
    if cache_path.exists():
        try:
            cached = json.loads(cache_path.read_text())
            cached["cached"] = True
            return cached
        except (json.JSONDecodeError, OSError):
            pass  # corrupt cache — re-solve

    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.results import cache
    from market_sim.results.evolution_ledger import load_ledgers_for_run
    from market_sim.results.export import _summarize_year

    cache.CACHE_ROOT = Path(spec.cache_root)
    out: dict = {
        "rung_id": spec.rung_id,
        "test_id": spec.test_id,
        "iso": spec.iso,
        "rung_label": spec.rung_label,
        "overrides": spec.overrides,
        "status": "ok",
        "metrics": {},
        "cached": False,
    }
    try:
        clean = _apply_probe_patches(spec.overrides, spec.iso)
        from market_sim import runner

        config = ScenarioConfig(
            iso=spec.iso,
            use_campd_bins=False,  # legacy bins bound runtime (plan §2 Tier 1)
            start_year=spec.start_year,
            end_year=spec.end_year,
            **clean,
        )
        key = runner.run_scenario_iso(config, spec.iso)
        run_dir = cache.CACHE_ROOT / spec.iso / key
        ledgers = load_ledgers_for_run(run_dir)
        metrics = _extract_metrics(spec, config, cache, key, ledgers, _summarize_year)
        out["metrics"] = metrics
    except Exception as exc:  # noqa: BLE001 — a bad rung is data, not a crash
        out["status"] = "failed"
        out["error"] = f"{type(exc).__name__}: {exc}"
        logger.warning("rung %s failed: %s", spec.rung_id, out["error"])

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(out, indent=2))
    except OSError:
        pass
    return out


def _extract_metrics(spec, config, cache, key, ledgers, summarize) -> dict:
    """Read the per-rung scalar metrics the expectations score, from the cache.

    Every value here is a single scalar keyed by the name the Expectation table
    references; per-year detail is folded into aggregates so the ladder scorer
    stays simple.
    """
    from market_sim.config.constants import MARKET_DESIGN

    years = list(range(spec.start_year, spec.end_year + 1))
    coal_twh = gas_cc_twh = 0.0
    co2_mt_total = 0.0
    lw_prices: list[float] = []
    scarcity_hours = 0
    rps_duals: list[float | None] = []
    mass_cap_prices: list[float] = []
    cap_first: dict | None = None
    cap_last: dict = {}
    renew_build_gw = 0.0
    total_build_gw = 0.0
    for year in years:
        result = cache.load_result(spec.iso, key, year)
        context = cache.load_fleet_context(spec.iso, key, year)
        summary = summarize(result, context)
        gen = summary["generation_twh"]
        coal_twh += gen.get("coal", 0.0)
        gas_cc_twh += gen.get("gas_cc", 0.0)
        co2_mt_total += summary["emissions_mt"]
        # Load-weighted price proxy: the summary's mean zonal price (no per-zone
        # demand weight persisted here — the mean is the ladder-comparable
        # scalar the tornado also uses).
        lw_prices.append(summary["avg_price"])
        scarcity_hours += int((result.slack.sum(axis=0) > 1.0).sum())
        rps_duals.append(result.rps_shadow_price)
        if result.co2_cap_price:
            mass_cap_prices.append(float(max(result.co2_cap_price)))
        if cap_first is None:
            cap_first = dict(summary["capacity_gw"])
        cap_last = summary["capacity_gw"]

    # Capacity evolution aggregates from the ledgers.
    reserve_margins: list[tuple[int, float]] = []
    entry_thermal_gw = 0.0
    for y in sorted(ledgers):
        led = ledgers[y]
        rm = led.get("reserve_margin")
        if rm is not None:
            reserve_margins.append((y, float(rm)))
        for a in led.get("thermal_additions", []):
            entry_thermal_gw += float(a.get("mw", 0.0)) / 1000.0
        for a in led.get("renewable_additions", []):
            renew_build_gw += float(a.get("mw", 0.0)) / 1000.0
        for a in led.get("thermal_additions", []):
            total_build_gw += float(a.get("mw", 0.0)) / 1000.0
        for a in led.get("storage_additions", []):
            total_build_gw += float(a.get("mw", 0.0)) / 1000.0
    total_build_gw += renew_build_gw

    # Retired thermal GW = first-year minus last-year thermal capacity (the only
    # observable retirement signal without threading an explicit log, same as
    # the tornado).
    retired_thermal_gw = 0.0
    if cap_first is not None:
        for fuel in THERMAL_FUELS:
            drop = cap_first.get(fuel, 0.0) - cap_last.get(fuel, 0.0)
            if drop > 0:
                retired_thermal_gw += drop

    final_rm = reserve_margins[-1][1] if reserve_margins else None
    rps_final = next((d for d in reversed(rps_duals) if d is not None), None)
    acp = _acp_ceiling(config)

    metrics: dict = {
        "coal_twh": round(coal_twh, 4),
        "gas_cc_twh": round(gas_cc_twh, 4),
        "co2_mt_total": round(co2_mt_total, 4),
        "lw_price": round(sum(lw_prices) / len(lw_prices), 3) if lw_prices else None,
        "scarcity_hours": scarcity_hours,
        "entry_thermal_gw": round(entry_thermal_gw, 4),
        "renewable_build_gw": round(renew_build_gw, 4),
        "total_build_gw": round(total_build_gw, 4),
        "retired_thermal_gw": round(retired_thermal_gw, 4),
        "reserve_margin_final": round(final_rm, 5) if final_rm is not None else None,
    }
    if mass_cap_prices:
        metrics["mass_cap_price"] = round(mass_cap_prices[-1], 3)
    if rps_final is not None and acp:
        metrics["rps_dual_over_acp"] = round(rps_final / acp, 4)
    # T1.9 storage capacity value per MW — the model's OWN marginal storage
    # accreditation at the final fleet: ELCC(4h reference duration) x the
    # saturation derate x the portfolio dilution, evaluated at the last
    # solved year's storage fleet power (persisted in the evolution ledger
    # since CR-3.1). This is the physical firm-capacity value of the next
    # storage MW — the quantity the plan's T1.9 expectation names; in
    # energy-only ERCOT the $ capacity price is 0 by design, so the
    # accreditation fraction (not a fabricated $ value) is the saturating
    # observable. Absent (SKIP) only when no ledger carries the fleet state
    # (pre-CR-3.1 caches).
    storage_rows = [
        (y, ledgers[y])
        for y in sorted(ledgers)
        if ledgers[y].get("storage_power_mw") is not None
    ]
    if storage_rows:
        from market_sim.config.constants import STORAGE_ELCC_SATURATION_EXPONENT
        from market_sim.config.constants import (
            STORAGE_DEPLOYMENT_CEILING_MW as _CEIL,
        )
        from market_sim.model.capacity import _storage_portfolio_elcc_dilution
        from market_sim.model.storage import _elcc_for_duration

        _, last = storage_rows[-1]
        fleet_mw = float(last["storage_power_mw"])
        ceiling = _CEIL.get(spec.iso, 0.0)
        pen = 0.0 if ceiling <= 0.0 else min(1.0, fleet_mw / ceiling)
        marginal = (
            _elcc_for_duration(4.0)
            * (1.0 - pen) ** STORAGE_ELCC_SATURATION_EXPONENT
            * _storage_portfolio_elcc_dilution(fleet_mw, spec.iso)
        )
        metrics["storage_fleet_mw"] = round(fleet_mw, 1)
        metrics["storage_cap_value_per_mw"] = round(marginal, 5)
        firm = last.get("storage_firm_mw")
        if firm and fleet_mw > 0.0:
            metrics["storage_fleet_avg_elcc"] = round(float(firm) / fleet_mw, 5)
        # Duration tilt (report column): share of new-built storage MW with
        # duration >= 6 h across the horizon — rises with saturation if the
        # duration-ELCC economics are doing their job.
        new_mw = longdur_mw = 0.0
        for _, led in storage_rows:
            for add in led.get("storage_additions", []) or []:
                mw = float(add.get("mw", 0.0))
                new_mw += mw
                if float(add.get("duration_h", 0.0)) >= 6.0:
                    longdur_mw += mw
        if new_mw > 0.0:
            metrics["storage_new_longdur_share"] = round(longdur_mw / new_mw, 4)
    design = MARKET_DESIGN.get(spec.iso)
    if design is not None and design.capacity_market:
        metrics["net_cone"] = design.net_cone_per_kw_yr
    return metrics


def _acp_ceiling(config) -> float | None:
    """Best-effort ISO RPS ACP ceiling ($/MWh) for the T1.6 ratio."""
    try:
        from market_sim.policy.rps import get_rps_acp

        return float(get_rps_acp(config.iso))
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def resolve_dynamic_rungs(ladder: Ladder, solved: dict[str, dict]) -> list[Rung]:
    """Fill in rungs whose overrides depend on an earlier rung's result.

    Currently only T1.2: ``_mass_cap_from_anchor`` multiplies the anchor rung's
    realized CO2 (in tons) to set ``mass_cap_tons``. Returns the rung list with
    those placeholders resolved (or dropped if the anchor didn't solve).
    """
    anchor = solved.get("anchor_c25")
    resolved: list[Rung] = []
    for rung in ladder.rungs:
        mult = rung.overrides.get("_mass_cap_from_anchor")
        if mult is None:
            resolved.append(rung)
            continue
        if not anchor or anchor.get("status") != "ok":
            continue  # can't set the cap without the anchor
        co2_mt = anchor.get("metrics", {}).get("co2_mt_total")
        if co2_mt is None:
            continue
        tons = co2_mt * 1e6 * float(mult)
        ov = {k: v for k, v in rung.overrides.items() if k != "_mass_cap_from_anchor"}
        ov["mass_cap_tons"] = tons
        resolved.append(Rung(rung.label, ov))
    return resolved


def make_rung_specs(
    ladder, iso, start_year, end_year, cache_root, metrics_root, rungs=None
):
    """Build a :class:`RungSpec` per rung for one ISO."""
    specs = []
    for rung in rungs if rungs is not None else ladder.rungs:
        rung_id = f"{ladder.test_id}:{iso}:{rung.label}"
        safe = rung_id.replace(":", "__").replace(" ", "_")
        specs.append(
            RungSpec(
                rung_id=rung_id,
                test_id=ladder.test_id,
                iso=iso,
                rung_label=rung.label,
                overrides=dict(rung.overrides),
                start_year=start_year,
                end_year=end_year,
                cache_root=cache_root,
                metrics_cache=str(Path(metrics_root) / iso / f"{safe}.json"),
            )
        )
    return specs


def run_specs(specs, workers, evaluate_fn=None):
    """Solve a batch of rung specs; return ``{rung_label: metrics_dict}``.

    ``evaluate_fn`` is a test seam (as in the tornado): when supplied the rungs
    run in-process; otherwise each solves in a fresh worker
    (``max_tasks_per_child=1`` frees its memory on exit), capped at ``workers``.
    """
    results: dict[str, dict] = {}
    if evaluate_fn is not None:
        for spec in specs:
            results[spec.rung_label] = evaluate_fn(asdict(spec))
        return results
    workers = max(1, int(workers))
    with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
        futures = {pool.submit(evaluate_rung, asdict(s)): s.rung_label for s in specs}
        for fut in as_completed(futures):
            lbl = futures[fut]
            results[lbl] = fut.result()
            logger.info("  rung %s -> %s", lbl, results[lbl].get("status"))
    return results


def run_ladder(
    ladder,
    iso,
    start_year,
    end_year,
    cache_root,
    metrics_root,
    workers,
    max_rungs=None,
    evaluate_fn=None,
) -> dict:
    """Solve every rung of one ladder for one ISO and score its expectations."""
    rungs = ladder.rungs if max_rungs is None else ladder.rungs[:max_rungs]

    # First pass solves only the STATIC rungs — anchor-dependent rungs (T1.2's
    # ``_mass_cap_from_anchor``) can't be solved until their driver value is
    # resolved from the anchor, so solving them now would waste a run on an
    # unresolved config.
    static = [r for r in rungs if r.overrides.get("_mass_cap_from_anchor") is None]
    static_specs = make_rung_specs(
        ladder, iso, start_year, end_year, cache_root, metrics_root, static
    )
    solved = run_specs(static_specs, workers, evaluate_fn)

    # Second pass: resolve anchor-dependent rungs against the solved anchor and
    # solve them. Skipped when the ladder is truncated below its anchor.
    if any(r.overrides.get("_mass_cap_from_anchor") for r in rungs):
        dyn = resolve_dynamic_rungs(ladder, solved)
        dyn = [r for r in dyn if r.overrides.get("_mass_cap_from_anchor") is None]
        dyn = [r for r in dyn if r.label not in solved]  # don't re-solve the anchor
        if dyn:
            dyn_specs = make_rung_specs(
                ladder, iso, start_year, end_year, cache_root, metrics_root, dyn
            )
            solved.update(run_specs(dyn_specs, workers, evaluate_fn))

    rung_rows = [solved[r.label] for r in rungs if r.label in solved]
    rung_rows += [v for k, v in solved.items() if k not in {r.label for r in rungs}]
    ok_rows = [r for r in rung_rows if r.get("status") == "ok"]

    expectations = _expectations_for(ladder, iso)
    ledger = [evaluate_expectation(e, ok_rows) for e in expectations]
    return {
        "test_id": ladder.test_id,
        "iso": iso,
        "driver": ladder.driver,
        "note": ladder.note,
        "rungs": rung_rows,
        "expectations": ledger,
    }


def _expectations_for(ladder: Ladder, iso: str) -> list[Expectation]:
    """Select the expectations that apply to this ISO.

    T1.7 splits: the monotone-retirement gate (T1.7a) applies to capacity-market
    ISOs; the byte-identical negative control (T1.7b) applies to ERCOT. Every
    other ladder's expectations apply to all of its ISOs.
    """
    from market_sim.config.constants import DEFAULT_MARKET_DESIGN, MARKET_DESIGN

    is_cap_market = MARKET_DESIGN.get(iso, DEFAULT_MARKET_DESIGN).capacity_market
    out = []
    for e in ladder.expectations:
        if e.expr_id == "T1.7a" and not is_cap_market:
            continue
        if e.expr_id == "T1.7b" and is_cap_market:
            continue
        out.append(e)
    return out


# --------------------------------------------------------------------------- #
# Report (tornado style: markdown + machine-readable JSON)
# --------------------------------------------------------------------------- #
def render_report(
    iso, start_year, end_year, ladder_results, run_date, max_rungs=None
) -> str:
    """Render the committed markdown driver-battery report."""
    lines: list[str] = []
    a = lines.append
    a(f"# Driver battery — {iso} forecast {start_year}-{end_year}")
    a("")
    a(
        f"*Generated {run_date} by `scripts/run_driver_battery.py` "
        "(plan §2 Tier 1). Forecast probe — NOT a backcast dashboard run.*"
    )
    a("")
    a(
        "Single-driver directional & elasticity ladders. Each expectation was "
        "**pre-registered** (in the ladder table in this script) before the run; "
        "a gated FAIL is a root-cause issue, never a threshold to widen "
        "(rules 1/11/14). This is measurement, not tuning."
    )
    a("")
    if max_rungs is not None:
        a(
            f"> **Harness smoke run** — rungs capped at {max_rungs} per ladder to "
            "prove the rig; monotonicity checks that need ≥2 rungs report SKIP. "
            "The full battery (all rungs) is P-1A."
        )
        a("")
    a("## Run configuration")
    a("")
    a(f"- **ISO:** {iso}")
    a(f"- **Horizon:** {start_year}-{end_year} (sequential years, rule 12)")
    a(
        "- **Fleet representation:** legacy equal-width bins "
        "(`use_campd_bins=False`) — runtime trade, same as the tornado"
    )
    a("")

    # Summary scoreboard.
    n_pass = n_fail = n_warn = n_skip = 0
    for lr in ladder_results:
        for e in lr["expectations"]:
            n_pass += e["status"] == PASS
            n_fail += e["status"] == FAIL
            n_warn += e["status"] == WARN
            n_skip += e["status"] == SKIP
    a("## Scoreboard")
    a("")
    a(
        f"**{n_pass} PASS · {n_fail} FAIL · {n_warn} WARN · {n_skip} SKIP** "
        f"across {len(ladder_results)} ladders."
    )
    a("")
    a("| Test | Driver | Expectation | Gate | Status | Detail |")
    a("|---|---|---|:--:|:--:|---|")
    for lr in ladder_results:
        for e in lr["expectations"]:
            gate = "gate" if e["gate"] else "rpt"
            a(
                f"| {e['expr_id']} | {lr['driver']} | {e['description']} | "
                f"{gate} | {e['status']} | {e['detail']} |"
            )
    a("")

    # Per-ladder rung detail.
    a("## Per-ladder rungs")
    a("")
    for lr in ladder_results:
        a(f"### {lr['test_id']} — {lr['driver']}")
        a("")
        if lr["note"]:
            a(f"_{lr['note']}_")
            a("")
        a("| Rung | Status | Overrides | Key metrics |")
        a("|---|:--:|---|---|")
        for r in lr["rungs"]:
            ov = {k: v for k, v in r.get("overrides", {}).items()}
            m = r.get("metrics", {})
            keymetrics = ", ".join(
                f"{k}={v}"
                for k, v in m.items()
                if k
                in {
                    "coal_twh",
                    "co2_mt_total",
                    "lw_price",
                    "scarcity_hours",
                    "retired_thermal_gw",
                    "mass_cap_price",
                    "rps_dual_over_acp",
                    "reserve_margin_final",
                }
            )
            status = r.get("status", "?")
            if r.get("cached"):
                status += " (cached)"
            if r.get("error"):
                keymetrics = r["error"]
            a(f"| {r.get('rung_label', '?')} | {status} | `{ov}` | {keymetrics} |")
        a("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--iso", default="ERCOT", help="ISO to run (ERCOT or PJM).")
    p.add_argument("--start-year", type=int, default=2026)
    p.add_argument("--end-year", type=int, default=2030)
    p.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Max concurrent solve processes (rule 12 caps at ~2).",
    )
    p.add_argument(
        "--tests",
        nargs="+",
        default=None,
        help="Restrict to these ladder ids (e.g. T1.1 T1.3).",
    )
    p.add_argument(
        "--max-rungs",
        type=int,
        default=None,
        help="Cap rungs per ladder (harness smoke uses 1).",
    )
    p.add_argument(
        "--out",
        default="docs/handoffs",
        help="Directory for the markdown + JSON report.",
    )
    p.add_argument(
        "--cache-root",
        default=None,
        help="Disposable solve-cache root (default: under --out).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    args = _build_parser().parse_args(argv)
    iso = args.iso.upper()

    ladders = build_ladders()
    if args.tests:
        keep = set(args.tests)
        ladders = [lad for lad in ladders if lad.test_id in keep]
        if not ladders:
            raise SystemExit(f"no ladders match --tests {args.tests}")
    # Only ladders that name this ISO.
    ladders = [lad for lad in ladders if iso in lad.isos]
    if not ladders:
        raise SystemExit(f"no ladders registered for ISO {iso}")

    out_dir = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_root = args.cache_root or str(out_dir / f"_battery_cache_{iso}")
    metrics_root = str(out_dir / "_battery_metrics")

    logger.info(
        "driver battery %s %d-%d: %d ladders, %d workers, max_rungs=%s",
        iso,
        args.start_year,
        args.end_year,
        len(ladders),
        args.workers,
        args.max_rungs,
    )

    t0 = time.perf_counter()
    ladder_results = []
    for ladder in ladders:
        logger.info("ladder %s (%s)", ladder.test_id, ladder.driver)
        ladder_results.append(
            run_ladder(
                ladder,
                iso,
                args.start_year,
                args.end_year,
                cache_root,
                metrics_root,
                args.workers,
                max_rungs=args.max_rungs,
            )
        )
    elapsed = time.perf_counter() - t0
    logger.info("all ladders finished in %.1fs", elapsed)

    run_date = date.today().isoformat()
    report = render_report(
        iso,
        args.start_year,
        args.end_year,
        ladder_results,
        run_date,
        max_rungs=args.max_rungs,
    )
    stem = f"driver-battery-{iso.lower()}-{run_date}"
    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"
    md_path.write_text(report)
    json_path.write_text(
        json.dumps(
            {
                "iso": iso,
                "start_year": args.start_year,
                "end_year": args.end_year,
                "max_rungs": args.max_rungs,
                "elapsed_s": round(elapsed, 1),
                "ladders": ladder_results,
            },
            indent=2,
        )
    )
    logger.info("wrote %s and %s", md_path, json_path)
    print(f"driver-battery report: {md_path}")

    n_fail = sum(
        e["status"] == FAIL for lr in ladder_results for e in lr["expectations"]
    )
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
