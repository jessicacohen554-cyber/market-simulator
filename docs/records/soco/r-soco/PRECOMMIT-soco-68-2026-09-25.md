# PRECOMMIT — soco-68: `summer_derate_basis_aware` on the SOCO keeper recipe, 2019–2025

Lane soco-68, 2026-09-25. This document was written and pushed **before any shard was launched**. The parent
solves nothing (rule 32(a)). Each year is solved in its own shard (rule 36), and each shard pushes its full bundle
(rule 34). The evidence is in `FINDING-soco-68-2026-09-25.md`.

## 1. Lever

**The field.** `summer_derate_basis_aware` is an **existing** registered `ScenarioConfig` field (miso-148, MISO
cell `K`). It is default off, sits in `_CACHE_KEY_OPTIONAL_FIELDS`, and is dropped at `"False"`. It already has a
matrix row. SOCO's cell is `U`. No code changes.

**The construction.** On `plant_level_fleet`, the flat `SUMMER_CLASS_DERATE` (CC_REGULAR / CC_CHP 10 %,
CT_PEAKER / CT_CHP 12.5 %) is suppressed Jun–Sep for plants whose LP pmax **is** the published EIA-860
net-summer rating (`fleet.summer_basis_measured_plants`). It is kept for plants the always-on CC guard clipped
onto nameplate and for plants absent from EIA-860.

**Why this lever and not the routed "capability basis".** The per-plant decomposition (FINDING §1) splits the
plant-grain CC excess into two parts:

- **CEMS above LP pmax (basis):** 0.2–0.6 TWh a year.
- **CEMS within pmax but above availability:** 5.5–8.4 TWh a year.

The largest identified, parameter-free part of the second channel is this double count (FINDING §2). The basis
cells `cc_winter_capability_basis`, `cc_nameplate_summer_derate` and `cc_summer_derate_reconciled_basis` act only
under `cc_nameplate_summer_derate`. That is a different capacity construction, which would re-base every CC plant to
nameplate and drop the statistical POF / WEFOR for CC. It is not the minimal repair of the measured defect.

**Rule check:**

| rule | how this lever meets it |
|---|---|
| 19 | It replaces a double application of one ambient loss. It does not add a second mechanism. `cc_capacity_reconcile_path` (the guard-clipped plants) is routed, not stacked. |
| 14 | The model's summer ceiling sits below measured summer output in 12,600–17,400 CC plant-hours a year. |
| 13 | It regenerates from any EIA-860 vintage. It is not a measured overlay, and it is forecast-valid. |
| 21 / 24 | Zero free parameters. It is a boolean over a data predicate, on a registered field. |
| 25 | SOCO's own census. MISO's `K` fills no SOCO cell. |

**Not a re-test of any `R`/`I`/`G` cell.** `tranche_startup_amortization` stays `G`, pending the SOCO-65 §4
owner question. The `offer_curve_by_group` bands are not a lever here, because SOCO has no price reference.

## 2. Census (zero LP, fleet rebuilds on the keeper recipe; FINDING §3)

- **G-DRIFT against `b2397ae0`: all INERT.** Every LP input, labels included, is bit-identical in all seven
  years. The committed `soco67_span` bundle is the control.
- **The arm moves only `availability`**, on 167–172 units a year, in Jun–Sep only. `pmax`, `mc` and the unit ids
  are byte-identical.
- **Class availability moves by:** CC_REGULAR +2.88…+3.56 TWh, CT_PEAKER +3.20…+3.38, CC_CHP +0.08…+0.12, and
  CT_CHP +0.05.
- **Mechanism log (`basis-aware summer derate (SOCO)`):** 168–174 units suppressed. 13–23 units are kept, at
  plants {6073, 7897, 55382, 57037} plus 3 / 533 / 643 / 54730 / 54880 by vintage.

## 3. Recipe

Each shard runs one year, `<Y>` ∈ {2019, …, 2025}, pinned to the SHA that carries this document. The shard pins
it itself as step 0:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
python3 scripts/hydrate_data.py --profile soco
PYTHONPATH=. python3 scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. python3 scripts/data/curate_demand_profile.py
python3 scripts/replay_keeper.py results/calibration/soco67_span --years <Y> \
  --out-dir results/calibration/soco68_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true \
  --note "soco-68 <Y>: soco-67 keeper recipe + summer_derate_basis_aware (flat summer class derate suppressed on net-summer-rated plants; rule 19)"
```

**Hard stops. A shard that sees otherwise stops and does not push.**

- `git rev-parse HEAD` equals the pinned SHA.
- `run_config.json` `scenario_config` shows the seven `--set` fields true.
- Every band is 1.0.
- `dispatch/<Y>_P1.parquet` is present.
- `gas_prices[<Y>]` equals the keeper's value (2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52).
- The solve log contains `container preflight:` and `memory peak:`.
- The solve log contains `basis-aware summer derate (SOCO): flat _SUMMER_CLASS_DERATE SUPPRESSED for`.

## 4. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

These are measured against the keeper's committed legs (`soco67_span`) and anchored on the FINDING §3 greedy
estimate.

- **E1 (every year, direction and size).**

  | class | expected Δ, TWh |
  |---|---|
  | CC_REGULAR | +0.8 to +3.0 |
  | CT_PEAKER | −0.4 to −2.2 |
  | COAL_PRB + COAL_BIT | 0 to −1.5 |
  | ST_GAS | ≤ 0.5 in magnitude |
  | every other class | ≤ 0.3 in magnitude |

  Solved CC_REGULAR energy stays ≤ its armed availability.
- **E2 (2023 C1).** CT_PEAKER moves from +5.95 TWh / +2.5 pp to between +3.8 and +5.6 TWh, which is about
  +1.6 to +2.4 pp. The 2023 margin widens and stays PASS.
- **E3 (C1 status).** No C1 row changes status in any year. The keeper passes every scored row, and the greedy
  keeps every row in band:
  - 2023 COAL_PRB goes about −1.6 → −2.4 TWh.
  - 2021 CT_PEAKER goes about −1.5 → −2.3 TWh.
  - The 2019–2022 CC_REGULAR under-dispatch (−3.5 … −6.5 TWh) narrows.
- **E4 (unserved).** Unserved stays 0 MWh in 2019–2024. 2025 falls from 813.8 MWh or stays equal. Summer CC and
  CT capacity only rises.
- **E5 (other criteria).** C2, C4, C6 and C8 PASS in every year. C3a/b/c stay UNSCORABLE. `gen_soco60b` B1/B2
  are unchanged, because they are benchmark-side.

## 5. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff** all three of these hold:

- All seven legs solve cleanly with the §3 hard stops met.
- Every leg's log shows the basis-aware line. Its kept-plant set is a subset of the plants the CC nameplate
  guard clipped plus plants absent from the solve-year EIA-860, as in the §2 census.
- No year's unserved energy increases against the keeper.

This holds **whatever C1–C8 do**. The mechanism removes a double application of one ambient loss, which rules 19
and 14 require removed. Gate regressions, if any, are reported at full magnitude. The owner decides (rule 31), and
the owner's standing ruling is "if structural integrity improves but gates regress that may still be a keeper".

If the owner promotes, rule 35 prunes `2026-09-25-soco67-precod-clip`. The incoming run covers the full union
{2019, …, 2025}, the year set enumerated from every registered SOCO sidecar.

## 6. Retrievability (rule 34(e))

- **Legs.** Each shard pushes `results/calibration/soco68_<Y>/` (full bundle, including `dispatch/`) to
  `claude/soco68-<Y>`.
- **Composite.** The parent composes `soco68_span` and lands it on `main` via the lane PR. The per-year dirs are
  gitignored in the parent.
- **Cost.** Any leg not landed is costed as a re-solve, ~2–15 min of LP per year.
