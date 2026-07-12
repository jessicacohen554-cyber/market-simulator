#!/usr/bin/env python
"""Golden-scenario band regression for forecast runs (W2-P5, plan §2.3).

One pinned reference scenario — ERCOT reference config, 2026-2040, solved on
real HiGHS (rule 12: years sequential within the invocation) — with banded
quantities stored in ``tests/golden/ercot_2026_2040.json``:

* annual CO2 (±2%)
* capacity by fuel at the final solved year, 2040 (±1 GW/fuel)
* annual load-weighted price (±5%)
* total system cost, the LP objective value (±2%)
* cumulative builds by tech, summed from the evolution ledger (±10%, or a
  50 MW floor when the golden value itself is ~0, to avoid a divide-by-zero
  on a tech with no golden builds)

The golden values are seeded by the first run of ``seed`` below and pinned
until an explicit regeneration commit. Per the design's regeneration policy
(rule 23's "frozen against residuals" spirit, applied to a forecast fixture
instead of a calibration parameter): **a band exit is a finding, never an
invitation to auto-regenerate.** ``check`` never writes the golden file; only
``seed --force --reason "..."`` does, and the reason it is given is recorded
in the file's provenance so a reviewer can see, from the diff alone, what
code change the new goldens are supposed to reflect.

Usage::

    # Seed (only works once; refuses to overwrite an existing golden without
    # --force):
    python scripts/golden_forecast_bands.py seed \
        --reason "initial W2-P5 §2.3 golden seed, HEAD 455ed9f"

    # Regenerate after an intentional behavior change:
    python scripts/golden_forecast_bands.py seed --force \
        --reason "PR #NNNN changed the ORDC scarcity adder; goldens re-seeded to reflect it"

    # Check the current code against the pinned golden (this is what CI runs,
    # via tests/test_golden_forecast_bands.py):
    python scripts/golden_forecast_bands.py check
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

# Repo import bootstrap so the script runs from a checkout without an
# install. Mirrors scripts/check_forecast_invariants.py's own bootstrap;
# the repo root (for `from scripts import ...`) and src/ (for the package)
# both need to be on sys.path.
REPO = Path(__file__).resolve().parent.parent
_SRC = REPO / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results import cache as cachemod  # noqa: E402
from market_sim.runner import run_scenario_iso  # noqa: E402
from scripts import check_forecast_invariants as C  # noqa: E402

GOLDEN_DIR = REPO / "tests" / "golden"
GOLDEN_PATH = GOLDEN_DIR / "ercot_2026_2040.json"
RUN_CONFIG_PATH = GOLDEN_DIR / "ercot_2026_2040.run_config.json"

# The pinned reference scenario. Originally plan §2.3's "ERCOT reference
# config, 2026-2032"; extended to 2026-2040 (P-3A, full-horizon findings
# 2026-07-12) to add a deeper mid-horizon checkpoint -- the end-year capacity
# snapshot now pins 2040 (past the OBBBA IRA cliffs and the bulk of the
# announced-retirement wave) instead of 2032, and the annual CO2/price/cost
# series covers 15 years instead of 7. use_campd_bins=False (legacy
# heat-rate bins, not ERCOT's CAMPD-default per-plant binning) bounds runtime
# for the weekly CI tier -- the same tradeoff forecast-invariants.yml's
# existing paired-invariants job already makes for the same reason. Every
# other field is ScenarioConfig's default, including confirmed_exits_enabled=
# True (flipped default-on by PR #1434, 2026-07-05) -- the goldens below bake
# that default in.
REFERENCE_SCENARIO_KWARGS = dict(
    iso="ERCOT",
    mode="forecast",
    start_year=2026,
    end_year=2040,
    hours=8760,
    use_campd_bins=False,
)

# Band specs, one per banded quantity (plan §2.3). "relative": |c-g| <=
# tol*|g|. "absolute": |c-g| <= tol. "relative_or_absolute": the wider of a
# relative band and an absolute floor, so a golden value of ~0 doesn't force
# a zero-tolerance check.
BANDS: dict[str, dict] = {
    "annual_co2_tons": {"kind": "relative", "tol": 0.02},
    "annual_lw_price_per_mwh": {"kind": "relative", "tol": 0.05},
    "system_cost_usd": {"kind": "relative", "tol": 0.02},
    "capacity_by_fuel_end_year_mw": {"kind": "absolute", "tol": 1000.0},
    "cumulative_builds_by_tech_mw": {
        "kind": "relative_or_absolute",
        "tol": 0.10,
        "abs_floor": 50.0,
    },
}

REGEN_POLICY = (
    "Never auto-regenerate on a band exit (this is a finding, not a widening "
    "target -- see docs/handoffs/forecast-validation-program-2026-07.md §2.3 "
    "and CLAUDE.md rule 23's frozen-against-residuals spirit). To "
    "regenerate: run `python scripts/golden_forecast_bands.py seed --force "
    '--reason "<explicit citation of the causal code change>"` and commit '
    "the new tests/golden/ercot_2026_2040*.json alongside that change."
)


# --------------------------------------------------------------------------- #
# Solve + metric extraction
# --------------------------------------------------------------------------- #
def solve_reference(cache_root: Path) -> tuple[C.Run, Path, ScenarioConfig]:
    """Solve the pinned reference scenario into ``cache_root`` and load it."""
    cachemod.CACHE_ROOT = cache_root
    config = ScenarioConfig(**REFERENCE_SCENARIO_KWARGS)
    key = run_scenario_iso(config, config.iso)
    run_dir = cache_root / config.iso / key
    return C.load_run(run_dir), run_dir, config


def compute_metrics(run: C.Run) -> dict:
    """Extract the five banded quantities (plan §2.3) from a loaded ``Run``."""
    years = run.solved_years
    if not years:
        raise ValueError("run has no solved years")

    annual_co2: dict[str, float] = {}
    annual_price: dict[str, float] = {}
    annual_cost: dict[str, float] = {}
    for year in years:
        yd = run.years[year]
        co2 = C._annual_co2_tons(yd)
        if co2 is None and yd.context is not None:
            # The forecast path's DispatchResult carries no populated
            # `emissions` array (that's a downstream/backcast-only step), so
            # reconstruct CO2 the same way scripts/score_capacity_hindcast.py's
            # model_co2_by_year does: dispatch x the fleet context's
            # per-generator emission rate (tCO2/MWh).
            rate = np.asarray(yd.context.emission_rate, dtype=float)
            gen_mwh = np.asarray(yd.result.dispatch, dtype=float).sum(axis=1)
            co2 = float((gen_mwh * rate).sum())
        if co2 is not None:
            annual_co2[str(year)] = co2
        annual_price[str(year)] = C._load_weighted_price(yd)
        annual_cost[str(year)] = float(yd.result.objective_value)

    end_year = max(years)
    end_ctx = run.years[end_year].context
    capacity_by_fuel: dict[str, float] = {}
    storage_energy_cap_mwh = None
    if end_ctx is not None:
        for fuel, mw in zip(end_ctx.fuel_types, end_ctx.pmax_mw):
            capacity_by_fuel[fuel] = capacity_by_fuel.get(fuel, 0.0) + float(mw)
        capacity_by_fuel["wind"] = float(end_ctx.wind_cap_mw)
        capacity_by_fuel["solar"] = float(end_ctx.solar_cap_mw)
        storage_energy_cap_mwh = float(end_ctx.storage_energy_cap_mwh)

    # Cumulative builds by tech: sum every year's ledgered new capacity.
    # thermal_additions + renewable_additions + storage_additions are genuine
    # incremental MW; ccs_retrofits convert existing gas_cc capacity in place
    # (no new MW) so they are deliberately excluded from "builds".
    builds_by_tech: dict[str, float] = {}
    for ledger in run.ledgers.values():
        for rec in ledger.get("thermal_additions", []):
            builds_by_tech[rec["fuel"]] = builds_by_tech.get(rec["fuel"], 0.0) + float(
                rec["mw"]
            )
        for rec in ledger.get("renewable_additions", []):
            builds_by_tech[rec["tech"]] = builds_by_tech.get(rec["tech"], 0.0) + float(
                rec["mw"]
            )
        for rec in ledger.get("storage_additions", []):
            tech = rec.get("tech", "storage")
            builds_by_tech[tech] = builds_by_tech.get(tech, 0.0) + float(rec["mw"])

    return {
        "years": years,
        "capacity_end_year": end_year,
        "annual_co2_tons": annual_co2,
        "annual_lw_price_per_mwh": annual_price,
        "system_cost_usd": annual_cost,
        "capacity_by_fuel_end_year_mw": capacity_by_fuel,
        "cumulative_builds_by_tech_mw": builds_by_tech,
        "storage_energy_cap_end_year_mwh": storage_energy_cap_mwh,
    }


# --------------------------------------------------------------------------- #
# Band checking
# --------------------------------------------------------------------------- #
def _check_scalar_dict(
    golden: dict, computed: dict, band: dict, label: str
) -> list[str]:
    """Compare two ``{key: float}`` dicts under one band spec; return violations."""
    violations = []
    for key in sorted(set(golden) | set(computed)):
        g = float(golden.get(key, 0.0))
        c = float(computed.get(key, 0.0))
        kind = band["kind"]
        if kind == "relative":
            denom = abs(g) if abs(g) > 1e-9 else 1.0
            tol = band["tol"] * denom
        elif kind == "absolute":
            tol = band["tol"]
        elif kind == "relative_or_absolute":
            tol = max(band["tol"] * abs(g), band["abs_floor"])
        else:
            raise ValueError(f"unknown band kind {kind!r}")
        if abs(c - g) > tol:
            violations.append(
                f"{label}[{key}]: golden={g:.6g} computed={c:.6g} "
                f"|Δ|={abs(c - g):.6g} > band={tol:.6g}"
            )
    return violations


def check_bands(golden: dict, computed: dict) -> list[str]:
    """Compare a loaded golden payload's ``golden`` section against fresh metrics.

    Returns a list of human-readable violation strings; empty means every
    banded quantity is within tolerance.
    """
    violations: list[str] = []
    for metric, band in BANDS.items():
        violations.extend(
            _check_scalar_dict(golden[metric], computed[metric], band, metric)
        )
    return violations


# --------------------------------------------------------------------------- #
# Git provenance
# --------------------------------------------------------------------------- #
def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO, text=True, capture_output=True, check=True
    ).stdout.strip()


def _git_dirty() -> bool:
    return bool(_git("status", "--porcelain"))


# --------------------------------------------------------------------------- #
# CLI commands
# --------------------------------------------------------------------------- #
def cmd_seed(args: argparse.Namespace) -> int:
    if GOLDEN_PATH.exists() and not args.force:
        print(
            f"refusing to overwrite existing golden {GOLDEN_PATH} without "
            f"--force.\n{REGEN_POLICY}",
            file=sys.stderr,
        )
        return 1
    if not args.reason or not args.reason.strip():
        print(
            "refusing to seed/regenerate without --reason citing the "
            "intended behavior change (or, for the first seed, the seeding "
            "context).",
            file=sys.stderr,
        )
        return 1
    if _git_dirty() and not args.allow_dirty:
        print(
            "refusing to seed from a dirty working tree (provenance would "
            "not be reproducible from the recorded SHA). Commit or stash, "
            "or pass --allow-dirty to override.",
            file=sys.stderr,
        )
        return 1

    sha = _git("rev-parse", "HEAD")
    commit_date = _git("show", "-s", "--format=%cI", "HEAD")

    with tempfile.TemporaryDirectory(prefix="golden-forecast-bands-") as tmp:
        run, run_dir, config = solve_reference(Path(tmp))
        metrics = compute_metrics(run)

        run_config_payload = {
            "scenario_config": dataclasses.asdict(config),
            "git_sha": sha,
            "cache_key": run_dir.name,
        }
        RUN_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        RUN_CONFIG_PATH.write_text(
            json.dumps(run_config_payload, indent=2, sort_keys=True) + "\n"
        )

        payload = {
            "schema_version": 1,
            "description": (
                "Golden-scenario band regression fixture (forecast-validation "
                "program W2-P5, plan §2.3; horizon extended 2032->2040 in "
                "P-3A, 2026-07-12, for a deeper checkpoint). Pins an ERCOT "
                "reference forecast, 2026-2040, on real HiGHS; check_bands() "
                "compares a fresh solve of the same REFERENCE_SCENARIO_KWARGS "
                "against the values below."
            ),
            "scenario": REFERENCE_SCENARIO_KWARGS,
            "provenance": {
                "seeded_git_sha": sha,
                "seeded_git_sha_short": sha[:12],
                "seeded_git_commit_date": commit_date,
                "seed_reason": args.reason,
                "seeded_by": "scripts/golden_forecast_bands.py seed",
                "run_config_file": RUN_CONFIG_PATH.name,
                "notes": (
                    "confirmed_exits_enabled default-ON as of PR #1434 "
                    "(commit bc4a3f3, 2026-07-05) is baked into these "
                    "golden values -- ScenarioConfig.confirmed_exits_enabled "
                    "defaults True and REFERENCE_SCENARIO_KWARGS does not "
                    "override it. " + REGEN_POLICY
                ),
            },
            "bands": BANDS,
            "golden": metrics,
        }
        GOLDEN_PATH.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    print(f"wrote {GOLDEN_PATH}")
    print(f"wrote {RUN_CONFIG_PATH}")
    print(f"seeded at git SHA {sha} ({commit_date})")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    if not GOLDEN_PATH.exists():
        print(
            f"no golden fixture at {GOLDEN_PATH} -- seed it first with "
            "`python scripts/golden_forecast_bands.py seed --reason ...`",
            file=sys.stderr,
        )
        return 1

    payload = json.loads(GOLDEN_PATH.read_text())
    with tempfile.TemporaryDirectory(prefix="golden-forecast-bands-check-") as tmp:
        run, _run_dir, _config = solve_reference(Path(tmp))
        computed = compute_metrics(run)

    violations = check_bands(payload["golden"], computed)
    seeded_sha = payload["provenance"]["seeded_git_sha"]
    if violations:
        print(
            f"FAIL: {len(violations)} golden-band violation(s) vs golden "
            f"seeded at {seeded_sha}:"
        )
        for v in violations:
            print(f"  {v}")
        print(REGEN_POLICY)
        return 1

    print(f"PASS: all golden bands hold vs golden seeded at {seeded_sha}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_seed = sub.add_parser("seed", help="seed or regenerate the golden fixture")
    p_seed.add_argument("--force", action="store_true")
    p_seed.add_argument(
        "--reason", required=True, help="cite the seeding context or causal code change"
    )
    p_seed.add_argument("--allow-dirty", action="store_true")
    p_seed.set_defaults(func=cmd_seed)

    p_check = sub.add_parser("check", help="solve fresh and compare to the golden")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
