# FINDING — SOCO-11: EPA CAMPD (AL/GA) + FERC-714 zonal load + interchange

**Lane:** SOCO-11 · **Date:** 2026-09-13 · **Branch:** `claude/soco-11-fetch-a7f3`
(cut at pinned `2c2fc065`) · **Profile:** `shared` · **Charter:**
`docs/multi-iso/soco-addition-plan-2026-09.md` §2.4, §2.5, §5 row SOCO-11, §6 rows 1-3.

## 0. Headline

| Item | Result |
|---|---|
| **(1) CEMS AL/GA** | **ALL EIGHT LANDED** — {AL,GA} × {2023,2024,2025,2026-Q1}, every one schema-equal to `MS_2024.parquet` |
| **(2) FERC-714 spine** | **LANDED; THE RECONCILIATION GATE FAILS.** The three chartered respondents are **73.2 %** of the BA's metered demand — short **61.4 / 66.2 / 64.2 TWh** (26.8 / 27.7 / 26.8 %) in 2023 / 2024 / 2025. Nothing rescaled; raw landed, failure documented, lane stopped, as chartered |
| **(3) Interchange** | **LANDED and CONFIRMS the charter** — SOCO is a net exporter of **+10.155 / +10.832 / +13.038 TWh**, against the charter's 10.2 / 10.8 / 13.0 |
| Blocked | FERC's own bulk host, **403 from this egress too** (§4). Route 1 (PUDL) served the item, so nothing is outstanding |

## 1. Got / blocked

| # | Item | Status | Route | Path |
|---|---|---|---|---|
| 1 | CAMPD hourly CEMS AL 2023/2024/2025 | **got** | `api.epa.gov` bulk state CSV, anonymous | `data/raw/campd-unit-level/AL_{2023,2024,2025}.parquet` |
| 1b | CAMPD hourly CEMS GA 2023/2024/2025 | **got** | same | `data/raw/campd-unit-level/GA_{2023,2024,2025}.parquet` |
| 1c | CAMPD hourly CEMS AL/GA 2026 partial | **got** | `api.epa.gov` bulk **quarterly** national CSV, `--quarters 1` | `…/{AL,GA}_2026.parquet` |
| 2 | FERC-714 hourly planning-area demand | **got** (route 1) | PUDL S3 nightly parquet | `data/raw/zone-specific-demand/SOCO/soco_ferc714_hourly_planning_area_demand_2023-2025.parquet` |
| 2b | FERC-714 via FERC's own bulk CSV | **blocked 403** | `www.ferc.gov` | — (route 1 served the item) |
| 3 | SOCO BA-to-BA interchange 2023-2025 | **got** | EIA Grid Monitor six-month bulk CSVs, **keyless** | `data/raw/eia-930-interchange/SOCO interchange hourly.parquet` |
| — | `EIA_API_KEY` | **absent** | — | worked around with `--source bulk`, per charter |

### Blocked table — exact URLs and statuses

| URL | Method | Status | Bytes |
|---|---|---|---|
| `https://www.ferc.gov/sites/default/files/2020-06/Form-714-csv-files.zip` | HEAD | **403** | — |
| `https://www.ferc.gov/sites/default/files/2020-06/Form-714-csv-files.zip` | GET, `Range: 0-1023` | **403** | 5,574 (error body) |
| `https://www.ferc.gov/industries-data/electric/general-information/electric-industry-forms/form-no-714-annual-electric/data` | HEAD | **403** | — |
| `https://www.ferc.gov/` | HEAD | **403** | — |

FERC's static host refuses this egress exactly as it refused the charter's —
**the whole host, including its landing page**, so this is an egress block and
not a missing artifact. Route 1 (PUDL) is the committed route and needs no
fallback. Nothing was transcribed from memory and no secondary-source value
was used.

## 2. Item 1 — CEMS

```
python scripts/data/fetch_campd_unit_level.py --year <2023|2024|2025> --states AL GA
python scripts/data/fetch_campd_unit_level.py --year 2026 --quarters 1 --states AL GA \
    --holdout-intake SOCO
```

Each state-year CSV is ~187 MB; each was fetched, converted, verified and
**deleted before the next** per the charter's disk plan. Peak writable-disk
use never exceeded one intermediate CSV.

| file | rows | facilities | units | span | MB | schema == `MS_2024` |
|---|---:|---:|---:|---|---:|---|
| `AL_2023.parquet` | 740,328 | 23 | 88 | 2023-01-01 .. 2023-12-31 | 3.34 | **OK** |
| `AL_2024.parquet` | 772,992 | 23 | 88 | 2024-01-01 .. 2024-12-31 | 3.31 | **OK** |
| `AL_2025.parquet` | 770,880 | 23 | 88 | 2025-01-01 .. 2025-12-31 | 3.30 | **OK** |
| `AL_2026.parquet` | 190,080 | 23 | 88 | 2026-01-01 .. 2026-03-31 | 0.81 | **OK** |
| `GA_2023.parquet` | 1,147,560 | 32 | 131 | 2023-01-01 .. 2023-12-31 | 3.11 | **OK** |
| `GA_2024.parquet` | 1,150,704 | 32 | 131 | 2024-01-01 .. 2024-12-31 | 3.11 | **OK** |
| `GA_2025.parquet` | 1,147,560 | 32 | 131 | 2025-01-01 .. 2025-12-31 | 3.23 | **OK** |
| `GA_2026.parquet` | 282,960 | 32 | 131 | 2026-01-01 .. 2026-03-31 | 0.81 | **OK** |

**Schema check.** The fetcher asserts against *the same state's newest
sibling*, which for the first AL and GA files was `WY_2026.parquet`. The
charter names `MS_2024` specifically, so all eight were **re-checked against
`MS_2024.parquet` after the fact** — all sixteen `(name, arrow type)` pairs
identical in every file, and each file confined to its own year.

**Seven of eight are exact units × hours rectangles.** `AL_2023` is not:
five units stop reporting mid-year — Barry unit 8, Colbert `CCT9` / `CCT10` /
`CCT11` (2,208 h each, Q1 only) and Charles R Lowman `CC1` (4,416 h, H1) —
for 30,552 rows against 88 × 8,760. Carried unmodified; `data/raw` is
immutable and this is EPA's own coverage.

**A state extract is not a BA extract.** Colbert is TVA's and Lowman is
PowerSouth's. The SOCO fleet crosswalk (SOCO-30) must filter these files to
the SOCO BA rather than treating AL+GA as the footprint.

**`SHA256SUMS.txt` was NOT touched**, deliberately. Its own header scopes it
to the 35 gitignored `<ST>_2018.parquet` extracts; the 2019-2026 files are
tracked, so git's blob hashes are their integrity record. Adding rows for
tracked files would misrepresent that file's scope. **Routed to the desk** in
case the charter intended otherwise.

## 3. Item 2 — the FERC-714 spine, and the gate that fails

Full provenance, the eight-respondent table and the diagnostic reasoning are
in the committed `data/raw/zone-specific-demand/SOCO/SOURCES.md`. The gate
itself:

### 3.1 Timezone alignment applied

**`America/Chicago`, measured on two independent sources, not assumed** — the
footprint spans two civil zones (AL/MS Central, GA Eastern) so this could not
be taken for granted:

* the committed `SOCO hourly.parquet` carries exactly two UTC-minus-local
  offsets, **6 h on 9,171 rows and 5 h on 17,133**, switching on the US DST
  dates — CST/CDT, never EST/EDT;
* every Southern FERC-714 respondent (Alabama Power 2, Georgia Power 183,
  Mississippi Power 184, Southern Power 186, and the SOCO BA respondent 142)
  reports `timezone = America/Chicago`. MEAG and Tallahassee report
  `America/New_York`; PUDL's `datetime_utc` resolves each respondent's own
  zone, so the join is unaffected.

**Georgia Power's operating clock is Eastern; Central is the BA's reporting
clock**, and that is what these products are stamped on. A
`"SOCO": "America/Chicago"` key was added to `BA_TIMEZONE` on that basis
(additive only).

**The join itself is zero-shift UTC, measured.** Correlating the three
respondents' hourly sum against `SOCO hourly.parquet::Demand` over shifts
−4 h .. +4 h:

| shift | −4 | −3 | −2 | −1 | **0** | +1 | +2 | +3 | +4 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| pearson r | 0.7371 | 0.8370 | 0.9186 | 0.9733 | **0.9935** | 0.9755 | 0.9235 | 0.8451 | 0.7485 |

A sharp single peak at k = 0: `datetime_utc` and `UTC time` are the same stamp.

### 3.2 THE GATE — FAILED

| year | 714 three TWh | 930 BA TWh | residual TWh | residual % | pearson r | max abs Δ MW | mean Δ MW | median abs Δ MW |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 168.059 | 229.436 | **61.377** | **26.75** | 0.995967 | 13,155 | 7,007 | 6,560 |
| 2024 | 173.123 | 239.349 | **66.226** | **27.67** | 0.995795 | 13,386 | 7,539 | 7,125 |
| 2025 | 175.357 | 239.518 | **64.161** | **26.79** | 0.990045 | 14,706 | 7,324 | 6,916 |

Shape right (r ≈ 0.99), level short by a quarter in **every hour of every
year**. That is the signature of whole planning areas absent from the sum,
not of a scaling error.

**Per the charter and rule 13 `[R-MEASURED]`: nothing was rescaled to close
it.** The raw is landed, the failure is documented, the lane stops here. **No
load share was derived** (rule 23 `[R-FROZEN-DERIVE]` — that is SOCO-32's).

### 3.3 Diagnostic offered to the desk, NOT applied

Two further planning areas file the same schedule and are the Georgia
Integrated Transmission System's other co-owners:

| sum | 2023 resid % | 2024 resid % | 2025 resid % |
|---|---:|---:|---:|
| three operating companies **(the gate)** | **26.75** | **27.67** | **26.79** |
| + Oglethorpe (107) + MEAG (210) | 3.03 | 2.92 | 1.26 |
| + Southern Power Co (186) | 1.63 | 1.50 | −0.03 |
| + PowerSouth (1) + Tallahassee (34) **(falsifier)** | **−2.28** | **−2.41** | **−4.15** |

The falsifier row is the reason this is evidence rather than curve-fitting:
PowerSouth and Tallahassee run **their own** balancing authorities (`AEC`,
`TAL`), and adding them **overshoots**. The enumeration discriminates on BA
membership, not on whichever combination minimises the residual.

**What this lane could NOT establish — routed to the desk.** PUDL's
county attribution gives 100 % containment inside the SOCO BA's 252-county
footprint for Alabama Power (59/59), Georgia Power (155/155) and Mississippi
Power (23/23), and 0/1 for Tallahassee — so the test works where it has data.
But PUDL carries **no county attribution at all** for Oglethorpe, MEAG,
Southern Power or PowerSouth: G&T cooperatives and joint-action agencies have
no retail territory of their own. **A documented BA-membership citation is
needed before any load share is built on the five- or six-respondent sum.**
This is a documents question, so it may sit naturally with SOCO-12.

**Also note there is no BA-level 714 series to check against**: the SOCO BA
is itself a respondent (142, `eia_code` 18195) but has filed no hourly demand
since 2006.

### 3.4 The largest hourly residuals are the 930 side's defects, not the 714's

At 2025-10-23T21 UTC the BA series reads **12,638 MW** while all five
respondents behave normally and sum to 24,694; 2025-09-19T17 (21,203 vs
33,763) and 2025-09-06T15 (16,405 vs 28,408) are the same class. Those hours
drive the 2025 `max abs Δ` in every row of the tables above. Under rule 14
`[R-ACCURATE]` the 714 series is the better-behaved one in those hours, and
the 930 dropouts are a separate defect for SOCO-10's 930 screen.

## 4. Item 3 — interchange

```
python scripts/data/fetch_eia930_interchange.py --ba SOCO --source bulk --years 2023 2024 2025
```

Keyless bulk route (no `EIA_API_KEY` in this container, as in the charter's).
236,736 rows, nine DIBAs, 2023-01-01 01:00 .. 2026-01-01 00:00 on
`America/Chicago`.

**Sign convention: EIA's — positive = SOCO EXPORTS to the DIBA.** Verified
rather than assumed, by the sum-of-legs agreeing in *sign and magnitude* with
the BA-level `Total interchange` column (below).

### 4.1 System net — CONFIRMS the charter

| year | sum of legs TWh | BA `Total interchange` TWh | charter's measurement |
|---|---:|---:|---:|
| 2023 | **+10.155** | +10.156 | 10.2 |
| 2024 | **+10.832** | +10.831 | 10.8 |
| 2025 | **+13.038** | +13.021 | 13.0 |

SOCO is a net **exporter** in all three years, and growing. Agreement between
the per-seam legs and the BA book is **0.001 / 0.001 / 0.017 TWh** — far
tighter than the usual gap (SWPP's is 0.4-0.7 TWh). Hour by hour on the local
clock, **24,100 of 26,294** joined hours are *exactly* equal (r = 0.9986);
every ±1 h shift collapses that to ~50.

### 4.2 Data quality — the cleanest book in the corpus

* **Zero NaN hours**, on any DIBA, in any year (SWPP: 97 / 361 / 936).
* Full grain on every DIBA: 8,759 / 8,784 / 8,760 h — the three absent hours
  are the DST spring-forward 02:00 local, correctly so.
* **No impossible print.** Extremes are `TVA` −3,150 MW and `FPL` +2,843 MW,
  both plausible for those ties. Nothing of the SWPP `AECI` −5.4 M MW class.
* `AEC` (PowerSouth) is **not** booked as a SOCO seam in this product,
  although its territory is embedded in Southern's.

### 4.3 Duration curves — per counterparty, per year, MW

Positive = SOCO exports to the DIBA.

| yr | DIBA | min | p1 | p5 | p25 | p50 | p75 | p95 | p99 | max | % h exporting | net TWh |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | `DUK` | -1,797 | -1,349 | -988 | -597 | -382 | -206 | 21 | 184 | 402 | 6.0 | -3.692 |
| 2023 | `FPC` | -169 | -123 | -80 | -32 | 2 | 43 | 124 | 201 | 313 | 51.0 | +0.082 |
| 2023 | `FPL` | -1,008 | -551 | -276 | 36 | 243 | 550 | 1,235 | 1,863 | 2,622 | 78.7 | +2.903 |
| 2023 | `MISO` | -683 | -319 | -49 | 276 | 497 | 726 | 1,054 | 1,267 | 1,507 | 93.5 | +4.388 |
| 2023 | `SC` | -57 | 69 | 182 | 347 | 464 | 583 | 736 | 836 | 984 | 99.7 | +4.055 |
| 2023 | `SCEG` | -75 | 167 | 384 | 679 | 827 | 975 | 1,152 | 1,268 | 1,462 | 99.7 | +7.119 |
| 2023 | `SEPA` | -784 | -630 | -473 | -274 | -203 | -139 | -70 | -19 | 10 | 0.2 | -1.949 |
| 2023 | `TAL` | -66 | -33 | 0 | 44 | 79 | 116 | 166 | 198 | 294 | 94.7 | +0.706 |
| 2023 | `TVA` | -2,663 | -1,730 | -1,391 | -881 | -453 | 38 | 784 | 1,365 | 2,940 | 26.7 | -3.456 |
| 2024 | `DUK` | -1,779 | -1,339 | -1,030 | -642 | -427 | -209 | 42 | 248 | 633 | 6.6 | -3.859 |
| 2024 | `FPC` | -262 | -174 | -110 | -43 | -6 | 30 | 125 | 209 | 298 | 44.8 | -0.024 |
| 2024 | `FPL` | -1,280 | -823 | -471 | 34 | 308 | 561 | 1,188 | 1,731 | 2,843 | 77.3 | +2.770 |
| 2024 | `MISO` | -478 | -145 | 11 | 304 | 504 | 708 | 1,020 | 1,332 | 1,780 | 95.3 | +4.494 |
| 2024 | `SC` | -189 | 0 | 181 | 377 | 527 | 665 | 862 | 1,030 | 1,242 | 98.7 | +4.588 |
| 2024 | `SCEG` | -57 | 407 | 656 | 888 | 1,026 | 1,153 | 1,303 | 1,393 | 1,537 | 99.9 | +8.845 |
| 2024 | `SEPA` | -904 | -685 | -568 | -378 | -264 | -188 | -109 | -55 | 48 | 0.1 | -2.580 |
| 2024 | `TAL` | -67 | -30 | 1 | 47 | 72 | 107 | 157 | 185 | 274 | 95.1 | +0.672 |
| 2024 | `TVA` | -2,507 | -1,751 | -1,371 | -854 | -516 | -149 | 658 | 1,538 | 3,007 | 18.0 | -4.075 |
| 2025 | `DUK` | -1,954 | -1,554 | -1,219 | -771 | -472 | -148 | 220 | 465 | 863 | 12.3 | -4.159 |
| 2025 | `FPC` | -354 | -252 | -187 | -93 | -46 | 0 | 82 | 162 | 303 | 24.8 | -0.419 |
| 2025 | `FPL` | -996 | -515 | -219 | 109 | 294 | 522 | 1,038 | 1,481 | 1,969 | 85.0 | +2.911 |
| 2025 | `MISO` | -628 | -279 | -92 | 275 | 546 | 799 | 1,166 | 1,359 | 1,657 | 91.4 | +4.725 |
| 2025 | `SC` | -64 | 0 | 130 | 416 | 556 | 693 | 940 | 1,124 | 1,241 | 95.8 | +4.834 |
| 2025 | `SCEG` | -40 | 336 | 657 | 959 | 1,109 | 1,305 | 1,524 | 1,718 | 2,123 | 100.0 | +9.779 |
| 2025 | `SEPA` | -910 | -695 | -553 | -350 | -247 | -160 | -41 | 58 | 217 | 2.8 | -2.311 |
| 2025 | `TAL` | -91 | -40 | -18 | 28 | 63 | 99 | 144 | 179 | 291 | 88.9 | +0.556 |
| 2025 | `TVA` | -3,150 | -1,734 | -1,300 | -778 | -368 | 71 | 859 | 1,408 | 2,689 | 28.4 | -2.878 |

**Reading it:** `SEPA` (federal hydro, Southeastern Power Administration) and
`DUK` are near-unidirectional imports; `SCEG` and `SC` near-unidirectional
exports (~100 % and 96-100 % of hours). `TVA` is the only genuinely two-way
seam — 27 / 18 / 28 % of hours exporting, with a ±2,500-3,150 MW range —
and is the one a seam ladder will actually have to model as bidirectional.
`FPC` is small and drifting from balanced to import across the window.

## 5. Files landed

| path | bytes | note |
|---|---:|---|
| `data/raw/campd-unit-level/{AL,GA}_{2023,2024,2025,2026}.parquet` | 8 files, 17.9 MB | + README section |
| `data/raw/zone-specific-demand/SOCO/soco_ferc714_hourly_planning_area_demand_2023-2025.parquet` | 3,181,096 | NEW dir |
| `data/raw/zone-specific-demand/SOCO/SOURCES.md` | — | NEW |
| `data/raw/eia-930-interchange/SOCO interchange hourly.parquet` | — | + README section |
| `scripts/data/fetch_eia930_hourly.py` | — | **additive key only**: `"SOCO": "America/Chicago"` |

No existing raw file was modified. No `src/`, `configs/`, `tests/`,
`frontend/` or shared-record edit. No matrix cell moved (rule 28 — this lane
tests no mechanism). No CI workflow added. No solve run.

## 6. Routed to the desk

1. **The 714 gate fails and the fix is a citation, not a fetch.** Oglethorpe
   and MEAG close it to ~1-3 %, but their BA membership cannot be documented
   from PUDL. Someone must supply a primary citation before SOCO-32 builds a
   share. Natural fit: **SOCO-12**.
2. **The 930 `Demand` column has dropout hours in 2025** (§3.4), independent
   of the 714 question. For **SOCO-10**'s 930 defect screen.
3. **Timezone (gate G19) is answered from this lane's side**: Central, on two
   independent sources, for both the demand and interchange products. SOCO-10
   owns the gate — this is offered as corroboration, not as its closure. If
   SOCO-10 concludes otherwise, the `BA_TIMEZONE` key must be revisited.
4. **`SHA256SUMS.txt`**: not touched, for the scope reason in §2. Confirm.
5. **Holdout widening is cheap**: the PUDL table spans 2006-2026 for all eight
   respondents, so 2019-2022 is a re-slice of the same pull — no new route, no
   key. CEMS back years are the same `--holdout-intake` route SPP-15 used.

## Log entry

```
### soco-11 — 2026-09-13 — CEMS AL/GA + FERC-714 spine + interchange

Landed all eight {AL,GA} x {2023,2024,2025,2026-Q1} CAMPD extracts
(schema-equal to MS_2024; AL 23 fac / 88 units, GA 32 / 131), the FERC-714
hourly planning-area demand spine (8 respondents, 210,431 rows, via PUDL --
FERC's own host 403s from this egress as it did at charter), and the SOCO
BA-to-BA interchange book (236,736 rows, 9 DIBAs, keyless bulk route).

THE 714 RECONCILIATION GATE FAILS: the three chartered respondents are 73.2%
of the BA's metered demand (short 61.4 / 66.2 / 64.2 TWh; r = 0.996 / 0.996 /
0.990). Nothing rescaled -- raw landed, failure documented, lane stopped, per
rule 13. Diagnostic offered not applied: Oglethorpe + MEAG close it to
3.0 / 2.9 / 1.3%, and the falsifier (PowerSouth + Tallahassee, own BAs)
overshoots to -2.3 / -2.4 / -4.2%. BLOCKER ROUTED: PUDL carries no county
attribution for Oglethorpe or MEAG, so their BA membership needs a primary
citation before SOCO-32 builds any share.

Interchange CONFIRMS the charter: SOCO nets +10.155 / +10.832 / +13.038 TWh
exported, agreeing with the BA book to 0.001 / 0.001 / 0.017 TWh. Zero NaN
hours and no impossible print -- the cleanest interchange book in the corpus.
TVA is the only genuinely two-way seam.

Timezone: America/Chicago, measured on two independent sources (930 offsets
are CST/CDT; every Southern 714 respondent reports Central). BA_TIMEZONE
gains "SOCO" as an additive key.
```
