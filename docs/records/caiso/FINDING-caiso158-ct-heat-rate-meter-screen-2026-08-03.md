# FINDING — caiso-158: executing the caiso-156 charter (the CT heat-rate hour-grain band screen)

**Session:** caiso-158. **Branch:** `claude/caiso-backcast-calibration-6ubjfb`.
**Charter:** `PREREG-caiso156-ct-heat-rate-meter-screen-2026-08-02.md` +
`PREREG-caiso156-ADDENDUM-rebaseline-cache-2026-08-02.md` (written this session,
before any arm solved).

**Headline.** The caiso-146 §2.4 meter defect is FIXED and the corrected
artifacts ship for all six ISOs, reproducing every pre-registered prediction
exactly. The A/B is **LIVE and score-neutral**: the screen moves real energy
(CAISO up to 602 MW in a single class-hour, 4,117 of 8,760 hours changed) and
re-prices CT_PEAKER downward in energy in every year of every solved ISO, while
flipping **zero** criteria and **zero** D-gates. Two silent-corruption defects
in the *evidence pipeline* were found and closed before they could produce
wrong-but-plausible results.

---

## 1. What shipped (rule 14 `[R-ACCURATE]`, rule 23 `[R-FROZEN-DERIVE]`)

`scripts/data/derive_campd_ct_heat_rates.py` now applies its own declared
physical band `[_HR_MIN, _HR_MAX] = [6.0, 25.0]` MMBtu/MWh **per loaded hour**,
not only to the plant aggregate, and evaluates the `_MIN_LOADED_HOURS` trust
gate on the in-band hours. **Zero new parameters.** Cap percentile, loaded
fraction, all-hours `gross_mwh` weights, parasitic conversion, the
plant-aggregate flag and the `flag == "ok"` application rule are untouched.

All six re-derived artifacts reproduce the pre-registered §2 table **exactly**
(cap-weighted applied map, net MMBtu/MWh):

| ISO | pre-fix | post-fix | Δ | predicted Δ |
|---|---|---|---|---|
| CAISO | 9.6603 | 9.8362 | **+0.1759** | +0.176 ✓ |
| NYISO | 12.0769 | 12.4355 | **+0.3586** | +0.359 ✓ |
| NEISO | 9.6291 | 9.8006 | **+0.1715** | +0.171 ✓ |
| PJM | 11.5817 | 11.6511 | **+0.0693** | +0.069 ✓ |
| MISO | 11.8677 | 11.8972 | **+0.0295** | +0.030 ✓ |
| ERCOT | 11.8796 | 11.9425 | **+0.0629** | +0.063 ✓ |

Named movers match to 4 dp: Delano (58122) 6.5725 → 9.4213 — back inside the
physical band; Darby 10.5885 → 12.6954; Gowanus 15.2804 → 16.9538; Narrows
15.7537 → 16.7814; Potter 8.8734 → 9.2711. Unit drops match exactly: NYISO 1
(2494 `CT03-6`), NEISO 1 (63559), MISO 1 (6063); CAISO / PJM / ERCOT none.

## 2. Gate results

**K1 artifact fidelity** — every arm records the md5 of the artifact it solved
against, captured at solve time. Arm A tree = pre-fix bytes (CAISO
`1806043149…`, NEISO `9f14549543…`, NYISO `749f4ffff4…`); arm B tree = post-fix
(NEISO `293c6f6c52…`). PASS.

**K2 control integrity** — each arm A reproduces its ISO's committed keeper on
**every model-determined criterion** and on **all six D-gates**
(D1/D2/D4/D5/D9/D10):

| ISO | control vs keeper | result |
|---|---|---|
| CAISO | `caiso157_restore_B` | fuelmix, sysvol, price_shape, dispatch_corr, shape (C7), forced_share (C8) all MATCH; D1–D10 all MATCH |
| NEISO | `neiso72_hy_window_B` | fuelmix, sysvol, price_mean, price_shape, dispatch_corr, forced_share MATCH; shape SKIPPED both sides (C7 scorer-skipped for NEISO, neiso-70); D1–D10 all MATCH |
| NYISO | `nyiso112_combined_D` | all model-determined criteria MATCH; D1–D10 all MATCH |

The only differences anywhere are **attestation-dependent bookkeeping**: a probe
arm carries no rule-21 DOF ledger, so `governance` scores `UNATTESTED` and the
ledgered caveats cannot be downgraded `FAIL → CAVEAT`. Not dispatch. PASS.

**K3 liveness** — the number the ADDENDUM §B cache collision would have zeroed:

| ISO | year | max abs Δ CT_PEAKER class-hour | hours changed | CT_PEAKER energy (TWh) |
|---|---|---|---|---|
| CAISO | 2023 | **601.639 MW** | 4117 / 8760 | 1.9217 → 1.6599 (**−0.2618**) |
| CAISO | 2024 | 480.866 MW | 1774 / 8760 | 0.7132 → 0.6370 (−0.0762) |
| CAISO | 2025 | 495.673 MW | 2599 / 8760 | 0.5333 → 0.4157 (−0.1176) |
| NEISO | 2023 | 118.840 MW | 705 / 8760 | 0.3088 → 0.2877 (−0.0211) |
| NEISO | 2024 | 118.873 MW | 2081 / 8760 | 0.8433 → 0.7566 (−0.0867) |
| NEISO | 2025 | 150.403 MW | 2566 / 8760 | 1.7174 → 1.6163 (−0.1011) |
| NYISO | 2023 | 469.266 MW | 398 / 8760 | 0.4240 → 0.4118 (−0.0121) |
| NYISO | 2024 | 170.659 MW | 185 / 8760 | 0.3353 → 0.3307 (−0.0045) |
| NYISO | 2025 | 237.474 MW | 789 / 8760 | 1.1046 → 1.0687 (−0.0359) |

**Nine ISO-years, nine negative CT_PEAKER deltas, zero criterion flips, zero
D-gate flips.** NYISO's A/B carries the largest artifact movement of the three
(+0.359 cap-weighted) yet the smallest dispatch response — its CT fleet is
already largely out of merit, so re-pricing it moves fewer hours (185–789)
than CAISO's (1774–4117).

**K4 config equality** — NEISO arm A vs arm B `run_config.json` differ in
exactly four keys, all provenance (`git.sha`, `calibration_flags.git_sha`,
`timestamp`, `model_changes_note`). **Zero ScenarioConfig-field diffs.** PASS.

**K5 year span** — every bundle carries exactly [2023, 2024, 2025] (rule 16).

**K6 the correction is not driven by drops** — applied-map delta recomputed with
the dropped units retained at their screened rates:

| ISO | shipped Δ | drops-retained Δ | divergence | verdict |
|---|---|---|---|---|
| NEISO | +0.1715 | +0.1319 | 23.1 % | PASS (< 25 %) |
| NYISO | +0.3586 | +0.3557 | 0.8 % | PASS |
| MISO | +0.0295 | +0.0260 | 11.7 % | PASS |
| CAISO / PJM / ERCOT | — | — | 0 drops | trivially PASS |

Sign agrees everywhere. The screen is meter hygiene, not selection.

## 3. Pre-registered directions — every one confirmed

1. **CT_PEAKER energy FALLS in all solved ISOs** (§5.1) — CONFIRMED, all six
   ISO-years above are negative. **One magnitude exceedance reported honestly:**
   the prereg predicted CAISO −0.00 to −0.15 TWh/yr; **2023 came in at −0.2618
   TWh**, ~1.7× the top of the predicted band (2024 and 2025 land inside it).
   Direction right, 2023 magnitude under-predicted.
2. **λ / C3a nudges UP** (§5.3) — CONFIRMED, and well inside tolerance.
   Load-weighted mean LMP, arm A → arm B:
   CAISO +0.195 % / +0.099 % / +0.111 % of level (2023/24/25);
   NEISO +0.045 % / +0.055 % / +0.083 %;
   NYISO +0.028 % / +0.020 % / +0.080 %.
   The prereg pre-committed that an adverse C3a move ≥ 1.0 pp would trigger the
   ledger discipline and a LOYO check. **The largest move is +0.20 pp**, so the
   trigger is not reached and no LOYO escalation is owed. CAISO's ledgered
   C3a-2025 caveat moves adversely by **+0.11 pp** — real, disclosed, immaterial
   against the 1.0 pp bar, and *not* a reason to revert an accurate input
   (rule 14).
3. **C3c tail counts essentially unchanged** (§5.4) — confirmed: `price_tail`
   does not flip in any arm.
4. **C7/C8 stable** (§5.5) — confirmed: `shape` and `forced_share` do not flip;
   no C8 breach of the 0.15 peaker cap in any arm.

## 4. Two evidence-pipeline defects found and closed (both silent)

These are the session's most transferable findings. Each would have produced a
wrong-but-plausible result that looked exactly like a legitimate verdict.

**(a) The arm-B cache-key collision — would have voided the whole experiment.**
`ScenarioConfig.cache_key()` hashes `asdict(self)`, config fields only; the CT
heat-rate artifact is a CSV read at fleet-build time and its bytes never enter
the hash. No `note` / `out_dir` / `git_sha` / `timestamp` field exists on
`ScenarioConfig` to differentiate the arms either. Since the prereg
*deliberately* makes both arms value-identical (K4 gates it), both hash to
`b8ba9f5ddbabf057`. `runner.py:1369` short-circuits on that key against the
**global** `results/<ISO>/<cache_key>/` tree (`runner.py:2149` populates it;
`.gitignore:229-233` documents it), and neither `run_calibration_full.py` nor
`replay_keeper.py` redirects `CACHE_ROOT`. Arm B would have loaded arm A's
dispatch and never re-solved — **K3 would have read 0.000 in every ISO**, and
"score-inert everywhere" would have been reported as a finding. Closed by the
ADDENDUM §B cold-solve protocol: `results/<ISO>/` is scrubbed before every arm
and each solve log checked. Every solve this session logged `(cold)`.

**(b) `legitimacy_diagnostics.json` must be generated AFTER dashboard
registration, and `metrics.json` re-scored after that.** The D-2 rule-20
materiality guard reads `total_load_mwh` from the run's dashboard payload via
`find_registry_sidecar`. With no sidecar it is `None`, which **disables the
guard** (the function's own docstring: "leaves the guard disabled") and gates
every class. That manufactured a D-2 **FAIL** on NEISO's 0.068 TWh coal class —
`load_share` 0.0022, i.e. 0.22 % of load — whose forced share was *byte-identical*
to the committed keeper's 0.3252. Read naively it looks like a K2 stop-the-lane
control flip; it is an absent denominator. Separately, `dashboard_add_run`
writes `metrics.json` before the diagnostics exist, so C7 `shape` and C8
`forced_share` scored `SKIPPED`; `calibration_verdict.py --write-metrics`
re-scores both to PASS.

**The correct per-arm order is: solve → register → diagnostics → re-score.**
Any session that generates diagnostics straight after the solve is reading a
disabled D-2 guard and unscored C7/C8.

## 5. Scope cut, declared

**PJM has no A/B this session.** Its arm A was not launched. Reasons, on the
record: PJM is the largest LP in the set (handoff records ~15.5 GB peak RSS
against a 15 GB box with no swap, no swap available), and it carries the
**smallest** predicted effect of the four — +0.069 cap-weighted, which the
prereg itself flags as possibly "score-inert" (§5.1, K3). Spending two long
solves at real OOM risk on the lane least likely to move would have cost the
lanes that do. **PJM's corrected artifact ships regardless** (rule 14, §7); only
its A/B evidence is deferred. A successor session on a larger box should run
the pair, or use the `--years` + `--reuse-solved` per-year invocation chain
(`replay_keeper.py`'s documented OOM mitigation) to fit it in one bundle.

MISO and ERCOT re-derive only, exactly as chartered — neither keeper arms the
artifact (re-verified from `meta.json` this session).

## 6. Retention note

Registering six arms across three ISOs pushed six older runs off the
top-15-per-ISO retention sweep, including **`2026-07-23-neiso-2022-holdout-validation`**
— a rule-22 VALIDATION artifact. It remains recoverable from git history, and
it is flagged here because automatic retention should not silently consume
holdout evidence. `dashboard_add_run.py --no-prune` exists and is the right
flag when a session registers several arms at once.

## 7. DO-NOT-REDO

* **Do not re-open whether the band should be applied per hour.** It is the
  module's own declared meter guard; applying it only to the aggregate was the
  defect. Measured, pre-registered, and reproduced to 4 dp in six ISOs.
* **Do not re-test the screen as a mechanism.** It is an INPUT CORRECTION with
  zero `ScenarioConfig` surface; no matrix cell changes verdict on it. The
  `measured_ct_heat_rates` cells keep their existing per-ISO verdicts; only the
  row's note/evidence is updated (rule 28b).
* **Do not read "zero criterion flips" as "inert".** K3 shows the screen moves
  real energy in thousands of hours; it re-prices the class without moving the
  scorecard. Those are different claims.
* **Do not generate `legitimacy_diagnostics.json` before registering the run**
  (§4b), and do not read a pre-registration D-2 FAIL on a sub-2 %-of-load class
  as a real breach.
* **Do not run an A/B whose two arms share a `cache_key` without scrubbing
  `results/<ISO>/` between them** (§4a).

## 8. Follow-up lane items (not done here)

1. **`cache_key` blindness to input-artifact provenance** (§4a) is an
   engine-level defect of the same class, affecting every measured-input
   correction in every ISO, not just this one. Any future session that corrects
   a measured artifact and re-solves the same config silently reuses stale
   results. Fixing it is core-infrastructure surgery (it changes every cached
   run's key) and was out of this charter.
2. **PJM A/B** (§5).
3. **Keeper promotion** of the corrected artifact for CAISO / NEISO / NYISO
   requires authoring each ISO's rule-21 attestation; see §9.

## 9. Promotion assessment

On the prereg §7 promotion rule, the corrected artifact is a **recommended
keeper candidate for all three solved ISOs — CAISO, NEISO and NYISO**:

* K1–K6 all PASS.
* Arm B carries **no protective FAIL** — C7 `shape` PASS (CAISO), C8
  `forced_share` PASS, D-4 off-window binding clean.
* **No load-bearing criterion flips PASS → FAIL** vs arm A — zero flips of any
  kind, on any criterion or D-gate.
* Zero free parameters added, so the DOF ledger is the incumbent keeper's
  unchanged (`n_residual` unmoved) — rule 21 is satisfiable without inventing a
  parameter.
* The input is strictly more accurate (rule 14): the incumbent keepers are
  currently solving against an artifact known to be diluted low by impossible
  meter hours.

**The one blocker is mechanical, not evidentiary:** an arm bundle carries no
governance attestation, so it scores `NOT-YET` and its ledgered caveats cannot
downgrade `FAIL → CAVEAT` — which fails the "determination no worse than the
committed keeper's" clause on a technicality. Promotion therefore requires
authoring the per-ISO attestation (the `gen_<iso><n>_attestation.py` pattern,
~260 lines) and then re-scoring; that is the successor session's first task, and
it is deliberately NOT rushed at the end of a long session, because a hastily
authored DOF ledger is exactly the artifact that should never be hasty.
