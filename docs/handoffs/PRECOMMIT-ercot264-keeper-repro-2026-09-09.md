# PRECOMMIT — ercot-264: five-year keeper reproduction at HEAD on the repaired benchmark basis

**Session:** ercot-264 (continuation of ercot-263), 2026-09-09. Branch `claude/ercot264-keeper-repro`.
**Base:** `origin/main` at session time. **Keeper:** `2026-09-09-ercot261-corroborated-gas-level`.
**Owner instruction:** *"Do a run"* / *"run all years including holdouts."*

---

## 1. What is being solved, and why it is not a fitted arm

**The keeper's own recipe, byte-faithful, across all five years 2021–2025.** Zero deltas: no
`--set`, no `ScenarioConfig` override, no new mechanism, no new parameter. `replay_keeper.py`
reconstructs the 288 kwargs from the bundle's own `meta.json`.

**There is nothing here to select on**, so rule 1 `[R-STRUCT]`'s fitted-mechanism concern does not
attach: an arm with no free parameter and no alternative cannot be chosen because it moved a
residual. This is a **verification** run.

**Why it is worth the LP** — three things the committed artifacts cannot answer:

1. **HEAD drift.** `check_bench_freshness` reports **22–26 engine commits** under
   `src/market_sim/data|config` since the ERCOT bench parts were committed. Those can move the
   plant→class map, the CHP shares and the EIA-923 reconciliation. Nobody has re-solved ERCOT at
   HEAD. **If the keeper no longer reproduces, that is a finding and it is the point of the run.**
2. **The committed bundle is SLIM.** `results/calibration/ercot261_five_year_keeper` carries
   `hourly/` but **no root `system.parquet`, no `dispatch/`, no `floors/`** — the heavy parquets
   were pruned. The payload therefore cannot be re-rendered from it. A full bundle restores that.
3. **First fresh solve on the repaired basis.** ercot-263 re-scored the committed payload; this
   scores a freshly solved one.

## 2. Phase 0 (rule 29) — already spent, and it is why this is a reproduction and not a mechanism

ercot-263's phase 0 established, at zero LP, that the 2021 C3b residual is **95.7% February**, that
its cause is the corroboration filter replacing Feb-2021's `+54.376 $/MMBtu` measured basis with
`+0.390`, and that **all three repair routes are closed**: the raw monthly basis is ercot-254
(refused under rule 1 — C3c 234 → 688 h vs 258 actual), the offer-band scale is ercot-262 (±0.004),
and the correct daily-basis repair is **un-armable for lack of data**. Re-confirmed this session:
no Waha, HSC, or ERCOT fuel-index daily file exists anywhere under `data/raw` — the daily hub series
on disk are Algonquin, CAISO citygate, MISO citygate, Transco Z6 and Henry Hub only.

**So no mechanism arm is available to solve.** The run that IS available is the reproduction above.

## 3. G-DRIFT (rule 29(b))

**Not applicable in its usual form, because drift is the measurand.** G-DRIFT exists to decide
whether the keeper's committed legs may stand as a control without a control solve. Here the
*experiment* is "does the keeper still reproduce at HEAD", so the committed legs are the
comparison by construction and **no control solve is spent** — 5 solves, not 10.

## 4. The recipe partition — three legs, and the shards must prove they got the right one

`meta.config_partition_overrides` (schema `composite-per-year-recipe/v1`) is machine-readable and
`enforce_single_recipe_partition` **refuses a mixed span**, so the span is solved one year per shard:

| years | leg | `ercot_offer_swcap_clip` | CC_REGULAR `peak` |
|---|---|---|---|
| 2021, 2022 | CARVE-OUT | `True` | **151.008** |
| 2023 | CARVE-OUT (+ `ercot_zonal_spread_ep_referenced: False`) | `True` | **151.008** |
| 2024, 2025 | FORWARD (base recipe) | `False` | **4.576** |

## 5. Holdout authorization (rule 22)

2021 and 2022 are **validation tier**; ERCOT holds the `complete` marker (declared 2026-08-31) and
the holdout freeze scopes to `locked_test` alone, so they are authorized and iterable and their
shards pass `--holdout-authorized`. 2023/2024/2025 are train tier and must **not** pass it.
**2019 and H1-2026 are FROZEN and are not solved, scored or registered here.** "All years including
holdouts" is therefore 2021–2025, which is exactly the keeper's registered span (rule 16
`[R-ALLYEARS]`).

## 6. SEALED PREDICTIONS — written before any solve

**P1 (reproduction).** Each year's freshly solved system price reproduces the committed keeper's
within tight tolerance. *Falsified if any year's annual load-weighted LMP moves > 1%.*

**P2 (scored rows).** On the repaired basis the fresh solve scores at or near
C3b {2021 0.559, 2022 0.172, 2023 0.097, 2024 0.122, 2025 0.106} and
C3a {2021 −6.7%, 2022 −8.1%, 2023 −6.5%, 2024 −0.3%, 2025 −6.8%}.

**P3 (determination).** NOT-YET on `price_shape` alone; train tier {2023,2024,2025} carries no
failure, so ERCOT stays CALIBRATED under rule 30(c).

**P4 (the honest alternative).** **If HEAD has moved the keeper, P1/P2 are falsified and the run's
value is the drift measurement, not a promotion.** I commit in advance to reporting a drifted result
at full magnitude rather than treating it as a failed run, and to NOT hunting for a config that
restores the old numbers — that would be fitting to a remembered residual.

**P5 (promotion).** A byte-faithful reproduction is **not automatically a new keeper**: same recipe,
same id lineage. It is promotable only if the owner wants the refreshed full bundle to become the
registered artifact. **The owner's standing rule — structural integrity up, gates down may still be
a keeper — is noted and will be applied to whatever comes back, but the session will not promote
without the owner's word.**

## 7. Rule 31 `[R-RETAIN]`

Every shard bundle is **gitignored, never `rm`'d**. Nothing is deleted before the owner rules on
promotion. The promotion question goes to the owner explicitly before the session ends, with the
statement that the bundles live on ephemeral container disk.

## 8. Shard hard-stop conditions (each shard checks these itself)

1. `git rev-parse HEAD` equals the pinned 40-char SHA.
2. Its `run_config.json` shows the **leg from §4** for its year — a shard that sees otherwise STOPS
   and does not push.
3. 2021/2022 pass `--holdout-authorized`; 2023/2024/2025 do not.
4. A shard **never** runs `dashboard_add_run.py`, `build_manifest.py`, `build_status.py`, or touches
   `frontend/data/backcast/**`; **never** edits anything under `src/` or `scripts/`; **never** uses
   `git add -A` or `git add .`. On any blocker it STOPS and reports rather than repairing.
