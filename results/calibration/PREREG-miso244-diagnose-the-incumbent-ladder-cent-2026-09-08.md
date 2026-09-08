# PREREG miso-244 — **DIAGNOSE THE ONE-CENT GAP BETWEEN `MISO_SEAM_LADDER_BY_YEAR` AND ITS OWN DERIVE.** Zero LP, and the diagnosis is the deliverable

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — the only lever in this lane
with a confirmed construction defect behind it, handed forward by miso-243 §7.1 as a **named
successor with its exact magnitude and location**, un-diagnosed.

**Keeper at session start: `2026-09-07-miso-243-spp-pairing`** (bundle
`results/calibration/miso243_sppair_K`), DETERMINATION **CALIBRATED**, C3c the single ledgered
non-downgrading caveat, DOF ledger **41/2**. Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; MISO holds
no `complete` marker and **no out-of-training year will be solved, scored or registered.** MISO
carries exactly **one** registered run (rule 15) and will still carry exactly one when this session
ends.

**THERE IS NO RUBRIC FAILURE IN MISO.** All six ISO keepers score CALIBRATED. This session does not
invent one, does not target C3c, and proposes no offer adder, ORDC offset, scarcity multiplier or
any level tuned to a residual.

**This document is pushed BEFORE any adjudicating quantity is computed, together with the probe
that computes them** (`scripts/probes/_miso244_incumbent_ladder_cent_phase0.py`). Every decision
rule, bar and disposition below is fixed here; none may be written after seeing a number.

**THE HANDOFF'S OWN INSTRUCTION IS THE SESSION'S SHAPE:** *"DIAGNOSE THE CENT BEFORE PROPOSING
ANYTHING … DO NOT re-derive first and diagnose after. … If the cent is a transcription artifact,
SAY SO AND STOP: that is a complete session result and it costs zero LP."* This PREREG is written
so that the STOP outcome is a **pre-registered disposition**, not a retreat.

---

## 0. The facts this rests on, established from SOURCE and COMMITTED ARTIFACTS before this document was written

No adjudicating quantity appears in §0. Every item is a code reading, a committed-table reading, a
committed-config reading or a predecessor's published column, and each is cited.

**F1 — THE OBJECT.** `MISO_SEAM_LADDER_BY_YEAR`
(`src/market_sim/model/interchange/spec.py:1504`) is the incumbent per-year MISO-hub-anchored Q-Q
band ladder: 3 years × 4 seams (PJM / SPP / South / Manitoba) × 2 sides × 8 bands = **192 committed
entries**, each a 2-decimal `$/MWh`. Its derive is
`scripts/data/derive_miso_seam_ladders.py::derive`, which calls `_derive_one` per seam and returns
`[round(p, 2) for p in imp]` / `[round(p, 2) for p in exp]`.

**F2 — THE GAP, as miso-243 published it.** miso-243's P-2 leg measured, as a disclosed by-product
of its own failed leg (`ADDENDUM-miso243-my-own-p2-leg-failed-…` §0a;
`_miso243_spp_pairing_repair_phase0.json` → `gates.P_2_byte_identity.detail`), the per-seam
`max |committed − derive(HEAD)|`:

| year | PJM | SPP | South | Manitoba |
|---|---:|---:|---:|---:|
| 2023 | **0.01** | 0.00 | **0.01** | 0.00 |
| 2024 | 0.00 | 0.00 | **0.01** | 0.00 |
| 2025 | 0.00 | 0.00 | 0.00 | 0.00 |

Three entries, each exactly **0.01** — the magnitude of `NO_WASH_EPS`. It is **PRE-EXISTING**
(present with the old caller, unrelated to miso-243's pairing repair), it was **reported and not
fixed**, and it is **un-diagnosed**. miso-243 published only the per-seam maxima, so **which band
of which side** is not yet on the record.

**F3 — THE ESTIMATOR, read from source.** `_derive_one(da, flow, spec, notes)`:

```python
step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES          # PJM 912.5, SPP 500, South 375, MHEB 362.5
mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
imp  = [np.quantile(da, 1.0 - (flow >  m).mean()) for m in mids]
exp  = [np.quantile(da,       (flow < -m).mean()) for m in mids]
lim  = min(imp) - NO_WASH_EPS                                 # NO_WASH_EPS = 0.01
for k, s in enumerate(exp):
    if s > lim: notes.append(...); exp[k] = lim               # same-seam no-wash clamp
return {"import": [round(p, 2) for p in imp], "export": [round(p, 2) for p in exp]}
```

Two roundings are therefore possible sources of a whole cent: the terminal `round(p, 2)`, and the
clamp value `lim`, which is computed from the **UNROUNDED** `imp` list.

**F4 — THE PRICE SERIES IS A 2-DECIMAL QUANTITY STORED AT REDUCED PRECISION.** The coupling anchor
is the measured MISO **Indiana-hub DA** LMP, `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`
column `da` (43,800 rows; years 2022–2026). Published LMPs are cent-denominated, and the column
reads back with float32 round-trip signatures (`25.610001`, `24.389999`), i.e. absolute
representation error of order `1e-6`–`1e-5` over the `$10`–`$400` range the ladder spans.
`np.quantile`'s linear interpolation between two adjacent cent-valued prices can therefore land
**exactly on a half-cent**, where `round(·, 2)` is a tie and a perturbation of order `1e-6` decides
which cent it returns. **This is a code+data reading, not a claim about the gap**; §2 states the
prediction it implies and §2.4 states how that prediction can fail.

**F5 — THE INCUMBENT TABLE HAS NO RULE-23 REPRODUCTION PIN, AND THAT IS WHY A CENT COULD SIT THERE
UNSEEN.** `tests/iso/miso/test_miso_seam_ladder.py` pins the incumbent table's **shape**
(`test_every_backcast_year_covers_every_seam_and_band`), **monotonicity**
(`test_import_ladders_rise_and_export_ladders_fall`), its **no-wash ordering**
(`test_same_seam_no_wash_ordering`) and one **spot value** (`test_pjm_2025_base_band_is_the_derived_value`,
$21.82) — but **no test re-runs `derive()` and compares.** The only reproduce-the-derive pin in the
file is `test_registry_reproduces_the_frozen_derivation` (line 459), which covers the **SPP HOURLY**
ladder alone, at `atol=0.005`. An incumbent-table pin at that same tolerance would **fail today** on
these three entries.

**F6 — WHICH ROWS OF THE TABLE REACH A SOLVE ON THIS KEEPER.** Read from the keeper's committed
`results/calibration/miso243_sppair_K/run_config.json`: `miso_seam_measured_ladder=True`,
`miso_seam_neighbour_anchored_ladder=True`, `miso_seam_neighbour_hourly_ladder=True`,
`miso_seam_neighbour_hourly_spp=True`. `interchange/miso.py::inject_miso_seam_ladder_prices`
overlays the PJM hourly ladder and then the SPP hourly ladder **on top of** the incumbent table
(`ladder = {**ladder, **hourly}`, then `{**ladder, **spp_rows}`), as alternatives that **displace**,
never stack. **So only the `South` and `Manitoba` rows of `MISO_SEAM_LADDER_BY_YEAR` are priced into
this keeper's LP.** The PJM 2023 cent is therefore **INERT on this keeper** and only the two South
cents (2023, 2024) can reach a solve — the handoff's claim, verified here independently from the
committed config and the injection code.

**F7 — GIT ARCHAEOLOGY IS NOT AVAILABLE FOR THIS QUESTION, AND THIS SESSION DOES NOT LEAN ON IT.**
CLAUDE.md records that the 2026-08-16 history rewrite stripped superseded blobs and force-pushed, so
*"every pre-2026-08-16 commit-sha citation outside `docs/governance/citation-commit-map.txt` is now a
dead (or, for short prefixes, possibly WRONG) reference."* `git log -- <path>` on the derive script,
on `spec.py`'s table region and on all three source parquets returns only post-rewrite merge
commits. **The diagnosis below is therefore built entirely on measurement, not on history.**

**F8 — THE G-DRIFT BASELINE.** The keeper's `run_config.json` records `git.sha = 710d4dad`, which is
**not a valid object in this clone** (`git cat-file -t` → MISSING) — miso-243's branch was rebased
after the solve. The merged equivalent **`5b5fb538`** ("miso-243: repair the SPP ladder's cross-year
pairing; 2024 screen clears all four gates") **is** an ancestor of `origin/main`
(`git merge-base --is-ancestor` → true, verified after `git fetch origin main`) and is the baseline
this session uses if it ever needs one.

---

## 1. WHAT IS GATED AND WHAT IS REPORTED — declared here, honoured afterwards

**GATED** (a failure stops the session and is published first, at full magnitude): the five
provenance legs **G-P2 / G-SPP / G-POOL / G-DOC / G-ROW** (§2.1), the identity leg **I-1** (§2.2),
the verdict statistic **`t_max`** and the verdict rule (§2.3), and — only on a `NOT-A-TIE` verdict —
the liveness gate **L** (§3).

**REPORTED, NEVER GATED**: the exact `(year, seam, side, band)` location of every mismatch (**D-3**);
the no-wash clamp census (**D-4**); the alternative-clamp reconstruction (**D-5**); the tie-mechanism
decomposition (**D-1′**); the exact-cent recompute (**D-1″**, whose falsification duty is stated in
§2.4); the `da` dtype; F6's liveness scope; every band value; and every criterion value of the
keeper. **No scored criterion, no residual and no band comparison appears in any bar.**

**BASIS, named on every statement (the discipline the handoff carries from miso-234).** The
incumbent ladder's coupling anchor is the measured Indiana-hub **DA** (`da`). The `ok`/row set is
the derive's own `dropna` over `da` + the three registry seam columns (Manitoba derives independently
on its own `da`+MHEB rows). The SPP anchor, where it appears, is the measured **SPP NORTH hub DA**.
The model basis, where it appears, is the keeper's committed `MISO_external` P1 price. They are
never interchanged, and miso-232's measured decile column (+1,303 / +1,384 / +948) is **not**
restated as reproduced by anything here.

---

## 2. PHASE 0 — the legs, the bars, and the verdict rule. **All zero-LP**

### 2.1 THE PROVENANCE GATE — five legs, reference values restated as LITERALS in the probe

The probe hard-codes every reference value below, so it runs and adjudicates **even if the
predecessor's artifact is missing** (the handoff's explicit requirement). Each leg reproduces a
predecessor quantity **in the predecessor's own metric, reading its estimator rather than its
label**.

| leg | what it reproduces | bar |
|---|---|---|
| **G-P2** | miso-243's P-2 per-seam `max\|committed − derive(HEAD)\|` table (F2), all 12 cells | **exact at 2 dp** |
| **G-SPP** | the committed `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR` reproduces from HEAD's repaired derive (miso-243 §3a leg 2), all 48 entries | **exactly 0.0** |
| **G-POOL** | the committed `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_POOLED` reproduces (miso-243 G-V5), all 16 entries | **exactly 0.0** |
| **G-DOC** | the derive's own docstring `corr(measured SPP flow, MISO DA − SPP hub DA)` = **+0.041 / −0.020 / +0.050** | **≤ 0.002** |
| **G-ROW** | `load_joined().loc[[y]]` is **8,760** rows/year; the SPP hub join preserves the row count; and the registry non-NaN row set `n(R_D)` = **8,754 / 8,757 / 8,757** (miso-243 P-1's own `n_rows_R_D`) | **exact** |
| **G-RAW** *(instrument validity)* | this probe's own **raw** replication of `_derive_one` (reading the estimator, not the label: the same `qq_import`/`qq_export`, the same midpoint grid, the same `min(imp) − NO_WASH_EPS` clamp, the same per-seam row sets) must satisfy `round(raw, 2) == derive()` for **all 192 entries** | **exact at 2 dp** |

**G-RAW is this session's own falsifiable leg** — the whole verdict of §2.3 is computed on `raw`, so if this probe's raw capture is not the derive's own pre-rounding value, `t_max` means nothing and the session stops there and says so.

**A failed provenance leg means this session's instrument does not reproduce the record it is
diagnosing, and the session publishes that failure FIRST and at full magnitude before anything
else** — the miso-243 §0a template. **No bar here may be moved to pass; a repair must be declared in
a pushed addendum before the repaired numbers exist and must be STRICTER.**

### 2.2 **I-1 — THE IDENTITY LEG, AND IT CAN KILL THIS SESSION'S FRAMING**

The estimator asserts an identity: band `k`'s import price is the DA quantile whose exceedance
duration equals the measured duration of the seam flowing deeper than `mid_k`, and the export side
mirrors it. Tested **on the COMMITTED incumbent table** (not on the derive's own output, where it
would be trivially true), for all 4 seams × 3 years × 8 bands × 2 sides, on each seam's own row set:

> **import**: the target `P(flow > mid_k)` must lie in `[P(da > c_k) − 0.002, P(da ≥ c_k) + 0.002]`
> **export**: the target `P(flow < −mid_k)` must lie in `[P(da < c_k) − 0.002, P(da ≤ c_k) + 0.002]`

The two-sided `>` / `≥` form is used because prices tie at the cent and several bands saturate at
`min(da)` / `max(da)`; the ±0.002 absorbs the 2-dp rounding of `c_k` and the `1/n ≈ 1.1e-4`
granularity. **If this fails broadly, the committed table did not come from this construction on
this row set, and §2.3's entire interpretation is void** — that outcome would be the session's
result, published as such.

### 2.3 **THE VERDICT — one statistic, one rule, fixed here**

For every one of the 192 entries let `raw` be the **unrounded** value `_derive_one` computes at
HEAD (captured before its terminal `round(p, 2)`, including any no-wash clamp), `c` the committed
value, and `e = raw − c`. An entry **mismatches** iff `round(raw, 2) ≠ c`.

> **`t = |e| − 0.005`** for each mismatching entry, and **`t_max = max t`**.

`t` is the distance of the current estimate **past** the half-cent boundary that separates the two
cents. It is the only quantity that can distinguish the two live explanations, because a mismatch
means `|e| > 0.005` by definition and the question is *by how much*.

> **V-ARTIFACT** iff **`t_max ≤ 1e-4`** — every mismatching entry's current estimate sits on the
> half-cent boundary to within **one hundredth of a cent**. Then the committed cent and the HEAD
> cent are **both correct roundings of the same estimate**, separated only by a tie, and the gap is
> a **ROUNDING ARTIFACT**.
>
> **V-NOT-A-TIE** iff **`t_max > 1e-4`** — the committed value is **not** a rounding of the current
> estimate. Sub-classified, reported not gated, by D-4/D-5: **CLAMP-TRANSCRIPTION** if every
> mismatching entry is a no-wash-clamped export band whose committed value is reproduced by
> `round(min(round(imp, 2)) − NO_WASH_EPS, 2)` (the clamp taken off the ROUNDED imports);
> **UNEXPLAINED** otherwise.

**Why `1e-4`.** It is **50× smaller** than the half-cent the verdict turns on, so a genuine movement
of even 2 % of a cent is caught; and it is **≥ 10× larger** than the float32 round-trip scale F4
measures over this price range, so representation noise cannot manufacture a `NOT-A-TIE`. The bar
is set from those two magnitudes and from nothing else — **no residual, no criterion and no band
comparison enters it.**

### 2.4 **D-1″ — THE PREDICTION THIS SESSION MAKES BEFORE MEASURING, AND THE FALSIFICATION IT OWES**

F4 implies a specific cause. **The prediction, stated before the number exists:** *if the verdict is
V-ARTIFACT, then re-running the identical derive with the `da` series snapped to exact cents in
float64 (`np.round(da, 2)`, which is what a published LMP actually is) reproduces the committed
table at **exactly 0.00 on all 192 entries**.*

**This is the ONLY alternative construction this session will try, it is named here before any
result, and it CANNOT MOVE THE VERDICT** — §2.3's rule is the verdict. If V-ARTIFACT holds and
D-1″ does **not** reproduce, this session **publishes that its cause story failed** and reports the
verdict as **ARTIFACT, CAUSE UNIDENTIFIED**. No second transformation is tried; searching
transformations until one reproduces would be the fitted-mechanism selection rule 1 `[R-STRUCT]`
forbids, applied to a derive instead of a solve.

### 2.5 REPORTED-ONLY measurements (§1)

**D-3** the exact `(year, seam, side, band)` of every mismatch, with `raw`, `c` and `e` — new
information the record does not yet carry. **D-4** HEAD's `derive()` `notes` per year (the derive
docstring and `spec.py`'s own comment both assert the no-wash ordering *"holds naturally in all
years"*; a clamp note would contradict the committed documentation and is a finding either way).
**D-5** the alternative-clamp reconstruction. **D-1′** for each mismatch, the two source prices the
quantile interpolates between and the interpolation weight — a tie shows as a landing exactly on a
half-cent. **D-6** the `da` column dtype as stored.

---

## 3. DISPOSITION — fixed here, so that STOP is a pre-registered outcome rather than a retreat

**On V-ARTIFACT** (either sub-case): **THE DIAGNOSIS IS THE SESSION'S RESULT. ZERO LP.** No
re-derive is proposed, no table is edited, no mechanism is armed, no cell verdict moves, and **no
solve is authorized.** A rounding tie is not a construction defect: both cents are correct
roundings of the same measured estimate, and re-deriving to move `$0.01` on a band would be a
change with **no measured object behind it**. The deliverable is the FINDING plus the named,
**un-acted** successor of §4.

**On V-NOT-A-TIE**: a rule-23 `[R-FROZEN-DERIVE]` re-derive becomes a **candidate** — never an
action taken in the same breath as the diagnosis (the handoff's explicit order). It must first clear
the liveness gate below, and **no LP is authorized unless it does.**

> **L — LIVENESS, STOP-only, zero-LP, computed on the KEEPER'S COMMITTED SIDECAR.** For each year,
> replace the **live** seams' incumbent bands (F6: `South`, `Manitoba`) with their HEAD-derived
> counterparts and measure, on the model basis (the keeper's committed `MISO_external` P1 price from
> `hourly/system_<year>.parquet`):
> * **`L`** = the share of the year's hours whose South band-count vector `(n_i, n_e)` changes;
> * **`Δq̂` = 375 MW × (Δn̄_i − Δn̄_e)`** (South's own step, `3000 / 8`), the pre-solve mean-flow
>   prediction, in the identical form miso-243's P-4 used.
>
> **If `max_year L ≤ 0.001` AND `max_year |Δq̂| ≤ 5 MW`, the correction is measured INERT and NO
> SCREEN SOLVE IS AUTHORIZED** — rule 29 `[R-SCREEN]`'s own inert-mechanism clause — and the session
> publishes the diagnosis and stops.
>
> Both are **footprint** measures computed from two ladders and one committed price series, with
> **zero scored criterion, zero band comparison and zero residual in them**. A gate that read *"did
> C3a improve"* is the fitted-mechanism selection rule 1 forbids; this session does not run one.

**If L does not stop it**, the session proceeds to rule 29's ladder in full — a G-DRIFT audit from
**`5b5fb538`** (F8) classifying **every** hunk over `src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`, with
any **shared data seam MEASURED rather than classified from its gate**; a **ONE-year** screen whose
year is named by `L` (`argmax_year L`, ties to the earliest — **fixed here, before `L` exists**, and
**if `L` names a year other than the one this session expects, `L` wins**); four pre-registered
STRUCTURAL STOP-only gates declared in a pushed addendum **before the screen runs**; and the full
span in **ONE** `--year 2023 2024 2025` invocation and **ONE** bundle only if the screen clears
(rules 12 / 16 / 29).

**Under every branch:** rule 31 `[R-RETAIN]` — nothing solved is deleted; any bundle produced is
`.gitignore`d, kept on local disk, and the promotion question is surfaced explicitly in the final
report with the statement that it will not survive the session.

---

## 4. What this session hands forward regardless of verdict

1. **THE MISSING RULE-23 REPRODUCTION PIN (F5).** The incumbent table is the ONLY MISO seam ladder
   with no test that re-runs its derive and compares. This is named here as a successor; whether it
   is added in this session depends on the verdict, because a pin written at `atol=0.005` against a
   table separated from its derive by a rounding **tie** would be a flapping test, and the right
   construction of such a pin is part of what the diagnosis decides.
2. **THE STRUCTURAL ITEM RULE 1 NAMES IS UNTOUCHED** and this session does not close it: the model's
   SPP seam is 0.70–0.79 spread-correlated while the measured one is +0.0409 / −0.0200 / +0.0502.
3. **C3c REMAINS THE DESIGNATED FRONTIER** (MISO model 3 / 7 / 11 h > $200 vs measured 30 / 37 / 88).
   It opens only by a new admissible measured identification under its own charter **plus an owner
   ruling**. **None is proposed, computed or armed here.**
4. **UNCHANGED AND NOT RE-TESTED** (miso-235…243, and this session re-opens none of them): the SPP
   quantity-side charter stays **REFUSED — no DOF-free form** (miso-241 §5, C1–C7, census DONE);
   queue item 1 stays **ANSWERED AND DECOMPOSED**; the merit test's sign and basis stay **REFUTED**;
   the PJM/SPP idle contrast stays a **measured-record** fact; the external-bus-price identification
   half stays **CLOSED**; per-seam external-node split **REFUSED at zero LP**; saturation
   **REFUTED**; miso-239 Q-A **MIXED** / Q-C **SURVIVES**; the `(month × hod)` template hypothesis
   **REMOVED**; the PJM import/export asymmetry **CLOSED FOR PJM**; South's neighbour-state route
   **CLOSED**; `miso_manitoba_seam` **CLOSED as already-armed**; `internal_congestion_split` **G**;
   `vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
   `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap` **G**;
   `miso_south_firm_export_block` **G**; `miso_south_export_ladder_rt_tail` **R**;
   `miso_south_gas_delivered_cost_basis` **R**.
5. **SOUTH stays excluded from the hourly form** and that stays a **DATA boundary**: SOCO and TVA
   publish no hub price.

## 5. Non-claims, fixed here

1. **No mechanism is proposed by this document.** No `ScenarioConfig` field is created or changed,
   and the DOF ledger stays **41/2** unless a later, separately pre-registered step changes it.
2. **Every number this session produces is UN-TARGETABLE**: nothing is tuned, selected or reconciled
   to a predecessor's published value, and where a value agrees with one it is disclosed as
   **expected** (a deterministic estimator run twice on the same series) rather than presented as
   independent corroboration.
3. **No out-of-training year will be solved, scored or registered**, and no marker is sought.
4. **MISO has no failing gate**, this session does not invent one, and nothing here trades a passing
   gate for anything.
5. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage.** No 2025 C1 pass is read as
   evidence anywhere in this session.
