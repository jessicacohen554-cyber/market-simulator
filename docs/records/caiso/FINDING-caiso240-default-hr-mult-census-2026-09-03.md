# FINDING — caiso-240: 22 of the 28 uncited class multipliers are DEAD; the live remainder is not where anyone expected it

**Session caiso-240, 2026-09-03. Branch `claude/caiso-239-hr-mult-census-ycpdgu`.**
Pre-registered in `PRECOMMIT-caiso240-default-hr-mult-census-2026-09-03.md`
(`bfa6999a`, pushed **before any footprint measurement**) and
`PRECOMMIT-caiso240-ADDENDUM-arm-2026-09-03.md` (`30389e1a`, pushed **before the
solve**). The full census, its per-cell grades and the §7 second object are in
`ASSESSMENT-caiso240-default-hr-mult-census-2026-09-03.md`; this file records the
arm, its gates and the predictions scored.

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read and the whole solve stayed inside **2023–2025**.

**Keeper: `2026-09-02-caiso-239-b1-stgas` → `2026-09-03-caiso-240-b1-stgas`.**
Determination **UNCHANGED at NOT-YET**, C3a the sole load-bearing FAIL.

---

## §1 — HEADLINE

caiso-239 §9 item 1 asked for a rule-24 `[R-REGISTRY]` census of
`campd_bins._DEFAULT_HR_MULT_BY_GROUP`'s 28 uncited literals. Measured on **all
six designated keepers, with zero solves**:

* **22 of the 28 are DEAD in every one of the six ISOs.** Five of the seven `mr`
  literals are dead **by construction** — `bins_to_fleet` builds a must-run
  tranche only for non-CHP coal — and every `CC_*` / `CT_*` `mc` / `econ` /
  `peak` literal is overridden by an offer curve in every keeper.
* **The largest live cell anywhere is `COAL:mr` (MISO 61 tranches / 12,709 MW;
  PJM 52 / 10,393 MW; ERCOT 10 / 3,650 MW) and it is mostly PRICED-BUT-INERT** —
  the coal `_mustrun` tranche's fuel is sunk under take-or-pay, so its heat rate
  moves with the literal and its marginal cost does not (0 of 10 ERCOT, 20 of 52
  PJM, 15 of 61 MISO rows are economically live).
* **`ST_CHP` is the one class in the model whose ENTIRE offer surface is uncited
  literals.** No keeper of any ISO configures an `ST_CHP` offer curve. Under rule
  25 `[R-ISO-SCOPE]` that is an **ask for the MISO / PJM / NYISO / NEISO lanes**,
  never an arm here.
* **On the CAISO keeper exactly TWO cells survive caiso-239** — `ST_GAS:econ` =
  1.00 (3 tranches, 2,240.8 MW) and `ST_GAS:peak` = 1.10 (3 tranches, 428.8 MW),
  both on the same three once-through-cooling steamers through the same bypass.

**The peak one is armed, solved, registered and PROMOTED TO KEEPER** (`2026-09-03-caiso-240-b1-stgas`, superseding `2026-09-02-caiso-239-b1-stgas`; `audit_keepers --iso CAISO` PASS 0/0). Its measured counterpart,
**1.166**, is *already the value the CAISO ST_GAS class band carries* — armed at
caiso-231 on the CT bucket that `derive_caiso_offer_surface.py` discloses
**contains these very steamers** — and the bypass keeps that re-grounded band
from reaching any of them, so on the keeper it prices only two EIA-860
retired-window units. **The measurement is withheld from its own population.**
That is caiso-239's structural inversion again, one band over.

**The larger cell is REFUSED at this grain, not taken**: `ST_GAS:econ`'s
counterpart is a two-endpoint ramp against a single flat model band, so choosing
an endpoint would be a free parameter (precommit §6(3)).

---

## §2 — THE INSTRUMENT PASSED BOTH PRE-REGISTERED FALSIFIERS

* **M-1 (null pass) — PASS.** A baseline→baseline rebuild of the CAISO keeper is
  byte-identical in `unit_ids`, `heat_rate` and `mc_base` across all 1,801 rows.
* **M-2 (two-point validation) — PASS.** `ST_GAS.mc` is responsive on **exactly
  3** tranches (plants 315 / 335 / 350) in **every** year on the caiso-231
  predecessor recipe — reproducing caiso-239 F-1 — and on **ZERO** in every year
  on the caiso-239 keeper. This validates the instrument *and* independently
  verifies that caiso-239's repair retired the literal it claimed to retire.

The caiso-238 error is made structurally impossible: each cell carries its **own
unique probe factor**, so a row's cell is identified by its measured heat-rate
ratio, never inferred from its group or name. Across 18 ISO-years, **zero** rows
moved at any other ratio (`indirect = 0`) and **zero** were clip-suppressed.

---

## §3 — THE ARM: WHAT WAS BUILT, AND WHAT IT COSTS

`ScenarioConfig.caiso_st_gas_peak_measured` — gated, **default off**, per-ISO
registry `constants.ST_GAS_PEAK_MEASURED_HR_MULT_BY_ISO` (CAISO **1.166**, cited
to `caiso_offer_curve_measured.json` → `CT_PEAKER.bands.peak`). One gated limb in
`fleet/assembly.py`'s `offer is None` branch, **band-disjoint** from its caiso-239
sibling (rule 19 `[R-ONE-MECH]`; a unit test pins that arming both moves exactly
two bands). An ISO with no registry entry is a **hard error** at both the config
gate and the consumer (rule 25). Threaded onto `--replay-bundle`. Registered in
`_BACKCAST_ONLY_OVERLAY_FIELDS` — unlike caiso-239's, which arms a measured
*physical* ratio; this arms measured **OASIS bid conduct** (rule 13).

Run: **`2026-09-03-caiso-240-b1-stgas`**, bundle
`results/calibration/caiso240_b1_stgas_peak_measured`. The caiso-239 keeper's
`meta.json` replayed at HEAD with the single flag delta, P1 scored, 2023 / 2024 /
2025 sequential in one invocation and one bundle (rules 12 / 16). No control arm
(caiso-231 standing directive).

**PROMOTED to CAISO keeper**, superseding `2026-09-02-caiso-239-b1-stgas`.
`audit_keepers --iso CAISO` **PASS, 0 failures, 0 warnings**. CAISO holds no
`complete` and no `final` marker, so rule 22 D-5(b) re-keying does not attach.

---

## §4 — GATES, SCORED

| gate | verdict | measurement |
|---|---|---|
| **G-STRUCT** | **PASS** | Verified **pre-solve** on the rebuilt fleet in all three years: exactly **3 of 1,801** rows move, all three the OTC steamers' `_peak` tranches (plants 315 / 335 / 350), at the **exact** ratio 1.166 / 1.10 = **1.060000000000**; 0 other bands, 0 other groups, 0 other ISOs. The solved fleet agrees — ST_GAS is the only class that loses energy, and within it only the repriced tranches can respond. |
| **G-INERT** | **PASS** | Not byte-identical: 2024 ST_GAS sheds **11.8 GWh** to CT_PEAKER (+6.5), CC_REGULAR (+3.6) and imports (+1.2). |
| **G-CTRL** | **PASS** on its dispatch-identity leg | 2023 and 2025 reproduce the keeper to within **0.001 TWh in every class** (max abs delta 0.000735 and 0.000196 TWh). This is the §0.7(1) re-specification, and it binds because the mechanism has an inert year. |
| **G-C1** | **PASS** | 12/12, free 8/8, unchanged. |
| **G-C3b** | **PASS** | unchanged; the 2025 composition-watch tripwire did not fire. |
| **G-C8** | **PASS** | unchanged. |
| **G-CAVEAT** | **PASS** | budget 1 of 1 — C3c alone, ledgered; 0 protective. |
| **G-C3a** | **SPLIT — verdict leg PASS, bound leg FAIL** | No year flips; 2023 stays PASS; every scored criterion identical. **But the 2024 move exceeds its pre-registered bound by 4.5×.** See §5. |

**Every scored criterion is identical to the predecessor keeper**, and the grade
summary is unchanged (scored 8 / target 6 / commercial 0 / ledgered 1 / fails 1).

---

## §5 — THE PRE-REGISTERED BOUND FAILED IN 2024. IT IS DISCLOSED, NOT RE-FITTED.

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| **pre-registered bound** (pushed to `origin` before the solve) | +0.0014 | **+0.0011** | zero-to-tolerance |
| **measured** | +0.0003 | **+0.0049** | +0.0000 |
| | inside | **EXCEEDS, 4.5×** | inside |

The precommit fixed the response in advance: *"a bound violation is a defect in
the estimator or the mechanism, reported as such, **never re-fitted**."*

**ROOT CAUSE, MEASURED — and it is an ESTIMATOR defect, not a mechanism defect.**
The caiso-230 §H form sums `ω · p_z · |Δmult/mult|` over the zone-hours where the
repriced tranche is **itself the matched marginal rung** — **14 such zone-hours in
2024**. It is structurally blind to **indirect re-dispatch**, and indirect
re-dispatch is this arm's *dominant* channel: raising the ST_GAS peak band pushes
11.8 GWh out of those tranches and onto CT_PEAKER, CC_REGULAR and imports, which
lifts price in hours where the ST_GAS peak rung was **never** the matched
marginal rung and which the estimator therefore never counts.

**THIS CORRECTS A LOAD-BEARING CLAIM IN THE CAISO LANE'S TOOLKIT.** caiso-230,
caiso-231 and caiso-239 all describe the §H form as *"a strict **upper** bound"*,
and caiso-231/239 each observed it over-predicting (by 4–13× and 3–4×
respectively), which looked like confirmation. **It is not an upper bound.** It
over-predicts when the repriced rung's own marginal hours dominate, and
**under-predicts when the displaced energy lands on rungs that were already
marginal elsewhere**. Both caiso-231 and caiso-239 happened to be in the first
regime; this arm is in the second. Any future session quoting §H as a ceiling is
quoting it wrongly. **This is the THIRD gate-spec defect this family has
disclosed** (caiso-239 found the G-CTRL field-diff defect and the degenerate-zero
defect; §0.7 inherited both rather than re-discovering them).

**Reported at full magnitude, and put in proportion:** +0.0049 $/MWh on a
$39.0060 → $39.0109 price level is **0.013 %** of the price and **0.6 %** of
2024's required move (−0.848 $/MWh). No year flips; the reported C3a percentages
are unchanged at the scorecard's precision.

---

## §5b — PROMOTION BASIS

The owner's standing standard — *"structural integrity improving while gates
regress may still be a keeper"* — is met **in its strongest form**: structural
integrity strictly improves (an uncited ERCOT-lineage literal on 428.8 MW of SP15
OTC steam peak capacity retires to the ISO's own measured value, zero free
parameters) and **no scored criterion regresses at all**. The session's own
pre-registered promotion rule keyed on *"G-C3a shows no verdict flip"*, which is
satisfied; the bound failure is recorded against the estimator, and this finding
is where it is recorded.

---

## §5c — PREDICTIONS, SCORED AGAINST INTEREST

P-1 through P-6 are scored in the assessment (§6 there): **two falsified**
(P-4 ERCOT-vs-median, by a tie at 10 responsive tranches; P-6 CAISO's largest
live cell is not in the `mr` family — CAISO has no live `mr` cell at all), **one
right for the wrong reason** (P-1 survives its falsifier but I reasoned from the
route without first measuring whether any gas must-run tranche exists — the
caiso-238 error in miniature, made by the session that built the instrument to
prevent it), **three confirmed** (P-2, P-3, P-5).

**P-7 — the DOF ledger does not move — HOLDS.** `build_dof_ledger.py` rebuilt the
arm's ledger; the retired literal lives in `campd_bins.py`, which
`_count_scalars` does not read, exactly as pre-registered for the third
consecutive session. The counter measures the offer surface's SIZE, not its
fitted content.

---

## §6 — DISCLOSURES, EACH REGISTERED RATHER THAN DISCOVERED AFTER A MISS

**§6.1 — The population match is CONTAINMENT, not coincidence, and is WEAKER
than caiso-239's.** caiso-239 armed `avg_committed_p50` whose ten CAMPD units
**are** plants 315 / 335 / 350 and no others. This arm's 1.166 comes from the
OASIS **CT bucket**, which is pooled `CT_PEAKER + CT_CHP + ST_GAS` conduct with
**masked ids**, so the steamers cannot be isolated inside it. What is established
is that the derive says they are *in* it — *"the three OTC/RMR steamers (ST_GAS …)
and priced CT_CHP curves land in the CT bucket"* — which is the same basis
caiso-231 re-grounded the ST_GAS class band on and was promoted for. Stated here
so nobody reads this arm as carrying caiso-239's strength of identification.

**§6.2 — The 2025 bound is degenerate, and that was declared in advance.**
Precommit §0.7(2) inherited caiso-239's second gate-spec defect and fixed the
reading **before** measuring: a bound of zero is reported as *"zero to within the
estimator's attribution tolerance"*, never as an exact zero. 2025 has **zero
matched-marginal zone-hours** for the responsive tranches, so the §H form is
silent there by construction; a small measured 2025 move is a bound-form
limitation, not a falsification. Nothing was re-fitted and the bound was not
widened after the fact.

**§6.3 — The caiso-231 "no control arms" owner flag, ANSWERED for this arm.**
Precommit §0.8 asked whether the funded cell would be live in all three years, in
which case the directive would leave the arm with no independent check at all.
**It is not** — 2025's zero matched-marginal zone-hours is exactly the inert year
G-CTRL's dispatch-identity leg needs. The gap the parent flagged is therefore not
realised here, **but the flag stands for the next arm that is live everywhere**,
and the `run_config` field diff will not supply the missing check.

**§6.4 — A DECLARED REBUILD DEVIATION, for PJM only, in the census.** PJM's
keeper arms `pjm_da_virtual_bids` and `data/raw/pjm-da-virtuals/` is one of the
BLOAT-B corpus conversions: its payload is untracked at tip and was stripped from
history on 2026-08-16, so the directory holds only its README and the mechanism
hard-fails ("never silently no-ops"). Rather than drop PJM from the census, the
flag is disarmed **for the rebuild only**, identically in the baseline and
perturbed passes. It cannot touch the measured object — virtual bids add
demand-side LP units and never enter `fleet_to_bins` / `bins_to_fleet`, where
every thermal band heat rate is set — so it cancels in the diff. Declared in the
probe's code, in its provenance block, and here.

**§6.5 — The census was assembled from four probe invocations, not one.** Same
HEAD, same deterministic probe, each ISO on its own keeper; the split is a
scheduling consequence of §6.4 and of running the census alongside the solve.
Recorded in the artifact's `_provenance.merged_from`.

---

## §7 — DO-NOT-REDO ADDS

1. **Never re-propose any of the five gas `mr` literals** (`CC_CHP`,
   `CC_REGULAR`, `CT_CHP`, `CT_PEAKER`, `ST_GAS`, `ST_CHP` `:mr`) **as a repair
   target.** They are dead **by construction**: `assembly.py` sets
   `mustrun_cap = 0.0` for every non-coal bin, so the tranche is never built. Any
   future proposal must first change *that*, and say so.
2. **Never quote `COAL:mr` as an economically live off-registry channel without
   its mc-live split.** It sets 12.7 GW (MISO) / 10.4 GW (PJM) / 3.6 GW (ERCOT)
   of heat rate but only 15 / 20 / 0 of its 61 / 52 / 10 tranches move marginal
   cost, because the `_mustrun` tranche's fuel is sunk under take-or-pay.
3. **Never re-census `_DEFAULT_HR_MULT_BY_GROUP` without new evidence.** All 28
   cells × 6 keepers × 3 years are measured, with both method falsifiers passing;
   the artifact is `_caiso240_default_hr_mult_census.json`. A re-census is
   warranted only when a keeper changes or a new offer-curve key is added.
4. **Never arm `ST_GAS:econ` by picking one endpoint of the measured ramp.** It
   is a free parameter, and the complete repair is the §7 mechanism, which is
   dependency-blocked (see 5).
5. **Never split `ST_GAS_PEAKER_PLANTS`'s offer-curve scope as posed.** Handing
   plants 315/335/350 the class curve re-imposes the caiso-239-refused
   `committed = 0.81` on them. The admissible move is the byte-identity rename
   (assessment §7.3), not the behaviour change.
6. **Never transfer CAISO's 1.166 to ERCOT's six bypassed ST_GAS plants**
   (rule 25). Their matrix cell is `U`: an ERCOT lane derives ERCOT's own
   measured peak band or the cell stays `U`.
7. **Never re-propose this mechanism as a C3a lever.** Its direction is adverse
   by construction (+6.0 % on a peak band).
