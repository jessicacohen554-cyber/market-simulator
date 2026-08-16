# PRECOMMIT — ercot-210 / CONDUCT-PHASE-0: the out-of-year conduct-transfer identifiability test

> **Status: PRE-REGISTERED. Pushed BEFORE any delivery-2023 SCED row is read.**
> Read-only measurement on committed corpora. NO LP, no solve, no year scored,
> no run registered, no `ScenarioConfig` field, no mechanism-matrix cell or row
> edit, no keeper contact. The verdict is MECHANICAL under §7 and is binding on
> the session that writes it.
>
> Keeper at precommit (rule 24 baseline read, resolved from
> `frontend/data/backcast/keepers/ERCOT.json` at this session's fetch):
> **`2026-08-15-ercot204-rule26-delete`** — determination NOT-YET, fail set
> {C3a-2023, C3b-2023}, C3c the single ledgered CAVEAT ×3.

---

## 0. WHAT IS BEING MEASURED, IN ONE SENTENCE

Are ERCOT scarcity-hour **offer surfaces** (storage foremost; thermal
top-of-stack alongside) expressible as a function of **forward-computable
drivers** — tightness/PRC percentile, and for storage the SOC/AS position —
such that a function fit **only** on delivery-2024/2025 60-day disclosures
reproduces the delivery-2023 scarcity-hour surfaces **at matched tightness**?

The answer is a number, not an argument, and §7 fixes the number that decides it
before any 2023 row is read.

## 1. CHARTER AND SIGNATURE

Executed under **X-1**, signed by the owner by dispatch of CONDUCT-PHASE-0
(2026-08-16) and made durable at the foot of
`docs/ASSESSMENT-ercot209-2023-scarcity-calibration-path-2026-08-15.md`
(§ RESOLUTIONS — CARD X). The signature, verbatim:

> "X-1 SIGNED (owner): Phase-0 of the card-R R-C conduct-layer program is chartered as a READ-ONLY
> identifiability/transfer measurement. Q-B and R-A are SCOPED, not reopened: they continue to bar any
> competitive-offer-class C3a/C3b-2023 lever round; they do not bar this measurement, which solves nothing,
> scores no price criterion, feeds no model input, and creates no ScenarioConfig field. 2023 conduct
> surfaces appear ONLY as the transfer test's evaluation target (measured-vs-measured). The verdict is
> mechanical under a pre-registered STOP rule; a Phase-1 build charter, if any, returns to the owner as its
> own card. If Phase-0 stops, Door D (card W wait-for-data, ~mid-2027) is the recorded floor."

The task is ASSESSMENT-ercot209 §3 Door A's Phase-0. Doors B and C remain
unsigned; Door D is the pre-registered fallback if this test stops.

## 2. STANDING RULINGS — CITED, NOT RE-LITIGATED

- **Q-B FINAL** (`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md`;
  licence re-test FAILED at ercot-191, L1 0.3857 vs 0.90): no competitive-offer-class
  C3a-2023 spend of any kind. **SCOPED, not reopened**, by X-1: this session
  computes **no C3a value**, runs no lever, and touches no offer-curve constant.
- **R-A** (`docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md`):
  NOT-YET stands; no C3b-2023-targeted determination rounds. This session
  computes **no C3b value** and no NRMSE of anything.
- **No C3a / C3b / C3c number is produced by this session, in any year.** The
  only 2023 quantities read are *measured offer-curve rows and measured reserve
  telemetry* — never a model output, never a scored criterion, never a price
  residual.
- **Rule 13 `[R-MEASURED]`**: delivery-2023 conduct surfaces are the transfer
  test's **evaluation target only** (measured-vs-measured). Nothing measured
  here enters any model input, and no artifact of this session is consumable by
  a solve.
- **Rule 22 `[R-HOLDOUT]`**: years referenced are {2023, 2024, 2025} only. No
  holdout year is read, no marker is sought or spent.
- **Rule 25 `[R-ISO-SCOPE]`**: ERCOT only.
- **Rules 5/24**: no config surface; no `ScenarioConfig` field, no CLI flag, no
  constant.
- **Rule 28 `[R-MECH-MATRIX]`**: **no matrix row or cell edit** — no mechanism
  is tested here. This is the ercot-182/189/196/200 *card-is-a-read* precedent:
  a measurement that adjudicates no mechanism mints no cell verdict.
- **Rule 27 `[R-PUSH]`**: every file ≥300 lines is edited locally and
  blob-verified after push, on whichever transport carried it.

## 3. DO-NOT-REDO (rule 28a) — why this object is none of the four dead instruments

Read first: `docs/mechanism-testing-matrix.md` §5.1 and
`docs/codebase-site/data/mechanism-matrix/ERCOT.js`. The lane is **off-queue by
design** — the chartered queue is empty (ercot-206 Phase A(1)) and X-1 is the
new charter. The four instruments this session must not rebuild, and the
distinction in each case:

| dead instrument | what it was | why this object is not it |
|---|---|---|
| **ercot-195 V0** — across-year tightness-conditioned rent function (model-free NON-IDENTIFIABLE, 4/14 folds) | **7 annual anchors** (vintages 2019–2025), response = the monitor's **annual CT/CC net revenue $/kW-yr**, conditioning = one scalar tightness summary **per year**, folds = leave-one-**vintage**-out **across four ORDC/design regimes** | **Different grain, different response, different population.** Here the unit is an **hour × class**, the response is a **submitted offer-curve statistic** (not a rent), the conditioning is an **hourly within-year percentile**, and the fit population is **thousands of hours inside the post-ECRS regime**, not 7 across-regime annual points. V0's proof was that its 7 anchors contain near-tied pairs whose rent gap is irreducible — a statement about **7 annual points**, which says nothing about hour-grain conduct. §7's **T5** re-runs V0's own model-free tie test at this grain and **will report NON-IDENTIFIABLE if the same pathology appears here**; that is the honest way to inherit V0, not to assume its verdict. |
| **ercot-162** — measured storage RT offer surface **fed verbatim** as an LP marginal cost (`R`; discharge collapsed ~74 %/yr) | a **mechanism arm**: transplanting the measured surface into the solve | **Nothing is fed anywhere.** This session runs no LP and creates no field. ercot-162 refuted *feeding* the surface; it did not measure whether the surface is a **function of forward drivers** — which is the only question here, and the prerequisite Phase-1 would need before anything could ever be built. |
| **ercot-204 §A + ercot-203b** — the published-RTORPA overlay (rule 19 / rule 13) | overlaying ERCOT's **published price adder** on the model's price | **No published price series is read at all.** §5's driver set is **quantity-only, by construction**: `prc`, `rtolcap`, `HSL`, `HASL`. The `system_lambda` / `rtorpa` / `rtoffpa` / `rtordpa` columns of `ercot_<year>_ordc_reserves_hourly.parquet` are **never read** — the probe selects columns explicitly and the JSON records the read set. |
| **ercot-201** — the E1 dispersion repair | a **build** whose identification route was barred by an adjudicated prior stop | Nothing is built. The dispersion object is not touched; the response here is an offer-price **quantile/share**, not a dispersion statistic, and no ercot-201 artifact is read or extended. |

**Positively stated:** the object is *hour-grain conduct surfaces within one
design regime* — a fit population confined to the post-ECRS, $5,000-SWCAP years
2024/2025, evaluated against 2023 at matched tightness percentile. It has never
been measured. `U` is the honest status of the question, and no cell is minted
either way.

## 4. DATA COVERAGE — INVENTORIED BEFORE THE DESIGN WAS FIXED

Coverage was inventoried first, per the dispatch, and it **shaped** the fit
window below. Nothing here is a fresh MIS fetch; every byte is committed or
restored from a git pin.

### 4.1 NP3-965 60-day SCED Gen Resource corpus (the conduct surfaces)

| window | publications | delivery | tracked at tip? | status |
|---|---|---|---|---|
| ERCOT-157 re-upload | 2023-03 .. 2024-03 (**323 shards**) | 2023-01 .. 2024-01 | **TRACKED** | present after hydration; 12 publication months verified on disk |
| BLOAT-B-5 item A2 | 2024-04 .. 2026-02 (**673 shards**) | 2024-02 .. 2025-12 | **UNTRACKED** (gitignored payload, no history rewrite) | **RESTORED from pin `726f389d94c45141bac83eacfdaea5e18a465c56`** per `data/raw/ercot/SCED/README.md`; never re-fetched from MIS (that route decays) |
| `rtcb-format-2026/` quarantine | 2026-02 .. 2026-03 (27 parts) | 2025-12-05 .. 31 | **UNTRACKED** | restored with the window; **NOT READ** — the quarantine stays load-bearing, globs stay non-recursive, this lane stops at delivery 2025-12-04 |
| loose probe extracts | — | 2024/2025 sample days | 3 of 4 **UNTRACKED** (BLOAT-B-5 item B1b) | **RESTORED from the same pin**; **superseded** by the full-year corpus for this test and not unioned with it (`_sced_source_files`' own supersession rule) |

**Restore verified byte-exact before the design was fixed:** `sha256sum -c
data/raw/ercot/SCED/SHA256SUMS.txt` returns **1,023 / 1,023 OK** (996 top-level
shards + the 27 quarantine parts), zero mismatches and zero missing files. The
manifest's post-slim hashes *are* the untracked bytes' hashes, exactly as the
corpus README states, so the restored corpus is the same corpus every prior
ERCOT lane read.

Known gap, carried not repaired: **deliveries 2024-01-10..23** aged out of the
free MIS list before the ercot-183 fetch and exist only in the owner's local
archive. Those 14 days are **excluded from the fit population by absence**; the
probe records the count of fit hours lost to them. No 2023 delivery day is
affected.

### 4.2 Reserve/tightness telemetry (the drivers)

`data/raw/ercot/ercot_<year>_ordc_reserves_hourly.parquet` — **TRACKED for
2023, 2024 and 2025**, hourly on the model's non-leap clock, columns
`prc`, `rtolcap`, `rtoffcap`, `rtolhsl` (quantities, **read**) and
`system_lambda`, `rtorpa`, `rtoffpa`, `rtordpa` (prices, **NOT read**).
Row counts 8760/8760/8760; **2025 carries 648 null `prc` hours** (the
post-2025-12-04 RTC+B tail), so delivery-2025 percentiles are taken over its
**8,112 valid hours** — the same denominator the ercot-195 V0 record used.

**No required measured series is unrecoverable. The test proceeds.**

### 4.3 The regime fact the coverage itself exposes, recorded before any fit

Measured `prc` p50 rises **6,750 (2023) → 9,039 (2024) → 11,055 (2025) MW**.
The system is structurally longer each year, so **raw PRC MW is not comparable
across years** and a level-based conditioning variable would measure the fleet,
not conduct. That is precisely how V0 died. The design below therefore
conditions on **within-year percentile rank only**, and §6 states what that
does and does not absorb.

## 5. THE CONDUCT-FUNCTION FAMILY (fixed here; no post-hoc respecification)

### 5.1 Unit of observation

One row per **(delivery hour `h`, class `c`)**, `c ∈ {STORAGE, THERMAL}`.

- **STORAGE** = `Resource Type == "PWRSTR"`, telemetered-ONLINE, **ONTEST
  excluded** — the ERCOT-154 population discipline, imported from
  `ercot161_pwrstr_conduct_census` rather than re-implemented.
- **THERMAL** = `SCED_THERMAL_TYPES` and `ONLINE_STATES` imported **verbatim**
  from `scripts/probes/ercot155_dispersion_census.py` (CCGT90, CCLE90, SCGT90,
  SCLE90, CLLIG, CLLIM, GSREH, GSNONR, GSSUP, RECIP, DSL).

### 5.2 The measured offer surface (the response)

Per resource-interval, the **above-LSL SCED2 offer segments capped at HASL** —
the ERCOT-154/161 construction, MW = `min(cum_MW, HASL) − max(prev, LSL)`,
prices in **absolute $/MWh** (the gas-multiple basis is refuted for storage).
Segments are pooled to the hour, MW-weighted. Three responses per (h, c):

| symbol | definition |
|---|---|
| `p50` | MW-weighted median segment price, $/MWh |
| `p90` | MW-weighted 90th-percentile segment price, $/MWh |
| `s500` | share of above-LSL offered MW priced ≥ $500/MWh (**fleet-size invariant** — this is why a share, not a GW: the ERCOT storage fleet roughly triples across 2023→2025 and an absolute-GW target would measure fleet growth) |

Prices enter as `log10(max(price, 1.0))` for `p50`/`p90`; the $1/MWh floor is
fixed here and applies identically in every year and fold.

**Class headline statistic** (what §7's T1 binds): **`p50` for STORAGE**
(scarcity-hour storage offers are the level that forms the tail) and **`p90` for
THERMAL** (the top-of-stack, which is the thermal object card R names). The
other quantile is measured and reported for both classes, but does not gate.

### 5.3 The drivers — forward-computable, QUANTITY-ONLY

| symbol | definition | forward analogue (rule 13) |
|---|---|---|
| `x1` tightness | `1 − ` within-year percentile rank of `prc(h)` | the model's own reserve margin / PRC counterpart |
| `x2` online-capability | within-year percentile rank of `rtolcap(h)` | `derive_ercot_rtolcap_forward`'s committed forward construction |
| `x3` AS position | MW-weighted mean of `(HSL − HASL)/HSL` over class-`c` online resources in `h` | the LP's own AS awards |
| `x4` availability/SOC proxy | MW-weighted mean of `HSL / HSL_ref` where `HSL_ref` = the resource's delivery-year p98 telemetered HSL (`_cap_ref`, imported verbatim from `ercot163_cc_commitment_state_census`) | for storage, SOC-limited discharge power — the LP's own `SOC[s,t]` |
| `x5` season | `1` if month ∈ {6,7,8,9} else `0` | calendar |

**No price of any kind is a driver.** `system_lambda`, `rtorpa`, `rtoffpa`,
`rtordpa`, RTSPP, LMP and every settlement price are outside the read set; the
probe selects columns explicitly and writes the read set into its JSON so the
claim is auditable rather than asserted.

### 5.4 Candidate forms and how ONE is selected — on the fit side only

Six candidates, fixed here:

`{ linear in (x1..x5) ; linear + x1² ; linear in logit(x1) and (x2..x5) }`
× `{ response in log10 (prices) / raw (share) ; response in level }`

fitted by **MW-weighted ordinary least squares**. Selection is by **5-fold
cross-validation inside the FIT YEARS ONLY** (folds = contiguous blocks of
delivery days, so hours of one day never straddle a fold). **The winning form is
frozen before any delivery-2023 row is read, and only that form is transferred.**
There is no search over forms on the 2023 side, and a failing verdict is never
retried with another form. That is the V0/ercot-208 discipline, stated here so
it binds.

## 6. FIT WINDOW, TRANSFER TARGETS, FOLDS, AND THE CONFOUNDS

### 6.1 Fit window (chosen after §4's coverage inventory, before any 2023 read)

Delivery-**2024** and delivery-**2025** hours with **`x1 ≥ 0.90`** — the tightest
10 % of each year (≈ 876 + 811 hours). Rationale, stated in advance: the object
is *scarcity-hour* conduct, so the fit stays inside the scarcity regime; 10 %
gives ~1,690 hours to identify at most 7 coefficients per response, a margin V0
never had; and both fit years sit in one design regime (post-ECRS, $5,000 SWCAP).

### 6.2 Transfer target

Delivery-**2023** hours with **`x1 ≥ 0.98`** (tightest 2 %, matched tightness,
strictly inside the fit's driver support). **Primary evaluation is restricted to
post-ECRS 2023 — delivery on or after 2023-06-10.** Pre-ECRS 2023 hours are
measured and reported as the regime contrast, and **do not gate**.

### 6.3 Folds

1. **OUT-OF-YEAR (headline).** Fit {2024 ∪ 2025} → predict 2023.
2. **LOYO across 2023 months.** The headline error is decomposed into the
   post-ECRS 2023 calendar months Jun–Dec (7). A month is **admissible** iff it
   carries **≥ 10** evaluation hours; months below that are reported as
   UNDERPOWERED and excluded from the counting rule (never silently dropped —
   the count of excluded months and their hours is written to the JSON).
3. **WITHIN-REGIME CONTROL.** Fit 2024 alone → predict 2025 at `x1 ≥ 0.98`, same
   monthly-fold rule. This is the discriminator: if the function cannot transfer
   *within* one regime, a 2023 failure is a statement about the driver set, not
   about 2023.

### 6.4 Confounds, stated up front

- **ECRS launch (2023-06-10).** ECRS is deducted from PRC-eligible reserves, so
  it shifts the `prc` level and its within-year distribution. Handling: (a)
  conditioning is on **within-year percentile rank**, which absorbs a pure level
  shift; (b) primary evaluation is **post-ECRS 2023 only**; (c) the pre-ECRS
  contrast is reported so the residual regime effect is visible rather than
  assumed away. What this does **not** absorb: a change in the *mapping* from
  tightness to conduct. Measuring exactly that is the point of the test.
- **ORDC vintage.** SWCAP is $5,000 across 2023–2025 and the ORDC changes the
  2022 SOM attributes sit before the window, so vintage is constant across fit
  and test *by the published record*. Any residual vintage effect is
  indistinguishable from the ECRS effect at this grain and is reported jointly,
  never separately claimed.
- **Season.** Fit-year tightness is winter-weighted in 2024 (84 of 176 tightest-2 %
  hours in January) and summer/fall-weighted in 2025 — measured from committed
  telemetry before the design was fixed, and the reason `x5` is a driver. The
  headline is additionally reported **summer-restricted** for transparency; the
  gate is the pooled result.
- **Fleet growth.** Absorbed by construction: `s500` is a share and `x4` is
  normalized by each resource's own p98 HSL.

## 7. THE MECHANICAL THRESHOLD TABLE — fixed before any 2023 row is read

Errors are **predicted vs measured, measured-vs-measured**, per fold, per class.
"Within band" = `|pred − meas| ≤ max(relative bar × meas, absolute floor)`.

| id | what it binds | band | fold rule to PASS |
|---|---|---|---|
| **T1** | class **headline** price statistic (STORAGE `p50`, THERMAL `p90`), out-of-year fit → 2023 | **±35 % or ±$50/MWh, whichever is LARGER** | **≥ 5 of 7** admissible post-ECRS 2023 monthly folds **AND Aug-2023 AND Sep-2023 both within band**, for **BOTH** classes |
| **T2** | `s500`, the offered-MW share ≥ $500/MWh, out-of-year fit → 2023 | **±0.15 absolute share or ±40 % relative, whichever is LARGER** | same fold rule as T1, both classes |
| **T3** | non-degeneracy (**fit years only** — not a 2023 read) | predicted headline at `x1 ≥ 0.98` ≥ **3×** predicted headline at `0.40 ≤ x1 ≤ 0.60` | must hold for **both** classes |
| **T4** | within-regime control, fit 2024 → predict 2025 | T1's band | **≥ 5** of the admissible 2025 monthly folds, **both** classes |
| **T5** | model-free identifiability (V0 §4's own test, re-run at hour grain) | a **τ-tied pair** is a (fit-hour, 2023-hour) pair with `\|Δx_j\| ≤ 0.05` on every scaled driver and identical `x5`; its **irreducible error** is `\|Δy\|/2` (no function of these drivers can do better on both members) | **< 10 %** of tested τ-tied pairs may have irreducible error exceeding T1's band, for **both** classes |

**T1's ±35 % is not a convenience number.** It is tied to the object: the
C3a-2023 miss is **−33.2 %**. A conduct function whose own out-of-year transfer
error exceeds the size of the gap it exists to close cannot close it. The band is
therefore set at the smallest round figure that still admits an error as large as
the gap itself — a deliberately *generous* bar, chosen so that a PASS means
something and a FAIL cannot be blamed on strictness.

**Aug-2023 and Sep-2023 are named explicitly** because they carry **96.2 %** of
the C3b-2023 squared residual (`ercot193_c3b_decomposition`, committed). A
transfer that works in mild months and fails on the object months is not a
transfer for this program's purpose.

### 7.1 THE VERDICT RULE — binding, no partial credit

```
TRANSFERABLE   iff  T1 AND T2 AND T3 AND T4 AND T5 all PASS
NOT-TRANSFERABLE   otherwise
```

- If the verdict is **NOT-TRANSFERABLE**: it is recorded at full magnitude,
  **nothing is chartered**, no cell is minted, and **Door D (card W
  wait-for-data, ~mid-2027) becomes the recorded floor** with the exhaustion
  proof extended one model class up. There is no re-specification, no second
  driver set, no widened band, and no "close enough" narrative.
- If the verdict is **TRANSFERABLE**: the session writes a **DRAFT Phase-1 build
  charter card for the owner — not executed**, and still charters nothing
  itself. Phase-1 returns to the owner as its own card, per X-1.
- **T5 governs how the failure is described.** If T5 fails, the verdict is
  reported as **model-free non-identifiable at this grain** (V0's own idiom, now
  measured at hour grain rather than assumed from 7 annual points). If T5 passes
  but T1/T2 fail, the object is identifiable in-regime but **does not transfer
  across the 2023 boundary**, and the ECRS/vintage confound is the named
  candidate. Those are different findings for the owner and will not be
  conflated.

## 8. DELIVERABLES AND WHAT THIS SESSION WILL NOT DO

**Produces:** this precommit; one read-only probe under `scripts/probes/`; one
JSON under `results/calibration/`; a FINDING doc arguing **both admissibility
directions** (the §2.6 pattern); one `docs/calibration-log/ercot.md` entry
claiming the **ercot-210** shorthand (log tail read: *"Next shorthand:
ercot-210"* — claimed, no collision, nothing renamed); and, **only if §7.1
returns TRANSFERABLE**, a draft Phase-1 card.

**Will not:** solve, score, register a run, touch the dashboard, edit the
mechanism matrix, add a `ScenarioConfig` field or CLI flag, add a
`.github/workflows/*.yml`, touch another ISO, touch another branch, or open a
pull request. Landing is **push-and-stop** on `claude/ercot-conduct-phase0-y66ell`;
the owner merges.

**Keeper at session start and (by construction) at session end:**
`2026-08-15-ercot204-rule26-delete`.
