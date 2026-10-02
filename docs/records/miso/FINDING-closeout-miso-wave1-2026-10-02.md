# FINDING — closeout-MISO wave 1: tail derived (C3c 2019–21 scored), L3/L4 coal continuum and the R-3 fall-2021 take ceiling both fail their zero-LP gates. No PRECOMMIT, no solve; keeper unchanged.

```
LANE     : closeout-MISO wave 1 (desk charter 2026-10-02, docs/backcast-closeout-plan-2026-10.md §3.3; rulings R-3, R-15)
KEEPER   : 2026-09-28-miso-280-splitremap (results/calibration/miso280_span), unchanged
LP       : none (fleet-only rebuilds, the miso-297 bid stack, the miso-288/289/290 dual emulator)
PROBES   : scripts/probes/_closeout_miso_l3l4_census.py      -> results/phase0/miso/_closeout_miso_l3l4_census.json
           scripts/probes/_closeout_miso_r3_ceiling_census.py -> results/phase0/miso/_closeout_miso_r3_ceiling_census.json
CELLS    : coal_econ_two_sided U -> R; coal_prb_committed_dispatchable R, coal_prb_committed_split R (retested on the
           miso-296/297 evidence, stay R); coal_fuel_inventory K (evidence added). MISO shard only (rule 28).
```

## 0a. Actual RT tail 2019–2021 (step 0a)

`scripts/data/derive_actual_tail.py`, unchanged, on the committed hub series (`actual_lmp_hourly_MISO.parquet`, 94c1be04).
RT > $200: **2019 17 h, 2020 8 h, 2021 48 h** (coverage 1.0; DA 0 / 0 / 44). Only MISO rows changed in `actual_tail.json`.
Keeper rescored (`calibration_verdict.py --write-metrics`, `build_status.py --iso MISO`, rubric v3.13):

| criterion | before | after |
|---|---|---|
| C3c 2019 | SKIP | **CAVEAT** (0 vs 17 h, model-class) |
| C3c 2020 | SKIP | **PASS** (small-count \|Δ\| = 8 ≤ 10) |
| C3c 2021 | SKIP | **CAVEAT** (0 vs 48 h, model-class) |
| everything else | — | unchanged |

Determination **NOT-YET before and after** (C1 ST_GAS 2019, C3a 2020, C3b 2021). Exactly the plan pre-read.

## 0b. Max Gen registry transcription — DEFERRED

Waits on the owner's OATI PDF (R-15); desk update 2026-10-02: no owner downloads today, the post-W0 span runs without
it and 0b becomes a later hygiene input.

## 2. L3 + L4 census (C3a 2020, +11.6 %)

Gate (plan §3.3 step 2, stated before this lane): ≥ −$1.0/MWh at q1–q4 in 2020 **and** COAL_PRB 2019/2021/2022 inside
the ±8 TWh C1 band (static × 0.27 LP conversion, miso-224/225).

MISO incremental/average HR ratio (frozen `derive_coal_incremental_hr_ratio.derive("MISO")`, output to scratch only —
the derive is SOCO-scoped and nothing under `data/` was written): pooled 0.898 (econ_low) / 0.923 (econ_high); 2020
cap-weighted PRB 0.913/0.946, BIT 0.872/0.875, LIGNITE 0.852/0.850.

| arm (2020) | coal share all / q1–q4 (IMM 0.40) | ΔP q1–q4 lw mean | PRB 2019 / 2021 / 2022 (LP-conv.) | gate |
|---|---|---:|---|---|
| KEEPER | 0.254 / 0.199 | 0 | 6.40 / 5.68 / 5.28 | — |
| L3 (registered two-sided, replaces band mult.) | 0.365 / 0.328 | −1.24 | **10.29 / 8.54** / 6.06 | FAIL (PRB) |
| L3flag (committed + econ) | 0.371 / 0.330 | −1.33 | **10.80 / 8.97** / 6.22 | FAIL (PRB) |
| L3stack (on the band multiplier) | 0.301 / 0.248 | −0.44 | 7.10 / 6.32 / 5.56 | FAIL (price) |
| L4a (cycling slice, spot share literal) | 0.248 / 0.200 | −0.20 | 7.08 / 6.12 / 5.33 | FAIL (price) |
| L4b (cycling slice, swing ton at spot) | 0.406 / 0.371 | **+0.88** | 4.54 / 5.36 / 5.32 | FAIL (price) |
| L3+L4a | 0.370 / 0.329 | −1.39 | **10.96 / 9.05** / 6.18 | FAIL (PRB) |
| L3+L4b | 0.508 / 0.481 | −0.36 | 7.75 / 7.92 / 6.14 | FAIL (price) |

Reading: the arms that reach the price do it by re-meriting PRB energy that 2019/2021 already carry at the band edge;
the form that reaches the IMM coal share (L3+L4b) prices the cycling slice at $24–27, not the ~$15 real margin, so
the low-load price barely moves. L4 replaces the take-or-pay discount on the slice (rule 19) and differs from miso-102
`sunk_fixed` (whole committed band at average HR × 1.1, no split). The keeper reproduction is exact for 2019–2022 and
within $0.5 for 2023–2025 (drift unexamined; all deltas are against this run's own KEEPER). The two R cells stay R.

## R-3. Fall-2021 take ceiling (C3b 2021, 0.201)

Form declared before any price: per keeper yard, `C[y,m] = R_meas[y,m] + max(0, S_meas[y,m−1] − S_min[y])` (EIA-923
Page 5 receipts at lot heat content; Sch. 2 stocks; `S_min` = miso-289's prior-years `d_min` identification, not
searched). Rule 19: it **replaces** the pooled B/12 limb and the per-yard annual rows. Ex-ante kill rules (probe
docstring): K1 binds Sep–Nov 2021; K2 near-slack Jun–Aug 2021; K3 no static C3a/C3b gate crossing in any year; K4
≤ 1.5 TWh off keeper P1 where it does not bind. Emulator INC 2022 reproduces miso-290 INC exactly (51.45 / 235.29 TWh).

| | result |
|---|---|
| K1 fall 2021 | PASS — 22/28/25 yards bind Sep/Oct/Nov; coal −1.72 TWh vs INC (Sep–Nov 64.7 vs bench 56.9) |
| K2 summer 2021 | FAIL on rows (11/15/20 bind Jun–Aug); removing B/12 releases +8.9 TWh summer coal (82.1 vs bench 79.8) |
| C3b 2021 (static overlay) | **0.201 → 0.189** (Sep–Nov SSE −15 %); C3a 2021 −5.6 → −9.0 % |
| K3 | **FAIL** — C3a 2019 +8.7 → +11.5 %; C3a 2022 −5.1 → −15.8 %, C3b 2022 0.122 → 0.220 (2022 coal +42.5 TWh vs INC without B/12) |
| K4 | vacuous (every year-month binds ≥ 2 yards) |

Two structural reasons, not a tuning question: (i) measured stocks fell below the declared `S_min` in many
yard-months (2019 Mar 26 yards; 2021 Jul/Aug 9–10), so where the envelope binds it is close to a pin of measured burn
(`C − burn = S[m] − S_min`) — the rule-13 "never the burn" line; (ii) non-cumulative, it re-offers the whole
above-`S_min` pile every month, so it is loose in aggregate and can only replace B/12 by releasing summer and 2022 coal.
The tightening (cumulative `S_dec − S_min + ΣR`) is the measured-receipts pile, the bank family killed in miso-287…290.
Keeping B/12 alongside it stacks two limbs on one phenomenon (rule 19). **No PRECOMMIT.** Fall-2021 conservation stays
on the ledger (plan §3.3 ledger row).

## Hygiene

The keeper bundle carries no `unit_marginal_<Y>.parquet` (rule 15); the next full span writes it (required for any
promotion).

## Step 3 — the span

Held until W0 (`claude/closeout-b-w0-foundation`) merges and the desk releases. Nothing from wave 1 passed, so the span
carries no new MISO lever: it would be the keeper recipe on the post-W0 foundation (W0 re-solve), writing
`unit_marginal_<Y>`, with 0b deferred.

## Where MISO stands

Full span NOT-YET on C1 ST_GAS 2019 (routed, R-15), C3a 2020 (no admissible lever clears its census; honest ceiling
≈ +7 % with West/Plains congestion G), C3b 2021 (Uri routed; the R-3 form fails K3). C3c 2019/2021 ledgered
model-class caveats, 2020 PASS. Train 2023–2025 CALIBRATED.
