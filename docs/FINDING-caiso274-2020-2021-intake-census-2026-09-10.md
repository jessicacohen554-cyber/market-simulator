# FINDING — caiso-274: the CAISO 2020/2021 backcast intake is BLOCKED, and why

**Session:** caiso-274 (card B of the caiso-273 charter). **Date:** 2026-09-10.
**Pinned revision:** `5df291c5254ec0871f9a84ed36ea6cc4e2a9f9f7`. **Zero LP spent.**

## 0 — Verdict

Neither target is deliverable in a zero-LP intake lane.

| Target | 2020 | 2021 |
|---|---|---|
| `caiso_supply_consistent_demand_<y>.csv` | **NOT DELIVERED** | **NOT DELIVERED** |
| `bench/CAISO/<y>.json.gz` | **NOT DELIVERED** | **NOT DELIVERED** |

Two independent blockers, both established below by measurement:

* **B-1 (both years, both targets, structural).** A bench part cannot be built
  without a solved bundle. The demand artifact reads the bench part. So both
  targets sit behind a **bench-scaffold LP solve** — the same circularity
  caiso-262 named in `PRECOMMIT-caiso262-2022-touchpoint-2026-09-07.md` §5.1
  and broke by spending one.
* **B-2 (data, 2020 hard / 2021 partial).** The bench part carries `avgLMP`, a
  measured price. CAISO has **no committed 2020 LMP at all** and only
  **2021-04-27 onward** for 2021; and as of today the OASIS re-fetch boundary
  has moved to **2021-08-12**, so the missing head of 2021 is not recoverable
  either. A 2020 bench part cannot carry a price actual by any route.

**2020 additionally carries a source defect (§4) that the pre-registered guard
recipe would NOT catch.** 2021's upstream data is otherwise clean.

## 1 — Phase-0 availability census

Measured on this container at the pinned SHA. (The repo arrived as a FULL
clone, so `hydrate_data.py --profile caiso` was a no-op — it says so and exits
0; nothing here is a sparse-checkout artifact.)

| Source | Path | 2020 | 2021 | Measured |
|---|---|---|---|---|
| EIA-930 BALANCE (raw) | `data/raw/eia-930/EIA930_BALANCE_{2020,2021}_{Jan_Jun,Jul_Dec}.parquet` | **PRESENT** | **PRESENT** | CISO 8,784 / 8,760 rows |
| EIA-930 CISO hourly extract | `data/raw/eia-930-hourly/CISO hourly.parquet` | **PRESENT** | **PRESENT** | see §2 |
| CAMPD unit-level CEMS | `data/raw/campd-unit-level/CA_{2020,2021}.parquet` | **PRESENT** | **PRESENT** | 126 plants, 1,103,760 rows each (=126×8760) |
| EIA-923 monthly generation | `data/raw/_processed-legacy/eia923_monthly_generation.parquet` | **PRESENT** | **PRESENT** | 15,115 / 15,796 rows |
| EIA-923 monthly fuel costs | `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` | **PRESENT** | **PRESENT** | 8,225 / 8,476 rows |
| EIA-860 fleet vintages | `data/raw/eia-860/vintage_{2020,2021}/` | **PRESENT** | **PRESENT** | both vintages on disk (2018–2024) |
| Delivered gas — CA citygate daily | `data/raw/gas-prices/caiso_citygate_daily.csv` | **PRESENT** | **PRESENT** | 213 / 231 daily rows |
| Delivered gas — EIA CA citygate monthly | `data/raw/gas-prices/eia_citygate_CA_monthly.csv` | **PRESENT** | **PRESENT** | continuous from 2015-01 |
| NRC reactor status (nuclear) | `data/raw/nrc-reactor-status/{2020,2021}PowerStatus.txt` | **PRESENT** | **PRESENT** | both files on disk |
| **CAISO LMP (hourly DAM/RTM)** | `data/raw/lmp-data/CAISO/CAISO_{dam,rtm}_hourly_<y>.csv` | **ABSENT** | **PARTIAL** | no 2020 file; 2021 spans **2021-04-27 → year end** only (DAM 5,977 h/node, RTM 4,513 h/node, of 8,760) |
| **CARB allowance price** | `data/raw/policy/carbon-auction-results/carbon-auction-results.csv`; `STATE_CARBON_PRICE_BY_ISO["CAISO"]` | was ABSENT → **LANDED** (§9.1) | was ABSENT → **LANDED** (§9.1) | CARB rows started **2022 Q1** and the config dict is still `{2022…2025}`; the eight 2020/2021 auction rows were transcribed by this session, the config anchor is not installed (out of scope) |
| Derived nuclear availability | `data/raw/nuclear-availability-CAISO.csv` | **ABSENT** | **ABSENT** | file spans 2022–2025 only; derivable, but gated on a config anchor — see §9.2 |
| Derived actual LMP / tail | `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`, `actual_lmp.json` | **ABSENT** | **ABSENT** | years 2022–2026 only; blocked by the LMP row above |

Derived-artifact rows are **downstream**, not upstream gaps: nuclear
availability regenerates from the NRC + EIA-923 files already present. The
CARB and LMP rows are genuine source gaps.

## 2 — EIA-930 CISO cell completeness (non-null hours per year)

| year | rows | Demand | Net generation | Total interchange | NG: NG | NG: SUN | NG: WND | NG: WAT |
|---|---|---|---|---|---|---|---|---|
| 2020 | 8760 | 8781 | 8782 | 8784 | 8780 | 8780 | 8781 | **3109** |
| 2021 | 8760 | 8755 | 8755 | 8736 | 8755 | 8755 | 8755 | 8755 |
| 2022 | 8760 | 8757 | 8757 | 8760 | 8757 | 8757 | 8757 | 8757 |

(Counts are over the raw calendar year — 2020 is a leap year, 8,784 h; the
loader's `_eia_hourly_frame_filled` returns the model's 8,760-hour frame, so
rule 8 `[R-8760]` is satisfied and Feb-29 is dropped as for every other ISO.)

Every cell the demand construction consumes — `Net generation`, `NG: NG`,
`Total interchange` — is essentially complete in both years. **`NG: WAT` is
only 35 % populated in 2020**; it does not enter the demand construction and
CAISO hydro's `classFull` actual comes from EIA-923, but it would leave the
2020 bench part's raw `e930` hydro cell unusable.

## 3 — The blocker, precisely (B-1)

`derive_caiso_supply_consistent_demand.py` opens
`frontend/data/backcast/bench/CAISO/<year>.json.gz` and reads
`bench.e930.gas_cems_grid`, `bench.e930.gas_cogen_grid`, the per-plant CEMS
hourly series and `bench.classFull`. It `SystemExit`s without them.

Bench parts are written by `render_calibration_html.build_payload` →
`render_backcast._write_bench_part`. Inside `build_payload` the year loop reads
`<bundle>/dispatch/<year>_P1.parquet` and derives `classes_p` / `zone_p` from
it; the bench plant map is then built by intersecting the CAMPD plants against
that dispatch map (`# CAMPD plant absent from the dispatch (as before)`), and
`bplants[key]["zone"]` comes from the dispatch too. **So the bench plant set
and its zone attribution are run-dependent, and a bench part for a year with no
bundle requires a solve.**

**Correction to the card-B charter.** The charter names
`scripts/data/regen_caiso_bench_cems.py` as the bench "builder". It is not — it
is an *amender*: it opens an existing `<year>.json.gz` and rewrites fields in
it, and its `YEARS` is `(2023, 2024, 2025)`. The 2022 part was never passed
through it. Since the CEMS-anchor rework landed inline in `build_payload`
(the `_iso_anchor in EIA930_NG_CELL_CORRUPT` block writes `gas_cems_grid`,
`gas_cogen_grid`, `fossil_cems_grid`), **`build_payload` is the sole canonical
writer for a new year and `regen_caiso_bench_cems.py` is not on the path at
all.** Verified: the committed 2022 and 2023 parts carry identical
`meta.builderFingerprint` `bee29e135d42` and both carry the anchor fields.

The route a follow-on lane must take is therefore caiso-262 §5.1's, unchanged:
a **bench-scaffold solve** (the keeper recipe with
`--no-caiso-supply-consistent-demand`), never scored, never registered, whose
only surviving output is the bench part — then the demand derive, then the real
rung, then G-BENCH byte-identity of the part rebuilt from the rung's bundle.

## 4 — The 2020 source defect (report before anyone spends a solve)

The CISO EIA-930 `Demand ≈ Net generation + Total interchange` identity is
violated in 2020 by an order of magnitude more than in any neighbouring year.
Measured on the **raw** `EIA930_BALANCE` parquets (TWh; `ident = NG − TI`,
`gap = Demand − ident`):

| year | Net generation | Total interchange | Demand | ident | **gap** |
|---|---|---|---|---|---|
| 2020 | 138.936 | −59.390 | 217.893 | 198.326 | **+19.566** |
| 2021 | 158.912 | −54.372 | 219.050 | 213.284 | +5.766 |
| 2022 | 170.080 | −48.672 | 223.596 | 218.752 | +4.845 |
| 2023 | 183.975 | −28.457 | 218.134 | 212.432 | +5.702 |

The EIA `(Adjusted)` columns do **not** close it (2020 gap `+19.613`). The
`Demand` cell itself is stable across the four years (217.9 / 219.1 / 223.6 /
218.1); it is the **`Net generation` cell that is ~20 TWh short in 2020** and
climbs into family by 2021 — a reporting-coverage vintage effect in CISO's own
930 submissions, not something the model can repair.

**Why this matters and why the pre-registered guard would miss it.** The demand
construction begins `NetGen(t) − NG_cell(t) … − TI(t)`, so a ~19.6 TWh NetGen
deficit propagates ≈1:1 into derived 2020 demand. The G-DEMAND recipe
(caiso-262 §5.2) admits a wedge in `[−1.5, max(W23,W24,W25) + 1.5]`; I measured
that band below as `[−1.500, +19.176]` TWh. **A 2020 derive corrupted by
exactly this defect lands inside the band** — the band's generous upper limb
was sized by the NG-cell corruption of 2024/25, and it happens to be almost
exactly the size of 2020's deficit. The guard would pass a bad year silently.

Recommendation, for the owner rather than for this lane to act on: **2021 is
the sound rung; 2020 should not be derived on this construction** without
either an independent NetGen reconciliation or an explicit ruling. Stated as a
finding, not acted on.

## 5 — Numbers a follow-on lane can pre-register (computed here, before any derive)

These are the ex-ante values the caiso-262 recipes call for, computed now so
they cannot later be fitted to their own output.

### 5.1 G-DEMAND wedge band (`_ANNUAL_GUARD`)

`wedge(y) = [930 CISO NetGen − TI](y) − derived demand(y)`, on the loader's
filled 8,760-hour frame, from the committed artifacts:

* W2023 = **+5.417**, W2024 = **+10.779**, W2025 = **+17.676** TWh
  (reproduces caiso-262's +5.416 / +10.780 / +17.675 to rounding — the
  construction is reproduced, not re-invented).
* Band = `[−1.500, +19.176]` TWh.
* 2020 identity total **197.925** TWh → admissible window **[178.7, 199.4]** TWh.
* 2021 identity total **213.565** TWh → admissible window **[194.4, 215.1]** TWh.

**See §4 before using the 2020 window.**

### 5.2 CEMS bench-gas reproduction anchor (`_CEMS_GUARD` basis)

CAMPD decodes cleanly for both years. On the committed 2022 bench part's own
86 gas plant codes (`nodata` excluded) — the closest zero-LP proxy to the real
bench-coverage basis:

| year | CEMS gas (full-plant), 2022-bench plant basis | codes present in CAMPD |
|---|---|---|
| 2020 | **59.293** TWh | 85 / 86 |
| 2021 | **63.866** TWh | 86 / 86 |
| 2022 | 65.825 TWh | 86 / 86 |

The 2022 figure reproduces the committed part's own `cems_full`
(65.825 = 63.042 grid + 2.783 BTM) **exactly**, which is what makes the 2020
and 2021 figures trustworthy as pre-registration anchors.

Caveat that must not be dropped: the true 2020/2021 bench plant set is those
years' *own* dispatch fleet, so a unit retired before 2022 is missing from this
basis. These are **lower bounds on coverage**, not the anchor itself. On the
whole-fleet gas-group basis the same extracts give 58.972 (2020) / 63.615
(2021) / 65.586 (2022) TWh.

## 6 — OASIS GroupZip retention: RE-MEASURED, and it has moved

`fetch_caiso_oasis_grp.py` and `data/raw/lmp-data/CAISO/README.md` both say
"re-measure it, never hardcode it", and both record caiso-263's 2026-09-07
binary search: earliest served DAM trade date **2021-04-27**.

**Re-binary-searched 2026-09-10 through the session proxy: the boundary is now
`2021-08-12`.**

| probe | result |
|---|---|
| `DAM_LMP_GRP` v12 2023-01-01 (control) | HTTP 200, **11,938,424 B** — byte-size-identical to the pinned `SHA256SUMS.txt` entry; the endpoint works from this container |
| 2022-06-01 | DATA, 12,310,663 B |
| 2022-01-01 | DATA, 10,059,855 B |
| 2021-10-01 | DATA, 10,293,307 B |
| 2021-08-16 | DATA, 10,248,979 B |
| **2021-08-12** | **DATA, 10,362,306 B** ← earliest served |
| **2021-08-11** | **no-data envelope, 3,023 B** |
| 2021-08-08 / 08-09 / 08-10 | no-data envelope |
| 2021-07-01, 2021-04-27, 2021-04-01, 2021-01-15, 2020-06-01 | no-data envelope |
| `RTM_LMP_GRP` v3 2021-08-12 / 2021-08-11 | DATA 7,603,266 B / no-data — RTM tracks the same boundary |

Probes were repeated to rule out rate-limit flake: 2021-08-11 and 2021-08-12
each reproduced their verdict on a second pass, and the small responses are the
~3 KB "No data returned" envelope caiso-263 documented, not a 429/403.

Consequences, stated plainly:

* **2020 CAISO LMP is unreachable on every known route** — per-node `SingleZip`
  (~39-month window), GroupZip (now 2021-08-12), and the hand-downloaded GRP
  zips, whose bytes the 2026-08-16 history rewrite stripped.
* **2021 is worse than the committed CSVs suggest.** The tracked hourly
  aggregates hold 2021-04-27 onward (5,977 DAM h/node) because they were folded
  when GroupZip still served that date. Nothing before **2021-08-12** can be
  re-fetched now — so the committed 2021 head (Apr 27 → Aug 11) is itself
  irreplaceable, and roughly **the first third of 2021 has no price actual and
  never will**.
* This is a **moving boundary that has lost ~3.5 months of reach in 3 calendar
  days**. That rate is not smooth-sliding-window behaviour and I do not claim to
  explain it; it is reported as measured. Any lane that wants 2021 or 2022
  CAISO prices should treat the archive as actively perishing and fetch first.

## 7 — What this session changed

* `data/raw/lmp-data/CAISO/README.md` — appended a dated correction recording
  the re-measured boundary (the file's own established pattern; the prior
  "CORRECTION 2026-09-06" block sits above it). No source bytes touched.
* `scripts/data/fetch_caiso_oasis_grp.py` — docstring correction only, same
  measurement. No behaviour change; the script never hardcoded the date.
* This document.

**Nothing was written under `frontend/data/backcast/`, nothing was registered,
no bundle was produced, no LP was solved, and no builder's `YEARS` or guard
table was extended** — extending `derive_caiso_supply_consistent_demand.py`'s
`YEARS` to a year whose bench part does not exist would leave the script unable
to run at all on `main`, since it rewrites every listed year on any invocation.

## 8 — What a follow-on lane needs, in order

1. **Owner ruling on 2020** (§4). If 2020 proceeds, it needs a NetGen
   reconciliation the current construction does not have; and it can carry no
   price actual regardless (§6). Recommendation: **drop 2020, take 2021 only.**
2. **CARB 2020/2021 allowance prices** (§1) — 8 quarterly auction settlements
   transcribed to `carbon-auction-results.csv` and meaned into
   `STATE_CARBON_PRICE_BY_ISO["CAISO"]`, exactly as caiso-262's S-1 did for
   2022. `ww2.arb.ca.gov` blocks automated fetches, so this is transcription
   from named CARB sources, never inference. Without it a 2020/2021 CAISO solve
   prices CARB allowances at **$0/t** — ~$11–12/MWh on a CC, and merit-order
   distorting.
3. **Nuclear**: `derive_nuclear_monthly_cf.py` then
   `derive_nuclear_availability.py` for the target years — inputs present.
4. **Accept that 2021's C3c/price scoring is ~2/3-year at best** (§6), and say
   so on the rung rather than scoring a partial year as a whole one.
5. **Then, and only then, the bench-scaffold solve** (§3) under caiso-262
   §5.1's scaffold discipline, followed by the demand derive and the rung.

Steps 1–4 are all zero-LP and none of them were in this card's stated scope.
**Step 2 is now DONE and step 3 is half done — see §9.**

## 9 — What this session delivered beyond the census

The card's two targets are blocked (§0). These are the in-scope, zero-LP intake
items the census exposed, taken as far as this lane's scope allows.

### 9.1 CARB 2020/2021 allowance prices — LANDED

Eight rows added to `data/raw/policy/carbon-auction-results/carbon-auction-results.csv`,
each **transcribed** from the primary joint publication (the CARB + MELCC
*Summary Results Report* for that auction, Current Auction settlement price in
USD, read directly from the report PDF):

| auction | held | $/tonne | | auction | held | $/tonne |
|---|---|---|---|---|---|---|
| #22 | 2020-02-19 | 17.87 | | #26 | 2021-02-17 | 17.80 |
| #23 | 2020-05-20 | 16.68 | | #27 | 2021-05-19 | 18.80 |
| #24 | 2020-08-18 | 16.68 | | #28 | 2021-08-18 | 23.30 |
| #25 | 2020-11-17 | 16.93 | | #29 | 2021-11-17 | 28.26 |

`ww2.arb.ca.gov` still blocks automated fetches exactly as the corpus README
documents. The reports were reached instead through Québec's
`environnement.gouv.qc.ca` — the joint programme's **co-publisher**, not a
secondary reporter — and each row's `source_page` is the PDF actually read.
This is stronger attribution than the committed 2022–2025 rows, which cite a
CARB press release cross-checked against secondary commentary.
`allowances_sold` / `allowances_offered` are left blank: the volume tables do
not extract reliably across these report vintages, and 12 of the 14 committed
CARB rows already leave them blank. **No number is inferred.**

Applying the committed annual-mean recipe gives the CAISO anchors
**2020: 17.04** and **2021: 22.04** $/tonne. **Not installed** —
`STATE_CARBON_PRICE_BY_ISO` lives in `src/market_sim/config/`, outside this
lane. What makes the two means trustworthy is that the same recipe over the
existing rows reproduces the committed anchors exactly: 2022 `28.4500` → 28.45,
2023 `33.0275` → 33.03, 2024 `35.2325` → 35.23.

Validation: the curate script writes 54 schema-valid rows;
`tests/curation/test_curate_carbon_auction_results.py` 5 passed.

### 9.2 Nuclear — anchors derived, availability still gated

`derive_nuclear_monthly_cf.py --isos CAISO --years 2020 2021` runs cleanly and
**prints only** (it writes no file). Its output, from EIA-923 already on disk:

```
"CAISO": {
    2020: [1.00, 0.95, 1.00, 1.00, 0.96, 1.00, 0.77, 0.96, 0.99, 0.26, 0.49, 0.51],
    2021: [0.77, 0.53, 0.50, 0.57, 1.00, 1.00, 1.00, 1.00, 1.00, 0.72, 0.90, 1.00],
},
```

(The autumn-2020 and spring-2021 troughs are Diablo Canyon refuelling outages.)

`derive_nuclear_availability.py --iso CAISO --years 2020 2021` then refuses the
years: *"NO NUCLEAR_MONTHLY_CF_BY_YEAR[CAISO] anchor — rows would be RAW-ONLY
(unreconciled), a recipe asymmetry vs the anchored years; drop the year or land
the anchor first."* The anchor is a `src/market_sim/config/` table, so landing
it is not this lane's call. Both artifacts are left untouched.

> **TRAP for whoever finishes this.** `derive_nuclear_availability.py`
> **REPLACES** `data/raw/nuclear-availability-CAISO.csv` with exactly the years
> passed to `--years`. Run here with `--years 2020 2021` it dropped both years
> (no anchor) and still rewrote the file down to **1,462 rows / 2 reactors**,
> destroying the committed 2022–2025 extract (2,616 rows). This session caught
> it with a sha256 snapshot and restored the file byte-identically
> (`e375b448f7ec…`), and the CSV is unmodified in this branch. **Always pass the
> full year span**, and snapshot before running.

### 9.3 CAISO 2021 RTM prices — the perishing 50 days

The census found **50 RTM trade days (2021-08-12 … 2021-09-30) that were
missing from the committed aggregate AND still fetchable** — and, per §6, are
days that will stop being fetchable as the boundary advances. Every missing
**DAM** day is already unreachable, so RTM is the whole of what could still be
saved. This session started that crawl
(`fetch_caiso_oasis_grp.py --market rtm --start 2021-08-12 --end 2021-09-30
--sleep 7`, ~195 s and 24 GroupZip requests per trade date, extract-and-discard
so peak disk stays ~200 MB).

**COMPLETED.** 50/50 fetched, **0 missing, 0 partial**, 8.756 GB transferred
over 9,734 s. Folded with `postprocess_oasis_downloads.py --stage-dir`:

| | before | after |
|---|---|---|
| rows | 45,130 | **57,130** (+12,000 = 50 d × 24 h × 10 nodes) |
| trade days (TH_SP15) | 188 | **238** (none lost) |
| finite hours / node | 4,513 | **5,713** |

Verified against a pre-fold snapshot: all 45,130 pre-existing rows survive with
values identical across `LMP`/`MCC`/`MCE`/`MCL`/`MGHG`, the 10-node set is
unchanged, every row is local-year 2021, and the header matches the 2022–2025
aggregates exactly. The diff's 75 deletions are re-sorted rows, not dropped
data. Pushed blob verified against local (`bb54e2f5da4e…`, 57,131 lines).

`fetch_caiso_intertie_lmp.py --from-grp-windows --years 2021` was run first per
this corpus's documented ordering trap; it reads **DAM** windows, found nothing
in an RTM-only crawl, and correctly wrote nothing — the intertie parquet is
untouched.

**This does NOT make 2021 a price basis.** `derive_actual_lmp.CAISO_MIN_HOURS`
is 6,500 and the DAM ceiling for 2021 is 5,976 obtainable hours, so 2021 still
cannot clear the guard without an explicit `CAISO_PARTIAL_YEARS` amendment —
not made here. What the backfill buys is that the RT side of a future 2021 rung
is 65 % covered instead of 51 %, and those 50 days are now safe from the
advancing boundary.

> **Side effect, caught and reverted.** `postprocess_oasis_downloads.py` globs
> *every* window CSV under the raw dirs, not only the ones this session
> fetched. It also folded and staged out **5 tracked
> `zone-specific-demand/CAISO/load_ALL_*.csv`** windows left by an earlier
> session (and rewrote two `CAISO_tac_load_hourly_*.csv` byte-identically).
> The 5 files were restored byte-identically and the commit touches one file
> only. A lane running this script should `git status` immediately afterwards.
