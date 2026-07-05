# Scalar remediation W0 closure — B-GOV-1 (2026-07-05)

**Session type:** verification + DOF-ledger completion only. No dispatch-affecting value
changed, no LP solved, no residual chased. Executes
`docs/handoffs/scalar-remediation-plan-2026-07.md` §5 W0 / `docs/handoffs/scalar-remediation-prompts-2026-07.md`
B-GOV-1.

## 1. C-2 closure — confirmed

`COAL_MAX_CF_BY_PLANT` lives in `constants.py:1089-1092` as a plant-only dict (298/6179/7097),
derived by `scripts/derive_coal_max_cf.py` (pooled 99th-percentile daily-max CF from CAMPD
hourly extracts, 2023-2025). The former `(6179, 2025)` per-year override is gone — `fleet.py:538`
documents the deletion explicitly ("a single confirmed-unit-outage year has no forward
analogue"). **Closed.**

## 2. C-11 closure — confirmed

`python scripts/legitimacy_diagnostics.py --keepers` → **PASS** for all six keepers, no D-9
failures. The D-9 check (`run_d9` in `legitimacy_diagnostics.py`) verifies for every non-ERCOT
keeper that (a) `gas_offer_curve=True` never leaves a group uncovered by
`offer_curve_by_group` (which would fall through to the ERCOT-mirrored generic
`_GAS_TRANCHE_SHARES`), and (b) no committed-HR-override group is missing its
econ/peak override (which would fall through to the ERCOT-fitted HR literals). Zero failures
across CAISO/PJM/NYISO/NEISO/MISO. Full report attached:
`docs/handoffs/d9-keeper-quarantine-report-2026-07-05.md` (+ `.json` machine artifact). **Closed.**

## 3. `offer_curves.py` rule-24 sweep

Full sweep of `src/market_sim/data/offer_curves.py`. Findings:

| Literal | Where | Verdict |
|---|---|---|
| `_GAS_TRANCHE_SHARES` (0.30/0.60/0.10, 0.40/0.50/0.10, 0/0.88/0.12) | module-level dict, L162-169 | **Compliant** — documented in-file as structural capacity splits (not tuned HR multipliers), ISO-neutral per rule 24's neutral-band/structural-share exception. No action. |
| `_hr_override(value, default)` callers (`CC_ECON_HR_OVERRIDE_DEFAULT` etc.) | L557-588 | **Compliant** — defaults are named constants imported from `constants.py`, not inline literals (this is exactly what C-11's closure moved them to). No action. |
| `getattr(config, "*_intermediate_cf_threshold", 50.0)` ×3 (L279/286/293) | offer path | **Neutral, no action** — `50.0` is not a new/independent knob: it's a byte-identical duplicate of `ScenarioConfig`'s own field default (`scenarios.py:1878/1893/1914`). The getattr fallback is dead code in practice (config always carries the field); nothing to lift since the canonical value already lives in `ScenarioConfig`. |
| `getattr(config, "iso", "ERCOT")` ×4 (L278/285/292/507) | offer path | **Neutral, no action** — duplicates `ScenarioConfig.iso`'s own default (`scenarios.py:34`). Same reasoning as above. |

No non-neutral inline fallback literal found in the offer path — the previously-flagged
ERCOT-fitted HR fallbacks (1.2/1.8/1.5/1.1/1.3) are already the `constants.py` named defaults
D-9 enforces. **No findings requiring escalation.**

## 4. DOF ledger — `build_dof_ledger.py --all-keepers`

Ran (idempotent — byte-identical rewrite, `--check` reported "current" both before and after)
for all six keepers:

| ISO | entries | residual | root-caused |
|---|---|---|---|
| ERCOT | 10 | 9 | 9/9 |
| CAISO | 10 | 8 | 8/8 |
| PJM | 9 | 7 | 7/7 |
| NYISO | 9 | 7 | 7/7 |
| NEISO | 8 | 6 | 6/6 |
| MISO | 7 | 6 | 6/6 |

Verified specifics:
- **C-1** `COAL_SIGMOID_DEFAULTS[<ISO>]` rows carry the D-8 §2C identification note verbatim
  ("floor by 2024, gas_mid/ceil by 2025 — `docs/out-of-sample-results-2026-07.md` §2C").
- **C-4** `CHP_BTM_PCT_BY_SECTOR['merchant']` row: `value: 35.0`, `identification: residual`,
  root-cause "no independent merchant-CHP host-load source found yet — replace when one exists".
- **C-8** `coal_take_or_pay_tranches` row: `identification: residual`, root-cause references
  audit C-8 (ground on EIA-923 fuel-cost dispersion contract data, or freeze via rule 23).
- **Committed-tranche multiplier < 0.85**: found in run_configs at CAISO ST_GAS (0.81),
  PJM CC_CHP (0.66), PJM ST_GAS (0.475), PJM COAL_LIGNITE/PRB/BIT/WC/COAL (0.51-0.68),
  NEISO ST_GAS (0.81), MISO ST_GAS (0.81) — all fall inside each ISO's `offer_curve_by_group`
  ledger entry, which is `identification: residual` with a non-empty `root_cause`
  (in-sample-only identification, open D-6/D-7 holdout items). This satisfies audit §2.1's
  "R6-with-issue" bar (residual + open root-cause reference); no per-scalar physical rationale
  was invented for these bands in this session (none exists yet — inventing one would itself be
  a rule-1 violation).

## 5. Rule-26 stale-prose deletions

- `src/market_sim/results/scarcity.py::effective_reliability_deployment_mw` docstring: removed
  the narrative naming the deleted `ordc_reliability_deployment_mw` knob and its retirement
  history; kept only the current-state fact (ORDC carries no offset; RTC+B uses
  `rtcb_reliability_deployment_mw`).
- `src/market_sim/config/scenarios.py::pumped_storage_dispatch_adder` docstring: removed the
  narrative naming the retired PJM $10 fitted value and its retirement story; kept only the
  current-state fact (`PUMPED_STORAGE_DISPATCH_ADDER_BY_ISO` is empty for every ISO) and pointed
  to the constant's own comment for the retirement history (that comment is a genuine root-cause
  finding — a measurement-error diagnosis — not narrative keeping a knob alive, so it was left
  as-is; only scenarios.py was in scope per the plan).
- The two remaining `ordc_reliability_deployment_mw` mentions elsewhere in `scenarios.py`
  (L422-431, L458) were left untouched: they document that the field was *deleted* from the
  dataclass (confirmed: `ScenarioConfig(ordc_reliability_deployment_mw=...)` raises `TypeError`
  today) rather than narrating a value that could be re-armed — the failure mode rule 26 guards
  against. Not in the plan's named scope either.

## 6. `audit_keepers.py`

E8 passes for all six keepers ("DOF ledger present (N entries, M residual, all with root
causes)"). One pre-existing, out-of-scope failure: `status.js` is stale (S1) because newer
same-ISO probes have been registered since each keeper — unrelated to the DOF ledger and not
touched by this session. E7 warnings (newer same-ISO runs exist) are likewise pre-existing and
out of scope for a verification-only session.

## Summary

| Item | Status |
|---|---|
| C-2 | Closed, verified |
| C-11 | Closed, verified (D-9 report attached) |
| offer_curves.py rule-24 sweep | Clean — no findings |
| DOF ledger | 100% coverage across all 6 keepers; C-1/C-4/C-8/<0.85-committed specifics confirmed |
| Rule-26 stale prose | Deleted (scarcity.py, scenarios.py) |
| audit_keepers E8 | PASS (all 6 keepers) |
