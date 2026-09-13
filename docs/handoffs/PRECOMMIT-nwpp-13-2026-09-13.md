# PRECOMMIT — NWPP-13: the WEIM-derived footprint hourly price index, STOP-gated (card N2 option a)

**Lane** NWPP-13 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-13 ·
**Branch** `claude/nwpp-13-weim-price-index-3pp1a8` · **Base** `4d9c3251` (`origin/main` at launch;
the charter's pin was `c93b0d27`, desk refresh `5341b234`) · **Data profile** `shared` ·
**Charter** `docs/multi-iso/nwpp-addition-plan-2026-09.md` §8 W1 NWPP-13 · **Ruling** card N2,
sitting #1 (both limbs) — the charter's "only start after N2" condition is satisfied.

**This document is pushed BEFORE any price, transfer or Mid-C value is read.** Every rule and every
number below is declared here and is not re-cut after the series is seen. A gate written or loosened
after seeing the series would make this a fitted benchmark — the object rules 1 `[R-STRUCT]` and 13
`[R-MEASURED]` exist to refuse — and every later NWPP price criterion would then be scored against a
number chosen to look right rather than a number that is right. I know that; the record should show
I knew it before the fetch, which is why this file exists.

---

## 0. What was read before this document, and what was not

The charter asks that the PRECOMMIT precede the data. It cannot precede *metadata*: a node-set rule
has to be written against the catalogue that exists, and a coverage gate against the retention that
exists. So the line drawn is **values vs. structure**, and it is stated here so the desk can check it:

| read before this document | what of it | values seen? |
|---|---|---|
| CAISO OASIS `ATL_APNODE` catalogue (2,525 rows, pulled 2026-09-13) | node ids, types, effective dates | no prices |
| OASIS availability probes, `PRC_RTPD_LMP` and `ENE_EIM_TRANSFER` | HTTP code, `ERR_CODE` (1000 = no data) vs. row count and column header; the retention edge | **no** — row counts and headers only |
| EIA ICE workbooks `ice_electric-{2023,2024,2025}final.xlsx` | column headers, hub names, Mid-C row counts, count of multi-day delivery rows | no prices, no volumes |
| WEIM quarterly benefits PDFs Q1-2023 … Q4-2025 | downloaded (12 × HTTP 200); **not opened** | no |
| EIA-930 `EIA930_BALANCE_*.parquet` | column names only | no |
| `scripts/calibration_verdict.py` | `PRICE_MEAN_TOL = 0.10`; the partial-year masking path (`_covered_months` / `rt_cov.mon`) | — |
| `scripts/data/derive_actual_lmp.py` | `_STD_TZ`, `_std_hour_index`, `_densify_std`, the 8760 non-leap calendar | — |

The one price value in my possession is the charter's own: `$63.9213/MWh`, the first interval of
`PACW_BPAT.PSEI-APND` on 2023-07-15, quoted in plan §2.6. No NWPP model run exists and none is used.

---

## 1. The object being built — and what it is not

A **WEIM 15-minute imbalance-market LMP**, at each participating BAA's **default load aggregation
point**, aggregated to the hour and demand-weighted to the footprint. It is the price at which a
BAA's real-time load imbalance settles in the only market that clears any of this footprint's energy
in 2023–2025. It is **not** a day-ahead price (there was none; EDAM post-dates the window — the
sidecar's `da` column will be NaN for every hour, and the rubric's DA diagnostic will read SKIPPED),
and it is **not** the price of all the footprint's energy: base schedules are bilateral and settle
outside it. Whether that gap is a misalignment or a reconcilable one is exactly what gate D2 and gate
D3 below decide, with numbers fixed here.

---

## 2. (a) The NODE SET — the rule, then the nodes it picks

**Rule.** For every balancing authority in the ruled N1 footprint (17 BAs), take the OASIS apnode of
type **`DEPZ`** (the "default EIM load aggregation point", id form `ELAP_<BAA>-APND`) if the
catalogue carries one for that BA. Nothing else.

Why that type and not the two the charter named:

- **`EIMT` nodes** (`PACW_BPAT.PSEI-APND` and 166 others in the footprint) are **EIM transfer**
  scheduling points — each prices a *transfer between two BAAs*. Plan §2.6 already says that is not
  the object a BAA-internal load price is. They are not used.
- **`CASP` nodes** (`CGAP_{DOPD,CHPD,GCPD}_MIDC-APND`) are **CAISO scheduling points** at the Mid-C
  interchange: the price CAISO pays for an import there is CAISO's price, one step from the SP15/NP15
  substitution gate G17 refuses. They are not used.
- **`EPZ`-type `ELAP_*`** nodes exist for `CHPD`, `DOPD`, `GCPD`, `WAUW` — BAs that are **not** WEIM
  participants. A `PRC_RTPD_LMP` probe on `ELAP_GCPD-APND` (2024-07-10) returned `ERR_CODE 1000`, no
  data: no market clears there and no price is published. They are not used, and their load is
  reported as **unpriced** (§3).

**The nodes the rule picks — 12, all effective before the window opens, so the set is constant over
2023-06 → 2025-12:**

| BA | node | effective (catalogue) | 2024 load share (plan §2.5) | N5-recommended zone (unruled) |
|---|---|---|---:|---|
| BPAT | `ELAP_BPAT-APND` | 2022-05-03 | 20.26 % | NWPP-NW |
| PSEI | `ELAP_PSEI-APND` | 2016-10-01 | 8.53 % | NWPP-NW |
| SCL | `ELAP_SCL-APND` | 2020-04-01 | 3.23 % | NWPP-NW |
| TPWR | `ELAP_TPWR-APND` | 2022-03-02 | 1.56 % | NWPP-NW |
| PGE | `ELAP_PGE-APND` | 2017-10-01 | 7.79 % | NWPP-OR |
| PACW | `ELAP_PACW-APND` | 2014-10-15 | 7.30 % | NWPP-OR |
| IPCO | `ELAP_IPCO-APND` | 2018-04-04 | 6.43 % | NWPP-INLAND |
| AVA | `ELAP_AVA-APND` | 2022-03-02 | 4.44 % | NWPP-INLAND |
| NWMT | `ELAP_NWMT-APND` | 2021-06-16 | 4.18 % | NWPP-INLAND |
| PACE | `ELAP_PACE-APND` | 2014-10-15 | 18.10 % | NWPP-EAST |
| NEVP | `ELAP_NEVP-APND` | 2015-12-01 | 14.11 % | NWPP-SNV |
| AVRN | `ELAP_AVRN-APND` | 2023-04-05 | 0.00 % (generation-only) | NWPP-NW (supply side) |

Priced load = **95.93 %** of the 2024 footprint. **Unpriced: CHPD 0.68 + DOPD 0.82 + GCPD 2.29 +
WAUW 0.28 = 4.07 %**, stated at full magnitude; `AVRN` and `GRID` carry no load. `AVRN`'s price is
fetched and stored (it is a footprint BAA on the supply side) but carries zero weight everywhere.

**Card N5 is not pre-empted.** The committed raw store is **per BA**; the N5 zone column above is the
desk's recommendation and is used only for the Mid-C reconciliation group (§5 D3) and a FINDING table.
If N5 rules a different grouping, the zonal series is a re-group of committed bytes, no re-fetch.

---

## 3. (b) The WEIGHTING — demand-weighted on the measured EIA-930 series

BA hourly prices become a footprint hourly price as the **demand-weighted mean over the 11 load-carrying
priced BAs**, weights = that hour's `Demand (MW) (Adjusted)` from the committed
`data/raw/eia-930/EIA930_BALANCE_<yr>_<half>.parquet` (plan §2.5 / gate G20's convention, so the 30
defective hours never enter a weight).

Why this and not the alternatives:

- **Not WEIM transfer-volume-weighted.** Transfers are the market's *thin* slice (§5 D2 measures how
  thin); weighting a load price by transfer MW would weight by market depth, not by who consumes.
- **Not a simple mean.** BPAT is 20.26 % of load, TPWR 1.56 %; an equal-weight mean would price the
  footprint as if Tacoma were Bonneville.
- Demand-weighting is **the same construction the rubric scores** (`rt_lw` = the committed hourly
  actual weighted by the measured demand the model dispatches), so the benchmark and its scoring
  weight agree by construction.

**Missing members.** In an hour where some BAs are NaN, the weight renormalises over the priced BAs
**only if they carry ≥ 90 % of that hour's 11-BA demand**; otherwise the footprint hour is NaN.
Nothing is carried forward and nothing is interpolated.

---

## 4. (c) The AGGREGATION and the CLOCK

- **Source product:** `PRC_RTPD_LMP`, `market_run_id=RTPD`, `version=1` — the 15-minute market's
  LMP at the node. All four components are stored (`LMP_PRC`, `LMP_ENE_PRC`, `LMP_CONG_PRC`,
  `LMP_LOSS_PRC`); the index uses `LMP_PRC`.
- **15-min → hour:** the **simple mean of the four settlement intervals** whose `INTERVALSTARTTIME_GMT`
  falls in the UTC hour. Settlement intervals are equal-length, so the time-mean *is* the hour's
  average settlement price. An hour with **fewer than 3 of its 4 intervals** present is **NaN**.
  Missing intervals are **never carried, never interpolated** — not toward a neighbour, and never
  toward anything a model produces.
- **Clock:** each UTC instant is indexed onto the model's **fixed non-leap 8760-hour clock on Pacific
  STANDARD time (`Etc/GMT+8`)**, through `derive_actual_lmp._std_hour_index` imported unchanged —
  the CAISO sidecar's `_STD_TZ` convention, Feb 29 dropped. Reasons: (i) card N6's desk
  recommendation names `America/Los_Angeles` as the reporting zone (81.6 % of load; 14 of 17 BAs file
  Pacific in EIA-930); (ii) every committed `_validation-source` sidecar sits on its ISO's fixed
  standard clock — SPP-51c is the record of what a six-hour clock defect does to a load-bearing
  criterion; (iii) a fixed offset from UTC has no DST ambiguity.
  **Dependency, stated:** the charter says the convention must match NWPP-10's finding; no
  `claude/nwpp-10-*` branch exists on the remote at this base sha, so NWPP-10 has not landed. The
  raw store keeps the **UTC instant**, so whatever N6 / NWPP-10 fix, the sidecar is a re-index of
  committed bytes — no re-fetch. If NWPP-10 lands a different canonical hour before this lane's PR,
  the builder is re-run on that convention and the FINDING says so.

---

## 5. (d) THE STOP GATE — pass/fail numbers, fixed now

The gate is **STOP-only**: it can refuse the series; it can never promote a run, and it never reads
any model residual (none exists). All of D1–D4 must PASS for the verdict **SERIES LANDED**; any one
failing is **NO**.

### D1 — coverage (and the 2023 retention fact, declared before the fetch)

OASIS retention slides with the calendar. Measured 2026-09-13 by availability probe (ERR 1000 vs.
data, no values read): `PRC_RTPD_LMP` at `ELAP_PACW-APND` returns **no data for 2023-05-31 and
earlier, data from 2023-06-01**; `ENE_EIM_TRANSFER` has the same edge. **2023 can therefore be at
most Jun 1 – Dec 31 = 214 days = 5,136 hours = 58.6 % of the year**, and that ceiling falls by one
day per calendar day. The edge is re-measured at fetch time and the first served day is recorded.

| leg | PASS requires |
|---|---|
| D1.1 fetch completeness | for every node and every served day: 96 intervals × 4 components; per-node hourly coverage ≥ **95 %** of the hours inside the served window, each year |
| D1.2 footprint coverage, full years | **2024 ≥ 8,322** and **2025 ≥ 8,322** non-NaN footprint hours (95 % of 8,760) |
| D1.3 footprint coverage, 2023 | **≥ 4,380** non-NaN footprint hours (50 % of the year), which a complete fetch delivers (5,136) and a materially incomplete one does not |

**2023 is declared a PARTIAL-BY-RETENTION year now, whatever D1.3 reads.** It is scoreable only on
the scorer's masked path (`calibration_verdict._covered_months`, driven by `rt_cov.mon` in
`actual_lmp.json` — NWPP-31's file, **routed**, not mine), on which the model is masked to the same
months. The precedent is CAISO 2023 (`derive_actual_lmp.CAISO_MIN_HOURS`, the Mar–Dec year that the
masked path was built for). The determination basis for any 2023 NWPP number reads "price scored on
Jun–Dec only". The 50 % bar is a convention set with the edge already known; the honest number is the
coverage itself, and the FINDING reports it at full magnitude regardless of the bar.

### D2 — the WEIM volume share (the crux; threshold fixed before measurement)

**Quantity.** Gross WEIM transfer energy of the 11 footprint WEIM BAAs,
`Σ_BAA Σ_intervals |EIM_XFER_MW| × 0.25 h`, from OASIS `ENE_EIM_TRANSFER` (`version=2`,
`market_run_id=RTPD`, `baa_grp_id=ALL`, probed 2026-09-13: 23 BAAs, one row per BAA per 15-min
interval) — the market's own settled transfer quantity, per BAA, per interval. **Denominator:** the
17-BA footprint demand energy on the same hours (`Demand (MW) (Adjusted)`, plan §2.5). The 11-BA
denominator is reported beside it.

**Threshold: share ≥ 5.0 % in 2024, in 2025, and in the covered 2023 window (each separately).**

Why 5 %: WEIM occupies, relative to bilateral base schedules, the structural position an ISO's
real-time market occupies relative to its day-ahead market — it clears the deviation, and the RT LMP
is nonetheless the benchmark this rubric scores in every ISO. The RT layer of an organised market is a
few per cent of load; a WEIM that re-optimises less than one-twentieth of the footprint's energy across
BAAs would be thinner than that layer, and its price would be the price of a residual, not of the
footprint. Five per cent is a convention on that argument, not a derived number, and it is written
down before the fetch so that it cannot become one afterwards.

**Stated limitation.** Transfers are the *cross-BAA* slice of what WEIM clears; the intra-BAA
imbalance energy WEIM dispatches is not published per BAA. The measured share is therefore a **lower
bound** on the cleared volume, and the threshold is applied to the lower bound — the conservative
direction.

**Cross-check (STOP if it fails).** The WEIM quarterly benefits reports (westerneim.com, Q1-2023 …
Q4-2025, downloaded) publish per-BAA transfer volumes. For the footprint BAAs and the quarters inside
the served window, the OASIS-summed volume must agree with the reports' published volume within
**±10 %**; if it does not, the OASIS quantity is not what this document says it is, and the lane
stops to reconcile before D2 is scored.

### D3 — reconciliation against Mid-C Peak (the independent anchor; never the benchmark)

**Anchor rows.** `Mid C Peak` rows of the three ICE workbooks with **delivery start = delivery end**
(single-day products). Multi-day package rows (59 / 55 / 55 of 244 / 225 / 229) are **excluded**: the
workbook does not itemise which days a package covers, so a per-day comparison would be a guess.
Delivery days are taken from the workbook, so no holiday table is needed; a weekday census of the
single-day rows is reported (an on-peak product should show no Sundays — a structural check on the
product's definition, not a gate).

**WEIM side.** For each anchor delivery date *D* (a Pacific calendar day): `W_D` = the simple mean over
the **16 heavy-load hours HE07–HE22 Pacific PREVAILING time** (the WSPP/WECC on-peak block that the
Mid-C peak product delivers) of the **NW-group** price — demand-weighted `BPAT / PSEI / SCL / TPWR`,
Mid-C being the mid-Columbia hub inside that group. The raw store is UTC, so the prevailing-time block
is exact (UTC 14:00–06:00 in PDT months, 15:00–07:00 in PST). `ELAP_BPAT` alone is reported as a
diagnostic column, not gated. `M_D` = the row's `Wtd avg price $/MWh`.

| leg | PASS requires, in **each** year (2023 on its Jun–Dec dates) |
|---|---|
| D3.1 level | `|mean_D W_D − mean_D M_D| / mean_D M_D ≤ 10 %` — `PRICE_MEAN_TOL`: the benchmark must agree with its independent anchor at least as tightly as the rubric will hold the model to the benchmark, else the benchmark's own uncertainty exceeds the gate it feeds |
| D3.2 shape | Pearson `r(W_D, M_D)` across delivery days ≥ **0.80** |
| D3.3 support | `n_D ≥ 100` delivery days (2023: `≥ 60`) |

Stated ex ante: a DA-bilateral vs RT-imbalance premium is real and its sign is expected to be RT
below DA on average; its magnitude is unknown to me. If the measured level gap exceeds 10 % the gate
FAILS and the NO is written; the tolerance is not re-cut to 15 %.

### D4 — structural sanity (STOP only)

No priced BA has a negative annual mean; no hourly footprint price outside `[−$500, $2,000]/MWh`
(a value past CAISO's hard cap is a parse defect, not a price); footprint load-weighted annual mean in
`(0, 250]` $/MWh. Any breach is a build defect and stops the lane; none of these is a fit.

### Verdict rule

`SERIES LANDED` ⇔ D1.1 ∧ D1.2 ∧ D1.3 ∧ D2 (every year, cross-check held) ∧ D3.1 ∧ D3.2 ∧ D3.3
(every year) ∧ D4. Otherwise `NO`, with the failing cell named.

---

## 6. (e) What happens on NO

- **Nothing** is written to `data/raw/_validation-source/`.
- The raw store `data/raw/nwpp-weim/` and the builder still land: the store is measured market data
  in this lane's own region, worth having whatever the verdict, and the FINDING must be reproducible.
- The FINDING's first line is `NO — <failing cell, measured value vs. bar>`, and the ruled fallback
  (card N2 limb b: a determination naming its own basis, never a bare `CALIBRATED`) applies to any
  later NWPP run. A NO is a successful lane.

---

## 7. What is landed on SERIES LANDED, and its shape

`data/raw/_validation-source/actual_lmp_hourly_NWPP.parquet` — `year` int16 · `hour` int16 (0–8759,
fixed-PST non-leap clock) · `rt` float32 (the footprint demand-weighted WEIM hourly LMP; NaN where
D1's rules say so) · `da` float32 (all NaN — no day-ahead market existed). 8,760 rows per year,
2023–2025. Exactly the SPP / CAISO system-file schema.

**Not landed by this lane** (outside FILES YOU OWN — routed to NWPP-DESK in the FINDING): a per-BA
zonal validation file (the per-BA hourly series lives in the raw store, so it is a zero-cost derive),
the `actual_lmp.json` NWPP block with `rt_cov.mon` (NWPP-31), `TAIL_THRESHOLD["NWPP"]` (gate G6),
the `_validation-source/README.md` row.

---

## 8. The fetch plan (paging measured, not assumed)

- `PRC_RTPD_LMP`: **12 nodes per request, one calendar month per request** — measured 2026-09-13:
  12 nodes × 31 days returned 142,848 rows = 12 × 31 × 96 × 4, i.e. complete (the multi-node
  truncation `fetch_caiso_oasis.py` documents for `PRC_LMP` did not occur for this product). Every
  response is checked against its expected row count and the window halves on a shortfall.
  Window: first served day (walked from 2023-06-01 backwards one day at a time until ERR 1000)
  → 2026-01-01 08:00 UTC. ≈ 31 requests.
- `ENE_EIM_TRANSFER`: `version=2`, `RTPD`, `baa_grp_id=ALL`, one month per request (measured: 31 days
  → 68,356 rows). ≈ 31 requests. All 23 BAAs stored; footprint subset used.
- ≥ 6 s between requests; HTTP 429 backs off 15 s × attempt. Nothing runs in parallel against OASIS.
- ICE: the three `ice_electric-<yr>final.xlsx` workbooks (HTTP 200, 2026-09-13), `Mid C Peak` rows
  only. SP15 / NP15 / Palo Verde columns are in the same sheet and are **not read into any artifact**.
- Committed store (`data/raw/nwpp-weim/`, README + SOURCES + SHA256SUMS in the `spp-planning`
  template): `weim_rtpd_lmp_15min.parquet` (interval_start_utc, baa, lmp, mce, mcc, mcl),
  `weim_transfer_15min.parquet` (interval_start_utc, baa, xfer_mw), `midc_peak_daily.parquet`,
  `weim_hourly_by_ba.parquet` (year, hour, baa, lmp — the per-BA product on the model clock), and
  `gate.json` (every measured cell of §5). Raw CSV pulls are not committed (the ERCOT / NYISO / SPP
  precedent): OASIS retention makes the committed parquet the durable record, and a forward year
  regenerates from the same query — rule 13's forward test.

---

## 9. Rules this lane is bound by, restated in one line each

1 `[R-STRUCT]` no residual is read, and the gate cannot promote; 13 `[R-MEASURED]` every input is a
market quantity that regenerates for a forward year; 14 `[R-ACCURATE]` if the real series makes a
later backcast look worse that is a bug elsewhere, never a reason to touch the index; 23
`[R-FROZEN-DERIVE]` the builder re-runs only when its sources change; 25 `[R-ISO-SCOPE]` nothing
CAISO-priced enters (G17); 27 `[R-PUSH]` fetch-back verify every pushed file ≥ 300 lines; §8.0 no
shared record is edited — the FINDING carries a `## Log entry` for the desk.
