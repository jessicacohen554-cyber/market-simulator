"""NYISO load-forecast spec — 2026 Gold Book (Load & Capacity Data Report).

The Gold Book is a PDF, so its tables are transcribed into
``data/raw/load-forecast/nyiso/nyiso.csv`` and read by the package's default
:func:`~scripts.lib.load_forecast.parse_unified_csv`. The source document is
**not duplicated** under this datatype: it already lives at
``data/raw/NYISO/2026-Gold-Book-Public.pdf`` as a gitignored corpus payload with
its verified re-fetch URL and ``SHA256SUMS.txt`` record, and every row's
``source_doc`` cites that path.

Tables carried, each validated when transcribed:

* **I-1a** — NYCA annual energy GWh + summer peak MW + winter peak MW for the
  **Lower / Baseline / Higher** demand forecasts, 2026-2056. Validated against
  the edition's own printed CAGR block (2026-31 energy: -0.16 % / 1.18 % /
  2.58 %).
* **I-11b** — Electric Vehicle Annual Energy Usage by zone A-K ("Total
  Cumulative Impacts", i.e. inclusive of the existing EV stock).
* **I-13a** — Building Electrification Annual Energy Usage by zone A-K
  ("Cumulative **Future** Impacts", i.e. already incremental to the base year).
  This is the wider end-use category — space + water heating, cooking and other
  end uses — so it is carried as ``building_electrification``, not as
  ``heat_pump``.
* **I-14** — Large Load Forecast annual energy GWh by zone A-K. A **large-load**
  forecast, not a data-centre-only one (Zone C's ramp is a semiconductor fab),
  which is why it is carried as ``large_load``.

I-11b/I-13a/I-14 were each validated by checking that the zone columns sum to
the publication's own NYCA column in every year.
"""

from __future__ import annotations

from . import IsoSpec, register

# NYCA load zones as the Gold Book labels them. The zone -> model-zone map is
# the consumer's (config/iso_configs.py), never this datatype's.
NYCA_ZONES: tuple[str, ...] = tuple(f"Zone {c}" for c in "ABCDEFGHIJK")

SPEC = register(
    IsoSpec(
        iso="NYISO",
        edition="Gold Book 2026",
        vintage=2026,
        default_basis="net",
    )
)
