# FINDING (pjm-h3b) — PJM 2022's C3a AND C3b are ONE defect, it is the scarcity tail,
# and 84 % of it is a single weather event

**Session** `pjm-h3` (phase 0b) · **ISO** PJM · **Date** 2026-09-13 · **Base** `origin/main` @ `c93b0d27`
**ZERO LP.** Committed artifacts only (`pjm_d4_4_TP/hourly/system_2022.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_PJM.parquet`). Nothing armed, nothing registered,
no shared code touched, no `ScenarioConfig` field added.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNCHANGED.**

---

## 1. RESULT

> **PJM 2022's C3a FAIL (−10.7 %) is not a stack, merit-order or fuel-passthrough defect. It is
> the scarcity tail — and it is dominated by Winter Storm Elliott.**
>
> * **18 hours of 8,760 (0.2 %) carry 84 % of the entire annual price gap.** Actual mean in those
>   hours **$2,071**; model **$144**.
> * **15 of those 18 are 23–24 December 2022** — Elliott. The other 3 are 13 June 2022.
> * **The other 8,668 hours are OVER-priced**: the body runs **+1.5 %** (model $63.49 vs actual
>   $62.54), contributing **−20 %** to the gap.
> * **C3b is the same defect.** Dropping the top 18 actual hours cuts the price-duration error by
>   **73 %**; dropping the top 92 cuts it by **85 %**.
>
> **Consequence: C3a-2022, C3b-2022 and the ledgered C3c-2022 caveat are ONE phenomenon, already
> accepted by the rubric as a model-class limitation. There is no admissible in-model lever, and
> every body-directed lever moves 2022 the WRONG WAY.**

## 2. THE DECOMPOSITION

Model = load-weighted zonal price from the keeper's own committed `system_2022.parquet` (`P1`);
actual = RT hourly. Model mean **64.074**, actual **68.792** → gap **−$4.717/MWh (−6.9 %)**.

| actual RT band | hours | actual mean | model mean | missing $ | annual-mean contribution | **share of the $4.717 gap** |
|---|---:|---:|---:|---:|---:|---:|
| > $200 | 92 | $658.24 | $118.88 | $49,621 | **$5.664/MWh** | **120.1 %** |
| > $500 | 26 | $1,638.73 | $136.81 | $39,050 | $4.458/MWh | 94.5 % |
| **> $1,000** | **18** | **$2,071.29** | **$143.74** | $34,696 | **$3.961/MWh** | **84.0 %** |
| **the remaining 8,668 hours** | 8,668 | — | — | — | **−$0.947/MWh** | **−20.1 %** |

The tail over-explains the gap (120 %) because the body offsets it: **the model's ordinary hours
are already too expensive.**

## 3. THE 18 HOURS ARE A STORM

`hours > $1,000 by date` — **2022-12-23: 6 · 2022-12-24: 9 · 2022-06-13: 3**. The December pair is
**Winter Storm Elliott**; the top actual hour on 2022-12-23 reaches **$2,192** and 2022-12-24
carries nine of the eighteen. By month, 35 of the 92 hours above $200 fall in December.

## 4. C3b IS NOT AN INDEPENDENT MISS

Price-duration NRMSE, recomputed on my own normalisation (so the **absolute** values are not the
scorer's 0.246 — only the **ratios** are quotable):

| basis | NRMSE | reduction |
|---|---:|---:|
| all 8,760 hours | 1.392 | — |
| excluding the top **18** actual hours | **0.382** | **−73 %** |
| excluding the top 26 | 0.293 | −79 % |
| excluding the top **92** | **0.208** | **−85 %** |
| excluding the top 500 | 0.150 | −89 % |

Eighteen hours — two tenths of one percent of the year — carry three quarters of the shape error.

## 5. WHY THIS CLOSES THE 2022 LANE RATHER THAN OPENING IT

1. **It is already a ledgered, accepted limitation.** C3c-2022 reads CAVEAT
   (`ACCEPTED MODEL-CLASS LIMITATION`) at model 3 h vs actual 92 h. This finding shows C3a-2022 and
   C3b-2022 are the *same* miss measured two other ways. The rubric already accepts that this model
   class — energy-only LMP with no administrative scarcity adder — does not form a $2,000 price.
2. **Both routes to forming one are closed.** An adder (`ordc_scarcity_overlay`) is `G`, refused by
   rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`, and the 2026-09-13 owner re-opening explicitly does
   **not** license it. Reserve scarcity was the structural route, and **this session's own screen
   refuted it for PJM** — the SYNC product split prices in 1.22 % of hours against a 22.3× supply
   margin (`RESULT-pjm-h3-reserve-sync-screen-2026-09-13.md` §11).
3. **Every body-directed lever is counter-indicated.** The body is **+1.5 %** over already. An offer
   curve, passthrough or merit-order change that lifts ordinary hours to chase the annual mean makes
   8,668 hours worse to chase 18. That is fitting to a residual by the only route left, and rule 1
   forbids it.
4. **A tuned multiplier cannot reach it either.** Closing $4.72/MWh through the body needs ~7 % on
   8,668 hours that are already 1.5 % high; the authorized band-multiplier channel (rules 1/13,
   2026-09-05) is year-invariant by condition (b), so the same move would push 2023–2025 — which
   pass at −3.6 / −5.1 / −9.3 % — further out of band in the *same* direction.

## 6. WHAT THIS DOES NOT SAY

It does **not** say PJM 2022 is calibrated: C3a and C3b remain FAIL and are reported at full
magnitude. It says the *object* behind them is the accepted scarcity-tail limitation, not an
unexplored tuning defect — so the honest next step is **not** a 2022 price lever.

It also does **not** touch **C1 CC_REGULAR-2022 (+22.56 TWh)**, which is a genuine, separate volume
miss. That one is already scheduled to move on its own: the merged `gov-hydro-seam-1` PS→`OTHER`
repair makes `reconcile_vintage_classes` newly fire in PJM 2021/2022 at the next registration,
taking CC_REGULAR-2022 to **+12.81 TWh** (`FINDING-pjm-h2-holdout-basis-2026-09-12.md` §3), with
**zero determination flips**. The residual after that is the live C1 object, and it is a **volume**
question, not a price one.

## 7. RULES

Rule 29 `[R-SCREEN]` clause 0 (zero-LP phase 0; it closed a lane rather than opening a solve) ·
rule 1 `[R-STRUCT]` (§5.3/§5.4 — no lever selected on the residual, and the one the residual would
suggest is refused) · rule 30(c) (no held-out year touches PJM's determination) · rule 32
`[R-SHARD]` (a) (the parent ran no LP).
