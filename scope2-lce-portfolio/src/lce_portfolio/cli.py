"""Command-line entry point for the LCE portfolio optimizer.

Usage::

    python -m lce_portfolio --load load.csv --lmp bau_lmp.csv --iso SAMPLE \
        --deltas 1 2 5 7 10 20 --out-dir data/outputs

    # or drive a run entirely from a config file (ADR 0010/0011 load_file /
    # lmp_file fields), batching every ISO in the load file:
    python -m lce_portfolio --config run.json --all-isos --out-dir data/outputs

    # persist a run into the committed results store (ADR 0014 §5):
    python -m lce_portfolio --config run.json --results --run-id my_run

Reads a load-intake file and an LMP file, runs the premium sweep (Mode A by
default), writes Parquet outputs + run metadata, and prints a summary. Every
run also emits the ADR 0014 report (``report.json`` + ``report.html``; opt
out with ``--no-report``, size-tune with ``--report-hourly``); ``--results``
persists the whole run under ``results/<run-id>/`` instead of the gitignored
``--out-dir`` default. Fully standalone — no ``market_sim`` import.
Validation errors (bad schema, missing hours, unknown ISO) are reported as a
single clean message, not a traceback.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

from lce_portfolio.config import PortfolioConfig
from lce_portfolio.intake import (
    load_intake,
    prepare_emission_rate,
    prepare_lmp,
    prepare_load,
)
from lce_portfolio.outputs import summarize, write_outputs, write_report
from lce_portfolio.profiles import build_cf_matrix, profile_source
from lce_portfolio.resources import load_resource_arrays
from lce_portfolio.sweep import run_sweep

#: Root of the committed per-run results store (ADR 0014 §5), relative to the
#: working directory (the tool is run from ``scope2-lce-portfolio/``).
#: ``data/outputs/`` stays the gitignored ad-hoc default.
RESULTS_ROOT = Path("results")

#: Safe results-store run ids (ADR 0014 §5): one path component, starting with
#: an alphanumeric — no separators, no leading dot, no whitespace. Anything
#: else could make ``RESULTS_ROOT / run_id`` escape the store (an absolute or
#: ``../`` id resolves outside ``results/``), which is then ``rmtree``'d.
_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")


def validate_run_id(run_id: str) -> str:
    """Return ``run_id`` if it is a single safe path component, else raise.

    Guards the ``--results`` store: ``results/<run-id>/`` is deleted before
    being rewritten, so a run id containing a path separator, ``..``, an
    absolute path, or whitespace must never reach that composition
    (audit findings IO-1/CL-2).
    """
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError(
            f"invalid --run-id {run_id!r}: must be a single path component "
            "of letters, digits, '.', '_' or '-', starting with a letter or "
            "digit (no separators, spaces, or leading dot)"
        )
    return run_id


def compose_run_id(isos: list[str], mode: str, now: datetime | None = None) -> str:
    """Compose the default run id ``<iso|multi>_<mode>_<YYYYMMDD-HHMMSS>``
    (ADR 0014 §5); multi-ISO batches use the literal ``multi``."""
    stamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    iso_part = isos[0] if len(isos) == 1 else "multi"
    return f"{iso_part}_{mode}_{stamp}"


#: Default Mode A premium caps when neither --deltas nor a config file sets
#: them ($/MWh; the sample-sweep ladder).
DEFAULT_DELTAS = (1.0, 2.0, 5.0, 7.0, 10.0, 20.0)
#: Default Mode B matching targets when --targets is given with no values via
#: config (fractions of annual load).
DEFAULT_TARGETS = (0.8, 0.9, 1.0)


def build_config(args: argparse.Namespace) -> PortfolioConfig:
    """Assemble a base :class:`PortfolioConfig` from a file and/or CLI args.

    ``--config`` provides the base (including its ``load_file``/``lmp_file``,
    ADR 0010/0011); explicitly-given sweep flags (``--deltas``/``--targets``/
    ``--sensitivity``/``--load-growth-*``/``--storage-charge-policy``) then
    override the file values
    (audit finding CL-1 — they were previously discarded silently; the
    argparse defaults are ``None`` sentinels so "explicitly given" is
    detectable). ISO selection is always CLI. Without ``--config`` the flags
    (or their documented defaults) build the whole config.
    """
    overrides: dict = {}
    if args.targets is not None:
        overrides["mode"] = "matching_target"
        overrides["matching_targets"] = tuple(args.targets)
    elif args.deltas is not None:
        overrides["mode"] = "premium_cap"
    if args.deltas is not None:
        overrides["premium_deltas"] = tuple(args.deltas)
    if args.sensitivity is not None:
        overrides["lcoe_sensitivity"] = args.sensitivity
    if args.load_growth_rate is not None:
        overrides["load_growth_rate"] = args.load_growth_rate
    if args.load_growth_years is not None:
        overrides["load_growth_years"] = args.load_growth_years
    if args.storage_charge_policy is not None:
        overrides["storage_charge_policy"] = args.storage_charge_policy

    if args.config:
        base = PortfolioConfig.from_file(args.config)
        return base.with_overrides(**overrides) if overrides else base
    return PortfolioConfig(
        iso=args.iso or "SAMPLE",
        mode=overrides.get("mode", "premium_cap"),
        premium_deltas=overrides.get("premium_deltas", DEFAULT_DELTAS),
        matching_targets=overrides.get("matching_targets", DEFAULT_TARGETS),
        lcoe_sensitivity=overrides.get("lcoe_sensitivity", "mid"),
        load_growth_rate=overrides.get("load_growth_rate", 0.0),
        load_growth_years=overrides.get("load_growth_years", 0),
        storage_charge_policy=overrides.get("storage_charge_policy", "arbitrage"),
    )


def run_one_iso(
    config: PortfolioConfig,
    load_path: str | Path,
    lmp_path: str | Path,
    out_dir: str | Path,
    emissions_path: str | Path | None = None,
    *,
    report: bool = True,
    run_id: str | None = None,
    report_hourly: str = "selected",
):
    """Run the full pipeline for a single ISO (``config.iso``) and write outputs.

    ``emissions_path`` is the optional hourly fossil-average CO2-rate file
    (ADR 0013, ``(hour, iso, fossil_avg_co2_rate)``); when absent,
    residual-carbon reporting is off (``residual_co2_tons == 0``), mirroring
    the pre-carbon SAMPLE behavior.

    ``report``/``run_id``/``report_hourly`` thread through to
    :func:`~lce_portfolio.outputs.write_outputs` (ADR 0014 §6): by default a
    single-ISO call also emits ``report.json`` + ``report.html``; the CLI's
    batch path passes ``report=False`` here and writes one combined report for
    the whole run instead. Returns the solved
    :class:`~lce_portfolio.sweep.SweepResult` so callers can assemble that
    batch report.
    """
    resources = load_resource_arrays(config)
    load = prepare_load(load_path, config.iso, config)
    lmp = prepare_lmp(lmp_path, config.iso)
    emission_rate = (
        prepare_emission_rate(emissions_path, config.iso) if emissions_path else None
    )
    # profile_shape_year decouples the CF-profile vintage from the modeled
    # `year` (config.py docstring); when set, a missing file is a hard error
    # instead of the default warn-and-synthetic-fallback.
    shape_year = (
        config.profile_shape_year
        if config.profile_shape_year is not None
        else config.year
    )
    cf = build_cf_matrix(
        resources,
        config.iso,
        shape_year,
        required=config.profile_shape_year is not None,
    )
    # Real-vs-synthetic shape provenance for the metadata sidecar (audit
    # finding DL-8): a synthetic-shaped run must be identifiable from its
    # outputs, not just a transient stderr warning.
    shape_source = profile_source(config.iso, shape_year)

    sweep = run_sweep(config, resources, load, lmp, cf, emission_rate=emission_rate)
    paths = write_outputs(
        sweep,
        out_dir,
        config=config,
        report=report,
        run_id=run_id,
        report_hourly=report_hourly,
        metadata_extra={"profile_source": shape_source},
    )
    print(summarize(sweep))
    print("wrote: " + "  ".join(str(v) for v in paths.values()) + "\n")
    return sweep


def _isos_in_load(load_path: str | Path) -> list[str]:
    """Distinct ISO names present in the load-intake file."""
    return sorted(load_intake(load_path)["iso"].unique().tolist())


def _errmsg(exc: BaseException) -> str:
    """Render an exception for the CLI without str(KeyError)'s repr quotes.

    ``str(KeyError("msg"))`` is ``'"msg"'`` — spurious double quotes around an
    otherwise good message (audit finding CL-8).
    """
    if isinstance(exc, KeyError) and exc.args:
        return str(exc.args[0])
    return str(exc)


def main(argv: list[str] | None = None) -> int:
    """Parse args, run the sweep for one or all ISOs, write outputs.

    The load/LMP/emissions file paths come from ``--load``/``--lmp``/
    ``--emissions`` if given, else from ``config.load_file``/``config.lmp_file``/
    ``config.emissions_file`` (ADR 0010/0011/0012); a missing load or LMP path
    is a clean CLI error, not a traceback, while a missing emissions path just
    leaves residual-carbon reporting off.
    """
    p = argparse.ArgumentParser(description="Scope 2 hourly LCE portfolio optimizer")
    p.add_argument("--load", default=None, help="load-intake CSV/Parquet")
    p.add_argument("--lmp", default=None, help="BAU LMP CSV/Parquet")
    p.add_argument(
        "--emissions",
        default=None,
        help="hourly fossil-average CO2-rate CSV/Parquet (ADR 0013, optional)",
    )
    p.add_argument("--iso", default=None, help="ISO to run (or use --all-isos)")
    p.add_argument(
        "--all-isos", action="store_true", help="run every ISO in the load file"
    )
    p.add_argument("--config", default=None, help="JSON/YAML config file (base config)")
    p.add_argument(
        "--deltas",
        type=float,
        nargs="+",
        default=None,
        help="premium caps $/MWh (Mode A; default 1 2 5 7 10 20). Sweep flags "
        "override --config values when both are given.",
    )
    p.add_argument(
        "--targets",
        type=float,
        nargs="+",
        default=None,
        help="matching targets (switches to Mode B; overrides --config)",
    )
    p.add_argument(
        "--sensitivity",
        choices=["low", "mid", "high"],
        default=None,
        help="LCOE sensitivity column (default mid; overrides --config)",
    )
    p.add_argument("--load-growth-rate", type=float, default=None)
    p.add_argument("--load-growth-years", type=int, default=None)
    p.add_argument(
        "--storage-charge-policy",
        choices=["arbitrage", "excess_clean_only"],
        default=None,
        help="storage grid interaction (ADR 0017): arbitrage (default) lets "
        "storage charge from the grid and export discharge at LMP; "
        "excess_clean_only restricts charging to the portfolio's excess "
        "contracted clean generation (no grid trading; overrides --config)",
    )
    p.add_argument("--out-dir", default="data/outputs")
    p.add_argument(
        "--no-report",
        action="store_true",
        help="suppress report.json + report.html (emitted by default, ADR 0014 §6)",
    )
    p.add_argument(
        "--run-id",
        default=None,
        help="run id for the report/results folder; default composes "
        "<iso|multi>_<mode>_<YYYYMMDD-HHMMSS> (ADR 0014 §5)",
    )
    p.add_argument(
        "--results",
        action="store_true",
        help="persist into the committed results/<run-id>/ store instead of "
        "--out-dir; re-using a run id overwrites its directory (ADR 0014 §5)",
    )
    p.add_argument(
        "--report-hourly",
        choices=["selected", "all"],
        default="selected",
        help="which setpoints get §2.7 hourly series in the report payload "
        "(ADR 0014 §3 size discipline)",
    )
    args = p.parse_args(argv)

    if not args.all_isos and not (args.iso or args.config):
        p.error("specify --iso, --all-isos, or a --config with an iso")

    try:
        base = build_config(args)
        load_path = args.load or base.load_file
        lmp_path = args.lmp or base.lmp_file
        # Optional (ADR 0013): no emissions file means residual-carbon
        # reporting stays off, so this is never a CLI error.
        emissions_path = args.emissions or base.emissions_file
        if not load_path:
            p.error("specify --load or set load_file in --config")
        if not lmp_path:
            p.error("specify --lmp or set lmp_file in --config")

        isos = _isos_in_load(load_path) if args.all_isos else [args.iso or base.iso]
        if not isos:
            # Backstop for CL-9: a header-only load file must not become a
            # silent exit-0 no-op (load_intake also rejects it upstream).
            raise ValueError(f"load file {load_path} contains no data rows")

        # Resolve the run directory + id (ADR 0014 §5): --results composes
        # results/<run-id>/ (committed store; re-using an id overwrites its
        # directory), while --out-dir stays the gitignored ad-hoc default.
        run_id = validate_run_id(args.run_id or compose_run_id(isos, base.mode))
        if args.results:
            # Write into a scratch sibling and swap only on success (audit
            # findings IO-7/CL-3): deleting results/<run-id>/ up front meant a
            # failed re-run destroyed the previous good results and could
            # leave a partial directory behind.
            final_dir = RESULTS_ROOT / run_id
            out_dir = RESULTS_ROOT / f"{run_id}.tmp"
            if out_dir.exists():
                shutil.rmtree(out_dir)
        else:
            final_dir = None
            out_dir = Path(args.out_dir)

        # Per-ISO Parquet + metadata are written inside the loop; the report
        # is one per run (single or batch — §2.6), written after it. In an
        # --all-isos batch a failing ISO no longer aborts the run (audit
        # finding CL-7): it is recorded, the others still solve, and the
        # combined report covers the successes.
        sweeps, configs, failures = [], [], []
        for iso in isos:
            config = base.with_overrides(iso=iso)
            try:
                sweep = run_one_iso(
                    config,
                    load_path,
                    lmp_path,
                    out_dir,
                    emissions_path=emissions_path,
                    report=False,
                )
            except (ValueError, KeyError, OSError) as exc:
                if not args.all_isos:
                    raise
                failures.append(iso)
                print(f"ISO {iso}: FAILED — {_errmsg(exc)}", file=sys.stderr)
                continue
            sweeps.append(sweep)
            configs.append(config)
        if not args.no_report and sweeps:
            paths = write_report(
                sweeps,
                configs,
                out_dir,
                run_id=run_id,
                report_hourly=args.report_hourly,
            )
            print("report: " + "  ".join(str(v) for v in paths.values()))
        if final_dir is not None and sweeps:
            # Atomic-ish publish: the previous run directory is replaced only
            # after the whole new run (all ISOs + report) has been written.
            if final_dir.exists():
                shutil.rmtree(final_dir)
            out_dir.rename(final_dir)
            print(f"results: {final_dir}")
        if failures:
            print(
                f"{len(failures)} of {len(isos)} ISO(s) failed: " + ", ".join(failures),
                file=sys.stderr,
            )
            return 1
        if not sweeps:
            print("error: no ISO produced results", file=sys.stderr)
            return 1
        # Every setpoint infeasible/failed is a run failure, not a quiet
        # success (audit finding CL-4) — the rows are flagged in summarize().
        if all(r.status != "Optimal" for s in sweeps for r in s.results):
            print(
                "error: no setpoint solved to optimality (all infeasible or "
                "failed — see the flagged rows above)",
                file=sys.stderr,
            )
            return 1
    except (ValueError, KeyError, OSError) as exc:
        # OSError covers FileNotFoundError plus e.g. IsADirectoryError from a
        # directory passed as --load/--lmp (audit finding CL-13).
        print(f"error: {_errmsg(exc)}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
