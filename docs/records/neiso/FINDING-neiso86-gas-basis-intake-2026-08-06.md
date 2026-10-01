# FINDING — neiso-86: the NEISO hub-basis input is repaired for 2018–2022 and 2026

**Session:** neiso-86, 2026-08-06
**Type:** DATA INTAKE (rule 22 channel 1). **NO LP WAS BUILT. NO YEAR WAS SOLVED, SCORED OR REGISTERED.**
**Pre-registration:** `results/calibration/PREREG-neiso86-gas-basis-intake-2026-08-06.md`, committed
(`5b27332f`) **before** any data byte was edited.
**Keeper:** UNCHANGED (`2026-08-05-neiso-83-ca1-reclass`).
**Mechanism cells:** UNCHANGED. No mechanism tested, proposed or armed (rule 28(d)).
**New DOF:** ZERO.
**Gate outcome:** **V1 PASS · V2 PASS · V3 FAIL (gate premise falsified by control — reported, not reconciled) · V4 PASS · V5 PASS.**

---

## 0. Headline

NEISO's hub basis was sourced from the EIA `N3050MA3` LDC city-gate **purchase-portfolio average**
for 2015–2022 and 2026, which is **seasonally inverted** relative to the marginal Algonquin basis a
gas unit's offer tracks. It is now sourced, for the owner-authorized window, from the **measured
ISO-NE Massachusetts natural gas index** — the same series and the same provenance style already
committed for 2023–2025.

**Every authorized complete year flips from inverted to correct:**

| `winter(Jan,Feb,Dec) − summer(Jun,Jul,Aug)` | 2018 | 2019 | 2020 | 2021 | 2022 |
|---|---|---|---|---|---|
| **before** (EIA N3050MA3 proxy) | −4.79 | −6.71 | −7.18 | −8.56 | −7.84 |
| **after** (measured ISO-NE MA index) | **+2.85** | **+2.80** | **+1.32** | **+3.78** | **+11.56** |

against the correctly-sourced measured years 2023–2025 (+2.83 / +4.54 / +10.97). **Zero fitted
parameters, zero new degrees of freedom, no `ScenarioConfig` field, no mechanism.**

The 2022 January row moves from **+2.3545** (proxy) to **+15.7370** (measured $20.12/MMBtu index −
$4.383 Henry Hub). The August row moves from **+10.3931** to **−0.4357**. That is the inversion,
removed at its source.

---

## 1. Governance posture

- **The holdout spend freeze was respected in full.** `holdout-freeze.json` is ACTIVE. It freezes
  SOLVE / SCORE / REGISTRATION; it does not freeze data intake (its own `scope.not_frozen`, and rule
  22 channel 1). **No year was solved, scored or registered** — before or after the intake. No LP was
  constructed at any point in this session.
- **Owner authorization was requested first and logged**, naming the exact years, per rule 22
  channel 1. Authorized window: **NEISO 2018, 2019, 2020, 2021, 2022, 2026**. Recorded in
  `frontend/data/backcast/calibration-complete.json` → `intake_log`.
- **2019 is the SPENT locked-test year.** Its DATA is repaired under explicit owner authorization.
  **The one-shot is NOT re-opened, NOT re-scored and NOT re-interpreted** — it stands exactly as
  scored, on the proxy input it consumed. See §5.3.
- **Validation was no-LP only**: byte comparison against the pre-intake blobs, source cross-checks,
  and an independent-series plausibility test. Reproducible via
  `scripts/probes/_neiso86_intake_gates.py` (builds no LP).
- **2022 is iterable validation evidence** (rule 22). No number here is a skill claim, nothing was
  tuned against the 2022 residual, and the neiso-85 attribution figures are cited nowhere in the
  intake commits (V4).

## 2. What the source is, and how the transformation was proven before adoption

ISO-NE's monthly "Monthly wholesale electricity prices and demand in New England" recaps publish the
**Massachusetts natural gas index price**, defined in the posts as "a volume-weighted average of
trades at four natural gas delivery points in Massachusetts, including two Algonquin points, the
Tennessee Gas Pipeline, and the Dracut Interconnect". Identical wording, units ($/MMBtu) and monthly
convention in the 2018/2020/2022 posts as in the committed 2023–2025 posts. **Same quantity, same
boundary, same convention** — Phase-0 step 1 satisfied.

The stored quantity is `basis = MA index − Henry Hub monthly mean`. Verified against a committed row
and **its own cited source URL** before anything was written:

> Jan-2023 recap **$4.73/MMBtu** − Henry Hub **3.273** = **1.457 → 1.46** = the committed
> `NEISO,2023,1` row. Exact.

**Then falsified at scale.** The extractor was run over the entire in-sample window it is forbidden
to write, and compared to the 36 hand-transcribed committed rows:

- **33/36 exact**, 2 rounding ties (|Δ| = 0.01, `2024-07` and `2025-10`), **1 material** — `2025-08`,
  which the committed row's own `source` field declares an **interpolation** (§5.4).

A pipeline that regenerates 33/36 of someone else's independently transcribed rows is a validated
pipeline. Extraction additionally cross-checks the "By the numbers" table figure against the
narrative sentence in the same post and **raises on disagreement** rather than preferring one, which
is what prevents grabbing a prior-year comparison column.

## 3. Pre-registered gate outcomes

### V1 — SEASONALITY SIGN · **PASS**
All five complete authorized years satisfy `winter − summer > 0` (table in §0). Every one reverses.

**V1b (2026 substitute) · PASS**, `mean(Jan,Feb) − mean(Apr,May) = +14.20`. As pre-registered this
is the **weaker** check and is **not** reported as V1 passing: the ISO-NE recaps run only through
May-2026, so 2026 has no Jun/Jul/Aug and **V1 is NOT EVALUABLE** there. Declared in the PREREG in
advance, not after seeing the result.

### V2 — IN-SAMPLE INVARIANCE · **PASS** *(the gate that protects the keeper)*
- NEISO **2023–2025** basis rows: **36 before, 36 after, byte-identical.**
- `algonquin_citygate_daily.csv`: **all 124 pre-existing lines preserved**, 0 lost (437 now).

Held **by construction**, not by inspection: the basis writer rebuilds the file from its original
lines and re-emits every non-authorized line unchanged, refusing to write if any differs; the AGT
scraper's `--merge` mode independently asserts every pre-existing row survives byte-identical.

### V3 — LEVEL PLAUSIBILITY · **FAIL** *(reported as a FAIL; NOT reconciled)*
13 of 15 authorized winter months sit **below** the measured EIA-923 ISO-month delivered cost.
Per the PREREG, a V3 miss is reported, and **no adjustment, shift or blend was applied to make it
pass.** Nothing was changed in response to it.

**A control run establishes the gate's premise is wrong, not the data.** Applying V3 unchanged to
the **already-measured, keeper-validated in-sample years**:

| | 2023-01 | 2023-02 | 2023-12 | 2024-01 | 2024-02 | 2024-12 | 2025-01 | 2025-02 | 2025-12 |
|---|---|---|---|---|---|---|---|---|---|
| hub | 4.73 | 8.13 | 3.22 | 7.68 | 3.49 | 9.13 | 16.92 | 14.62 | 14.90 |
| EIA-923 | 15.17 | 11.84 | 5.55 | 11.69 | 9.81 | 8.53 | 19.46 | 16.16 | 15.79 |
| V3 | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL |

**8/9 of the designated keeper's own measured months fail V3 identically.** A gate that rejects the
keeper's validated input cannot be evidence against an intake that reproduces that same input's
construction.

The mechanism is visible and is already documented in the repo. NEISO's EIA-923 gas sample is
**2 reporting plants** (4 in 2018–2020) — measured this session — and `pipeline/backcast_config.py`
already records it as "rest[ing] on two reporting plants (partly LNG-priced)", which is the stated
reason the hub overlay was designed to **supersede** the 923 series for NEISO in the first place. An
LNG-contracted plant's delivered winter cost can sit well above pipeline hub spot, so 923 is not a
valid lower bound on the marginal hub. **V3 was a badly-premised gate.** It is recorded as FAILED,
and this paragraph is post-hoc interpretation, explicitly labelled as such.

For completeness, the intake moved V3 in the right direction anyway: **15/15 failing before → 13/15
after**, with 2022-01 (6.74 → 20.12 vs 16.27) and 2021-02 flipping to PASS and 2022-02 landing at
14.59 against 14.60.

### V4 — NO RESIDUAL FITTING · **PASS**
The intake commits cite the data change only. No commit message or row field references a price
residual, MAE, gate score, or the neiso-85 attribution figures. **Source selection was fixed in
PREREG §2.1 before any corrected value was computed**, on boundary correctness alone — the ISO-NE MA
index because it is the marginal hub the offer tracks. No candidate source was ever compared on
score.

### V5 — CROSS-ISO NON-INTERFERENCE · **PASS**
**804 non-NEISO lines, byte-identical.** CAISO, ERCOT, MISO, NYISO, PJM, SPP untouched. **CAISO was
deliberately left alone** despite arming the same overlay and being 100 % proxy in all years
including its tuned window — that is the CAISO lane's under rule 25 `[R-ISO-SCOPE]` and no CAISO
cell or row was touched.

## 4. The second file — the Algonquin daily leg (and why it mattered more than expected)

`data/raw/gas-prices/algonquin_citygate_daily.csv` covered **2023–2025 only**. The overlay docstring
is explicit that with `gas_hub_basis_daily` set the covered-month price is the daily-resolved AGT
series, "falling back to the flat monthly hub when the daily series is unavailable" — and the daily
leg is what "trips the dual-fuel switch."

**The NEISO 2022 touchpoint ran `gas_hub_basis_daily=True`** (read from its committed
`run_config.json`). With no 2022 AGT prints, the daily leg fell through to its **Transco Z6 NY
shape-borrow fallback**. So 2022 carried an inverted monthly level *and* a borrowed within-month
shape — a wider gap than "lost the daily resolution."

Extended with the existing committed scraper (`--merge`, 292 archive pages, 0 fetch failures):

| year | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| AGT prints | 55 | 56 | 45 | 94 | **62** | 44 | 49 | 30 | 1 |

**+313 new measured prints** (312 across 2018–2022, 1 for 2026), 123 committed rows frozen. Every 2022 winter month now carries ≥2 real
prints, so the **primary measured-AGT leg fires instead of the fallback** — including the real cold-day
blowouts on their true calendar days: **$22.69 (2022-01-19), $22.81 (2022-02-03), $22.48 (2022-02-14)**.

## 5. Declared residuals — nothing left silent

### 5.1 2018 March–June are UNOBTAINABLE and remain on the defective proxy
ISO-NE migrated its newswire mid-2018 and those four recaps were never carried over: the WordPress
archive jumps 2018-03-26 → 2018-08-24, the legacy `isonewswire.com/updates/2018/…` URLs 301-redirect
to the homepage, and the Wayback CDX holds no capture. Three independent retrieval routes were tried
and failed.

**Consequence, stated plainly: 2018 is now a MIXED year** — 8 measured months and 4 proxy months, and
**June-2018 (+6.2124) is one of the inverted summer values.** V1 passes for 2018 both as literally
specified (+2.85, using the retained proxy June) and on measured months only (+4.90, summer = Jul/Aug).
**2018 should not be solved until those four rows are resolved**, or the residual inversion will fire
in exactly the month it is worst.

Those rows were **left in place rather than deleted**. Deleting them would drop the overlay's month
coverage from 12/12 to 8/12 and hand those months to the EIA-923 fallback — a change to a mechanism's
coverage, not a data repair, and outside what was authorized. Flagged for the owner as a follow-up
decision, not taken unilaterally.

### 5.2 2015–2017 remain on the proxy
Not authorized, not touched. All 36 rows remain inverted (−0.58 / −2.29 / −4.37). Any future use of
those years must treat their NEISO basis as known-defective.

### 5.3 2026 is partial, on both legs
- **Monthly basis: Jan–May only.** June-2026 onward has no published recap as of 2026-08-06. V1 and
  V3 are both NOT EVALUABLE for 2026 (no summer months; no EIA-923 receipts) — declared in advance.
- **AGT daily: 1 print.** EIA has archived only one 2026 weekly page under `archivenew_ngwu`
  (2026/01_08 resolves; 02_05 onward 404). Low impact — the daily leg is a backcast mechanism, a
  backcast of H1-2026 is quarantined, and forecast-mode runs do not use it — but it is a real gap and
  is recorded as one.

### 5.4 An IN-SAMPLE row is stale, and was deliberately NOT touched (V2)
`NEISO,2025,8` is committed as an **interpolation** (+0.04 from Jul/Sep) because the N3050 proxy was
rejected and no measured figure was available at the time. **A measured figure now exists**: the
Aug-2025 recap (published 2025-10-02, after that row was written) states **$2.53/MMBtu** in both its
table and its narrative → basis **−0.3829**, a 0.42 $/MMBtu difference in a near-zero summer month.

**This session did not change it.** 2025 is in-sample and V2 is absolute. Recorded here for a
future in-sample-authorized session; it is a stale-but-honest interpolation, not a defect of the
same kind as the inversion.

### 5.5 The 2019 spent locked-test one-shot
Its NEISO rows are repaired (2019 basis now +3.82 Jan / −0.29 Jun, was +1.64 / +7.78). **The spent
one-shot stands exactly as scored, on the proxy input it consumed.** After this intake the committed
input no longer byte-matches what that one-shot read. This note is the load-bearing record of that
discontinuity. **Nothing here re-opens, re-scores or re-interprets it** (rule 22).

## 6. What is now UNBLOCKED but NOT DONE

1. **A corrected 2022 re-solve.** Needs its own **separate owner lift** of the still-active holdout
   freeze. **Not requested in this session**, per the charter.
2. **The C3c winter-derate depth/trigger identification.** neiso-85 established it cannot be
   identified while the input is inverted — "any depth tuned against this winter residual would be
   absorbing a fuel-price error." That blocker is removed for 2019–2022; the lane still needs its own
   authorization and its own charter.
3. **2018 Mar–Jun** (§5.1) and **2015–2017** (§5.2) — an owner decision on whether to drop the
   retained proxy rows so the 923 fallback fires, and whether to authorize 2015–2017.
4. **The Aug-2025 in-sample refresh** (§5.4) — needs in-sample authorization; V2 forbade it here.
5. **CAISO** arms the same overlay and is 100 % proxy in **all** years including its tuned window.
   Rule 25 `[R-ISO-SCOPE]`: flagged for the CAISO lane, untouched here.

## 7. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | Honoured — a correctness fix at the input, not a fitted adder; no mechanism chartered. |
| 11 `[R-DOCSTRING]` | Both new scripts carry module + public-function docstrings. |
| 13 `[R-MEASURED]` | The intaken series is a measured, forward-reproducible market input, not an outcome pinned to actuals. |
| 14 `[R-ACCURATE]` | The governing rule. A real measured series used on the wrong boundary, replaced by a correctly-bounded measured series; the unobtainable months are documented, not guessed. |
| 22 `[R-HOLDOUT]` | Freeze respected; intake authorized per-ISO/per-window and logged; no-LP validation only; 2019 data repaired without re-opening the spent one-shot; no skill claim. |
| 23 `[R-FROZEN-DERIVE]` | V4 — commits cite the data change only. |
| 24 `[R-REGISTRY]` | No new tunable; no off-registry channel. |
| 25 `[R-ISO-SCOPE]` | V5 — no other ISO touched; CAISO explicitly left to its own lane. |
| 27 `[R-PUSH]` | Opus session; data written to disk by script and pushed as exact on-disk bytes; blobs verified post-push. |
| 28 `[R-MECH-MATRIX]` | No mechanism tested ⇒ no cell verdict minted (duty d). No new `ScenarioConfig` field ⇒ duty (c) not engaged. The §5.6 neiso-85 block and the `gas_hub_basis_overlay` row note are updated to record the input as repaired (duty b). |

## 8. Artifacts

| path | contents |
|---|---|
| `scripts/data/fetch_isone_ma_gas_index.py` | Fetches the measured ISO-NE MA index; rebuilds NEISO basis rows with V2/V5 write guards |
| `scripts/probes/_neiso86_intake_gates.py` | Evaluates V1–V5 against the pre-intake blobs. **Builds no LP** |
| `data/raw/gas-prices/isone_ma_gas_index_monthly.csv` | The measured index series, 97 months, one source URL per row |
| `data/raw/gas_basis_by_iso_month.csv` | 61 NEISO rows corrected (2018×8, 2019×12, 2020×12, 2021×12, 2022×12, 2026×5) |
| `data/raw/gas-prices/algonquin_citygate_daily.csv` | +313 measured AGT prints (2018–2022, 2026) |
| `results/calibration/_neiso86_intake_gates.json` | Machine-readable gate outcomes |
