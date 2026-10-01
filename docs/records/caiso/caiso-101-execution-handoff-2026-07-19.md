# CAISO-101 handoff — both asks GRANTED and executed; keeper = caiso-101 (WP-3 CHP steam level); cycling-cost REJECTED with the inelastic-volume finding

**Session 2026-07-19 (CAISO-101) outcome:** the owner ruled BOTH pending asks
GRANTED in-session. (1) The caiso-100 cycling-cost B-leg executed per
FINDING-caiso100 §6 → **REJECTED PROBE** on the pre-registered volume gates
(`2026-07-19-caiso-100-cycling-cost`); en route it exposed and fixed the
hidden unrecorded CAISO $5/MWh `run_year` adder fallback + prb-channel stomp
(issue #2546, FINDING-caiso100 §8). (2) WP-3 CT_CHP steam-level re-derive at
scope (a)+(b) executed → **PROMOTED to CAISO keeper**
(`2026-07-19-caiso-101-chp-steam`, bundle `caiso101_wp3_B`): C3a FAIL→PASS,
C5a improves every year, LOYO ≤4.6 % class-level. Determination NOT-YET,
fail set **{C3c, C4, C5a(2024 CAVEAT)}**. Calibration-log entry: 2026-07-19
caiso-101. Registry 14/15 (caiso-80 pair pruned).

## What CAISO-101 established (do not re-derive)

- **Battery charge volume is INELASTIC to marginal cost.** The measured fleet
  buys its full volume at a revealed $11-17/MWh conduct cost; pricing that
  cost as a marginal bid adder ($14.25 derived) collapses model throughput
  below the ±15 % guard in every year while fixing the belly price. The
  belly's remaining over-price is an inelastic-conduct phenomenon (DA-award
  allocation, RA/AS obligation charging), NOT a bid-ladder level. Any future
  charge-economics mechanism must hold volume while re-pricing the margin.
- The keeper lineage's live battery adder was $5 (hidden fallback), not 0.
  run_config now records the effective value; the prb channel governs when it
  carries the key. The $5 literal's disposition is an OPEN owner ask
  (issue #2546): delete (byte-behavior change, needs re-gate) vs migrate to a
  registered default.
- The CT_CHP class is now level-correct (gap −0.57/−0.48/+0.20 TWh vs
  −1.8/−1.8/−1.1): lens (a) loading-when-on + lens (b) EIA-923
  delivery-implied level, `steam_level_cf` in `thermal_tranches_CAISO.csv`,
  reader `fleet.thermal_tranche_chp_steam_level`. Frozen per rule 23.
- Evening under-price DEEPENED with the CHP baseload (−5.8/−4.9/−3.0): the
  evening merit stack is now the largest λ-ladder residual.

## Paste-ready next-session prompt

```
<<<CAISO-102 — INELASTIC-CHARGE DERIVE / EVENING MERIT RESIDUAL>>>
MODEL ASSIGNMENT: Opus or Fable (core-infra scope possible; CLAUDE.md rule 26).

STATE (2026-07-19, post-CAISO-101): CAISO keeper = 2026-07-19-caiso-101-chp-steam
(WP-3 CHP steam level, PROMOTED), NOT-YET, fail {C3c, C4, C5a(2024 CAVEAT)};
C1 12/12, C2/C3a/C3b/C6/C7/C8 PASS — C3a is OUT of the fail set for the first
time. caiso-100 cycling adder REJECTED (volume collapse; measured charge volume
is inelastic to marginal cost — FINDING-caiso100 s6/s8 + the caiso-101 log
entry). Hidden $5 adder fallback discovered/fixed/recorded (issue #2546, owner
disposition OPEN). Evening resid deepened to -5.8/-4.9/-3.0 (largest ladder
residual); belly +6.0/+6.6/+5.0 remains (inelastic-conduct channels).

DO (priority):
1. DERIVE-FIRST re-charter of the residual belly on the inelastic-conduct
   channels, armed with the caiso-101 inelasticity finding: measure (a) the
   DA-award allocation of battery charge (DA vs RT award split at the fleet
   grain available), (b) AS-deployment charging variance, (c) the
   shoulder/overnight inelastic charge (the -4/-8% annual under-charge OUTSIDE
   the belly). NO LP until a channel is measured (caiso-93/94 protocol); file
   an owner ask for any mechanism.
2. Evening merit-stack diagnosis (the -5.8/-4.9/-3.0): who serves the measured
   evening that the model prices too cheap — decompose by class/fuel on the
   same-machine keeper repro (reuse caiso101_wp3_B if same machine, else fresh
   repro; the FINDING-caiso92b protocol).
3. Issue #2546 owner ruling if carried: the $5 fallback literal (delete +
   re-gate vs registered default) + pre-caiso-99 record corrections.

GUARDRAILS: all 3 years one bundle (rule 16); NO twin (rule 21); SEQUENTIAL
solves (~23 min/leg, 15 GB box OOMs on 2 concurrent); solves IN-SESSION only
(billed CI). Step 0 fresh container: .venv/bin/python scripts/regenerate_clean.py
(~10 min), confirm data/clean/confirmed-retirements/CAISO/ exists.

DO NOT REDO (caiso-100/101 + prior): any battery adder value (14.25 REJECTED on
volume gates; no sweep, rule 25 — the mechanism family "marginal bid adder" is
volume-refuted, not just the value); the day-threshold hypothesis (CLOSED);
re-deriving the WP-3 steam level or its LOYO (frozen rule 23; steam_level_cf
committed); the p25 statistic (superseded, deleted); tightening the caiso-99
shape envelope; re-arming caiso_storage_as_reservation; the
caiso-94/96/97/99/101 mechanisms or derive gates (frozen); widening caiso-87;
more CC commitment forcing; CT_PEAKER floor; cutting CC offer costs; any year
outside 2023-2025 (rule 22 — no CAISO calibration-complete marker).

GIT: main advances fast -> git fetch origin main + rebase BEFORE push (expect
the calibration-log append-append conflict; keep BOTH entries; keepers.json has
BOTH a top-level ISO field AND a "keepers" array — update BOTH on any swap, the
array is what audit_keepers/build_status consume). git push WORKS on this
machine class; blob-verify pushed sources >=300 lines by SHA (rule 27).
<<<END>>>
```
