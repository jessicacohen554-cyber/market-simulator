# GATESPEC — caiso-193 (lane 2): the granted narrow arm — `wefor_residual = 0.0` scoped `{CC_REGULAR, CC_CHP}`, `wefor_multiplier → 1.0`

**Authored by caiso-191 on 2026-08-11, BEFORE any lane-2 measurement exists.** These
gates are fixed and fail-closed. Authorization: owner ruling 2 (caiso-187 option 2,
GRANTED, independent of option 1 — `caiso191-owner-rulings-2026-08-11.md`).

## 0. Direction-hazard regime (verbatim, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

Concretely: the arm adds ~3.5 pp of CC availability (the statistical term the
multiplier was compensating), which lowers price. The prize is the LEDGER (11/8 →
11/7), never the fit — caiso-187 PRECHECK §1a's words, unchanged.

## 1. The caiso-187 §4 pre-registration defect, and its cure (STEP-3 obligation)

**What the defect was, precisely.** caiso-187's PRECHECK §2 defined the arm's value
as ONE capacity-weighted scalar aggregated over ALL covered classes present in the
CAISO fleet (`{CC_REGULAR, CC_CHP, ST_GAS}`), which on the measured data gives
0.0303. But the same PRECHECK's protective gates G-NODOUBLE and G-SCOPE state that a
class with `X_c = 0` gets NO relief — and ST_GAS has zero overlay coverage
(`X_c = 0`), so applying the 0.0303 scalar to it would cut its removal from 0.147 to
0.0303, a ~12 pp capability release to the one class with no measured overlay at all.
**The aggregation rule and the protective gate were mutually inconsistent on the
data**; caiso-187 declared the inconsistency (§4), refused to repair its own
pre-registration mid-session, and escalated. The owner has now resolved it by
granting the gate-consistent reading (ruling 2).

**The cure this measuring session MUST implement — a clean re-pre-registration:**

1. A fresh PRECHECK, committed and pushed BEFORE any solve, that declares the
   **scoped-groups form as the only form**: `wefor_residual` applies only to the
   classes enumerated in `wefor_residual_groups`. **Cross-class aggregation over
   heterogeneous overlay coverage is forbidden, permanently, in this lane.**
2. The protective gate is declared **dominant over any formula**: a class with
   `X_c = 0` takes no relief under any arithmetic. This ordering is stated in the
   PRECHECK before measurement, so it can never again be discovered mid-session.
3. The arm's values are the OWNER-GRANTED ones — `wefor_residual = 0.0`,
   `wefor_residual_groups = {CC_REGULAR, CC_CHP}`, `wefor_multiplier = 1.0` — taken
   from the FROZEN caiso-187 identification record
   (`_caiso187_residual_identification.json`). **No recomputation, no
   re-aggregation, no second value.** Recomputing after seeing any price voids the
   session (the caiso-187 G-FROZEN clause, inherited whole).
4. ST_GAS keeps its full statistical WEFOR, untouched, in this arm (its question is
   lane 3's).

## 2. Objective

Retire DOF ledger entry #5 — `wefor_multiplier = 0.7`, `identification: "residual"` —
by replacing the fitted compensation with the measured repair the code's own comment
prescribes (`data/fleet/arrays.py`: cap the statistical WEFOR at the short-outage
residual where the CAMPD overlay already carries every ≥5-day event). Target end
state: `wefor_multiplier` neutral at 1.0 and the ledger at **11 / 7** (the entry
moves `residual` → `measured`, or leaves the ledger).

## 3. Exogenous instrument closure

The committed CAISO CAMPD extract (read through the SHIPPED loader,
`outages.unit_outage_derate_factors`), `constants.THERMAL_AVAILABILITY` (NOT
re-derived — rule 23), EIA-860 class capacities, and the frozen
`_caiso187_residual_identification.json`. **No LMP/price series anywhere in any
derivation or gate statistic.** No data byte written; the extract is read-only.

## 4. Numeric gates — each with its written anchor

| gate | bar | anchor |
|---|---|---|
| **G-COV** | CAMPD-observed coverage ≥ **95 %** of each relieved class's capacity: the share of CC_REGULAR (resp. CC_CHP) EIA-860 capacity belonging to plants present in the committed CAMPD CAISO extract population. A class below 95 % is EXCLUDED from `wefor_residual_groups` (fail-closed); uncovered units keep their full WEFOR by construction when their class is excluded. | 40 CFR Part 75 makes CEMS reporting mandatory for gas units ≥ 25 MW serving generators, so the class should be near-fully observed BY REGULATION; the 5 % tolerance covers small/exempt units. A class-level relief over a class the overlay does not observe would be exactly the G-NODOUBLE violation this lane exists to prevent. |
| **G-DOF** | Ledger moves **11/8 → 11/7, verified by arithmetic on the built attestation**: `n_entries` 11 unchanged, `n_residual` 8 → 7, the `wefor_multiplier` entry re-identified `residual` → `measured` (or removed, giving 10/7). An INCREASE is an automatic FAIL. NO decrease is a failure of the thesis and is reported as one. | The committed keeper attestation (`caiso188_d1_micseam/calibration_attestation.json`, `free_parameters` 11/8) — a pre-existing repo measurement; the target is its arithmetic consequence, not a chosen number. |
| **G-ONEMECH** | The A/B `scenario_config` diff is EXACTLY the three-field move (`wefor_multiplier` 0.7→1.0, `wefor_residual` None→0.0, `wefor_residual_groups` None→{CC_REGULAR, CC_CHP}) and nothing else, verified over the full config diff. This is ONE mechanism (rule 19): splitting it would solve a known-wrong configuration (the full uncompensated double count), which rule 1 forbids spending LP on. | FINDING-caiso187 PRECHECK §3 — the pre-existing single-mechanism argument, inherited unchanged. |
| **G-SIXISO** | ERCOT's 0.02 and PJM's 0.015 are byte-untouched and never cited as evidence for the CAISO value (rule 25). No other ISO's config, keeper, extract, or cell written. | Rule 25 `[R-ISO-SCOPE]` — standing. |

## 5. Conservative-default rules

* A class failing G-COV is excluded, never partially relieved (bias against the
  favorable direction — exclusion keeps MORE removal in place).
* If BOTH classes fail G-COV the arm is dead; the null result is reported (that too
  is a finding: the grant was conditioned on an observability that failed).
* No compensating adjustment of any other availability input in the same arm.

## 6. Kill criteria

* Any recomputation or re-aggregation of the residual value ⇒ void.
* G-DOF increase ⇒ automatic fail.
* Any price read before the value/config is frozen and pushed ⇒ void.
* Coverage below bar for both classes ⇒ no solve, null-FINDING.

## 7. A/B protocol

* **CONTROL** — the caiso-188 keeper recipe re-solved in the session's own
  environment (`--replay-bundle results/calibration/caiso188_d1_micseam`; the
  capacity-deliverability partition materialized and verified by log line;
  `hydro_ror_split` explicitly False, disclosed — integration protocol §3). Ratified
  reproduction tolerance (C3a ±0.1 pp/yr, C3b ±0.005) met and the noise floor quoted
  BEFORE any treated delta is read.
* **ARM** — control + the three-field move (G-ONEMECH). All of 2023+2024+2025 in one
  bundle per arm (rule 16), years sequential, arms sequential (rule 12), both
  registered (rule 15) with `legitimacy_diagnostics.json`.
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta is the
  wefor_multiplier/wefor_residual/wefor_residual_groups replacement — a fitted
  compensation replaced by the owner-granted measured repair; no other input differs."

## 8. Required artifacts

* `results/calibration/PRECHECK-caiso193-wefor-residual-<date>.md` — the §1 clean
  re-pre-registration, committed before any solve.
* Record: `results/calibration/_caiso193_wefor_coverage.json` — the G-COV
  measurement and the G-DOF arithmetic.
* Run bundles `caiso193_l2_control`, `caiso193_l2_wefor` (a lane-3 session sharing
  the control re-uses it, disclosed).
* `results/calibration/FINDING-caiso193-wefor-residual-<date>.md` with gate tally,
  the direction-hazard clause quoted, matrix duty-(b) update in-session (the
  verdict-bearing `wefor_residual` row caiso-187 split out).

## 9. Composition caveat (binding on wave 2)

This arm's zero-residual value rests on `X_c ≥ W_c` measured on the UNFILTERED
overlay. At the Wave-2 rung that composes this arm on top of lane 1's filtered
extract, `X_c^filtered ≥ W_c` must be re-verified for both granted classes through
the frozen caiso-187 §2 formula. If it no longer holds, this arm is structurally
unsupported on the composed base: **deterministic skip** (continue on the previous
base), record the interaction, escalate to closeout — never a recomputed value
mid-ladder (integration protocol §5).
