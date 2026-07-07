# Gap Register — 2026-07 Comprehensive Audit

**Audited:** main @ `cae7ebb` (post-#1437), 2026-07-05/06.
**Mandate:** read-only stocktake of every workstream, judged against two strategic goals —
**(A) External usability**: a competent stranger can obtain the data, run the model, and reproduce a published result.
**(B) Energy-modeling legitimacy**: every skill claim survives a hostile referee (no tuning channel, no answer-key leak, pre-registered out-of-sample validation, honest limitations).

**Method:** five parallel read-only sweeps — (1) all `docs/handoffs/` + calibration logs + `docs/multi-iso/` (30 workstreams), (2) merged-PR/issue harvest #1339–#1437 + in-flight inventory, (3) legitimacy question set re-run against code (rules 13/14/17–26), (4) stranger-simulation usability trace, (5) verification of 18 named open threads. Claims were verified against code/artifacts (including live runs of `audit_keepers.py --check` and `legitimacy_diagnostics.py --keepers`), not doc prose; where verification exceeded budget the item is marked **UNVERIFIED**. Severity: **blocks-release** (gates goal A), **blocks-claim** (gates goal B), **debt**. Effort: **S**mall / **M**edium / **L**arge / **SH** (solve-heavy — requires multi-hour LP solves).

---

## 1. State snapshot

- **Keepers:** all 6 ISOs designated (`ercot32-ordc-total-rtolcap`, `caiso-51-firm-base`, `pjm-77-ct-relfloor`, `nyiso-41-hub-prices`, `neiso-48-ct-floor`, `miso-41-ct-evening`). All six score **NOT-YET** on `scripts/calibration_verdict.py` (status.js 2026-07-05 18:07).
- **Calibration-complete:** `frontend/data/backcast/calibration-complete.json` → `"complete": {}`. No ISO declared; 2022/H1-2026 holdouts fully quarantined from solves/scores.
- **CI is RED on main:** live `python scripts/audit_keepers.py --check` exits 1 — PJM E9 (sidecar names `pjm-77-ct-relfloor-ablation`, registry JSON missing) + MISO E9 (no twin at all); 7 warnings (E7 staleness ×4, E9 grandfathers ×3). `ci.yml` `quarantine-gates` (lines 67–91) runs this on every PR, so every PR fails the gate until fixed.
- **In-flight work:** zero open PRs; only `origin/main` and this audit branch exist. Scope-ownership claims in merged PR text (orchestrator refactor owns `runner.py`/`run_calibration*.py`/`pipeline/`; "separate effort" owns E9 twins) refer to sessions that are now merged/idle — **effectively everything below is unowned**.
- **Open-issue ledger:** 12 open issues (#1302, #1335, #1336, #1344–#1350, #1372, #1373) are the declared follow-up queue for the body-less `push_files` PRs.

---

### Addendum — state as of 2026-07-06 PM (post-wave-3 governance pass)

*Verified against live `origin/main` in this session; does not rewrite the
snapshot above, which is left as the 2026-07-05/06 audit baseline.*

- **Quarantine gate is GREEN.** Live `python scripts/audit_keepers.py --check`
  now exits **0** (was exit 1 at audit time): 0 failures, 6 warnings (E7
  staleness ×5 — ERCOT/CAISO/PJM/NEISO/MISO — + 1 E9 grandfather, CAISO). `G-01`
  and `G-02` are **closed**: PJM (`pjm-77-ct-relfloor`) and MISO
  (`miso-41-ct-evening`) both now carry a registered ablation twin
  (`2026-07-05-pjm-77-ct-relfloor-ablation`,
  `2026-07-06-miso-41-ct-evening-ablation`) and MISO now has a
  `calibration_attestation.json`
  (`results/calibration/MISO/miso_41_ct_evening_window/`). **`G-03` is NOT
  closed** — checked, not assumed: `audit_keepers.py`'s
  `E9_ABLATION_TWIN_GRANDFATHER` frozenset still carries the live (uncommented)
  entry `"2026-07-03-miso-39-reserve-pergen"`, long superseded as MISO's
  keeper and no longer needed now that `miso-41-ct-evening` has its own twin;
  removing it is `scripts/audit_keepers.py` code and so out of this pass's
  file-ownership scope (sidecars/status/docs only) — left for a future code
  session.
- **Keeper swaps since the audit:** ERCOT `ercot32-ordc-total-rtolcap` →
  **`2026-07-06-ercot34-stage4-overlay-off`** (AS co-opt Stage-4 overlay-off
  integration, owner sign-off — closes **G-38**'s "Stage 4 run not done"
  blocker); NYISO `nyiso-41-hub-prices` → **`2026-07-06-nyiso-53-li-tsl`**
  (Zone-K LCR/TSL import-cap mechanism replacing the LI 0.45 self-supply floor,
  issue #1345's fix direction). Both new keepers carry a `calibration_attestation.json`
  DOF ledger (5 free-parameter entries each) and a registered zero-forcing
  ablation twin — rule-21 spot-checked and confirmed in this session; a
  `calibration-keeper-auditor` pass also confirmed no drift in the
  Calibration Status page, per-keeper run-report headers, `keepers.json`, or
  `status.js` for either new keeper.
- **#1345:** the LI floor mechanism fix described in the issue's "fix
  direction (future batch, W3/W4)" section has **landed** in `nyiso-53`'s
  recipe (`nyiso_li_lcr_tsl`, driven by the committed `nyiso.csv` LCR/TSL
  table). The **GitHub issue itself is still open** as of this session —
  closing it is a visible cross-cutting action outside this pass's file
  ownership (sidecars/status/named docs only); flagged here rather than
  closed unilaterally. Recommend the owner close #1345 referencing
  `2026-07-06-nyiso-53-li-tsl`.
- **G-17 decided:** the holdout-policy memo's Option 1-vs-2 adjudication is
  **DECIDED — Option 2, 2026-07-06** (`holdout-policy-memo-2026-07.md` §(e)),
  now reflected in CLAUDE.md rule 22's amended text.
- **G-04 (E7 staleness) is NOT closed by this pass** — see
  `docs/handoffs/e7-staleness-memo-2026-07.md`'s 2026-07-06-PM addendum: the
  owner-approved four-sidecar cleanup turned out to be a no-op (every named
  probe has since been superseded as "newest" by a further, un-adjudicated
  same-day run for ERCOT/CAISO/PJM; NYISO's is moot because the keeper swap
  itself already resolved it). Fresh, still-open E7 WARNs stand against
  `ercot36-head-config-faithful`, `caiso-56-zero-drag`, `pjm-80-srmc-reground`,
  and (unadjudicated, unrelated to this memo) `neiso-wfuelsec-ab-v2off` /
  `miso-42-coal-econ`. No sidecar was edited.
- **G-09 (D-9 report staleness) is closed**: `docs/handoffs/d9-keeper-quarantine-report-2026-07-05.md`
  was already regenerated in-band by both keeper-swap commits (`81819e6` ERCOT,
  `30627ab` NYISO) and verified current in this session — no edit needed.
- **G-10 (statmode twin staleness) refreshed, not resolved:** explicit
  truth-in-labeling stale-boxes now exist in
  `docs/statistical-mode-results-2026-07.md` for **both** ERCOT and NYISO
  (NYISO's box pre-existed and was accurate; ERCOT's was added this session).
  The D-7 twins themselves are **not** re-run — that is a separate solve
  session, out of scope here (no solves this pass).
- **Memos delivered this session:** E7 staleness memo status line updated
  (no edit applied — see above); D-7 statmode staleness boxes refreshed;
  D-9 report verified current; this addendum.
- **Zero open PRs**, confirmed via `mcp__github__list_pull_requests`; branch
  `claude/post-wave-3-governance-tcub42` is even with `origin/main`
  (`ac11191`) at session start.

---

### Addendum — state as of 2026-07-06 EVE (post-#1500 tranche review)

*Appended by the wave-manager tranche-review session; full verdicts in
`docs/handoffs/wave-manager-tranche-review-2026-07-06.md`.*

- **Tranche #1491–#1500 reviewed adversarially** (8 PRs; #1492/#1495 are issues):
  #1491/#1493/#1494/#1497/#1499 CLEAN (bounded caveats in the review doc);
  #1498 DEFICIENT-minor (keeper bookkeeping: stale bundle `metrics.json`,
  missing NEISO statmode stale-box, D-2 `''`-bucket mis-attribution, undeclared
  reach-ratio DOF dependency); #1500 DEFICIENT-hygiene (merged before CI
  finished; two PR-caused test failures now live on main).
- **CI is RED on main again** (was green at the 07-06 PM addendum): fast tier —
  stale hydro expectation (#1495, from the #1490 EIA-930 backfill) + the two
  #1500 data-contract failures; quarantine gates — `legitimacy_diagnostics.py
  --keepers` D-2 recompute mismatch on 4 keepers (#1488: `''`-bucket
  denominator machinery + genuine NYISO post-re-derivation staleness).
  `audit_keepers.py --check` itself stays PASS (6 warnings).
- **Keeper churn:** NEISO swapped to `2026-07-06-neiso-49-stgas-netload`
  (#1498) — rule-16/21 artifacts verified present; caveat budget UNCHANGED
  (hard C2+C7 2>1, soft C3a/b/c+C5b 4>2), so NEISO is closer structurally
  (first ST_GAS D-1 pass, 2025) but not budget-closer. ERCOT `ercot34`
  promotion also closed G-12 (replay-gap attribution, ercot35/36 A/B) and
  flips C1-2024 to PASS, mooting §4's "C1-2024 ledger" judgment item.
- **Rows refreshed in this session** (§3.1–3.4 below): W21/G-25 (MISO
  commitment-posture lever BUILT, honesty-gate-REJECTED probe `miso-43`
  registered, default-off); G-16 (new NEISO keeper: 2025 ST_GAS pass, 2023/24
  still FAIL); G-12 (closed per above); G-38 (Stage-4 run done, ercot34
  promoted). G-18/G-45/G-46/G-47/G-48/G-49-doc-half landed in earlier waves
  (verified on disk this session).
- **New open issues since the audit:** #1483/#1484 (PJM G-21 re-grounding
  relocated the miss; C8 drag decision unblocked), #1488/#1495 (CI reds),
  #1492 (CAISO reserve co-opt design, anchors collected).
- **Owner-decision queue** (8 items) recorded in the review doc §"Owner-decision queue".

---

### Addendum — 2026-07-06 (calibration-complete adjudication, NYISO + NEISO)

*Appended by the marker-adjudication session; full record in the 2026-07-06
calibration-log entry of the same name.*

- The rubric-v2 memo §6 recommendation (declare NYISO and NEISO complete) was
  put to the owner with verified preconditions (both keepers re-scored
  CALIBRATED-WITH-CAVEATS at HEAD; `audit_keepers.py --check` exit 0; U-01
  resolved; G-13 adjudicated moot for nyiso-53). **Owner HELD both markers:**
  NYISO until #1344 (reserve-scarcity data ask) lands — the C8 CT
  forced-share caveat dominates; NEISO until the winter-fuel Component-B /
  C7 ST_GAS residual is re-examined. `calibration-complete.json` remains
  `"complete": {}`; the 2022/H1-2026 holdouts stay fully quarantined for all
  six ISOs; no solve, intake, or dashboard change was made.
- G-19's costing note stands: NYISO/NEISO one-shot execution requires
  first-time holdout intake (CAMPD 2022 state files, zonal load/SMD 2022, hub
  LMP 2022, keeper-lever gas-basis series 2022) and the H1-2026 half is
  publication-blocked (CAMPD Q2-2026, delivered gas May+, F3).

---

### Addendum — 2026-07-06 (post-#1503–#1532 wave-manager tranche review)

*Appended by the same-day evening wave-manager tranche-review session; supplemental hygiene notes on register entries for three PRs in the final handoff batch.*

- **PR #1523 register hygiene note:** #1523 is a **byte-identical duplicate re-push** of #1522 (no new content, same commit/bundle payload). Flagged here as a register-keeping hygiene note, not a defect requiring rework or separate adjudication. The bundled probes/attestation/dashboard entries stand as filed under #1522's sidecar; no duplicate entry or separate keeper line required.

- **PR #1506 dashboard claim correction:** The PR's headline (neiso-49 metrics.json re-attested UNATTESTED→attested) **does NOT appear in #1506's own diff**. Verification found the file was re-attested by the rubric-v2 rescore commit `8e12e34` (post-#1436 keeper-swap wave), not by #1506's changes. #1506 mis-describes its own content; the stated defect fix (#1498's stale bundle + missing neiso statmode-stale box + D-2 bucket mis-attribution) is real and fixed on main, but the metrics.json attestation claim should be credited to the rubric-v2 rescore, not #1506. No re-gate needed; entry stands as corrected.

- **PR #1532 FPR adoption flagged for owner review:** #1532 adopts the published PJM/MISO FPR ratio directly (`ICAP_TO_UCAP_RATIO` from the RTO market filings) to replace the calibrated forward-scarcity equivalent. **OPEN forecast-side flag:** #1513's own handoff §6 explicitly said FPR adoption would NOT occur, citing the incompatibility: FPR embeds ~77% marginal-ELCC capacity-value (market floor estimate) vs the model's ~0.92 = (1−EFORd) supply-side basis → sign-flip risk on net-new-entry payoff in high-scarcity scenarios. Logged here as an **OPEN item for owner review before any forecast promotion**, pending reconciliation of the basis mismatch.

---

## 2. Workstream inventory

Status verified against code/artifacts; "doc-lag" marks where the plan doc's own status section is wrong (both directions occur).

| # | Workstream (primary doc) | Verified status | Key open items |
|---|---|---|---|
| W1 | Orchestrator unification (`handoffs/orchestrator-unification-plan-2026-07.md`) | Stages 0/1/5 delivered; **stages 2/3/4/6/7 not started** (`src/market_sim/pipeline/` holds only `spec/prior/result.py`) | Fleet unification, P2 core, backcast-config/getattr fold (incl. `caiso_ra_min_load_frac` 0.40 trap, plan L219); MISO golden uncapturable (15 GB OOM); A5 forecast ERCOT reserve cap |
| W2 | Scalar remediation (`handoffs/scalar-remediation-plan-2026-07.md`) | W0 closed, W1/W2 substantially done (plan §0 stale = doc-lag); **W3/W4/W5 open** | C-16/C-17/C-18/C-6/C-9/C-15 intakes; C-3 AS endogenization; C-14 `CAISO_BIDIR_EXPORT_CAP_MW=4361.0` static (transmission.py:339); W5 close blocked by E9 red |
| W3 | Probability bounds (`handoffs/probability-bounds-plan-2026-07.md`) | PB-0..PB-4 machinery all landed (doc header "design only" = doc-lag) | **PB-5 production ERCOT band never run** (`frontend/data/forecast/` = synthetic fixture only); λ(h) hindcast conditioning UNMEASURED; datacenter axis ties to unbuilt CX-4 |
| W4 | FOM + scarcity joint protocol (`handoffs/fom-scarcity-joint-protocol-2026-07-05*.md`) | Stages 1+2 run; **flip refused twice — FOM inert** behind nameplate→accredited floor + 15.2 GW backstop flood | Foresight A/B never run on reconciled code (no promotion); 3 recorded unblocking paths unrun; tornado FOM re-centring deferred |
| W5 | Capacity economics (`handoffs/capacity-economics-plan-2026-07.md`) | Stages 1–2 landed (#1396/#1417/#1413/#1432): accredited floor, pro-forma screen revenue, shape-aware VRE entry | CX-4 DC-load block unbuilt (grep: no datacenter symbols in src); **CX-6a nuclear-RPS fix marked "FIX NOW" but NOT landed** (nuclear in `_CLEAN_FUELS`, capacity.py:127, gets RPS shadow at :964); CX-6b WACC; ORDC footing as hindcast default |
| W6 | Sensitivity tornado (`handoffs/sensitivity-tornado-ercot-2026-07-04.md`) | Landed + ERCOT run | Retirement DOFs show zero leverage on 2026–28 window; 2035 re-run owed |
| W7 | MIP UC crossbench (`handoffs/mip-uc-crossbench-*.md`) | Diagnostic landed | **DP-1: P1 has no min-load → +34% committed CC energy vs MIP**; remediation not started |
| W8 | Emissions mass cap (`handoffs/emissions-mass-cap-plan-2026-07.md`) | Implemented default-off; forecast path wired (runner.py:1199–1218); **backcast harness now wired too (G-29, closed 2026-07-06)** | RGGI dual-vs-auction probe now runnable via either calibration script; NOx cap + banking/borrowing follow-ons remain |
| W9 | CO2 forward rates (`handoffs/emissions-co2-rate-plan-2026-07.md`) | Landed incl. 7-yr CAMPD intake | `use_plant_emission_rates_v2=False` never flipped though its stated precondition landed; scenarios.py:388 rationale comment stale |
| W10 | Control-retrofit forward channel (`handoffs/emission-control-retrofit-forward-channel-2026-07.md`) | Landed | Triple-gated inert (v2 flag + retrofit flag + forecast mode) until E2 NOx/SO2 wave |
| W11 | CO2 keeper re-gate (`handoffs/co2-keeper-regate-2026-07-05.md`) | Done; serves as the pending-re-gate ledger | NYISO stale-vs-HEAD entry outstanding |
| W12 | Confirmed retirements (`handoffs/confirmed-retirement-plan-2026-07.md`) | Registry 6-ISO (#1420); default ON (#1434) with forecast-only hard gate + byte-identical backcast proof | **Braunig double-count** (registry rows coexist with `BIN_FORCED_DERATE_BY_YEAR["SC_STGAS3"]` hardcode, fleet.py:4347) deferred; **CAMPD plant_code identity loss** — exits ≥2 yrs into a CAMPD forecast unmatched (capacity.py:2346–2354; `keep_plant_codes` attempt reverted); capacity.py:2340 comment still says "default off" |
| W13 | Forecast validation program (`handoffs/forecast-validation-program-2026-07.md`) | Core landed; doc's "CI not landed" claims CONTRADICTED (ci.yml exists = doc-lag) | Golden-scenario band regression not seeded (no `tests/golden/`); NEISO default forecast infeasible (F0); PJM 2021 demand re-run pending |
| W14 | Capacity hindcasts (`docs/hindcast-reports/`) | 5 runs registered; screens materially fixed (1afe440, 2e43ad6); wind +58%→−21%; retirements 0→9.7 GW | **Solar entry still 0 GW** — harness leaves `scarcity_pricing_enabled=False` (flat ~$25 duals), recorded flip not done; **retirement recall now 94% false-retire** (zone re-aggregation grain) diagnosed only; PJM not re-run with reversal channel; I7 floor-doesn't-force-build FAIL stands (#1426) |
| W15 | Out-of-sample / D-6 D-8 (`docs/out-of-sample-results-2026-07.md`) | D-6 zero solves (quarantine intact); D-8 run | Undiagnosed **CAISO keeper-reproducibility drift on HEAD** (issue #1346); ERCOT keeper also not container-reproducible (FINDING-ercot §6.3) |
| W16 | Statmode D-7 (`docs/statistical-mode-results-2026-07.md`) | Refreshed (#1425) | CAISO/NYISO r2 solves confounded (no same-SHA keeper replay); NYISO inherits B-NYI-1 de-leak uncompensated; **PJM/MISO statmode twins now stale after the 07-05 keeper swaps (rule unmet, unflagged)**; ERCOT-vs-others criteria denominators not comparable |
| W17 | Holdout policy (`handoffs/holdout-policy-memo-2026-07.md`) | CI wiring done (de facto Option 2) | Option 1-vs-2 **owner adjudication still open**; `--holdout-authorized` entry-point guard never landed — direct `--year 2022` is ungated (run_calibration_full.py:4619) |
| W18 | D-9 keeper quarantine report (`handoffs/d9-keeper-quarantine-report-2026-07-05.md`) | PASS artifact; CI-regenerated | Committed file stale vs 07-05 keeper swaps; contains no D-8 content despite label |
| W19 | Multi-ISO triage (`handoffs/multi-iso-triage-2026-07.md`) | **Plan only — nothing executed** | Rule-16 MISO amendment; 27-file docs reorg; keeper refs already superseded |
| W20 | NEISO winter fuel (`docs/multi-iso/neiso-winter-fuel-inventory-plan-2026-07.md`) | Component A code landed default-off (`winter_fuel_inventory.py`, dispatch.py:545; doc header "not implemented" = doc-lag); probe run per handoff notes | Probe found inventory cap INERT / oil under-ran; Component B (winter must-run) unbuilt; **no calibration-log/dashboard registration of the probes found (rule 15)** — probe-run status partially UNVERIFIED |
| W21 | MISO scarcity tail (`docs/multi-iso/miso-scarcity-tail-diagnosis.md`) | Mechanism landed (BPM-002 curve, no fitted breakpoints); gate CLOSED-NEGATIVE — >$200 tail still 0 h (kept per rule 1). **Commitment-posture lever now BUILT** (2026-07-06, G-25/DP-1 pooled SA design, zero fitted parameters, default-off) and probed (`miso-43-commitment-posture`): **honesty-gate REJECTED** — modeled postured online headroom 3.7–4.2× the measured MISO ASM series; lever stays default-off, keeper unchanged, $200 tail still 0 h ×3. | Midwest locational reserve zone still unbuilt (DATA-BLOCKED); coal offered $4–5 below SRMC open |
| W22 | ERCOT AS co-opt (`handoffs/ercot-as-coopt-plan-2026-07.md`) | Stages 0/1/2/5 in (#1366, #1416) | **Stage 4 overlay-off integration run + keeper decision NOT done**; Stage 3 HSL intake credential-blocked; "ercot40" run-label collision |
| W23 | Forward RTOLCAP WS-A (`handoffs/ercot-rtolcap-forward-2026-07.md`) | Gate PASSED (Δdw ≤ $0.11) | ±11% level residuals documented not closed; forecast storage term unexercised |
| W24 | Storage-AS duration gate WS-B (`handoffs/ercot-storage-as-duration-gate-2026-07.md`) | Built + probed | Validation 0.54–0.61× — **below the 0.8–1.3× acceptance band** |
| W25 | NYISO downstate reserve (`handoffs/nyiso-downstate-reserve-incidence-2026-06.md`, issue #1344) | Both static levers refuted; frontier ledgered; RCPF overlay landed default-off/inert | #1344 endogenous scarcity price formation data-blocked (measured prices exist; condition-varying requirement doesn't); SENY MW placeholder (nyiso-rcpf-overlay.md:134) |
| W26 | ERCOT HSL intake (`handoffs/ercot-hsl-2024-25-intake-attempt-2026-07.md`) | BLOCKED — ERCOT SiteMinder/401 credentials wall | Gross-up fallback stands |
| W27 | PJM CC overgen / reserve (`docs/pjm-cc-overgen-recommendation-2026-06.md`, `docs/multi-iso/pjm-reserve-ordc.md`) | Analysis done, partially superseded by pjm-77 | Rank-2 per-gen reserve co-opt blocked on memory + ramp-rate data absent from FleetArrays |
| W28 | Scope2 LCE portfolio (`scope2-lce-portfolio/`) | 6-ISO backcast bridge done (#1418/#1429) | CAISO Mode A no-cost-tiebreak degenerate frontier — needs LP-design follow-up |
| W29 | Demand-loading hardening (#1437) | Seam hardened | `strict_demand_profile` field not threaded to runner.py:470/:861; default flip pending clean-tree CI precondition |
| W30 | Misc multi-ISO | — | miso-zonal-gate2: intra-Midwest zone-mean order "entirely absent"; NEISO F2 blocked on U4 upload |

---

## 2b. Cross-reference: earlier gap documents folded into this register

Two earlier gap-tracking documents predate this register. Their open items are
subsumed here; their closed items are recorded for traceability. Update status
in THIS register, not in the earlier documents (which now carry supersession
notices pointing here).

**Forecast-methodology gaps** (`docs/forecast-methodology-gaps-2026-06.md`, 13
items G1–G13): 8 closed before this register was written (G5–G10, G12, G13);
G2 is a backcast-bridge needing no build. The 4 open items map to:

| Methodology gap | This register | Notes |
|-----------------|---------------|-------|
| G1 (flagship AS co-opt) | G-20, G-22, G-25, W22 | Scarcity + shape + commitment + AS co-opt workstream |
| G3 (ECRS requirement) | G-20, W22 | Folded into scarcity + AS co-opt |
| G4 (Load-resource RRS-UFR) | G-20, W22 | Folded into scarcity + AS co-opt |
| G11 (MISO neighbor-HR) | G-26 | Scalar family (neighbor-implied-HR forecast) |

**Wiring gap inventory** (`docs/audit-wiring-iso-gaps/gap-inventory.md`, 22
items A1–A13 / B1–B5 / C1–C4): 15 of 16 actionable items LANDED. The sole
open item maps to:

| Wiring gap | This register | Notes |
|------------|---------------|-------|
| A5 (ERCOT single-product reserve supply cap) | W1 Stage 2 | Absorbed into orchestrator unification |

---

## 3. Gap register

### 3.1 Governance & CI (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-01 | ~~**CI red on main**: PJM keeper's ablation twin dangling, MISO keeper has no twin.~~ **CLOSED (2026-07-06, triage session)**: caiso-58 was the last E9 blocker (PJM/MISO twins already landed). Solved + registered the zero-forcing ablation twin `2026-07-06-caiso58-v2-regate-ablation` (ablation_of=caiso58_v2_regate), linked from the CAISO keeper sidecar `ablation_twin`. `audit_keepers.py --check` now **exits 0**. NOTE: greening `audit_keepers` unmasks a SECOND quarantine-gates red — see **G-59** (D-2 recompute). | audit_keepers.py:213–252 (ablation_twin_finding); registry/2026-07-06-caiso58-v2-regate-ablation.json; verified `--check` exit 0 at HEAD | B | ~~blocks-claim~~ closed | done |
| G-02 | MISO keeper bundle **unattested** — no `calibration_attestation.json`; rubric §C6 alone forces NOT-YET. | `results/calibration/MISO/miso_41_ct_evening_window/`; calibration-determination-rubric §C6 | B | blocks-claim | S (judgment + file) |
| G-03 | ~~E9 grandfather list stale — still names superseded `miso-39-reserve-pergen`.~~ **CLOSED (2026-07-06)**: entry removed from the `E9_ABLATION_TWIN_GRANDFATHER` frozenset (commented tombstone remains at audit_keepers.py:132). | audit_keepers.py (verified at HEAD) | B | ~~debt~~ closed | done |
| G-04 | ~~E7 staleness unadjudicated: newer registry runs exist for keepers.~~ **ADJUDICATED (2026-07-06, triage session)**: per-ISO swap-or-keep memo. CAISO (`caiso51-statmode-v2`), NYISO (`nyiso-54-downstate-daily`), NEISO (`neiso-wfuelsec-ab-v2off`) newer runs are non-keeper statmode/attribution/probe twins → **E7 false-positives, KEEP**. ERCOT (`ercot38-measured-hsl-2425`) is all-years + more-measured (rule #10) but **unattested** and regresses C2 while fixing C3a/C5c → **escalated to owner** (no auto-swap). | docs/handoffs/e7-staleness-adjudication-2026-07-06.md | B | ~~debt~~ closed (ERCOT owner-decision pending) | done |
| G-05 | Rule-20 forced-energy budget breached by 4/6 keepers' committed bundles: ERCOT CT 11.1% (2023), CAISO CT 27.5–32.6%, PJM CT 12.1% (2024), NYISO CT 46–49% + ST_GAS 43.8–64.5% (caps 10/30%). Disclosed via C8-hard NOT-YET, but rule's letter says "a keeper fails". | `results/calibration/<bundle>/legitimacy_diagnostics.md` D-2 rows; legitimacy_diagnostics.py:110–112 | B | blocks-claim | SH (structural, per ISO) |
| G-06 | ~~CI's keeper-wide legitimacy run covers only D-9/D-6 — no CI step recomputes D-2 from parquets.~~ **CLOSED (2026-07-06)**: `legitimacy_diagnostics.py --keepers` now recomputes D-2 forced-energy from each bundle's committed data rather than trusting the JSON at face value; wired into the `quarantine-gates` CI job (ci.yml:70/:93–96). | ci.yml:70,93–96 (verified at HEAD) | B | ~~debt~~ closed | done |
| G-07 | ~~`FORWARD_SKILL_ENV` env knob can alter neighbor prices for forecast years — off-registry channel by rule-23 letter (unreachable in scored backcasts).~~ **CLOSED (2026-07-06, PR #1558)**: env knob removed from `neighbor_price.py`; no env-var neighbor-price channel remains at HEAD. | src/market_sim/data/neighbor_price.py (verified clean at HEAD) | B | ~~debt~~ closed | done |
| G-59 | ~~**CI red (masked)**: the `quarantine-gates` job's 2nd step `legitimacy_diagnostics.py --keepers` FAILs its D-2 forced-energy recompute on the CURRENT keepers — committed forced-shares drift from a fresh recompute (caiso-58 CC_REGULAR 0.0527 vs 0.0003; pjm-83, miso-44 also drift).~~ **CLOSED (2026-07-07)**: root-caused NOT to stale artifacts but to the keeper recompute being a structural **lower bound** — `run_year(fleet_only=True)` runs no P2 solve, so it cannot rebuild the P2 `ra_mustoffer_bridge` (caiso-58 CC_REGULAR = 3.24 TWh RA must-offer, `MECH_RA_MUSTOFFER`; the gate already flags this `lower_bound`), and boundary-plant class-attribution jitter shifts a material share ≤ 1.65 pp (measured worst case CAISO CT_PEAKER; all other material classes < 0.2 pp). The committed shares are FAITHFUL — they match the owner-written caiso-58 sidecar disclosure (CT 59.7/65.9/65.4%). The originally-proposed *regenerate-to-recompute* fix was **REJECTED** (owner-confirmed 2026-07-06): it would erase the real disclosed forced energy and rewrite owner-attested shares to less-accurate values. **Fixed the gate instead** — `run_d2_keepers_verify` now subtracts the committed `ra_mustoffer_bridge` contribution and compares the REBUILDABLE per-class gated share within `D2_VERIFY_SHARE_TOL`=2.5 pp (still fails a genuinely stale artifact off by more). `legitimacy_diagnostics.py --keepers` exits 0 (all 6 keepers PASS D-2/D-6/D-9); **no committed artifact modified**. | scripts/legitimacy_diagnostics.py:158-177 (D2_VERIFY_SHARE_TOL rationale), :894-1044 (run_d2_keepers_verify), :1020 (bridge exclusion); tests/test_legitimacy_diagnostics.py:807 (TestD2KeepersVerify, 11 tests incl. bridge-exclusion + jitter-tolerance + staleness-still-fails) | B | ~~blocks-claim~~ closed | done |
| G-60 | ~~**CI red**: fast-tier pytest `test_campd_bins.py::...test_emission_rate_uses_physical_hr_uniform_across_tranches` FAILs — a per-plant CO₂ rate (0.530) exceeds the CO₂ implied by the plant's highest bid-tranche HR (0.491).~~ **CLOSED (2026-07-07, PR #1604 commit `eeb5da6`)**: the invariant was legitimately scoped past the `use_plant_emission_rates_v2` measured-rate override — a v2 plant CO₂ rate is a measured CAMPD input (rule 13), not the physical-HR-derived value the test asserted, so the test now excludes v2-overridden plants rather than the code being "wrong". Test PASSES on main at HEAD. | tests/test_campd_bins.py (scoped past v2 override); verified `pytest` pass at HEAD | B | ~~blocks-claim~~ closed | done |
| G-08 | ~~Rule-16 all-years list amendment (add MISO) unexecuted; triage doc says MISO already complies — doc edit only.~~ **CLOSED (2026-07-06, docs sweep PR #1555)**: CLAUDE.md rule 16 now lists MISO in the all-years ISO list. | CLAUDE.md rule 16 (verified at HEAD) | B | ~~debt~~ closed | done |
| G-09 | ~~D-9 quarantine report committed artifact stale vs 07-05 keeper swaps.~~ **CLOSED (2026-07-06, triage session)**: regenerated via `legitimacy_diagnostics.py --keepers --report` against the current 6 keepers (0 superseded ids; was caiso-51/pjm-77/neiso-48/miso-41). D-9 overlay quarantine PASSES all 6. The regen ALSO surfaced that the current keepers' committed D-2 forced-shares drift from a fresh recompute → new CI red **G-59**. | handoffs/d9-keeper-quarantine-report-2026-07-05.md (verified 0 stale ids at HEAD) | B | ~~debt~~ closed | done |
| G-10 | Statmode D-7 integrity. **LABELING HALF DONE (2026-07-06, triage session)**: all six ISO sections now carry a stale-box naming (stale id → current keeper) — NEISO box newly created, ERCOT C1–C8-vs-C1–C5c incomparability flagged at three levels, D-2 `''`-bucket mis-attribution disclosed; 10 statmode registry sidecars marked STALE; a re-solve queue was added. **STILL OPEN**: PJM/MISO need a same-SHA keeper replay; CAISO/NYISO/NEISO r2/v2 twins remain confounded — the D-7 numbers are not yet valid for the current keepers. | statistical-mode-results-2026-07.md (stale-boxes + Re-solve queue at HEAD); #1425 | B | blocks-claim (for any D-7 skill quote) | SH (re-solves) |

### 3.2 Keeper integrity & reproducibility (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-11 | ~~CAISO keeper drift undiagnosed~~ **DIAGNOSED, disposition open (2026-07-06, L-10 wave-3)**: the drift is PR #1279 (the caiso-52 CT-floor scrub) — a legitimate rule-17/18/19 correction, NOT a regression; input hashes byte-identical across the run chain (code, not data). Do not revert. Disclosed on the caiso-51 sidecar. Remaining: the re-gate — the L-10 continuation solved the re-gate candidate at HEAD (`caiso-58`, keeper config + `use_plant_emission_rates_v2=True` per L-8 §9.6, caiso-55 as its v2-off twin); keeper swap is an owner decision (rule-20 tension: every drag-ON HEAD arm carries C8 59–71%). **OWNER DECISION (2026-07-06): swap to caiso-58. The C8 forced-energy budget is not a legitimate blocker when the forcing comes from structural reliability floors — the ct_netload_drag is a local-reliability commitment mechanism, and gating a keeper on its forced share runs counter to rule 1 (right market structure first). Combined with G-15 option C (local-capacity-revenue proxy) as the path to retire the drag.** **SWAP EXECUTED — CLOSED (2026-07-06)**: `2026-07-06-caiso-58-v2-regate` promoted to CAISO keeper (`keepers.json`, commit c043957), DOF ledger seeded (7e3708f); the keeper's byte-faithful HEAD replay with `use_plant_emission_rates_v2=True` also completes CAISO's G-39 re-gate. C8 59.7/65.9/65.4% disclosed on the sidecar per the owner decision. | keepers.json + registry `2026-07-06-caiso-58-v2-regate.json` (verified at HEAD) | B | ~~owner-decided~~ closed | done |
| G-12 | ~~ERCOT keeper not container-reproducible (replay CC_REGULAR 145.4 vs committed 133.2 TWh; 2024 C3a +2.3% vs +9.1%) — D-8 stability thread.~~ **CLOSED (2026-07-06, ercot34 promotion).** Attributed via the registered A/B pair `ercot35-replay-metagap-arm` (un-persisted-field replay) / `ercot36-head-config-faithful` (same keeper meta, all four un-persisted gas-geography fields restored, HEAD code): even config-faithful the keeper doesn't reproduce, and the residual is exactly two legitimate merged re-derives since the keeper's commit (coal max-CF ceiling re-derive + fleet.py curated-bin CHP relabelling) — not non-determinism. Resolved by the ercot34 promotion, which also flips C1-2024 to PASS. | FINDING-ercot-priceshape-2026-07.md §6.3 (original finding); `docs/handoffs/wave-manager-tranche-review-2026-07-06.md` (closure attribution); registry `2026-07-06-ercot35-replay-metagap-arm.json` / `2026-07-06-ercot36-head-config-faithful.json` | B | ~~blocks-claim~~ closed | done |
| G-13 | NYISO keeper STALE-VS-HEAD: not reproducible since the CT offer de-leak (0c6c833); "every NYISO solve is blocked until the CT offer level is grounded" (LI/NYC delivered-gas data ask). | #1421/#1427; calibration-log 2026-07-04 | B | blocks-claim | SH + external data |
| G-14 | ~~caiso-51 bundle internal inconsistency~~ **ADJUDICATED + CORRECTED (2026-07-06, L-10 wave-3)**: `meta.json` was the truth (the solve log proves `capacity_deliverability_limits` set the MIC seam cap 16,055/16,452/16,148 MW and `caiso_perhub_firm_base` was live); `run_config.json` had serialized dataclass defaults (keeper-era harness never threaded the two kwargs into `recorded_cfg`). Corrected in-file with a `post_hoc_corrections` record (46317a2). Residual harness gap: `caiso_perhub_firm_base` still un-threaded into `recorded_cfg` at HEAD (L-2/L-6 owners). | results/calibration/caiso51_firm_base/run_config.json (post_hoc_corrections) | B | closed (residual harness item) | done |
| G-15 | D-8 CAISO CT-drag instability — **closure A/B EXECUTED and FAILED (2026-07-06, L-10 cont.)**: the registered arm `2026-07-06-caiso-57-ramp-lcr` (drag OFF + ramp+LCR ON, full span, at HEAD) fails criterion (i) in all years (evening CT 309/146/106 MW vs drag ~690-860/~580-600/~425-445, actual 850/770/303) while (ii)/(iii) hold (D-2 CT forced 0.4/1.0/0.03%). Per the fail branch the drag STAYS, G-15 stays open, D-8 LOYO gate stays red. Failure evidence relocates the suppressor to P2 commitment economics (no LCR-dual/BCR credit in the hurdle — the follow-up build; D-8 closure doc §6). **OWNER DECISION (2026-07-06): option C — build a simpler local-capacity-revenue proxy in the retirement/commitment screen (not the full P2 rework). Combined with G-11 swap into a single CAISO keeper handoff.** **PROXY BUILT + PROBED (2026-07-06, PR #1556/#1561/#1565)**: LCR commitment-credit proxy (CAISO BCR/CPM analogue, Tariff §40.6) landed (8ef79ea) and probed as `2026-07-06-caiso-59-lcr-proxy` (proxy ON, drag OFF): CT 1.39/0.40/0.78 vs measured 3.05/3.30/1.65 TWh — structurally correct but does NOT alone replace the drag's CT-holding (drops ~0.6–1.3 TWh/yr vs caiso-58). Drag stays ON in the keeper; the residual CT gap needs a complementary mechanism (the drag carried both commitment-value AND scarcity-pricing roles — D-8 closure §6). Remaining: that complementary mechanism (the scarcity-tail overlay from the same PR set is the candidate); G-15 stays open, narrowed. | registry `2026-07-06-caiso-59-lcr-proxy.json`; docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §6 | B | open (proxy landed; complementary mechanism next) | SH (probe + keeper re-gate) |
| G-16 | ~~**UPDATED (2026-07-06, new keeper `neiso_stgas_netload`/neiso-49; re-verified post rubric-v2 recalibration).** ST_GAS D-1 now PASSES for the first time in 2025 (profile_r 0.844, off-peak cv_ratio 2.87), via the Connecticut ST_GAS net-load reliability-commitment limb + measured CAMPD-derived offer bands. 2023/2024 still FAIL (2023: r 0.49, cv_ratio 4.606 — off-peak CV collapse fixed from 35.4 but profile mis-phased evening-vs-actual-midday; 2024: r 0.725, cv_ratio 0.0 — flat-floor-only year at $2.19 HH gas). Keeper carries C7 as its single protective-tier ledgered caveat (1/1 budget), not a clean pass. Under rubric v1 this scored NOT-YET (hard 2>1, soft 4>2); under rubric v2 (`docs/calibration-determination-rubric.md` §9, landed 2026-07-06 after this row was last touched) the same run scores **CALIBRATED-WITH-CAVEATS** — zero FAILs, C2/C3a/C3b sit in the commercial band (auto caveats, unbudgeted), C3c+C5b are the 2 ledgered caveats (2/3 budget), C7 is the 1 protective caveat (1/1 budget).~~ **SUPERSEDED — IMMATERIAL-GATED, no structural work warranted (2026-07-07 materiality audit).** Two things moved, same day the paragraph above was written (2026-07-06): (a) the keeper swapped again to `2026-07-06-neiso-50-head-repro` — a byte-reproducible re-solve of the identical neiso-49 recipe (bundle `results/calibration/neiso49_resolve_confirm`; the row's cited `results/calibration/neiso_stgas_netload/` path never existed on disk) — and (b) the rubric v2.1 owner amendment landed a C7/C8 class-materiality floor. Verified at HEAD: NEISO ST_GAS annual energy is 0.2% / 0.1% / 0.3% of ISO load (2023/24/25, `max(model, actual)`, well under the 2% line); CT_PEAKER (0.5/0.7/0.6%) is the only other C7-gated NEISO class and also clears the floor. Gate definition + rationale (explicitly names NEISO ST_GAS 0.1–0.3% as one of the cases the 2% cut was calibrated against): `scripts/calibration_verdict.py:252-264` (`PROTECTIVE_MIN_LOAD_FRAC = 0.02`). Share computed by `_class_load_share` (`scripts/calibration_verdict.py:1266-1281`) and applied in `score_shape` (`scripts/calibration_verdict.py:1343-1359`). The current keeper's committed `results/calibration/neiso49_resolve_confirm/metrics.json` → `criteria.shape.records` shows ST_GAS and CT_PEAKER `status: "SKIPPED"` for all three years with the immateriality magnitude string, and `caveats.protective: []` — C7 no longer counts as even a ledgered caveat for this keeper (stronger than the "1/1 budget" claimed in the struck paragraph). **Reopens automatically if ST_GAS's own share ever crosses 2%** (a fuel-price shift or more oil-limit-binding hours could do it) — the underlying diurnal miss (profile r 0.49–0.85, off-peak CV mis-phased in 2023/24 per the metrics.json magnitude strings) is unchanged and would resume gating C7 at that point. | `scripts/calibration_verdict.py:252-264` (materiality floor + rationale), `:1266-1281` (`_class_load_share`), `:1343-1359` (`score_shape` gate application); `results/calibration/neiso49_resolve_confirm/metrics.json` (`criteria.shape.records`, `caveats.protective`); `frontend/data/backcast/registry/2026-07-06-neiso-50-head-repro.json` (keeper swap definition) | B | immaterial (reported by D-1, not gated) | done |

### 3.3 Holdout quarantine (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-17 | **Rule-22 intake-clause breach pending adjudication**: 2022 + H1-2026 raw source data for ERCOT+PJM landed 2026-07-04 under explicit owner instruction (PRs #1298/#1300/#1304) — no solve/score occurred (D-6 PASS, all 109 sidecars ⊂ 2023–25; bench dirs clean), but the memo's Option 1 (re-quarantine) vs Option 2 (amend rule text) decision is open. Until adjudicated, rule 22's text and the tree disagree. | data/raw/campd-unit-level/TX_2022.parquet et al.; out-of-sample-results-2026-07.md §1.1; handoffs/holdout-policy-memo-2026-07.md | B | blocks-claim | S (judgment + doc) |
| G-18 | No entry-point holdout gate: `run_calibration_full.py --year 2022` runs ungated (`--year` has no `choices=`/check); only the GH-Actions wrapper is gated. The memo's `--holdout-authorized` guard never landed. | scripts/run_calibration_full.py:4619 | B | blocks-claim | S |
| G-19 | Holdout one-shot validation data intake absent for CAISO/MISO/NYISO/NEISO — correct per rule 22 (deferred to validation time), recorded here so it is costed into any completion plan, not discovered at declaration time. **OWNER DECISION (2026-07-06): option B — defer intake to declaration time. No pre-authorization; intake happens when an ISO's calibration-complete marker is imminent.** | out-of-sample-results-2026-07.md §1 | B | debt (by design, owner-confirmed) | M (at declaration) |

### 3.4 Structural / mechanism gaps blocking calibration-complete (goal B — per ISO)

Full adjudication in §4. Register entries for the cross-ISO structural items:

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-20 | Scarcity price formation absent/insufficient in 4 ISOs (C3c ≈ 0 h): PJM (per-gen reserve/ORDC Phase 2 memory-blocked; ramp rates absent from FleetArrays), MISO (tail 0 h despite BPM curve — commitment posture + Midwest reserve zone unbuilt), NYISO (#1344 data-blocked), CAISO (no mechanism; C3c 0 h; log cites ~455h-vs-21h driver unknown). | pjm-reserve-ordc.md; miso-scarcity-tail-diagnosis.md:147–199; issue #1344; per-ISO adjudication | B | blocks-claim | SH each |
| G-21 | **PJM CLOSED (adopted 2026-07-06, keeper `pjm-83-srmc-reground`, L-13):** ST_GAS 0.48× and CT_INTERMEDIATE 0.9× re-grounded to the Manual-15 SRMC floor 1.00× — correct offer physics (rule 1), promoted on structure even though it adds a C2 sysvol FAIL (2025 coal +6.2%; 2024 CC over-run). The relocated volume residual is the unmodeled ST_GAS RMR/local-deliverability driver → **new issue #1483** (open); #1484 (C8 denominator) mooted (D-2 passes at the 0.15 budget both ways). Issue #1302 (generalize to NYISO/MISO/NEISO/CAISO committed bands) still open for the other ISOs. | FINDING-pjm-burndown-2026-07.md §2; calibration-log 2026-07-06 L-13; issues #1302/#1483 | B | blocks-claim | SH |
| G-22 | ERCOT price-shape structural miss: scarcity tail energy-offer-carried in reality but keeper's peak band collapsed to class p50; ~3.2 GW online-capability wedge (P1 perfect commitment); ercot33 offer-wall probe rejected. | FINDING-ercot-priceshape-2026-07.md §5–6 | B | blocks-claim | SH |
| G-23 | MISO C1 canonical miss: CC_REGULAR +44.35/+43.22 TWh (2023/24) — the rubric's own exemplar of a genuine structural miss; ct-evening floor didn't close it. Plus C5b storage throughput +1330% (2025) and C2 coal 2025 +8.8%. | rubric §C1; miso-41 attest data (status.js) | B | blocks-claim | SH |
| G-24 | NEISO winter fuel: Component A landed default-off, probe found the inventory cap inert (oil under-ran); Component B (winter must-run limb) unbuilt; the four soft caveats (C3a/b/c + C5b) all trace to this one missing mechanism. Probes not found in calibration-log/dashboard (rule-15 breach if they completed). | winter_fuel_inventory.py; dispatch.py:545; scenarios.py:946; neiso-winter-fuel plan | B | blocks-claim | SH (Component B + registered probe) |
| G-25 | ~~P1 commitment fidelity: MIP crossbench shows P1 (no min-load) carries +34% committed CC energy vs MIP; remediation unscoped.~~ **STRUCK / WON'T-FIX (2026-07-07, owner decision)** — over-engineered and not relevant to the live problem. On re-verification the only crossbench that exists is **ERCOT 2026 / first 744h / gas_cc only** (`diag_uc_mip_crossbench.py`); it was **never run on MISO/CAISO**, and its sign is the **opposite** of the framing: P1-LP commits 2,960,907 MWh vs MIP-UC 3,924,019 MWh, i.e. P1 **under-books** committed CC min-load energy by ~33% (the "+34%" is MIP over P1, mis-stated as P1 over MIP). An integrality bias that pushes committed CC energy *up* cannot explain a CC *over-run*. The real MISO/CAISO CC_REGULAR over-run is a merit-order / reliability / CT–ST_GAS–coal-drag / contract issue owned by **G-23**, not a commitment-fidelity gap. The rejected `miso-43-commitment-posture` lever stays default-off (rule 26). | docs/handoffs/mip-uc-crossbench-ercot-2026-gas_cc-mlf050-2026-07-04.md (ERCOT-only; P1 2.96M vs MIP 3.92M MWh) | B | ~~blocks-claim~~ struck (not-relevant) | won't-fix |
| G-26 | Residual-identified scalars still live, all on-ledger with open root-cause issues (rule 21's honest form, but each is an open channel a referee will probe): merchant CHP 35.0 (#1335), CC peaking pct (C-12), wefor 0.7/0.015 (#1348), coal sigmoids (#1347), COAL_TRANCHES + offer steps (#1336), CAISO WECC 7500 forecast fallback (#1373), NYISO LI 0.45 (#1345), seam tranches (#1350/C-6), PGE-TAC split (#1372), GAS_AVAILABILITY_FACTOR dead code (#1349). | constants.py:170–171, :200–205, :214–218; scenarios.py:1945/1962; iso_configs.py:332–337; transmission.py:339 | B | debt→blocks-claim per item | S–SH per item |
| G-27 | ~~Braunig confirmed-exit double-count: registry rows coexist with `BIN_FORCED_DERATE_BY_YEAR["SC_STGAS3"]={2025:0.686}` hardcode.~~ **CLOSED (2026-07-06)**: the `SC_STGAS3` hardcode is removed from `fleet.py` at HEAD; the confirmed-retirements registry is the single Braunig exit channel. | fleet.py (verified: no `SC_STGAS3` refs at HEAD) | B | ~~debt~~ closed | done |
| G-28 | ~~CAMPD plant_code identity loss: plant-binned units lose `plant_code` on post-base-year re-aggregation, so confirmed exits effective ≥2 yrs into a CAMPD forecast go unmatched (`keep_plant_codes` attempt reverted). Caps the just-flipped confirmed-exit channel's reach.~~ **CLOSED (2026-07-07)**: `aggregate_fleet` now passes CAMPD per-plant tranches (`is_campd_bin`) through un-aggregated — mirroring the existing `retirement_year` passthrough and `build_base_fleet`'s own year-1 grain — so `plant_code` + the tranche offer curve survive every projected year's re-aggregation. `apply_confirmed_exits` (matches by `plant_code`) now matches CAMPD plants at any exit year; retirement grain is per-plant not lumpy-zone (feeds G-31). Structural, not a `keep_plant_codes`-style propagation patch: the merge that dropped identity is removed, not worked around. Backcast keepers byte-identical (backcast never routes CAMPD bins through `aggregate_fleet`). Regression tests `test_fleet.py::test_campd_bins_pass_through_preserving_plant_code` / `_under_n_bins`. | fleet.py:2761 (`or g.is_campd_bin`); capacity.py:2584 (NOTE); tests/test_fleet.py | B | ~~blocks-claim (forecast)~~ closed | done |
| G-29 | ~~Mass-cap unreachable from the backcast harness: `run_calibration*.py` never thread `get_active_policy_constraints` — D-5 forecast/backcast parity gap; RGGI dual-vs-auction validation probe unrunnable.~~ **CLOSED (2026-07-06)**: `policy/constraints.py::build_mass_cap_dispatch_kwargs` (returns `{}`, byte-identical, when no cap is active) is now called from both `run_calibration.py::run_year` and `run_calibration_full.py::solve_and_persist` (own `--mass-cap-enabled`/`--mass-cap-tons`/`--mass-cap-program` CLI flags + `recorded_cfg` fidelity), so a backcast config with an active mass cap applies it identically to the forecast path. | constraints.py; run_calibration.py:2575–2584; run_calibration_full.py (`solve_and_persist` signature/run_year call/recorded_cfg block); tests/test_constraints.py; tests/test_recorded_cfg_fidelity.py | B | ~~blocks-claim~~ closed | done |

### 3.5 Forecast-side validation gaps (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-30 | Hindcast solar entry still 0 GW — root-caused to harness `scarcity_pricing_enabled=False` (flat ~$25 duals); the recorded one-line harness flip + re-run not done. | hindcast s2 report :25–40 | B | blocks-claim | M (flip) + SH (re-run) |
| G-31 | Hindcast retirement recall now 94% false-retire (over-corrected from 0-recall; lumpy zone re-aggregation grain) — diagnosed only. | ercot-2021-2025-realized-s2 report | B | blocks-claim | SH |
| G-32 | FOM flip + foresight promotion both undone: ATB FOM defaults still 12/8/40 (scenarios.py:248–256); flip refused twice for a real reason (adequacy-backstop flood masks it); foresight A/B never run on reconciled code; three recorded unblocking paths unrun. | fom-scarcity-joint-protocol-stage2 §3/§5; scenarios.py:717/:727 | B | blocks-claim | SH |
| G-33 | **RESOLVED.** CX-6a nuclear-RPS eligibility landed in full: the capacity retirement-screen RPS-shadow credit was split to `_RPS_ELIGIBLE_FUELS={wind,solar}` (a202a9f), and the dispatch RPS constraint row (`_build_rps_row`) now excludes nuclear too (this PR) so nuclear no longer counts toward the RPS target or its REC dual. The new-entry screen was already correct (`_RENEWABLE_NEW_FUELS`). `_CLEAN_FUELS`/`_FIRM_CLEAN_FUELS` retain nuclear/hydro for the clean-share and firm-clean *reporting* bases (not RPS). Nuclear support flows via `eac_price_nuclear` (ZEC/CES). Golden re-verified post-fix (see G-36). | dispatch.py `_build_rps_row`; capacity.py `_RPS_ELIGIBLE_FUELS`; tests: test_dispatch.py RPS suite + test_capacity.py::test_nuclear_not_credited_rps_shadow_in_retirement_screen | B | ~~blocks-claim (forecast)~~ RESOLVED | S–M |
| G-34 | CX-4 data-center load block. **MODULE BUILT (2026-07-06, triage session)**: `src/market_sim/data/datacenter.py` + `tests/test_datacenter.py` (29 pass); per-ISO cumulative DC-MW trajectories in `constants.DATACENTER_ADDITIONS_MW` (each anchor cited to primary ISO source); `ScenarioConfig.datacenter_load_path` default `"off"` ⇒ byte-identical, hard-errors in backcast mode (rule 22); tier-2/modeled-off. **STILL OPEN**: `add_datacenter_block` is not yet called from the demand-assembly/runner path, the electrification adder is not built, and the PB uncertainty datacenter axis is not wired. | src/market_sim/data/datacenter.py; config/constants.py (DATACENTER_ADDITIONS_MW); config/scenarios.py (datacenter_load_path) | B | blocks-claim (forecast credibility) | M (integration remains) |
| G-35 | ~~PB-5 production ERCOT probability band never run — the entire PB-0..4 machinery has only a synthetic fixture behind the public fan-chart page.~~ **DEFERRED (owner decision, 2026-07-07): parked until backcast calibration is established.** Not a blocking gap — the model's ability to run many scenarios is already demonstrated by the thousands of committed backcast/forecast solves, so PB-5 has nothing left to prove on that front and is not worth a multi-hour solve batch now. When it is built (post-calibration), the ensemble must be assembled from **separate, sequential** per-scenario solves: a single per-plant/keeper LP already approaches the memory ceiling (rule 12), so running ensemble members concurrently OOMs — the concurrent `ProcessPoolExecutor` member path in `ensemble.py` is NOT the intended production route and should be run at workers=1 (or one invocation per scenario) when the batch is eventually done. The PB-0..4 machinery (`matrix.py`, `uncertainty.py`, `structural_prior.py`, `ensemble.py`) stays landed and unit-tested; only the production batch + fan-chart wiring is deferred. | frontend/data/forecast/synthetic-fixture-ercot-v1.js; results/ensemble/; ensemble.py `_MAX_FORECAST_WORKERS` | B | ~~blocks-claim~~ **deferred (post-calibration)** | SH |
| G-36 | ~~Golden-scenario band regression seeded + re-verified~~ (done, #1438/#1446). **NEISO default-forecast infeasibility (F0) RESOLVED 2026-07-07:** IIS pinned it to the annual RPS row (`dispatch._build_rps_row`) — a hard `wind+solar ≥ 0.30×demand` with no escape, unmeetable by NEISO's ~4 GW front-of-meter VRE (~10 % of target). Fixed with a real-market **Alternative Compliance Payment escape column** (`VariableLayout.n_rec_acp` + `_rec_acp_off`, the ACP-coefficient in `_build_rps_row`, its ACP price in `build_cost_vector`, its `0≤ACP≤inf` bound in `build_variable_bounds`, and the per_hour zero-block; per-ISO ACP `constants.STATE_RPS_ACP` NEISO 65/CAISO 50/NYISO 40 $/MWh cited; `policy.rps.get_rps_acp`; threaded `runner.py`→`pipeline.spec.DispatchSpec`→`DispatchModel`) that keeps the row feasible and caps the REC dual at the ACP; ERCOT/PJM byte-identical (no RPS → no column). Full 8760 NEISO 2026 forecast now solves; 3 ACP dispatch tests (`test_dispatch.py::TestRPSConstraint`) + `test_capacity.py::TestGetRPSACP` green. **Deferred (owner, this session):** actually firing `forecast-invariants.yml` on Actions — skipped as redundant, since the tier is ERCOT-only and this change is provably byte-identical for ERCOT (the golden bands cannot move); left to the weekly cron. | F0 = forecast-invariant-findings.md; `dispatch.py:_build_rps_row`; `constants.py:STATE_RPS_ACP`; `policy/rps.py:get_rps_acp`; #1438; #1446 | B | ~~blocks-claim~~ F0 RESOLVED; heavy-tier fire deferred | M–SH |
| G-37 | ~~Storage-AS duration gate validates at 0.54–0.61× — below its own 0.8–1.3× acceptance band; shipped anyway (default-gated).~~ **DIAGNOSED (2026-07-07): dispatch-choice LIMITATION, not a coupling bug — stays open debt, coupling NOT the defect.** Reproduced 0.54/0.55/0.61× (bundle 166, exact `storage_reserve_dispatch`). The coupling (power-competition + duration gate, `dispatch.py:1441-1494`, SOC coupling `:1481-1483`) is structurally correct: hourly split shows storage keeps ~0.8× in loose midday charging hours (h11–16) and loses AS in the tight evening peak (h17–22, ratio 0.13–0.41) — tracking battery *discharge*, so evening SOC depletion from energy arbitrage forecloses AS via the (correct) gate. The recorded "free loose-hour thermal → tight-hour share" diagnosis is **backwards** (corrected in the handoff). Missing mechanisms (neither a knob, both out of scope for the storage coupling): (a) forward AS commitment under uncertainty vs perfect-foresight P1 greedy arbitrage; (b) evening fast-AS scarcity price formation (grounded ramp-qualified thermal-reserve limit, `data/ramp_capability.py`). Default-off, **not in the ERCOT keeper** (`ercot34`), so byte-identical; no LP change made. | `FINDING-ercot-storage-as-g37-2026-07.md`; `dispatch.py:1441-1494`; `run_calibration_full.py:772-774` | B | ~~debt~~ diagnosed (open debt) | SH |
| G-38 | ~~ERCOT AS co-opt Stage 4 (overlay-off endogenous integration, gates G-1..G-7, keeper decision) not run~~ **DONE (2026-07-06).** Stage 4 run (`2026-07-06-ercot34-stage4-overlay-off`: DAM-AS overlay retired + WS-A forward RTOLCAP/RTOFFCAP formula supply) completed and **promoted to keeper**, replacing the RTOLCAP-overlay keeper; G-3/G-5/G-6 PASS, G-1/G-2/G-4 disclosed misses per the run's own attestation. Stage 3 HSL intake remains credential-blocked (owner action, W22); "ercot40" label collision is now moot (superseded by the ercot34/35/36 run set). | ercot-as-coopt-plan §7; registry `2026-07-06-ercot34-stage4-overlay-off.json`; `frontend/data/backcast/keepers.json` (ERCOT); `docs/handoffs/wave-manager-tranche-review-2026-07-06.md` | B | ~~blocks-claim (overlay-replacement goal)~~ done | done |
| G-39 | ~~`use_plant_emission_rates_v2` never flipped though its stated precondition (7-yr CAMPD history) landed.~~ **OWNER DECISION (2026-07-06): option B — flip to True, re-gate incrementally.** **FLIP EXECUTED (2026-07-06)**: `use_plant_emission_rates_v2: bool = True` at scenarios.py:391 with the owner-decision rationale in the adjacent comment. Remaining: the incremental per-ISO re-gates piggyback on each ISO's next keeper cycle (CAISO's `caiso-58` already carries v2=True). | scenarios.py:391 (verified at HEAD); W9/W10 docs | B | flip done; re-gates piggyback | piggyback re-gates only |
| G-40 | ~~MISO memory ceiling (~15 GB/year LP) blocks regression-golden capture AND ensembles for MISO; unsolved infra constraint.~~ **REDUCED (2026-07-07, branch `claude/miso-memory-ceiling-me17ea`)**: the OOM is a *construction-peak in the LP builder*, not the HiGHS solve — attributed with `scripts/profile_lp_memory.py` (per-block nnz + construction/solve RSS split) to (a) the per-gen reserve block's dense `(n_gen,T)` cap intermediate and (b) `build_constraints`' pairwise `sp.vstack` chain. Both cut **byte-identically** (full-A CSR hash unchanged `2ef9d653db6e3cac` / `a95e92574ac37116`): (b) `_vstack_csr_free` single-pass freeing concat (already on main, ~1.17 GiB); (a) `_build_reserve_rows_pergen` now forms `pmax*availability` on the reserve-member subset only and `del`s it before the `joint` kron (this branch) — measured −0.78 GiB at the synthetic n_gen=12000 reserve-construction peak (4.84→4.06 GiB), scaling as ~n_gen×T×8 B. Pinned by `tests/test_dispatch_vstack_memory.py` + 132 reserve/posture tests. **Still open (not struck as done):** end-to-end MISO-keeper-under-15 GB unconfirmed here (no `data/clean` MISO partition on this 15 GB box); confirm via `MARKET_SIM_MEM_DEBUG=1 scripts/run_calibration_full.py --keeper miso-… ` on a ≥16 GB provisioned box before declaring golden-capture/ensembles unblocked. | dispatch.py:1651 (`cap_members`), :1906 (`_vstack_csr_free`); scripts/profile_lp_memory.py; orchestrator-unification-plan-2026-07.md §7.3.8 G-40 update | B | ~~debt~~ reduced (confirm on prov. box) | L |
| G-41 | PJM hindcast invariant I7 still FAILs (~1–4 k MW "floor doesn't force-build"). **DECISION MEMO DRAFTED (2026-07-06, triage session)**: framed as an invariant-DEFINITION owner decision (absolute floor vs retirement-bounded), not a harness bug. Root cause F1: `apply_reserve_margin_build` backstop exists but is gated off (`reserve_margin_build_enabled=False`, scenarios.py). Memo recommends a **market-design-dependent** split (absolute floor + backstop-on for capacity-market ISOs incl. PJM; retirement-bounded for energy-only ERCOT), with two preconditions. **OWNER DECISION + code change pending** (forecast-side only; no keeper re-gate). | docs/handoffs/pjm-hindcast-i7-decision-2026-07-06.md; capacity.py `apply_reserve_margin_build`; scenarios.py `reserve_margin_build_enabled` | B | debt (owner decision pending) | M |
| G-42 | Scope2 CAISO Mode A degenerate frontier (no-cost-tiebreak) — flagged, needs LP-design fix. | #1429 | B | debt | M |
| G-43 | ~~`strict_demand_profile` not threaded into runner solve paths — silent demand-corruption fallback remains possible until flipped.~~ **CLOSED (2026-07-06, PR #1557)**: `strict_demand_profile=config.strict_demand_profile` threaded at both runner.py solve paths (:475/:867) and exposed as a scenario knob. | runner.py:475/:867 (verified at HEAD) | B | ~~debt~~ closed | done |
| G-44 | ~~Pre-existing test failure on main: `test_export.py::test_year_summary_has_expected_fields`.~~ **CLOSED (2026-07-06)**: `TestExportScenarioJson::test_year_summary_has_expected_fields` passes at HEAD (verified live). | tests/test_export.py:188 (verified green at HEAD) | both | ~~debt~~ closed | done |

### 3.6 External usability (goal A)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-45 | **Backcast CLI `--help` crashes** — unescaped `%` in an argparse help string kills the documented entry point (`ValueError: unsupported format character 'C'`). A stranger cannot enumerate the ~1000 lines of flags. | scripts/run_calibration_full.py:4703; README.md:29 | A | blocks-release | S (one-line) |
| G-46 | **No runnable documented forecast**: `market-sim run` requires `--config` but no base scenario YAML exists anywhere; docs cite `scenarios/ercot_base.yaml` and `sweeps/capacity_sensitivity.yaml` — neither path exists. Schema must be reverse-engineered from scenarios.py:3409. | runner.py:1864–1867; docs/codebase/07-runner-and-cli.md:142–151; configs/ | A | blocks-release | S–M (write + doc one config) |
| G-47 | README's own test command fails: root `pytest` collection Interrupted by `scope2-lce-portfolio/tests/conftest.py:11` (`lce_portfolio` not installed; no `testpaths` in pyproject); README says "~1937 tests" vs 2924 actual. | README.md:43–48; pyproject.toml | A | blocks-release | S |
| G-48 | No data licensing/redistribution statement despite ~2.5 GB of committed EIA/EPA/ISO downloads; LICENSE is code-only Apache-2.0. PJM DataMiner / CAISO OASIS carry use-terms a redistributor should cite. | LICENSE; data/README.md | A | blocks-release | M (research + doc) |
| G-49 | Dashboard numbers not independently verifiable: displayed metrics live only in gzip+base64 `runs/<id>.js` blobs; committed bundles are slim (dispatch/, system.parquet gitignored); verification = full re-solve; the registration recipe is canonical only in `.claude/skills/calibration-report/SKILL.md` + CLAUDE.md rule 14 — agent instructions, not user docs. | frontend/data/backcast/runs/; .gitignore slim-bundle block | A | blocks-release (for "reproduce a published result") | M (doc + plaintext metrics sidecar) |
| G-50 | Raw-data provenance dir-level tribal: 9/12 sampled `data/raw/` subdirs have no README (incl. 805 MB `data/raw/ercot`); the file↔fetch-script mapping is undocumented for hand-assembled dirs; `pjm-energy-offers` refetch instructions live inside `.gitignore` comments (lines 15–20). | data/raw/; .gitignore:15–20 | A | debt | M |
| G-51 | Two divergent install paths (uv vs `run-simulator.sh` pip venv + launcher UI) with no statement of which is canonical. | run-simulator.sh; pyproject.toml | A | debt | S |
| G-52 | README quickstart is a single-year run with no note that rule 16 forbids single-year keepers (fine as smoke test, unstated). | README.md:29 | A | debt | S |

### 3.7 Docs-vs-code drift (goal A / hygiene)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-53 | ~~Capacity-evolution step-numbering conflict: CLAUDE.md "step 0→1→2" vs spec :657 "step 1b/2/3" for the same mechanisms.~~ **CLOSED (2026-07-06, docs sweep)**: CLAUDE.md capacity-evolution block now states "Same step numbering as `model-methodology-spec.md` §5.1". | CLAUDE.md:161 (verified at HEAD) | A | ~~debt~~ closed | done |
| G-54 | ~~CLAUDE.md architecture block under-describes the tree.~~ **CLOSED (2026-07-06, docs sweep PR #1555)**: architecture block now lists `pipeline/`, `ensemble.py`, `matrix.py`, `uncertainty.py`, `structural_prior.py`, `model/ancillary.py`, `policy/cap_and_trade.py`, `results/{rcpf,scarcity,evolution_ledger}.py`, and the expanded config/data module inventory. | CLAUDE.md architecture block (verified at HEAD) | A | ~~debt~~ closed | done |
| G-55 | `paths.py` docstring claims CLEAN_DIR is "future… nothing reads them yet" while 10+ modules read the clean seam. | src/market_sim/config/paths.py:25–27 | A | debt | S |
| G-56 | Plan-doc status sections systematically lag the tree ~1 day in BOTH directions (scalar/PB/NEISO-winter docs describe landed work as pending; forecast-validation/holdout docs describe since-landed CI as missing). A referee reading docs alone gets the wrong state either way. | W2/W3/W13/W17/W20 rows above | both | debt | S–M (`/sync-docs` sweep) |
| G-57 | ~~Stale in-code comments contradicting behavior: capacity.py:2340 "default off" (flag now default-ON); scenarios.py:388 v2 rationale.~~ **CLOSED (2026-07-06)**: capacity.py comments now read "default on, flipped 2026-07-05" (lines 12/2412/2575); scenarios.py:385–390 rationale rewritten with the G-39 owner decision. | capacity.py; scenarios.py:385–391 (verified at HEAD) | A | ~~debt~~ closed | done |
| G-58 | ~~README layout block omits `configs/`, `scope2-lce-portfolio/`, `results/hindcast/`.~~ **CLOSED (2026-07-06, docs sweep PR #1555)**: all three now present in the README layout block (:81/:96/:99). | README.md:81–102 (verified at HEAD) | A | ~~debt~~ closed | done |

### 3.8 UNVERIFIED / conflicting-evidence items

| ID | Item | Notes |
|---|---|---|
| U-01 | ~~NEISO winter-fuel probe registration state~~ **RESOLVED (2026-07-06, calibration-complete adjudication session): the probes were registered all along.** Component-A pair `2026-07-04-neiso-inventorycap-inert-probe` + `2026-07-04-neiso-dailybasis-oil-underrun` and Component-B pair `2026-07-06-neiso-wfuelsec-ab-v2`/`-v2off` each carry a registry sidecar, a `runs/<id>.js` payload, and a calibration-log entry (2026-07-04 / 2026-07-06). Rule 15 satisfied; no breach. | The audit's sweep predated/missed the 2026-07-04 landings. No action. |
| U-02 | "Confirmed-exit double-derate fix" as a named fix | No dedicated fix/test exists under that name; the derate-XOR-drop guard IS landed (capacity.py:316–352). Interpreted as: guard landed, Braunig hardcode overlap (G-27) is the surviving double-count risk. |
| U-03 | CX-6a evidence location | Plan cites dispatch.py:380–398; verification found the live defect at capacity.py:127/:964. Both cited in G-33; exact remediation site to be confirmed by implementer. |
| U-04 | G-14 caiso-51 meta/run_config disagreement | Found by the handoffs sweep; which file carries the truth was not adjudicated within budget. |
| U-05 | Empty-body PRs (~70 of 90) | Their follow-ups are assumed fully captured by the 12 open issues; individual commit-message markers were not exhaustively read. |

---

## 4. Per-ISO calibration-complete adjudication

All six keepers score **NOT-YET**; `complete: {}`. Rubric: eligible only at ≥ CALIBRATED-WITH-CAVEATS. Ordering closest→furthest: **NEISO ≈ NYISO, then ERCOT ≈ PJM, then MISO ≈ CAISO**. Cross-ISO shared blockers: ablation twins 5/6 missing (G-01), holdout intake for 4 ISOs deferred-by-design (G-19), E7 staleness judgment (G-04).

**Key finding: no ISO is judgment-only ready. Every ISO carries ≥1 work-ready blocker.** The only judgment-ready items anywhere are: ERCOT's C1-2024 ledger entry (insufficient alone — 2 hard caveats > budget 1), PJM's C8 drag-sizing/D-2-exemption decision, and MISO's C6 attestation (insufficient alone — C1 +44 TWh stands).

| ISO | Blocks the marker | Judgment-ready | Work-ready |
|---|---|---|---|
| **NEISO** | Caveat budget only (hard 2>1, soft 4>2); **no FAILs** — closest of the six | C2 re-score when final EIA-923 vintage lands | C7 ST_GAS diurnal root cause; winter oil-inventory build (collapses C3a/b/c + C5b, = G-24) |
| **NYISO** | C8 HARD FAIL (floors force 43–65% of class energy); 4 soft caveats > 2; keeper stale-vs-HEAD (G-13) | — | Floor re-derivation post delivered-fuel intake; #1344 scarcity formation; Iroquois Z2 / LI-NYC citygate data asks |
| **ERCOT** | C3b/c shape FAIL; C1-2024 CC −8.1 TWh; C8 11.1%; repro drift (G-12) | Ledger C1-2024 twin (doesn't unblock: 2 hard caveats > 1) | Offer-surface + commitment-thinness build (G-22); CC volume; C8; D-8 drift |
| **PJM** | keeper `pjm-83-srmc-reground` (2026-07-06): G-21 sub-SRMC bands re-grounded (C1/C2 offer-grounding CLOSED); CT_CHP D-4 fix DONE; D-2 PASS at 0.15; C3a/b/c FAIL (no reserve/ORDC) + new C2 sysvol FAIL (ST_GAS driver #1483) | reserve/ORDC Phase 2 + ST_GAS RMR/deliverability driver (#1483) | reserve/ORDC Phase 2 (memory + ramp data); ST_GAS actual-volume root cause (#1483) |
| **MISO** | C6 unattested (G-02); C1 +44 TWh (G-23); C3 all FAIL; C5b/c FAIL; C2 coal FAIL | C6 attestation; rule-16 doc amendment (G-08) | CC merit-order root cause; scarcity posture; storage throughput cost |
| **CAISO** | Worst: C3a +20–42% FAIL; C7/C8 floor FAILs; **undiagnosed HEAD drift (G-11)**; C4/C1/C2/C5a FAIL | — | Drift bisect FIRST (promotion is laundering until then); WECC import intake (#1373/#1372); evening-CT merit order; scarcity mechanism |

---

## 5. Proposed execution plan

Gaps grouped into parallel-safe lanes with exclusive file ownership. No lane below is owned by an in-flight session (zero open PRs; the "orchestrator refactor" and "E9 separate effort" owners are merged/idle — their scopes are re-assigned here as L-6 and L-1 explicitly). Solve-heavy lanes obey CLAUDE.md rule 12: ≤2 concurrent per-plant multi-zone invocations; years sequential within an invocation.

**Suggested model tiers** — mechanical doc/code fixes: Sonnet (or Haiku for pure prose); scoped single-mechanism code+test: Sonnet/Opus; calibration root-cause + keeper decisions: Opus/Fable; owner judgments: human + any tier drafting the memo.

### Wave 1 — unblock the board (all parallel-safe)

| Lane | Gaps | Scope & file ownership | Tier |
|---|---|---|---|
| **L-1 Governance/CI green** | G-01, G-02, G-03, G-09, G-04 (draft memo) | Run `scripts/run_pjm77_ablation_twin.py`, author+run MISO twin, register both (`results/calibration/**`, `frontend/data/backcast/registry/**`, `runs/**`); write MISO attestation; prune grandfather list (`scripts/audit_keepers.py` list only); refresh D-9 report. Exit: `audit_keepers.py --check` exits 0. | Opus (solves are mechanical but registration must be exact) |
| **L-2 Entry-point + holdout hardening** | G-18, G-45, G-17 (memo draft), G-06 | Owns `scripts/run_calibration_full.py` (argparse block ONLY: fix `%` crash, add holdout year gate w/ `--holdout-authorized`), `ci.yml`, `scripts/legitimacy_diagnostics.py` (D-2 recompute). Drafts Option-1/2 adjudication memo for owner sign-off. | Sonnet |
| **L-3 Stranger onboarding** | G-46, G-47, G-51, G-52, G-58 | Owns `README.md`, `pyproject.toml` (testpaths), new `configs/scenarios/ercot_base.yaml` + parse test, `docs/codebase/07-runner-and-cli.md` (fix phantom paths). MUST NOT touch run_calibration_full.py (L-2's). | Sonnet |
| **L-4 Data provenance & licensing** | G-48, G-50, G-49 (doc half) | Owns `data/raw/**/README.md`, new `docs/data-licensing.md`, new `docs/verifying-dashboard-numbers.md` (promote skill recipe to user docs; propose plaintext metrics sidecar — implementation deferred to L-5). | Sonnet (Haiku for READMEs) |
| **L-5 Doc-drift sync** | G-53–G-58, G-08, plan-doc status sections (G-56), W19 triage doc refresh | Owns `CLAUDE.md`, `model-methodology-spec.md`, `docs/handoffs/*` status headers, stale code comments (comment-only edits). Run as a single `/sync-docs`-style sweep AFTER L-1..L-4 merge to avoid churn. | Sonnet |

### Wave 2 — parity & forecast validation (parallel after Wave 1)

| Lane | Gaps | Scope & file ownership | Tier |
|---|---|---|---|
| **L-6 Orchestrator unification (stages 2/3/4/6/7) + parity** | W1 remainder, G-29 (mass-cap backcast wiring), G-43 (strict_demand_profile), the getattr fold | Owns `src/market_sim/pipeline/**`, `runner.py`, `scripts/run_calibration.py` solve core (coordinate: L-2 owns the argparse block of run_calibration_full.py — merge L-2 first). Largest single lane; do stages sequentially with the Stage-0 regression gate after each. | Fable/Opus, L |
| **L-7 Capacity economics & hindcast closure** | G-30, G-31, G-32, G-33, G-41, G-34 (design first), tornado 2035 re-run (W6) | Owns `model/capacity.py`, hindcast harness scripts, `docs/handoffs/capacity-economics-*`, `fom-scarcity-*`. Sequence: CX-6a fix → harness scarcity flip + hindcast re-run → foresight A/B on reconciled code → FOM unblocking paths → retirement-grain design. | Opus/Fable, SH |
| **L-8 Emissions forward decisions** | G-39, W10 activation plan, NOx cap follow-on (W8) | Owns `policy/cap_and_trade.py`, `policy/constraints.py` docs, emission-rate flags + plan docs. Mostly decision memos + a v2-flip re-gate probe. | Sonnet draft + Opus probe |
| **L-9 PB-5 production band** | G-35 (**deferred post-calibration, owner 2026-07-07**), G-36 (golden seeding + heavy-tier trigger) | Owns `configs/uncertainty_ercot.yaml`, `results/ensemble/**`, `frontend/data/forecast/**`, `tests/golden/**`. G-35's production band is parked until backcast calibration is established (see the G-35 row); the lane's remaining live work is G-36. When PB-5 is eventually run, ensemble members solve **sequentially/separately** (concurrent members OOM, rule 12). | Opus, SH |

### Wave 3 — per-ISO calibration lanes (max 2 solve lanes concurrent; each owns only its ISO's registry/bundle namespace + per-ISO config sections; shared-file edits to `fleet.py`/`iso_configs.py` must be section-scoped and rebased serially)

| Lane | Gaps | First move | Tier |
|---|---|---|---|
| **L-10 CAISO** | G-11 (FIRST), G-14, G-15, then evening-CT merit order + #1373/#1372 intakes | Bisect the post-07-03 drift before anything else — promotion before diagnosis is laundering. | Fable |
| **L-11 NYISO** | G-13, #1344, #1345, floor re-derivation | File the LI/NYC delivered-gas + Iroquois Z2 data asks immediately (longest external lead time). | Fable |
| **L-12 ERCOT** | G-22, G-12, G-38 (Stage-4 integration), G-37 | Stage-4 overlay-off integration run is the designed vehicle; fold price-shape work into its gates. | Fable |
| **L-13 PJM** | G-21 re-grounding cycle, C8 drag decision (owner), CT_CHP D-4 fix (small, do first), reserve/ORDC design | CT_CHP window fix + drag decision memo in day 1; re-grounding solve cycle after. | Opus/Fable |
| **L-14 MISO** | G-23, G-40 (memory), scarcity posture, storage throughput | Storage-throughput adder probe is the cheapest FAIL to clear; CC merit-order is the long pole. | Fable |
| **L-15 NEISO** | G-24 (Component B + registered probe), C7 ST_GAS, U-01 lookup | Closest ISO to the first calibration-complete marker — highest strategic leverage per solve. | Opus/Fable |

Post-completion (any ISO): the one-shot holdout validation per rule 22 (G-19 intake at that moment, frozen keeper, score once, record whatever results).

---

## 6. Top-10 if only two days remain

1. **G-01 + G-02 + G-03: make `audit_keepers.py --check` green** (PJM twin script already exists; MISO twin + attestation). Goal B. The repo's own CI currently refutes its flagship compliance claim on every PR — a hostile referee needs one command to dismiss rule 21. Cheapest large credibility item on the board.
2. **G-17 + G-18: adjudicate the holdout memo and gate the entry point.** Goal B. The quarantine is the program's single most load-bearing legitimacy claim; today the rule text and the tree disagree (ERCOT/PJM intake) and a one-flag CLI call can solve 2022 ungated. One owner decision + ~20 lines closes both.
3. **G-45: fix the `--help` crash.** Goal A. One character (`%%`). The very first command a stranger runs against the documented entry point currently stack-traces; nothing says "you cannot use this" louder.
4. **G-46: commit a base forecast scenario YAML + fix the phantom doc paths.** Goal A. The product is a *forecasting* model whose forecast mode has no runnable documented invocation; docs cite two files that don't exist. One example config + a parse test converts the headline capability from tribal to demonstrable.
5. **G-11: start the caiso-51 drift bisect (+ resolve G-14).** Goal B. The dashboard publishes keeper numbers current main demonstrably cannot reproduce, and the bundle's own meta/run_config disagree — the closest thing in the repo to an answer-key symptom even though it's likely a regression. Two days won't finish the re-solve; the bisect and the meta.json adjudication can land, which converts "undiagnosed" into "scoped".
6. **G-47: fix README's pytest command (testpaths) + G-44 test_export failure.** Goal A. The stranger's second command (run the tests) currently fails at collection, and one test fails even in-tree. Both are small; together with #3 they make the first-hour experience honest.
7. **G-48: write the data licensing/redistribution statement.** Goal A. 2.5 GB of committed agency/ISO data with zero stated terms is release-blocking legal debt for any external user; a survey of the actual source terms (EIA/EPA public domain vs PJM/CAISO conditional) is a day of document work, no code.
8. **G-49: publish "how to verify a dashboard number".** Goal A. Reproducing a published result is goal A's endpoint, and the recipe currently lives in agent skill files. Documenting the run→bundle→registry→dashboard chain (and proposing the plaintext metrics sidecar) makes every published number auditable in principle.
9. **G-04 + G-09 + G-10 (bookkeeping half): adjudicate E7 staleness, refresh the D-9 report, flag the stale statmode twins.** Goal B. All three are truth-in-labeling items on the public dashboard — cheap edits that remove standing WARNs and unflagged staleness a referee would read as carelessness.
10. **G-33: land the CX-6a nuclear-RPS eligibility fix.** Goal B. Marked "FIX NOW" in the plan, small blast radius, and it corrupts every forecast's entry economics — the highest-leverage forecast-correctness item achievable inside two days (the hindcast re-run to prove it can queue behind).

---

*Register compiled from six sweep reports (workstreams, PR/issue harvest, legitimacy question set, usability trace, named-thread verification, per-ISO adjudication). Everything above is evidence-cited or explicitly UNVERIFIED; no code, config, data, keeper, or dashboard artifact was modified in producing it.*
