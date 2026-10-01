# PRECOMMIT — R-ERCOT-11: W A Parish split repaired (capacity boundary + split-child heat rates)

**Session:** R-ERCOT-11, 2026-09-28. **Written before any solve.** The pinned SHA is the commit that carries this file.

**Keeper and control:** `2026-09-27-r-10-parish-fuelscope`, bundle `results/calibration/r_ercot10_parish_span`, 2019–2025, solved at `a33eeb3a6444d646965a9090ee840c8fdb8a8c1e`. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)). No control solve.

**Authority:** owner ruling on R-ERCOT-10's card, verbatim *"Add Parish WAP1–4 (Recommended)"* — a rule-14 fleet-coverage fix at W A Parish, making "every plant-code-keyed seam tolerate two groups at one code" (outage derive, partial derive, EIA-923 class override, DAM plant availability, heat-rate resolver, offer surface, benchmark mapping). `offer_curve_by_group` is untouched (rule 1(c)); the 2023 k=33 owner hold stands; promotion is the owner's (rules 31/35).

## 1. Phase 0 (zero LP): the ruling's premise is FALSE — the real defect is the split's boundary

R-ERCOT-10 reported WAP1–4 "in the ERCOT fleet in no year". Measured this session:

| claim | measured | source |
|---|---|---|
| WAP1–4 absent from the fleet | **Present in every year** as split code `34702` "W A Parish [ST]", ST_GAS, 16 tranches, 1,565 MW (`scripts/tag_mixed_plants.py` convention `parent*10+digit`). The keeper dispatches it at **2.63 / 2.45 / 2.54 / 2.90 / 2.89 / 3.53 / 3.73 TWh** (2019–25). | `fleet_only` rebuild; keeper payload `plants["34702"].m_ann` |
| unit outages need a two-group seam | **Already routed**: WAP5–8 → (3470, COAL), WAP1–4 → (34702, ST_GAS) | `src/market_sim/data/outages.py:298` |
| partial derate needs a two-group seam | **Already fuel-scoped** (R-ERCOT-10); regenerated this session at HEAD, base and arm: all four extracts byte-identical to committed (capacity-invariant) | `derive_partial_outages.py` re-run, §3 |
| C1 benchmark books Parish gas to coal | **No.** `classFull` classifies EIA-923 row by row (fuel × prime mover): Parish NG-ST (1.18 / 1.00 / 1.88 / 1.79 / 1.63 / 2.40 / 2.61 TWh) is in ST_GAS. Only the per-plant *diagnostic* row `bench.plants["3470"].e_ann` carries the whole plant (C1 does not read it). R-ERCOT-3's and R-ERCOT-10's Parish "actual" (14.33 TWh 2019, etc.) used that row, so the Parish **coal** shortfall they quote is overstated by the NG-ST amount. | `run_calibration_full._benchmark_eia923_frame`; bench files |
| DAM availability | class-level fractions; capacity-free | `ercot-thermal-dam-availability*.csv` |

**Defect 1 — the split is on the wrong capacity boundary (rule 14).** Every other bin-sheet row is EIA-860 nameplate (ratio 1.000; Barney Davis's split 730 + 352 = 1,082 is exact). At Parish the plant total is right (4,008) but **294 MW of coal sits in the gas row**:

| row | sheet MW | EIA-860 nameplate |
|---|---|---|
| 3470 W A Parish [COAL] (WAP5–8, SUB) | 2,443.0 | **2,736.8** |
| 34702 W A Parish [ST] (WAP1–4, NG ST) | 1,565.0 | **1,255.3** |
| (GT1, 16.3 MW NG GT, 1967; EIA-923 ≤ 0.003 TWh/yr) | — | not modelled |

**Defect 2 — split children never read their measured heat rate (rule 14).** `campd_st_heat_rates_ERCOT.csv` pairs WAP1–4 (4 boilers, 1,105 MW summer) and Davis ST1 to their ST_GAS rows but keys them at the CAMPD facility (3470 / 4939) — correct for the per-generator fleets that derive reads. `resolve_bin_heat_rates` looks up the synthetic child code, misses, and falls to the sheet: **10.76 at 34702 (the coal row's plant average)** and 10.7 at 49392, against measured 11.52–11.97 and 12.54–12.88.

## 2. What changes (two input-identity corrections, zero free parameters, no new `ScenarioConfig` field)

1. `data/raw/reference/custom-bin-assignments.csv`: 3470 `Nameplate_MW` 2443.0 → **2736.8**; 34702 1565.0 → **1255.3** (EIA-860 operable, `Energy Source 1` SUB vs NG-ST). sha256 `417e596c…` → `ed909139…`.
2. `src/market_sim/data/fleet/campd_bins.py`: `split_child_parent_codes()` (a tagged row whose `code // 10` is a tagged row) and, in `resolve_bin_heat_rates`, a child that misses on its own code reads its parent's entry **in its own family's map**. Reaches exactly two rows, 34702 and 49392 (unit test `tests/unit/data/test_r_ercot_bin_heat_rates.py`). Backcast-only by construction (the resolver runs only when a `heat_rate_year` is passed).

Why no flag: both are the R-ERCOT-8/10 class of correction (a measured input on the right boundary), no tunable, ERCOT-only (no other ISO carries split codes). Rule 23: no derive is re-run against a residual.

## 3. Zero-LP footprint (`fleet_only` census of every LP unit, keeper recipe, base vs arm; `scripts/probes/_r_ercot11_parish_split_census.py`)

| code | year | pmax b→a | avail TWh b→a (Δ) | must-run TWh b→a | cap-wtd mean mc b→a |
|---|---|---|---|---|---|
| 3470 | 2019 | 2443→2736.8 | 16.985→19.324 (+2.340) | 1.533→1.533 | 20.51→20.51 |
| 3470 | 2020 | 2443→2736.8 | 14.548→16.645 (+2.097) | 1.480→1.494 | 20.40→20.40 |
| 3470 | 2021 | 2443→2736.8 | 13.151→15.051 (+1.900) | 1.500→1.533 | 23.17→23.17 |
| 3470 | 2022 | 2443→2736.8 | 11.549→13.270 (+1.721) | 1.491→1.516 | 22.64→22.64 |
| 3470 | 2023 | 2443→2736.8 | 13.682→15.640 (+1.958) | 1.409→1.433 | 24.26→24.26 |
| 3470 | 2024 | 2443→2736.8 | 14.137→16.185 (+2.047) | 1.369→1.376 | 20.24→20.24 |
| 3470 | 2025 | 2443→2736.8 | 16.530→18.767 (+2.238) | 1.533→1.533 | 20.58→20.58 |
| 34702 | 2019 | 1565→1255.3 | 6.624→4.327 (-2.297) | 1.322→0.756 | 401.38→433.40 |
| 34702 | 2020 | 1565→1255.3 | 6.332→3.984 (-2.348) | 1.112→0.633 | 369.75→398.98 |
| 34702 | 2021 | 1565→1255.3 | 8.605→6.211 (-2.394) | 1.158→0.796 | 693.62→744.78 |
| 34702 | 2022 | 1565→1255.3 | 8.915→6.600 (-2.315) | 1.320→0.954 | 617.98→679.22 |
| 34702 | 2023 | 1565→1255.3 | 8.845→6.855 (-1.990) | 1.151→0.757 | 412.18→458.07 |
| 34702 | 2024 | 1565→1255.3 | 7.896→5.780 (-2.116) | 1.346→0.954 | 33.01→35.04 |
| 34702 | 2025 | 1565→1255.3 | 9.518→7.466 (-2.052) | 1.260→0.876 | 40.11→43.08 |
| 49392 | 2019 | 352→352 | 2.617→2.626 (+0.009) | 0.131→0.131 | 608.03→717.73 |
| 49392 | 2020 | 352→352 | 2.652→2.660 (+0.008) | 0.061→0.061 | 702.97→845.26 |
| 49392 | 2021 | 352→352 | 2.736→2.745 (+0.009) | 0.103→0.103 | 757.18→887.11 |
| 49392 | 2022 | 352→352 | 2.658→2.666 (+0.007) | 0.081→0.081 | 829.09→978.69 |
| 49392 | 2023 | 352→352 | 2.360→2.365 (+0.005) | 0.172→0.172 | 607.95→711.58 |
| 49392 | 2024 | 352→352 | 2.472→2.483 (+0.011) | 0.042→0.042 | 45.92→53.59 |
| 49392 | 2025 | 352→352 | 2.456→2.470 (+0.014) | 0.003→0.003 | 56.17→65.56 |

**Attribution (two extra censuses: heat-rate fix alone, capacity fix alone).**
- The heat-rate fix is **fully local**: only 34702 / 49392 move.
- The capacity fix moves two fleet-wide constructs that are *defined over model gas capacity*, so the corrected capacity is their correct input:
  - the ERCOT zonal gas-basis spread (gas-capacity-weighted demeaning; log: 2020 spread top 3.06 → 3.05 $/MMBtu, West deep −$0.01) → non-Parish CC_REGULAR mean mc **−0.25 / −0.42 / −0.37 / −0.39 / −0.23 / −0.01 / −0.02 $/MWh** (2019–25);
  - the class-level DAM gas event cap → other ST_GAS plants' available energy **+0.17 / +0.14 / +0.17 / +0.14 / +0.10 / +0.20 / +0.27 TWh**.
- Cleared-share boundary: +1 floored econ row in some years (the relabelled Parish tranche).
- Nothing else moves. Coal must-run floors are absolute (EIA-860 min configuration), so Parish coal must-run is unchanged.

**Partial-outage extracts.** `derive_partial_outages.py --years 2019..2026 --emit-units --emit-shaped --emit-shaped-dayguard` at HEAD reproduces all four committed files exactly on the old sheet, and yields **identical** rows on the new one (the derate is normalised to the plant's own reference ceiling). Nothing to regenerate.

## 4. G-DRIFT (keeper SHA `a33eeb3a` → HEAD `058c5713`)

Three commits touch the solve path: SPP-93 (`spp_zone_partition`, default `north_south`, SPP-only branches in `iso_configs`, `eia860._assign_zones`, `renewables`, `zonal_shares`, `runner`, `run_calibration`), SPP-94 (SPP curtailment rows), soco-81 (`coal_econ_marginal_hr_two_sided`, default False, absent from every ERCOT year; SOCO artifact). New data: `spp_plant_reserve_zone.csv`, `coal_incremental_hr_ratio_SOCO.csv`. **Every hunk INERT for ERCOT. Form 4 valid.** LIVE: only this lane's two edits (§2).

## 5. Sealed predictions (arm vs keeper, P1)

Keeper baselines (payload): Parish coal 3470 = 11.10 / 6.99 / 12.15 / 10.80 / 8.82 / 10.33 / 14.53 TWh; 34702 = 2.63 / 2.45 / 2.54 / 2.90 / 2.89 / 3.53 / 3.73; 49392 = 0.22 / 0.08 / 0.94 / 0.24 / 0.30 / 0.26 / 0.18. C1 (model − classFull, TWh): COAL_PRB −10.13 / −14.15 / −3.08 / +4.25 / −3.01 / −2.54 / +1.88; ST_GAS +5.24 / +7.65 / +0.22 / +0.30 / +0.63 / −0.09 / −1.19; CC_REGULAR +8.17 / +7.98 / −2.60 / −9.72 / +2.39 / −1.21 / −0.98. C1 band ±8.00 TWh.

- **P1 (Parish coal).** Rises in every year by between 0.3× and 1.0× its Δ-available energy: 2019 [+0.70, +2.34], 2020 [+0.63, +2.10], 2021 [+0.57, +1.90], 2022 [+0.52, +1.72], 2023 [+0.59, +1.96], 2024 [+0.61, +2.05], 2025 [+0.67, +2.24].
- **P2 (Parish gas 34702).** Falls in every year, by 20–70 %.
- **P3 (Davis ST 49392).** Falls or holds in every year.
- **P4 (C1 COAL_PRB).** 2019 narrows to [−9.6, −7.9] — **KNIFE EDGE**: it passes only if the class gains ≥ 2.13 TWh; predicted to stay FAIL. 2020 narrows to [−13.6, −12.1], stays FAIL. 2022 widens to [+4.7, +6.0], stays PASS. 2025 to [+2.4, +4.1], PASS.
- **P5 (C1 ST_GAS).** Falls in every year by 0.5–3.0 TWh; stays PASS in every year (2019/2020 overshoot narrows).
- **P6 (C1 CC_REGULAR).** 2019 moves to [+6.0, +8.4] (may flip to PASS); 2020 stays PASS within [+6.0, +8.0]; **2022 worsens to [−11.5, −9.7], stays FAIL.**
- **P7 (price).** Load-weighted P1 price moves −3 % to +0.5 % in 2019–2023 and −2 % to +0.5 % in 2024/2025.
  - **2025 C3a ∈ [−11.0, −9.2] — NAMED RISK.** It sits 0.6 pts inside the ±10 % band; a crossing below −10.0 % flips 2025 to NOT-YET.
  - **2024 C3a ∈ [−10.3, −8.5] — NAMED RISK**, same mechanism.
  - C3b moves ≤ 0.03 in 2024/2025.
- **P8 (tail).** h > $1k changes by ≤ 3 per year; slack changes by ≤ 1,500 MWh per year (2021 February week the only plausible mover).
- **P9 (train tier).** 2023 stays NOT-YET (owner hold): C3a ∈ [−22.0, −18.5], C3b 0.29 ± 0.03. No C8 gate changes a determination.

## 6. Decision rule (fixed now)

Rules 14 and 1 govern: the repair is kept on its identity, never on the scores.
- **2024 and 2025 stay CALIBRATED** → recommend **promote** (owner's standing instruction: "Is it an improvement? Then promote").
- **2024 or 2025 flips to NOT-YET** → report at full magnitude with its root cause and put it to the owner, **with no recommendation to revert** the correction; do not promote without the owner's word.
- Nothing is pruned before the owner rules (rules 31/35).

## 7. DOF ledger (carried VERBATIM from the keeper; this arm adds NO entry)

A capacity correction to EIA-860 nameplate and a key-routing fix carry no free scalar. The offer-curve band multipliers are unchanged leg for leg (rule 1(c)); `config_partition_overrides` are carried from the keeper untouched. The ledger below is R-ERCOT-10 PRECOMMIT §7's block, byte-for-byte.

```json
{
 "schema": "dof-ledger/v1",
 "seeded": "2026-07-04 S5 governance session \u2014 audit \u00a73 class-C table + W1d residual-identified/forecast-risk markers (docs/model-legitimacy-audit-2026-07.md; CLAUDE.md rule 20)",
 "n_entries": 12,
 "n_residual": 7,
 "entries": [
  {
   "name": "offer_curve_by_group",
   "where": "run_config.scenario_config.offer_curve_by_group",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": {
    "CC_REGULAR": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak",
     "peak_ladder",
     "phys_committed",
     "phys_econ_high",
     "phys_econ_low",
     "phys_peak"
    ],
    "CC_INTERMEDIATE": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak"
    ],
    "CC_CHP": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak",
     "peak_ladder",
     "phys_committed",
     "phys_econ_high",
     "phys_econ_low",
     "phys_peak"
    ],
    "CT_CHP": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "peak",
     "phys_committed",
     "phys_econ_high",
     "phys_econ_low",
     "phys_peak"
    ],
    "CT_PEAKER": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak",
     "peak_ladder",
     "phys_committed",
     "phys_econ_high",
     "phys_econ_low",
     "phys_peak"
    ],
    "CT_INTERMEDIATE": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak"
    ],
    "ST_GAS": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak",
     "peak_ladder",
     "phys_committed",
     "phys_econ_high",
     "phys_econ_low",
     "phys_peak"
    ],
    "ST_GAS_INTERMEDIATE": [
     "committed",
     "econ_high",
     "econ_low",
     "econ_low_share",
     "pct_peaking",
     "peak"
    ]
   },
   "n_scalars": 107,
   "source": "per-group HR-band multipliers \u2014 the rule-#1-sanctioned offer-curve tuning surface (audit C-8/C-11/C-13)",
   "root_cause": "identified in-sample only (2023-2025); no held-out validation exists \u2014 open: the one-shot D-6 holdout score (CLAUDE.md rule 22) and the D-7 statistical-mode gap reported on the Calibration Status page"
  },
  {
   "name": "offer_curve_smoothing",
   "where": "run_config.scenario_config.offer_curve_smoothing_*",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": {
    "offer_curve_smoothing_n": 6,
    "offer_curve_smoothing_mid": 0.35,
    "offer_curve_smoothing_exp": 1.0
   },
   "n_scalars": 3,
   "source": "econ-ramp shape of the offer curve (rule-#1 scope)",
   "root_cause": "identified in-sample only (2023-2025); no held-out validation exists \u2014 open: the one-shot D-6 holdout score (CLAUDE.md rule 22) and the D-7 statistical-mode gap reported on the Calibration Status page"
  },
  {
   "name": "coal_perplant_offer_curves (per-plant measured TPO curves)",
   "where": "constants.COAL_PERPLANT_OFFER_CURVE_BY_ISO via run_config.scenario_config.coal_perplant_offer_curves; applied in fleet.legacy_bins.apply_coal_tranches",
   "identification": "measured-physical",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "n_scalars": 0,
   "source": "each plant's merged modal 60-Day SCED Submitted TPO supply curve, pooled over the four 2024-2025 disclosure subsets \u2014 verbatim submitted conduct, zero fitted parameters (frozen scripts/data/derive_coal_perplant_offer.py; provenance data/raw/_processed-legacy/coal_perplant_offer_curves_ERCOT.json; ERCOT-144, chartered by ERCOT-143 \u00a72's per-plant measurement)",
   "note": "re-derive trigger is a new SCED disclosure subset only (rule 23), never a residual; representation bounds declared in the ERCOT-144 precommit: the 2023 application is an extrapolation (no 2023 SCED exists), levels are fuel-invariant by measurement (mid-band only \u2014 _mustrun/_peak keep their measured fuel/gas responses), and within-tranche measured dispersion is capacity-weight averaged at the CAMPD tranche grain"
  },
  {
   "name": "wefor_multiplier",
   "where": "run_config.scenario_config.wefor_multiplier",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": 0.7,
   "source": "wind EFOR haircut (audit C-15) \u2014 the name admits residual identification; stated purpose is coal shoulder-month generation",
   "root_cause": "audit C-15 open item: replace with a measured wind availability/curtailment input or delete; identified in-sample only (2023-2025); no held-out validation exists \u2014 open: the one-shot D-6 holdout score (CLAUDE.md rule 22) and the D-7 statistical-mode gap reported on the Calibration Status page"
  },
  {
   "name": "wefor_residual",
   "where": "run_config.scenario_config.wefor_residual (groups ['ST_CHP', 'ST_GAS'])",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": 0.02,
   "source": "wind-EFOR residual relief term (audit C-15) \u2014 residual-identified by name",
   "root_cause": "audit C-15 open item; statistical mode turns this off and the fit degrades (docs/statistical-mode-results-2026-07.md); identified in-sample only (2023-2025); no held-out validation exists \u2014 open: the one-shot D-6 holdout score (CLAUDE.md rule 22) and the D-7 statistical-mode gap reported on the Calibration Status page"
  },
  {
   "name": "battery_dispatch_adder",
   "where": "run_config.scenario_config.battery_dispatch_adder",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": 10.0,
   "source": "grid-battery throughput/cycling adder $/MWh \u2014 inside the literature range (NREL ATB 2024 cycle-life ~$15-25/MWh; Xu et al. 2018 $25-50/MWh) but the specific value is calibrated",
   "root_cause": "reduced-form stand-in for cycling degradation + AS opportunity cost; forward-valid replacement is the measured AS power reservation (storage_as_commitment) + an ATB-derived degradation cost \u2014 open item to re-derive from those"
  },
  {
   "name": "ercot_adaptive_half_life_days / ercot_adaptive_beta",
   "where": "run_config.scenario_config.ercot_adaptive_*",
   "identification": "measured-physical",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": [
    30.0,
    3.0077
   ],
   "n_scalars": 2,
   "source": "EWMA half-life (days) and gain beta of the daily spike-frequency expectation P_hat, SSE-fit of implied_P(d) = evening storage offer p50 / ordc_voll on P_hat(d) over admissible days 2023-06-10..12-31 on the pre-registered grid (PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md Amendment 1 family v2; artifact results/phase0/ercot/ercot221_adaptive_phase0.json). The armed path consumes only the model's own pass-1 price path (Amendment 4) \u2014 the measured surface is identification evidence only. Phase-0 v1+v2 FAILED their gates; Phase-1 entered on owner instruction (recorded in the precommit Amendment 2), so these constants are additionally flagged by that standing record."
  },
  {
   "name": "CHP_BTM_PCT_BY_SECTOR['merchant']",
   "where": "constants.py CHP_BTM_PCT_BY_SECTOR",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": 35.0,
   "source": "merchant CHP behind-the-meter share \u2014 industrial/commercial re-derived from EIA-923 Schedule-8 (S3), merchant retained at its prior fitted value (audit C-4; W1d marker)",
   "root_cause": "no independent merchant-CHP host-load source found yet \u2014 replace when one exists (constants.py comment); survey of candidate sources + recommended EIA-923 Schedule-8 intake path: docs/records/misc/merchant-chp-host-load-memo-2026-07.md; open: https://github.com/jessicacohen554-cyber/market-simulator/issues/1335"
  },
  {
   "name": "reliability_floor coefficients",
   "where": "data/raw/reference/reliability_floor_coeffs_ERCOT.csv",
   "identification": "measured-physical",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "source": "temperature/net-load day-gated commitment floors, CAMPD-derived (frozen derive script); the three Spearman-rho sign-flip limbs are R1-disabled (r1_disabled=True, ships off)",
   "note": "D-8 \u00a72B: the three sign-flip limbs (PJM ComEd/CC_REGULAR, CAISO SP15/ST_GAS + SP15/CC_REGULAR tmax) were UNIDENTIFIED out-of-training and are now permanently disabled under rule R1 (B-LIMB-1; derive R1_DISABLED_LIMBS). Remaining R6-keep drift limbs (drift >gate, no sign flip): ERCOT Houston CT +13.5%, PJM EMAAC ST_GAS +35.8%, SWMAAC CT -15.6%, ATSI rho-decay limbs \u2014 kept enabled with this caveat; re-derive trigger is the 2026 CAMPD publication (a source-data change), never a residual (rule 23)"
  },
  {
   "name": "offer_2023_discrete_peak_scale (ercot-235 k_peak, re-selected at ercot-236)",
   "where": "run_config.scenario_config.offer_curve_by_group (2023-discrete values: gas-group peak/phys_peak/peak_ladder multipliers x33.0 vs the cross-year keeper recipe, applied UNDER the SWCAP offer-domain clip ercot_offer_swcap_clip)",
   "identification": "residual",
   "lineage_solves": "11 solves (ercot-235 rounds 1-4, PRECOMMIT-ercot235) + 5 solves (ercot-236 D-1 diagnosis, V-0/V-1 verification legs and the {27,33} re-bracket, PRECOMMIT-ercot236-h4097-shed-repair-2026-08-25.md)",
   "value": {
    "k_peak": 33.0,
    "k_eh": 1.0
   },
   "n_scalars": 1,
   "source": "rule-1-sanctioned offer-curve tuning surface, 2023-discrete under the OWNER ORDER of 2026-08-25 (ercot-235 log entry: solve 2023 for its own conditions; rule-16 waiver invoked; Q-B/R-A superseded by the owner). Re-selected on the SWCAP-clipped surface after the ercot-236 h4097 repair (the clip is a market constant + an epsilon-class tiebreaker, NOT a fitted value): min |official C3a-2023| over the clean precommitted candidates {24, 27, 30, 33}. At k=33 the top gas peak tranches saturate at the clip level $4,999.99 \u2014 exactly where the MEASURED 2023 evening asks saturate (ercot-161/162: SCED asks $3.4-5k at the $5k cap), so the tuned surface expresses the documented conduct: a scarcity wall AT the cap, not past it",
   "root_cause": "the adjudicated 2023 model-class conduct object (C3c exceptions ledger lineage; ercot-209/211/216): an LP with competitive offers cannot form the ECRS-era scarcity equilibrium, so the 2023-discrete level is carried as an explicit tuned parameter, identified in-sample on 2023 only; no held-out validation exists",
   "applies_to_years": [
    2023
   ]
  },
  {
   "name": "netload_drag_layup_window_mask",
   "where": "run_config.scenario_config.netload_drag_layup_window_mask",
   "identification": "measured",
   "value": true,
   "source": "NOT A DEGREE OF FREEDOM \u2014 a boolean gate on a measured-conduct overlay with zero scalars. The dated windows, the per-unit capacity shares and the 0.90 out-of-merit threshold all live in the frozen derive layer (rule 23 [R-FROZEN-DERIVE]: scripts/lib/outage_detect.py + scripts/data/derive_campd_unit_outages.py --merit-order-guard); the extract is consumed, never re-derived, and it is the SAME accumulator, unit->plant routing and capacity denominator as the unit-outage availability overlay, so the two shares are additive by construction. Listed for visibility under rule 21 [R-DOF]; n_residual is unchanged."
  },
  {
   "name": "ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU",
   "where": "config/constants.py; gates ScenarioConfig.ercot_ep_gas_basis_corroborated",
   "identification": "measured-distribution",
   "lineage_solves": "0 solves \u2014 set ex ante from the input data, never swept",
   "value": 1.0,
   "note": "ercot-261. The maximum |disagreement| in $/MMBtu between two INDEPENDENT measurements of the same quantity \u2014 the EIA N3045TX3 state survey and the EIA-923 Schedule-5 TX quantity-weighted plant receipts \u2014 for a month's survey print to be admissible as an HOURLY delivered-gas level. Identified on the observed disagreement distribution over all 84 months 2019-01..2025-12: the two series agree within $0.85 in 82 of them and the only outliers are 2021-02 ($13.77) and 2021-12 ($3.47), with NO month in the factor-4.1 empty gap between. 1.00 sits inside that gap. It reads FUEL SERIES ONLY \u2014 never a price, load, dispatch or model output \u2014 so it is not an input rescaled to a residual (rules 1 [R-STRUCT] / 13 [R-MEASURED]), and it was registered in the PRECOMMIT above the solve and never swept against a criterion. It selects which MEASURED month is admissible; the measurement it admits carries zero DOF."
  }
 ],
 "ercot255_note": "UNCHANGED at n_entries=10 / n_residual=7. ercot_zonal_spread_ep_referenced contributes NO ledger entry: it carries no value to fit (the reference is the already-loaded ep_basis, and no weighting choice exists), so there is nothing to identify. Rule 21 [R-DOF]."
}
```


## 8. Execution

Seven shards, one per year 2019–2025 (rules 34(c) / 36), prompts in `docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-11.md`, pinned to the SHA of the commit carrying this file. Each runs `replay_keeper.py results/calibration/r_ercot10_parish_span --years <Y>` with no overrides (the arm is the data and the resolver), checks the input sha256s below, the config signature and the heat-rate log line, and pushes its full bundle. The parent composes (`_r_ercot_compose_span.py --side arm --chp-off`), runs `stamp_config_partition --check`, attests, registers (`dashboard_add_run.py --no-prune`), runs `calibration_verdict` per year on the keeper's scoring basis, and writes the RESULT.

**Input sha256 at the pinned SHA:**
```
6c4dcbe798991489e1cbf5594e4bc71bd62dbfcf279f98cce93c1c8b6f1e7638  data/raw/ercot-thermal-dam-availability.csv
837fea435f73dbe33ba7e5b2ec435f81cbbba0dc832e898b9620ae6dfca8a60b  data/raw/ercot-thermal-dam-availability-hourly.csv
bd7ea9fdbfef60c772ca75c9a2e8c0af0b790a5084c7cd00e88667a25c4face0  data/raw/ercot-thermal-dam-availability-site-hourly.parquet
be846bf880d4f05697acf7c87f5ba6c9bc884c87b480b6674731c495467d5cd4  data/raw/campd-unit-outages.csv
d0d03bf0a0d2b6974bdfeff58c942662b3673e9f88df79ed6c2a69ea8278aeef  data/raw/campd-unit-outages-short.csv
679880f766187a949dbca28a87fd35c135f889a341fb761da165457138ddf8f1  data/raw/campd-unit-outages-shortgas.csv
40a4b2961a9589871d70684a8766c5a9a72c8be8553d70c52574fe467ac2ff74  data/raw/campd-unit-outages-hourgrain.csv
11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f  data/raw/campd-unit-outages-short-hourgrain.csv
43b672412fd4d90fdb3e8df3775cebd4cb9703d9dced0a213821cf1dac40a431  data/raw/campd-unit-outages-shortgas-hourgrain.csv
ed9091397f4804fa4533218539bb6e449dd6231fbf7978a52a63a94dd2f2dc83  data/raw/reference/custom-bin-assignments.csv
89e807b245c3fafdc7124f860f6396174d834185f821ca26d268ef8cfe60ff2c  data/raw/campd-partial-outages.csv
3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a  data/raw/campd-partial-outages-shaped.csv
3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c  data/raw/campd-partial-outages-shaped-dayguard.csv
b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426  data/raw/campd-partial-outages-units.csv
721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6  data/raw/reference/ercot-dam-plant-crosswalk.csv
0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10  data/raw/reference/ercot-dam-gas-site-seeds.csv
b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv
633a19b855eb0302a10ac49272b6aecbe162fac013c591681637c1c19f042f7c  data/raw/_processed-legacy/campd_st_heat_rates_ERCOT.csv
```
