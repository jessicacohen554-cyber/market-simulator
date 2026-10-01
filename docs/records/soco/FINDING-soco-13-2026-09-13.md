# FINDING — SOCO-13: the FERC-EQR price index — **NO**. The index builds cleanly and covers 99 % of hours, but the short-term bilateral slice is 2.6–3.7 % of the footprint's energy against a pre-registered 5 % bar, and its level sits 12 / 54 / 72 % above the SEEM auditor's annual clearing price against a 15 % bar. Nothing landed to `_validation-source`.

**Lane** SOCO-13 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/soco-13-eqr-price-84k5yi` · **Base** `33a7c961` at launch, rebased onto `28e7a6a3` ·
**Data profile** `shared` · **PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-13-2026-09-13.md` (pushed at
`ee32cf75` before any value was read; addendum A at `535d87c5` before any index value existed; both
carried unchanged through the rebase as `81faf6a4` / `7757ef9d`) · **Ruling** card S2, both limbs ·
**Raw store** `data/raw/ferc-eqr/` (README, SOURCES, SHA256SUMS, `gate.json`, `filter_ledger.json`) ·
**Builder** `scripts/data/build_soco_eqr_price_index.py`.

## 0. Verdict first

**VERDICT: NO** — three of the five pre-registered gates fail, in every year or in two of three:

| gate | bar | 2023 | 2024 | 2025 | |
|---|---|---:|---:|---:|:--:|
| **D2.2** volume share of SOCO demand | ≥ 5.0 % | **3.66 %** | **2.69 %** | **2.64 %** | ✗ every year |
| **D3.1** level vs the SEEM auditor's annual weighted-average price | ±15 % | +11.7 % | **+54.2 %** | **+72.1 %** | ✗ 2024, 2025 |
| **D4.2** index ÷ F-class CC fuel cost | 0.8–2.0 | 1.68 | 1.95 | **2.008** | ✗ 2025 |

D1 (coverage), D2.1 (thinness), D3.2 (shape, 0.86–0.88), D3.3 (support), D4.1 (gas tracking, 0.78)
and D5 (structure) all pass. No bar was moved after the series was seen; the one post-PRECOMMIT
change is addendum A, which corrected the D3 anchor's **source** before `build` was first run and
moved no number (§2.3 reports D3 on the original letter too, and it fails there as well).

The gate is a STOP gate. It refused the series; it promoted nothing; it read no model residual (none
exists). A NO is a successful outcome of this lane. Card S2 limb (b) is the ruled fallback and is
already implemented: rubric **v3.8** (lane SOCO-22, merged at `28e7a6a3` while this lane ran) gives a
SOCO run the determination `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`, never `CALIBRATED`, with the
price gap on the determination basis. **Gate G17 survives:** no neighbouring hub, no adjusted series,
no SEEM average is proposed in its place.

**What the NO says and does not say (§3):** the EQR index is a real, reproducible, hourly, measured
price of the energy that changed hands inside the SOCO balancing authority — and it is the price of a
thin, scarcity-exposed bilateral slice, not of the footprint's marginal energy. It is kept, in the raw
store, as what it is.

## 1. What was built (all committed under `data/raw/ferc-eqr/`)

| artifact | rows | what |
|---|---:|---|
| `eqr_soco_pod_transactions.parquet` | 981,070 | every EQR transaction row with `point_of_delivery_balancing_authority == SOCO`, 2023 Q1 → 2025 Q4, all 26 fields as text (+ filing member, quarter, salvage flag) — extracted from **1,830,599,267** transaction rows across 12 bulk quarterly files (41.0 GB, streamed one quarter at a time, hashed, deleted) |
| `soco_eqr_hourly_utc.parquet` | 26,286 | the per-UTC-hour product after the PRECOMMIT §2–§4 filters: `mwh · n_rows · n_sellers · mwh_15min · price · thin` |
| `seem_auditor_monthly_prices.csv` | 100 | gate D3's anchor: 14 text-borne 2025 values (as printed) + 86 digitised Peak / Off-Peak monthly bars from the three annual-report figures, with source, page, resolution and basis |
| `fuel_cost_anchor_monthly.csv` | 96 | gate D4's anchor: EIA delivered gas AL / GA / MS → $/MMBtu → F-class CC fuel cost |
| `filter_ledger.json`, `gate.json` | — | every rule's exclusion and every gate cell |

**The fetch.** The EQR Report Viewer's *Downloads → Quarterly Filings → All Companies* panel serves the
bulk files at `…/DownloadRepositoryProd/<token>/BulkNew/CSV/CSV_<year>_Q<q>.zip` (HTTP 200 anonymous,
`Accept-Ranges`, ~10 MB/s here); the panel renders only after an ASP.NET postback, which
`build_soco_eqr_price_index.py links` replays. `www.ferc.gov` is 403 from this egress (SOCO-11's
finding re-confirmed), `eqrds.ferc.gov` is a CONNECT 502, and `data.ferc.gov` carries no EQR dataset —
so the viewer's bulk route is the only one that worked, and it worked completely. Each quarter is a zip
of 3,191–3,914 per-filing zips; five of them across the span are truncated by the filer (no central
directory) and were salvaged by walking their local headers — none held a SOCO row. Whole-quarter row
counts, byte lengths, `sha256` and defective members are in `_pulls/manifest_<quarter>.json` and
`SHA256SUMS.txt`. FERC republishes a quarter's file when a filer refiles (`Last-Modified` 2026-08-24 →
2026-09-13 across the twelve), so the committed extract is the durable record of what was read.

**The filters, as measured** (`filter_ledger.json`; 488.8 TWh of standardised MWh in the raw extract):

| PRECOMMIT rule | rows excluded | TWh excluded | note |
|---|---:|---:|---|
| standardised quantity / price numeric, quantity > 0 | 152,416 | 0.18 | capacity-, transmission- and flat-rated rows carry no standardised MWh |
| `product_name == ENERGY` | 48,360 | 124.27 | `REQUIREMENTS SERVICE` (cost-based full requirements) is the bulk of it |
| `class_name ∈ {F, NF}` | 60,863 | 56.20 | unit power (`UP`) |
| `term_name == ST` | 113,797 | 207.18 | long-term contract deliveries — 42 % of all SOCO-POD MWh |
| pricing increment ∈ {5, 15, H, D} | 357,740 | 76.39 | monthly- and yearly-priced products itemised per hour |
| not `Electric Index`, not `RTO/ISO` | 36 | 0.01 | gate G17 |
| energy-denominated units · intra-Southern · known time zone · datetimes parse | 0 | 0 | — |
| span ≤ 25 h | 3,385 | 3.43 | weekly and monthly aggregates filed as one row |
| **index** | **244,473** | **21.15** | 2023: 8.40 · 2024: 6.43 · 2025: 6.32 TWh |

Exact duplicates across a quarter's filings: 0. Salvaged rows in the index: 0.

## 2. The gate table — PRECOMMIT §5, filled in

### 2.1 D1 — coverage: PASS

| leg | bar | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|
| D1.1 priced hours (fixed-CST year) | ≥ 8,322 | **8,741** (99.8 %) | **8,748** (99.9 %) | **8,677** (99.1 %) |
| D1.2 lowest monthly coverage | ≥ 0.90 (`PRICE_MONTH_COVERAGE_MIN`) | 0.997 | 0.997 | **0.954** (Feb 2025) |

All 36 months clear the scorer's own month bar. NaN hours are not diurnally concentrated (share by
standard hour 0.1–1.0 %, highest at HE01). The thin-hour rule fired on 0.9–2.5 % of hours (D2.1).

### 2.2 D2 — depth and thinness: **FAIL on depth, every year**

| leg | bar | 2023 | 2024 | 2025 |
|---|---|---:|---:|---:|
| D2.1 share of priced hours with < 5 source rows | ≤ 25 % | 1.03 % | 0.90 % | 2.54 % |
| median source rows per priced hour (5th–95th pct 7–51) | — | 23 | 23 | 21 |
| median distinct sellers per hour | — | 8 | 7 | 7 |
| indexed MWh | — | 8,401,556 | 6,430,151 | 6,316,985 |
| SOCO demand MWh (EIA-930 `Demand`) | — | 229,463,088 | 239,329,600 | 239,379,904 |
| **D2.2 volume share** | **≥ 5.0 %** | **3.66 %** | **2.69 %** | **2.64 %** |

The hours are not thin — twenty-odd transactions from seven or eight sellers is a working market hour.
The *slice* is thin: short-term energy delivered inside SOCO under FERC-jurisdictional contracts is one
thirty-seventh of the footprint's load, falling through the window. That is the structural fact the
charter suspected in plan §2.6 ("thin hours may not clear at all" turned out to be the wrong worry; the
right one is that the whole traded layer is small next to a vertically-integrated system's self-supply).
The 5 % bar was set before the fetch on the sister lane's RT-market analogy and is not re-argued here.

### 2.3 D3 — reconciliation against the SEEM auditor: **FAIL on level (2024, 2025); shape PASSES**

**The anchor, as built (addendum A).** 36 months × Peak / Off-Peak digitised from the annual reports'
*Monthly Clearing Prices* figures (2023: Figure 4, Jan 2023 → Apr 2024, full raster, $0–$70 axis
labelled in the image's alpha mask; 2024: Figure 9, Avg. + Jan → Dec, vector axis; 2025: Figure 5,
Avg. + Dec 2024 → Dec 2025, vector axis), at $0.09–0.14/MWh per pixel. Three digitisation checks, all
in `gate.json`: (i) the five months two figures both carry agree within $0.03–0.27, except Jan 2024
Off-Peak where the auditor's own two figures differ ($34.86 in the 2023 report vs $32.85 in the 2024
report); (ii) the 2025 text-borne all-hours values sit between the digitised Peak and Off-Peak bars in
every month from April on — as an all-hours average must — while the three flagged months do not
(Jan text $40 vs bars $45.5; Feb text $11.5 and Mar text $10 are the same reports' bid-offer
*spreads*, printed with a `/kWh` unit); (iii) the 2024 Avg. bars ($25.2 Peak / $20.0 Off-Peak)
bracket the annual text's $23. The 2025 Avg. Off-Peak bar reads $39.2 against a monthly Off-Peak mean
of $30.2 and is recorded as an unexplained figure feature; the Avg. bars are not used.

| leg | bar | 2023 | 2024 | 2025 | |
|---|---|---:|---:|---:|:--:|
| index annual MWh-weighted mean `I_year` | — | $33.51 | $35.48 | $55.08 | |
| SEEM annual weighted-average price `S_year` (annual report text) | — | $30 | $23 | $32 | |
| **D3.1 level gap** | **±15 %** | **+11.7 %** ✓ | **+54.2 %** ✗ | **+72.1 %** ✗ | ✗ |
| D3.2 shape, Peak-vs-Peak `r` (36 months) | ≥ 0.80 | 0.856 | | | ✓ |
| D3.2 shape, Off-Peak-vs-Off-Peak `r` (36 months) | ≥ 0.80 | 0.878 | | | ✓ |
| D3.2 shape, pooled (72 points) | ≥ 0.80 | 0.855 | | | ✓ |
| D3.3 support | ≥ 30 months | 36 (digitised) | | | ✓ |

**On the letter of the original definition** (text-borne monthly values only, before addendum A):
support 12 months (✗ < 30), `r` = 0.36 (✗) — the 2025 months, three of which are the flagged
misprints. D3 fails either way, and on different legs.

The monthly picture (`I` = index MWh-weighted mean; `S` = SEEM digitised; $/MWh):

| month | I all | I peak | I off | S peak | S off | month | I all | I peak | I off | S peak | S off | month | I all | I peak | I off | S peak | S off |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 2023-01 | 40.3 | 40.6 | 39.7 | 32.2 | 31.1 | 2024-01 | 55.1 | 55.0 | 55.2 | 35.3 | 32.9 | 2025-01 | **111.6** | 108.9 | 117.2 | 45.5 | 45.5 |
| 2023-02 | 32.0 | 32.4 | 31.1 | 27.3 | 24.7 | 2024-02 | 22.1 | 22.2 | 22.0 | 17.2 | 17.3 | 2025-02 | 70.3 | 73.3 | 64.1 | 35.8 | 32.1 |
| 2023-03 | 33.2 | 33.9 | 31.2 | 24.9 | 22.8 | 2024-03 | 21.3 | 21.1 | 21.7 | 14.7 | 13.2 | 2025-03 | 42.8 | 42.4 | 43.7 | 30.0 | 30.9 |
| 2023-04 | 28.2 | 29.6 | 24.7 | 22.6 | 18.8 | 2024-04 | 28.4 | 28.8 | 27.1 | 17.3 | 14.8 | 2025-04 | 42.2 | 43.2 | 38.7 | 29.8 | 28.2 |
| 2023-05 | 26.6 | 27.6 | 23.7 | 22.7 | 17.6 | 2024-05 | 37.8 | 39.0 | 32.7 | 25.8 | 18.5 | 2025-05 | 37.1 | 38.2 | 32.6 | 28.9 | 23.6 |
| 2023-06 | 29.0 | 30.5 | 23.7 | 24.2 | 17.3 | 2024-06 | 40.3 | 41.5 | 36.7 | 32.0 | 23.3 | 2025-06 | 59.9 | 64.1 | 44.6 | 32.5 | 26.3 |
| 2023-07 | 40.1 | 42.5 | 33.3 | 32.8 | 22.8 | 2024-07 | 42.3 | 44.1 | 35.3 | 29.9 | 20.0 | 2025-07 | 67.5 | 71.1 | 52.0 | 40.4 | 29.9 |
| 2023-08 | 39.3 | 41.0 | 34.3 | 34.1 | 23.7 | 2024-08 | 36.9 | 38.8 | 30.3 | 27.7 | 18.7 | 2025-08 | 43.2 | 45.6 | 34.7 | 34.0 | 25.5 |
| 2023-09 | 34.3 | 36.2 | 28.9 | 29.5 | 20.3 | 2024-09 | 34.9 | 36.2 | 30.5 | 27.3 | 20.5 | 2025-09 | 41.1 | 43.7 | 31.4 | 32.7 | 24.5 |
| 2023-10 | 32.0 | 33.0 | 27.9 | 28.4 | 22.2 | 2024-10 | 34.8 | 36.0 | 31.7 | 25.4 | 20.3 | 2025-10 | 39.6 | 41.4 | 36.1 | 30.9 | 27.7 |
| 2023-11 | 35.9 | 36.0 | 35.6 | 26.9 | 23.0 | 2024-11 | 30.3 | 31.1 | 28.4 | 21.6 | 18.0 | 2025-11 | 42.9 | 43.2 | 42.3 | 30.2 | 30.6 |
| 2023-12 | 31.8 | 32.0 | 31.3 | 23.9 | 22.4 | 2024-12 | 42.2 | 42.9 | 40.7 | 29.1 | 27.4 | 2025-12 | 57.9 | 57.8 | 58.0 | 40.7 | 37.6 |

The two series move together (the shape legs) and the EQR index sits above SEEM in **every one of the
36 months**, by a margin that widens with scarcity: the median monthly ratio is 1.35, and January 2025
is 2.5×.

### 2.4 D4 — boundedness against the fuel-cost stack: **FAIL, 2025 (by 0.4 % of the band's edge)**

| leg | bar | measured | |
|---|---|---:|:--:|
| D4.1 monthly `r(I, FC_AL)`, 36 months | ≥ 0.70 | **0.783** | ✓ |
| D4.2 `I_year / FC_year` 2023 (FC $19.94) | 0.8–2.0 | 1.681 | ✓ |
| D4.2 2024 (FC $18.22) | 0.8–2.0 | 1.947 | ✓ |
| D4.2 2025 (FC $27.43) | 0.8–2.0 | **2.008** | ✗ |

The index tracks gas (D4.1), and its ratio to the marginal gas unit's fuel cost has risen every year:
1.68 → 1.95 → 2.01. The 2025 breach is by 0.4 % of the bar and is reported as measured; the ratio's
climb is the finding, not the decimal.

### 2.5 D5 — structural sanity: PASS

Annual MWh-weighted means $33.51 / $35.48 / $55.08 (all in (0, 250]); hourly range $7.94 … $512.38
(2025-01-22; all inside [−100, 3000]); on-peak above off-peak in every year (34.6 vs 30.5; 36.4 vs
32.7; 56.2 vs 51.9); the prevailing-hour diurnal profile is physical (trough $33.1 at 02:00, peak
$41.9 at 17:00, morning shoulder $38.4 at 06:00). The clock and the allocation are right.

## 3. What the index is made of, and why it lands where it does

**Composition** (share of indexed MWh; MWh-weighted price):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| hourly-priced `H` | 65 % @ $32.8 | 50 % @ $33.7 | 46 % @ $54.8 |
| daily block `D` | 33 % @ $32.4 | 45 % @ $32.7 | 49 % @ $55.1 |
| 15-minute `15` (SEEM matches delivered into SOCO) | 2.5 % @ **$66.4** | 5.0 % @ **$77.4** | 5.2 % @ $57.1 |
| rate type `Fixed` / `Formula` | 88 % / 12 % | 95 % / 5 % | 95 % / 5 % |
| top-5 sellers' share (HHI over the span: 926) | 62 % | 59 % | 64 % |
| leading sellers | Constellation 16 %, Mercuria 16 %, Southern Co. Services 13 %, TEA 9 %, Morgan Stanley 8 % | Constellation 21 %, Morgan Stanley 11 %, SCS 11 %, EDF 10 % | SCS 22 %, Oglethorpe 14 %, Constellation 12 %, EDF 9 % |
| hourly price p50 / p95 / p99 | $30.0 / $46.9 / $61.7 | $30.3 / $60.0 / $101.5 | $39.0 / $80.9 / $200.4 |
| hours above $100 | 7 | 95 | 345 |
| MWh-weighted mean ÷ median | 1.12 | 1.17 | 1.41 |

**Three things this establishes.**

1. **The level failure is scarcity, not a construction error.** The 2025 median hour ($39.0) rose 29 %
   on 2024's while the CC fuel cost rose 51 %; the *mean* rose 55 % because the tail did. January 2025
   alone averages $111.6: the daily MWh-weighted index reads $36–84 through 19 January, then
   **$221 / $240 / $378 / $259 / $190 / $153 on 20–25 January** (Winter Storm Enzo), then $32–50.
   June–July 2025 average $60–68 with Peak $64–71. These are the prices at which energy was bought into
   the Southern footprint when it was scarce; every seller class carries them (2025: SCS $54,
   Oglethorpe $50, Constellation $71, EDF $53, FPL $58, Mercuria $60), every pricing increment carries
   them (`H` $54.8, `D` $55.1, `15` $57.1), and fixed-rate rows carry them (95 % of MWh at $54.7).
   A split-the-savings 15-minute exchange average — SEEM's statistic — does not carry them, by
   construction: it prices the midpoint of two utilities' marginal costs on the residual they choose to
   exchange, and in a scarcity hour the exchange thins while bilateral firm energy clears at the buyer's
   outage cost. The two objects agree in shape (`r` 0.86–0.88) and disagree in level exactly where the
   PRECOMMIT said a level disagreement would be diagnostic.

2. **The SEEM anchor is SEEM-wide, and the SOCO-delivered SEEM matches confirm it.** The 15-minute
   rows — SEEM matches whose sink is inside SOCO — price at $66 / $77 / $57 across the three years,
   two to three times the SEEM-wide averages the auditor reports ($30 / $23 / $32), and correlate with
   them only at 0.32 monthly. SOCO is the *expensive* segment of a platform whose auditor reports
   segment averages from $9 to $91. That is the first of SOCO-12 §0.2's four reasons the anchor could
   only ever be a boundedness check, measured.

3. **The slice is thin, and it is getting thinner.** 8.4 → 6.4 → 6.3 TWh of short-term energy against
   229–239 TWh of load, with the `H` share falling and the daily-block share rising. Vertically
   integrated dispatch does not transact; what reaches EQR at a SOCO delivery point is the marginal
   top-up and the off-system sale, and that layer is one-third of the size the 5 % bar demanded.

**Rule 14 `[R-ACCURATE]` read correctly here.** The EQR data is accurate — for the quantity it prices.
Rule 14's own misalignment exception ("a different boundary … a different aggregation") is what
applies: the object is real and the object is not the model's object (the marginal cost of serving
*all* load, which is what an LP dual is). Scoring an LP dual against a 2.6 % bilateral slice whose 2025
mean is 41 % above its own median would hold the model to a number that is, by measurement, not the
price of that quantity. The series is kept, in the raw store, as what it is; it is not promoted to the
benchmark of a different quantity.

## 4. What is landed, what is not, and what is routed to SOCO-DESK

- **Landed:** the raw store (§1), the builder, the PRECOMMIT with addendum A, this FINDING.
  **Not landed:** `data/raw/_validation-source/actual_lmp_hourly_SOCO.parquet` (`gate --land` refuses on
  NO; not run).
- **Card S2 limb (b) applies** to every SOCO run, and rubric v3.8 already expresses it
  (`PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; `scripts/calibration_verdict.py`, lane SOCO-22). The price
  gap on the determination basis is the one this lane measured: *no public price of the footprint's
  marginal energy exists; the one measured price is a 2.6–3.7 % bilateral slice whose level runs
  12–72 % above the SEEM auditor's average and 1.7–2.0× the marginal gas unit's fuel cost.*
- **Routed, for the desk to rule — not decided here.** As the sister lane found for WEIM, two honest
  options exist. **(i)** Score no price criterion (the ruled fallback; this lane's recommendation for
  the first keeper). **(ii)** Use the EQR index as an explicitly-labelled *bilateral short-term energy*
  benchmark — buildable at zero cost from the committed store, 99 % hourly coverage, a real diurnal
  and seasonal shape, and the only hourly price object this footprint will ever have — with the
  measured level relationship named on every determination basis. Option (ii) is **a new owner
  ruling (an S2 amendment), never a re-run of this gate**: the gate was pre-registered, it read NO,
  and re-cutting it to admit the series is the fitted benchmark the PRECOMMIT refused in writing. A
  third option — scaling the index toward SEEM, gas cost or any model number — is refused by this lane
  as the tuned adjustment rule 13 forbids.
- **Gate G6** (`TAIL_THRESHOLD["SOCO"]`, `actual_tail.json`) and **card S9**: the three edits are
  **deliberately skipped** — S2 yielded no series — and the skip is documented here as the plan requires.
- **SOCO-31 / `actual_lmp.json`:** no SOCO block is needed; the v3.8 branch keys on its absence.
- **`_STD_TZ["SOCO"] = "Etc/GMT+6"`** (`derive_actual_lmp.py`): not needed now; if option (ii) is ever
  ruled, SOCO-20 registers it and the committed UTC-hourly product is a re-index, never a re-fetch.
- **`_validation-source/README.md`:** no row needed (nothing landed).
- **Matrix shard `mechanism-matrix/SOCO.js`** (landed by SOCO-21 while this lane ran): no mechanism was
  tested and no `ScenarioConfig` field added, so the rule-28(b) cell duty is vacuous for this lane.
- **Shards:** none launched — this lane ran no LP (rules 32–34 not engaged; nothing to archive).
- **Disk / retention (rule 31):** every solved artifact is committed; the 41 GB of bulk zips were
  hashed and deleted as the PRECOMMIT §8 declared (they are FERC's, re-fetchable, and not results).

## 5. Reproducibility, rule 13's forward test, and identity

`links → (download) → extract → fetch-seem → build → gate` regenerates every committed artifact from
the sources in `SOURCES.md`; every number above is in `gate.json` / `filter_ledger.json`. A forward
year regenerates from the same bulk files with no change to any rule (rule 13's test is met by
construction). `SHA256SUMS.txt` carries the hash of every tracked artifact, of every untracked pull,
and of each deleted bulk zip. Three facts worth knowing before anyone reuses the store: (a) the
`increment_name` field is a **pricing** increment, not a reporting grain — 24,762 monthly-priced
ENERGY rows in 2024 Q3 alone are filed one row per hour; (b) `RTO/ISO`-priced rows exist at SOCO
delivery points (sales into MISO settled at MISO's price) and are gate G17's back door — the filter
closes it; (c) the three defective inner zips per year are truncated uploads whose local headers still
walk, and none carried a SOCO row.

## 6. Rules, files, verification

Rules 1 / 13 / 14 / 23 / 25 / 27 / §8.0 as the PRECOMMIT §9 states them, each honoured: no residual
read; every input a regenerable market quantity; the accurate series kept as what it is; the builder
re-runs only on source change; nothing priced in a neighbouring market entered (index- and
RTO-priced rows excluded); every pushed file ≥ 300 lines fetch-back verified by blob hash; no shared
record edited. **Files touched:** `docs/handoffs/PRECOMMIT-soco-13-2026-09-13.md`, this FINDING,
`scripts/data/build_soco_eqr_price_index.py`, `data/raw/ferc-eqr/**` (with its own `.gitignore` for
`_pulls/`). Nothing under `src/`, `tests/`, any `_validation-source` file, `actual_lmp.json`, the
plan, the ledger, `soco.md`, or any other lane's files.

## Log entry

## soco-13 — 2026-09-13

**FERC-EQR price index (card S2 option a): NO.** PRECOMMIT pushed before any value was read; STOP
gate D1 / D5 pass, **D2.2 fails every year** (indexed short-term energy 3.66 / 2.69 / 2.64 % of SOCO
demand vs ≥ 5 %), **D3.1 fails 2024 / 2025** (index $33.5 / $35.5 / $55.1 vs the SEEM auditor's
$30 / $23 / $32, +11.7 / +54.2 / +72.1 % vs ±15 %; shape passes, `r` 0.86–0.88 Peak / Off-Peak
against the digitised annual-report figures), **D4.2 fails 2025** (2.008× the F-class CC fuel cost vs
a 2.0 ceiling; gas tracking `r` 0.78 passes). The level gap is scarcity in the bilateral slice
(Jan 20–25 2025 daily $153–378; 2025 mean/median 1.41), present in every seller and increment; the
SOCO-delivered SEEM matches price at 2–3× the SEEM-wide average, so the anchor is confirmed
SEEM-wide, not SOCO. Raw store `data/raw/ferc-eqr/` committed (981,070 SOCO-POD rows from 1.83 bn
EQR rows / 41 GB streamed; 26,286-hour UTC index, 99 % priced; digitised SEEM anchor; fuel-cost
anchor; ledger; gate). **Nothing landed to `_validation-source`**; S2 limb (b) / rubric v3.8 applies;
G6 and S9 skipped by design. Routed: (i) price unscored vs (ii) a labelled bilateral benchmark = a new
owner ruling, never a re-cut gate. `FINDING-soco-13-2026-09-13.md`.
