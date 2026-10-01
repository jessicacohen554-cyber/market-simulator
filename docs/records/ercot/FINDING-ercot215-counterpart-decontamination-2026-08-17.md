# FINDING — ercot-215 (G-SPUR lane Phase-1, owner-answered): the counterpart decontamination is BUILT, G-EXACT passes IN FULL, the mechanical verdict is REJECTED-AS-ARMED on the pre-registered G-C3c kill, and the armed member is **PROMOTED ON OWNER INSTRUCTION** — the mid-band spill lane CLOSES as a solved identification

**Session ercot-215, 2026-08-17, branch
`claude/ercot-215-ordc-decontamination-xsbhwn`.** Precommit (pushed before any
solve, commit `c0ed2f7`):
`docs/PRECOMMIT-ercot215-counterpart-decontamination-2026-08-17.md`. Keeper
resolved fresh at session start: **`2026-08-16-ercot213-arm-pubanchor`**
(NOT-YET, fail set {C3b-2023} alone, C3c-2025 the single ledgered caveat).
Keeper at session end: **`2026-08-17-ercot215-arm-decontam`** — promoted per
the owner instruction given in advance at the ercot-214 close and re-confirmed
live mid-session ("Is this a recommended keeper candidate? If so plz promote.
If structural integrity improves but gates regress that may still be a
keeper."). Runs registered with payloads:
**`2026-08-17-ercot215-ctl-headbase`** / **`2026-08-17-ercot215-arm-decontam`**
(bundles `results/calibration/ercot215_control_A` / `ercot215_decontam_B`).
Probes: `results/calibration/ercot215_gexact.json`, `ercot215_ab.json`,
`ercot215_anchor_gates.json`, `ercot215_coal148.json`.

## 0. VERDICT — both halves, neither rewritten

* **The mechanical verdict is REJECTED-AS-ARMED on G-C3c**, exactly as the
  precommit §2 pre-registered ex ante from the ercot-214 counterfactual: the
  model tail moves away from actual in every year (2023: 123 → 67 of 181;
  2024: 33 → 22 of 53; 2025: 3 → 1 of 31). Every other gate passes, G-SPUR —
  the object's own gate — among them. The verdict stands unrewritten.
* **The promotion executed on the owner's standing structural standard on top
  of that verdict** (the ercot-188/213 pattern, third application): the
  keeper's tail and C3a-2023 gains were measured at ercot-214 to ride a
  price-formation channel the 2023-25 design cannot emit, and the
  decontaminated member removes that channel with **zero fitted scalars**
  while reproducing the published adder incidence at its real order of
  magnitude. Both records stand.

## 1. G-EXACT — the added build gate, PASSED IN FULL (`ercot215_gexact.json`)

The delta is post-solve additive (it moves no MW), so the ercot-214
counterfactual was the armed member's scorecard by construction. Measured:

* **(a) Spurious hour SETS** match exactly in all three years — 2023
  repointed = {5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821, 5822} (= the
  control set), 2024 = {336-339, 345-349, 2540, 2829} (= the control set),
  2025 = {3355} (energy-made, un-masked).
* **(b) Adder incidence** nonzero/>$1/>$100 = **564/175/37**, **177/36/3**,
  **67/5/0** at the counterfactual thresholds (the census probe's strict
  `> 0` count reads 178 in 2024 — one hour whose min-ed component is below
  1e-9; both counts are true on their own thresholds).
* **(c) Max adders to the cent**: $4,701.14 (2023 — the true VOLL-cap hour,
  untouched, λ $298.86 + adder = exactly $5,000 = VOLL) / $355.98 / $14.61.
* **(d) G-CAP**: 0 violations in all 26,280 hours.
* **(e) Dispatch byte-identity**: all 9 non-system hourly sidecars
  (class_hourly / storage / reserve_family × 3 years) **sha256-identical to
  the keeper's committed bundle**.

## 2. THE GATE TABLE (full magnitude, control → armed, pinned environment)

Both members solved at the same tree on the keeper's TRUE solve environment
(python 3.11.15, highspy 1.15.1 / numpy 2.4.6 / scipy 1.17.1 / pandas 3.0.5 /
pyarrow 25.0.1 / pydantic 2.13.4, venv outside the project per the ercot-213
standing note), full span 2023+2024+2025 sequential in one invocation each,
the two invocations sequential (peak RSS 12.7 GB against 15 GB).

| gate | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **G-REPRO′** | control **12/12 sidecars sha256-IDENTICAL to the keeper** (no ERCOT-effective HEAD drift); official determination reproduces exactly: NOT-YET, {C3b-2023} | | | **PASS — strongest form** |
| G-SHED (no increase) | 0 → 0 | 1 → 1 (h3067, identical) | 0 → 0 | **PASS** |
| **G-C3c** (not away from actual) | 123 → **67** (181) | 33 → **22** (53) | 3 → **1** (31) | **KILL** — pre-registered §2 |
| **G-SPUR** (≤ +5; the object's own gate) | 17 → **9** = control set exactly | 13 → **11** = control set exactly | 0 → **1** (h3355¹) | **PASS** |
| G-SPAN (≤ 2.0 %) | 0.0 % | 0.0 % | 0.0 % | PASS (identity) |
| G-COAL148 (rise ≤ 0.5 TWh) | 0.0 | 0.0 | 0.0 | PASS |
| G-OWNER | — | C3a-2024 PASS, C3b-2024 PASS | C3a-2025 PASS | PASS |
| G-DOF | `n_entries` 8 / `n_residual` **6**, identical control-vs-arm and vs keeper | | | PASS |
| G-D2 | D-4 section **byte-identical** keeper = control = armed (the 3 pre-existing `reliability_floor × CT_PEAKER` h14-21 rows; no new row) | | | PASS |
| G-CAP | max $4,701.14 @ λ $298.86 → λ+adder = $5,000.00 | max $355.98 | max $14.61 | **PASS** — 0/26,280 |
| **G-EXACT** | §1 — full pass | | | **PASS** |

¹ h3355 (2025-05-20 19h) is energy-made (λ $214.30, actual $134.84); the arm
had held it above the band top with a $1,196.56 phantom adder. The repoint
restores G-SPUR to the energy-made baseline in all three years.

**LOYO:** structurally N/A as pre-registered (parameter-free); per-year deltas
above stand in its place.

## 3. THE OFFICIAL SCORECARD OF THE NEW KEEPER (Q-B/R-A phrasing — 2023 movement side-effect-reported at full magnitude, never a basis)

`scripts/calibration_verdict.py` on the registered armed run:

* **Determination NOT-YET, fail set {C3a-2023, C3b-2023}** — the precommit
  §4's expected post-promotion scorecard, landed exactly. The fail set WIDENS
  from the superseded keeper's {C3b-2023}, by deliberate decontamination.
* **C3a-2023: +0.4 % → −40.1 %** [MODEL MISS]; C3a-2024/2025 PASS.
* **C3b-2023: NRMSE 0.203 → 0.736** [MODEL MISS]; C3b-2024 PASS.
* **C3c: CAVEAT ×3, re-ledgered** (ACCEPTED MODEL-CLASS LIMITATION):
  68/181 (0.38×), 22/53 (0.42×), 1/31 (0.03×) h > $200/MWh RT, at full
  magnitude — the 2023/2024 ledger chains carried from the last keeper that
  ledgered them (ercot-204, full owner-decision genealogy), 2025's from the
  ercot-213 keeper, all three with the ercot-215 re-opening carry. The
  lone-C3c standing rule stays silent because other criteria fail.
* **C6 PASSES** on the fresh ercot-215 attestation
  (`gen_ercot215_attestation.py`); C1 16/16, C2, C4, C8 PASS; the five
  2025 preliminary-vintage C1 gas-class SKIPs carry unchanged.
* Probe-basis mirrors (demand-weighted, `_ercot173_ab`): c3a-2023
  +0.40 → −30.38 %, nrmse 2.2127 → 3.4522; 2024 14.06 → 7.88 %; 2025
  1.21 → 0.51 %. No improvement anywhere is claimed as a basis; no failure
  is minimised.

**Why the widened fail set is the honest state:** ercot-214 §2 measured that
116/117 of the superseded keeper's 2023 deep (>$100) adder hours were
contaminated by the AS-product shortfall-ramp step — published settled RTORPA
p50 was $14.2 in those hours (> $100 in only 15 of them), while the real 2023
tail was conduct-made (actual > $200 in 181 h against 17 h of > $100 published
adder). The keeper was reproducing a conduct-made tail through an AS-plan
penalty ramp the real market does not price. Removing the channel returns the
2023 price object to the model-class ledger where ercot-209/211 adjudicated
it, at its true magnitude.

## 4. WHAT THE NEW KEEPER IS

The ercot-213 recipe plus **one boolean, zero fitted scalars**:
`ercot_ordc_adder_family_counterpart` — inside the armed published-anchor
branch, `gamma' = min(gamma_all, gamma_ordc_family)`, the ORDC total family's
own balance-row dual component of the all-tier cap dual, instead of the
contaminated sum. Identification: the 2023-25 market-design fact (no RT
per-product scarcity pricing — `model/reserves/spec.py`,
`ercot_ordc_only_scarcity` citation block) + the ercot-214 exact decomposition
(808/808 writing hours) + the family dual's two-regime match to published
RTORPA (rank-corr 0.709/0.807/0.758). Anchor, single-counterpart form,
protocol cap and netting untouched; the ramp's in-LP withholding role
untouched — only its export into the written price stops. Registered as the
THIRD LEG on `ercot_multiproduct_as` (nyiso-121 census), with a matching CLI
flag, recorded in `meta.json`, provably inert alone (tests
`tests/unit/pipeline/test_ordc_family_counterpart.py`, 7 tests + the 7
ercot-213 siblings all passing). `reserve_price_by_family=None` under the
armed flag is a loud `ValueError`, never a silent fallback.

## 5. ROSTER, RETENTION AND HOUSEKEEPING — flagged, not decided quietly

* ERCOT's registry now holds **5 runs**: the keeper
  (`2026-08-17-ercot215-arm-decontam`), its control
  (`-ctl-headbase`, which is ALSO the HEAD-current byte-reproduction record
  of the superseded keeper), the immediate-prior keeper
  (`2026-08-16-ercot213-arm-pubanchor`), that keeper's control
  (`2026-08-16-ercot213-ctl-headbase`), and
  `2026-08-15-ercot204-rule26-delete`. Under the owner's retention directive
  ("the current keeper runs, and runs prior to the keeper come off"), the
  last two are candidates to prune (`scripts/prune_iso_runs.py --iso ERCOT`);
  the ercot-213 arm stays as the immediate-prior comparison per the
  ercot-204→213 precedent. **Left for the owner** — 5 runs is well under
  top-15 and nothing dangles.
* `check_registry_payload_parity.py` reports one PRE-EXISTING failure,
  unrelated to this lane: `results/calibration/caiso200_h0_control` (landed
  with the caiso-200 merge, PR #4065) maps to no retained sidecar. Not
  touched here (rule 25); flagged for the CAISO lane.
* Mid-session, PR #4064 (this branch at its pre-registration state) was
  merged to main and the branch deleted; the remaining work was rebased onto
  the refreshed main and re-pushed on the same branch name per the standing
  merged-PR protocol. The A/B solves pre-date that merge but the merged
  content is byte-identical to what was solved (the merge WAS this branch).

## 6. GOVERNANCE

Q-B FINAL + R-A cited and honoured: every C3a/C3b-2023 number here is
side-effect reporting at full magnitude; the mechanical rule read only the §3
gates (it killed on G-C3c), and the promotion rests on the owner's §0
instruction plus the measured structural identification. The ISO posture
after promotion is **NOT-YET held as the honest public claim per R-A**, with
both failing criteria the closed 2023 model-class price object (Q-B: no
further C3a-2023 spend; R-A: re-charter ERCOT sessions off the 2023 price
criteria) and C3c the ledgered model-class caveat ×3. ercot-206 B0 honoured —
no LOLP-table arming. ercot-211 Door A honoured — no conduct work; the 2023
tail returned to the C3c ledger, not chased. 28a honoured — the bare netting
not re-tested (it rides armed inside the keeper recipe). V0/ercot-201
DO-NOT-REDO honoured. Rule 22: {2023, 2024, 2025} only, no marker sought;
ERCOT holds no `complete`/`final` marker so no `calibration-complete.json`
re-key (D-5(b)). Rule 25: ERCOT only. Rules 5/23: zero fitted scalars — both
operands are LP duals of the same solve. Rules 5/24: the field is a
registered `solve_and_persist` kwarg recorded in `meta.json`; no off-registry
channel. Rule 27: edits local, exact on-disk bytes pushed, pushed files
blob-verified (incl. the 1.6 MB run payloads). Rule 28: the 28c third-leg
registration on the base row + the 28b cell verdict + the shard keeper/gates
re-stamp + the §5.1 prose-header re-stamp land in this same session;
`check_mechanism_matrix.py` exit 0 clean. The G-SPUR band-top blindness
(FINDING-ercot214 §5) is NOT a gate change here — flagged for a future owner
gate revision only. No new workflows, no cron, solves ran in-session. No PR
opened by this session (push-and-stop; the owner merges — and mid-session
merged the first half as PR #4064).

**Session consumed the ercot-215 shorthand. Next shorthand: ercot-216**
(ercot-199 remains unclaimed).
