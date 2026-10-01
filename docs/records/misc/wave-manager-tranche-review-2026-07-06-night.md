# Wave-manager tranche review — merged PRs #1503–#1532 (2026-07-06 NIGHT)

**Reviewer:** wave-manager session (adversarial, artifact-based). Five parallel verification
sweeps over the tranche, cross-checked against source on `origin/main` @ `890b37f`, plus live
re-runs on that tree:

- `pytest tests/ -x --timeout=120 -q` → **exit 0** (green)
- `legitimacy_diagnostics.py --keepers` → **exit 0, PASS** (D-2 recompute now `pass`/`skip
  (immaterial)` on all keepers)
- `audit_keepers.py --check` → **PASS, 0 failures, 6 E7 stale-keeper warnings** (benign — the
  registry carries newer *probe* runs than the keepers by design)

**Bottom line up front:** CI is **green** on main (the FIX cluster fixed the two red causes the
prior review flagged). **No keeper flipped** — `keepers.json` at HEAD is byte-for-byte the wave-3
snapshot (ercot34 / caiso-51 / pjm-77 / nyiso-53 / neiso-49 / miso-41). All three probe rejections
(ercot37, pjm-82, caiso-59) correctly left their keepers untouched. Four DEFICIENT findings, none
CI-blocking; the load-bearing one is **NEISO keeper-reproducibility drift from #1515** (a
default-ON change to the keeper's own operative floor). No `src/` changes modified this review.

---

## Part 1 — Verdicts

| PR | Claim | Verdict | Key evidence |
|---|---|---|---|
| #1503 | Prior wave-manager addendum (#1501 CLEAN) | **RECORDED** | Tranche boundary; already the prior manager's own doc. |
| #1504 | Re-score 6 keepers under rubric v2 + benchmark table | **RECORDED (goalpost caveat)** | Memo real, all 6 ISOs in §5. Assertion-only rescore, no solves. **NEISO NOT-YET→CALIBRATED-WITH-CAVEATS is manufactured here** by reclassifying a *hard C7 FAIL* as a "ledgered protective" caveat + commercial-band anchor. Memo also asserts NYISO CALIBRATED, but deployed `status.js` hard-gates NYISO **NOT-YET** (C8 FAIL) — memo overstates vs shipped artifact. |
| #1505 | Fast-tier: hydro climatology 15.59→15.87, register `ramp-capability` datatype | **CLEAN** | `tests/test_hydro.py:711`, `tests/test_clean_io.py:48`, dictionary §731 all present; fast tier green. Nit: claimed demand-profile coverage row is back to all-dashes (`data-dictionary.md:49`) — cosmetic. |
| #1506 | Regenerate neiso-49 metrics.json + G-16 row + labels | **DEFICIENT (minor)** | Real deliverables: caiso-58 rounding reconcile, statmode stale-boxes, gap-register G-16/W21, DOF ledger n 8→9. **But its headline (metrics.json UNATTESTED→attested) is NOT in its diff** — the file was already attested by the rubric-v2 rescore (`8e12e34`), not this PR, and #1506's description of the file contents is wrong. No solve artifacts touched. |
| #1508 | Remove E9 grandfather `miso-39-reserve-pergen`; rename `2026-07-03-32-head-regate` | **CLEAN** | `E9_ABLATION_TWIN_GRANDFATHER` now only `caiso-51-firm-base`; id renamed to `2026-07-06-ercot32-head-regate` (registry+runs); repo-wide grep of old id = 0 hits; audit exit 0. |
| #1509 | CX-4 data-center load design memo | **CLEAN** | 1 file, +528, docs only. |
| #1510 | ERCOT G-22 CT offer-surface design note | **CLEAN** | 1 file, +193, docs only. |
| #1511 | Port `pjm_commitment_posture` lever, default-off | **CLEAN** | `scenarios.py:1958 = False`; MISO shared-code port; gated on flag + `iso=="PJM"`. |
| #1512 | Fix D-2 recompute (#1488) + 2%-of-load materiality guard | **DEFICIENT** | Machinery fix real (dominant-group attribution, `''`-bucket exclusion, bench loads). **But the guard is 2.5% (`D2_MATERIAL_MIN_LOAD_SHARE=0.025`, legitimacy_diagnostics.py:133), NOT the rubric's 2% (`PROTECTIVE_MIN_LOAD_FRAC=0.02`, calibration_verdict.py:264)** the title/body/CLAUDE.md rule 20/dashboard all cite. Two gates disagree on "material": a class at 2.0–2.5% (rubric names NEISO CT 2.1–2.3%) is C8-gated but quarantine-skipped. Denominator single-sided (`total_by_class`), not the rubric's `max(model,actual)`. Material classes still checked at tight tol. |
| #1513 | ICAP-vs-UCAP audit findings (recording) | **DEFICIENT (mislabeled)** | Not docs-only: also lands a gated forecast mechanism (`market_design_retirement_floor` in scenarios.py + capacity.py gates + harness flags + 5 tests). All default-off/byte-identical, so harmless — but it carries real forecast-path source the "recording" label hides. |
| #1514 | Owner HOLD on NYISO/NEISO calibration-complete | **CLEAN** | `calibration-complete.json` `complete: {}` unchanged. Docs-only (3 files). Both markers HELD with explicit lift conditions (see Part 3 §3). Quarantine intact. |
| #1515 | NEISO C7 root causes: CAMPD-bin commitment override + netload-basis fix | **DEFICIENT (load-bearing)** | Mechanism code lands in `src/` (good), registered artifacts untouched, `class_commitment_overrides` limb default-off (`None` config). **But the netload limb is default-ON and alters the keeper:** #1515 appended `threshold_percentile=70` to the **`enabled=True`** NEISO ST_GAS netload row (`reliability_floor_coeffs_NEISO.csv:26` — the very floor neiso-49 `stgas-netload` is named for), and `transmission.py:3091-3093` now recomputes `threshold_gw = np.percentile(daily_peak_gw, 70)` at runtime instead of the fixed 16.02 GW. So re-running neiso-49's config at HEAD produces a **different flagged-day set → different dispatch**, while #1520 asserts "no keeper change." Keeper reproducibility drift. |
| #1516 | Orchestrator Stage 6 code merge | **RECORDED (partial gate)** | Stage-6 code merged **before** the §7.3.7 re-gate finished. Fidelity PASS 3/5 (ERCOT 140/140, CAISO 122/122+2 expected drift, NEISO 142/142). **Missing: PJM (OOM SIGKILL), NYISO (env gap — empty capacity-deliverability partition, recapture running), MISO (OOM).** |
| #1517 | ERCOT `ercot_ct_offer_surface` lever, default-off | **CLEAN** | `scenarios.py:2748 = False`; surface MEASURED from 60-Day DAM disclosure, frozen (rule 20); low-regime→byte-identical off; 6 isolation tests. |
| #1518 | CAISO `_caiso_design` reserve co-opt + ramp10, default-off | **CLEAN** | `caiso_reserve_coopt = False`; `iso=="CAISO"` short-circuit unless flag on; all constants primary-cited (BAL-002-WECC-3, tariff §27/§30/§39), none residual-fitted. |
| #1519 | caiso-59 reserve-coopt PROBE — real but inert, keeper stays | **RECORDED (honest)** | Sidecar full-span `[2023,2024,2025]`, labeled PROBE, NOT-YET; keepers.json unchanged. Minor: only the reserve-ON arm bundle committed (OFF twin not on disk — acceptable for a probe). |
| #1520 | Owner scoping decision — no forced-commitment compute | **RECORDED** | 1 file, `calibration-log.md`, +22. Note: framed as a probe-skip, reframed 9 min later by #1522 as a rubric gating change. **Its "no keeper change" assertion is contradicted by #1515's live netload limb (see #1515).** |
| #1521 | Hook ERCOT offer surface into backcast solve path | **CLEAN** | `run_calibration.py:3853` wraps the call in `if getattr(config,"ercot_ct_offer_surface",False) and iso=="ERCOT"` — default/keeper path unchanged; only fires when G-22 flag on. Rule-1/24 satisfied. |
| #1522 | C7 rubric: classes <2.5% of ISO load no longer gate | **RECORDED** | Real code: `score_shape` + `D1_SHAPE_MATERIALITY_LOAD_FRAC=0.025`, 4 tests. Superseded 14 min later by #1524 (→2% `PROTECTIVE_MIN_LOAD_FRAC`, `max(model,actual)`). Used actual-only share — a gaming hole #1524 closed. |
| #1523 | (identical title to #1522) | **DEFICIENT (duplicate)** | Byte-identical content diff to #1522 (`git diff` on changed files = empty); same branch head, merged 2 min later. Pure re-push onto a newer base — no new content. |
| #1524 | Rubric v2.1: C7/C8 materiality floor "2%" + peaker cap 15% | **RECORDED (code/doc mismatch)** | Peaker cap confirmed (`D2_PEAKER_MAX_SHARE=0.15`). The **scorer** floor is 2% (`PROTECTIVE_MIN_LOAD_FRAC=0.02`) but the **quarantine gate** stayed 2.5% (see #1512). **No headline determination flipped** (before/after `status.js`: NEISO CALIBRATED both, other five NOT-YET both). Sub-criteria moved: PJM C8 FAIL→PASS (cap 10→15%, class @12.1%); NEISO C7 CAVEAT→SKIPPED. |
| #1525 | Register ercot37 G-22 A/B (REJECTED probe) | **RECORDED (honest)** | Sidecar "(PROBE — REJECTED)…Keeper stays ercot34; mechanism default-off"; run_configs record real off/on A/B. |
| #1526 | D-7 statmode probes ERCOT + CAISO (throwaway) | **CLEAN** | Both `keeper=None`, full-span, absent from keepers.json. Found statmode *worsens* fit (ERCOT +5, CAISO flat) — confirms structural > curve-fit. |
| #1527 | Stabilize D-2 gate: skip immaterial classes | **RECORDED** | `run_d2_keepers_verify` skips rows flagged immaterial either side; `test_material_class_drift_still_fails` preserves material coverage. Legit fix for cross-machine float non-determinism on a ~0.007 TWh never-gating class. Caveat: immaterial-class committed D-2 shares are no longer reproducibility-checked — quietly walks back #1512's "reproducible by construction" claim. |
| #1528 | Stage 6 gate: partial e46ab11 baseline evidence | **RECORDED (genuinely partial)** | A retroactive evidence record, not a merge gate. Confirms 3/5 fidelity PASS; PJM/NYISO/MISO captures outstanding. **The `STAGE6_GATE_RESULT` marker in the plan doc still literally reads `RESULT-PENDING`** (unfilled placeholder) — doc hygiene. |
| #1529 | Preserve ercot37 run_config/meta, gitignore disposable | **CLEAN** | `.gitignore` excludes only the probe parquet dirs; `git ls-files` shows meta.json+run_config.json force-tracked. Provenance intact. |
| #1530 | PJM posture impl + register pjm-82 REJECTED | **RECORDED (honest)** | Gated `reserve_config.py:1277`; byte-identical off; `SUMMARY-posture-gate.md` "Pre-committed decision: REJECT" (level FAIL all years, ratio ~2.7–3.1×); keeper stays pjm-77. |
| #1531 | Gitignore posture.parquet | **CLEAN** | `.gitignore:240` ignores only the regenerable parquet; bundle keeps SUMMARY/metrics/run_config/meta tracked. |
| #1532 | Storage-ELCC dilution + PJM/MISO ICAP-vs-UCAP fix; records stage 5 | **RECORDED (forecast flag)** | Confined to capacity **evolution** (forecast-only) — no backcast/keeper path. All new magic numbers cited (PJM BRA FPR/IRM, MISO LOLE Module E-1, Dec-2025 CDR). **Flag:** adopts the published FPR ratio directly (`ICAP_TO_UCAP_RATIO`) — exactly what #1513's own handoff §6 said it would NOT do (FPR embeds ~77% marginal-ELCC vs the model's ~0.92 `(1−EFORd)` supply basis → sign-flip risk). Plan-vs-code divergence on a forecast-mode requirement. Stage-5 gates **both FAIL honestly** (retirement pace 14.79 GW/yr vs 0.5–2; backstop 34,124 MW vs ≈0); stage 6 blocked on the G-31 zone-bin re-aggregation fix. |

### Focus-question answers
- **Keeper flipped without rule-21?** No keeper flipped at all. But #1515 mutated the neiso-49 keeper's *operative floor* in a default-ON path without a re-solve/re-registration — a reproducibility breach short of a swap (DEFICIENT, Part 2 FIX-A).
- **Probe rejections (ercot37/pjm-82/caiso-59) left keepers unchanged?** Yes, all three — verified against keepers.json @ HEAD and each sidecar.
- **Stage 6 complete or partial?** Landed (code merged, 3/5 ISO fidelity PASS) but the full-set gate is **partial** — PJM/MISO OOM-blocked (G-40 memory), NYISO recapture in progress. The `STAGE6_GATE_RESULT` marker is an unfilled `RESULT-PENDING` placeholder.
- **D-2 materiality guard (#1527) real fix or workaround?** Real for the machinery (dominant-group attribution + `''`-bucket exclusion), and the immaterial-skip is a legitimate float-nondeterminism guard that keeps material-class coverage. But it introduces the **2.5% vs 2% split** vs the rubric scorer (DEFICIENT, FIX-B).
- **NEISO C7 (#1515) touched the keeper bundle or just mechanism?** Registered artifacts untouched, but the default solve path (the enabled netload floor) is altered → keeper no longer reproducible (FIX-A).
- **Did rubric v2.1 invalidate any keeper verdict?** No headline determination flipped at v2.1. The verdict-manufacturing move was **v2 (#1504)** — NEISO's sole CALIBRATED-WITH-CAVEATS rests on the v2 redefinition, not a solve. The owner HOLD (#1514) correctly keeps NEISO gated regardless.

---

## Part 2 — FIX prompts

### FIX-A — NEISO keeper-reproducibility drift (#1515) — **highest value; needs a Fable solve**
Doubles as the owner's NEISO calibration-complete lift condition (C7 Component-B / ST_GAS
re-exam, #1514). Lane: `data/raw/reference/reliability_floor_coeffs_NEISO.csv`,
`src/market_sim/model/transmission.py`, `results/calibration/neiso*`, `frontend/data/backcast/*`.

```
You are the NEISO calibration owner. On main @ HEAD, PR #1515 changed the NEISO keeper's own
operative floor without re-registering it: it appended `threshold_percentile=70` to the
`enabled=True` NEISO ST_GAS `netload` row in
`data/raw/reference/reliability_floor_coeffs_NEISO.csv` (row 26 — the floor the keeper
`2026-07-06-neiso-49-stgas-netload` is named for), and `transmission.py:3091-3093` now recomputes
the GW threshold as p70 of the *model's own* daily-peak net-load at runtime instead of the fixed
16.02 GW. Re-running the neiso-49 config at HEAD therefore no longer reproduces its registered
dispatch (the PR body itself notes flagged-day count moves from ~110/yr to ~30% of days), while
#1520 asserts "no keeper change." The keeper's registered bundle is frozen but its config is no
longer faithful to it — a rule-1 reproducibility breach.

Resolve it the structurally-correct way (CLAUDE.md rules 1, 11, 16, 20):
1. Re-solve NEISO across the FULL span `--year 2023 2024 2025` in ONE bundle with the p70
   net-load basis as the operative ST_GAS floor (this is the C7 Component-B re-examination the
   owner is holding NEISO's calibration-complete marker on, #1514).
2. Register it as a NEW keeper candidate (`neiso-50-*`) with its zero-forcing ablation twin, a
   DOF ledger that declares the p70-percentile derivation source, and the rule-20 D-2 readout.
   Score C7 for 2023/24/25 and report whether the diurnal FAIL is genuinely fixed vs merely
   SKIPPED-immaterial.
3. If C7 now passes structurally, propose the keeper swap (owner decision). If it does not,
   register it honestly as a NOT-YET candidate and either (a) gate the p70 limb behind a
   default-off config field so neiso-49 stays reproducible, or (b) revert the CSV row to the
   fixed 16.02 GW basis pending a validated re-solve — do NOT leave a default-ON change under a
   frozen keeper.
Register the run on the dashboard in this session (calibration-report skill) and update the
G-16 register row. Do not touch any other ISO's files.
```

### FIX-B — Unify the materiality constant (2.5% quarantine gate vs 2% rubric scorer) — **no solve (Opus)**
Lane: `scripts/legitimacy_diagnostics.py`, `tests/test_legitimacy_diagnostics.py`.

```
On main @ HEAD the D-2 forced-energy QUARANTINE gate and the determination RUBRIC enforce
different materiality lines. `scripts/legitimacy_diagnostics.py:133` uses
`D2_MATERIAL_MIN_LOAD_SHARE = 0.025` (2.5%), while `scripts/calibration_verdict.py:264` uses
`PROTECTIVE_MIN_LOAD_FRAC = 0.02` (2%) — the value CLAUDE.md rule 20, PR #1512/#1524 bodies, and
the dashboard tol strings all cite. A merchant class at 2.0–2.5% of ISO load (the rubric names
NEISO CT at 2.1–2.3%) is therefore gated by C8/keeper scoring yet skipped by the quarantine gate:
the two gates disagree on what "material" means, and the quarantine side is 0.5pp looser than the
rubric it cites.

Fix (CLAUDE.md rules 17/20/23 — one materiality line, no off-registry constants):
1. Make the D-2 gate consume the single rubric constant `PROTECTIVE_MIN_LOAD_FRAC = 0.02` (import
   it from `calibration_verdict.py` or promote it to a shared module) and delete the duplicate
   `D2_MATERIAL_MIN_LOAD_SHARE`.
2. Switch the D-2 materiality denominator from the single-sided `total_by_class` to the rubric's
   `max(model, actual)` energy, so a binding floor cannot hide a class under the line (rule 20
   amendment, matches `score_shape`).
3. Add/extend a test asserting a class at 2.2% is treated identically by both the quarantine gate
   and the rubric scorer. Re-run `legitimacy_diagnostics.py --keepers` and confirm still exit 0.
No solves; scripts + tests only. Do not touch any keeper bundle or `src/`.
```

### FIX-C — Doc/bookkeeping hygiene (bundle) — **no solve (Opus)**
Lane: `docs/handoffs/orchestrator-unification-plan-2026-07.md`, `docs/gap-register-2026-07.md`,
`frontend/data/backcast/registry/` (miso-42/caiso-58 only if promos re-run).

```
Three small hygiene items surfaced in the #1503–#1532 review. Fix docs/registry only, no solves:
1. `docs/handoffs/orchestrator-unification-plan-2026-07.md`: the `<!-- STAGE6_GATE_RESULT -->`
   marker still literally reads `RESULT-PENDING` even though §7.3.6/7.3.7 record 3/5 ISO fidelity
   PASS (ERCOT/CAISO/NEISO) and PJM/MISO OOM-blocked + NYISO recapture-in-progress. Fill the
   marker with the honest partial state (3 PASS, PJM/MISO OOM-waived pending G-40 memory host,
   NYISO recapture running) so the doc stops asserting "pending" for work that is recorded.
2. Record in the gap register that PR #1523 was a byte-identical duplicate re-push of #1522
   (no content) and that #1506's headline metrics.json claim was fixed by the rubric-v2 rescore
   `8e12e34`, not by #1506 — so the audit trail is accurate.
3. Note the #1532 forecast-mode flag (ICAP/UCAP adopts the published FPR ratio that #1513's own
   handoff §6 said NOT to adopt — sign-flip risk against the model's (1−EFORd) supply basis) as
   an open forecast-side item for owner review before any forecast promotion.
```

---

## Part 3 — Next-wave prompts & unblock assessment

### 1. PROMO-MISO (miso-41 → miso-42) — **ready, no solve; OWNER DECISION**
Verified: `miso-42-coal-econ` + its ablation twin `miso-42-coal-econ-ablation` are fully
registered (registry sidecars + `runs/*.js` payloads present). The swap is pure bookkeeping. It
did NOT land last wave because the keeper-swap step (keepers.json + status regen) was never
executed — a **governance/owner decision**, not a failed solve. Lane: `frontend/data/backcast/`.

```
No-solve keeper promotion. On main @ HEAD, promote MISO keeper miso-41 → miso-42-coal-econ (its
bundle, ablation twin, and dashboard payload are already registered from the L-14 continuation).
Steps: (1) set `frontend/data/backcast/keepers.json` MISO → `2026-07-06-miso-42-coal-econ`;
(2) run `scripts/build_status.py` to refresh status.js; (3) run the calibration-keeper-auditor
agent to confirm the Calibration Status page and per-run headers match the miso-42 bundle;
(4) update the calibration log + G-25 register row. Verify `audit_keepers.py --check` and
`legitimacy_diagnostics.py --keepers` both stay exit 0. Owner sign-off required before merge
(keeper-swap governance is unresolved — MISO/ERCOT lanes deferred self-promotion last wave; NEISO
self-promoted). Lane: frontend/data/backcast/* + docs only.
```

### 2. PROMO-CAISO (caiso-51 → caiso-58) — **BLOCKED: needs the ablation twin (Fable solve)**
Verified: `caiso-58-v2-regate` has a registry sidecar + `runs/*.js` + a solve bundle
(`results/calibration/caiso58_v2_regate/`), **but no ablation twin is registered** (grep for a
caiso-58 ablation in registry/runs = 0 hits). Rule-24 requires a zero-forcing twin alongside any
keeper. That twin is the missing solve — this is why PROMO-CAISO stalled. Lane:
`results/calibration/caiso58*`, `frontend/data/backcast/*`.

```
CAISO keeper promotion, needs one solve. caiso-58-v2-regate is registered as a candidate but has
NO zero-forcing ablation twin — rule 24 blocks promotion without it. (1) Re-solve the caiso-58
recipe's ablation twin (`ScenarioConfig.as_zero_forcing_ablation`, structural protected set kept)
across `--year 2023 2024 2025` in one bundle on HEAD; (2) register it alongside caiso-58 (E9
keeper-vs-twin delta) via calibration-report; (3) confirm caiso-58's DOF ledger + attestation are
complete and the v2 re-gate rationale is structural (rule 1), not lower-MAE; (4) THEN propose the
keeper swap keepers.json CAISO → caiso-58 + build_status + keeper-auditor (owner decision).
Do not promote before the twin is on disk and registered. Lane: caiso bundles + frontend/backcast.
```

### 3. NYISO/NEISO calibration-complete — **HOLD STANDS; do NOT produce a lift memo**
The owner (#1514) already adjudicated with **explicit, still-unmet lift conditions**:
- **NYISO: held until PR #1344 lands** (reserve-scarcity data ask). The C8 CT forced-share caveat
  dominates (92.7% / 86.7% / 56.6% forced-at-floor across 2023/24/25). Also note the deployed
  `status.js` hard-gates NYISO **NOT-YET** (C8 FAIL) — the #1504 memo's "CALIBRATED" assertion is
  an overstatement; NYISO is not marker-ready on the shipped artifact regardless.
- **NEISO: held until the winter-fuel Component-B / C7 ST_GAS residual is re-examined** — which is
  exactly **FIX-A**. The C7 re-grounding mechanism exists (#1515) but was never solved/validated
  and currently drifts the keeper. FIX-A *is* the NEISO lift path.

No memo to lift is warranted this wave. The unblock is FIX-A (NEISO) and #1344 landing (NYISO,
credential/owner-blocked, owner-queue #8). Recommend the owner-queue item read: "NYISO/NEISO
holdout markers remain HELD per #1514; NEISO lifts on a successful FIX-A re-solve, NYISO on #1344."

### 4. Remaining statmode ISOs (D-7) — **UNBLOCKED (Opus/diagnostic)**
#1526 covered ERCOT + CAISO (both found statmode *worsens* fit — good structural evidence).
PJM / NYISO / NEISO / MISO still need D-7 statmode probes under rubric v2.1. All throwaway
diagnostics, keepers untouched, full-span. Lane: `results/calibration/*statmode*`,
`frontend/data/backcast/registry/*statmode*`.

```
D-7 statmode diagnostic probes for PJM, NYISO, NEISO, MISO (ERCOT/CAISO done in #1526). For each
ISO, solve the current keeper config with statmode ON as a throwaway full-span [2023,2024,2025]
probe (keeper=None, absent from keepers.json), score it under rubric v2.1, and register it as a
diagnostic. Report whether statmode moves the fit (expected: worsens or flat, confirming
structural > curve-fit per the ERCOT/CAISO result). Do NOT flip any keeper. These are independent
per-ISO invocations — run them as concurrent background jobs (cap ~2 per-plant LPs at once for
memory). Lane: per-ISO statmode bundles + registry sidecars only.
```

### 5. Orchestrator Stage 6 completion + Stage 7 — **PARTIALLY BLOCKED (G-40 memory)**
Stage 6 landed (code + 3/5 fidelity). Outstanding: PJM + MISO captures are **OOM-blocked** (G-40,
needs the ≥24 GB solve host — owner-queue #9); NYISO recapture is in progress after the
capacity-deliverability env-gap fix. Stage 7 (not started, gated on Stage 6) folds the
`getattr(config,…)` fallbacks into explicit fields under a byte-identity gate and **removes the
`caiso_ra_min_load_frac` getattr `0.40` fallback — a rule-26 re-armable answer key.** Dispatch
Stage-6-finish only once the memory host is funded; Stage 7 can be *designed* now.

```
Orchestrator unification Stage 6 finish + Stage 7 design. Stage 6: complete the builder-swap
fidelity gate for the 3 outstanding ISOs — NYISO (recapture after the capacity-deliverability
partition fix), and PJM + MISO (OOM-blocked; requires the ≥24 GB host, G-40 — confirm host before
starting). Byte-diff vs `stage6-before-e46ab11` at atol=rtol=1e-9 across the full 5-ISO set, then
fill the `STAGE6_GATE_RESULT` marker with the real pass/fail. Stage 7 (design only until Stage 6
passes): enumerate every `getattr(config,…)` fallback literal on the solve path, plan their
extraction into explicit `backcast_config.py`/`overlays.py` fields, and specifically flag
`caiso_ra_min_load_frac`'s `0.40` getattr fallback for deletion (rule 26 — a deprecated knob that
still parses is a re-armable answer key). Lane: src/market_sim/pipeline/*, scripts/*orchestrat*,
docs/handoffs/orchestrator-unification-plan-2026-07.md.
```

### 6. Capacity economics Stage 5 → 6 — **BLOCKED on G-31**
#1532 recorded Stage 5 with **both gates FAILing honestly** (retirement pace 14.79 GW/yr vs
target 0.5–2; backstop 34,124 MW vs ≈0), diagnosed as the G-31 zone-bin re-aggregation cliff the
floor was masking. Stage 6 / forecast-side use is gated on the G-31 retirement-grain fix + owner
sign-off. This is the right next capacity lane once G-31 is scoped; the #1532 FPR-ratio flag
(FIX-C item 3) should be resolved in the same lane.

---

## Owner-decision queue (updated)

1. **MISO keeper swap** (miso-41 → miso-42): ready, no-solve; PROMO-MISO prompt above. Governance:
   may a lane self-promote, or does this need explicit owner sign-off? (NEISO self-promoted last
   wave; MISO/ERCOT deferred — governance still inconsistent.)
2. **CAISO keeper swap** (caiso-51 → caiso-58): blocked on the missing ablation twin (one Fable
   solve, PROMO-CAISO prompt above), then owner sign-off.
3. **NYISO/NEISO calibration-complete: HOLD stands** (#1514). NEISO lifts on a successful FIX-A
   re-solve; NYISO lifts on #1344 landing. No action urged this wave.
4. **#1532 forecast ICAP/UCAP FPR-ratio**: adopts the published FPR value #1513 §6 said not to —
   review before any forecast promotion.
5. Keeper-swap governance: may a lane self-promote? (unresolved, blocks #1/#2 cleanly).
6. PJM C8 drag: drag-sizing vs D-2-exemption (#1484) — carried.
7. Foresight `entry_lookahead_reprice` option (B) sign-off (#1496 memo) — carried.
8. **#1344 NYISO reserve-scarcity data ask** — gates the NYISO holdout marker; credential/owner
   action.
9. **G-40 MISO memory** — ≥24 GB solve host gates PJM/MISO Stage-6 fidelity captures + MISO
   full-span solves.
10. W22 ERCOT HSL intake: credential-blocked (owner action) — carried.
```
