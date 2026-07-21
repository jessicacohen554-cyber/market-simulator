"""The AEO/IPM-style deterministic scenario matrix (PB-0 / PB-1.1).

Runs a base forecast scenario once per named case in a
:class:`~market_sim.config.scenarios.SweepDefinition` (``cases`` mode --
``configs/scenario_matrix.yaml`` holds the 13 cases from
``docs/handoffs/probability-bounds-plan-2026-07.md`` §1.2) and reports each
case's emissions trajectory plus the min/max envelope across cases.

THIS IS A DETERMINISTIC SCENARIO RANGE, NOT A PROBABILITY BAND (plan §1.3):
no likelihood attaches to any case or to the envelope between them. Every
artifact this module writes carries that label so nothing downstream can
quote it as a probability statement.

Cases are independent solves with no cross-dependency, so they run in
parallel -- but capped at :data:`MAX_CONCURRENT_CASES` (plan §1.3, CLAUDE.md
rule 12/16: a 25-year forecast member is GB-scale and multi-zone ISOs cannot
run more than ~2 concurrent invocations). Each case still solves its own
years strictly sequentially (``run_scenario_iso``'s year loop; rule 12).
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from market_sim.config.constants import END_YEAR, START_YEAR
from market_sim.config.scenarios import ScenarioConfig, SweepDefinition
from market_sim.results import cache
from market_sim.results.export import _summarize_year

logger = logging.getLogger(__name__)

# The plan's explicit concurrency cap (§1.3): "one invocation per case
# internally (years sequential), <=2 cases concurrent". Never exceeded even
# if a caller asks for more workers.
MAX_CONCURRENT_CASES = 2

LABEL = "deterministic scenario range -- NOT a probability band"


def matrix_configs(
    base_config: ScenarioConfig, sweep_def: SweepDefinition
) -> dict[str, ScenarioConfig]:
    """Expand a matrix definition into ``{case_name: config}`` onto a base config.

    Args:
        base_config: The forecast scenario every case overrides onto.
        sweep_def: A ``cases``-mode ``SweepDefinition`` (e.g. loaded from
            ``configs/scenario_matrix.yaml``).

    Returns:
        One config per named case, in the YAML's own order.

    Raises:
        ValueError: If ``base_config`` is not in forecast mode (the matrix is
            a forecast tool, matching the weather ensemble's guard), or if
            ``sweep_def`` has no ``cases`` (it is a cartesian sweep, not a
            named-case matrix).
    """
    if base_config.mode != "forecast":
        raise ValueError(
            "the scenario matrix is a forecast tool; base config mode must "
            f"be 'forecast', got {base_config.mode!r}. A backcast pins a "
            "single historical year by design (CLAUDE.md forecast/backcast "
            "split; rule 22 holdout quarantine)."
        )
    return sweep_def.case_configs(base_config)


def run_matrix(
    configs: dict[str, ScenarioConfig],
    iso: str,
    workers: int | None = None,
) -> dict[str, str]:
    """Run one forecast per named case and return each case's cache key.

    Args:
        configs: Map of case name to config (see :func:`matrix_configs`).
        iso: ISO identifier every case runs against.
        workers: Concurrent worker processes, hard-capped at
            :data:`MAX_CONCURRENT_CASES` regardless of the requested value.
            Defaults to the cap. ``1`` runs cases in-process.

    Returns:
        A dict mapping each case name to the ``cache_key`` of its run.
    """
    # Public picklable worker entry point; local import mirrors ensemble.py
    # (runner.py imports this module for its CLI subcommand — api delegates
    # to runner lazily, so there is no module-load cycle).
    from market_sim.pipeline.api import run_pair

    iso = iso.upper()
    if not configs:
        raise ValueError("configs must be non-empty")

    workers = (
        MAX_CONCURRENT_CASES if workers is None else min(workers, MAX_CONCURRENT_CASES)
    )

    names = list(configs.keys())
    pairs = [(configs[name], iso) for name in names]

    logger.info("run_matrix start: iso=%s cases=%s workers=%d", iso, names, workers)

    if workers == 1:
        keys = [run_pair(pair) for pair in pairs]
    else:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            keys = list(executor.map(run_pair, pairs))

    return dict(zip(names, keys))


def build_matrix_frame(iso: str, members: dict[str, str]) -> pd.DataFrame:
    """Load every case's cached results and build the long-format trajectory table.

    Args:
        iso: ISO identifier the members were run for.
        members: Map of case name to ``cache_key`` (the return value of
            :func:`run_matrix`).

    Returns:
        A long-format DataFrame with columns ``case``, ``year``,
        ``emissions_mt``, ``cache_key``, ``label`` -- one row per
        (case, year) actually cached (a partial/smoke run's missing years
        are simply absent, not an error).
    """
    iso = iso.upper()
    rows: list[dict] = []
    for case, key in members.items():
        for year in range(START_YEAR, END_YEAR + 1):
            if not cache.is_cached(iso, key, year):
                continue
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            summary = _summarize_year(result, context)
            rows.append(
                {
                    "case": case,
                    "year": year,
                    "emissions_mt": summary["emissions_mt"],
                    "cache_key": key,
                    "label": LABEL,
                }
            )
    return pd.DataFrame(
        rows, columns=["case", "year", "emissions_mt", "cache_key", "label"]
    )


def compute_envelope(matrix_df: pd.DataFrame) -> pd.DataFrame:
    """Compute the per-year min/max emissions envelope across cases.

    Args:
        matrix_df: A trajectory table from :func:`build_matrix_frame`.

    Returns:
        A DataFrame with columns ``year``, ``min_mt``, ``min_case``,
        ``max_mt``, ``max_case``, ``label``, one row per year present in
        ``matrix_df``.
    """
    if matrix_df.empty:
        return pd.DataFrame(
            columns=["year", "min_mt", "min_case", "max_mt", "max_case", "label"]
        )
    rows = []
    for year, group in matrix_df.groupby("year"):
        min_row = group.loc[group["emissions_mt"].idxmin()]
        max_row = group.loc[group["emissions_mt"].idxmax()]
        rows.append(
            {
                "year": int(year),
                "min_mt": float(min_row["emissions_mt"]),
                "min_case": str(min_row["case"]),
                "max_mt": float(max_row["emissions_mt"]),
                "max_case": str(max_row["case"]),
                "label": LABEL,
            }
        )
    return pd.DataFrame(rows).sort_values("year").reset_index(drop=True)


def matrix_id_for(iso: str, base_config: ScenarioConfig, matrix_path) -> str:
    """Return a deterministic, human-readable id for one matrix run.

    Combines the ISO, the matrix YAML's file stem, and the first 10 hex
    chars of the *base* config's cache key (before any case overrides) --
    the same base run against a different matrix file, or the same matrix
    against a different base, gets a distinct id.
    """
    matrix_name = Path(matrix_path).stem
    return f"{iso.lower()}_{matrix_name}_{base_config.cache_key()[:10]}"


def _write_summary_md(
    path: Path,
    iso: str,
    matrix_id: str,
    matrix_df: pd.DataFrame,
    envelope_df: pd.DataFrame,
    members: dict[str, str],
) -> None:
    """Write the plain-markdown case/envelope summary table."""
    lines = [
        f"# Scenario matrix -- {iso} -- {matrix_id}",
        "",
        f"**{LABEL.upper()}**",
        "",
        "13 named AEO/IPM-style cases (docs/handoffs/probability-bounds-plan-"
        "2026-07.md §1.2), not a factorial sweep and not a sampled "
        "distribution. No likelihood attaches to any case or to the envelope "
        "between them.",
        "",
        "## Cases run",
        "",
        "| Case | Cache key |",
        "|---|---|",
    ]
    for case, key in members.items():
        lines.append(f"| {case} | `{key}` |")

    lines += ["", "## Emissions trajectory (Mt CO2)", ""]
    if matrix_df.empty:
        lines.append("_No cached years yet._")
    else:
        cases = sorted(matrix_df["case"].unique())
        years = sorted(matrix_df["year"].unique())
        pivot = matrix_df.pivot(index="year", columns="case", values="emissions_mt")
        header = "| Year | " + " | ".join(cases) + " |"
        sep = "|---|" + "---|" * len(cases)
        lines += [header, sep]
        for year in years:
            row = [
                f"{pivot.loc[year, c]:.2f}" if c in pivot.columns else "" for c in cases
            ]
            lines.append(f"| {year} | " + " | ".join(row) + " |")

    lines += ["", "## Envelope (min/max across cases)", ""]
    if envelope_df.empty:
        lines.append("_No cached years yet._")
    else:
        lines += ["| Year | Min Mt (case) | Max Mt (case) |", "|---|---|---|"]
        for _, row in envelope_df.iterrows():
            lines.append(
                f"| {int(row['year'])} | {row['min_mt']:.2f} ({row['min_case']}) "
                f"| {row['max_mt']:.2f} ({row['max_case']}) |"
            )

    path.write_text("\n".join(lines) + "\n")


def write_matrix_outputs(
    iso: str,
    base_config: ScenarioConfig,
    matrix_path,
    members: dict[str, str],
    out_dir=None,
) -> Path:
    """Load cached case results and write the matrix output bundle.

    Writes ``matrix.parquet`` (per-case trajectory), ``envelope.parquet``
    (per-year min/max across cases), ``summary.md`` (human-readable table),
    and ``meta.json`` (matrix id, label, cases-to-cache-key map, base config).
    Every file carries the deterministic-scenario-range label (plan §1.3,
    §4.2).

    Args:
        iso: ISO identifier the members were run for.
        base_config: The base forecast config the cases overrode onto.
        matrix_path: Path to the matrix YAML that produced ``members``.
        members: Map of case name to cache key (:func:`run_matrix`'s return).
        out_dir: Output directory; defaults to
            ``results/ensemble/<matrix_id>/``.

    Returns:
        The output directory written to.
    """
    iso = iso.upper()
    matrix_id = matrix_id_for(iso, base_config, matrix_path)
    out_dir = (
        Path(out_dir) if out_dir is not None else Path("results/ensemble") / matrix_id
    )
    out_dir.mkdir(parents=True, exist_ok=True)

    matrix_df = build_matrix_frame(iso, members)
    envelope_df = compute_envelope(matrix_df)

    matrix_df.to_parquet(out_dir / "matrix.parquet", index=False)
    envelope_df.to_parquet(out_dir / "envelope.parquet", index=False)
    _write_summary_md(
        out_dir / "summary.md", iso, matrix_id, matrix_df, envelope_df, members
    )

    meta = {
        "matrix_id": matrix_id,
        "iso": iso,
        "label": LABEL,
        "matrix_path": str(matrix_path),
        "cases": members,
        "base_config": asdict(base_config),
        "years_present": sorted(int(y) for y in matrix_df["year"].unique())
        if not matrix_df.empty
        else [],
    }
    (out_dir / "meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True))

    logger.info(
        "write_matrix_outputs: iso=%s matrix_id=%s cases=%d out_dir=%s",
        iso,
        matrix_id,
        len(members),
        out_dir,
    )
    return out_dir


def run_matrix_cli(
    config_path,
    matrix_path,
    iso: str | None = None,
    workers: int | None = None,
    out_dir=None,
) -> Path:
    """End-to-end entry point for the ``market-sim matrix`` subcommand.

    Loads the base config and matrix definition, runs every case (capped at
    :data:`MAX_CONCURRENT_CASES` concurrent), and writes the output bundle.

    Args:
        config_path: Path to the base forecast scenario YAML.
        matrix_path: Path to a ``cases``-mode sweep YAML
            (e.g. ``configs/scenario_matrix.yaml``).
        iso: ISO identifier; defaults to the base config's own ISO.
        workers: Concurrent worker processes; see :func:`run_matrix`.
        out_dir: Output directory; defaults to
            ``results/ensemble/<matrix_id>/``.

    Returns:
        The output directory written to.
    """
    base_config = ScenarioConfig.from_yaml(config_path)
    iso = (iso or base_config.iso).upper()
    sweep_def = SweepDefinition.from_yaml(matrix_path)

    configs = matrix_configs(base_config, sweep_def)
    members = run_matrix(configs, iso, workers)
    return write_matrix_outputs(iso, base_config, matrix_path, members, out_dir)
