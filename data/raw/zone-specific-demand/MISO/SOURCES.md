# MISO sub-regional demand provenance

`miso_subba_demand_2023-2025.csv` — hourly metered demand (MWh) by MISO
EIA-930 sub-balancing-area, 2023-01-01 .. 2025-12-31.

Source: EIA Hourly Electric Grid Monitor, API v2
`electricity/rto/region-sub-ba-data` (frequency=hourly, parent=MISO).
Pulled 2026-06-22 with the project EIA_API_KEY.

## 2019–2022 + H1-2026 (2026-07-10 rule-22 holdout intake)

`miso_subba_demand_2019.csv`, `_2020.csv`, `_2021.csv`, `_2022.csv`,
`_2026.csv` — same product/schema as the 2023-2025 file (hourly metered
demand, MWh, by MISO EIA-930 sub-balancing-area), pulled per-year rather
than as one combined file since each year landed as a separate rule-22
holdout-intake batch.

Source: EIA Hourly Electric Grid Monitor, API v2
`electricity/rto/region-sub-ba-data` (frequency=hourly, parent=MISO).
Pulled 2026-07-10 with the project EIA_API_KEY — same product and pull
mechanics as the 2023-2025 file above.

Coverage: `miso_subba_demand_2019.csv` .. `_2022.csv` each span their full
calendar year (2019-01-01 .. year-end); `miso_subba_demand_2026.csv` is
partial-year, 2026-01-01T00 .. 2026-06-30T23 (the latest period available
at fetch time).

**2018 is unavailable at the source** — EIA's `region-sub-ba-data` product
starts 2019-01-01; this is a genuine source-coverage limit, not a fetch
failure, so no 2018 file exists or will be added for MISO under this
product.

**Transport note:** these five files were committed via a direct `git
push` of the plain CSVs (not the gzip+base64 chunked convention described
in the parent `README.md`) — a same-session size probe found `git push`
completes normally for this payload (no HTTP 413), and chunking would have
required moving the files' full gzip+base64 content through the assisting
agent's own context, which is not viable at this row count (megabytes of
high-entropy base64 tokenize far more expensively than the chunking
convention assumes). The committed bytes are verified byte-identical to
the source pull (`cmp` against the original download, plus git blob SHA
match pre/post push).

MISO reports six sub-BAs (LRZ groupings):
  0001 = Zone 1            -> region North
  0027 = Zones 2 and 7     -> region Central
  0035 = Zones 3 and 5     -> region Central
  0004 = Zone 4            -> region Central
  0006 = Zone 6            -> region Central
  8910 = Zones 8, 9 and 10 -> region South

Region crosswalk uses MISO's OFFICIAL North/Central/South definition
(North = LRZ 1 only). See docs/multi-iso/miso-data-audit.md for the
recommended load_share and the zone-definition caveat (the model's
MISO-North docstring describes LRZ 1+2+3, which EIA's bundled 0027/0035
sub-BAs cannot cleanly separate).
