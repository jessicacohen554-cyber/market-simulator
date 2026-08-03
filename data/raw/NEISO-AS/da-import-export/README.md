# NEISO (ISO-NE) Day-Ahead SUBMITTED import-offer / export-bid book

One ISO Express report, the external-transaction analogue of the sibling
`da-energy-offers/` (internal generator offers) and `da-demand-bids/`
(demand + virtuals). Served from the **static** historical-report tree (the
`transform/csv/hbdayaheadimpexp` form 404s), one operating day per file
(~0.35 MB), still behind the report page's `isox_token` cookie:

    https://www.iso-ne.com/static-transform/csv/histRpts/da-import-export/hbdayaheadimpexp_<YYYYMMDD>.csv

Report title: *Day-Ahead Import and Export Historical Offer and Bid Report*
(ISO Express → Pricing → "Real-Time and Day-Ahead Import Offer and Export Bid
Data"). Published on the first day of the fourth month following the
operating month, per the FERC-ordered lag.

## Columns

`Day`, `Hour Ending`, `Market Type` (always `DA` in this tree), `Masked
Customer ID`, `Masked Originating Location ID`, `Masked Destination Location
ID`, `Emergency Flag`, `Direction`, `Transaction Type`, `Price`, `Bid MW`.

| field | values | meaning |
|---|---|---|
| `Direction` | `IMPORT` / `EXPORT` | supply into the control area / demand leaving it |
| `Transaction Type` | `DISPATCHABLE` | priced — clears against the LMP (`Price` populated) |
| | `FIXED` | self-scheduled, price-insensitive (`Price` blank) |
| `Bid MW` | MW | per-hour block width; one row per hour per transaction |

Measured shape (2025-06-24 / 2025-12-15): 3,847 / 4,344 day-rows, IMPORT
3,330 / 3,696 vs EXPORT 517 / 648, DISPATCHABLE 2,010 / 2,105 vs FIXED
1,837 / 2,239.

## Why this corpus exists — and what does NOT exist (neiso-79)

**ISO-NE publishes no day-ahead CLEARED external-transaction series and no
day-ahead net-interchange series anywhere on ISO Express.** Verified against
the full report trees: every interchange report on the Grid tree is
real-time/actual (*Real-Time Actual Scheduled Interchange*, *External
Interface Metered Data*, and the 15-minute and five-minute variants), the
Load & Demand tree's only day-ahead cleared quantity is *Hourly Day-Ahead
Cleared Demand*, and the Pricing tree's only external report is this
submitted book. The authenticated Web Services API adds
`/actualinterchange`, `/hourlybainterchange`, `/fiveminuteexternalflow` — all
**actual**, not day-ahead — and `/hbimportexport`, which is this same
submitted report.

That absence is a real finding, not a gap to be papered over. What a cleared
series would have supplied is a **check**, not the crossing quantity itself:
it would let a traversal verify that the import book actually cleared where
the crossing says it did. What it must **not** be substituted with is
EIA-930 interchange — that is ACTUAL NET hourly interchange, a different
quantity at a different grain from DA scheduled imports, and swapping one for
the other is exactly the rule-14 `[R-ACCURATE]` grain-misalignment trap.
`scripts/data/derive_neiso_import_tranches.py` uses the EIA-930 series for
its own (different) purpose and is untouched by this corpus.

The submitted priced book is, for the neiso-79 crossing-quantity
reconciliation, **strictly better than a cleared quantity would have been**:
imports enter ISO-NE's day-ahead market as priced supply offers, so crossing
them jointly with the internal offer book lets the import depth clear
*endogenously* instead of being assumed. That is what dissolves the neiso-76
§D depth sensitivity (a flat 3 GW allowance halved the traversal).

## Layout

    hbdayaheadimpexp_<YYYYMMDD>.csv      # submitted DA external book, one per day

**Gitignored** (the NYISO-archive push-limit precedent). Regenerate with the
committed fetcher:

    python scripts/data/fetch_neiso_da_import_export.py --years 2023 2024 2025

Known source gaps: the endpoint answers an unpublished operating day with a
~31-byte stub rather than a 404 — the same publication pattern the sibling
`da-energy-offers/` and `da-demand-bids/` READMEs document (2023-01-15 is one
such day). The fetcher counts these separately as "empty postings".

Rule 13: this is a measured market input on the offer/bid side, read only by
probes; nothing derived from it is armed in any solve, and no `data/` loader
or derive reads this directory. Coverage policy: train years 2023-2025 only
(CLAUDE.md rule 22).

DATA NEEDED: none beyond the public report. The day-ahead **cleared**
external series does not exist publicly (above); do not add a proxy for it.
