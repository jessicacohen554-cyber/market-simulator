"""CES premium-ladder campaign report (national-ces-eac-premium plan §5.4).

Reads one scenario-matrix output directory — the bundle written by
``matrix.write_matrix_outputs`` whose ``meta.json`` maps case names to cache
keys — plus each case's cached dispatch results, evolution ledgers and (when
present) the financial report parquets written by
``generate_financial_reports.py``, and emits the per-ISO campaign CSV/MD set,
every delta measured against the BAU case:

    {iso}_clean_share_vs_premium.csv   premium level vs credit-weighted clean share
    {iso}_capacity_by_fuel_deltas.csv  per-year capacity & generation by fuel vs BAU
    {iso}_evolution_deltas.csv         builds / retirements / retrofits vs BAU (ledgers)
    {iso}_captured_price_by_tech.csv   dispatch-weighted captured energy price by tech
    {iso}_curtailment_by_tech.csv      VRE potential vs delivered vs curtailed energy
    {iso}_premium_capture.csv          credited delivered / potential MWh per case-year
    {iso}_plant_revenue_deltas.csv     per-plant revenue & attribute deltas vs BAU
    {iso}_company_revenue_deltas.csv   per-company revenue & attribute deltas vs BAU
    {iso}_ces_campaign_report.md       human-readable summary + input-coverage notes

Revenue-delta tables reuse the ``compare_scenarios.py`` conventions (one wide
row per plant/company, per-scenario value columns joined with ``_``, plus a
``delta_<case>`` column per non-BAU case). All dollars are real 2026$ unless
``--nominal`` adds ``*_nominal`` companions via
``results/export.py::real_to_nominal`` (post-processing only — the model is
real-dollar throughout).

Usage:
    python scripts/report_ces_campaign.py \\
        --matrix-dir results/ensemble/<matrix_id>/ \\
        [--financial-reports-root reports/] [--bau-case BAU] \\
        [--output-dir <matrix-dir>/ces_report/] [--years 2026-2050] [--nominal]
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import START_YEAR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.policy.federal_ces import (  # noqa: E402
    premium_for_year,
    reporting_credit_fractions,
)
from market_sim.results import cache  # noqa: E402
from market_sim.results.export import real_to_nominal  # noqa: E402

# The generic "difference two cached cases" machinery lives in the scenario
# delta report (SCN-WS0 deliverable 2); this script keeps only the
# premium-specific tables and delegates the rest, so there is ONE
# implementation of each generic table in the tree. The names below are
# re-bound at module scope because they are this module's long-standing public
# surface (its tests and other scripts import them from here).
from scripts.report_scenario_deltas import (  # noqa: E402
    add_reference_deltas as add_bau_deltas,
    captured_price_frame,
    case_config,
    cached_years,
    ledger_events_frame,
    load_meta,
    md_table as _md_table,
    parse_years as _parse_years,
    pivot_vs_reference as pivot_vs_bau,
)
from scripts.report_scenario_deltas import (  # noqa: E402
    collect_case_year_frames as _collect_generic_frames,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("report_ces_campaign")

# Dollar-valued per-year columns eligible for the optional nominal companion.
_NOMINAL_HEADLINE_COLS = ("premium_usd_per_mwh", "avg_price_usd_per_mwh")


def collect_case_year_frames(
    iso: str,
    cases: dict[str, str],
    configs: dict[str, "ScenarioConfig | None"],
    years_filter: list[int] | None,
) -> dict[str, pd.DataFrame]:
    """Build the long per-(case, year) frames for the CES premium ladder.

    The ``headline``, ``by_fuel`` and ``curtailment`` frames are the generic
    ones (``report_scenario_deltas.collect_case_year_frames``) with the
    ladder's own ``premium_usd_per_mwh`` column joined onto the headline; the
    ``capture`` frame is premium-specific and built here.

    * ``headline`` — premium level, clean share, negative-price hours,
      average price, total generation and emissions per case-year (the
      clean-share-vs-premium curve's raw rows), plus every other per-year
      scalar the annual summary carries.
    * ``by_fuel`` — capacity (GW), generation (TWh) and CO2 (Mt) per fuel per
      case-year (wind/solar folded in, as in ``_summarize_year``).
    * ``curtailment`` — VRE potential vs delivered vs curtailed MWh per
      tech per case-year.
    * ``capture`` — credited delivered vs potential MWh and the
      premium-capture rate per case-year. Credited potential prices the
      crediting fractions onto nameplate energy for the thermal fleet
      (per-unit availability is not persisted in the cached context) and
      onto CF-weighted available energy for wind/solar; the definition is
      restated in the MD notes.

    Args:
        iso: ISO identifier from the matrix meta.
        cases: Map of case name to cache key (``meta.json`` ``cases``).
        configs: Map of case name to its cached config (or ``None``).
        years_filter: Optional explicit year restriction.

    Returns:
        ``{"headline": ..., "by_fuel": ..., "curtailment": ..., "capture": ...}``.
    """
    frames = _collect_generic_frames(iso, cases, configs, years_filter)

    premiums = {
        (case, year): (
            premium_for_year(configs[case], year) if configs[case] is not None else 0.0
        )
        for case in cases
        for year in cached_years(iso, cases[case], years_filter)
    }
    headline = frames["headline"]
    if not headline.empty:
        headline.insert(
            2,
            "premium_usd_per_mwh",
            [
                premiums[(c, y)]
                for c, y in zip(headline["case"], headline["year"], strict=True)
            ],
        )
    frames["headline"] = headline

    capture_rows: list[dict] = []
    for case, key in cases.items():
        config = configs[case]
        for year in cached_years(iso, key, years_filter):
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            # Premium capture: credit-weighted delivered vs potential MWh.
            fractions = reporting_credit_fractions(
                config, context.fuel_types, context.emission_rate
            )
            wind_frac, solar_frac = reporting_credit_fractions(
                config, ["wind", "solar"], [0.0, 0.0]
            )
            wind_mwh = float(result.wind_dispatched.sum())
            solar_mwh = float(result.solar_dispatched.sum())
            gen_per_unit = np.asarray(result.dispatch, dtype=float).sum(axis=1)
            hours = result.dispatch.shape[1]
            delivered = (
                float((gen_per_unit * fractions).sum())
                + wind_frac * wind_mwh
                + solar_frac * solar_mwh
            )
            potential = (
                float((np.asarray(context.pmax_mw, dtype=float) * fractions).sum())
                * hours
                + wind_frac * float(context.wind_potential_mwh)
                + solar_frac * float(context.solar_potential_mwh)
            )
            capture_rows.append(
                {
                    "case": case,
                    "year": year,
                    "premium_usd_per_mwh": premiums[(case, year)],
                    "credited_delivered_mwh": delivered,
                    "credited_potential_mwh": potential,
                    "premium_capture_rate": (
                        delivered / potential if potential > 0.0 else 0.0
                    ),
                }
            )
    frames["capture"] = pd.DataFrame(capture_rows)
    return frames


def _load_yearly(scenario_dir: Path, prefix: str) -> pd.DataFrame:
    """Concatenate every ``{prefix}_{year}.parquet`` in a report directory.

    Mirrors ``compare_scenarios.py::_load_yearly`` (the shared report-parquet
    reading convention); the year is read from the filename when the frame
    lacks a ``year`` column.
    """
    frames: list[pd.DataFrame] = []
    for path in sorted(scenario_dir.glob(f"{prefix}_*.parquet")):
        stem_year = path.stem.rsplit("_", 1)[-1]
        if not stem_year.isdigit():
            continue
        block = pd.read_parquet(path)
        if "year" not in block.columns:
            block["year"] = int(stem_year)
        frames.append(block)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def load_financials(
    cases: dict[str, str],
    reports_root: Path,
    years_filter: list[int] | None,
    nominal: bool,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame], list[str]]:
    """Load each case's plant/company financial report parquets.

    Args:
        cases: Map of case name to cache key; each case's reports are
            expected under ``reports_root/<cache_key>/`` (the layout
            ``generate_financial_reports.py`` writes).
        reports_root: Root directory of the per-scenario report dirs.
        years_filter: Optional explicit year restriction.
        nominal: When True, add ``*_nominal`` companions to the dollar
            columns (converted per-year BEFORE any cross-year summing).

    Returns:
        ``(plant_by_case, company_by_case, missing)`` — per-case frames and
        the list of cases with no financial parquets for the MD notes.
    """
    plant_by_case: dict[str, pd.DataFrame] = {}
    company_by_case: dict[str, pd.DataFrame] = {}
    missing: list[str] = []
    for case, key in cases.items():
        report_dir = reports_root / key
        plant = _load_yearly(report_dir, "plant_annual")
        company = _load_yearly(report_dir, "company_annual")
        if plant.empty and company.empty:
            missing.append(case)
            continue
        for frame, cols in (
            (plant, ("revenue", "attribute_revenue")),
            (company, ("owned_revenue", "owned_attribute_revenue")),
        ):
            if frame.empty:
                continue
            if years_filter is not None:
                frame.drop(frame[~frame["year"].isin(years_filter)].index, inplace=True)
            for col in cols:
                if col not in frame.columns:
                    # Pre-W2-B parquets carry no attribute line; report 0.
                    frame[col] = 0.0
                if nominal:
                    frame[f"{col}_nominal"] = real_to_nominal(
                        frame[col].to_numpy(dtype=float),
                        frame["year"].to_numpy(dtype=int),
                    )
        if not plant.empty:
            plant_by_case[case] = plant
        if not company.empty:
            company_by_case[case] = company
    return plant_by_case, company_by_case, missing


def write_markdown_report(
    path: Path,
    meta: dict,
    configs: dict[str, "ScenarioConfig | None"],
    frames: dict[str, pd.DataFrame],
    evolution: pd.DataFrame,
    company_deltas: pd.DataFrame,
    notes: list[str],
    nominal: bool,
) -> None:
    """Write the human-readable campaign summary markdown.

    Headline tables only (the CSVs carry the full detail): the
    clean-share-vs-premium curve, final-year capacity deltas, evolution
    totals, premium capture, and the largest company revenue deltas, plus a
    notes section restating metric definitions and any missing inputs.
    """
    iso = meta["iso"]
    headline = frames["headline"]
    lines = [
        f"# CES premium-ladder campaign report — {iso} — {meta.get('matrix_id', '')}",
        "",
        f"**{meta.get('label', 'deterministic scenario range')}** — deltas are",
        "case-vs-BAU differences on one deterministic ladder, not a probability",
        "statement. Dollars are real 2026$"
        + (" (nominal companions included via --nominal)." if nominal else "."),
        "",
        "## Cases",
        "",
        "| Case | Cache key | Crediting | Premium @2026 ($/MWh) |",
        "|---|---|---|---|",
    ]
    for case, key in meta["cases"].items():
        config = configs.get(case)
        crediting = config.federal_ces_crediting if config is not None else "?"
        enabled = bool(config is not None and config.federal_ces_enabled)
        premium = premium_for_year(config, START_YEAR) if config is not None else 0.0
        lines.append(
            f"| {case} | `{key}` | {crediting if enabled else '(CES off)'} "
            f"| {premium:.2f} |"
        )

    lines += ["", "## Clean-share vs premium", ""]
    if headline.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(headline["year"].max())
        curve = headline[headline["year"] == last_year][
            [
                "case",
                "premium_usd_per_mwh",
                "clean_share",
                "negative_price_hours",
                "avg_price_usd_per_mwh",
            ]
        ].sort_values("premium_usd_per_mwh")
        lines.append(f"Final cached year on disk: **{last_year}**.")
        lines.append("")
        lines += _md_table(curve)

    lines += ["", "## Capacity deltas vs BAU (final year, GW)", ""]
    by_fuel = frames["by_fuel"]
    if by_fuel.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(by_fuel["year"].max())
        snap = by_fuel[
            (by_fuel["year"] == last_year) & (by_fuel["capacity_gw_delta"].abs() > 0)
        ][["case", "fuel", "capacity_gw", "capacity_gw_bau", "capacity_gw_delta"]]
        if snap.empty:
            lines.append(
                f"_No capacity differences vs BAU in {last_year} "
                "(fleet evolution identical across cases)._"
            )
        else:
            lines += _md_table(snap.sort_values(["case", "fuel"]))

    lines += ["", "## Capacity-evolution deltas vs BAU (ledger totals, MW)", ""]
    if evolution.empty:
        lines.append("_No evolution ledgers found (backcast or fixture cache)._")
    else:
        totals = evolution.groupby(["case", "event", "tech"], as_index=False).agg(
            mw=("mw", "sum"), mw_delta=("mw_delta", "sum")
        )
        totals = totals[(totals["mw"].abs() > 0) | (totals["mw_delta"].abs() > 0)]
        lines += _md_table(totals, float_fmt="{:.1f}")

    lines += ["", "## Premium capture (credited delivered / potential MWh)", ""]
    capture = frames["capture"]
    if capture.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(capture["year"].max())
        lines += _md_table(
            capture[capture["year"] == last_year][
                [
                    "case",
                    "premium_usd_per_mwh",
                    "credited_delivered_mwh",
                    "credited_potential_mwh",
                    "premium_capture_rate",
                ]
            ]
        )

    lines += ["", "## Largest company revenue deltas vs BAU", ""]
    if company_deltas.empty:
        lines.append(
            "_No financial report parquets found — run "
            "`scripts/generate_financial_reports.py` per case first._"
        )
    else:
        delta_cols = [
            c for c in company_deltas.columns if c.startswith("owned_revenue_delta_")
        ]
        if delta_cols:
            ranked = company_deltas.assign(
                _rank=company_deltas[delta_cols].abs().max(axis=1)
            ).sort_values("_rank", ascending=False)
            top = ranked.head(10)[["parent_company"] + delta_cols]
            lines += _md_table(top, float_fmt="{:,.0f}")
        else:
            lines.append("_Only the BAU case has financial reports — no deltas._")

    lines += [
        "",
        "## Notes & definitions",
        "",
        "- `clean_share` = credit-weighted generation / total generation, using",
        "  each case's own crediting RULE (reporting-side, ungated by",
        "  `federal_ces_enabled`) so the BAU anchor is the real physical clean",
        "  share. Storage discharge is excluded from both sides (owner D5).",
        "- `negative_price_hours` is the zone-averaged count of hours clearing",
        "  below $0/MWh (total negative zone-hours / zone count).",
        "- `premium_capture_rate` prices credited potential at nameplate energy",
        "  for thermal units (per-unit availability is not persisted in the",
        "  cached context) and CF-weighted available energy for wind/solar, so",
        "  it blends economic dispatch depth with curtailment erosion.",
        "- `attribute_revenue` is the certificate line only (max of legacy",
        "  `eac_price_*` and federal premium × credit fraction, one certificate",
        "  per MWh); PTC/ITC/45U/45Q tax credits are deliberately excluded.",
        "- Campaign runs are gated on the §7 capacity-screen readiness criteria",
        "  (plan D9/W3-R); treat capacity-evolution deltas produced before that",
        "  GO as structural smoke, not results.",
    ]
    for note in notes:
        lines.append(f"- {note}")

    path.write_text("\n".join(lines) + "\n")
    logger.info("wrote %s", path)


def main(argv: list[str] | None = None) -> None:
    """Build the full CES campaign report set from a matrix out-dir."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix-dir",
        type=Path,
        required=True,
        help="Matrix output directory holding meta.json (write_matrix_outputs).",
    )
    parser.add_argument(
        "--financial-reports-root",
        type=Path,
        default=REPO / "reports",
        help="Root of per-scenario generate_financial_reports.py output dirs "
        "(reports/<cache_key>/).",
    )
    parser.add_argument("--bau-case", default="BAU")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Defaults to <matrix-dir>/ces_report/.",
    )
    parser.add_argument(
        "--years", default=None, help="Optional year restriction, e.g. 2026-2050."
    )
    parser.add_argument(
        "--nominal",
        action="store_true",
        help="Add nominal-dollar companion columns via real_to_nominal.",
    )
    args = parser.parse_args(argv)

    meta = load_meta(args.matrix_dir)
    iso = str(meta["iso"]).upper()
    cases: dict[str, str] = dict(meta["cases"])
    if args.bau_case not in cases:
        raise SystemExit(
            f"BAU case {args.bau_case!r} not in matrix cases {sorted(cases)}"
        )
    years_filter = _parse_years(args.years) if args.years else None
    out_dir = args.output_dir or (args.matrix_dir / "ces_report")
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = iso.lower()
    notes: list[str] = []

    configs = {case: case_config(iso, key) for case, key in cases.items()}
    for case, config in configs.items():
        if config is None:
            notes.append(
                f"Case `{case}` had no cached config.yaml — default crediting "
                "and a zero premium were assumed."
            )

    frames = collect_case_year_frames(iso, cases, configs, years_filter)

    # Clean-share-vs-premium curve (+ negative-price hours, avg price).
    headline = add_bau_deltas(
        frames["headline"],
        args.bau_case,
        ["year"],
        ["clean_share", "negative_price_hours", "avg_price_usd_per_mwh"],
    )
    if args.nominal and not headline.empty:
        for col in _NOMINAL_HEADLINE_COLS:
            headline[f"{col}_nominal"] = real_to_nominal(
                headline[col].to_numpy(dtype=float),
                headline["year"].to_numpy(dtype=int),
            )
    frames["headline"] = headline
    headline.to_csv(out_dir / f"{prefix}_clean_share_vs_premium.csv", index=False)

    # Capacity & generation by fuel, per year, vs BAU.
    by_fuel = add_bau_deltas(
        frames["by_fuel"],
        args.bau_case,
        ["year", "fuel"],
        ["capacity_gw", "generation_twh"],
    )
    frames["by_fuel"] = by_fuel
    by_fuel.to_csv(out_dir / f"{prefix}_capacity_by_fuel_deltas.csv", index=False)

    # Curtailment by tech vs BAU.
    curtailment = add_bau_deltas(
        frames["curtailment"],
        args.bau_case,
        ["year", "tech"],
        ["curtailed_mwh", "curtailment_rate"],
    )
    curtailment.to_csv(out_dir / f"{prefix}_curtailment_by_tech.csv", index=False)

    # Premium capture per case-year (BAU rows carry the zero-premium anchor).
    frames["capture"].to_csv(out_dir / f"{prefix}_premium_capture.csv", index=False)

    # Evolution ledger deltas.
    events, missing_ledgers = ledger_events_frame(iso, cases, years_filter)
    evolution = add_bau_deltas(events, args.bau_case, ["year", "event", "tech"], ["mw"])
    if not evolution.empty:
        # A (year, event, tech) absent from BAU is a genuine zero baseline.
        evolution["mw_bau"] = evolution["mw_bau"].fillna(0.0)
        evolution["mw_delta"] = evolution["mw"] - evolution["mw_bau"]
    evolution.to_csv(out_dir / f"{prefix}_evolution_deltas.csv", index=False)
    if missing_ledgers:
        notes.append(
            "No evolution ledgers for case(s): "
            + ", ".join(f"`{c}`" for c in missing_ledgers)
            + " — builds/retirements/retrofit deltas are partial."
        )

    # Plant / company revenue deltas from the financial report parquets.
    plant_by_case, company_by_case, missing_fin = load_financials(
        cases, args.financial_reports_root, years_filter, args.nominal
    )
    if missing_fin:
        notes.append(
            "No financial report parquets for case(s): "
            + ", ".join(f"`{c}`" for c in missing_fin)
            + " — run scripts/generate_financial_reports.py per case for full "
            "revenue deltas."
        )
    plant_cols = ["revenue", "attribute_revenue", "net_operating_income"]
    company_cols = ["owned_revenue", "owned_attribute_revenue"]
    if args.nominal:
        plant_cols += ["revenue_nominal", "attribute_revenue_nominal"]
        company_cols += ["owned_revenue_nominal", "owned_attribute_revenue_nominal"]
    plant_deltas = pivot_vs_bau(
        plant_by_case,
        ["plant_code", "generator_id", "zone", "fuel_type"],
        plant_cols,
        args.bau_case,
    )
    plant_deltas.to_csv(out_dir / f"{prefix}_plant_revenue_deltas.csv", index=False)
    company_deltas = pivot_vs_bau(
        company_by_case, ["parent_company"], company_cols, args.bau_case
    )
    company_deltas.to_csv(out_dir / f"{prefix}_company_revenue_deltas.csv", index=False)

    # Captured price by tech vs BAU.
    captured = captured_price_frame(iso, cases, plant_by_case, years_filter)
    captured = add_bau_deltas(
        captured, args.bau_case, ["year", "tech"], ["captured_price_usd_per_mwh"]
    )
    if args.nominal and not captured.empty:
        captured["captured_price_usd_per_mwh_nominal"] = real_to_nominal(
            captured["captured_price_usd_per_mwh"].to_numpy(dtype=float),
            captured["year"].to_numpy(dtype=int),
        )
    captured.to_csv(out_dir / f"{prefix}_captured_price_by_tech.csv", index=False)

    write_markdown_report(
        out_dir / f"{prefix}_ces_campaign_report.md",
        meta,
        configs,
        frames,
        evolution,
        company_deltas,
        notes,
        args.nominal,
    )
    logger.info("CES campaign report set written → %s", out_dir)


if __name__ == "__main__":
    main()
