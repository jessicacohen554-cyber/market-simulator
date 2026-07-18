"""Reader for the ``benchmark-corridor`` clean datatype (FC-5 external corridor).

The model-/scorer-side consumption seam for the external forecast-corridor
anchors — 2030/2035/2040 capacity mix, generation (energy) mix, and
power-sector CO2 by ISO/region, per external source (EIA AEO2025, NREL Standard
Scenarios, ISO planning documents). Curated by
``scripts/data/curate_benchmark_corridor.py``; read here through
:func:`scripts.lib.clean_io.read_clean` (path resolved by
``market_sim.config.paths``), exactly like every other clean datatype.

**Context, never a fit target (CLAUDE.md rule 13).** These anchors feed the
FC-5 external-corridor check as CONTEXT: a model-vs-benchmark divergence is
reported *with an explanation* (the cross-model-corridor discipline), and is
never scored as a miss and never a value the model is tuned toward.
:func:`corridor_context` builds the committed anchor table the forecast scorer
(``scripts/forecast_verdict.py --benchmark-corridor``) reads — anchor rows carry
no verdict, and the missing-source list makes an unfinished intake visible
rather than silently passing.
"""

from __future__ import annotations

import pandas as pd

from scripts.lib import clean_io

DATATYPE = "benchmark-corridor"

# The FC-5 benchmark-source inventory (forecast determination rubric §6). The
# loader derives "missing sources" against this list when the curation-time
# registry is not in scope; a consistency test ties it to the registered source
# specs so the two never drift. Each id carries a one-line provenance.
EXPECTED_SOURCES: dict[str, str] = {
    "AEO2025": "EIA Annual Energy Outlook 2025 regional electricity tables (fetchable)",
    "StdScen2024": "NREL Standard Scenarios 2024 Mid-case regional cap/gen (manual)",
    "ERCOT_CDR_2025": "ERCOT Capacity, Demand and Reserves report, Dec 2025 (manual)",
    "PJM_LOAD_2026": "PJM 2026 Load Forecast + 4R at-risk retirement study (manual)",
    "NYISO_GOLDBOOK_2026": "NYISO 2026 Load & Capacity Data 'Gold Book' (manual)",
    "ISONE_CELT_2026": "ISO-NE 2026 CELT report (manual)",
    "CAISO_IEPR_2025": "CEC IEPR 2025 + CPUC PSP / 2025-26 TPP (manual)",
    "MISO_FUTURES": "MISO Futures / OMS-MISO survey capacity outlook (manual)",
}

# Fields surfaced in the FC-5 context table (compact; full provenance stays in
# the clean parquet). `quantity` and `target_year` are the labels the scorer
# prints, so they are always present.
_CONTEXT_FIELDS: tuple[str, ...] = (
    "source",
    "iso",
    "region",
    "scenario",
    "target_year",
    "quantity",
    "tech",
    "value",
    "unit",
    "note",
)


def load_benchmark_corridor(
    *,
    iso: str | None = None,
    source: str | None = None,
    quantity: str | None = None,
    validate: bool = True,
) -> pd.DataFrame:
    """Read the curated benchmark-corridor anchors, optionally filtered.

    Returns the tidy long frame (one row per source/iso/region/scenario/
    target_year/quantity/tech). Raises ``FileNotFoundError`` with a regenerate
    hint if the clean partition is absent (the clean tree is gitignored /
    regenerated from committed raw by ``curate_benchmark_corridor.py``).
    """
    df = clean_io.read_clean(DATATYPE, validate=validate)
    if iso is not None:
        df = df[df["iso"] == iso]
    if source is not None:
        df = df[df["source"] == source]
    if quantity is not None:
        df = df[df["quantity"] == quantity]
    return df.reset_index(drop=True)


def iso_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Sum the region rows to per-ISO totals (capacity/generation/CO2 are extensive).

    Groups by (source, iso, vintage, scenario, target_year, quantity, tech, unit)
    and sums ``value`` — so a multi-region ISO (PJM/MISO/NYISO/CAISO) collapses
    its EMM-subregion rows into one ISO total. ``region`` is replaced with
    ``"<iso> (sum of N regions)"``.
    """
    if df.empty:
        return df.copy()
    grp = [
        "source",
        "iso",
        "vintage",
        "scenario",
        "target_year",
        "quantity",
        "tech",
        "unit",
    ]
    agg = df.groupby(grp, dropna=False, as_index=False)["value"].sum()
    counts = df.groupby(grp, dropna=False, as_index=False)["region"].nunique()
    agg = agg.merge(counts.rename(columns={"region": "_nregions"}), on=grp, how="left")
    agg["region"] = (
        agg["iso"].astype(str)
        + " (sum of "
        + agg["_nregions"].astype(str)
        + " regions)"
    )
    return agg.drop(columns=["_nregions"])


def corridor_context(
    df: pd.DataFrame,
    *,
    missing_sources: list[str] | None = None,
    iso: str | None = None,
) -> dict:
    """Build the FC-5 CONTEXT table the forecast scorer reads (never a fit target).

    Anchor rows carry NO ``verdict`` — the per-row divergence disposition is
    authored by the FC-5 scoring session against the model snapshots, never
    here. ``missing_sources`` (registered/expected sources not yet on disk) is
    surfaced so an unfinished intake reads as SKIPPED-with-context, holding a T2
    promotion, rather than silently passing (rubric §3/§6).
    """
    frame = df if df is not None else pd.DataFrame(columns=list(_CONTEXT_FIELDS))
    if iso is not None and not frame.empty:
        frame = frame[frame["iso"] == iso]
    present = sorted(frame["source"].unique().tolist()) if not frame.empty else []
    if missing_sources is None:
        missing_sources = sorted(set(EXPECTED_SOURCES) - set(present))
    rows = []
    for _, r in frame.iterrows():
        rows.append({k: (None if pd.isna(r[k]) else r[k]) for k in _CONTEXT_FIELDS})
    return {
        "datatype": DATATYPE,
        "context_only": True,
        "generated_from": "benchmark-corridor clean datatype (FF-0F intake); FC-5 context, never a fit target (rule 13)",
        "iso": iso,
        "sources": present,
        "missing_sources": sorted(missing_sources),
        "rows": rows,
    }
