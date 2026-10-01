# ADDENDUM to PRECOMMIT-pjm-h13 — the touchpoint years' pre-solve reallocation, recorded BEFORE any shard landed (2026-09-20)

**NO GATE MOVES.** G1–G5 and the reported/gating asymmetry of
`docs/handoffs/PRECOMMIT-pjm-h13-2026-09-20.md` §4 stand exactly as pushed at
`ed3f5efdbcdd20a6317eb05add357f1909a736d6`, which is the SHA all six shards are pinned to. This
addendum only extends §2.1's table from three years to six. It is committed **while the shards are
still solving and before any arm result exists**, so it cannot have been written to fit an outcome.

Same probe, same zero-LP path (`scripts/probes/pjm_h13_drag_allocation_phase0.py`,
`run_year(..., fleet_only=True)`).

## The six-year pre-solve picture

| year | plant | ctl TWh | arm TWh | Δ TWh | ctl hrs | arm hrs | ctl median | arm median |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 3131 Shawville | 0.6357 | 0.2527 | **−0.3830** | 7042 | 3321 | 63.231 | 265.572 |
| 2020 | 3138 New Castle | 0.3522 | 0.5413 | +0.1891 | 7042 | 6739 | **0.000** | **0.000** |
| 2020 | 3140 Brunner Island | 1.5237 | 1.3855 | −0.1382 | 7042 | 6253 | 8.079 | 145.417 |
| 2020 | 1353 Big Sandy | 0.2121 | 0.5219 | **+0.3098** | 4515 | 4491 | 238.427 | 238.427 |
| 2021 | 3131 Shawville | 0.6751 | 0.2276 | **−0.4476** | 7556 | 3893 | **0.000** | **44.290** |
| 2021 | 3138 New Castle | 0.3536 | 0.5024 | +0.1488 | 6764 | 6556 | **0.000** | **0.000** |
| 2021 | 3140 Brunner Island | 1.7169 | 1.7030 | −0.0140 | 7556 | 6977 | 193.559 | 241.949 |
| 2021 | 1353 Big Sandy | 0.1871 | 0.4696 | **+0.2824** | 3797 | 3783 | 109.515 | 109.515 |
| 2022 | 3131 Shawville | 0.7415 | 0.2702 | **−0.4714** | 7664 | 4023 | **0.000** | **202.351** |
| 2022 | 3138 New Castle | 0.4184 | 0.7018 | +0.2834 | 7688 | 7504 | **0.000** | **0.000** |
| 2022 | 3140 Brunner Island | 1.8151 | 1.7404 | −0.0746 | 7688 | 7191 | 452.616 | 501.111 |
| 2022 | 1353 Big Sandy | 0.1822 | 0.4583 | **+0.2761** | 3792 | 3792 | 92.639 | 92.639 |

**Aggregate-neutral to 0.0000 TWh in all six years** (2020 2.7870; 2021 3.0041; 2022 3.2110;
2023 2.8355; 2024 3.1229; 2025 3.5270). The rule-19 claim holds across the whole span.

## The two things this changes about what the lane EXPECTS — stated, not hidden

**1. Shawville is the win, and it is large.** On the floor-array basis 3131's measured median over
its own floored hours goes **0.000 → 44.290** (2021) and **0.000 → 202.351** (2022) — i.e. the arm
moves its floor out of the hours the meter says it is dark, which is precisely the rule-17
`[R-FLOOR-WINDOW]` repair the card is chartered on. Its footprint also falls 48–53 %.

**2. New Castle is NOT repaired, and its floor GROWS.** 3138's median stays **0.000 → 0.000** in
all three touchpoint years while it *gains* 0.149–0.283 TWh of floor. The merit fill loads it
*earlier* because it is cheap on bid heat rate — which is the **KNOWN WEAKNESS the mechanism was
registered with**: heat rate is an imperfect proxy for commitment order (ERCOT measured
Spearman(heat rate, CAMPD online fraction) at −0.286, p = 0.49, in 2025). PJM's New Castle is that
weakness with a name: cheap on paper, idle in fact.

**Consequence for G4, and it is deliberately NOT relaxed.** G4 asks that **at least one** of
{3131, 3138} flip FAIL → pass in ≥ 3 of the years it currently fails. The pre-solve evidence says
3131 is the candidate and 3138 will very likely not be. **That is what the gate already says**, and
the gate is not being rewritten now that the direction is visible — G4's bar was set at "at least
one" before any of this was measured, and it stays there. If the solve shows 3131 flipping and 3138
standing, G4 passes on its own terms and **the 3138 failure is reported at full magnitude as the
mechanism's named residual defect**, not as a caveat and not as a success.

**G3 remains the gate that can kill the card**, and the New Castle direction is exactly how it might:
if 3138's growing floor adds a D-4 failure anywhere, or if the six-year total does not fall below 12,
G3 fails and the arm is refused whatever 3131 does. Baseline, for the record:
**2020 3 · 2021 2 · 2022 2 · 2023 1 · 2024 2 · 2025 2 = 12.**

**Reminder of §2.1(a)'s limit, which applies to every number above.** This is the *pre-solve floor
array*; D-4 scores the hours the floor *actually binds in the solved dispatch*, a ~3× smaller set.
None of these medians is a D-4 verdict and none of them is offered as one. Only the shards decide.
