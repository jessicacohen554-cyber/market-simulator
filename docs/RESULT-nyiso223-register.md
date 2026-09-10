# RESULT — nyiso-223 shard `nyiso223-register`: 4-year hub gap-fill composite

**Date:** 2026-09-10 · **ISO:** NYISO · **Shard:** `nyiso223-register` (registration shard)
**Pinned SHA:** `7689d59ad5ef1343e44c3dae3544e7f8bba415c5`
**RUN_ID:** `2026-09-10-nyiso-223-gapfill-span`
**Bundle:** `results/calibration/nyiso223_gapfill_span/` (gitignored family; slim set force-added)

## 1. What was solved

The designated NYISO keeper recipe (`nyiso_fuelvintage_A`, run
`2026-09-09-nyiso-221-fuelvintage-span`) replayed with **one** registered field added:

```
--set nyiso_hub_gap_month_level=true
```

A calendar day the measured Transco Z6 NY archive never priced takes the month's own
observed level instead of the nearest print's clamped deviation. Zero free parameters,
exactly mean-preserving. Solved across **every year NYISO can score** — 2022, 2023, 2024,
2025 — in ONE invocation, ONE bundle, years sequential (rules 12 `[R-PARALLEL]` /
16 `[R-ALLYEARS]`).

## 2. Pre-solve gate (zero LP) — PASS, all four years

Reproduced the pre-registered footprint exactly before any LP was spent:

| year | annual mean | Dec-tail off | Dec-tail on | changed hours | verdict |
|------|-------------|--------------|-------------|---------------|---------|
| 2022 | 8.4431 | 8.049 | 8.949 | 4440 | MATCH |
| 2023 | 3.3566 | 3.919 | 3.683 | 4416 | MATCH |
| 2024 | 2.7969 | 3.877 | 4.061 | 5880 | MATCH |
| 2025 | 5.5602 | 7.256 | 7.256 | 6552 | MATCH |

## 3. Post-solve signature — PASS (7/7)

`nyiso_hub_gap_month_level` **true** · `offer_curve_by_group.CC_REGULAR.peak` **2.25** ·
`.pct_peaking` **8.0** · `nyiso_gas_commitment_bridge` **true** ·
`nyiso_dynamic_reserve_requirements` **true** · `meta.iso` **NYISO** ·
`meta.years` **[2022, 2023, 2024, 2025]**.

## 4. Determination (verbatim from `dashboard_add_run.py`)

```
RUN_ID=2026-09-10-nyiso-223-gapfill-span
DETERMINATION: NOT-YET [NYISO nyiso 223 gapfill span] — governance gate UNATTESTED: no governance attestation in bundle
```

Rubric v3.6. Grade summary: scored 7 · target_grade 3 · commercial_grade 0 · ledgered 0 ·
fails 4. Caveat ledger: **empty** — `protective []`, `ledgered []`, `commercial_band []`
(budgets protective_max 0, ledgered_max 1, neither spent).

**The determination basis carries exactly one line, and it is not a scored criterion:**
`governance gate UNATTESTED: no governance attestation in bundle`.

## 5. Scored criteria, per year

| criterion | tier | status | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| C1 fuel-mix by class | load-bearing | **FAIL** | **FAIL** CC_REGULAR +5.05 TWh, +3.8pp | PASS (7/7) | PASS (7/7) | SKIPPED — preliminary EIA-923 vintage |
| C2 system volume | load-bearing | PASS | PASS (gas; C1 flags CC_REGULAR) | PASS | PASS | SKIPPED −1.1% |
| C3a mean LMP | load-bearing | **FAIL** | **FAIL** −13.9% (69.82 vs 81.12) | PASS +4.4% (33.65 vs 32.25) | PASS +5.5% (40.22 vs 38.12) | PASS −7.1% (61.72 vs 66.43) |
| C3b price duration/shape | load-bearing | **FAIL** | **FAIL** NRMSE 0.245 | PASS 0.122 | PASS 0.182 | PASS 0.158 |
| C3c price tail / scarcity | supporting | **FAIL** | **FAIL** 10h vs 101h (0.10×) | **FAIL** 2h vs 10h (0.20×) | **FAIL** 0h vs 13h (0.00×) | **FAIL** 3h vs 42h (0.07×) |
| C4 dispatch correlation | supporting | PASS | PASS r=0.910 NRMSE 0.156 | PASS r=0.942 NRMSE 0.123 | PASS r=0.895 NRMSE 0.135 | PASS r=0.841 NRMSE 0.188 |
| C6 governance | protective | **UNATTESTED** | — | — | — | — |
| C8 forced-energy share | protective | PASS | PASS | PASS | PASS | PASS |

C3a/C3b tolerances: ±10 % target/commercial; NRMSE ≤ 0.20. C3c tolerance [0.5×, 2×] of
RT actual. D-10 free-class C1: **all 20/21 · free 14/15** (pinned, excluded from free:
CC_CHP, ST_CHP).

C1 2025 and C2 2025-gas are SKIPPED on the **preliminary EIA-923 vintage** (11/20, 12/17,
17/20, 3/10, 2/6 prior plants missing per class) — not gated; C2 family grid reconcile
covers those classes.

### Reported-only streams

C5a CO2 vs eGRID: 2022 **+1.6 %** · 2023 **+1.5 %** · 2024 **+0.4 %** · 2025 **+4.3 %** (all PASS,
reported-only since v2.9 — contributes no status, caveat or determination).

D-A diurnal amplitude (band-free): 2022 62.7 % of measured (r +0.866) · 2023 61.2 % (r +0.922) ·
2024 52.6 % (r +0.889) · 2025 41.8 % (r +0.881); phase OK in all four years.

## 6. Model annual mean LMP — sibling-shard cross-check, ALL FOUR AGREE

The expectation list mixes **one load-weighted** figure with **three simple** means. Once
that is accounted for, every value reproduces exactly and there is **no disagreement**:

| year | simple mean | load-weighted | expected | basis that matches |
|------|-------------|---------------|----------|--------------------|
| 2022 | 65.1949 | **69.8215** | 69.8215 | load-weighted ("LW", as labelled) |
| 2023 | **32.3600** | 33.6521 | 32.3600 | simple |
| 2024 | **38.7081** | 40.2188 | 38.7081 | simple |
| 2025 | **58.5074** | 61.7227 | 58.5074 | simple |

Note the scorer's C3a operand is the **load-weighted** mean, so the C3a column in §5 quotes
33.65 / 40.22 / 61.72 for 2023–2025, not the simple means above. Both are stated so neither
is mistaken for the other.

## 7. The one blocker: C6 UNATTESTED

`replay_keeper.py` does not write `calibration_attestation.json`, and there is **no generic
writer** — every attestation in this repo comes from a bespoke, hand-authored
`scripts/gen_<session>_attestation.py` that declares that run's DOF ledger (rule 21
`[R-DOF]`) and its `authorized_price_tuning` block (rule 1 `[R-STRUCT]` condition (e)).

This shard did **not** author one, for two reasons, and both are deliberate:

1. Creating `scripts/gen_nyiso223_attestation.py` is an edit under `scripts/`, forbidden by
   name in this shard's brief (rule 32 `[R-SHARD]` (c)6).
2. Attesting is a governance act. A shard fabricating a governance attestation to clear a
   protective gate is precisely the "shard that repairs infrastructure is a FAILURE" case.

**The parent owns this seam** (rule 32 `[R-SHARD]` (d)). The run is registered and every
number above is final; only the attestation is outstanding.

## 8. Reading of the result (this shard's assessment, not a scored output)

The failing set is **concentrated in 2022**, the newly-added year. 2023/2024/2025 are clean
on every load-bearing criterion — C1, C2, C3a, C3b all PASS — and their only miss is C3c,
which rule 22 `[R-C3C]` makes an auto-ledgered, non-downgrading caveat when it is the lone
failure and governance passes. 2022 is what carries the C1 / C3a / C3b failures (CC_REGULAR
+5.05 TWh; mean LMP −13.9 %; NRMSE 0.245).

Stated plainly so it is not over-read: with an attestation in place the run as a whole would
still read NOT-YET, because C3c is **not** the lone failure across the composite. The
observation is about **which year** drives the fails, not a claim that the run passes.

## 9. Promotion question — UNRESOLVED, and the artifacts are perishable (rule 31 `[R-RETAIN]`)

The full 164 MB bundle sits on **local disk only** and is **gitignored**
(`.gitignore:1759`, `results/calibration/nyiso223_gapfill_*/`). This container is ephemeral:
the heavy `dispatch/`, `system.parquet`, `storage.parquet`, `flows.parquet` and the
`unit_hourly_*` / `network_*` sidecars **will not survive session reclamation**. Committed
here is only the ~6.9 MB slim set.

Nothing has been deleted (rule 31 `[R-RETAIN]`). **The owner has not ruled on promotion.**
Re-solving this span costs ~16.5 min of LP (992.6 s measured). Per rule 31's
surface-before-the-session-ends duty, the question is asked here explicitly rather than
left unasked.

## 10. Solve wall-clock

| year | data_prep | solve_p0 | markup | solve_p1 | results_write | **total** |
|------|-----------|----------|--------|----------|---------------|-----------|
| 2022 | 35.1 s | 100.7 s | 4.8 s | 92.4 s | 7.9 s | **240.8 s** |
| 2023 | 11.1 s | 100.1 s | 5.0 s | 97.8 s | 7.9 s | **221.8 s** |
| 2024 | 9.9 s | 129.8 s | 4.7 s | 133.1 s | 7.9 s | **285.4 s** |
| 2025 | 10.4 s | 111.8 s | 4.6 s | 109.9 s | 7.9 s | **244.6 s** |

Total **992.6 s ≈ 16.5 min** (04:26:01 → 04:42:52 UTC). Peak RSS 5.94 GB (2023).

## 11. What this shard did NOT do (parent's seam, rule 32 `[R-SHARD]` (d))

`build_status.py` · `prune_iso_runs.py` · `stamp_touchpoint_holdout.py` ·
`frontend/data/backcast/keepers/NYISO.json` · `calibration-complete.json` · any edit under
`src/` or `scripts/` · any PR · any deletion of a result.
