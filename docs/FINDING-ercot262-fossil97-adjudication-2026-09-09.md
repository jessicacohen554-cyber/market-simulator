# FINDING — ercot-262 (fossil gas offer bands ×0.97): ADJUDICATED, **DO NOT PROMOTE**

> Adjudication of the five solved arm bundles against the incumbent keeper
> `2026-09-09-ercot261-corroborated-gas-level`. Zero LP spent: every number below is read
> from committed artifacts (the arm bundles' `hourly/system_<year>.parquet` +
> `run_config.json`, the keeper's committed sidecars, and the keeper's own registered
> verdict via `scripts/calibration_verdict.py --run-id … --json`).
>
> PRECOMMIT: `docs/PRECOMMIT-ercot262-fossil-offer-97-2026-09-09.md`.

## 1. Verdict

**NOT a recommended keeper.** Every gate is clean and nothing FAILs that did not already
FAIL — but the arm's improvements land **entirely in the two validation-tier years, which
rule 30(c) forbids from gating**, while **all three training-tier years degrade**. The
determination does not move, and the arm misses its own target of record.

## 2. The premise defect — why this was not visible before the solve

The PRECOMMIT's **P1** reads: *"All five years currently over-price (2021 +4.2 %, 2022
+9.8 %, 2023 +24.3 %, 2024 +15.1 %, 2025 +4.0 %), so a uniform band cut is directionally
right everywhere."*

**That is true on the bench `avgLMP.rt` equal-hour basis, and false on the basis C3a is
actually scored on.** `score_price_mean`'s v2.4 basis ladder scores 2023–2025 against a
**load-weighted** actual; only 2021/2022 fall through to the LEGACY equal-hour basis. The
registered keeper verdict states the scored actuals directly:

| year | basis the scorer used | actual | keeper model | keeper C3a |
|---|---|---|---|---|
| 2021 | LEGACY equal-hour | 148.19 | 154.42 | **+4.2 %** |
| 2022 | LEGACY equal-hour | 62.30 | 68.40 | **+9.8 %** |
| 2023 | load-weighted | **64.32** | 60.12 | **−6.5 %** |
| 2024 | load-weighted | **30.99** | 30.89 | **−0.3 %** |
| 2025 | load-weighted | **36.29** | 33.81 | **−6.8 %** |

So the three training years were **already under-priced** before the arm. A uniform 3 % cut
moves them further below actual — the opposite of the intended direction. The equal-hour
bench numbers the PRECOMMIT quoted for those years (+24.3 / +15.1 / +4.0 %) are not the
numbers C3a gates on.

The load-weighted actual exceeds the equal-hour actual in every year (independently
reproduced from `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`: 2021
148.19 → 162.90, 2022 62.30 → 71.75, 2023 48.36 → 61.97, 2024 26.82 → 28.78, 2025
32.49 → 33.64), because ERCOT scarcity coincides with high load. That is the whole effect.

## 3. C3a — arm vs keeper, on the scorer's own actuals

The model side reproduces the registered keeper **to the cent** (60.12 / 30.89 / 33.81),
so these arm figures are on the scorer's basis, not a proxy.

| year | tier | actual | keeper | arm | keeper C3a | arm C3a | move |
|---|---|---|---|---|---|---|---|
| 2021 | validation | 148.19 | 154.43 | 153.84 | +4.21 % | **+3.81 %** | BETTER |
| 2022 | validation | 62.30 | 68.40 | 67.71 | +9.79 % | **+8.68 %** | BETTER |
| 2023 | **TRAIN** | 64.32 | 60.12 | 59.15 | −6.53 % | **−8.04 %** | **WORSE** |
| 2024 | **TRAIN** | 30.99 | 30.89 | 30.46 | −0.32 % | **−1.72 %** | **WORSE** |
| 2025 | **TRAIN** | 36.29 | 33.81 | 33.27 | −6.85 % | **−8.32 %** | **WORSE** |

All ten rows stay inside the ±10 % band, so **no C3a row flips PASS → FAIL** — but the
training tier, which is the only tier that sets ERCOT's determination (rule 30(c)), moves
away from actual in all three years, and 2023/2025 now sit within 2 pp of the failing edge.

## 4. The target of record — P4 REFUTED

C3b-2021 (NRMSE 0.238 against a 0.20 gate) is the incumbent's **only** failing criterion
and the arm's stated purpose. Reproduced exactly on the scorer's basis (my calc returns the
registered 0.238 / 0.099 for 2021 / 2022):

```
C3b 2021   KEEPER 0.237987   ARM 0.238363   delta +0.000376  (marginally WORSE)
```

**It does not improve — it degrades slightly.** Cause, from the monthly decomposition:
February 2021 (Uri) is the one **under**-priced month (model 1422.13 vs actual 1521.84,
−101.10) and its magnitude dominates the RMSE, so a uniform cut moves the dominant term
further from actual while shaving the smaller over-priced months. A level multiplier cannot
reach this object; the residual is a **shape** defect concentrated in one extreme month.

The five-year determination therefore stays **NOT-YET on `price_shape` alone**, exactly as
the incumbent already reads, and ERCOT stays **CALIBRATED** on the train tier either way.
The arm unlocks nothing.

## 5. Pre-registered gates — all clean (the arm is not disqualified, merely pointless)

| id | gate | result |
|---|---|---|
| **G-1** | no `phys_*` / `econ_low_share` / `pct_peaking` drift | **PASS** — 0 violations over 5 years |
| **G-2** | no non-gas class in the resolved curve | **PASS** — 8 gas classes, no COAL |
| **G-3** | every band = keeper × declared factor (≤1e-6) | **PASS** — 160/160 bands exact |
| **G-4** | dump MWh > 1.0 in any year | **PASS** — 0.0 MWh in all five (keeper likewise) |
| **G-5** | load-bearing PASS → FAIL in 2023/2024/2025 | **PASS** — none |

Carve-out/forward legs resolve correctly: `ercot_offer_swcap_clip` true for 2021/2022/2023,
false for 2024/2025.

## 6. Directional predictions

| # | prediction | outcome |
|---|---|---|
| P1 | every year's LMP falls | **CONFIRMED** (−0.38 % to −1.61 %) |
| P2 | −2 % to −6 % on annual LW LMP | **MISSED** — delivered −0.38 % to −1.61 %, well under the band |
| P3 | 2023 improves most; 2025 risks overshooting negative | **half** — 2023 largest absolute move (−0.97 $/MWh); 2025 does **not** overshoot |
| P4 | C3b-2021 improves to 0.20–0.235 | **REFUTED** — 0.238 → 0.238 (+0.000376, worse) |
| P5 | C3c 2021 falls to 195–220 h | **REFUTED** — unchanged at 223 h; only 2023 moves (180 → 178) |
| P6 | C1 shifts toward gas, coal lighter | **CONFIRMED** — COAL_PRB −0.35 / −0.73 / −0.78 / −0.32 TWh (2021/23/24/25) |

On P6: coal moves **away** from actual in 2021/2023/2024 (already light) and toward it in
2025 (heavy). C1 does **not** flip — every coal row stays far inside its ±8.00 TWh band —
but three of four years get worse. Reported at full magnitude, gating neither way.

## 7. What this does and does not say

It does **not** say the authorized price-tuning channel is wrong, and no rule-1 `[R-STRUCT]`
condition was breached: the multiplier was owner-set, declared ex ante, year-invariant,
never swept, and ledgered. Conditions (a)–(e) all hold. The arm is **governance-clean and
substantively inert-to-negative**.

What it says is that **ERCOT's remaining price residual is not a level residual.** On the
scored basis the level is already good in the training tier (2024 is −0.3 %), and the open
object is C3b-2021 — a single-month shape defect at Uri. A uniform band multiplier is the
wrong instrument for it, in either direction.

## 8. Disposition

- **Not promoted.** The incumbent `2026-09-09-ercot261-corroborated-gas-level` stands.
- **Not registered** on the dashboard: the arm changes no determination and rule 15's
  retention is keeper-only, so registering it would add a card that is pruned at the next
  promotion. Its numbers live here and in git history — the same delete-not-archive
  discipline rules 15/29 already state.
- **Bundles retained on local disk** per rule 31 `[R-RETAIN]` pending the owner's ruling;
  they are gitignored apart from the slim sidecars already merged to `main`.
- **Successor object** for the next ERCOT calibration session: **C3b-2021, the February
  under-price**, not the annual level. See §9 of the handoff.
