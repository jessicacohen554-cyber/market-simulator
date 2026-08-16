# PRECHECK — caiso-197 (lane 2 RE-RUN): the owner-granted narrow arm on the re-anchored caiso-196 base — `wefor_residual = 0.0` scoped `{CC_REGULAR}`, `wefor_multiplier → 1.0` — pre-registered A/B, committed BEFORE any solve

**Committed and pushed before any LP of this session runs (control included).**
These gates are fixed and fail-closed. Gate spec applied as written:
`GATESPEC-caiso193-wefor-residual-2026-08-11.md` (authored by caiso-191 BEFORE any
lane-2 measurement, owner ruling 2) — **no band edited, no gate re-interpreted**.
This is the re-run that FINDING-caiso193 §4 item 2 prepared and escalated: the
original lane-2 arm was killed before solve at G-COV on the frozen instrument
(both granted classes below the 95 % bar); the caiso-196 El Segundo remap repair
made the instrument complete, G-COV now passes for CC_REGULAR under BOTH
population readings on the committed record
(`results/calibration/_caiso196_gcov_remeasure.json`), and the owner's caiso-196
promotion (2026-08-16, FINDING-caiso196 §7) re-anchored the campaign control to
the caiso-196 keeper base and chartered exactly this arm ("the lane-2 re-run
({CC_REGULAR}-scoped) and lanes 3/5 compose on it"). The session brief
(caiso-197) names this rung 1 of the close-out ladder.

## 0. Direction-hazard regime (verbatim from the GATESPEC, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

Concretely: the arm zeroes the statistical WEFOR term on CC_REGULAR (adds CC
capability, lowers price — the flattering direction) while simultaneously
returning every OTHER thermal class's WEFOR to its full statistical value
(multiplier 0.7 → 1.0 — the anti-flattering direction for those classes). The
prize is the LEDGER (the fitted `wefor_multiplier` compensation retired), never
the fit — caiso-187 PRECHECK §1a's words, unchanged. No price series is read
before the values below are frozen and this file is pushed.

## 1. The §1 cure clauses (GATESPEC §1, restated as binding here)

1. **Scoped-groups form is the ONLY form.** `wefor_residual` applies only to the
   classes enumerated in `wefor_residual_groups`. Cross-class aggregation over
   heterogeneous overlay coverage is forbidden, permanently, in this lane.
2. **The protective gate is DOMINANT over any formula.** A class with `X_c = 0`
   takes no relief under any arithmetic; a class failing G-COV is EXCLUDED
   (fail-closed), never partially relieved. This ordering is stated here, before
   any solve, so it can never again be discovered mid-session.
3. **The arm's values are the OWNER-GRANTED ones, FROZEN — no recomputation, no
   re-aggregation, no second value** (the caiso-187 G-FROZEN clause, inherited
   whole; recomputing after seeing any price voids the session):
   * `wefor_residual = 0.0` — from the frozen identification record
     `_caiso187_residual_identification.json`: `residual_c = max(0, W_c − X_c)`
     with W = 0.05 and CC_REGULAR X_c far above W in every year. On the
     REPAIRED extract X_c = **0.2443 / 0.2916 / 0.3528** (2023/24/25, committed
     in the caiso-196 record and keeper note) = **4.9–7.1× W**, so 0.0 is
     invariant by the frozen formula's own arithmetic. The repair could only
     RAISE X_c; the value cannot move. **No recomputation is performed.**
   * `wefor_residual_groups = {"CC_REGULAR"}` — the GATESPEC §4 G-COV
     fail-closed subset: CC_CHP measures 0.678375 (extract population) /
     0.635703 (strict CEMS 2023–25) against the 0.95 bar and stays EXCLUDED —
     a REAL CEMS-exemption observability limit (12 of 21 plants absent, small
     industrial cogens outside 40 CFR Part 75's practical coverage), not
     repairable by plumbing. CC_REGULAR measures **0.975784 / 0.966664** —
     ≥ 0.95 under BOTH defensible readings, strict reading gating
     (`_caiso196_gcov_remeasure.json`, committed 2026-08-15,
     `g_cov_surviving_groups = ["CC_REGULAR"]`).
   * `wefor_multiplier = 1.0` — the fitted 0.7 compensation retired to neutral.
4. **ST_GAS keeps its full statistical WEFOR, untouched** (its question is lane
   3's; `gas_st_wefor_base_override` stays `None` in this arm). Coal and CT
   likewise untouched. CC_CHP keeps its full statistical WEFOR by construction
   (excluded class, clause 2).

## 2. Objective (GATESPEC §2)

Retire DOF ledger entry `wefor_multiplier = 0.7` (`identification: "residual"`,
the ERCOT-fitted global availability compensation) by replacing the fitted
compensation with the measured repair the code's own comment prescribes
(`data/fleet/arrays.py`: cap the statistical WEFOR at the short-outage residual
where the CAMPD overlay already carries every ≥5-day event — and on the repaired
instrument that residual is measured 0.0 for CC_REGULAR). Target end state:
`wefor_multiplier` neutral at 1.0 and the ledger at **11/7 or 10/7** (GATESPEC
G-DOF: the entry re-identifies `residual → measured`, "or removed, giving
10/7"). **Code-arithmetic expectation, stated before the solve:**
`build_dof_ledger.py` emits the `wefor_multiplier` entry only when the value is
neither None nor 1.0, and emits a `wefor_residual` entry only for a nonzero
value (0.0 is not a degree of freedom — it is the frozen measurement's
arithmetic identity, not a chosen scalar). The expected built ledger is
therefore **n_entries 10 / n_residual 7** — the sanctioned "removed" path. An
INCREASE on either count is an automatic FAIL; no decrease in `n_residual` is a
failure of the thesis and is reported as one.

## 3. A/B protocol (re-anchored per FINDING-caiso196 §7; GATESPEC §7 otherwise unchanged)

* **CONTROL** (`results/calibration/caiso197_l2_control`) — the caiso-196 keeper
  recipe re-solved in this session's own environment from its committed bundle,
  never a remembered CLI string:
  `python scripts/replay_keeper.py results/calibration/caiso196_e1_elsegundo
  --out-dir results/calibration/caiso197_l2_control --set hydro_ror_split=false`
  with `data/clean/capacity-deliverability/CAISO` MATERIALIZED FIRST
  (`scripts/data/curate_capacity_deliverability.py --isos CAISO`) and verified by
  the `seam import cap set to 16055 / 16452 / 16148 MW` log lines during the
  solve; `hydro_ror_split` explicitly False with no hydro-plant-modes partition
  consumed — both disclosed (integration protocol §3, keeper's proven-effective
  configuration). Warm-start pinned off by the replay driver
  (`MARKET_SIM_WARMSTART_XYEAR=0`).
* **RATIFIED TOLERANCE (control gate):** per year, |ΔC3a| ≤ 0.1 pp and
  |ΔC3b| ≤ 0.005 against the keeper's committed values — C3a
  **+4.4 / +11.7 / +14.5 %** and C3b **0.077 / 0.155 / 0.176** (2023/24/25,
  FINDING-caiso196 §4/§7). The control delta is quoted as the NOISE FLOOR at
  full precision BEFORE any treated delta is read; bit-zero against the keeper's
  committed `hourly/` sidecars is the expected CAISO norm (caiso-184/188/196
  G-CTRL) and, if measured, is quoted as exactly that. Outside tolerance ⇒
  **stop-the-line finding about the head, NO ARM SOLVES**, escalate.
* **ARM** (`results/calibration/caiso197_l2_wefor`) — control + EXACTLY the
  three-field move:
  `python scripts/replay_keeper.py results/calibration/caiso196_e1_elsegundo
  --out-dir results/calibration/caiso197_l2_wefor --set hydro_ror_split=false
  --set wefor_multiplier=1.0 --set wefor_residual=0.0
  --set 'wefor_residual_groups=["CC_REGULAR"]'`
* Rule 16: 2023+2024+2025 in one bundle per arm; years sequential, arms
  sequential (rule 12); both bundles registered on the dashboard (rule 15) with
  `legitimacy_diagnostics.json`; environment: highspy 1.14.0 / python 3.11.15 —
  **identical to the keeper bundle's own recorded environment** (no cross-build
  leg needed this time).
* A lane-3 session sharing this control re-uses it, disclosed in both FINDINGs
  (GATESPEC §7's own sharing clause).
* Single-mechanism statement, required verbatim in the FINDING: "The A/B delta
  is the wefor_multiplier/wefor_residual/wefor_residual_groups replacement — a
  fitted compensation replaced by the owner-granted measured repair; no other
  input differs."

## 4. Numeric gates (GATESPEC §4, applied as written; G-COV already measured on the committed record)

| gate | bar | status at PRECHECK time |
|---|---|---|
| **G-COV** | ≥ 95 % of each relieved class's EIA-860 capacity in the committed CAMPD CAISO extract population; a class below the bar is EXCLUDED fail-closed. | **MEASURED, committed, pre-session**: CC_REGULAR 0.975784 (extract pop) / 0.966664 (strict CEMS 2023–25) — PASS both readings, strict gating. CC_CHP 0.678375 / 0.635703 — FAIL, EXCLUDED (its full statistical WEFOR retained). Record: `_caiso196_gcov_remeasure.json`. The measurement is NOT re-run this session; the committed record governs. |
| **G-DOF** | `n_residual` 8 → 7 with `n_entries` 11 (re-identified) or 10 (removed); verified by arithmetic on the built attestation of the arm bundle (`build_dof_ledger.py`). An INCREASE is an automatic FAIL. NO decrease fails the thesis and is reported as one. | To be verified on the built bundles. Control expectation: 11/8 byte-equal to the keeper's committed ledger. Arm expectation: **10/7** (§2). |
| **G-ONEMECH** | The A/B `scenario_config` diff is EXACTLY the three-field move — `wefor_multiplier` 0.7→1.0, `wefor_residual` None→0.0, `wefor_residual_groups` None→{CC_REGULAR} — and nothing else, verified over the FULL config diff of the two bundles' `run_config.json`. | To be verified on the built bundles. The {CC_REGULAR} scope (vs the ruling's {CC_REGULAR, CC_CHP}) is the GATESPEC's OWN §4 fail-closed subset, prescribed by its text ("A class below 95 % is EXCLUDED from `wefor_residual_groups`"), confirmed within-grant by FINDING-caiso193 §3. |
| **G-SIXISO** | ERCOT's 0.02 and PJM's 0.015 byte-untouched, never cited as evidence for the CAISO value; no other ISO's config, keeper, extract, or matrix cell written. | Binding throughout; verified at FINDING time (this session solves CAISO only and edits only the CAISO matrix shard). |

## 5. Kill criteria (GATESPEC §6, inherited whole)

* Any recomputation or re-aggregation of the residual value ⇒ void.
* G-DOF increase ⇒ automatic fail.
* Any price read before the value/config was frozen and pushed ⇒ void. (The
  values above are the owner-granted constants from the frozen caiso-187 record;
  nothing here derives from any price series, and no solve has run.)
* Control outside the ratified tolerance ⇒ no arm solves; stop-the-line FINDING.
* Criteria-panel pass→fail flips at the arm (C3b the named watch; C1-2023
  CC_REGULAR is already FAIL at the base and is watched for movement, not flip)
  ⇒ integration-protocol §5: input-side re-examination ONLY; ACCEPT-WITH-FLIP +
  escalate if the input survives; never silent rejection, never a C3a consult.

## 6. Required artifacts

* This PRECHECK, committed and pushed before any solve (control included).
* Bundles `results/calibration/caiso197_l2_control`, `caiso197_l2_wefor`
  (run ids minted by the replay driver's dating rule for overridden runs).
* `results/calibration/FINDING-caiso197-wefor-rerun-2026-08-16.md` — gate tally,
  §0 clause quoted verbatim, single-mechanism statement verbatim, matrix duty
  (b) in-session (`wefor_residual` CAISO cell moves off R on this arm's verdict;
  evidence citation updated either way), calibration-log entry in
  `docs/calibration-log/caiso.md`.
* DOF ledgers built into both bundles' `calibration_attestation.json`
  (`build_dof_ledger.py`), the G-DOF arithmetic quoted in the FINDING.

## 7. What this session does NOT do

No keeper shard edit on this arm's own authority (a promotion, if any, follows
the integration protocol §6 C3a-blind posture and the Wave-2 composition — this
arm is rung 1 of the surviving ladder, and lanes 3/5 are chartered to compose on
the re-anchored base in this same campaign). No holdout year touched (2023–2025
only; the spend freeze and both markers untouched). No other ISO touched. The
DO-NOT-REDO cells stay frozen (export/absorption caiso-142 §H; offer rungs
caiso-131 §10; reserve tiers caiso-144; `hydro_ror_split` R at G-SHARE
caiso-194 — its re-anchoring is a NEW charter this session does not open; lane 1
guard already applied caiso-192; lane 6 desk-refused caiso-191).
