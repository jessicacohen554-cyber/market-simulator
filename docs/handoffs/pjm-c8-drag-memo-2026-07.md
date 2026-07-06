# PJM C8 drag decision memo — drag-sizing vs D-2 exemption (OWNER DECIDES)

**Status: DRAFT for owner adjudication — 2026-07-06, L-13 (Wave-3 PJM lane).
Nothing in this memo has been applied. No parameter, gate, or rule text was
changed in the drafting session.**

## 1. The question

The pjm-77 keeper's only remaining D-2 failure is the CT net-load drag's
forced-energy share in 2024: **12.1 % of CT_PEAKER energy dispatched at the
binding drag floor, vs rule 20's 10 % peaker budget** (2023 7.6 % and 2025
7.9 % pass). The gap register (§4 PJM row) marks the disposition as the ISO's
one judgment-ready item: **re-size the drag, or exempt it from the D-2
budget.** Rule 20's letter says "a keeper fails" on a breach; pjm-77 currently
carries it as a disclosed C8-hard NOT-YET caveat (the G-05 pattern shared by
4/6 keepers).

## 2. Background — what the drag is

`ct_netload_drag` is PJM CT_PEAKER's **single** commitment mechanism (rule 19;
the temperature reliability limbs for the class are dropped while the drag is
active — `drop_drag_owned_reliability_specs`, pjm-77's promotion fix). It is a
ramp-windowed [15,22) min-gen floor whose coefficients are **regressed from
measurement, not fitted to any residual**: CAMPD pure-play CT fleet CF vs
EIA-930 PJM net-load, pooled 2023–2025, hinge fit
(`scripts/derive_pjm_ct_netload_drag.py`; slope 0.01108/GW, intercept −0.9987,
cap 0.46). Its identification is year-stable (ramp-window Spearman ρ = 0.50 /
0.51 / 0.60; hinge SSE 0.133 vs 0.176 for the unclipped line — burndown §4)
and its window is clean (D-4: 0 % off-window binding, all years). It stands in
for real market behaviour the P1 LP cannot produce — reserve/ramp deployment
duty on peakers — pending the per-gen reserve/ORDC co-optimization (G-20,
memory-blocked; `docs/multi-iso/pjm-reserve-ordc.md` Phase 2).

| year | drag-floored TWh | forced at floor TWh | model CT_PEAKER TWh | forced share | budget |
|---|---|---|---|---|---|
| 2023 | 2.27 | 1.93 | 25.36 | 7.6 % | 10 % |
| 2024 | 2.85 | 2.49 | 20.68 | **12.1 %** | 10 % |
| 2025 | 3.03 | 2.61 | 33.06 | 7.9 % | 10 % |

## 3. New evidence (this session): the breach is denominator-driven

Benchmarked against EIA-923 actuals (`bench/PJM/<year>.json.gz` classFull):

| year | actual CT_PEAKER TWh | model CT_PEAKER TWh | model − actual | forced share **at actual volume** |
|---|---|---|---|---|
| 2023 | 26.09 | 25.36 | −0.7 | 7.4 % |
| 2024 | 28.06 | 20.68 | **−7.4 (−26 %)** | **8.9 %** |
| 2025 | 24.73 | 33.06 | +8.3 (+34 %) | 10.6 % |

Two observations:

1. **2024 — the breach year — is the year the model most under-dispatches
   CT_PEAKER economically.** The drag numerator (2.49 TWh) is ordinary; the
   denominator is 7.4 TWh short of actuals. Had the model dispatched the
   actual volume, the share would be 8.9 % — inside the budget. The breach is
   substantially an artifact of a *different* open miss: the model's CT volume
   year-ordering is inverted vs actuals (model 2025 > 2023 > 2024; actual
   2024 > 2023 > 2025).
2. A prime suspect for that under-dispatch is on this lane's own queue:
   the **sub-SRMC ST_GAS offers (0.48×/0.66×) flood ST_GAS energy** (model
   18.2 / 15.8 / 18.6 TWh vs actual 8.6 / 12.4 / 14.3 — up to +112 %),
   displacing merit-order energy that in reality peakers served. The G-21
   re-grounding cycle (ST_GAS & CT_INTERMEDIATE → the 1.0× Manual-15 SRMC
   floor) directly attacks this and its full-span D-2 will re-measure the drag
   share on a corrected denominator.

## 4. Option A — drag-sizing

Re-size the drag so the 2024 share lands ≤ 10 %: shrink the cap (0.46 →
~0.38), damp the slope, or re-derive with a stricter functional form.

**Evidence against:**

- The coefficients are measured-behaviour parameters. **Rule 24 freezes them
  against residuals/diagnostics** — they re-derive only when CAMPD/EIA-930
  source data updates. There is no data change; the only motivation would be
  the D-2 number itself, i.e. tuning a measured mechanism to a gate.
- The breach term is the **denominator** (§3). Shrinking the drag would delete
  real, measured deployment energy in *all three years* (2023/2025 already
  pass) to offset a 2024 economic under-dispatch that is a separate open bug.
  This is exactly the compensating-error move rule 14 forbids: burying one
  error inside another input.
- The burndown (§4, §7) already adjudicated this: "unresolvable by weakening
  the drag … a grounded reserve-deployment floor sized to measured CT can
  exceed the rule-20 merchant budget in a tight year" — a tension to resolve
  by decision or root cause, "not a fit move".

**Rule-20 implication:** the budget's letter is preserved, but by making a
grounded mechanism smaller than its own measurement — i.e. rule 20 would be
satisfied at the direct expense of rules 14/24 and the DOF ledger's "no
residual-identified re-fits" attestation. A hostile referee reading the derive
history would see the cap move from 0.46 to a value with no measurement basis
in the same commit that cleared the gate.

## 5. Option B — D-2 exemption

Reclassify `MECH_CT_NETLOAD_DRAG` out of the gated set (today only structural
must-run is exempt: nuclear, `chp_steam`, coal take-or-pay), either by adding
it to `D2_EXEMPT_MECHS` (blanket) or by giving measured deployment floors
their own budget class.

**Evidence for:**

- The drag is not "commitment scaffolding" (rule 20's target); it is a
  **measured deployment floor** — the reduced-form stand-in for reserve/ramp
  duty, an admissible measured-input class under rule 13 ("a measured
  ancillary-service power reservation"). Its energy is real market behaviour
  the LP has no other channel for; counting it against a budget whose premise
  is "floors must not do the dispatch model's job" mislabels it — deployment
  energy is precisely the part of dispatch the P1 model *cannot* do.
- Its identification discipline is stronger than the exempt structural floors:
  windowed (D-4 0 % off-window), year-stable D-8, derivation frozen (rule 24),
  and its coefficients sit in the keeper's DOF ledger with a measurement
  source.

**Evidence against:**

- **The CAISO precedent cuts hard the other way.** CAISO's CT drag/floor
  family shows slope +18 % LOYO instability with the floor carrying ≈ 90 % of
  class energy (G-15), and the undiagnosed HEAD drift moved CAISO forced
  shares to 60–71 % (G-11). Had the drag family been D-2-exempt, C8 would have
  been blind to both. The budget is the tripwire that keeps a "measured"
  deployment floor from quietly becoming the dispatch model.
- Exempting the exact mechanism that breached, immediately after it breached,
  is gate-shopping in optics even when the rationale is sound — it needs owner
  sign-off and a rule-20 text amendment, not a lane-level code edit.
- §3 shows the 2024 breach is mostly *not* the drag's fault. Exempting it
  would permanently remove coverage to resolve what is likely a transient
  artifact of the ST_GAS/CT_INTERMEDIATE mispricing.

**Rule-20 implication:** requires amending the rule to recognize a second
floor category — *measured deployment floors* — distinct from commitment
scaffolding. If taken, it should NOT be a blanket exemption: replace the
share-of-class budget with a **measurement-anchored fidelity gate** (per year,
drag-forced MWh ≤ the derivation's own predicted deployment envelope — hinge
CF × available capacity summed over window hours, with a stated tolerance), so
the mechanism stays gated against exceeding its measurement even after it
stops being gated against class share. The CAISO drag would fail such a gate
today — which is the correct outcome and the test of the gate's honesty.

## 6. Recommendation (drafter's, non-binding)

**Neither option yet — sequence the decision behind the G-21 re-grounding
cycle, then take the narrow form of B only if the breach survives.**

1. The G-21 full-span re-grounded run (this lane, in progress) removes the
   sub-SRMC ST_GAS/CT_INTERMEDIATE offers that are the prime suspect for the
   2024 CT_PEAKER under-dispatch. Its registered D-2 re-measures the drag
   share on a corrected denominator, at zero incremental cost.
2. **If the 2024 share falls ≤ 10 %**: the breach was the denominator artifact
   (§3). Close the item with no rule change and no drag change — rule 20
   stands unamended, Option A/B both moot.
3. **If the breach survives re-grounding**: adopt Option B in its narrow form
   (deployment-floor category + measurement-anchored fidelity gate, rule-20
   text amendment, owner-signed). Blanket `D2_EXEMPT_MECHS` addition is not
   recommended in any branch (CAISO counter-precedent, §5).
4. Option A is not recommended in any branch: no data change licenses a
   re-derivation (rule 24), and the sizing lever cannot fix a denominator
   problem without deleting measured energy in the passing years.
5. Either way, the drag's rule-19 endgame is unchanged: it is replaced
   outright when the per-gen reserve/ORDC co-optimization (G-20 Phase 2)
   lands, at which point this entire question retires.

**STOP — decision is the owner's.** This memo deliberately makes no change to
`D2_EXEMPT_MECHS`, `D4_WINDOWS`, rule text, drag coefficients, or any keeper
artifact.

## 6a. Addendum 2026-07-06 — §6's sequencing bet did NOT pay off; C8 got worse

The G-21 cycle completed (`docs/calibration-log.md` 2026-07-06 entry,
`pjm-79`/`pjm-80` probes). Re-grounding ST_GAS/CT_INTERMEDIATE to 1.0×
predicted in §6.1 that the corrected denominator would either resolve the
breach or leave it unchanged. **Neither happened: the 2024 CT_PEAKER share
ROSE from 12.0% to 14.0%** (2.49→2.65 TWh forced ÷ 20.69→18.95 TWh class
total). The de-flooded ST_GAS energy went almost entirely to CC_REGULAR
(+8–10 TWh/yr), not to CT_PEAKER — the class total shrank slightly (CT_PEAKER
model volume 20.7→19.0 TWh in 2024, moving further from the 28.1 TWh actual)
while the drag's own forced numerator was essentially unchanged (drag
coefficients untouched, so its predicted deployment envelope didn't move).

This **falsifies the §3 hypothesis that the ST_GAS flood was displacing real
CT_PEAKER volume** — it was displacing CC_REGULAR instead. The breach is not
a denominator artifact of the sub-SRMC bands; it is a **standalone,
class-intrinsic result of the drag's measured deployment fraction exceeding
10% of a shrinking CT_PEAKER total in the tight 2024 year**, independent of
the ST_GAS mispricing.

**Updated recommendation:** §6 step 2's exit condition (re-grounding clears
the breach) is now known FALSE. Per step 3, the narrow Option B form
(measured-deployment-floor category + measurement-anchored fidelity gate,
owner-signed rule-20 amendment) is the live path — **the decision no longer
needs to wait on any further G-21 work**; that dependency is resolved (in the
negative). Option A remains not recommended (§4, unchanged). The owner can
adjudicate now.

**Addendum 2026-07-06 (L-13 posture probe — null result).** The
`pjm_commitment_posture` A/B probe (pjm-82 vs pjm-81;
`docs/handoffs/pjm-commitment-posture-port-2026-07.md`) does **not** move the
CT_PEAKER denominator: 2024 class total 20.69 → 20.59 TWh (−0.10), the breach-year
forced share stays **12.0 %** (D-2 numerator 2.49 → 2.47 TWh). The posture's
min-load coupling pins a little more CC_REGULAR baseload (+1.5 TWh/yr) and shaves
ST_GAS/CT slightly — it does not repair the 2024 CT_PEAKER under-dispatch. So the
C8 disposition above is **unchanged**; this probe adds no new denominator evidence.
The C8 decision remains the owner's.

## 7. Sources

- `results/calibration/pjm77_ct_relfloor_reconcile/legitimacy_diagnostics.json`
  (D-2/D-4 committed rows), `calibration_attestation.json` (drag coefficients,
  residuals_note, DOF ledger).
- `docs/FINDING-pjm-burndown-2026-07.md` §4–§7 + 2026-07-06 addendum.
- `frontend/data/backcast/bench/PJM/{2023,2024,2025}.json.gz` `classFull`
  (EIA-923 actuals used in §3).
- `scripts/derive_pjm_ct_netload_drag.py` (derivation + its frozen-parameter
  contract), `scripts/legitimacy_diagnostics.py` (D2_EXEMPT_MECHS,
  D2_PEAKER_MAX_SHARE = 0.10).
- `docs/gap-register-2026-07.md` G-05/G-11/G-15/G-20/G-21, §4 PJM row.
