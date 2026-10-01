# PRECHECK — caiso-182: extend the MEASURED offer surface to the three UNCOVERED classes, retiring fitted residue

**Pre-registered before any offer-surface value was derived from the bid corpus and
before any scored metric was read.** Session caiso-182, 2026-08-08. CAISO only.

Keeper `2026-08-06-caiso-175-tac-intake` (**NOT-YET**, rubric v3.1, 8 criteria, **C3a the
sole FAIL**: 2023 +4.2 % PASS, 2024 +11.5 % FAIL, 2025 +14.7 % FAIL, RT, band ±10 %).
DOF **11 / 8**. `complete` **NOT held** (withdrawn 2026-08-06). **HOLDOUT SPEND FREEZE
ACTIVE** — 2023 / 2024 / 2025 only. `calibration-complete.json` and `holdout-freeze.json`
are owner acts and are **not written** by this session.

---

## 0. DISCLOSURE — exactly what was read before this document was written

Pre-registration is worthless if the design was already shaped by the numbers it claims to
predate, so the boundary is stated rather than implied. Before writing this, I read:

* the committed **model-side** class census (`data/processed/bin_assignments_CAISO.csv`) —
  class counts, nameplate MW, cap-weighted `Plant_Avg_HR`, per-plant HR/MW quantiles;
* the committed `caiso_offer_curve_measured.json` / `caiso_offer_surface_condbinned.json`
  **`_provenance` blocks** (classifier constants, G1–G4 gate records, per-year band mults)
  — i.e. the *already-published* record of the incumbent derive;
* the keeper's `calibration_attestation.json` DOF ledger and `run_config.json` flags;
* `derive_caiso_offer_surface.py` in full, and the `_CAISO_OFFER_CURVE` block.

**Not read, because it does not yet exist in this container:** any value derived from the
OASIS bid corpus on this session's re-fetch. The corpus is **gitignored and was absent**
(§2), so no recovered-HR distribution, no conduct ratio and no candidate band existed at
authoring time. The identification tests in §5 are therefore genuinely blind.

**No LP has been run. No scored metric has been read.**

---

## 1. P0-1 — THE DO-NOT-REDO AUDIT, FIRST AND EXPLICIT

`docs/mechanism-testing-matrix.md` §5.2 records the CAISO **in-model lever queue as EMPTY
of untested members** (caiso-163 closed the last one), and item 2 (seam/intertie) as
**STRUCK/CLOSED** at caiso-142/143/167. §5.2's own standard for re-entry is *"new evidence
against a named caiso-140/141/142/143/144 DO-NOT-REDO cell"*.

**This session is NOT a re-test of a closed cell, for a reason that is a measurement rather
than a re-framing.** The relevant cell is `measured_offer_surface` CAISO = **K** — *armed
and keeping*, never rejected, never inert, never governance-refused. Nothing here re-opens
an `R`/`I`/`G` adjudication. What caiso-181 added is new **positive** evidence that
**locates** the caiso-180 open residual: interior CEMS contradiction is **exactly 0** in
599,736 interior in-window hours, both bars clear, so the envelope is measured
depth-correct and the +1.1 / +1.6 pp **belongs to the offer curves**. That is an
elimination performed on data, and it converts "the offer curves are suspected" into "the
offer curves are the remaining owner".

The object here is the **uncovered residue of a cell already adjudicated K** — extending a
keeping mechanism's coverage, not re-litigating a refusal. Concretely, `measured_offer_surface`
covers 2 of the 5 registered gas classes; this session asks whether the other 3 can be
covered too.

**If this were a re-test of a closed cell I would stop and report that.** It is not, and the
distinction is checkable: no cell in the CAISO column moves from `R`, `I` or `G`.

### 1a. Levers this session may NOT touch (carried forward, not re-derived)

`battery_dispatch_adder` (permanent declared-residual DOF; all three exits closed at
caiso-176/178/179 — **not** re-derived from NREL ATB, NREL cost benchmarks, PNNL-33283 or
LFP warranties); routing the LP through `_degradation_cost_per_mwh`; the
AS-power-reservation family (caiso-74/127/129); any N–S topology lever (caiso-164 §0/§6,
**FORBIDDEN**); `caiso_ps_charge_shape_anchor` (stays `G`, input walled); the seam/intertie
family (item 2, STRUCK); `unit_outage_short_windows` / `unit_partial_outage_windows`
(caiso-180 `I`, zero coal in CAMPD's CAISO population); the CAISO outage envelope's
**DEPTH** (caiso-181 SETTLED — not re-audited, not reverted, not haircut).
`caiso_dam_outages` stays `U` and is **NOT armed** here.

### 1b. THE caiso-181 §7.2 BASIS IS CORRECTED, AND THE CORRECTION BINDS

caiso-181 named this successor on the **rule-23 `[R-FROZEN-DERIVE]` source-data-changed**
basis, cited to the 2026-07-24 CAMPD change. **That basis is wrong and is not used.** The
CAISO offer surface derives from **OASIS public bids + the citygate gas series**; neither
changed on 2026-07-24, and nothing in the offer path consumes the outage envelope. Rule 23
is therefore **NOT triggered**, and this session may not re-value any frozen identification
constant. The binding basis is **rule 21 `[R-DOF]` + rule 14 `[R-ACCURATE]`**: fitted
multipliers are a declared residual with a named measured replacement, and the legitimate
move is to **extend measured coverage so those residual entries retire** — the contract the
deriver's own docstring already states ("a rule-24/25 SHRINK of the fitted surface").

---

## 2. P0-2 — BE-1 REPRODUCIBILITY, AND THE BLOCKER THAT WAS ON THE CRITICAL PATH

### 2a. The corpus was ABSENT, not merely un-curated

`data/raw/caiso-public-bids/` is **gitignored** (`.gitignore:86`) and this container carried
**only its README** — zero daily zips, and no `data/clean/` tree at all. caiso-178's
"FETCHED IN FULL" status describes a *previous* container, not a committed artifact. The
corpus is re-fetchable (OASIS answered a probe request HTTP 200 / 366,685 B / valid zip
with a 10.3 MB CSV member), and a full re-fetch of the 1,096 train-window trade dates at the
fetcher's mandatory 6 s spacing is running.

**Consequence, stated plainly:** BE-1 is reproducibility against a **re-fetched** corpus.
If OASIS has revised any trade date since the committed artifact was derived, BE-1 can fail
for a source reason rather than a code reason. That is disclosed here, in advance, and is
itself a reportable finding rather than a licence to proceed on an unreproducible base.

### 2b. The curation memory ceiling — FIXED, PROVEN, AND ALREADY COMMITTED

caiso-178 measured `curate_dam_public_bids.py` at ~14.3 GB for a 365-day year against a
~15 GB ceiling. Root cause, confirmed by reading: `_curate_spec` holds every day-frame and
`pd.concat`s them, then `write_clean` takes a **full `pa.Table.from_pandas` copy on top**.

Fixed as the charter directs — **pure engineering, zero model semantics, its own commit**
(`dd482f0a`). `clean_io.write_clean_iter` streams chunks into a `ParquetWriter`, bounding
peak memory at one row group. **Proven byte-equivalent before use**, 40 days / 3,552,863
rows (`scripts/probes/_caiso182_curate_stream_be.py`,
`results/calibration/_caiso182_curate_stream_be.json`):

| leg | check | result |
|---|---|---|
| **BE-A** | frame equality incl. columns, dtypes, row order | **PASS** |
| **BE-B** | row-group layout `[1048576, 1048576, 1048576, 407135]` | **PASS** |
| **BE-C** | normalised data sha256 `fb5535a9…76d3ed5` | **PASS**, identical |

Raw-file byte identity is **impossible by construction** — `_build_metadata` stamps
`created_utc` at write time — so BE-C normalises exactly `created_utc` + `git_commit` on
**both** sides. Both legs write identical partition keys and are separated by redirecting
`CLEAN_DIR`, so embedded metadata cannot mask a real difference. (A first run of the probe
**failed** BE-C on a probe artifact — the two legs wrote different `year` keys — and the
harness was corrected rather than the bar moved; recorded here so the PASS is not read as
first-try.)

### 2c. BE-1 protocol and its bar

Run the **UNMODIFIED** `derive_caiso_offer_surface.py` over trade years 2023–2025 against
the re-fetched, re-curated corpus and compare the **consumed content** of both JSONs to the
committed artifacts.

* **BE-1 PASS** = consumed content byte-identical after removing `_provenance.derived_utc`
  (the only field that is a timestamp by construction). This is the caiso-153 §D-2 standard,
  which that session met ("only `derived_utc` differs").
* **Environment disclosure, pre-registered:** this container runs **pandas 3.0.5 / numpy
  2.4.6 / pyarrow 25.0.0 / scipy 1.17.1**. pandas 3.x is a **major-version bump** over
  whatever produced the committed artifact (derived 2026-08-02), and pandas 3 defaults to
  PyArrow-backed strings. A groupby-median or float-formatting difference could move a
  consumed digit **without any code or data change**. If BE-1 fails, the pre-registered
  first move is to **localise the failure** (source-data diff vs library diff) and report it
  — never to adjust a constant to make it pass.
* **NO BE-1, NO ARM A.** If BE-1 cannot be established, ARM A is not derived, and this is
  reported plainly rather than derived on an unreproducible base.

---

## 3. P0-3 — THE COVERAGE + CONTAMINATION CENSUS (model side measured; bid side pre-registered)

### 3a. Coverage — the model-side half, from committed data

| class | plants | nameplate MW | share of thermal fleet | cap-wt `Plant_Avg_HR` | measured surface |
|---|---:|---:|---:|---:|---|
| CC_REGULAR | 28 | 13,708.1 | 47.43 % | 7.44 | **COVERED** |
| CT_PEAKER | 134 | 7,616.3 | 26.35 % | 10.86 | **COVERED** |
| ST_GAS | 3 | 2,858.8 | 9.89 % | 11.85 | **UNCOVERED** |
| CC_CHP | 21 | 2,706.7 | 9.37 % | 6.90 | **UNCOVERED** |
| CT_CHP | 71 | 1,961.9 | 6.79 % | 11.01 | **UNCOVERED** |
| COAL | 1 | 50.0 | 0.17 % | 5.61 | n/a (Argus Cogen, not a CAMPD reporter) |

**26.0 % of the model's thermal capacity — 7,527.4 MW — prices on 100 % fitted,
ERCOT-inherited multipliers**, and `_CAISO_OFFER_CURVE`'s own comment concedes they "are
NOT CAISO-grounded … preserved verbatim". ST_GAS is precisely the class caiso-180 measured
**backfilling** the CC_REGULAR the accurate envelope removed.

### 3b. Contamination — the bid-side half, and the bound already on record

G1 as recorded: CC bucket **11,935 MW** (0.871 × CC_REGULAR alone), CT bucket **9,950 MW**
(1.306 × CT_PEAKER alone). Against the *combined* populations the classifier can actually
reach, those read 11,935 / 16,415 = **0.727** and 9,950 / 12,437 = **0.800** — i.e. the CT
bucket's 1.306 "over-shoot" is close to what CT_CHP + ST_GAS contribute, which is what the
deriver's `[0.5, 1.6]` CT band was explicitly widened to allow ("the ST_GAS/CT_CHP
contamination allowance"). **Reported as the arithmetic it is, not as proof** — the masked
ids preclude a per-plant check.

### 3c. THE IDENTIFICATION TESTS — bars fixed here, before the corpus lands

The charter permits an additional cut only if it is **identified from the recovered-HR
distribution itself** (or a published capability/NQC inventory), never chosen to move a
band, a class energy or a price.

**IT-2 — SEPARABILITY (the charter's named route).** Candidate boundaries are the midpoints
between adjacent registered class base HRs — **existing constants, not new ones**: CC_CHP
6.90 | CC_REGULAR 7.44 → **7.17**; CT_PEAKER 10.86 | CT_CHP 11.01 → **10.94**; CT_CHP 11.01
| ST_GAS 11.85 → **11.43**.

> **IT-2 PASSES** for a boundary iff (a) the cap-weighted density of recovered `slope`
> exhibits an **antimode within ±1.0 MMBtu/MWh** of it — the same standard G2 imposed on the
> incumbent 8.5 cut ("the cut must sit in a capacity-density valley") — **and** (b) the
> resulting sub-bucket capacity reconciles to the target class's fleet MW inside the G1
> bounds already registered for that side.
>
> **If IT-2 fails, the separation route does not exist and ARM A does not take it.** No cut
> is placed "close enough"; no bound is widened to admit one.

**Pre-registered expectation, recorded so it can be falsified:** IT-2 will likely **FAIL**
for the CT-side boundaries. The three CT-like classes' base HRs span **0.99 MMBtu/MWh
total** (10.86 / 11.01 / 11.85) while the measured slope distribution's own interquartile
width is **3.87** (p25 7.49, p75 11.36, caiso-153 §B). A 0.15-wide class cannot be cut out
of a distribution that wide. I expect the CC-side boundary (7.17, separating CC_CHP 6.90
from CC_REGULAR 7.44) to fail for the same reason.

**IT-1 — CONDUCT HOMOGENEITY (the fallback route, tested only if IT-2 fails).** The model's
own semantics are `mc = mult × plant_HR × gas + VOM + carbon`, so a band multiplier is a
**dimensionless conduct ratio** — how many times its own marginal fuel+carbon cost a
resource bids — and it is transferable across classes **iff that ratio does not itself vary
with heat rate**. That is directly measurable on the recovered axis:

> Within each measured bucket, stratify gas-classified resources into **terciles of
> recovered `slope`** and compute, per consumed band (`econ_low`, `econ_high`, `peak`), the
> cap-weighted median conduct ratio
> `m_i = (band_price_i − VOM_bucket) / (slope_i × (gas + CO2 × P_carbon))`
> — normalised by each resource's **own** recovered HR, not the class constant.
>
> **IT-1 PASSES** iff, for every consumed band in that bucket, `max − min` across terciles
> is within **`max(0.08, 10 %)`** of the pooled value — the deriver's **own frozen G3
> tolerance** (`LOYO_ABS` / `LOYO_REL`), reused rather than invented.
>
> **If IT-1 fails, the bucket band is NOT transferable and ARM A is REFUSED.** A failure is
> reported at full magnitude as a measured fact about CAISO conduct.

The tercile stratification is a **test instrument only**. It enters no LP value, no
artifact and no config; it is not a fitted scalar and cannot become one.

---

## 4. P0-4 — THE DIRECTION IS PRE-REGISTERED AS UNKNOWN

I may not predict or target a C3a sign, and do not. Measured offer conduct is what it is.
The **caiso-163 precedent binds**: a published/measured input **STAYS IN** even when the
residual moves the wrong way, and a worse residual is then a **DISCOVERED BUG** (rules 1 /
14), never grounds to revert.

C3a will be **REPORTED at full magnitude for all three years whichever way it moves**, and
is **NEVER the promotion basis** — it is a live FAIL, so rule 1 forbids a C3a move being the
*reason* for a promotion and rule 13 forbids any quantity tuned to it. The promotion basis,
if any, is that the model prices classes on **measured conduct** instead of fitted
multipliers and **retires declared DOF**.

**If the residual does not close, that is a legitimate and expected outcome and will be said
plainly.** The honest successor is then the remaining named contributor — the **WALLED**
hourly pumped-storage water state (`FINDING-caiso140` §B / the caiso-141 A2 data wall) —
which is an **owner-funded intake decision, not a session lever**. No close will be
manufactured.

---

## 5. ARM A — the design, and its decision tree

One config delta off the keeper recipe, reproduced via
`--replay-bundle results/calibration/caiso175_tac_intake` (**never** a remembered CLI
string), `--year 2023 2024 2025` in **ONE** invocation, years sequential.

```
BE-1 fails ─────────────────────────► ARM A NOT BUILT. Report. (§2c)
BE-1 passes
   ├── IT-2 passes for a boundary ──► ROUTE (i) SEPARATION: derive per-class measured
   │                                   bands directly for the separated class.
   ├── IT-2 fails, IT-1 passes ─────► ROUTE (ii) BUCKET-BAND: the measured band of a
   │                                   bucket is applied to EVERY model class in that
   │                                   bucket (CC bucket → CC_CHP; CT bucket → CT_CHP,
   │                                   ST_GAS), each at its OWN base heat rate.
   └── IT-2 fails and IT-1 fails ───► ARM A REFUSED. No LP. Report the blocked verdict.
```

Route (ii) is **not** an approximation dressed as a measurement: the measured band is a
cap-weighted median over a bucket whose population **demonstrably includes** the uncovered
classes (§3b), so applying it to that bucket's full membership is what was actually
measured — and it is strictly more faithful than the status quo, which applies the bucket
median to part of the bucket and leaves the rest on ERCOT inheritance. IT-1 is the test that
this is true rather than merely plausible.

**Scope limit, pre-registered.** ARM A touches the **static econ/peak bands only**. The
**committed** band stays unarmed for every class (the Lever-A inversion lesson, rule 19
`[R-ONE-MECH]`), and the condbinned peak ladder is **not** extended to new classes in this
session.

---

## 6. ARM B — the caiso-181 H-EDGE construction repair (independent of A, zero DOF)

Run only if A is blocked, or after A is adjudicated. **Its own precommit section, as a
rule-23 derive-**grain** change** (the ercot-174 BE-1/BE-2/BE-3 class).

**The defect,** confirmed by caiso-181 at 100 % concentration and sized at 2.42 / 2.38 /
2.57 % of envelope depth: the deriver detects in **hours** (`start = clock[s]`,
`last = clock[e-1]`) but writes `strftime("%Y-%m-%d")`, and the loader re-expands
`outage_start` 00:00 → `outage_end` 23:00 — asserting up to 23 h per edge it never detected,
exactly where the event contract guarantees the neighbouring hour was **running**. Max
distance from a window boundary 22 h < 24, every year.

**DESIGN CONSTRAINT — the writer and loader serve ALL SIX ISOs.** The repair MUST be
**backward-compatible and per-ISO adoptable**: add **OPTIONAL** `outage_start_hour` /
`outage_end_hour` columns; the loader consumes them **when present** and falls back to the
current day-granular reconstruction **when absent**; re-derive **CAISO's extract ONLY**.

> **Any change that alters another ISO's committed extract or its keeper's availability is
> OUT OF SCOPE and fails the arm** (rule 25 `[R-ISO-SCOPE]`, rule 28 duty d).

**Proof obligation:** DETECTION is unchanged — the same windows, only their expressed grain
differs. Asserted BE-style: same window count, same (plant, start-day, end-day) tuples, same
order, for every ISO's extract; and for the five non-CAISO ISOs the re-derived file must be
**sha256-identical** to committed.

---

## 7. GATES — pre-registered, fail-closed, and they FAIL the arm

| gate | bar |
|---|---|
| **G-DOF** | `n_entries` / `n_residual` **11/8 → 11/7 or lower** for ARM A; **EXACTLY 11/8** for ARM B. **An increase in either count is an AUTOMATIC FAIL.** |
| **G-NOFIT** | **ZERO** new fitted scalars. Every number entering the LP read from the measured artifact or a published source with a citation. A value settable only by looking at an output is an **OPEN ROOT-CAUSE ISSUE, reported not installed** (rule 21). |
| **G-FROZEN** | Every frozen identification constant **byte-unchanged**, diffed and shown: the `_MIN_DAYS`-class constants, `BODY_FRAC` 0.35, `GAS_MIN_R` 0.6, `hr_cut` 8.5, the Theil-Sen estimator choice, `GAS_SLOPE_RANGE`, `GAS_MIN_DAYS`, `MIN_CAP_MW`. |
| **G-C1** | C1 free-class fuelmix **PASS** on every free class, all three years. |
| **G-CAISO180** | \|ΔTWh\| must not exceed the FULL magnitude of the regeneration leg it reverses: **CC_REGULAR 0.11 / 0.44 / 0.67**, **ST_GAS 0.03 / 0.13 / 0.07**, **CT_PEAKER 0.02 / 0.04 / 0.06**. Exceeding it = over-corrected past the whole leg → **FAIL**. |
| **G-PROT** | C6 and C8 **PASS**; C8 stays **SCORED** (every arm registers its own `legitimacy_diagnostics.json`). |
| **G-LOYO** | Any mechanism-change-driven verdict flip scored **leave-one-year-out within 2023–2025 BEFORE any promotion** (rule 22). |
| **CONTROL** | **MANDATORY if any arm solves** (§8). |

### 7a. G-DOF — A GRANULARITY DEFECT IN THE GATE, FOUND AT P0 AND REPORTED, NOT WORKED AROUND

The ledger is **hand-maintained and asserted**, not derived from the config. Its 11 entries,
8 residual, are: `offer_curve_by_group` (**112 scalars**, covering CC_REGULAR,
CC_INTERMEDIATE, CC_CHP, CT_CHP, CT_PEAKER, CT_INTERMEDIATE, ST_GAS, ST_GAS_INTERMEDIATE and
five COAL_* groups), `offer_curve_committed_below_floor[CAISO]` (1 scalar: ST_GAS
`committed` 0.81), `offer_curve_smoothing`, `COAL_SIGMOID_DEFAULTS[CAISO]`,
`wefor_multiplier`, `battery_dispatch_adder`, `WECC_import_simultaneous.cap_mw`,
`IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]`.

**A coverage extension cannot move `n_residual` off 8.** Covering CC_CHP / CT_CHP / ST_GAS
retires 9–12 *scalars* inside entry 1, but that entry stays residual because the
`*_INTERMEDIATE` groups, the COAL groups, every `committed` band, `econ_low_share` and
`pct_peaking` remain fitted. The only offer-path entry small enough to retire whole is
entry 2 — and retiring it means arming a **measured `committed` band**, which the deriver's
own frozen method **refuses** to arm (step 5, the Lever-A inversion lesson, rule 19).
Splitting entry 1 into measured/residual halves would push `n_entries` to 12, which
G-DOF makes an automatic fail.

> **Consequence, pre-registered:** as written, **G-DOF is unachievable by the chartered ARM
> A object**, for a reason internal to the ledger's granularity rather than to the work.
> **The gate is NOT relaxed, re-scoped or re-interpreted.** ARM A will be scored against
> G-DOF **verbatim**; if it retires scalars but no entry, it is reported as **G-DOF FAIL on
> the letter**, **no promotion follows**, and the granularity defect is escalated to the
> owner as a charter/ledger item. The scalar-granularity retirement (112 → 112 − k) is
> reported **alongside** as the honest diagnostic, explicitly labelled a *different
> measurement from the one the gate names*.

This is filed at **P0, before any arm was built**, so it cannot be mistaken for a
post-hoc excuse for a gate the work failed.

---

## 8. CONTROL — mandatory if any arm solves

caiso-180 **and** caiso-181 both measured same-head drift at **exactly $0.000**. A fresh
control must reproduce the keeper **TO THE CENT**; **if it does not, THAT is the finding**
and it is reported at full magnitude as its own result.

* Reproduction by **`--replay-bundle results/calibration/caiso175_tac_intake`** — the
  documented recipe contract, never a remembered CLI string.
* `scenario_config` verified **fail-closed** with the caiso-180 **L1 / L2 / L3** split:
  **L1** exact on the keeper's own key set; **L2** arm-to-arm over the full union; **L3**
  additive drift gated on *code-default* **and** *non-CAISO scope*.
* **REUSE `scripts/probes/_caiso180_arm_identity.py`** — not re-invented.
* Its **§3a leg-2 ordering gate is WITHDRAWN AS MALFORMED and is NOT reinstated** (window
  count is not envelope depth; falsified by caiso-180's own measurement). Pairwise
  **distinctness** plus the **sha ladder** remain the load-bearing proofs.

---

## 9. WHAT THIS SESSION MAY NOT DO

* **No re-valuing of any frozen identification constant** (§1b — rule 23 is not triggered).
* **No quantity tuned to C3a**, in any form — no adder, no haircut, no band nudged because
  the residual is +11.5 / +14.7 % (rule 13 `[R-MEASURED]`).
* **No off-registry channel** (rule 24): every change is a registered field or an artifact
  byte, never an env var or CLI-only knob.
* **No cross-ISO verdict transfer** (rule 25, rule 28 duty d); no other ISO's keeper shard,
  registry sidecar, status part or bench file written.
* **No out-of-training year** solved, scored or registered; the freeze is respected and both
  markers left untouched (owner acts).
* **No mechanism armed that is not pre-registered here** — including `caiso_dam_outages`.
* **No promotion on a C3a move** (rule 1).

## 10. REGISTRATION

Every arm that **solves** is registered (rule 15) with its own `legitimacy_diagnostics.json`
so C8 stays **SCORED**, all three years in **one** bundle (rule 16). The CAISO matrix cells
and §5.2 header are updated in **this** session (rule 28 duty b); a new `ScenarioConfig`
field lands with its matrix row in the same PR (duty c).

**If P0 establishes that neither arm can be built on committed data, nothing is registered,
no LP is spent, and that result is filed** — a clean blocked verdict is worth more than a
fitted close.
