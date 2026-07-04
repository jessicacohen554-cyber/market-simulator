"""One-at-a-time (OAT) sensitivity / tornado diagnostic for the forecast layer.

Audit prompt PP-3.1 (``docs/model-audit-prompt-pack-2026-06.md``) and CLAUDE.md
rule 15 (the DOF ledger): quantify how much each high-leverage forecast knob
moves the emissions trajectory, the load-weighted price, and the retirement
pace, so the overfitting surface can be measured and contained.

**What it does.** For one ISO over a short forecast horizon it runs a base case
and then, for each registered parameter, one ``low`` and one ``high`` band run
with everything else held at its default. Each run is a full forward solve
(capacity evolution + P0/P1 dispatch, sequential years, exactly as
``runner.run_scenario_iso`` does it). It then reads three headline metrics back
out of the cached per-year bundles:

  * ``co2_mt_final`` / ``co2_mt_total`` — annual CO2 (million tonnes), from
    ``results.export._summarize_year`` (dispatch x FleetContext.emission_rate).
  * ``avg_price`` — mean zonal LMP over the horizon.
  * ``retired_thermal_gw`` — cumulative thermal capacity retired between the
    first and last horizon year (the only observable retirement signal; nothing
    persists an explicit retirement log — see ``capacity.evolve_fleet``).

The tornado ranks the parameters by the magnitude of the (high - low) swing in
each metric and writes a committed markdown report plus a machine-readable JSON.

**This is measurement and containment, not tuning.** Nothing here changes a
calibrated value or a keeper; it only perturbs a config and observes the output
(PP-3.1: "do not tune anything"). Per CLAUDE.md rule 12/15 the year loop inside
each run stays sequential, and separate runs are capped at ``--workers`` (default
2) concurrent processes to stay within memory.

**Runtime note.** The default base config uses ``use_campd_bins=False`` (the
legacy equal-width heat-rate fleet) so ~30 forward runs finish in a reasonable
wall-clock. The per-plant CAMPD fleet (``--campd-bins``) is far more faithful
but ~3x slower per year; the *ranking* of leverage — the deliverable that feeds
the DOF ledger — is robust to the fleet granularity, and the report flags the
choice explicitly.

Usage::

    python scripts/run_sensitivity_tornado.py --iso ERCOT \
        --start-year 2026 --end-year 2028 --workers 2 \
        --out docs/handoffs

    # quick smoke (two params, one evolution year)
    python scripts/run_sensitivity_tornado.py --iso ERCOT \
        --start-year 2026 --end-year 2027 --only gas_price coal_fom_multiplier
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

logger = logging.getLogger("sensitivity_tornado")

# Fuels whose year-over-year capacity drop counts as a thermal retirement. Wind
# and solar are modeled as zonal pools (they grow, never "retire" here); storage
# is tracked separately. Matches results.export._summarize_year fuel keys.
THERMAL_FUELS: tuple[str, ...] = (
    "coal",
    "gas_cc",
    "gas_ct",
    "gas_st",
    "oil",
    "nuclear",
)


# --------------------------------------------------------------------------- #
# Parameter registry
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class ParamPerturbation:
    """One tornado parameter and its low/high band.

    Attributes:
        key: Short stable identifier used on the CLI and in the report.
        label: Human-readable name.
        unit: Unit string for the displayed values.
        base_display: How the base (unperturbed) value reads in the report.
        low_display: Display string for the low band value.
        high_display: Display string for the high band value.
        low_overrides: ``ScenarioConfig.with_overrides`` kwargs for the low run.
        high_overrides: ``ScenarioConfig.with_overrides`` kwargs for the high run.
        citation: Provenance of the base value (CLAUDE.md rule 5).
        category: ``"forecast"`` (drives capacity evolution / retirements) or
            ``"dispatch"`` (merit order / price, emissions only indirectly).
        note: Optional caveat (e.g. a one-sided band).
    """

    key: str
    label: str
    unit: str
    base_display: str
    low_display: str
    high_display: str
    low_overrides: dict
    high_overrides: dict
    citation: str
    category: str
    note: str = ""


def build_registry() -> list[ParamPerturbation]:
    """Return the tornado parameter registry (the ~15 highest-leverage knobs).

    Every band is expressed as :meth:`ScenarioConfig.with_overrides` kwargs, so
    each variant is a first-class config whose ``cache_key`` captures the
    perturbation (no off-registry monkeypatch channel — CLAUDE.md rule 24). The
    bands are ranked roughly by expected emissions leverage; the actual ranking
    is what the run measures.

    Returns:
        The list of :class:`ParamPerturbation` entries.
    """
    return [
        ParamPerturbation(
            key="gas_price",
            label="Henry Hub gas price level",
            unit="$/MMBtu",
            base_display="mid path (~3.0)",
            low_display="2.55 (-15%)",
            high_display="3.45 (+15%)",
            low_overrides={"gas_price_override": 2.55},
            high_overrides={"gas_price_override": 3.45},
            citation="EIA AEO2025 (HENRY_HUB_TRAJECTORIES, constants.py:673)",
            category="forecast",
            note="Flat pin via gas_price_override isolates the level swing.",
        ),
        ParamPerturbation(
            key="demand_growth",
            label="Demand growth path",
            unit="path",
            base_display="mid",
            low_display="low",
            high_display="high",
            low_overrides={"demand_growth_path": "low"},
            high_overrides={"demand_growth_path": "high"},
            citation="EIA STEO / ERCOT CDR (DEMAND_GROWTH_RATES, constants.py:598)",
            category="forecast",
        ),
        ParamPerturbation(
            key="carbon_price",
            label="Carbon price path",
            unit="path",
            base_display="zero",
            low_display="zero",
            high_display="high",
            low_overrides={"carbon_price_path": "zero"},
            high_overrides={"carbon_price_path": "high"},
            citation="RFF (CARBON_PRICE_PATHS, constants.py:1200)",
            category="forecast",
            note="One-sided: forecast default carbon is zero (the floor).",
        ),
        ParamPerturbation(
            key="coal_fom_multiplier",
            label="Coal FOM multiplier (retirement)",
            unit="x",
            base_display="1.30",
            low_display="1.15",
            high_display="1.45",
            low_overrides={"retirement_fom_multiplier_coal": 1.15},
            high_overrides={"retirement_fom_multiplier_coal": 1.45},
            citation="Lazard LCOE 2024 (scenarios.py:136)",
            category="forecast",
        ),
        ParamPerturbation(
            key="reserve_margin",
            label="Retirement reliability floor",
            unit="fraction",
            base_display="0.15",
            low_display="0.10",
            high_display="0.20",
            low_overrides={"retirement_reserve_margin": 0.10},
            high_overrides={"retirement_reserve_margin": 0.20},
            citation="Reserve-margin heuristic (scenarios.py:144)",
            category="forecast",
        ),
        ParamPerturbation(
            key="retire_years_gas_cc",
            label="Gas-CC consecutive-loss retirement years",
            unit="years",
            base_display="3",
            low_display="2",
            high_display="4",
            low_overrides={"retirement_years_gas_cc": 2},
            high_overrides={"retirement_years_gas_cc": 4},
            citation="Retirement screen threshold (scenarios.py:129-135)",
            category="forecast",
        ),
        ParamPerturbation(
            key="fixed_om_coal",
            label="Coal going-forward FOM bar",
            unit="$/kW-yr",
            base_display="40.0",
            low_display="30.0",
            high_display="50.0",
            low_overrides={"fixed_om_coal": 30.0},
            high_overrides={"fixed_om_coal": 50.0},
            citation="NREL ATB legacy-steam (scenarios.py:146-162)",
            category="forecast",
        ),
        ParamPerturbation(
            key="fixed_om_gas_cc",
            label="Gas-CC going-forward FOM bar",
            unit="$/kW-yr",
            base_display="12.0",
            low_display="9.0",
            high_display="15.0",
            low_overrides={"fixed_om_gas_cc": 9.0},
            high_overrides={"fixed_om_gas_cc": 15.0},
            citation="NREL ATB (scenarios.py:146-162)",
            category="forecast",
        ),
        ParamPerturbation(
            key="fixed_om_gas_ct",
            label="Gas-CT going-forward FOM bar",
            unit="$/kW-yr",
            base_display="8.0",
            low_display="6.0",
            high_display="10.0",
            low_overrides={"fixed_om_gas_ct": 6.0},
            high_overrides={"fixed_om_gas_ct": 10.0},
            citation="NREL ATB (scenarios.py:146-162)",
            category="forecast",
        ),
        ParamPerturbation(
            key="renewable_buildout",
            label="Renewable buildout pace",
            unit="pace",
            base_display="mid",
            low_display="slow",
            high_display="aggressive",
            low_overrides={"renewable_buildout_pace": "slow"},
            high_overrides={"renewable_buildout_pace": "aggressive"},
            citation="NREL ATB entry (renewable_buildout_pace, scenarios.py:65)",
            category="forecast",
        ),
        ParamPerturbation(
            key="renewable_cf",
            label="Renewable capacity-factor scalar",
            unit="x",
            base_display="1.00",
            low_display="0.95",
            high_display="1.05",
            low_overrides={"renewable_cf_adjustment": 0.95},
            high_overrides={"renewable_cf_adjustment": 1.05},
            citation="Model design scalar (scenarios.py:1635)",
            category="dispatch",
        ),
        ParamPerturbation(
            key="storage_deployment",
            label="Storage deployment pace",
            unit="pace",
            base_display="mid",
            low_display="low",
            high_display="high",
            low_overrides={"storage_deployment": "low"},
            high_overrides={"storage_deployment": "high"},
            citation="EIA-860 storage pipeline (storage_deployment, scenarios.py:66)",
            category="forecast",
        ),
        ParamPerturbation(
            key="battery_adder",
            label="Battery dispatch adder",
            unit="$/MWh",
            base_display="0.0",
            low_display="0.0",
            high_display="5.0",
            low_overrides={"battery_dispatch_adder": 0.0},
            high_overrides={"battery_dispatch_adder": 5.0},
            citation="Xu et al. 2018 cycle-aging (scenarios.py:2526)",
            category="dispatch",
            note="One-sided: adder floor is 0.",
        ),
        ParamPerturbation(
            key="voll",
            label="Value of lost load (price cap)",
            unit="$/MWh",
            base_display="5000",
            low_display="4000",
            high_display="6000",
            low_overrides={"voll": 4000.0},
            high_overrides={"voll": 6000.0},
            citation="ISO price cap (iso_configs.py; scenarios.py:41)",
            category="dispatch",
        ),
        ParamPerturbation(
            key="retire_years_coal",
            label="Coal consecutive-loss retirement years",
            unit="years",
            base_display="1",
            low_display="1",
            high_display="2",
            low_overrides={"retirement_years_coal": 1},
            high_overrides={"retirement_years_coal": 2},
            citation="Retirement screen threshold (scenarios.py:129)",
            category="forecast",
            note="One-sided: coal floor is 1 year.",
        ),
    ]


# --------------------------------------------------------------------------- #
# Variant specs + solve/extract
# --------------------------------------------------------------------------- #
@dataclass
class VariantSpec:
    """A single forward run to execute (picklable for a worker process)."""

    variant_id: str
    param_key: str
    direction: str  # "base" | "low" | "high"
    iso: str
    base_overrides: dict
    overrides: dict
    start_year: int
    end_year: int
    cache_root: str


@dataclass
class VariantResult:
    """Metrics read back from one forward run."""

    variant_id: str
    param_key: str
    direction: str
    status: str
    co2_mt_final: float | None = None
    co2_mt_total: float | None = None
    avg_price: float | None = None
    retired_thermal_gw: float | None = None
    retired_by_fuel: dict = field(default_factory=dict)
    per_year: list = field(default_factory=list)
    error: str | None = None


def _build_config(spec: VariantSpec):
    """Construct the perturbed :class:`ScenarioConfig` for a spec."""
    from market_sim.config.scenarios import ScenarioConfig

    config = ScenarioConfig(iso=spec.iso, **spec.base_overrides)
    if spec.overrides:
        config = config.with_overrides(**spec.overrides)
    return config


def evaluate_variant(spec_dict: dict) -> dict:
    """Run one forward solve and return its headline metrics as a dict.

    Executed in a worker process (must be a top-level, picklable function). It
    caps the horizon by rebinding ``runner.START_YEAR`` / ``runner.END_YEAR``
    (the same mechanism the test-suite uses; there is no horizon field on
    ``ScenarioConfig``) and isolates the disposable cache under
    ``spec.cache_root`` so distinct variants never collide.

    Args:
        spec_dict: A :class:`VariantSpec` serialized with ``dataclasses.asdict``.

    Returns:
        A :class:`VariantResult` serialized with ``dataclasses.asdict``. A
        failed solve is captured (``status="failed"``, ``error`` set) rather
        than raised, so one infeasible band never aborts the whole tornado.
    """
    spec = VariantSpec(**spec_dict)
    from market_sim import runner
    from market_sim.results import cache
    from market_sim.results.export import _summarize_year

    runner.START_YEAR = spec.start_year
    runner.END_YEAR = spec.end_year
    cache.CACHE_ROOT = Path(spec.cache_root)

    result = VariantResult(
        variant_id=spec.variant_id,
        param_key=spec.param_key,
        direction=spec.direction,
        status="ok",
    )
    try:
        config = _build_config(spec)
        key = runner.run_scenario_iso(config, spec.iso)

        per_year = []
        cap_by_fuel_first: dict[str, float] | None = None
        cap_by_fuel_last: dict[str, float] = {}
        for year in range(spec.start_year, spec.end_year + 1):
            dispatch_result = cache.load_result(spec.iso, key, year)
            context = cache.load_fleet_context(spec.iso, key, year)
            summary = _summarize_year(dispatch_result, context)
            cap_gw = summary["capacity_gw"]
            per_year.append(
                {
                    "year": year,
                    "co2_mt": summary["emissions_mt"],
                    "avg_price": summary["avg_price"],
                    "capacity_gw": cap_gw,
                }
            )
            if cap_by_fuel_first is None:
                cap_by_fuel_first = dict(cap_gw)
            cap_by_fuel_last = cap_gw

        result.per_year = per_year
        result.co2_mt_final = per_year[-1]["co2_mt"]
        result.co2_mt_total = float(sum(y["co2_mt"] for y in per_year))
        result.avg_price = float(np.mean([y["avg_price"] for y in per_year]))

        retired = {}
        if cap_by_fuel_first is not None:
            for fuel in THERMAL_FUELS:
                drop = cap_by_fuel_first.get(fuel, 0.0) - cap_by_fuel_last.get(
                    fuel, 0.0
                )
                if drop > 1e-6:
                    retired[fuel] = round(drop, 4)
        result.retired_by_fuel = retired
        result.retired_thermal_gw = round(float(sum(retired.values())), 4)
    except Exception as exc:  # noqa: BLE001 - a bad band is data, not a crash
        result.status = "failed"
        result.error = f"{type(exc).__name__}: {exc}"
        logger.warning("variant %s failed: %s", spec.variant_id, result.error)
    return asdict(result)


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def make_specs(
    iso: str,
    registry: list[ParamPerturbation],
    base_overrides: dict,
    start_year: int,
    end_year: int,
    cache_root: str,
) -> list[VariantSpec]:
    """Build the base spec plus one low and one high spec per parameter."""
    specs = [
        VariantSpec(
            variant_id="base",
            param_key="base",
            direction="base",
            iso=iso,
            base_overrides=dict(base_overrides),
            overrides={},
            start_year=start_year,
            end_year=end_year,
            cache_root=cache_root,
        )
    ]
    for param in registry:
        for direction, overrides in (
            ("low", param.low_overrides),
            ("high", param.high_overrides),
        ):
            specs.append(
                VariantSpec(
                    variant_id=f"{param.key}:{direction}",
                    param_key=param.key,
                    direction=direction,
                    iso=iso,
                    base_overrides=dict(base_overrides),
                    overrides=dict(overrides),
                    start_year=start_year,
                    end_year=end_year,
                    cache_root=cache_root,
                )
            )
    return specs


def run_tornado(
    specs: list[VariantSpec],
    workers: int = 2,
    evaluate_fn=None,
) -> dict[str, VariantResult]:
    """Execute every variant spec and collect its :class:`VariantResult`.

    Args:
        specs: The variant specs from :func:`make_specs`.
        workers: Maximum concurrent solve processes (CLAUDE.md rule 12 caps this
            at ~2 for memory). Ignored when ``evaluate_fn`` is supplied.
        evaluate_fn: Injection seam for tests — a callable taking a spec dict and
            returning a result dict. When ``None`` the real
            :func:`evaluate_variant` runs in a fresh process per variant
            (``max_tasks_per_child=1`` frees each solve's memory on exit).

    Returns:
        Mapping of ``variant_id`` to :class:`VariantResult`.
    """
    results: dict[str, VariantResult] = {}
    if evaluate_fn is not None:
        for spec in specs:
            results[spec.variant_id] = VariantResult(**evaluate_fn(asdict(spec)))
        return results

    workers = max(1, int(workers))
    with ProcessPoolExecutor(max_workers=workers, max_tasks_per_child=1) as pool:
        futures = {
            pool.submit(evaluate_variant, asdict(spec)): spec.variant_id
            for spec in specs
        }
        done = 0
        total = len(futures)
        for fut in as_completed(futures):
            vid = futures[fut]
            results[vid] = VariantResult(**fut.result())
            done += 1
            logger.info("[%d/%d] %s -> %s", done, total, vid, results[vid].status)
    return results


# --------------------------------------------------------------------------- #
# Ranking + report
# --------------------------------------------------------------------------- #
_METRICS = (
    ("co2_mt_final", "CO2 final year (Mt)"),
    ("co2_mt_total", "CO2 horizon total (Mt)"),
    ("avg_price", "Avg price ($/MWh)"),
    ("retired_thermal_gw", "Thermal retired (GW)"),
)


def rank_results(
    registry: list[ParamPerturbation],
    results: dict[str, VariantResult],
) -> dict:
    """Compute (high - low) swings per parameter and rank by magnitude.

    Args:
        registry: The parameter registry that produced ``results``.
        results: Output of :func:`run_tornado`.

    Returns:
        A dict with a ``base`` metrics block and, per metric key, a list of
        ``{key, label, low, high, delta, abs_delta}`` rows sorted by
        ``abs_delta`` descending. Parameters whose low or high run failed are
        listed under ``failed``.
    """
    base = results.get("base")
    base_metrics = {
        m: getattr(base, m) if base and base.status == "ok" else None
        for m, _ in _METRICS
    }

    ranked: dict[str, list] = {m: [] for m, _ in _METRICS}
    failed: list[str] = []
    for param in registry:
        low = results.get(f"{param.key}:low")
        high = results.get(f"{param.key}:high")
        if not low or not high or low.status != "ok" or high.status != "ok":
            failed.append(param.key)
            continue
        for metric, _ in _METRICS:
            lo = getattr(low, metric)
            hi = getattr(high, metric)
            if lo is None or hi is None:
                continue
            delta = hi - lo
            ranked[metric].append(
                {
                    "key": param.key,
                    "label": param.label,
                    "category": param.category,
                    "low": lo,
                    "high": hi,
                    "delta": round(delta, 4),
                    "abs_delta": round(abs(delta), 4),
                }
            )
    for metric in ranked:
        ranked[metric].sort(key=lambda r: r["abs_delta"], reverse=True)
    return {"base": base_metrics, "ranked": ranked, "failed": failed}


def render_report(
    iso: str,
    start_year: int,
    end_year: int,
    base_overrides: dict,
    registry: list[ParamPerturbation],
    results: dict[str, VariantResult],
    ranking: dict,
    run_date: str,
) -> str:
    """Render the committed markdown tornado report."""
    lines: list[str] = []
    a = lines.append
    a(f"# Sensitivity tornado — {iso} forecast {start_year}-{end_year}")
    a("")
    a(
        f"*Generated {run_date} by `scripts/run_sensitivity_tornado.py` "
        "(PP-3.1 / CLAUDE.md rule 15 DOF ledger).*"
    )
    a("")
    a(
        "One-at-a-time (OAT) +/- band sensitivity of the highest-leverage forecast "
        "knobs. Each row is the full-model swing from the parameter's low band to "
        "its high band with every other parameter held at default. This is "
        "**measurement, not tuning** — no calibrated value or keeper was changed."
    )
    a("")
    a("## Run configuration")
    a("")
    a(f"- **ISO:** {iso}")
    a(f"- **Horizon:** {start_year}-{end_year} (sequential years, rule 12)")
    bins = (
        "per-plant CAMPD"
        if base_overrides.get("use_campd_bins")
        else "legacy equal-width bins"
    )
    a(
        f"- **Fleet representation:** {bins} "
        f"(`use_campd_bins={base_overrides.get('use_campd_bins', True)}`)"
    )
    a(f"- **Base overrides:** `{base_overrides}`")
    a("")
    base_m = ranking["base"]
    a("### Base case")
    a("")
    a("| Metric | Value |")
    a("|---|---|")
    for m, label in _METRICS:
        v = base_m.get(m)
        a(f"| {label} | {v if v is not None else 'n/a'} |")
    a("")

    a("## Tornado rankings")
    a("")
    a("`delta = high - low`. Rows sorted by |delta| (most sensitive first).")
    for metric, label in _METRICS:
        a("")
        a(f"### {label}")
        a("")
        rows = ranking["ranked"].get(metric, [])
        if not rows:
            a("_No successful comparisons._")
            continue
        a("| Rank | Parameter | Cat. | Low | High | delta | |delta| |")
        a("|---:|---|---|---:|---:|---:|---:|")
        for i, r in enumerate(rows, 1):
            a(
                f"| {i} | {r['label']} | {r['category']} | {r['low']} | "
                f"{r['high']} | {r['delta']:+.4g} | {r['abs_delta']:.4g} |"
            )
    a("")

    a("## Parameter bands")
    a("")
    a("| Parameter | Base | Low | High | Unit | Cat. | Citation |")
    a("|---|---|---|---|---|---|---|")
    for p in registry:
        a(
            f"| {p.label} | {p.base_display} | {p.low_display} | {p.high_display} "
            f"| {p.unit} | {p.category} | {p.citation} |"
        )
    a("")
    if any(p.note for p in registry):
        a("**Band notes:**")
        for p in registry:
            if p.note:
                a(f"- *{p.label}:* {p.note}")
        a("")

    if ranking["failed"]:
        a("## Failed bands")
        a("")
        a(
            "These parameters had a low or high run that did not solve (e.g. an "
            "infeasible perturbation); their swings are omitted from the ranking."
        )
        a("")
        for key in ranking["failed"]:
            for direction in ("low", "high"):
                r = results.get(f"{key}:{direction}")
                if r and r.status != "ok":
                    a(f"- `{key}:{direction}` — {r.error}")
        a("")

    a("## Interpretation & caveats")
    a("")
    a(
        "- **OAT ignores interactions.** A tornado shows marginal leverage around "
        "the base point only; it does not capture joint moves (e.g. gas x carbon). "
        "Use the structured scenario matrix (PP-1.1) for interactions."
    )
    a(
        "- **Short horizon.** Retirement signals accumulate over the run; a "
        f"{end_year - start_year + 1}-year window captures near-term exits, not the "
        "2040 fleet. Re-run with a longer `--end-year` for mid-century leverage."
    )
    a(
        "- **Fleet granularity.** The legacy-bin default trades per-plant fidelity "
        "for runtime; the leverage *ranking* is the deliverable and is robust to it."
    )
    a(
        "- **One-sided bands** (carbon, battery adder, coal retire-years) sit at a "
        "natural floor; their delta is a one-directional response, not a symmetric "
        "band."
    )
    a("")
    a("## DOF-ledger feed")
    a("")
    a(
        "The forecast-category parameters with the largest CO2 leverage are the "
        "free degrees of freedom most in need of an identification source in the "
        "keeper attestation (CLAUDE.md rule 21). Ranked CO2-final leverage:"
    )
    a("")
    co2_rows = ranking["ranked"].get("co2_mt_final", [])
    for i, r in enumerate([x for x in co2_rows if x["category"] == "forecast"][:8], 1):
        a(
            f"{i}. **{r['label']}** — {r['abs_delta']:.4g} Mt swing "
            f"({r['low']} -> {r['high']} Mt)"
        )
    a("")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--iso", default="ERCOT", help="ISO to run (default ERCOT).")
    p.add_argument("--start-year", type=int, default=2026)
    p.add_argument("--end-year", type=int, default=2028)
    p.add_argument(
        "--workers",
        type=int,
        default=2,
        help="Max concurrent solve processes (rule 12 caps at ~2).",
    )
    p.add_argument(
        "--campd-bins",
        action="store_true",
        help="Use the per-plant CAMPD fleet (faithful but ~3x slower). "
        "Default is the legacy equal-width fleet.",
    )
    p.add_argument(
        "--only",
        nargs="+",
        default=None,
        help="Restrict to these parameter keys (default: all).",
    )
    p.add_argument(
        "--out",
        default="docs/handoffs",
        help="Directory for the markdown + JSON report.",
    )
    p.add_argument(
        "--cache-root",
        default=None,
        help="Disposable solve-cache root (default: a temp dir under --out).",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: run the tornado and write the committed report."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    args = _build_parser().parse_args(argv)
    iso = args.iso.upper()

    registry = build_registry()
    if args.only:
        keep = set(args.only)
        registry = [p for p in registry if p.key in keep]
        if not registry:
            raise SystemExit(f"no registry params match --only {args.only}")

    base_overrides = {"use_campd_bins": bool(args.campd_bins)}

    out_dir = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    cache_root = args.cache_root or str(out_dir / f"_tornado_cache_{iso}")

    specs = make_specs(
        iso, registry, base_overrides, args.start_year, args.end_year, cache_root
    )
    logger.info(
        "tornado %s %d-%d: %d params, %d runs, %d workers",
        iso,
        args.start_year,
        args.end_year,
        len(registry),
        len(specs),
        args.workers,
    )

    t0 = time.perf_counter()
    results = run_tornado(specs, workers=args.workers)
    elapsed = time.perf_counter() - t0
    logger.info("all runs finished in %.1fs", elapsed)

    ranking = rank_results(registry, results)
    run_date = date.today().isoformat()
    report = render_report(
        iso,
        args.start_year,
        args.end_year,
        base_overrides,
        registry,
        results,
        ranking,
        run_date,
    )

    stem = f"sensitivity-tornado-{iso.lower()}-{run_date}"
    md_path = out_dir / f"{stem}.md"
    json_path = out_dir / f"{stem}.json"
    md_path.write_text(report)
    json_path.write_text(
        json.dumps(
            {
                "iso": iso,
                "start_year": args.start_year,
                "end_year": args.end_year,
                "base_overrides": base_overrides,
                "elapsed_s": round(elapsed, 1),
                "results": {k: asdict(v) for k, v in results.items()},
                "ranking": ranking,
            },
            indent=2,
        )
    )
    logger.info("wrote %s and %s", md_path, json_path)
    print(f"tornado report: {md_path}")


if __name__ == "__main__":
    main()
