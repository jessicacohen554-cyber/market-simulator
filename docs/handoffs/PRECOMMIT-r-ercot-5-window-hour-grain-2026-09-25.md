# PRECOMMIT — R-ERCOT-5: ERCOT CAMPD full-stop windows at their DETECTED hour grain

**Session:** R-ERCOT-5, 2026-09-25. **Written before any solve.** The pinned SHA is the commit that carries this file.
**Keeper and control:** `2026-09-25-r-4-day-guard`, bundle `results/calibration/r_ercot4_dayguard_span`, 2019–2025. Its committed bundle is the control for every year (G-CTRL form 4, rule 29(b)); no control solve is spent.
**Why this arms without a separate owner ask:** the handoff's Step 3 authorizes an arm when Step 1 finds a construction defect with a material footprint. FINDING-r-ercot-5 §3 is that defect (every year, 3.1–4.8 TWh of generation inside the day-expanded windows of the very units they declare out; ~0.7 GW mean restored in 2019's scarcity hours). **Promotion stays the owner's call** (rules 31/35).

## 1. The mechanism (an existing registered field, zero new scalars)

**Field:** `ScenarioConfig.unit_outage_window_hour_grain` (nyiso-229; default `False`; already in the cache-key default-drop list). **No new field** — rule 19: one field for one phenomenon (the day-granular reconstruction of detected-hour windows).

**What changes:** a new ERCOT branch of the field's path selector, ERCOT only.
- `outages.unit_outage_csv_for_iso`: ERCOT + field + no per-unit flag → `data/raw/campd-unit-outages-hourgrain.csv`.
- `outages.unit_outage_short_csv_for_iso` / `unit_outage_short_gas_csv_for_iso` → `-short-hourgrain.csv` / `-shortgas-hourgrain.csv`; `unit_outage_short_derate_factors` forwards `hour_grain`.
- `fleet.arrays`: the availability stack (standard + short layers) AND the ERCOT-148/149 precedence cap's `_cap_layers` read the same grain, so the cap cannot re-impose the edges.
- Every non-ERCOT path is unchanged by construction (the NYISO predicate is untouched; NYISO/other-ISO short paths ignore the flag). Unit tests: `tests/unit/data/test_unit_outage_window_hour_grain.py` (`TestErcotFamily`, `TestErcotCommittedCompanions`), 26 pass.

**The companions** (sha256):
| file | sha256 | rows |
|---|---|---|
| `data/raw/campd-unit-outages-hourgrain.csv` | `9f57063cc84f4017cd389d174863e5a7e0ff7d8d9dae6dd5ad06a04ca2e887a9` | 6,700 |
| `data/raw/campd-unit-outages-short-hourgrain.csv` | `11831770dd9b57efa7c0b6108ac9b44aa2dbd56e26f7cd31c09e3e2f4510e21f` | 177 |
| `data/raw/campd-unit-outages-shortgas-hourgrain.csv` | `6b592d028a856e3d0cfe536128ff3c1fef84a57b48c356a46d8af09afc9bd761` | 3,086 |

**Rule 23 frozen-derive proof.**
- Written by `scripts/data/derive_campd_unit_outages.py --iso ERCOT --hour-grain` with the incumbents' own invocations (std: `--merit-order-guard --years 2019..2026`; short: `--short-windows`; shortgas: `--short-windows --short-window-groups gas --merit-order-guard`; each sidecar records it, now including `hour_grain: true`).
- The deriver's in-process assertions hold: every hour window is a non-empty SUBSET of its day window, its length reproduces `duration_days`, and the base-column projection equals the flag-absent frame.
- **The base-column projection of each companion equals the committed incumbent, whole file** (std: 5,845 re-derived 2019–2026 rows + the 855 committed 2018 rows carried verbatim with null hours — the 2018 CAMPD vintage is gitignored (BLOAT-S2); the loader reconstructs a null-hour row at day grain, per row).
- **Found and fixed on the way:** COAL-SUB relabelled the bin sheet and this deriver silently lost every coal window (std and short re-derived with ZERO coal rows). Repaired through `artifact_class` in the ERCOT branch (the R-ERCOT-4 repair of the partial deriver, same seam). With it the committed ERCOT std / layup / short / shortgas extracts reproduce line-for-line (2019+). The short incumbent and its sidecar re-derive byte-identically with the sidecar-writer change (it records `hour_grain` only when set). The non-ERCOT branch has the same break and is left to its lanes (rule 25).

**Why it is structural (rule 1), not fitted.** A unit cannot be fully stopped and generating in the same hour. The detector detected the window in hours; the schema rounded it to days. Kept or rejected on that identity, never on the residual. Zero new parameters (rule 21): no threshold, no constant.

**Rule 13 forward story.** Measured outage windows are the backcast availability input they already were; the grain is a property of the same detection pass, identical for any year's extract.

## 2. Zero-LP seam (fleet-only, field ON vs keeper; FINDING-r-ercot-5 §3)

- **A/A null:** field OFF at the edited HEAD vs the pre-edit build, 2019: all 251 stage arrays byte-identical (availability pre/post-DAM/final, pmax, mc_base, min_gen).
- Capability restored per year (TWh): coal +0.63…+0.83; CC +2.5…+4.8 gross (−0.65…−1.15 redistributed by the DAM class-hour water-fill); ST +0.5…+1.7 gross.
- Capability below own-hour CEMS (TWh, A → B): CC 3.77 → 2.17 (2019), 4.09 → 2.34 (2020), 3.71 → 1.85 (2021), 4.11 → 2.93 (2023), 4.89 → 3.96 (2024), 4.52 → 3.57 (2025); coal −0.3…−0.4 every year.
- Mean MW restored in P1 >$1k/slack hours: 2019 ~694 (coal 148 / CC 277 / ST 269); 2021 ~865; 2022 ~967; 2023 ~91; 2024 ~1,135.
- Table: `docs/handoffs/r-ercot/r_ercot5_hourgrain_seam.txt`.

## 3. G-DRIFT (keeper leg SHA `845ca5f13c2b1a2777f472406afc8dd8f0a85318` → HEAD)

`git diff 845ca5f1 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib scripts/replay_keeper.py data/raw/_validation-source data/raw/reference` — 12 files, every hunk classified:
- **miso-272 `cc_block_summer_rating`** (scenarios.py field + cache-key tables; eia860.py; assembly.py / run_calibration.py kwarg plumbing; arrays.py point-of-use guard): default-off, absent from the ERCOT recipe; the arrays.py guard is `not is_ercot` — **INERT**.
- **EIA-930 remote-generation double-booking repair** (constants.py table, frames.py, actuals.py rename): keyed to `PSEI` only; ERCO has no entry — **INERT** (and benchmark-side).
- **`_validation-source`**: SPP parquets + NWPP `calibration_reference.json` rows, README — another ISO — **INERT**.
- Nothing LIVE, nothing UNDETERMINED. **Form 4 is valid**: the arm is differenced against the committed keeper numbers. The only other change on the solve path is this arm's own (off-path byte-identical by the A/A null).

## 4. Sealed predictions (arm vs keeper, per year)

Keeper baselines (committed sidecars / R-ERCOT-4 RESULT, official `calibration_verdict`):

| year | LW $/MWh | P1 slack MWh | h > $1k | C3a | C3b | C3c (>$200 h, model vs RT) | verdict |
|---|---|---|---|---|---|---|---|
| 2019 | 93.53 | 6,666.9 | 72 | +99.4 % | 1.837 | 156 vs 106 | NOT-YET |
| 2020 | 30.33 | 0.0 | 5 | +19.0 % | 0.457 | 49 vs 56 | NOT-YET |
| 2021 | 175.12 | 10,266.4 | 131 | +5.8 % | 0.137 | 688 vs 258 | CALIBRATED |
| 2022 | 70.69 | 0.0 | 22 | −5.0 % | 0.128 | 99 vs 196 | CALIBRATED |
| 2023 | 61.37 | 135.2 | 62 | −4.6 % | 0.122 | 187 vs 181 | CALIBRATED |
| 2024 | 31.06 | 641.5 | 5 | +0.2 % | 0.116 | 26 vs 53 (caveat) | CALIBRATED |
| 2025 | 34.34 | 0.0 | 0 | −5.4 % | 0.097 | 1 vs 31 (caveat) | CALIBRATED |

- **P1 (every year).** LW price does not rise; P1 slack does not rise; hours > $1k do not rise. Coal P1 energy rises by 0–0.8 TWh. CC_REGULAR + ST_GAS P1 energy moves by < ±1.5 TWh.
- **P2 (2019, the object).** Slack falls ≥ 20 % (≤ 5,330 MWh). Hours > $1k fall to 50–68. The 14 March + July phantom hours fall by ≥ 5. C3a improves by 3–20 pts and stays FAIL; C3b stays FAIL.
- **P3 (2020).** C3a moves ≤ 3 pts toward actual and stays FAIL; the COAL_PRB gap (−13.56 TWh) closes by < 0.5 TWh. 2020 stays FINDING-r-ercot-3's offer-conduct object.
- **P4 (2021).** Slack falls; C3b stays PASS (≤ 0.17); C3a moves ≤ 5 pts toward cheaper.
- **P5 (2022–2025).** Every year stays CALIBRATED at the year level. Each C3a moves ≤ 4 pts, toward cheaper. 2024's >$200 tail count stays ≤ 26 (its ledgered C3c caveat persists). **Train-tier determination stays CALIBRATED.**
- **P6 (C8 forced share).** No material class crosses its forced-energy cap because of this arm.

## 5. Decision rule (fixed now; identical to R-ERCOT-4 §5)

- **Rule 1 governs.** The grain repair is kept or rejected on the physical identity, not on the scores.
  - If every train year stays CALIBRATED, the recommendation is **promote**, whatever the validation years do.
  - If a train year flips to NOT-YET, report it at full magnitude with its root cause (rule 14) and put it to the owner **with no recommendation to revert**.
- **Promotion is the owner's call** (rules 31/35). Nothing is pruned without that ruling.

## 6. DOF ledger (carried VERBATIM from the keeper attestation)

- 12 entries, 7 residual. This arm adds **no entry**: the only quantities are the detector's own detected start/end hours.
- Offer-curve band multipliers are unchanged leg-for-leg (rule 1(c)). Nothing is re-tuned.

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

**Shards:** seven, one per year 2019–2025 (rules 34(c) / 36). Prompts: `docs/handoffs/r-ercot/SHARD-PROMPTS-r-ercot-5.md`, pinned to the SHA of the commit carrying this file.

**Each shard** runs `replay_keeper.py results/calibration/r_ercot4_dayguard_span --years <Y> --set unit_outage_window_hour_grain=true`, checks the input sha256s, the per-year config signature and the resolved-input record (`campd_unit_outages.path` = the `-hourgrain` companion), and pushes its full bundle (`dispatch/<Y>_P1.parquet` included) through a `.gitignore` negation and a plain `git add`.

**The parent then:** fetches and verifies each leg; composes with `scripts/probes/_r_ercot_compose_span.py --side arm` (field added to MUST_AGREE); `stamp_config_partition.py --check`; attests (keeper attestation, `attested_by` updated); `dashboard_add_run.py --no-prune`; `calibration_verdict --years` per tier; updates the ERCOT matrix cell, writes RESULT + calibration-log entry; archives the shards; asks the promotion question.
