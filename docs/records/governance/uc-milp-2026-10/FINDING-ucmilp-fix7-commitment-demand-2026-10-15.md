# FINDING — UC-1-FIX-7: the UC window commits against a commitment demand (uc-1.7)

Lane UC-1-FIX-7 · chartered by UC-DESK · owner ruling UC-DESK r13 (2026-10-15) · engine `uc-1.6 → uc-1.7`.

## 1. What changed

| Piece | Where |
|---|---|
| Field `uc_commitment_demand_source` (`"actual"` default \| `"da_forecast"`), registered at `'actual'` (no key moves), TIER_TAGS 1, refused without `unit_commitment_milp` | `config/scenarios.py` |
| Commitment demand builder (backcast: measured EIA-930 DF; forecast: measured error profile) | `data/commitment_demand.py` |
| Zone weights factored out of `load_demand` (no behaviour change) and reused for the DF increment | `data/eia930/demand.py::load_zone_weights` |
| Windows sliced from `UcStage.commit.demand`; digest and solve log carry it | `pipeline/uc.py` |
| Data QA `COMMITMENT_DF_DATA_ERROR_FRACTION = 0.30` (the UC-DIAG cut, §3 of FINDING-ucmilp-diag-undercommit); seasons = WMO DJF/MAM/JJA/SON | `config/constants.py` (solve surface declared) |
| Forward profile: clean datatype `load-forecast-error` (season × hour, mean `(DF − actual)/actual`, every complete year) | `scripts/data/derive_load_forecast_error.py`, schema, `clean_profiles` forecast lane |
| Matrix row `uc_commitment_demand_source`, `U` in all nine shards | `mechanism-matrix.js` + shards |

P1, the reserve rows and the P0 targets are untouched. P1 clears on actual load (rule 4).

## 2. Data mapping and misalignment (rule 14)

- **Backcast increment** = `load_zone_weights · (DF − Demand) · (1 + td_loss_factor)`, on the same `<BA> hourly` filled frame (same local model clock) the loader reads. This is `load_demand` with the forecast in place of the metered load. Interchange and must-run residuals stay as the solve built them.
- EIA-930 DF is the **BA's own day-ahead forecast**, not the DA-cleared load or the RUC load. For SPP (`SWPP`) it is the same BA as the model demand.
- NWPP is a pool frame (summed members). CAISO's armed demand corrections (clock realign, supply-consistent series) re-clock or replace the metered series; the increment stays on the EIA-930 clock (up to 1 h misaligned where the realign is armed), and it is split by the default TAC shares even under `caiso_tac_shares_standard_time` (the zonal split differs; the system total does not). UC-DIAG found the bias immaterial for CAISO.

## 3. Zero-LP reading: SPP backcast increment (this field's own seam)

| Year | QA-dropped h | Mean MW | Top-100 load h median MW | Max MW | Min MW |
|---|---|---|---|---|---|
| 2019 | 64 | +830 | +907 | +8,156 | −10,460 |
| 2020 | 36 | +1,078 | +717 | +5,964 | −3,417 |
| 2021 | 69 | +967 | +902 | +10,168 | −11,118 |
| 2022 | 0 | +894 | +1,165 | +5,616 | −5,667 |
| 2023 | 1 | +561 | +268 | +7,486 | −7,544 |
| 2024 | 2 | −239 | −549 | +7,567 | −9,310 |
| 2025 | 63 | +2,073 | +3,535 | +10,841 | −11,415 |

This agrees with UC-DIAG (+0.8 to +1.3 GW at peak, 2019–22). The forward profile (SPP 2016–25) averages +2.5 %; MISO (2018–25) averages +2.4 %.

## 4. Gates

- **G-OFF.** On the toy stage (two loads, 48 h), main `80521461` (uc-1.6) and this branch (uc-1.7, field at default) give the same SHA-256 over `u/v/w`, P1 dispatch, prices, objective and the P1 bounds (`73becfab1785d51b`). The default `cache_key` is unchanged. At `"actual"` the windows receive the P1 demand object itself (`test_actual_source_is_the_p1_demand_object`). The same hash is reproduced after merging main `01b90bd0` (#7253, #7262, #7263, #7264) against that main.
- **Trivial case** (`tests/unit/model/uc/test_commitment_demand_stage.py`): 1 zone, 48 h, CC 2 × 100 MW. Actual 150 MW commits one unit. A forecast 60 MW higher commits two. P1 still clears 150 MW: the CC floor holds and the nuclear unit backs down and sets the price.
- **Seen in the toy:** at night the forecast (100 MW) commits one unit whose 50 MW floor exceeds the actual 40 MW, and P1 dumps the excess. This is the cost of over-commitment that a forecast error carries. P1 has no real-time decommitment. Read it in the repro: SPP's mean bias is positive.

## 5. PRECOMMIT — repro shard (declared before launch)

- **One shard:** SPP 2020, arm B (`unit_commitment_milp=true`, `st_gas_mustrun_per_plant=false`, `coal_sync_floor_release=true`) plus `uc_commitment_demand_source="da_forecast"`, at the uc-1.7 pin. Control: the committed uc-1.5 arm B bundle `docs/records/spp/ucmilp/data/ucmilp3_spp_b_span` (rule 29b, no control solve).
- **Headline readings (fixed now):** top-100-load-hour committed ST_GAS and CC GW (from `uc_schedule`, `online_mw`), against the uc-1.5 arm B; C3a, C3b and C1 against the uc-1.5 arm B `metrics.json`.
- **Context readings:** P1 dump MWh; mean and p99 price; the `commitment_demand` row of `uc_solve_log`.
- **Not a tuning run.** No value is chosen from these readings. Nothing is registered (rule 15 applies only at a registration the desk decides).
- **G-DRIFT** from uc-1.5 to this pin: uc-1.6 (u-gated reserve headroom; a no-op without co-opt, and SPP arm B has none) and uc-1.7 (this field). The repro differs from the uc-1.5 arm B by the commitment demand alone.

## 6. Repro result

SPP 2020, arm B (`unit_commitment_milp`, `st_gas_mustrun_per_plant=false`, `coal_sync_floor_release=true`) with `uc_commitment_demand_source="da_forecast"`. Shard `session_01ALAmFzXrSA7xw8LG16fCi1` ran at `3111853c`. The bundle is commit `1090b5dd` on `claude/ucfix7-spp-b-2020` (20 files, `dispatch/2020_P1.parquet` present, legitimacy PASS). The shard was verified (bytes extracted locally) and then archived.

Control: the committed uc-1.5 arm B (`docs/records/spp/ucmilp/data/ucmilp3_spp_b_span`). Its `run_config_2020` differs from the repro only in `uc_commitment_demand_source`. Both runs have 219 clusters and 92 integers. The engine changes between them are uc-1.6 (a no-op here; this arm runs no reserve co-optimisation) and uc-1.7 (this field). Scoring: `calibration_verdict.py`, rubric 3.20 (the control's rubric), through a local `dashboard_add_run --no-prune`. The sidecar is kept out of git with `.git/info/exclude` and is never committed. Benchmark frames were restored at zero LP with `--restore-shared-inputs`, hash-verified against `meta.json`.

| Reading (2020) | uc-1.5 arm B (control) | uc-1.7 arm B + DA forecast | Δ |
|---|---|---|---|
| Commitment increment, top-100 load h (median) | 0 (actual) | +717 MW (mean +1,078; 36 QA-dropped h) | — |
| Committed CC, top-100 load h | 8.23 GW | 8.24 GW | +0.01 |
| Committed ST_GAS, top-100 load h | 1.27 GW | 1.81 GW | **+0.54** |
| Committed coal, top-100 load h | 16.31 GW | 16.41 GW | +0.10 |
| Committed ST_GAS / CC / coal, annual mean | 0.75 / 5.58 / 10.04 GW | 0.95 / 5.76 / 10.54 GW | +0.20 / +0.18 / +0.50 |
| Starts ST_GAS / CC / coal | 243 / 1,580 / 350 | 343 / 1,560 / 389 | +100 / −20 / +39 |
| C1 CC_REGULAR (TWh) | +2.13 | +2.73 PASS | +0.60 |
| C1 COAL_PRB (TWh) | −4.20 | −3.07 PASS | +1.13 |
| C1 ST_GAS (TWh) | −7.40 | −6.76 PASS | +0.64 |
| C1 CT_PEAKER (TWh) | **+9.84 F** | +7.47 PASS | **−2.37 (FAIL→PASS)** |
| C1 other (repro) | — | COAL_LIGNITE −1.27, COAL_BIT −0.04, CC_CHP +0.33, ST_CHP −0.23; all PASS (C1 8/8) | — |
| C3a mean LMP vs RT | **+36.7 % F** | **+30.7 % F** ($21.59 vs $16.52) | −6.0 pp |
| C3b monthly NRMSE | **0.421 F** | **0.367 F** | −0.054 |
| C3c hours > $200 (model / actual) | 0 / 23 | 0 / 23 | 0 |
| Top-100-load-hour mean price | $33.52 | $30.56 | −$2.96 |
| Unserved / dump | 0 / 0 MWh | 0 / 0 MWh | 0 |
| Uplift (share of UC-cluster revenue) | $4.7 M (0.16 %) | $14.4 M (0.50 %) | +$9.7 M |
| Start cost / no-load | $32.3 M / $179.5 M | $34.5 M / $191.6 M | +$2.2 M / +$12.2 M |

**Reading.**
- The mechanism works as designed. A forecast increment of +0.72 GW at peak commits +0.65 GW more slow-start capacity at peak. Nearly all of it is ST_GAS, and CC is unchanged.
- That extra capacity displaces CT: CT_PEAKER energy falls 2.4 TWh and C1 CT_PEAKER flips FAIL→PASS. ST_GAS, PRB and CC all move toward actual.
- Price moves in the right direction but does not close the gap. C3a goes +36.7 → +30.7 % and C3b 0.421 → 0.367. Both still FAIL, and both remain worse than the floors-on keeper control (+27.7 % / 0.345).
- No P1 dump: SPP's positive bias does not over-commit past what actual load absorbs at the committed floors in 2020.
- Uplift triples. It is still small (0.5 % of cluster revenue), which is the expected cost of committing on a forecast that runs above actual.
- Not a tuning reading: no value was chosen from it. One year only, pre-merge engine (below).

The shard is pinned to `3111853c`, which is the PRE-MERGE engine: uc-1.7 commitment demand on the uc-1.6 base, before main's per-unit `ut_h`/`mlf` (#7262/#7264, epochs 2026-10-15a/b) and the VLR pocket rows (#7263, default off). It stays valid evidence for the mechanism (UC-DESK, 2026-10-15). Its control, the uc-1.5 arm B, likewise predates the per-unit `uc-params`. The repro therefore isolates the commitment demand, but its levels are not the post-merge engine's.
