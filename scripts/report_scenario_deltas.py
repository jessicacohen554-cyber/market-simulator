"""Generic scenario-campaign delta report (SCN-WS0 deliverable 2).

Reads one scenario-matrix output directory — the bundle written by
``matrix.write_matrix_outputs`` whose ``meta.json`` maps case names to cache
keys — plus each case's cached dispatch results and evolution ledgers, and
emits the per-ISO delta set, every difference measured against a NAMED
REFERENCE CASE (``--reference-case``, the plan's REF; §3.0):

    {iso}_headline_deltas.csv          every per-year scalar metric vs REF
                                       (+ backstop_built_mw / _mwh, SCN-WS4b)
    {iso}_by_fuel_deltas.csv           capacity / generation / CO2 by fuel vs REF
    {iso}_emissions_by_zone_deltas.csv CO2 by zone vs REF
    {iso}_cumulative_co2_deltas.csv    running and total CO2 delta vs REF
    {iso}_evolution_deltas.csv         builds / retirements / retrofits vs REF
    {iso}_captured_price_by_tech.csv   dispatch-weighted captured energy price
    {iso}_curtailment_by_tech.csv      VRE potential vs delivered vs curtailed
    {iso}_scenario_deltas_report.md    human-readable summary + notes

This module is the GENERIC half of ``report_ces_campaign.py``: that script
keeps its premium-specific tables (clean-share-vs-premium, premium capture,
plant/company revenue deltas) and imports the generic machinery from here, so
there is one implementation of "difference two cached cases" in the tree.

The reference case is a NAME, not a premium level, so the same report serves a
carbon-price ladder, a CES ladder, a load case or a policy corner. Deltas on
one deterministic case set are a scenario range, never a probability statement
(``matrix.LABEL``).

**The "backstop-built" column (SCN-WS4b, plan §3 WS-4 item 3).** The headline
frame carries ``backstop_built_mw`` (the reserve-margin adequacy backstop's
``gas_ct`` on the books in that year — every ledger ``thermal_additions`` row
tagged ``source == "reserve_backstop"`` in that year or earlier, net of a later
retirement of the same unit) and ``backstop_built_mwh`` (those units' energy in
the year's cached dispatch, matched by ``unit_id``). Both are derived from the
evolution ledger the report already reads and the dispatch it already loads —
no new persisted field, no solve. The column exists so a curve-ON ISO's CO2
delta can be read with the administratively-built share beside it: the
backstop fires in PJM/MISO/NYISO/NEISO/CAISO only
(``capacity_evolution.adequacy.resolve_reserve_margin_build_enabled``), so for
energy-only ERCOT the column is 0.0 by market design and ``unserved_mwh`` is
the adequacy line to read instead (``docs/handoffs/load-hi-adequacy-reading-
2026-09-06.md``).

Usage:
    python scripts/report_scenario_deltas.py \\
        --matrix-dir results/ensemble/<matrix_id>/ \\
        --reference-case REF \\
        [--output-dir <matrix-dir>/scenario_report/] [--years 2026-2050]
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
from market_sim.results import cache  # noqa: E402
from market_sim.results.emissions import IMPORT_CO2_DISCLOSURE  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402
from market_sim.results.export import _summarize_year  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("report_scenario_deltas")

# The annual summary's ``avg_price`` is carried under this name so the headline
# frame states its unit; it is also the column name ``report_ces_campaign.py``
# has always used. Every other scalar keeps its ``_summarize_year`` key.
AVG_PRICE_COL = "avg_price_usd_per_mwh"

# The evolution ledger's channel tag for a reserve-margin backstop build
# (``results/evolution_ledger.py`` schema: ``thermal_additions[].source`` is
# ``planned`` | ``economic`` | ``reserve_backstop``; the writer is
# ``capacity_evolution/evolve.py`` at the ``apply_reserve_margin_build`` seam).
BACKSTOP_SOURCE = "reserve_backstop"
# Headline-frame column names for the backstop-built pair (SCN-WS4b).
BACKSTOP_MW_COL = "backstop_built_mw"
BACKSTOP_MWH_COL = "backstop_built_mwh"


def backstop_units_by_year(ledgers: dict[int, dict]) -> dict[int, dict[str, float]]:
    """Return the reserve-backstop units on the books through each ledger year.

    Walks the run's ledgers in year order and accumulates every
    ``thermal_additions`` row whose ``source`` is :data:`BACKSTOP_SOURCE`
    (``{unit_id: mw}``); a later ``retirements`` row naming one of those units
    removes it, so the map is "on the books", not "ever built". Within a year
    retirements are applied before additions, matching the evolution order
    (retirement steps 0-3 precede the step-6 backstop), so a unit built in a
    year can never be netted out in that same year.

    Args:
        ledgers: ``{year: ledger_dict}`` from
            :func:`market_sim.results.evolution_ledger.load_ledgers_for_run`.

    Returns:
        ``{year: {unit_id: mw}}`` — the cumulative backstop fleet after that
        year's evolution, one entry per ledger year (empty dicts where nothing
        is on the books). Empty in, empty out.
    """
    on_books: dict[str, float] = {}
    out: dict[int, dict[str, float]] = {}
    for year in sorted(ledgers):
        led = ledgers[year]
        for r in led.get("retirements", []) or []:
            on_books.pop(str(r.get("unit_id")), None)
        for r in led.get("thermal_additions", []) or []:
            if str(r.get("source") or "") != BACKSTOP_SOURCE:
                continue
            uid = str(r.get("unit_id"))
            on_books[uid] = on_books.get(uid, 0.0) + float(r.get("mw", 0.0) or 0.0)
        out[year] = dict(on_books)
    return out


def backstop_units_for_cases(
    iso: str, cases: dict[str, str]
) -> dict[str, dict[int, dict[str, float]]]:
    """Load every case's ledgers and return its per-year backstop fleet map.

    A case with no ledgers on disk (a backcast or fixture cache) maps to an
    empty dict, which the column reads as 0.0 — the same "no ledger" case
    :func:`ledger_events_frame` reports in the notes.

    Args:
        iso: ISO identifier.
        cases: Map of case name to cache key.

    Returns:
        ``{case: {year: {unit_id: mw}}}`` (see :func:`backstop_units_by_year`).
    """
    out: dict[str, dict[int, dict[str, float]]] = {}
    for case, key in cases.items():
        cache_dir = cache.get_cache_path(iso, key, START_YEAR).parent
        out[case] = backstop_units_by_year(load_ledgers_for_run(cache_dir))
    return out


def _backstop_on_books(
    by_year: dict[int, dict[str, float]], year: int
) -> dict[str, float]:
    """Return the backstop fleet on the books in ``year``.

    The ledger written for ``year`` describes the fleet the year was solved
    on, so an exact match is used when present; otherwise the latest ledger
    year at or before ``year`` (a bridge year carries the prior fleet). Years
    before the first ledger read empty.
    """
    if year in by_year:
        return by_year[year]
    prior = [y for y in by_year if y <= year]
    return by_year[max(prior)] if prior else {}


def parse_years(spec: str) -> list[int]:
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

    Runner caches always carry one; a missing config is reported so the
    report's notes can say which case fell back to defaults.
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
    backstop_units: dict[str, dict[int, dict[str, float]]] | None = None,
    notes: list[str] | None = None,
) -> dict[str, pd.DataFrame]:
    """Build the long per-(case, year) frames from the cached dispatch.

    One pass over every case's cached years produces four long frames:

    * ``headline`` — every per-year SCALAR metric the annual summary carries
      (``emissions_mt``, ``import_co2_mt_reported``, ``unserved_mwh``,
      ``clean_share``, ``negative_price_hours``, ``curtailment_twh``,
      ``storage_cycles``, ``nox_tonnes``, ``so2_tonnes``, ``peak_price``, and
      ``avg_price`` under :data:`AVG_PRICE_COL`) plus total ``generation_twh``.
      The set widens automatically when ``_summarize_year`` grows a scalar.
      When ``backstop_units`` is given it also carries the SCN-WS4b
      backstop-built pair — :data:`BACKSTOP_MW_COL` (the reserve-backstop
      ``gas_ct`` MW on the books that year) and :data:`BACKSTOP_MWH_COL`
      (those units' energy in the year's dispatch, matched on ``unit_id``).
    * ``by_fuel`` — capacity (GW), generation (TWh) and CO2 (Mt) per fuel per
      case-year (wind/solar folded in, as in ``_summarize_year``).
    * ``by_zone`` — CO2 (Mt) per zone per case-year.
    * ``curtailment`` — VRE potential vs delivered vs curtailed MWh per tech
      per case-year.

    Args:
        iso: ISO identifier from the matrix meta.
        cases: Map of case name to cache key (``meta.json`` ``cases``).
        configs: Map of case name to its cached config (or ``None``), passed
            through to ``_summarize_year`` for the crediting rule.
        years_filter: Optional explicit year restriction.
        backstop_units: Optional ``{case: {year: {unit_id: mw}}}`` from
            :func:`backstop_units_for_cases`; ``None`` omits the pair (the
            pre-SCN-WS4b frame, column-for-column).
        notes: Optional list the function appends report notes to — one per
            case-year whose ledger names a backstop unit the cached fleet does
            not carry (a silent 0 MWh would otherwise hide it).

    Returns:
        ``{"headline": ..., "by_fuel": ..., "by_zone": ..., "curtailment": ...}``.
    """
    headline_rows: list[dict] = []
    fuel_rows: list[dict] = []
    zone_rows: list[dict] = []
    curtailment_rows: list[dict] = []

    for case, key in cases.items():
        config = configs.get(case)
        for year in cached_years(iso, key, years_filter):
            result = cache.load_result(iso, key, year)
            context = cache.load_fleet_context(iso, key, year)
            summary = _summarize_year(result, context, config)

            scalars = {
                k: v
                for k, v in summary.items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            }
            scalars[AVG_PRICE_COL] = scalars.pop("avg_price")
            if backstop_units is not None:
                on_books = _backstop_on_books(backstop_units.get(case, {}), year)
                scalars[BACKSTOP_MW_COL] = round(sum(on_books.values()), 3)
                ids = set(on_books)
                # Boolean mask over the generator axis: one row per cached unit
                # whose id the ledger tagged as a backstop build (vectorized
                # over hours, rule 2 [R-VECTOR]).
                mask = np.array([u in ids for u in context.unit_ids], dtype=bool)
                scalars[BACKSTOP_MWH_COL] = round(
                    float(np.asarray(result.dispatch, dtype=float)[mask].sum()), 3
                )
                unmatched = sorted(ids - set(context.unit_ids))
                if unmatched and notes is not None:
                    notes.append(
                        f"Case `{case}` {year}: ledger names reserve-backstop unit(s) "
                        + ", ".join(f"`{u}`" for u in unmatched)
                        + f" absent from the cached fleet — `{BACKSTOP_MWH_COL}` "
                        "excludes them (MW still counted from the ledger)."
                    )
            headline_rows.append(
                {
                    "case": case,
                    "year": year,
                    **scalars,
                    "generation_twh": round(sum(summary["generation_twh"].values()), 4),
                }
            )

            fuels = (
                set(summary["generation_twh"])
                | set(summary["capacity_gw"])
                | set(summary["emissions_by_fuel_mt"])
            )
            for fuel in sorted(fuels):
                fuel_rows.append(
                    {
                        "case": case,
                        "year": year,
                        "fuel": fuel,
                        "capacity_gw": summary["capacity_gw"].get(fuel, 0.0),
                        "generation_twh": summary["generation_twh"].get(fuel, 0.0),
                        "emissions_mt": summary["emissions_by_fuel_mt"].get(fuel, 0.0),
                    }
                )

            for zone in sorted(summary["emissions_by_zone_mt"]):
                zone_rows.append(
                    {
                        "case": case,
                        "year": year,
                        "zone": zone,
                        "emissions_mt": summary["emissions_by_zone_mt"][zone],
                    }
                )

            for tech, delivered, potential in (
                (
                    "wind",
                    float(result.wind_dispatched.sum()),
                    float(context.wind_potential_mwh),
                ),
                (
                    "solar",
                    float(result.solar_dispatched.sum()),
                    float(context.solar_potential_mwh),
                ),
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

    return {
        "headline": pd.DataFrame(headline_rows),
        "by_fuel": pd.DataFrame(fuel_rows),
        "by_zone": pd.DataFrame(zone_rows),
        "curtailment": pd.DataFrame(curtailment_rows),
    }


def add_reference_deltas(
    df: pd.DataFrame,
    reference_case: str,
    keys: list[str],
    value_cols: list[str],
) -> pd.DataFrame:
    """Append per-row reference and delta columns to a long frame.

    Args:
        df: Long frame carrying a ``case`` column plus ``keys`` and
            ``value_cols``.
        reference_case: The reference case name (REF/BAU).
        keys: Join keys identifying comparable rows across cases
            (e.g. ``["year", "fuel"]``).
        value_cols: Columns to difference; each gains ``<col>_bau`` and
            ``<col>_delta``. The ``_bau`` suffix is historical (it predates
            the rename to a named reference case) and is kept so every
            existing reader and CSV consumer is unaffected.

    Returns:
        ``df`` with the reference and delta columns appended (reference rows
        difference to zero against themselves).
    """
    if df.empty:
        return df
    ref = (
        df[df["case"] == reference_case][keys + value_cols]
        .rename(columns={c: f"{c}_bau" for c in value_cols})
        .drop_duplicates(subset=keys)
    )
    out = df.merge(ref, on=keys, how="left")
    for col in value_cols:
        out[f"{col}_delta"] = out[col] - out[f"{col}_bau"]
    return out


def cumulative_co2_deltas(headline: pd.DataFrame, reference_case: str) -> pd.DataFrame:
    """Return the running and total CO2 delta vs the reference, per case.

    Args:
        headline: The headline frame from :func:`collect_case_year_frames`
            (needs ``case``, ``year``, ``emissions_mt``; the reported-only
            ``import_co2_mt_reported`` rides along when present, always as its
            own column and never summed into the CO2 delta).
        reference_case: The reference case name.

    Returns:
        A frame with ``case``, ``year``, ``emissions_mt``, ``emissions_mt_bau``,
        ``emissions_mt_delta``, ``cumulative_emissions_mt_delta`` and (when the
        input carries it) the same three columns for
        ``import_co2_mt_reported``. Empty in, empty out.
    """
    if headline.empty:
        return pd.DataFrame()
    value_cols = ["emissions_mt"]
    if "import_co2_mt_reported" in headline.columns:
        value_cols.append("import_co2_mt_reported")
    out = add_reference_deltas(
        headline[["case", "year", *value_cols]], reference_case, ["year"], value_cols
    ).sort_values(["case", "year"])
    for col in value_cols:
        out[f"cumulative_{col}_delta"] = out.groupby("case")[f"{col}_delta"].cumsum()
    return out.reset_index(drop=True)


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
        disk (a backcast or fixture cache) for the report notes.
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


def pivot_vs_reference(
    per_case: dict[str, pd.DataFrame],
    index_cols: list[str],
    value_cols: list[str],
    reference_case: str,
) -> pd.DataFrame:
    """Pivot per-case frames wide and add per-case deltas vs the reference.

    The ``compare_scenarios.py`` convention generalized from two scenarios
    to a ladder: values are summed onto ``index_cols`` per case, pivoted
    wide (columns ``{value}_{case}``), and every non-reference case gains a
    ``{value}_delta_{case}`` column against the reference column.

    Args:
        per_case: Map of case name to its long frame.
        index_cols: Identity columns (e.g. plant keys or company name).
        value_cols: Columns to sum and difference.
        reference_case: The reference case name.

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
    if reference_case in cases:
        for col in value_cols:
            for case in cases:
                if case == reference_case or (col, case) not in wide.columns:
                    continue
                base = (
                    wide[(col, reference_case)]
                    if (col, reference_case) in wide.columns
                    else 0.0
                )
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

    ``plant_by_case`` may be empty (no financial reports on disk), in which
    case only the wind/solar rows are produced.
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


def md_table(df: pd.DataFrame, float_fmt: str = "{:.3f}") -> list[str]:
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
    reference_case: str,
    frames: dict[str, pd.DataFrame],
    cumulative: pd.DataFrame,
    evolution: pd.DataFrame,
    notes: list[str],
) -> None:
    """Write the human-readable scenario-delta summary markdown.

    Headline tables only (the CSVs carry the full detail): the final-year
    headline deltas, the cumulative CO2 delta per case, the final-year
    capacity/generation/CO2 deltas by fuel, the CO2 deltas by zone, and the
    evolution totals — plus a notes section restating what each side line
    means and what is missing.
    """
    iso = meta["iso"]
    headline = frames["headline"]
    lines = [
        f"# Scenario delta report — {iso} — {meta.get('matrix_id', '')}",
        "",
        f"**{meta.get('label', 'deterministic scenario range')}** — deltas are",
        f"case-vs-`{reference_case}` differences on one deterministic case set,",
        "not a probability statement. Dollars are real 2026$.",
        "",
        "## Cases",
        "",
        "| Case | Cache key | Reference? |",
        "|---|---|---|",
    ]
    for case, key in meta["cases"].items():
        lines.append(
            f"| {case} | `{key}` | {'**REF**' if case == reference_case else ''} |"
        )

    lines += ["", f"## Headline deltas vs `{reference_case}` (final cached year)", ""]
    if headline.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(headline["year"].max())
        cols = [
            c
            for c in (
                "case",
                "emissions_mt",
                "emissions_mt_delta",
                "import_co2_mt_reported",
                "unserved_mwh",
                BACKSTOP_MW_COL,
                BACKSTOP_MWH_COL,
                AVG_PRICE_COL,
                f"{AVG_PRICE_COL}_delta",
                "curtailment_twh",
                "clean_share",
            )
            if c in headline.columns
        ]
        lines.append(f"Final cached year on disk: **{last_year}**.")
        lines.append("")
        lines += md_table(headline[headline["year"] == last_year][cols])

    lines += ["", f"## Cumulative CO2 delta vs `{reference_case}` (Mt)", ""]
    if cumulative.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(cumulative["year"].max())
        totals = cumulative[cumulative["year"] == last_year][
            ["case", "year", "cumulative_emissions_mt_delta"]
        ]
        lines.append(f"Running sum of the per-year CO2 delta, through **{last_year}**.")
        lines.append("")
        lines += md_table(totals)

    lines += ["", "## By-fuel deltas (final year)", ""]
    by_fuel = frames["by_fuel"]
    if by_fuel.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(by_fuel["year"].max())
        snap = by_fuel[
            (by_fuel["year"] == last_year)
            & (
                by_fuel["capacity_gw_delta"].abs().gt(0)
                | by_fuel["generation_twh_delta"].abs().gt(0)
                | by_fuel["emissions_mt_delta"].abs().gt(0)
            )
        ][
            [
                "case",
                "fuel",
                "capacity_gw_delta",
                "generation_twh_delta",
                "emissions_mt_delta",
            ]
        ]
        if snap.empty:
            lines.append(
                f"_No by-fuel differences vs `{reference_case}` in {last_year}._"
            )
        else:
            lines += md_table(snap.sort_values(["case", "fuel"]))

    lines += ["", "## By-zone CO2 deltas (final year, Mt)", ""]
    by_zone = frames["by_zone"]
    if by_zone.empty:
        lines.append("_No cached case-years found._")
    else:
        last_year = int(by_zone["year"].max())
        snap = by_zone[
            (by_zone["year"] == last_year) & (by_zone["emissions_mt_delta"].abs() > 0)
        ][["case", "zone", "emissions_mt", "emissions_mt_delta"]]
        lines += md_table(snap.sort_values(["case", "zone"]))

    lines += [
        "",
        f"## Capacity-evolution deltas vs `{reference_case}` (ledger totals, MW)",
        "",
    ]
    if evolution.empty:
        lines.append("_No evolution ledgers found (backcast or fixture cache)._")
    else:
        totals = evolution.groupby(["case", "event", "tech"], as_index=False).agg(
            mw=("mw", "sum"), mw_delta=("mw_delta", "sum")
        )
        totals = totals[(totals["mw"].abs() > 0) | (totals["mw_delta"].abs() > 0)]
        lines += md_table(totals, float_fmt="{:.1f}")

    lines += [
        "",
        "## Notes & definitions",
        "",
        "- Every delta is `case − " + reference_case + "` on the same year.",
        "- `emissions_mt` is attributional in-ISO CO2 on the eGRID generation",
        "  basis: `Σ dispatch × per-generator rate`. There is no marginal rate",
        "  anywhere in the model (plan §2.5 G-E6); the DELTA between two",
        "  full-system runs is itself the consequential number.",
        "- " + IMPORT_CO2_DISCLOSURE,
        "- `unserved_mwh` is the slack column's annual energy. A case whose CO2",
        "  falls while unserved energy rises has not decarbonized — read the two",
        "  together. A CO2 number read under binding slack is understated by",
        "  the shed energy (plan §2.4 G-L4).",
        "- `backstop_built_mw` is the reserve-margin adequacy backstop's gas_ct",
        "  on the books in the year (ledger `thermal_additions` rows tagged",
        '  `source == "reserve_backstop"`, that year or earlier, net of a later',
        "  retirement); `backstop_built_mwh` is those units' energy in the",
        "  year's dispatch. It is the administratively-built share of a curve-ON",
        "  ISO's response (PJM/MISO/NYISO/NEISO/CAISO); energy-only ERCOT has no",
        "  backstop by market design, reads 0.0 here, and reports its adequacy",
        "  through `unserved_mwh` instead (SCN-WS4b adequacy reading).",
        "- `curtailment_twh` / the curtailment CSV are VRE potential minus",
        "  delivered energy; `clean_share` is credit-weighted generation over",
        "  total generation on each case's own crediting rule.",
    ]
    for note in notes:
        lines.append(f"- {note}")

    path.write_text("\n".join(lines) + "\n")
    logger.info("wrote %s", path)


def main(argv: list[str] | None = None) -> None:
    """Build the generic scenario-delta report set from a matrix out-dir."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix-dir",
        type=Path,
        required=True,
        help="Matrix output directory holding meta.json (write_matrix_outputs).",
    )
    parser.add_argument(
        "--reference-case",
        default="REF",
        help="Case every delta is measured against (the plan's REF; §3.0).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Defaults to <matrix-dir>/scenario_report/.",
    )
    parser.add_argument(
        "--years", default=None, help="Optional year restriction, e.g. 2026-2050."
    )
    parser.add_argument(
        "--financial-reports-root",
        type=Path,
        default=None,
        help="Optional root of per-scenario generate_financial_reports.py output "
        "dirs (reports/<cache_key>/); adds thermal captured prices.",
    )
    args = parser.parse_args(argv)

    meta = load_meta(args.matrix_dir)
    iso = str(meta["iso"]).upper()
    cases: dict[str, str] = dict(meta["cases"])
    ref = args.reference_case
    if ref not in cases:
        raise SystemExit(f"reference case {ref!r} not in matrix cases {sorted(cases)}")
    years_filter = parse_years(args.years) if args.years else None
    out_dir = args.output_dir or (args.matrix_dir / "scenario_report")
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = iso.lower()
    notes: list[str] = []

    configs = {case: case_config(iso, key) for case, key in cases.items()}
    for case, config in configs.items():
        if config is None:
            notes.append(
                f"Case `{case}` had no cached config.yaml — default crediting "
                "was assumed."
            )

    backstop_units = backstop_units_for_cases(iso, cases)
    frames = collect_case_year_frames(
        iso, cases, configs, years_filter, backstop_units=backstop_units, notes=notes
    )

    # Headline: every per-year scalar metric, differenced vs the reference.
    headline = frames["headline"]
    if not headline.empty:
        metric_cols = [
            c
            for c in headline.columns
            if c not in ("case", "year") and pd.api.types.is_numeric_dtype(headline[c])
        ]
        headline = add_reference_deltas(headline, ref, ["year"], metric_cols)
    frames["headline"] = headline
    headline.to_csv(out_dir / f"{prefix}_headline_deltas.csv", index=False)

    # Capacity / generation / CO2 by fuel, per year, vs the reference.
    by_fuel = add_reference_deltas(
        frames["by_fuel"],
        ref,
        ["year", "fuel"],
        ["capacity_gw", "generation_twh", "emissions_mt"],
    )
    frames["by_fuel"] = by_fuel
    by_fuel.to_csv(out_dir / f"{prefix}_by_fuel_deltas.csv", index=False)

    # CO2 by zone.
    by_zone = add_reference_deltas(
        frames["by_zone"], ref, ["year", "zone"], ["emissions_mt"]
    )
    frames["by_zone"] = by_zone
    by_zone.to_csv(out_dir / f"{prefix}_emissions_by_zone_deltas.csv", index=False)

    # Cumulative CO2 delta.
    cumulative = cumulative_co2_deltas(frames["headline"], ref)
    cumulative.to_csv(out_dir / f"{prefix}_cumulative_co2_deltas.csv", index=False)

    # Curtailment by tech vs the reference.
    curtailment = add_reference_deltas(
        frames["curtailment"],
        ref,
        ["year", "tech"],
        ["curtailed_mwh", "curtailment_rate"],
    )
    curtailment.to_csv(out_dir / f"{prefix}_curtailment_by_tech.csv", index=False)

    # Evolution ledger deltas.
    events, missing_ledgers = ledger_events_frame(iso, cases, years_filter)
    evolution = add_reference_deltas(events, ref, ["year", "event", "tech"], ["mw"])
    if not evolution.empty:
        # A (year, event, tech) absent from the reference is a genuine zero.
        evolution["mw_bau"] = evolution["mw_bau"].fillna(0.0)
        evolution["mw_delta"] = evolution["mw"] - evolution["mw_bau"]
    evolution.to_csv(out_dir / f"{prefix}_evolution_deltas.csv", index=False)
    if missing_ledgers:
        notes.append(
            "No evolution ledgers for case(s): "
            + ", ".join(f"`{c}`" for c in missing_ledgers)
            + " — builds/retirements/retrofit deltas are partial."
        )

    # Captured price by tech vs the reference. Thermal rows need the financial
    # report parquets; without them the frame carries the VRE pools only.
    plant_by_case: dict[str, pd.DataFrame] = {}
    if args.financial_reports_root is not None:
        from scripts.report_ces_campaign import load_financials

        plant_by_case, _company, missing_fin = load_financials(
            cases, args.financial_reports_root, years_filter, nominal=False
        )
        if missing_fin:
            notes.append(
                "No financial report parquets for case(s): "
                + ", ".join(f"`{c}`" for c in missing_fin)
                + " — thermal captured prices are partial."
            )
    else:
        notes.append(
            "No --financial-reports-root given — captured prices cover the "
            "wind/solar pools only."
        )
    captured = add_reference_deltas(
        captured_price_frame(iso, cases, plant_by_case, years_filter),
        ref,
        ["year", "tech"],
        ["captured_price_usd_per_mwh"],
    )
    captured.to_csv(out_dir / f"{prefix}_captured_price_by_tech.csv", index=False)

    write_markdown_report(
        out_dir / f"{prefix}_scenario_deltas_report.md",
        meta,
        ref,
        frames,
        cumulative,
        evolution,
        notes,
    )
    logger.info("scenario delta report set written → %s", out_dir)


if __name__ == "__main__":
    main()
