"""NREL Standard Scenarios 2024 source for ``benchmark-corridor`` (manual download).

NREL Standard Scenarios 2024 Mid-case regional capacity/generation projections
(2030/2035) — the ReEDS-based projection the corridor memo places next to AEO as
context (``docs/handoffs/cross-model-corridor-2026-07-13.md``). **Manual
download:** the Scenario Viewer data API (``scenarioviewer.nrel.gov``) is
proxy-blocked (502 tunnel) and the OEDI ReEDS S3 mirror does not expose the
Standard Scenarios 2024 regional CSV at a stable path, so the value tables
cannot be fetched in-session (rubric §6 anticipated the "viewer-only retrieval
problem"). When the CSV is downloaded it lands as a unified CSV
(``data/raw/benchmark-corridor/stdscen2024/stdscen2024.csv``) with the canonical
columns and is picked up by the generic reader — no code change. See the raw
README for the exact retrieval steps and the ``DATA NEEDED`` marker.
"""

from __future__ import annotations

from scripts.lib import benchmark_corridor as bc

bc.register(
    bc.SourceSpec(
        source="StdScen2024",
        raw_subdir="stdscen2024",
        isos=("ERCOT", "PJM", "MISO", "NYISO", "NEISO", "CAISO", "national"),
        vintage="2024",
        description=(
            "NREL Standard Scenarios 2024 Mid-case regional capacity/generation "
            "(2030/2035) — projection-vs-projection context (ReEDS)."
        ),
        fetchable=False,  # Scenario Viewer API proxy-blocked; manual CSV export.
        parse=None,  # generic unified-CSV reader
        citation="https://www.nrel.gov/analysis/standard-scenarios.html (Standard Scenarios 2024; Scenario Viewer CSV export)",
    )
)
