# RESULT nyiso-149 — the CHP lay-up duty CURVE passes every pre-registered gate and is PROMOTED: the first NYISO keeper CALIBRATED on the authoritative benchmark

Session nyiso-149, 2026-08-22. Prereg
`PREREG-nyiso149-chp-duty-curve-2026-08-22.md` committed and pushed before any
arm solved; the §7 basis-defect disclosure appended before the corrected
solve. Gates record `_nyiso149_duty_curve_gates.json` (first-solve record
`_nyiso149_duty_curve_gates_basis.json`); identification
`_nyiso149_chp_duty_curve_phase0.json`; benchmark ruling (Job 1, the blocking
owner charter) `FINDING-nyiso149-bench-root-cause-2026-08-22.md`.
Years 2023/2024/2025, one bundle per arm, years and arms sequential; holdout
freeze ACTIVE and untouched.

**Registered (rule 15): `2026-08-22-nyiso-149-duty-curve` (ARM F, corrected —
PROMOTED TO KEEPER) and `2026-08-22-nyiso-149-basis-probe` (ARM F's first,
mis-based solve — the seam-defect record).** The BASE replay reproduces the
registered `2026-08-20-nyiso-147a-chp-btm` **bit-exactly** (max |Δprice| = 0.0
over every zone-hour of all three years) and is not double-registered — that
identity also proves this session's whole code footprint (the Job-1
`btm_bench_twh` pin and the duty-curve machinery) byte-inert at defaults.

---

## 1. THE SCORECARD

| gate | verdict | |
|---|---|---|
| **IDENT** | **PASS** | base ≡ registered 147a, max \|Δprice\| = 0.0 ×3 years |
| **F-K1** exactness | **PASS** | exactly one config field differs: `chp_layup_duty_curve` (git_sha/timestamp reported as provenance) |
| **F-K2** liveness | **PASS** (2nd solve) | LP-entry composition exact to 0.01 MW on all 7 census plants; committed = 0 everywhere; zero non-census movement. **FAILED on the first solve** — see §3 |
| **F-K3** graded conduct | **PASS** | all 21 plant-years in-band vs their own CAMPD meters; cohort 291 → 413 → 988 GWh reproduces the metered ordering into dear 2025 |
| **F-K4** conduct rows | **PASS** | zero new failing D-1/D-2/D-4 rows; the base's **D2 ST_GAS-2024 30.4 % forced-share failure is CLEARED** |
| **F-K5** criteria | **PASS** | C1 **14/14** — including CC_REGULAR-2024, the criterion that made the prior keeper NOT-YET — C2/C3a/C3b/C4/C8 PASS; no base-PASS criterion flips |
| **F-K6** (reported) | — | system lw: 2023 33.32 (+3.3 %), 2024 36.53 (−4.2 %), 2025 60.57 (−8.8 %) vs base 32.73/35.84/58.36 |

**DETERMINATION: CALIBRATED** (attested C6; C3c the single ledgered caveat —
model 1/0/0 h > $300 vs RT actual 10/13/42 h — auto-ledgered, non-downgrading,
rubric v3.3). `audit_keepers --iso NYISO`: **PASS 0/0** after promotion.

## 2. WHAT THE GRADED CURVE DOES THAT THE SINGLE BAND COULD NOT

nyiso-148 rejected `chp_layup_duty_split` because one peak band is bang-bang:
the cohort sat ~OFF in cheap 2023/2024 (Selkirk 0.03–0.05× its meter) and
STILL OVER in dear 2025 (Lockport 3.96×). The duty curve's measured econ/peak
MW with a withheld remainder produces the graded response the meters show:

| plant (×meter) | base (147a) | rejected split (148) | **duty curve (149)** |
|---|---|---|---|
| Selkirk 2023/24/25 | 2.0× / 6.8× / 3.2× | 0.03× / 0.04× / 0.05× | **0.54× / 1.76× / 0.85×** |
| Lockport 2023/24/25 | 14.3× / 6.8× / 6.4× | 0.89× / 0.24× / 3.96× | **1.23× / 0.56× / 1.05×** |

And the criteria the base failed all clear: **C3a-2025 −12.2 % → −8.8 %
(PASS)**, **C3b-2025 NRMSE 0.210 → PASS**, **C8 → PASS** (the ST_GAS-2024
30.4 % forced share falls under the cap once the cohort's cheap-year econ MW
serves load the bridge was otherwise forcing).

Composition honesty: the duty statistics are measured **conditional on
envelope-live hours** (the same frozen outage extract the recipe applies), so
where the envelope carries the mothball spells (six of seven plants, within
~0.02 of metered live share) the offer carries only the residual price
response, and where it does not (Lockport, ~1.0 available vs 0.12–0.44 live)
the offer carries the whole duty. Rule 19 with a measured seam, not a claim.

## 3. THE F-K2 CATCH — the seam-defect class, caught pre-scoring this time

ARM F's first solve applied the artifact's pct-of-census-pmax fractions to the
**bin nameplate** — a different capacity basis — over-offering every plant by
1.01–1.35× (Selkirk 251.9 vs 199.4 MW = exactly 754/596.6). This is the fourth
member of the nyiso-146b/148 seam-defect class, and the first one caught
**before any scoring**: gate F-K2 tests band composition at the LP-entry
grain, the prereg §7 disclosure landed before the corrected solve, and the fix
is the **MW contract** — the artifact carries `econ_mw`/`peak_mw` (the duty is
`s·L·HSL`, basis-free) and all three seams consume the MW at the **CAP level**
(the econ residual would silently re-absorb a pct-level withhold). The
mis-based solve is registered as `2026-08-22-nyiso-149-basis-probe`; its
conduct was already in-band (F-K3 passed) — the defect was offered capacity,
not shape.

## 4. PROMOTION PROTOCOL EXECUTED

Keeper shard → `2026-08-22-nyiso-149-duty-curve` + `build_status --iso NYISO`
(**NYISO: CALIBRATED**); rule-22 D-5(b) marker re-key with determination
re-verification (NOT-YET → CALIBRATED: the label improves, the
worse-determination stop does not fire; `keeper_at_declaration` preserved;
`rekey_history` appended); attestation with governance booleans, the C3c caveat carried by the
rule-22 STANDING RULE (explicit exceptions deliberately empty — the
promotion-time entries lacked a "kind" tag and mis-routed the
classification; caught by the keeper-text audit, fixed at the source, run
re-registered), and the seeded DOF ledger (8 entries, all inherited from
the 146c lineage — this session adds **zero** free parameters);
`audit_keepers --iso NYISO` PASS 0/0; NYISO matrix shard re-stamped (keeper +
gates; `chp_btm_measured` **R → K** with the R record preserved;
`offer_curve_by_group` third leg K) and the §5.5 prose header re-stamped.
`marker_reexamination_open` is annotated PREMISE RESOLVED (the flag's premise
— a NOT-YET keeper — no longer holds) but **left open for the owner** who
flagged it; the holdout freeze outranks everything either way.

## 5. WHAT THIS KEEPER DOES NOT CLAIM

* **The 2025 offer-level object stays OPEN.** C3a-2025 passes at −8.8 %, but
  nyiso-148 proved ~$6.57/MWh of the base's gap is price-formation work no CHP
  mechanism can reach (energy is conserved). The owner card
  (`DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`) is pending;
  its Q2 annotation concern now applies to a −8.8 % pass instead of a −2.2 %
  cancellation — materially more honest, still not "validated".
* **C3c** remains the ledgered model-class limitation, reported at full
  magnitude (1/0/0 vs 10/13/42 h).
* **The zonal gradient** (ASSESSMENT-nyiso148 §2.3) and the **Flynn
  start-count excess** remain open lane items; RHO_CLIP, the Iroquois winter
  spread, the D-4 vintage guard and the Astoria attribution remain owner/lane
  items out of this session's scope.

## 6. GOVERNANCE

* Holdout freeze ACTIVE; every year solved, scored or read is 2023/2024/2025.
* Rule 15: both completed solves registered; keeper hourly sidecars committed.
* Rule 21: zero new free parameters (bands declared a priori in the committed
  phase-0 probe; membership/HSL/pmax frozen census fields; offer levels =
  existing class multipliers).
* Rule 23: the duty artifact re-derives only on CAMPD / MIS-LBMP / outage
  extract updates; census and BTM shares untouched.
* Rule 28: shard + prose header re-stamped in this session; matrix checker
  clean (0 errors, 0 warnings).
* DO-NOT-REDO honoured; OUT-OF-LANE items untouched.

## 7. REPRODUCTION

```
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso147_armA_recipe --out-dir results/calibration/nyiso149_base
python scripts/run_calibration_full.py --replay-bundle results/calibration/nyiso149_armF_recipe --out-dir results/calibration/nyiso149_armF
python scripts/legitimacy_diagnostics.py --bundle results/calibration/nyiso149_armF --iso NYISO --years 2023 2024 2025 --json-out results/calibration/nyiso149_armF/legitimacy_diagnostics.json
python scripts/probes/_nyiso149_duty_curve_gates.py
python scripts/calibration_verdict.py --run-id 2026-08-22-nyiso-149-duty-curve
python scripts/audit_keepers.py --iso NYISO
```
