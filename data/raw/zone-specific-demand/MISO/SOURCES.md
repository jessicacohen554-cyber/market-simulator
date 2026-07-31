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

**2018 is unavailable through the API** — EIA's `region-sub-ba-data` product
starts 2019-01-01. That is a genuine limit of *that* product, not of the data:
see the H2-2018 correction below.

## H2-2018 (2026-07-31 rule-22 holdout intake) — the API's start date is not the data's

`miso_subba_demand_2018.csv` — **26,454 rows**, 4,409 hours × the same six
sub-BAs, `2018-07-01T06` .. `2018-12-31T23`. The claim above that 2018 "will
never be added" was **half wrong**: EIA publishes the same sub-BA demand,
without registration, in the Hourly Electric Grid Monitor's six-month bulk
extracts, and those reach back to **2018-07-01** —

    https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_SUBREGION_2018_Jul_Dec.csv

H1-2018 genuinely does not exist (`EIA930_SUBREGION_2018_Jan_Jun.csv` serves an
HTML "page not found" body with a 200 status): sub-BA reporting began mid-2018.

**Clock, verified rather than assumed.** The API's `period` for this product is
the **UTC hour-ending** stamp, not a local one. Joining the committed
`miso_subba_demand_2019.csv` to the 2019-H1 Grid Monitor extract on `UTC Time at
End of Hour` reproduces **4,343 / 4,343** values exactly; every other offset from
−8 h to +8 h matches essentially nothing (the next best is 0.2 %). The Grid
Monitor's own "Local Time" column is NOT used — for MISO it is stamped at a
fixed UTC−5 year-round, which is neither the API's convention nor Central time.

**Producer:** `scripts/data/fetch_eia930_subba_demand.py --iso MISO --years 2018`
(key-free; MERGE-never-replace; partitioned by *period* year, so the handful of
hours whose UTC stamp spills into the neighbouring year stay in the neighbour's
file — this file has **zero** overlap with `miso_subba_demand_2019.csv`). Output
matches the committed convention byte for byte: CRLF, period-descending with
sub-BA ascending inside each hour, zero-padded 4-character codes, and the
2019-2022-era `subba-name` vintage ("Zone 1 - MISO", which the 2026 file drops).

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
