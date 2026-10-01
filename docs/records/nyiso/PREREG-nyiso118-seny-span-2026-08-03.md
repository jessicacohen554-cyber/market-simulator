# PRE-REGISTRATION — nyiso-118: arming `nyiso_ordc_measured_step_span` (the SENY demand-curve span fix)

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (rule 16 — one
bundle per arm) · **Keeper at session start:** `2026-08-03-nyiso-117-nyc-rcpf`
(CALIBRATED-WITH-CAVEATS, C3c the sole ledgered caveat, 3/0/14) · **Committed and
pushed BEFORE either solve.**

---

## §1 — what this session is, and what it is NOT

`nyiso_ordc_measured_step_span` is matrix cell **`U`** — implemented, never armed.
nyiso-117 screened it **ex ante with no solve spent** and recorded **S-OVER**
(`results/calibration/nyiso117_seny_rcpf_curve_screen.json`). **That measurement is
DONE and is NOT re-run here.** This session spends the solve the screen deliberately
did not.

**This session arms exactly ONE flag.** The screen also established that the model's
SENY *level/step structure* is wrong in a second, independent way (the published curve
is a $500 base **plus** a $40 increment; the model carries only the base, as a
`critical_mw=0` ramp). **That is a SECOND mechanism and is NOT touched here** — rule 19
`[R-ONE-MECH]` forbids folding it into the span flag. It would need its own
pre-registration and its own arm. §6 records why, and §7 binds it.

## §2 — arms

Both from the **designated keeper's** recipe over 2023, 2024, 2025 in one bundle each
(rule 16), launched concurrently (rule 12, 2-way cap):

| arm | bundle | delta |
|---|---|---|
| **CONTROL** | `results/calibration/nyiso118_control` | zero-delta replay of `nyiso117_nyc_stepcurve` at THIS session's HEAD |
| **TREATMENT** | `results/calibration/nyiso118_seny_span` | `--set nyiso_ordc_measured_step_span=true` |

**A same-HEAD control is MANDATORY.** Every attribution below is
**treatment-vs-control at one HEAD**, never treatment-vs-keeper. Provenance is
established by **comparing the dispatch**, never by inferring vintage from commit
ordering — `git merge-base --is-ancestor` exits **128** (`fatal: Not a valid object
name`) for an unfetched commit and the ordinary `cmd && yes || no` idiom silently maps
that to a plain negative (nyiso-117 §9).

## §3 — what the flag does, and the ONE live coupling, both settled EX ANTE on CONSTRUCTION

The flag scales each dynamic family's ORDC width vector by
`requirement[t] / requirement_static`, restoring the construction identity **total step
width == the hour's requirement**. The published RCPF penalties are
requirement-**independent**, so the widths are the only part of the curve carrying the
requirement.

**The coupling hazard, stated so it is not discovered late.** The LI locational ladder
(`nyiso_li_locational_reserve`, **ARMED on the keeper**) already applies this same span
translation **family-scoped and unconditionally** to `li_30min_total`, deliberately
without flipping the global flag. Arming the global flag must not **double-apply** it
to LI.

**DISCHARGED BEFORE THE SOLVE, on CONSTRUCTION.**
`scripts/probes/_nyiso118_span_construction_probe.py` →
`results/calibration/nyiso118_span_construction_probe.json` builds the NYISO
`ReserveDesign` **twice at one HEAD** on the keeper's reserve flags and diffs every
family's `requirement`, `ordc_penalties` and `ordc_step_widths`. **No LP is solved and
no dual is read** — because the question is about how the curve is BUILT, and `dual` /
`held_mw` are solved outputs of a co-optimization whose byte-identity can only pass when
the mechanism does nothing (the nyiso-115 G2 error, nyiso-117 PREREG §3.1).

Measured, all three years:

| family | widths | requirement | penalties | reachable price |
|---|---|---|---|---|
| `li_30min_total` | **IDENTICAL** | IDENTICAL | IDENTICAL | IDENTICAL |
| `nyc_10min_total`, `nyc_30min_total` | changed (185/227/120 h) | IDENTICAL | IDENTICAL | **IDENTICAL ($0.000)** |
| `seny_30min_total` | changed (6,239/6,249/6,231 h) | IDENTICAL | IDENTICAL | **CHANGED (max $437.50/$437.50/$375.00, 6,102/6,064/6,139 h)** |
| `east_10min_total`, `li_10min_total`, `nyca_10min_spin`, `nyca_10min_total`, `nyca_30min_total` | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL |

**The LI double-apply does not occur** — `li_30min_total` is byte-identical in all
three vectors. The guard is structural, not incidental: the code applies the scaling
under `if name in dynamic_req and (measured_step_span or name in span_scaled)`, and
`or` is boolean, not additive; LI's family-scoped entry has already normalized its
widths, so the global flag finds nothing left to scale.

**Two corrections to the record, both discovered by this probe and neither cosmetic:**

1. **The blast radius is THREE families, not one.** `_nyiso_design`'s docstring claims
   the flag is a "No-op wherever measured == static (NYCA, East, NYC)". **That is false
   for NYC**: NYC's measured requirement dips *below* its static base in 185/227/120
   hours (mean 490.8 vs 500 MW), so the flag narrows the NYC bands there. The docstring
   is corrected in this session's code commit.
2. **But NYC is not re-PRICED — only re-REPRESENTED.** Shortfall is bounded above by
   the hour's requirement (`held ≥ 0`), so band width beyond `requirement[t]` is
   unreachable padding. On the reachable domain `[0, requirement[t]]` the NYC price
   function is **pointwise identical** in both arms ($0.000 max delta, 0 hours, all
   three years) — because the frozen NYC step curve collapses that family to a **single
   flat band** at the published $25 RCPF, and trimming unreachable padding off a flat
   band cannot move a price. **The frozen NYC mechanism (rule 23) is therefore not
   disturbed**, and this session does not re-open, re-level or re-scope it.

This is also what proves the construction instrument **has discriminating power**: it
separates a re-priced family (SENY) from a merely re-represented one (NYC) from an
untouched one (LI). It is not a gate that can only pass by doing nothing.

## §4 — the EXPECTED PARTIAL, pre-registered as such

**The flag re-SPANS the curve; it does NOT change the $500 penalty and does NOT add the
published $40 increment step.** Measured on construction, before the solve:

* SENY's penalty vector is **unchanged** (`penalties_identical = True`, all years), and
  its **first rung is still $62.50** (`$500/8`) in both arms.
* The measured SENY envelope caps at **$23.92 / $30.37 / $40.00**.

**Therefore: arming this flag alone CANNOT bring SENY inside the measured envelope.**
Its first rung sits above the entire measured ceiling in every year, whatever the span.
What it can do is make the ramp **shallower** (rungs widen up to 1.385×), so a given
shortfall MW clears at a lower rung. Pre-registered as a **PARTIAL**: a span fix
addresses the *width* defect and leaves the *level/step-structure* defect standing. **A
result that closes the span defect but leaves SENY over-priced is the PREDICTED
outcome, not a failure of the mechanism**, and will not be reported as closing the
S-OVER finding.

**Direction, pre-registered with its exception.** The re-span prices **lower** where
measured > static (69 % of hours) and **higher** where measured < static. Measured on
construction: 265,399 / 264,039 / 267,874 probe points price lower against 2,101 /
1,889 / 1,188 higher. The direction is therefore **predominantly but not monotonically
downward**, and is stated that way rather than as "the flag lowers SENY".

## §5 — the C3c null, pre-registered

**SENY is expected to leave C3c UNCHANGED at 3/0/14.** C3c is closed as a lever lane
(nyiso-115 §11, nyiso-116, nyiso-117 §5): both admissible routes shut on measurement,
the queue is exhausted, and the re-open condition is a `Capital_Hudson` → Zone-F/Zone-G
**topology split** requiring its own owner charter. **This session does not re-open
it.** A C3c move would be a finding to explain, not a success to claim.

## §6 — GATES, each on an instrument that can observe what it claims

Reserve gates read `hourly/reserve_family_<year>.parquet` — the per-family dual,
requirement, held MW and ORDC shortfall. **Never** `system.parquet`'s `reserve_price`,
which is the cross-family SUM broadcast identically to every zone and is inert by
construction for any locational question (the nyiso-113 K3/K4 error).

**Byte-identity means float32 EXACT equality (`np.array_equal`).** The sidecar columns
are float32 with spacing 7.6e-06–6.1e-05 MW, so a 1e-6 MW tolerance is unsatisfiable in
principle (nyiso-116 G3/P4). No tolerance is used anywhere below.

| id | gate | pass condition |
|---|---|---|
| **G1** | the flag is armed and the re-span is live | `seny_30min_total`'s ORDC widths are hourly and total step width == `requirement_mw` in **every** hour of all three years in the treatment, and **not** in the control |
| **G2a** | **scope — CONSTRUCTION leg (the KILL leg)** | every family except `seny_30min_total` and the NYC pair has `requirement_mw` float32-EXACTLY identical to control, all three years |
| **G2b** | **LI non-double-apply — CONSTRUCTION leg (the KILL leg)** | `li_30min_total`'s ORDC width vector and `requirement_mw` float32-EXACTLY identical between arms, all three years (already discharged ex ante in §3; re-verified on the committed sidecars) |
| **G2c** | **scope — independent corroboration, no parquet** | the solve log's `%d ORDC steps` line is **unchanged in count** between arms in both P0 and P1, all three years (the flag re-spans widths; it adds and removes **no** steps), copied into each bundle as `ordc_steps.log` |
| **G2d** | scope — reported, **NOT a kill** | non-SENY `dual`, `held_mw` and `shortfall_mw` deltas reported; a change is a **finding to explain**, not automatically a leak — they are co-optimization outputs and may move through general equilibrium even where the curve is untouched |
| **G3** | LP row identity | `held + shortfall ≥ requirement` everywhere, tight exactly where the family prices, both arms |
| **G4** | no feasibility damage | zero unserved-energy slack and zero dump in **both** arms, all three years |
| **G5** | span | 2023–2025 in one bundle per arm; **no** year outside 2023–2025 solved, scored or read (rule 22 — the holdout spend freeze is ACTIVE) |
| **G6** | scoring | `legitimacy_diagnostics.py` + `calibration_verdict.py` run per bundle; C1/C2/C3a/C3b/C3c/C4/C6/C7/C8 reported for BOTH arms against each other |

### §6.1 — KILLS, each discharged by MEASUREMENT

| id | kill | fires when |
|---|---|---|
| **K-A** | **LI double-apply** | `li_30min_total`'s widths or `requirement_mw` differ between arms → the global flag re-scaled an already-scaled family. **Pre-discharged on construction (§3); re-verified on the committed sidecars.** |
| **K-B** | **frozen-NYC disturbance** | the NYC pair's reachable price function differs between arms → the flag moved the rule-23-frozen NYC curve. **Pre-discharged on construction (§3, $0.000).** |
| **K-C** | **scope leak** | any family outside {SENY, NYC pair} has a non-identical `requirement_mw` |
| **K-D** | **feasibility damage** | non-zero slack or dump appears in the treatment where the control had none |
| **K-E** | **construction identity not restored** | the treatment still shows hours where SENY's total step width ≠ `requirement_mw` — the flag failed to do the one thing it exists to do |

**If a control degenerates (no power to discriminate), it is reported as
UNINFORMATIVE — never as a pass** (nyiso-117 §6.1). The §3 construction instrument is
demonstrated non-degenerate above: SENY separates on it.

## §7 — no-tuning clauses, binding

Nothing below is derived, re-derived, re-levelled or re-scoped in this session:

* the **SENY $500 penalty**, its `critical_mw = 0`, and the `n_ramp = 8`
  discretization — the flag touches **widths only**;
* the **published $40 SENY increment** — a SECOND mechanism, not armed here (rule 19);
* the **NYC $25/MW RCPF and its NYC-pair scope** — frozen (rule 23), CLOSED, solved
  twice bit-identically;
* the **LI reserve levels, $25 value and On-Peak calendar**;
* the **ramp envelope**, the **227-3 compliance file**, and the
  `nyiso_gas_bridge_*` measured min-load / min-run parameters.

**No parameter is fitted to a residual.** The flag introduces **no new number**: the
scale factor is `requirement[t] / requirement_static`, both already-committed measured
inputs (rule 14 `[R-ACCURATE]` — this stops the static estimate leaking back in through
the curve's span).

## §8 — governance

* **Rule 15** — both arms registered on the dashboard in this session, keeper or not.
* **Rule 16** — 2023, 2024, 2025 in ONE bundle per arm; no single-year keeper.
* **Rule 19** — the SENY level/step-structure question is NOT folded into this flag.
* **Rule 22** — the holdout spend freeze is **ACTIVE**; no year outside 2023–2025 is
  solved, scored or read, validation tier included.
* **Rule 23** — the frozen NYC and LI parameters are not re-derived.
* **Rule 27** — every push touching a file ≥ 300 lines is blob-verified.
* **Rule 28(b)** — `nyiso_ordc_measured_step_span`'s cell moves off `U` to its measured
  verdict in **this** session.
* **Rule 25 / 28(d)** — no other ISO's cell is adjudicated here.

## §9 — decision rule, fixed before the solve

* **All gates pass, no kill fires, and the construction identity is restored** → the
  flag is a **rule-14 `[R-ACCURATE]` construction-consistency fix** and is a **promotion
  candidate on structure** (rule 1 `[R-STRUCT]`) — *not* on whether the residual
  improved. A worse fit does **not** reject it; a better fit does not by itself justify
  it.
* **A kill fires** → **REJECTED**, recorded with the measurement that killed it.
* **Gates pass but scored fields are unchanged** → **INERT at ISO scope**, recorded as
  `I`, not as a pass.
* **The residual moves and the gates pass** → reported as a structural result with the
  §4 PARTIAL restated: the span defect is closed, the level/step defect is **not**.
