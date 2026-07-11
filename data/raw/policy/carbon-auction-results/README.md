# carbon-auction-results — raw

Source root for the `carbon-auction-results` clean datatype
(`data/dictionary/schema/carbon-auction-results.schema.yaml`). Curated by
`scripts/curate_carbon_auction_results.py`, which reads
`carbon-auction-results.csv` in this directory and writes schema-valid
Parquet to `data/clean/carbon-auction-results/carbon-auction-results.parquet`.

## Why this exists, and how it differs from the sibling datatypes

`rggi-co2-budgets` and `carb-cap-schedule` (landed in an earlier session)
carry each program's published allowance **budget** and **Auction
Reserve/CCR/ECR price-control-band schedule** — the forecast-anchor inputs
`policy/cap_and_trade.py` actually consumes. This datatype instead lands the
**realized per-auction clearing price** — the D1 "refresh anchors" ask
(forecast-driver audit plan §4, N10) and a validation observable: compare
`STATE_CARBON_PRICE_BY_ISO`'s 2023-2025 *annual* anchors (`constants.py:1636`)
against the *quarterly* series here, and compare any future carbon-price
trajectory against the realized auction history — **never fit or pin to it**
(CLAUDE.md rules 1/13; same governance the P-0B sibling session's
capacity-market auction-history datatype uses).

## RGGI: fetched cleanly

`https://www.rggi.org/auctions/auction-results/prices-volumes` is reachable
and publishes a complete table (auction number, date, clearing price,
allowances sold/offered) for every auction since program inception. All 12
auctions in 2023-2025 (Q1 2023 = Auction 59 through Q4 2025 = Auction 70) are
landed with exact dates and full volumes. **Auctions 71-72 (Q1/Q2 2026) are
intentionally excluded** — 2026 is under the CLAUDE.md rule 22 holdout
quarantine, same as the sibling `rggi-co2-budgets` datatype's 2022/2026
omission.

## CARB: `ww2.arb.ca.gov` blocks automated fetches — MANUAL DOWNLOADS NEEDED

Every URL pattern and technique tried against `ww2.arb.ca.gov` failed from
this environment (not a DNS/proxy-domain block like `nrel.gov` — the domain
resolves and connects, but the application layer rejects the request):

| URL | Method | Result |
|---|---|---|
| `.../auction-information/auction-notices-and-reports` | GET, default UA | HTTP 403 |
| `.../auction-information/auction-notices-and-reports` | GET, browser UA | HTTP 503 |
| `.../resources/documents/summary-auction-settlement-prices-and-results` | GET, WebFetch | HTTP 405 |
| `.../sites/default/files/2025-11/nc-nov_2025_summary_results_report.pdf` (static asset) | GET, browser UA | HTTP 405 |
| `.../auction-information` | GET, browser UA | HTTP 405 |

Given this, CARB's per-auction settlement prices in the raw CSV were instead
collected via web search of CARB's own press-release titles/text (each
individually indexed and excerpted, e.g. "the 34th auction... settled at
$27.85") and one EIA *Today in Energy* article that reports on CARB results
directly. Every row's `source_page` is the specific URL the price was
attributed to. **`auction_number` is populated only where a source
explicitly named it** (34-38, 40, 43) — never inferred by arithmetic from
neighboring quarters, even though CARB's numbering is in fact sequential and
quarterly (CLAUDE.md: no value guessing extends to metadata, not just
prices).

**MANUAL DOWNLOADS NEEDED** (a human/browser session should complete these
from `ww2.arb.ca.gov/our-work/programs/cap-and-trade-program/auction-information/auction-notices-and-reports`
or the "Summary of Auction Settlement Prices and Results" page):

- [ ] CARB Q3 2025 (August 2025, Auction 44) settlement price — a search
      result mentioned "35.84 CAD (25.87 USD)" for this auction but that
      figure is identical to the confirmed May 2025 price and could not be
      confidently attributed as August's actual clearing price (rather than
      a stale/misattributed snippet or a different reported quantity) — left
      out rather than risk a wrong number.
- [ ] CARB Q4 2025 (November 2025, Auction 45) settlement price — auction
      confirmed to exist (CARB press release title found), price not
      recovered from search snippets.
- [ ] CARB `allowances_sold`/`allowances_offered` volumes — not recovered
      for any CARB row (search results gave prices, rarely volumes); RGGI
      has full volumes for every row.

## Expected file

`carbon-auction-results.csv` — one row per (program, year, quarter), columns:

```
program,year,quarter,auction_date,auction_number,clearing_price,price_unit,allowances_sold,allowances_offered,source_doc,source_page
```

- `program`: `RGGI` | `CARB`.
- `price_unit`: `usd_per_short_ton` (RGGI's allowance unit) | `usd_per_tonne`
  (CARB/Quebec use metric tonnes CO2e) — **never conflate the two units**;
  RGGI $12.50-26.73/short-ton and CARB $25.87-41.76/tonne are not
  directly comparable without a unit conversion (1 short ton = 0.907185
  tonne).

## DATA (landed)

- [x] RGGI — 12/12 quarters, 2023-2025, exact dates + full volumes.
- [x] CARB — 10/12 quarters, 2023-2025, prices only (no volumes); 2 gaps
      logged above as MANUAL DOWNLOADS NEEDED.

## Consumer

None yet (intake only this session). Future consumer: a "refresh anchors"
update to `STATE_CARBON_PRICE_BY_ISO` (currently annual 2023-2025 averages)
and/or a T3.2-style validation check comparing a carbon-price trajectory
against this realized history (forecast-driver audit plan §2 Tier 3).

## Current program parameters (CCR/ECR triggers, floor) — status note

The task's other ask this covers — "note current program parameters
(CCR/ECR triggers, floor)" — is **already landed data**, from an earlier
session, in the sibling datatypes:

- **RGGI** (`data/raw/policy/rggi-co2-budgets/rggi-co2-budgets.csv`): 2025
  Cost Containment Reserve trigger $17.03/short ton, Emissions Containment
  Reserve trigger $7.86/short ton, minimum reserve (floor) price $2.62/short
  ton (RGGI 2017/2021 Model Rule §5.3/§6.3, +7%/yr and +2.5%/yr escalation
  respectively).
- **CARB** (`data/raw/policy/carb-cap-schedule/carb-cap-schedule.csv`):
  Auction Reserve (floor) price $22.21 (2023) / $24.04 (2024) / $25.94
  (2025) per tonne (17 CCR §95911(c), statutory 5%+CPI escalation).

Both are current as of the latest non-quarantined year (2025) — verified
during this session (no update needed). A **2026 CCR/ECR/floor figure would
already be publicly published** (both escalators are formula-driven and
known a year ahead) but is intentionally **not** added here: the sibling
datatypes' curate scripts quarantine *any* row for budget_year 2026
regardless of metric (CLAUDE.md rule 22), and this datatype's auction-result
rows follow the same line (RGGI auctions 71-72 / any CARB 2026 auction
excluded above) — for consistency, the trigger-price schedule is held to the
same bar rather than carving out a "parameters aren't actuals" exception.
