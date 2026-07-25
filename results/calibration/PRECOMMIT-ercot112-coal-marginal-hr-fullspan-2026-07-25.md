# PRE-COMMIT ADJUDICATION — ERCOT-112 full-span gate of `coal_econ_marginal_hr_bound`

**Written 2026-07-25, BEFORE any 2024/2025 result was read.** Rule 1: the criteria are
fixed here so the verdict cannot be reverse-engineered from the residual.

## What is being gated

The mechanism landed in ERCOT-111 (`ScenarioConfig.coal_econ_marginal_hr_bound`,
default off): each coal class's economic-tranche heat-rate band (`econ_low`/`econ_high`)
is floored at the ISO's own measured CAMPD marginal-HR p50
(`data/raw/reference/ercot_campd_marginal_hr_summary.csv`). For ERCOT this lifts exactly
one band — `COAL_PRB.econ_low 0.400 -> 0.886`.

This is a **rule-13 measured input** (a physical incremental heat rate, reproducible for a
forward year, responsive to changed conditions). It replaces a *fitted* 0.400 that had no
measurement behind it. Per rules 1 and 14 it stays in regardless of what the residual does;
what this gate decides is only whether it is ready to be put in front of the owner for
**promotion into the keeper**, not whether the mechanism is legitimate.

## Arms (both full-span 2023-2024-2025, single invocation each, years sequential)

| arm | id | config delta vs keeper `ercot_netrev_margin` |
|---|---|---|
| **B** (baseline) | `ercot112_coal_avail_only_fullspan` | `ercot_thermal_dam_availability_coal=true` |
| **T** (treatment) | `ercot112_coal_marginal_hr_fullspan` | `ercot_thermal_dam_availability_coal=true` **+** `coal_econ_marginal_hr_bound=true` |

Arm B exists because ERCOT-110 only ever solved 2023; without it there is no like-for-like
2024/2025 baseline and any T-vs-keeper comparison would confound two deltas.

## PRIMARY criteria (decided now)

**P1 — direction, per year.** For **each** of 2024 and 2025, the annual coal
generation ratio (model / actual) must move **toward 1.0** in T relative to arm B.
Formally `|ratio_T − 1| < |ratio_B − 1|` for both years. 2023 is expected to reproduce
ERCOT-111 (1.161 → 1.053) and is a replication check, not fresh evidence.

**P2 — no over-fire.** No year in T may show the ercot41/43 over-fire failure signature.
Concretely: coal must not *under*-shoot past the baseline's error on the other side
(`ratio_T ≥ 0.90` in every year), and the C3a/C3c scarcity criteria must not degrade
by more than noise (C3a no worse than baseline by >2 percentage points; C3c settled-hour
count not worse by >5 hours in any year).

**P3 — leave-one-year-out (rule 24).** Holding out each of 2023 / 2024 / 2025 in turn,
the mechanism's sign must be stable: the improvement must not be carried by a single year.
Concretely, P1's direction test must hold in **at least 2 of 3** years, and no year may
degrade `|ratio − 1|` by more than **0.05**. In-sample gain with held-out degradation is
overfitting, not skill — a single-year-carried result is a FAIL for promotion purposes
even if the 3-year mean improves.

## SECONDARY / reported-not-gated

- Jun–Sep coal ratio per year (the seasonal leg that ERCOT-111 passed at 1.207 → 1.169).
- Gas TWh vs actual — coal displacement should land in gas, not in slack/dump.
- Monthly ratio table per year, to see whether the shoulder-month over-shoot
  (Mar 0.85 / Oct 0.95 / Dec 0.87 in 2023) is a stable signature or a 2023 artifact.
- Full rubric determination + criteria deltas for both arms.

## Declared in advance: what would NOT count

- A lower system-wide price MAE is **not** evidence for this mechanism and will not be
  used to argue for it (rule 1 — the objective is structural fidelity, not fit).
- The known limitation stands and is not re-litigated: the arms are byte-identical in
  140 of 144 actual ≥$300 hours. Any scarcity-hour movement in the ≥$300 set is noise,
  not a result.

## Verdict recorded after the fact

_(filled in below once both arms complete — see the FINDING doc for the full write-up)_
