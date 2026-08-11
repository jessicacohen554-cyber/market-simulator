# FINDING — caiso-194 (close-out campaign LANE 4): the `hydro_ror_split` classification is **REFUSED at G-SHARE**; the mechanism is proven to ENGAGE, but on an inadmissible partition. **Killed before LP. Keeper untouched.**

**Session:** caiso-194, 2026-08-11. **Branch:** `claude/caiso-194-hydro-ror-split-3s85bx`.
**Gate spec:** `GATESPEC-caiso194-hydro-ror-split-2026-08-11.md` (authored caiso-191,
before any measurement — bands not edited, not reinterpreted).
**Pre-registration:** `PRECHECK-caiso194-hydro-ror-split-2026-08-11.md` (commit `2df253f`,
pushed before the completion rules ran on the unlabeled remainder).

## 0. Direction-hazard clause, quoted verbatim as required

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

**No C3a value appears anywhere in this FINDING, in either direction — no arm was
solved, so none exists.** The refusal below is decided entirely on the pre-registered
structural gates.

## 1. Outcome

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-DET** | deterministic build; `tests/test_curate_hydro_plant_modes.py` green; `validate_clean` passes | data-byte identical across two consecutive runs (content sha256 `af3b82ac…` both); 4/4 tests pass; `validate_clean` passes | **PASS** (with a band-wording escalation, §4) |
| **G-COVER** | ≥ 90 % of CAISO conventional-hydro nameplate classified | **99.9407 %** of 6,740.300 MW | **PASS** |
| **G-SHARE** | full-population non-shapeable capacity share within ±10 pp of the labeled-subset share | **13.4956 %** vs anchor **24.4621 %** → **−10.9665 pp** | **FAIL** |
| **G-ENGAGE** | partition read by the solve, four legs | legs (a)/(b)/data-end proven; legs (c)/(d) not reached — no LP run | **N/A — killed before LP** |
| **G-C3B-WATCH** | C3b watch on the arm | no arm solved | **N/A** |
| **G-SIXISO** | CAISO-only build | `DEFAULT_ISOS = ("CAISO",)`; no other ISO's partition, config, or cell touched | **PASS** |

**GATESPEC §5 kill criterion fires:** *"G-SHARE fails ⇒ the classification is refused;
no arm registered as a keeper candidate; the confrontation reported."*

Accordingly: **no A/B was solved, no bundle produced, no run registered, no promotion
proposed, keeper `2026-08-09-caiso-188-d1-micseam` untouched.** The single-mechanism
statement the GATESPEC requires verbatim is recorded for the record but describes a
delta that was never solved: *"The A/B delta is the hydro-plant-modes partition made
effective under `hydro_ror_split`; no other input differs."*

## 2. The confrontation (G-SHARE), as §5 requires it be reported

The partition builds cleanly — 195 plants, 6,703.125 MW EHA CH, 84 run-of-river-class
and 111 reservoir-class, methods `eha_mode` 97 / `hilarri_reservoir` 78 /
`hilarri_no_reservoir` 13 / `corps_dam` 7 / `hilarri_canal` 0. It fails the provenance
gate:

| population | capacity | non-shapeable share |
|---|---|---|
| EHA `Mode`-labeled subset (anchor, pre-committed) | 2,046.125 MW | **24.4621 %** |
| full population after completion rules | 6,703.125 MW | **13.4956 %** |
| unlabeled remainder alone (rules 2–5 govern) | 4,657.000 MW | **8.6773 %** |

Delta **−10.9665 pp** against a ±10 pp band — a miss of 0.9665 pp. Verified by an
independent recomputation straight from the EHA source, and free of any grain
confound: **zero** EIA plants carry both a labeled and an unlabeled EHA row, so the
anchor and the measurement are the same statistic on disjoint populations.

### 2.1 The failure is NOT a directional bias in the completion rules

The obvious reading — the rules over-assign "shapeable" — is **false**, and measuring
it is what makes this finding worth more than the verdict letter. Scoring rules 2–5
against the EHA labels on the subset where both exist:

* false **shapeable** (truth RoR/canal, rules say shapeable): 8 plants, 93.9 MW
* false **non-shapeable**: 3 plants, 218.2 MW
* on that subset the rules predict **30.5370 %** non-shapeable against a truth of
  24.4621 % — they lean **+6.07 pp toward non-shapeable**, the opposite direction

So on the only set where the rules can be audited they are conservative in the
direction G-SHARE polices, yet they return 8.68 % on the remainder.

### 2.2 What actually drives the gap: the two populations are not alike

EHA labels the *small* plants and leaves the *large reservoir projects* unlabeled:

| population | n | Σ MW | mean | median | max | share held by >100 MW plants |
|---|---|---|---|---|---|---|
| labeled | 97 | 2,046.1 | 21.1 | 5.9 | 253.0 | 42.1 % (6 plants) |
| unlabeled | 99 | 4,657.0 | 47.0 | 12.1 | 351.0 | 59.5 % (16 plants) |

The unlabeled remainder is headed by Edward C Hyatt (Oroville, 351.0 MW), Colgate
(315.0), Devil Canyon (276.2), Mammoth Pool (190.0), Big Creek 3 (174.5), James B
Black (168.6), Pine Flat (165.0, correctly caught as a Corps release-taker by rule 3)
and Dion R Holm (156.8). These are canonical large reservoir/peaking projects, and
classifying them shapeable is *physically* the expected answer — Hyatt is among the
most shapeable hydro plants in California.

**Therefore the measured evidence points at the gate's transfer premise, not at the
classifier.** G-SHARE assumes the labeled subset's non-shapeable share is the right
expectation for the full population; the two populations differ by 2.2× in mean unit
size and systematically in project type, so that assumption is not supported by the
source data. This is reported as a confrontation and **escalated** (§4) — it is
explicitly **not** used to rescue the arm. The band is binding, it failed, and the
classification is refused.

## 3. What was nevertheless established: the mechanism DOES engage (caiso-188 closed)

caiso-188 §6 left open whether `hydro_ror_split` has ever run in any CAISO LP —
G-CTRL reproduced the keeper exactly from an environment with no partition. That
question is now answered at the object level, **with no LP and no solve**, by
`scripts/probes/_caiso194_engagement.py` → `_caiso194_engagement.json`:

| year | hydro units built | RoR-stamped off / on | stamped MW (share of fleet) | monthly budget identical off vs on |
|---|---|---|---|---|
| 2023 | 166 | 0 / **67** | 802.3 (12.47 %) | **True** |
| 2024 | 160 | 0 / **61** | 797.0 (12.13 %) | **True** |
| 2025 | 26 | 0 / **3** | 312.8 (7.99 %) | **True** |

With the partition present the classifier **is** read and RoR units **are** stamped
flat at `budget[g, m] / hours[m]` (clipped to nameplate; the clip logs on 23 and 10
plant-months in 2023/2024 — the pre-existing source-data inconsistency the code already
warns about). With it absent, nothing is stamped.

Two things follow. First, **caiso-188's inertness was the absent partition, not a
structurally dead mechanism** — the wiring works. Second, the monthly energy budget is
**bit-identical off vs on in all three years**, confirming the mechanism redistributes
*when* the water runs and never *how much*, which is the rule-13 forward story the
module claims.

The unit tests carry the same result independently:
`TestHydroRoRSplit::test_split_stamps_ror_at_its_own_flat_budget` and
`::test_split_off_is_inert` both **pass** once the fleet's data dependencies are
present.

*(2025's 26-unit fleet is the known truncated EIA-923 early-release vintage — CAISO
retention ~16 % — already documented in the mechanism-matrix `hydro_level_923_hy` /
`hydro_budget_nameplate_aware` notes. It is not a caiso-194 effect and nothing here
depends on it.)*

## 4. Escalations to the owner — NOT resolved in-session, NOT edited

1. **G-DET's literal band is unsatisfiable by construction.** It reads "two
   consecutive curator runs produce byte-identical **partitions**". No clean partition
   of any datatype can satisfy that: `scripts/lib/clean_io.py` stamps
   `market_sim.created_utc` on every write, and documents its own standard at lines
   388–394 — output is *"data-byte identical … Only the provenance metadata differs,
   and only in the fields that are timestamps by construction (`created_utc`)"*.
   Measured here: the two runs' **only** differing bytes are that timestamp; the
   classification content hash is identical (`af3b82ac…`). Recorded as **PASS on the
   repo's own documented determinism standard**, which is also the standard the gate's
   own anchor states ("a plant's hydraulic mode does not depend on the run"). The band
   wording, not the classifier, is what needs the owner's pen.
2. **G-SHARE's transfer premise** (§2.2). The labeled and unlabeled populations differ
   systematically in unit size and project type, so the labeled share may not be a
   sound expectation for the full population. Raised as evidence for the owner; the
   band was applied as written and the arm refused regardless.
3. **Two contradictions between the lane-4 handoff and verifiable state**, reported
   rather than silently resolved:
   * The handoff states "PRECHECK is already discharged by the GATESPEC (say so)."
     The GATESPEC §7 requires a PRECHECK artifact carrying the G-SHARE labeled-subset
     share, and contains no such share. Resolved in the conservative direction: the
     PRECHECK was written and committed before the completion rules ran
     (`2df253f`). Nothing was relaxed.
   * The handoff pins state to `main@6a37611`; `origin/main` at session start was
     **`a3a7cd1`** ("Merge pull request #3874 … miso-152-calibration"). All work here
     is based on `a3a7cd1`. No CAISO-relevant contradiction was found in the state the
     handoff described — the caiso-190 inheritances (`check_clean_partitions` on both
     solve paths, `resolved_inputs.hydro_plant_modes`) are present as described.

## 5. Compliance statements

**RULE 28 `[R-MECH-MATRIX]` statement.** Duty (b) discharged in-session: the CAISO
shard cell for `hydro_ror_split` moves **`K` → `R`** with this FINDING as the citation.
The refusal is at **classification provenance (G-SHARE)** and is explicitly **not** a
dispatch-level refutation of the mechanism — §3 shows it engages correctly. A repaired
or re-anchored classifier is therefore a **new charter**, not a DO-NOT-REDO-frozen
cell; duty (a)'s re-test prohibition covers the refused classification as built, not
the mechanism forever. No other ISO's shard, cell, config, or keeper was touched
(duty d / rule 25).

**Rule 15 `[R-DASHBOARD]`.** No run is registered because **no solve was run** — the
kill fired before LP. Rule 15 governs completed runs; there is no bundle, sidecar, or
payload to commit. The deliverables are this FINDING, the PRECHECK, the record
artifacts, and the matrix + log updates.

**Rule 16 `[R-ALLYEARS]`.** Not engaged — no bundle was produced. Had the A/B run it
would have been 2023+2024+2025 in one bundle per arm.

**caiso-141 wall (GATESPEC §2, owner ruling 4).** No gate, probe, or diagnostic in this
session scored hydro or pumped-storage **output** against actuals. Every number above
is either a published source attribute (EHA `Mode`, HILARRI linkage, Corps ownership),
a nameplate census (EIA-860), or model-side fleet construction. No LMP series, no
CEMS/CAMPD conduct, no EIA-930 `WAT`, no CAISO Today's Outlook, no CDEC telemetry
entered any measurement. Pumped storage was never touched (lane 5's object).

**Rules 23/24.** No threshold, weight, or rule ordering in the shipped curator was
changed; the partition was never hand-edited; no off-registry channel was introduced.
The two probes added are read-only diagnostics.

## 6. Artifacts

* `results/calibration/PRECHECK-caiso194-hydro-ror-split-2026-08-11.md` — anchors,
  committed pre-measurement (`2df253f`)
* `results/calibration/_caiso194_ror_partition.json` — per-plant classification, method
  counts, coverage arithmetic, determinism hashes, gate verdicts
* `results/calibration/_caiso194_engagement.json` — the §3 engagement evidence
* `scripts/probes/_caiso194_precheck_labeled_share.py` — the G-SHARE anchor (rule 1 only)
* `scripts/probes/_caiso194_partition_record.py` — G-COVER / G-SHARE arithmetic
* `scripts/probes/_caiso194_engagement.py` — object-level engagement probe (no LP)

## 7. SESSION-REPORT

```
SESSION:        caiso-194 (close-out campaign Wave 1, lane 4)
OBJECT:         make ScenarioConfig.hydro_ror_split effective via the
                hydro-plant-modes clean partition, then A/B it
OUTCOME:        CLASSIFICATION REFUSED at G-SHARE (-10.9665 pp vs +/-10 pp).
                Killed before LP per GATESPEC section 5. No arm solved.
GATES:          G-DET PASS (repo standard; band wording escalated)
                G-COVER PASS 99.9407 % of 6,740.300 MW
                G-SHARE FAIL 13.4956 % vs 24.4621 % anchor, -10.9665 pp
                G-SIXISO PASS (CAISO-only)
                G-ENGAGE / G-C3B-WATCH N/A - no LP reached
SIDE RESULT:    caiso-188's open question CLOSED - the mechanism DOES engage
                (67/61/3 units stamped 2023/24/25, 0 with the flag off,
                monthly budget bit-identical off vs on). Inertness was the
                absent partition, not dead wiring.
C3a:            NOT MEASURED, NOT QUOTED - no arm solved (direction-hazard
                clause: inadmissible in either direction regardless)
KEEPER:         2026-08-09-caiso-188-d1-micseam UNTOUCHED. No promotion.
REGISTERED:     nothing - no completed run exists (rule 15 not engaged)
CELL:           CAISO hydro_ror_split  K -> R  (provenance refusal, not a
                dispatch-level refutation; a repaired classifier is a new
                charter, not DO-NOT-REDO frozen)
ESCALATED:      (1) G-DET literal byte-identity unsatisfiable for ANY clean
                    partition (clean_io stamps created_utc; its own documented
                    standard is data-byte identity)
                (2) G-SHARE transfer premise - labeled vs unlabeled populations
                    differ 2.2x in mean unit size; EHA labels the small plants
                    and leaves the large reservoir projects unlabeled
                (3) handoff contradictions: PRECHECK "already discharged"
                    (it was not - written and committed); main@6a37611 vs
                    actual a3a7cd1
WALL:           caiso-141 respected - no hydro/PS output scored against
                actuals anywhere in this session
NEXT:           owner ruling on escalations (1) and (2). If the G-SHARE anchor
                is re-specified against a population-matched expectation, the
                A/B becomes runnable unchanged - the partition builds, covers
                99.94 %, and provably engages.
```
