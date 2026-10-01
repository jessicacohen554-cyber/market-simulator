# PREREG miso-245 — **ATTRIBUTE THE DRIFT IN `MISO_SEAM_LADDER_BY_YEAR`.** The one-line test miso-244 was barred from running, pre-registered cleanly. Zero LP

**Queue item taken (rule 28(a)): the handoff's RECOMMENDED item** — miso-244 §7.1's named successor,
handed forward with its hypothesis, its decision rule and its three integer coordinates already
fixed. This document pre-registers that test **and scopes every pre-commitment to its branch**, which
is the one thing miso-244's own §2.4 failed to do (its FINDING §0c records the defect against
interest).

**Keeper at session start: `2026-09-07-miso-243-spp-pairing`** (bundle
`results/calibration/miso243_sppair_K`), DETERMINATION **CALIBRATED**, C3c the single ledgered
non-downgrading caveat, DOF ledger **41/2**. Rule 22 `[R-HOLDOUT]`: **2023–2025 only**; MISO holds no
`complete` marker and **no out-of-training year will be solved, scored or registered.** MISO carries
exactly **one** registered run (rule 15) and will still carry exactly one when this session ends,
unless the A-CONFIRMED branch of §4 runs to a promoted keeper.

**THERE IS NO RUBRIC FAILURE IN MISO.** All six ISO keepers score CALIBRATED. This session does not
invent one, does not target C3c, and proposes no offer adder, ORDC offset, scarcity multiplier or any
level tuned to a residual.

**This document is pushed BEFORE any adjudicating quantity is computed, together with the probe that
computes them** (`scripts/probes/_miso245_ladder_drift_attribution_phase0.py`). Every decision rule,
bar and disposition below is fixed here; none may be written after seeing a number.

---

## 0. The facts this rests on — all established by miso-244 and NOT re-measured here

No adjudicating quantity appears in §0. Every item is a settled predecessor result, a code reading or
a committed-artifact reading, and each is cited. **This session re-measures none of them**; it
reproduces the ones its own instrument depends on as literal-valued provenance legs (§2.1).

**F1 — THE OBJECT AND ITS VERDICT.** `MISO_SEAM_LADDER_BY_YEAR`
(`src/market_sim/model/interchange/spec.py`) is the incumbent per-year MISO-hub-anchored Q-Q band
ladder: 3 years × 4 seams × 2 sides × 8 bands = **192 committed 2-dp entries**. miso-244 established
on a rule fixed before any number existed that the gap between it and `derive()` at HEAD is
**`V-NOT-A-TIE`**: `t_max` = **0.0049998** against a **1e-4** tie bar, a miss by a factor of 50. The
tie sub-class and the no-wash-clamp sub-class are both **REFUTED**
(`FINDING-miso244-the-cent-is-real-drift-and-the-re-derive-is-refused-2026-09-08.md` §§0b, 2).
**Not re-run here.**

**F2 — THE THREE ENTRIES, located by miso-244** (`_miso244_incumbent_ladder_cent_phase0.json`,
`reported.D3_mismatch_locations`):

| # | year | seam | side | band | committed | raw at HEAD | rounds to | `t` | live on the keeper? |
|---|---|---|---|---|---:|---:|---:|---:|---|
| 1 | 2023 | PJM | import | 5 | 27.86 | 27.8661822587 | 27.87 | 0.00118 | **no** — displaced by the hourly overlay |
| 2 | 2023 | South | export | 4 | 27.69 | 27.6962803582 | 27.70 | 0.00128 | **yes** |
| 3 | 2024 | South | export | 5 | 23.77 | 23.7600002289 | 23.76 | **0.00500** | **yes** |

Directions are **MIXED**. **Not re-derived here** — restated as literals and reproduced by G-LOC.

**F3 — THE ESTIMATOR, read from source** (`scripts/data/derive_miso_seam_ladders.py`), unchanged and
untouched by this session:

```python
imp_k = np.quantile(da, 1.0 - (flow >  mid_k).mean())     # qq_import
exp_k = np.quantile(da,       (flow < -mid_k).mean())     # qq_export
lim   = min(imp) - NO_WASH_EPS                            # same-seam no-wash, off UNROUNDED imports
exp[k] = lim if exp[k] > lim else exp[k]
return [round(p, 2) for p in imp], [round(p, 2) for p in exp]
```

`np.quantile` defaults to `method="linear"`: the estimate sits at `h = q·(n−1)` and interpolates the
two adjacent order statistics.

**F4 — THE ESTIMATOR FAMILY IS ALREADY ELIMINATED** (miso-244 §3, arithmetic on its own recorded
interpolation, **not re-derived here**): entries 1 and 2 both require the **lower** order statistic
(`frac` 0.618 / 0.628, `x_lo`/`x_hi` exactly one cent apart, committed `= round(x_lo, 2)`), while
entry 3 **refutes** `lower` — there `x_lo == x_hi == 23.760000` , a degenerate position where all
five members of numpy's `h = q·(n−1)` family return `23.76` against a committed `23.77`. **No uniform
change of estimator explains both.** What remains is that the **sample** differs.

**F5 — THE THREE INTEGER COORDINATES.** The quantile's `q` recorded in miso-244's D-1′ resolves to an
integer duration count on an `n = 8,760` row set — `q = 1 − c/n` on the import side, `q = c/n` on the
export side:

| # | `n` | `q` (miso-244 D-1′) | recovered count `c` |
|---|---:|---:|---:|
| 1 | 8760 | 0.3818493150684932 | **5,415** |
| 2 | 8760 | 0.37203196347031964 | **3,259** |
| 3 | 8760 | 0.34748858447488584 | **3,044** |

Recovery is arithmetic, and **G-COUNT (§2.1) gates it** rather than assuming it.

**F6 — THE FINGERPRINT IS PERISHABLE, AND THAT FIXES THE ORDER OF WORK.** Every other ladder derived
on the same series reproduces at **exactly 0.0** — the per-year SPP hourly offsets, the pooled forward
SPP ladder, and miso-243's PJM annual and PJM hourly ladders. The incumbent table is the **last
surviving copy of its own derivation vintage** (miso-244 §3). **No re-derive is performed before the
attribution verdict**, in either branch, and under A-REFUTED none is performed at all.

**F7 — THE GUARD IN PLACE.**
`tests/iso/miso/test_miso_seam_ladder.py::TestLadderRegistry::test_incumbent_registry_reproduces_the_frozen_derivation`
pins all 192 entries at `atol=0.005` except the three of F2, pinned **harder** at both exact values in
`_MISO244_KNOWN_LADDER_DIVERGENCES`. **This session never widens that tolerance.** Those entries are
DELETED (rule 26 `[R-DELETE]`) if and only if the table is reconciled, which happens only under the
A-CONFIRMED branch of §4.

**F8 — THE G-DRIFT BASELINE.** The keeper's `run_config.json` records `git.sha = 710d4dad`, which is
**not a valid object in this clone** (re-verified: `git cat-file -t` → MISSING). The merged
equivalent **`5b5fb538`** is an ancestor of `origin/main` (re-verified with
`git merge-base --is-ancestor`), and so is **`a667073f`**, which miso-244 audited to. **This session
audits `a667073f..HEAD` only** — the range miso-244 did not cover — and re-runs `surface_stamp`.

---

## 1. WHAT IS GATED AND WHAT IS REPORTED — declared here, honoured afterwards

**GATED** (a failure stops the session and is published FIRST, at full magnitude): the instrument and
provenance legs **G-RAW / G-QUANT / G-COUNT / G-REPRO / G-LOC / G-DIR** (§2.1), and **the attribution
statistic `M` with its rule** (§2.2). Under the A-CONFIRMED branch only, **G-DRIFT** (§4) additionally
gates whether the keeper's committed bundle may serve as the control, and the four screen gates
declared in a pushed addendum gate the screen.

**REPORTED, NEVER GATED**: every per-entry `m_j` and its signed `Δ` at full magnitude; the flip-distance
`f_j` for all 192 entries and the three mismatches' rank and separation within it; the degenerate-run
census behind entry 3; whether the no-wash clamp binds anywhere under perturbation; the price-side
counterpart of `m_j` (a **restatement** of miso-244's already-published `t_j`, explicitly not a new
measurement); the P-1 source-data provenance reading (§2.4); and every band and criterion value of the
keeper. **No scored criterion, no residual and no band comparison appears in any bar.**

**BASIS, named on every statement** (the discipline the handoff carries from miso-234). The incumbent
ladder's coupling anchor is the measured Indiana-hub **DA** (`actual_lmp_hourly_MISO.parquet` `da`,
stored **float32**); the row sets are the derive's own per-seam `dropna`. Where the SPP anchor appears
it is the measured **SPP NORTH hub DA**. Where the model basis appears it is the keeper's committed
**P1** bus price, and the South bands are hosted on **`MISO_external_South`**, not `MISO_external`
(`miso_south_seam_split` armed on the keeper; miso-244 §0d). They are never interchanged, and
miso-232's measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by
anything here.

---

## 2. PHASE 0 — the legs, the statistic and the rule. **All zero-LP**

### 2.1 THE PROVENANCE + INSTRUMENT GATE — six legs, every reference value a LITERAL in the probe

The probe hard-codes every reference value below, so it runs and adjudicates **even if the
predecessor's artifact is missing** (the handoff's explicit requirement). Each leg reads a
predecessor's **estimator**, not its label.

| leg | what it asserts | bar |
|---|---|---|
| **G-RAW** | this probe's own replication of `_derive_one` satisfies `round(raw, 2) == derive()` for all **192** entries | exact at 2 dp |
| **G-QUANT** | this probe's vectorised linear-interpolation quantile reproduces `np.quantile(da, q)` at `Δ = 0` for all **192** entries | ≤ **1e-12** |
| **G-COUNT** | for all 192 entries the measured duration share × `n` is an integer, **and** the three mismatching entries' recovered counts are exactly **5,415 / 3,259 / 3,044** (F5) | ≤ **1e-6** from integer; counts exact |
| **G-REPRO** | the probe reproduces miso-244's published D-1′ record for the three entries — `n`, `q`, `lo_index`, `frac`, `x_lo`, `x_hi`, `value` | ≤ **1e-9** each |
| **G-LOC** | **exactly three** entries mismatch, at exactly the F2 coordinates, with the F2 committed and `round(raw,2)` values | exact |
| **G-DIR** | each entry's reaching perturbation carries the sign quantile monotonicity requires — **#1 `Δ > 0`** (import, `raw > committed`), **#2 `Δ < 0`** (export, `raw > committed`), **#3 `Δ > 0`** (export, `raw < committed`) | exact, where `m_j` is finite |

**G-QUANT and G-COUNT are this session's own falsifiable legs.** The whole statistic is computed on a
hand-vectorised quantile evaluated at a reconstructed integer count; if either is not the estimator's
own object, `M` means nothing and the session stops there and says so. **G-DIR is an instrument leg,
not evidence** — it restates quantile monotonicity, and a violation means this session's arithmetic is
wrong, never that the hypothesis is interesting.

**A failed leg means this session's instrument does not reproduce the record it is diagnosing, and
the session publishes that failure FIRST and at full magnitude before anything else.** **No bar here
may be moved to pass; a repair must be declared in a pushed addendum before the repaired numbers exist
and must be STRICTER.**

### 2.2 **THE ATTRIBUTION STATISTIC AND ITS RULE — fixed here, before any number exists**

**The hypothesis, as miso-244 §7.1 handed it forward, verbatim in substance:** *if the committed table
came from this estimator on a marginally different SAMPLE, each mismatching entry's committed value is
reachable by perturbing THAT ENTRY'S OWN integer exceedance/depth COUNT by at most ±1 hour out of
8,760, holding estimator and price series fixed. A single entry needing more REFUTES it.*

Operationalised, with **exactly one integer knob moved and everything else held fixed** — the same
`da` row set, the same sorted order statistics, the same midpoint-depth grid, the same no-wash clamp
`lim` computed on the **unperturbed** import list, and every other one of the 192 entries untouched:

> For entry `j` with recovered count `c_j` on `n_j` hours and `Q(·)` the identical
> `np.quantile(da_j, ·, method="linear")`:
>
> `v_j(Δ) = Q(1 − (c_j+Δ)/n_j)` on the **import** side, `v_j(Δ) = Q((c_j+Δ)/n_j)` on the **export**
> side, the export side then passed through the estimator's own clamp (`lim` if the value exceeds it).
>
> **`m_j = min { |Δ| : Δ ∈ ℤ, 0 ≤ c_j+Δ ≤ n_j, round(v_j(Δ), 2) = committed_j }`**, and `m_j = +∞`
> if no such `Δ` exists.
>
> **`M = max_j m_j`** over the three mismatching entries.

> **`A-CONFIRMED` iff `M ≤ 1`.** **`A-REFUTED` iff `M ≥ 2`** — an infeasible `m_j` counts as `+∞`.

**Why the bar is ±1 and why it is not moved.** It is the handed-forward rule, and it is the **minimal**
possible perturbation of an integer count, so it is a **strict** operationalisation by construction.
That strictness is declared here rather than discovered later: see §2.3.

### 2.3 **THE SCOPE OF THE TEST, STATED BEFORE IT RUNS — this is not a post-hoc softening**

* **`A-CONFIRMED` attributes the cause** to a minimal difference in the measured flow sample. That is
  a **source-data** difference, which is exactly what rule 23 `[R-FROZEN-DERIVE]` requires a
  re-derivation commit to cite, so a re-derive becomes admissible **with this measurement as the
  citation** — and only then.
* **`A-REFUTED` refutes that specific minimal form and NOTHING WIDER.** It does **not** refute "the
  sample moved": a larger flow revision, or a revision on the **price** side, would both survive it.
  Under A-REFUTED the object is bigger than a sample nudge, the successor is the **source-data
  provenance** of `data/raw/eia-930-interchange/MISO interchange hourly.parquet` and
  `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`, and **the session says so and stops**
  — which the handoff pre-declares to be a complete session result at zero LP.
* **THIS CLAUSE BINDS UNDER `A-REFUTED` ONLY** *(scoped to its branch — the drafting lesson miso-244
  §0c recorded against interest)*: **no second transformation is tried.** This session will not re-run
  the derive under a different quantile convention, a larger perturbation, a perturbed price series or
  a re-fetched vintage until the committed table reappears. Searching transformations until one
  reproduces is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, applied to a derive instead
  of a solve. **Under `A-CONFIRMED` the clause does not bind and §4's ladder proceeds.**

### 2.4 REPORTED-ONLY measurements, declared here (§1)

* **R-1** each `m_j` and its signed `Δ_j`, at full magnitude, whatever they are.
* **R-2 the flip distance `f_j` for ALL 192 entries** — the minimal `|Δ|` that changes an entry's
  rounded cent at all, the same construction applied to matching entries. Reported: the three
  mismatches' `f_j`, their **rank** among 192, and the separation `max_{mismatch} f` vs
  `min_{match} f`. **Its only admissible reading is descriptive** — whether the three drifted entries
  are also the most rounding-fragile at HEAD, which is what a small sample perturbation would predict.
  **It cannot move the verdict in either direction and is never used to argue past the ±1 bar.**
* **R-3** the degenerate-run census behind entry 3: how many hours of the 2024 `da` row set sit at
  exactly `x_lo`, which is the arithmetic reason `m_3` is whatever it is.
* **R-4** whether the no-wash clamp binds anywhere under perturbation (miso-244 D-4 measured **zero**
  clamp notes in any year at `Δ = 0`).
* **R-5 the price-side counterpart, DISCLOSED AS A RESTATEMENT AND NOT A MEASUREMENT.** The price
  perturbation the committed cent needs is exactly miso-244's already-published `t_j` — **0.00118 /
  0.00128 / 0.00500 $/MWh** at the relevant order statistics. It is reported beside `m_j` so the
  count-side and price-side magnitudes are read together; **it is arithmetic on a published number,
  it is not new evidence, and it adjudicates nothing.**
* **P-1 SOURCE-DATA PROVENANCE READING**, run under **both** branches: the on-disk vintage record of
  the two source parquets — their corpus `README.md` and `SHA256SUMS.txt` where one exists, their
  row counts, year spans and column dtypes, and whether `git log` carries any non-merge commit
  touching them. **REPORTED-ONLY, with NO decision rule attached**: it is a read of the record, it
  **cannot** license a re-derive by itself, and it is the handle the A-REFUTED successor starts from.
  *(F7 of the miso-244 PREREG stands: the 2026-08-16 history rewrite makes sha archaeology
  unreliable, and nothing here leans on it.)*

---

## 3. DISPOSITION UNDER `A-REFUTED` — fixed here, so that STOP is a pre-registered outcome

**THE DIAGNOSIS IS THE SESSION'S RESULT. ZERO LP.** No re-derive is performed, no committed table is
edited, no mechanism is armed, no `ScenarioConfig` field is created or changed, no cell verdict moves,
the DOF ledger stays **41/2**, the keeper stays `2026-09-07-miso-243-spp-pairing`, and **no solve is
authorized.** The F7 pin stays exactly as it is — **never widened, and its known-divergence entries
are NOT deleted**, because deletion is conditioned on reconciliation and no reconciliation occurs.
The deliverables are the FINDING, the probe and its JSON, the P-1 provenance reading, and the named
successor.

## 4. DISPOSITION UNDER `A-CONFIRMED` — rule 29 `[R-SCREEN]` in full, and every step fixed here

1. **THE RE-DERIVE, with its citation.** `MISO_SEAM_LADDER_BY_YEAR`'s three drifted entries are
   reconciled to `derive()` at HEAD — **and nothing else in the table moves**, which is itself checked
   (the other 189 entries must be byte-identical). The commit cites this session's attribution
   measurement as the data change rule 23 requires. The F7 pin's `_MISO244_KNOWN_LADDER_DIVERGENCES`
   entries are **DELETED** (rule 26 `[R-DELETE]`), never absorbed into a wider tolerance, and the pin
   must then pass at `atol=0.005` on all 192 with no exceptions.
2. **G-DRIFT, `a667073f..HEAD`** (F8) — every hunk on the backcast solve path classified INERT with
   its reason cited or LIVE, over `src/market_sim scripts/run_calibration.py
   scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`, with
   **any shared data seam MEASURED rather than classified from its gate**, plus
   `surface_stamp("MISO", keeper_config)` re-run. **All INERT ⇒ form 4 holds and the keeper's
   committed bundle is the control; a LIVE hunk is the only thing that earns a control solve.**
3. **A ONE-YEAR SCREEN ON 2024.** The screen year is **named here, before anything runs**, by the
   mechanism's own measured footprint and never by a residual: `argmax_year L` over miso-244's
   published liveness table (`L` = 0.00000 / **0.00982** / 0.00000 on `MISO_external_South`), ties to
   the earliest ⇒ **2024**, with `Δq̂` = **+3.682 MW**. **If a re-measured footprint names a different
   year, the footprint wins, not this sentence.**
4. **FOUR STRUCTURAL STOP-ONLY GATES, declared in a pushed ADDENDUM BEFORE the screen runs.** They ask
   whether the correction does what its own arithmetic says — direction and order of magnitude of the
   dispatch response, footprint confined to the rows the correction touches, the identity it asserts,
   and no non-target load-bearing criterion flipping PASS → FAIL. **None of them is the target
   residual**, and they may kill the arm but can never promote it.
5. **THE FULL SPAN ONLY IF THE SCREEN CLEARS**, as ONE `--year 2023 2024 2025` invocation and ONE
   bundle (rules 12 / 16 / 29), years sequential, `replay_keeper.py` off the keeper's bundle, with the
   attestation carried forward and re-stamped so C6 does not read UNATTESTED.
6. **Rule 31 `[R-RETAIN]`** throughout: nothing solved is deleted. Any bundle produced is
   `.gitignore`d and moved outside `results/calibration/` (or given a leading underscore) so the parity
   sweep stays green, is **kept on local disk**, and **the promotion question is surfaced explicitly in
   the final report** with the statement that it will not survive the session.

---

## 5. What this session hands forward regardless of branch

1. **THE ATTRIBUTION VERDICT AND ITS MAGNITUDE** — `M` at full magnitude, plus the per-entry `m_j`, so
   a successor knows not just whether ±1 works but how far the object actually sits from it.
2. **THE FINGERPRINT PROTECTION HOLDS** unless the table is reconciled: F7's pin is never widened, and
   under A-REFUTED it is not touched at all.
3. **THE STRUCTURAL ITEM RULE 1 NAMES IS UNTOUCHED** and this session does not close it: the model's
   SPP seam is 0.70–0.79 spread-correlated while the measured one is +0.0409 / −0.0200 / +0.0502. The
   seam being idle is not the anomaly; its being spread-driven is.
4. **C3c REMAINS THE DESIGNATED FRONTIER** (MISO model 3 / 7 / 11 h > $200 vs measured 30 / 37 / 88).
   It opens only by a new admissible measured identification under its own charter **plus an owner
   ruling** — never by an offer adder, ORDC offset, scarcity multiplier or any level tuned to the tail.
   **None is proposed, computed or armed here.**
5. **UNCHANGED AND NOT RE-TESTED** (miso-235…244, and this session re-opens none of them): the one-cent
   gap's verdict stays **`V-NOT-A-TIE`** and its clamp/tie sub-classes stay **REFUTED**; the SPP
   quantity-side charter stays **REFUSED — no DOF-free form** (miso-241 §5, C1–C7, census DONE); queue
   item 1 stays **ANSWERED AND DECOMPOSED**; the merit test's sign and basis stay **REFUTED**; the
   PJM/SPP idle contrast stays a **measured-record** fact; the external-bus-price identification half
   stays **CLOSED**; per-seam external-node split **REFUSED at zero LP**; saturation **REFUTED**;
   miso-239 Q-A **MIXED** / Q-C **SURVIVES**; miso-240 Q-B **UNRESOLVED**; the `(month × hod)` template
   hypothesis **REMOVED**; the PJM import/export asymmetry **CLOSED FOR PJM**; South's neighbour-state
   route **CLOSED**; `miso_manitoba_seam` **CLOSED as already-armed**; `internal_congestion_split` **G**;
   `vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
   `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap` **G**; `miso_south_firm_export_block`
   **G**; `miso_south_export_ladder_rt_tail` **R**; `miso_south_gas_delivered_cost_basis` **R**.
6. **SOUTH stays excluded from the hourly form** and that stays a **DATA boundary**: SOCO and TVA
   publish no hub price. The pooled forward SPP ladder stays untouched (rule 13 intact).

## 6. Non-claims, fixed here

1. **No mechanism is proposed by this document.** No `ScenarioConfig` field is created or changed in
   either branch, and the DOF ledger stays **41/2** in both — a reconciliation of three committed
   quantile values to their own frozen estimator adds **zero free parameters**.
2. **Every number this session produces is UN-TARGETABLE**: nothing is tuned, selected or reconciled to
   a predecessor's published value, and where a value agrees with one it is disclosed as **expected**
   (a deterministic estimator run twice on the same series) rather than presented as independent
   corroboration.
3. **No out-of-training year will be solved, scored or registered**, and no marker is sought.
4. **MISO has no failing gate**, this session does not invent one, and nothing here trades a passing
   gate for anything.
5. **2025 C1/C2 are SKIPPED on the preliminary EIA-923 vintage.** No 2025 C1 pass is read as evidence
   anywhere in this session.
