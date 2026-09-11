# RESULT — pjm-d4-4 span: the arm IS a keeper candidate, and registration is blocked on co-location

**Session:** pjm-d4-4 · **Date:** 2026-09-11 · Owner ruling in force: *"If structural integrity
improves but gates regress that may still be a keeper."* Continues
`docs/RESULT-pjm-d4-4-forced-outage-composition-2026-09-10.md`.

## §1 — THE HEADLINE

**The training span survives intact, and the arm does not need the owner's latitude to do it: NO
training-span gate regresses out of band, and the determination is unchanged.**

| span | control (incumbent `2026-09-10-pjm-d4-2-stgas`) | ARM | status flips |
|---|---|---|---|
| **TRAINING 2023-2025** | **CALIBRATED**, 0 caveats | **CALIBRATED**, 0 caveats | **0** |
| **HOLDOUT 2020-2021** | NOT-YET | NOT-YET | **1, and it is FAVOURABLE** (2020 C1 CC_REGULAR FAIL → PASS) |

*(2022 was still solving when this was written; its shard stalled in setup and was resumed. The
span verdict above is on the five years in hand.)*

## §2 — HOW IT WAS SCORED, AND WHY THAT METHOD IS ADMISSIBLE

Registration needs the heavy bundle (§4), so the arm could not be registered and then scored the
normal way. It was scored the way the screen shard's item 4 established and validated: take the
incumbent keeper's committed payload and substitute, per year, (a) the arm's own class TWh as a
**delta** on `gmModel` and (b) an `lmp` block rebuilt from the arm's own
`hourly/system_<year>.parquet` on the payload's own load-weighted construction.

**The control leg is the same code path fed the incumbent's own sidecars, so any method error
cancels — and it reproduces the committed verdict exactly (`CALIBRATED`, 0 caveats).** That is the
validation; without it no arm number here would be quoted.

**What this method does NOT re-measure, stated so nothing is over-claimed:** C4 (hourly dispatch
correlation), C6 (governance) and C8 (forced share) are read from the INCUMBENT's committed
artifacts, because the substitution touches only `gmModel` and `lmp`. The arm's own
`legitimacy_diagnostics.json` exists for 2023/24/25 and is NOT scored here. Those three criteria are
therefore **unverified on the arm** and must be re-scored from a registered bundle before promotion.

## §3 — EVERY MOVED CELL, BOTH DIRECTIONS, NOTHING NETTED OUT

### Training span 2023-2025 — determination CALIBRATED both sides

| criterion | year | control | ARM | |
|---|---|---|---|---|
| **C3a** price mean | 2023 | PASS −1.3 % | **PASS −0.5 %** | better |
| | 2024 | PASS −5.2 % | **PASS −4.2 %** | better |
| | 2025 | PASS −8.3 % | **PASS −7.8 %** | better |
| **C3b** price shape | 2023 | PASS 0.111 | PASS **0.112** | *worse* |
| | 2024 | PASS 0.130 | **PASS 0.128** | better |
| | 2025 | PASS 0.154 | **PASS 0.152** | better |
| **C1** CC_REGULAR | 2023 | PASS +6.04 TWh | **PASS +2.86 TWh** | much better |
| | 2024 | PASS +4.08 TWh | **PASS +0.67 TWh** | much better |
| **C1** COAL_BIT | 2023 | PASS +1.33 TWh | PASS **+2.10 TWh** | *worse* |
| | 2024 | PASS −1.88 TWh | **PASS −1.13 TWh** | better (toward 0) |
| **C1** CT_PEAKER | 2023 | PASS −2.00 TWh | **PASS −1.13 TWh** | better |
| | 2024 | PASS +0.54 TWh | PASS **+1.82 TWh** | *worse* |
| **C1** ST_GAS | 2023 | PASS +2.04 TWh | PASS **+2.44 TWh** | *worse* |
| | 2024 | PASS −1.28 TWh | **PASS −0.93 TWh** | better |
| **C2** coal | 2025 | +9.3 % | **+9.6 %** | *worse* |
| **C2** gas | 2025 | +2.4 % | **+2.2 %** | better |

**The pattern is coherent and it is the mechanism's own signature:** removing gas availability moves
energy off CC_REGULAR — the class that was most over-generating — and some of it lands on coal and
CT_PEAKER, which move the wrong way. C1's largest error cell improves by 3.2 and 3.4 TWh; the costs
are tenths of a TWh and every one stays inside its PASS band.

### Holdout span 2020-2021 — NOT-YET both sides (rule 30(c): a held-out year never downgrades PJM)

| criterion | year | control | ARM | |
|---|---|---|---|---|
| **C1** CC_REGULAR | 2020 | **FAIL +10.28 TWh** | **PASS +7.56 TWh** | **the one status flip, favourable** |
| | 2021 | FAIL +29.16 TWh | FAIL **+26.31 TWh** | better, still FAIL |
| **C1** COAL_BIT | 2020 | FAIL +21.97 TWh | FAIL **+22.83 TWh** | *worse*, already FAIL |
| **C3a** | 2020 | FAIL +21.4 % | FAIL **+22.3 %** | *worse*, already FAIL |
| | 2021 | PASS +4.9 % | PASS **+5.8 %** | *worse*, still PASS |
| **C3b** | 2020 | FAIL 0.234 | FAIL **0.242** | *worse*, already FAIL |
| | 2021 | PASS 0.114 | PASS **0.118** | *worse*, still PASS |

**2020 degrading is PREDICTED, not anomalous, and it was predicted before this solve.** 2020 is the
**opposite defect** — the model prices **+21.4 % OVER** actual there (ADDENDUM §1, which flagged
2020 as "NOT this card"). Deepening the outage envelope raises price, so it must make an
over-pricing year worse. That it does exactly that, and only there, is evidence the mechanism is
behaving structurally rather than fitting.

## §4 — WHY THE ARM IS NOT REGISTERED, AND WHAT IT WOULD COST

`dashboard_add_run.py` → `render_calibration_html.build_payload` reads, per bundle:
`system.parquet`, `storage.parquet`, `btm.parquet`, **`dispatch/<year>_P1.parquet`**, and the shared
`eia923` / `eia930` / `campd` input parquets under `results/calibration/_shared/PJM/`. **None of
those is in the slim file set the six shards were told to push** — that was an error in the shard
prompt design, and it is mine. Each shard's full ~196 MB bundle sits on its own ephemeral container,
and **no single container holds all six years**, so the composite cannot be assembled anywhere.

**The registrable-keeper path is therefore ONE container solving all six years sequentially in a
single invocation** (rule 12 `[R-PARALLEL]`: years sequential within a run), then composing,
registering and pushing from there. Cost: **~2.5-3 h of LP in one container.** This breaks rule 32(b)'s
20-minute-per-shard-commit guidance, and the rule's own subdivision escape ("shards launch shards")
does **not** rescue it, because registration inherently requires co-location. Stated rather than
papered over.

## §5 — THE RECOMMENDATION, CHANGED AGAIN AND SAID SO

Before the screen I recommended spending the span. After the screen killed the tail claim I
recommended **not** spending it. **The span is now spent and the numbers are better than the screen
predicted**: the arm improves C1's worst cell by 3.2-3.4 TWh and C3a in all three training years,
holds CALIBRATED with zero caveats, and flips a holdout FAIL to PASS.

**On the evidence in hand this IS a keeper candidate and I recommend promotion** — subject to the
two conditions §2 names honestly: C4/C6/C8 are unverified on the arm and must be re-scored from a
registered bundle, and 2022 must land so the span is complete under rule 16 `[R-ALLYEARS]`.
