# ADDENDUM — miso-251 RUNG-2020 shard: phase-0 heartbeat, written BEFORE the first LP

```
SHARD           : RUNG-2020
SESSION         : miso-251
BRANCH          : claude/miso251-tp2020
PINNED SHA      : dc57d4a29b374cb7897c1503bc4d4721aa568fb0
YEAR            : 2020        (Henry Hub $2.03)
KEEPER REPLAYED : 2026-09-09-miso-250-ep-gas  (results/calibration/miso_fuelvintage_A)
OUT-DIR         : results/calibration/miso251_tp2020
CHARTER         : docs/ADDENDUM-miso251-the-falsifiable-regime-test-2026-09-10.md §3
SIBLING         : RUNG-2021 on claude/miso251-tp2021 — never touched by this shard
```

**This document is pushed before the solve so the record cannot be written to fit the
result** (shard protocol §4, T+25 heartbeat; rule 29 `[R-SCREEN]` pre-registration).

---

## 1. Hard stops — all three PASSED, values as read

| # | check | value read | verdict |
|---|---|---|---|
| 1 | `git rev-parse HEAD` | `dc57d4a29b374cb7897c1503bc4d4721aa568fb0` | **PASS** |
| 2 | keeper `meta.json` `iso` / `years` | `MISO` / `[2023, 2024, 2025]` | **PASS** |
| 2 | `offer_curve_by_group.CC_REGULAR.committed` | `1.1055` | **PASS** |
| 2 | `offer_curve_by_group.CT_PEAKER.peak` | `4.4` | **PASS** |
| 2 | `summer_wefor_share_override` | `1.0599` | **PASS** |
| 3 | `parse_miso_shares(2020, zones)` | **`(6, 8760)`** — a real measured array, not `None` | **PASS** |

Hard stop 3 is the zonal-allocation repair the SCREEN shard landed for 2022
(`docs/RESULT-miso251-screen2022-2026-09-10.md`), confirmed live for 2020: this rung
solves on measured hourly zone shares, not flat sample averages.

Never pulled, never rebased, never synced. The tree is the pinned SHA exactly.

## 2. Environment — pins match the keeper's own `environment` block

`highspy 1.14.0 · numpy 2.4.6 · scipy 1.17.1 · pandas 3.0.3 · pyarrow 24.0.0 ·
pydantic 2.13.4` — read from `results/calibration/miso_fuelvintage_A/meta.json`
and installed, not copied blindly. Swap provisioned (15.7 GiB RAM + 8.0 GiB swap);
`MALLOC_ARENA_MAX=2`, `MARKET_SIM_HIGHS_THREADS=1`, `OMP_NUM_THREADS=1` exported for
the solve. `capacity-deliverability` clean partition rebuilt (MISO 776 rows).

## 3. The declared input degradation — the ONLY config delta

```
--set miso_measured_reserve_requirements=false
--set miso_reserve_online_gated=false
```

Identical to the 2022 rung's, forced by the same purged source and for the same
reason: MISO published **no** ASM record before 2023 (`docs.misoenergy.org` retains a
rolling ~3.5-year window; the 2026-07-31 intake's authoritative 5,481-request sweep of
2018–2022 found **0 days published**, and the documented Data Exchange fallback needs
`MISO_PRICING_API_KEY`, absent from both environment and repo). The loader hard-errors
rather than falling back silently, and `miso_reserve_online_gated` is its hard
dependent. The run therefore uses **MISO's own published static RBDC construction** —
the construction a FORECAST year uses — so rule 13 `[R-MEASURED]`'s forward test is met
by construction. Not a lever, not tuned, not swept. 2023–2025 are untouched.

## 4. Scope limit, stated up front — this rung CANNOT read plain CALIBRATED

`actual_lmp.json` carries **no MISO block before 2022**, so **C3a, C3b and C3c are
UNSCORABLE on 2020**. An unscored load-bearing criterion downgrades, so this rung reads
`CALIBRATED-WITH-CAVEATS` at best on `unscored criteria`. **That is a fact about MISO's
LMP retention, not a model result**, and it is reported as such wherever it appears.
What 2020 CAN say is C1 (its `calibration_reference.json` MISO 2020 block is present —
`coal 202.1613`, `gas_cc 151.0141`, `gas_ct 30.7925`, `gas_st 29.5298`, `nuclear
95.1076`, `wind 72.7669`, `hydro 11.2703`, `oil 4.7807`, `solar 2.563` TWh), C2, C4 and
C8 — and **C1 is the criterion the §3 prediction is made on**, so the test is answerable
on exactly the evidence this year carries.

## 5. The pre-registered prediction this shard tests (charter §3, NOT restated to fit)

2020's Henry Hub is **$2.03** — essentially inside the $2.19–3.52 regime the keeper's
offer bands were identified in, where the keeper's own coal residual runs **−5.77
(2023) / −9.18 (2024) / −10.66 (2025) TWh**, i.e. coal *light*. 2022's $6.45 is 1.8×
outside it and coal ran **+50.46 TWh** heavy.

* **H1 (regime-bound) predicts:** `|coal residual| < 15 TWh` on 2020, of the same
  (light/negative) sign.
* **H1 IS FALSIFIED IF** 2020 returns a coal excess `> +20 TWh` at $2.03 gas — which
  would mean the recipe fails out of sample *generally*, not just out of regime.

The reported number is `coal residual = (model − actual)` summed over `COAL_PRB +
COAL_BIT + COAL_LIGNITE`, from the C1 records of `calibration_verdict.py`.

**This shard reports the number and does NOT adjudicate the hypothesis.** The gate is
STOP-only (rule 29 `[R-SCREEN]`): it can kill the fuel-regime explanation, it cannot
promote anything, it contributes to no determination, and **nothing is tuned, cut or
swept against it either way** — whatever the number turns out to be.

## 6. Rule 30(c) — this rung cannot move MISO's headline

MISO's determination is the train-tier 2023–2025 verdict and nothing else. A held-out
year is iterable model-SELECTION evidence: it cannot certify and it cannot decertify.
Since `[R-HOLDOUT]` was removed (2026-09-09) that is true of every year.
