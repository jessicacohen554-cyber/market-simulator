#!/usr/bin/env python
"""Run ONE CES premium-ladder leg as its own invocation (FF-3F, L-CES).

The hardened premium-ladder harness. A CES campaign is a config LIST — the
``cases``-mode matrix YAML (``configs/ces_premium_matrix*.yaml``: BAU / CES-20 /
CES-40 / …) expanded onto a base forecast config through
:func:`market_sim.matrix.matrix_configs` — so the campaign is *data, not code*.
This driver solves exactly ONE named case per invocation, which is what the
§2.1b "10-hour rule" requires: every schedulable invocation is capped at 5
solve-years, so a full campaign is N independent ≤5-year leg invocations, each
solving its years strictly sequentially (rule 12), never one process fanning
the whole ladder.

Each leg reuses the instrumented solve engine
(``run_full_horizon.solve_and_summarize``) so it writes the SAME
``full_horizon_summary.json`` sidecar that ``register_forecast_baseline.py``
consumes (``--kind ces-poc``) — per-year wall/RSS, the honest I1-I14 invariant
list, and the headline trajectory. Legs solve into the DEFAULT ``results/``
cache (``redirect_cache=False``) so the report and the bundle can assemble every
leg by its ``cache_key``.

Two modes:

* ``--case NAME`` — solve that one leg (its own invocation).
* ``--assemble`` — build the matrix bundle (``meta.json`` + trajectory tables)
  from the legs already cached, with NO solve, so ``report_ces_campaign.py`` can
  consume the ladder. Cache-only: it never crosses the §2.1b window cap.

Usage (T1 POC — ERCOT 2026-2030, each leg its own invocation)::

    # one leg per invocation (rule 12: years sequential inside each):
    MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \\
      python scripts/run_ces_leg.py \\
        --config configs/scenarios/ercot_ces_poc_2026_2030.yaml \\
        --matrix configs/ces_premium_matrix_poc.yaml \\
        --case BAU --out-dir results/ff-ces-t1/BAU
    # … repeat --case CES-20, --case CES-40 …

    # then assemble the bundle from cache (no solve) for the report:
    python scripts/run_ces_leg.py \\
        --config configs/scenarios/ercot_ces_poc_2026_2030.yaml \\
        --matrix configs/ces_premium_matrix_poc.yaml \\
        --assemble --out-dir results/ff-ces-t1/bundle

The full 2026-2050 campaign (each leg one owner-authorized 25-year invocation,
``--full-solve-authorized``) stays §2.1b-deferred; this driver builds/proves the
machinery at T1 only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.scenarios import ScenarioConfig, SweepDefinition  # noqa: E402
from market_sim.matrix import matrix_configs, write_matrix_outputs  # noqa: E402
from market_sim.policy.federal_ces import premium_for_year  # noqa: E402
from scripts.run_full_horizon import (  # noqa: E402
    assert_schedulable,
    solve_and_summarize,
)


def _load_ladder(
    config_path: Path, matrix_path: Path, iso_override: str | None
) -> tuple[ScenarioConfig, dict[str, ScenarioConfig], str]:
    """Load the base config + ladder YAML and expand to ``{case: config}``.

    Returns ``(base_config, case_configs, iso)``. ``matrix_configs`` enforces
    forecast mode + a non-empty ``cases`` mapping (the campaign-is-data seam);
    the ISO is the CLI override or the base config's own.
    """
    base = ScenarioConfig.from_yaml(config_path)
    sweep = SweepDefinition.from_yaml(matrix_path)
    configs = matrix_configs(base, sweep)  # forecast-mode + cases-mode guarded
    iso = (iso_override or base.iso).upper()
    return base, configs, iso


def _leg_meta(case: str, leg: ScenarioConfig, campaign: str) -> dict:
    """The CES-provenance block recorded in the leg's summary (and sidecar).

    ``premium_for_year`` at the leg's start year is 0.0 for BAU (CES disabled)
    and the flat real premium otherwise — the same value the report reads.
    """
    return {
        "case": case,
        "campaign": campaign,
        "federal_ces_enabled": bool(leg.federal_ces_enabled),
        "federal_ces_crediting": leg.federal_ces_crediting,
        "premium_usd_per_mwh": premium_for_year(leg, leg.start_year),
    }


def run_leg(
    config_path: Path,
    matrix_path: Path,
    case: str,
    out_dir: Path,
    iso_override: str | None,
    full_solve_authorized: bool,
    sample_interval: float,
    campaign: str | None,
) -> dict:
    """Solve one named ladder leg as its own invocation; return its summary."""
    base, configs, iso = _load_ladder(config_path, matrix_path, iso_override)
    if case not in configs:
        raise SystemExit(
            f"case {case!r} is not in the ladder {matrix_path.name}; "
            f"available cases: {sorted(configs)}"
        )
    leg = configs[case]

    # §2.1b window cap — mirrors run_full_horizon's gate. One leg is one
    # invocation; a >5-year leg needs the owner's per-campaign authorization.
    assert_schedulable(leg.start_year, leg.end_year, full_solve_authorized)

    campaign = campaign or matrix_path.stem
    print(
        f"[ces-leg] {iso} case={case} {leg.start_year}-{leg.end_year} "
        f"premium={_leg_meta(case, leg, campaign)['premium_usd_per_mwh']:.1f} "
        f"crediting={leg.federal_ces_crediting} "
        f"enabled={leg.federal_ces_enabled}"
    )
    # redirect_cache=False → the leg lands in the DEFAULT results/ cache, where
    # the bundle + report resolve every case by cache_key.
    return solve_and_summarize(
        leg,
        iso,
        out_dir,
        sample_interval=sample_interval,
        redirect_cache=False,
        extra_summary=_leg_meta(case, leg, campaign),
    )


def assemble_bundle(
    config_path: Path,
    matrix_path: Path,
    out_dir: Path,
    iso_override: str | None,
    legs_dir: Path,
) -> Path:
    """Build the matrix bundle from the already-solved legs (NO solve).

    The ``cache_key`` is read from each leg's ``full_horizon_summary.json``
    (matched by its recorded ``case``), NOT recomputed from the config: the
    runner resolves the policy bundle and applies ISO default-overrides BEFORE
    it hashes the config (``runner.run_scenario_iso``), so a naive
    ``config.cache_key()`` in a fresh process does not reproduce the key the
    solve actually used. The summary records the real key, so it is the single
    source of truth. Those keys become ``meta.json`` (case → cache_key) via
    :func:`market_sim.matrix.write_matrix_outputs`, which reads the DEFAULT
    cache to assemble the trajectory table and envelope. A case whose summary
    is absent is skipped (``report_ces_campaign.py`` reports the gap). Purely a
    cache read — zero solve-years, so it never touches the §2.1b cap.
    """
    base, configs, iso = _load_ladder(config_path, matrix_path, iso_override)
    members: dict[str, str] = {}
    for summary_path in sorted(legs_dir.glob("*/full_horizon_summary.json")):
        summary = json.loads(summary_path.read_text())
        case, key = summary.get("case"), summary.get("cache_key")
        if case in configs and key:
            members[case] = key
    if not members:
        raise SystemExit(
            f"no leg summaries under {legs_dir}/*/full_horizon_summary.json — "
            f"run the legs first (--case ...)"
        )
    print(f"[ces-leg] assembling bundle for {iso}: {len(members)} cases")
    for case in configs:  # ladder order; flag any case not yet solved
        print(f"    {case:<10} {members.get(case, '(no summary — skipped)')}")
    return write_matrix_outputs(iso, base, matrix_path, members, out_dir=out_dir)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Base forecast scenario YAML the ladder overrides onto.",
    )
    ap.add_argument(
        "--matrix",
        type=Path,
        required=True,
        help="Cases-mode ladder YAML (e.g. configs/ces_premium_matrix_poc.yaml).",
    )
    ap.add_argument("--iso", default=None, help="Defaults to the base config's ISO.")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument(
        "--legs-dir",
        type=Path,
        default=None,
        help="--assemble only: parent dir holding each leg's <case>/"
        "full_horizon_summary.json. Defaults to the bundle out-dir's parent.",
    )
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--case",
        default=None,
        help="Solve this one ladder leg (its own invocation).",
    )
    mode.add_argument(
        "--assemble",
        action="store_true",
        help="Build the matrix bundle from already-cached legs (no solve).",
    )
    ap.add_argument(
        "--campaign", default=None, help="Campaign tag (default: matrix stem)."
    )
    ap.add_argument("--sample-interval", type=float, default=0.5)
    ap.add_argument(
        "--full-solve-authorized",
        action="store_true",
        help=(
            "Lift the §2.1b 5-solve-year window cap for this leg — required for a "
            "full 2026-2050 campaign leg, and only with session-logged owner "
            "authorization (plan §2.1b(d)). A T1 (≤5-year) leg needs none."
        ),
    )
    args = ap.parse_args(argv)

    if args.assemble:
        legs_dir = args.legs_dir or args.out_dir.parent
        assemble_bundle(args.config, args.matrix, args.out_dir, args.iso, legs_dir)
        return 0

    summary = run_leg(
        args.config,
        args.matrix,
        args.case,
        args.out_dir,
        args.iso,
        args.full_solve_authorized,
        args.sample_interval,
        args.campaign,
    )
    return 1 if summary.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
