# ASSESSMENT — NEISO & PJM validation touchpoints re-walked on the current keepers

**Session:** neiso-pjm-validation-touchpoints · **Date:** 2026-09-05 ·
**HEAD:** `6619fb4a` · **Branch:** `claude/neiso-pjm-validation-touchpoints-fs3eor`
**Keepers under test:** NEISO `2026-08-17-neiso-99-joint-p1` (bundle `neiso99_joint_B`) ·
PJM `2026-08-15-pjm-162-inputclock` (bundle `pjm_debugb_inputclock_A`)

---

## 0. The question, and the answer

> **Had the validation touchpoints been run for NEISO and PJM on the CURRENT keeper configs?**
>
> ## **NO — not one rung, for either ISO.**

| ISO | 2022 | 2021 | 2020 |
|---|---|---|---|
| **NEISO** | ran 2026-08-06 (`2026-08-06-neiso-2022-corrected-basis`) on the **neiso-87** recipe → **STALE**, and pruned from the dashboard 2026-08-09 | **never run** (formally refused on data readiness, `ASSESSMENT-neiso92`) | **never run**, never assessed |
| **PJM** | ran 2026-08-05 (`2026-08-05-pjm-2022-touchpoint`) on the **pjm-152** recipe, i.e. the **pre-repair input clock** that pjm-162 *is* → **STALE**, pruned | **never run** | **never run**; demand feed measured DEFECTIVE (`ASSESSMENT-pjm-final-readiness`) |

Both ISOs' keepers moved **after** their only touchpoint was scored, and both moves were
measured-input repairs applied to every year. Under rule 22's own instruction — *when we hit
go, the config is already precisely the frontier keeper, with nothing left to prepare* — a
ladder measured on a superseded recipe is not a walked ladder.

## 1. Gate state — verified at HEAD, not assumed

| gate | state | evidence |
|---|---|---|
| Holdout spend **freeze** | **ACTIVE but TIER-SCOPED to the LOCKED TEST alone** | `holdout-freeze.json` `scope.tiers = ["locked_test"]`; `holdout_policy.frozen_tiers()` returns `frozenset({'locked_test'})` at HEAD. The validation tier was lifted from the freeze by the 2026-08-26 owner ruling (card 6) and is governed by the `complete` marker + `--holdout-authorized` alone. |
| Tier of 2020 / 2021 / 2022 | **validation** | `holdout_policy.tier_for_year` → `validation` for all three |
| NEISO / PJM `complete` | **held** (2026-07-07 / 2026-07-31) | `calibration-complete.json` |
| NEISO / PJM `final` | **absent** | Locked test NOT granted to either ISO and never spent. **Untouched by this session.** |

Every solve below ran through `enforce_holdout_year_gate` and printed the tier warning; no
locked-test year was solved, scored or registered.

## 2. NEISO — the full ladder, on `2026-08-17-neiso-99-joint-p1`

Registered: `2026-09-05-neiso-2022-touchpoint-k99` (bundle `neiso_tp2022_k99`) and
`2026-09-05-neiso-2020-2021-touchpoints` (bundle `neiso_tp2021_2020_k99`).

| rung | determination | what moved |
|---|---|---|
| **2022** | **CALIBRATED** | **zero degraded criteria.** Every criterion holds against the keeper's in-sample column; the lone blemish is the ledgered C3c (model 0 h vs RT actual 117 h > $300), which is carried on both sides and does not downgrade under rubric v3.3. C3a lands at −0.7 % vs DA. |
| **2021** | **CALIBRATED** | clean — **C3c passes too** (2021 has 0 actual RT hours > $300, so the tail is scored on the small-count rule and the model's 0 h matches). Zero caveats. First solve of this rung, ever. |
| **2020** | **NOT-YET** | **lone FAIL: C3a mean LMP +13.7 %** (model $27.81 vs actual RT $23.39). C1, C2, C3b, C3c, C4, C6 and C8 all PASS; C5a CO2 −1.6 %. |

**The 2022 result is the load-bearing one.** It is the first 2022 number that measures the
current frozen recipe, and it is *better* than the recipe it replaces (`CALIBRATED` against
the stale rung's `CALIBRATED-WITH-CAVEATS`, with C3a degraded there and held here). The
neiso-97 SMD-clock and neiso-99 outage-routing repairs — both measured-input corrections with
zero free parameters — **hold out-of-sample.** That is the outcome rule 22's loop is designed
to produce and it did not have to come out this way.

### 2.1 The neiso-92 refusal of 2021 is OVERTAKEN — measured, not waived

`ASSESSMENT-neiso92-2021-readiness-2026-08-13` refused 2021 on four DEGRADED inputs, one
(**nuclear availability**) severe enough on its own to reproduce the neiso-85 failure mode:
+0.96 TWh of phantom annual nuclear, +1.25 TWh of it in October alone. **All four have since
been repaired.** Measured at HEAD this session, before any solve:

| neiso-92 gap | coverage at HEAD | verdict |
|---|---|---|
| `nuclear-availability-NEISO.csv` (per-reactor NRC overlay) | **2019–2025** (1,095–1,098 rows/yr, 3 reactors) — was 2023–2025 | **REPAIRED** |
| `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` (monthly anchor) | **2019–2025** — was 2023–2025 | **REPAIRED** |
| `IMPORT_/EXPORT_TRANCHES_BY_YEAR['NEISO']` | **2019–2025** — was 2023–2025 | **REPAIRED** |
| `eia860_chp_by_year` / `parasitic_load_factors` | **2018–2025 / 2019–2025 (+ pooled)** | **REPAIRED** |

2021 no longer falls through to the static climatology on either nuclear layer, which is
exactly the failure the refusal was written to prevent. **The refusal was correct when
written and is now spent** — this is data prep landing, which rule 22 (as amended 2026-08-06,
*"what is held out is the SCORE, never the DATA"*) leaves unrestricted and unmarked.

### 2.2 What 2020's C3a miss is, and what it is not

+13.7 % on a $23.39/MWh year is **$3.20/MWh of absolute error** — the smallest absolute miss
of the three rungs (2021 and 2022 both pass at higher price levels). It is a *percentage*
failure on the cheapest year in the record, not a large mis-pricing.

**Do not treat it as a tuning target.** Rule 22 step 3 sends a validation miss back to
2023–2025 to be diagnosed as an *object*, and there are two named candidates that the
evidence already points at, neither of them a parameter:

1. **2020 is the COVID year** — the lowest-load, lowest-price year in the span, and the one
   whose merit order sits furthest from the tuned window. A model that prices the belly
   slightly high will show it worst here.
2. **The C3c/D-A amplitude signature is different in 2020**: hod amplitude 30.6 % of measured
   with hod r +0.960 (2021: 47.6 % at r +0.936). The model's diurnal range is compressed
   while its *shape* correlation is the highest of the three years — a level story, not a
   shape story, which points at the offer stack's low end rather than at commitment.

Neither is diagnosed here, and **nothing was tuned**: this session measured and reported only.

## 3. PJM

*(Section 3 is completed after the PJM solve lands — see §3.2, which is measured and final.)*

### 3.2 PJM 2020 is NOT DATA-READY — three independent blockers, all measured at HEAD

The 2020 rung was **not** solved, and should not be requested until these are repaired. This
is not a governance refusal (PJM holds `complete`, and 2020 is validation tier) — it is a data
refusal on the neiso-85 principle: a spend against a defective input measures the defect.

**(a) The zonal demand feed is systematically inflated at peak, and carries two impossible
hours.** From `load_demand('PJM', y)` at HEAD (no LP, no model output). The loader's own
spike guard fires and repairs 5 hours above 2.5× median — and the defect *survives it*,
because 197,438 / 84,976 = 2.32×:

| year | system max (MW) | p99.9 | max/p99.9 | annual energy |
|---|---|---|---|---|
| 2019 | 157,644 | 151,110 | 1.04 | 831.9 TWh |
| **2020** | **197,438** | **148,785** | **1.33** | **809.6 TWh** |
| 2021 | 153,412 | 151,915 | 1.01 | 834.0 TWh |
| 2022 | 152,376 | 147,488 | 1.03 | 842.0 TWh |

The top two hours of 2020 are `2020-07-27 11:00` at **197,438 MW** and `2020-07-28 15:00` at
**181,841 MW**, against a third-highest hour of 151,534 MW. Both exceed PJM's published
all-time system peak (~165.5 GW, 2006-08-02), and an 11:00 annual peak is not a PJM summer
peak shape.

It is **not** confined to two hours. Every zone's 2020 annual maximum is inflated against the
mean of its 2019 and 2021 maxima:

| zone | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| 2020 vs mean(2019, 2021) | +0.9 % | +17.1 % | +22.5 % | +15.4 % | +18.0 % | +27.1 % | +26.6 % | +26.9 % |

Seven of eight zones peak 15–27 % high **while 2020 carries the lowest annual energy in the
record** (COVID). Peak up 27 %, energy down: incoherent as load, coherent as a metering
artifact. Solving it as-is would dispatch against impossible hours in exactly the
scarcity-formation window C3c gates.

**(b) `calibration_reference.json` has no PJM 2020 block.** PJM's reference years are
`[2019, 2021, 2022, 2023, 2024, 2025]` — 2020 is the only gap. (NEISO's are complete,
2019–2025, which is part of why NEISO's ladder could be walked in full.)

**(c) `PJM_2020_renewable_capacity.csv` does not exist.** Same year set as (b).

Blockers (b) and (c) are pure data prep on sources already on disk; (a) needs a decision, not
just a fetch — see §5.

## 4. Two stated limits on every comparison in this document

Both are recorded in each bundle's `calibration_attestation.json` and in each sidecar's
`holdout.envelopeCaveat`, so no reader has to rediscover them.

**(i) HEAD drift between the two columns — MEASURED, and it is INERT.** A touchpoint's
in-sample column is the *keeper's* committed determination, solved at its own HEAD; the holdout
column is solved at this session's HEAD. NEISO's keeper solved at `b7904a1` (2026-08-17) and
these rungs at `6619fb4a` (2026-09-05).

A rule-30 `G-DRIFT` hunk-level audit was attempted first, as the rule directs, and **is not
dischargeable at reasonable cost**: `git diff b7904a1 6619fb4a` over the solve path
(`src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`, `data/raw/_validation-source`,
`data/raw/reference`) is **120 files / +119,273 lines** spanning five other ISOs' lanes. Asserting
"every hunk INERT" over that would be a claim, not an audit. A **LIVE** hunk is what earns a
control solve under rule 30(b), and an unclassifiable diff is treated as LIVE.

So the control was solved: `neiso_headctrl_k99`, the keeper recipe replayed on **its own training
years 2023–2025** at this session's HEAD, one invocation, all three years fresh, no holdout year
and no `--holdout-authorized`. Differenced against the keeper's committed hourly sidecars:

| series | worst drift, 2023–2025 |
|---|---|
| system mean zonal **price** | **−0.008 %** (max −$0.0032/MWh, on a $38.41 year) |
| system **demand**, **slack**, **dump**, **reserve_price** | **0.000 000 %** — bit-identical |
| **total generation** | **≤ 0.0008 %** |
| worst **per-class annual energy** (14 classes) | **0.17 %** (ST_GAS 2025; CT_PEAKER 0.07 % 2024) |

Nineteen days and 120 changed files moved NEISO's mean price by three tenths of a cent per MWh,
and moved nothing at all in the load, slack, dump or reserve rows. That residual is degenerate-LP
tie-breaking, not a code effect — the rule-19 `[R-EPSILON]` storage tiebreaker and equal-cost
tranche ordering are enough to explain it. **HEAD drift is INERT for the NEISO backcast path, and
the in-sample-vs-holdout comparison in §2 is like-for-like.** This is measured rather than
asserted, which is the whole reason the control was worth 15 minutes of LP.

**The same measurement has NOT been made for PJM** and should not be assumed to transfer
(rule 25 `[R-ISO-SCOPE]`): PJM's keeper solved at a different HEAD, and its recipe arms
mechanisms — `pjm_measured_interface_limits`, `pjm_da_virtual_bids`, `measured_ramp_capability` —
that NEISO's does not touch. PJM's touchpoints carry the drift as an open limit.

**(ii) Bench-part vintage — RESOLVED for NEISO during this session.** `dashboard_add_run.py`
writes each year's benchmark part with the builder at HEAD, so the first registration put
2020/2021/2022 on the current builder while NEISO's 2023–2025 parts still predated it
(fingerprint `b2f21b9a00d3`; the scorer emitted a STALE BENCHMARK warning naming them). PR #4845
(`y12-bench-ast-fingerprint`) landed on main mid-session and this branch was rebased onto it;
re-registering both runs put **every NEISO bench part 2020–2025 on one builder** (fingerprint
`4254168edcfe`) and the STALE BENCHMARK warning is gone. Determinations were **unchanged** across
the rebuild — 2022 `CALIBRATED`, 2020+2021 `NOT-YET` on the same lone C3a — so the result does not
depend on the bench vintage either way.

## 5. What should happen next

1. **Solve PJM's same-HEAD in-sample control** (2023–2025 on the pjm-162 recipe). NEISO's is
   done and measured INERT (§4 i); PJM's is the one open limit on its touchpoints, and the
   verdict does not transfer across ISOs.
2. **Diagnose NEISO 2020's C3a as an object, on 2023–2025** (rule 22 step 3), starting from
   the compressed-diurnal-amplitude signature in §2.2. Do not tune to 2020.
3. **Repair the PJM 2020 demand feed** before any 2020 spend is requested — and note the fix
   is *not* simply tightening the 2.5× spike threshold, which would reach the two hours but
   not the seven-zone peak inflation behind them. That is its own data lane.
4. **Backfill PJM 2020's `calibration_reference` block and renewable-capacity file** — pure
   prep, unrestricted, no marker.
5. **Do not read any number here as out-of-sample skill.** Validation tier is iterable
   model-SELECTION evidence by construction. The locked test (2019 / H1-2026) remains
   never-granted for both ISOs and is untouched.
