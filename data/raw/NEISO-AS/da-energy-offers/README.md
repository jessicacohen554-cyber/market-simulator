# NEISO (ISO-NE) Day-Ahead Energy Market historical offer data

Source: ISO Express "Day-Ahead Energy Market Historical Offer Report"
(tree `day-ahead-energy-offer-data`), CSV endpoint (isox_token cookie):

    https://www.iso-ne.com/transform/csv/hbdayaheadenergyoffer?start=YYYYMMDD

One operating day per file (~1.3 MB): per (hour, masked asset) the full DA
supply offer — Economic Max/Min, cold/intermediate/hot startup, no-load, up
to 10 incremental (price, MW) segments (segment 1 begins at Economic Min),
Claim 10 / Claim 30 (claimed 10-/30-minute capability MW — the physics
fast-start segmentation), Unit Status (ECONOMIC / MUST_RUN / UNAVAILABLE).
Masked Lead Participant ID / Masked Asset ID only; ~4-month publication lag.

Purpose: the measured OFFER surface for the NEISO winter scarcity charter
Limb B (scarcity-anticipating DA offer formation, the ERCOT G-22 §8
heterogeneity-preserving analogue). Rule-13 discipline: offer distributions
are derived conditioned on a FORWARD-REPRODUCIBLE tightness driver and are
never fitted to the price residual. Measured PRICES stay validation-only.

## Layout

    hbdayaheadenergyoffer_<YYYYMMDD>.csv    # daily files, gitignored

Regenerate with the committed downloader (train years only, rule 22):

    python scripts/fetch_neiso_da_energy_offers.py --years 2023 2024 2025

KNOWN SOURCE GAPS: the endpoint returns an empty report ("T","0 lines") for
a subset of days (~20% in early sampling; e.g. 2023-01-06) — re-fetch
confirms genuinely absent postings, not transient failures. All 2023-2025
DA>$300 tail-event days ARE published (2023-02-03, 2024-06-20, 2025-06-24,
2025-07-16, 2025-07-29 verified). Delete zero-row files and re-run the
downloader to retry; document residual coverage in the derive provenance.

DATA NEEDED: none beyond the public report.
