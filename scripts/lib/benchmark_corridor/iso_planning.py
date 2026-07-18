"""ISO planning-document sources for ``benchmark-corridor`` (manual downloads).

The per-ISO planning outlooks the FC-5 corridor confronts (rubric §6 items 3-8):
ERCOT CDR, PJM Load Forecast + RTEP/4R, NYISO Gold Book, ISO-NE CELT, CAISO/CPUC
IEPR + PSP, and the MISO futures/OMS survey. Every one publishes its
capacity-expansion / load / retirement tables as **PDF or XLSX** (no open data
API for the projection tables), so each is a **manual download**: the portal is
reachable but the numbers live inside a document. Extracting a number by hand
and transcribing it from a secondary summary would violate rule 5, so no value
is committed here — each source is a ``DATA NEEDED`` row in its raw README with
the exact document + table locator, and it lands later as a unified CSV
(``data/raw/benchmark-corridor/<subdir>/<subdir>.csv``, canonical columns) that
the generic reader picks up with no code change.

These share the generic unified-CSV parser (there is no per-source *parsing*
logic to isolate — the difference between them is provenance, not format), so
they register in one module. Adding a seventh ISO document is one more
:func:`~scripts.lib.benchmark_corridor.register` call plus a raw subdir.
"""

from __future__ import annotations

from scripts.lib import benchmark_corridor as bc

# (source, raw_subdir, isos, vintage, description, citation)
_MANUAL_SOURCES: tuple[tuple[str, str, tuple[str, ...], str, str, str], ...] = (
    (
        "ERCOT_CDR_2025",
        "ercot-cdr-2025",
        ("ERCOT",),
        "2025-12",
        "ERCOT Capacity, Demand and Reserves (CDR) report, Dec 2025 vintage — "
        "planned capacity additions by tech to 2030, peak-load scenarios, reserve margins.",
        "https://www.ercot.com/gridinfo/resource (Capacity, Demand and Reserves Report, December 2025)",
    ),
    (
        "PJM_LOAD_2026",
        "pjm-load-2026",
        ("PJM",),
        "2026-01",
        "PJM 2026 Load Forecast Report — summer/winter peak and energy growth to ~2036; "
        "paired with the 4R at-risk-retirement study (Feb 2023) for the retirement-GW anchor.",
        "https://www.pjm.com/planning/resource-adequacy-planning/load-forecast-dev-process "
        "(2026 Load Forecast Report); PJM 4R retirement study (Feb 2023)",
    ),
    (
        "NYISO_GOLDBOOK_2026",
        "nyiso-goldbook-2026",
        ("NYISO",),
        "2026",
        "NYISO 2026 Load & Capacity Data report ('Gold Book') — table-form capacity "
        "and load forecasts by zone/statewide.",
        "https://www.nyiso.com/library (2026 Load & Capacity Data 'Gold Book', XLSX/PDF)",
    ),
    (
        "ISONE_CELT_2026",
        "isone-celt-2026",
        ("NEISO",),
        "2026-05",
        "ISO-NE 2026 CELT (Capacity, Energy, Loads, and Transmission) report — energy/peak "
        "forecasts including the winter-flip rows (the D12 shape anchor).",
        "https://www.iso-ne.com/system-planning/system-plans-studies/celt (2026 CELT, XLSX/PDF)",
    ),
    (
        "CAISO_IEPR_2025",
        "caiso-iepr-2025",
        ("CAISO",),
        "2025",
        "CEC IEPR 2025 demand forecast + CPUC Preferred System Plan (D.24-02-047) / "
        "2025-26 TPP new-build by tech to 2035.",
        "https://www.energy.ca.gov/data-reports/reports/integrated-energy-policy-report "
        "(2025 IEPR); CPUC PSP D.24-02-047 / 2025-26 TPP",
    ),
    (
        "MISO_FUTURES",
        "miso-futures",
        ("MISO",),
        "2025",
        "MISO Futures / OMS-MISO Survey capacity-outlook rows — MISO's benchmark side "
        "(absent from the corridor memo's model side, its benchmark side should land anyway).",
        "https://www.misoenergy.org/planning/transmission-planning/miso-futures/ "
        "(MISO Futures); OMS-MISO Survey",
    ),
)

for _source, _sub, _isos, _vintage, _desc, _cite in _MANUAL_SOURCES:
    bc.register(
        bc.SourceSpec(
            source=_source,
            raw_subdir=_sub,
            isos=_isos,
            vintage=_vintage,
            description=_desc,
            fetchable=False,  # table-in-PDF/XLSX; manual download.
            parse=None,  # generic unified-CSV reader
            citation=_cite,
        )
    )
