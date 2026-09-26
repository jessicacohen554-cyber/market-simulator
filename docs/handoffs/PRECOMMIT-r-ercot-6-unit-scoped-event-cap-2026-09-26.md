# PRECOMMIT — R-ERCOT-6: the ercot-174 unit-scoped window × partial composition, re-tested against the repaired partial layer

**Session:** R-ERCOT-6, 2026-09-26. **Written before any solve.** The pinned SHA is the commit that carries this file.

**Keeper and control:** `2026-09-25-r-5-hour-grain`, bundle `results/calibration/r_ercot5_hourgrain_span`, 2019–2025. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)); no control solve is spent.

**Owner leave (rule 28(a), re-opening an R cell):** granted this session on the zero-LP card of `FINDING-r-ercot-6-double-count-retest-2026-09-26.md`. The option chosen was verbatim "Arm B + hour-grain mask". **Promotion stays the owner's call** (rules 31/35).

## 1. The mechanism (an existing registered field, zero new scalars)

**Field:** `ScenarioConfig.ercot_dam_availability_event_cap_unit_scoped` (ercot-174; default `False`; matrix R 2026-08-06, re-opened here). **No new field** (rule 19).

**What it does:** inside the ERCOT-148/149 measured-event precedence cap, the window-layer ceiling and the plant partial plateau compose by `min()` at the hours where both layers carry the SAME CAMPD unit. That is where the product removes one unit's downtime twice. Everywhere else they compose by the incumbent product. The result is bounded: product ≤ result ≤ min.

**One construction repair, made before any solve (rule 14 consistency):**
- `outages.unit_outage_active_units` now takes `hour_grain` and forwards it to `unit_outage_csv_for_iso`.
- `fleet.arrays` passes the cap's own `_hg`.
- Before this, the shared-unit mask was read from the day-grain window file while the R-ERCOT-5 keeper's window factor is hour-grain, so the mask claimed shared hours the factor no longer removes.
- Measured effect ≤ 0.012 TWh/yr of coal capability. It is repaired so the arm is the construction it claims to be, not for its footprint.
- Default `False`: byte-identical.
- Tests: `tests/unit/data/test_outages.py::UnitOutageActiveUnitsHourGrainTest` (2 new; the file's 94 pass).

**Why it is structural (rule 1).** Two measured layers both remove the same unit's downtime at the same hour, so their product counts it twice (rule 19). The fix is kept or rejected on that identity, never on the residual. Zero new parameters (rule 21).

**Rule 13 forward story.** Both layers are the backcast measured-availability inputs they already were. The composition rule is a property of the two extracts' unit ids, identical for any year's extract.

## 2. Zero-LP seam (fleet-only; FINDING-r-ercot-6 §1)

**A/A null:** field OFF at the edited HEAD vs the pre-edit build, 2023: all 244 stage arrays byte-identical.

**Arm reproduction:** field ON at the edited HEAD equals the zero-LP `hgmask` variant, 2023, on all 244 arrays.

Coal capability, arm vs keeper (TWh):

| year | lift | ≤ own CEMS | above | below-CEMS gap A → B | in-merit | scar MW | CC lift |
|---|---|---|---|---|---|---|---|
| 2019 | 5.13 | 2.72 | 2.41 | 3.83 → 1.11 | 3.43 | 76 | 1.08 |
| 2020 | 4.19 | 1.58 | 2.62 | 2.21 → 0.63 | 1.88 | 0 | 1.31 |
| 2021 | 6.40 | 3.69 | 2.70 | 4.67 → 0.97 | 5.46 | 443 | 1.07 |
| 2022 | 4.26 | 2.52 | 1.74 | 3.30 → 0.79 | 3.68 | 277 | 0.58 |
| 2023 | 3.67 | 1.04 | 2.62 | 1.73 → 0.69 | 1.84 | 70 | 0.72 |
| 2024 | 5.03 | 1.96 | 3.07 | 2.75 → 0.79 | 2.98 | 485 | 1.40 |
| 2025 | 4.22 | 2.15 | 2.07 | 2.86 → 0.71 | 3.33 | — | 1.80 |

Table: `docs/handoffs/r-ercot/r_ercot6_unitscoped_seam.txt` (variant `Bh`).

## 3. G-DRIFT (keeper solve SHA `d20ca118d439c33e7813ffd6ba5f76b11c67c2a0` → pinned HEAD)

`git diff d20ca118 <pinned> -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/replay_keeper.py scripts/lib data/raw/_validation-source data/raw/reference` covers 21 files (+1,430 / −67). `replay_keeper.py` and `scripts/lib` are unchanged. Every hunk is classified against the keeper's seven `run_config_<Y>.json`; none of the 12 new fields appears in any keeper year, and all 12 default to `False`.

**The 12 new default-off `ScenarioConfig` fields — INERT.**
- The fields: `unit_outage_membership_repair`, `unit_outage_unit_fuel_routing`, `nuclear_dormancy_defers_to_vintage_exit`, `nwpp_demand_plant_basis`, `pjm_zonal_gas_basis_skip_923_priced`, `wefor_residual_short_screened_coal`, `coal_committed_nested_on_mustrun`, `caiso_import_gas_coupling_ladder_only`, `caiso_intertie_gap_fill_measured_gas`, `reliability_floor_layup_window_mask`, `caiso_intertie_gap_fill_measured_dam` and `cc_eia923_identity_emission_basis`.
- Their point-of-use branches, all gated off for ERCOT:
  - `fleet.arrays`: nuclear dormancy; short-screened coal WEFOR relief, whose callee raises on ERCOT; membership / unit-fuel selector kwargs, PJM files only.
  - `outages.py`: the memberrepair selector, `unit_outage_short_screened_*`, and the layup selector args. For ERCOT the layup selector returns early, before the new branch.
  - `campd_bins.py`: the identity CO2 basis and the coal committed-nested band.
  - `interchange/core.py`: `layup_removed=None`.
  - `run_calibration.py`: `_reliability_floor_layup_shares` returns None; the `resolve_coal_budget_arms` refactor gives (False, False) for ERCOT; the `apply_pjm_zonal_gas_basis` `skip_cells` path is PJM-only.
- The cache-key drop value is `"False"` for all of them, so the keeper's key does not move.

**Other-ISO branches — INERT.**
- NWPP: `eia930/demand.py` and `envelopes.py` plant-basis code, `runner.py` / `run_calibration_full.py` `nwpp_demand_plant_basis`, and `nwpp_plant_basis_energy.csv`.
- CAISO: the intertie DAM gap-fill (`envelopes.py`, `interchange/caiso.py` + `spec.py`, `neighbor_price.py`, `fuel/electric_power.py`) and `wecc_intertie_lmp_hourly_CAISO_gapfill_dam.parquet`. The `measured_import_hub_prices` `reset_index` refactor gives the same values.
- PJM: `fuel/resolve.py` / `basis/pjm.py` `skip_cells`. It is also a no-op because `pjm_zonal_gas_basis` is false.

**Metadata / diagnostics — INERT.**
- `config/paths.py`: `EIA_923_GENERATION_FUEL_*`, unread.
- `resolved_inputs.py`: companion-gate kwargs, provenance only.
- `floor_mechanisms.EXTRA_ZERO_FORCING_FIELDS`: the ablation construction only.

**The one UNGATED shared-code change — INERT for ERCOT by data.**
- The change: `campd_bins._APPLIED_MEASURED_FLAGS = {ok, eia923_identity}`.
- Why it is inert here: no ERCOT measured heat-rate artifact carries an `eia923_identity` row. Verified with `grep -c` = 0 on all 8 `_processed-legacy/campd_{cc,ct,st,coal}_heat_rates_ERCOT{,_units}.csv`.
- It must be re-checked if an ERCOT heat-rate artifact is ever re-derived.

**The arm's own hunks — gated.**
- `outages.unit_outage_active_units(hour_grain=)` and the `arrays.py` call site.
- They are gated by `ercot_dam_availability_event_cap_unit_scoped`, which is `false` in all seven keeper years. A/A null: byte-identical.

**Addendum (rebase onto main `d2256cef` before pinning).** Four further files on the path, all INERT:
- neiso-117 `reconcile_floors_to_yard_budget` (`coal_fuel_inventory.py` plus its call in `run_calibration.py`): runs only inside `if _coal_plant_armed:`. `resolve_coal_budget_arms` returns (False, False) for ERCOT because both coal-inventory flags are false in all seven keeper years.
- `scripts/lib/key_provenance.py` and `forecast_parity_registry.py`: governance census / parity tooling, not the solve path.

**Verdict: nothing LIVE. Form 4 is valid; the committed keeper is the control.** The subagent-run audit was spot-checked by the parent on the ungated hunk.

## 4. Sealed predictions (arm vs keeper, per year, P1)

**Keeper baseline** (RESULT-r-ercot-5):

| year | LW $/MWh | slack MWh | h > $1k | coal TWh | CC+ST TWh | C3a | C3b |
|---|---|---|---|---|---|---|---|
| 2019 | 74.94 | 5,806 | 53 | 64.18 | 158.42 | +59.8 % | 1.334 |
| 2020 | 28.48 | 0 | 5 | 51.70 | 153.25 | +11.7 % | 0.361 |
| 2021 | 169.89 | 6,430 | 123 | 71.74 | 125.82 | +2.6 % | 0.136 |
| 2022 | 68.44 | 0 | 18 | 76.70 | 138.47 | −8.1 % | 0.164 |
| 2023 | 59.47 | 0 | 59 | 59.89 | 164.59 | −7.5 % | 0.133 |
| 2024 | 29.24 | 454 | 2 | 56.84 | 163.45 | −5.6 % | 0.120 |
| 2025 | 33.79 | 0 | 0 | 64.61 | 156.89 | −6.9 % | 0.108 |

**P1 (every year): coal rises, bounded by the in-merit lift.**
- Δcoal ∈ [+0.2, in-merit]: 2019 ≤ 3.43; 2020 ≤ 1.88; 2021 ≤ 5.46; 2022 ≤ 3.68; 2023 ≤ 1.84; 2024 ≤ 2.98; 2025 ≤ 3.33 TWh.
- CC+ST falls by Δcoal ± 0.7 TWh.

**P2 (every year): no price-side quantity rises.**
- LW price change ≤ +0.3 %.
- P1 slack and the count of hours > $1k do not rise.

**P3 (every year): the price falls by at most these amounts.**
- ≤ 3 % in 2020, 2022, 2023 and 2025, where the scarcity-hour lift is ≤ 277 MW over ≤ 59 h.
- ≤ 8 % in 2019, 2021 and 2024.

**P4 (train tier): the determination stays CALIBRATED.** C3a moves cheaper by ≤ 2.5 pts in every train year and stays inside ±10 %:
- 2023 ∈ [−10.0, −7.5]
- 2024 ∈ [−8.1, −5.6]
- 2025 ∈ [−9.4, −6.9]

**The named risk:** 2023 crossing −10 % would flip the train determination to NOT-YET. It is reported, not reverted (§5).

**P5 (C1 coal):**
- The 2023/2024 coal shortfall (−2.40 / −1.93 TWh) narrows.
- The 2025 coal overshoot (+1.23) grows, and so does 2022's (+4.78, validation).
- 2019/2020 stay NOT-YET; their COAL_PRB gap narrows by ≤ the in-merit lift.

**P6 (C8):** no forced-share gate changes a determination.

## 5. Decision rule (fixed now; identical to R-ERCOT-5 §5)

**Rule 1 governs.** The composition is kept or rejected on the double-count identity, not on the scores.
- If every train year stays CALIBRATED, the recommendation is **promote**, whatever the validation years do.
- If a train year flips to NOT-YET, report it at full magnitude with its root cause (rule 14). Put it to the owner **with no recommendation to revert**.

**Promotion is the owner's call** (rules 31/35). Nothing is pruned without that ruling.

## 6. DOF ledger (carried VERBATIM from the keeper attestation)

- 12 entries, 7 residual.
- This arm adds **no entry**: the composition keys on the two extracts' CAMPD unit ids and carries no scalar.
- Offer-curve band multipliers are unchanged leg-for-leg (rule 1(c)); `config_partition_overrides` are carried from the keeper untouched.

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

## 7. Execution

**Shards:** seven, one per year 2019–2025 (rules 34(c) / 36). Prompts: `docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-6.md`, pinned to the SHA of the commit carrying this file.

**Each shard:**
- runs `replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years <Y> --set ercot_dam_availability_event_cap_unit_scoped=true`;
- checks the input sha256s (now including `campd-partial-outages-units.csv`), the per-year config signature and the unit-scoped log line;
- pushes its full bundle (`dispatch/<Y>_P1.parquet` included) through a `.gitignore` negation and a plain `git add`.

**The parent then:**
1. Fetches and verifies each leg the moment it lands.
2. Composes with `scripts/probes/_r_ercot_compose_span.py --side arm --chp-off`, with the field added to MUST_AGREE.
3. Runs `stamp_config_partition.py --check`.
4. Attests.
5. Registers with `dashboard_add_run.py --no-prune`.
6. Runs `calibration_verdict --years` per tier.
7. Updates the ERCOT matrix cell and writes the RESULT and calibration-log entry.
8. Archives the shards and asks the promotion question.
