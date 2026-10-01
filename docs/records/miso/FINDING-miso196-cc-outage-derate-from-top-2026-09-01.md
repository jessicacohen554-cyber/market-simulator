# FINDING miso-196 — `cc_outage_derate_from_top` clears phase 0 on MISO's own conduct record; and the W5 control check finds a shipped reproducibility defect that does NOT reach the keeper (2026-09-01)

**Session:** miso-196 (2026-09-01). **Keeper:** `2026-08-30-miso-191-bexit`
(bundle `results/calibration/miso191_bax_B`), **UNCHANGED**. No field added, no
field re-semanticized, no matrix row created, no keeper promoted.

**Charter:** the FINDING-miso195 §6 named successor — the APPLICATION-SHAPE leg
of the outage-overlay family, `cc_outage_derate_from_top` (`scenarios.py:11908`,
default `False`, **armed on the CAISO and PJM designated keepers**, `False` on
MISO's), registered as a literal sub-scalar on the `campd_outage_windows` matrix
row. Run as a **rule-1 `[R-STRUCT]` structure test with a declared-adverse face
and a pre-committed escalation posture** — never as the level fix.

Artifacts: probe `scripts/probes/_miso196_outage_derate_from_top_phase0.py`
(**rule frozen in the docstring and pushed at `fef3dcb6` BEFORE any adjudicating
quantity**), census record
`results/calibration/_miso196_outage_derate_from_top_phase0.json`, pre-registration
`PREREG-miso196-cc-outage-derate-from-top-2026-09-01.md` (**pushed at `64f184f1`,
blob-verified, BEFORE the arm existed**).

---

## 0. Ask A — the zero-solve validation, reproduced exactly as handed off

| gate | result |
|---|---|
| `calibration_verdict --run-id 2026-08-30-miso-191-bexit` | **NOT-YET** on **{C3a-2025 −12.3405%} ALONE** |
| C1 / C2 / C3b / C4 | PASS (C1 16/16 · free 12/12) |
| C3c | the single **ledgered** caveat (all three years) |
| C6 / C8 | PASS; C8 carries both grounded notes (2023 CT_PEAKER 15.6%, 2025 ST_GAS 34.2%) |
| `audit_keepers --iso MISO` | PASS, 0/0 |
| `build_status --iso MISO --check` | in sync |
| `check_mechanism_matrix.py` | integrity OK |

Distance to band unchanged, **+2.34 pp**.

## 1. A basis error caught BEFORE the freeze — which is what the satisfiability pass is for

The frozen rule requires mechanical satisfiability of every basis to be verified
on the control before the rule is pushed. It earned its keep immediately. An
earlier draft read the **raw per-unit fleet** (`load_fleet_from_csv` straight
into `generators_to_fleet_arrays`), whose MISO `CC_REGULAR` rows are physical
**sibling units sharing one heat rate** (`991_GT1`, `991_GT2`, `991_STG1`, all
at HR 6.51) — not the offer-curve tranches the solve builds under
`use_campd_bins=True` / `plant_level_fleet=True`. On that basis the seam's own
merit-order sort (`sorted(idxs, key=heat_rate)`) would have been a **pure tie**,
its "committed < econ < peak" ordering meaningless, and every witness would have
been measured on a fleet the LP never sees.

The satisfiability pass surfaced it (no band suffix resolved), and the basis was
corrected **before the freeze** to the shipped tranche path —
`load_retired_within_window` → `load_or_synthesize_bins` → `bins_to_fleet` →
`generators_to_fleet_arrays` — on which bands resolve as
`committed` / `econ<N>` / `peak`. **No adjudicating quantity was computed on the
wrong basis.** The correction is recorded in the frozen docstring.

## 2. Phase 0 — every witness, at full magnitude. `CHARTER_AB = true`

Population **P** = `CC_REGULAR` LP rows at plants with ≥ 2 tranches — exactly
the rows the seam's `cc_by_plant` loop reallocates (44/45/45 plants,
333/341/341 rows). CC_CHP is outside the population by construction.

| witness | line (frozen ex ante) | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **W1** differing plant-hours in S | ≥ 25% | **96.3%** | **95.9%** | **86.0%** |
| **W1** full-year | reported | 83.8% | 83.5% | 79.0% |
| **W2** positive band movement in S | ≥ 1% of class pmax | **8.56%** | **8.64%** | **8.52%** |
| **W4** floor-channel lower bound vs C1 headroom | ≥ headroom ⇒ refute | CLEAR | CLEAR | N/A (unbanded) |
| **W5** single-delta identity | 0 non-P rows; MW preserved to 1e-6 | **CLEAN** 6.3e-16 | **CLEAN** | **CLEAN** |

**W3 conduct — PASS, and it is the structural heart of the session.**

## 3. W3 — MISO's own CAMPD record supports the `from_top` premise and contradicts pro-rata

The mechanism's justification is that a partially-out CC plant runs its
**surviving** capability near full load rather than backing down proportionally.
Measured on MISO's own record (rule 25 — no CAISO/PJM parameter or verdict is
transferred; their `K` is a registration, not evidence here), over 2023–2025,
on the model's own CC population:

| quantity | value |
|---|---:|
| surviving units' CF **inside** partial-outage windows | **0.6166** |
| the **same units'** CF when their plant is whole | **0.6825** |
| **ratio** | **0.9035** |
| `f` = surviving share of plant capacity in those windows | 0.6036 |
| bar = (1 + f)/2, derived from the data, no level constant | **0.8018** |
| partial / full surviving-unit hours | 208,934 / 738,148 |
| partial windows (of 1,403 CC windows) | 1,264 |

The two forms make **opposite** predictions and the data separates them
cleanly: `from_top` predicts ratio ≈ 1.0, strict pro-rata predicts ratio ≈ f =
0.60. MISO's measurement is **0.90** — a partially-out MISO CC plant keeps ~90%
of its normal loading on the surviving train. The bar was the midpoint,
procedurally derived from the measured `f` rather than chosen, and the result
clears it by 0.10.

## 4. W2 — the object the lever moves (mean MW: full-year / scarce set S)

| band | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `committed` | +840 / **+1,152** | +814 / **+1,171** | +809 / **+1,147** |
| `econ` | −54 / −147 | −9 / −116 | +0.3 / −117 |
| `peak` | −787 / **−1,005** | −805 / **−1,055** | −810 / **−1,031** |

Total plant MW is preserved to 6e-16 (W5): this is a reallocation across the
offer curve, not a removal.

## 5. TWO THINGS REPORTED AGAINST THE CLEAN GATES, not behind them

**(a) W4's `CLEAR` rules out nothing, because MISO's CC class has no floor.**
`CC_REGULAR` carries **no `min_gen` floor on this keeper** —
`cc_mustrun_per_plant=False`, no D-2 forced-energy row in any year, and the
class-aggregate `min_gen` measures **0.0 MW in both arms**. The arm's `min_gen`
change is therefore identically zero and the floor channel W4 was frozen to
bound **cannot bite**.

This also corrects half of the row def's own justification as it applies here:
*"the committed floor keeps its level"* describes a floor MISO does not have.
What `committed` is in MISO is a cheap offer-curve **band**, not a forced floor.
The mechanism reduces here to a pure supply-curve shape change, and its C1
exposure runs entirely through the **economic** channel — which phase 0 cannot
bound without a solve. Rather than let a vacuous `CLEAR` stand as reassurance,
that exposure was named as PREREG kill **K-1 with ex-ante arithmetic**: 2024
CC_REGULAR sits at **+6.664 TWh against the ±8.00 TWh band (1.336 TWh of
headroom)** while the arm frees a year-mean **+814 MW** of cheap `committed`
capability = **7.13 TWh** at 8,760 h, so **a realised conversion above ~19%
blows the band**. (The charter quoted +6.820 from miso-188; the current keeper
reads **+6.664**. Code and committed artifacts are the source of truth.)

**(b) The provenance split, reported and NOT gated.** Of the 2025 mean
availability shortfall on P (**9,105 MW** against **27,747 MW** of capacity),
the **measured CAMPD overlay supplies 65.0%** and the statistical WEFOR/POF
base the remaining **35.0%**. The row def defends the mechanism as a
partial-*outage* conduct rule; on MISO's fleet that justification covers the
majority — not the whole — of what it reallocates. The frozen rule deliberately
declined to invent a bar for this, because an expected-availability derate also
loads the cheap tranches first in expectation, so the split cuts both ways. It
is on the record either way.

## 6. THE INCIDENTAL FINDING — a shipped reproducibility defect, and the correction that it does NOT reach the keeper

**What W5's control check found.** The frozen W5 fired **BUG on 2023 alone**
(6 non-P rows moved, worst relative total-MW error 0.100) while 2024/2025 read
CLEAN at 6e-16. **The lever is not the cause.** A control identity — the **same
config built twice** — differs:

| quantity | value |
|---|---:|
| rows / plants / plant capacity affected | **58 / 7 / 7,722.8 MW** |
| classes | `CC_REGULAR`, `CT_PEAKER` |
| hours | **2,928** (h3624–h6551 = exactly Jun 1 00:00 – Sep 30 23:00) |
| `pmax` identical | **yes** |
| max availability delta | **0.1088** |
| first build minus later builds | **+1,544.1 GWh** (mean **+527.4 MW** over the summer window) |

**Root cause, traced in shipped code.** `_CC_PMAX_RECONCILED_PLANTS`
(`data/fleet/eia860.py:776`, written at :875) is a **last-writer-wins module
global keyed only by ISO**, written by every fleet-record load — including
narrow auxiliary loads whose record set legitimately reconciles nothing. The
traced write sequence is `_iso_plant_capacity → load_retired_within_window`
writing `MISO=[]` **after** the main `load_fleet_from_csv` wrote the correct
seven plants; `_iso_plant_capacity` is cached, so it clobbers on the **first**
build only. `_basis_aware_suppresses` (`arrays.py:463`) then reads the empty set
under the armed `summer_derate_basis_aware` and **suppresses the flat summer
ambient derate for the seven plants that should keep it**.

**THE CORRECTION, stated at the same prominence as the report.** The PREREG
deliberately declined to assert that the keeper's own solve was affected,
because that depends on the runner's call order, which the probe did not
measure. **The A/B control leg settles it, and it settles it in the safer
direction.** The load-bearing solve's own log, on **2023 — the first solved
year of the replay** — reads:

> `basis-aware summer derate (MISO): flat _SUMMER_CLASS_DERATE SUPPRESSED for
> 1204 of 1272 flat-derate units; KEPT for 68 unit(s) across 10 plant(s) still
> on a nameplate-like basis [1403, 7842, 52006, 54748, 55218, 55220, 55380,
> 55418, 55467, 55620]`

All seven reconciled plants (1403, 55218, 55220, 55380, 55418, 55467, 55620)
are **KEPT** on the flat derate in the first solved year. **The shipped runner
populates the global before the arrays build even in year one, so no keeper —
MISO's or any other ISO's — is contaminated by this defect.** It is a real
order-dependence in those functions, reachable by callers whose order differs
(this session's probe harness), and it is **not** reached on the load-bearing
path. That materially downgrades its severity from how it first appeared, and
the downgrade is recorded here rather than left to a reader to discover.

**Not fixed in this session, deliberately.** The repair is a solve-affecting
change to core fleet code; even though no keeper is currently contaminated, a
change there re-bases summer availability and needs its own charter, PREREG and
A/B — not a side edit in a lever session (one lever per session). Named as a
successor in §8.

## 7. THE A/B — RUN, AND REJECTED ON ITS OWN PRE-REGISTERED KILL

Both legs solved 2023-2025 in one invocation each, legs sequential (rule 12),
both registered same-session (rule 15): `2026-09-01-miso-196-control`
(`miso196_control_A`) and `2026-09-01-miso-196-fromtop` (`miso196_top_B`).
Scorer `scripts/probes/_miso196_ab_gates.py`, **committed at `74d92131` while
the control leg was still solving** — every kill was evaluated by code written
blind to the numbers it judges. Record `_miso196_ab_gates.json`.

| gate | result |
|---|---|
| **S-0** control integrity | **PASS — BIT-IDENTICAL**, 12/12 keeper sidecars, max_abs_diff **0** |
| **S-1** single delta | **PASS** — exactly `cc_outage_derate_from_top: false -> true` |
| **S-2** tranche-band liveness | **UNSCORED** (basis absent — see below) |
| **K-1** PASS->FAIL flip | **KILL — FIRES on both class-years named ex ante** |
| **K-2** C3b through 0.20 | PASS (arm 0.081 / 0.115 / 0.190) |
| **K-3** new D-4 | PASS |
| **K-4** DOF `n_residual` | **UNSCORED** (replay bundles carry no attestation) |

**K-1, the kill, on exactly the two class-years PREREG §6 named before the solve:**

| C1 2024 (band ±8.00 TWh) | control | arm |
|---|---:|---:|
| `CC_REGULAR` | +6.664 **PASS** | **+12.013 FAIL** |
| `ST_GAS` | −7.553 **PASS** | **−8.092 FAIL** |

**The ex-ante arithmetic was validated almost exactly.** PREREG §6 stated the
arm frees a year-mean +814 MW of cheap `committed` capability = **7.13 TWh** at
8,760 h against **1.336 TWh** of headroom, so **a realised conversion above
~19% blows the band**. Measured CC_REGULAR class energy, control -> arm:
**2023 +4.910, 2024 +5.290, 2025 +4.740 TWh** — a 2024 conversion of **74%**,
nearly four times the threshold. `ST_GAS` is displaced further out of merit,
reproducing the miso-193 K-1 class pair exactly.

**C3a — the declared adverse face, verified in direction and magnitude:**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| control | +0.0913 | −4.5511 | −12.3405 |
| arm | −1.0959 | −5.9752 | **−13.5504** |
| adverse face (pp) | 1.0046 | 1.4241 | 1.2099 |

**DOWN in all three years — the frozen prediction (conf 0.75) verifies**, on
the keeper's sole failing criterion. Per rule 1 this is reported, never
weighed: it is not why the arm is rejected.

**TWO GATES COULD NOT FIRE, DISCLOSED RATHER THAN COUNTED AS PASSES.**
**S-2** reads LP tranche-band dispatch, but **every persisted artifact
aggregates tranche rows back to the physical unit** (ids like `30_1`), so its
frozen basis exists in no committed artifact. The scorer already carried a
`None -> UNSCORED` path for exactly this; the defect was that "no band
resolved" fell through to a spurious FAIL. Corrected to UNSCORED — **not
passed, never silently** — and the class-grain energy shift above is reported
as evidence, explicitly **not** substituted for the gate. **K-4** reads the
DOF ledger, which a `replay_keeper` bundle does not write, so `n_residual` is
`None` on both legs. Neither changes the outcome: K-1 had already fired.
(Analytically K-4 is safe by construction — this lever introduces ZERO free
parameters, being a boolean application-shape switch.)

## 7a. Verdict, and why the owner posture does NOT carry this arm

**REJECT the arm on its own pre-registered kill. Keeper UNCHANGED at
`2026-08-30-miso-191-bexit`. NOT a keeper candidate. No promotion.**

The pre-committed posture (PREREG §7) routes a clean-gates/adverse-face
outcome to owner escalation — but that branch requires the **kills silent**,
and K-1 fired. The standing owner posture ("structural integrity improves but
gates regress may still be a keeper") does not reach this arm either: what
regressed is not a magnitude on an already-failing criterion, it is **two
classes leaving their C1 band outright**, on the exact class-years this
session named in writing before the solve. Promoting through a kill that was
pre-registered and then fired would make the pre-registration decorative.

**WHAT THE REJECTION DOES NOT MEAN — the structural reading, stated in the
lever's favour.** W3 stands unrefuted: MISO's own CAMPD record says a
partially-out CC plant keeps ~90% of its normal loading on the surviving
train (ratio 0.9035 against a pro-rata prediction of 0.6036). The mechanism is
real conduct, and rule 1 forbids concluding "revert it because the fit got
worse". The honest reading is the rule-14 compensating-error pattern: the
**pro-rata form was silently masking a pre-existing CC over-dispatch** — the
keeper already sits +6.664 TWh high on CC_REGULAR-2024 — and arming the
structurally-faithful form removes the drag that was hiding it, exposing the
defect at full size. **The open root-cause question this A/B produces is
therefore "why is MISO CC_REGULAR ~+6.7 TWh over before any of this?", not
"should `cc_outage_derate_from_top` exist".** That question is handed on; it
is not a lever this session may adopt.

## 8. What is handed on

1. **The CC_REGULAR over-dispatch root cause** (§7a): the keeper is +6.664 TWh
   high on CC_REGULAR-2024 *before* this lever, and the pro-rata outage
   application was masking it. A structurally-faithful application form cannot
   be armed until that is fixed — which is the real successor, and it is a
   root-cause investigation, not a lever.
2. **Re-testing `cc_outage_derate_from_top` AFTER that repair.** The cell is
   adjudicated for THIS keeper only; the mechanism's conduct case (W3) is
   measured, MISO-native and unrefuted, so it should be re-offered once the CC
   level defect is closed — not treated as closed itself.
3. **The `_CC_PMAX_RECONCILED_PLANTS` order-dependence** (§6) — a real defect,
   **no keeper contaminated** (now proven: S-0 reproduces the keeper
   bit-identically from a fresh process), needing its own charter because the
   repair is solve-affecting core code.
4. Census queue otherwise unchanged: `egrid_identity_heat_rates` (K@NYISO),
   `tac_load_coverage` (K@CAISO), `lcr_tsl_published` (K@CAISO+NYISO).

**Not touched** (charter "not yours to decide"): the D-4 posture ruling; the
miso-141 §11 nameplate-basis switch (MISO CC pmax **is** the net-summer rating,
owner court — this lever was evaluated on that basis as-is); the D-2
seam-response 5(i) admissibility ruling; the class-resolved outage data ask; the
C8 provenance-materiality floor; the RHO_CLIP band; the miso-189 §7.3 residue;
the `correlated_forced_outage` backcast default. Rule 22: **2023–2025 only** —
MISO holds neither a `complete` nor a `final` marker, the holdout freeze is
active, and no out-of-training year was solved, scored or read.

## 9. Reproduction

```
python3 scripts/probes/_miso196_outage_derate_from_top_phase0.py
python3 scripts/probes/_miso196_outage_derate_from_top_phase0.py --satisfiability
```
