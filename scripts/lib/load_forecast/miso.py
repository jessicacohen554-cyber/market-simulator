"""MISO load-forecast spec — 2026 Long-Term Load Forecast Results Summary.

MISO publishes the LTLF as a **slide deck whose series are charts**, not as a
workbook, so there is nothing for a native parser to open: the values are
transcribed into ``data/raw/load-forecast/miso/miso.csv`` and read by the
package's default :func:`~scripts.lib.load_forecast.parse_unified_csv`. Two
kinds of row are in that CSV and both are labelled in ``source_page``:

* values the deck **prints in words** (slide 16's forecast-change drivers:
  2026 peak 124 GW -> 2046 184 GW, range 149-232; data centres +32 GW, range
  22-44; EV +11 GW, range 8-14), and
* series read from the PDF's own **vector path coordinates**, calibrated on the
  axis tick text and validated against a printed label before use — the
  protocol SCN-WS4a established for slide 21. Slide 15's net-energy series
  reproduces the deck's printed "~678" (2026), "~1,104" (2046 Current) and
  "~1,404" (2046 High); slide 21's data-centre series reproduces 9.6 TWh (2026)
  and 266 TWh (2046); slide 24's EV series reproduces the 62 TWh of 2026-2046
  growth the deck reports.

This is an **edition bump**: ``constants.DEMAND_GROWTH_RATES["MISO"]`` cited the
Sept-2025 vintage until this intake (rule 23 ``[R-FROZEN-DERIVE]`` — the
re-derivation is on the source update, never on a residual).

Low/High are drawn only as a **2046 endpoint bar**, so MISO has no published
low/high *series*; the CSV carries the endpoints and nothing is interpolated
here. MISO's driver-level per-LRZ data is behind the 403-walled
``www.misoenergy.org`` host and is not in this datatype
(``data/raw/load-forecast/README.md``).
"""

from __future__ import annotations

from . import IsoSpec, register

# MISO's published regions and their LRZ membership (2026 LTLF slide 21/26).
# Documentary constant — the region -> model-zone map is the consumer's
# (config/iso_configs.py), never this datatype's.
PUBLISHED_REGIONS: dict[str, tuple[int, ...]] = {
    "MISO North": (1, 3),
    "MISO Central": (2, 4, 5, 6, 7),
    "MISO South": (8, 9, 10),
}

SPEC = register(
    IsoSpec(
        iso="MISO",
        edition="2026 LTLF",
        vintage=2026,
        default_basis="net",
    )
)
