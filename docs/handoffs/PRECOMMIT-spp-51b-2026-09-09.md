# PRECOMMIT — SPP-51b: the price LEVEL residual — WHICH CHANNEL, decided at rule-29 phase 0

> **LANE COLLISION** — the SPP-51b charter was issued to two sessions. This is **session B**'s
> pre-registration; the primary lane's is `PRECOMMIT-spp-51b-2026-09-08.md` and its record
> `FINDING-spp-51b-2026-09-09.md` is canonical. See the session-B FINDING's header.

**Lane** SPP-51b · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-09 ·
**Branch** `claude/spp-51b-price-level-j0glj8` (base `origin/main` `15bbb371`) · **Data profile** `spp` ·
**Charter** SPP desk r#15, issued after owner ruling P15 declined SPP-50's promotion.

---

## 0. ORDER OF WORK — disclosed, not glossed

**Phase 0 was executed BEFORE this document was written.** This PRECOMMIT records the method,
the instruments and the decision the measurements produced; it is **not** a pre-registration of
that decision, and it does not claim to be.

What pre-registration exists to protect is a **selection**: an arm chosen because of what it did to
a criterion. **This lane selects nothing.** It spends **zero LP**, declares no arm, promotes no
mechanism, touches no keeper, and ends in a **refusal** — the same shape as SPP-46 and SPP-55, both
of which ended at phase 0. The one place pre-registration would have bound is rule 1 `[R-STRUCT]`
carve-out condition (c) — *"the value is set ex ante and declared in the PRECOMMIT before the
solve"* — and that condition is never reached, because the lane does not reach channel (C).

Had phase 0 pointed at (C), the declared config and its identifying construction would have been
pushed here before any solve, and the STOP gate with it. It did not. The record below is therefore
a **method + result** document, and the honest label for it is that, not "pre-registration".

## 1. The question the charter asks

`offer_curve_by_group` is adjudicated **`R`** for SPP. The charter re-opens the cell on NEW EVIDENCE
(rule 28's DO-NOT-REDO discipline): the `R` was minted while ~100 % of the CT over-run sat on rows
whose own inputs were physically implausible (SPP-46 §0.2), those inputs are now repaired repo-wide
(SPP-49, owner ruling P19), and SPP-50 measured the consequence — the merit order is substantially
fixed and a price residual is left standing in the open.

**I find the argument to re-open sound, and record why before touching the cell.** The `R` verdict
was minted on an object — "does a band multiplier rotate SPP's stack" — measured on an input surface
the repo has since ruled wrong. Re-asking it on the repaired surface is not a re-test of an
adjudicated cell; it is the same question on a different object. What the lane may **not** do is
promote a multiplier because the residual moved, and it does not.

## 2. Phase 0 — the three questions, and the instruments that answer them

Rule 29 step 0: zero LP, and it decides the lane.

| step | question | instrument |
|---|---|---|
| **0.1** | In the rich hours, WHO sets the price and what is that unit's marginal cost made of? | `docs/handoffs/spp51b/prices.py` (each run's hourly ISO price recovered from its own committed payload), `marginal.py` (LP input arrays rebuilt at HEAD; near-price rows by available MW), `stack.py` (the model's own merit order at its own thermal residual) |
| **0.2** | Is the level error a FUEL-BASIS error — a rule-14 input repair with zero DOF? | `fuelleg.py` (marginal fuel against SPP's own published state delivered reference; the one-lever arithmetic), `wedge.py` (the SPP-49 R-5 Permian cohort's own reach) |
| **0.3** | Which channel: (A) fuel-basis repair, (B) a missing structural object, (C) the rule-1 carve-out band? | the numbers 0.1/0.2 produce, with the decision rules in §3 |

### 2.1 The control — stated plainly, per the charter

Owner ruling P15 declined SPP-50's promotion, so keeper-3 `2026-09-07-spp-3-screened-input` is
still SPP's designated keeper — but `main` now carries SPP-48's repaired wind parquets and SPP-49's
two seams, so **keeper-3 does not reproduce on `main`'s own inputs and rule 29(b) form 4 does not
hold unqualified for SPP.** G-DRIFT `623184f3 → 15bbb371` over `src/market_sim scripts/lib
scripts/run_calibration*.py data/raw/_validation-source data/raw/reference` is **46 files,
+5,335 / −134**, and the two SPP-49 seams (`data/fuel/plant_prices.py` +228,
`data/fleet/eia860.py` +114) are **LIVE on SPP's backcast path** on the input side, as are SPP-48's
regenerated wind parquets.

**This lane therefore does not use keeper-3 as a price control at all.** It uses SPP-50's own
committed payload for SPP-50's prices, and keeper-3's committed hourlies for **three quantities
only**, each verified common to both runs rather than assumed:

| quantity | why it is common to both runs | verification |
|---|---|---|
| system demand (the load axis) | `demand` is a measured input, unmoved by either repair | SPP-50 §4: `demand` **bit-identical** in all three years |
| hourly thermal residual load | the repairs moved the split BETWEEN thermal classes, not the thermal total | annual thermal totals keeper-3 vs SPP-50: **−0.01 / −0.03 / −0.01 TWh (−0.02 %)** |
| zonal price spread | used ONLY as an order-of-magnitude bound on congestion, and reported as keeper-3's | reported as keeper-3's, never as SPP-50's |

No leg differences a keeper-3 number against an SPP-50 number.

### 2.2 That the rebuilt arrays ARE SPP-50's input surface — proven, not assumed

The arrays are rebuilt at HEAD on keeper-3's own recipe through the sanctioned
`run_year(fleet_only=True)` seam (`scripts.replay_keeper.run_year_kwargs` +
`derived_run_year_inputs`), the same reconstruction SPP-49's census and SPP-50's array census used.
Three independent checks that the result is SPP-50's surface:

- **fleet** 1,122 units in 2024/2025, 1,125 in 2023 — SPP-50 §4's census exactly;
- **seam 1** fires with SPP-49 §0.3's SPP counts **to the row**: 2024 `544 in band / 60 low /
  11 negative / 25 high → reference (19 plants)`; 2025 `505 / 37 / 5 / 6`, `227` on the US fallback;
- **seam 2** clamps the named plants (57881 Pioneer 3.429 → 9.0, 56606, 56238, 59726, 65295, 64420,
  65374, 56348).

### 2.3 Price recovery — validated against ground truth

`lmpDeltaHr` in a committed payload is `model_iso_price − actual_rt` as signed int16
(`render_calibration_html._b64_i16`, 1 $/MWh resolution), so `model = actual + delta` recovers the
hourly ISO price of a run whose bundle no longer exists — the only route to SPP-50's price surface,
since its 119 MB bundle died with its session (rule 31's ephemeral-container case, desk error E-13).
**Validated on keeper-3, where both routes exist**: payload-recovered vs its own committed
`system_<year>.parquet` demand-weighted price, `max|Δ| = 0.500` and `mean|Δ| = 0.2490–0.2499` in all
three years — exactly the int16 quantization floor, i.e. no error beyond the encoding.

## 3. The decision rules (§0's disclosure applies: these are the rules applied, stated as rules)

- **(A) fuel-basis repair** is the answer only if a defensible reference change on a named cohort
  can close the residual. It is refused if the model's marginal fuel is already at or below the
  published reference, if the residual requires opposite-signed fuel moves in the same year, or if
  the named cohort's **arithmetic ceiling** (its entire fuel bill to zero) falls short of the gap.
- **(C) the carve-out band** is the answer only if the channel's own measured transfer function can
  produce the SHAPE of the residual. It is refused if the residual reverses sign across the load
  range while the lever is measured flat across it — and refused independently if the model's cost
  surface is already correct where the residual sits, because a multiplier bending a correct surface
  to offset an error introduced elsewhere is the compensating error rule 14 `[R-ACCURATE]` forbids
  ("do not bury the error back inside an inaccurate input").
- **(B)** is what remains, and the lane's duty is then to NAME the object with a measured magnitude,
  not to shrug.

**No gate in this lane is read against C3a or C3b.** Gating on the criterion the channel targets is
the selection rule 1 forbids. C3a/C3b are reported at full magnitude as RESULTS.

## 4. Rule 31 `[R-RETAIN]`

**No bundle is written and no LP is spent**, so rule 31 has nothing to retain and no `.gitignore`
entry is owed — the SPP-46 / SPP-55 / merit-order posture. Every number the lane cites is in this
document and in `FINDING-spp-51b-2026-09-09.md`; the instruments are committed under
`docs/handoffs/spp51b/`.

## 5. Scope

FILES TOUCHED: this PRECOMMIT, the FINDING, `docs/handoffs/spp51b/`, and the
`offer_curve_by_group` cell line in `docs/codebase-site/data/mechanism-matrix/SPP.js`.
NOT TOUCHED: the plan, the ledger, `docs/calibration-log/spp.md`, `CHANGELOG.md`,
`keepers/SPP.json` and the promotion file set, the shard's keeper/gates stamp,
`frontend/data/forecast/`, any other ISO's anything, `plant_prices.py`, `eia860.py`,
`scripts/lib/wind_shape.py`.
