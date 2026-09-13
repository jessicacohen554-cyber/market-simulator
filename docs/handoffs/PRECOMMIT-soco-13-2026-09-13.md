# PRECOMMIT — SOCO-13: the FERC-EQR footprint hourly price index, STOP-gated (card S2 option a)

**Lane** SOCO-13 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/soco-13-eqr-price-84k5yi` · **Base** `33a7c961` (`origin/main`, the charter's pin) ·
**Data profile** `shared` · **Charter** `docs/multi-iso/soco-addition-plan-2026-09.md` §8 W1 SOCO-13,
§2.6, §3 card S2, §5 row SOCO-13 · **Ruling** card S2, both limbs (owner, 2026-09-13) · **Sister
precedent** `docs/handoffs/PRECOMMIT-nwpp-13-2026-09-13.md` / `FINDING-nwpp-13-2026-09-13.md`.

**This document is pushed BEFORE any price or quantity value is read.** Every filter, every
allocation rule and every gate number below is declared here and is not re-cut after the series
is seen. A gate written or loosened after seeing the series would make this a fitted benchmark —
the object rules 1 `[R-STRUCT]` and 13 `[R-MEASURED]` exist to refuse — and every later SOCO
price criterion would be scored against a number chosen to look right rather than a number that is
right. The program is not blocked on my success: card S2 limb (b) is ruled and lane SOCO-22 is
building it. There is therefore no reason to land a series that does not clear its own bar, and
I say so here so the record shows I knew it before the fetch. A documented NO is a complete lane.

---

## 0. What was read before this document, and what was not

The charter asks that the PRECOMMIT precede the data. It cannot precede *metadata*: a footprint
filter has to be written against the spellings the filers actually use, and a product filter
against the field vocabulary that exists. The line drawn is the sister lane's — **values vs.
structure** — and it is stated here so the desk can check it:

| read before this document | what of it | prices or MWh seen? |
|---|---|---|
| `eqrreportviewer.ferc.gov` index page and its Downloads tab (one ASP.NET postback) | tab layout; the bulk-file URL grammar; the 14 quarterly `CSV_<year>_Q<q>.zip` links 2023 Q1 → 2026 Q2 with `Content-Length` and `Last-Modified` from `HEAD` | no |
| `CSV_2024_Q3.zip` central directory (range requests) and then the whole file (3.94 GB, downloaded) | 3,521 inner per-filing zips; the four CSV kinds and their **header rows** | no |
| **catalogue pass** over that one quarter (`scratchpad/catalogue_phase2.py`, reproduced in the FINDING), `usecols` restricted to the categorical and datetime columns — `transaction_quantity`, `price`, `standardized_quantity`, `standardized_price`, `total_*_charge` were **never read into memory** | distinct values and **row counts** of `point_of_delivery_balancing_authority`, `point_of_delivery_specific_location`, `product_name`, `class_name`, `term_name`, `increment_name`, `increment_peaking_name`, `type_of_rate`, `rate_units`, `time_zone`, `exchange_brokerage_service`, seller / customer names; the distribution of `end − begin` spans; one inner zip (`CSV_2024_Q3_5596771_1561913.ZIP`, 2.55 MB) that Python's `zipfile` cannot open | **no** — counts of rows and hours only |
| `eqronline.ferc.gov` filing guide and links PDFs | submission mechanics; host list | no |
| SEEM auditor page `/auditor-reports/` | the 39 monthly PDF links 2023-01 → 2025-12; all 36 in-window monthly reports **downloaded, not opened** | no |
| `data/raw/soco-planning/transcriptions/SEEM_Auditor_Monthly_Report_2026-07.txt` | the report's **structure** — where the monthly average clearing price sentence sits (a 2026 month, outside the window) | one out-of-window value ($35, July 2026) |
| `data/raw/gas-prices/eia_delivered_gas_AL_monthly_2023-2025.csv` (SOCO-12's committed file) | header + first four rows, to confirm the schema | four 2023 gas prices ($/Mcf), which are an INPUT to anchor D4, not a price of the index |
| `scripts/calibration_verdict.py` | `PRICE_MEAN_TOL = 0.10`; `PRICE_MONTH_COVERAGE_MIN = 0.90`; the masked path (`_covered_months` / `rt_cov.mon`) | — |
| `scripts/data/derive_actual_lmp.py`, `build_spp_lmp_reference.py`, `build_nwpp_weim_price_index.py` | `_STD_TZ`, `_std_hour_index`, the 8760 non-leap fixed-standard-time calendar, the sidecar schema, the `gate --land` shape | — |
| `src/market_sim/config/constants.py`, `data/fuel/electric_power.py` | `HEAT_RATE_BINS["gas_cc"]`, `MCF_TO_MMBTU = 1.036` | — |

The price values in my possession are the charter's own: the SEEM auditor's annual weighted-average
clearing prices **~$30 / ~$23 / ~$32 per MWh** for 2023 / 2024 / 2025 (SOCO-12 §0.2). No SOCO model
run exists and none is used. **What was NOT read:** any EQR price or quantity column, any SEEM
monthly report inside the window, any EIA-923 or ICE price.

---

## 1. The object being built — and what it is not

A **footprint-hourly, volume-weighted price of short-term wholesale energy delivered inside the
SOCO balancing authority**, built from the transaction rows every FERC-jurisdictional seller files in
its Electric Quarterly Report: for each hour, `Σ price_i × MWh_i,h / Σ MWh_i,h` over the
transactions delivering in that hour at a SOCO point of delivery. It is a **measured bilateral
market price** — the price at which energy actually changed hands in this footprint — which is the
rule-13 test: it regenerates for a forward year from the same filings and responds to conditions.

It is **not** an LMP (no market clears one), **not** a day-ahead price (the sidecar's `da` column
will be NaN for every hour and the rubric's DA diagnostic reads SKIPPED), and **not** the price of
all the footprint's energy: Southern's own dispatch is cost-based and never transacts. Whether the
traded slice is deep enough, and whether its price is the marginal-energy price of the region,
is exactly what gates D2, D3 and D4 decide, with numbers fixed here.

---

## 2. (a) The FOOTPRINT filter — delivery point, not counterparty

**Rule.** A row is in the footprint iff `point_of_delivery_balancing_authority`, upper-cased and
stripped, is **`SOCO`**. Nothing else defines the footprint.

Why the delivery point and not the seller or buyer: an LMP is the price of energy *at a location*.
A marketer's sale to Alabama Power at a SOCO point and Southern's sale to a Georgia cooperative at a
SOCO point are both prices of energy in this footprint; Southern's export to TVA, filed at a TVA
delivery point, is the price of energy in TVA's. The filter therefore keys on the one field whose
meaning is locational.

Spellings, from the catalogue pass (§0): **`SOCO` is the only spelling in use** — 86,371 of the
167,360,233 transaction rows in 2024 Q3, and no `SOUTHERN` / `SOCO ` / `SOUTHERN COMPANY` variant
exists among the 80+ POD codes seen. Rows whose POD BA is another code but whose
`point_of_delivery_specific_location` names Southern (2024 Q3: `MISO` 12,345 · `TVA` 5,199 ·
`HUB` 5,184 rows, e.g. location `TVA/SOCO`) are **not** admitted — the seller chose the BA code,
and a location string is not a balancing-authority attribution. Their count is reported, not used.

**Counterparty exclusions, declared now.** Rows in which **both** the seller and the customer are
Southern Company subsidiaries (`Alabama Power`, `Georgia Power`, `Mississippi Power`,
`Southern Power`, `Southern Company Services`, `Southern Electric Generating`, matched
case-insensitively on the name fields) are **excluded**: an intra-corporate transfer is not an
arm's-length price. Every other seller and customer is admitted, and the FINDING reports seller
concentration (top-5 share and HHI of indexed MWh) at full magnitude so the reader can see whose
price this is.

---

## 3. (b) The PRODUCT filter — short-term energy, and nothing that is not

A footprint row enters the index iff **every** condition holds:

| field | admitted | excluded, and why |
|---|---|---|
| `product_name` | `ENERGY` (case-insensitive: the catalogue carries both `ENERGY` and `Energy`) | everything else — `REQUIREMENTS SERVICE` (17,210 rows in 2024 Q3: cost-based full-requirements supply), `CAPACITY`, `BOOKED OUT POWER` (a financial unwind, no delivery), `ENERGY IMBALANCE`, `TOLLING ENERGY`, `OTHER`, reserves, `SCHEDULE SYSTEM CONTROL & DISPATCH`, `REACTIVE SUPPLY & VOLTAGE CONTROL`, `GRANDFATHERED BUNDLED`, `FUEL CHARGE` |
| `class_name` | `F`, `NF` (firm / non-firm) | `UP` (unit power — unit-contingent, priced on the unit), `N/A` |
| `term_name` | `ST` (short-term, < 1 year) | `LT` — a long-term contract price is a hedge struck years earlier, not the price of energy in the hour |
| `increment_name` | `5`, `15`, `H`, `D` — the sub-daily and daily **pricing** increments | `W`, `M`, `Y`, `LT`, `N/A` — weekly and longer blocks (charter (b)). **This keys on the pricing increment, never on how the rows were reported:** the catalogue shows 24,762 `M`-increment ENERGY rows filed one row per hour (span 0.98 h) in 2024 Q3 — a monthly-priced product carries one price for its month however finely its deliveries are itemised, and it is excluded |
| `type_of_rate` | `Fixed` / `FIXED`, `Formula` / `FORMULA`, blank | **`Electric Index`** — SOCO has no index, so an index-priced deal settles on a neighbouring hub's number, gate G17's forbidden import; **`RTO/ISO`** — a transaction settled at an RTO's price is that RTO's LMP at the seam (the catalogue's `RTO/ISO` rows sit against MISO as the customer), and admitting it would let MISO-South's price into SOCO's benchmark through the back door, which G17 refuses absolutely. A blank rate type is a filing omission on a row that still carries a price; it is admitted and its share reported |
| `rate_units` | `$/MWH`, `$/KWH` — the two energy-denominated units in the catalogue (FERC's `standardized_price` puts both on $/MWh) | `$/KW-MO`, `$/MW-MO`, `$/MW`, `$/KVA`, `FLAT RATE` / `Flat Rate` — a per-capacity or flat rate standardised to $/MWh is a capacity charge in disguise |
| `standardized_quantity`, `standardized_price` | both numeric, quantity > 0 | missing / non-numeric / non-positive quantity |

Every match is on the upper-cased, stripped field value. The FINDING reports the MWh excluded by
**each** row of this table, so the reader can see what the index is not made of. For scale, the
2024 Q3 catalogue puts the candidate set at `ST` × ENERGY × {`15`: 9,953 · `H`: 8,914 · `D`: 3,277}
rows before the rate-type, units and counterparty screens — the `15`-increment rows being, by their
15-minute spans, almost certainly SEEM matches (§5 D3's overlap measurement).

**The one product judgement that is a judgement.** `increment_peaking_name` (`P` / `OP` / `FP`)
is admitted in all three values: a peak block and an off-peak block are both energy in the hours
they cover, and the allocation in §4 puts each in its own hours.

---

## 4. (c) The AGGREGATION, the allocation and the CLOCK

- **Price and quantity fields:** `standardized_price` ($/MWh) and `standardized_quantity` (MWh) —
  FERC's own normalisation of the filer's `price` / `transaction_quantity` / `rate_units`.
- **Row time → UTC.** `transaction_begin_date` / `transaction_end_date` are `YYYYMMDDHHMM`
  wall-clock in the row's `time_zone` code. The catalogue's codes and their conversions, fixed now:
  `CP` → `America/Chicago`, `EP` → `America/New_York`, `MP` → `America/Denver` (prevailing, through
  the IANA zone); `CS` → UTC−6, `CD` → UTC−5, `ES` → UTC−5, `ED` → UTC−4, `PS` → UTC−8 (fixed
  offsets). Any other code is a row-level defect: the row is dropped and counted.
- **Block → hours.** `end` is adjusted to a clock boundary: `end == begin` reads as one hour;
  an `end` minute of 59, 14, 29 or 44 (the catalogue's hourly and quarter-hourly rows are filed
  `:00 → :59` and `:00 → :14`) reads as `end + 1 min`. The row covers the clock hours in `[begin, end)`,
  `n = ceil((end − begin) / 1 h)`, and its MWh are allocated **uniformly**, `MWh / n` to each hour,
  at the row's price. A block product *is* a flat MW delivery across its hours, so uniform is the
  physical allocation, not an estimate.
- **Rows spanning more than 25 hours are excluded** from the hourly index whatever their
  `increment_name` says (25, not 24, so the fall-back day's daily block survives). A weekly or
  monthly aggregate carries one price for many hours; smearing it uniformly would flatten the very
  shape C3b scores. Their MWh are reported by span class.
- **Deduplication.** Exact duplicate rows (all 26 fields) across a quarter's filings are collapsed
  to one; the count is reported.
- **The hourly index.** `P_h = Σ_i p_i × q_i,h / Σ_i q_i,h` over the allocated rows of hour `h`.
- **Thin hours are NaN.** An hour with **fewer than 2 source rows** or **less than 20 MWh** of allocated
  volume is NaN (a single trade is a price, not a market; 20 MWh is < 0.1 % of an average
  footprint hour). Nothing is carried forward, nothing is interpolated — not toward a neighbour,
  and never toward anything a model produces.
- **Clock.** Each UTC hour is indexed onto the model's **fixed non-leap 8760-hour clock on Central
  STANDARD time (`Etc/GMT+6`)** through `derive_actual_lmp._std_hour_index` imported unchanged.
  Reasons: (i) SOCO-10 closed gate G19 by measurement — the `SOCO` BA files EIA-930 on the
  **Central** clock (`convert_eia930.BA_TIMEZONES["SOCO"] = "US/Central"`), and the timezone is a
  property of the BA, not of a Georgia zone; (ii) every committed `_validation-source` sidecar sits
  on its ISO's fixed *standard* clock, the same calendar the EIA-930 loader builds the demand on
  (SPP-51c is the record of what a clock defect does to a load-bearing criterion); (iii) a fixed
  offset has no DST ambiguity. **Dependency, stated:** `derive_actual_lmp._STD_TZ` carries no
  `SOCO` key at this base sha; registering `"SOCO": "Etc/GMT+6"` is SOCO-20's, routed in the
  FINDING. The raw store keeps the UTC hour, so any other canonical hour is a re-index of committed
  bytes, never a re-fetch.

---

## 5. (d) THE STOP GATE — pass/fail numbers, fixed now

The gate is **STOP-only**: it can refuse the series; it can never promote a run, and it never reads
any model residual (none exists). All of D1–D5 must PASS, in every year, for the verdict
**SERIES LANDED**; any one failing is **NO**.

### D1 — coverage

| leg | PASS requires |
|---|---|
| D1.1 annual | **≥ 8,322** non-NaN footprint hours in each of 2023, 2024, 2025 (95 % of 8,760 — the sister lane's full-year bar) |
| D1.2 monthly | **every** calendar month ≥ **90 %** of its hours non-NaN — `calibration_verdict.PRICE_MONTH_COVERAGE_MIN`, the scorer's own definition of a month it will score; a benchmark that cannot clear the scorer's month bar in some month makes that month unscorable, and a year with an unscorable month is not a benchmark year |

There is no partial-by-retention year here (EQR is permanent), so no masked-path carve-out is
declared. The diurnal distribution of NaN hours is reported (a series thin only overnight is
biased in shape even when it clears the count).

### D2 — depth and thinness

| leg | PASS requires, in each year |
|---|---|
| D2.1 thin hours | share of non-NaN hours resting on **fewer than 5** source rows (a 15-minute row counts as one) ≤ **25 %** |
| D2.2 volume share | indexed MWh (after §3 and §4) ÷ SOCO demand MWh (`data/raw/eia-930-hourly/SOCO hourly.parquet::Demand`, the same series the model dispatches) ≥ **5.0 %** |

Why 5 %: the sister lane's argument, unchanged. The short-term bilateral layer occupies, relative
to Southern's cost-based self-supply, the position an RT market occupies relative to its DA
market — it clears the deviation, and the RT LMP is nonetheless the benchmark this rubric scores in
every ISO. A traded slice below one-twentieth of the footprint's energy would be thinner than that
layer and its price the price of a residual. Five per cent is a convention on that argument, written
down before the fetch so that it cannot become a derived number afterwards.

### D3 — reconciliation against the SEEM auditor's clearing price (public anchor; independence qualified)

**Anchor rows.** For each month 2023-01 → 2025-12, the **average clearing price** the SEEM
Independent Market Auditor states in the text of that month's public report (the sentence of the
form *"The average clearing price in July was $35/MWh"*, page-cited), and the annual
weighted-average price from each annual report. Transcribed after this document is pushed, into
`data/raw/ferc-eqr/seem_auditor_monthly_prices.csv` with report + page per row. Where a month's
report states no such value, that month is absent from the anchor and the FINDING says so.

**Index side.** `I_m` = the MWh-weighted mean of the hourly index over the month's hours (UTC
month, the auditor's own basis being calendar months on the platform's Eastern clock — a boundary
error of a few hours in 720 cannot move a 15 % band).

| leg | PASS requires |
|---|---|
| D3.1 level | for each year, `|I_year − S_year| / S_year ≤ 15 %`, `S_year` the auditor's annual weighted-average price |
| D3.2 shape | Pearson `r(I_m, S_m)` across the months both series carry ≥ **0.80** |
| D3.3 support | ≥ 30 of the 36 months carry an anchor value |

**Why 15 % and not the rubric's 10 %.** The sister lane held its benchmark to `PRICE_MEAN_TOL`
because Mid-C Peak prices the same object its index priced (the Northwest's bilateral energy). SEEM
does **not** price this index's object, on the four grounds SOCO-12 §0.2 established: it is
SEEM-wide (24 members across 12 states), it clears a 15-minute residual exchange at a
split-the-savings price, it is ~0.5 % of SOCO demand, and it is monthly. It is a **boundedness**
anchor — the two prices are both marginal-energy prices of one gas-driven region and should agree in
level to within the difference of their constructions, which I put at 15 % ex ante. A 10 % bar would
test an identity that is false by construction; a 25 % bar would admit a series that prices a
different quantity (a capacity-laden or index-priced leakage). If the measured gap exceeds 15 % the
gate FAILS and the NO is written; the tolerance is not re-cut.

**Independence, stated honestly.** SEEM trades are bilateral and are themselves EQR-reportable
(SEEM's own FAQ routes price disclosure to FERC reporting), so some rows of the anchor's
underlying transactions may also be rows of the index. The auditor's *computation* is independent
— a third party over the platform's own records — but the *transactions* may overlap. The FINDING
measures the overlap where a field makes it measurable (`exchange_brokerage_service` naming SEEM,
or `increment_name` = `15`) and reports it; where it is not measurable, the FINDING says so. D3 is
kept as a gate either way because a level disagreement would still be diagnostic; the fully
independent anchor is D4.

### D4 — boundedness against the fuel-cost stack (fully independent)

**Anchor.** `FC_m` = the marginal fuel cost of an F-class combined cycle burning that month's
delivered gas: EIA `N3045AL3` (Alabama, delivered to electric power, $/Mcf — the only footprint state
EIA publishes through 2025-12; SOCO-12 §4) ÷ `MCF_TO_MMBTU = 1.036` × `HEAT_RATE_BINS["gas_cc"]["f_class"] = 6.7`
MMBtu/MWh. Georgia and Mississippi are reported beside it for the months they cover (through
2024-12). No VOM, no adder: the anchor is a fuel cost, not a price estimate, and it is used only for
the two comparisons below.

| leg | PASS requires |
|---|---|
| D4.1 shape | Pearson `r(I_m, FC_m)` over the 36 months ≥ **0.70** — gas is the dominant driver of Southeast wholesale prices; a series that does not track it is not an energy price |
| D4.2 level | for each year, `I_year / FC_year` within **[0.8, 2.0]** — below 0.8 the index is priced off something cheaper than the marginal gas unit in a gas-on-the-margin year (cost-based affiliate rows leaking); above 2.0 it carries something that is not energy (capacity, an index import, a units defect) |

Declared ex ante: the band was checked for plausibility against the only price values in my
possession (the auditor's ~$30 / ~$23 / ~$32) and the committed gas prices — SEEM itself would sit
inside it in all three years. That is what a boundedness band is for; it says nothing about where
the EQR index will land.

### D5 — structural sanity (STOP only)

No hourly footprint price outside `[−$100, $3,000]/MWh` (a bilateral trade beyond that is a units or
parse defect, not a price); annual volume-weighted mean in `(0, 250]`; the on-peak mean
(hour-beginning 06:00–21:59 Central prevailing, the WSPP 6×16 block) **exceeds** the off-peak mean in
every year (a clock or allocation error flattens or inverts the diurnal shape). Any breach is a build
defect and stops the lane; none of these is a fit.

### Verdict rule

`SERIES LANDED` ⇔ D1.1 ∧ D1.2 ∧ D2.1 ∧ D2.2 ∧ D3.1 ∧ D3.2 ∧ D3.3 ∧ D4.1 ∧ D4.2 ∧ D5, every year.
Otherwise `NO`, with the failing cell named.

---

## 6. (e) What happens on NO

- **Nothing** is written to `data/raw/_validation-source/`.
- The raw store `data/raw/ferc-eqr/` and the builder still land: the footprint's EQR extract is
  measured market data worth having whatever the verdict, and the FINDING must be reproducible
  without a 43 GB re-fetch.
- The FINDING's first line is `NO — <failing cell, measured value vs. bar>`, card S2 limb (b) applies
  to any SOCO run (a determination naming its own basis, never `CALIBRATED`, the price gap at full
  magnitude), and gate G6's `TAIL_THRESHOLD["SOCO"]` edits are skipped with the skip documented.
  A NO is a successful lane.
- **No proxy.** Gate G17 survives the ruling: if this index fails, the answer is the documented NO,
  never MISO-South, never PJM AD, never an "adjusted" series, never the SEEM average written as
  SOCO's hourly price.

---

## 7. What is landed on SERIES LANDED, and its shape

`data/raw/_validation-source/actual_lmp_hourly_SOCO.parquet` — `year` int16 · `hour` int16
(0–8759, fixed-CST non-leap clock) · `rt` float32 (the footprint volume-weighted EQR hourly price;
NaN where §4's rules say so) · `da` float32 (all NaN — no day-ahead market exists). 8,760 rows per
year, 2023–2025. Exactly the SPP / CAISO / NWPP system-file schema.

**Not landed by this lane** (outside FILES YOU OWN — routed to SOCO-DESK in the FINDING): the
`actual_lmp.json` SOCO block (SOCO-31), `TAIL_THRESHOLD["SOCO"]` (gate G6, and card S9's threshold
is to be set from the measured distribution, never to make C3c pass), `_STD_TZ["SOCO"]` (SOCO-20),
the `_validation-source/README.md` row.

---

## 8. The fetch plan

- **Source.** The EQR Report Viewer's *Downloads → Quarterly Filings → All Companies* bulk files,
  `https://eqrreportviewer.ferc.gov/DownloadRepositoryProd/<repository token>/BulkNew/CSV/CSV_<year>_Q<q>.zip`,
  one per quarter, 2023 Q1 → 2025 Q4 (12 files, 3.3–3.9 GB each, `Accept-Ranges: bytes`). The
  token is read from the viewer page at fetch time (it is not assumed stable). Measured 2026-09-13:
  HTTP 200 anonymous, ~10 MB/s through this egress; `www.ferc.gov` 403, `eqrds.ferc.gov` CONNECT 502
  (the legacy download host is not reachable from here), `data.ferc.gov` reachable but its catalogue
  carries no EQR dataset and its API is key-gated. Each bulk file is a zip of per-filing zips, each
  holding `*_ident.CSV`, `*_contracts.CSV`, `*_transactions.CSV`, `*_indexPub.CSV`.
- **Streaming, not storing.** Disk allows one quarter at a time: download → read every filing's
  `transactions` CSV → keep the rows whose POD BA is `SOCO` (all products, all 26 fields) → delete
  the zip. An inner zip that does not open is logged with its name and size and skipped (one such
  member exists in 2024 Q3, found in the catalogue pass). Whole-quarter row counts are logged.
- **Committed store** `data/raw/ferc-eqr/` (README + SOURCES + SHA256SUMS in the `spp-planning`
  template; `_pulls/` gitignored): `eqr_soco_pod_transactions.parquet` (every SOCO-POD row,
  2023–2025, all fields — the footprint's raw extract, so the FINDING regenerates without a
  re-fetch), `soco_eqr_hourly_utc.parquet` (`hour_utc · price · mwh · n_rows · n_sellers` — the
  per-hour product), `seem_auditor_monthly_prices.csv`, `fuel_cost_anchor_monthly.csv`,
  `gate.json` (every measured cell of §5). If the raw extract exceeds 100 MB the product-filtered
  subset is committed instead and the README says so.
- **Rule 13's forward test** is met by construction: a forward year regenerates from the same
  bulk files with no change to any rule above.

---

## 9. Rules this lane is bound by, restated in one line each

1 `[R-STRUCT]` no residual is read and the gate cannot promote; 13 `[R-MEASURED]` every input is a
market quantity that regenerates for a forward year; 14 `[R-ACCURATE]` if the real series makes a
later backcast look worse that is a bug elsewhere, never a reason to touch the index; 23
`[R-FROZEN-DERIVE]` the builder re-runs only when its sources change; 25 `[R-ISO-SCOPE]` / G17
nothing priced in a neighbouring market enters; 27 `[R-PUSH]` fetch-back verify every pushed file
≥ 300 lines; §8.0 no shared record is edited — the FINDING carries a `## Log entry` for the desk.
