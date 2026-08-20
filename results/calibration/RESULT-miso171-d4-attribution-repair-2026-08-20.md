# RESULT miso-171 (carry-forward a) — the D-4/D-2 plant-grain class-attribution defect is REPAIRED at unit grain, and every designated keeper re-scores with ZERO determination movement

**Session miso-171 (2026-08-20), the charter's carry-forward item (a). NO LP
SPENT — the repair is scorer-side (`scripts/legitimacy_diagnostics.py`), the
re-score is regeneration + verdict runs over committed bundles, and every
bundle is byte-identical after the measurement (the harness swaps
`legitimacy_diagnostics.json` in place and restores it).** Record:
`results/calibration/_miso171_d4_attribution_rescore.json`, harness
`scripts/probes/_miso171_d4_attribution_rescore.py`, 5 regression tests in
`tests/scoring/test_legitimacy_diagnostics.py` (97 pass).

## 1. The defect and the repair

`aggregate_floors_by_plant` labels a plant row with its **most-common unit
group**, so a mixed-class site's floor carried by a MINORITY-class unit was
charged to the majority class's C8 legs — the D-2 mechanism rows (budget
numerator + the mechanism list `_d4_provenance` walks) and the D-4
(mechanism × class) window/conduct selection. The live case (miso-170 K-1
forensic): plant 1104's CT_PEAKER netload floor was tested, and convicted,
under **ST_GAS's** D-4 conduct row in every pre-repair MISO artifact.

The repair is `FloorClassMatrix`: the plant-hour **floor class** under the
SAME maximum-composition rule the plant-hour mechanism already uses — the
class of the unit contributing the largest floor that hour, empty unit groups
imputed to the plant majority first (the #1488 rule unchanged, so
single-class plants attribute exactly as before). D-2 attribution and D-4
selection key on it; class DENOMINATORS stay on the row label (the dispatch
grain — at-floor plant-hours have dispatch ≈ the floor, so the re-attributed
numerator is the floored slice's own energy to within the at-floor
tolerance). The pre-repair rule is preserved behind `floor_klass=None`, so
direct callers and legacy artifacts re-score byte-identically. Of the
charter's two repair options, this is the "split to (mechanism, class) at
unit grain" one; the alternative ("gate the conduct rider on the floor's own
declared window") was not taken because it repairs only the conduct-rider
half — the D-2 mechanism list would still route a mixed site's minority
floor into the wrong class's provenance leg.

## 2. The re-score, every designated keeper (before = regen at HEAD-sans-repair, after = regen at HEAD; both share one rebuilt-floors baseline)

| ISO | committed | before | after | before→after movement |
|---|---|---|---|---|
| ERCOT `2026-08-19-ercot221-arm-adaptive` | NOT-YET / C8 PASS | NOT-YET / C8 PASS | NOT-YET / C8 PASS | **zero deltas** (no mixed-class floored plants) |
| PJM `2026-08-15-pjm-162-inputclock` | CALIBRATED / C8 PASS | NOT-YET / C8 FAIL | NOT-YET / C8 FAIL | **3 C8 records FAIL→PASS** (§3); determination unchanged |
| CAISO `2026-08-17-caiso-200-h1-memberpanel` | NOT-YET / C8 PASS | NOT-YET / C8 PASS | NOT-YET / C8 PASS | zero deltas |
| NYISO `2026-08-19-nyiso-146c-state-scoped` | CALIBRATED / C8 PASS | CALIBRATED / C8 PASS | CALIBRATED / C8 PASS | zero deltas |
| NEISO `2026-08-17-neiso-99-joint-p1` | CALIBRATED / C8 PASS | CALIBRATED / C8 PASS | CALIBRATED / C8 PASS | zero deltas |
| MISO `2026-08-19-miso-170-sitegrain` | NOT-YET / C8 FAIL | NOT-YET / C8 FAIL | NOT-YET / C8 FAIL | attribution moves (§3); zero C8 record flips |

**DETERMINATION FLIPS before→after: NONE, in any ISO.** The charter's
escalation trigger ("a flip in another ISO is an owner escalation") does not
fire.

## 3. What actually moves — the two mirror-image mixed-site cases

* **MISO** (the chartering case): ~0.24–0.34 TWh/yr of `reliability_floor`
  energy moves from ST_GAS and CC_REGULAR onto CT_PEAKER, its true carrier.
  ST_GAS budget shares 31.2/31.9/43.6 % → 30.5/31.0/42.6 % (still FAIL —
  1402's window defect, the real C8-2023 blocker, is untouched as expected).
  CT_PEAKER-2023 lands at 15.17 % vs its 15 % cap — over budget by the width
  of the re-attribution — and **grounds cleanly** (its mechanisms clear D-4,
  its D-1 shape clears), so its C8 record stays PASS. The phantom
  `reliability_floor × ST_GAS` D-4 rows (incl. plant 990's conduct rows)
  disappear. Zero C8 record flips.
* **PJM** (the mirror image, found by the re-score): mixed sites labeled
  CT_PEAKER carrying ST_GAS floors had inflated CT_PEAKER's budget leg to
  16.4/16.8/16.8 % — over its 15 % cap in ALL THREE YEARS of the regen
  baseline, whose conditional pass then failed. The repair returns that
  energy to ST_GAS (52.6→64.7, 49.0→58.3, 40.0→50.6 %, all grounding via the
  rule-20 provenance+shape path except the pre-existing 2025 failure below)
  and CT_PEAKER passes its budget outright (10.9/12.6/11.3 %):
  **C8 CT_PEAKER 2023/2024/2025 FAIL→PASS.** The repair un-convicts a
  mis-attributed class — the same defect, opposite sign.

## 4. Pre-existing exposure DISCLOSED, not created (and not repaired) here

The committed-vs-regenerated gap the miso-169 K-3 caveat first put before
the owner is now measured at PJM too: on the shared regen baseline (either
code version) the PJM keeper scores **NOT-YET on forced_share — ST_GAS-2025
C8 FAIL — while its committed artifact reads CALIBRATED**. This is the
rebuild-path/nyiso-143-rider exposure family (regenerated diagnostics differ
from the keeper's committed, solve-time diagnostics; the rebuilt floors also
exclude the P1-dependent RA bridge and the chp_steam layer, both disclosed
in the artifact's own notes), it predates this session's change, and this
repair narrows it at PJM (three of the four regen-baseline C8 failures were
the mis-attribution). **Owner-relevant, unresolved: any freshly regenerated
PJM diagnostics artifact would fail C8 on ST_GAS-2025 at HEAD.** CAISO's
regen baseline likewise carries 23 D-4 row failures absent from its
committed artifact (C8 and determination unchanged there).

## 5. Carry-forward items raised, not decided (charter §4 b–d)

* **(b) 1402 per-year `online_frac`** — MISO's sole C8 blocker, a REAL
  window defect (pooled 0.508 vs per-year metered 0.2495/0.6134/0.6548).
  Needs its own prereg, its own A/B solve pair, its own DOF answer. NOT
  attempted here (an LP lane, not a scorer lane). 1402 is never added to
  the lay-up census (rules 1/14; the line has held three times).
* **(c) Ames (1122) p25-level basis** — `p25_cf = 0.674` reconstructs
  against NAMEPLATE while the measured p25-of-online is 33 MW = 0.304 of
  nameplate (0.674 × its ~49 MW available-capacity base = 33.0 exactly).
  Own identification, own A/B; never an exclusion (the floor is right in
  kind, wrong in LEVEL). Plausibly reaches other deep-derate ST_GAS plants.
* **(d) Two C8 rubric design questions — OWNER decisions, raised with the
  measurements, rubric NOT amended:** (i) the forced-share denominator is
  the model's own class output, so MISO's gate moved 31 % → 44 % in 2025 on
  a year-invariant floor purely because gas went $2.19 → $3.52 and economic
  output shrank around it; this session adds a second sensitivity
  measurement — the MISO CT_PEAKER-2023 budget leg lands at 15.17 % vs a
  15 % cap purely on attribution grain, i.e. the cap is knife-edge-sensitive
  to instrument conventions; (ii) there is no materiality floor INSIDE the
  provenance leg, so a plant contributing 0.005 % of class energy can fail
  the whole class (the miso-169 K-3 four-tiny-plants case).

## 6. Reproduction

Regenerate D2/D4 for a keeper bundle at each code version
(`--only D2 D4 --json-out …`; the "before" is `git show
3e1ac27~1:scripts/legitimacy_diagnostics.py`), then
`python3 scripts/probes/_miso171_d4_attribution_rescore.py --variants-dir
<dir> --isos ERCOT PJM CAISO NYISO NEISO MISO`. Requires the ISO data
profiles (floors rebuild via `run_year(fleet_only=True)`), the clean
partitions `capacity-deliverability`, `transfer-interface-limits`,
`ramp-capability`, `nyiso-interface-flows` (`scripts/regenerate_clean.py`),
and the gitignored `pjm-da-virtuals` corpus re-fetched
(`scripts/data/fetch_pjm_da_virtuals.py`).
