# FINDING — caiso-126: the RoR-split family, honestly classified, moves every window toward measured — overnight 2-3× beyond the fixed-λ prediction (the water-value feedback is REAL) — and is KILLED as armed by evening starvation (K1-2024), the caiso-125 §4b spread compression surfacing exactly where predicted

**Keeper `2026-07-23-caiso-netrev-margin-keeper` UNCHANGED. Arm B registered
as a REJECTED probe (`2026-07-27-caiso-126-ror-split`, rule 15); promotion was
never on the table (owner-gated, and two pre-registered kills fired).**

Gates: `results/calibration/PREREG-caiso126-ror-split-2026-07-27.md`
(committed at `08d8113`, before arm B solved). Scorer:
`scripts/probes/_caiso126_ror_ab.py` (committed). Arms:
`caiso126_control_A` (NOT registered, FINDING-caiso92b protocol) /
`caiso126_rorsplit_B`, both 3-year single invocations at the same HEAD,
sequential (rule 12/16), seam import cap 16,148 MW (2025) affirmatively
logged in all six year-solves.

---

## §1 — the classifier intake inverts the caiso-125 premise's WEIGHT

The external classifier (ORNL EHA FY2024 `Mode` + the documented categorical
HILARRI/Corps-dam completion; `data/clean/hydro-plant-modes`, curated by
`scripts/data/curate_hydro_plant_modes.py`, validated residual-blind at 86/97
plants / 84.7 % of labeled MW) classifies the CISO conventional-hydro fleet:

- **By count**: 84/195 plants RoR-class (~43 % — the caiso-125 §4c "~half"
  reading was count-weighted, and it was right *as a count*).
- **By energy**: only **12.5 / 11.1 / 10.3 %** of the 2023/24/25 budget. The
  large systems (SWP Hyatt/Devil Canyon, Big Creek, the PG&E Pit/Feather
  cascades, Hetch Hetchy) are reservoir-backed and operationally peaking.

The caiso-125 greedy CF ≥ 0.45 proxy's 42.7–60.7 % "RoR share" was therefore
NOT run-of-river physics: it mostly flat-lined **high-CF shapeable** plants
(EHA-labeled Peaking plants running near capacity in wet years — Rock Creek,
Big Creek 1/2/2A/4, Cresta, Pit 3, Hyatt at CF 0.81 in 2024). Its
window-matching success conflated two drivers: true non-shapeability (~10 %
of energy) and wet-year headroom exhaustion (which the LP's own
budget-vs-pmax feasibility already represents per plant). Alternate
completions measured and rejected: FC_Dock mode-propagation covers 0/100
NaN plants; EHA FY2023 carries the identical NaN set; GRanD-linkage alone
under-covers (26 FN on the labeled set).

## §2 — the A/B: every window moves toward measured; the LP feedback is real

Pre-solve, the fixed-λ greedy proxy predicted the honest 10-12 % split moves
overnight only −55/−132/−49 MW (PREREG §3). Measured LP result (B − A):

| gap (model − meas, MW) | 2023 | 2024 | 2025 | gate |
|---|---|---|---|---|
| overnight (hod 0-6) | +311 → **+160** | +249 → **+92** | +308 → **+211** | P1: PASS 2024; FAIL 2023/25 (>150) — improved EVERY year |
| belly (hod 9-15) | −583 → **−92** | −611 → **−58** | −549 → **−83** | P2: PASS all years |
| evening (hod 17-21) | +126 → **−251** | −114 → **−376** | +5 → **−264** | **K1: KILL 2024** (−376 > 300) |
| D-1 profile_r | 0.960 → 0.966 | 0.974 → 0.976 | 0.985 → 0.977 | P3 (pair): PASS all years |
| D-1 cv_ratio | 1.98 → 1.19 | 1.81 → 1.11 | 1.67 → 1.17 | (amplitude error −80…−87 %) |
| h < 10 MW | 270 → **0** | 692 → **0** | 604 → **0** | parks-at-zero eliminated |
| gas (TWh) | +0.351 | +0.361 | +0.176 | S1: C5a-aligned |
| CA λ | −0.50 % | −1.24 % | −0.22 % | S1: C3a-aligned (toward actual) |

The overnight moved **−151/−157/−97 MW — 1.2-3× the fixed-λ prediction**:
removing the RoR budget from the shapeable pool plus reconciling the floor
raised the reservoir pool's marginal water value into the overnight λ band,
the one channel FINDING-caiso125 §1-§3 proved no within-envelope lever could
reach and the one thing the no-feedback proxy could not measure. The
caiso-124 profile-r trap did not recur: the pre-registered D-1-pair gate
(profile_r ≥ 0.8 absolute + amplitude improvement) PASSES all years,
including 2025 where raw r declines 0.985 → 0.977 — exactly the case the
corrected gate was designed to score honestly.

Mechanism accounting is clean: D-4 off-window 0.0000 for `hydro_ror_flat`
AND `hydro_min_flow` (all years); D-2 forced shares 12.0/11.1/10.0 %
(RoR flat) + 16.2/16.6/14.5 % (reconciled floor) of the hydro class —
non-thermal, C8 untouched (PASS). Arm A reproduces the committed
`caiso124_control_A` **digit-for-digit** (max hourly hydro delta 0.000 MW,
λ identical), so the default-off code is byte-inert on the keeper recipe and
the `dc72d7b..HEAD` window carries no basis caveat.

## §3 — why it is KILLED anyway (both kills pre-registered)

**K1 — evening starvation (the load-bearing kill).** B's evening lands
−251/−376/−264 MW *below* measured (arm A: +126/−114/+5); 2024 breaches the
±300 bound. The family's forced base (RoR flat + reconciled Q95 floor ≈
28/28/24 % of the water) holds the belly and overnight nearer reality, and
the LP re-optimizes the *shapeable remainder* against its own λ surface —
whose evening−overnight premium is compressed ~2× (caiso-125 §4b: model
+9.0/+5.0/+2.8 $/MWh vs implied real +15.6/+9.9/+5.3). At half the real
premium the LP under-values the evening peak and pays the belly floor out of
it — the same channel that killed caiso-124 (K3), now caught by the explicit
evening-window kill instead of a shape proxy. **This is not fixable
hydro-side** (rule 1): with ~72-76 % of the water still economically shaped,
any hydro-side patch that forces the evening would pin the measured outcome
(rule 13). The evening λ-formation lane (caiso-103→108, hub separation /
spread compression) is the prerequisite; this family should be RE-TESTED
unchanged once that lane lands a structural fix.

**K4 — the nameplate-clip clause (formal).** Measured pre-solve: the flat
level's nameplate clip discards 1.335/1.269/0.169 % of the RoR class budget
(30/28/15 plant-months) vs the pre-registered 1 % bound — fired for 2023/24.
Substantively the control shares the identical under-delivery (a plant-month
with budget > nameplate-hours cannot deliver it in ANY arm — the LP is
bounded by pmax), so the clip changes nothing relative to A; the root cause
is the uniform EIA-930 fleet-wide monthly scale factor inflating small-plant
budgets above nameplate-hours. Per the caiso-124 discipline the gate stands
as scored; the fix (nameplate-aware budget scaling) is an ISO-generic
`load_hydro_budget` change needing its own lane, never a mid-A/B amendment.

## §4 — rubric (reported, not gated — rule 1)

Arm B official (`calibration_verdict`, registered artifacts): **NOT-YET**,
fail {C3a-2025 +10.9 %, C3c, C5a −11.0/−10.3/−13.5 %}; C1/C2/C3b/C4/C7/C8
PASS; C6 UNATTESTED (probe). C3a-2025 is the caiso-123 attributed extract
basis (arm A's λ reads the same +1.0 % control class); the family's own λ
effect is −0.50/−1.24/−0.22 % *toward* the actual. C5a moves the right way
but only ~+0.2 pp (the +0.35 TWh/yr gas recovery is ~5 % of the 6-8 TWh
C5a gas deficit — the overnight hydro excess was a live but minor
contributor; the import/gas substitution lane (caiso-109/111) remains the
main line). S3 h>$200: 0 hours in both arms (unchanged).

## §5 — rule-22 LOYO record

Zero fitted parameters (categorical external classifier; the plant's own
budget as the level; the frozen caiso-124 percentile) ⇒ LOYO reduces to
per-year gate consistency (PREREG §7): overnight/belly/amplitude improve in
**every year independently**; the K1 breach is confined to 2024 but the
evening degradation is same-signed in all three years (−377/−262/−269 MW of
movement) — the kill is a systematic mechanism property, not a single-year
artifact. No re-tuning against any year occurred (nothing to tune).

## §6 — disposition

1. **Keeper UNCHANGED**; B registered as REJECTED probe
   `2026-07-27-caiso-126-ror-split`; arm A unregistered; retention pruned
   `2026-07-18-caiso-97-evening-trim`.
2. **The mechanism + classifier stay in the tree, default off** (byte-inert
   off, proven digit-for-digit): the family is the structurally correct
   hydro-side representation (rule 1) awaiting the evening λ-formation
   prerequisite. Its re-test is a one-flag replay once that lane lands.
3. **caiso-124's floor re-test is complete** (inside this family, as
   caiso-125 §6.2 chartered): the floor's belly fix survives reconciliation
   (P2 PASS with the pair-gate clean), and its evening-payment defect is now
   attributed to the spread compression, not the floor's own level.
4. **Follow-ups raised, not armed**: (a) the evening λ-formation lane is the
   blocker for the entire hydro family — priority; (b) the EIA-930
   scale-factor / nameplate inconsistency (K4's root cause) — small,
   ISO-generic, own lane; (c) the classifier's 4 pondage-peaker FNs
   (Pit 5, Cresta, San Joaquin 2) mis-classify ~2 % of budget — immaterial
   now, revisit only with a new external vintage (rule 21).

## §7 — DO-NOT-REDO (this lane, additions)

- Re-deriving the RoR classification from CF or any model/residual quantity
  (rule 13/24; the external intake exists precisely to replace it).
- Re-running this A/B at the same spread compression (the K1 outcome is
  determined by the §3 channel; re-test belongs AFTER an evening λ fix).
- Widening/moving K1 or the P1 150 MW bound post-hoc (caiso-124 lesson).
- A hydro-side evening floor/pin to offset the starvation (rule 13 outcome
  pin by construction).
- Re-measuring the nameplate-clip loss (quantified here; its fix is a data
  lane, not a gate amendment).

## §8 — ADDENDUM (same session, later): OWNER PROMOTION

After this finding was written, the owner authorized promotion on the
"performs better or is more structurally sound" criterion (rule 1
[R-STRUCT] / rule 14 [R-ACCURATE]). Decision facts, measured before
promoting:

1. **Structure**: B replaces falsified physics (a fully-shapeable hydro
   fleet parking at 0 MW for 270-692 h/yr against a measured p5 of
   738-954 MW) with an external, categorical, zero-DOF classification; all
   forcing declared, D-4 clean, C6 attested.
2. **Performance, honest same-basis comparison** (arm A at the same HEAD):
   better on overnight, belly, amplitude, parks-at-zero, budget
   utilisation, gas volume (C5a direction) and λ level (C3a direction);
   worse only on the evening hydro volume window.
3. **The evening starvation is λ-neutral** (evening λ +0.09/−0.01/+0.05
   $/MWh; the hub-priced import rung sets the evening price, caiso-105) —
   a volume-shape cost created by removing the unphysical compensator,
   rule 14's exact "the estimate was silently compensating" case. The
   spread-compression root cause is chartered (caiso-127) and this keeper
   is the honest base to fix it on.
4. **The prior keeper's C3a-2025 PASS was non-reproducible** (caiso-123:
   partial-extract basis, a rule-13 reproducibility failure baked into the
   committed bundle). This keeper scores FAIL +10.9 % on the honest
   full-derivation basis — the paper regression is the removal of an
   artifact, deliberately NOT ledgered as an attestation exception while
   the neiso-66 freeze holds.

**The as-armed prereg verdict (K1 + K4) stands recorded and unedited**; the
promotion is a separate owner act on structural-fidelity grounds, exactly
the rule-1 clause ("a run is a keeper because it is the most structurally
faithful, not because it has the lowest MAE — a more-accurate run that is
missing real structure is not a keeper"). Keeper set to
`2026-07-27-caiso-126-ror-split` (keepers/CAISO.json), attestation written
(zero-DOF ledger carry), status rebuilt (NOT-YET, fail {C3a-2025, C3c,
C5a}), `audit_keepers --iso CAISO` PASS.
