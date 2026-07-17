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
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import END_YEAR, START_YEAR  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.policy.federal_ces import (  # noqa: E402
    premium_for_year,
    reporting_credit_fractions,
)
from market_sim.results import cache  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.results.export import _summarize_year, real_to_nominal  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("report_ces_campaign")

# Dollar-valued per-year columns eligible for the optional nominal companion.
_NOMINAL_HEADLINE_COLS = ("premium_usd_per_mwh", "avg_price_usd_per_mwh")


def _parse_years(spec: str) -> list[int]:
    """Parse a ``2026-2050`` or ``2026,2030`` year spec into a list of ints."""
    if "-" in spec:
        lo, hi = (int(x) for x in spec.split("-", 1))
        return list(range(lo, hi + 1))
    return [int(x) for x in spec.split(",")]


def load_meta(matrix_dir: Path) -> dict:
    """Load and sanity-check a matrix bundle's ``meta.json``.

    Args:
        matrix_dir: The matrix output directory
            (``results/ensemble/<matrix_id>/``).

    Returns:
        The parsed meta dict (``iso``, ``cases``, ``label``, ...).

    Raises:
        SystemExit: When ``meta.json`` is missing or carries no cases.
    """
    meta_path = matrix_dir / "meta.json"
    if not meta_path.exists():
        raise SystemExit(f"no meta.json in {matrix_dir} — not a matrix out-dir?")
    meta = json.loads(meta_path.read_text())
    if not meta.get("cases"):
        raise SystemExit(f"{meta_path} has no cases")
    return meta


def case_config(iso: str, cache_key: str) -> ScenarioConfig | None:
    """Load one case's cached ``config.yaml``, or ``None`` when absent.

    The config drives the case's premium path and crediting rule. Runner
    caches always carry one; a missing config is reported (the case then
    falls back to default crediting and a zero premium).
    """
    config_path = cache.get_config_path(iso, cache_key, START_YEAR)
    if not config_path.exists():
        logger.warning("no config.yaml for cache key %s — default crediting", cache_key)
        return None
    return ScenarioConfig.from_yaml(config_path)


def cached_years(iso: str, cache_key: str, years_filter: list[int] | None) -> list[int]:
    """Return the case's cached years, optionally restricted to a filter."""
    years = [
        y for y in range(START_YEAR, END_YEAR + 1) if cache.is_cached(iso, cache_key, y)
    ]
    if years_filter is not None:
        years = [y for y in years if y in years_filter]
    return years


def collect_case_year_frames(
    iso: str,
    cases: dict[str, str],
    configs: dict[str, "ScenarioConfig | None"],
    years_filter: list[int] | None,
) -> dict[str, pd.DataFrame]:
    """Build the long per-(case, year) frames from the cached dispatch.

    One pass over every case's cached years produces four long frames:

    * ``headline`` — premium level, clean share, negative-price hours,
      average price, total generation and emissions per case-year (the
      clean-share-vs-premium curve's raw rows).
    * ``by_fuel`` — capacity (GW) and generation (TWh) per fuel per
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
    headline_rows: list[dict] = []
    fuel_rows: list[dict] = []
    curtailment_rows: list[dict] = []
    capture_rows: list[dict] = []

    for case, key in cases.items():
        config = configs[case]
        for year in cached_years(iso, key, years_filter):
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            summary = _summarize_year(result, context, config)
            premium = premium_for_year(config, year) if config is not None else 0.0

            headline_rows.append(
                {
                    "case": case,
                    "year": year,
                    "premium_usd_per_mwh": premium,
                    "clean_share": summary["clean_share"],
                    "negative_price_hours": summary["negative_price_hours"],
                    "avg_price_usd_per_mwh": summary["avg_price"],
                    "generation_twh": round(sum(summary["generation_twh"].values()), 4),
                    "emissions_mt": summary["emissions_mt"],
                }
            )

            fuels = set(summary["generation_twh"]) | set(summary["capacity_gw"])
            for fuel in sorted(fuels):
                fuel_rows.append(
                    {
                        "case": case,
                        "year": year,
                        "fuel": fuel,
                        "capacity_gw": summary["capacity_gw"].get(fuel, 0.0),
                        "generation_twh": summary["generation_twh"].get(fuel, 0.0),
                    }
                )

            wind_mwh = float(result.wind_dispatched.sum())
            solar_mwh = float(result.solar_dispatched.sum())
            for tech, delivered, potential in (
                ("wind", wind_mwh, float(context.wind_potential_mwh)),
                ("solar", solar_mwh, float(context.solar_potential_mwh)),
            ):
                curtailed = max(potential - delivered, 0.0)
                curtailment_rows.append(
                    {
                        "case": case,
                        "year": year,
                        "tech": tech,
                        "potential_mwh": potential,
                        "delivered_mwh": delivered,
                        "curtailed_mwh": curtailed,
                        "curtailment_rate": (
                            curtailed / potential if potential > 0.0 else 0.0
                        ),
                    }
                )

            # Premium capture: credit-weighted delivered vs potential MWh.
            fractions = reporting_credit_fractions(
                config, context.fuel_types, context.emission_rate
            )
            wind_frac, solar_frac = reporting_credit_fractions(
                config, ["wind", "solar"], [0.0, 0.0]
            )
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
                    "premium_usd_per_mwh": premium,
                    "credited_delivered_mwh": delivered,
                    "credited_potential_mwh": potential,
                    "premium_capture_rate": (
                        delivered / potential if potential > 0.0 else 0.0
                    ),
                }
            )

    return {
        "headline": pd.DataFrame(headline_rows),
        "by_fuel": pd.DataFrame(fuel_rows),
        "curtailment": pd.DataFrame(curtailment_rows),
        "capture": pd.DataFrame(capture_rows),
    }


def add_bau_deltas(
    df: pd.DataFrame,
    bau_case: str,
    keys: list[str],
    value_cols: list[str],
) -> pd.DataFrame:
    """Append per-row BAU reference and delta columns to a long frame.

    Args:
        df: Long frame carrying a ``case`` column plus ``keys`` and
            ``value_cols``.
        bau_case: The reference case name.
        keys: Join keys identifying comparable rows across cases
            (e.g. ``["year", "fuel"]``).
        value_cols: Columns to difference; each gains ``<col>_bau`` and
            ``<col>_delta``.

    Returns:
        ``df`` with the reference and delta columns appended (BAU rows
        difference to zero against themselves).
    """
    if df.empty:
        return df
    bau = (
        df[df["case"] == bau_case][keys + value_cols]
        .rename(columns={c: f"{c}_bau" for c in value_cols})
        .drop_duplicates(subset=keys)
    )
    out = df.merge(bau, on=keys, how="left")
    for col in value_cols:
        out[f"{col}_delta"] = out[col] - out[f"{col}_bau"]
    return out


def ledger_events_frame(
    iso: str,
    cases: dict[str, str],
    years_filter: list[int] | None,
) -> tuple[pd.DataFrame, list[str]]:
    """Aggregate every case's evolution ledgers into a long event frame.

    Events are the capacity-evolution channels the ledger records
    (``results/evolution_ledger.py`` schema): retirements (confirmed /
    announced / economic — legacy ``known`` rows pass through), thermal /
    renewable / storage additions, and CCS retrofits. MW are summed per
    ``(case, year, event, tech)``.

    Args:
        iso: ISO identifier.
        cases: Map of case name to cache key.
        years_filter: Optional explicit year restriction.

    Returns:
        A ``(frame, missing)`` pair: the long frame with columns ``case,
        year, event, tech, mw`` and the list of cases with no ledgers on
        disk (a backcast or fixture cache) for the MD notes.
    """
    rows: list[dict] = []
    missing: list[str] = []
    for case, key in cases.items():
        cache_dir = cache.get_cache_path(iso, key, START_YEAR).parent
        ledgers = load_ledgers_for_run(cache_dir)
        if not ledgers:
            missing.append(case)
            continue
        for year, ledger in ledgers.items():
            if years_filter is not None and year not in years_filter:
                continue
            for r in ledger.get("retirements", []):
                rows.append(
                    {
                        "case": case,
                        "year": year,
                        "event": "retirement",
                        "tech": r.get("fuel", "unknown"),
                        "mw": float(r.get("mw", 0.0)),
                    }
                )
            for r in ledger.get("thermal_additions", []):
                rows.append(
                    {
                        "case": case,
                        "year": year,
                        "event": "build",
                        "tech": r.get("fuel", "unknown"),
                        "mw": float(r.get("mw", 0.0)),
                    }
                )
            for r in ledger.get("renewable_additions", []):
                rows.append(
                    {
                        "case": case,
                        "year": year,
                        "event": "build",
                        "tech": r.get("tech", "unknown"),
                        "mw": float(r.get("mw", 0.0)),
                    }
                )
            for r in ledger.get("storage_additions", []):
                rows.append(
                    {
                        "case": case,
                        "year": year,
                        "event": "build",
                        "tech": r.get("tech", "storage"),
                        "mw": float(r.get("mw", 0.0)),
                    }
                )
            for r in ledger.get("ccs_retrofits", []):
                rows.append(
                    {
                        "case": case,
                        "year": year,
                        "event": "retrofit",
                        "tech": r.get("to_fuel", "gas_cc_ccs"),
                        "mw": float(r.get("mw", 0.0)),
                    }
                )
    frame = pd.DataFrame(rows, columns=["case", "year", "event", "tech", "mw"])
    if not frame.empty:
        frame = frame.groupby(["case", "year", "event", "tech"], as_index=False)[
            "mw"
        ].sum()
    return frame, missing


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


def pivot_vs_bau(
    per_case: dict[str, pd.DataFrame],
    index_cols: list[str],
    value_cols: list[str],
    bau_case: str,
) -> pd.DataFrame:
    """Pivot per-case frames wide and add per-case deltas vs BAU.

    The ``compare_scenarios.py`` convention generalized from two scenarios
    to a ladder: values are summed onto ``index_cols`` per case, pivoted
    wide (columns ``{value}_{case}``), and every non-BAU case gains a
    ``{value}_delta_{case}`` column against the BAU column.

    Args:
        per_case: Map of case name to its long frame.
        index_cols: Identity columns (e.g. plant keys or company name).
        value_cols: Columns to sum and difference.
        bau_case: The reference case name.

    Returns:
        One wide row per identity, or an empty frame when no case has data.
        A value column absent from every case's frame is skipped; one absent
        from only some frames sums as missing (NaN) for those cases.
    """
    frames = [
        df.assign(case=case)[
            index_cols + ["case"] + [c for c in value_cols if c in df.columns]
        ]
        for case, df in per_case.items()
        if not df.empty
    ]
    if not frames:
        return pd.DataFrame()
    combined = pd.concat(frames, ignore_index=True)
    value_cols = [c for c in value_cols if c in combined.columns]
    if not value_cols:
        return pd.DataFrame()
    wide = combined.pivot_table(
        index=index_cols, columns="case", values=value_cols, aggfunc="sum"
    )
    cases = list(dict.fromkeys(combined["case"]))
    if bau_case in cases:
        for col in value_cols:
            for case in cases:
                if case == bau_case or (col, case) not in wide.columns:
                    continue
                base = wide[(col, bau_case)] if (col, bau_case) in wide.columns else 0.0
                wide[(col, f"delta_{case}")] = wide[(col, case)] - base
    wide.columns = ["_".join(str(c) for c in col) for col in wide.columns]
    return wide.reset_index()


def captured_price_frame(
    iso: str,
    cases: dict[str, str],
    plant_by_case: dict[str, pd.DataFrame],
    years_filter: list[int] | None,
) -> pd.DataFrame:
    """Build the dispatch-weighted captured energy price by tech per case-year.

    Thermal techs come from the plant financial parquets (revenue ÷
    generation by fuel, i.e. the generation-weighted captured LP dual);
    wind and solar come straight from the cached dispatch (zonal dispatch ⊙
    zonal prices — the pools live outside the plant fleet). Prices are real
    2026$/MWh; zero-generation (tech, year) cells are dropped.
    """
    rows: list[dict] = []
    for case, plant in plant_by_case.items():
        if plant.empty:
            continue
        grouped = plant.groupby(["year", "fuel_type"], as_index=False).agg(
            revenue=("revenue", "sum"), generation_mwh=("generation_mwh", "sum")
        )
        grouped = grouped[grouped["generation_mwh"] > 0.0]
        for r in grouped.itertuples(index=False):
            rows.append(
                {
                    "case": case,
                    "year": int(r.year),
                    "tech": str(r.fuel_type),
                    "captured_price_usd_per_mwh": r.revenue / r.generation_mwh,
                    "source": "plant_financials",
                }
            )
    for case, key in cases.items():
        for year in cached_years(iso, key, years_filter):
            result = cache.load_result(iso, key, year)
            prices = np.asarray(result.prices, dtype=float)
            for tech, dispatched in (
                ("wind", np.asarray(result.wind_dispatched, dtype=float)),
                ("solar", np.asarray(result.solar_dispatched, dtype=float)),
            ):
                total = float(dispatched.sum())
                if total <= 0.0:
                    continue
                rows.append(
                    {
                        "case": case,
                        "year": year,
                        "tech": tech,
                        "captured_price_usd_per_mwh": float((dispatched * prices).sum())
                        / total,
                        "source": "dispatch_cache",
                    }
                )
    return pd.DataFrame(
        rows, columns=["case", "year", "tech", "captured_price_usd_per_mwh", "source"]
    )


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
