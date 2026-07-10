"""Reader for the ``som-competitive-conduct`` clean datatype.

Market-monitor (Potomac Economics SOM / IMM quarterly) competitive-conduct
statistics — price-cost mark-up, output-gap economic-withholding levels, and
the coal economic-offer vs must-run (self-commitment) start decomposition —
hand-transcribed with per-row source_doc/source_page provenance
(``scripts/curate_som_competitive_conduct.py``).

These are grounding/citation inputs, not solve-time series: the MISO coal
offer level (near-cost, mark-up ~ 0; ``_MISO_OFFER_CURVE`` COAL entries in
``pipeline/backcast_config.py``) cites them, and
``tests/test_curate_som_competitive_conduct.py`` freezes the cited values
(CLAUDE.md rule 23 — they re-derive only when a new SOM publishes).
"""

from __future__ import annotations

import pandas as pd

from scripts.lib import clean_io


def read_som_conduct(iso: str) -> pd.DataFrame:
    """Return an ISO's SOM competitive-conduct rows from ``data/clean``.

    One row per ``(iso, year, period, fleet_segment, metric)`` — see the
    schema for the metric vocabulary. Raises ``FileNotFoundError`` when the
    ISO has no curated partition (run
    ``python scripts/curate_som_competitive_conduct.py`` first).
    """
    return clean_io.read_clean("som-competitive-conduct", iso=iso.upper())
