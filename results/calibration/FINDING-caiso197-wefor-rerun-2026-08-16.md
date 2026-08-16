# FINDING — caiso-197 (lane 2 RE-RUN): `wefor_residual = 0.0` scoped `{CC_REGULAR}` is **ACCEPTED on all four pre-registered gates** — the ledger retires the fitted `wefor_multiplier` (11/8 → 10/7), and the keeper's disclosed C1-2023 CC_REGULAR FAIL heals in the arm (−4.44 → −3.94 TWh, back in band) with C3b clean in every year

**Pre-registration:** `PRECHECK-caiso197-wefor-rerun-2026-08-16.md`, committed and
pushed at `995cfe2c7` BEFORE any solve of this session ran (control included).
Gate spec applied as written: `GATESPEC-caiso193-wefor-residual-2026-08-11.md`
(owner ruling 2; the {CC_REGULAR} scope is the gatespec's own §4 fail-closed
subset on the repaired instrument). No band edited. Keeper UNCHANGED at
`2026-08-15-caiso-196-e1-elsegundo` this lane (promotion is Wave 2's §6
question, C3a-blind). 2023–2025 only; both holdout markers and the spend freeze
untouched. Registered runs: **`2026-08-16-caiso-197-l2-control`** and
**`2026-08-16-caiso-197-l2-wefor`** (both NOT-YET, C6 UNATTESTED — the standard
non-keeper A/B posture, caiso-196 precedent).

## 0. Direction-hazard regime (verbatim from the GATESPEC, binding)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

**Single-mechanism statement (required verbatim):** The A/B delta is the
wefor_multiplier/wefor_residual/wefor_residual_groups replacement — a fitted
compensation replaced by the owner-granted measured repair; no other input
differs.

## 1. Gate tally — 4/4 PASS

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-COV** | ≥ 95 % of each relieved class's capacity CAMPD-observed; below-bar classes EXCLUDED fail-closed | CC_REGULAR **0.975784** (extract population) / **0.966664** (strict CEMS 2023–25) — ≥ 0.95 BOTH readings, strict gating; CC_CHP 0.678375 / 0.635703 — EXCLUDED (full statistical WEFOR retained; a real CEMS-exemption limit). Committed pre-session record `_caiso196_gcov_remeasure.json`, not re-run. | **PASS** |
| **G-DOF** | `n_residual` 8 → 7; `n_entries` 11 (re-identified) or 10 (removed); increase = automatic FAIL | Built ledgers (`build_dof_ledger.py`): control **11/8** (byte-consistent with the keeper's committed ledger); arm **10/7** — the sanctioned "removed" path, exactly the PRECHECK §2 code-arithmetic expectation: `wefor_multiplier` at neutral 1.0 leaves the ledger (the fitted compensation retired), and `wefor_residual = 0.0` is not a free parameter (zero is the frozen measurement's arithmetic identity, not a chosen scalar — the builder's own condition). | **PASS** |
| **G-ONEMECH** | A/B `scenario_config` diff EXACTLY the three-field move, verified over the FULL config | Measured over every key of both committed `run_config.json`s: `wefor_multiplier` 0.7→1.0, `wefor_residual` None→0.0, `wefor_residual_groups` None→["CC_REGULAR"] — **and nothing else** (`_caiso197_l2_gates.json`, `g_onemech.pass: true`). ST_GAS's `gas_st_wefor_base_override` None in both (lane 3's object, untouched); CC_CHP relieved nowhere. | **PASS** |
| **G-SIXISO** | ERCOT 0.02 / PJM 0.015 byte-untouched, never cited as evidence; no other ISO's file written | This session solves CAISO only; the five other ISOs' configs, keepers, extracts and matrix shards carry no edit beyond the rule-28c `.` cell registration of the (unrelated) lane-5 row. The CAISO value is the frozen owner grant, derived from no other ISO's number. | **PASS** |

Protocol §3 environment legs: seam import caps logged **16055 / 16452 / 16148
MW** in the control and arm solves (MIC partition materialized in-session, 386
rows — the committed intake count); `hydro_ror_split=false` disclosed in both
run notes (no hydro-plant-modes partition consumed — the loud WARN is the
caiso-190 guard's designed disclosure); warm-start pinned off by the replay
driver; arms solved sequentially (rule 12); environment highspy 1.14.0 /
python 3.11.15 — **identical to the keeper bundle's own recorded stack**.

## 2. Control: BIT-ZERO on the re-anchored base (noise floor quoted first)

`caiso197_l2_control` (the caiso-196 keeper recipe replayed per FINDING-caiso196
§7's re-anchor) reproduces the committed keeper **BIT-ZERO**: max |Δ| = 0.0
over every zone-hour of `hourly/system_*.parquet` (prices included) AND every
class-hour of `hourly/class_hourly_*.parquet`, all three years
(`_caiso197_ctrl_tolerance.json`). ΔC3a = 0.0 pp and ΔC3b = 0.000 identically;
the ratified tolerance (|ΔC3a| ≤ 0.1 pp/yr, |ΔC3b| ≤ 0.005) is met with a noise
floor of exactly zero, quoted before any treated delta was read. At the metric
level the control reprints the keeper's committed values to the digit: C3a
+4.4/+11.7/+14.5 %, C3b 0.077/0.155/0.176, C1-2023 CC_REGULAR −4.44 TWh/−1.9 pp
FAIL. The caiso-184/188/196 bit-zero norm holds on the re-anchored base.

## 3. What the arm does — engagement and the criteria panel

**Engagement** (model artifacts only): the three-field move changes prices in
**34,577 / 36,780 / 35,883 of 61,320 zone-hours** (2023/24/25), max single-hour
|Δprice| $82.0/$539.3/$61.3, and moves class-hour dispatch up to
2,256/2,287/2,700 MW (`_caiso197_l2_gates.json`). Not remotely inert: the
double-count relief releases real CC_REGULAR capability (its statistical WEFOR
term was compensating events the measured overlay already carries).

**Criteria panel** (registration-scored on committed artifacts):

| criterion | control | arm |
|---|---|---|
| C1 fuel-mix | **FAIL** — 2023 CC_REGULAR −4.44 TWh / −1.9 pp (the keeper's disclosed ACCEPT-WITH-FLIP row) | **PASS 12/12 (free 8/8)** — 2023 CC_REGULAR **−3.94 TWh / −1.6 pp, back IN BAND**; 2024 −1.21 → −0.79 TWh |
| C2 system volume | PASS | PASS |
| C3b price shape | PASS 0.077/0.155/0.176 | **PASS 0.076/0.152/0.173** — the §5 named watch: no flip, every year improves slightly |
| C3c price tail | FAIL→ledgerable (the standing caveat) | unchanged (magnitudes re-measured at any promotion per caiso-189 §8.3) |
| C8 forced share | PASS (`legitimacy_diagnostics.json` both bundles) | PASS |
| C3a mean LMP | +4.4/+11.7/+14.5 % (transparency only) | +4.0/+11.1/+14.1 % (reported per §0; **never consulted** — the flattering sign, as pre-registered) |

**No criteria-panel pass→fail flip occurred anywhere** — protocol §5 does not
fire. The one row that MOVES verdict is FAIL→PASS: the keeper's C1-2023
CC_REGULAR miss — which FINDING-caiso196 §3 adjudicated as "the standing
CC-side under-dispatch made visible" once El Segundo's phantom 3.2 TWh was
removed — closes to −3.94 TWh when the OTHER half of the same double-count is
repaired (the class keeps its full measured outage overlay while its
statistical WEFOR term, which duplicated exactly the ≥5-day events the overlay
carries, goes to the measured residual 0.0). Two data repairs, one root
mechanism, each accepted on its own structural gates.

## 4. The ledger — the lane's chartered prize

`wefor_multiplier = 0.7` (identification "residual", the ERCOT-fitted global
availability compensation, lineage ≥52 solves) **leaves the CAISO ledger**:
11 entries / 8 residual → **10 / 7**. The GATESPEC §2 target end state is
reached on its sanctioned "removed" arithmetic. No compensating adjustment of
any other availability input rides along (G-ONEMECH's empty-elsewhere diff is
the proof).

## 5. Composition posture (Wave 2)

* Rung inclusion: this arm's gates PASS ⇒ **rung 1 of the surviving ladder**
  (lane 1 empty per caiso-192; lane 4 R per caiso-194).
* The §9 composition caveat (X_c^filtered ≥ W_c recheck): satisfied by
  identity on this base — the committed extract IS the merit-guard-filtered
  extract (caiso-192), X_c = 0.2443/0.2916/0.3528 ≥ 4.9× W = 0.05 (frozen
  caiso-196 record), and no extract byte moved during the ladder (the Desert
  Star NV intake landed RAW FILES ONLY this session; the extract re-derive is
  explicitly deferred post-ladder, its own rule-23 charter).
* Lanes 3/5 compose on top per the fixed order; their FINDINGs disclose the
  shared control.

## 6. Artifacts

Registered: `2026-08-16-caiso-197-l2-control` / `2026-08-16-caiso-197-l2-wefor`
(bundles `results/calibration/caiso197_l2_{control,wefor}`, each with
`legitimacy_diagnostics.json`, built `calibration_attestation.json`
free-parameters ledgers 11/8 and 10/7, `metrics.json`; hourly sidecars
committed per the caiso-188/196 A/B precedent). Records:
`_caiso197_ctrl_tolerance.json` (bit-zero control),
`_caiso197_l2_gates.json` (G-ONEMECH + engagement), probes
`scripts/probes/_caiso197_ctrl_tolerance.py` / `_caiso197_l2_gates.py`.
Matrix duty (b): `wefor_residual` CAISO cell **R → K-candidate pending Wave-2
§6** — recorded this session as the arm's acceptance with the evidence
citation updated (the cell's final letter follows the campaign's promotion
outcome; the acceptance itself is unconditional). Bench parts
`frontend/data/backcast/bench/CAISO/{2023,2024,2025}.json.gz` changed at
registration: the Desert Star NV CAMPD intake (this session's parallel
errand) adds the plant's CEMS series to the ACTUALS side's CAMPD limb — the
caiso-196 measurement-side pattern; all caiso-197 bundles register against
this SAME bench, and C1 (EIA-923-scored) is measured UNAFFECTED: the control
reprints the keeper's committed −4.44 TWh row exactly. Environment: partial
clone + `hydrate_data.py --profile caiso`; `curate_capacity_deliverability.py
--isos CAISO` (386 rows); replay driver's strict unmapped-key guard bricked the first control attempt
on the nyiso-136 rule-26-deleted `nyiso_solar_registry_cod_dates` key — the
drift class the guard exists to surface; a parallel session's
`_RULE26_DELETED_UNCONDITIONAL` (merged to main mid-campaign) is the incumbent
handling this branch rebased onto, and caiso-197 contributes the three
pinning tests (out-of-owning-ISO silent drop — the CAISO replay case —
collapsed-value replay, wrong-polarity refusal).
