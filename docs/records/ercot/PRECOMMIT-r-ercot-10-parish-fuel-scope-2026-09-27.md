# PRECOMMIT — R-ERCOT-10: W A Parish partial-outage derate, fuel-scoped to its coal units (rule 14)

**Session:** R-ERCOT-10, 2026-09-27. **Written before any solve.** The pinned SHA is the commit that carries this file.

**Keeper and control:** `2026-09-27-r-8-fusco`, bundle `results/calibration/r_ercot8_fusco_span`, 2019–2025. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)). No control solve is spent.

**Authority:** owner ruling at R-ERCOT-9 (FINDING-r-ercot-9 §6), verbatim *"Hold k=33, work validation (Recommended)"*. This lane works the physical validation-year items. `offer_curve_by_group` is untouched (rule 1(c)), and promotion is the owner's call (rules 31/35).

## 1. Phase 0 (zero LP): what the three validation items are

| item | named physical object | verdict |
|---|---|---|
| (a) 2019/2020 COAL_PRB C1 −11.2 / −14.6 TWh | **(i)** The per-plant coal offer levels are measured on 2024–25 SCED, with no fuel term, and applied to 2019–22 (FINDING-r-ercot-3 §2). **(ii)** At **W A Parish the partial-outage derate is built from the facility-summed CEMS**, which includes the gas steam units WAP1–4 (0.9–2.2 TWh/yr), and is then applied to the coal-only 2,443 MW bin. | (i) no admissible arm on disk. 60-Day SCED exists only from 2023-03. 60-Day DAM curves 2018–22 are on disk (`data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_*`), but Parish and Martin Lake submit **no** DAM energy curve in any year, and turning DAM into SCED would need a new bridge with DOF. `coal_offer_level_rebasis` is R. **Owner data decision.** (ii) **ARM (this PRECOMMIT).** |
| (b) 2022 CC_REGULAR C1 −10.05 TWh | Decomposed as COAL_PRB **+4.78** (Martin Lake +4.2, Coleto +1.7) plus a benchmark-to-load basis residual of **−4.37 TWh** net. The benchmark total is 433.50 against model and EIA-930 generation of 429.1 / 428.7. The driver is the same static coal offer conduct against HH $6.45: 8.5 of 9.96 GW of available coal sits below the CC p25. No CC plant is missing from the fleet, and CC availability does not bind (218.8 TWh available vs 125.8 dispatched). | No admissible arm. Same data ask as (a)(i). The basis residual is a scorer-side question for the owner. |
| (c) Decker Creek 3548 steam 1–2 | The steam units (321 + 405 MW, retired 2020-10 / 2022-03) are in the fleet in **no** year. The 206 MW CT row is relabelled ST_GAS in 2019–22 by the EIA-923 class override. Gap ≈ 0.45 TWh/yr, 2019–21 only. ST_GAS already runs +52 % / +86 % over actual in 2019/20. | **Not worth an arm.** The fix is a plant-code seam touching ≥ 5 plant-keyed consumers, and it cannot help C1. Routed as an open rule-14 fleet item. The bench file also double-counts 3548 (CT-only CEMS flag). |

Probes (committed, zero LP): `scripts/probes/_r_ercot10_{coal_headroom,dam_coal_levels,cc2022_merit,decker_seam}.py`.

## 2. What changes (input correction, rule 14; no new `ScenarioConfig` field)

**Defect.** `scripts/data/derive_partial_outages.py` builds each candidate's CF series from `campd.plant_hourly_grid(df, code, yr)`, which sums **every** CEMS unit at the plant code. At W A Parish (3470), the COAL bin holds WAP5–8, while WAP1–4 are gas steam in no bin. The gas units' output enters the plateau's normal-ceiling reference, and the resulting derate is applied to the coal bin. Measured:
- CEMS hourly p99, coal vs facility: 2,656 vs 3,599 MW (2019); 2,634 vs 3,526 MW (2024).
- 2019-01-04: coal ran at a 1,824 MW daily max, but the committed day-guarded derate (0.542 × 2,443) allowed 1,324 MW.

This is the rule-14 misaligned-boundary case. The source is right; its boundary was not the bin's.

**Fix.** The derive reads each plant's unit fuel families from the unit-level CAMPD extract (`primaryFuelInfo`). **Only** at a plant whose units span both families, the series becomes the unit-level sum over the bin's own family. Every other plant keeps the facility series byte-for-byte.

**Regenerated** (`--years 2019..2026 --emit-units --emit-shaped --emit-shaped-dayguard`): `campd-partial-outages{,-units,-shaped,-shaped-dayguard}.csv`.
- **2018 rows are kept as committed.** CAMPD TX 2018 is no longer on disk (BLOAT-S2), and no ERCOT backcast solves 2018.
- **Reproduction proof.** At HEAD without the fix, the derive reproduces every committed 2019–2026 row except one set: **Jack Fusco 55357**, whose rows (dayguard 15 in 2022 and 10 in 2024; 675.6 MW CC) R-ERCOT-8 left stale when it added Fusco to the bin sheet. Rule 14 carries them in too. With the fix, **only 3470 and 55357 rows differ** from the committed files, and row order is preserved.
- **Fuel-scope log.** The only plant scoped is 3470, in every year: `['WAP5'..'WAP8'] of ['WAP1'..'WAP8']`.

**Rule 23.** This is a construction-defect repair, not a residual-driven re-derive. The plateau constants are untouched.

**Rule 13.** CEMS unit fuel and output regenerate for any year, and the overlay is backcast-only, as before.

## 3. Zero-LP footprint (`fleet_only` rebuilds of the keeper recipe, committed vs corrected extracts)

**Parish COAL_PRB available energy (Σ pmax × availability), TWh:**

| year | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| keeper | 14.525 | 12.641 | 12.660 | 12.133 | 13.293 | 13.868 | 15.793 |
| arm | 16.985 | 14.548 | 13.151 | 11.549 | 13.682 | 14.137 | 16.530 |
| Δ | **+2.460** | **+1.907** | +0.491 | **−0.584** | +0.389 | +0.270 | +0.737 |
| actual (EIA-923 net) | 14.33 | 10.81 | 14.82 | 13.12 | 10.74 | 12.17 | (CEMS gross 14.72) |

- Every other coal plant: |Δ| = 0.0000 TWh.
- **2022 is a real deeper derate.** With the gas units removed, genuine coal partial outages are no longer masked.
- **Fusco:** derated **175 GWh** (2022) and **74 GWh** (2024) of capability. Its CC energy is not in the coal census.

## 4. G-DRIFT (keeper solve SHA `5696a72ce54327901681016a417e4900bba70db1` → origin/main `a6347bd8`)

- 43 files changed and every hunk is classified (subagent audit, spot-checked).
- **INERT:** six new default-off fields, all absent from every keeper year (`unit_outage_full_rederive`, `campd_unit_fuel_split`, `coal_fuel_inventory_take_floor`, `nyiso_li_seam_posted_limit_cap`, `caiso_intertie_partial_year_measured`, `pjm_offer_midcurve_shape_segments`). No existing default flipped.
- **INERT:** the `retiree_cems_cap` deletion (the keeper records False; `replay_keeper` drops it); the zero-width take-slack LP columns; the NYISO, CAISO, PJM, MISO, NWPP and SOCO branches and artifacts; `forecast_parity_registry`.
- **SCORING-ONLY:** `_validation-source/actual_lmp.json` ERCOT 2019–2025 and `actual_lmp_zonal_ERCOT.parquet` (R-ERCOT-9 clock repair). No solve path reads them.
- **Verdict: nothing LIVE except this lane's own edits (§2). Form 4 is valid.**
- **Scoring basis.** The arm registers on the repaired clock, so every C3a/C3b comparison is made against the keeper **re-scored on the same basis**. Where only the old-basis number is available, it is labelled.

## 5. Sealed predictions (arm vs keeper, P1)

**Keeper baseline:** RESULT-r-ercot-8 table. C3a on the new clock basis is the R-ERCOT-9 §4 estimate: 2019 +27.0, 2023 −20.6, 2024 −8.8, 2025 −9.2 %.

- **P1 (Parish).** Parish P1 generation moves in the direction of Δ-capability and by no more than its size.
  - 2019: +0.3 to +2.46 TWh; 2020: +0.3 to +1.91 TWh; 2021, 2023, 2024 and 2025: 0 to +Δ.
  - 2022: −0.58 to 0.
- **P2 (C1 coal).** COAL_PRB (model − actual) narrows in 2019/2020 by 0.3–2.5 TWh and **stays a C1 FAIL** (−11.2 / −14.6 TWh is far larger than any Δ).
  - CC_REGULAR's 2019/2020 overshoot narrows by ≤ the coal gain.
  - 2022's CC_REGULAR −10.05 moves by ≤ 0.6 TWh and stays a FAIL.
- **P3 (price).** Added cheap coal lowers or holds price.
  - LW moves −4 % to +0.3 % in 2019/2020 and −2 % to +0.3 % in 2021 and 2023–2025.
  - 2022 moves −0.3 % to +2 %.
- **P4 (tail).** Slack and h > $1k do not rise in any year except 2022, where each may rise by ≤ 3 h.
- **P5 (train tier; the determination).**
  - 2023 stays NOT-YET: C3a ∈ [−22.0, −20.0] (new basis), C3b 0.29 ± 0.03.
  - 2024: C3a ∈ [−9.8, −8.6].
  - **2025: C3a ∈ [−10.2, −9.1] — a NAMED RISK.** It sits 0.8 pts inside the ±10 % band on the new basis, and +0.74 TWh of $20 coal lowers price. A crossing below −10.0 % would flip 2025 to NOT-YET.
  - C3b moves ≤ 0.02 in 2024/2025.
- **P6.** No C8 forced-share gate changes a determination.
  - The validation years 2019/2020/2022 stay NOT-YET on C1.
  - 2019 C3a improves or holds, landing in [+18, +27] % on the new basis.

## 6. Decision rule (fixed now)

**Rules 14 and 1 govern.** The repair is kept on its identity (the bin's own units), never on the scores.
- **Promote.** If 2024 and 2025 stay CALIBRATED, the recommendation is **promote**. The ISO still reads NOT-YET on 2023, as ruled.
- **Train-year flip.** If 2024 or 2025 flips to NOT-YET, it is reported at full magnitude with its root cause, and put to the owner **with no recommendation to revert**. A correct Parish availability exposing a price bias is a rule-14 discovery.
- **Owner's call.** Promotion is the owner's (rules 31/35), and nothing is pruned before the owner rules.

## 7. DOF ledger (carried VERBATIM from the keeper attestation; this arm adds NO entry)

A fuel-family unit filter carries no free scalar. The offer-curve band multipliers are unchanged leg for leg (rule 1(c)), and `config_partition_overrides` are carried from the keeper untouched.

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
   "source": "EWMA half-life (days) and gain beta of the daily spike-frequency expectation P_hat, SSE-fit of implied_P(d) = evening storage offer p50 / ordc_voll on P_hat(d) over admissible days 2023-06-10..12-31 on the pre-registered grid (PRECOMMIT-ercot221-adaptive-expectation-2026-08-18.md Amendment 1 family v2; artifact results/calibration/ercot221_adaptive_phase0.json). The armed path consumes only the model's own pass-1 price path (Amendment 4) \u2014 the measured surface is identification evidence only. Phase-0 v1+v2 FAILED their gates; Phase-1 entered on owner instruction (recorded in the precommit Amendment 2), so these constants are additionally flagged by that standing record."
  },
  {
   "name": "CHP_BTM_PCT_BY_SECTOR['merchant']",
   "where": "constants.py CHP_BTM_PCT_BY_SECTOR",
   "identification": "residual",
   "lineage_solves": ">=165 solves (audit \u00a75.1)",
   "value": 35.0,
   "source": "merchant CHP behind-the-meter share \u2014 industrial/commercial re-derived from EIA-923 Schedule-8 (S3), merchant retained at its prior fitted value (audit C-4; W1d marker)",
   "root_cause": "no independent merchant-CHP host-load source found yet \u2014 replace when one exists (constants.py comment); survey of candidate sources + recommended EIA-923 Schedule-8 intake path: docs/handoffs/merchant-chp-host-load-memo-2026-07.md; open: https://github.com/jessicacohen554-cyber/market-simulator/issues/1335"
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

**Seven shards**, one per year 2019–2025 (rules 34(c) / 36), from `docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-10.md`, pinned to the SHA of the commit carrying this file.

**Each shard:**
- runs `replay_keeper.py results/calibration/r_ercot8_fusco_span --years <Y>` with **no `--set`**, because the arm is the data;
- checks the input sha256s below, the config signature and the bin-count log line;
- pushes its full bundle.

**The parent then:**
1. Fetches and verifies each leg.
2. Composes (`_r_ercot_compose_span.py --side arm --chp-off`).
3. Runs `stamp_config_partition --check`.
4. Attests.
5. Registers (`dashboard_add_run.py --no-prune`).
6. Runs `calibration_verdict` per tier and per year.
7. Writes the RESULT and the calibration-log entry, and archives the shards.

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
417e596cf73d70417d4b3f74abffa80e2f384cb9388bbf9d6ad200ee9cd86d90  data/raw/reference/custom-bin-assignments.csv
89e807b245c3fafdc7124f860f6396174d834185f821ca26d268ef8cfe60ff2c  data/raw/campd-partial-outages.csv
3f1b421d7337e971fc265f9103bc3377ebc0857fd4876fb58d4fbb356c89e40a  data/raw/campd-partial-outages-shaped.csv
3c384fc0c465b686f5b520334d335c3bfa0058c2c129e6416563af25fffe719c  data/raw/campd-partial-outages-shaped-dayguard.csv
b6145d5a3d01373356bde6138a6f4ea7d284346b613125a0ac63d167d92cd426  data/raw/campd-partial-outages-units.csv
721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6  data/raw/reference/ercot-dam-plant-crosswalk.csv
0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10  data/raw/reference/ercot-dam-gas-site-seeds.csv
b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv
```
