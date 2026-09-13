# FINDING — NWPP-11 (data), 2026-09-13

Lane NWPP-11 [OPUS], `DATA PROFILE: shared`, branch
`claude/nwpp-11-data-fetch-73uu4i`, base `4d9c3251` (contains the desk refresh
`5341b234` and `origin/main` pin `c93b0d27`). Charter: NWPP desk r#2 issuance,
`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-11, §6 rows 1-3, 6, 12.

---

## 0. REPORT FIRST

**Every one of {ID, OR, UT, WA} × {2023, 2024, 2025} landed** — all twelve, plus
all four 2026 Q1 partials, sixteen files, each schema-verified against a sibling
by the fetcher's own assertion.

**The 17-BA derive reconciled to ZERO** — all 17 balancing authorities × all 3
years, element-wise exact identity against the BALANCE source
(`mismatched_hours` 0, `unmatched_hours` 0) and a **0.000000 MWh** annual
residual on both the raw and the adjusted demand series. Hour grids complete at
8,760 / 8,784 / 8,760 per BA per year.

**One finding outranks both**, and it is not something to correct away:
**BPAT's EIA-930 energy identity `D = NG − TI` is broken by ~4 GW continuously
from 2023-01 to 2025-05 and closes to exactly 0 MW from 2025-06 onward.** Over
2023-2025 that is a **+84.27 TWh** residual at BPAT against ≤ 0.36 TWh at every
other BA. EIA's own `(Adjusted)` family does **not** close it. §4.3.

---

## 1. Got / blocked

| # | Item | Route | Result |
|---|---|---|---|
| 1 | CAMPD CEMS ID/OR/UT/WA 2023-2026 | `fetch_campd_unit_level.py`, unmodified | **GOT** — 16 files, schema == sibling |
| 1b | CAMPD CEMS **CO** | — | **SKIPPED BY DESIGN**, documented §2.3. No URL requested, nothing blocked |
| 2 | 17 per-BA hourly extracts | **DERIVE** from committed BALANCE; no network | **GOT** — 17 files, reconciled to zero |
| 3 | Per-counterparty DIBA interchange × 17 BAs | `fetch_eia930_interchange.py --source bulk` (key-free) | **GOT** — 17 files, 2,278,882 rows |
| 4 | EIA-923 monthly hydro, footprint | committed extract + EIA-860 join | **GOT for 2023-2024**; **2025 is a source-side early release**, §5.2 |
| 5 | BPA `baltwg.txt` | `transmission.bpa.gov` | **GOT** (HTTP 200, 79,728 B) — but it is a **rolling 7-day window**, §6.1 |

### Blocked, with exact URL and status

| URL | Status | Consequence |
|---|---|---|
| `https://transmission.bpa.gov/business/operations/wind/WindGenTotalLoadYTD_2023.xls` | **404** | no BPA historical archive found on this path |
| `…/WindGenTotalLoadYTD_2024.xls` | **404** | same |
| `…/WindGenTotalLoadYTD_2025.xls` | **404** | same |
| `…/operations/Wind/WindGenTotalLoadYTD_2023.xls` (capitalised) | **404** | same |
| `…/operations/wind/BPA_Wind_Data_2023.xls` | **404** | same |
| `https://www.eia.gov/electricity/data/eia923/xls/f923_2025.zip` | **301** (unresolved) | superseded by the `archive/` path below, which served 200 |

Four of the five BPA URLs are **path guesses of mine**, not paths the charter or
the plan named; they are listed so the next lane does not repeat them. **No
value anywhere in this FINDING is transcribed from memory or taken from a
secondary source.** Item (5) therefore **STOPS** at the reconciliation the
rolling feed can support (§6.2) and routes the archive question to the desk
(§7 R-1).

### Not a block — a documented-equivalent substitution

`EIA_API_KEY` is **unset** in this container and no `.env` carries one (plan
§2.4, re-measured). The interchange fetch therefore used
`fetch_eia930_interchange.py --source bulk` — EIA's Hourly Electric Grid Monitor
six-month CSVs, **no registration, no key** — which `neiso-93` (2026-08-14)
verified equivalent to the `api` route over the committed 2023-2025 ISNE span.
Recorded in `data/raw/eia-930-interchange/SOURCES-NWPP.md`. The **load spine
needed no key at all**: it is a derive from committed bytes (plan §2.5).

---

## 2. Item (1) — CAMPD hourly CEMS, ID / OR / UT / WA

`scripts/data/fetch_campd_unit_level.py`, no edits:

    --year <2023|2024|2025> --states ID OR UT WA
    --year 2026 --quarters 1 --states ID OR UT WA --holdout-intake NWPP

The charter warned each state-year CSV was ~187 MB and told me to plan the
disk. **Measured, they are far smaller** — these are small-fleet states and the
whole four-state 2023 pass completed in under 20 s. The driver deleted the CSV
cache between years anyway; peak disk use never exceeded 1.8 GB against a 16 GB
allowance.

### 2.1 Per-file census (and the schema check)

Every file passed the fetcher's own `_verify_against_sibling`: arrow schema
equal to a sibling and every row inside its own year. The first ID file was
checked against `WY_2026.parquet`, each later file against that state's own
prior year.

| file | rows | facilities | units | span |
|---|---:|---:|---:|---|
| `ID_2023.parquet` | 70,080 | 5 | 8 | 2023-01-01 .. 2023-12-31 |
| `ID_2024.parquet` | 70,272 | 5 | 8 | 2024-01-01 .. 2024-12-31 |
| `ID_2025.parquet` | 70,080 | 5 | 8 | 2025-01-01 .. 2025-12-31 |
| `ID_2026.parquet` | 17,280 | 5 | 8 | 2026-01-01 .. 2026-03-31 |
| `OR_2023.parquet` | 122,640 | 7 | 14 | 2023-01-01 .. 2023-12-31 |
| `OR_2024.parquet` | 122,976 | 7 | 14 | 2024-01-01 .. 2024-12-31 |
| `OR_2025.parquet` | 122,640 | 7 | 14 | 2025-01-01 .. 2025-12-31 |
| `OR_2026.parquet` | 30,240 | 7 | 14 | 2026-01-01 .. 2026-03-31 |
| `UT_2023.parquet` | 254,040 | 11 | 29 | 2023-01-01 .. 2023-12-31 |
| `UT_2024.parquet` | 254,736 | 11 | 29 | 2024-01-01 .. 2024-12-31 |
| `UT_2025.parquet` | 260,664 | 11 | **31** | 2025-01-01 .. 2025-12-31 |
| `UT_2026.parquet` | 66,960 | 11 | 31 | 2026-01-01 .. 2026-03-31 |
| `WA_2023.parquet` | 148,920 | 11 | 17 | 2023-01-01 .. 2023-12-31 |
| `WA_2024.parquet` | 149,328 | 11 | 17 | 2024-01-01 .. 2024-12-31 |
| `WA_2025.parquet` | 148,920 | 11 | 17 | 2025-01-01 .. 2025-12-31 |
| `WA_2026.parquet` | 36,720 | 11 | 17 | 2026-01-01 .. 2026-03-31 |

### 2.2 The one non-rectangle, and it is real

Fifteen of sixteen files are exact `units × hours` rectangles. **`UT_2025` is
not**: Intermountain (EIA 6481) units `3SGA` (4,416 h, H2 only) and `4SGA`
(2,208 h, Q4 only) enter mid-year — the IPP Renewed repowering. The unit count
steps 29 → 31 between 2024 and 2025 and holds at 31 into 2026. A commissioning
event carried unmodified, not a gap.

### 2.3 CO is skipped, and the skip is documented

Colorado enters the footprint through a single **7.5 MW solar row in PACE**
(plan §2.1 by-state table, card N8). There is no CO combustion unit for CEMS to
observe, so a CO extract would land rows this program can never use. **No CO URL
was requested and nothing returned an error** — this is a scoping decision, not
a block.

### 2.4 Said at the gate, per card N8

CEMS observes **combustion units only**. This fleet is 36.3 % conventional hydro
+ 24.9 % wind/solar + 1.2 % nuclear by nameplate, so **CAMPD reaches at most
~32 % of it** — materially less than in ERCOT or SPP. The per-plant binning path
(`use_campd_bins`) and the outage/tranche artifacts it feeds therefore cover
correspondingly less of this ISO. **Scoping fact for NWPP-30, not a reason to
skip the fetch.**

### 2.5 SHA256SUMS

**No rows added**, on the SOCO-11 precedent immediately above it in the README:
that file's declared scope is the 35 gitignored `<ST>_2018.parquet` extracts
only, and tracked files carry git's own blob hashes as their integrity record.

---

## 3. Item (2) — the 17-BA derive, and the trap inside it

**This is a DERIVE, not a fetch, and that is the point** (plan §2.5/§6 row 2).
All 17 NWPP BAs are already in `data/raw/eia-930/EIA930_BALANCE_<yr>_<half>
.parquet`. No `EIA_API_KEY`, no network call.

New `scripts/data/build_nwpp_ba_hourly_from_balance.py` is the **create**
counterpart of `extend_eia930_hourly_from_balance.py`'s **extend**: the latter
reads an existing extract to learn the target column layout and so cannot open a
BA that has none. Every value mapping is **imported from it and reused verbatim**
(rule 23 `[R-FROZEN-DERIVE]`); the new module adds only the create path, the
taxonomy split, and the `(Adjusted)` columns.

### 3.1 THE TAXONOMY TRAP — the one thing that would have silently ruined this

`build_new_rows` detects EIA's mid-2024 taxonomy revamp with
`any("Excluding Pumped Storage" in c for c in raw.columns)` over the
**concatenated** frame. Its existing callers pass a single all-legacy span, so
this has never bitten. Pass a span that crosses the switch and **every legacy
row reads as new-taxonomy and returns NaN for hydro, coal, solar and wind.**

Measured on the first attempt: **BPAT 2023-01-01 01:00 local came back with
`NG: WAT` = NaN where the source carries 5,324 MW** — on the most hydro-heavy BA
in the country. `NG: NG` and `NG: NUC` survived (their column names are
identical in both taxonomies), so the file would have looked plausible.

The create script calls `build_new_rows` **once per `(year, half)`** and
concatenates. Era boundary **detected from each file's own schema, never
assumed**:

| file | columns | taxonomy |
|---|---:|---|
| `EIA930_BALANCE_2023_Jan_Jun` | 44 | legacy |
| `EIA930_BALANCE_2023_Jul_Dec` | 44 | legacy |
| `EIA930_BALANCE_2024_Jan_Jun` | 44 | legacy |
| `EIA930_BALANCE_2024_Jul_Dec` | 65 | **new** |
| `EIA930_BALANCE_2025_Jan_Jun` | 65 | new |
| `EIA930_BALANCE_2025_Jul_Dec` | 65 | new |
| `EIA930_BALANCE_2026_Jan_Jun` | 65 | new |

### 3.2 The reconciliation gate — all 51 BA-years at exactly zero

The derive selects, renames and narrows to the sibling schema's float32; it
never transforms a value. So the gate is **element-wise exact identity**: every
derived cell equals `float32(source cell)` or both are NaN.

A first version gated on the annual MWh sum alone and **fired** — BPAT 2023
residual −1.0 MWh on 57.66 TWh. That was float32 accumulation in the sum
(~3 × 10⁻⁸ relative), not a data defect, and the fix was to make the check
*stronger* rather than to loosen the tolerance: compare element-wise, and take
both annual sums over the same float32 values so a passing element-wise check
forces a residual of exactly 0.0.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| BAs passing `mismatched_hours == 0` | **17 / 17** | **17 / 17** | **17 / 17** |
| BAs passing `unmatched_hours == 0` | **17 / 17** | **17 / 17** | **17 / 17** |
| Max \|annual demand residual\| (MWh) | **0.000000** | **0.000000** | **0.000000** |
| Rows per BA | 8,760 | 8,784 | 8,760 |

**Per-BA annual demand (TWh), raw column, with the raw and `(Adjusted)` peaks:**

| BA | 2023 | 2024 | 2025 | raw peak MW (worst yr) | adj peak MW |
|---|---:|---:|---:|---:|---:|
| BPAT | 57.664 | 59.072 | 61.109 | 11,537 | 11,537 |
| PACE | 50.799 | 52.770 | 53.605 | **65,826** (2023) | 8,941 |
| NEVP | 38.520 | 41.142 | 40.695 | **69,812** (2025) | 9,239 |
| PSEI | 24.901 | 24.886 | 24.865 | 5,293 | 5,293 |
| PGE | 22.493 | 22.701 | 23.499 | 4,504 | 4,504 |
| PACW | 20.956 | 21.283 | 20.248 | 4,195 | 4,195 |
| IPCO | 18.284 | 18.762 | 18.928 | 4,111 | 4,111 |
| AVA | 13.076 | 12.950 | 14.035 | **810,948** (2025) | 2,525 |
| NWMT | 11.944 | 12.180 | 11.976 | **100,285** (2025) | 2,147 |
| SCL | 9.529 | 9.429 | 9.420 | 2,027 | 2,027 |
| GCPD | 6.255 | 6.685 | 6.740 | 1,058 | 1,058 |
| TPWR | 4.796 | 4.557 | 4.540 | 984 | 984 |
| DOPD | 2.239 | 2.389 | 2.435 | 553 | 553 |
| CHPD | 1.976 | 1.974 | 1.983 | 583 | 583 |
| WAUW | 0.830 | 0.804 | 0.794 | 167 | 167 |
| AVRN | — | — | — | null in all hours | null |
| GRID | — | — | — | null in all hours | null |
| **footprint** | **284.26** | **291.58** | **294.87** | | |

Against the plan's §2.5 measurement (283.97 / 291.56 / 294.86 TWh): **+0.10 % /
+0.01 % / +0.00 %**. The 2023 gap is the plan's screen — my column is raw.

**The §2.5 defect inventory reproduces exactly**, independently: AVA 810,948 MW,
NWMT 100,285, NEVP ~69-70 GW, PACE 65,826. The `(Adjusted)` family screens every
one of them.

Non-null demand hours: **394,556** against the plan's 394,424 — a 132-hour
difference. Mine derives exactly: 15 load-carrying BAs × 26,304 hours = 394,560,
less 4 null hours (CHPD 2024 ×1, GCPD 2024 ×1, SCL 2024 ×2). **Routed, not
reconciled** — §7 R-2.

### 3.3 Both column families are carried, and I did not choose

**NWPP-10's defect convention has NOT landed at this pin** — no
`docs/multi-iso/nwpp-data-audit.md`, no remote branch matching `nwpp`. Per the
charter, both families are produced.

The 17 columns are byte-identical in name, order and arrow type to
`SWPP hourly.parquet` (asserted at write time by `verify_schema`), plus three
**appended** columns: `Demand (Adjusted)`, `Net generation (Adjusted)`,
`Total interchange (Adjusted)`.

All three region series, not demand alone, **because the `D = NG − TI` triple
must stay internally consistent whichever family is selected** — mixing adjusted
demand with raw net generation would break it by construction. Choosing between
them remains NWPP-10's.

One property worth stating: **the `(Adjusted)` family is imputed as well as
screened, so it can be LARGER than raw** (SCL 2025: 9.476 vs 9.420 TWh; NWMT
2023: 11.946 vs 11.944). It is not "raw minus outliers".

### 3.4 No `NG: GEO` column — measured, then decided by the existing convention

The siblings' layout has none; the legacy taxonomy does not break geothermal out
at all; adding the column would make the same energy jump from `NG: OTH` to
`NG: GEO` at the 2024 H2 boundary. Folding it into `NG: OTH` in both eras is
`extend_eia930_hourly_from_balance`'s own `_NEW_OPTIONAL_MAP` convention, applied
unchanged. **Measured magnitude: IPCO only, 240,452 MWh over 2024H2-2025; every
other NWPP BA reports zero** — including NEVP, which is worth a second look by
whoever owns the Nevada fleet crosswalk.

### 3.5 The 17 additive `BA_TIMEZONE` keys (collision C-5)

Appended **after** SOCO's key, which is untouched. +32 lines, 0 deletions.

**MEASURED off the BALANCE bytes' own UTC-minus-local offsets**, never inferred
from geography — the same identification SOCO's key is built on:

* **14 BAs at 7 h / 8 h** (8,712 / 4,465 rows across the three new-taxonomy
  halves) → `America/Los_Angeles`: BPAT PACW PGE PSEI AVA IPCO CHPD DOPD GCPD
  SCL TPWR AVRN GRID **NEVP**.
* **3 BAs at 6 h / 7 h** → `America/Denver`: **PACE** (PacifiCorp *East* —
  Utah/Wyoming/Idaho), **NWMT** (NorthWestern Montana), **WAUW** (WAPA Upper
  Great Plains West).

Both groups switch on the **US DST dates** — the 2025 spring-forward measured at
local `2025-03-09 03:00` in every one — so neither is a no-DST zone:
`America/Denver`, never `America/Phoenix`. **NEVP is Pacific despite the
Mountain-state name**; Las Vegas is Pacific and the offsets say so.

The derive itself does **not** depend on these keys (BALANCE carries
`Local Time at End of Hour` directly), and neither does the keyless interchange
route. They are for the `api` paths.

---

## 4. Item (3) — per-counterparty interchange, and the finding that matters

17 files, **2,278,882 rows**, 30 distinct counterparties, 13 of them outside the
footprint.

**SIGN CONVENTION, stated because every reading below depends on it:
`mw > 0` means the named BA EXPORTS to the DIBA.** EIA's own `TI` convention,
inherited unchanged.

### 4.1 External net position by counterparty (TWh, + = footprint exports)

| DIBA | 2023 | 2024 | 2025 | what it is |
|---|---:|---:|---:|---|
| **CISO** | **+8.691** | **+11.388** | **+12.504** | CAISO — largest external counterparty, growing |
| BCHA | +9.476 | +7.567 | +2.772 | BC Hydro — **collapsing** |
| WACM | −6.766 | −4.997 | −2.707 | WAPA Colorado-Missouri — largest net import source |
| SRP | +4.400 | +3.835 | +4.364 | Salt River Project |
| LDWP | −2.204 | −3.830 | −0.459 | LA Dept of Water & Power |
| PNM | +2.074 | +2.179 | +2.002 | |
| BANC | +1.156 | +2.069 | +2.760 | Balancing Authority of Northern California |
| AZPS | −1.192 | −0.980 | +0.206 | |
| WALC | −2.497 | +0.960 | +1.183 | |
| WWA / GWA / SWPP / AESO | −1.687 | −1.159 | −1.383 | four small legs, netted |
| **TOTAL** | **+12.449** | **+17.033** | **+21.241** | |

### 4.2 CAISO-facing — card N4's magnitude

**CAISO proper is `CISO`.** `LDWP`, `BANC`, `IID` and `TIDC` are California BAs
but are **not** CAISO, and lumping them together hides a sign flip, so they are
reported separately.

**`CISO` net: +8.691 / +11.388 / +12.504 TWh**, and the seam is overwhelmingly
one-directional — the footprint exports in **7,510 / 7,936 / 8,041 of ~8,760
hours (86 % / 90 % / 92 %)**.

**Duration curve of the summed CISO seam (MW, + = NWPP exports):**

| year | p0 (max export) | p5 | p25 | p50 | p75 | p95 | p100 (max import) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | +5,957 | +2,444 | +1,620 | +1,020 | +393 | −618 | −1,737 |
| 2024 | +5,380 | +2,709 | +1,913 | +1,389 | +703 | −314 | −1,424 |
| 2025 | +6,578 | +2,937 | +2,074 | +1,513 | +778 | −231 | −1,482 |

**Per-leg (TWh):**

| leg | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| NEVP → CISO | +7.558 | +9.184 | +9.453 |
| BPAT → CISO | +1.141 | +2.194 | +3.026 |
| PACW → CISO | −0.008 | +0.009 | +0.025 |
| BPAT → LDWP | +6.139 | +5.643 | +6.188 |
| **NEVP → LDWP** | **−8.663** | **−9.340** | **−7.501** |
| BPAT → BANC | +1.156 | +2.069 | +2.760 |
| PACE → LDWP | +0.320 | −0.132 | +0.853 |

NEVP is simultaneously the largest *exporter* to CAISO and the largest
*importer* from LADWP, at similar magnitude. Any N4 object that nets "NEVP vs
California" to one number destroys that structure.

### 4.3 THE FOOTPRINT NET POSITION DOES NOT CLOSE — and the divergence is the finding

Three estimates of the same quantity (TWh, + = net export):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `Σ NG − Σ D` (from the 17 derived extracts) | **−6.686** | **−3.128** | **+5.194** |
| `Σ Total interchange` | **+28.737** | **+32.709** | **+18.231** |
| external DIBA sum | **+12.449** | **+17.033** | **+21.241** |

They disagree by 16-20 TWh, and **essentially all of it is one BA.** Per-BA
identity residual `D − (NG − TI)` over 2023-2025:

| BA | residual, raw (TWh) | residual, `(Adjusted)` (TWh) |
|---|---:|---:|
| **BPAT** | **+84.271** | **+84.284** |
| NEVP | −0.125 | −0.364 |
| GCPD | +0.109 | +0.109 |
| PGE | +0.036 | +0.036 |
| IPCO | +0.016 | +0.016 |
| every other BA (12) | \|·\| ≤ 0.003 | \|·\| ≤ 0.002 |

**EIA's `(Adjusted)` family does NOT close it** — the two columns agree to
~0.01 TWh on an 84 TWh residual. So NWPP-10's column ruling, whichever way it
goes, does not touch this.

**And the residual has a date.** BPAT monthly mean residual, MW:

| 2023-01 | … | 2025-03 | 2025-04 | 2025-05 | **2025-06** | 2025-07 | … | 2025-12 |
|---:|---|---:|---:|---:|---:|---:|---|---:|
| 4,436 | 2,546-4,729 | 3,504 | 2,782 | 2,791 | **0** | **0** | 0 | **0** |

It does not decay — it steps from 2,791 MW in May 2025 to **exactly 0 MW in June
2025** and stays at 0 in every subsequent month. That is a **discrete reporting
change at BPAT effective 2025-06**, not a drift.

BPA's own feed header names the mechanism (§6.2, quoted verbatim): its BA
"includes some that are not BPA's" and excludes "loads served by transfer,
scheduled out of region, or scheduled to customers with their own BAs such as
Seattle and Tacoma" — i.e. BPAT wheels, and pre-2025-06 its `Total Interchange`
carried flow its `Demand` and `Net Generation` did not.

**Consequences, stated rather than corrected away:**

1. This footprint's net position **cannot** be computed as `Σ NG − Σ D`, nor as
   `Σ TI`; the external-DIBA sum still contains BPAT's through-flow.
2. The 2023 → 2025 growth in external net exports (+12.4 → +21.2 TWh) is
   **partly an artifact of the 2025-06 convention change**, not purely a real
   trend. Anyone quoting it as a trend is quoting two bases.
3. Internal DIBA legs should be exact negatives and are not: total internal
   asymmetry **+16.318 / +15.700 / −3.966 TWh** (2023/24/25). **Every material
   asymmetric pair involves BPAT** — worst `BPAT↔GRID` +7.092 TWh (2024),
   `AVRN↔BPAT` +3.762, `BPAT↔SCL` +3.023. The 2025 sign flip is the same
   convention change (`BPAT↔PGE` −4.562, `BPAT↔PSEI` −3.060 in 2025 against
   ≈ 0 in 2023-2024). **Zero of the 34 pairs is one-sided** — both BAs always
   report; they disagree.

### 4.4 A second, separate source conflict: GRID

`GRID`'s EIA-930 net generation is **16.790 / 18.632 / 17.707 TWh**. Its EIA-860
operable fleet in the plan's §2.1 census is **689.4 MW**, whose maximum possible
annual output is 6.04-6.06 TWh. **Implied capacity factor 2.78 / 3.08 / 2.93 —
i.e. 278-308 %, physically impossible.**

So either the 860 `Balancing Authority Code` attribution materially understates
what GRID balances, or GRID's 930 net generation includes resources it balances
for others. ~11-13 TWh/yr is unattributed either way. **`AVRN` by contrast is
consistent** — 7.757 / 9.137 / 8.426 TWh on 2,848.7 MW, CF 0.31-0.37, exactly
right for a wind/solar BA.

This bears directly on **card N5**'s open question of where AVRN and GRID
generation lands. Routed, §7 R-3.

---

## 5. Item (4) — EIA-923 monthly hydro

`data/raw/nwpp-hydro/`, 7,212 plant-months. Pure extract: a filter, a reshape,
one EIA-860 nameplate join. Population `prime_mover == "HY"` (fuel `WAT`) in the
17 BAs; pumped storage excluded by design, matching `load_hydro_budget`'s own
population (the footprint's single PS plant is 314.0 MW, BPAT).

### 5.1 Footprint monthly total (GWh)

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **year** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 9,695 | 8,291 | 7,788 | 7,280 | **14,745** | 10,069 | 9,316 | 8,986 | 6,574 | 6,678 | 8,408 | 9,098 | **106.928 TWh** |
| 2024 | 9,133 | 8,173 | 9,398 | 8,765 | 10,476 | 10,872 | 10,300 | 8,965 | 6,696 | 6,645 | 8,618 | 9,860 | **107.900 TWh** |
| 2025 | 7,097 | 5,545 | 6,709 | 7,053 | 6,875 | 6,300 | 5,447 | 5,817 | 4,192 | 5,047 | 5,827 | 9,029 | **74.936 TWh** |

Real hydrology, not noise: the **May-2023 freshet** peaks at 14,745 GWh against
10,476 in May 2024, and September is the trough in every year.

### 5.2 THE 2025 TRAP — and why the raw year-over-year number is wrong

| year | plants | net generation | 860 nameplate joined |
|---|---:|---:|---:|
| 2023 | 290 | 106.928 TWh | 35,719.5 MW |
| 2024 | 286 | 107.900 TWh | 35,707.5 MW |
| **2025** | **25** | 74.936 TWh | 24,515.6 MW |

**2025 is an EIA-923 EARLY RELEASE carrying only the monthly-survey reporters** —
25 of ~290 footprint hydro plants, 139 of 1,391 nationally, 3,427 of 13,210
plants across all fuels. `EIA923_LATEST_FINAL_VINTAGE` is 2024 at this pin.

**Verified, not assumed, to be the newest 2025 vintage that exists.** I fetched
EIA's own `https://www.eia.gov/electricity/data/eia923/archive/xls/f923_2025.zip`
(HTTP 200, 19,708,197 B → `EIA923_Schedules_2_3_4_5_M_12_2025_20FEB2026.xlsx`)
and counted it: **identical** 7,653 rows / 3,427 plants / 139 national HY plants
/ **25 footprint HY plants**. So this is a **source** state, not a repo gap, and
it is the same one `load_hydro_budget`'s `backfill_year` and
`monthly_target_mwh` arguments already document for CAISO and NEISO 2025.
**Nothing is filled.** The choice among backfill, repin and wait is NWPP-32's.

**The 25-plant panel is not a random sample and must not be read as one.** It is
a **strict subset of both complete years**, covers **68.6 % of nameplate and
66.0 % of 2023 energy**, and contains **all eight ≥ 1 GW plants** (Grand Coulee,
Chief Joseph, John Day, The Dalles, Rocky Reach, Wanapum, Bonneville, Boundary).
The largest absentee is McNary, 990.5 MW.

So a like-for-like comparison is available, and it is the only honest one:

| on the same 25 plants | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| net generation (TWh) | 70.620 | 69.738 | **74.936** |
| vs 2023 | — | −1.2 % | **+6.1 %** |
| vs 2024 | — | — | **+7.5 %** |

**2025 was a WETTER year on the large plants than either 2023 or 2024.**
Comparing the raw annual totals (74.9 vs 107.9 TWh) would read as a **31 %
drought** and would be **wrong**. That trap is why the panel comparison is
computed and committed rather than left to the next lane.

### 5.3 Flags — reported, never filled

`nwpp_hydro_monthly_923_flags.csv`, one row per plant-year:

| flag | 2023 | 2024 | magnitude (2023) |
|---|---:|---:|---|
| `missing_months` | **0** | **0** | series are complete wherever a plant reports |
| `all_zero` | 7 | 3 | 34.1 MW — 0.10 % of nameplate, 0.00 % of energy |
| `cf_over_1` | 31 | 31 | 757.9 MW — 2.12 % of nameplate, 3.83 % of energy |
| `negative_months` | 41 | 30 | 811.9 MW — 2.27 % of nameplate, 1.60 % of energy |

* **`cf_over_1`** — monthly energy exceeding 860 nameplate × hours, so the two
  records disagree. Worst: **Nooksack Hydro** (PSEI, 860 nameplate 1.5 MW, max
  monthly CF **1.78**), Wanship (PACE, 1.9 MW, 1.29), Ryan (NWMT, 55.2 MW,
  1.26), Arrowrock (IPCO, 15.0 MW, 1.24), Long Lake (AVA, 70.0 MW, 1.20).
  Concentrated in small plants, so the likely cause is a **stale or partial 860
  nameplate**, not inflated 923 energy. It bears on NWPP-32's MW envelope under
  rule 14 `[R-ACCURATE]`, which is why it is surfaced rather than clipped.
* **`negative_months`** — physically real where station service exceeds output.
  Four plants report negative in **all twelve** months of a year: Prospect 3
  (−174 MWh), Prospect 4 (−60), Weber (−185), Hydro III (−70). All tiny.
* **`all_zero`** — largest is **Electron** (PSEI, 22.8 MW) at zero across both
  2023 and 2024, consistent with a multi-year outage. **`Port Townsend Paper`**
  (BPAT) carries a 923 hydro row with **no EIA-860 hydro nameplate at all**.

### 5.4 Restated so it is not rediscovered in W4 (plan §2.7, card N3)

This artifact is twelve monthly totals per plant. It cannot express hydraulic
coupling down a river — and **eight of the footprint's ten largest hydro plants
are one Columbia-mainstem chain** — nor sub-monthly reservoir carryover and
refill, nor flood-control / fish-spill obligations. Those are NWPP-32's and
NWPP-36's problem. This extract is what they will be built on.

---

## 6. Item (5) — the BPA cross-check

### 6.1 The feed landed, and it cannot do the job the charter asked of it

`https://transmission.bpa.gov/Business/Operations/Wind/baltwg.txt` — **HTTP 200,
79,728 bytes, 2,028 lines**, fetched 2026-09-13. Columns `Date/Time, Load, VER,
Hydro, Fossil/Biomass, Nuclear` at **5-minute** resolution.

**It is a rolling 7-day window**: `2026-09-07 00:00 .. 2026-09-13 00:40`
Pacific, 1,736 populated rows. The committed BALANCE archive ends **2026-06**,
and item (2)'s extracts cover **2023-2025**. **There is zero period overlap**, so
the hour-by-hour reconciliation the charter specified is **not possible from
this feed**, today or on any future day.

My five guesses at a historical-archive path all returned **404** (§1). **Item
(5) STOPS there** per the charter — no transcription from memory, no
secondary-source values. The archive question is routed (§7 R-1).

### 6.2 What the feed DOES settle — two things, and both matter

**(a) Its header is the documentary evidence for §4.3.** Quoted verbatim from
the fetched bytes, lines 6-8:

> This represents loads and resources in BPA's Balancing Authority (BA)
> including some that are not BPA's.
> It does not include BPA loads served by transfer, scheduled out of region,
> or scheduled to customers with their own BAs such as Seattle and Tacoma

Seattle (`SCL`) and Tacoma (`TPWR`) are separate EIA-930 BAs **inside this
footprint**. So BPA's own publication states that its BA boundary and its
load definition do not line up the way a single `D = NG − TI` identity assumes.

**(b) A level cross-check IS possible on the same calendar week**, comparing the
BPA feed's Sep 7-13 2026 means against BPAT's EIA-930 Sep 7-13 means in each
derived year. **This is explicitly NOT like-for-like** — different years — and is
reported as a structural plausibility check only:

| | BPA feed (Sep 7-13, 2026) | BPAT 930 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|
| Load | 6,521 MW | 5,834 (−10.5 %) | 6,139 (−5.9 %) | 6,335 (−2.9 %) |
| Hydro | 4,382 MW | 4,681 (+6.8 %) | 4,891 (+11.6 %) | 4,311 (−1.6 %) |
| **Nuclear** | **1,137 MW** | **1,140 (+0.3 %)** | **1,130 (−0.6 %)** | **1,137 (+0.0 %)** |
| VER / wind+solar | 810 MW | 785 | 1,180 | 817 |

**Nuclear matches to 0.0-0.6 %** — Columbia Generating Station, the footprint's
only nuclear unit, at 1,137 MW in both records. That is a hard anchor proving
the two feeds describe the same balancing authority. Load agrees within
−2.9 % to −10.5 %, trending closer year by year exactly as load growth implies.
Hydro agrees within normal inter-annual hydrology for a fixed calendar week.

**The divergence is entirely in interchange, and it corroborates §4.3
independently.** Over that same week:

| | BPAT `NG − D` | BPAT `Total interchange` |
|---|---:|---:|
| 2023 | 1,871 MW | **6,447 MW** |
| 2024 | 2,088 MW | **6,927 MW** |
| **2025** | **1,052 MW** | **1,052 MW** — identical |

and the BPA feed's own mean `generation − load` for that week is **839 MW** —
the order of the 2025 figure, not of the 2023/2024 one.

**This is a finding, not something corrected away.** No value in any committed
file was adjusted.

### 6.3 The snapshot is deliberately NOT committed

Plan §6 row 12 targets `data/raw/nwpp-planning/`, but §5 gives that directory to
**NWPP-12**, and it is not in this lane's `FILES YOU OWN`. Committing a
7-day rolling snapshot there would also commit an artifact that is stale
tomorrow and can never serve the stated purpose. Per collision rule 5 the lane
**STOPS and routes** (§7 R-1) rather than writing outside its region. Every
number above is reproducible from the URL in one command.

---

## 7. Routed to NWPP-DESK

| # | Item |
|---|---|
| **R-1** | **`data/raw/nwpp-planning/` ownership + the BPA archive.** Plan §6 row 12 assigns the BPA feed to NWPP-11 with a target directory §5 gives to NWPP-12 — a region overlap (collision rule 5). Nothing was written there. Separately: `baltwg.txt` is a **rolling 7-day window**, so it can never support the 2023-2025 reconciliation the charter asked for; five archive-path guesses 404'd (§1). If BPA historical data is wanted, the desk should name a route (BPA's own historical-data page, or the PUDL FERC-714 parquet §2.4 already probed at 200) and assign it. |
| **R-2** | **394,556 vs the plan's 394,424 non-null demand hours.** Mine derives exactly (15 load-carrying BAs × 26,304, less 4 measured nulls). Not reconciled — probably a different screen or year filter in §2.5. Worth one line in the plan so the two numbers stop competing. |
| **R-3** | **GRID's 860↔930 conflict (§4.4).** Implied CF 278-308 % against the §2.1 census. ~11-13 TWh/yr unattributed. This is card **N5** input (where AVRN/GRID generation lands) and should reach NWPP-10 before it finalises the fleet census. |
| **R-4** | **BPAT's 2025-06 reporting-convention change (§4.3).** The most consequential thing in this FINDING. It means the footprint's interchange record is on **two incompatible bases** inside the 2023-2025 window, which bears on N4 (seam magnitude), N5 (zone grouping and whether BPAT can be treated as one node) and anything NWPP-20 registers as an import object. It should be a **card**, not a lane detail. |
| **R-5** | **Two new scripts, not enumerated in §5.** `build_nwpp_ba_hourly_from_balance.py` (item 2 needed a *create* path; the existing script only *extends*, and the charter's "produce BOTH raw and Adjusted" required a column it cannot emit) and `build_nwpp_hydro_monthly.py` (item 4 has no existing script). Both are new files no other lane owns, both import the frozen mappings rather than restating them, and neither is a solve-affecting tunable (rules 21/24 untouched). Flagged for the record. |

---

## 8. Rules

* **13 `[R-MEASURED]` / 14 `[R-ACCURATE]`** — every number here is measured. Where
  a source is wrong (AVA 810,948 MW; GRID CF 3.08; Nooksack CF 1.78) or
  incomplete (923 2025), it is **reported at full magnitude and left alone**. No
  value is filled, screened, scaled or interpolated in any committed file.
* **23 `[R-FROZEN-DERIVE]`** — the 930 derive imports `extend_eia930_hourly_from_
  balance`'s mappings verbatim; the hydro extract applies no parameter at all.
* **26 `[R-DELETE]`** — nothing deprecated or zeroed.
* **27 `[R-PUSH]`** — four small-pack `git push` commits (14 MB / 48 MB / 18 MB /
  0.2 MB), each on a freshly-fetched base. The one file ≥ 300 lines
  (`build_nwpp_ba_hourly_from_balance.py`, 389) was **fetched back and verified
  byte-identical** (sha256 `1f4bdc24dcf1eaa1…`, 389 lines both sides); the
  shared `fetch_eia930_hourly.py` was verified too although it is 226 lines. No
  `push_files` for any parquet. The ruff pre-push gate fired once on formatting;
  both scripts were formatted and AST-verified unchanged, and the derive re-ran
  to the same zero residual afterwards.
* **28 `[R-MECH-MATRIX]`** — **no cell touched.** This lane adds no mechanism, no
  `ScenarioConfig` field and no calibration CLI flag; NWPP has no shard yet
  (NWPP-21 is held on collision C-2).
* **§8.0 collision rules** — no shared record edited. Not the plan, the ledger,
  `docs/calibration-log/nwpp.md`, `CHANGELOG.md`, any keeper/gates stamp, any
  matrix shard, `docs/multi-iso/nwpp-data-audit.md` (NWPP-10's), or any `soco*`
  file. **C-5 honoured**: SOCO's `BA_TIMEZONE` key is untouched and the 17 NWPP
  keys are appended after it. This FINDING is the lane's only new record.
* **No LP was run** (rule 32 `[R-SHARD]` — nothing in this lane requires one) and
  **no CI workflow was added**.

---

## Log entry

### nwpp-11 — 2026-09-13

Data lane. Landed the NWPP footprint's four missing CEMS states, derived its
17-BA load spine, fetched its per-counterparty interchange keylessly, and
extracted its monthly hydro. Five items, five commits, no shared record touched.

**CEMS (item 1).** ID/OR/UT/WA × 2023-2026, sixteen files, each schema-verified
against a sibling by `fetch_campd_unit_level.py`'s own assertion. Fifteen are
exact `units × hours` rectangles; `UT_2025` is not, because Intermountain
`3SGA`/`4SGA` enter mid-year (IPP Renewed) — a real commissioning event, carried
unmodified. CO skipped by design (one 7.5 MW solar row in PACE), documented, no
URL requested. Stated at the gate per card N8: CAMPD reaches ≤ ~32 % of this
fleet's nameplate, which scopes NWPP-30.

**The 930 derive (item 2).** All 17 BAs × 3 years reconcile to the source at
**element-wise exact identity** and a **0.000000 MWh** annual residual; hour
grids complete. Footprint demand 284.26 / 291.58 / 294.87 TWh, within 0.10 % of
§2.5. The trap worth knowing: `build_new_rows` detects EIA's mid-2024 taxonomy
over the *concatenated* frame, so one call spanning the switch NaNs every legacy
row's hydro, coal, solar and wind — measured at BPAT 2023-01-01 01:00, where a
real 5,324 MW `NG: WAT` arrived as NaN. The new create script calls it once per
`(year, half)`. NWPP-10's convention has not landed, so **both** the raw and
`(Adjusted)` region families are carried, complete and unchosen — all three
series, so the `D = NG − TI` triple stays consistent either way. The 17 additive
`BA_TIMEZONE` keys are **measured** off the BALANCE offsets: 14 Pacific, and
PACE/NWMT/WAUW Mountain, all on US DST dates. SOCO's key untouched (C-5).

**Interchange (item 3) — and the finding that outranks the rest.** 2.28 M rows,
key-free bulk route (no `EIA_API_KEY` in this container). CAISO-facing magnitude
for card N4: **CISO +8.69 / +11.39 / +12.50 TWh**, one-directional in 86-92 % of
hours, p50 +1.0 to +1.5 GW; the largest single leg is NEVP→CISO, and NEVP→LDWP
runs the *other* way at similar size, so a netted "California" number destroys
real structure. But the footprint's net position **does not close**: `Σ NG − Σ D`,
`Σ TI` and the external-DIBA sum disagree by 16-20 TWh, and **essentially all of
it is BPAT** — a `D − (NG − TI)` residual of **+84.27 TWh** over 2023-2025
against ≤ 0.36 TWh at every other BA. EIA's `(Adjusted)` family does not close
it. And it has a date: the monthly residual steps from **2,791 MW in 2025-05 to
exactly 0 MW in 2025-06** and stays there — a **discrete reporting-convention
change**, so the window's interchange record sits on two incompatible bases. The
2023→2025 growth in external net exports is therefore partly an artifact.
Routed as **R-4**, recommended as a card. Separately, **GRID** reports 16.8-18.6
TWh/yr against an §2.1 census of 689.4 MW — implied CF **278-308 %**, physically
impossible; AVRN is clean at CF 0.31-0.37. Routed as **R-3** for card N5.

**Hydro (item 4).** 7,212 plant-months. 2023 = 290 plants / 106.93 TWh, 2024 =
286 / 107.90. **2025 is an EIA-923 early release at 25 plants**, and I verified
against EIA's own `f923_2025.zip` that this is the newest 2025 vintage that
exists — a source state, not a repo gap; nothing filled. The panel is a strict
subset of both complete years covering **68.6 % of nameplate** and **all eight
≥ 1 GW plants**, so like-for-like **2025 runs +6.1 % vs 2023 and +7.5 % vs
2024 — a wetter year**. Reading the raw totals (74.9 vs 107.9 TWh) as a 31 %
drought would be wrong, which is why the panel comparison is committed. Flags:
zero missing months; `cf_over_1` 31 plant-years (2.1 % of nameplate, worst
Nooksack at CF 1.78 — most likely a stale 860 nameplate, relevant to NWPP-32's
MW envelope under rule 14); four tiny plants negative in all twelve months;
Electron zero across two years.

**BPA cross-check (item 5).** `baltwg.txt` fetched (HTTP 200), but it is a
**rolling 7-day window** with **zero overlap** to 2023-2025 or to BALANCE, so
the reconciliation as chartered is impossible from it; five archive-path guesses
404'd and the item **STOPPED** there. What it did settle: its header is the
documentary evidence for the BPAT finding (BPA's BA "includes some that are not
BPA's" and excludes load "scheduled to customers with their own BAs such as
Seattle and Tacoma" — both separate EIA-930 BAs inside this footprint), and a
same-calendar-week level check anchors hard on **nuclear, matching to 0.0-0.6 %**
(Columbia, 1,137 MW in both records) with load within −2.9 % to −10.5 %. The
divergence is entirely interchange, and in 2025 BPAT's `TI` and `NG − D` are
**identical** — corroborating R-4 from an independent publication.

Routed: R-1 `nwpp-planning/` ownership + a real BPA archive route; R-2 the
394,556 vs 394,424 hour count; R-3 GRID; R-4 the BPAT convention change (card);
R-5 two new scripts not enumerated in §5. No LP, no CI workflow, no matrix cell,
no shared record.
