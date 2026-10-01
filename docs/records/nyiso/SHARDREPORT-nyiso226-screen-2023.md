# SHARDREPORT — nyiso-226 SCREEN shard, NYISO 2023 arm

Rule 32 `[R-SHARD]` solve shard for session nyiso-226. **Numbers only — this shard scores
nothing, compares nothing to the keeper, and recommends nothing** (rule 32(d): all scoring,
gate evaluation and the promotion question are the parent's).

## Provenance

| field | value |
|---|---|
| pinned `git rev-parse HEAD` | `a61c1131ea7fb63147c3067fd284dc3fb898ae03` (verified equal) |
| keeper replayed | `results/calibration/nyiso_fuelvintage_A`, `meta.json` `git_sha` = `da2e7076` (verified) |
| authority | `docs/PRECOMMIT-nyiso226-nyc-base-rebasis-2026-09-10.md` §1, §6 |
| arm out-dir | `results/calibration/nyiso226_screen_2023/` (local disk only — NOT committed, NOT deleted) |
| solve wall clock | **5 min 00 s** (16:07:48 → 16:12:48 UTC); budget 20 min |

## The arm

Exactly one cell of `data/raw/reference/reliability_floor_coeffs_NYISO.csv` (line 6), the
`NYISO,NYC,ST_GAS,tmax,-50.0` row:

```
floor_pct  0.175  ->  0.16629202320362052
```

`git diff --stat` = `1 file changed, 1 insertion(+), 1 deletion(-)`. No other row, column or
byte of that file moved; no `ScenarioConfig` delta. Pre-solve verification printed exactly:

```
ARM floor_pct = 0.16629202320362052 enabled= True distribution= pro_rata
rows total 46
```

## ARM 2023 class TWh (`hourly/class_hourly_2023.parquet`, P1)

| class | TWh |
|---|---|
| COAL_PRB | 0.000000 |
| COAL_BIT | 0.000000 |
| oil | 0.149817 |
| solar | 0.279821 |
| CT_PEAKER | 0.398197 |
| biomass | 0.839526 |
| ST_CHP | 1.372494 |
| CT_CHP | 1.543037 |
| OTHER | 2.197331 |
| wind | 4.590724 |
| ST_GAS | **9.731508** |
| CC_CHP | 15.926029 |
| import | 23.336016 |
| hydro | 26.615767 |
| nuclear | 27.487143 |
| CC_REGULAR | 33.843945 |
| **TOTAL** | **148.311356** |

## ARM 2023 system (`hourly/system_2023.parquet`)

Columns: `year, pass, zone, hour, price, slack, dump, demand, reserve_price`

| column | mean | p95 | max |
|---|---|---|---|
| price | 33.0433 | 50.6789 | 326.4235 |
| slack | 0.0000 | 0.0000 | 0.0000 |
| dump | 0.0000 | 0.0000 | 0.0000 |
| demand | 2797.7330 | 6661.3667 | 10379.9529 |
| reserve_price | 0.1096 | 0.0000 | 90.0000 |
| hour | 4379.5000 | 8321.0500 | 8759.0000 |
| year | 2023.0000 | 2023.0000 | 2023.0000 |

`slack` and `dump` are identically zero across all zone-hours.

## D-2 rows (`legitimacy_diagnostics.json`)

| year | class | mechanism | forced_twh | class_total_twh | share_of_class |
|---|---|---|---|---|---|
| 2023 | (none) | nuclear_mustrun | 27.4871 | 35.3716 | 0.7771 |
| 2023 | (none) | firm_import | 7.8840 | 35.3716 | 0.2229 |
| 2023 | CC_CHP | chp_steam | 0.0130 | 15.9532 | 0.0008 |
| 2023 | CC_REGULAR | nyiso_gas_commitment_bridge | 0.3574 | 31.9738 | 0.0112 |
| 2023 | CT_CHP | chp_steam | 0.0002 | 2.8550 | 0.0001 |
| 2023 | ST_CHP | chp_steam | 0.0078 | 0.0676 | 0.1147 |
| 2023 | ST_GAS | **reliability_floor** | **1.8716** | **11.7730** | **0.1590** |
| 2023 | ST_GAS | nyiso_gas_commitment_bridge | 0.0070 | 11.7730 | 0.0006 |
| 2023 | hydro | hydro_min_flow | 7.7249 | 26.6158 | 0.2902 |

## D-4 `reliability_floor` rows

| check | floor | window | plant | floored_twh | offwin_twh | offwin_share | binding_hrs | meas_median_mw | meas_zero_share | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| window | reliability_floor × ST_GAS | h0-23 | — | 1.8716 | 0.0 | 0.0 | — | — | — | pass |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 2480 | 0.0015 | — | 0.0008 | 157 | 0.0 | 1.0 | **FAIL** |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 2490 | 0.3101 | — | 0.1657 | 3227 | 96.634 | 0.3812 | pass |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 2511 | 0.4028 | — | 0.2152 | 7685 | 135.391 | 0.0513 | pass |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 2516 | 0.9082 | — | 0.4853 | 7819 | 218.974 | 0.1219 | pass |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 2625 | 0.0197 | — | 0.0105 | 165 | 521.382 | 0.0788 | pass |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 8006 | 0.0009 | — | 0.0005 | 18 | 254.649 | 0.0 | pass |
| unit-conduct | reliability_floor × ST_GAS | h0-23 | 8906 | 0.2283 | — | 0.1220 | 5546 | 0.0 | 0.511 | **FAIL** |

## Gates block (verbatim)

```json
{"d1_min_profile_r": 0.8, "d1_min_cv_ratio": 0.5, "d1_offpeak_last_hour": 14,
 "d1_gated_classes": ["CT_PEAKER", "ST_GAS", "COAL", "COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC"],
 "d2_peaker_max_share": 0.15, "d2_merchant_max_share": 0.3,
 "d2_exempt_classes": ["CC_CHP", "CT_CHP", "ST_CHP", "nuclear"],
 "d4_max_offwindow_share": 0.05}
```

## `metrics.json`

**ABSENT** from the arm bundle. Per the shard instruction this is not a failure and this shard
did **not** build one. Bundle contents as written: `btm.parquet`, `dispatch/`, `floors/`,
`flows.parquet`, `hourly/`, `legitimacy_diagnostics.json`, `meta.json`, `model_changes.diff`,
`run_config.json`, `storage.parquet`, `system.parquet`.

## WARNING / ERROR scan

**No ERROR, no traceback, no infeasibility.** 28 `WARNING:` lines, all pre-existing
data-hygiene notices repeated across the fleet-build passes, plus the diagnostics gate notice:

- eGRID heat-rate reconciliations: plant 55641 (14.964 → 6.880, CC ceiling), plants 2681 /
  57186 / 59453 clamped up to the 9.000 simple-cycle floor (SPP-49).
- NYISO CC pmax reconciliations against trusted bounds: 7314 (−29.5 MW), 10190 (−20.0 MW),
  56196 (−102.0 MW) — corrupt summer-capacity rows.
- `18 of 45 NYISO generators not in eGRID lookup — assigned fallback zone` (×2).
- `no hydro-plant-modes clean partition for NYISO` (×2).
- `legitimacy diagnostics gate FAIL on the replayed bundle (artifact still written; C7/C8
  score from its contents)` — the artifact **was** written; the D-4 unit-conduct FAILs above
  are its content. The parent evaluates this; the shard does not.

The diagnostics report embedded in the solve log also prints `Overall: **FAIL**` and
`## D-4 off-window binding — FAIL`, and notes that the per-unit conduct rider skipped 125
floored rows with no measured series (hydro / nuclear / renewables / interchange pseudo-units).
D-10 free-class-only rescore printed **PASS** (2/2 wind/solar rows `delivered_pinned`,
advisory-only).

## Notes for the parent

1. **`.gitignore` correctly covers the bundle.** `.gitignore:1913` carries
   `results/calibration/nyiso226_*/`, so every file of the arm bundle is ignored and
   `git status --short --untracked-files=all -- results/` is empty. (An earlier check in this
   shard appeared to say otherwise: `git check-ignore` was run *before* the directory existed,
   and the pattern's trailing slash only matches a real directory. No repair was needed and
   none was attempted.) Only the two named paths were staged; `git status --short` confirmed
   nothing else.
2. The arm bundle is on this shard's **local disk only** and was **not deleted**
   (rule 31 `[R-RETAIN]`). It will not survive container reclamation.
