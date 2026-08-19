# RESULT nyiso-146 — per-plant measured min-run: floors delivered EXACTLY, object UNMOVED. REJECTED on its own gates, and the rejection is the finding.

Session nyiso-146. Keeper at HEAD **unchanged**:
`2026-08-18-nyiso-144-layup-exclusion` (CALIBRATED, C3c the lone ledgered
caveat). Both arms solved 2023+2024+2025 in one bundle each (rule 16), years
sequential, arms sequential (rule 12); holdout freeze ACTIVE and untouched
(rule 22). Pre-registration committed BEFORE either solve:
`PREREG-nyiso146-perplant-min-run-2026-08-19.md` (+ two pre-solve amendments,
each committed before the arm was launched). Both arms REGISTERED (rule 15):
**`2026-08-19-nyiso-146-control`** / **`2026-08-19-nyiso-146-perplant-minrun`**.
Gates record: `_nyiso146_ab_gates.json`.

## 1. VERDICT — REJECTED per the pre-registered promote criterion

| gate | verdict | one line |
|---|---|---|
| K1 exactness | **PASS** | exactly one field differs: `nyiso_gas_bridge_plant_min_run` False → True |
| K2(a) floor delivery | **PASS-with-one-edge** | all 15 per-plant arm/control ratios inside ±25 % of prediction; 5 of 6 leg totals inside ±5 %; the gas_st-2025 leg lands +5.3 % vs the rebased prediction (band edge; the CC legs, 92 % of the volume, land at −0.3 to +2.1 %). D-4 corroboration passes every year. |
| K2(b) start bands | **FAIL** | Bethlehem P1 starts 327→302 / 526→476 / 262→250 = −7.6 / −9.5 / −4.6 % against bars of ≥50 / ≥10 / ≥10 % |
| K3(a) the object | **FAIL** | 2539 median run length 12→12 / 7→7 / 14→**12** h — flat, falls in 2025 |
| K3(b)(c) no-degrade | PASS | full cohort inside bands; Flynn +4.9/+5.8/+3.9 % ≤ +25 % |
| K4 D-4/D-2 (K6′) | **FAIL** | ONE new D-4 unit-conduct failure: 54574 Saranac 2024 (its measured p25 of 14 h < class 21 h shrinks its floor and the redistributed binding hours land on zero-metered hours); escalation fired (CC forced share 4.4→6.3 % in 2023) and leg (a) is violated |
| K5 gated criteria | PASS | the FULL production verdicts are line-identical but for the SKIPPED DA diagnostic (mean LMP −0.6 %): C1/C2/C3a/C3b/C4/C8 PASS both arms, **C3c bit-identical 2/0/5 h**, C6 UNATTESTED (probe-normal) |
| K6(a) LOYO | PASS | cleared ex ante in the prereg |

**The mechanism did exactly what it was identified to do and it did not repair
the object.** That combination is what makes this a finding rather than a
plumbing failure: the floor rose 685→1,329 / 567→686 / 492→611 GWh at
Bethlehem (ratios 1.94/1.21/1.24, within the predicted bands), the runs it
merges merged — and P1 still starts the plant 250-476 times a year against
6-7 metered.

## 2. THE DIAGNOSIS — where the fragmentation actually lives

The min-run extension (and every gap-bridge leg) floors only hours the unit
was **OFF in the base-cost P0 pattern**. Measured on the arm's own bundles:

* Bethlehem's floored-union on-share (P0-on ∪ floor) rose 0.64 → 0.92 (2023),
  exactly as predicted — the P0-side fragmentation is glued.
* Its P1 starts barely moved, because **P1's bid-cost pass shuts the plant
  inside P0-committed hours**, where no gap/extension floor exists. The
  startup-amortized markup re-prices the upper tranches, the LP decommits
  mid-run, and the pattern shatters *above* the floor.

This is precisely the state the ercot141 `floor_online_hours` detector leg was
built for (its own docstring: "a synchronized thermal unit cannot operate
below its minimum stable load, so its LSL block is must-take in EVERY online
hour, not only the ones between two runs" — the gap legs model the *restart*
decision; that leg models the STATE the gaps interpolate between). The leg is
ISO-scoped to ERCOT (`ercot_gas_bridge_online_hours`) and NYISO has never
tested it (rule 25 — no transfer; NYISO must test on its own evidence, which
this A/B now supplies). **That is the named successor lever, chartered in
PREREG-nyiso146b.**

## 3. WHAT STANDS

* **The phase-0 measurement stands regardless of the rejection**: the CC class
  is not one run-length population (per-plant p25 7 → 646 h, 92× spread;
  ST_GAS 2.5 → 213 h), and the identification artifact
  (`campd_perplant_min_run_NYISO.csv`, rule 23) is frozen, correct, and
  reusable — the min-run VALUES were never the defect; the mechanism's REACH
  was.
* The `nyiso_gas_bridge_plant_min_run` field stays in `ScenarioConfig`,
  default **off**, cell verdict **R** in the NYISO shard.
* The K4 conviction (Saranac 2024) is a real protective catch: a shorter
  measured min-run redistributes floor onto hours the meter says the plant was
  off — the per-plant values must ride a mechanism that also holds the ON
  state, or not at all.

## 4. GOVERNANCE

* Rule 15: both arms registered whatever the outcome — done, same session.
* Rule 28(b): NYISO shard cell updated (rejection + citation) — same session.
* Rule 1: the rejection is NOT "the residual didn't move" — the fit was
  essentially unchanged (K5); the arm is rejected because it fails its own
  pre-registered object gates and adds a D-4 conviction.
* No promotion; keeper, `complete` marker and freeze untouched.

## 5. REPRODUCTION

```
python scripts/probes/_nyiso146_perplant_minrun_phase0.py
python scripts/data/derive_campd_perplant_min_run.py --iso NYISO
python scripts/probes/_nyiso146_k2_prediction.py
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso144_layup_arm --out-dir results/calibration/nyiso146_control
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso146_arm_recipe --out-dir results/calibration/nyiso146_perplant_arm
python scripts/probes/_nyiso146_ab_gates.py
```
