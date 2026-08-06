"""NYISO A/B driver: solve arms on the DESIGNATED KEEPER's recipe.

**Re-pointed 2026-08-06 (nyiso-129) and kept live for the successor lane.**
:data:`KEEPER_RUN_CONFIG` now reads the newly promoted
``2026-08-06-nyiso-128-solar-basis`` (bundle ``nyiso128_treatment``) instead of
the superseded ``nyiso125_seam_A``, because an A/B whose control reproduces a
*superseded* recipe is exactly the stale-baseline defect that fired nyiso-128's
K6 gate. Two consequences to know before running it: ``--arm control`` now
reproduces the **solar-basis keeper** (that flag is in the keeper's own recorded
override block), so ``--arm treatment`` is a no-op duplicate of it; and a NEW
lever is armed with ``--override FIELD=VALUE`` rather than by editing this file.

The NYISO keeper was **not produced by the documented CLI** — nyiso-127 recorded the same finding when it discovered
``--nyiso-seam-deliverability-envelope`` had no argparse path at all. Thirteen
of the keeper's non-default ``ScenarioConfig`` fields have no CLI flag and are
not built into ``run_calibration_full.main``'s ``prb_overrides`` dict; they
reach the solve only through that dict's **generic override channel**
(``run_calibration_full.py:3465`` applies it wholesale via
``config.with_overrides``).

So the faithful reproduction is not a guessed command line — it is the keeper's
**own recorded provenance block**, ``run_config.json ->
calibration_flags.coal_prb_sigmoid_overrides`` (31 entries), replayed through
the same entry point. This driver:

1. runs ``main()`` with the CLI-expressible half of the recipe, intercepting
   :func:`solve_and_persist` to capture every kwarg the CLI path would pass
   (so nothing drifts from the documented plumbing);
2. merges the keeper's recorded 31-entry override dict into the captured
   ``prb_overrides``, which is what supplies the thirteen CLI-less fields;
3. optionally arms ``nyiso_solar_market_generator_basis`` (the treatment); and
4. calls :func:`solve_and_persist` for real.

Kill gate **K6** (PREREG §7) is what validates this: the control must reproduce
the keeper's C3a to ±0.2 pp. ``--verify-only`` runs a short-hours solve and
diffs the emitted ``scenario_config`` against the keeper's, so a recipe defect
is caught in minutes instead of after a multi-hour solve.

Usage::

    python scripts/probes/_nyiso128_solve_ab.py --arm control --verify-only
    python scripts/probes/_nyiso128_solve_ab.py --arm control   --years 2023 2024 2025
    python scripts/probes/_nyiso128_solve_ab.py --arm control --years 2023 2024 2025 \
        --override some_new_lever=true --out-dir results/calibration/nyiso130_B
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

# The DESIGNATED keeper's own run_config — the provenance record every arm is
# built from and verified against. RE-POINTED 2026-08-06 (nyiso-129) from
# nyiso125_seam_A to the newly promoted nyiso128_treatment. Keep this pointing at
# the CURRENT keeper: an A/B whose control reproduces a superseded recipe is the
# stale-baseline failure that fired nyiso-128's K6 gate. Consequence to know
# before using it: the current keeper ALREADY carries
# ``nyiso_solar_market_generator_basis``, so ``--arm control`` now reproduces the
# solar-basis keeper, and ``--arm treatment`` (which sets that same flag) is a
# no-op duplicate of it. A new lever is added with ``--override KEY=VALUE``.
KEEPER_RUN_CONFIG = REPO / "results/calibration/nyiso128_treatment/run_config.json"

# The CLI-expressible half of the keeper recipe. Everything else arrives through
# the recorded override block (see the module docstring).
CLI_RECIPE: list[str] = [
    "--iso", "NYISO",
    "--energy-reserve-coopt",
    "--ramp-limits",
    "--nuclear-unit-availability",
    "--coal-mustrun-per-plant",
    "--coal-drop-pof",
    "--coal-prb-sigmoid",
    "--prb-sigmoid-tiered",
    "--gas-hub-basis-overlay",
    "--gas-hub-basis-daily",
    "--gas-offer-margin",
    "--gas-offer-margin-zonal-anchor",
    "--tranche-startup-amortization",
    "--tranche-startup-measured-runs",
    "--nysdec-peaker-rule",
    "--priced-interchange",
    "--nyiso-dynamic-reserve-requirements",
    "--nyiso-hydro-reserve-eligible",
    "--nyiso-scr-edrp",
    "--nyiso-scr-edrp-reserve-eligible",
    "--nyiso-local-selfsupply",
    "--nyiso-firm-imports",
    "--nyiso-import-reconciliation",
    "--nyiso-import-hub-prices",
    "--nyiso-li-locational-reserve",
    "--nyiso-seam-deliverability-envelope",
    "--nyiso-gas-commitment-bridge",
    "--nyiso-gas-bridge-min-run",
    "--nyiso-gas-bridge-cc-min-run-hours", "21",
    "--nyiso-gas-bridge-st-min-run-hours", "13",
]

# Fields the smoke/verify diff must ignore: set per-year by construction.
_VERIFY_IGNORE = frozenset({"hours", "weather_year", "gas_price_override", "mode"})


def keeper_overrides() -> dict:
    """Return the keeper's recorded generic-override block.

    Returns:
        The ``calibration_flags.coal_prb_sigmoid_overrides`` dict from the
        keeper bundle's ``run_config.json`` — the run's own provenance record
        of every armed non-default toggle.

    Raises:
        FileNotFoundError: if the keeper bundle is not present.
    """
    if not KEEPER_RUN_CONFIG.exists():
        raise FileNotFoundError(f"keeper run_config missing: {KEEPER_RUN_CONFIG}")
    cfg = json.loads(KEEPER_RUN_CONFIG.read_text())
    return dict(cfg["calibration_flags"]["coal_prb_sigmoid_overrides"])


def capture_cli_kwargs(years: list[int], hours: int, out_dir: Path) -> dict:
    """Run ``main()`` far enough to capture the kwargs the CLI path would pass.

    :func:`solve_and_persist` is monkeypatched to record its kwargs and raise,
    so no LP is built. This keeps the driver bound to the documented CLI
    plumbing instead of re-deriving it.

    Args:
        years: Solve years.
        hours: Hours per year.
        out_dir: Bundle root.

    Returns:
        The captured kwargs dict, ready to be amended and re-dispatched.

    Raises:
        RuntimeError: if ``main()`` returned without reaching the solve.
    """
    import scripts.run_calibration_full as rcf

    captured: dict = {}

    class _Stop(Exception):
        """Sentinel raised to unwind main() once the kwargs are captured."""

    def _spy(*args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        raise _Stop

    real = rcf.solve_and_persist
    rcf.solve_and_persist = _spy
    argv = list(sys.argv)
    sys.argv = (
        ["run_calibration_full.py", *CLI_RECIPE,
         "--year", *[str(y) for y in years],
         "--hours", str(hours), "--out-dir", str(out_dir)]
    )
    try:
        rcf.main()
    except _Stop:
        pass
    finally:
        rcf.solve_and_persist = real
        sys.argv = argv
    if "kwargs" not in captured:
        raise RuntimeError("main() never reached solve_and_persist")
    return captured


def verify(out_dir: Path) -> int:
    """Diff a solved bundle's ``scenario_config`` against the keeper's.

    Args:
        out_dir: Bundle root of the just-solved arm.

    Returns:
        Process exit status: 0 when every keeper field is reproduced.
    """
    keeper = json.loads(KEEPER_RUN_CONFIG.read_text())["scenario_config"]
    got = json.loads((out_dir / "run_config.json").read_text())["scenario_config"]
    missing = {
        f: (keeper[f], got.get(f, "<absent>"))
        for f in keeper
        if f not in _VERIFY_IGNORE and got.get(f, "<absent>") != keeper[f]
    }
    if not missing:
        print(f"RECIPE FIDELITY: PASS — all {len(keeper)} keeper fields reproduced")
        return 0
    print(f"RECIPE FIDELITY: FAIL — {len(missing)} field(s) not reproduced")
    for f, (kv, gv) in sorted(missing.items()):
        print(f"  {f}: keeper {kv!r} | got {gv!r}")
    return 1


def main() -> int:
    """Solve one arm of the nyiso-128 A/B on the keeper recipe."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=("control", "treatment"), required=True)
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--hours", type=int, default=8760)
    ap.add_argument("--out-dir", type=Path, default=None)
    ap.add_argument(
        "--verify-only",
        action="store_true",
        help="short-hours solve + config diff against the keeper, no full run",
    )
    ap.add_argument(
        "--override",
        action="append",
        default=[],
        metavar="FIELD=VALUE",
        help=(
            "extra ScenarioConfig field to arm on top of the keeper recipe, "
            "repeatable — the way a NEW lever is A/B'd without editing this file "
            "(VALUE is parsed as JSON, so use true/false/12.5/\"text\"). Note "
            "--verify-only will report each one as a keeper-fidelity difference, "
            "which is the intended reading: it is the arm's single declared delta."
        ),
    )
    args = ap.parse_args()

    hours = 24 if args.verify_only else args.hours
    out_dir = args.out_dir or (
        REPO / "results/calibration" / f"nyiso128_{args.arm}"
    )
    years = [args.years[0]] if args.verify_only else args.years

    cap = capture_cli_kwargs(years, hours, out_dir)
    kwargs = cap["kwargs"]
    overrides = dict(kwargs.get("prb_overrides") or {})
    overrides.update(keeper_overrides())
    if args.arm == "treatment":
        overrides["nyiso_solar_market_generator_basis"] = True
    for item in args.override:
        field, _, raw = item.partition("=")
        if not _:
            raise SystemExit(f"--override needs FIELD=VALUE, got {item!r}")
        try:
            overrides[field.strip()] = json.loads(raw)
        except json.JSONDecodeError:
            overrides[field.strip()] = raw  # bare string, e.g. --override mode=backcast
    kwargs["prb_overrides"] = overrides

    print(f"nyiso-128 {args.arm}: years={years} hours={hours} out={out_dir}")
    print(f"  overrides carried: {len(overrides)} "
          f"(solar basis = {overrides.get('nyiso_solar_market_generator_basis', False)})")

    import scripts.run_calibration_full as rcf

    rcf.solve_and_persist(*cap["args"], **kwargs)
    return verify(out_dir) if args.verify_only else 0


if __name__ == "__main__":
    raise SystemExit(main())
