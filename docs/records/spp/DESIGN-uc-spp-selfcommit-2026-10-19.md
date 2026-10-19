# DESIGN — UC-native self-commitment for EIA-860 Sector-1 ST_GAS (SPP), 2026-10-19

**Lane:** UC-SPP-SELFCOMMIT · **Branch:** `claude/uc-spp-selfcommit` · **Base:** `main` `bf9830b6`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner ruling **R24** (`docs/uc-milp-program-plan-2026-10.md` §8).
**Evidence:** `docs/records/spp/ucmilp/FINDING-spp-south-scarcity-2026-10-18.md` (#7285) §§2, 3, 5 P1.
**LP in this lane:** zero (build only; unit tests on 1-zone toy cases). **Data profile:** `spp`.

## 0. Verdict

| check | result |
|---|---|
| **Rule 13 (admissibility)** | **ADMISSIBLE** on the pooled multi-year basis (§3). No hard stop. |
| Rule 19 (one mechanism) | Replaces `st_gas_mustrun_per_plant` (+ its p25 level swap); refused together (§4). |
| Rule 21 (DOF) | Zero fitted values. Two constants, both definitional (§2). |
| Rule 17 / 18 | Relaxes on outage and inside carried min-down; unit physics (mlf, min-up/down) unchanged (§5). |
| Default | Off. Every committed key unmoved (registered in `_CACHE_KEY_OPTIONAL_FIELDS` at `False`). |

## 1. The mechanism

Field `spp_selfcommit_sector1_st_gas` (bool, default `False`, SPP only, requires `unit_commitment_milp`).

For each **integer `st_gas` UC cluster** `c` whose plant is EIA-860 **Sector 1** and has a positive pooled CEMS `online_frac` `f`:

- **Window:** `k = round(f × T)` hours, taken as `round(k/24)` whole operating days ranked by **mean P1 system load** (same helpers as the incumbent floor: `data/fleet/arrays.py::_commitment_day_order` / `_mustrun_window_hours`, SPP-64 / spp-27).
- **Row, per required hour:** `u[c,t] ≥ min(1, u_upper[c,t], ceil(n_c · a[c,t]))`.
- **Level:** none. The online unit's MW is free above the existing coupling row `P ≥ mlf · pbar · a · u` (measured `uc-params` mlf).
- **Pricing:** integer rows of the UC window, never priced. P1 sees them only through MECH 28 schedule bounds (rule 4).

Code: `model/uc/selfcommit.py` (arrays), `model/uc/window.py::_add_selfcommit_rows` (rows), `pipeline/uc.py` (sources, log, digest), `diagnose.py` (family `selfcommit`).

What changes vs the keeper's floor:

| | `st_gas_mustrun_per_plant` (keeper, P1) | this (UC) |
|---|---|---|
| forces | MW (committed tranche) in P1 | commitment state `u ≥ 1` in the UC |
| level | committed tranche MW | measured mlf, free above |
| who decides the MW | floor | P1 economics |
| start / no-load cost | not seen | paid once in the UC (uplift sidecar) |
| min-up / min-down | not seen | enforced (rule 18) |

## 2. Inputs and citations (rules 5, 14, 21, 24)

| input | source | value / basis |
|---|---|---|
| Sector | Form EIA-860 Schedule 2 `Sector`, `eia860_plant_sectors()` at the run's vintage | SPP: **22 / 22** ST_GAS artifact plants are Sector 1 |
| `online_frac` | `thermal_tranches[-splitremap]-SPP.csv`, frozen `derive_thermal_tranches.py` (sync = net MW > 1 % nameplate, all hours as denominator), pooled **2023–2025**; same selector as `assembly.py` (keeper reads `-splitremap-`) | 0.055 (E 12th St) … 0.954 (Nichols); Seminole 0.616, Wilkes 0.766, Muskogee 0.648, Southwestern 0.773 |
| ranking signal | P1 demand summed over zones | the solve year's own load |
| mlf | `uc-params` (CAMPD min stable load), already in the UC | e.g. Seminole 0.225, Wilkes 0.137 |
| `UC_SELFCOMMIT_EIA860_SECTORS = (1,)` | EIA's published code for Electric Utility | definitional |
| `UC_SELFCOMMIT_MIN_UNITS_ONLINE = 1` | the definition of `online_frac` (ANY unit synchronized) | definitional |

No new derive, no per-plant dict, no env var, no fallback in the offer path. Arm-over-gap guard extended (`campd_bins._TRANCHE_GATE_COLUMNS`): an armed run on an artifact missing the column raises.

## 3. Rule 13 — can the share be produced for a forward year from forward drivers?

**Yes, for every input.**

1. **Sector** — a published per-plant attribute. A forward year reads the latest EIA-860 vintage; a sale re-sectors the plant at the next vintage; a retired plant leaves the fleet and its cluster.
2. **`online_frac`** — a multi-year CEMS statistic. Its forward form is the same estimator on the most recent multi-year CAMPD window, the family already admitted for forecast emission rates and for the incumbent floor R5 (`st_gas_mustrun_per_plant`, `PRECOMMIT-spp-64` §2; scenarios.py field note: "online fraction re-derive from multi-year CAMPD … rule 13 admissible").
3. **Placement** — on the forward year's own system load. Not CAMPD on/off hours (killed, SPP-46). Not a P0-pattern window (killed, SPP-44).
4. **Not outcome pinning** — it fixes a count of committed hours, not MWh, prices or hours copied from the meter. Dispatch above min-load stays economic.

**Does it respond to changed conditions?** Partly, and this is stated rather than hidden:

- It responds to load (placement), outages, retirement, ownership change, and new CEMS history as it lands.
- It does **not** respond inside a forecast horizon to fuel price or policy: a utility steamer self-commits its historical share under any carbon price until the history moves. The incumbent floor carries the same limit. **Forecast-program caveat**, not a stop: if the forecast program arms this, it should declare the share frozen at the last derive window.

**Backcast notes (not admissibility failures):**

- The pooled window (2023–25) **overlaps the scored years 2023–25**; for 2019–22 it is out-of-window. A plant whose share moved across years is mis-sized in some years (the MISO Little Gypsy / PJM-h15 pattern, rule 17). The backcast fix in the repo is the per-year vintage (`mustrun_online_frac_per_year`, backcast-only), and **SPP has no per-year artifact**. This build does not add one and does not read that gate. If the test arm's D-4 conduct check fails on 2019–22, the per-year SPP derive is the next step (a rule-23 grain refinement, not a re-fit).

## 4. Rule 19 — D-2 enumeration: what already floors SPP ST_GAS

From the keeper recipe (`results/calibration/closeout_spp_nuc_span/run_config.json`) and the UC refusal sets:

| mechanism | keeper | under UC arm (U4b) | with this arm |
|---|---|---|---|
| `st_gas_mustrun_per_plant` (R5) | **on** | off (lane delta) | **refused together** |
| `st_gas_mustrun_p25_level` | off | off | refused together |
| `mustrun_window_commitment_grain` | on | inert (floor off) | not read; day grain is built in |
| `gas_st_netload_drag` | off | off | unchanged (off) |
| `reliability_floor` | off | off | unchanged |
| `spp_gas_commitment_bridge`, `spp_commitment_posture` | off | refused by UC | refused by UC |
| `vlr_pocket_commitment` | — | — | different ISO (MISO); no SPP partition |
| UC schedule bounds (MECH 28) | — | the vehicle | the vehicle (no new floor id) |

One mechanism for ST_GAS self-commitment: this row, inside the one commitment stage. No P1 floor is added.

## 5. Rule 17 / 18 behaviour (tested)

`tests/unit/model/uc/test_window_selfcommit.py`, 11 cases:

- **Trivial 1-unit / 24 h:** priced-out steamer is off without the row; with it, `u = 1` in exactly the required hours (8–20) and 0 elsewhere.
- **Level:** online at exactly `mlf · pbar` when it is the dearest energy — no P floor above min-load.
- **Rule 17:** outage hours build no row and do not force the unit on (relaxed count = 4); derated hours (a = 0.5) still commit, at `mlf · pbar · 0.5`.
- **Rule 18:** a carried min-down relaxes the row; a 2-h required block with min-up 6 h stays on ≥ 6 h because of the unit's own min-up.
- **Builder:** Sector ≠ 1, missing Sector, zero share → skipped with reason; whole-day placement by mean load (a single hot hour does not outrank a hot day).
- **Stage:** gate off builds nothing (log `null`); gate on holds day 2 (higher mean load) and logs clusters, required hours, rows; digest differs.
- **Config:** refused without UC, outside SPP, beside the per-plant floor; `cache_key` unchanged at `False`.

**Known risk carried into the test (MISO VLR V-3):** a row that holds a steamer on through consecutive top-load days under-cycles it (MISO pocket starts 0.44× / 0.15× CEMS). With min-up 52–114 h on these SPP units, scattered top days may also be bridged by min-up into longer runs than the share. Both are measured in §6, not pre-corrected.

## 6. TEST ARM (for a later lane; nothing run here)

**Control (rule 29b):** the UC-SPP-CONTROL bundle `results/calibration/uc_spp_control_span` (owner ruling R25: keeper recipe re-solved on the R22/R23-fixed data, all 7 years). No control solve.

**Arm S** — every SPP year, one shard per year (rules 16, 32, 36), bundles pushed (rule 34):

```
replay_keeper.py results/calibration/closeout_spp_nuc_span --years <y>
  --set unit_commitment_milp=true
  --set st_gas_mustrun_per_plant=false
  --set coal_sync_floor_release=true
  --set energy_reserve_coopt=true
  --set spp_spinning_reserve_share=true
  --set uc_commitment_demand_source='"da_forecast"'
  --set spp_selfcommit_sector1_st_gas=true
```

= U4b (PRECOMMIT-ucmilp5-spp §1.1) + this field, on fixed data.

**Attribution gap (desk decision before launch):** the only UC-without-selfcommit run (U4b) is on the pre-R22/R23 data. Without a U4b-on-fixed-data arm, the S − control delta mixes "UC stage" with "self-commitment". Options: (a) solve U4b' (U4b on fixed data) beside S — a second arm, not a control; (b) attribute against U4b on old data with the datafix as a declared confound.

**Report (every year):**

1. **Unserved, split by cause**, per slack hour (South and SPP-wide), in the FINDING's order data → commitment → corridor, and reversed:
   - *data-cause:* hour inside an R22/R23 repaired run (should be ~0 after the fix);
   - *commitment-cause:* South slow-start (ST_GAS + CC) capacity available (`cap_mw × a`) but uncommitted (`u = 0`) ≥ the slack MW;
   - *corridor-cause:* N→S flow at the registered 3,400 MW and no commitment-cause cover;
   - *other:* the remainder.
   Hours and MWh per cause, S vs control vs U4b.
2. **Per-plant ST_GAS on-share** (u > 0, and P1 mw > 0) vs CEMS, every Sector-1 plant; pass band ±0.05 (the MISO V-2 standard).
3. **Starts ÷ CEMS starts** per plant (V-3). Under-cycling is an open item, not a level change.
4. **D-4 conduct:** share of required hours where the plant's CEMS meter is dark (rule 17), by year; 2019–22 separately (out-of-window, §3).
5. **Over-coverage:** South ST_GAS MW vs CEMS net at the 2023-08-10 and 2023 South-peak hours (FINDING §3: the keeper ran 4.75 vs 3.88 GW). S must not be judged on reproducing the keeper's no-slack outcome.
6. **Rows / relief:** `selfcommit_rows`, `selfcommit_relaxed_hours` per window from `uc_solve_log`.
7. Rubric gates and C-cells as usual; rule-20 forced-energy share of ST_GAS under MECH 28.

**Kills (proposed; the test lane's PRECOMMIT fixes them ex ante):** unserved > control in any year with commitment-cause share not falling; any per-plant on-share > CEMS + 0.10 in a scored year; D-4 dark share > 30 % on any plant-year.

## 7. Files

`src/market_sim/model/uc/selfcommit.py` (new) · `model/uc/window.py` · `model/uc/diagnose.py` · `pipeline/uc.py` · `config/scenarios.py` (field, validator, cache-key registration, `UC_SELFCOMMIT_ISOS`, TIER_TAGS) · `config/constants.py` (2 constants) · `config/solve_surface_declared.py` (2 entries, generated) · `data/fleet/campd_bins.py` (coverage guard) · `tests/unit/model/uc/test_window_selfcommit.py` · mechanism matrix (row + `U` in all 9 shards; anchors re-fixed) · `docs/codebase/09-unit-commitment.md` · `model-methodology-spec.md` §1.6.
