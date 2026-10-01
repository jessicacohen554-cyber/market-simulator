# GATESPEC — caiso-194 (lane 4): make `hydro_ror_split` EFFECTIVE — the deterministic RoR partition, built, engaged, and solved

**Authored by caiso-191 on 2026-08-11, BEFORE any lane-4 measurement exists.** These
gates are fixed and fail-closed. The lane discharges the caiso-188 §6 filing: the
keeper's `meta.json` advertises `hydro_ror_split: true`, but caiso-188 G-CTRL proved
by exact reproduction (max |Δ| = 0.00 MW from an environment with no
`hydro-plant-modes` partition) that **the mechanism has never run in any CAISO
keeper's LP**. Arming it genuinely is its own A/B with its own pre-registration —
this is that charter's gate spec.

## 0. Direction-hazard regime (verbatim, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

For this lane specifically the sign is not one-way (removing RoR shapeability moves
prices in both directions across the year); the clause binds identically — C3a is
inadmissible as acceptance evidence in EITHER direction, and no gate below reads it.

## 1. Objective

Build the `hydro-plant-modes` clean partition deterministically from ORNL EHA FY2024
+ HILARRI v4 via the shipped curator (`scripts/data/curate_hydro_plant_modes.py`,
consumed through `src/market_sim/data/hydro_modes.py::load_hydro_shapeable`), with
tests green, and solve the arm with the partition materialized so the dispatch
mechanism (`ScenarioConfig.hydro_ror_split`) actually constrains RoR plants. The
classification is a static plant attribute with a rule-13 forward story (re-run the
curation against updated EHA/HILARRI vintages — the module docstring's own words).

## 2. Exogenous instrument closure

* ORNL EHA FY2024 (`Mode` labels, `CH_MW` capacities, BA codes, dam ownership),
  HILARRI v4 (reservoir association, project type), the Corps-dam ownership strings,
  and the EIA-860 plant join — the curator's documented inputs, nothing more.
* **FORBIDDEN in the classifier AND in every gate, probe, and diagnostic: any
  LMP/price series, any CEMS/CAMPD conduct, and any measured hydro/PS OUTPUT series**
  — EIA-930 `WAT`, CAISO Today's Outlook hydro, CDEC telemetry. The caiso-141 wall
  stands (owner ruling 4): no gate may score pumping or hydro output against actuals
  (rule 13; caiso-140 §G's PS-caveat clause). Acceptance rests on classification
  provenance + engagement ONLY.

## 3. Numeric gates — each with its written anchor

| gate | bar | anchor |
|---|---|---|
| **G-DET** | The partition build is deterministic: two consecutive curator runs produce byte-identical partitions; `tests/test_curate_hydro_plant_modes.py` green; `clean_io.validate_clean` passes. No hand-edit of the partition, ever (rules 23/24). | The curator's own rule-order design and its committed test file — a pre-existing repo instrument. Determinism is a physical-stationarity claim: a plant's hydraulic mode does not depend on the run. |
| **G-COVER** | ≥ **90 %** of CAISO conventional-hydro nameplate (EIA-860, the model's own hydro fleet basis) appears classified in the partition. | ORNL EHA is the census instrument of the US hydro fleet; a partition missing >10 % of nameplate is an incomplete intake, not a classifier — the mechanism would then silently bifurcate the fleet on data presence rather than on hydraulic mode. |
| **G-ENGAGE** | Proof the partition was READ by the arm's solve, all four legs: (a) the wired `check_clean_partitions` guard passes with the partition present (and the control, run WITHOUT it, confirms the guard fires — the caiso-188 wiring, exercised); (b) the arm's solve log carries no `"no hydro-plant-modes clean partition"` WARN; (c) the arm's LP DIFFERS from control (a bit-identical arm ⇒ the mechanism is INERT — report `I`, do not accept; the exact caiso-188 failure mode this lane exists to close); (d) if the caiso-190 `resolved_inputs` record has merged by solve time, cite it as the engagement instrument — it had NOT merged at authorship (verified on origin/main, 2026-08-11), so legs (a)–(c) are the binding proof. | caiso-188 §7 item 5: never treat "the run_config records the flag as armed" as evidence the mechanism ran — check the gate, the call site, and the DATA. All three failure modes have been measured on this ISO; this gate is their union. |
| **G-SHARE** | The classified capacity-weighted NON-SHAPEABLE (RoR + canal + release-taker) share of the full population lies within **±10 pp** of the same share computed on the EHA `Mode`-LABELED subset alone — and the labeled-subset share is computed and COMMITTED IN THE PRECHECK **before** the completion rules run on the unlabeled remainder. | The EHA `Mode` labels are the published expectation the curator's completion rules were validated against (the script's own labeled-subset validation, per its docstring). If the full-population share lands far from the labeled subset's, the completion rules — not the water — are setting the answer. The anchor is a published attribute of the source data, fixed before the measurement it gates. |
| **G-C3B-WATCH** | C3b is the WATCH criterion. The control's own C3b is re-measured at full precision FIRST (the campaign frame records the 2025 margin as 0.164 against the 0.20 bar — an orchestrating-session figure; the session must re-derive it, since the committed bundle metrics carry status only). An arm C3b pass→fail flip goes to the **criteria-flip protocol** (integration protocol §6): input-side re-examination only — an input-side defect kills the arm; otherwise ACCEPT-WITH-FLIP and escalate to closeout/owner. **Never silent rejection** (rule 14 forbids rejecting an accurate input on fit). | Rule 14 verbatim: if accurate data makes the backcast worse, something else was compensating — the accurate input stays and the root cause is opened. |
| **G-SIXISO** | The partition is built CAISO-only (`isos=["CAISO"]`); no other ISO's partition, config, or cell is touched (rule 25 — the curator has "only been reviewed/registered for some ISOs — CAISO first", per the module docstring). | Rule 25 `[R-ISO-SCOPE]` — standing. |

## 4. Conservative-default rules

* A plant the documented rule order cannot classify is REPORTED and omitted — never
  hand-assigned, never defaulted by direction. (The rules are direction-blind by
  construction; ambiguity is an intake gap, not a knob.)
* Pure-PS plants (`CH_MW` NaN) and non-CISO BA rows never enter the table (the
  shipped exclusion, pinned by test) — lane 4 does not touch pumped storage; PS is
  lane 5's object and ONLY under that lane's own gates.
* No threshold, weight, or rule ordering may be changed from the shipped curator; a
  genuinely needed rule change is a new charter, not a lane-4 act (rule 23).

## 5. Kill criteria

* Tests red, G-DET or G-COVER fail ⇒ **no solve** (kill before LP, the caiso-186
  discipline).
* G-SHARE fails ⇒ the classification is refused; no arm registered as a keeper
  candidate; the confrontation reported.
* G-ENGAGE leg (c) shows a bit-identical arm ⇒ the mechanism is INERT at this head;
  cell stamped `I` from this evidence; not an acceptance.
* Any gate, probe, or diagnostic found scoring hydro/PS output against actuals ⇒
  session void (caiso-141 wall; rule 13).

## 6. A/B protocol

* **CONTROL** — the caiso-188 keeper recipe re-solved per integration protocol §3:
  `--replay-bundle results/calibration/caiso188_d1_micseam`, capacity-deliverability
  partition materialized (log-verified), and `hydro_ror_split` explicitly **False**
  with NO `hydro-plant-modes` partition present — the keeper's proven-effective
  configuration. Ratified tolerance met, noise floor quoted first.
* **ARM** — control + {the materialized `hydro-plant-modes` partition,
  `hydro_ror_split = True`}. **ONE mechanism** (rule 19): making the advertised split
  effective. Nothing else differs.
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms sequential
  (rule 12); both registered (rule 15) with `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is
  the hydro-plant-modes partition made effective under `hydro_ror_split`; no other
  input differs."

## 7. Required artifacts

* `results/calibration/PRECHECK-caiso194-hydro-ror-split-<date>.md` — committed
  before the curator runs on the full population; carries the G-SHARE labeled-subset
  share.
* Record: `results/calibration/_caiso194_ror_partition.json` — per-plant
  classification, method counts, coverage arithmetic, the two-run byte-identity
  hashes.
* Run bundles `caiso194_l4_control`, `caiso194_l4_ror`.
* `results/calibration/FINDING-caiso194-hydro-ror-split-<date>.md` with gate tally,
  the direction-hazard clause quoted, and the matrix duty-(b) update in-session
  (`hydro_ror_split` CAISO cell — currently advertised-but-inert, per caiso-188).
