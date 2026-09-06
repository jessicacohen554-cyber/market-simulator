#!/usr/bin/env python
"""Roll a scenario campaign up across the modeled ISOs (SCN-WS0 deliverable 3).

Closes G-E2 (``docs/handoffs/forecast-scenario-readiness-plan-2026-09.md``
§2.5): ``collate_full_horizon.py`` writes one row per ISO and never sums, so
"what does this case do to system-wide emissions" had no artifact.

Reads every ``<root>/<iso>/<case>/full_horizon_summary.json`` written by
``run_full_horizon.py`` (any nesting works — the summary names its own ISO and
the directory holding it names the case) and emits:

    campaign_emissions_by_iso.csv     per (case, iso, year) CO2 + side lines
    campaign_emissions_system.csv     per (case, year) summed across ISOs
    campaign_delta_table.csv          case-vs-reference deltas, per ISO and summed
    campaign_report.md                the headline tables + the disclosure block

WHAT THE SUM IS, AND WHAT IT IS NOT (plan §3.0). The total is the
:data:`SYSTEM_LABEL` — the six modeled ISOs, roughly two thirds of US load. It
is **never** labelled "national": SPP, the Southeast and the non-ISO West are
outside the model and stay outside the number. Three side lines ride beside
the total and are **never added into it**:

  (i)   import-attributed CO2 — the LP holds import emission rates at zero by
        design, so a case that shifts imports moves real emissions the total
        cannot see (G-E3);
  (ii)  unserved energy in MWh — a case whose CO2 falls while unserved energy
        rises has not decarbonized;
  (iii) the ISOs *not* modeled, and any of the six missing from this campaign.

CO2 levels come from each summary's own ``trajectory[].co2_mt``, so the
campaign total is the same quantity the forecast dashboard already reports.
The two side lines are not in the summary schema, so they are reconstructed
from the run's cached year parquets through the shared
``results/export.py::_summarize_year`` seam — the same code path every other
delta table uses. A run whose cache has been pruned reports its CO2 level and
a blank side line, never a silent zero.

Pure post-processing: it never solves, tunes, or changes a threshold.

Usage::

    python scripts/collate_scenario_campaign.py --root results/<campaign> \\
        [--reference-case REF] [--out-dir results/<campaign>/_rollup]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from market_sim.config.iso_configs import SUPPORTED_ISOS  # noqa: E402
from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.results.emissions import IMPORT_CO2_DISCLOSURE  # noqa: E402
from market_sim.results.export import _summarize_year  # noqa: E402

# Importing results.outputs attaches ``DispatchResult.from_parquet`` and
# ``read_fleet_context`` (late-bound in that module) — same reason
# collate_full_horizon.py imports it explicitly.
from market_sim.results.outputs import read_fleet_context  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("collate_scenario_campaign")

ISO_ORDER = list(SUPPORTED_ISOS)

#: What the campaign total is allowed to be called. Never "national" — the
#: model covers six ISOs, not the country (plan §3.0).
SYSTEM_LABEL = "six-ISO modeled system"

#: Value of the delta table's ``delta_coverage`` column when a row's two
#: operands span exactly the same ISO set — i.e. nothing had to be dropped to
#: make the difference well-formed.
COVERAGE_FULL = "full"

#: The (iii) side line: what is outside the number, stated every time it is
#: printed so no reader can mistake the total for a US figure.
NOT_MODELED_NOTE = (
    "Outside this total: SPP, the Southeast (Southern/TVA/Duke and the rest of "
    "SERC), and the non-ISO West (the WECC balancing areas outside CAISO). The "
    "six modeled ISOs are roughly two thirds of US load; the remaining third is "
    "not modeled and is not estimated here."
)


def discover_summaries(root: Path) -> list[tuple[str, str, Path]]:
    """Find every ``full_horizon_summary.json`` under ``root``.

    Args:
        root: The campaign root, conventionally ``results/<campaign>/``.

    Returns:
        ``(iso, case, path)`` triples sorted by ISO order then case. The ISO
        is read from the summary itself (never guessed from the path) and the
        case is the name of the directory holding the summary.
    """
    found: list[tuple[str, str, Path]] = []
    for path in sorted(root.rglob("full_horizon_summary.json")):
        try:
            iso = str(json.loads(path.read_text())["iso"]).upper()
        except (json.JSONDecodeError, KeyError, OSError) as exc:
            logger.warning("skipping %s: %s", path, exc)
            continue
        found.append((iso, path.parent.name, path))
    order = {iso: i for i, iso in enumerate(ISO_ORDER)}
    return sorted(found, key=lambda t: (order.get(t[0], len(order)), t[1]))


def side_lines_for_run(run_dir: Path | None) -> dict[int, dict[str, float]]:
    """Reconstruct the per-year side lines from a run's cached parquets.

    Args:
        run_dir: The summary's ``run_dir`` (the scenario cache directory), or
            ``None`` when the summary carries none.

    Returns:
        ``{year: {"import_co2_mt_reported": ..., "unserved_mwh": ...}}`` for
        every cached final-pass year. Empty when the cache is absent or
        pruned — the caller then reports a blank side line rather than a zero.
    """
    out: dict[int, dict[str, float]] = {}
    if run_dir is None or not run_dir.exists():
        return out
    for pq in sorted(run_dir.glob("year_*.parquet")):
        if pq.stem.endswith("_p1"):
            continue
        try:
            year = int(pq.stem.replace("year_", ""))
        except ValueError:
            continue
        try:
            summary = _summarize_year(
                DispatchResult.from_parquet(pq), read_fleet_context(pq)
            )
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("no side lines for %s: %s", pq, exc)
            continue
        out[year] = {
            "import_co2_mt_reported": summary["import_co2_mt_reported"],
            "unserved_mwh": summary["unserved_mwh"],
        }
    return out


def order_isos(isos) -> list[str]:
    """Sort ISO names into :data:`ISO_ORDER`, unknown names last.

    Args:
        isos: Any iterable of ISO names; duplicates are preserved.

    Returns:
        The names in registry order.
    """
    return sorted(isos, key=lambda i: ISO_ORDER.index(i) if i in ISO_ORDER else 99)


def build_iso_frame(summaries: list[tuple[str, str, Path]]) -> pd.DataFrame:
    """Build the long per-(case, iso, year) frame from the campaign summaries.

    Args:
        summaries: The triples from :func:`discover_summaries`.

    Returns:
        A frame with columns ``case``, ``iso``, ``year``, ``emissions_mt``,
        ``import_co2_mt_reported``, ``unserved_mwh``, ``cache_key``. Side-line
        columns are NaN where the run's cache is gone.
    """
    rows: list[dict] = []
    for iso, case, path in summaries:
        summary = json.loads(path.read_text())
        run_dir = summary.get("run_dir")
        sides = side_lines_for_run(Path(run_dir) if run_dir else None)
        for entry in summary.get("trajectory") or []:
            year = int(entry["year"])
            side = sides.get(year, {})
            rows.append(
                {
                    "case": case,
                    "iso": iso,
                    "year": year,
                    "emissions_mt": entry.get("co2_mt"),
                    "import_co2_mt_reported": side.get("import_co2_mt_reported"),
                    "unserved_mwh": side.get("unserved_mwh"),
                    "cache_key": summary.get("cache_key"),
                }
            )
    return pd.DataFrame(
        rows,
        columns=[
            "case",
            "iso",
            "year",
            "emissions_mt",
            "import_co2_mt_reported",
            "unserved_mwh",
            "cache_key",
        ],
    )


def build_system_frame(iso_frame: pd.DataFrame) -> pd.DataFrame:
    """Sum the per-ISO frame to the modeled-system total, per (case, year).

    The sum spans THE ISOs PRESENT, which is not necessarily all six — the
    ``isos`` and ``n_isos`` columns say which, so a partial campaign can never
    be read as the whole system by accident.

    Args:
        iso_frame: The frame from :func:`build_iso_frame`.

    Returns:
        A frame with ``case``, ``year``, ``emissions_mt``,
        ``import_co2_mt_reported``, ``unserved_mwh``, ``n_isos``, ``isos``,
        ``isos_missing`` and ``label``. The side lines are summed only where
        EVERY contributing ISO reported one; a partial side line reads NaN
        rather than a total that silently omits an ISO.
    """
    if iso_frame.empty:
        return pd.DataFrame(
            columns=[
                "case",
                "year",
                "emissions_mt",
                "import_co2_mt_reported",
                "unserved_mwh",
                "n_isos",
                "isos",
                "isos_missing",
                "label",
            ]
        )
    rows: list[dict] = []
    for (case, year), group in iso_frame.groupby(["case", "year"]):
        isos = order_isos(group["iso"].unique())
        rows.append(
            {
                "case": case,
                "year": int(year),
                "emissions_mt": round(float(group["emissions_mt"].sum()), 4),
                "import_co2_mt_reported": (
                    round(float(group["import_co2_mt_reported"].sum()), 4)
                    if group["import_co2_mt_reported"].notna().all()
                    else float("nan")
                ),
                "unserved_mwh": (
                    round(float(group["unserved_mwh"].sum()), 3)
                    if group["unserved_mwh"].notna().all()
                    else float("nan")
                ),
                "n_isos": len(isos),
                "isos": "+".join(isos),
                "isos_missing": "+".join(i for i in ISO_ORDER if i not in isos),
                "label": SYSTEM_LABEL,
            }
        )
    return pd.DataFrame(rows).sort_values(["case", "year"]).reset_index(drop=True)


def _coverage_note(
    case: str,
    reference_case: str,
    common: list[str],
    ref_isos: list[str],
    case_isos: list[str],
) -> str:
    """Say, in the row's own words, which ISO set the delta was computed on.

    Args:
        case: The case the row belongs to.
        reference_case: The case the delta is measured against.
        common: The ISOs both cases carry, in registry order.
        ref_isos: The reference case's ISOs, in registry order.
        case_isos: This case's ISOs, in registry order.

    Returns:
        :data:`COVERAGE_FULL` when the two operands span the same system, else
        a sentence naming every ISO that had to be dropped and from which side.
    """
    if not common:
        return f"NO DELTA - no ISO in common with {reference_case}"
    ref_only = [i for i in ref_isos if i not in common]
    case_only = [i for i in case_isos if i not in common]
    if not ref_only and not case_only:
        return COVERAGE_FULL
    parts = []
    if ref_only:
        parts.append(f"{'+'.join(ref_only)} in {reference_case} but not in {case}")
    if case_only:
        parts.append(f"{'+'.join(case_only)} in {case} but not in {reference_case}")
    return "COMMON-SET ONLY (" + "; ".join(parts) + ")"


def _system_delta_rows(
    iso_frame: pd.DataFrame, system_frame: pd.DataFrame, reference_case: str
) -> list[dict]:
    """The system-scope rows of the delta table, on the COMMON ISO set.

    The defect this exists to prevent (routed by SCN-WS5A-LOAD,
    ``docs/handoffs/STATUS-scn-ws5a-load-2026-09-06.md`` "Routed defect"): the
    system-scope delta used to be *(sum over the case's ISOs)* minus *(sum over
    the reference case's ISOs)* with nothing restricting the two to the same
    system, so a case with a legitimately degenerate arm differenced against a
    reference with wider coverage by exactly the missing ISOs' levels. Measured
    on the ``scn-campaign-load-2026-09-06`` artifacts: ``LOAD-HI-ORGANIC``
    covered {ERCOT, NYISO} while ``REF`` covered {ERCOT, NEISO, NYISO}, and the
    2030 system delta read **+5.4620 Mt** where the common-set answer is
    **+18.8300 Mt** — a 71 % understatement equal to NEISO's REF level. This is
    structural, not a partial-campaign transient: PJM and NEISO ship
    ``LOAD-HI == LOAD-HI-ORGANIC`` byte-for-byte, so their ORGANIC arm is
    correctly never solved and every full campaign hits it.

    So BOTH operands are restricted to ``isos(case) ∩ isos(reference_case)``
    before summing, the row is labelled with that intersection
    (``delta_isos`` / ``delta_n_isos``), and ``delta_coverage`` says when the
    intersection is a strict subset of either side's ISO set. A row with no
    common ISO at all emits NaN, never a computable-looking number over
    mismatched systems.

    ``emissions_mt`` and ``emissions_mt_ref`` are therefore restricted the same
    way, so ``delta = emissions_mt − emissions_mt_ref`` holds *within the row*
    for a reader who subtracts. The unrestricted level — the campaign total over
    whatever ISOs a case actually carries — is unchanged and stays in
    ``campaign_emissions_system.csv`` beside its own ``isos`` / ``isos_missing``
    columns.

    Args:
        iso_frame: Per-(case, iso, year) frame.
        system_frame: Per-(case, year) frame, which enumerates the system-scope
            (case, year) rows to emit.
        reference_case: The case every delta is measured against.

    Returns:
        One row dict per system-scope (case, year).
    """
    present: dict[tuple[str, int], list[str]] = {}
    level: dict[tuple[str, int, str], float] = {}
    for row in iso_frame.itertuples(index=False):
        key = (row.case, int(row.year))
        present.setdefault(key, []).append(row.iso)
        # First-wins, matching the drop_duplicates this replaced: a campaign
        # tree holding two summaries for one (case, iso, year) is pathological,
        # and the pre-repair table resolved it the same way.
        level.setdefault((row.case, int(row.year), row.iso), row.emissions_mt)

    def _sum(case: str, year: int, isos: list[str]) -> float:
        # NaN-skipping, exactly as ``build_system_frame``'s group sum is, so a
        # full-coverage system delta reads off the same arithmetic as the level.
        vals = [level.get((case, year, iso)) for iso in isos]
        return round(float(pd.Series(vals, dtype="float64").sum()), 4)

    rows: list[dict] = []
    for row in system_frame.itertuples(index=False):
        case, year = row.case, int(row.year)
        case_isos = order_isos(present.get((case, year), []))
        ref_isos = order_isos(present.get((reference_case, year), []))
        common = order_isos(set(case_isos) & set(ref_isos))
        rows.append(
            {
                "scope": SYSTEM_LABEL,
                "case": case,
                "year": year,
                "emissions_mt": _sum(case, year, common) if common else float("nan"),
                "emissions_mt_ref": (
                    _sum(reference_case, year, common) if common else float("nan")
                ),
                "delta_isos": "+".join(common),
                "delta_n_isos": len(common),
                "delta_coverage": _coverage_note(
                    case, reference_case, common, ref_isos, case_isos
                ),
            }
        )
    return rows


def _iso_delta_rows(iso_frame: pd.DataFrame, reference_case: str) -> list[dict]:
    """The per-ISO rows of the delta table (one ISO differenced against itself).

    Unchanged in substance from the pre-repair merge — an ISO scope has only
    ever compared like with like — and given the same three coverage columns so
    the table has one schema.

    Args:
        iso_frame: Per-(case, iso, year) frame.
        reference_case: The case every delta is measured against.

    Returns:
        One row dict per (case, iso, year).
    """
    ref: dict[tuple[int, str], float] = {}
    for row in iso_frame[iso_frame["case"] == reference_case].itertuples(index=False):
        ref.setdefault((int(row.year), row.iso), row.emissions_mt)
    rows: list[dict] = []
    for row in iso_frame.itertuples(index=False):
        key = (int(row.year), row.iso)
        rows.append(
            {
                "scope": row.iso,
                "case": row.case,
                "year": int(row.year),
                "emissions_mt": row.emissions_mt,
                "emissions_mt_ref": ref.get(key, float("nan")),
                "delta_isos": row.iso,
                "delta_n_isos": 1,
                "delta_coverage": (
                    COVERAGE_FULL
                    if key in ref
                    else f"NO DELTA - {row.iso} absent from {reference_case}"
                ),
            }
        )
    return rows


def build_delta_table(
    iso_frame: pd.DataFrame, system_frame: pd.DataFrame, reference_case: str
) -> pd.DataFrame:
    """Build the campaign-level delta table vs the reference case.

    The system-scope row differences the two cases on the ISO set they SHARE —
    see :func:`_system_delta_rows` for the defect that requires it and the
    measured before/after.

    Args:
        iso_frame: Per-(case, iso, year) frame.
        system_frame: Per-(case, year) modeled-system frame.
        reference_case: The case every delta is measured against.

    Returns:
        A long frame with ``scope`` (an ISO name, or :data:`SYSTEM_LABEL`),
        ``case``, ``year``, ``emissions_mt``, ``emissions_mt_ref``,
        ``emissions_mt_delta``, ``cumulative_emissions_mt_delta`` (the running
        sum over years within a scope and case), and the three columns naming
        the ISO set the row's delta was actually computed on: ``delta_isos``,
        ``delta_n_isos`` and ``delta_coverage``.
    """
    rows: list[dict] = []
    if not iso_frame.empty:
        rows += _iso_delta_rows(iso_frame, reference_case)
    if not system_frame.empty:
        rows += _system_delta_rows(iso_frame, system_frame, reference_case)
    if not rows:
        return pd.DataFrame()
    out = pd.DataFrame(rows)
    out["emissions_mt_delta"] = out["emissions_mt"] - out["emissions_mt_ref"]
    out = out.sort_values(["scope", "case", "year"])
    out["cumulative_emissions_mt_delta"] = out.groupby(["scope", "case"])[
        "emissions_mt_delta"
    ].cumsum()
    return out[
        [
            "scope",
            "case",
            "year",
            "emissions_mt",
            "emissions_mt_ref",
            "emissions_mt_delta",
            "cumulative_emissions_mt_delta",
            "delta_isos",
            "delta_n_isos",
            "delta_coverage",
        ]
    ].reset_index(drop=True)


def _md_table(df: pd.DataFrame, float_fmt: str = "{:.3f}") -> list[str]:
    """Render a small DataFrame as GitHub-markdown table lines."""
    if df.empty:
        return ["_No data._"]
    cols = list(df.columns)
    lines = ["| " + " | ".join(str(c) for c in cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = [float_fmt.format(v) if isinstance(v, float) else str(v) for v in row]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def write_markdown(
    path: Path,
    root: Path,
    reference_case: str,
    iso_frame: pd.DataFrame,
    system_frame: pd.DataFrame,
    deltas: pd.DataFrame,
) -> None:
    """Write the campaign rollup markdown, disclosure block included."""
    lines = [
        f"# Scenario campaign rollup — {root.name}",
        "",
        f"Total is the **{SYSTEM_LABEL}**, NOT a national figure.",
        "",
        f"{NOT_MODELED_NOTE}",
        "",
        "## Coverage",
        "",
    ]
    if system_frame.empty:
        lines.append("_No summaries found._")
    else:
        cover = (
            system_frame.groupby("case", as_index=False)
            .agg(
                years=("year", "count"),
                n_isos=("n_isos", "max"),
                isos=("isos", "last"),
                isos_missing=("isos_missing", "last"),
            )
            .sort_values("case")
        )
        lines += _md_table(cover, float_fmt="{:.0f}")

    lines += ["", f"## Modeled-system CO2 (Mt) — {SYSTEM_LABEL}", ""]
    if system_frame.empty:
        lines.append("_No summaries found._")
    else:
        lines += _md_table(
            system_frame[
                [
                    "case",
                    "year",
                    "emissions_mt",
                    "import_co2_mt_reported",
                    "unserved_mwh",
                ]
            ]
        )

    lines += ["", f"## CO2 delta vs `{reference_case}` (Mt)", ""]
    if deltas.empty:
        lines.append("_No summaries found._")
    else:
        last_year = int(deltas["year"].max())
        snap = deltas[
            (deltas["year"] == last_year) & (deltas["case"] != reference_case)
        ][
            [
                "scope",
                "case",
                "emissions_mt_delta",
                "cumulative_emissions_mt_delta",
                "delta_isos",
                "delta_coverage",
            ]
        ]
        lines.append(
            f"Final campaign year **{last_year}**; the cumulative column is the "
            "running sum of the per-year delta over every year in the campaign."
        )
        lines.append("")
        lines.append(
            f"`delta_isos` is the ISO set the row's delta was computed on — the "
            f"intersection of the case's ISOs with `{reference_case}`'s, so both "
            "operands span the same system. `delta_coverage` reads "
            f"`{COVERAGE_FULL}` when nothing had to be dropped, and otherwise "
            "names every ISO that did and from which side."
        )
        lines.append("")
        lines += _md_table(snap)

    lines += [
        "",
        "## Side lines — reported beside the total, never inside it",
        "",
        f"1. **Import-attributed CO2.** {IMPORT_CO2_DISCLOSURE}",
        "2. **Unserved energy (MWh).** The slack column's annual energy. A case",
        "   whose CO2 falls while unserved energy rises has not decarbonized; it",
        "   has shed load. Read the two together, always.",
        f"3. **ISOs not modeled.** {NOT_MODELED_NOTE}",
        "",
        "A blank side-line cell means that run's cache was not on disk when the",
        "rollup ran, so the line could not be reconstructed — it is never a zero.",
    ]
    path.write_text("\n".join(lines) + "\n")
    logger.info("wrote %s", path)


def main(argv: list[str] | None = None) -> None:
    """Collate a scenario campaign into the per-ISO and system-total tables."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="Campaign root holding <iso>/<case>/full_horizon_summary.json.",
    )
    parser.add_argument(
        "--reference-case",
        default="REF",
        help="Case every delta is measured against (the plan's REF; §3.0).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Defaults to <root>/_rollup/.",
    )
    args = parser.parse_args(argv)

    if not args.root.exists():
        raise SystemExit(f"no such campaign root: {args.root}")
    out_dir = args.out_dir or (args.root / "_rollup")
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = discover_summaries(args.root)
    if not summaries:
        raise SystemExit(f"no full_horizon_summary.json found under {args.root}")
    logger.info(
        "found %d summaries: %s",
        len(summaries),
        ", ".join(f"{iso}/{case}" for iso, case, _ in summaries),
    )

    iso_frame = build_iso_frame(summaries)
    system_frame = build_system_frame(iso_frame)
    cases = sorted(iso_frame["case"].unique()) if not iso_frame.empty else []
    if args.reference_case not in cases:
        raise SystemExit(
            f"reference case {args.reference_case!r} not in campaign cases {cases}"
        )
    deltas = build_delta_table(iso_frame, system_frame, args.reference_case)

    iso_frame.to_csv(out_dir / "campaign_emissions_by_iso.csv", index=False)
    system_frame.to_csv(out_dir / "campaign_emissions_system.csv", index=False)
    deltas.to_csv(out_dir / "campaign_delta_table.csv", index=False)
    write_markdown(
        out_dir / "campaign_report.md",
        args.root,
        args.reference_case,
        iso_frame,
        system_frame,
        deltas,
    )
    logger.info("campaign rollup written → %s", out_dir)


if __name__ == "__main__":
    main()
