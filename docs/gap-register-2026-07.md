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

### Addendum — 2026-07-06 (comprehensive §3 re-verification against HEAD)

*Every open/partial §3 row was re-checked against the live tree (five parallel
code/artifact sweeps), not against doc prose. The §3 tables below now carry the
verified status; this addendum is the summary.*

- **Current keeper set (verified `keepers.json`):** ERCOT `ercot34-stage4-overlay-off`,
  CAISO `caiso-58-v2-regate`, PJM `pjm-83-srmc-reground`, NYISO `nyiso-53-li-tsl`,
  NEISO `neiso-50-head-repro`, MISO `miso-44-wefor-neutral`. `calibration-complete.json`
  = `{}` — no ISO declared; 2022/H1-2026 holdouts fully quarantined (no sidecar carries
  a 2022/2026 solve year). The §1 snapshot keeper list is the 2026-07-05 audit baseline
  and is intentionally left as-is.
- **Newly CLOSED since the register was last counted (17):** G-02, G-06, G-08, G-17,
  G-18, G-42, G-44, G-45, G-46, G-47, G-48, G-49, G-50, G-51, G-52, G-56 — plus **G-21**
  (PJM re-grounded, keeper `pjm-83`; ST_GAS-volume driver relocated to open issue #1483).
  (G-03, G-07, G-27, G-39, G-43, G-53, G-54, G-55, G-57, G-58 were closed in the prior
  register commits and are verified still-true.)
- **CI still RED, cause moved:** **G-01 is NOT closed** — the PJM/MISO ablation-twin
  fix landed, but the 2026-07-06 swap promoted **`caiso-58` with no ablation twin**, so
  `audit_keepers.py --check` still exits 1 (E9 on CAISO). Registering a caiso-58
  zero-forcing twin is the one action that greens the gate.
- **PARTIAL (mechanism landed, gap narrowed, not adopted):** G-13 (NYISO de-staled to
  nyiso-53, reproduces; CT-offer grounding data-blocked), G-15 (CAISO scarcity-tail +
  LCR-credit code landed, default-off, drag stays), G-24 (NEISO winter Component B built,
  probe negative, default-off), G-25 (commitment-posture lever built, honesty-gate
  rejected), G-26 (4 of ~10 scalars retired), G-30 (harness flag flipped, symptom
  persists), G-34 (design only), G-36 (golden seeded).
- **G-05 narrowed:** rubric v2.1 carve-outs now clear ERCOT+PJM; only **CAISO CT** and
  **NYISO ST_GAS** remain material rule-20 breaches.
- **Still OPEN (structural / solve-heavy, unchanged):** G-01 (CI red, CAISO twin),
  G-04, G-09, G-10, G-16, G-19 (debt by design), G-20, G-22, G-23, G-25, G-28, G-29,
  G-31, G-32, G-35, G-37, G-40, G-41.
- **Verified tally (of 58 G-items): 32 CLOSED, 8 PARTIAL, 18 OPEN.** Plus 5 U-items
  (§3.8), all resolved or no-action. So of the full 63: ~37 done/no-action, 8 partial,
  18 open — the open set is now almost entirely the structural, solve-heavy, per-ISO
  calibration work plus the one CI-red twin (G-01).

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
| W8 | Emissions mass cap (`handoffs/emissions-mass-cap-plan-2026-07.md`) | Implemented default-off; forecast path wired (runner.py:1199–1218) | **Unreachable from backcast harness** (zero refs in `run_calibration*.py` — verified grep); RGGI dual-vs-auction probe unrunnable; NOx cap + banking/borrowing follow-ons |
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
| G-01 | **REFRAMED — original cause fixed, CI still red on a NEW keeper (re-verified 2026-07-06)**: PJM (`pjm-83`) and MISO (`miso-44`) now carry registered ablation twins and PASS. BUT the 2026-07-06 keeper swaps promoted **`caiso-58-v2-regate` with NO ablation twin** → live `audit_keepers.py --check` still exits 1 (E9 fail on CAISO). The rule-21 gap moved ISOs; register+run a caiso-58 zero-forcing ablation twin to green CI. | Live `audit_keepers.py --check` exit 1 (E9 CAISO); frontend/data/backcast/registry (no caiso-58 twin) | B | blocks-claim (blocks every PR gate) | M (1 solve + register) |
| G-02 | ~~MISO keeper bundle unattested — no `calibration_attestation.json`.~~ **CLOSED (re-verified 2026-07-06)**: current MISO keeper `miso-44-wefor-neutral` bundle carries `calibration_attestation.json` (`results/calibration/MISO/miso_44_wefor_neutral/`, ~11 KB). | results/calibration/MISO/miso_44_wefor_neutral/calibration_attestation.json (verified) | B | ~~blocks-claim~~ closed | done |
| G-03 | ~~E9 grandfather list stale — still names superseded `miso-39-reserve-pergen`.~~ **CLOSED (2026-07-06)**: entry removed from the `E9_ABLATION_TWIN_GRANDFATHER` frozenset (commented tombstone remains at audit_keepers.py:132). | audit_keepers.py (verified at HEAD) | B | ~~debt~~ closed | done |
| G-04 | E7 staleness unadjudicated (standing WARN, non-fatal — re-verified 2026-07-06): newer registry runs exist for the current keepers (ERCOT `ercot37-g22-surface-on`, CAISO `caiso51-statmode-v2`, NYISO `nyiso-54-downstate-daily`, NEISO `neiso-wfuelsec-ab-v2off`). Warnings only; do not fail the gate. Swap-or-keep is a per-keeper judgment. | `audit_keepers.py --check` E7 WARNs (verified 2026-07-06) | B | debt | S (judgment) |
| G-05 | **NARROWED to 2 ISOs (re-verified 2026-07-06)**: rubric v2.1 (peaker cap 15%, <2%-load immateriality carve-out) now clears **ERCOT** (CT 12.7/1.1/1.2%, immaterial) and **PJM** (CT 9.2/14.5/10.2% under the 15% cap) — both D-2 PASS. Still materially breached: **CAISO** CT_PEAKER 59.7/65.9/65.4% (ct_netload_drag) and **NYISO** ST_GAS 60.8/69.8/59.7% (reliability_floor) — both D-2 FAIL, material. Structural, per-ISO. | current keeper `legitimacy_diagnostics.md` D-2 rows (caiso58 FAIL, nyiso53 FAIL; ercot/pjm PASS) | B | blocks-claim | SH (CAISO+NYISO) |
| G-06 | ~~CI's keeper-wide legitimacy run covers only D-9/D-6 — no CI step recomputes D-2 from parquets.~~ **CLOSED (2026-07-06)**: `legitimacy_diagnostics.py --keepers` now recomputes D-2 forced-energy from each bundle's committed data rather than trusting the JSON at face value; wired into the `quarantine-gates` CI job (ci.yml:70/:93–96). | ci.yml:70,93–96 (verified at HEAD) | B | ~~debt~~ closed | done |
| G-07 | ~~`FORWARD_SKILL_ENV` env knob can alter neighbor prices for forecast years — off-registry channel by rule-23 letter (unreachable in scored backcasts).~~ **CLOSED (2026-07-06, PR #1558)**: env knob removed from `neighbor_price.py`; no env-var neighbor-price channel remains at HEAD. | src/market_sim/data/neighbor_price.py (verified clean at HEAD) | B | ~~debt~~ closed | done |
| G-08 | ~~Rule-16 all-years list amendment (add MISO) unexecuted; triage doc says MISO already complies — doc edit only.~~ **CLOSED (2026-07-06, docs sweep PR #1555)**: CLAUDE.md rule 16 now lists MISO in the all-years ISO list. | CLAUDE.md rule 16 (verified at HEAD) | B | ~~debt~~ closed | done |
| G-09 | D-9 quarantine report **still stale (re-verified 2026-07-06)** — references superseded keepers (caiso-51, pjm-77, neiso-48, miso-41); only ERCOT (ercot34) and NYISO (nyiso-53) still match. 4 of 6 keepers swapped since the report; not regenerated. Carries no D-8 content despite its label. | handoffs/d9-keeper-quarantine-report-2026-07-05.md vs keepers.json (verified) | B | debt | S |
| G-10 | Statmode D-7 integrity **worse (re-verified 2026-07-06)**: EVERY twin is keyed to a superseded keeper id — ERCOT (twin ercot32 vs keeper ercot34, only ERCOT carries a stale-box), PJM (pjm-76 vs pjm-83), MISO (miso-39 vs miso-44), CAISO (caiso-51 vs caiso-58), NYISO (nyiso-41 vs nyiso-53), NEISO (neiso-43 vs neiso-50). None reproduce a current keeper; PJM/MISO/rest silently old. | statistical-mode-results-2026-07.md vs keepers.json (all 6 stale, verified) | B | blocks-claim (for any D-7 skill quote) | M–SH (re-solves) |

### 3.2 Keeper integrity & reproducibility (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-11 | ~~CAISO keeper drift undiagnosed~~ **DIAGNOSED, disposition open (2026-07-06, L-10 wave-3)**: the drift is PR #1279 (the caiso-52 CT-floor scrub) — a legitimate rule-17/18/19 correction, NOT a regression; input hashes byte-identical across the run chain (code, not data). Do not revert. Disclosed on the caiso-51 sidecar. Remaining: the re-gate — the L-10 continuation solved the re-gate candidate at HEAD (`caiso-58`, keeper config + `use_plant_emission_rates_v2=True` per L-8 §9.6, caiso-55 as its v2-off twin); keeper swap is an owner decision (rule-20 tension: every drag-ON HEAD arm carries C8 59–71%). **OWNER DECISION (2026-07-06): swap to caiso-58. The C8 forced-energy budget is not a legitimate blocker when the forcing comes from structural reliability floors — the ct_netload_drag is a local-reliability commitment mechanism, and gating a keeper on its forced share runs counter to rule 1 (right market structure first). Combined with G-15 option C (local-capacity-revenue proxy) as the path to retire the drag.** **SWAP EXECUTED — CLOSED (2026-07-06)**: `2026-07-06-caiso-58-v2-regate` promoted to CAISO keeper (`keepers.json`, commit c043957), DOF ledger seeded (7e3708f); the keeper's byte-faithful HEAD replay with `use_plant_emission_rates_v2=True` also completes CAISO's G-39 re-gate. C8 59.7/65.9/65.4% disclosed on the sidecar per the owner decision. | keepers.json + registry `2026-07-06-caiso-58-v2-regate.json` (verified at HEAD) | B | ~~owner-decided~~ closed | done |
| G-12 | ~~ERCOT keeper not container-reproducible (replay CC_REGULAR 145.4 vs committed 133.2 TWh; 2024 C3a +2.3% vs +9.1%) — D-8 stability thread.~~ **CLOSED (2026-07-06, ercot34 promotion).** Attributed via the registered A/B pair `ercot35-replay-metagap-arm` (un-persisted-field replay) / `ercot36-head-config-faithful` (same keeper meta, all four un-persisted gas-geography fields restored, HEAD code): even config-faithful the keeper doesn't reproduce, and the residual is exactly two legitimate merged re-derives since the keeper's commit (coal max-CF ceiling re-derive + fleet.py curated-bin CHP relabelling) — not non-determinism. Resolved by the ercot34 promotion, which also flips C1-2024 to PASS. | FINDING-ercot-priceshape-2026-07.md §6.3 (original finding); `docs/handoffs/wave-manager-tranche-review-2026-07-06.md` (closure attribution); registry `2026-07-06-ercot35-replay-metagap-arm.json` / `2026-07-06-ercot36-head-config-faithful.json` | B | ~~blocks-claim~~ closed | done |
| G-13 | **PARTIAL — de-staled, CT grounding still data-blocked (re-verified 2026-07-06)**: NYISO keeper is now `nyiso-53-li-tsl`, which REPRODUCES at HEAD (nyiso-41 meta replayed = nyiso-52 base + Zone-K LCR/TSL cap + v2 ride-along), so the stale-vs-HEAD/de-leak concern is CLOSED. Remaining open item: proper CT offer grounding awaits the LI/NYC LDC citygate/interruptible delivered-gas intake (data-blocked); the keeper uses a measured downstate-CT citygate premium stand-in. | nyiso53_litsl_v2 attestation `_open_items` (verified); #1421/#1427 | B | blocks-claim (CT grounding) | SH + external data |
| G-14 | ~~caiso-51 bundle internal inconsistency~~ **ADJUDICATED + CORRECTED (2026-07-06, L-10 wave-3)**: `meta.json` was the truth (the solve log proves `capacity_deliverability_limits` set the MIC seam cap 16,055/16,452/16,148 MW and `caiso_perhub_firm_base` was live); `run_config.json` had serialized dataclass defaults (keeper-era harness never threaded the two kwargs into `recorded_cfg`). Corrected in-file with a `post_hoc_corrections` record (46317a2). Residual harness gap: `caiso_perhub_firm_base` still un-threaded into `recorded_cfg` at HEAD (L-2/L-6 owners). | results/calibration/caiso51_firm_base/run_config.json (post_hoc_corrections) | B | closed (residual harness item) | done |
| G-15 | D-8 CAISO CT-drag instability — **closure A/B EXECUTED and FAILED (2026-07-06, L-10 cont.)**: the registered arm `2026-07-06-caiso-57-ramp-lcr` (drag OFF + ramp+LCR ON, full span, at HEAD) fails criterion (i) in all years (evening CT 309/146/106 MW vs drag ~690-860/~580-600/~425-445, actual 850/770/303) while (ii)/(iii) hold (D-2 CT forced 0.4/1.0/0.03%). Per the fail branch the drag STAYS, G-15 stays open, D-8 LOYO gate stays red. Failure evidence relocates the suppressor to P2 commitment economics (no LCR-dual/BCR credit in the hurdle — the follow-up build; D-8 closure doc §6). **OWNER DECISION (2026-07-06): option C — build a simpler local-capacity-revenue proxy in the retirement/commitment screen (not the full P2 rework). Combined with G-11 swap into a single CAISO keeper handoff.** **PROXY BUILT + PROBED (2026-07-06, PR #1556/#1561/#1565)**: LCR commitment-credit proxy (CAISO BCR/CPM analogue, Tariff §40.6) landed (8ef79ea) and probed as `2026-07-06-caiso-59-lcr-proxy` (proxy ON, drag OFF): CT 1.39/0.40/0.78 vs measured 3.05/3.30/1.65 TWh — structurally correct but does NOT alone replace the drag's CT-holding (drops ~0.6–1.3 TWh/yr vs caiso-58). Drag stays ON in the keeper; the residual CT gap needs a complementary mechanism (the drag carried both commitment-value AND scarcity-pricing roles — D-8 closure §6). Remaining: that complementary mechanism (the scarcity-tail overlay from the same PR set is the candidate); G-15 stays open, narrowed. | registry `2026-07-06-caiso-59-lcr-proxy.json`; docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §6 | B | open (proxy landed; complementary mechanism next) | SH (probe + keeper re-gate) |
| G-16 | **UPDATED (2026-07-06, keeper now `neiso-50-head-repro` — a reproducibility re-solve of neiso-49 on clean HEAD; a fresh zero-forcing ablation twin `2026-07-06-neiso-50-ablation` is registered and E9-passes).** ST_GAS C7 is now SKIPPED as immaterial (ST_GAS <0.1% of ISO load, rubric v2.1) but the class ledger still lists C7 2023/2024 as OPEN ROOT CAUSE (evening-vs-midday phase; 2024 flat-floor cv 0.0), 2025 PASS; C3a price level slightly WORSE than neiso-49 (−10.4/−8.6/−4.4%) from the lost non-reproducible HQ separation + the de-leak. Residual carried, immaterial-gated. Original neiso-49 detail: ST_GAS D-1 now PASSES for the first time in 2025 (profile_r 0.844, off-peak cv_ratio 2.87), via the Connecticut ST_GAS net-load reliability-commitment limb + measured CAMPD-derived offer bands. 2023/2024 still FAIL (2023: r 0.49, cv_ratio 4.606 — off-peak CV collapse fixed from 35.4 but profile mis-phased evening-vs-actual-midday; 2024: r 0.725, cv_ratio 0.0 — flat-floor-only year at $2.19 HH gas). Keeper carries C7 as its single protective-tier ledgered caveat (1/1 budget), not a clean pass. Under rubric v1 this scored NOT-YET (hard 2>1, soft 4>2); under rubric v2 (`docs/calibration-determination-rubric.md` §9, landed 2026-07-06 after this row was last touched) the same run scores **CALIBRATED-WITH-CAVEATS** — zero FAILs, C2/C3a/C3b sit in the commercial band (auto caveats, unbudgeted), C3c+C5b are the 2 ledgered caveats (2/3 budget), C7 is the 1 protective caveat (1/1 budget). | `results/calibration/neiso_stgas_netload/metrics.json` (rubric_version 2); `frontend/data/backcast/status.js` (NEISO keeper entry); `results/calibration/neiso_stgas_netload/calibration_attestation.json`; `docs/handoffs/wave-manager-tranche-review-2026-07-06.md` | B | blocks-claim (residual C7 gap) | SH |

### 3.3 Holdout quarantine (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-17 | ~~Rule-22 intake-clause breach pending adjudication.~~ **CLOSED (re-verified 2026-07-06)**: DECIDED — Option 2, 2026-07-06 (holdout-policy-memo §(e); CLAUDE.md rule 22 carries the amendment). Rule text and tree now agree. Original detail: 2022 + H1-2026 raw source data for ERCOT+PJM landed 2026-07-04 under explicit owner instruction (PRs #1298/#1300/#1304) — no solve/score occurred (D-6 PASS, all 109 sidecars ⊂ 2023–25; bench dirs clean), but the memo's Option 1 (re-quarantine) vs Option 2 (amend rule text) decision is open. Until adjudicated, rule 22's text and the tree disagree. | data/raw/campd-unit-level/TX_2022.parquet et al.; out-of-sample-results-2026-07.md §1.1; handoffs/holdout-policy-memo-2026-07.md | B | blocks-claim | S (judgment + doc) |
| G-18 | ~~No entry-point holdout gate: `run_calibration_full.py --year 2022` runs ungated.~~ **CLOSED (re-verified 2026-07-06)**: `enforce_holdout_year_gate(years, iso, holdout_authorized)` (run_calibration_full.py:4801) requires BOTH `--holdout-authorized` AND a calibration-complete marker; invoked at the entry point (:6961). | scripts/run_calibration_full.py:4801/:6961 (verified) | B | ~~blocks-claim~~ closed | done |
| G-19 | Holdout one-shot validation intake for CAISO/MISO/NYISO/NEISO deferred by design (**OWNER DECISION 2026-07-06: option B — defer to declaration time**). **Quarantine confirmed intact (re-verified 2026-07-06)**: no registry sidecar carries a 2022 or 2026 solve year; `calibration-complete.json` = `{}`. Costed here, not a live gap. | out-of-sample-results §1; all sidecar spans ⊂ 2023–25 (verified) | B | debt (by design, owner-confirmed) | M (at declaration) |

### 3.4 Structural / mechanism gaps blocking calibration-complete (goal B — per ISO)

Full adjudication in §4. Register entries for the cross-ISO structural items:

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-20 | Scarcity price formation absent in 4 keepers (C3c ≈ 0 h — re-verified 2026-07-06): PJM (`pjm-83`), MISO (`miso-44`), CAISO (`caiso-58`, gained a code overlay `caiso_scarcity_pricing` but default-OFF even in the caiso-59 probe), NYISO (`nyiso-53`, `nyiso_rcpf_enabled=False`). ERCOT remains the only ISO with live ORDC scarcity. No new landed mechanism closes C3c≈0h. | current keeper configs (scarcity overlays OFF); pjm-reserve-ordc.md; miso-scarcity-tail-diagnosis.md; #1344 | B | blocks-claim | SH each |
| G-21 | ~~PJM sub-SRMC offer artifacts.~~ **PJM CLOSED (re-verified 2026-07-06, keeper `pjm-83-srmc-reground`, PR #1566):** ST_GAS 0.48× and CT_INTERMEDIATE 0.9× re-grounded to the Manual-15 SRMC floor 1.00× — correct offer physics (rule 1), promoted on structure even though it adds a C2 sysvol FAIL (2025 coal +6.2%; 2024 CC over-run). The relocated volume residual is the unmodeled ST_GAS RMR/local-deliverability driver → **new issue #1483** (open); #1484 (C8 denominator) mooted (D-2 passes at the 0.15 budget both ways). Issue #1302 (generalize to NYISO/MISO/NEISO/CAISO committed bands) still open for the other ISOs. | FINDING-pjm-burndown-2026-07.md §2; calibration-log 2026-07-06 L-13; issues #1302/#1483 | B | blocks-claim | SH |
| G-22 | ERCOT price-shape structural miss (still open — re-verified 2026-07-06): peak band collapsed to class p50; ~3.2 GW online-capability wedge (P1 perfect commitment). The `ercot37-g22-surface` CT offer-surface A/B probe (PRs #1524/#1525/#1529) was **run and REJECTED**; keeper stays `ercot34`. Only ERCOT change since is HSL measured-data intake, not an offer/commitment build. | FINDING-ercot-priceshape §5–6; ercot37_g22surface_{on,off} bundles (rejected) | B | blocks-claim | SH |
| G-23 | MISO C1 canonical miss (still open — re-verified 2026-07-06, keeper now `miso-44-wefor-neutral`): C1 fuelmix FAIL + C2 sysvol FAIL (metrics NOT-YET); CC_REGULAR grid-delivered miss +20.03/+19.05 TWh (2023/24) per attestation; ST_GAS −8.53/−11.01. No merit-order fix — large CC over-run persists. | miso-44 metrics.json + attestation (verified) | B | blocks-claim | SH |
| G-24 | **PARTIAL — Component B now BUILT, not adopted (re-verified 2026-07-06)**: `apply_winter_fuelsec_mustrun` (winter_fuel_inventory.py:331) + `neiso_winter_fuelsec_mustrun`/`min_stable_pct`/`tmin_c` fields (scenarios.py:1039–1073) landed with a `MECH_WINTER_FUELSEC` D-2 tag; the A+B probe (commit 64fbf87) was NEGATIVE, so the flag stays default-off and keeper stays `neiso-50` (Component A inert). Mechanism exists; the winter residual is still open. | data/winter_fuel_inventory.py:331; scenarios.py:1039–1073; A+B probe negative (verified) | B | blocks-claim | SH (adoption / complementary) |
| G-25 | P1 commitment fidelity: MIP crossbench shows P1 (no min-load) carries +34% committed CC energy vs MIP (DP-1); remediation unscoped. Interacts with G-22's commitment-thinness wedge. **Remediation attempt (2026-07-06):** the design-note pooled linear commitment-posture lever (MISO `miso-43-commitment-posture`, zero fitted params) was built and probed against the measured MISO ASM series — **honesty-gate REJECTED** (postured online headroom 3.7–4.2× too loose vs measured cleared reserve; C1 CC row unchanged +0.8/+0.5/+0.3 TWh). Lever stays default-off; the +34% commitment-fidelity gap remains open and unscoped beyond this rejected attempt. | handoffs/mip-uc-crossbench-*-2026-07-04.md; registry `2026-07-06-miso-43-commitment-posture.json` | B | blocks-claim (long-run) | L–SH |
| G-26 | **PARTIAL — 4 sub-items resolved (re-verified 2026-07-06)**: CLOSED — `GAS_AVAILABILITY_FACTOR` dead code removed (#1349, zero refs in src); WECC 7500 replaced in-keeper by published MIC (`caiso-58` capacity_deliverability_limits=True; 7500 survives only as flag-off fallback, #1373); NYISO LI 0.45 replaced in-keeper by published Zone-K LCR/TSL (`nyiso-53` nyiso_li_lcr_tsl=True; 0.45 flag-off fallback only, #1345); wefor 0.7/0.015 neutralized to 1.0 (#1348, miso-44). STILL LIVE — merchant CHP 35.0 (#1335, no independent source), coal sigmoids (#1347), COAL_TRANCHES/offer steps (#1336), seam tranches (#1350), PGE-TAC split (#1372), CC peaking pct (C-12). | constants.py:171 (CHP 35.0 live); interchange_config.py:664 / constants.py:2682 (fallbacks); scenarios.py:2204 (wefor 1.0) | B | debt→blocks-claim per item | S–SH per open item |
| G-27 | ~~Braunig confirmed-exit double-count: registry rows coexist with `BIN_FORCED_DERATE_BY_YEAR["SC_STGAS3"]={2025:0.686}` hardcode.~~ **CLOSED (2026-07-06)**: the `SC_STGAS3` hardcode is removed from `fleet.py` at HEAD; the confirmed-retirements registry is the single Braunig exit channel. | fleet.py (verified: no `SC_STGAS3` refs at HEAD) | B | ~~debt~~ closed | done |
| G-28 | CAMPD plant_code identity loss: plant-binned units lose `plant_code` on post-base-year re-aggregation, so confirmed exits effective ≥2 yrs into a CAMPD forecast go unmatched (`keep_plant_codes` attempt reverted). Caps the just-flipped confirmed-exit channel's reach. | capacity.py:2346–2354 | B | blocks-claim (forecast) | L |
| G-29 | Mass-cap unreachable from the backcast harness: `run_calibration*.py` never thread `get_active_policy_constraints` — D-5 forecast/backcast parity gap; RGGI dual-vs-auction validation probe unrunnable. | grep verified zero refs; emissions-mass-cap-plan :93–108; runner.py:1199–1218 | B | blocks-claim (for any RGGI-validity claim) | M |

### 3.5 Forecast-side validation gaps (goal B)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-30 | **PARTIAL — flag flipped, symptom persists (re-verified 2026-07-06)**: the harness now sets `scarcity_pricing_enabled=True` (run_capacity_hindcast.py:134), but the realized hindcast still shows solar entry 0.0 GW / −100% FAIL — the docstring says adoption "awaits the G-31 grain fix". So the named cause is fixed; the downstream 0-GW symptom is now coupled to G-31. | run_capacity_hindcast.py:134; ercot-2021-2025-realized report:29 (verified) | B | blocks-claim | SH (blocked on G-31) |
| G-31 | Hindcast retirement recall now 94% false-retire (over-corrected from 0-recall; lumpy zone re-aggregation grain) — diagnosed only. | ercot-2021-2025-realized-s2 report | B | blocks-claim | SH |
| G-32 | FOM flip + foresight promotion both undone: ATB FOM defaults still 12/8/40 (scenarios.py:248–256); flip refused twice for a real reason (adequacy-backstop flood masks it); foresight A/B never run on reconciled code; three recorded unblocking paths unrun. | fom-scarcity-joint-protocol-stage2 §3/§5; scenarios.py:717/:727 | B | blocks-claim | SH |
| G-33 | **RESOLVED.** CX-6a nuclear-RPS eligibility landed in full: the capacity retirement-screen RPS-shadow credit was split to `_RPS_ELIGIBLE_FUELS={wind,solar}` (a202a9f), and the dispatch RPS constraint row (`_build_rps_row`) now excludes nuclear too (this PR) so nuclear no longer counts toward the RPS target or its REC dual. The new-entry screen was already correct (`_RENEWABLE_NEW_FUELS`). `_CLEAN_FUELS`/`_FIRM_CLEAN_FUELS` retain nuclear/hydro for the clean-share and firm-clean *reporting* bases (not RPS). Nuclear support flows via `eac_price_nuclear` (ZEC/CES). Golden re-verified post-fix (see G-36). | dispatch.py `_build_rps_row`; capacity.py `_RPS_ELIGIBLE_FUELS`; tests: test_dispatch.py RPS suite + test_capacity.py::test_nuclear_not_credited_rps_shadow_in_retirement_screen | B | ~~blocks-claim (forecast)~~ RESOLVED | S–M |
| G-34 | **PARTIAL — design landed, code unbuilt (2026-07-06, PR #1509)**: the CX-4 data-center load block + electrification design memo shipped (`docs/handoffs/cx4-datacenter-load-design-2026-07.md`), but the load-block builder and its runner wiring are still unbuilt (no datacenter symbols in `src/` at HEAD). Design half done; implementation + PB-axis consumption (G-35) remain open. | docs/handoffs/cx4-datacenter-load-design-2026-07.md; grep src/ (empty at HEAD) | B | blocks-claim (forecast credibility) | L (impl remaining) |
| G-35 | PB-5 production ERCOT probability band never run — the entire PB-0..4 machinery has only a synthetic fixture behind the public fan-chart page. | frontend/data/forecast/synthetic-fixture-ercot-v1.js; results/ensemble/ | B | blocks-claim | SH |
| G-36 | Golden-scenario band regression **now seeded** (`tests/golden/ercot_2026_2032.json`, #1438) and **re-verified** post-fix: regenerated with a real 7-year re-solve at HEAD after the confirmed-exit double-derate fix (#1446) and CX-6a (G-33), both causal citations recorded in the fixture provenance. Verified #1446 is a no-op for the legacy-bin golden (no `data/clean` tree in the golden solve env → 0 confirmed exits; ERCOT registry is Braunig 2025-effective gas_st unit-grain, the drop path #1446 left unaffected). **Still open:** NEISO default forecast infeasible (F0); `forecast-invariants.yml` heavy tier never fired on Actions. | forecast-validation-program :532–533; #1419; #1438; #1446 | B | blocks-claim | M–SH |
| G-37 | Storage-AS duration gate validates at 0.54–0.61× — below its own 0.8–1.3× acceptance band; shipped anyway (default-gated). | ercot-storage-as-duration-gate-2026-07.md | B | debt | SH |
| G-38 | ~~ERCOT AS co-opt Stage 4 (overlay-off endogenous integration, gates G-1..G-7, keeper decision) not run~~ **DONE (2026-07-06).** Stage 4 run (`2026-07-06-ercot34-stage4-overlay-off`: DAM-AS overlay retired + WS-A forward RTOLCAP/RTOFFCAP formula supply) completed and **promoted to keeper**, replacing the RTOLCAP-overlay keeper; G-3/G-5/G-6 PASS, G-1/G-2/G-4 disclosed misses per the run's own attestation. Stage 3 HSL intake remains credential-blocked (owner action, W22); "ercot40" label collision is now moot (superseded by the ercot34/35/36 run set). | ercot-as-coopt-plan §7; registry `2026-07-06-ercot34-stage4-overlay-off.json`; `frontend/data/backcast/keepers.json` (ERCOT); `docs/handoffs/wave-manager-tranche-review-2026-07-06.md` | B | ~~blocks-claim (overlay-replacement goal)~~ done | done |
| G-39 | ~~`use_plant_emission_rates_v2` never flipped though its stated precondition (7-yr CAMPD history) landed.~~ **OWNER DECISION (2026-07-06): option B — flip to True, re-gate incrementally.** **FLIP EXECUTED (2026-07-06)**: `use_plant_emission_rates_v2: bool = True` at scenarios.py:391 with the owner-decision rationale in the adjacent comment. Remaining: the incremental per-ISO re-gates piggyback on each ISO's next keeper cycle (CAISO's `caiso-58` already carries v2=True). | scenarios.py:391 (verified at HEAD); W9/W10 docs | B | flip done; re-gates piggyback | piggyback re-gates only |
| G-40 | MISO memory ceiling (~15 GB/year LP) blocks regression-golden capture AND ensembles for MISO; unsolved infra constraint. | orchestrator plan (MISO golden OOM note) | B | debt | L |
| G-41 | PJM hindcast invariant I7 still FAILs (~1–4 k MW "floor doesn't force-build"); out of scope in #1426, not since cleared. | #1426 PR text; hindcast harness | B | debt | M |
| G-42 | ~~Scope2 CAISO Mode A degenerate frontier (no-cost-tiebreak) — flagged, needs LP-design fix.~~ **CLOSED (2026-07-06, ADR 0019)**: a deterministic per-MW build-size tiebreak (`config.build_tiebreak_epsilon`) breaks the degenerate saturation without moving the true optimum (mirrors the storage-ε pattern, rule #8); covered by `scope2-lce-portfolio/tests/test_mode_a_build_tiebreak.py`. | scope2-lce-portfolio/src/lce_portfolio/lp.py:594–609 + test (verified at HEAD) | B | ~~debt~~ closed | done |
| G-43 | ~~`strict_demand_profile` not threaded into runner solve paths — silent demand-corruption fallback remains possible until flipped.~~ **CLOSED (2026-07-06, PR #1557)**: `strict_demand_profile=config.strict_demand_profile` threaded at both runner.py solve paths (:475/:867) and exposed as a scenario knob. | runner.py:475/:867 (verified at HEAD) | B | ~~debt~~ closed | done |
| G-44 | ~~Pre-existing test failure on main: `test_export.py::test_year_summary_has_expected_fields`.~~ **CLOSED (2026-07-06)**: `TestExportScenarioJson::test_year_summary_has_expected_fields` passes at HEAD (verified live). | tests/test_export.py:188 (verified green at HEAD) | both | ~~debt~~ closed | done |

### 3.6 External usability (goal A)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-45 | ~~Backcast CLI `--help` crashes (unescaped `%` in argparse).~~ **CLOSED (re-verified 2026-07-06)**: `run_calibration_full.py --help` exits 0, full help renders, no ValueError. | scripts/run_calibration_full.py --help exit 0 (verified) | A | ~~blocks-release~~ closed | done |
| G-46 | ~~No runnable documented forecast — no base scenario YAML exists.~~ **CLOSED (re-verified 2026-07-06)**: `configs/scenarios/ercot_base.yaml` exists (valid `mode: forecast, iso: ERCOT, start_year: 2026, end_year: 2050`); `scenario_matrix.yaml` + `uncertainty_ercot.yaml` also present. | configs/scenarios/ercot_base.yaml (verified) | A | ~~blocks-release~~ closed | done |
| G-47 | ~~README test command fails at collection; no `testpaths` in pyproject.~~ **CLOSED (re-verified 2026-07-06)**: `pyproject.toml:39` sets `testpaths = ["tests"]`, so root `pytest` no longer collects the scope2 subpackage. | pyproject.toml:39 (verified) | A | ~~blocks-release~~ closed | done |
| G-48 | ~~No data licensing/redistribution statement.~~ **CLOSED (re-verified 2026-07-06)**: `docs/data-licensing.md` (~2,257 words) surveys the source terms. | docs/data-licensing.md (verified) | A | ~~blocks-release~~ closed | done |
| G-49 | ~~Dashboard numbers not independently verifiable (recipe only in agent skill files).~~ **CLOSED (re-verified 2026-07-06)**: `docs/verifying-dashboard-numbers.md` (~1,270 words) documents the run→bundle→registry→dashboard chain as user docs. | docs/verifying-dashboard-numbers.md (verified) | A | ~~blocks-release~~ closed | done |
| G-50 | ~~Raw-data provenance dir-level tribal (9/12 subdirs no README).~~ **CLOSED (re-verified 2026-07-06)**: 40/40 `data/raw/` subdirs now carry a README. | data/raw/*/README.md 40/40 (verified) | A | ~~debt~~ closed | done |
| G-51 | ~~Two divergent install paths, no canonical statement.~~ **CLOSED (re-verified 2026-07-06)**: README names `uv` + `pyproject.toml`/`uv.lock` as canonical; `run-simulator.sh`/`.bat` labeled "convenience launcher only". | README.md install section (verified) | A | ~~debt~~ closed | done |
| G-52 | ~~README quickstart single-year run with no rule-16 note.~~ **CLOSED (re-verified 2026-07-06)**: README:50–54 states single-year runs are smoke tests only and cites rule 16 (keepers require `--year 2023 2024 2025`). | README.md:50–54 (verified) | A | ~~debt~~ closed | done |

### 3.7 Docs-vs-code drift (goal A / hygiene)

| ID | Gap | Evidence | Goal | Severity | Effort |
|---|---|---|---|---|---|
| G-53 | ~~Capacity-evolution step-numbering conflict: CLAUDE.md "step 0→1→2" vs spec :657 "step 1b/2/3" for the same mechanisms.~~ **CLOSED (2026-07-06, docs sweep)**: CLAUDE.md capacity-evolution block now states "Same step numbering as `model-methodology-spec.md` §5.1". | CLAUDE.md:161 (verified at HEAD) | A | ~~debt~~ closed | done |
| G-54 | ~~CLAUDE.md architecture block under-describes the tree.~~ **CLOSED (2026-07-06, docs sweep PR #1555)**: architecture block now lists `pipeline/`, `ensemble.py`, `matrix.py`, `uncertainty.py`, `structural_prior.py`, `model/ancillary.py`, `policy/cap_and_trade.py`, `results/{rcpf,scarcity,evolution_ledger}.py`, and the expanded config/data module inventory. | CLAUDE.md architecture block (verified at HEAD) | A | ~~debt~~ closed | done |
| G-55 | ~~`paths.py` docstring claims CLEAN_DIR is "future… nothing reads them yet".~~ **CLOSED (re-verified 2026-07-06)**: docstring now describes CLEAN_DIR as "curated, schema-validated Parquet — the write_clean/read_clean seam"; the stale claim is gone. | src/market_sim/config/paths.py (verified) | A | ~~debt~~ closed | done |
| G-56 | ~~Plan-doc status sections lag the tree in both directions.~~ **CLOSED (re-verified 2026-07-06, docs sweep PR #1555)**: PB header now "PB-0..PB-4 landed; PB-5 not"; forecast-validation §0 marks CI/invariant-checker/e2e "Landed" with dated annotations; holdout memo carries the Option-2 decision. | probability-bounds-plan / forecast-validation-program headers (verified synced) | both | ~~debt~~ closed | done |
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
| **L-9 PB-5 production band** | G-35, G-36 (golden seeding + heavy-tier trigger) | Owns `configs/uncertainty_ercot.yaml`, `results/ensemble/**`, `frontend/data/forecast/**`, `tests/golden/**`. Depends on L-7's CX-6a for credibility but runnable before CX-4 (document the missing datacenter axis honestly). | Opus, SH |

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
