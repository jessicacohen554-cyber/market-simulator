# FINDING — caiso-256 (second object): the CT-only partition arm was SCREENED on 2023 and **DIES ON S-1 BY THE REGISTERED RULE** — CT_PEAKER energy rose **+219.8 GWh** (1.645 → 1.864 TWh, the right direction, footprint confined, C1 and C4 unchanged) against a pre-registered floor of **311.8 GWh**. The full span is NOT spent; the artifact pair is REVERTED to the frozen construction, exactly as `df277e89`'s own stop rule says. **Escalated to the owner with the estimator's disclosed bias measured, not argued.** Keeper UNCHANGED.

**Session caiso-256, 2026-09-06.** Branch
`claude/caiso-storage-over-cycling-ymodu3`. Keeper
**`2026-09-05-caiso-252-b1-notrim`** UNCHANGED, DETERMINATION **CALIBRATED**
(re-verified at HEAD, rubric v3.6, `ADDENDUM-caiso256 §2`). Pre-registration:
`PRECOMMIT-caiso255-ct-only-partition-adoption-2026-09-06.md` (the owner's
grant, merged) + `ADDENDUM-caiso256-partition-screen-2026-09-06.md`
(`5ca18bf3`, pushed before the screen launched, fixing S-1's number). Rule 22:
2023–2025 only; no marker; freeze ACTIVE. **ONE LP-year spent** (the screen);
the screen bundle `results/calibration/caiso256_screen2023` is **deleted**
before this PR merges (rule 29(c)); every number it produced is below and in
`results/calibration/_caiso256_screen2023.json`.

---

## §1 — THE SCREEN, SCORED (G-CTRL form 4: the keeper's committed bundle is the control)

**Preconditions (ADDENDUM §3) — ALL PASS.** `resolved_inputs.seam_import_cap`
= `mic_partition` **16,055 MW** (the `capacity-deliverability` partition was
materialised first; without it the rebuild had warned it would solve on the
baked 7,500); `hydro_plant_modes.partition_present = true`, flag off;
`campd_unit_outages` and `thermal_tranches` sha256 identical to the keeper's;
driver log **"P1 route: COLD REBUILD"** (P0 471 s cold, objective
3,681,906,464.8; P1 547 s cold, 3,930,332,111.6) — the P1 basis seed
unreached, as `ADDENDUM-caiso255-solve-path-correction` said it would be.

| gate | registered | measured | verdict |
|---|---|---|---|
| **S-1** | CT_PEAKER 2023 energy RISES within **[311.8, 2,806.4] GWh** (ΔE_implied 935.5 GWh, factor 3 both ways) | **+219.8 GWh** (1.6447 → 1.8645 TWh, **+13.4 %**); 0 tranches rose | **FAIL — the arm dies here** |
| S-2 | nuclear / hydro / wind / solar each < 0.5 % of keeper energy | **0.0000 / 0.0022 / 0.0000 / 0.0027 %** | PASS |
| S-3 (C1 stop) | no class PASS → FAIL | CC_REGULAR 48.371 (actual 51.837, ±5.27), CC_CHP 8.479 (7.71), CT_PEAKER 1.864 (4.128), ST_GAS 0.081 (1.308) — **no flip** | PASS |
| S-4 (C4 stop) | gas r ≥ 0.70, NRMSE ≤ 0.30 | **0.879 / 0.287** vs keeper 0.880 / 0.285 (recomputed on the same construction: 0.880 / 0.285) | PASS |
| C3a (EXCLUDED) | — | +4.49 % vs keeper +4.65 % (actual RT lw $54.17) | reported |
| C3b | — | 0.0879 vs 0.0878 | reported |

**S-1 is a kill, not an escalation** (PRECOMMIT-caiso255 §7.2: *"FAIL ⇒ the
arm dies here"*). It is scored on the number fixed in `ADDENDUM-caiso256 §4`
before the solve, and **no gate is relaxed, re-run to a pass or redefined
after its result** (PRECOMMIT §5 stop rule 3). The 2024 and 2025 years are
never spent.

## §2 — WHAT THE MECHANISM DID, AND WHAT THE GATE MEASURED

**Everything the repair claims about its footprint is true on the screen.**
The CT bands fell, CT_PEAKER energy rose 13.4 %, ST_GAS fell 0.098 → 0.081 TWh
(through price alone — its offer is inert by construction, caiso-254 §3), the
CC classes gave up 0.188 + 0.014 TWh, imports 0.017 TWh, and the four
non-repriced classes moved by ≤ 0.003 %. C4 did not move (r −0.001, NRMSE
+0.002); C1 did not flip; C3a moved **down** 0.16 pt — the direction hazard
declared in advance, and excluded.

**What failed is the magnitude against a first-order count.** ΔE_implied
counts, for every one of the 784 CT tranches whose offer fell, the hours in
which the keeper's zonal price sat inside that tranche's (mc_new, mc_old]
band, and sums pmax over them. Sibling tranches of one plant
(`p57482_econc00 … econc04`, mc 73.5–76.3) have bands that all contain the same
hours, so the count charges one plant's capacity up to five times per hour;
when the first tranche clears, λ falls and the rest do not. The addendum
disclosed the bias as upward; the registered factor of 3 was the absorber, and
**it was not enough: the measured rise is 0.235 × the count (4.26× smaller),
below the 1/3 floor.**

**POST-HOC, REPORTED ONLY, NEVER SCORED** — computed *after* the verdict, for
the owner's re-charter decision and labelled as such in the probe: the same
count with at most **one tranche's worth of MW per (plant, hour)** gives
**261.5 GWh** over 79 plants. The measured rise is **0.84 ×** that. On a
plant-deduplicated estimator the arm would have sat inside a factor-3 band
(87–784 GWh) with room to spare. **That number does not and cannot change this
session's verdict**: choosing the estimator that passes after seeing both is
exactly the selection rule 29 and the PRECOMMIT's stop rule 3 forbid. It is
recorded so the owner can decide, on the merits, whether S-1 was measuring the
mechanism or the estimator.

## §3 — WHERE THE 220 GWh WENT: the rise deepens a KNOWN mis-allocation

CT_PEAKER by hour of day, arm vs keeper (2023 mean MW): the whole rise is the
evening ramp and evening peak — hod 16–23 **+32 / +68 / +78 / +87 / +89 / +75 /
+53 / +37 MW** — and Jul–Dec (35 / 34 / 28 / 31 / 22 / 29 GWh) with Jan–Feb
≈ 0. By plant, the arm's CT energy is **p57482 462 GWh, p57515 375, p57555
281** (the three LA-basin / SDGE peakers) against **Panoche 56803 at 172** —
i.e. the repair puts more energy into precisely the plants `FINDING-caiso252
§3.3` identified as clearing into the evening *instead of* the one plant that
carries the real CT energy, and `caiso-252 §7 #4` forbids reaching Panoche by
re-pricing the class. So even had S-1 cleared, the arm was moving the CT class
toward its C1 actual (4.128 TWh) through the wrong plants — a structural
observation worth more than the gate result, and one no estimator would have
changed.

## §4 — DISPOSITION: THE STOP RULE, EXECUTED

`df277e89`'s own commit message: *"If the screen's structural gates kill the
arm, this artifact is reverted and the frozen 2026-08-02 construction stands —
that is the registered stop rule."* Executed on this branch:
`data/raw/_validation-source/caiso_offer_curve_measured.json`,
`caiso_offer_surface_condbinned.json` and `caiso_offer_surface_summary.csv`
are restored **byte-exactly to `fa23c1f7`** (the keeper's solve basis), so a
keeper replay at HEAD is again the keeper. The repaired pair stays in git
history at `df277e89` and is re-applied with one `git checkout df277e89 --
<paths>` if the owner re-charters.

**Nothing is promoted, nothing registered (the screen bundle is a throwaway
probe, deleted), the keeper does not move, no `ScenarioConfig` field, no
`complete` marker.** The owner's grant of OPTION 1 is neither spent nor
withdrawn by this session: its *first screen* was run and the arm failed the
gate as registered.

## §5 — RAISED TO THE OWNER, NOT DECIDED HERE

1. **Re-charter S-1 on a plant-deduplicated estimator?** The grant, the
   corpus, the derive, the artifact (in history) and the phase-0 naming are all
   intact; a re-charter costs one PRECOMMIT addendum naming the new estimator
   *before* a new screen, plus one LP-year — and the screen's other gates
   already pass. §2's post-hoc number is the information; the choice is yours,
   because I have seen the result.
2. **Whether the arm is wanted at all given §3.** The rise lands on the three
   LA-basin / SDGE peakers, not Panoche; the CT volume miss is Panoche's
   (caiso-252). A repair that de-contaminates the bucket correctly and still
   allocates the energy to the wrong plants is structurally right about the
   *offer* and silent about the *plant* — that may still be worth adopting
   (the offer is measured; the allocation is a different object), but it is a
   judgment, not a gate.

## §6 — DISCLOSURES AGAINST INTEREST

1. **The estimator that killed the arm was mine**, written this session and
   fixed before the solve with its bias stated. It over-counted by 4.26× on a
   mechanism whose direction, footprint and non-target invariants all held.
   Had I registered the plant-deduplicated form, the arm would have cleared.
   I did not, and the registered one governs.
2. **I computed the post-hoc estimate knowing the answer.** It is labelled
   POST-HOC in the probe, the artifact and here, and it does no scoring work.
3. The handoff said the partition object's only blocker was a ~110-minute
   corpus re-fetch; it was not — the artifact was already on `main`. That was
   found by reading `git log` on the artifact, not asserted.
4. The screen bundle's `legitimacy_diagnostics.json` reports D-4 FAIL rows for
   `chp_steam` (h0–23) exactly as the keeper's does; the CHP classes are
   D-2-exempt and C8 passes on the keeper at HEAD. Reported, not scored on
   a screen.
5. **One LP-year was spent (the screen); 2024/2025 were not.** Rule 29(1)–(2)
   as written.

## §7 — DO-NOT-REDO ADDS

1. **Never register a price-held-fixed tranche count as a displacement gate
   without deduplicating sibling tranches of one plant.** Measured here: 4.26×
   over-count on 784 tranches / 79 plants.
2. **Never read S-1's failure as "the repair does not move CT_PEAKER".** It
   moved it +13.4 % in the registered direction with a confined footprint; what
   failed was a magnitude gate on a disclosed-biased estimator.
3. **Never re-apply `df277e89` without a pre-registered screen** — the stop
   rule it carries has now fired once.
4. **Never quote the arm's C3a −0.16 pt as evidence for it.** Excluded, and
   the declared hazard.
5. caiso-256 (storage) §6, caiso-255b §6, caiso-254 §6, caiso-253 §7,
   caiso-252 §7 and §12, and the chain they carry stand in full.

## §8 — DELIVERABLES

`ADDENDUM-caiso256-partition-screen-2026-09-06.md` (pushed first);
`scripts/probes/_caiso256_s1_implied_displacement.py` +
`_caiso256_s1_implied_displacement.json` (registered count, post-hoc field
labelled); `scripts/probes/_caiso256_screen2023.py` +
`_caiso256_screen2023.json`;
`_caiso256_gdrift_input_identity_artifact_reverted.json`; the artifact pair
reverted to `fa23c1f7` (an attestation generator was drafted for the full-span
bundle and deleted with it — superseded per-run scripts are deleted, never
archived); this finding; the
calibration-log entry; the matrix shard evidence append
(`measured_offer_surface`, no verdict move). Screen bundle deleted.
