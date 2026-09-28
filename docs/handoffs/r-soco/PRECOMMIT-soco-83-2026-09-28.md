# PRECOMMIT — soco-83: SOCO ST_GAS out-of-merit must-run floor (lambda-conditioned level, plant partition with the campaign floor)

Lane soco-83, 2026-09-28. Written, committed and pushed **before any solve**. The finding behind it is
`FINDING-soco-83-2026-09-28.md`.

- **Control:** keeper `2026-09-27-soco82-perunitdark-regen` (`results/calibration/soco82_span`), solved at `2265d524`.
- **Arm:** seven year-isolated shards (rule 36), composed at zero LP.

## 0. G-DRIFT (rule 29(b)) — `2265d524` → this SHA, solve path

| hunk | class | reason |
|---|---|---|
| `src/market_sim/data/renewables.py` | INERT | docstring only (SPP-94), SPP branch |
| `data/raw/spp-*` | INERT | another ISO's artifacts |
| `src/market_sim/data/ferc714.py`, `data/raw/ferc-714/*` | INERT | read by no solve path; only the derive and the status page read it |
| `src/market_sim/pipeline/commitment.py` (plant partition) | INERT for the keeper, LIVE for the arm | fires only when `st_gas_mustrun_per_plant` tags rows, and that flag is off in the keeper recipe |
| `thermal_tranches_oom_{cost,level_mw}_SOCO.csv` | INERT for the keeper, LIVE for the arm | read only under `st_gas_mustrun_oom_level` |

Every hunk is INERT for the keeper recipe, so form 4 holds: the keeper's committed bundle is the control.

## 1. What changes (owner rulings 2026-09-28, soco-83 decision cards)

Three existing, default-off `ScenarioConfig` flags are armed for SOCO:

- `st_gas_mustrun_per_plant`
- `st_gas_mustrun_p25_level`
- `st_gas_mustrun_oom_level`

**Level.** The level comes from `thermal_tranches_oom_level_mw_SOCO.csv`:

| plant | level (MW) | nameplate (MW) |
|---|---|---|
| Gaston 26 | 179 | 1020 |
| Yates 728 | 120 | 714 |
| Watson 2049 | 190 | 721 |

The derive is `derive_thermal_tranche_oom_level_mw.py --condition lambda`. The level is the p25 of each plant's measured net
output in its online hours when Southern's FERC-714 lambda sat below the plant's monthly cost, pooled over 2019–2025.

**Window, membership and clip** are the family's own, all unchanged:

- window: the top `online_frac` system-load hours;
- membership: the tranche artifact's p25/online_frac rows;
- clip: `pmax × availability`.

**Rule 19 partition.** Those three plants leave `soco_gas_st_campaign_commitment`. Greene County (10) keeps its campaign floor.
No plant carries two commitment floors.

**Parameter count:** zero fitted parameters, zero new `ScenarioConfig` fields.

**Rule 17 statement.**

| requirement | how this floor meets it |
|---|---|
| driver | measured commitment conduct: Southern holds these boilers near minimum load through hours its own lambda says they are out of merit (FINDING §2–3); the driver's cause is not identified, and that is ruled on by the owner |
| window | the family's top `online_frac` load-hours |
| forward | a static pooled per-plant level, like every level in the family |

**Stated weakness.** Lambda sits below ST cost in 63–91 % of *all* hours, so the conditioning set is broad.

## 2. Zero-LP census (fleet_only, keeper recipe + the three flags; `soco83` scratch `fleet_arm.py`)

In every year only Gaston, Yates and Watson's ST_GAS rows change. `mc_base` and availability are identical, and Greene (10) is
unfloored by the new mechanism. Floor TWh per plant:

| year | Gaston | Yates | Watson | total |
|---|---|---|---|---|
| 2019 | 0.850 | 0.675 | 1.129 | 2.65 |
| 2020 | 0.607 | 0.776 | 1.263 | 2.65 |
| 2021 | 0.635 | 0.718 | 1.291 | 2.64 |
| 2022 | 0.782 | 0.706 | 1.342 | 2.83 |
| 2023 | 0.697 | 0.761 | 1.345 | 2.80 |
| 2024 | 0.856 | 0.700 | 1.140 | 2.70 |
| 2025 | 0.810 | 0.727 | 1.274 | 2.81 |

## 3. Greedy (price-taker, `scripts/probes/_soco83_gas_split.py` + scratch greedy)

- **ST gain vs the keeper's plant hourlies:** about 2.0–2.6 TWh/yr. These are lambda-level greedy numbers; the fleet-built level is
  slightly higher.
- **Scorer-exact C1** with CC absorbing 60–100 % of it:

| row | keeper | arm (greedy) |
|---|---|---|
| 2021 CC_REGULAR | +3.05 pp FAIL | **+1.95 to +2.39 pp PASS** |
| ST_GAS, every year | — | improves by ~1 pp |

- Every other row stays PASS.
- **Rule 17 exposure, stated in advance:** about 0.5–0.66 TWh/yr of floor energy lands in hours the plants' CEMS shows offline
  (about 21 %).

## 4. Not tested here

- `mustrun_layup_window_mask`: SOCO's lay-up CSV covers only 2023–2025, so it would act asymmetrically. Routed to soco-84.
- DO-NOT-REDO list as in PRECOMMIT-soco-82 §4.

## 5. Recipe and hard stops

Each shard runs ONE year `<Y>` ∈ {2019, …, 2025} at the pinned SHA `<SHA>`, the commit carrying this document:

```
git fetch origin <SHA> && git checkout --detach <SHA> && test "$(git rev-parse HEAD)" = "<SHA>"
uv venv .venv && uv pip install -r requirements.txt && uv pip install --no-deps -e .
.venv/bin/python scripts/hydrate_data.py --profile soco
PYTHONPATH=. .venv/bin/python scripts/data/curate_hydro_plant_modes.py --iso SOCO
PYTHONPATH=. .venv/bin/python scripts/data/curate_demand_profile.py
PYTHONPATH=. .venv/bin/python scripts/run_calibration_full.py --restore-shared-inputs results/calibration/soco82_span
.venv/bin/python scripts/replay_keeper.py results/calibration/soco82_span --years <Y> \
  --out-dir results/calibration/soco83_<Y> \
  --set eia860_vintage_tracks_solve_year=true --set measured_chp_heat_rates=true \
  --set unit_outage_short_windows=true --set unit_outage_short_windows_gas=true \
  --set unit_partial_outage_windows=true --set unit_outage_precod_clip=true \
  --set summer_derate_basis_aware=true --set coal_mustrun_requires_measured_row=true \
  --set egrid_identity_heat_rates=true --set coal_econ_marginal_hr_two_sided=true \
  --set st_gas_mustrun_per_plant=true --set st_gas_mustrun_p25_level=true \
  --set st_gas_mustrun_oom_level=true \
  --note "soco-83 <Y>: soco-82 keeper recipe + SOCO ST_GAS out-of-merit must-run floor (lambda-conditioned level; plant partition with the campaign floor)"
```

**Hard stops.** A shard that sees otherwise stops and does not push.

- **Pinned SHA:** `git rev-parse HEAD` equals `<SHA>`.
- **Artifact hashes (`sha256sum`):**

| file | sha256 |
|---|---|
| `data/raw/_processed-legacy/thermal_tranches_oom_level_mw_SOCO.csv` | `722e65b582a8699df8ee947270e6ea9f3c56eac227204d474bcbf152d9d7f2ba` |
| `data/raw/campd-unit-outages-perunitdark-SOCO.csv` | `03ce606cfe118ef28e560739d12a005b2240aa112609e119c51a9f86ea2fd37c` |
| `data/raw/_processed-legacy/campd_gas_st_campaign_params_SOCO.csv` | `cc1be8f33fa267b23a0fdd13520a904a1c35522143e2210f54a2a9586d0e2dc1` |
| `data/raw/_processed-legacy/thermal_tranches_SOCO.csv` | `ab5ec265d192379551c14facc6f65d8d972f117a565bae36b0179bbf96122ad7` |

- **Solve log** carries all of:
  - `st_gas_mustrun_oom_level ARMED (SOCO): 3`;
  - `left to the per-plant must-run floor (rule 19 partition)` naming `[26, 728, 2049]`;
  - `container preflight:` and `memory peak:`.
- **`scenario_config`** shows all thirteen `--set` fields true, plus `soco_gas_st_campaign_commitment` true.
- **Offer tuning:** every `offer_curve_by_group` band is 1.0.
- **`gas_prices[<Y>]`** equals the keeper's: 2.57 / 2.03 / 3.72 / 6.45 / 2.54 / 2.19 / 3.52.
- **Bundle:** `dispatch/<Y>_P1.parquet` is present.

## 6. Pre-registered expectations (reported, NOT a promotion criterion — rule 1)

- **E1.** ST_GAS rises by 1.5–2.8 TWh in every year; CC_REGULAR falls by most of that.
- **E2.** 2021 C1 CC_REGULAR lands between +1.9 and +2.6 pp (PASS). No C1 row flips PASS → FAIL.
- **E3.** 2019 COAL_BIT is still a FAIL at the row level. It is scored as the v3.10 scoped ledgered caveat only if it stays an
  under-run.
- **E4.** Unserved energy is 0 in every year.
  - C6 PASS.
  - C8 ST_GAS forced share rises and may exceed 30 %. If it does, it passes only on the grounded path: MECH 16 × ST_GAS holds a
    cited D4_WINDOWS (0, 24) entry, plus D-1 shape.
- **E5. Expected determination: PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED).** The v3.10 scoped ledger on 2019 COAL_BIT
  would be the only blemish.

## 7. Promotion recommendation rule (fixed now)

Recommend this run as the SOCO keeper **iff all five hold**:

1. **Legs clean:** all seven legs solve cleanly, with the §5 hard stops met.
2. **The floor fires exactly as censused:** in every leg the only units floored by MECH 16 are the ST_GAS rows of 26 / 728 /
   2049, and the campaign floor covers no plant among them.
3. **No unserved-energy increase** in any year.
4. **C6 PASS and C8 PASS** (the grounded path counts), and `legitimacy_diagnostics` records no new D-4 FAIL.
5. **No C1, C2 or C4 row flips PASS → FAIL** anywhere in 2019–2025.

**Why (5) is here.** Unlike soco-82's input repair, this is a commitment floor, and a floor that makes the gates regress
elsewhere would be forcing the wrong shape (rule 20). The standing ruling ("If structural integrity improves but gates regress
that may still be a keeper") still lets the owner promote over (5), but this lane will not **recommend** it then.

**If it lands (rule 35):**

1. Enumerate the SOCO year union (2019–2025).
2. Run `audit_keepers` E1.
3. Run `prune_iso_runs --iso SOCO --force-uncite`, which removes `2026-09-27-soco82-perunitdark-regen`.

**If it does not land:** the two new level/cost artifacts stay committed (inert without the flags), and the result is recorded.

## 8. Retrievability (rule 34(e))

- **Shards:** each pushes its full bundle, `dispatch/<Y>_P1.parquet` included, to `claude/soco83-<Y>` through a `.gitignore`
  negation and a plain `git add`.
- **Parent:** fetches, verifies and composes `soco83_span`. The composite lands on `main` with this lane's PR.
- **Cost of a leg not landed:** about 2 min of LP per year.
