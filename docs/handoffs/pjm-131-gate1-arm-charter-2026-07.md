# CHARTER — pjm-131, arming gate 1 (the CC_CHP / ST_GAS overshoot against the meter)

**Lane:** `docs/handoffs/pjm-frontier-path-2026-07.md`.
**Predecessor:** pjm-130 (PR #2978 code / #2980 docs) —
`results/calibration/FINDING-pjm130-gate1-and-bench-symmetry-2026-07.md`.
**Inherited kill criteria:** pjm-130 charter §5, reproduced in §4 below, unmet-means-dead.

This document and the probe it pre-registers are **committed before the probe is
run**. Nothing below was written after seeing a number.

## 0. Settled going in — not re-litigated

The corrected CAMPD envelope stays in (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`);
post-keeper code drift is PJM-inert; gate 1 is displacement, measured (99.6 %,
r = −0.369, pjm-130 §1 — **not re-run**); gates 1 and 2 are one stratum; gate 3's
root cause is out of reach and is ledgered, not mechanised (rules 1 / 19); lane 2's
commitment-status half is closed terminal (pjm-128); the holdout freeze is active
(2023–2025 only, rule 22 `[R-HOLDOUT]`); keeper `2026-07-25-pjm-121-cc-belt` is
owner-only and is not touched.

## 1. Priority 1 — the re-conditioning memo — checked, still UNDECIDED

`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md` is **verified
undecided this session**: last commit `f1070d4`, the live banner still reads
"awaits the owner's decision", and no authorization exists anywhere in the tree.
Per the session's own instruction the memo is **not nudged, not re-derived, and
no proxy is taken** (rule 23 `[R-FROZEN-DERIVE]`). Gate 2 therefore stays blocked
and this session proceeds to gate 1.

## 2. The named candidate — a rule-14 accuracy inversion in the CHP host share

Gate 1's target is the 2023 overshoot **against the meter**: CC_CHP +2.54 TWh
(+41 %) and ST_GAS +1.72 TWh (+19 %), against CC_REGULAR −8.10 TWh (band 8.00).

For the three gas CHP classes the behind-the-meter host share is not a floor — it
is a **grid-capacity pull-out**. In `data/offer_curves.py::plant_cf_bands` (and
its `bins_to_fleet` twin) `pct_mr = chp_btm_pct(...)` and then, for non-coal,
`mustrun_cap = 0` and `grid_cap = nameplate × (1 − pct_mr/100)`. The same share
is the bench subtrahend: `run_calibration_full.py::_btm_frame` sizes
`btm[k] = Σ_p s_p × e923_class_p` from `chp_btm_pct` — its docstring calls it
"the identical share the LP hold-out uses", and pjm-130 established that the two
sides must move together.

**The inversion.** `chp_btm_pct` is the **sector-keyed estimate**
(`CHP_BTM_PCT_BY_SECTOR` — merchant 35.0, self-documented in `constants.py` as
"residual-identified, forecast-risk — no independent source yet"). A **measured
per-plant** replacement exists in the tree — `chp-btm-share`
(`scripts/data/curate_chp_btm_share.py`, `data.chp.measured_btm_share_by_plant`),
`btm_share = (eia923_net − campd_net)/eia923_net`, both sides measured and
independent of the model's dispatch — and `runner.py` resolves it **only for
forecast years**, explicitly leaving the backcast on the sector estimate. So the
mode we score against the meter uses the estimate and the mode we cannot score
uses the measurement. Rule 14 `[R-ACCURATE]` reads on this directly.

**Rule 14 commitment, stated before the measurement:** if the measured share is
admissible, it is the input this model should carry **whichever direction it
moves the residual**. A worse fit would be a discovered bug to root-cause, not a
reason to revert (rule 14's explicit clause). Adopting it is therefore *not*
conditional on gate 1. What §4 gates is only whether it is a legitimate **gate-1
arm** and whether it justifies spending a solve.

## 3. Probe — `scripts/probes/pjm131_chp_btm_precheck.py`, no LP

Committed inputs only: the `chp-btm-share` clean artifact (curated from the
already-committed `_processed-legacy` CAMPD + EIA-923 sources), `chp_btm_pct`,
the `pjm129_meritguard_a1` bundle's `meta.json` fleet reconstruction via
`scripts/lib/bundle_fleet.py` (**not** `_run_year_kwargs`), its committed
`hourly/class_hourly_2023.parquet`, and the committed PJM bench.

## 4. Pre-registered decision rules — unmet-means-dead

**Q1 — materiality.** `delta_cap = (s_applied − s_measured)/(1 − s_applied)`,
capacity-weighted over PJM CC_CHP plants.
→ **DEAD (no solve)** if `|delta_cap| < 5 %`: a swap that small cannot move a
41 % overshoot.

**Q2 — direction.** If `s_measured < s_applied` (measurement says *less* host
self-supply ⇒ *more* grid capacity), the swap can only enlarge the overshoot.
→ It remains the accurate input per §2, but it is **NOT a gate-1 arm**: record
the rule-14 finding, open the root cause, spend **no** solve on it as an arm.

**Q3 — capacity-bound invariance.** `kappa` = share of CC_CHP 2023 model energy
in hours where class dispatch ≥ 99 % of its reconstructed hour-varying grid-facing
available capacity.
- `kappa ≥ 0.80` — capacity-bound. Model and bench actual both scale by
  `(1 − s)`, so the **relative** overshoot is invariant and only the absolute TWh
  moves. Admissible as an absolute-TWh lever only, and Q4 must still pass.
- `kappa ≤ 0.20` — economically dispatched. Model energy barely responds to the
  cap while the bench actual falls in full ⇒ the overshoot **worsens**.
  → **REFUTED as a gate-1 arm.**
- otherwise — report the mixed elasticity; Q4 decides.

**Q4 — THE inherited kill criterion (pjm-130 charter §5).** Predicted 2023
overshoot after the swap, both sides moved:
`model_new = model_old × (1 − kappa × delta_cap)`,
`actual_new = actual_old × (1 − s_measured)/(1 − s_applied)`.
→ The arm survives **only if** `model_new − actual_new < model_old − actual_old`
for CC_CHP, i.e. the overshoot **against the meter** reduces. An arm that lifts
CC_REGULAR while leaving the returned classes above their metered energy is
displacement-neutral and is the refutation signature. Otherwise **DEAD**.

**Q5 — the ST_GAS half.** From the A1 bundle's committed
`legitimacy_diagnostics.json` (D-2 attribution, D-4 off-window binding): does
`gas_st_netload_drag` bind outside a declared, driver-justified window, and what
share of ST_GAS energy is forced?
→ Off-window binding is a rule 17 `[R-FLOOR-WINDOW]` bug and a real lever.
→ Clean and in-window ⇒ ST_GAS's +19 % is not a floor artifact: **ledger it, do
not mechanise it** (rules 1 / 19).

**If a solve is spent**, it additionally inherits, unmet-means-dead: C1 must not
lose a free class (A1 is 15/16, free 11/12); C2 stays PASS; scored
**leave-one-year-out within 2023–2025** before any promotion flag; rule 16
`[R-ALLYEARS]` — 2023 + 2024 + 2025 in ONE bundle, any single-year solve is a
throwaway diagnostic and is deleted, never registered.

## 5. What this session may not do

No edge re-tuning, no new floor, no adder, no haircut, no offer-band move, no
derive re-run against a residual (rules 1 / 20 / 23 / 24 / 26). No holdout year
(rule 22). No `keepers.json` edit. No CI job for a solve.
