# PRECOMMIT — R-ERCOT-8: Jack Fusco / Brazos Valley (55357) joins the ERCOT fleet, plus the small coverage repairs

**Session:** R-ERCOT-8, 2026-09-27. **Written before any solve.** The pinned SHA is the commit that carries this file.

**Keeper and control:** `2026-09-25-r-5-hour-grain`, bundle `results/calibration/r_ercot5_hourgrain_span`, 2019–2025. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)). No control solve is spent.

**Authority:** owner ruling 2026-09-26 on FINDING-r-ercot-7 §2, verbatim "Add Fusco, test in next lane". The owner accepted the BVE → 55357 match (name + owner Calpine). Promotion stays the owner's call (rules 31/35).

## 1. What changes (input corrections, rule 14; no new `ScenarioConfig` field)

**Jack Fusco Energy Center (EIA 55357), the material repair.**
- **Membership evidence.** ERCOT's 60-Day DAM Gen Resource Data lists `BVE_CC1_1/_2`, SP `BVE_CC1`, QSE `QCALP` (Calpine) in every file 2023–2026. EIA-860 gives NERC `TRE`, Fort Bend County. EIA's BA field `MISO` is the outlier. The CAMPD facility name is "Brazos Valley Energy, LP".
- **Bin-sheet row:** `CC_REGULAR, Houston, 675.6 MW, 2x1 F-class`.
  - Capacity is the EIA-860 **nameplate**. Every sheet row carries nameplate (Hidalgo 551.3, AVR 575.0, Colorado Bend II 1230.3, …), and one basis is kept (rule 19). The 602 MW net summer named in the handoff would be the only summer-basis row in the sheet.
  - Tranche and commitment columns copy the class peer Tenaska Frontier (2x1 F-class, Houston). They are an analog default, not a fitted value, and are stated as such.
  - Sheet HR 7.34 is the eGRID-2023 PLHTRT fallback. It is never applied while `measured_cc_heat_rates` is armed and the measured row exists.
- **Heat rate (measured, rule 13 input).**
  - `campd_cc_heat_rates_ERCOT.csv` gains 8 rows for 55357: pooled plus 2019–2025.
  - Net basis: pooled **7.3214** MMBtu/MWh (gross 7.1018 × parasitic 0.97), per year 7.19–7.39.
  - Boundary gross/net 1.031 is inside the guard band. Flag `ok` in every row.
  - Produced by the derive's OWN estimator (`docs/records/ercot/r-ercot/r_ercot8_fusco_cc_hr.py`) on Fusco's units, which the EIA-860 BA filter drops.
  - Every other row is frozen (rule 23). A whole-file re-derive at HEAD does not reproduce it: 55172 flips to `eia923_identity`, 55320 / 3631 move.
- **DAM crosswalk.** `BVE_CC1` is re-matched from Lost Pines 55154 (accepted=0) to 55357 (accepted=1) by a gas-site seed (`ercot-dam-gas-site-seeds.csv`). The edit is surgical: one row, exactly what the builder emits for it.
  - A full rebuild at HEAD is unsafe, for two reasons:
    - it drops all 26 coal rows (a COAL-SUB break in `build_ercot_dam_resource_crosswalk.py`; not fixed here, reported);
    - Fusco's `JACK` token unseats `JACKCNTY_CC1` (n_strong 1 → 2).
  - So `JACKCNTY_CC1 → 55230` is pinned by seed at its existing accepted identification.
- **Membership (rule 19: one boundary for fleet, benchmark and fuel pricing).** `zone_assignment._ercot_dam_admitted_zones` admits accepted DAM-crosswalk plants that the ERCO-BA geography misses, zoned by the same eGRID coordinate rule. 55357 → Houston.
  - Inert before the BVE acceptance: 1,406 members either way.
  - It admits exactly one plant after.
  - Without it, the fleet would carry Fusco while the EIA-923 C1 benchmark excluded its 2.34–3.65 TWh/yr of net generation.
- **CAMPD unit outages.** 40 standard and 30 short-gas windows for 55357 are inserted into the hour-grain files and their day-grain projections, from each sidecar's own invocation at HEAD. That re-derive reproduces every non-55357 row value-for-value. `campd-unit-outages-short*` (coal) and the partial-outage layers gain no Fusco rows: Fusco is a cycling CC below the partial derive's `_BASELOAD_CF = 0.55`.
- **Derive fix.** `derive_campd_unit_outages.py`'s ERCOT branch raised `NameError`, because a later local import of `artifact_class` shadowed the module import. The local import is removed.

**Hidalgo (55545).** Zone `Unknown` (→ `unknown_zone_default` = South_Central) becomes **South** (EIA-860 Hidalgo County; the eGRID zone lookup already reads South). The HR default 7.0 sits inside CAMPD 7762's measured 6.8–7.1 and is left alone.

**Not done, and why.**
- **Decker Creek steam 1–2 (3548).** `load_campd_bins` does not carry `Retirement_*` columns, and the outage and partial derives key one group per plant code (last row wins), so a second 3548 row would also re-route the CT row's windows. It needs a code seam of its own, and its reach is validation years only (retired 2020-10 / 2022-03). Deferred to a follow-up, not forced in here.
- **AVR (7512).** Zone default South_Central is already correct. The optional unit-level CAMPD crosswalk rows (AVR ← 3612 CT01/CT02, Hidalgo ← 7762) are not added: `per_unit_crosswalk` is off in the keeper, so they would be inert.
- **MISO.** Fusco also sits in MISO's EIA-860-BA fleet (`bin_assignments_MISO.csv`, `campd-unit-outages-MISO.csv`), so it is counted twice across the two ISOs. That is the MISO lane's to repair (rule 25); it is reported, not edited.

**Cache key / solve surface.** These are ungated data edits, so the keeper recipe replayed at the pinned SHA *is* the arm. `cache_key()` hashes the config and the solve-surface modules, not these CSVs, so a stale local `results/ERCOT/<key>/` could be served. Shards are fresh containers with no cache. After merge, a re-solve of the old keeper recipe reproduces the arm, not the keeper.

## 2. Zero-LP footprint (fleet-only rebuilds of the keeper recipe, main vs branch)

| year | Fusco capability TWh (pmax×avail) | Fusco applied HR (committed tranche) | Hidalgo capability TWh |
|---|---|---|---|
| 2019 | 3.841 | 7.307 | 3.941 (S_Central → South) |
| 2020 | 5.135 | 7.265 | 3.784 |
| 2021 | 4.470 | 7.348 | 4.003 |
| 2022 | 4.868 | 7.355 | 3.787 |
| 2023 | 4.428 | 7.376 | 3.882 |
| 2024 | 4.436 | 7.340 | 2.867 |
| 2025 | 4.891 | 7.175 | 4.139 |

- Fusco adds 17 tranche rows, 675.6 MW, in Houston, every year.
- **Collateral, attributed from the 2020 build-log diff.** Existing fleet-aggregate constructions respond to the added plant and to Hidalgo's zone move.
  - The ERCOT zonal gas basis spread moves −0.56..3.08 → −0.58..3.06 $/MMBtu. The level anchor is unchanged: −0.50 → EP +0.04.
  - The West deep delivered price moves $1.85 → $1.80.
  - Offer-surface, cleared-share and committed-margin row counts rise by Fusco's own rows.
- **Mean MC shift on other gas rows:** −2.5 $/MWh (2020), −0.3 (2023), +0.02 (2024).
- **Other rows' capability:** |Δ| ≤ 0.008 TWh per row (DAM plant-grain redistribution: 12 → 13 crosswalked CC plants).
- These are real mechanisms responding to the fleet. No new channel is opened.

## 3. G-DRIFT (keeper solve SHA `d20ca118d439c33e7813ffd6ba5f76b11c67c2a0` → origin/main `fcd46045`)

**How the audit was split.** `d20ca118` is the pre-rebase tip of R-ERCOT-5, so the audit splits at R-ERCOT-6's pinned `cf138c01`:
- `d20ca118 → cf138c01`: all INERT in PRECOMMIT-r-ercot-6 §3 and its addendum, reused.
- `cf138c01 → 2f117b63`: 35 files / 103 hunks, classified by a subagent and spot-checked here.
- `2f117b63 → fcd46045`: no change on the audited paths.

**The seven new default-off fields** are all absent from every keeper year: `ercot_dam_availability_event_cap_per_unit` (R-ERCOT-7), `unit_outage_netload_mask_repair`, `unit_outage_coal_extract_basis_share`, `admit_standby_units`, `neiso_winter_fuelsec_conduct_roster`, `nwpp_path76_alturas_link`, `miso_winter_gas_daily_delivered`. All carry the cache-key drop value `"False"`.

**Hunks classified INERT:**
- the shared outage/fleet hunks (net-load-mask companions, extract-basis share, standby admission, `campd_bins` `_mg` pass-through), gated off or ERCOT-excluded;
- the NWPP, NEISO, MISO and SOCO branches;
- derive-time and metadata hunks;
- `_validation-source` PJM, `reference/caiso-supply-consistent-demand`, and `reference/camd-eia-crosswalk` (no solve path reads it).

**ERCOT input files:** unchanged between the two SHAs.

**`_APPLIED_MEASURED_FLAGS`:** still zero `eia923_identity` rows in any ERCOT HR artifact, including the 8 new Fusco rows, which are all `ok`.

**Verdict: nothing LIVE except this lane's own edits (§1). Form 4 is valid.**

## 4. Sealed predictions (arm vs keeper, P1)

**Keeper baseline** (RESULT-r-ercot-5 / RESULT-r-ercot-6):

| year | LW $/MWh | slack MWh | h > $1k | coal TWh | C3a | C3b | C1 fails (keeper) |
|---|---|---|---|---|---|---|---|
| 2019 | 74.94 | 5,806 | 53 | 64.18 | +59.8 % | 1.334 | CC_REGULAR +10.05, COAL_PRB −10.77 |
| 2020 | 28.48 | 0 | 5 | 51.70 | +11.7 % | 0.361 | CC_REGULAR +11.03, COAL_PRB −14.12 |
| 2021 | 169.89 | 6,430 | 123 | 71.74 | +2.6 % | 0.136 | — |
| 2022 | 68.44 | 0 | 18 | 76.70 | −8.1 % | 0.164 | — |
| 2023 | 59.47 | 0 | 59 | 59.89 | −7.5 % | 0.133 | — |
| 2024 | 29.24 | 454 | 2 | 56.84 | −5.6 % | 0.120 | — |
| 2025 | 33.79 | 0 | 0 | 64.61 | −6.9 % | 0.108 | (CC skipped: prelim 923) |

- **P1 (every year).** Fusco P1 generation ∈ [1.5, 4.5] TWh.
  - Model CC_REGULAR rises by between 0 and Fusco's generation (it displaces other CC first).
  - Coal falls by ≤ 0.8 TWh.
- **P2 (C1 CC).** The C1 benchmark gains Fusco's EIA-923 net: 2.34 / 3.43 / 2.75 / 3.39 / 3.31 / 3.40 / 3.65 TWh for 2019–2025.
  - The CC_REGULAR gap (model − actual) therefore moves **down** by 0 to that amount.
  - 2019/2020's +10.05/+11.03 TWh overshoot narrows by 0.5–3.4 TWh. It stays a C1 FAIL.
- **P3 (price).** No year's LW price rises by more than +0.3 %. It falls by
  - ≤ 2.5 % in 2020, 2022, 2023 and 2025;
  - ≤ 5 % in 2019, 2021 and 2024 (the years with scarcity or slack hours, where +676 MW in Houston lands).
- **P4 (tail).** P1 slack and h > $1k do not rise. C3c counts move by ≤ 5 h in each train year.
- **P5 (train tier).** C3a moves cheaper by ≤ 2.5 pts and stays inside ±10 %:
  - 2023 ∈ [−10.0, −7.5]
  - 2024 ∈ [−8.1, −5.6]
  - 2025 ∈ [−9.4, −6.9]
  - C3b moves by ≤ 0.03 in each.
  - **The train (2023–2025) determination stays CALIBRATED.**
- **P6.** No C8 forced-share gate changes a determination. The 2019/2020 NOT-YET stands (COAL_PRB).
- **Named risk.** +676 MW of in-merit Houston CC lowers train-year prices, which already read −5.6 to −7.5 %; 2023 has ~2.5 pts of headroom. The C3a gap is mostly the LZ congestion basis (FINDING-r-ercot-6 §2), and no multiplier is tuned against it (rule 1(c)).

## 5. Decision rule (fixed now)

**Rules 14 and 1 govern.** Fusco is an ERCOT resource in ERCOT's own settlement record. It is kept on that identity, never on the scores.
- If every train year stays CALIBRATED, the recommendation is **promote**, whatever the validation years do.
- If a train year flips to NOT-YET, it is reported at full magnitude with its root cause. The fleet was missing ~676 MW, so a flip means something else was compensating (rule 14). It is put to the owner **with no recommendation to revert**.
- Promotion is the owner's call (rules 31/35). The owner's standing instruction for this session is "promote if a good candidate". Nothing is pruned before that ruling applies.

## 6. DOF ledger (carried VERBATIM from the keeper attestation)

This arm adds **no entry**: a fleet row, a crosswalk seed and a membership rule carry no free scalar. The tranche and commitment columns of the Fusco row copy a named class peer. Offer-curve band multipliers are unchanged leg for leg (rule 1(c)), and `config_partition_overrides` are carried from the keeper untouched.

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

## 7. Execution

**Seven shards**, one per year 2019–2025 (rules 34(c) / 36), from `docs/records/ercot/r-ercot/SHARD-PROMPTS-r-ercot-8.md` pinned to the SHA of the commit carrying this file.

**Each shard:**
- runs `replay_keeper.py results/calibration/r_ercot5_hourgrain_span --years <Y>` with **no `--set`**, because the arm is the data;
- checks the input sha256s below, the config signature and the admission / bin-count log lines;
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
720cb71f75bd6fb42ee572d5677951361be03929f1781f44666b4b2e88fa9295  data/raw/campd-partial-outages-shaped.csv
9d18dc2948f96a50403506a47c01f6b7b84ace6682bee7a139104723e0e313da  data/raw/campd-partial-outages-shaped-dayguard.csv
6c2541198016eb671845cc5b52baf530aa2efd7eab83ff81bfbb3aa7b87b0515  data/raw/campd-partial-outages-units.csv
721b284b67b54e6c49790be5a0a3ca23b0d666ad73ef2239cafcf91c206051c6  data/raw/reference/ercot-dam-plant-crosswalk.csv
0ff1948f98d6281edb1d41d8666fe885db96874f41d0836ff2282c1ecbd66a10  data/raw/reference/ercot-dam-gas-site-seeds.csv
b99a2c58ca5750c894a8e61fe41645512f2b2be375e4d4ee6852a6c989e74919  data/raw/_processed-legacy/campd_cc_heat_rates_ERCOT.csv
```
